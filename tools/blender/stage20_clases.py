"""
CONCORDIA - Etapa 20 (E7): distrito de las Clases.

  Plantilla SALON DE CLASE (18 x 14): piedra sobria (Toledo), portico de 4 columnas con fronton, teja ocre, y partes
  ajustables por clase (CLASS_PRESETS, CLASE_01..CLASE_08, nombres genericos para renombrar):
    - estandarte de 2.5 x 6 m (objeto aparte, UV 0..1 para el emblema, una textura por clase, color tierra apagado);
      un segundo estandarte en el hastial trasero para que se lea desde CAM_Iso cuando la fachada mira al otro lado
    - remate sobre el fronton (forma por clase)
    - 2 modelos de props de clase en peanas a la entrada + 3 MARKER_ClassProp_Slot_01..03
  N_CLASES es un parametro (<= numero de parcelas MARKER_Bld_SalonClase_*).
  Plaza de las Armas: DUMMY_Straw (3 variantes, MARKER_DamageNumber en el pecho), blancos, postes de prueba, valla baja.
  Casa de Reposicion "El Remiendo": extras (perchas de armaduras remendadas, espadas pulidas, cajones de botas y capas,
  letrero con parche cosido).
Marco local: +Y = door_direction, base a z = 0 sobre el pad.
"""

import colorsys
import math
import os
import random

import bpy  # noqa: F401,I001
from mathutils import Matrix, Vector

import bld_kit as K
import stage16_landmarks as L
import stage18_mercado as M
import stage19_oficios as O

ST, LIGHT, GRAY = "MAT_Limestone_Worn", "MAT_Limestone_Light", "MAT_Wall_Gray"
WOOD, IRON, BRONZE, WARM, SHARD = K.M_WOOD, K.M_IRON, "MAT_Bronze_Aged", "MAT_Window_Warm", "MAT_Shard_Blue"
STRAW = "MAT_Straw"
CLOTH = K.M_CLOTH
REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
N_CLASES = 8

# --------------------------------------------------------------------------- presets (renombrables)
CLASS_PRESETS = {
    "CLASE_01": {"color": "#866E5C", "emblem": "chevron", "finial": "spear", "props": ("weapon_rack", "shield_stand")},
    "CLASE_02": {"color": "#6E7480", "emblem": "circle", "finial": "orb", "props": ("lectern_book", "scroll_basket")},
    "CLASE_03": {"color": "#6F765A", "emblem": "triangle", "finial": "arrow", "props": ("bow_rack", "quiver_stand")},
    "CLASE_04": {"color": "#77707E", "emblem": "star", "finial": "star", "props": ("staff_stand", "crystal_pedestal")},
    "CLASE_05": {"color": "#7E6A52", "emblem": "square", "finial": "hammer", "props": ("mace_stand", "anvil_hammer")},
    "CLASE_06": {"color": "#6C7A68", "emblem": "diamond", "finial": "flame", "props": ("herb_table", "mortar_pot")},
    "CLASE_07": {"color": "#998A6A", "emblem": "crescent", "finial": "crescent", "props": ("lute_stand", "drum")},
    "CLASE_08": {"color": "#5E5A56", "emblem": "dagger", "finial": "pyramid", "props": ("dagger_table", "cloak_hook")},
}


def _hex(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))


def _lin(c):
    return ((c + 0.055) / 1.055) ** 2.4 if c > 0.04045 else c / 12.92


def preset_saturation(key):
    return colorsys.rgb_to_hsv(*_hex(CLASS_PRESETS[key]["color"]))[1]


# --------------------------------------------------------------------------- materiales y texturas de estandarte
def banner_texture(key, size=(512, 1024)):
    """Textura del estandarte: color tierra apagado, orla clara y emblema generico (placeholder) de la clase."""
    from PIL import Image, ImageDraw
    p = CLASS_PRESETS[key]
    base = tuple(int(c * 255) for c in _hex(p["color"]))
    light = tuple(min(255, int(c * 1.32 + 20)) for c in base)
    dark = tuple(int(c * 0.72) for c in base)
    W, H = size
    im = Image.new("RGB", size, base)
    d = ImageDraw.Draw(im)
    b = 26
    d.rectangle((b, b, W - b, H - b), outline=light, width=14)
    d.rectangle((b + 30, b + 30, W - b - 30, H - b - 30), outline=dark, width=4)
    cx, cy, r = W // 2, int(H * 0.38), 150
    e = p["emblem"]
    if e == "chevron":
        for k in (0, 1):
            y = cy - 60 + k * 110
            d.polygon([(cx - r, y), (cx, y + 90), (cx + r, y), (cx + r, y + 50), (cx, y + 140), (cx - r, y + 50)], fill=light)
    elif e == "circle":
        d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=light, width=34)
        d.ellipse((cx - 40, cy - 40, cx + 40, cy + 40), fill=light)
    elif e == "triangle":
        d.polygon([(cx, cy - r), (cx + r, cy + r * 0.8), (cx - r, cy + r * 0.8)], fill=light)
    elif e == "star":
        pts = []
        for i in range(10):
            a = -math.pi / 2 + math.pi * i / 5
            rr = r if i % 2 == 0 else r * 0.42
            pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
        d.polygon(pts, fill=light)
    elif e == "square":
        d.rectangle((cx - r * 0.8, cy - r * 0.8, cx + r * 0.8, cy + r * 0.8), outline=light, width=34)
        d.rectangle((cx - 45, cy - 45, cx + 45, cy + 45), fill=light)
    elif e == "diamond":
        d.polygon([(cx, cy - r), (cx + r * 0.7, cy), (cx, cy + r), (cx - r * 0.7, cy)], fill=light)
    elif e == "crescent":
        d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=light)
        d.ellipse((cx - r * 0.55, cy - r * 1.05, cx + r * 1.25, cy + r * 0.75), fill=base)
    elif e == "dagger":
        d.polygon([(cx, cy - r * 1.2), (cx + 32, cy + r * 0.6), (cx - 32, cy + r * 0.6)], fill=light)
        d.rectangle((cx - 90, cy + r * 0.6, cx + 90, cy + r * 0.6 + 26), fill=light)
        d.rectangle((cx - 16, cy + r * 0.6 + 26, cx + 16, cy + r * 1.05), fill=light)
    d.rectangle((b + 50, int(H * 0.74), W - b - 50, int(H * 0.74) + 10), fill=light)
    out_dir = os.path.join(REPO, "textures", "concordia", "MAT_Banner")
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, f"concordia_banner_{key.lower()}_albedo.png")
    im.save(path, optimize=True)
    return path


def ensure_materials(keys):
    out = {}
    if STRAW not in bpy.data.materials:
        m = bpy.data.materials.new(STRAW)
        m.use_nodes = True
        b = m.node_tree.nodes["Principled BSDF"]
        b.inputs["Base Color"].default_value = (_lin(0.651), _lin(0.580), _lin(0.447), 1)         # #A69472
        b.inputs["Roughness"].default_value = 0.95
        m["note"] = "paja de los maniquies #A69472 (saturacion 0.31)"
        out[STRAW] = "creado"
    for key in keys:
        name = f"MAT_Banner_{key}"
        path = banner_texture(key)
        m = bpy.data.materials.get(name)
        if m is None:
            m = bpy.data.materials.new(name)
            m.use_nodes = True
            nt = m.node_tree
            b = nt.nodes["Principled BSDF"]
            t = nt.nodes.new("ShaderNodeTexImage")
            t.name = "Albedo"
            nt.links.new(t.outputs["Color"], b.inputs["Base Color"])
            b.inputs["Roughness"].default_value = 0.9
            m.use_backface_culling = False
        img = bpy.data.images.load(path, check_existing=True)
        img.reload()
        m.node_tree.nodes["Albedo"].image = img
        m["preset"] = key
        m["color"] = CLASS_PRESETS[key]["color"]
        m["note"] = "estandarte: textura por clase (emblema generico de placeholder), UV 0..1, dos caras"
        out[name] = {"texture": os.path.relpath(path, REPO), "color": CLASS_PRESETS[key]["color"],
                     "saturation": round(preset_saturation(key), 3)}
    return out


# --------------------------------------------------------------------------- remates (finials) sobre el fronton
def finial(mb, kind, x, y, z):
    b = BRONZE
    mb.box((x - 0.35, y - 0.35, z - 0.05), (x + 0.35, y + 0.35, z + 0.25), ST)
    z += 0.25
    if kind == "spear":
        mb.rod((x, y, z), (x, y, z + 1.3), 0.04, b)
        L._ring_frustum(mb, x, y, 0.14, 0.0, z + 1.3, z + 1.9, 4, b)
    elif kind == "orb":
        O.bulb(mb, x, y, z + 0.45, 0.4, b)
        mb.rod((x, y, z + 0.85), (x, y, z + 1.3), 0.03, b)
    elif kind == "arrow":
        mb.rod((x, y, z), (x, y, z + 1.6), 0.035, b)
        L._ring_frustum(mb, x, y, 0.16, 0.0, z + 1.6, z + 2.0, 3, b)
        for s in (-1, 1):
            mb.rod((x, y, z + 0.1), (x + s * 0.18, y, z + 0.35), 0.02, b)
    elif kind == "star":
        mb.rod((x, y, z), (x, y, z + 0.6), 0.04, b)
        for k in range(4):
            a = math.pi / 4 * k
            mb.rod((x - 0.45 * math.cos(a), y, z + 1.05 - 0.45 * math.sin(a)), (x + 0.45 * math.cos(a), y, z + 1.05 + 0.45 * math.sin(a)),
                   0.04, b)
    elif kind == "hammer":
        mb.rod((x, y, z), (x, y, z + 1.1), 0.05, WOOD)
        mb.box((x - 0.4, y - 0.15, z + 1.1), (x + 0.4, y + 0.15, z + 1.4), b)
    elif kind == "flame":
        L._ring_frustum(mb, x, y, 0.32, 0.18, z, z + 0.4, 6, b)
        L._ring_frustum(mb, x, y, 0.18, 0.0, z + 0.4, z + 1.3, 6, b)
    elif kind == "crescent":
        mb.rod((x, y, z), (x, y, z + 0.5), 0.04, b)
        arc = [(x + 0.5 * math.cos(math.radians(200 + 140 * i / 6)), z + 1.0 + 0.5 * math.sin(math.radians(200 + 140 * i / 6)))
               for i in range(7)]
        L.rod_path(mb, [(px, pz) for px, pz in arc], y, 0.06, b)
    else:                                                  # pyramid
        L._ring_frustum(mb, x, y, 0.4, 0.0, z, z + 1.2, 4, b)


# --------------------------------------------------------------------------- props de clase (modelos)
def class_prop(mb, kind):
    w, i, b = WOOD, IRON, BRONZE
    if kind == "weapon_rack":
        for x in (-0.6, 0.6):
            mb.box((x - 0.05, -0.05, 0.0), (x + 0.05, 0.05, 1.5), w, skip=("z-",))
        mb.box((-0.65, -0.04, 1.2), (0.65, 0.04, 1.28), w)
        for k in range(4):
            x = -0.45 + 0.3 * k
            mb.box((x - 0.02, 0.06, 0.1), (x + 0.02, 0.09, 1.35), i)
    elif kind == "shield_stand":
        mb.rod((0, -0.2, 0), (0, 0.0, 1.0), 0.04, w)
        pts = [(0.4 * math.cos(2 * math.pi * k / 10), 0.05, 1.0 + 0.4 * math.sin(2 * math.pi * k / 10)) for k in range(10)]
        mb.face(pts, b, nrm=(0, 1, 0))
        mb.face(pts[::-1], w, nrm=(0, -1, 0))
    elif kind == "lectern_book":
        mb.box((-0.15, -0.15, 0.0), (0.15, 0.15, 1.0), w, skip=("z-",))
        mb.face([(-0.35, -0.25, 1.0), (0.35, -0.25, 1.0), (0.35, 0.2, 1.2), (-0.35, 0.2, 1.2)], w, nrm=(0, -0.4, 1))
        mb.face([(-0.3, -0.2, 1.03), (0.3, -0.2, 1.03), (0.3, 0.15, 1.22), (-0.3, 0.15, 1.22)], LIGHT, nrm=(0, -0.4, 1))
    elif kind == "scroll_basket":
        L._ring_frustum(mb, 0, 0, 0.3, 0.36, 0.0, 0.5, 8, w)
        for k in range(5):
            a = 2 * math.pi * k / 5
            O.cyl_axis(mb, (0.12 * math.cos(a), 0.12 * math.sin(a), 0.2), (0.15 * math.cos(a), 0.15 * math.sin(a), 0.9), 0.04, 6, LIGHT)
    elif kind == "bow_rack":
        for x in (-0.5, 0.5):
            mb.box((x - 0.05, -0.05, 0.0), (x + 0.05, 0.05, 1.6), w, skip=("z-",))
        mb.box((-0.55, -0.04, 1.5), (0.55, 0.04, 1.58), w)
        for x in (-0.25, 0.15):
            arc = [(x + 0.18 * math.sin(math.pi * k / 6), 0.25 + 1.2 * k / 6) for k in range(7)]
            L.rod_path(mb, arc, 0.08, 0.02, w)
    elif kind == "quiver_stand":
        O.cyl(mb, 0, 0, 0.14, 0.0, 0.8, 8, CLOTH[2], caps=False)
        for k in range(6):
            a = 2 * math.pi * k / 6
            mb.rod((0.06 * math.cos(a), 0.06 * math.sin(a), 0.7), (0.08 * math.cos(a), 0.08 * math.sin(a), 1.3), 0.01, w)
    elif kind == "staff_stand":
        mb.box((-0.25, -0.25, 0.0), (0.25, 0.25, 0.15), w)
        for x in (-0.1, 0.1):
            mb.rod((x, 0, 0.15), (x * 1.5, 0, 1.9), 0.03, w)
            O.bulb(mb, x * 1.5, 0, 2.0, 0.08, SHARD)
    elif kind == "crystal_pedestal":
        mb.box((-0.3, -0.3, 0.0), (0.3, 0.3, 0.8), ST, skip=("z-",))
        O.bulb(mb, 0, 0, 1.05, 0.22, SHARD)
    elif kind == "mace_stand":
        mb.box((-0.3, -0.2, 0.0), (0.3, 0.2, 0.12), w)
        for x in (-0.15, 0.15):
            mb.rod((x, 0, 0.12), (x, 0, 1.0), 0.03, w)
            O.bulb(mb, x, 0, 1.1, 0.12, i)
    elif kind == "anvil_hammer":
        O.anvil(mb)
        mb.rod((0.0, 0.0, 0.98), (0.3, 0.1, 1.0), 0.025, w)
        mb.box((-0.05, 0.05, 0.98), (0.05, 0.15, 1.08), i)
    elif kind == "herb_table":
        mb.box((-0.6, -0.3, 0.75), (0.6, 0.3, 0.8), w)
        for x in (-0.5, 0.5):
            mb.box((x - 0.04, -0.25, 0.0), (x + 0.04, 0.25, 0.75), w, skip=("z-",))
        for x in (-0.3, 0.0, 0.3):
            L._ring_frustum(mb, x, 0, 0.08, 0.1, 0.8, 0.95, 6, ST)
            O.clump(mb, x, 0, 0.95, 0.1, 0.18)
    elif kind == "mortar_pot":
        L._ring_frustum(mb, 0, 0, 0.25, 0.3, 0.0, 0.5, 8, ST, cap_top=True)
        mb.rod((0, 0, 0.5), (0.15, 0.05, 0.85), 0.03, ST)
    elif kind == "lute_stand":
        mb.rod((0, -0.2, 0), (0, 0, 0.9), 0.03, w)
        O.bulb(mb, 0, 0.05, 0.9, 0.22, w)
        mb.box((-0.03, 0.03, 1.05), (0.03, 0.08, 1.6), w)
    elif kind == "drum":
        O.cyl(mb, 0, 0, 0.35, 0.0, 0.6, 10, w, caps=False)
        mb.face([(0.35 * math.cos(2 * math.pi * k / 10), 0.35 * math.sin(2 * math.pi * k / 10), 0.6) for k in range(10)], LIGHT,
                nrm=(0, 0, 1))
    elif kind == "dagger_table":
        mb.box((-0.5, -0.3, 0.75), (0.5, 0.3, 0.8), w)
        for x in (-0.4, 0.4):
            mb.box((x - 0.04, -0.25, 0.0), (x + 0.04, 0.25, 0.75), w, skip=("z-",))
        for k in range(3):
            x = -0.25 + 0.25 * k
            mb.box((x - 0.02, -0.18, 0.8), (x + 0.02, 0.12, 0.82), i)
            mb.box((x - 0.06, 0.12, 0.8), (x + 0.06, 0.14, 0.83), w)
    else:                                                    # cloak_hook
        mb.box((-0.05, -0.05, 0.0), (0.05, 0.05, 1.8), w, skip=("z-",))
        q = [(-0.3, 0.07, 1.7), (0.3, 0.07, 1.7), (0.4, 0.12, 0.6), (-0.4, 0.12, 0.6)]
        mb.face(q, CLOTH[1], nrm=(0, 1, 0))
        mb.face(q[::-1], CLOTH[1], nrm=(0, -1, 0))


# --------------------------------------------------------------------------- plantilla del salon
class SAL:
    W, D = 18.0, 14.0
    YP = 3.4                  # muro frontal del cuerpo (el portico va de YP a 6.4)
    YF = 6.4                  # frente del portico
    H = 7.0
    PITCH = 26.0
    COLS = (-6.9, -2.3, 2.3, 6.9)
    SLOTS = ((-4.6, 4.6), (4.6, 4.6), (-8.0, 4.6))


def salon_meshes(rng, preset_key):
    S = SAL
    hw, hd = S.W / 2, S.D / 2
    body, roof = K.MB(), K.MB()
    p = CLASS_PRESETS[preset_key]
    # basamento y escalinata (dentro de la huella)
    body.box((-hw, -hd, 0.0), (hw, S.YF, 0.45), ST, skip=("z-",))
    for k in range(3):
        y0 = S.YF + 0.2 * k
        body.box((-hw + 0.6, y0, 0.0), (hw - 0.6, y0 + 0.2, 0.45 - 0.15 * (k + 1) + 0.15), ST, skip=("z-",))
    # muros
    for side in ("+Y", "-Y", "+X", "-X"):
        Y = S.YP if side == "+Y" else hd
        body.push(L.frame(side, hw, Y))
        if side in ("+Y", "-Y"):
            ua, ub = -hw, hw
        elif side == "+X":                    # u = -y, entre las caras interiores de los muros frontal y trasero
            ua, ub = -(S.YP - 0.7), hd - 0.7
        else:                                 # u = +y
            ua, ub = -hd + 0.7, S.YP - 0.7
        top = [(ub, S.H), (ua, S.H)]
        holes = []
        if side == "+Y":
            outer = L.with_door(ua, ub, L.lancet(0.0, 2.2, 0.0, 3.8), top)
            wins = (-5.2, 5.2)
        elif side == "-Y":
            outer = [(ua, 0), (ub, 0)] + top
            wins = (-5.2, 5.2)
        else:
            outer = [(ua, 0), (ub, 0)] + top
            wins = [u for u in ((-4.6, -1.2, 2.2) if side == "-X" else (-2.2, 1.2, 4.6))]
        holes = [M.rect(u, 3.9, 1.2, 2.8) for u in wins]
        L.plate(body, outer, holes, 0.7, ST)
        for u in wins:
            M.barred_rect_fill(body, u, 3.9, 1.2, 2.8, y_glass=-0.45, bars=2)
        body.box((ua - 0.1, -0.02, S.H - 0.3), (ub + 0.1, 0.18, S.H), ST, skip=("y-",))
        if side == "+Y":
            L.door_leaves(body, 2.2, 3.8, -0.5, -0.4, straps=3)
        body.pop()
    # portico: 4 columnas, entablamento, vigas laterales y techo
    for x in S.COLS:
        y = S.YF - 0.5
        body.box((x - 0.42, y - 0.42, 0.45), (x + 0.42, y + 0.42, 0.7), ST, skip=("z-",))
        L._ring_frustum(body, x, y, 0.32, 0.28, 0.7, S.H - 0.95, 10, LIGHT)
        body.box((x - 0.45, y - 0.45, S.H - 0.95), (x + 0.45, y + 0.45, S.H - 0.7), ST)
    body.box((-hw, S.YF - 1.0, S.H - 0.7), (hw, S.YF, S.H), ST)
    for s in (-1, 1):
        a, b = sorted((s * hw, s * (hw - 0.5)))
        body.box((a, S.YP, S.H - 0.7), (b, S.YF - 1.0, S.H), ST, skip=("y-", "y+"))
    body.face([(-hw, S.YP, S.H - 0.7), (hw, S.YP, S.H - 0.7), (hw, S.YF - 1.0, S.H - 0.7), (-hw, S.YF - 1.0, S.H - 0.7)], ST,
              nrm=(0, 0, -1))
    # fronton y hastial trasero
    t = math.tan(math.radians(S.PITCH))
    ridge = S.H + (hw + 0.5) * t - 0.5 * t
    body.push(Matrix.Translation((0, S.YF - 0.3, 0)))
    body.prism([(-hw, S.H), (hw, S.H), (0.0, ridge)], -0.3, 0.3, ST)
    body.pop()
    for s in (-1, 1):
        body.rod((s * (hw + 0.15), S.YF + 0.05, S.H + 0.05), (0, S.YF + 0.05, ridge + 0.12), 0.16, LIGHT)
    body.box((-hw - 0.15, S.YF - 0.6, S.H - 0.05), (hw + 0.15, S.YF + 0.2, S.H + 0.15), LIGHT)
    body.push(Matrix.Translation((0, -hd + 0.35, 0)))
    body.prism([(-hw, S.H), (hw, S.H), (0.0, ridge - 0.1)], -0.35, 0.35, ST)
    body.pop()
    finial(body, p["finial"], 0.0, S.YF - 0.3, ridge + 0.05)
    # peanas de los slots
    for x, y in S.SLOTS:
        body.box((x - 0.45, y - 0.45, 0.45), (x + 0.45, y + 0.45, 0.85), ST, skip=("z-",))
    patches = L.stone_patches(body, [(L.frame("-Y", hw, hd), -8.0, 8.0, 0.8, 3.0), (L.frame("+X", hw, hd), -3.0, 6.0, 0.8, 2.4)],
                              rng, rng.randint(2, 3))
    body.finish()
    # cubierta a dos aguas (cumbrera a lo largo de Y), alero 0.5
    roof.push(Matrix.Rotation(math.pi / 2, 4, "Z"))
    ye = hw + 0.5
    ze = S.H - 0.5 * t
    for sgn in (-1, 1):
        L.tile_slope(roof, -hd - 0.4, S.YF + 0.25, sgn * ye, 0.0, ze, ridge, rng, seg=3.6)
        roof.face([(-hd - 0.4, sgn * ye, ze - 0.02), (-hd - 0.4, 0, ridge - 0.02), (S.YF + 0.25, 0, ridge - 0.02),
                   (S.YF + 0.25, sgn * ye, ze - 0.02)], WOOD, nrm=(0, 0, -1))
        roof.box((-hd - 0.4, sgn * ye - 0.03, ze - 0.18), (S.YF + 0.25, sgn * ye + 0.03, ze), WOOD)
    roof.box((-hd - 0.4, -0.13, ridge - 0.02), (S.YF + 0.25, 0.13, ridge + 0.14), K.M_ROOF_B)
    reps = L.roof_repairs(roof, -hd, S.YF, ye, ze, ridge, rng, rng.randint(2, 3))
    roof.pop()
    roof.finish()
    mass = [("box", (-hw, -hd, 0.0), (hw, S.YP, S.H)), ("box", (-hw, S.YP, S.H - 0.7), (hw, S.YF, S.H)),
            ("box", (-hw, S.YF - 0.9, 0.45), (-hw + 0.9, S.YF, S.H)), ("box", (hw - 0.9, S.YF - 0.9, 0.45), (hw, S.YF, S.H)),
            ("box", (-hw, -hd, 0.0), (hw, S.YF + 0.6, 0.45))]
    return body, roof, {"ridge_m": round(ridge, 2), "stone_patches": patches, "roof_repairs": reps,
                        "door": (0.0, S.YP, 0.0), "interior": ((0.0, (S.YP - hd) / 2), (S.W - 1.4, S.YP + hd - 1.4, S.H)),
                        "banner_front_top": ridge - 0.9, "banner_back_top": ridge - 1.3}, mass, ridge


def banner(mb_unused=None, w=2.5, h=6.0, tip=0.6):
    """Malla del estandarte (cara +Y, origen en el centro del borde superior), con UV 0..1 y punta inferior; barra y
    remates de hierro aparte (en el cuerpo)."""
    import bmesh
    bm = bmesh.new()
    pts = [(-w / 2, 0.0, 0.0), (w / 2, 0.0, 0.0), (w / 2, 0.0, -h + tip), (0.0, 0.0, -h), (-w / 2, 0.0, -h + tip)]
    vs = [bm.verts.new(p) for p in pts]
    f = bm.faces.new(vs)
    f.normal_update()
    if f.normal.y < 0:
        f.normal_flip()
    uv = bm.loops.layers.uv.new("UVWorld")
    for lp in f.loops:
        x, _, z = lp.vert.co
        lp[uv].uv = ((x + w / 2) / w, (z + h) / h)
    return bm


# --------------------------------------------------------------------------- Plaza de las Armas
def dummy_straw(mb, variant):
    """Maniqui de paja y madera (estatico): poste, cuerpo de paja, cabeza de saco, brazos; A cruz, B escudo, C yelmo."""
    mb.box((-0.35, -0.35, 0.0), (0.35, 0.35, 0.12), WOOD)
    mb.rod((0, 0, 0.12), (0, 0, 2.0), 0.06, WOOD)
    L._ring_frustum(mb, 0, 0, 0.22, 0.3, 0.75, 1.15, 8, STRAW)
    L._ring_frustum(mb, 0, 0, 0.3, 0.26, 1.15, 1.55, 8, STRAW)
    L._ring_frustum(mb, 0, 0, 0.26, 0.12, 1.55, 1.68, 8, STRAW)
    for z in (0.95, 1.4):
        L._ring_frustum(mb, 0, 0, 0.31, 0.31, z - 0.03, z + 0.03, 8, "MAT_Cloth_Patch_C")
    O.bulb(mb, 0, 0, 1.85, 0.17, "MAT_Cloth_Patch_B")
    mb.rod((-0.75, 0, 1.45), (0.75, 0, 1.45), 0.045, WOOD)
    for s in (-1, 1):
        O.cyl_axis(mb, (s * 0.35, 0, 1.45), (s * 0.72, 0, 1.45), 0.09, 6, STRAW)
    if variant == "B":
        pts = [(0.75 + 0.02, 0.35 * math.cos(2 * math.pi * k / 10), 1.4 + 0.35 * math.sin(2 * math.pi * k / 10)) for k in range(10)]
        mb.face(pts, WOOD, nrm=(1, 0, 0))
        mb.face(pts[::-1], WOOD, nrm=(-1, 0, 0))
    elif variant == "C":
        L._ring_frustum(mb, 0, 0, 0.21, 0.17, 1.82, 2.08, 8, IRON, cap_top=True)
        mb.rod((0.72, 0, 1.45), (0.9, 0.15, 0.6), 0.03, IRON)


def test_post(mb):
    """Poste de prueba (pell): tronco con anillos de cuerda y muescas."""
    O.cyl(mb, 0, 0, 0.18, 0.0, 2.0, 8, WOOD)
    for z in (0.9, 1.3, 1.7):
        O.cyl(mb, 0, 0, 0.2, z - 0.04, z + 0.04, 8, "MAT_Cloth_Patch_C", caps=False)
    for z in (1.1, 1.5):
        mb.box((-0.19, -0.05, z - 0.02), (-0.1, 0.05, z + 0.02), IRON)


def fence(mb, pts_world, ground, gaps):
    """Valla baja de madera (0.9 m) siguiendo una polilinea cerrada en el plano; gaps = funcion (x, y) -> True si es
    un hueco. Postes cada 2.5 m, dos largueros."""
    n = 0
    for (x0, y0), (x1, y1) in zip(pts_world, pts_world[1:] + pts_world[:1]):
        L_ = math.hypot(x1 - x0, y1 - y0)
        k = max(1, int(L_ / 2.5))
        prev = None
        for i in range(k + 1):
            t = i / k
            x, y = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
            if gaps(x, y):
                prev = None
                continue
            z = ground(x, y)
            mb.box((x - 0.07, y - 0.07, z), (x + 0.07, y + 0.07, z + 0.95), WOOD, skip=("z-",))
            n += 1
            if prev is not None:
                (px, py, pz) = prev
                for hz in (0.45, 0.85):
                    mb.rod((px, py, pz + hz), (x, y, z + hz), 0.04, WOOD)
            prev = (x, y, z)
    return n


# --------------------------------------------------------------------------- Casa de Reposicion "El Remiendo"
def armor_rack(mb):
    """Percha con coraza remendada (parches de tela) y yelmo."""
    mb.box((-0.3, -0.25, 0.0), (0.3, 0.25, 0.1), WOOD)
    mb.rod((0, 0, 0.1), (0, 0, 1.75), 0.04, WOOD)
    mb.rod((-0.35, 0, 1.45), (0.35, 0, 1.45), 0.035, WOOD)
    L._ring_frustum(mb, 0, 0.02, 0.24, 0.3, 0.9, 1.45, 8, IRON, sy=0.6)
    mb.face([(-0.12, 0.2, 1.05), (0.06, 0.2, 1.05), (0.08, 0.2, 1.25), (-0.1, 0.2, 1.27)], CLOTH[0], nrm=(0, 1, 0))
    mb.face([(0.1, 0.19, 1.3), (0.2, 0.19, 1.28), (0.21, 0.19, 1.4), (0.11, 0.19, 1.42)], CLOTH[1], nrm=(0, 1, 0))
    L._ring_frustum(mb, 0, 0, 0.16, 0.12, 1.6, 1.82, 8, IRON, cap_top=True)


def sword_board(mb):
    """Tablero con 5 espadas viejas pulidas colgadas (cara +Y)."""
    mb.box((-1.0, 0.0, 0.0), (1.0, 0.06, 1.4), WOOD, skip=("y-",))
    for k in range(5):
        x = -0.8 + 0.4 * k
        mb.box((x - 0.035, 0.06, 0.15), (x + 0.035, 0.08, 1.05), "MAT_Bronze_Aged" if k == 2 else IRON, skip=("y-",))
        mb.box((x - 0.13, 0.06, 1.05), (x + 0.13, 0.1, 1.1), IRON, skip=("y-",))
        mb.box((x - 0.025, 0.06, 1.1), (x + 0.025, 0.1, 1.3), WOOD, skip=("y-",))


def boot_crate(mb, cloaks=False):
    mb.box((-0.4, -0.3, 0.0), (0.4, 0.3, 0.45), WOOD, skip=("z-",))
    if cloaks:
        for k, c in enumerate(CLOTH):
            mb.box((-0.35, -0.25 + 0.17 * k, 0.45), (0.35, -0.1 + 0.17 * k, 0.55 + 0.03 * k), c)
    else:
        for x in (-0.2, 0.15):
            mb.box((x - 0.07, -0.18, 0.45), (x + 0.07, 0.0, 0.75), "MAT_Wood_Dark")
            mb.box((x - 0.07, 0.0, 0.45), (x + 0.07, 0.2, 0.55), "MAT_Wood_Dark")


def sign_patch(mb):
    """SIGN_Hanging del kit con un parche cosido (tela de otro tono y puntadas)."""
    K.sign_hanging(mb)
    y = 0.6
    pts = [(0.04, y - 0.18, -0.72), (0.04, y + 0.2, -0.7), (0.04, y + 0.18, -0.4), (0.04, y - 0.2, -0.42)]
    mb.face(pts, CLOTH[2], nrm=(1, 0, 0))
    mb.face([(-0.04, p[1], p[2]) for p in pts][::-1], CLOTH[2], nrm=(-1, 0, 0))
    for k in range(5):
        z = -0.7 + 0.07 * k
        for sx in (0.045, -0.045):
            mb.box((sx - 0.003, y - 0.24, z), (sx + 0.003, y - 0.17, z + 0.012), IRON)
