"""
CONCORDIA - capturas de la etapa 15 (Torre del Faro).
  faro_iso        CAM_Iso ortho 62 (torre completa + arranque del haz)
  faro_galeria    primer plano de la galeria con el cristal (desde fuera, a la altura de la galeria)
  faro_calle      desde la calle a altura de personaje (puerta, rampa, canales)
  faro_tuberia    cenital de la curva CRV_LightPipe_Tesoreria_Faro y sus soportes (diagnostico 2D)
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
BLEND = os.path.join(REPO, "blender", f"{C.BLEND_BASENAME}_v15.blend")
OUT = os.path.join(REPO, "docs", "captures")


def main():
    bpy.ops.wm.open_mainfile(filepath=BLEND)
    scene = bpy.context.scene
    K.setup_render(scene)
    for o in list(bpy.data.collections["WALL_KIT"].all_objects):
        o.hide_render = True
    for o in bpy.data.objects:
        if o.name.endswith(("-colonly", "_LOD1", "_LOD2", "-navmesh", "-occonly")):
            o.hide_render = True
    root = bpy.data.objects["FARO"]
    mw = root.matrix_world
    c = mw.translation
    P = lambda n: os.path.join(OUT, f"stage15_{n}.png")  # noqa: E731
    cam_iso = bpy.data.objects[C.CAM_ISO_NAME]
    cam = K.iso_at(cam_iso, (c.x, c.y, c.z + 22.0), 62.0)
    cam.data.clip_end = 3000
    K.render(scene, cam, P("faro_iso"))
    K.annotate(scene, cam, P("faro_iso"), "Torre del Faro (40 m) - CAM_Iso ortho 62: rampa en espiral, 4 canales de luz, "
               "galeria con cristal y haz (80 m, Godot lo anima)",
               [("galeria +34", tuple(mw @ Vector((0, 4.4, 35.2)))), ("FARO_Crystal", tuple(mw @ Vector((0, 0, 39.0)))),
                ("puerta", tuple(mw @ Vector((0, 7.3, 2.6))))])
    fwd = (mw.to_3x3() @ Vector((0, 1, 0))).normalized()
    side = (mw.to_3x3() @ Vector((1, 0, 0))).normalized()
    cam = K.new_cam("TMP_gal", lens=30)
    eye = c + fwd * 11.0 + side * 6.0 + Vector((0, 0, 37.5))
    K.look_at(cam, eye, c + Vector((0, 0, 37.0)))
    K.render(scene, cam, P("faro_galeria"))
    K.annotate(scene, cam, P("faro_galeria"), "Galeria a +34 m: parapeto, 8 columnas, anillo superior y FARO_Crystal "
               "(prismas de 4 a 6 m, MAT_Shard_Blue emision 4.0)", [])
    cam = K.new_cam("TMP_street", lens=20)
    eye = c + fwd * 22.0 - side * 6.0 + Vector((0, 0, 1.7))
    K.look_at(cam, eye, c + Vector((0, 0, 13.0)))
    K.render(scene, cam, P("faro_calle"))
    K.annotate(scene, cam, P("faro_calle"), "Desde la plaza a altura de personaje: puerta, rampa con barandilla y "
               "canales de luz que bajan hasta el anillo del suelo", [])
    # diagnostico 2D de la curva
    from PIL import Image, ImageDraw, ImageFont
    S = 5
    x0, y0, x1, y1 = -40, 30, 70, 140
    img = Image.new("RGB", ((x1 - x0) * S, (y1 - y0) * S), (30, 30, 30))
    d = ImageDraw.Draw(img)
    me = bpy.data.objects["TRN_City"].data
    import numpy as np
    a = me.color_attributes.get("road_mask")
    v = np.zeros(len(me.loops) * 4, dtype=np.float32)
    a.data.foreach_get("color", v)
    ls = np.zeros(len(me.polygons), dtype=np.int64)
    me.polygons.foreach_get("loop_start", ls)
    road = v.reshape(-1, 4)[:, 0][ls]
    s2 = me.color_attributes.get("slab_ring_id")
    v2 = np.zeros(len(me.loops) * 4, dtype=np.float32)
    s2.data.foreach_get("color", v2)
    slab = v2.reshape(-1, 4)[:, 0][ls]
    cen = np.zeros(len(me.polygons) * 3, dtype=np.float32)
    me.polygons.foreach_get("center", cen)
    cen = cen.reshape(-1, 3)
    for (x, y, _), rr, sl in zip(cen, road, slab):
        if x0 < x < x1 and y0 < y < y1:
            col = (95, 95, 100) if rr > 0.5 else (150, 145, 135) if sl > 0.01 else (60, 55, 48)
            px, py = (x - x0) * S, (y1 - y) * S
            d.rectangle((px - 2, py - 2, px + 2, py + 2), fill=col)
    cu = bpy.data.objects["CRV_LightPipe_Tesoreria_Faro"].data
    pts = [(p.co.x, p.co.y) for p in cu.splines[0].points]
    d.line([((x - x0) * S, (y1 - y) * S) for x, y in pts], fill=(143, 208, 255), width=4)
    for o in bpy.data.objects:
        if o.name.startswith("MARKER_PipeSupport_"):
            x, y = o.location.x, o.location.y
            d.ellipse(((x - x0) * S - 6, (y1 - y) * S - 6, (x - x0) * S + 6, (y1 - y) * S + 6), outline=(255, 255, 255),
                      width=2)
    f = ImageFont.truetype("DejaVuSans.ttf", 22)
    d.rectangle((0, 0, img.size[0], 34), fill=(0, 0, 0))
    d.text((10, 6), "CRV_LightPipe_Tesoreria_Faro (azul) sobre calles (gris) y plaza (claro); circulos = soportes cada "
           "8 m", fill=(255, 255, 255), font=f)
    img.save(P("faro_tuberia"))
    _ = math


if __name__ == "__main__":
    main()
