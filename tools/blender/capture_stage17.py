"""
CONCORDIA - capturas de la etapa 17.
  faro_canales    base del Faro desde la plaza: canales de la torre unidos a los 4 canales del suelo
  faro_cartelas   ultima vuelta de la rampa: cartelas de piedra y barandillas continuas
  portal          Portal con pilares 2.0 x 2.0, luz 7.8 y velo 7.8 x 11 (CAM_Iso ortho 30)
"""

import os
import sys

import bpy
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import concordia_const as C  # noqa: E402
import capture_stage02 as K  # noqa: E402

REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
BLEND = os.path.join(REPO, "blender", f"{C.BLEND_BASENAME}_v17.blend")
OUT = os.path.join(REPO, "docs", "captures")


def P(n):
    return os.path.join(OUT, f"stage17_{n}.png")


def main():
    bpy.ops.wm.open_mainfile(filepath=BLEND)
    scene = bpy.context.scene
    K.setup_render(scene)
    for o in list(bpy.data.collections["WALL_KIT"].all_objects):
        o.hide_render = True
    for o in bpy.data.objects:
        if o.name.endswith(("-colonly", "_LOD1", "_LOD2", "-navmesh", "-occonly", "_InteriorVolume")):
            o.hide_render = True
    fr = bpy.data.objects["FARO"]
    mw = fr.matrix_world
    L = lambda x, y, z: mw @ Vector((x, y, z))  # noqa: E731
    cam = K.new_cam("TMP_c", lens=24)
    K.look_at(cam, L(4.5, 15.5, 6.5), L(0.0, 7.0, 1.2))
    K.render(scene, cam, P("faro_canales"))
    K.annotate(scene, cam, P("faro_canales"), "Faro: los 4 canales de la torre arrancan sobre los 4 de la plaza "
               "(+-0.6 y +-1.8 m; desfase 0 cm). Los interiores rodean el umbral con una L", [
                   ("canal +1.8", tuple(L(1.8, 9.0, 0.0))), ("L hacia +0.6", tuple(L(1.1, 7.7, 0.0))),
                   ("bajada x=1.55", tuple(L(1.55, 6.9, 2.5)))])
    cam = K.new_cam("TMP_k", lens=28)
    K.look_at(cam, L(11.0, -9.0, 27.5), L(0.0, 0.0, 30.5))
    K.render(scene, cam, P("faro_cartelas"))
    K.annotate(scene, cam, P("faro_cartelas"), "Ultima vuelta (+29.5 a +32): rampa separada del fuste sobre cartelas de "
               "piedra, barandilla exterior continua e interior en el tramo separado", [])
    cam = K.iso_at(bpy.data.objects[C.CAM_ISO_NAME], (0.0, 0.0, C.Z_PLAZA + 6.0 if hasattr(C, "Z_PLAZA") else 14.0), 30.0)
    cam.data.clip_end = 5000
    K.render(scene, cam, P("portal"))
    K.annotate(scene, cam, P("portal"), "Portal: pilares 2.0 x 2.0 m, luz 7.8 m, velo 7.8 x 11 m; esquinas a r 5.98 "
               "(pedestal r 6.0)", [])


if __name__ == "__main__":
    main()
