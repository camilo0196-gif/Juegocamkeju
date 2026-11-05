"""
CONCORDIA - Etapa 05 (red de calles y parcelas de los 4 distritos cardinales). v04 -> v05.

Pasos: raster de obstaculos (escena) -> plan (stage05_layout, seed 11) -> cortes, alturas, mascaras y
marcadores (stage05_streets) -> AO + mask_pack + material (stage02_shading, con empedrado) -> chunks + export.

Uso:
    python tools/blender/build_stage05.py [--in v04.blend] [--out v05.blend]
"""

import argparse
import json
import os
import sys
import time

import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import concordia_const as C  # noqa: E402

REPO = os.path.abspath(os.path.join(HERE, "..", ".."))


def parse_args():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    p = argparse.ArgumentParser()
    p.add_argument("--in", dest="inp", default=os.path.join(REPO, "blender", f"{C.BLEND_BASENAME}_v04.blend"))
    p.add_argument("--out", default=os.path.join(REPO, "blender", f"{C.BLEND_BASENAME}_v05.blend"))
    p.add_argument("--report", default=os.path.join(REPO, "docs", "reports", "stage05_streets.json"))
    p.add_argument("--layout", default=os.path.join(REPO, "docs", "reports", "stage05_layout.json"))
    p.add_argument("--export-dir", default=os.path.join(REPO, "export", "godot"))
    p.add_argument("--no-export", action="store_true")
    return p.parse_args(argv)


def main():
    args = parse_args()
    bpy.ops.wm.open_mainfile(filepath=args.inp)
    scene = bpy.context.scene
    stats = {"timings_s": {}}
    import stage05_obstacles as OB
    import stage05_streets as ST
    import stage02_shading as SH
    import stage02_chunks as CH
    t0 = time.time()
    codes, info = OB.build_raster()
    stats["obstacles"] = info
    with open(os.path.join(REPO, "docs", "reports", "stage02_terrain.json")) as fh:
        stairs = json.load(fh)["structures"]["stairs"]
    stats["timings_s"]["obstacles"] = round(time.time() - t0, 1)
    t0 = time.time()
    lay, rep, P, surf = ST.build(scene, stats, codes, stairs)
    stats["timings_s"]["streets"] = round(time.time() - t0, 1)
    print("[streets]", stats["timings_s"]["streets"], "s")
    t0 = time.time()
    SH.terrain_material = ST.street_material(SH.terrain_material)
    SH.build(scene, stats)
    stats["timings_s"]["shading"] = round(time.time() - t0, 1)
    print("[shading]", stats["timings_s"]["shading"], "s")
    if not args.no_export:
        t0 = time.time()
        CH.build(scene, stats, args.export_dir, {"concordia_plaza.glb": ["PLAZA"],
                                                 "concordia_districts_markers.glb": ["MARKERS_DISTRICTS"]})
        stats["timings_s"]["chunks"] = round(time.time() - t0, 1)
        print("[chunks]", stats["timings_s"]["chunks"], "s")
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.wm.save_as_mainfile(filepath=args.out, compress=True)
    os.makedirs(os.path.dirname(args.report), exist_ok=True)
    with open(args.report, "w") as fh:
        json.dump(stats, fh, indent=1, ensure_ascii=False, default=str)
    with open(args.layout, "w") as fh:
        json.dump(lay, fh, ensure_ascii=False, default=str)
    print("saved:", args.out)


if __name__ == "__main__":
    main()
