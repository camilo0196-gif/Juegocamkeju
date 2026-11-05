"""
CONCORDIA - capturas de la etapa 12 (kit de edificios).
  kit_sheet_muros         18 modulos de muro (6 tipos x 3 variantes), CAM_Iso
  kit_sheet_estructura    esquinas, entramado, contrafuerte, cornisa, arcos, escalera, balcones, tejados, chimeneas
  kit_sheet_props         toldos A/B/C, letrero, farolillo, cajas, barril, herramientas
  casa_prueba_iso         casa 12 x 9 m, 2 plantas, CAM_Iso (ortho 24)
  casa_prueba_personaje   a 1.7 m de altura, 15 m delante de la fachada
  casa_prueba_partes      Body / Roof / Props separados (Roof oculto = vista de "entrar")
"""

import math
import os
import sys

import bpy
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import concordia_const as C  # noqa: E402
import capture_stage02 as K  # noqa: E402

REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
BLEND = os.path.join(REPO, "blender", f"{C.BLEND_BASENAME}_v12.blend")
OUT = os.path.join(REPO, "docs", "captures")
STRUCT = ("CORNER_", "TIMBER_", "BUTTRESS_", "FLOOR_", "ARCH_", "STAIRS_", "BALCONY_", "ROOF_", "CHIMNEY_", "DORMER_")
PROPS = ("AWNING_", "SIGN_", "LANTERN_", "CRATE_", "BARREL", "TOOL_")


def frame(objs, cam_iso, margin=1.25):
    cen = sum((o.matrix_world.translation for o in objs), Vector()) / len(objs)
    cam = K.iso_at(cam_iso, (cen.x, cen.y, 1.5), 10.0)
    bpy.context.view_layer.update()
    from bpy_extras.object_utils import world_to_camera_view
    scene = bpy.context.scene
    xs, ys = [], []
    for o in objs:
        for b in o.bound_box:
            p = world_to_camera_view(scene, cam, o.matrix_world @ Vector(b))
            xs.append(p.x)
            ys.append(p.y)
    aspect = scene.render.resolution_x / scene.render.resolution_y
    span = max(max(xs) - min(xs), max(ys) - min(ys))
    cam.data.ortho_scale = 10.0 * span * margin
    # recentrar
    cx, cy = (max(xs) + min(xs)) / 2 - 0.5, (max(ys) + min(ys)) / 2 - 0.5
    right = cam.matrix_world.to_3x3() @ Vector((1, 0, 0))
    up = cam.matrix_world.to_3x3() @ Vector((0, 1, 0))
    cam.location += right * cx * 10.0 + up * cy * 10.0 / aspect
    return cam


def label_of(o):
    return f"{o.name}  {o.get('tris', len(o.data.polygons))} tris"


def main():
    only = set(sys.argv[sys.argv.index("--") + 1].split(",")) if "--" in sys.argv else None
    bpy.ops.wm.open_mainfile(filepath=BLEND)
    scene = bpy.context.scene
    K.setup_render(scene)
    for o in list(bpy.data.collections["WALL_KIT"].all_objects):
        o.hide_render = True
    cam_iso = bpy.data.objects[C.CAM_ISO_NAME]
    kit = [o for o in bpy.data.collections["BLD_KIT"].objects if o.get("kit_piece")]
    P = lambda n: os.path.join(OUT, f"stage12_{n}.png")  # noqa: E731

    def want(n):
        return only is None or n in only
    rx, ry = scene.render.resolution_x, scene.render.resolution_y
    scene.render.resolution_x, scene.render.resolution_y = 2400, 1500
    for tag, sel, title in (("kit_sheet_muros", lambda o: o.name.startswith("WALL_"),
                             "Kit BLD - muros 3 x 3.2 m (Solid, Window, Door, Arch, Barred, Shutter) x (limpia, "
                             "remiendo de piedra, vigas de reemplazo)"),
                            ("kit_sheet_estructura", lambda o: o.name.startswith(STRUCT),
                             "Kit BLD - esquinas, entramado, contrafuerte, cornisa, arcos 3/6 m, escalera, balcones, "
                             "tejados, chimeneas, buhardilla"),
                            ("kit_sheet_props", lambda o: o.name.startswith(PROPS),
                             "Kit BLD - toldos A/B/C, letrero colgante, farolillo de esquirla, cajas, barril, "
                             "herramientas")):
        if not want(tag):
            continue
        objs = [o for o in kit if sel(o)]
        cam = frame(objs, cam_iso)
        K.render(scene, cam, P(tag))
        K.annotate(scene, cam, P(tag), title,
                   [(label_of(o), o.matrix_world @ Vector((0, 0, max(v[2] for v in o.bound_box) + 0.3)))
                    for o in objs])
    scene.render.resolution_x, scene.render.resolution_y = rx, ry
    root = bpy.data.objects["TEST_Casa_12x9"]
    c = root.matrix_world.translation
    fwd = root.matrix_world.to_3x3() @ Vector((0, 1, 0))
    if want("casa_prueba_iso"):
        cam = K.iso_at(cam_iso, (c.x, c.y, 4.0), 24.0)
        K.render(scene, cam, P("casa_prueba_iso"))
        door = bpy.data.objects["MARKER_TEST_Casa_12x9_Door"].matrix_world.translation
        K.annotate(scene, cam, P("casa_prueba_iso"), "Casa de prueba 12 x 9 m, 2 plantas, entramado, dos aguas 40 - "
                   "CAM_Iso ortho 24", [("puerta (MARKER_..._Door)", tuple(door + Vector((0, 0, 1.2))))])
    if want("casa_prueba_personaje"):
        cam = K.new_cam("TMP_eye", lens=18)
        eye = c + fwd * 15.0 + Vector((0, 0, 1.7)) + root.matrix_world.to_3x3() @ Vector((-2.5, 0, 0))
        K.look_at(cam, eye, c + fwd * 2.0 + Vector((0, 0, 4.6)))
        K.render(scene, cam, P("casa_prueba_personaje"))
        K.annotate(scene, cam, P("casa_prueba_personaje"), "Casa de prueba a altura de personaje (1.7 m, 15 m delante "
                   "de la fachada)", [])
    if want("casa_prueba_partes"):
        roof = bpy.data.objects["TEST_Casa_12x9_Roof"]
        roof.hide_render = True
        cam = K.iso_at(cam_iso, (c.x, c.y, 3.0), 24.0)
        K.render(scene, cam, P("casa_prueba_partes"))
        K.annotate(scene, cam, P("casa_prueba_partes"), "Misma casa con _Roof oculto (como en Godot al entrar): "
                   "Body + Props + InteriorVolume (sin render)", [])
        roof.hide_render = False


if __name__ == "__main__":
    main()
