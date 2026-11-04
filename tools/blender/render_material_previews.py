"""
CONCORDIA - vista previa de la biblioteca de materiales: cada material sobre una esfera de
1 m de diametro y un plano de 4 x 4 m (UV en metros: 1 m = 1 tile). Cycles CPU.

Salida: docs/captures/stage04_materials_sheet.png (+ una imagen por material en el scratch)
"""

import os
import sys
import tempfile
from math import pi, radians

import bpy
from mathutils import Euler, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import material_library as ML  # noqa: E402

REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
OUT = os.path.join(REPO, "docs", "captures", "stage04_materials_sheet.png")
W, H = 800, 450
METALLIC = {"IronBlack": 0.85}


def setup():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    s = bpy.context.scene
    s.render.engine = "CYCLES"
    s.cycles.device = "CPU"
    s.cycles.samples = 40
    s.cycles.use_denoising = True
    s.render.resolution_x, s.render.resolution_y = W, H
    s.view_settings.view_transform = "AgX"
    w = bpy.data.worlds.new("w")
    w.use_nodes = True
    w.node_tree.nodes["Background"].inputs["Color"].default_value = (0.55, 0.6, 0.68, 1)
    w.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.8
    s.world = w
    sun = bpy.data.objects.new("sun", bpy.data.lights.new("sun", "SUN"))
    sun.data.energy = 3.5
    sun.data.angle = radians(3)
    sun.rotation_euler = Euler((radians(50), 0, radians(-35)))
    s.collection.objects.link(sun)
    bpy.ops.mesh.primitive_plane_add(size=4.0, location=(0, 0, 0))
    plane = bpy.context.active_object
    for lp in plane.data.uv_layers.active.data:
        lp.uv = (lp.uv[0] * 4.0, lp.uv[1] * 4.0)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.5, segments=64, ring_count=32, location=(0.6, 0.4, 0.5))
    sph = bpy.context.active_object
    bpy.ops.object.shade_smooth()
    for lp in sph.data.uv_layers.active.data:
        lp.uv = (lp.uv[0] * pi, lp.uv[1] * pi / 2)        # metros sobre la superficie
    cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam"))
    cam.data.lens = 40
    s.collection.objects.link(cam)
    cam.location = (3.6, -3.6, 2.6)
    cam.rotation_euler = (Vector((0.1, 0.2, 0.2)) - cam.location).to_track_quat("-Z", "Y").to_euler()
    s.camera = cam
    return plane, sph


def main():
    from PIL import Image, ImageDraw, ImageFont
    plane, sph = setup()
    tmp = tempfile.mkdtemp()
    tiles = []
    for name in ML.SETS:
        m = ML.make_material(f"MAT_{name}", name, METALLIC.get(name))
        for o in (plane, sph):
            o.data.materials.clear()
            o.data.materials.append(m)
        p = os.path.join(tmp, f"{name}.png")
        bpy.context.scene.render.filepath = p
        bpy.ops.render.render(write_still=True)
        tiles.append((name, p))
        print("render:", name)
    cols = 3
    rows = (len(tiles) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * W, rows * (H + 34)), (18, 18, 18))
    d = ImageDraw.Draw(sheet)
    f = ImageFont.truetype("DejaVuSans-Bold.ttf", 18)
    fs = ImageFont.truetype("DejaVuSans.ttf", 15)
    for i, (name, p) in enumerate(tiles):
        x, y = (i % cols) * W, (i // cols) * (H + 34)
        sheet.paste(Image.open(p), (x, y + 34))
        d.text((x + 8, y + 3), f"{name}", fill=(255, 255, 255), font=f)
        d.text((x + 8 + d.textlength(name, font=f) + 12, y + 7), ML.SETS[name][0] + " - " + ML.SETS[name][2],
               fill=(190, 190, 190), font=fs)
    sheet.save(OUT)
    print("sheet:", OUT)


if __name__ == "__main__":
    main()
