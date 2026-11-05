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


def main():
    stats = {"timings_s": {}}
    src = os.path.join(REPO, "blender", f"{C.BLEND_BASENAME}_v10.blend")
    out = os.path.join(REPO, "blender", f"{C.BLEND_BASENAME}_master_v11.blend")
    bpy.ops.wm.open_mainfile(filepath=src)
    t = time.time()
    G.cleanup(stats)
    stats["timings_s"]["cleanup"] = round(time.time() - t, 1)
    t = time.time()
    lod0, dmap, ccols = G.city_chunks(stats)
    ecols, rocks = G.exterior_chunks(stats, dmap)
    stats["timings_s"]["chunks_lods"] = round(time.time() - t, 1)
    t = time.time()
    sobjs, scol = G.structures(stats, dmap)
    navcol = G.nav_mesh(stats, dmap)
    occ = G.wall_occluders(stats)
    stats["timings_s"]["collision_nav_occ"] = round(time.time() - t, 1)
    empties, rows = G.markers(stats, os.path.join(REPO, "docs", "reports", "stage11_markers.csv"))
    # --- export
    t = time.time()
    files = {}
    city_objs = [o for c in ccols.values() for o in c.objects]
    for d in G.DISTRICTS:
        objs = [o for o in city_objs if o.get("district") == d]
        objs += [o for o in sobjs if o.get("district") == d]
        objs += [o for o in scol.objects if o.get("district") == d]
        objs += [o for o in navcol.objects if o.get("district") == d]
        files[f"concordia_terrain_{d}.glb"] = objs
    ext = [o for c in ecols.values() for o in c.objects]
    ext += [o for lst in rocks.values() for o in lst]
    files["concordia_terrain_exterior.glb"] = ext
    kit = [o for o in bpy.data.collections["WALL_KIT"].all_objects if o.type in ("MESH", "EMPTY")]
    kit += [o for o in bpy.data.collections["WALL_KIT_LODS"].all_objects if o.type == "MESH"]
    files["concordia_wall_kit.glb"] = list(dict.fromkeys(kit))
    files["concordia_wall_layout.glb"] = [o for o in bpy.data.collections["WALL_LAYOUT"].objects if o.type == "MESH"]
    files["concordia_markers.glb"] = empties
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
    for c in list(ccols.values()) + list(ecols.values()) + [scol, navcol, occ]:
        c.hide_render = True
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.wm.save_as_mainfile(filepath=out, compress=True)
    stats["master_blend"] = os.path.relpath(out, REPO)
    stats["master_blend_mb"] = round(os.path.getsize(out) / 2 ** 20, 1)
    with open(os.path.join(REPO, "docs", "reports", "stage11_godot.json"), "w") as fh:
        json.dump(stats, fh, indent=1, ensure_ascii=False, default=str)
    print("saved:", out)


if __name__ == "__main__":
    main()
