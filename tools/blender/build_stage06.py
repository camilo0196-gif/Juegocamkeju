"""
CONCORDIA - Etapa 06 (Moradas: parcelas, calles de servicio, escaleras, mascaras). v05 -> v06.

Pasos: raster de obstaculos -> stage06_moradas (trazado, terreno, mascaras, escaleras, pretiles, oclusion,
marcadores) -> AO + mask_pack + material -> chunks + export.

Uso:
    python tools/blender/build_stage06.py [--in v05.blend] [--out v06.blend] [--no-export]
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
    p.add_argument("--in", dest="inp", default=os.path.join(REPO, "blender", f"{C.BLEND_BASENAME}_v05.blend"))
    p.add_argument("--out", default=os.path.join(REPO, "blender", f"{C.BLEND_BASENAME}_v06.blend"))
    p.add_argument("--report", default=os.path.join(REPO, "docs", "reports", "stage06_moradas.json"))
    p.add_argument("--layout", default=os.path.join(REPO, "docs", "reports", "stage06_layout.json"))
    p.add_argument("--export-dir", default=os.path.join(REPO, "export", "godot"))
    p.add_argument("--no-export", action="store_true")
    return p.parse_args(argv)


def main():
    args = parse_args()
    bpy.ops.wm.open_mainfile(filepath=args.inp)
    scene = bpy.context.scene
    stats = {"timings_s": {}}
    import stage05_obstacles as OB
    import stage06_moradas as M
    import stage05_streets as S5
    import stage02_shading as SH
    import stage02_chunks as CH
    t0 = time.time()
    codes, info = OB.build_raster()
    stats["obstacles"] = info
    lays, setback = M.build(scene, stats, codes)
    stats["timings_s"]["moradas"] = round(time.time() - t0, 1)
    print("[moradas]", stats["timings_s"]["moradas"], "s", flush=True)
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
                                                                                   ("NE", "NO", "SO", "SE")]})
        stats["timings_s"]["chunks"] = round(time.time() - t0, 1)
        print("[chunks]", stats["timings_s"]["chunks"], "s", flush=True)
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.wm.save_as_mainfile(filepath=args.out, compress=True)
    with open(args.report, "w") as fh:
        json.dump(stats, fh, indent=1, ensure_ascii=False, default=str)
    slim = [{k: v for k, v in l.items()} for l in lays]
    with open(args.layout, "w") as fh:
        json.dump({"setback": setback, "moradas": slim}, fh, ensure_ascii=False, default=str)
    print("saved:", args.out)


if __name__ == "__main__":
    main()
