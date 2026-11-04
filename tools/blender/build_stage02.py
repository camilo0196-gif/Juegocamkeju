"""
CONCORDIA - Etapa 02 completa (orquestador). Genera concordia_v02.blend desde v01.

Pasos (en orden):
  terrain     stage02_terrain.py     malla MAESTRA TRN_City (1 m) + mascaras + QA de pendientes
  structures  stage02_structures.py  pretiles, contrafuertes, escaleras laterales, escalinatas
  shading     stage02_shading.py     MAT_Terrain_City, mascara de borde, AO horneada, mask_pack
  chunks      stage02_chunks.py      chunks de 50 m (LOD0/1/2), presupuesto, export .glb

Uso:
    python tools/blender/build_stage02.py                      # todo, desde v01
    python tools/blender/build_stage02.py --steps structures --in X.blend --out Y.blend
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
STEPS = ("terrain", "structures", "shading", "chunks")


def parse_args():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    p = argparse.ArgumentParser()
    p.add_argument("--in", dest="inp", default=os.path.join(REPO, "blender", f"{C.BLEND_BASENAME}_v01.blend"))
    p.add_argument("--out", default=os.path.join(REPO, "blender", f"{C.BLEND_BASENAME}_v02.blend"))
    p.add_argument("--report", default=os.path.join(REPO, "docs", "reports", "stage02_terrain.json"))
    p.add_argument("--export-dir", default=os.path.join(REPO, "export", "godot"))
    p.add_argument("--steps", default=",".join(STEPS))
    return p.parse_args(argv)


def main():
    args = parse_args()
    steps = [s for s in args.steps.split(",") if s]
    bpy.ops.wm.open_mainfile(filepath=args.inp)
    scene = bpy.context.scene
    stats = {}
    if os.path.exists(args.report) and "terrain" not in steps:
        with open(args.report) as fh:
            stats = json.load(fh)
    timings = stats.setdefault("timings_s", {})
    for step in steps:
        t0 = time.time()
        if step == "terrain":
            import stage02_terrain as m
            m.build(scene, stats)
        elif step == "structures":
            import stage02_structures as m
            m.build(scene, stats)
        elif step == "shading":
            import stage02_shading as m
            m.build(scene, stats)
        elif step == "chunks":
            import stage02_chunks as m
            m.build(scene, stats, args.export_dir)
        else:
            raise SystemExit(f"paso desconocido: {step}")
        timings[step] = round(time.time() - t0, 1)
        print(f"[{step}] {timings[step]} s")
    bpy.context.preferences.filepaths.save_version = 0
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=args.out, compress=True)
    os.makedirs(os.path.dirname(args.report), exist_ok=True)
    with open(args.report, "w") as fh:
        json.dump(stats, fh, indent=1, ensure_ascii=False)
    print("saved:", args.out)


if __name__ == "__main__":
    main()
