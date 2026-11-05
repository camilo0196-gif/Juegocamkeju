"""
CONCORDIA - capturas de la etapa 04 (muralla).

  eye_puerta_Alba_dentro   altura de personaje en la plazoleta de Oficios mirando la puerta Alba (k=0)
  iso_torre_linterna       CAM_Iso (ortho 50) sobre la torre de guardia k=44 (330 grados), al anochecer
  iso_mirador              CAM_Iso (ortho 45) sobre el mirador k=42 (315 grados)
  cenital                  toda la muralla desde arriba con el tipo de cada slot
  iso_overview             CAM_Iso, ortho temporal 460 (montaje completo)
  kit                      las piezas del kit en fila (fuera de la ciudad)
"""

import argparse
import os
import sys
from math import cos, radians, sin

import bpy
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Euler, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import concordia_const as C  # noqa: E402
import capture_stage02 as K  # noqa: E402
import terrain_profile as T  # noqa: E402

REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
DEFAULT_BLEND = os.path.join(REPO, "blender", f"{C.BLEND_BASENAME}_v04.blend")
DEFAULT_OUT = os.path.join(REPO, "docs", "captures")
TAG = "stage04"
ALL = ("gate", "mirador", "top", "iso", "kit", "morada", "door", "mirador_eye", "tower", "iso_dusk", "mirador_eye_dusk")


def parse_args():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    p = argparse.ArgumentParser()
    p.add_argument("--blend", default=DEFAULT_BLEND)
    p.add_argument("--out", default=DEFAULT_OUT)
    p.add_argument("--only", default=",".join(ALL))
    return p.parse_args(argv)


def dusk(scene):
    w = scene.world.node_tree.nodes["Background"]
    w.inputs["Color"].default_value = (0.10, 0.13, 0.22, 1)
    w.inputs["Strength"].default_value = 0.35
    sun = bpy.data.objects["TMP_sun"]
    sun.data.energy = 0.6
    sun.data.color = (1.0, 0.62, 0.42)
    sun.rotation_euler = Euler((radians(84), 0, radians(-60)))


def pol(a, r, z=0.0):
    x, y, _ = C.polar(a, r)
    return (x, y, z)


def main():
    args = parse_args()
    only = set(args.only.split(","))
    bpy.ops.wm.open_mainfile(filepath=args.blend)
    scene = bpy.context.scene
    os.makedirs(args.out, exist_ok=True)
    K.setup_render(scene)
    cam_iso = bpy.data.objects[C.CAM_ISO_NAME]
    P = lambda n: os.path.join(args.out, f"{TAG}_{n}.png")  # noqa: E731
    for o in list(bpy.data.collections["WALL_KIT"].all_objects):
        if isinstance(o, bpy.types.Object):
            o.hide_render = "kit" not in only or o.name.endswith("-colonly")
    for o in list(bpy.data.collections["WALL_LAYOUT"].objects):
        if o.name.endswith("-colonly"):
            o.hide_render = True

    if "gate" in only:
        cam = K.new_cam("TMP_eye_gate", lens=16)
        ex, ey = 172.0, -3.0
        K.look_at(cam, (ex, ey, T.height(ex, ey) + K.EYE), (200.0, 0.0, 6.0 + 9.0))
        K.render(scene, cam, P("eye_puerta_Alba_dentro"))
        K.annotate(scene, cam, P("eye_puerta_Alba_dentro"),
                   "Altura de personaje en la plazoleta de Oficios (r=176) mirando la Puerta del Alba por dentro",
                   [("runa 1.5 m (#8FD0FF, 2.5)", (196.0 - 0.07, 0.0, 11.0)),
                    ("STAIR_Gate L", pol(6.0, 193.5, 13.0)), ("STAIR_Gate R", pol(-6.0, 193.5, 13.0)),
                    ("torre 12 m x 24 m", pol(2.9, 201.0, 25.0))])
    if "mirador" in only:
        a = 42 * 7.5
        cam = K.iso_at(cam_iso, pol(a, 202.0, C.DATUM + 12.0), 45.0)
        K.render(scene, cam, P("iso45_mirador"))
        K.annotate(scene, cam, P("iso45_mirador"), "BASTION_Mirador (k=42, 315 grados) - CAM_Iso ortho 45",
                   [("balcon 4 x 2.5 m", pol(a, 206.0, C.DATUM + 14.0)), ("camino de ronda +12.4", pol(a + 2.0, 198.5, C.DATUM + 12.4))])
    if "top" in only:
        cam = K.new_cam("TMP_top", ortho=440.0)
        cam.location = (0, 0, 400)
        rx, ry = scene.render.resolution_x, scene.render.resolution_y
        scene.render.resolution_x = scene.render.resolution_y = 1600
        K.render(scene, cam, P("cenital"))
        from PIL import Image, ImageDraw, ImageFont
        img = Image.open(P("cenital")).convert("RGB")
        d = ImageDraw.Draw(img)
        W, H = img.size
        f = ImageFont.truetype("DejaVuSans-Bold.ttf", 16)
        colors = {"gate": (255, 80, 80), "tower": (255, 210, 60), "mirador": (90, 200, 255), "bastion": (230, 230, 230)}
        for o in bpy.data.collections["WALL_LAYOUT"].objects:
            if o.name.startswith("MARKER_WallSlot_"):
                k = o["k"]
                p = world_to_camera_view(scene, cam, o.location + Vector((0, 0, 20)))
                q = world_to_camera_view(scene, cam, Vector(pol(k * 7.5, 222.0, 30.0)))
                px, py = p.x * W, (1 - p.y) * H
                qx, qy = q.x * W, (1 - q.y) * H
                col = colors[o["type"]]
                d.ellipse([px - 5, py - 5, px + 5, py + 5], fill=col, outline=(0, 0, 0))
                if 0 < qx < W and 0 < qy < H:
                    d.text((qx - 9, qy - 8), f"{k:02d}", fill=col, font=f)
        img.save(P("cenital"))
        K.annotate(scene, cam, P("cenital"), "Muralla - cenital (Norte arriba), 48 slots", [],
                   ["Rojo = puertas (4) | Amarillo = torres de guardia (8)",
                    "Azul = BASTION_Mirador (4) | Blanco = BASTION_Open (32)"])
        scene.render.resolution_x, scene.render.resolution_y = rx, ry
    if "iso" in only:
        cam = K.iso_at(cam_iso, C.CAM_ISO_TARGET, 460.0)
        K.render(scene, cam, P("iso_overview"))
        K.annotate(scene, cam, P("iso_overview"), "Muralla montada - CAM_Iso, ortho TEMPORAL 460", [])
    if "kit" in only:
        cam = K.new_cam("TMP_kit", ortho=600.0 / 1.0)
        cam.data.ortho_scale = 560.0
        cam.rotation_euler = cam_iso.rotation_euler.copy()
        d = cam.rotation_euler.to_matrix() @ Vector((0, 0, -1))
        cam.location = Vector((25.0, -330.0, 10.0)) - d * 900
        K.render(scene, cam, P("kit"))
    if "morada" in only:
        a = 135.0 + 10.0
        cam = K.iso_at(cam_iso, pol(a, 194.0, C.DATUM + 8.0), 45.0)
        K.render(scene, cam, P("iso45_morada_NW_muralla"))
        K.annotate(scene, cam, P("iso45_morada_NW_muralla"),
                   "Morada NO junto a la muralla - CAM_Iso ortho 45 (el muro interior mira a la camara)",
                   [("runas a +4.5 (1 m sobre la Morada)", pol(a + 1.0, 196.9, C.DATUM + 4.5)),
                    ("plataforma +9.5", pol(a - 2.0, 192.0, 9.5)),
                    ("camino de ronda +12.4", pol(a + 3.0, 198.5, C.DATUM + 12.4))])
    if "door" in only:
        a = 20 * 7.5
        cam = K.iso_at(cam_iso, pol(a, 199.0, C.DATUM + 13.0), 30.0)
        K.render(scene, cam, P("iso30_torre_puerta_camino"))
        K.annotate(scene, cam, P("iso30_torre_puerta_camino"),
                   "TOWER_Guard (k=20, 150 grados): puerta 1.2 x 2.2 m al camino de ronda (+12.4) - ortho 30",
                   [("MARKER_TowerDoor_20 (+Y hacia el camino)", tuple(bpy.data.objects["MARKER_TowerDoor_20"].location))])
    if "mirador_eye" in only or "mirador_eye_dusk" in only:
        import stage04_wall as W
        from mathutils import Matrix
        k = 18
        m = W.slot_matrix(k * 7.5, C.WALL_RADIUS)
        # ojo en la esquina del balcon (junto al parapeto lateral, al fondo): el parapeto propio no tapa
        y_far = W.Y_OUT + W.BASTION_D / 2 - 0.2 + W.MIRADOR[1]
        eye = m @ Vector((-(W.MIRADOR[0] / 2 - 0.35), y_far - 0.4, W.BASTION_PLAT + 1.7))
        from math import cos as _cos

        def on_module(f, z):
            # punto sobre la cara exterior del modulo Seg18 (cuerda entre slots 18 y 19), f in [0, 1]
            rr = C.WALL_RADIUS * _cos(W.HALF) / _cos(radians((f - 0.5) * W.STEP_DEG))
            return W.slot_matrix((k + f) * W.STEP_DEG, rr) @ Vector((0.0, W.Y_OUT, z))
        tgt = on_module(0.55, W.RUNE_Z + 1.5)          # -X local = hacia k=19/20 (angulo creciente)
        for tag, is_dusk in (("mirador_eye", False), ("mirador_eye_dusk", True)):
            if tag not in only:
                continue
            if is_dusk:
                dusk(scene)
            cam = K.new_cam("TMP_eye_mir", lens=20)
            K.look_at(cam, eye, tgt)
            name = "eye_desde_mirador_k18" + ("_anochecer" if is_dusk else "")
            K.render(scene, cam, P(name))
            K.annotate(scene, cam, P(name),
                       "Desde el balcon del mirador k=18 (135 grados, suelo +13.9 sobre la base) mirando la cara exterior hacia k=19/20"
                       + (" - anochecer" if is_dusk else ""),
                       [("runas exteriores a +4.5", tuple(on_module(0.45, W.RUNE_Z))),
                        ("BASTION k=19", tuple(W.slot_matrix(19 * 7.5, C.WALL_RADIUS) @ Vector((0, W.Y_OUT + 2.5, 15.5)))),
                        ("TOWER_Guard k=20", tuple(W.slot_matrix(20 * 7.5, C.WALL_RADIUS) @ Vector((0, W.TOWER_CY, 26))))])
    if "iso_dusk" in only:
        dusk(scene)
        cam = K.iso_at(cam_iso, C.CAM_ISO_TARGET, 460.0)
        K.render(scene, cam, P("iso_overview_anochecer"))
        K.annotate(scene, cam, P("iso_overview_anochecer"),
                   "Muralla al anochecer - anillo de runas a +4.5 (MAT_Wall_Runes, emision 0.8), linternas 2.5", [])
    if "tower" in only:
        dusk(scene)
        a = 44 * 7.5
        cam = K.iso_at(cam_iso, pol(a, 204.0, C.DATUM + 16.0), 50.0)
        K.render(scene, cam, P("iso50_torre_linterna_anochecer"))
        K.annotate(scene, cam, P("iso50_torre_linterna_anochecer"),
                   "TOWER_Guard (k=44, 330 grados) al anochecer - CAM_Iso ortho 50 (luz de prueba)",
                   [("linterna 1.2 m (#8FD0FF, 2.5)", pol(a, 204.0, C.DATUM + 29.2)),
                    ("WALL_Mod_C: cadalso a medio terminar", pol(a - 4.6, 202.5, C.DATUM + 14.5))])


if __name__ == "__main__":
    main()
