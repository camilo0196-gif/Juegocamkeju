"""
CONCORDIA - Etapa 27 (E14): kit de interiores, sala de prueba 8 x 6 y piloto del Banco.
-> blender/concordia_interiors_v01.blend (materiales copiados de concordia_v26.blend), export/godot/int_banco.glb,
   docs/reports/stage27_interiors.json

Comprobaciones: tamano del interior = Banco_InteriorVolume (+-0.2 m); triangulos <= 40,000; rayos desde CAM_Iso al
Banquero, al mostrador y a la puerta de la boveda (con WALL_Near_A/B y techos ocultos); malla de navegacion
conectada desde MARKER_Interior_Spawn; pasos de >= 1.2 m (rejilla de 0.1 m, holgura 0.6 m); escalera <= 35 grados.
"""

import json
import math
import os
import sys
from collections import deque

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import concordia_const as C  # noqa: E402
import interior_kit as IK  # noqa: E402
import stage27_banco as SB  # noqa: E402

REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
SRC = os.path.join(REPO, "blender", f"{C.BLEND_BASENAME}_v26.blend")
OUT = os.path.join(REPO, "blender", "concordia_interiors_v01.blend")
EXP = os.path.join(REPO, "export", "godot", "int_banco.glb")
REPORT = os.path.join(REPO, "docs", "reports", "stage27_interiors.json")
MATS = ["MAT_Limestone_Worn", "MAT_Limestone_Light", "MAT_Wall_Gray", "MAT_Stone_Repair", "MAT_Plaza_Slab",
        "MAT_Wood_Dark", "MAT_Wood_Light", "MAT_Iron_Black", "MAT_Bronze_Aged", "MAT_Window_Warm", "MAT_Shard_Blue",
        "MAT_Ash_Gray", "MAT_Cloth_Patch_A", "MAT_Cloth_Patch_B", "MAT_Cloth_Patch_C", "MAT_Hide_R05"]
HIDDEN_ISO = ("WALL_Near_A", "WALL_Near_B", "CEILING", "CEILING_Vault")


def collection(name):
    c = bpy.data.collections.get(name) or bpy.data.collections.new(name)
    if c.name not in bpy.context.scene.collection.children:
        bpy.context.scene.collection.children.link(c)
    return c


def source_data():
    """Materiales de Concordia y datos del Banco (volumen interior, giro, puerta) desde concordia_v26."""
    with bpy.data.libraries.load(SRC, link=False) as (df, dt):
        dt.materials = [m for m in df.materials if m in MATS]
        dt.objects = [o for o in df.objects if o in ("Banco", "Banco_InteriorVolume", "MARKER_Banco_Door")]
    info = {}
    b = bpy.data.objects["Banco"]
    iv = bpy.data.objects["Banco_InteriorVolume"]
    vs = [v.co for v in iv.data.vertices]
    info["iv_size"] = [round(max(v[i] for v in vs) - min(v[i] for v in vs), 3) for i in range(3)]
    info["rot_deg"] = round(math.degrees(b.rotation_euler.z), 3)          # matrix_world sin evaluar al anexar
    info["door_local"] = [round(c, 3) for c in bpy.data.objects["MARKER_Banco_Door"].location]
    for n in ("Banco", "Banco_InteriorVolume", "MARKER_Banco_Door"):
        o = bpy.data.objects[n]
        me = o.data if o.type == "MESH" else None
        bpy.data.objects.remove(o)
        if me is not None and me.users == 0:
            bpy.data.meshes.remove(me)
    return info


def tri_count(objs):
    return sum(IK.tris(o) for o in objs if o.type == "MESH" and not o.name.endswith(("-colonly", "-navmesh")))


def group_of(o, it):
    p = o
    while p is not None and p is not it.frame:
        if p.get("interior_group"):
            return p["interior_group"]
        p = p.parent
    return None


def ray_check(it):
    """Antes de unir los modulos (los nombres dicen si es arco, pilar o reja)."""
    bpy.context.view_layer.update()
    verts, faces, owner = [], [], []
    for o in it.all_objects():
        if o.type != "MESH" or o.name.endswith(("-colonly", "-navmesh")) or group_of(o, it) in HIDDEN_ISO:
            continue
        mw = o.matrix_world
        b = len(verts)
        verts += [mw @ v.co for v in o.data.vertices]
        for p in o.data.polygons:
            faces.append([b + i for i in p.vertices])
            owner.append(o.name)
    bvh = BVHTree.FromPolygons(verts, faces, epsilon=1e-6)
    d = IK.CAM_BACK
    fm = it.frame.matrix_world
    targets = {
        "Banquero": ([(SB.BANKER[0], SB.BANKER[1] + dy, z) for z in (0.6, 1.0, 1.4, 1.75) for dy in (-0.2, 0.0, 0.2)], ()),
        "Mostrador": ([(SB.COUNTER_X - 0.47, y, 0.6) for y in (-5.25, -3.25, -1.25, 0.75, 2.75)] +
                      [(SB.COUNTER_X, y, 1.13) for y in (-5.25, -3.25, -1.25, 0.75, 2.75)], ("Counter",)),
        "Puerta_Boveda": ([(SB.VAULT_X0 - 0.06, y, z) for y in (-5.0, -4.4, -3.8) for z in (0.5, 1.5, 2.5)], ("VAULT_Door",)),
    }
    out = {}
    for name, (pts, own) in targets.items():
        vis = 0
        blockers = {}
        for p in pts:
            o = fm @ Vector(p) + d * 0.03
            hit_by = None
            for _ in range(8):
                loc, _n, idx, _dd = bvh.ray_cast(o, d, 500.0)
                if loc is None:
                    break
                if any(k in owner[idx] for k in own):
                    o = loc + d * 0.02
                    continue
                hit_by = owner[idx]
                break
            if hit_by is None:
                vis += 1
            else:
                blockers[hit_by] = blockers.get(hit_by, 0) + 1
        cls = {k: ("columna/arco" if ("Arch" in k or "Pillar" in k) else "reja" if "Grille" in k else "otro")
               for k in blockers}
        out[name] = {"points": len(pts), "visible": vis, "pct": round(100.0 * vis / len(pts), 1), "blockers": blockers,
                     "blocked_by_column_or_arch": sum(v for k, v in blockers.items() if cls[k] == "columna/arco"),
                     "blocker_class": cls}
    return out


def nav_reach(it, nav, keys):
    """Conectividad de la malla de navegacion desde el spawn (caras con arista comun)."""
    import bmesh
    bm = bmesh.new()
    bm.from_mesh(nav.data)
    bm.faces.ensure_lookup_table()
    cent = [f.calc_center_median() for f in bm.faces]

    def nearest(p):
        best, bi = 1e9, None
        for i, c in enumerate(cent):
            dd = (Vector((c.x, c.y)) - Vector((p[0], p[1]))).length + abs(c.z - p[2]) * 2
            if dd < best:
                best, bi = dd, i
        return bi, best
    s, _ = nearest(keys["spawn"])
    seen = {s}
    q = deque([s])
    while q:
        f = bm.faces[q.popleft()]
        for e in f.edges:
            for g in e.link_faces:
                if g.index not in seen:
                    seen.add(g.index)
                    q.append(g.index)
    res = {}
    for k, p in keys.items():
        i, dist = nearest(p)
        res[k] = {"reachable": i in seen and dist < 1.0, "dist_to_nav_m": round(dist, 2)}
    out = {"faces": len(bm.faces), "reached_faces": len(seen), "keys": res}
    bm.free()
    return out


def clearance_check(it, keys, level=0, start=None, cell=0.1, half=0.6):
    """Paso libre de >= 1.2 m: rejilla de 0.1 m del nivel, celdas con obstaculo o muro; distancia (Chebyshev) al
    obstaculo mas cercano; BFS desde 'start' por celdas con holgura >= 0.6 m; ¿se llega a cada punto clave?"""
    W, D = it.W, it.D
    nx, ny = int(W / cell), int(D / cell)
    INF = 10 ** 9
    dist = [[INF] * ny for _ in range(nx)]
    q = deque()
    region = [r for r in it.nav_regions if r[0] == level]
    for i in range(nx):
        for j in range(ny):
            x, y = -W / 2 + (i + 0.5) * cell, -D / 2 + (j + 0.5) * cell
            inside = any(rx0 <= x <= rx1 and ry0 <= y <= ry1 for (_lv, _z, rx0, ry0, rx1, ry1) in region)
            blocked = not inside or any(lv == level and ax0 <= x <= ax1 and ay0 <= y <= ay1
                                        for (lv, ax0, ay0, ax1, ay1) in it.obstacles)
            if blocked:
                dist[i][j] = 0
                q.append((i, j))
    for i in range(nx):                      # bordes de la sala = muro
        for j in (0, ny - 1):
            if dist[i][j]:
                dist[i][j] = 1
                q.append((i, j))
    for j in range(ny):
        for i in (0, nx - 1):
            if dist[i][j]:
                dist[i][j] = 1
                q.append((i, j))
    while q:
        i, j = q.popleft()
        for di in (-1, 0, 1):
            for dj in (-1, 0, 1):
                a, b = i + di, j + dj
                if 0 <= a < nx and 0 <= b < ny and dist[a][b] > dist[i][j] + 1:
                    dist[a][b] = dist[i][j] + 1
                    q.append((a, b))
    need = int(round(half / cell))

    def idx(p):
        return min(nx - 1, max(0, int((p[0] + W / 2) / cell))), min(ny - 1, max(0, int((p[1] + D / 2) / cell)))
    s = idx(start)
    seen = {s}
    q = deque([s])
    while q:
        i, j = q.popleft()
        for di, dj in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            a, b = i + di, j + dj
            if 0 <= a < nx and 0 <= b < ny and (a, b) not in seen and dist[a][b] >= need:
                seen.add((a, b))
                q.append((a, b))
    res = {}
    for k, p in keys.items():
        i, j = idx(p)
        best = None
        for di in range(-4, 5):
            for dj in range(-4, 5):
                if (i + di, j + dj) in seen:
                    best = True
        res[k] = bool(best)
    return {"start_clearance_m": round(dist[s[0]][s[1]] * cell, 2), "reachable_with_1.2m": res}


def test_room(col):
    it = IK.build_interior("Sala_Prueba_8x6", (8.0, 6.0, 3.2), "entramado", seed=1, world_rot_deg=0.0, door=(0.0, 3.0),
                           col=col, openings=[("+Y", 4.0, "door", 0), ("-X", 3.0, "window", 0)])
    it.inst("INT_Fireplace", SB.M(-1.0, 3.0, 0, 180), "Furniture")
    it.inst("BANK_Bench", SB.M(-1.5, 0.0, 0, 0), "Furniture")
    it.inst("BANK_Desk", SB.M(1.8, -1.0, 0, 0), "Furniture")
    it.inst("BANK_Chair", SB.M(1.8, -1.7, 0, 0), "Furniture")
    it.inst("BANK_Candle", SB.M(2.2, -1.0, 0.79), "Furniture")
    it.inst("INT_Pillar", SB.M(0.0, -0.5, 0), "Shell")
    it.inst("INT_Beam_Cross", SB.M(-1.0, -0.5, 3.2), "CEILING")
    it.light("LIGHT_Hearth", (-2.0, 2.4, 0.6), "#FF9A48", 1.0, 6.0)
    it.light("LIGHT_Window", (-3.4, 0.0, 1.9), "#FFE6C4", 0.45, 5.0, kind="omni_window")
    it.light("LIGHT_Candle", (2.2, -1.0, 1.05), "#FFA650", 0.35, 2.8)
    it.entry_markers(180.0, 0.0)
    it.nav_regions.append((0, 0.0, -4.0, -3.0, 4.0, 3.0))
    it.obstacles += [(0, -3.0, 2.25, -1.0, 3.0), (0, -2.5, -0.25, -0.5, 0.25), (0, 1.0, -1.4, 2.6, -0.6),
                     (0, -0.4, -0.9, 0.4, -0.1)]
    for g in ("Shell", "WALL_Near_A", "WALL_Near_B", "CEILING"):
        it.realize(g)
    it.collider()
    it.navmesh()
    it.root.location = (-200.0, 0.0, 0.0)
    return it


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.wm.save_as_mainfile(filepath=OUT)
    st = {"source": os.path.relpath(SRC, REPO)}
    st["banco_source"] = source_data()
    kit = collection("BLD_INT_KIT")
    st["kit_tris"] = IK.build_kit(kit)
    st["kit_labels"] = IK.kit_sheet(kit)
    props = collection("BLD_INT_PROPS")
    import random
    st["props_tris"] = SB.build_props(props, random.Random(2701))
    # --- piloto: Banco
    bcol = collection("INT_BANCO")
    it, info = SB.build(bcol, st["banco_source"]["rot_deg"], REPO)
    st["banco"] = info
    st["banco"]["near_walls"] = it.log.get("near_walls")
    st["banco"]["cam_local"] = it.log.get("cam_local")
    st["banco"]["rays_before_merge"] = ray_check(it)
    for g in ("Shell", "WALL_Near_A", "WALL_Near_B", "CEILING", "CEILING_Vault", "WALL_Near_Vault", "LEVEL_1"):
        if g in it.groups:
            it.realize(g)
    it.collider()
    nav = it.navmesh(cell=0.25)               # 0.5 m no cabe en la puerta del personal (1.235 m - 2 x 0.3)
    st["banco"]["rays_after_merge"] = ray_check(it)
    keys = {"spawn": (SB.DOOR[0], SB.DOOR[1] - 1.6, 0.0), "mostrador_publico": (SB.COUNTER_X - 1.0, SB.BANKER[1], 0.0),
            "zona_banquero": (6.4, SB.BANKER[1], 0.0), "boveda": (9.7, -5.0, 0.0), "archivo": (-7.2, -7.0, 0.0),
            "espera": (-1.2, 2.2, 0.0), "cuarto_personal": (9.5, 2.0, 0.0), "galeria": (0.0, 6.5, 3.2),
            "despacho": (8.5, 6.2, 3.2)}
    st["banco"]["navmesh"] = nav_reach(it, nav, keys)
    k0 = {k: v for k, v in keys.items() if v[2] == 0.0}
    k1 = {k: v for k, v in keys.items() if v[2] > 0.0}
    st["banco"]["corridors_1.2m"] = {"planta_baja": clearance_check(it, k0, 0, keys["spawn"]),
                                     "planta_alta": clearance_check(it, k1, 1, (-10.4, 5.4, 3.2))}
    objs = it.all_objects()
    t = tri_count(objs)
    st["banco"]["tris"] = {"total": t, "budget": 40000, "ok": t <= 40000,
                           "by_group": {g: tri_count([o for o in objs if group_of(o, it) == g]) for g in it.groups}}
    iv = st["banco"]["iv_size"] = st["banco_source"]["iv_size"]
    st["banco"]["size_check"] = {"interior_m": [it.W, it.D, it.H], "interior_volume_m": iv,
                                 "diff_m": [round(abs(a - b), 3) for a, b in zip((it.W, it.D, it.H), iv)],
                                 "ok": all(abs(a - b) <= 0.2 for a, b in zip((it.W, it.D, it.H), iv))}
    st["banco"]["groups"] = {g: len(list(e.children_recursive)) for g, e in it.groups.items()}
    # --- sala de prueba 8 x 6
    tcol = collection("INT_TEST")
    tr = test_room(tcol)
    st["test_room"] = {"near_walls": tr.log.get("near_walls"), "tris": tri_count(tr.all_objects())}
    # --- exportacion
    import stage11_godot as G
    bpy.context.view_layer.update()
    size = G.export_glb(objs, EXP)
    st["banco"]["export"] = {"file": os.path.relpath(EXP, REPO), "mb": round(size / 2 ** 20, 2), **G.glb_info(EXP)}
    bpy.ops.file.make_paths_relative()
    bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
    with open(REPORT, "w") as fh:
        json.dump(st, fh, indent=1, ensure_ascii=False, default=str)
    print("RESULT", json.dumps({k: st["banco"][k] for k in ("tris", "size_check", "rays_after_merge", "navmesh",
                                                            "corridors_1.2m", "stair", "boxes", "export")},
                               default=str)[:4000], flush=True)


if __name__ == "__main__":
    main()
