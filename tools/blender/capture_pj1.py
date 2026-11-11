"""
CONCORDIA - capturas del PJ1 (cuerpo base del elfo). Fondo gris neutro, luz uniforme (cielo gris + luz de relleno
suave), camaras ortograficas.
  pj1_tpose      frente, lado y espalda en una hoja (ortograficas)
  pj1_cara       cara y orejas de cerca: frente, tres cuartos y perfil
  pj1_iso        CAM_Iso (direccion de la ciudad, ortho 6) con el humano de referencia a la izquierda
  pj1_piezas     las 6 piezas del cuerpo en colores (frente y espalda) para revisar las costuras
  pj1_texturas   hoja con las texturas horneadas (albedo A y B, normal, ORM, ojos)
python capture_pj1.py <blend> <prefijo_salida> [nombres...]   (escribe <prefijo>_tpose.png, _cara.png, ...)
"""

import math
import os
import sys

import bpy
from mathutils import Vector

CAM_BACK = Vector((0.577, -0.577, 0.577))     # direccion de CAM_Iso (como en la ciudad)
GREY = (0.42, 0.42, 0.42, 1.0)
PARTS = {"Head": (0.85, 0.55, 0.45), "Torso": (0.45, 0.65, 0.85), "Arms": (0.55, 0.8, 0.5),
         "Hands": (0.9, 0.85, 0.4), "Legs": (0.75, 0.5, 0.8), "Feet": (0.5, 0.8, 0.8), "Eyes": (0.95, 0.95, 0.95)}


def setup(scene, res=(900, 1200)):
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = 24
    scene.cycles.use_denoising = True
    scene.render.resolution_x, scene.render.resolution_y = res
    scene.view_settings.view_transform = "AgX"
    w = bpy.data.worlds.new("PJ_World")
    w.use_nodes = True
    bg = w.node_tree.nodes["Background"]
    bg.inputs[0].default_value = GREY
    bg.inputs[1].default_value = 1.0
    scene.world = w
    for k, (rot, e) in enumerate((((55, 0, 30), 1.6), ((60, 0, 210), 0.6))):      # clave y relleno suaves
        ld = bpy.data.lights.new(f"PJ_Sun{k}", "SUN")
        ld.energy = e
        ld.angle = math.radians(20)
        lo = bpy.data.objects.new(f"PJ_Sun{k}", ld)
        lo.rotation_euler = [math.radians(a) for a in rot]
        scene.collection.objects.link(lo)


def cam(scene, eye, target, ortho=None, lens=85):
    cd = bpy.data.cameras.new("PJ_Cam")
    if ortho:
        cd.type, cd.ortho_scale = "ORTHO", ortho
    else:
        cd.lens = lens
    cd.clip_start, cd.clip_end = 0.01, 500
    c = bpy.data.objects.new("PJ_Cam", cd)
    scene.collection.objects.link(c)
    c.location = eye
    c.rotation_euler = (Vector(target) - Vector(eye)).to_track_quat("-Z", "Y").to_euler()
    scene.camera = c
    return c


def shot(scene, c, path):
    scene.render.filepath = path
    bpy.ops.render.render(write_still=True)
    bpy.data.objects.remove(c)
    return path


def sheet(paths, out, labels=None, cols=None):
    from PIL import Image, ImageDraw
    ims = [Image.open(p).convert("RGB") for p in paths]
    cols = cols or len(ims)
    rows = (len(ims) + cols - 1) // cols
    w, h = ims[0].size
    S = Image.new("RGB", (w * cols, h * rows), (107, 107, 107))
    d = ImageDraw.Draw(S)
    for i, im in enumerate(ims):
        x, y = (i % cols) * w, (i // cols) * h
        S.paste(im, (x, y))
        if labels:
            d.text((x + 12, y + 10), labels[i], fill=(255, 255, 255))
    S.save(out)
    for p in paths:
        os.remove(p)


def flat_parts(objs):
    for o in objs:
        key = next((k for k in PARTS if k in o.name), None)
        m = bpy.data.materials.new(f"TMP_{o.name}")
        m.diffuse_color = (*(PARTS[key] if key else (0.6, 0.6, 0.6)), 1)
        m.use_nodes = True
        m.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = m.diffuse_color
        o.data.materials.clear()
        o.data.materials.append(m)


def main():
    a = sys.argv[sys.argv.index("--") + 1:]
    blend, pre, only = a[0], a[1], set(a[2:])
    bpy.ops.wm.open_mainfile(filepath=blend)
    scene = bpy.context.scene
    body = [o for o in bpy.data.objects if o.type == "MESH" and o.get("pj_part") and not o.hide_render]
    ref = [o for o in bpy.data.objects if o.type == "MESH" and o.get("pj_ref")]
    for o in bpy.data.objects:
        if o.type == "MESH" and o not in body and o not in ref:
            o.hide_render = True
    vs = [o.matrix_world @ v.co for o in body for v in o.data.vertices]
    lo_, hi_ = Vector([min(v[i] for v in vs) for i in range(3)]), Vector([max(v[i] for v in vs) for i in range(3)])
    ctr, H = (lo_ + hi_) / 2, hi_.z - lo_.z
    head = Vector((0, 0, hi_.z - 0.13))

    def want(n):
        return not only or n in only
    if want("pj1_tpose") or want("pj1_piezas"):
        for o in ref:
            o.hide_render = True
    if want("pj1_tpose"):
        setup(scene)
        span = max(hi_.x - lo_.x, H) * 1.06
        ps = []
        for k, d in enumerate((Vector((0, -1, 0)), Vector((1, 0, 0)), Vector((0, 1, 0)))):
            ps.append(shot(scene, cam(scene, ctr + d * 20, ctr, ortho=span), f"{pre}_t{k}.png"))
        sheet(ps, f"{pre}_tpose.png", ["FRENTE (-Y)", "LADO (+X, izquierda del personaje)", "ESPALDA (+Y)"])
    if want("pj1_cara"):
        setup(scene, (900, 900))
        ps = []
        for k, d in enumerate((Vector((0, -1, 0.0)), Vector((0.7, -0.7, 0.05)), Vector((1, 0, 0.0)),
                               Vector((0.5, 0.86, 0.05)))):
            ps.append(shot(scene, cam(scene, head + d.normalized() * 6, head, ortho=0.42), f"{pre}_c{k}.png"))
        sheet(ps, f"{pre}_cara.png", ["FRENTE", "TRES CUARTOS", "PERFIL", "OREJA POR DETRAS"], cols=2)
    if want("pj1_iso"):
        for o in ref:
            o.hide_render = False
        setup(scene, (1200, 900))
        tgt = Vector((-0.6 if ref else 0.0, 0, 0.95))
        shot(scene, cam(scene, tgt + CAM_BACK * 60, tgt, ortho=6.0), f"{pre}_iso.png")
        for o in ref:
            o.hide_render = True
    if want("pj1_texturas"):
        from PIL import Image, ImageDraw
        tdir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "textures", "personajes", "elfo")
        names = [("elfo_m_albedo_abedul_1k.png", "ALBEDO A abedul"), ("elfo_m_albedo_corteza_1k.png", "ALBEDO B corteza"),
                 ("elfo_m_normal_1k.png", "NORMAL (OpenGL)"), ("elfo_m_orm_1k.png", "ORM (R AO, G rugosidad, B metal)"),
                 ("elfo_m_ojos_albedo_256.png", "OJOS 256")]
        S = Image.new("RGB", (1500, 1000), (107, 107, 107))
        d = ImageDraw.Draw(S)
        for i, (fn, lab) in enumerate(names):
            im = Image.open(os.path.join(tdir, fn)).convert("RGB").resize((480, 480))
            x, y = 10 + (i % 3) * 495, 10 + (i // 3) * 495
            S.paste(im, (x, y))
            d.text((x + 8, y + 8), lab, fill=(255, 255, 255))
        S.save(f"{pre}_texturas.png")
    if want("pj1_piezas"):
        flat_parts(body)
        setup(scene)
        span = max(hi_.x - lo_.x, H) * 1.06
        ps = [shot(scene, cam(scene, ctr + d * 20, ctr, ortho=span), f"{pre}_p{k}.png")
              for k, d in enumerate((Vector((0, -1, 0)), Vector((0, 1, 0))))]
        sheet(ps, f"{pre}_piezas.png", ["PIEZAS - FRENTE", "PIEZAS - ESPALDA"])


if __name__ == "__main__":
    main()
    os._exit(0)
