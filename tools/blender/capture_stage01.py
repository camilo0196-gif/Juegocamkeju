"""
CONCORDIA - capturas de verificacion de la etapa 01.

Abre concordia_v01.blend, anade PROXIES TEMPORALES (no se guardan) para hacer
visibles los Empties y las cotas de referencia, renderiza con Cycles (CPU) y
rotula los marcadores proyectando su posicion 3D a la imagen.

Proxies temporales (coleccion TMP_Capture, se descartan al terminar):
- Disco r=200 a DATUM (+6) = huella interior de la ciudad (solo referencia).
- Anillo 200..260 a Z=0 = yermo exterior (solo referencia).
- Disco r=60 a Z=+8 = Plaza del Portal.
- Por puerta: poste 0..+6, esfera en el Empty y cono apuntando hacia fuera.

Capturas:
1. iso_overview   CAM_Iso con ortho_scale temporal (la ciudad mide 400 m y
                  no cabe en 120; el .blend conserva 120).
2. iso_cam120     CAM_Iso exactamente como esta guardada (ortho 120).
3. eye_gate_E     Perspectiva a altura de personaje (1.7 m sobre DATUM)
                  24 m dentro de la Puerta del Alba, mirando al Este.
"""

import argparse
import os
import sys
from math import radians

import bpy
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Euler, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import concordia_const as C  # noqa: E402

REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
DEFAULT_BLEND = os.path.join(REPO, "blender", f"{C.BLEND_BASENAME}_v01.blend")
DEFAULT_OUT = os.path.join(REPO, "docs", "captures")

OVERVIEW_ORTHO = 460.0
SAMPLES = 48
EYE_HEIGHT = 1.7

# Colores de los proxies (neutros, NO son materiales del juego)
COL_CITY = (0.32, 0.31, 0.29, 1)
COL_YERMO = (0.12, 0.12, 0.12, 1)
COL_PLAZA = (0.62, 0.58, 0.50, 1)
COL_POLE = (0.03, 0.03, 0.03, 1)
COL_HEAD = (0.85, 0.85, 0.82, 1)


def parse_args():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    p = argparse.ArgumentParser()
    p.add_argument("--blend", default=DEFAULT_BLEND)
    p.add_argument("--out", default=DEFAULT_OUT)
    p.add_argument("--tag", default="stage01")
    return p.parse_args(argv)


def mat(name, rgba):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = rgba
    bsdf.inputs["Roughness"].default_value = 0.9
    return m


def add(col, obj_op, material, **kw):
    obj_op(**kw)
    o = bpy.context.active_object
    for c in o.users_collection:
        c.objects.unlink(o)
    col.objects.link(o)
    o.data.materials.append(material)
    return o


def build_proxies(scene):
    col = bpy.data.collections.new("TMP_Capture")
    scene.collection.children.link(col)
    m_city, m_yermo, m_plaza = mat("TMP_city", COL_CITY), mat("TMP_yermo", COL_YERMO), mat("TMP_plaza", COL_PLAZA)
    m_pole, m_head = mat("TMP_pole", COL_POLE), mat("TMP_head", COL_HEAD)
    ops = bpy.ops.mesh

    # Ciudad: cilindro 0..DATUM, r=200
    add(col, ops.primitive_cylinder_add, m_city, vertices=256, radius=C.WALL_RADIUS,
        depth=C.DATUM, location=(0, 0, C.DATUM / 2))
    # Yermo: disco grande a Z=0
    add(col, ops.primitive_circle_add, m_yermo, vertices=256, radius=C.WALL_RADIUS + 60,
        fill_type="NGON", location=(0, 0, C.Z_EXTERIOR))
    # Plaza: cilindro DATUM..Z_PLAZA, r=60
    h = C.Z_PLAZA - C.DATUM
    add(col, ops.primitive_cylinder_add, m_plaza, vertices=192, radius=C.PLAZA_RADIUS,
        depth=h, location=(0, 0, C.DATUM + h / 2))

    for name, (angle, _label) in C.GATES.items():
        x, y, z = C.polar(angle, C.GATE_RADIUS, C.GATE_Z)
        add(col, ops.primitive_cylinder_add, m_pole, vertices=16, radius=1.2,
            depth=z, location=(x, y, z / 2))
        add(col, ops.primitive_uv_sphere_add, m_head, segments=24, ring_count=12,
            radius=3.0, location=(x, y, z))
        cone = add(col, ops.primitive_cone_add, m_head, vertices=16, radius1=2.5, depth=8,
                   location=C.polar(angle, C.GATE_RADIUS + 7, z))
        cone.rotation_euler = (0, radians(90), radians(angle))  # punta hacia fuera
    return col


def setup_render(scene):
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = SAMPLES
    scene.cycles.use_denoising = True
    scene.view_settings.view_transform = "AgX"
    scene.render.image_settings.file_format = "PNG"
    world = bpy.data.worlds.new("TMP_world")
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.55, 0.57, 0.60, 1)
    world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.6
    scene.world = world
    sun = bpy.data.objects.new("TMP_sun", bpy.data.lights.new("TMP_sun", "SUN"))
    sun.data.energy = 3.5
    sun.data.angle = radians(2)
    sun.rotation_euler = Euler((radians(40), radians(10), radians(-30)))
    scene.collection.objects.link(sun)


def render(scene, path):
    scene.render.filepath = path
    bpy.ops.render.render(write_still=True)
    print("render:", path)


def annotate(scene, cam, path, title, labels):
    from PIL import Image, ImageDraw, ImageFont
    img = Image.open(path).convert("RGB")
    d = ImageDraw.Draw(img)
    W, H = img.size
    try:
        font = ImageFont.truetype("DejaVuSans-Bold.ttf", 26)
        small = ImageFont.truetype("DejaVuSans.ttf", 22)
    except OSError:
        font = small = ImageFont.load_default()
    for text, world_pt in labels:
        p = world_to_camera_view(scene, cam, Vector(world_pt))
        if not (0 <= p.x <= 1 and 0 <= p.y <= 1 and p.z > 0):
            continue
        px, py = p.x * W, (1 - p.y) * H
        d.ellipse([px - 6, py - 6, px + 6, py + 6], outline=(255, 255, 255), width=3)
        tx, ty = px + 14, py - 40
        bb = d.textbbox((tx, ty), text, font=font)
        if bb[2] > W - 10:  # no cabe a la derecha: etiqueta a la izquierda del punto
            tx = px - 14 - (bb[2] - bb[0])
            bb = d.textbbox((tx, ty), text, font=font)
        d.rectangle([bb[0] - 6, bb[1] - 4, bb[2] + 6, bb[3] + 4], fill=(0, 0, 0))
        d.text((tx, ty), text, fill=(255, 255, 255), font=font)
    d.rectangle([0, 0, W, 44], fill=(0, 0, 0))
    d.text((14, 9), title, fill=(255, 255, 255), font=small)
    img.save(path)


def main():
    args = parse_args()
    bpy.ops.wm.open_mainfile(filepath=args.blend)
    scene = bpy.context.scene
    os.makedirs(args.out, exist_ok=True)
    build_proxies(scene)
    setup_render(scene)
    cam = bpy.data.objects[C.CAM_ISO_NAME]
    gate_labels = [(f"{n}  ({C.GATES[n][1]})", tuple(bpy.data.objects[n].location)) for n in C.GATES]

    # 1. Vista general isometrica (ortho temporal)
    saved_scale = cam.data.ortho_scale
    cam.data.ortho_scale = OVERVIEW_ORTHO
    p1 = os.path.join(args.out, f"{args.tag}_iso_overview.png")
    render(scene, p1)
    annotate(scene, cam, p1,
             f"CAM_Iso  rot X54.736 Z45  |  ortho TEMPORAL {OVERVIEW_ORTHO:.0f} (guardada: {saved_scale:.0f})"
             f"  |  proxies temporales: muralla r200 @+6, plaza r60 @+8, yermo @0",
             gate_labels + [("Plaza r60 @+8", (0, 0, C.Z_PLAZA))])
    cam.data.ortho_scale = saved_scale

    # 2. CAM_Iso tal cual (ortho 120)
    p2 = os.path.join(args.out, f"{args.tag}_iso_cam120.png")
    render(scene, p2)
    annotate(scene, cam, p2, f"CAM_Iso tal como esta guardada: ortho {saved_scale:.0f} (ancho visible = {saved_scale:.0f} m)",
             [("Centro (0,0,+8)", (0, 0, C.Z_PLAZA))])

    # 3. Altura de personaje junto a la Puerta del Alba
    eye_data = bpy.data.cameras.new("TMP_eye")
    eye_data.lens = 28
    eye_data.clip_end = 2000
    eye = bpy.data.objects.new("TMP_eye", eye_data)
    scene.collection.objects.link(eye)
    eye.location = (C.GATE_RADIUS - 24, -6, C.DATUM + EYE_HEIGHT)
    target = Vector(C.polar(0.0, C.GATE_RADIUS, C.GATE_Z + 2))
    eye.rotation_euler = (target - eye.location).to_track_quat("-Z", "Y").to_euler()
    scene.camera = eye
    p3 = os.path.join(args.out, f"{args.tag}_eye_gate_E.png")
    render(scene, p3)
    annotate(scene, eye, p3, f"Altura de personaje: ojo a +{C.DATUM + EYE_HEIGHT:.1f} (1.7 m sobre DATUM), 24 m dentro de la Puerta del Alba",
             [(n, tuple(bpy.data.objects[n].location)) for n in ("MARKER_Gate_E",)])
    # No se guarda nada: el .blend queda intacto.


if __name__ == "__main__":
    main()
