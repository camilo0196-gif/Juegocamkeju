"""
CONCORDIA - Etapa 21 (E8): barrios de las razas. Plantilla con presets ajustables (N_RAZAS = 6).

Referencias reales: Mala Strana (Praga) para la mezcla de alturas y calles en cuesta, Cesky Krumlov y Rothenburg ob der
Tauber para las casas de piedra y madera con cubiertas empinadas, Toledo para las azoteas con pretil. Las yurtas (R05)
siguen el ger mongol (celosia de madera, fieltro, corona central).

Cada barrio (~35 x 35 m): 1 CASA DE LA RAZA (20 x 16, interior=true, la mas grande del barrio, bandera en la cubierta y
estandarte con el simbolo de la raza en la fachada, MARKER_RaceSpawn_xx delante de la puerta), las casas de sus
parcelas (assembler, preset de la raza) y 1 PLAZUELA de 10 m con fuente pequena o arbol viejo y 4 bancos.

RACE_PRESETS: material dominante, forma del tejado, escala de puerta y paleta. DOOR_SCALE escala la puerta, el dintel y
el umbral (bld_kit.DOOR_SCALE).
"""

import math
import os
import random
import sys

import bpy  # noqa: I001
import bmesh
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bld_kit as K  # noqa: E402

REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
N_RAZAS = 6

ST, LIGHT, GRAY = "MAT_Limestone_Worn", "MAT_Limestone_Light", "MAT_Wall_Gray"
WOOD, IRON, WATER, WARM = K.M_WOOD, K.M_IRON, "MAT_Water", K.M_WARM
HERB, COBBLE = "MAT_Herb_Green", "MAT_Cobble_Concordia"
# materiales nuevos de la etapa
WOOD_LIGHT = "MAT_Wood_Light"                 # albedo horneado (madera clara)
SLATE = "MAT_Roof_Slate"                      # albedo horneado (teja desaturada: pizarra gris)
SLATE_B, SLATE_BLUE = "MAT_Roof_Slate_B", "MAT_Roof_Slate_Blue"
SHINGLE, SHINGLE_B = "MAT_Roof_Shingle_Dark", "MAT_Roof_Shingle_Dark_B"
STONE_R01, SAND = "MAT_Stone_R01", "MAT_Stone_Sand"
GLASS_R04 = "MAT_Glass_R04"
FELT, HIDE = "MAT_Felt_R05", "MAT_Hide_R05"
LEAF_OLD = "MAT_Leaf_Old"

RACE_PRESETS = {
    "R01": {"material": "piedra", "roof": "gable", "pitch": 40.0, "door_scale": 1.0, "style": "stone",
            "ref": "Rothenburg / Cesky Krumlov: casas de piedra gris con hastial y pizarra",
            "wall": [STONE_R01, STONE_R01, GRAY], "trim": STONE_R01, "gable": STONE_R01, "roof_mat": SLATE,
            "roof_mat_b": SLATE_B, "color": "#6E6A66", "symbol": "tower"},
    "R02": {"material": "madera clara", "roof": "hip", "pitch": 34.0, "door_scale": 1.0, "style": "timber",
            "ref": "Mala Strana: casas de madera clara y revoco con cubierta a cuatro aguas",
            "wall": [WOOD_LIGHT, WOOD_LIGHT, LIGHT], "trim": LIGHT, "gable": WOOD_LIGHT, "roof_mat": "MAT_Roof_Tile_Ocher",
            "roof_mat_b": "MAT_Roof_Tile_Ocher_B", "color": "#8A7A5C", "symbol": "leaf"},
    "R03": {"material": "madera oscura", "roof": "gable", "pitch": 52.0, "door_scale": 0.9, "style": "timber",
            "ref": "Cesky Krumlov / Selva Negra: madera oscura y tejados muy inclinados",
            "wall": ["MAT_Wood_Dark", "MAT_Wood_Dark", STONE_R01], "trim": STONE_R01, "gable": "MAT_Wood_Dark",
            "roof_mat": SHINGLE, "roof_mat_b": SHINGLE_B, "color": "#5E4E42", "symbol": "pine"},
    "R04": {"material": "piedra y vidrio", "roof": "spire", "pitch": 58.0, "door_scale": 1.1, "style": "stone",
            "ref": "Cesky Krumlov (torre) / chapiteles de Praga: piedra clara, vidrio azul palido, cubiertas conicas",
            "wall": [LIGHT, LIGHT, STONE_R01], "trim": LIGHT, "gable": LIGHT, "roof_mat": SLATE_BLUE, "roof_mat_b": SLATE,
            "color": "#6C7A86", "symbol": "crystal", "glass": GLASS_R04},
    "R05": {"material": "pieles y madera", "roof": "yurt", "pitch": 28.0, "door_scale": 1.3, "style": "yurt",
            "ref": "ger mongol: celosia de madera clara, fieltro, cubierta de pieles y corona central",
            "wall": [FELT], "trim": WOOD_LIGHT, "gable": FELT, "roof_mat": HIDE, "roof_mat_b": FELT,
            "color": "#8A7260", "symbol": "sun"},
    "R06": {"material": "piedra y madera", "roof": "flat", "pitch": 0.0, "door_scale": 0.8, "style": "timber",
            "ref": "Toledo: planta baja de piedra arenisca, alta de entramado y azotea con pretil",
            "wall": [SAND, SAND, LIGHT], "trim": SAND, "gable": SAND, "roof_mat": GRAY, "roof_mat_b": GRAY,
            "color": "#9A8668", "symbol": "anvil"},
}


def _lin(c):
    return ((c + 0.055) / 1.055) ** 2.4 if c > 0.04045 else c / 12.92


def _hex(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4))


def saturation_hue(rgb):
    import colorsys
    h, s, v = colorsys.rgb_to_hsv(*rgb)
    return s, h * 360.0


# --------------------------------------------------------------------------- materiales
def _tinted(src, name, fac, note):
    """Copia de src con Mix Multiply (glTF: baseColorFactor)."""
    if name in bpy.data.materials:
        return False
    m = bpy.data.materials[src].copy()
    m.name = name
    N, Ln = m.node_tree.nodes, m.node_tree.links
    b = next(n for n in N if n.type == "BSDF_PRINCIPLED")
    mix = next((n for n in N if n.type == "MIX"), None)
    if mix is None:
        mix = N.new("ShaderNodeMix")
        mix.data_type = "RGBA"
        mix.blend_type = "MULTIPLY"
        mix.inputs["Factor"].default_value = 1.0
        Ln.new(N["Albedo"].outputs["Color"], mix.inputs["A"])
        Ln.new(mix.outputs["Result"], b.inputs["Base Color"])
    mix.inputs["B"].default_value = (*fac, 1.0)
    m["base_color_factor"] = ", ".join(f"{v:.2f}" for v in fac)
    m["note"] = note
    return True


def _baked(src, name, fn, fname, note):
    """Copia de src con el albedo transformado por fn (numpy, sRGB 0..1) y guardado como PNG nuevo."""
    if name in bpy.data.materials:
        return None
    import numpy as np
    from PIL import Image
    s = bpy.data.materials[src]
    img = s.node_tree.nodes["Albedo"].image
    a = np.asarray(Image.open(bpy.path.abspath(img.filepath)).convert("RGB")).astype(np.float32) / 255.0
    b = np.clip(fn(a), 0, 1)
    d = os.path.join(REPO, "textures", "concordia", name)
    os.makedirs(d, exist_ok=True)
    p = os.path.join(d, fname)
    Image.fromarray((b * 255 + 0.5).astype(np.uint8)).save(p, optimize=True)
    m = s.copy()
    m.name = name
    im = bpy.data.images.load(p, check_existing=True)
    im.colorspace_settings.name = "sRGB"
    m.node_tree.nodes["Albedo"].image = im
    m["note"] = note
    return {"albedo": os.path.relpath(p, REPO), "size": list(Image.open(p).size),
            "mean_srgb_before": round(float(a.mean()), 3), "mean_srgb_after": round(float(b.mean()), 3)}


def _flat(name, hex_c, rough=0.9, note=""):
    if name in bpy.data.materials:
        return False
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    r, g, bb = _hex(hex_c)
    b.inputs["Base Color"].default_value = (_lin(r), _lin(g), _lin(bb), 1)
    b.inputs["Roughness"].default_value = rough
    m["note"] = note
    return True


def race_banner_texture(key, size=(512, 1024)):
    """Estandarte de la raza: color tierra apagado, orla clara y simbolo (placeholder) en el tercio alto."""
    from PIL import Image, ImageDraw
    p = RACE_PRESETS[key]
    base = tuple(int(c * 255) for c in _hex(p["color"]))
    light = tuple(min(255, int(c * 1.38 + 22)) for c in base)
    dark = tuple(int(c * 0.7) for c in base)
    W, H = size
    im = Image.new("RGB", size, base)
    d = ImageDraw.Draw(im)
    b = 26
    d.rectangle((b, b, W - b, H - b), outline=light, width=14)
    d.rectangle((b + 30, b + 30, W - b - 30, H - b - 30), outline=dark, width=4)
    cx, cy, r = W // 2, int(H * 0.38), 150
    s = p["symbol"]
    if s == "tower":
        d.rectangle((cx - 70, cy - 60, cx + 70, cy + r), fill=light)
        for k in range(-2, 3):
            d.rectangle((cx + k * 32 - 12, cy - 100, cx + k * 32 + 12, cy - 60), fill=light)
        d.rectangle((cx - 22, cy + 70, cx + 22, cy + r), fill=base)
    elif s == "leaf":
        d.ellipse((cx - 80, cy - r, cx + 80, cy + r), fill=light)
        d.line((cx, cy - r + 20, cx, cy + r + 40), fill=base, width=12)
        for k in (-1, 0, 1):
            d.line((cx, cy + k * 60, cx - 60, cy + k * 60 - 50), fill=base, width=8)
            d.line((cx, cy + k * 60, cx + 60, cy + k * 60 - 50), fill=base, width=8)
    elif s == "pine":
        for k in range(3):
            y = cy - r + k * 80
            d.polygon([(cx, y), (cx + 70 + k * 35, y + 130), (cx - 70 - k * 35, y + 130)], fill=light)
        d.rectangle((cx - 16, cy + r + 10, cx + 16, cy + r + 60), fill=light)
    elif s == "crystal":
        d.polygon([(cx, cy - r - 20), (cx + 80, cy - 40), (cx + 55, cy + r), (cx - 55, cy + r), (cx - 80, cy - 40)],
                  fill=light)
        d.line((cx, cy - r - 20, cx, cy + r), fill=base, width=8)
        d.line((cx - 80, cy - 40, cx + 80, cy - 40), fill=base, width=8)
    elif s == "sun":
        d.ellipse((cx - 70, cy - 70, cx + 70, cy + 70), fill=light)
        for k in range(12):
            a = 2 * math.pi * k / 12
            d.line((cx + 95 * math.cos(a), cy + 95 * math.sin(a), cx + r * math.cos(a), cy + r * math.sin(a)),
                   fill=light, width=18)
    elif s == "anvil":
        d.polygon([(cx - r, cy - 50), (cx + 110, cy - 50), (cx + 110, cy + 10), (cx + 40, cy + 30), (cx + 40, cy + 80),
                   (cx + 90, cy + 120), (cx - 90, cy + 120), (cx - 40, cy + 80), (cx - 40, cy + 30), (cx - 100, cy + 10)],
                  fill=light)
    d.rectangle((b + 50, int(H * 0.74), W - b - 50, int(H * 0.74) + 10), fill=light)
    out_dir = os.path.join(REPO, "textures", "concordia", "MAT_Banner")
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, f"concordia_banner_raza_{key.lower()}_albedo.png")
    im.save(path, optimize=True)
    return path


def ensure_materials(keys):
    out = {}
    if WOOD_LIGHT not in bpy.data.materials:
        def light_wood(a):
            import numpy as np
            b = 1.0 - (1.0 - a) * 0.5                     # "screen" hacia el claro conservando la veta
            g = b.mean(axis=2, keepdims=True)
            b = g + (b - g) * 0.9
            return b * np.array([1.0, 0.93, 0.80], dtype=np.float32)
        out[WOOD_LIGHT] = _baked("MAT_Wood_Dark", WOOD_LIGHT, light_wood, "concordia_wood_light_albedo.png",
                                 "madera clara (R02, R05): albedo de MAT_Wood_Dark aclarado y templado, mismo ORM/normal")
    if SLATE not in bpy.data.materials:
        def slate(a):
            import numpy as np
            g = a.mean(axis=2, keepdims=True)
            b = g + (a - g) * 0.12                        # casi sin color: pizarra
            return b * np.array([0.78, 0.81, 0.86], dtype=np.float32)
        out[SLATE] = _baked("MAT_Roof_Tile_Ocher", SLATE, slate, "concordia_roof_slate_albedo.png",
                            "pizarra gris (R01, R04): albedo de la teja ocre desaturado y enfriado, mismo ORM/normal")
    for name, src, fac, note in (
            (SLATE_B, SLATE, (0.84, 0.84, 0.86), "pizarra de reparacion (otro tono)"),
            (SLATE_BLUE, SLATE, (0.74, 0.88, 1.0), "pizarra azulada (R04), tono 185-215"),
            (SHINGLE, "MAT_Roof_Tile_Ocher", (0.50, 0.43, 0.39), "teja oscura (R03)"),
            (SHINGLE_B, "MAT_Roof_Tile_Ocher", (0.42, 0.37, 0.34), "teja oscura de reparacion (R03)"),
            (STONE_R01, ST, (0.80, 0.80, 0.82), "piedra gris (R01)"),
            (SAND, ST, (1.0, 0.90, 0.76), "piedra arenisca (R06)"),
            (FELT, "MAT_Cloth_Patch_A", (1.0, 0.98, 0.92), "fieltro claro de yurta (R05)"),
            (HIDE, "MAT_Cloth_Patch_A", (0.62, 0.48, 0.37), "pieles y cuero (R05)")):
        if _tinted(src, name, fac, note):
            out[name] = {"src": src, "baseColorFactor": fac}
    if GLASS_R04 not in bpy.data.materials:
        m = bpy.data.materials["MAT_Pipe_Glass"].copy()
        m.name = GLASS_R04
        b = m.node_tree.nodes["Principled BSDF"]
        r, g, bb = _hex("#A9C9DC")
        b.inputs["Base Color"].default_value = (_lin(r), _lin(g), _lin(bb), 1)
        b.inputs["Alpha"].default_value = 0.35
        r, g, bb = _hex("#8FD0FF")
        b.inputs["Emission Color"].default_value = (_lin(r), _lin(g), _lin(bb), 1)
        b.inputs["Emission Strength"].default_value = 0.25
        m["note"] = "vidrio azul palido translucido (alpha 0.35) con emision baja 0.25 (#8FD0FF): R04"
        out[GLASS_R04] = {"base": "#A9C9DC", "alpha": 0.35, "emission": "#8FD0FF", "emission_strength": 0.25}
    if _flat(LEAF_OLD, "#5F6B4E", 0.95, "hojas del arbol viejo: verde apagado #5F6B4E"):
        out[LEAF_OLD] = {"color": "#5F6B4E"}
    for key in keys:
        name = f"MAT_Banner_{key}"
        path = race_banner_texture(key)
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
        m["color"] = RACE_PRESETS[key]["color"]
        m["note"] = "estandarte y bandera de la raza: textura por raza (simbolo de placeholder), UV 0..1, dos caras"
        out[name] = {"texture": os.path.relpath(path, REPO), "color": RACE_PRESETS[key]["color"]}
    return out


# --------------------------------------------------------------------------- utilidades sobre objetos
def remap_materials(obj, table):
    """Sustituye materiales por nombre en las ranuras de la malla (Body, Roof y sus LOD)."""
    me = obj.data
    n = 0
    for i, m in enumerate(me.materials):
        if m is not None and m.name in table and table[m.name] != m.name:
            me.materials[i] = bpy.data.materials[table[m.name]]
            n += 1
    return n


def glaze(obj, glass, src=WARM, off=0.025):
    """R04: delante de cada cristal calido de ventana, una lamina de vidrio azul palido translucido (2 tris por hueco).
    El cristal calido queda detras como fondo opaco (sin ver a traves del edificio)."""
    me = obj.data
    names = [m.name if m else "" for m in me.materials]
    if src not in names:
        return 0
    si = names.index(src)
    if glass not in names:
        me.materials.append(bpy.data.materials[glass])
        names.append(glass)
    gi = names.index(glass)
    bm = bmesh.new()
    bm.from_mesh(me)
    src_faces = [f for f in bm.faces if f.material_index == si]
    n = 0
    for f in src_faces:
        nrm = f.normal.copy()
        vs = [bm.verts.new(v.co + nrm * off) for v in f.verts]
        try:
            nf = bm.faces.new(vs)
        except ValueError:
            continue
        nf.material_index = gi
        nf.normal_update()
        if nf.normal.dot(nrm) < 0:
            nf.normal_flip()
        n += 1
    bm.to_mesh(me)
    bm.free()
    return n


def solid_above_door(plan, rng):
    """Casa de la raza: sin ventana encima de la puerta (ahi cuelga el estandarte)."""
    door = next((m for m in plan if m["side"] == "front" and m["floor"] == 0 and m["kind"] == "Door"), None)
    if door is None:
        return
    for m in plan:
        if m["side"] == "front" and m["floor"] >= 1 and m["i"] == door["i"]:
            m["kind"] = "Solid"
    _ = rng


# --------------------------------------------------------------------------- piezas
def turret(body, roof, x, y, r, z_top, cone_h, wall, roof_mat, glass=None, lantern=False, n=12, detail=0):
    """Torrecilla cilindrica (R04) con cono; con 'lantern', un tambor de vidrio translucido con nucleo calido debajo
    del cono. Devuelve la altura del vertice."""
    body.cylinder(r, -0.3, z_top, n, wall, caps=False, center=(x, y))
    if detail == 0:
        body.cylinder(r + 0.14, z_top - 0.3, z_top, n, wall, r1=r + 0.14, caps=False, center=(x, y))
        body.ngon_fill([(x + (r + 0.14) * math.cos(2 * math.pi * i / n), y + (r + 0.14) * math.sin(2 * math.pi * i / n),
                         z_top - 0.3) for i in range(n)], wall, flip=True)
        # aspilleras con vidrio (3, hacia fuera)
        for k in range(3):
            a = 2 * math.pi * (k + 0.5) / 3
            c, s = math.cos(a), math.sin(a)
            for z0 in (z_top * 0.35, z_top * 0.7):
                p = [(x + (r + 0.02) * c - 0.18 * -s, y + (r + 0.02) * s - 0.18 * c, z0),
                     (x + (r + 0.02) * c + 0.18 * -s, y + (r + 0.02) * s + 0.18 * c, z0),
                     (x + (r + 0.02) * c + 0.18 * -s, y + (r + 0.02) * s + 0.18 * c, z0 + 1.0),
                     (x + (r + 0.02) * c - 0.18 * -s, y + (r + 0.02) * s - 0.18 * c, z0 + 1.0)]
                body.face(p, WARM, nrm=(c, s, 0))
                if glass:
                    body.face([(px + 0.025 * c, py + 0.025 * s, pz) for px, py, pz in p], glass, nrm=(c, s, 0))
    z0 = z_top
    if lantern:
        body.cylinder(r - 0.6, z_top, z_top + 1.6, n, WARM, caps=False, center=(x, y))
        body.cylinder(r - 0.15, z_top, z_top + 1.6, n, glass, caps=False, center=(x, y))
        for i in range(0, n, 2):
            a = 2 * math.pi * i / n
            body.rod((x + (r - 0.1) * math.cos(a), y + (r - 0.1) * math.sin(a), z_top),
                     (x + (r - 0.1) * math.cos(a), y + (r - 0.1) * math.sin(a), z_top + 1.6), 0.06, IRON)
        z0 = z_top + 1.6
    R = r + 0.35
    roof.cylinder(R, z0 - 0.05, z0 + 0.12, n, WOOD, caps=False, center=(x, y))
    roof.ngon_fill([(x + R * math.cos(2 * math.pi * i / n), y + R * math.sin(2 * math.pi * i / n), z0 - 0.05)
                    for i in range(n)], WOOD, flip=True)
    apex = (x, y, z0 + 0.12 + cone_h)
    for i in range(n):
        a0, a1 = 2 * math.pi * i / n, 2 * math.pi * (i + 1) / n
        roof.face([(x + R * math.cos(a0), y + R * math.sin(a0), z0 + 0.12), (x + R * math.cos(a1), y + R * math.sin(a1),
                                                                            z0 + 0.12), apex], roof_mat,
                  nrm=(math.cos(a0 + math.pi / n), math.sin(a0 + math.pi / n), 0.5))
    roof.cylinder(0.05, apex[2] - 0.1, apex[2] + 1.0, 6, IRON, caps=True, center=(x, y))
    return apex[2]


def yurt(body, roof, cx, cy, r, wall_h, pitch, rng, door=None, n=16, detail=0, patches=2):
    """Yurta (ger): zocalo de piedra, muro de fieltro con fajas, cubierta conica de pieles hasta la corona (toono),
    cuerdas radiales y chimenea. door = (angulo, escala) -> marco y hoja de madera clara delante del fieltro.
    Devuelve (cota de la corona, centro de la puerta local o None)."""
    ring = lambda rr, z: [(cx + rr * math.cos(2 * math.pi * i / n), cy + rr * math.sin(2 * math.pi * i / n), z)
                          for i in range(n)]
    # zocalo (baja bajo la rasante) y muro
    body.cylinder(r + 0.12, -0.6, 0.25, n, ST, caps=False, center=(cx, cy))
    body.ngon_fill(ring(r + 0.12, 0.25), ST)
    body.cylinder(r, 0.25, wall_h, n, FELT, caps=False, center=(cx, cy))
    if detail == 0:
        body.cylinder(r + 0.035, 0.25, 0.75, n, HIDE, caps=False, center=(cx, cy))               # faldon de cuero
        for z in (wall_h * 0.42, wall_h * 0.8):
            body.cylinder(r + 0.03, z, z + 0.1, n, WOOD, caps=False, center=(cx, cy))         # fajas (cuerdas)
    # cubierta de pieles
    re, rc = r + 0.45, max(0.5, 0.14 * r)
    ze = wall_h - 0.12
    zc = ze + (re - rc) * math.tan(math.radians(pitch))
    roof.cylinder(re, ze, zc, n, HIDE, r1=rc, caps=False, center=(cx, cy))
    for i in range(n):                                                                         # sofito
        a0, a1 = 2 * math.pi * i / n, 2 * math.pi * (i + 1) / n
        roof.face([(cx + re * math.cos(a0), cy + re * math.sin(a0), ze), (cx + r * math.cos(a0), cy + r * math.sin(a0), ze),
                   (cx + r * math.cos(a1), cy + r * math.sin(a1), ze), (cx + re * math.cos(a1), cy + re * math.sin(a1), ze)],
                  WOOD_LIGHT, nrm=(0, 0, -1))
    # corona (toono) de madera clara, capucha de fieltro y chimenea
    roof.cylinder(rc + 0.08, zc - 0.05, zc + 0.28, n // 2, WOOD_LIGHT, caps=False, center=(cx, cy))
    roof.cylinder(rc + 0.1, zc + 0.28, zc + 0.75, n // 2, FELT, r1=0.12, caps=False, center=(cx, cy))
    roof.cylinder(0.11, zc + 0.3, zc + 1.6, 6, IRON, caps=True, center=(cx + rc * 0.4, cy - rc * 0.3))
    if detail == 0:
        # cuerdas radiales y anillo de cuerda a media pendiente
        for k in range(4):
            a = 2 * math.pi * (k + 0.125) / 4
            p0 = (cx + (re - 0.05) * math.cos(a), cy + (re - 0.05) * math.sin(a), ze + 0.06)
            p1 = (cx + (rc + 0.05) * math.cos(a), cy + (rc + 0.05) * math.sin(a), zc + 0.06)
            roof.rod(p0, p1, 0.04, WOOD)
        rm = (re + rc) / 2
        zm = (ze + zc) / 2
        roof.cylinder(rm + 0.02, zm + 0.02, zm + 0.12, n, WOOD, r1=rm - 0.05, caps=False, center=(cx, cy))
        # remiendos de piel de otro tono sobre la cubierta
        for _ in range(patches):
            a = rng.uniform(0, 2 * math.pi)
            da = rng.uniform(0.18, 0.3)
            t0 = rng.uniform(0.15, 0.45)
            t1 = t0 + rng.uniform(0.18, 0.3)
            pts = []
            for aa, t in ((a, t0), (a + da, t0), (a + da, t1), (a, t1)):
                rr = re + (rc - re) * t
                pts.append((cx + rr * math.cos(aa), cy + rr * math.sin(aa), ze + (zc - ze) * t + 0.05))
            roof.face(pts, FELT, nrm=(math.cos(a), math.sin(a), 1.5))
    dloc = None
    if door is not None:
        ang, ds = door
        c, s = math.cos(ang), math.sin(ang)
        w, h = min(1.3 * ds, 1.8), min(2.35 * ds, wall_h - 0.4)
        body.push(Matrix.Translation((cx + r * c, cy + r * s, 0.0)) @ Matrix.Rotation(ang - math.pi / 2, 4, "Z"))
        # umbral, marco, hoja y tejadillo de madera clara (la cara exterior en +Y)
        body.box((-w / 2 - 0.25, -0.2, 0.0), (w / 2 + 0.25, 0.45, 0.14 * ds), ST, skip=("z-",))
        body.box((-w / 2 - 0.18, -0.25, 0.14), (-w / 2, 0.22, h + 0.2), WOOD_LIGHT)
        body.box((w / 2, -0.25, 0.14), (w / 2 + 0.18, 0.22, h + 0.2), WOOD_LIGHT)
        body.box((-w / 2 - 0.18, -0.25, h), (w / 2 + 0.18, 0.22, h + 0.2), WOOD_LIGHT)
        body.box((-w / 2, -0.1, 0.14), (w / 2, 0.12, h), WOOD, skip=("y-",))
        for zz in (0.6, h * 0.5, h - 0.5):
            body.box((-w / 2 + 0.06, 0.12, zz), (w / 2 - 0.06, 0.14, zz + 0.08), IRON, skip=("y-",))
        body.prism([(-w / 2 - 0.45, h + 0.2), (w / 2 + 0.45, h + 0.2), (0.0, h + 0.75)], -0.3, 0.55, HIDE)
        body.pop()
        dloc = (cx + (r + 0.45) * c, cy + (r + 0.45) * s, 0.0)
    return zc, dloc


def flag_mesh(name, w=1.4, h=1.1, segs=3):
    """Bandera ondulada (cara +Y, origen en el mastil, borde superior en z=0) con UV recortada al simbolo del
    estandarte (misma textura: el recorte guarda la proporcion)."""
    me = bpy.data.meshes.get(name)
    if me is not None:
        return me
    bm = bmesh.new()
    uv = bm.loops.layers.uv.new("UVWorld")
    vh = 0.5 * (512.0 / w * h) / 1024.0            # media altura del recorte en V (textura 512 x 1024)
    vc = 0.62
    cols = []
    for i in range(segs + 1):
        x = w * i / segs
        dy = 0.12 * math.sin(math.pi * i / segs * 1.5)
        cols.append(((x, dy, 0.0), (x, dy, -h)))
    for i in range(segs):
        (a_top, a_bot), (b_top, b_bot) = cols[i], cols[i + 1]
        f = bm.faces.new([bm.verts.new(a_bot), bm.verts.new(b_bot), bm.verts.new(b_top), bm.verts.new(a_top)])
        for lp in f.loops:
            x, _, z = lp.vert.co
            lp[uv].uv = (x / w, vc - vh + (z + h) / h * 2 * vh)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    return me


def flag_pole(mb, h=3.6):
    mb.box((-0.18, -0.18, 0.0), (0.18, 0.18, 0.25), IRON)
    mb.rod((0.0, 0.0, 0.25), (0.0, 0.0, h), 0.045, WOOD, caps=True)
    mb.cylinder(0.09, h, h + 0.16, 6, "MAT_Bronze_Aged", caps=True)


def banner_pole(mb, w=1.8):
    mb.rod((-w / 2 - 0.15, 0.0, 0.0), (w / 2 + 0.15, 0.0, 0.0), 0.04, IRON)
    for s in (-1, 1):
        mb.rod((s * (w / 2 - 0.1), 0.0, 0.0), (s * (w / 2 - 0.1), -0.25, 0.18), 0.025, IRON)
        mb.cylinder(0.065, -0.065, 0.065, 6, "MAT_Bronze_Aged", caps=True, center=(s * (w / 2 + 0.2), 0.0))


def banner_mast(mb, h=6.5, arm=1.2):
    """Mastil exento (R05): poste de madera con travesano para el estandarte."""
    mb.box((-0.35, -0.35, -0.3), (0.35, 0.35, 0.35), ST)
    mb.rod((0.0, 0.0, 0.35), (0.0, 0.0, h), 0.11, WOOD, caps=True)
    mb.rod((-arm, 0.0, h - 0.4), (arm, 0.0, h - 0.4), 0.06, WOOD, caps=True)
    mb.cylinder(0.16, h, h + 0.3, 6, "MAT_Bronze_Aged", r1=0.02, caps=True)


# --------------------------------------------------------------------------- plazuela
def fountain_small(mb):
    """Fuente pequena: pila octogonal de 3.2 m, fuste con taza y 4 canos."""
    n = 8
    R, Ri, h = 1.6, 1.32, 0.55
    ring = lambda rr, z: [(rr * math.cos(2 * math.pi * (i + 0.5) / n), rr * math.sin(2 * math.pi * (i + 0.5) / n), z)
                          for i in range(n)]
    mb.cylinder(R, -0.4, h, n, ST, caps=False)
    o, i_ = ring(R, h), ring(Ri, h)
    for k in range(n):
        j = (k + 1) % n
        mb.face([o[k], o[j], i_[j], i_[k]], ST, nrm=(0, 0, 1))
    ii = ring(Ri, 0.15)
    for k in range(n):
        j = (k + 1) % n
        mb.face([i_[k], i_[j], ii[j], ii[k]], ST, nrm=(-(o[k][0] + o[j][0]), -(o[k][1] + o[j][1]), 0))
    mb.ngon_fill(ring(Ri, 0.42), WATER)
    mb.cylinder(0.24, 0.15, 1.45, n, ST, r1=0.18, caps=False)
    mb.cylinder(0.26, 1.3, 1.55, n, ST, r1=0.72, caps=False)
    mb.ngon_fill(ring(0.66, 1.5), WATER)
    mb.cylinder(0.12, 1.5, 2.0, 6, ST, r1=0.05, caps=True)
    for k in range(4):
        a = math.pi / 2 * k + math.pi / 4
        mb.rod((0.2 * math.cos(a), 0.2 * math.sin(a), 1.05), (0.55 * math.cos(a), 0.55 * math.sin(a), 0.98), 0.035,
               "MAT_Bronze_Aged")


def blob(mb, x, y, z, rx, rz, mat, rng, seg=6, rings=3):
    """Copa de follaje: esfera tosca con jitter."""
    pts = []
    for r_ in range(1, rings + 1):
        ph = math.pi * r_ / (rings + 1)
        row = []
        for s in range(seg):
            th = 2 * math.pi * (s + 0.5 * (r_ % 2)) / seg
            k = rng.uniform(0.85, 1.12)
            row.append((x + rx * k * math.sin(ph) * math.cos(th), y + rx * k * math.sin(ph) * math.sin(th),
                        z + rz * math.cos(ph)))
        pts.append(row)
    top, bot = (x, y, z + rz), (x, y, z - rz * 0.8)
    for s in range(seg):
        t = (s + 1) % seg
        mb.face([pts[0][s], pts[0][t], top], mat, nrm=(pts[0][s][0] - x, pts[0][s][1] - y, rz))
        mb.face([pts[-1][t], pts[-1][s], bot], mat, nrm=(pts[-1][s][0] - x, pts[-1][s][1] - y, -rz))
        for r_ in range(rings - 1):
            a, b = pts[r_], pts[r_ + 1]
            mb.face([a[s], b[s], b[t], a[t]], mat, nrm=(a[s][0] - x, a[s][1] - y, a[s][2] - z))


def old_tree(mb, rng):
    """Arbol viejo (~9 m): tronco inclinado y nudoso, 3 ramas, copa de 7 masas de hoja verde apagada y alcorque de
    piedra con asiento."""
    n = 10
    mb.cylinder(1.5, -0.4, 0.45, n, ST, caps=False)
    mb.cylinder(1.5, 0.45, 0.45, n, ST, r1=1.05, caps=False)
    mb.cylinder(1.05, 0.45, 0.05, n, ST, caps=False)
    mb.ngon_fill([(1.05 * math.cos(2 * math.pi * i / n), 1.05 * math.sin(2 * math.pi * i / n), 0.05) for i in range(n)],
                 "MAT_Ground_Cracked")
    lean = Vector((0.35, -0.2, 0.0))
    pts = [Vector((0, 0, 0)), Vector((0.15, -0.05, 1.4)) + lean * 0.3, Vector((0.25, -0.1, 2.8)) + lean * 0.7,
           Vector((0.1, 0.05, 3.8)) + lean]
    rads = [0.62, 0.46, 0.38, 0.3]
    for k in range(3):
        a, b = pts[k], pts[k + 1]
        d = b - a
        q = d.normalized().to_track_quat("Z", "Y")
        mb.push(Matrix.Translation(a) @ q.to_matrix().to_4x4())
        mb.cylinder(rads[k], 0.0, d.length + 0.05, 7, WOOD, r1=rads[k + 1], caps=False)
        mb.pop()
    top = pts[-1]
    tips = []
    for k in range(3):
        a = 2 * math.pi * k / 3 + rng.uniform(-0.3, 0.3)
        tip = top + Vector((2.3 * math.cos(a), 2.3 * math.sin(a), rng.uniform(1.4, 2.2)))
        d = tip - top
        q = d.normalized().to_track_quat("Z", "Y")
        mb.push(Matrix.Translation(top) @ q.to_matrix().to_4x4())
        mb.cylinder(0.24, 0.0, d.length, 6, WOOD, r1=0.1, caps=False)
        mb.pop()
        tips.append(tip)
    cen = top + Vector((0, 0, 2.6))
    blob(mb, cen.x, cen.y, cen.z, 2.6, 1.7, LEAF_OLD, rng, seg=7)
    for k, t in enumerate(tips):
        blob(mb, t.x, t.y, t.z + 0.3, 2.1, 1.4, LEAF_OLD if k % 2 else HERB, rng)
    for k in range(3):
        a = 2 * math.pi * (k + 0.5) / 3
        blob(mb, cen.x + 2.6 * math.cos(a), cen.y + 2.6 * math.sin(a), cen.z - 0.9, 1.6, 1.1, HERB, rng, seg=5, rings=2)


def bench(mb):
    """Banco de piedra con asiento de madera (1.8 m)."""
    for x in (-0.7, 0.7):
        mb.box((x - 0.14, -0.2, -0.1), (x + 0.14, 0.2, 0.42), ST, skip=("z-",))
    mb.box((-0.9, -0.24, 0.42), (0.9, 0.24, 0.5), WOOD_LIGHT)


def paving_disc(mb, g, cx, cy, r=5.0, n=24, lift=0.035):
    """Losas de la plazuela (10 m) siguiendo el terreno: anillo exterior + centro."""
    c = (cx, cy, g(cx, cy) + lift)
    for rr_in, rr_out in ((0.0, r * 0.55), (r * 0.55, r)):
        for i in range(n):
            a0, a1 = 2 * math.pi * i / n, 2 * math.pi * (i + 1) / n
            p = lambda rr, a: (cx + rr * math.cos(a), cy + rr * math.sin(a), g(cx + rr * math.cos(a), cy + rr * math.sin(a)) + lift)
            if rr_in == 0.0:
                mb.face([c, p(rr_out, a0), p(rr_out, a1)], COBBLE, nrm=(0, 0, 1))
            else:
                mb.face([p(rr_in, a0), p(rr_out, a0), p(rr_out, a1), p(rr_in, a1)], COBBLE, nrm=(0, 0, 1))
    for i in range(n):                                                   # bordillo
        a0, a1 = 2 * math.pi * i / n, 2 * math.pi * (i + 1) / n
        p0 = (cx + r * math.cos(a0), cy + r * math.sin(a0))
        p1 = (cx + r * math.cos(a1), cy + r * math.sin(a1))
        z0, z1 = g(*p0) + lift, g(*p1) + lift
        mb.face([(p0[0], p0[1], z0 - 0.15), (p1[0], p1[1], z1 - 0.15), (p1[0], p1[1], z1), (p0[0], p0[1], z0)], ST,
                nrm=(math.cos(a0), math.sin(a0), 0))


def roof_table(key):
    """Tabla de sustitucion de materiales del kit para un preset (trim, tejas)."""
    p = RACE_PRESETS[key]
    return {K.M_STONE: p["trim"], K.M_ROOF: p["roof_mat"], K.M_ROOF_B: p["roof_mat_b"]}


def preset_saturation(key):
    return saturation_hue(_hex(RACE_PRESETS[key]["color"]))


_ = (random, Vector)
