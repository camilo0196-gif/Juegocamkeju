"""
CONCORDIA - Etapa 03 (Plaza del Portal). Genera concordia_v03.blend desde v02.

Pasos: plaza (terreno + piezas + marcadores) -> shading (AO y mascaras de nuevo) ->
chunks + export (.glb del terreno, estructuras y plaza) -> comprobaciones.

Uso:
    python tools/blender/build_stage03.py [--in v02.blend] [--out v03.blend]
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
    p.add_argument("--in", dest="inp", default=os.path.join(REPO, "blender", f"{C.BLEND_BASENAME}_v02.blend"))
    p.add_argument("--out", default=os.path.join(REPO, "blender", f"{C.BLEND_BASENAME}_v03.blend"))
    p.add_argument("--report", default=os.path.join(REPO, "docs", "reports", "stage03_plaza.json"))
    p.add_argument("--export-dir", default=os.path.join(REPO, "export", "godot"))
    return p.parse_args(argv)


def main():
    args = parse_args()
    bpy.ops.wm.open_mainfile(filepath=args.inp)
    scene = bpy.context.scene
    stats = {"timings_s": {}}
    import stage03_plaza
    import stage02_shading
    import stage02_chunks
    import stage03_analysis
    steps = [("plaza", lambda: stage03_plaza.build(scene, stats)),
             ("shading", lambda: stage02_shading.build(scene, stats)),
             ("chunks", lambda: stage02_chunks.build(scene, stats, args.export_dir,
                                                     {"concordia_plaza.glb": ["PLAZA"]})),
             ("checks", lambda: stage03_analysis.build(scene, stats))]
    for name, fn in steps:
        t0 = time.time()
        fn()
        stats["timings_s"][name] = round(time.time() - t0, 1)
        print(f"[{name}] {stats['timings_s'][name]} s")
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.wm.save_as_mainfile(filepath=args.out, compress=True)
    os.makedirs(os.path.dirname(args.report), exist_ok=True)
    with open(args.report, "w") as fh:
        json.dump(stats, fh, indent=1, ensure_ascii=False)
    print("saved:", args.out)


if __name__ == "__main__":
    main()
