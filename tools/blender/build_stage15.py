"""
CONCORDIA - Etapa 15: Torre del Faro. concordia_v14.blend -> concordia_v15.blend (guardada antes de empezar)
+ export/godot/concordia_faro.glb + docs/reports/stage15_faro.json

Ademas: piezas PIPE_Light_* en BLD_KIT y la curva CRV_LightPipe_Tesoreria_Faro (BLD_PROPS/BLD_PIPES) trazada por
encima de las calles (A* sobre las caras de calle/plaza de TRN_City) a 9 m del suelo, con marcadores de soporte
cada 8 m. Comprobacion de visibilidad de la cima por rayos desde las calles principales.
"""

import heapq
import json
import math
import os
import random
import sys

import bpy  # noqa: I001  (bpy antes que bmesh con el modulo pip)
import bmesh
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import concordia_const as C  # noqa: E402
import stage13_portal as P13  # noqa: E402
import stage15_faro as F  # noqa: E402

REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
SRC = os.path.join(REPO, "blender", f"{C.BLEND_BASENAME}_v14.blend")
OUT = os.path.join(REPO, "blender", f"{C.BLEND_BASENAME}_v15.blend")
REPORT = os.path.join(REPO, "docs", "reports", "stage15_faro.json")
BUDGET = 20000
PIPE_H, SUPPORT_EVERY = 9.0, 8.0
TESORERIA_ROOF_Z = 9.6          # alero supuesto (3 plantas) sobre pad_z: el edificio aun no existe


def save():
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)


def tris(o):
    return sum(len(p.vertices) - 2 for p in o.data.polygons)


def city_bvh():
    o = bpy.data.objects["TRN_City"]
    return BVHTree.FromObject(o, bpy.context.evaluated_depsgraph_get())


def ground_at(bvh, x, y):
    h = bvh.ray_cast(Vector((x, y, 200)), Vector((0, 0, -1)))
    return h[0].z if h[0] else C.Z_PLAZA


# ---------------------------------------------------------------------------
def street_grid(cell=1.0, R=200):
    me = bpy.data.objects["TRN_City"].data

    def corner(n):
        a = me.color_attributes.get(n)
        v = np.zeros(len(me.loops) * 4, dtype=np.float32)
        a.data.foreach_get("color", v)
        return v.reshape(-1, 4)[:, 0]
    ls = np.zeros(len(me.polygons), dtype=np.int64)
    me.polygons.foreach_get("loop_start", ls)
    road, slab, ct = corner("road_mask")[ls], corner("slab_ring_id")[ls], np.rint(corner("cobble_type")[ls] * 8)
    cen = np.zeros(len(me.polygons) * 3, dtype=np.float32)
    me.polygons.foreach_get("center", cen)
    cen = cen.reshape(-1, 3)
    ok = ((road > 0.5) | (slab > 0.01)) & (ct != 7)
    n = int(2 * R / cell) + 1
    g = np.zeros((n, n), dtype=bool)
    ii = np.clip(((cen[ok, 0] + R) / cell).astype(int), 0, n - 1)
    jj = np.clip(((cen[ok, 1] + R) / cell).astype(int), 0, n - 1)
    g[ii, jj] = True
    g2 = g.copy()
    for di in (-1, 0, 1):
        for dj in (-1, 0, 1):
            g2 |= np.roll(np.roll(g, di, 0), dj, 1)
    # obstaculos: parcelas y basamentos de la plaza, pedestal del Portal, piedras y pedestales
    for o in bpy.data.collections["PLAZA"].objects:
        if o.type == "MESH" and o.name.startswith(("TRN_PlazaParcel", "TRN_Pad_", "TRN_PortalPedestal", "TRN_Atrio")):
            bb = [o.matrix_world @ Vector(b) for b in o.bound_box]
            x0, x1 = min(v.x for v in bb) - 1, max(v.x for v in bb) + 1
            y0, y1 = min(v.y for v in bb) - 1, max(v.y for v in bb) + 1
            g2[max(0, int((x0 + R) / cell)):int((x1 + R) / cell) + 1, max(0, int((y0 + R) / cell)):int((y1 + R) / cell) + 1] = False
    return g2, cell, R


def astar(g, a, b):
    n = g.shape[0]
    D = [(1, 0, 1.0), (-1, 0, 1.0), (0, 1, 1.0), (0, -1, 1.0), (1, 1, 1.414), (1, -1, 1.414), (-1, 1, 1.414),
         (-1, -1, 1.414)]
    openh = [(0.0, a, None)]
    best = {a: 0.0}
    prev = {}
    while openh:
        f, cur, d0 = heapq.heappop(openh)
        if cur == b:
            break
        for k, (dx, dy, c) in enumerate(D):
            nx, ny = cur[0] + dx, cur[1] + dy
            if not (0 <= nx < n and 0 <= ny < n) or not g[nx, ny]:
                continue
            turn = 0.0 if d0 is None or d0 == k else 0.6
            ng = best[cur] + c + turn
            if ng < best.get((nx, ny), 1e18):
                best[(nx, ny)] = ng
                prev[(nx, ny)] = cur
                h = math.hypot(b[0] - nx, b[1] - ny)
                heapq.heappush(openh, (ng + h, (nx, ny), k))
    if b not in prev:
        return None
    path = [b]
    while path[-1] != a:
        path.append(prev[path[-1]])
    return path[::-1]


def rdp(pts, eps):
    if len(pts) < 3:
        return pts
    a, b = Vector(pts[0]), Vector(pts[-1])
    ab = b - a
    dmax, idx = 0.0, 0
    for i in range(1, len(pts) - 1):
        p = Vector(pts[i])
        t = 0 if ab.length < 1e-9 else max(0, min(1, (p - a).dot(ab) / ab.length_squared))
        d = (a + ab * t - p).length
        if d > dmax:
            dmax, idx = d, i
    if dmax > eps:
        return rdp(pts[:idx + 1], eps)[:-1] + rdp(pts[idx:], eps)
    return [pts[0], pts[-1]]


def nearest_cell(g, cell, R, p):
    i0, j0 = int((p[0] + R) / cell), int((p[1] + R) / cell)
    best = None
    for r in range(0, 30):
        for i in range(i0 - r, i0 + r + 1):
            for j in range(j0 - r, j0 + r + 1):
                if 0 <= i < g.shape[0] and 0 <= j < g.shape[1] and g[i, j]:
                    d = (i - i0) ** 2 + (j - j0) ** 2
                    if best is None or d < best[0]:
                        best = (d, (i, j))
        if best:
            return best[1]
    return None


def pipe_curve(col, faro_root, stats):
    bvh = city_bvh()
    tes = bpy.data.objects["MARKER_Bld_TesoreriaMuralla"]
    tw = tes.matrix_world
    fwd = (tw.to_3x3() @ Vector((0, 1, 0))).normalized()
    D = float(tes["footprint_d"])
    roof = tw.translation + fwd * (D / 2 - 0.5) + Vector((0, 0, TESORERIA_ROOF_Z))
    street_start = tw.translation + fwd * (D / 2 + 3.0)
    fm = faro_root.matrix_world
    c = fm.translation
    arr_dir = (fm.to_3x3() @ Vector((1, 0, 0))).normalized()          # theta local 0: hacia la Tesoreria
    wall_pt = c + arr_dir * 7.25 + Vector((0, 0, 3.0))
    above = c + arr_dir * 7.6
    street_end = c + arr_dir * 10.5
    g, cell, R = street_grid()
    a = nearest_cell(g, cell, R, street_start)
    b = nearest_cell(g, cell, R, street_end)
    path = astar(g, a, b)
    stats["route_cells"] = len(path) if path else None
    pts = [((i + 0.5) * cell - R, (j + 0.5) * cell - R) for i, j in path]
    pts = rdp(pts, 1.5)
    dense = []
    for (x0, y0), (x1, y1) in zip(pts[:-1], pts[1:]):
        L = math.hypot(x1 - x0, y1 - y0)
        k = max(1, int(L))
        for s in range(k):
            dense.append((x0 + (x1 - x0) * s / k, y0 + (y1 - y0) * s / k))
    dense.append(pts[-1])
    zg = [ground_at(bvh, x, y) for x, y in dense]
    zp = []
    for i in range(len(dense)):
        win = zg[max(0, i - 6):i + 7]
        zp.append(max(win) + PIPE_H)
    poly = [roof] + [Vector((x, y, z)) for (x, y), z in zip(dense, zp)]
    tail = [Vector((above.x, above.y, zp[-1])), Vector((above.x, above.y, wall_pt.z)), wall_pt]
    poly += tail
    cu = bpy.data.curves.new("CRV_LightPipe_Tesoreria_Faro", "CURVE")
    cu.dimensions = "3D"
    sp = cu.splines.new("POLY")
    sp.points.add(len(poly) - 1)
    for p, q in zip(sp.points, poly):
        p.co = (q.x, q.y, q.z, 1.0)
    ob = bpy.data.objects.new("CRV_LightPipe_Tesoreria_Faro", cu)
    col.objects.link(ob)
    ob["from"] = "MARKER_Bld_TesoreriaMuralla (tejado, alero supuesto +9.6 m)"
    ob["to"] = "base del Faro (cara del zocalo, theta local 0, +3.0 m)"
    ob["height_over_street_m"] = PIPE_H
    ob["pipe_diameter_m"] = 0.4
    # soportes cada 8 m sobre el tramo elevado
    length = 0.0
    sup = []
    nxt = 0.0
    elevated = poly[1:len(poly) - 2]
    for p0, p1 in zip(elevated[:-1], elevated[1:]):
        seg = (Vector((p1.x, p1.y, 0)) - Vector((p0.x, p0.y, 0))).length
        while nxt <= length + seg:
            t = (nxt - length) / max(seg, 1e-6)
            q = p0.lerp(p1, t)
            gz = ground_at(bvh, q.x, q.y)
            sup.append((q, gz))
            nxt += SUPPORT_EVERY
        length += seg
    for k, (q, gz) in enumerate(sup, 1):
        e = bpy.data.objects.new(f"MARKER_PipeSupport_{k:02d}", None)
        e.empty_display_type = "PLAIN_AXES"
        col.objects.link(e)
        e.location = (q.x, q.y, gz)
        e["pipe_z"] = round(q.z, 3)
        e["support_height_m"] = round(q.z - gz, 3)
        e["piece"] = "PIPE_Light_Support"
    total = sum((b - a).length for a, b in zip(poly[:-1], poly[1:]))
    stats["pipe_curve"] = {"points": len(poly), "length_m": round(total, 1), "elevated_plan_length_m": round(length, 1),
                           "supports": len(sup), "support_every_m": SUPPORT_EVERY,
                           "start": [round(c, 2) for c in roof], "end": [round(c, 2) for c in wall_pt],
                           "min_clear_over_ground_m": round(min(q.z - gz for q, gz in sup), 2) if sup else None,
                           "note": "solo la curva y los marcadores de soporte; los tubos no se colocan todavia"}


# ---------------------------------------------------------------------------
def visibility(target, exclude_prefix=("FARO_",), stats=None):
    bm = bmesh.new()
    owners = []
    dg = bpy.context.evaluated_depsgraph_get()
    for o in bpy.data.objects:
        if o.type != "MESH" or o.hide_render or o.name.startswith(exclude_prefix) or o.name.endswith(
                ("-colonly", "_LOD1", "_LOD2", "-navmesh", "-occonly")):
            continue
        cn = o.users_collection[0].name if o.users_collection else ""
        if cn.startswith(("MATERIAL_LIBRARY", "BLD_KIT", "EXTERIOR", "GODOT_", "TERRAIN_CHUNKS", "LEGACY", "STREETS_AXES",
                          "WALL_KIT")):
            continue
        bb = [o.matrix_world @ Vector(b) for b in o.bound_box]
        if max(abs(v.x) for v in bb) > 260:
            continue
        me = o.evaluated_get(dg).to_mesh()
        n0 = len(bm.faces)
        tmp = bmesh.new()
        tmp.from_mesh(me)
        tmp.transform(o.matrix_world)
        tm = bpy.data.meshes.new("TMP_vis")
        tmp.to_mesh(tm)
        tmp.free()
        bm.from_mesh(tm)
        bpy.data.meshes.remove(tm)
        o.evaluated_get(dg).to_mesh_clear()
        owners.append((n0, len(bm.faces), o.name))
    bvh = BVHTree.FromBMesh(bm)
    gb = city_bvh()
    g, cell, R = street_grid()

    def on_street(x, y):
        i, j = int((x + R) / cell), int((y + R) / cell)
        return 0 <= i < g.shape[0] and 0 <= j < g.shape[1] and g[i, j]

    def owner(fi):
        for a, b, n in owners:
            if a <= fi < b:
                return n
        return "?"
    streets = {}
    for name, d in (("Avenida Norte", (0, 1)), ("Avenida Sur", (0, -1)), ("Avenida Este", (1, 0)),
                    ("Avenida Oeste", (-1, 0))):
        streets[name] = [(d[0] * r, d[1] * r) for r in range(62, 192, 8)]
    for rr in (100, 150):
        streets[f"Ronda r{rr}"] = [(rr * math.cos(math.radians(a)), rr * math.sin(math.radians(a))) for a in range(0, 360, 6)]
    rep = {}
    for name, pts in streets.items():
        vis, tot, block = 0, 0, {}
        for x, y in pts:
            if not on_street(x, y):
                continue
            eye = Vector((x, y, ground_at(gb, x, y) + 1.7))
            d = target - eye
            h = bvh.ray_cast(eye, d.normalized(), d.length - 0.3)
            tot += 1
            if h[0] is None:
                vis += 1
            else:
                n = owner(h[2])
                block[n] = block.get(n, 0) + 1
        rep[name] = {"samples": tot, "visible": vis, "pct": round(100 * vis / max(1, tot), 1),
                     "blocked_by": dict(sorted(block.items(), key=lambda kv: -kv[1])[:4])}
    bm.free()
    if stats is not None:
        stats["visibility"] = {"target": [round(c, 2) for c in target], "per_street": rep,
                               "note": "aun no hay edificios: hay que repetirlo cuando existan"}
    return rep


# ---------------------------------------------------------------------------
def main():
    st = {}
    bpy.ops.wm.open_mainfile(filepath=SRC)
    save()
    st["saved_before"] = os.path.relpath(OUT, REPO)
    st["materials"] = F.ensure_materials()
    import concordia_buildings as B
    col = bpy.data.collections["BLD_PORTAL"]
    for o in [o for o in col.objects if o.name.startswith(("FARO", "MARKER_Faro_Door"))]:
        bpy.data.objects.remove(o)
    mk = bpy.data.objects["MARKER_Faro"]
    mw = mk.matrix_world.copy()
    root = bpy.data.objects.new("FARO", None)
    col.objects.link(root)
    root.matrix_world = mw
    root["landmark"] = "Torre del Faro"

    def attach(o):
        o.parent = root
        o.matrix_parent_inverse = root.matrix_world.inverted()
        return o
    rng = random.Random(F.SEED)
    gb = city_bvh()
    inv = mw.inverted()

    def ground_local(r, t):
        p = mw @ F.pol(r, t, 0)
        return (inv @ Vector((p.x, p.y, ground_at(gb, p.x, p.y)))).z + 0.004
    # piedra (zocalo + fuste + galeria) -> puerta y canales por Boolean
    core, cornice, upper, cols, t_arr = F.build_stone(rng)
    so = core.to_object("TMP_FaroStone", col)
    so.matrix_world = mw
    co_o = cornice.to_object("TMP_FaroCornice", col)
    co_o.matrix_world = mw
    up_o = upper.to_object("TMP_FaroUpper", col, recalc=False)
    up_o.matrix_world = mw
    glow = P13.Mesh()
    P13.BOOL_LOG.clear()
    P13.boolean_cut(so, F.channel_cutters_and_strips(glow))
    ccut = F.channel_cutters_and_strips(P13.Mesh())
    for cme in ccut:
        P13.PROBES[cme.name] = []          # la sonda del canal no cae sobre la cornisa: se corta sin verificar
    P13.boolean_cut(co_o, ccut)
    st["boolean"] = list(P13.BOOL_LOG)
    F.ground_ring(glow, ground_local)
    extra = P13.Mesh()
    F.build_ramp(extra, 0)
    F.build_stair(extra)
    F.door_frame(extra)
    F.door_leaf(extra)
    # unir piedra + rampa/escalera/puerta + canales emisivos
    bm = bmesh.new()
    mats = []
    for me_src, names in ((so.data, [m.name for m in so.data.materials]), (None, extra.mats), (None, glow.mats)):
        pass
    tmp_objs = [co_o, up_o]
    for mm, nm in ((extra, "TMP_extra"), (glow, "TMP_glow")):
        o = mm.to_object(nm, col)
        o.matrix_world = mw
        tmp_objs.append(o)
    allo = [so] + tmp_objs
    for o in allo:
        off = len(mats)
        mats += [m.name for m in o.data.materials]
        t = o.data.copy()
        for p in t.polygons:
            p.material_index += off
        bm.from_mesh(t)
        bpy.data.meshes.remove(t)
    uniq = []
    for n in mats:
        if n not in uniq:
            uniq.append(n)
    remap = {i: uniq.index(n) for i, n in enumerate(mats)}
    for f in bm.faces:
        f.material_index = remap[f.material_index]
    me = bpy.data.meshes.new("FARO_Body")
    bm.to_mesh(me)
    bm.free()
    for n in uniq:
        me.materials.append(bpy.data.materials[n])
    for o in allo:
        d = o.data
        bpy.data.objects.remove(o)
        bpy.data.meshes.remove(d)
    body = bpy.data.objects.new("FARO_Body", me)
    col.objects.link(body)
    body.matrix_world = mw
    attach(body)
    B.box_uv(body)
    lods = P13.lods(body, col)
    for tag in ("LOD1", "LOD2"):
        attach(bpy.data.objects[f"FARO_Body_{tag}"])
    crystal, ctop = F.build_crystal(col, rng)
    crystal.matrix_world = mw
    attach(crystal)
    B.box_uv(crystal)
    beam = F.build_beam(col, ctop - 1.0)
    beam.matrix_world = mw
    attach(beam)
    # colision
    cm = P13.Mesh()
    F.frustum(cm, F.ZOC_R, F.ZOC_R, 0.0, F.ZOC_H, F.BASE, n=24, caps=True)
    for z0, z1, r0, r1 in F.SECTIONS:
        F.frustum(cm, r0, r1, z0, z1, F.BASE, n=16, caps=True)
    F.frustum(cm, F.GAL_R, F.GAL_R, F.Z_GAL - 0.45, F.Z_GAL, F.BASE, n=16, caps=True)
    colo = cm.to_object("FARO-colonly", col, )
    colo.data.materials.clear()
    colo.matrix_world = mw
    colo.hide_render = True
    attach(colo)
    rm = P13.Mesh()
    F.build_ramp(rm, 1)
    F.build_stair(rm)
    rcol = rm.to_object("FARO_Ramp-colonly", col)
    rcol.data.materials.clear()
    rcol.matrix_world = mw
    rcol.hide_render = True
    attach(rcol)
    # puerta
    dm = bpy.data.objects.new("MARKER_Faro_Door", None)
    dm.empty_display_type = "SINGLE_ARROW"
    col.objects.link(dm)
    dm.matrix_world = mw @ __import__("mathutils").Matrix.Translation(F.pol(F.ZOC_R, F.DOOR_T, 0))
    attach(dm)
    dm["axis"] = "+Y hacia fuera (hacia la plaza)"
    # tubos de luz: piezas del kit y curva
    kit = bpy.data.collections["BLD_KIT"]
    pieces = F.build_pipe_kit(kit)
    for o in pieces.values():
        B.box_uv(o)
    props = bpy.data.collections["BLD_PROPS"]
    pcol = bpy.data.collections.get("BLD_PIPES") or bpy.data.collections.new("BLD_PIPES")
    if pcol.name not in props.children:
        props.children.link(pcol)
    for o in list(pcol.objects):
        bpy.data.objects.remove(o)
    pipe_curve(pcol, root, st)
    st["pipe_kit"] = {n: o["tris"] for n, o in pieces.items()}
    # numeros
    t_body, t_cr, t_beam = tris(body), tris(crystal), tris(beam)
    st.update({"tris": {"FARO_Body": t_body, "FARO_Crystal": t_cr, "FARO_Beam": t_beam,
                        "total": t_body + t_cr + t_beam}, "budget": BUDGET, "ok": t_body + t_cr + t_beam <= BUDGET,
               "lods": lods, "crystal_top_local_m": round(ctop, 2),
               "height_total_m": round(ctop, 2), "ramp": {"turns": F.RAMP_TURNS, "pitch_m": round(F.PITCH, 3),
                                                         "width_m": F.RAMP_W, "arrival_deg": round(math.degrees(t_arr) % 360, 1)},
               "channels": {"count": 4, "width_m": F.CH_W, "depth_m": F.CH_D,
                            "vertical_clearance_to_ramp_m": [round(F.PITCH * f, 2) for f in (0.625, 0.375, 0.125, 0.875)]},
               "collision": [colo.name, rcol.name]})
    target = mw @ Vector((0, 0, ctop))
    visibility(target, stats=st)
    import stage11_godot as G
    objs = [root] + [o for o in col.objects if o.name.startswith(("FARO", "MARKER_Faro_Door")) and o is not root]
    path = os.path.join(REPO, "export", "godot", "concordia_faro.glb")
    size = G.export_glb(objs, path)
    st["export"] = {"file": os.path.relpath(path, REPO), "mb": round(size / 2 ** 20, 2), **G.glb_info(path)}
    save()
    with open(REPORT, "w") as fh:
        json.dump(st, fh, indent=1, ensure_ascii=False, default=str)
    print("saved:", OUT)
    print(json.dumps({k: st[k] for k in ("tris", "ok", "lods", "boolean", "pipe_curve", "pipe_kit", "height_total_m")},
                     default=str))
    print(json.dumps({k: (v["pct"], v["samples"], v["blocked_by"]) for k, v in st["visibility"]["per_street"].items()},
                     ensure_ascii=False))


if __name__ == "__main__":
    main()
