"""
CONCORDIA - capturas del PJ2 (cabello y ropa inicial del Sanador) sobre blender/elfo_v02.blend.
  tpose     frente, lado y espalda (ortograficas, fondo gris, luz uniforme)
  iso       CAM_Iso (direccion de la ciudad) a ortho 6 (escala de juego) y a ortho 2,5 (detalle)
  ocultar   8 vistas 3/4: todo puesto y cada pieza oculta (comprueba los HIDE_* del cuerpo)
  detalle   pelo por detras, cinturon con bolsitas y frascos, colgante, dobladillo bordado
  atlas     hoja del atlas (albedo con alfa sobre gris, normal, ORM, emision)
python capture_pj2.py <prefijo_salida> [nombres...]
"""

import os
import sys

import bpy
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import capture_pj1 as C1  # noqa: E402

REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
BLEND = os.path.join(REPO, "blender", "elfo_v02.blend")
PIECES = ("Robe_Top", "Robe_Skirt", "Hood", "Belt_Pouches", "Boots", "Bracers", "Hair_Elf")


def set_hidden(names):
    for o in bpy.data.objects:
        if o.get("pj_prenda"):
            h = o.name in names
            o.hide_render = h
            o.hide_viewport = h
    bpy.context.view_layer.update()


def main():
    a = sys.argv[sys.argv.index("--") + 1:]
    pre, only = a[0], set(a[1:])
    bpy.ops.wm.open_mainfile(filepath=BLEND)
    scene = bpy.context.scene
    for o in bpy.data.objects:
        if o.type == "MESH" and not (o.get("pj_part") or o.get("pj_prenda")):
            o.hide_render = True
    ctr = Vector((0, 0, 0.93))

    def want(n):
        return not only or n in only
    if want("tpose"):
        C1.setup(scene)
        span = 1.9 * 1.06
        ps = [C1.shot(scene, C1.cam(scene, ctr + d * 20, ctr, ortho=span), f"{pre}_t{k}.png")
              for k, d in enumerate((Vector((0, -1, 0)), Vector((1, 0, 0)), Vector((0, 1, 0))))]
        C1.sheet(ps, f"{pre}_tpose.png", ["FRENTE (-Y)", "LADO (+X)", "ESPALDA (+Y)"])
    if want("iso"):
        C1.setup(scene, (1200, 900))
        ps = [C1.shot(scene, C1.cam(scene, ctr + C1.CAM_BACK * 60, ctr, ortho=o), f"{pre}_i{k}.png")
              for k, o in enumerate((6.0, 2.5))]
        C1.sheet(ps, f"{pre}_iso.png", ["CAM_Iso ortho 6 (escala de juego)", "CAM_Iso ortho 2,5 (detalle)"])
    if want("ocultar"):
        C1.setup(scene, (600, 900))
        eye = ctr + Vector((1.6, -3.4, 0.55))
        ps, labs = [], []
        for k, hid in enumerate((None,) + PIECES):
            set_hidden({hid} if hid else set())
            ps.append(C1.shot(scene, C1.cam(scene, eye, ctr, lens=45), f"{pre}_o{k}.png"))
            labs.append("TODO PUESTO" if hid is None else f"SIN {hid}")
        set_hidden(set())
        C1.sheet(ps, f"{pre}_ocultar.png", labs, cols=4)
    if want("detalle"):
        C1.setup(scene, (900, 900))
        shots = [
            (Vector((0.55, 0.75, 1.80)), Vector((0, 0.04, 1.62)), 50, "PELO Y CAPUCHA POR DETRAS"),
            (Vector((0.35, -0.95, 1.12)), Vector((0.02, -0.05, 1.05)), 50, "CINTURON, BOLSITAS Y FRASCOS"),
            (Vector((0.18, -0.65, 1.42)), Vector((0, -0.12, 1.36)), 60, "COLGANTE (EMISION 1,0 #8FD0FF)"),
            (Vector((0.6, -1.2, 0.45)), Vector((0.05, -0.05, 0.3)), 50, "DOBLADILLO BORDADO Y BOTAS"),
        ]
        ps = [C1.shot(scene, C1.cam(scene, e, t, lens=l), f"{pre}_d{k}.png") for k, (e, t, l, _x) in enumerate(shots)]
        C1.sheet(ps, f"{pre}_detalle.png", [s[3] for s in shots], cols=2)
    if want("atlas"):
        from PIL import Image, ImageDraw
        td = os.path.join(REPO, "textures", "personajes", "sanador")
        S = Image.new("RGB", (1540, 1040), (107, 107, 107))
        d = ImageDraw.Draw(S)
        for i, (fn, lab) in enumerate((("albedo_1k", "ALBEDO (alfa sobre gris)"), ("normal_1k", "NORMAL"),
                                       ("orm_1k", "ORM"), ("emision_1k", "EMISION"))):
            im = Image.open(os.path.join(td, f"sanador_atlas_{fn}.png"))
            if im.mode == "RGBA":
                bg = Image.new("RGBA", im.size, (107, 107, 107, 255))
                im = Image.alpha_composite(bg, im)
            im = im.convert("RGB").resize((500, 500))
            x, y = 10 + (i % 2) * 765, 10 + (i // 2) * 515
            S.paste(im, (x, y))
            d.text((x + 8, y + 8), lab, fill=(255, 255, 255))
        S.save(f"{pre}_atlas.png")


if __name__ == "__main__":
    main()
    os._exit(0)
