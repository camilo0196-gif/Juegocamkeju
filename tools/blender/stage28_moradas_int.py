"""
CONCORDIA - Etapa 28: vitrina de trofeos (3 variantes) e interiores tipo de las Moradas (Habitacion, Casa pequena,
Casa grande) con build_interior (estilo entramado).

Referencias: casas de Cesky Krumlov y Rothenburg ob der Tauber: vigas bajas de madera, chimenea de piedra, muros de
revoco sobre zocalo de tablas, ventanas pequenas con postigos; luz calida y aspecto remendado.

Vitrina (MARKER_TrophyCase): un solo material MAT_TrophyCase (atlas 512: 3/4 madera oscura de Concordia, 1/4 vidrio
gris con alfa 0.3), <= 800 triangulos, LOD1 y LOD2, 6-9 Empties MARKER_Trophy_Slot_xx (+Y al frente) hijos de la
vitrina. Variantes: pared (9), mesa (6), nichos (9).

Plantillas (escena privada por puerta, la instancia Godot): giro fijo de -90 grados respecto a CAM_Iso, de modo que
la puerta (+Y) y el lado +X son los muros cercanos (WALL_Near_A/B) y el mobiliario mira a la camara desde -X / -Y.
"""

import math
import os

import bpy
from mathutils import Matrix, Vector

import bld_kit as K
import interior_kit as IK

WOOD, WOOD_L, IRON, STONE = IK.WOOD, IK.WOOD_L, IK.IRON, IK.STONE
TROPHY_MAT = "MAT_TrophyCase"
TEMPLATE_ROT = -90.0
H_LOW = 2.7                         # vigas bajas (Cesky Krumlov): 2.7 m de suelo a vigas


def M(x, y, z=0.0, yaw=0.0, sx=1.0, sy=1.0, sz=1.0):
    return Matrix.Translation((x, y, z)) @ Matrix.Rotation(math.radians(yaw), 4, "Z") @ \
        Matrix.Diagonal((sx, sy, sz, 1.0))


# --------------------------------------------------------------------------- material de la vitrina
def trophy_material(repo):
    m = bpy.data.materials.get(TROPHY_MAT)
    if m is not None:
        return m
    from PIL import Image
    src = os.path.join(repo, "textures", "concordia", "MAT_Wood_Dark", "concordia_wood_dark_albedo.png")
    out = os.path.join(repo, "textures", "concordia", TROPHY_MAT, "trophy_case_atlas_512.png")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    wood = Image.open(src).convert("RGB").resize((384, 512))
    img = Image.new("RGBA", (512, 512), (40, 46, 52, 77))
    img.paste(wood, (0, 0))
    from PIL import ImageDraw
    d = ImageDraw.Draw(img)
    for k in range(6):                                      # reflejos suaves del vidrio
        x = 400 + k * 18
        d.line([(x, 0), (x - 60, 512)], fill=(70, 78, 86, 90), width=3)
    img.save(out)
    m = bpy.data.materials.new(TROPHY_MAT)
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = bpy.data.images.load(out)
    nt.links.new(tex.outputs["Color"], b.inputs["Base Color"])
    nt.links.new(tex.outputs["Alpha"], b.inputs["Alpha"])
    b.inputs["Roughness"].default_value = 0.45
    try:
        m.surface_render_method = "BLENDED"
    except AttributeError:
        m.blend_method = "BLEND"
    m["note"] = "vitrina de trofeos: atlas 512 (u 0-0.75 madera oscura de Concordia, 0.75-1 vidrio alfa 0.3)"
    return m


def to_trophy_uv(o):
    """Un solo material: caras de madera -> u 0-0.75 (escala metrica), caras de vidrio -> centro de la franja."""
    me = o.data
    names = [s.material.name if s.material else "" for s in o.material_slots]
    uv = me.uv_layers.active.data
    for p in me.polygons:
        glass = names[p.material_index] == "MAT_Glass_R04" if p.material_index < len(names) else False
        lis = list(p.loop_indices)
        if glass:
            for li in lis:
                uv[li].uv = (0.875 + 0.1 * (uv[li].uv[0] % 1.0), 0.1 + 0.8 * (uv[li].uv[1] % 1.0))
            continue
        us = [uv[li].uv[0] for li in lis]
        vs = [uv[li].uv[1] for li in lis]
        du, dv = math.floor(min(us)), math.floor(min(vs))
        su = max(1.0, math.ceil(max(us) - du))
        sv = max(1.0, math.ceil(max(vs) - dv))
        for li in lis:
            u, v = uv[li].uv
            uv[li].uv = (0.75 * (u - du) / su * 0.98 + 0.005, (v - dv) / sv * 0.98 + 0.01)
    me.materials.clear()
    me.materials.append(bpy.data.materials[TROPHY_MAT])
    for p in me.polygons:
        p.material_index = 0


# --------------------------------------------------------------------------- vitrinas
GL = "MAT_Glass_R04"


def tc_wall(mb, detail):
    """De pared: 1.0 x 0.4 x 1.9 m; zocalo, costados, cornisa, fondo, 3 baldas; frente de dos hojas de vidrio con
    montante. 9 huecos (3 x 3)."""
    W, D, H = 1.0, 0.4, 1.9
    if detail == 2:
        mb.box((-W / 2, -D / 2, 0), (W / 2, D / 2, H), WOOD, skip=("z-", "y+"))
        mb.face([(-W / 2, D / 2, 0.15), (W / 2, D / 2, 0.15), (W / 2, D / 2, H), (-W / 2, D / 2, H)], GL, nrm=(0, 1, 0))
        mb.box((-W / 2, D / 2 - 0.001, 0), (W / 2, D / 2 + 0.01, 0.15), WOOD, skip=("z-", "y-"))
        return []
    mb.box((-W / 2 - 0.02, -D / 2, 0), (W / 2 + 0.02, D / 2 + 0.02, 0.15), WOOD, skip=("z-",))
    mb.box((-W / 2 - 0.04, -D / 2, H - 0.1), (W / 2 + 0.04, D / 2 + 0.04, H), WOOD)
    for x in (-W / 2, W / 2 - 0.05):
        mb.box((x, -D / 2, 0.15), (x + 0.05, D / 2, H - 0.1), WOOD, skip=("z-", "z+"))
    mb.box((-W / 2 + 0.05, -D / 2, 0.15), (W / 2 - 0.05, -D / 2 + 0.03, H - 0.1), WOOD, skip=("z-", "z+", "y-"))
    zs = (0.5, 0.95, 1.4)
    for z in zs:
        mb.box((-W / 2 + 0.05, -D / 2 + 0.03, z - 0.025), (W / 2 - 0.05, D / 2 - 0.04, z), WOOD)
    yg = D / 2 - 0.015
    mb.face([(-W / 2 + 0.05, yg, 0.15), (W / 2 - 0.05, yg, 0.15), (W / 2 - 0.05, yg, H - 0.1),
             (-W / 2 + 0.05, yg, H - 0.1)], GL, nrm=(0, 1, 0))
    if detail == 0:
        mb.box((-0.02, yg, 0.15), (0.02, D / 2 + 0.01, H - 0.1), WOOD, skip=("y-",))           # montante
        for x in (-0.06, 0.06):
            mb.box((x - 0.006, D / 2 + 0.01, 0.95), (x + 0.006, D / 2 + 0.025, 1.05), IK.BRONZE)  # tiradores
        mb.box((-W / 2 + 0.3, D / 2, 0.04), (-W / 2 + 0.52, D / 2 + 0.025, 0.11), WOOD_L)        # remiendo
    slots = []
    for r, z in enumerate((0.15,) + zs[:2]):
        for c, x in enumerate((-0.3, 0.0, 0.3)):
            slots.append((x, 0.0, z + (0.0 if r == 0 else 0.0)))
    return slots


def tc_table(mb, detail):
    """De mesa: 1.2 x 0.6 x 1.0 m; patas, faldon, caja con tapa y costados de vidrio. 6 huecos (2 x 3)."""
    W, D, Z0, H = 1.2, 0.6, 0.75, 1.0
    if detail == 2:
        mb.box((-W / 2, -D / 2, 0), (W / 2, D / 2, Z0), WOOD, skip=("z-",))
        mb.box((-W / 2, -D / 2, Z0), (W / 2, D / 2, H), GL, skip=("z-",))
        return []
    for x in (-W / 2 + 0.04, W / 2 - 0.1):
        for y in (-D / 2 + 0.04, D / 2 - 0.1):
            mb.box((x, y, 0), (x + 0.06, y + 0.06, Z0 - 0.08), WOOD, skip=("z-",))
    mb.box((-W / 2, -D / 2, Z0 - 0.08), (W / 2, D / 2, Z0), WOOD)
    if detail == 0:
        mb.box((-W / 2 + 0.1, -D / 2 + 0.1, 0.18), (W / 2 - 0.1, D / 2 - 0.1, 0.21), WOOD_L)     # balda baja
    for x in (-W / 2, W / 2 - 0.035):
        for y in (-D / 2, D / 2 - 0.035):
            mb.box((x + 0.004, y + 0.004, Z0), (x + 0.031, y + 0.031, H - 0.005), WOOD, skip=("z-",))
    mb.box((-W / 2, -D / 2, H - 0.03), (W / 2, -D / 2 + 0.035, H), WOOD, skip=("z-",))
    mb.box((-W / 2, D / 2 - 0.035, H - 0.03), (W / 2, D / 2, H), WOOD, skip=("z-",))
    gx, gy = W / 2 - 0.035, D / 2 - 0.035
    mb.face([(-gx, -gy, H - 0.01), (gx, -gy, H - 0.01), (gx, gy, H - 0.01), (-gx, gy, H - 0.01)], GL, nrm=(0, 0, 1))
    mb.face([(-gx, D / 2 - 0.02, Z0), (gx, D / 2 - 0.02, Z0), (gx, D / 2 - 0.02, H - 0.03), (-gx, D / 2 - 0.02, H - 0.03)],
            GL, nrm=(0, 1, 0))
    for x in (-W / 2 + 0.02, W / 2 - 0.02):
        mb.face([(x, -gy, Z0), (x, gy, Z0), (x, gy, H - 0.03), (x, -gy, H - 0.03)], GL, nrm=(1 if x > 0 else -1, 0, 0))
    return [(x, y, Z0) for y in (-0.12, 0.12) for x in (-0.38, 0.0, 0.38)]


def tc_niches(mb, detail):
    """Estante con nichos: 1.2 x 0.35 x 1.6 m; 3 x 3 nichos de 0.36 x 0.45 con arco rebajado de madera y vidrio
    delante. 9 huecos."""
    W, D, H = 1.2, 0.35, 1.6
    if detail == 2:
        mb.box((-W / 2, -D / 2, 0), (W / 2, D / 2, H), WOOD, skip=("z-", "y+"))
        mb.face([(-W / 2, D / 2, 0.1), (W / 2, D / 2, 0.1), (W / 2, D / 2, H), (-W / 2, D / 2, H)], GL, nrm=(0, 1, 0))
        mb.box((-W / 2, D / 2 - 0.001, 0), (W / 2, D / 2 + 0.01, 0.1), WOOD, skip=("z-", "y-"))
        return []
    mb.box((-W / 2, -D / 2, 0), (W / 2, D / 2, 0.1), WOOD, skip=("z-",))
    mb.box((-W / 2 - 0.03, -D / 2, H - 0.06), (W / 2 + 0.03, D / 2 + 0.03, H), WOOD)
    mb.box((-W / 2, -D / 2, 0.1), (W / 2, -D / 2 + 0.03, H - 0.06), WOOD, skip=("z-", "z+", "y-"))
    xs = [-W / 2 + k * W / 3 for k in range(4)]
    zs = [0.1 + k * 0.48 for k in range(4)]
    for k, x in enumerate(xs):
        x0 = x - (0.0 if k == 0 else 0.02)
        x1 = x + (0.04 if k == 0 else 0.0 if k == 3 else 0.02)
        if k == 3:
            x0 = x - 0.04
        mb.box((x0, -D / 2 + 0.03, 0.1), (x1, D / 2 - 0.006, H - 0.06), WOOD, skip=("z-", "z+"))
    for z in zs[1:3]:
        mb.box((-W / 2 + 0.04, -D / 2 + 0.03, z - 0.02), (W / 2 - 0.04, D / 2 - 0.012, z + 0.02), WOOD)
    if detail == 0:
        for i in range(3):
            for j in range(3):
                xc, zt = (xs[i] + xs[i + 1]) / 2, zs[j + 1] - 0.02
                IK.prism(mb, [(xc - 0.17, zt), (xc + 0.17, zt), (xc + 0.17, zt - 0.06), (xc, zt - 0.03),
                              (xc - 0.17, zt - 0.06)], D / 2 - 0.03, D / 2, WOOD_L, axis="y")
    yg = D / 2 - 0.035
    mb.face([(-W / 2 + 0.04, yg, 0.1), (W / 2 - 0.04, yg, 0.1), (W / 2 - 0.04, yg, H - 0.06), (-W / 2 + 0.04, yg, H - 0.06)],
            GL, nrm=(0, 1, 0))
    return [((xs[i] + xs[i + 1]) / 2, -0.02, zs[j] + 0.02) for j in range(3) for i in range(3)]


TROPHY_VARIANTS = {"pared": tc_wall, "mesa": tc_table, "nichos": tc_niches}


def build_trophy_cases(col, repo):
    """Crea TROPHY_Case_<v> (LOD0) con _LOD1 y _LOD2 y sus MARKER_Trophy_Slot_xx; devuelve informe."""
    trophy_material(repo)
    out = {}
    for k, (v, fn) in enumerate(TROPHY_VARIANTS.items()):
        res = {}
        root = None
        for detail, suf in ((0, ""), (1, "_LOD1"), (2, "_LOD2")):
            mb = K.MB()
            slots = fn(mb, detail)
            name = f"TROPHY_Case_{v}{suf}"
            o = IK.to_obj(mb, name, col)
            o.data.name = name
            to_trophy_uv(o)
            res[suf or "LOD0"] = IK.tris(o)
            if detail == 0:
                root = o
                o.location = (7000.0 + k * 2.5, 0.0, 0.0)
                o["trophy_case"] = v
                o["slots"] = len(slots)
                for i, p in enumerate(slots, 1):
                    e = bpy.data.objects.new(f"MARKER_Trophy_Slot_{v}_{i:02d}", None)
                    col.objects.link(e)
                    e.parent = o
                    e.location = p
                    e.empty_display_type = "SINGLE_ARROW"
                    e.empty_display_size = 0.12
                    e["slot"] = i
                    e["axis"] = "+Y local = frente"
                res["slots"] = len(slots)
            else:
                o.parent = root
                o.hide_render = True
                o.hide_viewport = True
        if res["LOD0"] > 800:
            raise RuntimeError(f"vitrina {v}: {res['LOD0']} triangulos > 800")
        out[v] = res
    return out


def place_trophy(it, variant, mw, group="Furniture", name=None, first_slot=1):
    """Instancia la vitrina (malla LOD0 compartida) con sus slots como Empties hijos (los nombra MARKER_Trophy_Slot_xx)."""
    src = bpy.data.objects[f"TROPHY_Case_{variant}"]
    o = it.inst(src.data.name, mw, group, name=name or f"TROPHY_{variant.capitalize()}_{it.name}")
    o["trophy_case"] = variant
    o["lods"] = [f"TROPHY_Case_{variant}_LOD1", f"TROPHY_Case_{variant}_LOD2"]
    for c in sorted([c for c in src.children if c.type == "EMPTY"], key=lambda c: c.name):
        k = c["slot"] + first_slot - 1
        e = bpy.data.objects.new(f"MARKER_Trophy_Slot_{k:02d}", None)
        it.col.objects.link(e)
        e.parent = o
        e.location = c.location
        e.empty_display_type = "SINGLE_ARROW"
        e.empty_display_size = 0.12
        e["slot"] = k
        e["trophy_case"] = variant
        e["axis"] = "+Y local = frente"
    return o


# --------------------------------------------------------------------------- props propios de las casas
def p_workbench(mb):
    """Mesa de trabajo basica 1.6 x 0.7 x 0.9 m: tablero grueso, patas, travesano, balda con herramientas."""
    mb.box((-0.8, -0.35, 0.82), (0.8, 0.35, 0.9), WOOD)
    for x in (-0.72, 0.64):
        for y in (-0.28, 0.2):
            mb.box((x, y, 0), (x + 0.08, y + 0.08, 0.82), WOOD, skip=("z-", "z+"))
    mb.box((-0.7, -0.3, 0.2), (0.7, 0.3, 0.24), WOOD_L)
    mb.box((-0.3, 0.33, 0.9), (0.1, 0.36, 0.95), IRON)                         # tope
    mb.box((0.35, -0.1, 0.9), (0.6, 0.1, 0.96), WOOD_L)                        # taco remendado
    mb.rod((-0.6, -0.1, 0.91), (-0.35, 0.05, 0.91), 0.012, IRON)               # escoplo


def p_planter(mb, rng):
    """Jardinera de hierbas 2.0 x 0.5 x 0.45 m de tablas con tierra y matas (MARKER_Garden encima)."""
    mb.box((-1.0, -0.25, 0), (1.0, 0.25, 0.45), WOOD, skip=("z-", "z+"))
    mb.box((-0.96, -0.21, 0.36), (0.96, 0.21, 0.38), IK.ASH)
    import props_mano as PM
    for k in range(7):
        x = -0.8 + k * 0.27
        PM.lathe(mb, [(0.02, 0.38), (0.11, 0.5), (0.07, 0.62), (0.0, 0.66)], 5, "MAT_Herb_Green" if k % 3 else "MAT_Straw",
                 center=(x, rng.uniform(-0.06, 0.06)), cap_bottom=False, cap_top=False)


def p_bed_simple(mb):
    """Cama de casa comunal 0.95 x 2.0 m: armazon, jergon remendado y manta."""
    mb.box((-0.48, -1.0, 0), (0.48, 1.0, 0.35), WOOD, skip=("z-",))
    mb.box((-0.48, -1.0, 0.35), (0.48, -0.94, 0.8), WOOD)
    mb.box((-0.44, -0.94, 0.35), (0.44, 0.96, 0.5), IK.CLOTH[0])
    mb.box((-0.46, -0.1, 0.5), (0.46, 0.98, 0.53), IK.CLOTH[1])
    mb.box((-0.3, -0.9, 0.5), (0.3, -0.6, 0.6), IK.CLOTH[2])                  # almohada


def build_house_props(col, rng):
    out = {}
    for n, fn in (("MOR_Workbench", p_workbench), ("MOR_Bed_Simple", p_bed_simple)):
        mb = K.MB()
        fn(mb)
        o = IK.to_obj(mb, n, col)
        o.data.name = n
        o.location = (7000.0, -50.0, 0.0)
        o.hide_render = True
        out[n] = IK.tris(o)
    mb = K.MB()
    p_planter(mb, rng)
    o = IK.to_obj(mb, "MOR_Planter", col)
    o.data.name = "MOR_Planter"
    o.location = (7000.0, -50.0, 0.0)
    o.hide_render = True
    out["MOR_Planter"] = IK.tris(o)
    return out


# --------------------------------------------------------------------------- utilidades de plantilla
def decor(it, n, loc, yaw, tipo):
    return it.marker(f"MARKER_Decor_Slot_{n:02d}", loc, yaw, tipo=tipo,
                     note="slot de decoracion: Godot instancia aqui un prop elegido por el jugador")


def partial_ceiling(it, x0, x1, y0, y1, z, every=1.15, group="CEILING"):
    mb = K.MB()
    mb.box((x0, y0, z), (x1, y1, z + 0.1), WOOD, skip=("z+",))
    it.unique(mb, f"{it.name}_CeilingBoards", group)
    m = max(1, round((x1 - x0) / every))
    for i in range(m + 1):
        x = max(x0 + 0.12, min(x1 - 0.12, x0 + (x1 - x0) * i / m))
        it.inst("INT_Beam_Straight", Matrix.Translation((x, y0, z)) @ Matrix.Rotation(math.pi / 2, 4, "Z") @
                Matrix.Diagonal(((y1 - y0) / 2, 1, 1, 1)), group)


def put(it, mesh, mw, obst=None, level=0, group="Furniture", name=None):
    o = it.inst(mesh, mw, group, name=name)
    if obst:
        lo, hi = obst
        it.colboxes.append((lo, hi))
        it.obstacles.append((level, lo[0], lo[1], hi[0], hi[1]))
    return o


# --------------------------------------------------------------------------- Habitacion 4 x 5
def habitacion(col, rng):
    W, D, H = 4.0, 5.0, H_LOW
    it = IK.build_interior("Morada_Habitacion", (W, D, H), "entramado", seed=2801, world_rot_deg=TEMPLATE_ROT,
                           door=(0.0, D / 2), col=col, openings=[("+Y", 2.0, "door", 0), ("-Y", 3.0, "window", 0)],
                           ceiling=False)
    partial_ceiling(it, -W / 2, W / 2, -D / 2, D / 2, H)
    put(it, "MOR_Bed_Simple", M(-1.45, -1.2, 0, 0), obst=((-1.95, -2.2, 0), (-0.95, -0.2, 0.8)))
    put(it, "PROP_Q_Chest_Wood", M(-1.45, 0.35, 0, -90, 0.75, 0.75, 0.75), obst=((-1.85, 0.0, 0), (-1.05, 0.7, 0.7)))
    tc = place_trophy(it, "pared", M(-0.5, -2.3, 0, 0))
    it.obstacles.append((0, -1.0, -2.5, 0.0, -2.1))
    it.colboxes.append(((-1.0, -2.5, 0), (0.0, -2.1, 1.9)))
    put(it, "PROP_AV_Table", M(1.3, -1.5, 0, 0, 0.75, 0.75, 1.0), obst=((0.75, -2.05, 0), (1.85, -0.95, 0.76)))
    put(it, "PROP_Q_Stool", M(1.3, -0.65, 0), obst=((1.05, -0.9, 0), (1.55, -0.4, 0.6)))
    put(it, "PROP_Q_Candle_1", M(1.5, -1.6, 0.76))
    put(it, "BANK_Rug", M(-0.2, -0.6, 0.005, 90))
    it.light("LIGHT_Window", (1.0, -2.3, 1.7), "#FFE6C4", 0.45, 4.5, kind="omni_window")
    it.light("LIGHT_Candle", (1.5, -1.6, 1.0), "#FFA650", 0.35, 2.8)
    it.light("LIGHT_Shard", (-0.5, -2.1, 2.0), "#8FD0FF", 0.25, 2.0, kind="shard")    # el unico azul: lamparilla
    it.entry_markers(180.0, 0.0)
    it.marker("MARKER_Interact_Chest", (-1.45, 0.95, 0), 90.0, tipo="chest", slots=40)
    it.marker("MARKER_Interact_TrophyCase", (-0.5, -1.6, 0), 180.0, tipo="trophy_case", variante="pared")
    it.marker("MARKER_TrophyCase", (-0.5, -2.3, 0), 0.0, variante="pared")
    for n, (loc, yaw, tipo) in enumerate((((1.95, 0.3, 1.6), -90, "pared"), ((0.3, -2.45, 1.7), 0, "pared"),
                                          ((1.6, -1.35, 0.76), 0, "mesa"), ((1.6, 2.0, 0.0), 180, "suelo")), 1):
        decor(it, n, loc, yaw, tipo)
    it.nav_regions.append((0, 0.0, -W / 2, -D / 2, W / 2, D / 2))
    keys = {"spawn": (0.0, D / 2 - 1.6, 0.0), "baul": (-1.45, 0.95, 0.0), "vitrina": (-0.5, -1.6, 0.0),
            "mesa": (1.3, -0.1, 0.0)}
    return it, keys, {"walls": "revoco sobre zocalo de tablas", "window": "-Y (postigo y luz calida)"}


# --------------------------------------------------------------------------- Casa pequena 6 x 8 con patio
def casa_pequena(col, rng):
    W, D, H = 6.0, 8.0, H_LOW
    YP = 1.5                                                # tabique entre la casa (y < YP) y el patio (y > YP)
    it = IK.build_interior("Morada_Casa_Pequena", (W, D, H), "entramado", seed=2802, world_rot_deg=TEMPLATE_ROT,
                           door=(0.0, D / 2), col=col, openings=[("+Y", 3.0, "door", 0), ("-X", 6.0, "window", 0)],
                           ceiling=False)
    partial_ceiling(it, -W / 2, W / 2, -D / 2, YP, H)
    # tabique con puerta (oculto al entrar en la casa: WALL_Near_Casa)
    g = it.group("WALL_Near_Casa")
    g["hide_when"] = "jugador dentro de la casa (y < 1.5): el tabique del patio tapa la sala desde CAM_Iso"
    n = Vector((0, 1))
    start = Vector((-W / 2, YP))
    for s, mesh in ((0.0, "INT_Wall_Panel"), (2.0, "INT_Door_Int"), (4.0, "INT_Wall_Panel_B")):
        it.inst(mesh, IK.frame_mat(start, n, s, 0.0, 1.0, H / IK.FH), "WALL_Near_Casa")
    it.colboxes += [((-W / 2, YP - 0.4, 0), (-0.65, YP, H)), ((0.65, YP - 0.4, 0), (W / 2, YP, H))]
    it.obstacles += [(0, -W / 2, YP - 0.4, -0.65, YP), (0, 0.65, YP - 0.4, W / 2, YP)]
    # patio: losas, banco, hierbas en tiesto, lena
    mb = K.MB()
    mb.box((-W / 2, YP, 0.0), (W / 2, D / 2, 0.02), IK.SLAB, skip=("z-",))
    it.unique(mb, "MOR_Patio_Slabs", "Shell")
    put(it, "BANK_Bench", M(-2.4, 2.9, 0, -90, 0.6), obst=((-2.7, 2.2, 0), (-2.1, 3.6, 0.9)))
    put(it, "PROP_AV_Grain_Sack", M(2.5, 3.5, 0), obst=((2.3, 3.3, 0), (2.7, 3.7, 0.5)))
    put(it, "PROP_Herb_Rack", M(2.3, 2.2, 0, -90, 0.8, 0.8, 0.8), obst=((2.1, 1.7, 0), (2.5, 2.7, 1.3)))
    # casa (todo contra los muros del fondo -X / -Y: se ve de frente desde CAM_Iso)
    put(it, "INT_Fireplace", M(-2.95, -D / 2, 0, 0, 1.0, 1.0, H / IK.FH), obst=((-2.95, -4.0, 0), (-0.95, -3.25, 1.5)))
    place_trophy(it, "nichos", M(-0.1, -3.8, 0, 0))
    it.obstacles.append((0, -0.75, -4.0, 0.55, -3.6))
    it.colboxes.append(((-0.75, -4.0, 0), (0.55, -3.6, 1.6)))
    put(it, "MOR_Workbench", M(1.9, -3.55, 0, 0), obst=((1.1, -3.95, 0), (2.7, -3.15, 0.96)))
    put(it, "MOR_Bed_Simple", M(-2.5, -2.0, 0, 0), obst=((-3.0, -3.0, 0), (-2.0, -1.0, 0.8)))
    put(it, "PROP_Q_Chest_Wood", M(-2.6, 0.55, 0, -90, 0.85, 0.85, 0.85), obst=((-3.0, 0.1, 0), (-2.15, 1.0, 0.8)))
    put(it, "PROP_AV_Table", M(0.5, -1.2, 0), obst=((0.1, -1.9, 0), (0.9, -0.5, 0.76)))
    for y in (-1.6, -0.8):
        put(it, "PROP_Q_Chair_1", M(1.25, y, 0, -90, 0.85, 0.85, 0.85), obst=((1.0, y - 0.25, 0), (1.5, y + 0.25, 1.0)))
    put(it, "PROP_Q_CandleStick", M(0.5, -1.0, 0.76))
    put(it, "BANK_Rug", M(0.5, -1.2, 0.005, 0))
    it.light("LIGHT_Hearth", (-1.95, -3.3, 0.6), "#FF9A48", 1.0, 6.0)
    it.light("LIGHT_Window", (-2.8, -2.0, 1.7), "#FFE6C4", 0.45, 4.5, kind="omni_window")
    it.light("LIGHT_Candle", (0.5, -1.0, 1.15), "#FFA650", 0.35, 2.8)
    it.light("LIGHT_Patio", (0.0, 2.8, 2.6), "#FFE6C4", 0.6, 6.0, kind="omni_window")
    it.light("LIGHT_Shard", (-0.1, -3.6, 1.9), "#8FD0FF", 0.25, 2.0, kind="shard")
    it.entry_markers(180.0, 0.0)
    it.marker("MARKER_Interact_Chest", (-1.9, 0.55, 0), 90.0, tipo="chest", slots=100)
    it.marker("MARKER_WorkStation_01", (1.9, -2.9, 0), 180.0, tipo="workstation", nivel="basica")
    it.marker("MARKER_Interact_TrophyCase", (-0.1, -3.1, 0), 180.0, tipo="trophy_case", variante="nichos")
    it.marker("MARKER_TrophyCase", (-0.1, -3.8, 0), 0.0, variante="nichos")
    for n, (loc, yaw, tipo) in enumerate((((-2.95, -0.2, 1.7), -90, "pared"), ((1.2, -3.95, 1.8), 0, "pared"),
                                          ((0.3, -1.4, 0.76), 0, "mesa"), ((2.6, -2.4, 0.0), 0, "suelo"),
                                          ((-2.5, 3.6, 0.0), 0, "patio"), ((0.8, 3.7, 0.0), 0, "patio")), 1):
        decor(it, n, loc, yaw, tipo)
    it.nav_regions.append((0, 0.0, -W / 2, -D / 2, W / 2, D / 2))
    keys = {"spawn": (0.0, D / 2 - 1.6, 0.0), "patio": (0.0, 3.0, 0.0), "baul": (-1.9, 0.55, 0.0),
            "mesa_trabajo": (1.9, -2.9, 0.0), "vitrina": (-0.1, -3.1, 0.0), "hogar": (-1.6, -2.55, 0.0),
            "cama": (-1.6, -2.0, 0.0)}
    return it, keys, {"patio_m": [W, D / 2 - YP], "house_m": [W, YP + D / 2], "partition": "WALL_Near_Casa"}


# --------------------------------------------------------------------------- Casa grande 8 x 10, dos plantas
def casa_grande(col, rng):
    W, D, FHg = 8.0, 10.0, IK.FH
    H = 2 * FHg
    Y_UP = -1.0                                             # entreplanta sobre y < -1 (muro del fondo -Y)
    it = IK.build_interior("Morada_Casa_Grande", (W, D, H), "entramado", seed=2803, world_rot_deg=TEMPLATE_ROT,
                           door=(0.0, D / 2), col=col, storeys=2,
                           openings=[("+Y", 4.0, "door", 0), ("-X", 7.0, "window", 0), ("-Y", 5.0, "window", 1),
                                     ("-X", 2.0, "window", 1)], ceiling=False)
    partial_ceiling(it, -W / 2, W / 2, -D / 2, D / 2, H)
    # entreplanta (LEVEL_1) sobre la mitad del fondo, barandilla al borde, escalera de 1.2 m junto al muro -X
    g = it.group("LEVEL_1")
    g["hide_when"] = "jugador en la planta baja y la entreplanta tapa lo que hay debajo (corte isometrico)"
    f1 = it.group("Furniture_L1")
    f1.parent = g
    mb = K.MB()
    mb.box((-W / 2, -D / 2, FHg - 0.32), (W / 2, Y_UP, FHg - 0.14), WOOD)
    for x in (-2.0, 0.0, 2.0):
        mb.box((x - 0.1, -D / 2, FHg - 0.52), (x + 0.1, Y_UP, FHg - 0.32), WOOD)
    it.unique(mb, "MOR_Grande_UpperSlab", "LEVEL_1")
    for i in range(4):
        for j in range(3):
            dep = (D / 2 + Y_UP) / 3
            it.inst("INT_Floor_Planks_B" if (i + j) % 4 == 2 else "INT_Floor_Planks",
                    M(-W / 2 + 2.0 * i, -D / 2 + j * dep, FHg, 0, 1.0, dep / 2, 1.0), "LEVEL_1")
    for x0, sx in ((-2.8, 1.0), (-0.8, 1.0), (1.2, 1.0), (3.2, 0.4)):
        it.inst("INT_Railing", M(x0, Y_UP - 0.15, FHg, 0, sx, 1.0, 1.0), "LEVEL_1")
    y_top, y_foot = Y_UP - 0.3, Y_UP - 0.3 + 5.0              # 5.0 m de tramo: pie a 1.3 m del muro de la puerta
    it.inst("INT_Stairs_Int", M(-W / 2 + 1.2, y_foot, 0, 180, 1.2, 1.0, 1.0), "Shell")
    it.ramps.append((-W / 2, -W / 2 + 1.2, y_top, y_foot, FHg, 0.0))
    it.patches = [(-W / 2, -W / 2 + 1.2, y_top - 0.5, y_top, FHg), (-W / 2, -W / 2 + 1.2, y_foot, y_foot + 0.5, 0.0)]
    it.colprisms.append(([(y_top, FHg), (y_foot, 0.0), (y_top, 0.0)], -W / 2, -W / 2 + 1.2, "x"))
    it.obstacles += [(0, -W / 2, y_top, -W / 2 + 1.25, y_foot)]
    hs = (FHg - 0.56) / IK.FH                               # bajo la entreplanta: campana a 2.64 m (sin tocar vigas)
    # planta baja, fondo (bajo la entreplanta, muro -Y): hogar, vitrina de pared y dos mesas de oficio
    put(it, "INT_Fireplace", M(-3.9, -D / 2, 0, 0, 1.0, 1.0, hs), obst=((-3.9, -5.0, 0), (-1.9, -4.25, 1.5)))
    place_trophy(it, "pared", M(-1.0, -4.8, 0, 0))
    it.obstacles.append((0, -1.5, -5.0, -0.5, -4.6))
    it.colboxes.append(((-1.5, -5.0, 0), (-0.5, -4.6, 1.9)))
    put(it, "MOR_Workbench", M(1.0, -4.55, 0, 0), obst=((0.2, -4.95, 0), (1.8, -4.15, 0.96)))
    put(it, "MOR_Workbench", M(3.05, -4.55, 0, 0), obst=((2.25, -4.95, 0), (3.85, -4.15, 0.96)))
    put(it, "PROP_Q_Chest_Wood", M(-3.5, -2.6, 0, -90, 1.0, 1.0, 1.0), obst=((-4.0, -3.1, 0), (-3.0, -2.1, 1.0)))
    put(it, "PROP_AV_Grain_Sack", M(3.6, -3.3, 0), obst=((3.4, -3.5, 0), (3.8, -3.1, 0.5)))
    # planta baja, delante: sala para recibir (mesa, sillas, banco, alfombra) y vitrina de mesa
    put(it, "PROP_AV_Table", M(2.0, 2.2, 0, 90), obst=((1.3, 1.8, 0), (2.7, 2.6, 0.76)))
    for x in (1.3, 2.0, 2.7):
        put(it, "PROP_Q_Chair_1", M(x, 1.35, 0, 0, 0.85, 0.85, 0.85), obst=((x - 0.25, 1.1, 0), (x + 0.25, 1.6, 1.0)))
    put(it, "BANK_Bench", M(2.0, 3.05, 0, 180, 0.8), obst=((1.2, 2.85, 0), (2.8, 3.25, 0.9)))
    put(it, "BANK_Rug", M(2.0, 2.2, 0.005, 0, 1.2, 1.2, 1.0))
    put(it, "PROP_Q_Mug", M(1.8, 2.3, 0.76))
    put(it, "PROP_Q_CandleStick", M(2.3, 2.1, 0.76))
    place_trophy(it, "mesa", M(-1.4, 1.1, 0, 0), name="TROPHY_Mesa_Morada_Casa_Grande", first_slot=10)
    it.obstacles.append((0, -2.0, 0.8, -0.8, 1.4))
    it.colboxes.append(((-2.0, 0.8, 0), (-0.8, 1.4, 1.0)))
    # jardin de hierbas junto a la fachada (dentro, bajo la ventana del muro de la puerta)
    put(it, "MOR_Planter", M(2.6, 4.65, 0, 180), obst=((1.6, 4.4, 0), (3.6, 4.9, 0.45)))
    # planta alta: dormitorio
    put(it, "MOR_Bed_Simple", M(2.8, -3.6, FHg - 0.02, 90, 1.3, 1.0, 1.0),
        obst=((1.8, -4.2, FHg), (3.9, -3.0, FHg + 0.8)), level=1, group="Furniture_L1")
    put(it, "PROP_AV_Table", M(-0.5, -4.3, FHg - 0.02, 90, 0.7, 0.7, 1.0),
        obst=((-1.0, -4.7, FHg), (0.0, -3.9, FHg + 0.76)), level=1, group="Furniture_L1")
    put(it, "PROP_Q_Stool", M(-0.5, -3.5, FHg - 0.02), obst=((-0.75, -3.75, FHg), (-0.25, -3.25, FHg + 0.6)), level=1,
        group="Furniture_L1")
    put(it, "BANK_Rug", M(1.0, -2.3, FHg - 0.015, 0), group="Furniture_L1")
    it.light("LIGHT_Hearth", (-2.9, -4.3, 0.6), "#FF9A48", 1.0, 7.0)
    it.light("LIGHT_Window_Sala", (-3.8, -2.0, 1.7), "#FFE6C4", 0.45, 5.0, kind="omni_window")
    it.light("LIGHT_Candle", (2.3, 2.1, 1.15), "#FFA650", 0.35, 2.8)
    it.light("LIGHT_Lamp_Taller", (2.0, -3.6, 2.3), "#FFB46B", 0.6, 5.0)
    it.light("LIGHT_Window_Alta", (1.0, -4.8, FHg + 1.7), "#FFE6C4", 0.45, 4.5, kind="omni_window")
    it.light("LIGHT_Shard", (-1.0, -4.6, 2.0), "#8FD0FF", 0.25, 2.0, kind="shard")
    it.entry_markers(180.0, 0.0)
    it.marker("MARKER_Interact_Chest", (-2.4, -2.6, 0), 90.0, tipo="chest", slots=200)
    it.marker("MARKER_WorkStation_01", (1.0, -3.9, 0), 180.0, tipo="workstation", oficio="libre")
    it.marker("MARKER_WorkStation_02", (3.05, -3.9, 0), 180.0, tipo="workstation", oficio="libre")
    it.marker("MARKER_Interact_TrophyCase", (-1.0, -4.1, 0), 180.0, tipo="trophy_case", variante="pared")
    it.marker("MARKER_TrophyCase", (-1.0, -4.8, 0), 0.0, variante="pared")
    it.marker("MARKER_TrophyCase_02", (-1.4, 1.1, 0), 0.0, variante="mesa")
    it.marker("MARKER_Garden", (2.6, 4.65, 0.45), 180.0, tipo="garden", plantas=7,
              note="jardinera de hierbas junto a la fachada; Godot cambia las matas segun la cosecha")
    it.marker("MARKER_Reception", (2.0, 2.2, 0), 0.0, tipo="sala_visitas", asientos=4)
    for n, (loc, yaw, tipo, lv) in enumerate((((-3.95, 3.5, 1.7), -90, "pared", 0), ((-3.95, -3.6, 1.6), -90, "pared", 0),
                                              ((2.3, 2.4, 0.76), 0, "mesa", 0), ((3.5, 0.6, 0.0), 0, "suelo", 0),
                                              ((-3.95, -2.5, FHg + 1.5), -90, "pared", 1),
                                              ((-1.8, -4.95, FHg + 1.6), 0, "pared", 1), ((-2.6, -1.8, FHg), 0, "suelo", 1)), 1):
        e = decor(it, n, loc, yaw, tipo)
        e["level"] = lv
    it.nav_regions.append((0, 0.0, -W / 2, -D / 2, W / 2, D / 2))
    it.nav_regions.append((1, FHg, -W / 2, -D / 2, W / 2, Y_UP - 0.15))
    keys = {"spawn": (0.0, D / 2 - 1.6, 0.0), "sala": (2.0, 0.5, 0.0), "baul": (-2.4, -2.6, 0.0),
            "taller_1": (1.0, -3.7, 0.0), "taller_2": (3.05, -3.7, 0.0), "vitrina": (-1.0, -4.0, 0.0),
            "hogar": (-2.9, -3.8, 0.0), "jardin": (2.6, 3.9, 0.0), "dormitorio": (1.0, -2.0, FHg)}
    return it, keys, {"storeys": 2, "upper": "entreplanta de 4 m sobre el fondo (y < -1), suelo a 3.2 m",
                      "stair": "1.2 m de ancho junto al muro -X, 32.6 grados, rellano de 1.3 m al pie"}


TEMPLATES = {"habitacion": (habitacion, 8000), "casa_pequena": (casa_pequena, 15000), "casa_grande": (casa_grande, 28000)}
