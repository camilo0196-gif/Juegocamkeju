"""
CONCORDIA - Etapa 18 (E5): el Mercado. concordia_v17.blend -> concordia_v18.blend (guardada antes de empezar)
+ export/godot/concordia_mercado.glb + docs/reports/stage18_mercado.json

Kit (concordia_buildings.build_building / fit_iso_height): Banco, Posada, Casa del Registro, MER_Casa_01..10.
A mano (stage18_mercado): Tesoreria de la Muralla, Gran Subasta, STALL_A..E, Fuente del Mercado, Tablon de Grupos,
letrero con vela, letrero de libro, puerta y candado del Banco.
Ademas (pendiente D de la etapa 17): LOD2 de color plano para Santuario, Salon y Faro (y para los edificios a mano
del Mercado), y la curva de los tubos de luz se engancha a la salida real del tejado de la Tesoreria.
"""

import json
import math
import os
import random
import sys

import bpy  # noqa: I001
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import concordia_const as C  # noqa: E402
import bld_kit as K  # noqa: E402
import concordia_buildings as B  # noqa: E402
import stage13_portal as P13  # noqa: E402
import stage16_landmarks as L  # noqa: E402
import stage18_mercado as M  # noqa: E402
import build_stage16 as B16  # noqa: E402
import lod_utils as LU  # noqa: E402

REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
SRC = os.path.join(REPO, "blender", f"{C.BLEND_BASENAME}_v17.blend")
OUT = os.path.join(REPO, "blender", f"{C.BLEND_BASENAME}_v18.blend")
REPORT = os.path.join(REPO, "docs", "reports", "stage18_mercado.json")
SEED = 1801
BUDGET = {"TesoreriaMuralla": 8000, "Banco": 6000, "GranSubasta": 7000, "Posada": 6500, "CasaRegistro": 3000,
          "STALL": 500, "FuenteMercado": 3000}


def save():
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)


def tris(o):
    return sum(len(p.vertices) - 2 for p in o.data.polygons) if o and o.type == "MESH" else 0


def mk(name):
    return bpy.data.objects[f"MARKER_Bld_{name}"]


def ground_fn():
    import build_stage15 as B15
    gb = B15.city_bvh()
    return lambda x, y: B15.ground_at(gb, x, y)


def collider(mb, name, col, root):
    me = bpy.data.meshes.new(name)
    mb.bm.to_mesh(me)
    mb.bm.free()
    o = bpy.data.objects.new(name, me)
    col.objects.link(o)
    o.parent = root
    o.display_type = "WIRE"
    o.hide_render = True
    return o


def custom_lods(body, roof, col, root, voxel=0.35, massing=None):
    """LOD1: diezmado 50 % de cuerpo y techo; LOD2: envolvente de color plano (pendiente D)."""
    out = {"LOD1": P13.lods(body, col, (("LOD1", 0.5),))["LOD1"]}
    if roof is not None:
        out["LOD1"] += P13.lods(roof, col, (("LOD1", 0.5),))["LOD1"]
    src = [body] + ([roof] if roof is not None else [])
    if massing:
        o, n, mat, note = LU.massing_lod2(massing, f"{body.name}_LOD2", src, col, root)
    else:
        o, n, mat, note = LU.flat_lod2(f"{body.name}_LOD2", src, col, root, int(0.15 * sum(tris(s) for s in src)),
                                       voxel=voxel)
    out["LOD2"], out["LOD2_material"] = n, note
    for s in src:
        for suf in ("_LOD1",):
            lo = bpy.data.objects.get(s.name + suf)
            if lo:
                lo.parent = root
                lo.matrix_parent_inverse = Matrix.Identity(4)
                lo.matrix_basis = s.matrix_basis.copy()
    return out


def iso_check(root, objs):
    bpy.context.view_layer.update()
    blk = B.iso_blocked([o for o in objs if o is not None], B.iso_targets(exclude_root=root))
    return sorted({n for n, _ in blk})


def awnings(marker_name, door_world, pcol, parent, prefix, skip_r=2.0):
    m = bpy.data.objects[marker_name]
    W = float(m["width_m"])
    inv = m.matrix_world.inverted()
    dl = inv @ door_world if door_world is not None else None
    items = []
    n = max(1, int(W // 3.0))
    for k in range(n):
        x = -W / 2 + 3.0 * (k + 0.5) + (W - 3.0 * n) / 2
        if dl is not None and abs(x - dl.x) < skip_r:
            continue
        items.append((x, k))
    objs = []
    for x, k in items:
        kind = ("AWNING_Patch_A", "AWNING_Patch_B", "AWNING_Patch_C")[k % 3]
        o = bpy.data.objects.new(f"{prefix}_Prop_{kind}_{k:02d}", B.prop_mesh(kind))
        pcol.objects.link(o)
        o.parent = parent
        o.matrix_world = m.matrix_world @ Matrix.Translation((x, 0.02, 2.9))
        objs.append(o)
    return objs


# ---------------------------------------------------------------------------
def build_tesoreria(col, pcol, st):
    name = "TesoreriaMuralla"
    m = mk(name)
    root = B16.new_root(name, m, col, "Tesoreria de la Muralla")
    rng = random.Random(B.rng_for(name, SEED))
    bmb, rmb, info = M.tesoreria_meshes(rng)
    body = B16.mesh_obj(bmb, f"{name}_Body", col, root)
    roof = B16.mesh_obj(rmb, f"{name}_Roof", col, root)
    lods = custom_lods(body, roof, col, root, massing="TesoreriaMuralla")
    T = M.TES
    dm = B16.door_marker(name, col, root, info["door_local"])
    c, sz = info["interior"]["center"], info["interior"]["size"]
    iv = B16.interior(name, col, root, sz[0] / 2, sz[1] / 2, sz[2], {"note": "planta baja + principal; vitrinas despues"})
    iv.location = (c[0], c[1], 0.0)
    cm = K.MB()
    cm.box((-T.W / 2, -T.D / 2, 0.0), (T.W / 2, T.YP, T.PAR), "MAT_Wall_Gray")
    cm.box((-T.W / 2, T.YP, T.F1), (T.W / 2, T.YF, T.PAR), "MAT_Wall_Gray")
    for cx in [T.BAY * k for k in range(-3, 4)][:-1]:
        u = cx + T.BAY / 2
        cm.box((u - 0.5, T.YF - T.T, 0.0), (u + 0.5, T.YF + 0.3, T.F1), "MAT_Wall_Gray")
    for u in (-T.W / 2 + 0.6, T.W / 2 - 0.6):
        cm.box((u - 0.6, T.YF - T.T, 0.0), (u + 0.6, T.YF, T.F1), "MAT_Wall_Gray")
    cm.box((T.TOWER[0], T.TOWER[2], T.PAR), (T.TOWER[1], T.TOWER[3], T.CROWN), "MAT_Wall_Gray")
    colo = collider(cm, f"{name}-colonly", col, root)
    # salidas de tubos (mundo) y marcadores
    mw = m.matrix_world
    outs = []
    for k, (x, y, z) in enumerate(info["outlets_local"], 1):
        e = bpy.data.objects.new(f"MARKER_PipeOutlet_{name}_{k:02d}", None)
        e.empty_display_type = "SPHERE"
        e.empty_display_size = 0.3
        col.objects.link(e)
        e.parent = root
        e.location = (x, y, z)
        e["outlet_z_over_pad_m"] = z
        e["pipe_diameter_m"] = 0.4
        outs.append(e)
    t = {"Body": tris(body), "Roof": tris(roof)}
    t["total"] = t["Body"] + t["Roof"]
    st[name] = {"marker": m.name, "tris": t, "budget": BUDGET[name], "ok": t["total"] <= BUDGET[name], "lods": lods,
                "dims": {"footprint": [T.W, T.D], "floors": 2, "floor_z": [T.F1, T.F2], "parapet": T.PAR,
                         "merlons_top": T.MER, "tower_top": T.CROWN, "arcade": "7 arcos de medio punto 2.8 m, 6 columnas",
                         "scales_bronze_m": 1.2, "outlets_z_over_pad": T.OUTLET_Z},
                "merlons": info["merlons"], "stone_patches": info["stone_patches"],
                "door_marker": dm.name, "interior": [iv.name, list(iv["interior_size_m"])], "collision": colo.name,
                "iso_blocks": iso_check(root, [body, roof]),
                "footprint_check": B16.check_footprint(body, T.W / 2, T.D / 2)}
    return root, outs


def hook_pipe(outs, st):
    """Engancha CRV_LightPipe_Tesoreria_Faro a la salida real (la mas cercana al segundo punto) pasando por la almenara
    que tiene delante."""
    cu = bpy.data.objects["CRV_LightPipe_Tesoreria_Faro"]
    sp = cu.data.splines[0]
    pts = [Vector(p.co[:3]) for p in sp.points]
    old0 = pts[0].copy()
    nxt = pts[1]
    best = min(outs, key=lambda e: (e.matrix_world.translation.xy - nxt.xy).length)
    p_out = best.matrix_world.translation.copy()
    root = best.parent
    crenel = root.matrix_world @ Vector((best.location.x, M.TES.YF + 0.6, best.location.z))
    new = [p_out, crenel] + pts[1:]
    cu.data.splines.clear()
    s2 = cu.data.splines.new("POLY")
    s2.points.add(len(new) - 1)
    for p, q in zip(s2.points, new):
        p.co = (q.x, q.y, q.z, 1.0)
    cu["provisional_first_point"] = False
    cu["first_point_note"] = f"salida real {best.name} (+{M.TES.OUTLET_Z} m sobre el pad), por la almenara de delante"
    e = bpy.data.objects.get("MARKER_PipeOutlet_TesoreriaMuralla")
    if e is not None:
        e.location = p_out
        e["provisional"] = False
        e["outlet"] = best.name
    best["connected_curve"] = cu.name
    pad_z = mk("TesoreriaMuralla")["pad_z"]
    st["pipe_hook"] = {"outlet": best.name, "outlet_world": [round(c, 3) for c in p_out],
                       "outlet_z_over_pad": round(p_out.z - pad_z, 3), "within_9p6_pm0p5": abs(p_out.z - pad_z - 9.6) <= 0.5,
                       "old_first_point": [round(c, 3) for c in old0], "moved_m": round((p_out - old0).length, 2),
                       "crenel_point": [round(c, 3) for c in crenel], "points": len(new)}


def build_banco(col, pcol, st):
    name = "Banco"

    def plan_edit(plan, rng):
        for m_ in plan:
            if m_["kind"] == "Door":
                continue
            m_["kind"] = "Solid"
            n = m_["n"]
            if m_["side"] == "front" and ((m_["floor"] == 0 and m_["i"] in (1, n - 2)) or
                                          (m_["floor"] == 1 and m_["i"] in (1, n // 2, n - 2))):
                m_["kind"] = "Barred"
            elif m_["side"] in ("left", "right", "back") and m_["floor"] == 1 and m_["i"] == n // 2:
                m_["kind"] = "Barred"
    root, objs, rep = B.fit_iso_height(name, 2, marker=mk(name), tipo_techo="flat", estilo="stone", seed=SEED,
                                       collection=col, props_collection=pcol, module_w=4.0, plan_edit=plan_edit,
                                       opts={"wall_mat": "MAT_Limestone_Light", "no_buttress": True})
    body = objs["Body"]
    W, D = rep["footprint"]
    dx = rep["door_local"][0]
    ex = K.MB()
    n_blocks = M.banco_extras(ex, dx, 1.3, 2.35, D / 2, W, random.Random(SEED))
    M.merge_mb_into(body, ex)
    ex.bm.free()
    B.box_uv(body)
    cm = K.MB()
    cm.box((-W / 2, -D / 2, 0.0), (W / 2, D / 2, rep["eave_height_m"] + 0.9), "MAT_Wall_Gray")
    colo = collider(cm, f"{name}-colonly", col, root)
    _finish_kit(name, root, objs, rep, st, colo, extra={"rustication_blocks": n_blocks,
                                                         "door": "hierro negro + candado de 1 m"})
    return root


def ground_footprint(o, hx, hy, zmax=2.2):
    """Como check_footprint pero solo con lo que esta por debajo de zmax (los balcones y aleros vuelan por encima)."""
    vs = [v.co for v in o.data.vertices if v.co.z < zmax]
    xs, ys = [v.x for v in vs], [v.y for v in vs]
    return {"over_x_m": round(max(0.0, max(xs) - hx, -hx - min(xs)), 3),
            "over_y_m": round(max(0.0, max(ys) - hy, -hy - min(ys)), 3), "below_z_m": zmax}


def _finish_kit(name, root, objs, rep, st, colo, extra=None):
    t = {k: tris(o) for k, o in objs.items() if k in ("Body", "Roof")}
    props = [c for c in root.children_recursive if "_Prop_" in c.name]
    t["Props"] = sum(tris(o) for o in props)
    t["total_body_roof"] = t.get("Body", 0) + t.get("Roof", 0)
    W, D = rep["footprint"]
    st[name] = {"marker": rep.get("marker"), "floors": rep["floors"], "style": rep["style"], "roof": rep["roof"],
                "eave_m": rep["eave_height_m"], "ridge_m": rep["ridge_height_m"], "tris": t,
                "budget": BUDGET.get(name), "ok": (t["total_body_roof"] <= BUDGET[name]) if name in BUDGET else None,
                "budget_class": rep.get("budget_class"), "lod_ratios": [rep["lod1_ratio"], rep["lod2_ratio"]],
                "iso_rule": rep.get("iso_rule"), "collision": colo.name if colo else None,
                "footprint_check": B16.check_footprint(objs["Body"], W / 2, D / 2),
                "footprint_ground_check": ground_footprint(objs["Body"], W / 2, D / 2), "door_local": rep["door_local"],
                **(extra or {})}


def build_subasta(col, pcol, st):
    name = "GranSubasta"
    m = mk(name)
    root = B16.new_root(name, m, col, "Gran Subasta (pabellon abierto)")
    root["interior"] = False
    rng = random.Random(B.rng_for(name, SEED))
    bmb, rmb, cmb, info = M.subasta_meshes(rng)
    body = B16.mesh_obj(bmb, f"{name}_Body", col, root)
    roof = B16.mesh_obj(rmb, f"{name}_Roof", col, root)
    lods = custom_lods(body, roof, col, root, massing="GranSubasta")
    colo = collider(cmb, f"{name}-colonly", col, root)
    t = {"Body": tris(body), "Roof": tris(roof)}
    t["total"] = t["Body"] + t["Roof"]
    S = M.SUB
    st[name] = {"marker": m.name, "tris": t, "budget": BUDGET[name], "ok": t["total"] <= BUDGET[name], "lods": lods,
                "dims": {"footprint": [S.W, S.D], "galleries_z": S.Z_GAL, "eave_z": S.Z_EAVE, "ridge_z": S.RIDGE,
                         "posts": 4 * S.NX, "platform": "5 x 3 x 0.8", "bell_m": 1.2, "price_boards": 6,
                         "roof_pitch_deg": info["pitch_deg"]},
                "roof_repairs": info["roof_repairs"], "collision": colo.name,
                "note": "pabellon abierto (interior=false por el prompt; el marcador decia interior=true): sin "
                        "MARKER_Door ni InteriorVolume. MARKER_Awning_03 no se usa: el alero de la cubierta hace de toldo.",
                "iso_blocks": iso_check(root, [body, roof]),
                "footprint_check": B16.check_footprint(body, S.W / 2, S.D / 2)}
    return root


def build_posada(col, pcol, st):
    name = "Posada"
    root, objs, rep = B.fit_iso_height(name, 3, marker=mk(name), tipo_techo="gable", estilo="timber", seed=SEED,
                                       collection=col, props_collection=pcol, module_w=4.0,
                                       opts={"side_detail": {"back": 1, "left": 1, "right": 1}, "roof_seg": 4.0,
                                             "eave": 0.9, "n_balconies": 2, "no_buttress": True})
    W, D = rep["footprint"]
    ridge = rep["ridge_height_m"]
    # chimenea enorme de piedra junto al hastial izquierdo, sobre la cumbrera
    ch = K.MB()
    x = -W / 2 + 2.6
    z0 = ridge - 2.2
    ch.box((x - 1.1, -0.8, z0), (x + 1.1, 0.8, ridge + 2.6), K.M_STONE, skip=("z-",))
    ch.box((x - 1.25, -0.95, ridge + 2.2), (x + 1.25, 0.95, ridge + 2.4), K.M_STONE)
    ch.box((x - 1.3, -1.0, ridge + 2.95), (x + 1.3, 1.0, ridge + 3.05), K.M_STONE)
    for dx in (-0.6, 0.6):
        ch.box((dx + x - 0.12, -0.12, ridge + 2.6), (dx + x + 0.12, 0.12, ridge + 2.95), K.M_STONE, skip=("z-",))
        ch.cylinder(0.14, ridge + 2.6, ridge + 3.3, 6, K.M_GRAY, caps=False, center=(x + dx, 0.0))
    M.merge_mb_into(objs["Roof"], ch)
    ch.bm.free()
    B.box_uv(objs["Roof"])
    # letrero con vela: sustituye al letrero colgante del kit
    cs = L._shared_mesh("POSADA_CandleSign", M.candle_sign, B.box_uv)
    sign = next((c for c in root.children_recursive if "SIGN_Hanging" in c.name), None)
    if sign is not None:
        sign.data = cs
        sign.name = f"{name}_Prop_CandleSign"
    # Tablon de Grupos (objeto aparte, en su marcador)
    tm = bpy.data.objects["MARKER_Prop_TablonGrupos"]
    tb = L._shared_mesh("POSADA_TablonGrupos", lambda mb: M.tablon(mb, random.Random(SEED + 5)), B.box_uv)
    to = bpy.data.objects.new("Posada_TablonGrupos", tb)
    col.objects.link(to)
    to.matrix_world = tm.matrix_world.copy()
    to["interactive"] = True
    to["size_m"] = "3 x 2"
    tcm = K.MB()
    tcm.box((-1.7, -0.2, 0.0), (1.7, 0.2, 3.0), "MAT_Wall_Gray")
    tco = collider(tcm, "Posada_TablonGrupos-colonly", col, None)
    tco.matrix_world = tm.matrix_world.copy()
    aw = awnings("MARKER_Awning_01", root.matrix_world @ Vector(rep["door_local"]), pcol,
                 next(c for c in root.children if c.name.endswith("_Props")), name)
    cm = K.MB()
    cm.box((-W / 2, -D / 2, 0.0), (W / 2, D / 2, rep["eave_height_m"]), "MAT_Wall_Gray")
    colo = collider(cm, f"{name}-colonly", col, root)
    _finish_kit(name, root, objs, rep, st, colo, extra={"chimney_top_m": round(ridge + 3.3, 2), "awnings": len(aw),
                                                         "tablon": [to.name, tris(to)], "candle_sign": tris(sign) if sign else None})
    return root, to


def build_registro(col, pcol, st):
    name = "CasaRegistro"
    root, objs, rep = B.fit_iso_height(name, 2, marker=mk(name), tipo_techo="gable_front", estilo="guild", seed=SEED,
                                       collection=col, props_collection=pcol, module_w=4.0,
                                       opts={"side_detail": {"back": 2, "left": 2, "right": 2}, "roof_seg": 6.0,
                                             "no_buttress": True})
    W, D = rep["footprint"]
    dx = rep["door_local"][0]
    nb = L._shared_mesh("REGISTRO_NoticeBoard", lambda mb: M.notice_board(mb, random.Random(SEED + 9)), B.box_uv)
    bk = L._shared_mesh("REGISTRO_BookSign", M.book_sign, B.box_uv)
    pe = next(c for c in root.children if c.name.endswith("_Props"))
    items = []
    for k, x in enumerate((dx - 2.3, dx + 2.3)):
        if abs(x) > W / 2 - 0.8:
            x = dx - 2.3 if x > dx else dx + 2.3
        o = bpy.data.objects.new(f"{name}_Prop_NoticeBoard_{k:02d}", nb)
        pcol.objects.link(o)
        o.parent = pe
        o.location = (x, D / 2 + 0.02, 1.0)
        items.append(o)
    sign = next((c for c in root.children_recursive if "SIGN_Hanging" in c.name), None)
    if sign is not None:
        sign.data = bk
        sign.name = f"{name}_Prop_BookSign"
    aw = awnings("MARKER_Awning_02", root.matrix_world @ Vector(rep["door_local"]), pcol, pe, name, skip_r=3.2)
    cm = K.MB()
    cm.box((-W / 2, -D / 2, 0.0), (W / 2, D / 2, rep["eave_height_m"]), "MAT_Wall_Gray")
    colo = collider(cm, f"{name}-colonly", col, root)
    _finish_kit(name, root, objs, rep, st, colo, extra={"notice_boards": len(items), "awnings": len(aw)})
    return root


def build_casas(col, pcol, st):
    roots = []
    for k in range(1, 11):
        name = f"MER_Casa_{k:02d}"
        rng = random.Random(B.rng_for(name, SEED))
        estilo = rng.choice(("timber", "timber", "guild", "stone"))
        techo = rng.choice(("gable", "gable_front", "hip"))
        use = rng.choice(("house", "shop", "house"))
        pisos = rng.choice((2, 3, 3))
        root, objs, rep = B.fit_iso_height(name, pisos, marker=mk(name), tipo_techo=techo, estilo=estilo, seed=SEED + k,
                                           collection=col, props_collection=pcol, use=use,
                                           opts={"side_detail": {"back": 1}, "roof_seg": 3.5, "no_buttress": True})
        W, D = rep["footprint"]
        cm = K.MB()
        cm.box((-W / 2, -D / 2, 0.0), (W / 2, D / 2, rep["eave_height_m"]), "MAT_Wall_Gray")
        colo = collider(cm, f"{name}-colonly", col, root)
        extra = {}
        if k == 1:
            extra["awnings"] = len(awnings("MARKER_Awning_04", root.matrix_world @ Vector(rep["door_local"]), pcol,
                                           next(c for c in root.children if c.name.endswith("_Props")), name))
        _finish_kit(name, root, objs, rep, st.setdefault("casas", {}), colo, extra={"use": use, **extra})
        roots.append(root)
    return roots


def build_stalls(col, kit, st):
    protos = {}
    for i, v in enumerate("ABCDE"):
        me = L._shared_mesh(f"STALL_{v}", lambda mb, v=v: M.stall(mb, v, random.Random(SEED + i)), B.box_uv)
        o = bpy.data.objects.get(f"STALL_{v}") or bpy.data.objects.new(f"STALL_{v}", me)
        o.data = me
        if o.name not in kit.objects:
            kit.objects.link(o)
        o.location = (3000.0 + 5.0 * i, 900.0, 0.0)
        o["tris"] = tris(o)
        protos[v] = o
    cme = bpy.data.meshes.get("STALL-colonly_mesh")
    if cme is None:
        cm = K.MB()
        cm.box((-1.4, 0.55, 0.0), (1.4, 1.45, 1.0), "MAT_Wall_Gray")
        cme = bpy.data.meshes.new("STALL-colonly_mesh")
        cm.bm.to_mesh(cme)
        cm.bm.free()
    inst = []
    for k in range(1, 15):
        m = mk(f"PuestoProvisiones_{k:02d}")
        v = "ABCDE"[(k - 1) % 5]
        o = bpy.data.objects.new(f"PuestoProvisiones_{k:02d}", protos[v].data)
        col.objects.link(o)
        o.matrix_world = m.matrix_world.copy()
        o["stall_variant"] = f"STALL_{v}"
        c = bpy.data.objects.new(f"PuestoProvisiones_{k:02d}-colonly", cme)
        col.objects.link(c)
        c.parent = o
        c.hide_render = True
        c.display_type = "WIRE"
        inst.append(o)
    st["stalls"] = {"variants": {k: v["tris"] for k, v in protos.items()}, "budget": BUDGET["STALL"],
                    "ok": all(v["tris"] <= BUDGET["STALL"] for v in protos.values()), "instances": len(inst),
                    "layout": {o.name: o["stall_variant"] for o in inst}}
    return inst


def build_fountain(col, st):
    m = bpy.data.objects["MARKER_Prop_FuenteMercado"]
    mw = m.matrix_world
    inv = mw.inverted()
    g = ground_fn()

    def gz(x, y):
        p = mw @ Vector((x, y, 0))
        return (inv @ Vector((p.x, p.y, g(p.x, p.y)))).z
    mouth = bpy.data.objects["CAU_SpringHead_Mouth"]
    mc = sum((mouth.matrix_world @ v.co for v in mouth.data.vertices), Vector()) / len(mouth.data.vertices)
    tl = inv @ Vector((mc.x, mc.y, 0))
    mb = K.MB()
    info = M.fountain(mb, gz, (tl.x, tl.y), bench_skip_deg=math.degrees(math.atan2(tl.y, tl.x)))
    mb.finish()
    me = bpy.data.meshes.new("FuenteMercado")
    mb.bm.to_mesh(me)
    mb.bm.free()
    for n in mb.mats:
        me.materials.append(bpy.data.materials[n])
    o = bpy.data.objects.new("FuenteMercado", me)
    col.objects.link(o)
    o.matrix_world = mw.copy()
    B.box_uv(o)
    lo = P13.lods(o, col, (("LOD1", 0.5),))
    c = P13.cylinder_col("FuenteMercado-colonly", 3.0, 0.0, 0.62, 16, col)
    c.matrix_world = mw.copy()
    st["FuenteMercado"] = {"tris": tris(o), "budget": BUDGET["FuenteMercado"], "ok": tris(o) <= BUDGET["FuenteMercado"],
                           "lods": lo, "basin_d_m": 6.0, "spouts": 4, "benches": len(info["benches_deg"]),
                           "benches_deg": info["benches_deg"], "overflow": info,
                           "spring_mouth_world": [round(c_, 2) for c_ in mc]}
    return o


def landmark_lod2_fix(st):
    """Pendiente D (etapa 17): LOD2 de color plano para Santuario, Salon y Faro (unico objeto <NOMBRE>_Body_LOD2)."""
    col = bpy.data.collections["BLD_PORTAL"]
    out = {}
    for root, parts, vox in (("SANTUARIO", ("SANTUARIO_Body", "SANTUARIO_Roof"), 0.3),
                             ("SALON_HAZANAS", ("SALON_HAZANAS_Body", "SALON_HAZANAS_Roof"), 0.35),
                             ("FARO", ("FARO_Body",), 0.3)):
        src = [bpy.data.objects[n] for n in parts]
        old = {n + "_LOD2": tris(bpy.data.objects.get(n + "_LOD2")) for n in parts}
        r = bpy.data.objects.get(f"{parts[1]}_LOD2") if len(parts) > 1 else None
        if r is not None:
            bpy.data.objects.remove(r)
        n0 = sum(tris(s) for s in src)
        if root == "FARO":                       # volumenes cerrados: la envolvente por voxeles funciona
            o, n, mat, note = LU.flat_lod2(f"{parts[0]}_LOD2", src, col, bpy.data.objects[root], int(0.15 * n0), voxel=vox)
        else:                                    # cubiertas de una cara: volumetria
            o, n, mat, note = LU.massing_lod2(root, f"{parts[0]}_LOD2", src, col, bpy.data.objects[root])
        out[root] = {"old_LOD2": old, "new_LOD2": [o.name, n], "material": mat, "note": note}
    st["lod2_fix_landmarks"] = out
    import stage11_godot as G
    import build_stage15 as B15
    for root, fname in (("SANTUARIO", "concordia_santuario.glb"), ("SALON_HAZANAS", "concordia_salon_hazanas.glb")):
        r = bpy.data.objects[root]
        G.export_glb([r] + list(r.children_recursive), os.path.join(REPO, "export", "godot", fname))
    B15.export_faro({})


def main():
    st = {}
    bpy.ops.wm.open_mainfile(filepath=SRC)
    save()
    st["saved_before"] = os.path.relpath(OUT, REPO)
    B.ensure_materials()
    st["materials"] = L.ensure_materials()
    col = bpy.data.collections["BLD_MERCADO"]
    pcol = bpy.data.collections["BLD_PROPS"]
    kit = bpy.data.collections["BLD_KIT"]
    for o in list(col.all_objects):
        bpy.data.objects.remove(o)
    landmark_lod2_fix(st)
    roots = []
    r, outs = build_tesoreria(col, pcol, st)
    roots.append(r)
    hook_pipe(outs, st)
    roots.append(build_banco(col, pcol, st))
    roots.append(build_subasta(col, pcol, st))
    r, tab = build_posada(col, pcol, st)
    roots.append(r)
    roots.append(build_registro(col, pcol, st))
    roots += build_casas(col, pcol, st)
    stalls = build_stalls(col, kit, st)
    fuente = build_fountain(col, st)
    for o in bpy.data.objects:
        if o.name.endswith(("_LOD1", "_LOD2")):
            o.hide_render = True
            o.hide_set(True)
    bpy.context.view_layer.update()
    # visibilidad de la cima del Faro con el Mercado construido
    import build_stage17 as B17
    with open(os.path.join(REPO, "docs", "reports", "stage15_faro.json")) as fh:
        tgt = Vector(json.load(fh)["visibility"]["target"])
    B17.faro_visibility(st, tgt)
    # export del distrito
    import stage11_godot as G
    objs = []
    for r in roots:
        objs += [r] + list(r.children_recursive)
    objs += [tab] + list(tab.children_recursive) + [bpy.data.objects["Posada_TablonGrupos-colonly"]]
    for s in stalls:
        objs += [s] + list(s.children)
    objs += [fuente, bpy.data.objects["FuenteMercado-colonly"], bpy.data.objects["FuenteMercado_LOD1"]]
    path = os.path.join(REPO, "export", "godot", "concordia_mercado.glb")
    size = G.export_glb(list(dict.fromkeys(objs)), path)
    st["export"] = {"file": os.path.relpath(path, REPO), "mb": round(size / 2 ** 20, 2), **G.glb_info(path)}
    for o in bpy.data.objects:
        if o.name.endswith(("_LOD1", "_LOD2")):
            o.hide_set(True)
    save()
    with open(REPORT, "w") as fh:
        json.dump(st, fh, indent=1, ensure_ascii=False, default=str)
    print("saved:", OUT)
    for k in ("TesoreriaMuralla", "Banco", "GranSubasta", "Posada", "CasaRegistro", "FuenteMercado", "stalls"):
        v = st[k]
        print(k, json.dumps({kk: v.get(kk) for kk in ("tris", "ok", "floors", "iso_rule", "iso_blocks", "footprint_check",
                                                        "footprint_ground_check", "variants")}, default=str)[:700])
    for k, v in st["casas"].items():
        print(k, v["floors"], v["style"], v["roof"], v["tris"]["total_body_roof"], v["budget_class"],
              (v["iso_rule"] or {}).get("history") if isinstance(v["iso_rule"], dict) else v["iso_rule"],
              v["footprint_check"]["over_x_m"], v["footprint_check"]["over_y_m"], v["footprint_ground_check"])
    print(json.dumps(st["pipe_hook"]))
    print(json.dumps({k: (v["axis_pct"], v.get("best_lane_pct")) for k, v in st["faro_visibility"].items()},
                     ensure_ascii=False))
    print(json.dumps(st["export"], default=str)[:400])
    print(json.dumps(st["lod2_fix_landmarks"], default=str)[:600])


if __name__ == "__main__":
    main()
