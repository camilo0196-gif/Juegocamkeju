"""
CONCORDIA - capturas de la etapa 08 (exterior de ceniza).

  iso_overview_exterior   CAM_Iso con ortho temporal 840 (ciudad + exterior + acantilados)
  eye_mirador_exterior    desde el balcon del mirador k=18 (NO) mirando hacia fuera: capas de relieve
  eye_mirador_k42         desde el mirador k=42 (SE)
  iso_puerta_sin_salida   CAM_Iso ortho 70 sobre la Puerta Norte por fuera (talud + ceniza, sin camino)
  cenital_exterior        cenital completa (Norte arriba)
"""

import os
import sys
from math import radians

import bpy
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import concordia_const as C  # noqa: E402
import capture_stage02 as K  # noqa: E402

REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
BLEND = os.path.join(REPO, "blender", f"{C.BLEND_BASENAME}_v08.blend")
OUT = os.path.join(REPO, "docs", "captures")


def main():
    only = set(sys.argv[sys.argv.index("--") + 1].split(",")) if "--" in sys.argv else None
    bpy.ops.wm.open_mainfile(filepath=BLEND)
    scene = bpy.context.scene
    K.setup_render(scene)
    scene.camera = None
    for o in list(bpy.data.collections["WALL_KIT"].all_objects):
        o.hide_render = True
    for o in list(bpy.data.collections["WALL_LAYOUT"].objects):
        if o.name.endswith("-colonly"):
            o.hide_render = True
    # niebla de distancia suave (solo vista previa: las tormentas de ceniza van en Godot)
    w = scene.world.node_tree.nodes["Background"]
    w.inputs["Color"].default_value = (0.42, 0.43, 0.45, 1)
    cam_iso = bpy.data.objects[C.CAM_ISO_NAME]
    import stage04_wall as W
    P = lambda n: os.path.join(OUT, f"stage08_{n}.png")  # noqa: E731

    def want(n):
        return only is None or n in only
    if want("iso_overview_exterior"):
        cam = K.iso_at(cam_iso, (0, 0, 0), 840.0)
        cam.data.clip_end = 3000
        K.render(scene, cam, P("iso_overview_exterior"))
        K.annotate(scene, cam, P("iso_overview_exterior"), "Exterior de ceniza (r 212-400) - CAM_Iso ortho TEMPORAL 840",
                   [("acantilados 25-40 m", (0, 395, 36)), ("cauce seco", (-150, 260, 0))])
    for tag, k in (("eye_mirador_exterior", 18), ("eye_mirador_k42", 42)):
        if not want(tag):
            continue
        m = W.slot_matrix(k * 7.5, C.WALL_RADIUS)
        y_far = W.Y_OUT + W.BASTION_D / 2 - 0.2 + W.MIRADOR[1]
        eye = m @ Vector((0.0, y_far - 0.3, W.BASTION_PLAT + 1.7))
        tgt = m @ Vector((0.0, 150.0, -8.0))
        cam = K.new_cam("TMP_eye_ext", lens=22)
        cam.data.clip_end = 2000
        K.look_at(cam, eye, tgt)
        K.render(scene, cam, P(tag))
        K.annotate(scene, cam, P(tag), f"Desde el balcon del mirador k={k} mirando el exterior: capas de relieve gris", [])
    if want("iso_puerta_sin_salida"):
        cam = K.iso_at(cam_iso, (0, -216, 1.0), 70.0)
        K.render(scene, cam, P("iso_puerta_sin_salida"))
        K.annotate(scene, cam, P("iso_puerta_sin_salida"), "Puerta Sur por fuera: talud de ceniza, foso seco, sin camino (ortho 70)",
                   [("talud +6 -> 0", (0, -208, 3.0)), ("foso seco (fondo -1.5)", (14, -217, -1.2)),
                    ("monton de ceniza", (0, -216, 1.5)), ("dunas 0.5-2 m", (-22, -232, 0.8))])
    if want("cenital_exterior"):
        cam = K.new_cam("TMP_top", ortho=820.0)
        cam.location = (0, 0, 600)
        cam.data.clip_end = 2000
        rx, ry = scene.render.resolution_x, scene.render.resolution_y
        scene.render.resolution_x = scene.render.resolution_y = 1800
        K.render(scene, cam, P("cenital_exterior"))
        K.annotate(scene, cam, P("cenital_exterior"), "Exterior - cenital (Norte arriba)", [])
        scene.render.resolution_x, scene.render.resolution_y = rx, ry


if __name__ == "__main__":
    main()
