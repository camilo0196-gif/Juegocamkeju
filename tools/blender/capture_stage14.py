"""
CONCORDIA - capturas de la etapa 14 (Obelisco de los Pisos). Solo para la captura se encienden los pisos 1..37
(MAT_Obelisk_Mark_Lit por objeto), como haria Godot; el .blend guardado los deja todos apagados.
  obelisco_iso      CAM_Iso ortho 34
  obelisco_cara     cara frontal (hacia la plaza) de cerca: filas 0-2 (pisos 1-5, 21-25 encendidos; 41-45 apagados)
  obelisco_numeros  primer plano de 5 marcas para leer los numerales (pisos 1-5 y 21-25)
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
BLEND = os.path.join(REPO, "blender", f"{C.BLEND_BASENAME}_v14.blend")
OUT = os.path.join(REPO, "docs", "captures")
LIT_UPTO = 37


def main():
    bpy.ops.wm.open_mainfile(filepath=BLEND)
    scene = bpy.context.scene
    K.setup_render(scene)
    for o in list(bpy.data.collections["WALL_KIT"].all_objects):
        o.hide_render = True
    for o in bpy.data.objects:
        if o.name.endswith(("-colonly", "_LOD1", "_LOD2", "-navmesh", "-occonly")):
            o.hide_render = True
    lit = bpy.data.materials["MAT_Obelisk_Mark_Lit"]
    for i in range(1, LIT_UPTO + 1):
        o = bpy.data.objects[f"OBELISK_Mark_{i:03d}"]
        o.material_slots[0].link = "OBJECT"
        o.material_slots[0].material = lit
    root = bpy.data.objects["OBELISK"]
    mw = root.matrix_world
    c = mw.translation
    front = (mw.to_3x3() @ Vector((0, 1, 0))).normalized()
    left = (mw.to_3x3() @ Vector((-1, 0, 0))).normalized()
    P = lambda n: os.path.join(OUT, f"stage14_{n}.png")  # noqa: E731
    cam = K.iso_at(bpy.data.objects[C.CAM_ISO_NAME], (c.x, c.y, c.z + 12.0), 44.0)
    K.render(scene, cam, P("obelisco_iso"))
    K.annotate(scene, cam, P("obelisco_iso"), f"Obelisco de los Pisos (25 m) - CAM_Iso ortho 44 - pisos 1-{LIT_UPTO} "
               "encendidos solo para la captura", [("piso 16", tuple(mw @ Vector((1.45, -0.98, 3.6)))),
                                                   ("piso 81 (fila 4)", tuple(mw @ Vector((-0.98, 1.05, 19.6))))])
    cam = K.new_cam("TMP_face", lens=28)
    eye = c + front * 9.0 + left * 3.0 + Vector((0, 0, 3.0))
    K.look_at(cam, eye, c + front * 1.2 + Vector((0, 0, 7.0)))
    K.render(scene, cam, P("obelisco_cara"))
    K.annotate(scene, cam, P("obelisco_cara"), "Cara frontal (hacia la plaza): filas 0-2 -> pisos 1-5 y 21-25 "
               "encendidos (#8FD0FF, 3.0), 41-45 apagados; placa con runa al pie",
               [(f"piso {n}", tuple(mw @ Vector((x, 1.5, z)))) for n, x, z in
                ((1, 1.0, 3.25), (21, 0.95, 7.25), (41, 0.9, 11.25))])
    cam = K.new_cam("TMP_num", lens=50)
    eye = c + front * 5.6 + Vector((0, 0, 3.75))
    K.look_at(cam, eye, c + front * 1.35 + Vector((0, 0, 3.6)))
    K.render(scene, cam, P("obelisco_numeros"))
    K.annotate(scene, cam, P("obelisco_numeros"), "Fila 0 de la cara frontal: pisos 1-5 (numerales cistercienses: palo + "
               "unidades arriba dcha + decenas arriba izda + centenas abajo dcha)",
               [(f"piso {n}", tuple(mw @ Vector(((2 - col) * 0.5, 1.5, 3.95)))) for n, col in
                ((1, 0), (2, 1), (3, 2), (4, 3), (5, 4))])


if __name__ == "__main__":
    main()
