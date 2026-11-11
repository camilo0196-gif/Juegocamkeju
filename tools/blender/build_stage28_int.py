"""
CONCORDIA - Etapa 28: vitrina de trofeos (3 variantes, LOD1/LOD2) e interiores tipo de las Moradas.
-> blender/concordia_moradas_int_v01.blend, export/godot/int_morada_<plantilla>.glb, export/godot/props_trophy_cases.glb,
   docs/reports/stage28_moradas_int.json

Kit y materiales como en la etapa 27; mobiliario: props a mano (etapas 27-28) y props CC0 importados del lote Mercado
(concordia_props_v01.blend; el usuario permitio props descargados en el mobiliario de Moradas). Comprobaciones por
plantilla: triangulos <= presupuesto, malla de navegacion (celda 0.25 m) conectada desde el spawn, pasos >= 1.2 m,
escalera <= 35 grados, rayos desde CAM_Iso a la vitrina, el baul y las mesas de oficio (muros cercanos y techo ocultos).
"""

import json
import math
import os
import random
import sys

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import interior_kit as IK  # noqa: E402
import stage27_banco as SB  # noqa: E402
import stage28_moradas_int as MI  # noqa: E402
import build_stage27 as B27  # noqa: E402

REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
OUT = os.path.join(REPO, "blender", "concordia_moradas_int_v01.blend")
PROPS_BLEND = os.path.join(REPO, "blender", "concordia_props_v01.blend")
REPORT = os.path.join(REPO, "docs", "reports", "stage28_moradas_int.json")
EXP = os.path.join(REPO, "export", "godot")
IMPORTED = ["PROP_AV_Table", "PROP_Q_Chair_1", "PROP_Q_Stool", "PROP_Q_Chest_Wood", "PROP_Q_Candle_1",
            "PROP_Q_CandleStick", "PROP_Q_Mug", "PROP_AV_Grain_Sack", "PROP_Herb_Rack"]
EXTRA_MATS = ["MAT_Glass_R04", "MAT_Hide_R05", "MAT_Felt_R05", "MAT_Straw", "MAT_Herb_Green", "MAT_Leaf_Old",
              "MAT_Roof_Tile_Ocher"]
HIDE_ISO = ("WALL_Near_A", "WALL_Near_B", "CEILING", "WALL_Near_Casa", "LEVEL_1", "Furniture_L1")


def collection(name):
    c = bpy.data.collections.get(name) or bpy.data.collections.new(name)
    if c.name not in bpy.context.scene.collection.children:
        bpy.context.scene.collection.children.link(c)
    return c


def source():
    with bpy.data.libraries.load(B27.SRC, link=False) as (df, dt):
        dt.materials = [m for m in df.materials if m in B27.MATS + EXTRA_MATS]
    with bpy.data.libraries.load(PROPS_BLEND, link=False) as (df, dt):
        dt.meshes = [m for m in df.meshes if m in IMPORTED]
    miss = [m for m in IMPORTED if bpy.data.meshes.get(m) is None]
    if miss:
        raise RuntimeError(f"faltan props importados: {miss}")
    return {m: sum(len(p.vertices) - 2 for p in bpy.data.meshes[m].polygons) for m in IMPORTED}


def group_of(o, it):
    p = o
    while p is not None and p is not it.frame:
        if p.get("interior_group"):
            return p["interior_group"]
        p = p.parent
    return None


def ray_vis(it, targets, hide=HIDE_ISO):
    """targets: {nombre: [(x, y, z) en el marco centrado]} -> % de puntos con la visual libre hacia CAM_Iso."""
    bpy.context.view_layer.update()
    verts, faces, owner = [], [], []
    for o in it.all_objects():
        if o.type != "MESH" or o.name.endswith(("-colonly", "-navmesh")) or group_of(o, it) in hide:
            continue
        mw = o.matrix_world
        b = len(verts)
        verts += [mw @ v.co for v in o.data.vertices]
        for p in o.data.polygons:
            faces.append([b + i for i in p.vertices])
            owner.append(o.name)
    bvh = BVHTree.FromPolygons(verts, faces, epsilon=1e-6)
    fm = it.frame.matrix_world
    out = {}
    for name, (pts, own) in targets.items():
        vis, by = 0, {}
        for p in pts:
            o = fm @ Vector(p) + IK.CAM_BACK * 0.03
            hit = None
            for _ in range(8):
                loc, _n, idx, _d = bvh.ray_cast(o, IK.CAM_BACK, 300.0)
                if loc is None:
                    break
                if any(k in owner[idx] for k in own):
                    o = loc + IK.CAM_BACK * 0.02
                    continue
                hit = owner[idx]
                break
            if hit is None:
                vis += 1
            else:
                by[hit] = by.get(hit, 0) + 1
        out[name] = {"points": len(pts), "pct": round(100.0 * vis / len(pts), 1), "blockers": by}
    return out


def pts_box(c, half, zs):
    x, y = c
    hx, hy = half
    return [(x + dx, y + dy, z) for z in zs for dx, dy in ((-hx, hy), (0, hy), (hx, hy))]


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.wm.save_as_mainfile(filepath=OUT)
    st = {"source": os.path.relpath(B27.SRC, REPO), "props_blend": os.path.relpath(PROPS_BLEND, REPO)}
    st["imported_props_tris"] = source()
    kit = collection("BLD_INT_KIT")
    st["kit_tris"] = IK.build_kit(kit)
    for o in kit.objects:
        o.location.z -= 50.0
        o.hide_render = True
    props = collection("BLD_INT_PROPS")
    SB.build_props(props, random.Random(2701))
    st["house_props_tris"] = MI.build_house_props(props, random.Random(2804))
    tcol = collection("BLD_TROPHY_CASES")
    st["trophy_cases"] = MI.build_trophy_cases(tcol, REPO)
    st["templates"] = {}
    import stage11_godot as G
    for k, (name, (fn, budget)) in enumerate(MI.TEMPLATES.items()):
        col = collection(f"INT_MORADA_{name.upper()}")
        it, keys, info = fn(col, random.Random(2810 + k))
        rep = {"size_m": [it.W, it.D, it.H], "budget": budget, **info, "near_walls": it.log.get("near_walls")}
        # visibilidad desde CAM_Iso antes de unir
        tg = {}
        for e in it.groups["Markers"].children:
            if e.name.startswith(("MARKER_TrophyCase", "MARKER_Interact_Chest", "MARKER_WorkStation")):
                p = e.location
                if p.z > 1.0:
                    continue                                   # la planta alta tiene su propio corte
                off = Vector((math.cos(e.rotation_euler.z + math.pi / 2), math.sin(e.rotation_euler.z + math.pi / 2)))
                c = (p.x, p.y) if e.name.startswith("MARKER_TrophyCase") else (p.x - off.x * 0.6, p.y - off.y * 0.6)
                tg[e.name] = (pts_box(c, (0.25, 0.1), (p.z + 0.5, p.z + 0.9, p.z + 1.3)),
                              ("TROPHY", "Chest", "Workbench"))
        rep["rays_cam_iso"] = ray_vis(it, tg)
        for g in list(it.groups):
            if g in ("Shell", "WALL_Near_A", "WALL_Near_B", "CEILING", "WALL_Near_Casa", "LEVEL_1"):
                it.realize(g)
        it.collider()
        nav = it.navmesh(cell=0.25)
        rep["navmesh"] = B27.nav_reach(it, nav, keys)
        k0 = {kk: v for kk, v in keys.items() if v[2] < 0.5}
        k1 = {kk: v for kk, v in keys.items() if v[2] >= 0.5}
        rep["corridors_1.2m"] = {"planta_baja": B27.clearance_check(it, k0, 0, keys["spawn"])}
        if k1:
            rep["corridors_1.2m"]["planta_alta"] = B27.clearance_check(it, k1, 1, (-3.3, -1.8, IK.FH))
            rep["stair_deg"] = round(math.degrees(math.atan2(IK.FH, 5.0)), 1)
        objs = it.all_objects()
        t = B27.tri_count(objs)
        rep["tris"] = {"total": t, "budget": budget, "ok": t <= budget,
                       "by_group": {g: B27.tri_count([o for o in objs if group_of(o, it) == g]) for g in it.groups}}
        rep["markers"] = sorted(e.name for e in it.groups["Markers"].children)
        rep["trophy_slots"] = sorted(c.name for o in objs if o.get("trophy_case") for c in o.children)
        rep["lights"] = {e.name: [e["light_color"], e["light_energy"]] for e in it.groups["Lights"].children}
        rep["blue_lights"] = sum(1 for e in it.groups["Lights"].children if e["light_color"].upper() == "#8FD0FF")
        it.root.location = (-300.0 - 30.0 * k, 0.0, 0.0)
        path = os.path.join(EXP, f"int_morada_{name}.glb")
        size = G.export_glb(objs, path)
        rep["export"] = {"file": os.path.relpath(path, REPO), "mb": round(size / 2 ** 20, 3), **G.glb_info(path)}
        st["templates"][name] = rep
        # nombres limpios ya exportados: en el .blend se les anade el sufijo de la plantilla para dejar libres los
        # nombres de la siguiente (Blender exige nombres unicos en todo el archivo)
        for o in objs:
            if not o.name.startswith("INT_"):
                o.name = f"{o.name}__{name}"
        print("TPL", name, t, budget, rep["navmesh"]["keys"], rep["rays_cam_iso"], flush=True)
    tc = [o for o in tcol.objects]
    for o in tc:
        o.hide_viewport = False
    path = os.path.join(EXP, "props_trophy_cases.glb")
    size = G.export_glb(tc, path)
    st["trophy_export"] = {"file": os.path.relpath(path, REPO), "mb": round(size / 2 ** 20, 3), **G.glb_info(path)}
    for o in tc:
        if o.name.endswith(("_LOD1", "_LOD2")):
            o.hide_viewport = True
    bpy.ops.file.make_paths_relative()
    bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
    with open(REPORT, "w") as fh:
        json.dump(st, fh, indent=1, ensure_ascii=False, default=str)
    print("DONE", json.dumps(st["trophy_cases"]), flush=True)


if __name__ == "__main__":
    main()
