"""
CONCORDIA - Etapa 11: preparacion para Godot 4. concordia_v10.blend -> concordia_master_v11.blend + export/godot/*.glb

Salidas:
  export/godot/concordia_terrain_<distrito>.glb   plaza, mercado, oficios, clases, razas, moradas, exterior
  export/godot/concordia_wall_kit.glb             piezas LOD0/1/2 + -colonly + -occonly + puertas de torre
  export/godot/concordia_wall_layout.glb          instancias del kit (comodidad; la colocacion tambien sale de WallSlot)
  export/godot/concordia_markers.glb              todos los Empties MARKER_* con sus propiedades (extras)
  docs/reports/stage11_godot.json, docs/reports/stage11_markers.csv
Uso: python tools/blender/build_stage11.py
"""

import json
import os
import sys
import time

import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import concordia_const as C  # noqa: E402
import stage11_godot as G  # noqa: E402

REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
EXP = os.path.join(REPO, "export", "godot")
SUPERSEDED = ("concordia_terrain.glb", "concordia_terrain_structures.glb", "concordia_plaza.glb",
              "concordia_districts_markers.glb", "concordia_moradas_markers.glb", "concordia_cauce.glb",
              "concordia_exterior.glb", "concordia_wall_kit_lods.glb")


REPORT = os.path.join(REPO, "docs", "reports", "stage11_godot.json")
MASTER = os.path.join(REPO, "blender", f"{C.BLEND_BASENAME}_master_v11.blend")


def build():
    stats = {"timings_s": {}}
    src = os.path.join(REPO, "blender", f"{C.BLEND_BASENAME}_v10.blend")
    bpy.ops.wm.open_mainfile(filepath=src)
    t = time.time()
    G.cleanup(stats)
    stats["timings_s"]["cleanup"] = round(time.time() - t, 1)
    t = time.time()
    lod0, dmap, ccols = G.city_chunks(stats)
    G.exterior_chunks(stats, dmap)
    stats["timings_s"]["chunks_lods"] = round(time.time() - t, 1)
    t = time.time()
    G.structures(stats, dmap)
    G.nav_mesh(stats, dmap)
    G.wall_occluders(stats)
    stats["timings_s"]["collision_nav_occ"] = round(time.time() - t, 1)
    G.markers(stats, os.path.join(REPO, "docs", "reports", "stage11_markers.csv"))
    for cn in [c.name for c in bpy.data.collections if c.name.startswith("GODOT_")]:
        bpy.data.collections[cn].hide_render = True
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.wm.save_as_mainfile(filepath=MASTER, compress=True)
    stats["master_blend"] = os.path.relpath(MASTER, REPO)
    with open(REPORT, "w") as fh:
        json.dump(stats, fh, indent=1, ensure_ascii=False, default=str)
    print("saved:", MASTER, flush=True)


def col_objs(prefix):
    return [o for c in bpy.data.collections if c.name.startswith(prefix) for o in c.objects]


def export():
    bpy.ops.wm.open_mainfile(filepath=MASTER)
    with open(REPORT) as fh:
        stats = json.load(fh)
    t = time.time()
    city = col_objs("GODOT_CITY_")
    sobjs = [o for cn in G.STRUCT_COLS for o in bpy.data.collections[cn].objects
             if o.type == "MESH" and not o.name.endswith("-colonly")]
    scol = col_objs("GODOT_STRUCT_COL")
    nav = col_objs("GODOT_NAVMESH")
    files = {}
    for d in G.DISTRICTS:
        files[f"concordia_terrain_{d}.glb"] = [o for o in city + sobjs + scol + nav if o.get("district") == d]
    ext = col_objs("GODOT_EXT_") + [o for o in bpy.data.collections["EXTERIOR"].objects if o.name.startswith("EXT_Rock_")]
    files["concordia_terrain_exterior.glb"] = ext
    kit = [o for o in bpy.data.collections["WALL_KIT"].all_objects if o.type in ("MESH", "EMPTY")]
    kit += [o for o in bpy.data.collections["WALL_KIT_LODS"].all_objects if o.type == "MESH"]
    files["concordia_wall_kit.glb"] = list(dict.fromkeys(kit))
    files["concordia_wall_layout.glb"] = [o for o in bpy.data.collections["WALL_LAYOUT"].objects if o.type == "MESH"]
    files["concordia_markers.glb"] = [o for o in bpy.data.objects if o.type == "EMPTY" and o.name.startswith("MARKER_")]
    for f in SUPERSEDED:
        p = os.path.join(EXP, f)
        if os.path.exists(p):
            os.remove(p)
    rep = {}
    for fname, objs in files.items():
        p = os.path.join(EXP, fname)
        size = G.export_glb(objs, p)
        rep[fname] = {"bytes": size, "mb": round(size / 2 ** 20, 2), "objects": len(objs), **G.glb_info(p)}
        print("export", fname, rep[fname], flush=True)
    stats["files"] = rep
    stats["tris_total_all_files"] = sum(r["tris"] for r in rep.values())
    stats["superseded_removed"] = list(SUPERSEDED)
    stats["timings_s"]["export"] = round(time.time() - t, 1)
    stats["master_blend_mb"] = round(os.path.getsize(MASTER) / 2 ** 20, 1)
    with open(REPORT, "w") as fh:
        json.dump(stats, fh, indent=1, ensure_ascii=False, default=str)
    print("exported", flush=True)


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    if "--export-only" not in argv:
        build()
    export()


if __name__ == "__main__":
    main()
