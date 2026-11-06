"""
CONCORDIA - Etapa 19 (E6): distrito Este (Oficios). Piezas singulares y extras de los edificios del kit.
Cada edificio se reconoce por la SILUETA desde CAM_Iso (que mira al NO): por eso los rasgos van tambien en el tejado o
en los lados que ve la camara cuando la puerta mira hacia el otro lado.
Marco local de cada pieza: +Y = door_direction, base a z = 0 sobre el pad.
"""

import math
import random

import bpy  # noqa: F401,I001
from mathutils import Matrix, Vector

import bld_kit as K
import stage16_landmarks as L
import stage18_mercado as M

ST, LIGHT, GRAY, ROCK = "MAT_Limestone_Worn", "MAT_Limestone_Light", "MAT_Wall_Gray", "MAT_Rock_Gray"
WOOD, IRON, BRONZE, GLASS = K.M_WOOD, K.M_IRON, "MAT_Bronze_Aged", "MAT_Pipe_Glass"
WARM, WATER, SHARD, BEAM = "MAT_Window_Warm", "MAT_Water", "MAT_Shard_Blue", "MAT_Faro_Beam"
EMBERS, HERB, SOIL = "MAT_Embers", "MAT_Herb_Green", "MAT_Ground_Cracked"
CLOTH = K.M_CLOTH
ROOF, ROOF_B = K.M_ROOF, K.M_ROOF_B


def _lin(c):
    return ((c + 0.055) / 1.055) ** 2.4 if c > 0.04045 else c / 12.92


def ensure_materials():
    out = {}
    if EMBERS not in bpy.data.materials:
        m = bpy.data.materials.new(EMBERS)
        m.use_nodes = True
        b = m.node_tree.nodes["Principled BSDF"]
        b.inputs["Base Color"].default_value = (_lin(0.16), _lin(0.10), _lin(0.07), 1)
        b.inputs["Roughness"].default_value = 0.9
        b.inputs["Emission Color"].default_value = (_lin(0.878), _lin(0.604), _lin(0.384), 1)    # #E09A62
        b.inputs["Emission Strength"].default_value = 1.5
        m["note"] = "brasas / metal fundido: naranja calido NATURAL (no magico), emision 1.5, #E09A62"
        out[EMBERS] = "creado"
    if HERB not in bpy.data.materials:
        m = bpy.data.materials.new(HERB)
        m.use_nodes = True
        b = m.node_tree.nodes["Principled BSDF"]
        b.inputs["Base Color"].default_value = (_lin(0.431), _lin(0.482), _lin(0.345), 1)        # #6E7B58 apagado
        b.inputs["Roughness"].default_value = 0.9
        m["note"] = "hierbas: verde apagado #6E7B58 (saturacion 0.28)"
        out[HERB] = "creado"
    return out


# ---------------------------------------------------------------------------
# utilidades
# ---------------------------------------------------------------------------
def cyl(mb, cx, cy, r, z0, z1, n, mat, caps=True, r1=None):
    mb.cylinder(r, z0, z1, n, mat, r1=r1, caps=caps, center=(cx, cy))


def cyl_axis(mb, a, b, r, n, mat, caps=True):
    """Cilindro entre dos puntos (eje cualquiera)."""
    a, b = Vector(a), Vector(b)
    d = b - a
    q = d.normalized().to_track_quat("Z", "Y")
    mb.push(Matrix.Translation(a) @ q.to_matrix().to_4x4())
    mb.cylinder(r, 0.0, d.length, n, mat, caps=caps)
    mb.pop()


def clump(mb, x, y, z, r, h, mat=HERB, n=5):
    """Mata de hierbas: piramide baja de n lados."""
    pts = [(x + r * math.cos(2 * math.pi * i / n), y + r * math.sin(2 * math.pi * i / n), z) for i in range(n)]
    for i in range(n):
        j = (i + 1) % n
        mb.face([pts[i], pts[j], (x, y, z + h)], mat, nrm=(pts[i][0] + pts[j][0] - 2 * x, pts[i][1] + pts[j][1] - 2 * y, r))


def bulb(mb, x, y, z, r, mat=GLASS):
    """Esfera tosca (octaedro estirado) para matraces y piedras."""
    pts = [(x + r, y, z), (x, y + r, z), (x - r, y, z), (x, y - r, z)]
    for i in range(4):
        j = (i + 1) % 4
        mb.face([pts[i], pts[j], (x, y, z + r * 1.2)], mat, nrm=(pts[i][0] + pts[j][0] - 2 * x, pts[i][1] + pts[j][1] - 2 * y, 0.5))
        mb.face([pts[j], pts[i], (x, y, z - r)], mat, nrm=(pts[i][0] + pts[j][0] - 2 * x, pts[i][1] + pts[j][1] - 2 * y, -0.5))


def anvil(mb):
    """Yunque sobre tocon (origen en el suelo)."""
    cyl(mb, 0, 0, 0.32, 0.0, 0.6, 8, WOOD)
    mb.box((-0.18, -0.12, 0.6), (0.18, 0.12, 0.72), IRON)
    mb.box((-0.12, -0.08, 0.72), (0.12, 0.08, 0.82), IRON, skip=("z-",))
    mb.box((-0.32, -0.13, 0.82), (0.3, 0.13, 0.98), IRON)
    mb.prism([(0.3, 0.82), (0.55, 0.92), (0.55, 0.96), (0.3, 0.98)], -0.06, 0.06, IRON)


def mine_cart(mb):
    """Vagoneta de mina (1.2 x 0.8), ruedas de 0.36 sobre carriles de 1.0 de via."""
    mb.prism([(-0.6, 0.35), (0.6, 0.35), (0.7, 1.0), (-0.7, 1.0)], -0.42, 0.42, WOOD)
    for x in (-0.45, 0.45):
        mb.box((x - 0.04, -0.44, 0.35), (x + 0.04, 0.44, 0.98), IRON, skip=("z-", "z+"))
    mb.face([(-0.65, -0.38, 0.9), (0.65, -0.38, 0.9), (0.65, 0.38, 0.9), (-0.65, 0.38, 0.9)], ROCK, nrm=(0, 0, 1))
    for x in (-0.4, 0.4):
        for y in (-0.5, 0.5):
            cyl_axis(mb, (x, y - 0.04 * (1 if y > 0 else -1), 0.18), (x, y + 0.04 * (1 if y > 0 else -1), 0.18), 0.18, 8, IRON)


def boat(mb, L4=4.0):
    """Barca de 4 m: casco por secciones (madera), bancada y remos."""
    secs = [(-2.0, 0.05, 0.55), (-1.4, 0.55, 0.45), (0.0, 0.75, 0.42), (1.3, 0.55, 0.45), (2.0, 0.05, 0.6)]
    prev = None
    for x, hw, zt in secs:
        cur = [(x, -hw, zt), (x, -hw * 0.6, 0.05), (x, hw * 0.6, 0.05), (x, hw, zt)]
        if prev:
            for i in range(3):
                mb.face([prev[i], prev[i + 1], cur[i + 1], cur[i]], WOOD, nrm=(0, (prev[i][1] + cur[i + 1][1]) * 0.5, -0.3))
                mb.face([prev[i + 1], prev[i], cur[i], cur[i + 1]], WOOD, nrm=(0, -(prev[i][1] + cur[i + 1][1]) * 0.5, 0.3))
        prev = cur
    mb.box((-0.15, -0.6, 0.3), (0.15, 0.6, 0.36), WOOD)
    for s in (-1, 1):
        mb.rod((-0.2, s * 0.5, 0.42), (1.2, s * 0.7, 0.3), 0.025, WOOD)


def net_frame(mb, w=2.4, h=2.2, rng=None):
    """Red colgada en dos postes: cuerdas en rejilla y un pano abolsado (cara +Y)."""
    for x in (-w / 2, w / 2):
        mb.box((x - 0.06, -0.06, 0.0), (x + 0.06, 0.06, h + 0.3), WOOD, skip=("z-",))
    mb.rod((-w / 2, 0, h + 0.2), (w / 2, 0, h + 0.2), 0.04, WOOD)
    for k in range(7):
        x = -w / 2 + 0.15 + (w - 0.3) * k / 6
        mb.rod((x, 0.0, h + 0.2), (x + 0.05, 0.12, 0.5), 0.008, WOOD)
    for z in (0.7, 1.2, 1.7):
        mb.rod((-w / 2 + 0.1, 0.1, z), (w / 2 - 0.1, 0.1, z), 0.008, WOOD)


def target(mb):
    """Blanco de tiro: diana de paja (disco) en caballete, anillos de tela."""
    for x in (-0.45, 0.45):
        mb.rod((x, -0.3, 0.0), (x * 0.6, 0.0, 1.5), 0.04, WOOD)
    mb.rod((0.0, 0.5, 0.0), (0.0, 0.05, 1.3), 0.04, WOOD)
    pts = lambda r: [(r * math.cos(2 * math.pi * i / 12), 0.06, 1.05 + r * math.sin(2 * math.pi * i / 12)) for i in range(12)]  # noqa: E731
    cyl_axis(mb, (0, 0.0, 1.05), (0, 0.06, 1.05), 0.6, 12, CLOTH[2], caps=False)
    mb.face(pts(0.6), CLOTH[2], nrm=(0, 1, 0))
    mb.face([(x, 0.065, z) for x, _, z in pts(0.38)], CLOTH[1], nrm=(0, 1, 0))
    mb.face([(x, 0.07, z) for x, _, z in pts(0.16)], CLOTH[0], nrm=(0, 1, 0))


def hide_rack(mb, w=1.6, h=1.3, mat=None):
    """Bastidor con piel estirada (cara +Y), sobre dos patas."""
    mat = mat or CLOTH[2]
    for x in (-w / 2, w / 2):
        mb.box((x - 0.05, -0.05, 0.0), (x + 0.05, 0.05, h + 1.0), WOOD, skip=("z-",))
    for z in (0.8, 0.8 + h):
        mb.box((-w / 2, -0.04, z - 0.04), (w / 2, 0.04, z + 0.04), WOOD, skip=("x-", "x+"))
    pts = [(-w / 2 + 0.15, 0.0, 0.95), (w / 2 - 0.2, 0.0, 0.9), (w / 2 - 0.12, 0.0, 0.8 + h - 0.12),
           (0.0, 0.0, 0.8 + h - 0.05), (-w / 2 + 0.12, 0.0, 0.8 + h - 0.15)]
    mb.face(pts, mat, nrm=(0, 1, 0))
    mb.face(pts[::-1], mat, nrm=(0, -1, 0))


def antlers(mb, s=1.0):
    """Cornamenta (hueso claro) clavada en un escudo de madera, cara +Y."""
    mb.box((-0.25 * s, 0.0, -0.35 * s), (0.25 * s, 0.06, 0.2 * s), WOOD, skip=("y-",))
    for sg in (-1, 1):
        a = (sg * 0.1 * s, 0.1, 0.1 * s)
        b = (sg * 0.55 * s, 0.25, 0.6 * s)
        c = (sg * 0.75 * s, 0.25, 1.1 * s)
        mb.rod(a, b, 0.035 * s, LIGHT)
        mb.rod(b, c, 0.03 * s, LIGHT)
        mb.rod(b, (sg * 0.35 * s, 0.3, 0.95 * s), 0.025 * s, LIGHT)
        mb.rod(((b[0] + c[0]) / 2, 0.25, (b[2] + c[2]) / 2), (sg * 1.0 * s, 0.3, 0.95 * s), 0.022 * s, LIGHT)


def log_pile(mb, length=4.0, r=0.28, rows=3):
    k = 0
    for row in range(rows):
        n = rows - row
        for i in range(n):
            y = (i - (n - 1) / 2) * 2 * r
            z = r + row * r * 1.7
            cyl_axis(mb, (-length / 2, y, z), (length / 2, y, z), r, 7, WOOD)
            k += 1
    return k


def alembic(mb, x, y, z):
    """Alambique: matraz de vidrio sobre un hornillo de hierro, cuello y serpentin de bronce."""
    mb.box((x - 0.2, y - 0.2, z), (x + 0.2, y + 0.2, z + 0.3), IRON, skip=("z-",))
    bulb(mb, x, y, z + 0.55, 0.25)
    mb.rod((x, y, z + 0.8), (x + 0.35, y, z + 1.05), 0.025, BRONZE)
    mb.rod((x + 0.35, y, z + 1.05), (x + 0.55, y, z + 0.6), 0.025, BRONZE)
    bulb(mb, x + 0.6, y, z + 0.4, 0.13)


def magnifier(mb):
    """Lupa de bronce colgada (cara +Y): aro, cristal y mango."""
    ring = [(0.35 * math.cos(2 * math.pi * i / 12), 0.35 * math.sin(2 * math.pi * i / 12)) for i in range(12)]
    L.rod_path(mb, ring, 0.0, 0.035, BRONZE, closed=True)
    mb.face([(x, 0.0, z) for x, z in ring], GLASS, nrm=(0, 1, 0))
    mb.rod((0.0, 0.0, -0.35), (0.0, 0.0, -0.9), 0.04, BRONZE)
    mb.rod((0.0, 0.0, 0.35), (0.0, 0.0, 0.7), 0.012, IRON)


def stone_ring_wall(mb, r_out, r_in, z0, z1, n, mat, t0=0.0, t1=2 * math.pi):
    for i in range(n):
        a, b = t0 + (t1 - t0) * i / n, t0 + (t1 - t0) * (i + 1) / n
        po = [(r_out * math.cos(t), r_out * math.sin(t)) for t in (a, b)]
        pi_ = [(r_in * math.cos(t), r_in * math.sin(t)) for t in (a, b)]
        m = (a + b) / 2
        mb.face([(*po[0], z0), (*po[1], z0), (*po[1], z1), (*po[0], z1)], mat, nrm=(math.cos(m), math.sin(m), 0))
        mb.face([(*pi_[1], z0), (*pi_[0], z0), (*pi_[0], z1), (*pi_[1], z1)], mat, nrm=(-math.cos(m), -math.sin(m), 0))
        mb.face([(*po[0], z1), (*po[1], z1), (*pi_[1], z1), (*pi_[0], z1)], mat, nrm=(0, 0, 1))


# ---------------------------------------------------------------------------
# extras de edificios del kit (se anaden al Body / Roof o como props)
# ---------------------------------------------------------------------------
def mineros_extras(body, roof, W, D, door_x, ridge):
    """Bocamina en la fachada (marco de madera ataludado + roca), pico gigante de 3 m dorado y castillete en el tejado
    (la silueta que ve la camara aunque la fachada mire al otro lado)."""
    y = D / 2
    for s in (-1, 1):
        body.rod((door_x + s * 1.45, y + 0.07, 0.0), (door_x + s * 1.15, y + 0.07, 3.1), 0.12, WOOD)
    body.box((door_x - 1.5, y, 3.05), (door_x + 1.5, y + 0.2, 3.35), WOOD, skip=("y-",))
    rng = random.Random(7)
    for k in range(11):
        a = math.pi * k / 10
        cx, cz = door_x - 2.0 * math.cos(a), 0.4 + 3.3 * math.sin(a)
        w, h = rng.uniform(0.5, 0.8), rng.uniform(0.45, 0.7)
        body.box((cx - w / 2, y, cz - h / 2), (cx + w / 2, y + 0.13, cz + h / 2), ROCK, skip=("y-",))
    # pico de 3 m sobre la puerta (mango de madera + cabeza curva de bronce)
    a, b = Vector((door_x - 1.2, y + 0.15, 3.9)), Vector((door_x + 1.3, y + 0.15, 5.4))
    body.rod(tuple(a), tuple(b), 0.06, WOOD)
    hc = b + Vector((0.05, 0, 0.05))
    body.rod(tuple(hc), tuple(hc + Vector((-0.6, 0, 0.55))), 0.08, BRONZE)
    body.rod(tuple(hc + Vector((-0.6, 0, 0.55))), tuple(hc + Vector((-1.2, 0, 0.75))), 0.06, BRONZE)
    body.rod(tuple(hc), tuple(hc + Vector((0.55, 0, -0.5))), 0.08, BRONZE)
    body.rod(tuple(hc + Vector((0.55, 0, -0.5))), tuple(hc + Vector((0.95, 0, -1.05))), 0.06, BRONZE)
    for t in (0.25, 0.75):
        p = a.lerp(b, t)
        body.box((p.x - 0.05, y, p.z - 0.05), (p.x + 0.05, y + 0.2, p.z + 0.05), IRON, skip=("y-",))
    # castillete de madera con polea sobre la cumbrera
    z0 = ridge - 0.2
    top = z0 + 5.5
    for s in (-1, 1):
        roof.rod((s * 1.4, -1.2, z0), (s * 0.35, 0.0, top), 0.11, WOOD)
        roof.rod((s * 1.4, 1.2, z0), (s * 0.35, 0.0, top), 0.11, WOOD)
        roof.rod((s * 1.2, -1.0, z0 + 2.0), (s * 1.2, 1.0, z0 + 2.0), 0.07, WOOD)
    roof.rod((-1.15, 0.0, z0 + 2.0), (1.15, 0.0, z0 + 2.0), 0.07, WOOD)
    roof.box((-0.5, -0.2, top - 0.1), (0.5, 0.2, top + 0.12), WOOD)
    ring = [(1.0 * math.cos(2 * math.pi * i / 12), top + 0.9 + 1.0 * math.sin(2 * math.pi * i / 12)) for i in range(12)]
    L.rod_path(roof, ring, 0.0, 0.06, IRON, closed=True)
    for k in range(4):
        aa = math.pi / 4 * k
        roof.rod((1.0 * math.cos(aa), 0.0, top + 0.9 + 1.0 * math.sin(aa)),
                 (-1.0 * math.cos(aa), 0.0, top + 0.9 - 1.0 * math.sin(aa)), 0.03, IRON)
    roof.rod((0.95, 0.0, top + 0.9), (0.95, D / 2 - 1.0, z0 - 1.5), 0.015, IRON)
    return {"headframe_top_m": round(top + 1.9, 2), "pick_m": round((b - a).length + 0.4, 2)}


def rails(mb, length=5.0, gauge=1.0):
    for x in (-gauge / 2, gauge / 2):
        mb.box((x - 0.035, 0.0, 0.08), (x + 0.035, length, 0.15), IRON, skip=("z-",))
    k = 0
    y = 0.3
    while y < length:
        mb.box((-0.75, y - 0.1, 0.0), (0.75, y + 0.1, 0.08), WOOD, skip=("z-",))
        y += 0.65
        k += 1
    return k


def forja_yard(mb, x0, x1, hy, rng):
    """Fundicion al aire libre en el patio [x0, x1] x [-hy, hy]: muro bajo, horno con crisol (brasas 1.5), moldes,
    pila de carbon, abrevadero de temple. Devuelve posiciones locales (yunques, vapor)."""
    for (a, b, c, d) in ((x0, -hy, x1, -hy + 0.4), (x0, hy - 0.4, x1, hy), (x1 - 0.4, -hy + 0.4, x1, -1.6),
                         (x1 - 0.4, 1.6, x1, hy - 0.4)):
        mb.box((a, b, 0.0), (c, d, 1.0), ST, skip=("z-",))
    cx = (x0 + x1) / 2
    # horno de fundicion con crisol
    mb.box((cx - 1.2, -1.2, 0.0), (cx + 1.2, 1.2, 1.2), ROCK, skip=("z-",))
    cyl(mb, cx, 0.0, 0.7, 1.2, 1.9, 10, IRON, caps=False, r1=0.8)
    mb.face([(cx + 0.72 * math.cos(2 * math.pi * i / 10), 0.72 * math.sin(2 * math.pi * i / 10), 1.8) for i in range(10)], EMBERS,
            nrm=(0, 0, 1))
    mb.face([(cx - 0.5, 1.21, 0.2), (cx + 0.5, 1.21, 0.2), (cx + 0.5, 1.21, 0.8), (cx - 0.5, 1.21, 0.8)], EMBERS, nrm=(0, 1, 0))
    for s in (-1, 1):
        mb.rod((cx + s * 0.95, -0.9, 1.2), (cx + s * 0.95, -0.9, 3.0), 0.06, IRON)
    mb.rod((cx - 0.95, -0.9, 3.0), (cx + 0.95, -0.9, 3.0), 0.06, IRON)
    # moldes, carbon, abrevadero
    for k in range(4):
        x = x0 + 1.2 + k * 0.9
        mb.box((x - 0.35, -hy + 1.2, 0.0), (x + 0.35, -hy + 2.0, 0.35), GRAY, skip=("z-",))
    cyl(mb, x1 - 1.6, -hy + 2.0, 1.1, 0.0, 0.9, 7, "MAT_Iron_Black", caps=False, r1=0.15)
    mb.box((x0 + 1.0, hy - 2.2, 0.0), (x0 + 3.4, hy - 1.4, 0.7), WOOD, skip=("z-",))
    mb.face([(x0 + 1.08, hy - 2.12, 0.62), (x0 + 3.32, hy - 2.12, 0.62), (x0 + 3.32, hy - 1.48, 0.62), (x0 + 1.08, hy - 1.48, 0.62)],
            WATER, nrm=(0, 0, 1))
    anvils = [(cx - 2.2, 2.2), (cx + 1.9, 2.6), (x0 + 1.5, 0.2)]
    return {"anvils": anvils, "steam": (x0 + 2.2, hy - 1.8, 0.8), "crucible": (cx, 0.0, 1.9)}


def chimney_tall(mb, x, y, z0, h, w0=1.8, w1=1.2):
    """Chimenea de piedra ataludada (w0 -> w1) de z0 a h, con remate."""
    pts0 = [(x - w0 / 2, y - w0 / 2), (x + w0 / 2, y - w0 / 2), (x + w0 / 2, y + w0 / 2), (x - w0 / 2, y + w0 / 2)]
    pts1 = [(x - w1 / 2, y - w1 / 2), (x + w1 / 2, y - w1 / 2), (x + w1 / 2, y + w1 / 2), (x - w1 / 2, y + w1 / 2)]
    for i in range(4):
        j = (i + 1) % 4
        nx, ny = (pts0[i][0] + pts0[j][0]) / 2 - x, (pts0[i][1] + pts0[j][1]) / 2 - y
        mb.face([(*pts0[i], z0), (*pts0[j], z0), (*pts1[j], h - 0.6), (*pts1[i], h - 0.6)], ST, nrm=(nx, ny, 0.05))
    mb.box((x - w1 / 2 - 0.15, y - w1 / 2 - 0.15, h - 0.6), (x + w1 / 2 + 0.15, y + w1 / 2 + 0.15, h), ST)
    mb.face([(x - w1 / 2 + 0.1, y - w1 / 2 + 0.1, h + 0.001), (x + w1 / 2 - 0.1, y - w1 / 2 + 0.1, h + 0.001),
             (x + w1 / 2 - 0.1, y + w1 / 2 - 0.1, h + 0.001), (x - w1 / 2 + 0.1, y + w1 / 2 - 0.1, h + 0.001)], IRON, nrm=(0, 0, 1))


def vats(mb, xs, y):
    """Tinas de curtido de madera (r 0.9, h 0.9) con liquido."""
    for x in xs:
        cyl(mb, x, y, 0.9, 0.0, 0.9, 10, WOOD, caps=False)
        for z in (0.2, 0.75):
            cyl(mb, x, y, 0.93, z - 0.04, z + 0.04, 10, IRON, caps=False)
        mb.face([(x + 0.86 * math.cos(2 * math.pi * i / 10), y + 0.86 * math.sin(2 * math.pi * i / 10), 0.75) for i in range(10)],
                "MAT_Ash_Gray", nrm=(0, 0, 1))


def loggia(mb, roof, W, D, z0, h, rng):
    """Planta abierta de telares sobre una azotea: postes, antepecho, 2 telares visibles, cubierta a dos aguas."""
    hw, hd = W / 2, D / 2
    for x in [-hw + 0.2 + (W - 0.4) * k / 5 for k in range(6)]:
        for y in (-hd + 0.2, hd - 0.2):
            mb.box((x - 0.12, y - 0.12, z0), (x + 0.12, y + 0.12, z0 + h), WOOD, skip=("z-", "z+"))
    for y in [-hd + 0.2 + (D - 0.4) * k / 3 for k in (1, 2)]:
        for x in (-hw + 0.2, hw - 0.2):
            mb.box((x - 0.12, y - 0.12, z0), (x + 0.12, y + 0.12, z0 + h), WOOD, skip=("z-", "z+"))
    mb.box((-hw, -hd, z0 + h - 0.25), (hw, hd, z0 + h), WOOD, skip=("z-",))
    for (a, b, c, d) in ((-hw, -hd, hw, -hd + 0.15), (-hw, hd - 0.15, hw, hd), (-hw, -hd, -hw + 0.15, hd), (hw - 0.15, -hd, hw, hd)):
        mb.box((a, b, z0 + 0.85), (c, d, z0 + 0.95), WOOD)
    mb.face([(-hw, -hd, z0 + 0.01), (hw, -hd, z0 + 0.01), (hw, hd, z0 + 0.01), (-hw, hd, z0 + 0.01)], WOOD, nrm=(0, 0, 1))
    for k, x in enumerate((-hw / 2, hw / 2)):
        mb.push(Matrix.Translation((x, 0.0, z0)))
        for xx in (-0.9, 0.9):
            for yy in (-0.6, 0.6):
                mb.box((xx - 0.05, yy - 0.05, 0.0), (xx + 0.05, yy + 0.05, 1.7), WOOD, skip=("z-",))
        mb.box((-0.95, -0.65, 1.6), (0.95, 0.65, 1.7), WOOD)
        cl = CLOTH[k % 3]
        mb.face([(-0.8, 0.0, 0.9), (0.8, 0.0, 0.9), (0.8, 0.0, 1.6), (-0.8, 0.0, 1.6)], cl, nrm=(0, 1, 0))
        mb.face([(-0.8, 0.0, 0.9), (0.8, 0.0, 0.9), (0.8, -0.6, 0.85), (-0.8, -0.6, 0.85)], cl, nrm=(0, 0, 1))
        mb.pop()
    roof.push(Matrix.Translation((0, 0, z0 + h)))
    ridge = K.roof_gable(roof, W, D, pitch=35.0, eave=0.6, rng=rng, repairs=2)
    roof.pop()
    for sx in (-1, 1):                               # hastiales abiertos con tirante y pendolon
        roof.rod((sx * hw, -hd, z0 + h), (sx * hw, hd, z0 + h), 0.07, WOOD)
        roof.rod((sx * hw, 0.0, z0 + h), (sx * hw, 0.0, z0 + h + ridge), 0.06, WOOD)
    return z0 + h + ridge


def hanging_cloths(mb, side_len, y_face, z_top, rng, n=4, drop=1.9):
    """Telas colgando de una baranda (cara +Y del marco actual)."""
    for k in range(n):
        x = -side_len / 2 + side_len * (k + 0.5) / n + rng.uniform(-0.2, 0.2)
        w = rng.uniform(0.5, 0.9)
        cl = CLOTH[rng.randrange(3)]
        q = [(x - w / 2, y_face, z_top), (x + w / 2, y_face, z_top), (x + w / 2, y_face + 0.05, z_top - drop),
             (x - w / 2, y_face + 0.05, z_top - drop)]
        mb.face(q, cl, nrm=(0, 1, 0))
        mb.face(q[::-1], cl, nrm=(0, -1, 0))


def waterwheel(mb, d=3.5, width=1.0, n=16):
    """Rueda hidraulica de paletas (eje = Y local, centro en el origen): 2 llantas, 8 radios por lado, n paletas y cubo."""
    r = d / 2
    for y in (-width / 2, width / 2):
        L.rod_path(mb, [(r * math.cos(2 * math.pi * i / n), r * math.sin(2 * math.pi * i / n)) for i in range(n)], y, 0.06, WOOD,
                   closed=True)
        for k in range(8):
            a = 2 * math.pi * k / 8
            mb.rod((0.2 * math.cos(a), y, 0.2 * math.sin(a)), (r * math.cos(a), y, r * math.sin(a)), 0.05, WOOD)
    for i in range(n):
        a = 2 * math.pi * (i + 0.5) / n
        c = Vector((r * math.cos(a), 0.0, r * math.sin(a)))
        t = Vector((-math.sin(a), 0, math.cos(a)))
        o = Vector((math.cos(a), 0, math.sin(a)))
        p = [c - o * 0.3 + t * 0.03, c + o * 0.15 + t * 0.03, c + o * 0.15 - t * 0.03, c - o * 0.3 - t * 0.03]
        q0 = [Vector((v.x, -width / 2, v.z)) for v in p]
        q1 = [Vector((v.x, width / 2, v.z)) for v in p]
        for j in range(4):
            jj = (j + 1) % 4
            mid = (q0[j] + q0[jj]) / 2
            mb.face([tuple(q0[j]), tuple(q0[jj]), tuple(q1[jj]), tuple(q1[j])], WOOD, nrm=(mid.x - c.x, 0, mid.z - c.z))
    cyl_axis(mb, (0, -width / 2 - 0.1, 0), (0, width / 2 + 0.1, 0), 0.22, 8, IRON)


# ---------------------------------------------------------------------------
# edificios hechos a mano: devuelven (body, roof, info, mass) - mass = volumetria para el LOD2
# ---------------------------------------------------------------------------
def herbolarios(rng, W=22.0, D=12.0):
    """Invernadero de vidrio (alpha 0.35) y madera de 16 x 7 con 3 bancales dentro, y terrazas de hierbas de 3
    escalones delante y a los lados."""
    body, roof = K.MB(), K.MB()
    gw, gd = 8.0, 3.6                    # semiancho / semifondo del invernadero
    cy = -1.4
    y0, y1 = cy - gd, cy + gd
    wall_h, z_e, z_r = 0.6, 3.2, 5.6
    # zocalo
    for (a, b, c, d) in ((-gw, y0, gw, y0 + 0.3), (-gw, y1 - 0.3, -0.8, y1), (0.8, y1 - 0.3, gw, y1),
                         (-gw, y0 + 0.3, -gw + 0.3, y1 - 0.3), (gw - 0.3, y0 + 0.3, gw, y1 - 0.3)):
        body.box((a, b, 0.0), (c, d, wall_h), ST, skip=("z-",))
    # vidrio: paredes y hastiales
    for y, s in ((y0, -1), (y1, 1)):
        body.face([(-gw, y, wall_h), (gw, y, wall_h), (gw, y, z_e), (-gw, y, z_e)], GLASS, nrm=(0, s, 0))
    for x, s in ((-gw, -1), (gw, 1)):
        body.face([(x, y0, wall_h), (x, y1, wall_h), (x, y1, z_e), (x, cy, z_r), (x, y0, z_e)], GLASS, nrm=(s, 0, 0))
    # estructura de madera
    xs = [-gw + 2.0 * k for k in range(9)]
    for x in xs:
        for y in (y0, y1):
            body.box((x - 0.07, y - 0.07, wall_h), (x + 0.07, y + 0.07, z_e), WOOD, skip=("z-", "z+"))
        for y in (y0, y1):
            roof.rod((x, y, z_e), (x, cy, z_r), 0.06, WOOD)
    for y in (y0, y1):
        body.box((-gw, y - 0.06, z_e - 0.12), (gw, y + 0.06, z_e), WOOD)
        body.box((-gw, y - 0.05, 1.9), (gw, y + 0.05, 1.98), WOOD, skip=("x-", "x+"))
    roof.box((-gw - 0.1, cy - 0.1, z_r - 0.05), (gw + 0.1, cy + 0.1, z_r + 0.12), WOOD)
    for sgn, ye in ((-1, y0), (1, y1)):
        roof.face([(-gw, ye, z_e + 0.02), (gw, ye, z_e + 0.02), (gw, cy, z_r + 0.02), (-gw, cy, z_r + 0.02)], GLASS,
                  nrm=(0, sgn * 0.6, 1))
    # puerta (marco) y bancales interiores con matas
    body.box((-0.8, y1 - 0.1, 0.0), (-0.65, y1 + 0.1, 2.4), WOOD)
    body.box((0.65, y1 - 0.1, 0.0), (0.8, y1 + 0.1, 2.4), WOOD)
    body.box((-0.8, y1 - 0.1, 2.3), (0.8, y1 + 0.1, 2.45), WOOD)
    for k, yb in enumerate((cy - 2.2, cy, cy + 2.2)):
        if k == 2:
            continue
        body.box((-gw + 0.8, yb - 0.5, 0.0), (gw - 0.8, yb + 0.5, 0.7), WOOD, skip=("z-",))
        body.face([(-gw + 0.85, yb - 0.45, 0.7), (gw - 0.85, yb - 0.45, 0.7), (gw - 0.85, yb + 0.45, 0.7), (-gw + 0.85, yb + 0.45, 0.7)],
                  SOIL, nrm=(0, 0, 1))
        for i in range(12):
            clump(body, -gw + 1.3 + i * 1.18, yb + rng.uniform(-0.2, 0.2), 0.7, 0.28, rng.uniform(0.3, 0.6))
    # terrazas de hierbas: 3 escalones (0.25 m) delante y a los lados
    n_cl = 0
    for k in range(3):
        z = 0.25 * (3 - k)
        a = y1 + 0.4 + 0.6 * k
        body.box((-W / 2 + 0.3, a, 0.0), (W / 2 - 0.3, a + 0.6, z), ST, skip=("z-",))
        for i in range(int((W - 1.0) / 0.9)):
            x = -W / 2 + 0.8 + i * 0.9
            if abs(x) < 1.0:
                continue
            clump(body, x, a + 0.3, z, 0.25, rng.uniform(0.25, 0.5))
            n_cl += 1
    for s in (-1, 1):
        for k in range(3):
            z = 0.25 * (3 - k)
            xa = s * (gw + 0.3 + 0.6 * k)
            xa, xb = sorted((xa, xa + s * 0.6))
            body.box((xa, y0, 0.0), (xb, y1, z), ST, skip=("z-",))
            for i in range(int((y1 - y0) / 0.9)):
                clump(body, (xa + xb) / 2, y0 + 0.4 + i * 0.9, z, 0.25, rng.uniform(0.25, 0.5))
                n_cl += 1
    body.finish()
    roof.finish()
    mass = [("box", (-gw, y0, 0.0), (gw, y1, z_e)), ("gable", -gw, gw, gd, z_e, z_r, cy),
            ("box", (-W / 2 + 0.3, y1 + 0.4, 0.0), (W / 2 - 0.3, y1 + 2.2, 0.6))]
    return body, roof, {"greenhouse": [2 * gw, 2 * gd, z_r], "herb_clumps": n_cl, "door": (0.0, y1, 0.0),
                        "interior": ((0.0, cy), (2 * gw - 0.6, 2 * gd - 0.6, z_e))}, mass


def alquimia(rng, W=16.0, D=12.0):
    """Torre estrecha de 4 plantas (6.5 x 6.5, 12.8 m + cubierta conica) con ventanas redondas, 2 balcones con
    alambiques, 2 chimeneas y un patio con tapia baja."""
    body, roof = K.MB(), K.MB()
    s = 3.25
    cyc = 0.5                                          # la torre algo adelantada en la parcela
    H = 12.8
    for side in ("+Y", "-Y", "+X", "-X"):
        fr = Matrix.Translation((0, cyc, 0)) @ L.frame(side, s, s)
        body.push(fr)
        holes = []
        for f in range(4):
            zc = 1.9 + 3.2 * f
            for u in ((-1.4, 1.4) if f > 0 else ((-1.6,) if side == "+Y" else (-1.4, 1.4))):
                holes.append(L.circle(u, zc, 0.45, 10))
        outer = [(-s, 0), (s, 0), (s, H), (-s, H)]
        if side == "+Y":
            outer = L.with_door(-s, s, L.lancet(0.9, 1.3, 0.0, 2.6), [(s, H), (-s, H)])
        L.plate(body, outer, holes, 0.5, ST)
        for (x, z) in [(sum(p[0] for p in h) / len(h), sum(p[1] for p in h) / len(h)) for h in holes]:
            body.face([(x + 0.45 * math.cos(2 * math.pi * i / 10), -0.3, z + 0.45 * math.sin(2 * math.pi * i / 10)) for i in range(10)],
                      WARM, nrm=(0, 1, 0))
            L.rod_path(body, L.circle(x, z, 0.52, 8), 0.03, 0.05, ST, closed=True)
        for f in range(1, 4):
            body.box((-s - 0.08, 0.0, 3.2 * f - 0.15), (s + 0.08, 0.12, 3.2 * f), ST, skip=("y-",))
        body.pop()
    if True:
        fr = Matrix.Translation((0, cyc, 0)) @ L.frame("+Y", s, s)
        body.push(fr)
        L.door_leaves(body, 1.3, 2.6, -0.4, -0.3, straps=2)
        body.pop()
    # balcones con alambiques (en los lados que ve la camara: -Y y +X de la torre)
    alems = 0
    for side, f in (("-Y", 2), ("+X", 3)):
        fr = Matrix.Translation((0, cyc, 0)) @ L.frame(side, s, s)
        body.push(fr)
        z = 3.2 * (f - 1) + 0.0
        body.box((-1.6, 0.0, z), (1.6, 1.1, z + 0.15), WOOD)
        for x in (-1.55, 1.55):
            body.box((x - 0.05, 1.0, z), (x + 0.05, 1.1, z + 1.0), IRON, skip=("z-",))
        body.box((-1.6, 1.02, z + 0.95), (1.6, 1.08, z + 1.0), IRON, skip=("x-", "x+"))
        for x in (-0.9, 0.3):
            alembic(body, x, 0.55, z + 0.15)
            alems += 1
        body.pop()
    # cubierta conica de 8 lados y 2 chimeneas
    L._ring_frustum(roof, 0.0, cyc, s * 1.25, s * 1.25, H, H + 0.25, 8, ST, cap_top=False)
    L._ring_frustum(roof, 0.0, cyc, s * 1.25, 0.0, H + 0.25, H + 4.6, 8, ROOF)
    chim = []
    for x, y in ((-1.6, cyc - 1.6), (1.7, cyc + 1.2)):
        zb = H + 0.25 + 4.35 * (1 - math.hypot(x, y - cyc) / (s * 1.25)) - 0.4
        roof.box((x - 0.3, y - 0.3, zb), (x + 0.3, y + 0.3, H + 5.6), ST, skip=("z-",))
        cyl(roof, x, y, 0.16, H + 5.6, H + 6.2, 6, IRON, caps=False)
        chim.append((x, y, H + 6.2))
    # tapia baja del patio
    for (a, b, c, d) in ((-W / 2, -D / 2, W / 2, -D / 2 + 0.3), (-W / 2, -D / 2, -W / 2 + 0.3, D / 2),
                         (W / 2 - 0.3, -D / 2, W / 2, D / 2)):
        body.box((a, b, 0.0), (c, d, 1.1), ST, skip=("z-",))
    body.finish()
    roof.finish()
    mass = [("box", (-s, cyc - s, 0.0), (s, cyc + s, H)), ("cone", 0.0, cyc, s * 1.25, H, H + 4.6, 8)]
    return body, roof, {"tower_m": [2 * s, 2 * s, H], "top_m": round(H + 4.6, 2), "chimneys": chim, "alembics": alems,
                        "door": (0.9, cyc + s, 0.0), "interior": ((0.0, cyc), (2 * s - 1.0, 2 * s - 1.0, H))}, mass


def hornos(rng, W=16.0, D=12.0):
    """Horno comunal grande (cupula de 5 m, boca con brasas 1.5) con chimenea y cobertizo abierto con 2 mesas largas."""
    body, roof = K.MB(), K.MB()
    ox, oy = -4.0, -2.0
    body.box((ox - 3.0, oy - 3.0, 0.0), (ox + 3.0, oy + 3.0, 1.1), ST, skip=("z-",))
    prof = [(2.6, 1.1), (2.55, 1.8), (2.3, 2.6), (1.8, 3.3), (1.0, 3.8), (0.0, 4.0)]
    for (r0, z0), (r1, z1) in zip(prof[:-1], prof[1:]):
        L._ring_frustum(body, ox, oy, r0, r1, z0, z1, 10, ST)
    body.box((ox - 1.0, oy + 2.0, 1.1), (ox + 1.0, oy + 3.1, 2.6), ST, skip=("z-",))
    body.face([(ox - 0.6, oy + 3.11, 1.2), (ox + 0.6, oy + 3.11, 1.2), (ox + 0.6, oy + 3.11, 2.1), (ox - 0.6, oy + 3.11, 2.1)],
              EMBERS, nrm=(0, 1, 0))
    chimney_tall(body, ox + 1.6, oy - 1.4, 2.5, 8.0, 0.9, 0.7)
    # cobertizo abierto (postes y cubierta a un agua) con 2 mesas largas y bancos
    x0, x1 = 0.5, W / 2 - 0.3
    for x in (x0, (x0 + x1) / 2, x1):
        for y in (-D / 2 + 0.3, D / 2 - 0.3):
            body.box((x - 0.12, y - 0.12, 0.0), (x + 0.12, y + 0.12, 3.6 if y > 0 else 2.8), WOOD, skip=("z-",))
    roof.push(Matrix.Translation(((x0 + x1) / 2, 0, 2.8)))
    K.roof_lean_to(roof, x1 - x0 + 0.8, D - 0.2, pitch=7.0, rng=rng)
    roof.pop()
    for x in (x0 + 1.6, x1 - 1.6):
        body.box((x - 0.5, -D / 2 + 1.0, 0.8), (x + 0.5, D / 2 - 1.0, 0.88), WOOD)
        for y in (-3.0, 0.0, 3.0):
            body.box((x - 0.4, y - 0.06, 0.0), (x + 0.4, y + 0.06, 0.8), WOOD, skip=("z-",))
        for sx in (-0.85, 0.85):
            body.box((x + sx - 0.15, -D / 2 + 1.0, 0.42), (x + sx + 0.15, D / 2 - 1.0, 0.48), WOOD)
    # lena junto al horno
    body.push(Matrix.Translation((-6.8, 3.5, 0.0)) @ Matrix.Rotation(math.pi / 2, 4, "Z"))
    log_pile(body, length=2.5, r=0.18, rows=3)
    body.pop()
    body.finish()
    roof.finish()
    mass = [("box", (ox - 3.0, oy - 3.0, 0.0), (ox + 3.0, oy + 3.0, 1.1)), ("cone", ox, oy, 2.6, 1.1, 4.0, 8),
            ("box", (ox + 1.15, oy - 1.85, 2.5), (ox + 2.05, oy - 0.95, 8.0)),
            ("box", (x0 - 0.4, -D / 2, 2.8), (x1 + 0.4, D / 2, 3.6))]
    return body, roof, {"oven_dome_d_m": 5.2, "chimney_m": 8.0, "tables": 2, "door": (2.5, D / 2, 0.0),
                        "interior": ((0.0, 0.0), (W - 1.0, D - 1.0, 3.5))}, mass


def joyeria(rng, w=10.0, d=10.0, off_y=1.0):
    """Joyeria y Tallado (10 x 10) en caliza clara: grandes escaparates en planta baja, lupas de bronce colgadas en
    ellos, planta alta con ventanas y cubierta a cuatro aguas."""
    body, roof = K.MB(), K.MB()
    hw, hd = w / 2, d / 2
    H1, H2 = 3.6, 6.6
    shops = {"+Y": [-2.8, 2.8], "+X": [-2.0, 2.0], "-X": [-2.0, 2.0], "-Y": [0.0]}
    mags = []
    for side in ("+Y", "-Y", "+X", "-X"):
        fr = Matrix.Translation((0, off_y, 0)) @ L.frame(side, hw, hd)
        body.push(fr)
        half = hw if side in ("+Y", "-Y") else hd - 0.45
        holes = [M.rect(u, 1.85, 2.4, 2.3) for u in shops[side]] + [L.lancet(u, 1.1, H1 + 0.7, H1 + 2.5) for u in
                                                                    ((-2.5, 0.0, 2.5) if side in ("+Y", "-Y") else (-2.0, 2.0))]
        outer = [(-half, 0), (half, 0), (half, H2), (-half, H2)]
        if side == "+Y":
            outer = L.with_door(-half, half, [(-0.7, 0.0), (-0.7, 2.4), (0.7, 2.4), (0.7, 0.0)], [(half, H2), (-half, H2)])
        L.plate(body, outer, holes, 0.45, LIGHT)
        for u in shops[side]:
            body.face([(x, -0.25, z) for x, z in M.rect(u, 1.85, 2.4, 2.3)], WARM, nrm=(0, 1, 0))
            body.box((u - 0.03, -0.25, 0.7), (u + 0.03, -0.18, 3.0), WOOD, skip=("y-",))
            body.box((u - 1.3, -0.05, 0.55), (u + 1.3, 0.2, 0.7), LIGHT)
            body.box((u - 1.35, -0.02, 3.0), (u + 1.35, 0.12, 3.2), WOOD, skip=("y-",))
            mags.append((side, u))
        for u in ((-2.5, 0.0, 2.5) if side in ("+Y", "-Y") else (-2.0, 2.0)):
            L.window_fill(body, u, 1.1, H1 + 0.7, H1 + 2.5, -0.27, 1, LIGHT, rose=False, glass=WARM)
        body.box((-half - 0.06, -0.02, H1 - 0.15), (half + 0.06, 0.12, H1), LIGHT, skip=("y-",))
        if side == "+Y":
            body.box((-0.75, -0.3, 0.0), (0.75, -0.2, 2.4), WOOD, skip=("y-",))
        body.pop()
    roof.push(Matrix.Translation((0, off_y, H2)))
    K.roof_hip(roof, w, d, rng=rng)
    roof.pop()
    body.finish()
    roof.finish()
    mass = [("box", (-hw, off_y - hd, 0.0), (hw, off_y + hd, H2)), ("cone", 0.0, off_y, hw * 1.15, H2, H2 + 4.2, 4)]
    return body, roof, {"size": [w, d], "shop_windows": len(mags), "magnifiers": mags, "door": (0.0, off_y + hd, 0.0),
                        "interior": ((0.0, off_y), (w - 0.9, d - 0.9, H2)), "off_y": off_y}, mass


def crisol(rng, R=11.0):
    """Crisol de las Piedras: tambor de piedra de 22 m (16 lados), 12 ventanales altos, cupula rebajada con oculo de
    3 m y haz azul que sube; cuenco de metal fundido de 4 m en el centro (las piedras flotantes van aparte)."""
    body, roof = K.MB(), K.MB()
    n = 16
    t = 0.9
    H = 8.0
    dirs = [2 * math.pi * i / n for i in range(n)]              # un lado mira exactamente a +Y (i = 4): la puerta
    for i in range(n):
        side_w = 2 * R * math.sin(math.pi / n)
        cx, cy = R * math.cos(math.pi / n) * math.cos(dirs[i]), R * math.cos(math.pi / n) * math.sin(dirs[i])
        fr = Matrix.Translation((cx, cy, 0)) @ Matrix.Rotation(dirs[i] - math.pi / 2, 4, "Z")
        body.push(fr)
        hw = side_w / 2 + 0.02
        holes = []
        door = i == n // 4
        if i % 4 != 1 and not door:
            holes.append(L.lancet(0.0, 1.5, 4.0, 7.2))
        outer = [(-hw, 0), (hw, 0), (hw, H), (-hw, H)]
        if door:
            outer = L.with_door(-hw, hw, L.lancet(0.0, 2.2, 0.0, 3.6), [(hw, H), (-hw, H)])
        L.plate(body, outer, holes, t, ST)
        for _ in holes:
            L.window_fill(body, 0.0, 1.5, 4.0, 7.2, -t * 0.5, 2, LIGHT, rose=False, glass="MAT_Stained_Glass_Blue")
        if door:
            L.door_leaves(body, 2.2, 3.6, -0.6, -0.5)
        body.box((-hw - 0.05, -0.02, H - 0.3), (hw + 0.05, 0.25, H), LIGHT, skip=("y-",))
        body.box((-hw - 0.05, -0.02, 0.0), (hw + 0.05, 0.12, 0.7), GRAY, skip=("y-", "z-"))
        if i % 4 == 1:
            body.box((-0.45, 0.0, 0.0), (0.45, 0.8, 6.5), ST, skip=("y-", "z-"))
            L.wedge_top(body, -0.45, 0.45, 0.0, 0.8, 6.5, 7.3, ST)
        body.pop()
    # cupula rebajada en 3 anillos hasta el oculo (r 1.5) y aro del oculo
    rings = [(R + 0.2, H), (8.5, H + 2.0), (5.0, H + 3.4), (1.5, H + 4.0)]
    for (r0, z0), (r1, z1) in zip(rings[:-1], rings[1:]):
        L._ring_frustum(roof, 0, 0, r0, r1, z0, z1, n, GRAY)
    L._ring_frustum(roof, 0, 0, 1.75, 1.75, H + 4.0, H + 4.35, n, LIGHT)
    L._ring_frustum(roof, 0, 0, 1.5, 1.5, H + 3.7, H + 4.35, n, LIGHT)
    # haz azul por el oculo (MAT_Faro_Beam, alpha 0.3; aditivo en Godot)
    L._ring_frustum(body, 0, 0, 1.4, 1.4, 1.5, H + 12.0, 12, BEAM)
    # cuenco de metal fundido (4 m) sobre peana
    L._ring_frustum(body, 0, 0, 2.6, 2.4, 0.0, 0.6, 16, ST, cap_top=True)
    L._ring_frustum(body, 0, 0, 1.4, 2.0, 0.6, 1.4, 16, IRON)
    body.face([(1.92 * math.cos(2 * math.pi * i / 16), 1.92 * math.sin(2 * math.pi * i / 16), 1.32) for i in range(16)], EMBERS,
              nrm=(0, 0, 1))
    body.finish()
    roof.finish()
    mass = [("cyl", 0.0, 0.0, R, 0.0, H, 12), ("cone", 0.0, 0.0, R + 0.2, H, H + 4.0, 12)]
    return body, roof, {"diameter_m": 2 * R, "windows": sum(1 for i in range(n) if i % 4 != 1 and i != n // 4), "oculus_d_m": 3.0,
                        "bowl_d_m": 4.0, "top_m": H + 4.35, "door": (0.0, R, 0.0),
                        "interior": ((0.0, 0.0), (2 * R - 3.0, 2 * R - 3.0, H))}, mass


def float_stone(mb, rng):
    """Esquirla azul pequena (MAT_Shard_Blue) para CRISOL_FloatStone."""
    h = rng.uniform(0.35, 0.6)
    r = rng.uniform(0.12, 0.2)
    pts = [(r * math.cos(2 * math.pi * i / 5), r * math.sin(2 * math.pi * i / 5), 0.0) for i in range(5)]
    for i in range(5):
        j = (i + 1) % 5
        mb.face([pts[i], pts[j], (0, 0, h)], SHARD, nrm=(pts[i][0] + pts[j][0], pts[i][1] + pts[j][1], 0.3))
        mb.face([pts[j], pts[i], (0, 0, -h * 0.6)], SHARD, nrm=(pts[i][0] + pts[j][0], pts[i][1] + pts[j][1], -0.3))


def reparaciones(rng, W=16.0, D=10.0):
    """Casa de Reparaciones: taller abierto (muro trasero y laterales de piedra, frente de postes), cubierta a un agua,
    yunque, pared de herramientas (TOOL_Rack, props) y banco largo."""
    body, roof = K.MB(), K.MB()
    hw, hd = W / 2, D / 2
    H = 3.4
    body.box((-hw, -hd, 0.0), (hw, -hd + 0.5, H + 0.9), ST, skip=("z-",))
    for s in (-1, 1):
        a, b = sorted((s * hw, s * (hw - 0.5)))
        body.box((a, -hd + 0.5, 0.0), (b, 0.0, H + 0.4), ST, skip=("z-",))
    for x in [-hw + 0.25 + (W - 0.5) * k / 4 for k in range(5)]:
        body.box((x - 0.15, hd - 0.4, 0.0), (x + 0.15, hd - 0.1, H), WOOD, skip=("z-",))
    body.box((-hw, hd - 0.42, H - 0.3), (hw, hd - 0.08, H), WOOD)
    roof.push(Matrix.Translation((0, 0, H)))
    K.roof_lean_to(roof, W + 0.6, D, pitch=10.0, rng=rng)
    roof.pop()
    body.box((-5.5, -hd + 1.0, 0.85), (5.5, -hd + 1.8, 0.95), WOOD)
    for x in (-5.2, -1.8, 1.8, 5.2):
        body.box((x - 0.06, -hd + 1.05, 0.0), (x + 0.06, -hd + 1.75, 0.85), WOOD, skip=("z-",))
    body.push(Matrix.Translation((3.0, 1.5, 0.0)))
    anvil(body)
    body.pop()
    for x in (-hw + 1.2, hw - 1.2):
        body.push(Matrix.Translation((x, hd - 1.2, 0.0)))
        K.barrel(body, n=8)
        body.pop()
    body.finish()
    roof.finish()
    mass = [("box", (-hw, -hd, 0.0), (hw, hd, H)), ("box", (-hw, -hd, H), (hw, hd, H + 1.2))]
    return body, roof, {"open_front": True, "door": (0.0, hd, 0.0), "interior": ((0.0, 0.0), (W - 1.0, D - 1.0, H)),
                        "tool_racks": [(-3.5, -hd + 0.5, 0.0), (2.5, -hd + 0.5, 0.0)]}, mass
