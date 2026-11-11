"""
CONCORDIA - Etapa 27: interior piloto del Banco de Concordia (int_banco.glb). Todo hecho a mano (regla del usuario:
el Banco no usa assets descargados ni IA).

Referencias: Palazzo Pubblico de Siena (volumen macizo, arcadas), antigua sede del Monte dei Paschi (sala sobria de
piedra), Porta Nigra (sillares pesados). Sobriedad, masa de piedra, rejas y luz escasa.

Marco centrado del edificio (el del Banco_InteriorVolume): x en [-11.55, 11.55], y en [-9.55, 9.55], z en [0, 6.4];
+Y = fachada de la calle (puerta de entrada en x = 2). CAM_Iso mira desde -x -y: muros cercanos -X y -Y.

Planta baja: vestibulo de doble altura; mostrador de 10 m (piedra y madera) con reja y ventanilla, el Banquero
detras (lado +X, de cara a la camara); sala de espera (3 bancos); archivo (estantes de doble cara con libros
contables) y escritorio; boveda al fondo a la derecha tras una puerta de hierro de 3 m, con BOXES_TOTAL cajas
numeradas en sus 4 paredes. Planta alta (LEVEL_1, a lo largo de la fachada): galeria con balaustrada sobre una
arcada, despacho con escritorio; escalera de piedra de 2 m de ancho (32.6 grados).
"""

import math
import os
import random

import bpy
from mathutils import Matrix, Vector

import bld_kit as K
import interior_kit as IK

BOXES_TOTAL = 200
OPEN_DEFAULT = 40                 # cajas 1..40 abiertas por defecto (Godot lo cambia segun el oro)
W, D, H = 23.1, 19.1, 6.4
DOOR = (2.0, D / 2)
VAULT_X0 = 7.5                    # tabique de la boveda (cara del vestibulo)
VAULT_T = 0.4
VAULT_DOOR = (-5.5, -3.3)         # tramo y de la puerta de la boveda (2.2 m)
VAULT_TOP = 4.9
COUNTER_X = 4.3
COUNTER_Y = (-5.75, 4.25)
TELLER_Y = 1.25  # centro de la ventanilla de cajero (INT_Grille_Teller, 1.2 m de luz)
BANKER = (5.0, 1.65)  # de pie tras el tablero, 0.35 m a +Y del centro de la ventanilla de cajero (y 1.25)
ARCADE_Y = 4.5
ARCADE_X = (-9.0, 11.55)
STAIR_X = (-11.4, -9.4)
STAIR_Y = (-0.5, 4.5)
NUM_MAT = "MAT_Bank_BoxNumbers"


def M(x, y, z=0.0, yaw=0.0, sx=1.0, sy=1.0, sz=1.0):
    return Matrix.Translation((x, y, z)) @ Matrix.Rotation(math.radians(yaw), 4, "Z") @ \
        Matrix.Diagonal((sx, sy, sz, 1.0))


# --------------------------------------------------------------------------- atlas de numeros
def number_atlas(repo):
    """Atlas 1024 x 1024: mitad superior placas claras (abierta), mitad inferior oscuras (cerrada); 20 x 10 celdas
    por mitad, numeros 1..200. Bronce apagado (saturacion <= 0.32)."""
    from PIL import Image, ImageDraw, ImageFont
    path = os.path.join(repo, "textures", "concordia", NUM_MAT, "bank_box_numbers_1k.png")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    img = Image.new("RGB", (1024, 1024), (40, 36, 30))
    d = ImageDraw.Draw(img)
    font = ImageFont.truetype("DejaVuSerif-Bold.ttf", 23)
    cw = 1024 / 20
    for half, (bg, fg, edge) in enumerate((((158, 140, 108), (46, 42, 36), (110, 96, 72)),
                                           ((74, 66, 52), (184, 169, 138), (50, 44, 36)))):
        for k in range(200):
            c, r = k % 20, k // 20
            x0, y0 = c * cw, half * 512 + r * cw
            d.rectangle([x0 + 2, y0 + 2, x0 + cw - 3, y0 + cw - 3], fill=bg, outline=edge, width=2)
            t = str(k + 1)
            bb = d.textbbox((0, 0), t, font=font)
            d.text((x0 + (cw - (bb[2] - bb[0])) / 2 - bb[0], y0 + (cw - (bb[3] - bb[1])) / 2 - bb[1]), t, fill=fg,
                   font=font)
    img.save(path)
    return path


def number_material(path):
    m = bpy.data.materials.get(NUM_MAT)
    if m is not None:
        return m
    m = bpy.data.materials.new(NUM_MAT)
    m.use_nodes = True
    N = m.node_tree.nodes
    b = N["Principled BSDF"]
    tex = N.new("ShaderNodeTexImage")
    tex.image = bpy.data.images.load(path)
    tex.image.filepath = bpy.path.relpath(path) if bpy.data.filepath else path
    tex.label = "Albedo"
    m.node_tree.links.new(tex.outputs["Color"], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = 0.5
    b.inputs["Metallic"].default_value = 0.65
    m["note"] = "placas de las cajas de deposito: atlas 1..200 (mitad clara = abierta, oscura = cerrada), 1K"
    return m


def plate_uv(n, locked):
    k = n - 1
    c, r = k % 20, k // 20
    u0, u1 = c / 20, (c + 1) / 20
    v1 = 1.0 - r * 0.05 - (0.5 if locked else 0.0)
    return u0, v1 - 0.05, u1, v1


# --------------------------------------------------------------------------- props (origen en la base, +Y = frente)
def p_bench(mb):
    mb.box((-1.0, -0.2, 0.42), (1.0, 0.2, 0.48), IK.WOOD)
    for x in (-0.82, 0.82):
        mb.box((x - 0.05, -0.18, 0), (x + 0.05, 0.18, 0.42), IK.WOOD, skip=("z-", "z+"))
        mb.box((x - 0.04, -0.24, 0.48), (x + 0.04, -0.18, 0.92), IK.WOOD, skip=("z-",))
    mb.box((-1.0, -0.25, 0.74), (1.0, -0.19, 0.9), IK.WOOD)


def p_desk(mb):
    mb.box((-0.8, -0.4, 0.74), (0.8, 0.4, 0.79), IK.WOOD)
    for x0 in (-0.78, 0.38):
        mb.box((x0, -0.38, 0), (x0 + 0.4, 0.38, 0.74), IK.WOOD, skip=("z-", "z+"))
        for k in range(3):
            z = 0.06 + k * 0.22
            mb.box((x0 + 0.03, 0.38, z), (x0 + 0.37, 0.4, z + 0.19), IK.WOOD_L, skip=("y-",))


def p_chair(mb):
    mb.box((-0.23, -0.23, 0.44), (0.23, 0.23, 0.48), IK.WOOD)
    for x in (-0.2, 0.2):
        for y in (-0.2, 0.2):
            mb.box((x - 0.025, y - 0.025, 0), (x + 0.025, y + 0.025, 0.44), IK.WOOD, skip=("z-", "z+"))
    for x in (-0.2, 0.2):
        mb.box((x - 0.025, -0.225, 0.48), (x + 0.025, -0.175, 1.0), IK.WOOD, skip=("z-",))
    for z in (0.66, 0.9):
        mb.box((-0.2, -0.22, z), (0.2, -0.18, z + 0.07), IK.WOOD)


def p_stool(mb):
    mb.box((-0.2, -0.2, 0.62), (0.2, 0.2, 0.67), IK.WOOD)
    for x in (-0.16, 0.16):
        for y in (-0.16, 0.16):
            mb.box((x - 0.025, y - 0.025, 0), (x + 0.025, y + 0.025, 0.62), IK.WOOD, skip=("z-", "z+"))
    mb.box((-0.16, -0.18, 0.25), (0.16, -0.14, 0.29), IK.WOOD)


def _books(mb, x0, x1, y0, y1, z, rng, face):
    x = x0
    mats = list(IK.CLOTH) + ["MAT_Hide_R05", "MAT_Hide_R05"]
    while x < x1 - 0.06:
        w = min(rng.uniform(0.18, 0.42), x1 - x)
        h = rng.uniform(0.22, 0.31)
        mb.box((x, y0, z), (x + w - 0.01, y1, z + h), rng.choice(mats), skip=("z-", face))
        x += w


def p_shelf(mb, rng, double=True):
    """Estanteria de 1.8 x (0.5 doble / 0.4) x 2.2 m con libros contables en 4 baldas (por grupos de lomos)."""
    d = 0.25 if double else 0.2
    for x in (-0.9, 0.87):
        mb.box((x, -d, 0), (x + 0.03, d, 2.2), IK.WOOD, skip=("z-",))
    for z in (0.08, 0.6, 1.12, 1.64, 2.17):
        mb.box((-0.87, -d, z - 0.03), (0.87, d, z), IK.WOOD, skip=("x-", "x+"))
    if not double:
        mb.box((-0.87, -d, 0.05), (0.87, -d + 0.02, 2.17), IK.WOOD, skip=("x-", "x+"))
    for z in (0.08, 0.6, 1.12, 1.64):
        _books(mb, -0.86, 0.86, 0.0, d - 0.03, z, rng, "y-")
        if double:
            _books(mb, -0.86, 0.86, -d + 0.03, 0.0, z, rng, "y+")


def p_ledger(mb):
    mb.box((-0.2, -0.15, 0), (0.0, 0.15, 0.03), "MAT_Hide_R05")
    mb.box((0.0, -0.15, 0), (0.2, 0.15, 0.03), "MAT_Hide_R05")
    mb.box((-0.19, -0.14, 0.03), (-0.005, 0.14, 0.045), IK.STONE_L, skip=("z-",))
    mb.box((0.005, -0.14, 0.03), (0.19, 0.14, 0.045), IK.STONE_L, skip=("z-",))


def p_scale(mb):
    mb.box((-0.12, -0.08, 0), (0.12, 0.08, 0.04), IK.BRONZE)
    mb.rod((0, 0, 0.04), (0, 0, 0.42), 0.012, IK.BRONZE)
    mb.rod((-0.2, 0, 0.42), (0.2, 0, 0.42), 0.008, IK.BRONZE)
    for x in (-0.2, 0.2):
        mb.rod((x, 0, 0.42), (x, 0, 0.18), 0.003, IK.IRON)
        mb.cylinder(0.07, 0.15, 0.18, 8, IK.BRONZE, r1=0.08, center=(x, 0))


def p_candle(mb):
    mb.cylinder(0.06, 0.0, 0.02, 6, IK.IRON)
    mb.cylinder(0.022, 0.02, 0.2, 6, IK.STONE_L)
    for a in (0.0, math.pi / 2):
        c, s = math.cos(a) * 0.02, math.sin(a) * 0.02
        mb.face([(-c, -s, 0.2), (c, s, 0.2), (0, 0, 0.27)], IK.WARM, nrm=(-s, c, 0))


def p_sconce(mb):
    """Lampara de aceite de pared: brazo de hierro, cazoleta de bronce y llama (cara a +Y, pared en y = 0)."""
    mb.box((-0.06, 0, -0.12), (0.06, 0.03, 0.12), IK.IRON, skip=("y-",))
    mb.rod((0, 0.02, 0.0), (0, 0.32, 0.06), 0.015, IK.IRON)
    mb.cylinder(0.08, 0.02, 0.09, 8, IK.BRONZE, r1=0.1, center=(0, 0.36))
    for a in (0.0, math.pi / 2):
        c, s = math.cos(a) * 0.03, math.sin(a) * 0.03
        mb.face([(-c, 0.36 - s, 0.09), (c, 0.36 + s, 0.09), (0, 0.36, 0.2)], IK.WARM, nrm=(-s, c, 0))


def p_strongbox(mb):
    mb.box((-0.35, -0.22, 0), (0.35, 0.22, 0.42), IK.WOOD, skip=("z-",))
    for x in (-0.25, 0.0, 0.25):
        mb.box((x - 0.025, -0.23, 0), (x + 0.025, 0.23, 0.43), IK.IRON, skip=("z-",))
    mb.box((-0.05, 0.22, 0.22), (0.05, 0.25, 0.34), IK.IRON, skip=("y-",))


def p_coins(mb):
    for x, y, h in ((-0.06, 0.0, 0.06), (0.05, 0.03, 0.04), (0.02, -0.06, 0.08)):
        mb.cylinder(0.035, 0.0, h, 6, IK.BRONZE, center=(x, y))


def p_rug(mb):
    mb.face([(-1.2, -0.8, 0.005), (1.2, -0.8, 0.005), (1.2, 0.8, 0.005), (-1.2, 0.8, 0.005)], IK.CLOTH[0], nrm=(0, 0, 1))


def p_box(mb, locked):
    """Caja de deposito: puerta de hierro de 0.33 x 0.29 m (sale 2.5 cm de la pared, cara +Y), pomo de bronce;
    cerrada: candado de hierro. La placa con el numero es una malla aparte por caja."""
    mb.box((-0.165, 0, 0.0), (0.165, 0.025, 0.29), IK.IRON, skip=("y-", "z-"))
    mb.box((0.11, 0.025, 0.1), (0.135, 0.04, 0.125), IK.BRONZE, skip=("y-",))
    if locked:
        mb.box((-0.03, 0.025, 0.04), (0.03, 0.05, 0.1), IK.IRON, skip=("y-",))
        mb.rod((-0.018, 0.038, 0.1), (0.018, 0.038, 0.1), 0.006, IK.IRON)


def p_vault_door(mb):
    """Puerta de la boveda: hoja de hierro de 2.2 x 3.0 m (cara +Y, 12 cm de grueso), 4 bandas con remaches,
    3 pernios, rueda de cierre con 4 radios, cerrojo y candado."""
    mb.box((-1.1, -0.12, 0.0), (1.1, 0.0, 3.0), IK.IRON, skip=("y-", "z-"))
    for z in (0.3, 1.05, 1.95, 2.7):
        mb.box((-1.08, 0.0, z - 0.06), (1.08, 0.018, z + 0.06), IK.IRON, skip=("y-",))
        for k in range(9):
            x = -0.96 + k * 0.24
            mb.box((x - 0.02, 0.018, z - 0.02), (x + 0.02, 0.032, z + 0.02), IK.BRONZE, skip=("y-",))
    for z in (0.3, 1.5, 2.7):
        mb.cylinder(0.045, z - 0.18, z + 0.18, 6, IK.IRON, center=(-1.1, 0.02))
    cx, cz, r = 0.35, 1.5, 0.32
    ring = [(cx + r * math.cos(2 * math.pi * i / 12), 0.05, cz + r * math.sin(2 * math.pi * i / 12)) for i in range(12)]
    for i in range(12):
        a, b = ring[i], ring[(i + 1) % 12]
        mb.rod(a, b, 0.02, IK.BRONZE)
    for i in range(4):
        a = math.pi / 4 + i * math.pi / 2
        mb.rod((cx, 0.05, cz), (cx + r * math.cos(a), 0.05, cz + r * math.sin(a)), 0.015, IK.BRONZE)
    mb.cylinder(0.06, 0.0, 0.08, 8, IK.BRONZE, center=(cx, cz))
    mb.box((0.7, 0.0, 1.38), (1.08, 0.03, 1.46), IK.IRON, skip=("y-",))
    mb.box((0.8, 0.03, 1.22), (0.9, 0.07, 1.36), IK.IRON)
    mb.rod((0.82, 0.05, 1.36), (0.88, 0.05, 1.36), 0.01, IK.IRON)


PROPS = {"BANK_Bench": p_bench, "BANK_Desk": p_desk, "BANK_Chair": p_chair, "BANK_Stool": p_stool,
         "BANK_Ledger_Open": p_ledger, "BANK_Scale": p_scale, "BANK_Candle": p_candle, "BANK_Sconce": p_sconce,
         "BANK_Strongbox": p_strongbox, "BANK_Coins": p_coins, "BANK_Rug": p_rug}


def build_props(col, rng):
    out = {}
    for n, fn in PROPS.items():
        mb = K.MB()
        fn(mb)
        o = IK.to_obj(mb, n, col)
        o.data.name = n
        out[n] = IK.tris(o)
    for n, dbl in (("BANK_Shelf_Ledgers", True), ("BANK_Shelf_Wall", False)):
        mb = K.MB()
        p_shelf(mb, random.Random(f"{n}-{rng.random()}"), double=dbl)
        o = IK.to_obj(mb, n, col)
        o.data.name = n
        out[n] = IK.tris(o)
    for n, lk in (("BANK_Box_Open", False), ("BANK_Box_Locked", True)):
        mb = K.MB()
        p_box(mb, lk)
        o = IK.to_obj(mb, n, col)
        o.data.name = n
        out[n] = IK.tris(o)
    for o in [bpy.data.objects[n] for n in out]:
        o.location = (6000.0, 0.0, -50.0)                 # fuera de la vista (mallas fuente)
        o.hide_render = True
    return out


# --------------------------------------------------------------------------- boveda
def vault(it, rng):
    """Tabique con puerta (WALL_Near_Vault: se oculta cuando el jugador entra), muro del fondo, boveda de canon
    con 3 arcos fajones (CEILING_Vault), puerta de hierro hecha a mano y farol de esquirla encima."""
    y_a, y_b = VAULT_DOOR
    # tabique x = 7.5..7.9 (cara del vestibulo a -X), hueco 2.2 x 3.0, arco de descarga encima
    mb = K.MB()
    mb.push(M(VAULT_X0, -D / 2, 0.0, 90.0))
    L = D / 2
    u0, u1 = y_a + D / 2, y_b + D / 2
    mb.slab_holes([(0, 0), (L, 0), (L, VAULT_TOP), (0, VAULT_TOP)], [[(u0, 0), (u0, 3.0), (u1, 3.0), (u1, 0)]],
                  -VAULT_T, 0.0, IK.BLOCK, reveal_mat=IK.STONE)
    for x0, x1 in ((u0 - 0.35, u0), (u1, u1 + 0.35)):
        mb.box((x0, 0.0, 0.0), (x1, 0.06, 3.0), IK.STONE, skip=("y-", "z-"))
    IK.prism(mb, IK.arc((u0 + u1) / 2, 3.0, 1.45, a0=0.0, a1=math.pi, n=10) +
             IK.arc((u0 + u1) / 2, 3.0, 1.75, a0=math.pi, a1=0.0, n=10), 0.0, 0.07, IK.STONE, axis="y")
    mb.box((u0 - 0.35, 0.0, 3.0), (u1 + 0.35, 0.06, 3.05), IK.STONE, skip=("y-",))
    mb.pop()
    it.unique(mb, "INT_Banco_VaultWall", "WALL_Near_Vault")
    it.groups["WALL_Near_Vault"]["hide_when"] = "jugador dentro de la boveda"
    # puerta de hierro (cara a -X)
    mb = K.MB()
    p_vault_door(mb)
    door = it.unique(mb, "VAULT_Door", "WALL_Near_Vault", M(VAULT_X0 - 0.0, (y_a + y_b) / 2, 0.0, 90.0), merge=False)
    door["animatable"] = "giro sobre el pernio (lado -Y local), 0 a 100 grados hacia el vestibulo"
    door["hinge_local"] = [-1.1, 0.0, 0.0]
    # farol de esquirla sobre la puerta (unico detalle azul)
    mb = K.MB()
    K.lantern_shard(mb)
    it.unique(mb, "VAULT_ShardLantern", "WALL_Near_Vault", M(VAULT_X0 - 0.0, (y_a + y_b) / 2, 3.45, 90.0))
    # muro del fondo de la boveda (y = -0.4..0) y boveda de canon
    mb = K.MB()
    mb.box((VAULT_X0 + VAULT_T, -0.4, 0.0), (W / 2, 0.0, VAULT_TOP), IK.BLOCK, skip=("z-",))
    it.unique(mb, "INT_Banco_VaultBackWall", "Shell")
    x0, x1 = VAULT_X0 + VAULT_T, W / 2
    r = (x1 - x0) / 2
    cx = (x0 + x1) / 2
    spring = 3.0
    mb = K.MB()
    n = 12
    pts = [(cx - r * math.cos(math.pi * i / n), spring + r * math.sin(math.pi * i / n)) for i in range(n + 1)]
    for i in range(n):
        (xa, za), (xb, zb) = pts[i], pts[i + 1]
        mb.face([(xa, -D / 2, za), (xb, -D / 2, zb), (xb, -0.4, zb), (xa, -0.4, za)], IK.BLOCK, nrm=(cx - xa, 0, spring - za))
    for yc in (-7.3, -5.0, -2.7):
        IK.prism(mb, IK.arc(cx, spring, r - 0.22, a0=0.0, a1=math.pi, n=10) + IK.arc(cx, spring, r, a0=math.pi, a1=0.0, n=10),
                 yc - 0.18, yc + 0.18, IK.STONE, axis="y")
    for yc in (-7.3, -5.0, -2.7):
        for xx in (x0, x1 - 0.25):
            mb.box((xx, yc - 0.2, spring - 0.25), (xx + 0.25, yc + 0.2, spring), IK.STONE)
    it.unique(mb, "INT_Banco_VaultVault", "CEILING_Vault")
    it.groups["CEILING_Vault"]["hide_when"] = "con CEILING o con el jugador dentro de la boveda"
    it.colboxes += [((VAULT_X0, -D / 2, 0), (VAULT_X0 + VAULT_T, y_a, VAULT_TOP)),
                    ((VAULT_X0, y_b, 0), (VAULT_X0 + VAULT_T, 0.0, VAULT_TOP)),
                    ((VAULT_X0, y_a, 3.0), (VAULT_X0 + VAULT_T, y_b, VAULT_TOP)),
                    ((VAULT_X0 + VAULT_T, -0.4, 0), (W / 2, 0.0, VAULT_TOP))]
    it.obstacles += [(0, VAULT_X0, -D / 2, VAULT_X0 + VAULT_T, y_a), (0, VAULT_X0, y_b, VAULT_X0 + VAULT_T, 0.0),
                     (0, VAULT_X0 + VAULT_T, -0.4, W / 2, 0.0)]
    return door


def deposit_boxes(it, num_mat):
    """BOXES_TOTAL cajas en las 4 paredes de la boveda (4 filas, 0.36 x 0.32 m). Cada caja: Empty BANK_Box_NNN
    (box_number, state) con el cuerpo (malla compartida BANK_Box_Open o BANK_Box_Locked) y su placa (malla propia,
    UV a su celda del atlas). Las cajas de las paredes cercanas a la camara cuelgan del grupo de esa pared."""
    x0, x1 = VAULT_X0 + VAULT_T, W / 2
    y0, y1 = -D / 2, -0.4
    pitch_x, pitch_z, z0, rows = 0.36, 0.32, 0.45, 4
    walls = [  # (nombre, grupo, inicio, normal hacia la sala, tramos utiles [(s0, s1)])
        ("+X", "Furniture", Vector((x1, y0)), Vector((-1, 0)), [(0.3, (y1 - y0) - 0.3)]),
        ("-Yv", "Furniture", Vector((x1, y1)), Vector((0, -1)), [(0.3, (x1 - x0) - 0.3)]),
        ("-Xv", "WALL_Near_Vault", Vector((x0, y1)), Vector((1, 0)),
         [(0.3, y1 - VAULT_DOOR[1] - 0.35), (y1 - VAULT_DOOR[0] + 0.35, (y1 - y0) - 0.3)]),
        ("-Y", "WALL_Near_B", Vector((x0, y0)), Vector((0, 1)), [(0.3, (x1 - x0) - 0.3)]),
    ]
    # el modulo corre por t = (n.y, -n.x); se corrigen los inicios para que t vaya en el sentido del tramo
    slots = []
    for name, grp, start, n, spans in walls:
        t = Vector((n.y, -n.x))
        cols = []
        for s0, s1 in spans:
            k = int((s1 - s0) // pitch_x)
            cols += [s0 + pitch_x * (i + 0.5) for i in range(k)]
        slots.append((name, grp, start, n, t, cols))
    total_cols = sum(len(c) for *_r, c in slots)
    alloc = [int(BOXES_TOTAL * len(c) / total_cols) for *_r, c in slots]
    i = 0
    while sum(alloc) < BOXES_TOTAL:
        alloc[i % len(alloc)] += 1
        i += 1
    num = 1
    rows_used = {}
    meshes = {False: bpy.data.meshes["BANK_Box_Open"], True: bpy.data.meshes["BANK_Box_Locked"]}
    for (name, grp, start, n, t, cols), cnt in zip(slots, alloc):
        nrows = min(rows, math.ceil(cnt / len(cols)))
        rows_used[name] = {"boxes": cnt, "cols": len(cols), "rows": nrows}
        rot = Matrix(((t.x, n.x, 0, 0), (t.y, n.y, 0, 0), (0, 0, 1, 0), (0, 0, 0, 1))) @ Matrix.Translation((0, 0.035, 0))
        # panel de acero detras de la reja de cajas (3.5 cm delante de la pared: los sillares salen 3 cm)
        mb = K.MB()
        smin, smax = min(cols) - pitch_x / 2, max(cols) + pitch_x / 2
        mb.box((smin - 0.04, 0.0, z0 - 0.05), (smax + 0.04, 0.012, z0 + nrows * pitch_z + 0.02), IK.IRON, skip=("y-",))
        it.unique(mb, f"BANK_BoxPanel_{name}", grp, Matrix.Translation((start.x, start.y, 0)) @ rot)
        placed = 0
        for r in range(nrows):
            z = z0 + (nrows - 1 - r) * pitch_z
            for s in reversed(cols):  # +X local queda a la IZQUIERDA de quien mira la caja: se numera de izq. a der.
                if placed >= cnt:
                    break
                p = start + t * s
                locked = num > OPEN_DEFAULT
                e = bpy.data.objects.new(f"BANK_Box_{num:03d}", None)
                it.col.objects.link(e)
                e.parent = it.group(grp)
                e.matrix_parent_inverse = Matrix.Identity(4)
                e.matrix_basis = Matrix.Translation((p.x, p.y, z)) @ rot @ Matrix.Translation((0, 0.012, 0))
                e.empty_display_size = 0.1
                e["box_number"] = num
                e["state"] = "Locked" if locked else "Open"
                e["godot"] = "cambiar la malla del hijo _Body entre BANK_Box_Open y BANK_Box_Locked; placa: " \
                             "instance uniform 'locked' suma 0.5 a v (mitad oscura del atlas)"
                body = bpy.data.objects.new(f"BANK_Box_{num:03d}_Body", meshes[locked])
                it.col.objects.link(body)
                body.parent = e
                # placa con UV propia
                me = bpy.data.meshes.new(f"BANK_BoxPlate_{num:03d}")
                u0, v0, u1, v1 = plate_uv(num, locked)
                vs = [(-0.055, 0.042, 0.16), (0.055, 0.042, 0.16), (0.055, 0.042, 0.27), (-0.055, 0.042, 0.27)]
                me.from_pydata(vs, [], [(0, 1, 2, 3)])
                uv = me.uv_layers.new(name="UVWorld")
                # vista de frente (mirando hacia -Y local) la x local crece hacia la izquierda: u invertida
                for li, (uu, vv) in zip(range(4), ((u1, v0), (u0, v0), (u0, v1), (u1, v1))):
                    uv.data[li].uv = (uu, vv)
                me.materials.append(num_mat)
                me.update()
                if me.polygons[0].normal.y < 0:
                    me.polygons[0].flip()
                pl = bpy.data.objects.new(f"BANK_Box_{num:03d}_Plate", me)
                it.col.objects.link(pl)
                pl.parent = e
                num += 1
                placed += 1
    return rows_used


# --------------------------------------------------------------------------- planta alta, escalera, arcada
def upper_floor(it, rng):
    g = "LEVEL_1"
    it.group(g)["hide_when"] = "jugador en la planta baja y la galeria tapa lo que hay debajo (corte isometrico)"
    zs = 3.2
    mb = K.MB()
    mb.box((ARCADE_X[0], ARCADE_Y + 0.25, zs - 0.3), (W / 2, D / 2, zs - 0.15), IK.WOOD)
    mb.box((-W / 2, ARCADE_Y, zs - 0.3), (ARCADE_X[0], D / 2, zs - 0.15), IK.WOOD)
    it.unique(mb, "INT_Banco_UpperSlab", g)
    # entarimado
    def tiles(xa, xb, ya, yb):
        nx, ny = max(1, round((xb - xa) / 2)), max(1, round((yb - ya) / 2))
        for i in range(nx):
            for j in range(ny):
                mesh = "INT_Floor_Planks_B" if rng.random() < 0.2 else "INT_Floor_Planks"
                it.inst(mesh, M(xa + i * (xb - xa) / nx, ya + j * (yb - ya) / ny, zs, 0, (xb - xa) / nx / 2,
                                (yb - ya) / ny / 2), g)
    tiles(ARCADE_X[0], W / 2, ARCADE_Y + 0.25, D / 2)
    tiles(-W / 2, ARCADE_X[0], ARCADE_Y, D / 2)
    # vigas bajo el forjado (a lo largo de y), sin viga sobre la puerta
    for x in [-10.5 + 2.0 * k for k in range(11)]:
        if abs(x - DOOR[0]) < 1.2:
            continue
        it.inst("INT_Beam_Straight", M(x, ARCADE_Y + 0.25, zs - 0.3, 90, (D / 2 - ARCADE_Y - 0.25) / 2), g)
    # balaustrada de la galeria sobre la arcada
    x0 = STAIR_X[1]
    L = W / 2 - x0
    m = round(L / 2)
    for k in range(m):
        it.inst("INT_Railing", M(x0 + k * L / m, ARCADE_Y, zs, 0, L / m / 2), g)
    it.colboxes += [((-W / 2, ARCADE_Y, zs - 0.3), (W / 2, D / 2, zs)), ((x0, ARCADE_Y - 0.15, zs), (W / 2, ARCADE_Y + 0.15, zs + 1.02))]
    it.obstacles.append((1, x0, ARCADE_Y - 0.15, W / 2, ARCADE_Y + 0.15))
    it.nav_regions.append((1, zs, -W / 2, ARCADE_Y, W / 2, D / 2))


def arcade(it):
    """Arcada de 5 vanos (INT_Arch_3m, 4.11 m) en y = 4.5 bajo la galeria; balaustradas del lado del personal en
    los vanos 4 y 5 con puerta de 1.235 m junto al muro +X."""
    x0, x1 = ARCADE_X
    n = 5
    w = (x1 - x0) / n
    for k in range(n):
        it.inst("INT_Arch_3m", M(x0 + k * w, ARCADE_Y, 0, 0, w / 4.0), "Shell")
        for xs in (x0 + k * w, x0 + (k + 1) * w - 0.5 * w / 4.0):
            it.colboxes.append(((xs, ARCADE_Y - 0.25, 0), (xs + 0.5 * w / 4.0, ARCADE_Y + 0.25, FH_())))
            it.obstacles.append((0, xs, ARCADE_Y - 0.25, xs + 0.5 * w / 4.0, ARCADE_Y + 0.25))
    for xa, xb in ((COUNTER_X + 0.4, x0 + 4 * w - 0.5 * w / 4.0), (x0 + 4 * w + 0.5 * w / 4.0, x1 - 1.235 - 0.5 * w / 4.0)):
        it.inst("INT_Railing", M(xa, ARCADE_Y, 0, 0, (xb - xa) / 2), "Shell")
        it.colboxes.append(((xa, ARCADE_Y - 0.14, 0), (xb, ARCADE_Y + 0.14, 1.02)))
        it.obstacles.append((0, xa, ARCADE_Y - 0.14, xb, ARCADE_Y + 0.14))
    return {"bays": n, "bay_w": round(w, 3), "staff_gate_m": 1.235}


def FH_():
    return IK.FH


def stair(it):
    xa, xb = STAIR_X
    ya, yb = STAIR_Y
    for k in range(2):
        it.inst("INT_Stairs_Int", M(xa + k * 1.0, ya, 0), "Shell")
    mb = K.MB()
    IK.prism(mb, [(ya, 0.0), (yb, IK.FH), (yb, IK.FH + 1.0), (ya, 1.0)], xb, xb + 0.25, IK.STONE, axis="x")
    it.unique(mb, "INT_Banco_StairParapet", "Shell")
    run = yb - ya
    it.colprisms.append(([(ya, 0.0), (yb, IK.FH), (yb, 0.0)], xa, xb, "x"))
    it.colboxes.append(((xb, ya, 0), (xb + 0.25, yb, IK.FH + 1.0)))
    it.obstacles.append((0, xa, ya, xb + 0.25, yb))
    it.ramps.append((xa, xb, -0.55, 4.45, 0.0, IK.FH))
    it.patches = getattr(it, "patches", []) + [(xa, xb, -1.05, -0.55, 0.0), (xa, xb, 4.45, 4.95, IK.FH)]
    return {"width_m": xb - xa, "run_m": run, "rise_m": IK.FH, "slope_deg": round(math.degrees(math.atan2(IK.FH, run)), 1)}


# --------------------------------------------------------------------------- mostrador y mobiliario
def counter(it):
    ya, yb = COUNTER_Y
    n = 5
    for k in range(n):
        y = yb - k * 2.0
        it.inst("INT_Counter_Straight_B" if k == 3 else "INT_Counter_Straight", M(COUNTER_X, y, 0, -90), "Shell")
        g = "INT_Grille_Teller" if k == 1 else "INT_Grille_Wicket" if k == 3 else "INT_Grille"
        it.inst(g, M(COUNTER_X, y, 1.1, -90), "Shell")
    # remate sur: murete hasta el tabique de la boveda
    mb = K.MB()
    mb.box((COUNTER_X - 0.4, ya - 0.4, 0), (VAULT_X0, ya, 1.1), IK.STONE, skip=("z-",))
    mb.box((COUNTER_X - 0.45, ya - 0.45, 1.0), (VAULT_X0, ya + 0.02, 1.1), IK.WOOD)
    it.unique(mb, "INT_Banco_CounterReturn", "Shell")
    it.colboxes += [((COUNTER_X - 0.45, ya, 0), (COUNTER_X + 0.45, yb, 2.6)), ((COUNTER_X - 0.45, ya - 0.45, 0), (VAULT_X0, ya, 1.1))]
    it.obstacles += [(0, COUNTER_X - 0.46, ya, COUNTER_X + 0.46, yb), (0, COUNTER_X - 0.45, ya - 0.45, VAULT_X0, ya)]
    return {"length_m": yb - ya, "grille_modules": n, "wickets": 1, "teller_window": {"clear_m": 1.2, "y": [yb - 2.0 - 1.6, yb - 2.0 - 0.4]}}


def furniture(it, rng):
    F = "Furniture"
    F1 = "Furniture_L1"
    it.group(F1).parent = it.group("LEVEL_1")
    rows = []

    def put(mesh, mw, grp=F, obst=None, level=0, name=None):
        o = it.inst(mesh, mw, grp, name=name or f"PROP_{mesh}")
        if obst:
            lo, hi = obst
            it.colboxes.append((lo, hi))
            it.obstacles.append((level, lo[0], lo[1], hi[0], hi[1]))
        rows.append(mesh)
        return o
    # sala de espera: 3 bancos de cara al mostrador
    for x in (-5.0, -2.5, 0.0):
        put("BANK_Bench", M(x, 2.2, 0, -90), obst=((x - 0.26, 1.2, 0), (x + 0.22, 3.2, 0.92)))
    # archivo: 3 filas de estantes de doble cara (2 por fila) y escritorio
    for yc in (-8.0, -6.0, -4.0):
        for xc in (-8.1, -6.3):
            put("BANK_Shelf_Ledgers", M(xc, yc, 0, 0), obst=((xc - 0.9, yc - 0.25, 0), (xc + 0.9, yc + 0.25, 2.2)))
    put("BANK_Desk", M(-6.6, -1.6, 0, 180), obst=((-7.4, -2.0, 0), (-5.8, -1.2, 0.8)))
    put("BANK_Chair", M(-6.6, -0.9, 0, 180), obst=((-6.85, -1.15, 0), (-6.35, -0.65, 1.0)))
    put("BANK_Ledger_Open", M(-6.5, -1.6, 0.79, 15))
    put("BANK_Candle", M(-7.2, -1.8, 0.79))
    # mostrador: banquero, taburete, libros, balanza, velas, monedas
    put("BANK_Stool", M(BANKER[0] + 0.2, BANKER[1], 0, 90), obst=((BANKER[0], BANKER[1] - 0.2, 0), (BANKER[0] + 0.4, BANKER[1] + 0.2, 0.67)))
    put("BANK_Ledger_Open", M(COUNTER_X, BANKER[1] - 0.6, 1.1, 90))
    put("BANK_Scale", M(COUNTER_X, -1.4, 1.1, 90))
    put("BANK_Coins", M(COUNTER_X + 0.1, 0.4, 1.1))
    for y in (-3.6, 3.2):
        put("BANK_Candle", M(COUNTER_X + 0.15, y, 1.1))
    # cuarto del personal tras la boveda
    for x, y in ((9.0, 1.0), (10.6, 2.4)):
        put("BANK_Strongbox", M(x, y, 0, 180), obst=((x - 0.36, y - 0.23, 0), (x + 0.36, y + 0.23, 0.45)))
    # hogar en la fachada (bajo la galeria)
    put("INT_Fireplace", M(-5.0, D / 2, 0, 180), obst=((-7.0, D / 2 - 0.75, 0), (-5.0, D / 2, 1.5)))
    # lamparas de aceite: pilares de la arcada (cara a -Y) y boveda
    x0, x1 = ARCADE_X
    w = (x1 - x0) / 5
    for k in (1, 2, 3):
        put("BANK_Sconce", M(x0 + k * w, ARCADE_Y - 0.25, 2.3, 180))
    put("BANK_Sconce", M(W / 2, -5.0, 2.3, 90))
    put("BANK_Sconce", M(9.73, -0.4, 2.3, 180))
    # planta alta: despacho
    zs = IK.FH
    put("BANK_Rug", M(8.5, 6.8, zs), grp=F1)
    put("BANK_Desk", M(8.5, 7.2, zs, 180), grp=F1, obst=((7.7, 6.8, zs), (9.3, 7.6, zs + 0.8)), level=1)
    put("BANK_Chair", M(8.5, 8.0, zs, 180), grp=F1, obst=((8.25, 7.75, zs), (8.75, 8.25, zs + 1.0)), level=1)
    put("BANK_Ledger_Open", M(8.7, 7.2, zs + 0.79, -10), grp=F1)
    put("BANK_Candle", M(8.0, 7.0, zs + 0.79), grp=F1)
    put("BANK_Shelf_Wall", M(5.9, D / 2 - 0.21, zs, 180), grp=F1, obst=((5.0, D / 2 - 0.42, zs), (6.8, D / 2, zs + 2.2)), level=1)
    put("BANK_Strongbox", M(10.7, 8.6, zs, 180), grp=F1, obst=((10.34, 8.37, zs), (11.06, 8.83, zs + 0.45)), level=1)
    put("BANK_Sconce", M(2.0, D / 2, zs + 2.0, 180), grp=F1)
    return rows


def lights(it):
    L = it.light
    warm, flame, day, blue = "#FFB46B", "#FFA650", "#FFE6C4", "#8FD0FF"
    x0, x1 = ARCADE_X
    w = (x1 - x0) / 5
    for k in (1, 2, 3):
        L(f"LIGHT_Lamp_{k:02d}", (x0 + k * w, ARCADE_Y - 0.65, 2.45), flame, 0.8, 6.0)
    L("LIGHT_Lamp_Vault", (W / 2 - 0.4, -5.0, 2.45), flame, 0.5, 4.0)
    L("LIGHT_Lamp_Vault_2", (9.73, -0.8, 2.45), flame, 0.5, 4.0)
    L("LIGHT_Lamp_Office", (2.0, D / 2 - 0.4, IK.FH + 2.15), flame, 0.6, 5.0)
    L("LIGHT_Hearth", (-6.0, D / 2 - 0.6, 0.6), "#FF9A48", 1.0, 7.0)
    for i, (x, y, z) in enumerate(((COUNTER_X + 0.15, -3.6, 1.35), (COUNTER_X + 0.15, 3.2, 1.35), (-7.2, -1.8, 1.05),
                                   (8.0, 7.0, IK.FH + 1.05))):
        L(f"LIGHT_Candle_{i + 1:02d}", (x, y, z), flame, 0.35, 2.8)
    for i, (x, y, z) in enumerate(((-8.5, D / 2 - 0.6, 1.9), (7.0, D / 2 - 0.6, 1.9), (W / 2 - 0.6, 2.5, 1.9),
                                   (-3.5, D / 2 - 0.6, IK.FH + 1.9), (8.5, D / 2 - 0.6, IK.FH + 1.9),
                                   (W / 2 - 0.6, 7.0, IK.FH + 1.9))):
        L(f"LIGHT_Window_{i + 1:02d}", (x, y, z), day, 0.45, 5.0, kind="omni_window")
    L("LIGHT_Shard_VaultDoor", (VAULT_X0 - 0.45, sum(VAULT_DOOR) / 2, 3.3), blue, 0.35, 3.0, kind="omni_magic")


def markers(it):
    it.entry_markers(inward_yaw_deg=180.0, exit_yaw_deg=0.0, spawn_dist=1.6)
    it.marker("MARKER_NPC_Slot_01", (BANKER[0], BANKER[1], 0.0), 90.0, npc="Banquero",
              note="detras del mostrador, mirando al publico (-X) y a la camara")
    it.marker("MARKER_Interact_Bank_Counter", (COUNTER_X - 1.0, TELLER_Y, 0.0), -90.0, tipo="bank_counter",
              accion="abre el banco")
    it.marker("MARKER_Interact_Vault", (VAULT_X0 - 0.8, sum(VAULT_DOOR) / 2, 0.0), -90.0, tipo="vault",
              accion="abre la boveda (cajas de deposito)")


OPENINGS = [("+Y", W / 2 - DOOR[0], "door_iron", 0),
            ("+Y", W / 2 + 8.5, "window", 0), ("+Y", W / 2 - 7.0, "window", 0),
            ("+X", 2.5 + D / 2, "window", 0),
            ("+Y", W / 2 + 8.5, "window", 1), ("+Y", W / 2 + 3.5, "window", 1), ("+Y", W / 2 - 3.0, "window", 1),
            ("+Y", W / 2 - 8.5, "window", 1), ("+X", -5.0 + D / 2, "window", 1), ("+X", 7.0 + D / 2, "window", 1),
            ("-X", D / 2 + 5.0, "window", 0), ("-Y", 5.55, "window", 1)]


def build(col, world_rot_deg, repo, seed=2701):
    rng = random.Random(seed)
    it = IK.Interior("Banco", (W, D, H), "piedra", seed, world_rot_deg, DOOR, col)
    it.shell(openings=OPENINGS, storeys=2)
    it.nav_regions.append((0, 0.0, -W / 2, -D / 2, W / 2, D / 2))
    info = {}
    info["vault_door"] = vault(it, rng).name
    path = number_atlas(repo)
    nm = number_material(path)
    info["boxes"] = deposit_boxes(it, nm)
    upper_floor(it, rng)
    info["arcade"] = arcade(it)
    info["stair"] = stair(it)
    info["counter"] = counter(it)
    info["furniture"] = furniture(it, rng)
    lights(it)
    markers(it)
    info["atlas"] = os.path.relpath(path, repo)
    return it, info
