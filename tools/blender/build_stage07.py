"""
CONCORDIA - Etapa 07 (Cauce, puentes, arcos entre barrios, escalinatas). v06 -> v07.

Pasos: stage07_cauce (canal, puentes, arcos, escalinatas, remiendos, marcadores) -> AO + mask_pack +
material -> chunks + export (concordia_cauce.glb).

Uso:
    python tools/blender/build_stage07.py [--in v06.blend] [--out v07.blend] [--no-export]
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
    p.add_argument("--in", dest="inp", default=os.path.join(REPO, "blender", f"{C.BLEND_BASENAME}_v06.blend"))
    p.add_argument("--out", default=os.path.join(REPO, "blender", f"{C.BLEND_BASENAME}_v07.blend"))
    p.add_argument("--report", default=os.path.join(REPO, "docs", "reports", "stage07_cauce.json"))
    p.add_argument("--export-dir", default=os.path.join(REPO, "export", "godot"))
    p.add_argument("--no-export", action="store_true")
    return p.parse_args(argv)


def main():
    args = parse_args()
    bpy.ops.wm.open_mainfile(filepath=args.inp)
    scene = bpy.context.scene
    stats = {"timings_s": {}}
    import stage07_cauce as M
    import stage05_streets as S5
    import stage02_shading as SH
    import stage02_chunks as CH
    t0 = time.time()
    M.build(scene, stats)
    stats["timings_s"]["cauce"] = round(time.time() - t0, 1)
    print("[cauce]", stats["timings_s"]["cauce"], "s", flush=True)
    t0 = time.time()
    SH.terrain_material = S5.street_material(SH.terrain_material)
    SH.build(scene, stats)
    stats["timings_s"]["shading"] = round(time.time() - t0, 1)
    print("[shading]", stats["timings_s"]["shading"], "s", flush=True)
    if not args.no_export:
        t0 = time.time()
        CH.build(scene, stats, args.export_dir, {"concordia_plaza.glb": ["PLAZA"],
                                                 "concordia_districts_markers.glb": ["MARKERS_DISTRICTS"],
                                                 "concordia_moradas_markers.glb": [f"MARKERS_Morada_{k}" for k in
                                                                                   ("NE", "NO", "SO", "SE")],
                                                 "concordia_cauce.glb": ["CAUCE"]})
        stats["timings_s"]["chunks"] = round(time.time() - t0, 1)
        print("[chunks]", stats["timings_s"]["chunks"], "s", flush=True)
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.wm.save_as_mainfile(filepath=args.out, compress=True)
    with open(args.report, "w") as fh:
        json.dump(stats, fh, indent=1, ensure_ascii=False, default=str)
    print("saved:", args.out)


if __name__ == "__main__":
    main()
