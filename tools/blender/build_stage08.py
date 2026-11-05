"""
CONCORDIA - Etapa 08 (terreno exterior de ceniza, r 212-400). v07 -> v08.

Uso:
    python tools/blender/build_stage08.py [--in v07.blend] [--out v08.blend] [--no-export]
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


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    p = argparse.ArgumentParser()
    p.add_argument("--in", dest="inp", default=os.path.join(REPO, "blender", f"{C.BLEND_BASENAME}_v07.blend"))
    p.add_argument("--out", default=os.path.join(REPO, "blender", f"{C.BLEND_BASENAME}_v08.blend"))
    p.add_argument("--report", default=os.path.join(REPO, "docs", "reports", "stage08_exterior.json"))
    p.add_argument("--export-dir", default=os.path.join(REPO, "export", "godot"))
    p.add_argument("--no-export", action="store_true")
    a = p.parse_args(argv)
    bpy.ops.wm.open_mainfile(filepath=a.inp)
    import stage08_exterior as X
    stats = {}
    t0 = time.time()
    X.build(bpy.context.scene, stats, None if a.no_export else a.export_dir)
    stats["time_s"] = round(time.time() - t0, 1)
    print("[exterior]", stats["time_s"], "s", flush=True)
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.wm.save_as_mainfile(filepath=a.out, compress=True)
    with open(a.report, "w") as fh:
        json.dump(stats, fh, indent=1, ensure_ascii=False, default=str)
    print("saved:", a.out)


if __name__ == "__main__":
    main()
