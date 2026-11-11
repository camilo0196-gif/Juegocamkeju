"""
CONCORDIA - capturas del PJ5 (LODs) sobre blender/concordia_personajes_master.blend (no se guarda).
Por LOD (0, 1, 2): de frente (cuerpo entero), isometrica (35,26 grados, como el juego) y dos de cerca para la
silueta: orejas (cabeza de frente) y dobladillo (falda de lado). Hoja: docs/captures/pj5_lods.png
python capture_pj5.py
"""

import json
import math
import os
import sys

import bpy
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import capture_pj1 as C1  # noqa: E402

REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
BLEND = os.path.join(REPO, "blender", "concordia_personajes_master.blend")
OUT = os.path.join(REPO, "docs", "captures")
REPORT = os.path.join(REPO, "docs", "reports", "pj5_lods.json")


def show(names):
    for o in bpy.data.objects:
        if o.type == "MESH":
            o.hide_render = o.name not in names
    bpy.context.view_layer.update()


def main():
    bpy.ops.wm.open_mainfile(filepath=BLEND)
    sc = bpy.context.scene
    rep = json.load(open(REPORT))
    lod0 = list(rep["lod0"].keys())
    # regla de Godot (TODO_GODOT_personaje.txt): con botas, la pieza Feet se oculta entera (en el LOD0 lo hace la
    # mascara HIDE_Feet de Blender; las copias LOD1 no llevan mascaras activas)
    lod1 = [n for n in rep["lod1"].keys() if n != "PJ_Elfo_Feet_LOD1"]
    lod2 = [rep["lod2"]["malla"]]
    C1.setup(sc, res=(600, 800))
    sc.cycles.samples = 16
    iso = (Vector((-1.0, -0.42, 0)).normalized() * math.cos(math.radians(35.264))
           + Vector((0, 0, math.sin(math.radians(35.264))))).normalized()
    views = [("frente", Vector((0, -10, 0.95)), Vector((0, 0, 0.95)), 2.2),
             ("isometrica", Vector((0, 0, 0.9)) + iso * 12.0, Vector((0, 0, 0.9)), 2.3),
             ("orejas", Vector((0, -10, 1.74)), Vector((0, 0, 1.74)), 0.42),
             ("dobladillo", Vector((-10, 0, 0.42)), Vector((0, 0, 0.42)), 0.75)]
    paths, labels = [], []
    for tag, objs, key in (("LOD0", lod0, "lod0_total"), ("LOD1", lod1, "lod1_total"), ("LOD2", lod2, None)):
        show(objs)
        n = rep[key] if key else rep["lod2"]["tris"]
        for vname, eye, tgt, scale in views:
            c = C1.cam(sc, eye, tgt, ortho=scale)
            paths.append(C1.shot(sc, c, os.path.join(OUT, f"_tmp_pj5_{tag}_{vname}.png")))
            labels.append(f"{tag}  {n} tris  ({vname})")
    out = os.path.join(OUT, "pj5_lods.png")
    C1.sheet(paths, out, labels=labels, cols=4)
    print("CAPTURA", out, flush=True)


if __name__ == "__main__":
    main()
    sys.stdout.flush()
    os._exit(0)
