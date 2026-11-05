"""
CONCORDIA - capturas de la etapa 09 (materiales).
  materiales_esferas   esfera de 1 m por material (UV de mundo, como en el juego), con etiqueta
  iso_ciudad           CAM_Iso, ortho temporal 460, ciudad entera con materiales
  iso_mercado          CAM_Iso ortho 110 sobre el Mercado (detalle de texturas)
"""

import os
import sys

import bpy
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import concordia_const as C  # noqa: E402
import capture_stage02 as K  # noqa: E402
import stage09_materials as SM  # noqa: E402

REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
BLEND = os.path.join(REPO, "blender", f"{C.BLEND_BASENAME}_v09.blend")
OUT = os.path.join(REPO, "docs", "captures")


def main():
    bpy.ops.wm.open_mainfile(filepath=BLEND)
    scene = bpy.context.scene
    K.setup_render(scene)
    for o in list(bpy.data.collections["WALL_KIT"].all_objects):
        o.hide_render = True
    for o in list(bpy.data.collections["WALL_LAYOUT"].objects):
        if o.name.endswith("-colonly"):
            o.hide_render = True
    P = lambda n: os.path.join(OUT, f"stage09_{n}.png")  # noqa: E731
    # esferas
    names = list(SM.MATS)
    xs = [1000 + (i % 6) * 1.5 for i in range(len(names))]
    ys = [1000 + (i // 6) * 1.5 for i in range(len(names))]
    cam = K.new_cam("TMP_spheres", ortho=10.5)
    cam.rotation_euler = (1.38, 0, 0)
    c = Vector((sum(xs) / len(xs), sum(ys) / len(ys), 0.5))
    d = cam.rotation_euler.to_matrix() @ Vector((0, 0, -1))
    cam.location = c - d * 40
    K.render(scene, cam, P("materiales_esferas"))
    K.annotate(scene, cam, P("materiales_esferas"), "Materiales de Concordia - esfera de 1 m por material (UV de mundo)",
               [(n[4:], (x, y, 1.08)) for n, x, y in zip(names, xs, ys)])
    cam_iso = bpy.data.objects[C.CAM_ISO_NAME]
    cam = K.iso_at(cam_iso, C.CAM_ISO_TARGET, 460.0)
    K.render(scene, cam, P("iso_ciudad"))
    K.annotate(scene, cam, P("iso_ciudad"), "Concordia con materiales - CAM_Iso, ortho TEMPORAL 460", [])
    cam = K.iso_at(cam_iso, (0.0, 120.0, 6.0), 110.0)
    K.render(scene, cam, P("iso_mercado"))
    K.annotate(scene, cam, P("iso_mercado"), "Mercado con materiales - CAM_Iso ortho 110", [])


if __name__ == "__main__":
    main()
