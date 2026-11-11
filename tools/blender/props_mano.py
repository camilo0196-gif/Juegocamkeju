"""
CONCORDIA - props hechos a mano (etapa 28): los 4 objetos que iban a IA (telar, fuelle, maniqui, casco de minero) y
los 14 triviales de la tabla de props. Estilo semirrealista oscuro de formas simples, escala real en metros, origen en
la base, +Y = frente (la cara que mira a CAM_Iso), <= 1,000 triangulos cada uno, solo materiales de Concordia.

Cada funcion p_<nombre>(mb, rng) dibuja en un K.MB. PROPS = {nombre: (funcion, nota)}.
"""

import math

from mathutils import Matrix, Vector

import bld_kit as K
import interior_kit as IK

WOOD, WOOD_L, IRON, BRONZE = IK.WOOD, IK.WOOD_L, IK.IRON, IK.BRONZE
STONE, ASH, SHARD = IK.STONE, IK.ASH, IK.SHARD
CA, CB, CC = IK.CLOTH
HIDE = "MAT_Hide_R05"
FELT = "MAT_Felt_R05"
GLASS = "MAT_Glass_R04"
HERB = "MAT_Herb_Green"
STRAW = "MAT_Straw"
STONE_L_FISH = IK.STONE_L
MATS_EXTRA = [HIDE, FELT, GLASS, HERB, STRAW]
MAX_TRIS = 1000


# --------------------------------------------------------------------------- utilidades
def lathe(mb, prof, n, mat, center=(0.0, 0.0), cap_bottom=True, cap_top=True, ry=1.0):
    """Revolucion de un perfil [(r, z)] alrededor de Z (ry escala el eje Y: secciones elipticas)."""
    cx, cy = center
    rings = [[(cx + r * math.cos(2 * math.pi * i / n), cy + ry * r * math.sin(2 * math.pi * i / n), z)
              for i in range(n)] for r, z in prof]
    loft(mb, rings, mat, cap_bottom, cap_top)


def loft(mb, rings, mat, cap_bottom=False, cap_top=False, closed=True):
    n = len(rings[0])
    m = n if closed else n - 1
    for a, b in zip(rings, rings[1:]):
        for i in range(m):
            j = (i + 1) % n
            mb.face([a[i], a[j], b[j], b[i]], mat)
    if cap_top and closed:
        mb.ngon_fill(rings[-1], mat)
    if cap_bottom and closed:
        mb.ngon_fill(rings[0], mat, flip=True)


def ellipse(cx, cy, z, rx, ry, n, a0=0.0):
    return [(cx + rx * math.cos(a0 + 2 * math.pi * i / n), cy + ry * math.sin(a0 + 2 * math.pi * i / n), z)
            for i in range(n)]


def octa(mb, c, rx, rz, mat, ry=None):
    """Octaedro (esquirla, gema, terron)."""
    ry = rx if ry is None else ry
    x, y, z = c
    pts = [(x + rx, y, z), (x, y + ry, z), (x - rx, y, z), (x, y - ry, z)]
    top, bot = (x, y, z + rz), (x, y, z - rz)
    for i in range(4):
        a, b = pts[i], pts[(i + 1) % 4]
        mb.face([a, b, top], mat)
        mb.face([b, a, bot], mat)


def arc_rods(mb, pts, r, mat):
    for a, b in zip(pts, pts[1:]):
        mb.rod(a, b, r, mat)


def rot_z(deg):
    return Matrix.Rotation(math.radians(deg), 4, "Z")


def at(x, y, z, deg=0.0):
    return Matrix.Translation((x, y, z)) @ rot_z(deg)


# --------------------------------------------------------------------------- los 4 objetos (antes "IA")
def p_loom(mb, rng):
    """Telar de suelo de 1.6 x 1.4 x 1.75 m: bastidor de 4 postes, enjulio de urdimbre (atras) y de tela (delante),
    castillo con 2 lizos colgados, batan, 4 pedales; urdimbre y tela a medio tejer con un remiendo."""
    W, Dd, H = 1.6, 1.4, 1.75
    x0, x1 = -W / 2, W / 2
    yf, yb = Dd / 2 - 0.05, -Dd / 2 + 0.05
    for x in (x0, x1 - 0.08):
        for y, h in ((yf - 0.08, 1.0), (yb, H)):
            mb.box((x, y, 0), (x + 0.08, y + 0.08, h), WOOD, skip=("z-",))
        mb.box((x + 0.012, yb + 0.012, 0.12), (x + 0.068, yf - 0.012, 0.2), WOOD)    # larguero bajo (sin coplanarios)
        mb.box((x + 0.012, yb + 0.012, 0.92), (x + 0.068, yf - 0.012, 0.99), WOOD)   # larguero alto
    mb.box((x0 - 0.01, yb + 0.012, H - 0.07), (x1 + 0.01, yb + 0.068, H - 0.01), WOOD)  # travesano del castillo
    mb.box((x0 - 0.01, -0.05, H - 0.07), (x1 + 0.01, 0.05, H - 0.01), WOOD)  # castillo (sobre los lizos)
    for x in (x0, x1 - 0.08):
        mb.box((x + 0.012, -0.04, 0.99), (x + 0.068, 0.04, H - 0.07), WOOD, skip=("z-", "z+"))
        mb.rod((x + 0.04, yb + 0.04, H - 0.04), (x + 0.04, 0.0, H - 0.04), 0.03, WOOD)
    # enjulios (cilindros a lo ancho)
    def beam(y, z, r, mat=WOOD_L):
        mb.push(Matrix.Translation((x0 + 0.08, y, z)) @ Matrix.Rotation(math.pi / 2, 4, "Y"))
        mb.cylinder(r, 0.0, W - 0.16, 8, mat)                                # giro Y +90: z local -> +X
        mb.pop()
    beam(yb + 0.04, 0.62, 0.07)                                               # urdimbre
    beam(yf - 0.04, 0.95, 0.05)                                               # pecho
    beam(yf - 0.12, 0.45, 0.07)                                               # tela enrollada
    mb.push(Matrix.Translation((x0 + 0.1, yf - 0.12, 0.45)) @ Matrix.Rotation(math.pi / 2, 4, "Y"))
    mb.cylinder(0.085, 0.0, W - 0.2, 8, CA)                                   # vueltas de tela
    mb.pop()
    # lizos: 2 marcos finos colgados del castillo
    for k, y in enumerate((-0.07, 0.07)):
        z0, z1 = 1.05 - 0.04 * k, 1.35 - 0.04 * k
        mb.box((x0 + 0.18, y - 0.012, z1), (x1 - 0.18, y + 0.012, z1 + 0.03), WOOD_L)
        mb.box((x0 + 0.18, y - 0.012, z0), (x1 - 0.18, y + 0.012, z0 + 0.03), WOOD_L)
        for x in (x0 + 0.3, x1 - 0.3):
            mb.rod((x, y, z1 + 0.03), (x, y, H - 0.08), 0.006, CC)
    # urdimbre: 16 hilos sueltos desde el enjulio trasero, por los lizos, hasta el batan
    xa, xb = x0 + 0.2, x1 - 0.2
    for i in range(16):
        x = xa + (xb - xa) * (i + 0.5) / 16
        zl = 1.2 if i % 2 else 1.16                                        # calada: hilos pares e impares
        mb.rod((x, yb + 0.04, 0.69), (x, -0.07 + 0.14 * (i % 2), zl), 0.0035, STRAW)
        mb.rod((x, -0.07 + 0.14 * (i % 2), zl), (x, 0.36, 0.975), 0.0035, STRAW)
    # batan (peine colgante)
    mb.box((x0 + 0.1, 0.33, 0.9), (x1 - 0.1, 0.39, 0.97), WOOD)
    mb.box((x0 + 0.1, 0.34, 1.32), (x1 - 0.1, 0.38, 1.37), WOOD)
    for x in (x0 + 0.1, x1 - 0.14):
        mb.box((x, 0.34, 0.97), (x + 0.04, 0.38, 1.32), WOOD, skip=("z-", "z+"))
        mb.rod((x + 0.02, 0.36, 1.37), (x + 0.02, 0.0, H - 0.08), 0.015, WOOD)
    # tela tejida desde el batan hasta el pecho (remendada)
    mb.face([(xa, 0.39, 0.97), (xb, 0.39, 0.97), (xb, yf - 0.04, 1.0), (xa, yf - 0.04, 1.0)], CA, nrm=(0, 0, 1))
    mb.face([(xa, yf - 0.02, 1.0), (xb, yf - 0.02, 1.0), (xb, yf - 0.02, 0.5), (xa, yf - 0.02, 0.5)], CA,
            nrm=(0, 1, 0))
    px = rng.uniform(xa + 0.15, xb - 0.45)
    mb.face([(px, 0.47, 0.99), (px + 0.28, 0.47, 0.99), (px + 0.28, 0.6, 1.0), (px, 0.6, 1.0)], CC, nrm=(0, 0, 1))
    # pedales
    for i in range(4):
        x = -0.3 + i * 0.2
        mb.box((x - 0.04, yb + 0.1, 0.03), (x + 0.04, yf - 0.25, 0.06), WOOD_L)
        mb.rod((x, 0.0, 0.06), (x, 0.0, 1.05), 0.005, CC)
    # lanzadera sobre la tela
    mb.box((px + 0.32, 0.5, 0.995), (px + 0.6, 0.54, 1.025), WOOD_L)


def p_bellows(mb, rng):
    """Fuelle de forja de 1.25 m sobre caballete: dos tablas en lagrima, cuerpo de cuero con 2 pliegues, boquilla de
    hierro hacia +X, varal para accionarlo y tablas reforzadas con fleje."""
    h = 0.62
    n = 12

    def tear(z, s=1.0):
        pts = []
        for i in range(n):
            a = 2 * math.pi * i / n
            r = 0.3 * s * (1.0 - 0.45 * max(0.0, math.cos(a)))
            pts.append((-0.05 + 0.42 * s * math.cos(a) * (1.0 + 0.25 * max(0.0, math.cos(a))),
                        r * math.sin(a), z))
        return pts
    # tablas
    for z0, z1 in ((h - 0.03, h), (h + 0.28, h + 0.31)):
        bot, top = tear(z0), tear(z1)
        loft(mb, [bot, top], WOOD, cap_bottom=True, cap_top=True)
    # cuerpo de cuero: anillos con pliegues
    rings = [tear(h), tear(h + 0.06, 1.07), tear(h + 0.11, 0.97), tear(h + 0.17, 1.08), tear(h + 0.22, 0.98),
             tear(h + 0.28, 1.0)]
    loft(mb, rings, HIDE)
    # boquilla
    mb.push(Matrix.Translation((0.43, 0.0, h + 0.14)) @ Matrix.Rotation(math.pi / 2, 4, "Y"))
    mb.cylinder(0.06, 0.0, 0.08, 8, IRON, r1=0.05)
    mb.cylinder(0.05, 0.08, 0.36, 8, IRON, r1=0.022)
    mb.pop()
    mb.box((0.36, -0.08, h - 0.04), (0.42, 0.08, h + 0.32), IRON)            # fleje de la boquilla
    # varal y cadena
    mb.rod((-0.45, 0.0, h + 0.31), (-0.82, 0.0, h + 0.36), 0.025, WOOD_L)
    mb.rod((-0.82, 0.0, h + 0.36), (-0.82, 0.0, h + 0.9), 0.008, IRON)
    mb.box((-0.88, -0.05, h + 0.9), (-0.76, 0.05, h + 0.94), WOOD_L)
    # flejes de las tablas
    for x in (-0.2, 0.12):
        mb.box((x, -0.3, h + 0.31), (x + 0.04, 0.3, h + 0.325), IRON, skip=("z-",))
    # caballete
    for x in (-0.3, 0.25):
        for s in (-1, 1):
            mb.rod((x, s * 0.08, h - 0.03), (x, s * 0.26, 0.0), 0.03, WOOD)
        mb.box((x - 0.04, -0.2, h - 0.08), (x + 0.04, 0.2, h - 0.03), WOOD)
    mb.box((-0.3, -0.02, 0.2), (0.25, 0.02, 0.26), WOOD)


def p_mannequin(mb, rng):
    """Maniqui de costura de 1.6 m: tripode, mastil, torso de madera sin cabeza (pomo en el cuello) y una tela
    remendada prendida en diagonal."""
    for k in range(3):
        a = math.radians(90 + 120 * k)
        mb.rod((0, 0, 0.12), (0.32 * math.cos(a), 0.32 * math.sin(a), 0.0), 0.022, WOOD)
    mb.cylinder(0.045, 0.06, 0.16, 6, WOOD)
    mb.cylinder(0.02, 0.16, 0.92, 6, WOOD_L)
    mb.cylinder(0.035, 0.86, 0.94, 6, IRON)                                  # abrazadera de altura
    n = 12
    prof = [(0.03, 0.94), (0.15, 0.96), (0.175, 1.06), (0.145, 1.17), (0.17, 1.30), (0.19, 1.38), (0.2, 1.46),
            (0.13, 1.52), (0.05, 1.55)]
    rings = [ellipse(0, 0, z, r, r * 0.68, n) for r, z in prof]
    loft(mb, rings, WOOD_L, cap_bottom=True)
    lathe(mb, [(0.05, 1.55), (0.045, 1.6), (0.03, 1.63), (0.0, 1.64)], 6, WOOD, cap_bottom=False, cap_top=False)
    # tela: banda en diagonal sobre el frente (de hombro izquierdo a cadera derecha), 1.5 cm por fuera
    k = 1.08
    band = []
    for i, (r, z) in enumerate(prof[1:7]):
        t = i / 5.0
        a_mid = math.radians(70 - 50 * t)                                     # gira hacia la cadera derecha
        row = [(k * r * math.cos(a_mid + d), k * r * 0.68 * math.sin(a_mid + d), z) for d in (-0.75, -0.25, 0.25, 0.75)]
        band.append(row)
    loft(mb, band, CB, closed=False)
    loft(mb, [list(reversed(r)) for r in band], CB, closed=False)             # doble cara
    # remiendo
    r, z = prof[3]
    a = math.radians(55)
    c = (1.1 * r * math.cos(a), 1.1 * r * 0.68 * math.sin(a))
    mb.face([(c[0] - 0.05, c[1] + 0.012, z - 0.05), (c[0] + 0.05, c[1] - 0.012, z - 0.05),
             (c[0] + 0.05, c[1] - 0.012, z + 0.05), (c[0] - 0.05, c[1] + 0.012, z + 0.05)], CC, nrm=(0.3, 1, 0))
    # cola de tela colgando de la cadera
    r, z = prof[2]
    mb.face([(0.1, 0.13, z), (0.2, 0.06, z), (0.24, 0.07, z - 0.45), (0.12, 0.15, z - 0.5)], CB, nrm=(0.4, 1, 0))
    mb.face([(0.2, 0.06, z), (0.1, 0.13, z), (0.12, 0.15, z - 0.5), (0.24, 0.07, z - 0.45)], CB, nrm=(-0.4, -1, 0))


def p_miner_helmet(mb, rng):
    """Casco de minero de hierro abollado (0.26 m), correa de cuero y lamparilla de aceite con una esquirla azul
    palido (MAT_Shard_Blue, #8FD0FF) delante. Origen en la base del ala."""
    n, rows = 12, 5
    rings = []
    for j in range(rows + 1):
        phi = (math.pi / 2) * j / rows
        z = 0.02 + 0.15 * math.sin(phi)
        r = 0.125 * math.cos(phi) + (0.001 if j == rows else 0.0)
        ring = []
        for i in range(n):
            a = 2 * math.pi * i / n
            dent = 1.0
            if (j, i) in ((2, 3), (3, 4), (2, 8)):
                dent = 0.88                                                    # abolladuras
            ring.append((dent * r * math.cos(a), dent * r * 1.1 * math.sin(a), z))
        rings.append(ring)
    loft(mb, rings, IRON, cap_top=True)
    brim_o = ellipse(0, 0, 0.0, 0.16, 0.18, n)
    brim_i = ellipse(0, 0, 0.02, 0.125, 0.1375, n)
    loft(mb, [brim_o, brim_i], IRON)
    loft(mb, [brim_i, brim_o], IRON)
    # correa de cuero (U bajo el ala, a los lados)
    pts = [(-0.125, -0.02, 0.025), (-0.12, -0.1, 0.012), (-0.08, -0.18, 0.006), (0.0, -0.21, 0.006),
           (0.08, -0.18, 0.006), (0.12, -0.1, 0.012), (0.125, -0.02, 0.025)]               # correa suelta detras
    arc_rods(mb, pts, 0.008, HIDE)
    # lamparilla: soporte, cazoleta de bronce, esquirla
    mb.box((-0.02, 0.135, 0.06), (0.02, 0.16, 0.13), IRON)
    lathe(mb, [(0.02, 0.1), (0.035, 0.115), (0.032, 0.14), (0.02, 0.145)], 8, BRONZE, center=(0.0, 0.19))
    mb.box((-0.006, 0.155, 0.11), (0.006, 0.175, 0.12), BRONZE)
    octa(mb, (0.0, 0.19, 0.168), 0.012, 0.024, SHARD)
    mb.cylinder(0.03, 0.145, 0.19, 8, GLASS, r1=0.022, caps=False, center=(0.0, 0.19))


# --------------------------------------------------------------------------- triviales
def p_ingots_coal(mb, rng):
    """Palet con 3 hiladas de lingotes (hierro y bronce) y un cajon de carbon."""
    mb.box((-0.45, -0.3, 0), (0.45, 0.3, 0.1), WOOD, skip=("z-",))
    for row in range(3):
        for i in range(4 if row % 2 == 0 else 3):
            if row % 2 == 0:
                x, y = -0.3 + i * 0.2, -0.0
                mb.push(at(x, y, 0.1 + row * 0.06, 90))
            else:
                mb.push(at(-0.2 + i * 0.2, 0.0, 0.1 + row * 0.06, 0))
            IK.prism(mb, [(-0.25, 0.0), (0.25, 0.0), (0.21, 0.06), (-0.21, 0.06)], -0.05, 0.05,
                     BRONZE if (row + i) % 3 == 0 else IRON, axis="y")
            mb.pop()
    # cajon de carbon
    mb.box((0.5, -0.25, 0), (0.95, 0.25, 0.04), WOOD, skip=("z-",))
    for (lo, hi) in (((0.5, -0.25, 0.04), (0.53, 0.25, 0.35)), ((0.92, -0.25, 0.04), (0.95, 0.25, 0.35)),
                     ((0.53, -0.25, 0.04), (0.92, -0.22, 0.35)), ((0.53, 0.22, 0.04), (0.92, 0.25, 0.35))):
        mb.box(lo, hi, WOOD, skip=("z-",))
    for _ in range(12):
        octa(mb, (rng.uniform(0.58, 0.87), rng.uniform(-0.17, 0.17), rng.uniform(0.3, 0.36)),
             rng.uniform(0.035, 0.06), rng.uniform(0.025, 0.045), IRON)


def p_cloth_rolls(mb, rng):
    """Estante bajo con 5 rollos de tela remendada (3 abajo, 2 encima) y uno de pie."""
    mb.box((-0.75, -0.3, 0.12), (0.75, 0.3, 0.16), WOOD)
    for x in (-0.72, 0.68):
        mb.box((x, -0.28, 0), (x + 0.04, 0.28, 0.12), WOOD, skip=("z-", "z+"))
    mats = (CA, CB, CC)
    for i, x in enumerate((-0.5, 0.0, 0.5)):
        mb.push(Matrix.Translation((x, 0.27, 0.27)) @ Matrix.Rotation(math.pi / 2, 4, "X"))
        mb.cylinder(0.11, 0.0, 0.54, 10, mats[i % 3])
        mb.pop()
    for i, x in enumerate((-0.25, 0.25)):
        mb.push(Matrix.Translation((x, 0.25, 0.47)) @ Matrix.Rotation(math.pi / 2, 4, "X"))
        mb.cylinder(0.1, 0.0, 0.5, 10, mats[(i + 1) % 3])
        mb.pop()
    mb.cylinder(0.09, 0.0, 1.1, 10, CA, center=(0.95, 0.0))
    mb.face([(0.95, 0.09, 0.2), (1.05, 0.12, 0.2), (1.07, 0.12, 0.85), (0.95, 0.091, 0.85)], CB, nrm=(0.5, 1, 0))


def p_bar_counter(mb, rng):
    """Mostrador de barra de la Posada: 2.0 x 0.6 x 1.05 m, tablero con vuelo, frente de tablas con 3 cuarterones,
    reposapies de hierro y estante interior (lado -Y, el del posadero)."""
    mb.box((-1.0, -0.3, 0.0), (1.0, 0.25, 1.0), WOOD, skip=("z-",))
    mb.box((-1.04, -0.32, 1.0), (1.04, 0.32, 1.05), WOOD_L)
    for i in range(3):
        x = -0.92 + i * 0.63
        mb.box((x, 0.25, 0.18), (x + 0.58, 0.27, 0.86), WOOD)
        mb.box((x + 0.06, 0.27, 0.24), (x + 0.52, 0.28, 0.8), WOOD_L)
    mb.box((-1.0, 0.25, 0.0), (1.0, 0.29, 0.1), WOOD)
    mb.rod((-0.98, 0.42, 0.18), (0.98, 0.42, 0.18), 0.02, IRON)
    for x in (-0.9, 0.0, 0.9):
        mb.rod((x, 0.28, 0.18), (x, 0.42, 0.18), 0.015, IRON)
    mb.box((-0.95, -0.34, 0.55), (0.95, -0.3, 0.58), WOOD_L)


def p_trestle(mb, rng):
    """Caballete de 1.1 m: viga y dos pares de patas en A con riostra."""
    mb.box((-0.55, -0.05, 0.72), (0.55, 0.05, 0.8), WOOD)
    for x in (-0.42, 0.42):
        for s in (-1, 1):
            mb.rod((x, s * 0.04, 0.74), (x + 0.04 * (1 if x > 0 else -1), s * 0.3, 0.0), 0.025, WOOD)
        mb.rod((x, -0.2, 0.25), (x, 0.2, 0.25), 0.018, WOOD_L)
    mb.rod((-0.42, 0.0, 0.25), (0.42, 0.0, 0.25), 0.018, WOOD_L)


def p_vise(mb, rng):
    """Tornillo de banco de hierro sobre taco de madera (0.3 m): mandibula fija y movil, husillo y manivela."""
    mb.box((-0.2, -0.15, 0), (0.2, 0.15, 0.08), WOOD, skip=("z-",))
    mb.box((-0.1, -0.06, 0.08), (0.1, 0.06, 0.11), IRON, skip=("z-",))
    mb.box((-0.08, -0.05, 0.11), (-0.02, 0.05, 0.27), IRON)
    mb.box((0.06, -0.05, 0.11), (0.12, 0.05, 0.27), IRON)
    mb.box((-0.02, -0.03, 0.12), (0.06, 0.03, 0.15), IRON)
    mb.push(Matrix.Translation((0.12, 0.0, 0.2)) @ Matrix.Rotation(math.pi / 2, 4, "Y"))
    mb.cylinder(0.012, 0.0, 0.14, 6, IRON)
    mb.pop()
    mb.rod((0.26, -0.11, 0.2), (0.26, 0.11, 0.2), 0.008, IRON)
    for y in (-0.11, 0.11):
        mb.box((0.25, y - 0.012, 0.19), (0.27, y + 0.012, 0.21), IRON)
    mb.box((-0.085, -0.051, 0.24), (-0.075, 0.051, 0.27), BRONZE)


def p_gavel(mb, rng):
    """Martillo de subastador (0.28 m) apoyado en su taco de resonancia."""
    lathe(mb, [(0.0, 0.0), (0.075, 0.0), (0.075, 0.035), (0.06, 0.045), (0.0, 0.045)], 12, WOOD,
          cap_bottom=False, cap_top=False)
    mb.push(Matrix.Translation((0.0, 0.0, 0.085)) @ Matrix.Rotation(math.pi / 2, 4, "X"))
    mb.cylinder(0.035, -0.06, 0.06, 10, WOOD_L)
    mb.cylinder(0.037, -0.065, -0.05, 10, BRONZE)
    mb.cylinder(0.037, 0.05, 0.065, 10, BRONZE)
    mb.pop()
    mb.rod((0.03, 0.0, 0.085), (0.26, 0.0, 0.05), 0.011, WOOD_L)


def p_ink_seal(mb, rng):
    """Tintero de bronce con pluma, sello de lacre (mango de madera y base de bronce) y barra de lacre."""
    lathe(mb, [(0.0, 0.0), (0.04, 0.0), (0.045, 0.035), (0.03, 0.055), (0.018, 0.06), (0.018, 0.065)], 10, BRONZE,
          cap_bottom=False, cap_top=True, center=(-0.08, 0.0))
    mb.face([(-0.08, 0.0, 0.06), (-0.075, 0.003, 0.06), (-0.16, -0.06, 0.24), (-0.175, -0.06, 0.25)], ASH,
            nrm=(0, 1, 0))
    mb.face([(-0.075, 0.003, 0.06), (-0.08, 0.0, 0.06), (-0.175, -0.06, 0.25), (-0.16, -0.06, 0.24)], ASH,
            nrm=(0, -1, 0))
    lathe(mb, [(0.0, 0.0), (0.022, 0.0), (0.022, 0.012), (0.01, 0.02), (0.012, 0.06), (0.018, 0.08),
               (0.0, 0.09)], 8, WOOD, cap_bottom=False, cap_top=False, center=(0.05, 0.0))
    mb.cylinder(0.023, 0.0, 0.013, 8, BRONZE, center=(0.05, 0.0))
    mb.box((0.1, -0.05, 0.0), (0.2, -0.035, 0.015), HIDE)                       # barra de lacre


def p_peel(mb, rng):
    """Pala de panadero de 1.8 m apoyada en la pared (+Y frente): mango y pala con el borde biselado."""
    tilt = math.radians(12)
    mb.push(Matrix.Translation((0, 0.3, 0)) @ Matrix.Rotation(tilt, 4, "X"))   # la punta se apoya en la pared (-Y)
    mb.cylinder(0.018, 0.0, 1.45, 6, WOOD_L)
    IK.prism(mb, [(-0.16, 1.45), (0.16, 1.45), (0.17, 1.7), (0.14, 1.8), (-0.14, 1.8), (-0.17, 1.7)], -0.01, 0.01,
             WOOD_L, axis="y")
    mb.pop()


def p_tanning_frame(mb, rng):
    """Bastidor de curtir de 1.4 x 1.6 m con pies y una piel tensada (cordaje como bandas), mas el raspador de dos
    mangos apoyado al pie."""
    W, H = 1.3, 1.5
    for x in (-W / 2, W / 2 - 0.07):
        mb.box((x, -0.035, 0.0), (x + 0.07, 0.035, H + 0.1), WOOD, skip=("z-",))
        mb.box((x - 0.15, -0.25, 0.0), (x + 0.22, -0.18, 0.06), WOOD, skip=("z-",))
        mb.box((x - 0.15, 0.18, 0.0), (x + 0.22, 0.25, 0.06), WOOD, skip=("z-",))
        mb.box((x, -0.18, 0.0), (x + 0.07, 0.18, 0.06), WOOD, skip=("z-",))
    for z in (0.25, H):
        mb.box((-W / 2, -0.035, z), (W / 2, 0.035, z + 0.07), WOOD)
    # piel (dos caras), 1.5 cm por delante del bastidor, con el contorno irregular
    pts = [(-0.45, 0.4), (-0.2, 0.33), (0.15, 0.36), (0.45, 0.42), (0.52, 0.85), (0.46, 1.32), (0.12, 1.42),
           (-0.25, 1.4), (-0.5, 1.3), (-0.53, 0.85)]
    front = [(x, 0.05, z) for x, z in pts]
    mb.ngon_fill(front, HIDE)
    mb.ngon_fill([(x, 0.049, z) for x, z in pts], HIDE, flip=True)
    for x, z in pts[::2]:
        ex = -W / 2 + 0.07 if x < 0 else W / 2 - 0.07
        mb.rod((x, 0.04, z), (ex if abs(x) > 0.3 else x, 0.0, z if abs(x) > 0.3 else (0.32 if z < 0.8 else H)),
               0.004, STRAW)
    # raspador
    mb.push(at(0.25, 0.3, 0.0, 10))
    mb.rod((-0.2, 0.0, 0.02), (0.2, 0.0, 0.02), 0.012, IRON)
    for x in (-0.24, 0.24):
        mb.cylinder(0.016, 0.0, 0.1, 6, WOOD_L, center=(x, 0.0))
    mb.pop()


def p_herb_rack(mb, rng):
    """Secadero de hierbas de 1.2 x 1.6 m: dos pies en H con 3 varales; 12 manojos colgados boca abajo."""
    for x in (-0.6, 0.55):
        mb.box((x, -0.04, 0.0), (x + 0.05, 0.04, 1.6), WOOD, skip=("z-",))
        mb.box((x - 0.1, -0.2, 0.0), (x + 0.15, 0.2, 0.05), WOOD, skip=("z-",))
    for z in (0.9, 1.25, 1.55):
        mb.rod((-0.6, 0.0, z), (0.6, 0.0, z), 0.015, WOOD_L)
    for k in range(12):
        z = (0.9, 1.25, 1.55)[k % 3]
        x = -0.45 + (k // 3) * 0.3 + rng.uniform(-0.04, 0.04)
        L = rng.uniform(0.18, 0.3)
        mb.rod((x, 0.0, z), (x, 0.0, z - 0.06), 0.004, STRAW)
        lathe(mb, [(0.012, z - 0.06), (0.05, z - 0.06 - L * 0.6), (0.02, z - 0.06 - L)], 5,
              HERB if k % 4 else STRAW, center=(x, 0.0), cap_bottom=False, cap_top=True)


def p_fish_crates(mb, rng):
    """Dos cajas de pescado de tablillas (una encima girada), pescados encima y dos canas apoyadas."""
    def crate(x, y, z, deg):
        mb.push(at(x, y, z, deg))
        mb.box((-0.3, -0.2, 0.0), (0.3, 0.2, 0.02), WOOD_L, skip=("z-",))
        for zz in (0.03, 0.12):
            for (lo, hi) in (((-0.3, -0.2, zz), (0.3, -0.18, zz + 0.07)), ((-0.3, 0.18, zz), (0.3, 0.2, zz + 0.07)),
                             ((-0.3, -0.18, zz), (-0.28, 0.18, zz + 0.07)), ((0.28, -0.18, zz), (0.3, 0.18, zz + 0.07))):
                mb.box(lo, hi, WOOD_L)
        mb.pop()
    crate(0.0, 0.0, 0.0, 0)
    crate(0.03, 0.0, 0.2, 12)
    for k in range(5):
        x, y = rng.uniform(-0.17, 0.2), rng.uniform(-0.1, 0.1)
        a = rng.uniform(-30, 30)
        mb.push(at(x, y, 0.44, a) @ Matrix.Rotation(math.pi / 2, 4, "Y"))   # tumbado de lado: fino en vertical
        lathe(mb, [(0.0, -0.18), (0.02, -0.08), (0.022, 0.05), (0.0, 0.14)], 6, STONE_L_FISH, ry=1.8,
              cap_bottom=False, cap_top=False)
        mb.pop()
    for k, x in enumerate((0.45, 0.6)):
        mb.rod((x, 0.05, 0.0), (x - 0.05, -0.12, 2.1 - 0.15 * k), 0.012, WOOD_L)
        mb.rod((x - 0.05, -0.12, 2.1 - 0.15 * k), (x - 0.1, 0.0, 1.0), 0.002, STRAW)


def p_longbow(mb, rng):
    """Arco largo de 1.85 m con su cuerda, colgado en un armero de pared de dos clavijas (+Y frente) con 6 flechas en
    un carcaj de cuero apoyado."""
    mb.box((-0.35, -0.04, 1.35), (0.35, 0.0, 1.45), WOOD)
    for x in (-0.22, 0.22):
        mb.rod((x, 0.0, 1.4), (x, 0.12, 1.42), 0.012, WOOD_L)
    pts = []
    for i in range(9):
        t = -1.0 + 2.0 * i / 8
        pts.append((0.92 * t, 0.1 + 0.12 * (1 - t * t), 1.47 + 0.02 * (1 - t * t)))
    for a, b in zip(pts, pts[1:]):
        r = 0.016 if abs(a[0]) < 0.3 else 0.011
        mb.rod(a, b, r, WOOD_L)
    mb.rod(pts[0], pts[-1], 0.002, STRAW)
    mb.box((-0.06, 0.2, 1.45), (0.06, 0.24, 1.53), HIDE)
    # carcaj apoyado en la pared, bajo el armero
    mb.push(Matrix.Translation((0.25, 0.1, 0.0)) @ Matrix.Rotation(math.radians(-10), 4, "X"))
    mb.cylinder(0.06, 0.0, 0.62, 8, HIDE, r1=0.07, caps=False)
    mb.cylinder(0.059, 0.02, 0.03, 8, HIDE)
    for k in range(6):
        a = 2 * math.pi * k / 6
        x, y = 0.035 * math.cos(a), 0.035 * math.sin(a)
        mb.rod((x, y, 0.3), (x * 1.3, y * 1.3, 0.85), 0.004, WOOD_L)
        mb.box((x * 1.3 - 0.003, y * 1.3 - 0.012, 0.8), (x * 1.3 + 0.003, y * 1.3 + 0.012, 0.86), CB)
    mb.pop()


def p_spinning_wheel(mb, rng):
    """Rueca de pedal de 0.95 m: banco inclinado de 3 patas, rueda de 0.55 m (16 tramos, 8 radios), montantes,
    huso con husada de lana, pedal y biela."""
    # banco
    mb.push(Matrix.Translation((0.0, 0.0, 0.42)) @ Matrix.Rotation(math.radians(-8), 4, "Y"))
    mb.box((-0.45, -0.12, 0.0), (0.45, 0.12, 0.05), WOOD)
    mb.pop()
    for x, y in ((-0.38, 0.0), (0.33, -0.09), (0.33, 0.09)):
        z = 0.42 + (-x) * math.tan(math.radians(8))
        mb.rod((x, y, z), (x * 1.15, y * 1.8, 0.0), 0.02, WOOD)
    # montantes de la rueda
    cx, cz, R = 0.15, 0.82, 0.27
    for y in (-0.06, 0.06):
        mb.rod((cx - 0.05, y, 0.46), (cx, y, cz + 0.03), 0.018, WOOD)
    # rueda (plano XZ en y = 0)
    ring = [(cx + R * math.cos(2 * math.pi * i / 16), 0.0, cz + R * math.sin(2 * math.pi * i / 16)) for i in range(17)]
    for a, b in zip(ring, ring[1:]):
        mb.rod(a, b, 0.016, WOOD_L)
    for i in range(8):
        a = 2 * math.pi * i / 8
        mb.rod((cx, 0.0, cz), (cx + R * math.cos(a), 0.0, cz + R * math.sin(a)), 0.006, WOOD_L)
    mb.push(Matrix.Translation((cx, -0.08, cz)) @ Matrix.Rotation(math.pi / 2, 4, "X"))
    mb.cylinder(0.035, -0.16, 0.0, 8, WOOD)
    mb.pop()
    # huso y husada al otro extremo
    mb.rod((-0.3, 0.0, 0.46), (-0.3, 0.0, 0.72), 0.016, WOOD)
    mb.rod((-0.22, 0.0, 0.46), (-0.22, 0.0, 0.72), 0.016, WOOD)
    mb.push(Matrix.Translation((-0.4, 0.0, 0.72)) @ Matrix.Rotation(math.pi / 2, 4, "Y"))
    mb.cylinder(0.008, 0.0, 0.3, 6, WOOD_L)
    mb.cylinder(0.04, 0.08, 0.18, 8, CA, r1=0.03)
    mb.pop()
    mb.rod((-0.26, 0.0, 0.73), (cx - R + 0.01, 0.0, cz), 0.002, STRAW)
    # pedal y biela
    mb.box((-0.1, -0.12, 0.04), (0.25, 0.12, 0.07), WOOD)
    mb.rod((0.2, 0.0, 0.07), (cx + 0.06, 0.0, cz - 0.06), 0.006, WOOD_L)


def p_jeweler_case(mb, rng):
    """Vitrina de joyero de 1.0 x 0.5 x 1.0 m: caja de madera sobre 4 patas, fondo de fieltro, tapa de vidrio
    inclinada hacia +Y; dentro gemas (vidrio), anillos y una balanza de bronce."""
    for x in (-0.48, 0.42):
        for y in (-0.23, 0.17):
            mb.box((x, y, 0.0), (x + 0.06, y + 0.06, 0.72), WOOD, skip=("z-",))
    mb.box((-0.5, -0.25, 0.72), (0.5, 0.25, 0.76), WOOD)
    mb.box((-0.5, -0.25, 0.76), (0.5, -0.21, 1.0), WOOD)                     # trasera alta
    mb.box((-0.5, 0.21, 0.76), (0.5, 0.25, 0.84), WOOD)                      # delantera baja
    for x in (-0.5, 0.46):
        IK.prism(mb, [(-0.25, 0.76), (0.25, 0.76), (0.25, 0.84), (-0.21, 1.0), (-0.25, 1.0)], x, x + 0.04, WOOD,
                 axis="x")
    mb.box((-0.46, -0.21, 0.76), (0.46, 0.21, 0.78), FELT)
    mb.face([(-0.46, 0.21, 0.845), (0.46, 0.21, 0.845), (0.46, -0.21, 1.005), (-0.46, -0.21, 1.005)], GLASS,
            nrm=(0, 0.5, 1))
    for k in range(7):
        octa(mb, (-0.38 + k * 0.11, rng.uniform(-0.1, 0.12), 0.8), 0.018, 0.02, GLASS)
    for k in range(4):
        x = -0.32 + k * 0.2
        mb.cylinder(0.018, 0.78, 0.79, 6, BRONZE, center=(x, -0.14))
    mb.cylinder(0.006, 0.78, 0.9, 6, BRONZE, center=(0.38, -0.12))
    mb.rod((0.3, -0.12, 0.9), (0.46, -0.12, 0.9), 0.004, BRONZE)


PROPS = {
    # los 4 de la lista de IA, ahora a mano
    "PROP_Loom": (p_loom, "Telar de suelo con tela remendada a medio tejer"),
    "PROP_Forge_Bellows": (p_bellows, "Fuelle de forja de cuero y madera, boquilla de hierro"),
    "PROP_Dress_Form": (p_mannequin, "Maniqui de costura (torso de madera sin cabeza) con tela remendada"),
    "PROP_Miner_Helmet": (p_miner_helmet, "Casco de minero abollado, correa de cuero, lamparilla con esquirla"),
    # triviales
    "PROP_Ingots_Coal": (p_ingots_coal, "Lingotes y carbon"),
    "PROP_Cloth_Rolls": (p_cloth_rolls, "Rollos de tela"),
    "PROP_Bar_Counter": (p_bar_counter, "Mostrador de barra (Posada)"),
    "PROP_Trestle": (p_trestle, "Caballete"),
    "PROP_Bench_Vise": (p_vise, "Tornillo de banco"),
    "PROP_Auction_Gavel": (p_gavel, "Martillo de subastador"),
    "PROP_Ink_Seal": (p_ink_seal, "Tintero y sello"),
    "PROP_Baker_Peel": (p_peel, "Pala de panadero"),
    "PROP_Tanning_Frame": (p_tanning_frame, "Bastidor y raspador de curtir"),
    "PROP_Herb_Rack": (p_herb_rack, "Secadero de hierbas"),
    "PROP_Fish_Crates": (p_fish_crates, "Cajas de pescado y canas"),
    "PROP_Longbow": (p_longbow, "Arco largo (armero de pared y carcaj)"),
    "PROP_Spinning_Wheel": (p_spinning_wheel, "Rueca"),
    "PROP_Jeweler_Case": (p_jeweler_case, "Vitrina de joyero"),
}
AI_FOUR = ("PROP_Loom", "PROP_Forge_Bellows", "PROP_Dress_Form", "PROP_Miner_Helmet")
_ = Vector
