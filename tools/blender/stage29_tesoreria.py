"""
CONCORDIA - Etapa 29: interior de la Tesoreria de la Muralla (int_tesoreria.glb). Todo hecho a mano (regla del
usuario: la Tesoreria no usa assets descargados ni IA).

Referencias: Palazzo Pubblico de Siena (salas macizas, arcos, luz tamizada) y gran salon medieval de piedra (muros
altos, vigas, poca luz). Funcion: compra esquirlas a precio fijo y cambia plata por oro (1 de oro = 100 de plata);
los tubos de luz azul hacia el Faro se ven entrar por el techo.

Marco centrado del TesoreriaMuralla_InteriorVolume: x en [-13.2, 13.2], y en [-6.8, 6.8], z en [0, 8.8], dos
plantas de 4.4 m; +Y = fachada de la plaza (puerta en x = 0). Giro del edificio -90: CAM_Iso mira desde +X +Y, asi
que los muros cercanos son +X y +Y (fachada) y todo lo importante va contra -X y -Y, de cara a la camara.

Planta baja: vestibulo con 2 mostradores contra el muro -X (taquillas con reja y ventanilla de cajero de 1.2 m;
Tesorero y Cambista detras, de cara al publico y a la camara), balanza grande de bronce en cada mostrador; arcada de
6 vanos bajo la galeria con los 4 tubos de luz (PIPE_Light_01-04, 0.4 m) subiendo por sus pilares hasta atravesar el
techo; 4 vitrinas delante de la arcada con las esquirlas de cada tipo (Opaca, Brillante, Latente, Madura);
contaduria bajo la galeria (estantes de libros, mesa, cofres). Escalera de piedra de 2 m contra el muro +X
(33.7 grados) que sube por un hueco del forjado.
Planta alta (LEVEL_1, a lo largo del muro del fondo -Y): galeria con balaustrada sobre la arcada, archivo y despacho
del tesorero (WALL_Near_Despacho) con la caja fuerte.
Ventanas en las mismas posiciones y medidas que las del exterior (TesoreriaMuralla_Body).
"""

import math
import random

import bpy
from mathutils import Matrix, Vector

import bld_kit as K
import interior_kit as IK
import stage27_banco as SB

W, D, H = 26.4, 13.6, 8.8
SH = H / 2                         # 4.4 m por planta
SZ = SH / IK.FH                    # escala vertical de los modulos del kit
DOOR = (0.0, D / 2)
COUNTER_X = -11.2                  # eje de los mostradores (tablero de x -11.66 a -10.74)
C1_Y0, C2_Y0 = 3.1, -1.7           # inicio de cada mostrador: modulo de ventanilla (2 m) + modulo de reja (1.6 m)
TELLER = {1: C1_Y0 + 1.0, 2: C2_Y0 + 1.0}        # centro de la ventanilla de cajero
NPC = {1: (-11.9, TELLER[1] - 0.4), 2: (-11.9, TELLER[2] - 0.4)}  # leccion 7: ventanilla 0.4 m hacia la camara
ARC_Y = -1.8                       # eje de la arcada; borde de la galeria en y = -1.55
GAL_Y = ARC_Y + 0.25
ARC_X0, ARC_X1, BAYS = -W / 2, 11.0, 6
BAY_W = (ARC_X1 - ARC_X0) / BAYS
PIERS = [ARC_X0 + k * BAY_W for k in range(1, BAYS)]
PIPE_X = PIERS[1:5]
PIPE_Y = GAL_Y + 0.05 + 0.2
VIT_Y = -0.45
VITRINAS = [  # (x, variante, tipo de esquirla)
    (0.5 * (PIERS[0] + PIERS[1]), "A", "Brillante"),
    (0.5 * (PIERS[1] + PIERS[2]), "B", "Opaca"),
    (0.5 * (PIERS[2] + PIERS[3]), "C", "Madura"),
    (0.5 * (PIERS[3] + PIERS[4]), "B", "Latente"),
]
STAIR_X = (11.2, W / 2 - 0.02)
STAIR_Y = (2.4, -4.2)              # pie (z 0) y llegada (z 4.4): 6.6 m de recorrido
DESP_X = -6.2                      # tabique del despacho (cara de la galeria)
DESP_DOOR = (-3.4, -2.0)
SHARD_MATS = {"Opaca": "MAT_Shard_Opaca", "Brillante": "MAT_Shard_Brillante", "Latente": "MAT_Shard_Latente",
              "Madura": "MAT_Shard_Madura"}
GLASS = "MAT_Pipe_Glass"           # vidrio sin emision (MAT_Glass_R04 emite azul: un azul de mas)
FELT = "MAT_Felt_R05"


def M(x, y, z=0.0, yaw=0.0, sx=1.0, sy=1.0, sz=1.0):
    return SB.M(x, y, z, yaw, sx, sy, sz)


# --------------------------------------------------------------------------- huecos (medidas del exterior)
def openings():
    """Ventanas y puerta en las posiciones de TesoreriaMuralla_Body (y interior = y del edificio + 1.4)."""
    z = lambda zz, k: (zz - k * SH) / SZ                       # noqa: E731  (m reales -> espacio del modulo)
    ground = IK.custom_module("INT_Window_Tes_PB", bpy.context.scene.collection, "window", w=1.0, z0=z(1.4, 0), z1=z(2.8, 0))
    upper = IK.custom_module("INT_Window_Tes_PA", bpy.context.scene.collection, "window", w=1.4, z0=z(5.6, 1), z1=z(7.8, 1))
    front = IK.custom_module("INT_Window_Tes_Fachada", bpy.context.scene.collection, "window", w=1.2, z0=z(1.2, 0),
                             z1=z(2.8, 0))
    door = IK.custom_module("INT_Door_Tes", bpy.context.scene.collection, "door", ow=1.6, oh=3.0 / SZ)
    ops = []
    for y in (-3.6, 1.4):                                   # muro -X: s = D/2 - y ; muro +X: s = y + D/2
        ops += [("-X", D / 2 - y, ground, 0), ("+X", y + D / 2, ground, 0)]
    for y in (-3.6, 0.4, 4.4):
        ops += [("-X", D / 2 - y, upper, 1), ("+X", y + D / 2, upper, 1)]
    for x in (-9.0, -3.0, 3.0, 9.0):                        # muro -Y: s = x + W/2
        ops.append(("-Y", x + W / 2, ground, 0))
    for x in (-10.0, -5.0, 0.0, 5.0, 10.0):
        ops.append(("-Y", x + W / 2, upper, 1))
    ops += [("+Y", W / 2 - DOOR[0], door, 0), ("+Y", W / 2 - 7.6, front, 0), ("+Y", W / 2 + 7.6, front, 0)]
    return ops


# --------------------------------------------------------------------------- materiales nuevos
def shard_materials():
    """Esquirlas por tipo: Opaca gris, Brillante azul tenue, Latente azul medio, Madura azul palido #8FD0FF emisiva
    (emision 1.0: la unica que brilla). Saturacion > 0.35 solo en tonos 185-215."""
    spec = {"MAT_Shard_Opaca": ("7C8288", 0.75, 0.0), "MAT_Shard_Brillante": ("B6CFDF", 0.15, 0.0),
            "MAT_Shard_Latente": ("5B8DB8", 0.3, 0.0), "MAT_Shard_Madura": ("8FD0FF", 0.25, 1.0)}
    out = {}
    for name, (hx, rough, em) in spec.items():
        m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
        m.use_nodes = True
        b = m.node_tree.nodes["Principled BSDF"]
        c = tuple(SB_lin(int(hx[i:i + 2], 16) / 255) for i in (0, 2, 4)) + (1.0,)
        b.inputs["Base Color"].default_value = c
        b.inputs["Roughness"].default_value = rough
        b.inputs["Emission Color"].default_value = c if em > 0 else (0, 0, 0, 1)
        b.inputs["Emission Strength"].default_value = em
        m.diffuse_color = c
        m["note"] = f"esquirla {name.split('_')[-1]} (#{hx}); emision {em}"
        out[name] = hx
    return out


def SB_lin(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


# --------------------------------------------------------------------------- props a mano (+Y = frente)
def p_shard(mb):
    """Esquirla: prisma hexagonal con dos puntas (24 tris), 0.18 m de alto, radio 0.045."""
    r, z0, z1, zt, zb = 0.045, 0.04, 0.14, 0.18, 0.0
    ring = lambda z: [(r * math.cos(math.pi / 3 * i), r * math.sin(math.pi / 3 * i), z) for i in range(6)]  # noqa
    lo, hi = ring(z0), ring(z1)
    for i in range(6):
        j = (i + 1) % 6
        mb.face([lo[i], lo[j], hi[j], hi[i]], "MAT_Shard_Opaca")
        mb.face([hi[i], hi[j], (0, 0, zt)], "MAT_Shard_Opaca")
        mb.face([lo[j], lo[i], (0, 0, zb)], "MAT_Shard_Opaca")


def p_scale_large(mb):
    """Balanza grande de bronce (0.78 m): base escalonada, columna, cruz con fiel, dos platos colgados."""
    mb.box((-0.2, -0.11, 0), (0.2, 0.11, 0.04), IK.BRONZE)
    mb.box((-0.14, -0.08, 0.04), (0.14, 0.08, 0.08), IK.BRONZE)
    mb.cylinder(0.022, 0.08, 0.7, 8, IK.BRONZE, caps=False)
    mb.box((-0.05, -0.03, 0.66), (0.05, 0.03, 0.72), IK.BRONZE)
    mb.rod((-0.32, 0, 0.7), (0.32, 0, 0.7), 0.012, IK.BRONZE, caps=True)
    mb.face([(-0.012, 0.031, 0.72), (0.012, 0.031, 0.72), (0, 0.031, 0.8)], IK.BRONZE, nrm=(0, 1, 0))
    for x in (-0.3, 0.3):
        for dy in (-0.06, 0.06):
            mb.rod((x, 0, 0.7), (x + dy * 0.5, dy, 0.3), 0.004, IK.IRON)
        mb.cylinder(0.11, 0.27, 0.3, 10, IK.BRONZE, r1=0.13, center=(x, 0))


def p_safe(mb):
    """Caja fuerte de la Tesoreria (1.0 x 0.75 x 1.5 m sobre zocalo): cuerpo de hierro con cantos reforzados, puerta
    con 3 pernios, rueda de 6 radios, bocallave de bronce, bandas remachadas y placa con el escudo de Concordia."""
    mb.box((-0.55, -0.42, 0), (0.55, 0.42, 0.12), IK.STONE, skip=("z-",))
    mb.box((-0.5, -0.375, 0.12), (0.5, 0.375, 1.62), IK.IRON, skip=("z-",))
    for sx in (-1, 1):
        for sy in (-1, 1):
            mb.box((sx * 0.5 - 0.035, sy * 0.375 - 0.035, 0.12), (sx * 0.5 + 0.035, sy * 0.375 + 0.035, 1.62), IK.IRON,
                   skip=("z-", "z+"))
    mb.box((-0.52, -0.395, 1.62), (0.52, 0.395, 1.68), IK.IRON)
    y = 0.375
    mb.box((-0.43, y, 0.2), (0.43, y + 0.03, 1.54), IK.IRON, skip=("y-",))                    # hoja
    for z in (0.32, 0.87, 1.42):
        mb.box((-0.45, y + 0.03, z - 0.04), (0.45, y + 0.045, z + 0.04), IK.IRON, skip=("y-",))
        for k in range(6):
            x = -0.375 + k * 0.15
            mb.box((x - 0.012, y + 0.045, z - 0.012), (x + 0.012, y + 0.058, z + 0.012), IK.BRONZE, skip=("y-",))
    for z in (0.35, 0.87, 1.39):
        mb.cylinder(0.03, z - 0.1, z + 0.1, 6, IK.IRON, center=(-0.45, y + 0.03))
    cx, cz, r = 0.12, 1.1, 0.16
    pts = [(cx + r * math.cos(2 * math.pi * i / 10), y + 0.07, cz + r * math.sin(2 * math.pi * i / 10)) for i in range(10)]
    for i in range(10):
        mb.rod(pts[i], pts[(i + 1) % 10], 0.012, IK.BRONZE)
    for i in range(6):
        a = 2 * math.pi * i / 6
        mb.rod((cx, y + 0.07, cz), (cx + r * math.cos(a), y + 0.07, cz + r * math.sin(a)), 0.009, IK.BRONZE)
    mb.box((cx - 0.03, y + 0.03, cz - 0.03), (cx + 0.03, y + 0.09, cz + 0.03), IK.BRONZE, skip=("y-",))
    mb.box((0.25, y + 0.03, 0.62), (0.35, y + 0.045, 0.76), IK.BRONZE, skip=("y-",))           # bocallave
    mb.box((-0.2, y + 0.03, 0.55), (0.0, y + 0.04, 0.7), IK.BRONZE, skip=("y-",))              # placa del escudo
    mb.face([(-0.1, y + 0.041, 0.57), (-0.04, y + 0.041, 0.62), (-0.1, y + 0.041, 0.68), (-0.16, y + 0.041, 0.62)],
            IK.IRON, nrm=(0, 1, 0))


def p_vitrina(mb, variant):
    """Vitrinas de la Tesoreria (<= 800 tris, vidrio sin emision):
    A: armario alto 1.6 x 0.55 x 2.1 m con 3 baldas de vidrio; B: mesa vitrina 1.4 x 0.7 x 1.1 m con tapa
    inclinada y cama de fieltro; C: pedestal de piedra 0.75 x 0.75 x 0.9 m con caja de vidrio de 0.62 m y aristas de
    bronce. Devuelve las alturas de las baldas (para las esquirlas)."""
    if variant == "A":
        w, d = 1.6, 0.55
        mb.box((-w / 2, -d / 2, 0), (w / 2, d / 2, 0.25), IK.WOOD, skip=("z-",))
        mb.box((-w / 2, -d / 2, 0.25), (w / 2, -d / 2 + 0.03, 2.0), IK.WOOD)                    # fondo
        for sx in (-1, 1):
            for sy in (-1, 1):
                x, yy = sx * (w / 2 - 0.03), sy * (d / 2 - 0.03)
                mb.box((x - 0.03, yy - 0.03, 0.25), (x + 0.03, yy + 0.03, 2.0), IK.WOOD, skip=("z-", "z+"))
        mb.box((-w / 2 - 0.04, -d / 2 - 0.02, 2.0), (w / 2 + 0.04, d / 2 + 0.04, 2.1), IK.WOOD)
        mb.box((-w / 2 - 0.02, d / 2, 1.92), (w / 2 + 0.02, d / 2 + 0.035, 1.98), IK.BRONZE, skip=("y-",))
        shelves = (0.55, 1.05, 1.55)
        for z in shelves:
            mb.box((-w / 2 + 0.06, -d / 2 + 0.03, z - 0.012), (w / 2 - 0.06, d / 2 - 0.06, z), GLASS)
            mb.box((-w / 2 + 0.06, d / 2 - 0.08, z - 0.03), (w / 2 - 0.06, d / 2 - 0.06, z), IK.BRONZE, skip=("y-",))
        mb.face([(-w / 2 + 0.06, d / 2 - 0.01, 0.27), (w / 2 - 0.06, d / 2 - 0.01, 0.27), (w / 2 - 0.06, d / 2 - 0.01, 1.98),
                 (-w / 2 + 0.06, d / 2 - 0.01, 1.98)], GLASS, nrm=(0, 1, 0))
        for sx in (-1, 1):
            mb.face([(sx * (w / 2 - 0.01), -d / 2 + 0.06, 0.27), (sx * (w / 2 - 0.01), d / 2 - 0.06, 0.27),
                     (sx * (w / 2 - 0.01), d / 2 - 0.06, 1.98), (sx * (w / 2 - 0.01), -d / 2 + 0.06, 1.98)], GLASS,
                    nrm=(sx, 0, 0))
        return [(z, (-w / 2 + 0.12, w / 2 - 0.12), (-d / 2 + 0.1, d / 2 - 0.14)) for z in shelves] + \
            [(0.25, (-w / 2 + 0.12, w / 2 - 0.12), (-d / 2 + 0.1, d / 2 - 0.14))]
    if variant == "B":
        w, d = 1.4, 0.7
        for sx in (-1, 1):
            for sy in (-1, 1):
                x, yy = sx * (w / 2 - 0.06), sy * (d / 2 - 0.06)
                mb.box((x - 0.035, yy - 0.035, 0), (x + 0.035, yy + 0.035, 0.7), IK.WOOD, skip=("z-",))
        mb.box((-w / 2, -d / 2, 0.62), (w / 2, d / 2, 0.82), IK.WOOD)
        mb.box((-w / 2 + 0.05, -d / 2 + 0.05, 0.82), (w / 2 - 0.05, d / 2 - 0.05, 0.84), FELT, skip=("z-",))
        mb.box((-w / 2 - 0.02, d / 2, 0.66), (w / 2 + 0.02, d / 2 + 0.03, 0.7), IK.BRONZE, skip=("y-",))
        zf, zb = 0.98, 1.12
        for sx in (-1, 1):                                        # postes de bronce en las esquinas
            for sy, zt in ((1, zf), (-1, zb)):
                x, yy = sx * (w / 2 - 0.02), sy * (d / 2 - 0.02)
                mb.box((x - 0.02, yy - 0.02, 0.82), (x + 0.02, yy + 0.02, zt), IK.BRONZE, skip=("z-",))
        mb.face([(-w / 2, d / 2 - 0.01, 0.82), (w / 2, d / 2 - 0.01, 0.82), (w / 2, d / 2 - 0.01, zf), (-w / 2, d / 2 - 0.01, zf)],
                GLASS, nrm=(0, 1, 0))
        mb.face([(-w / 2, -d / 2 + 0.01, 0.82), (w / 2, -d / 2 + 0.01, 0.82), (w / 2, -d / 2 + 0.01, zb), (-w / 2, -d / 2 + 0.01, zb)],
                GLASS, nrm=(0, -1, 0))
        for sx in (-1, 1):
            mb.face([(sx * (w / 2 - 0.01), -d / 2, 0.82), (sx * (w / 2 - 0.01), d / 2, 0.82), (sx * (w / 2 - 0.01), d / 2, zf),
                     (sx * (w / 2 - 0.01), -d / 2, zb)], GLASS, nrm=(sx, 0, 0))
        mb.face([(-w / 2, -d / 2, zb), (w / 2, -d / 2, zb), (w / 2, d / 2, zf), (-w / 2, d / 2, zf)], GLASS, nrm=(0, 0.6, 1))
        return [(0.84, (-w / 2 + 0.12, w / 2 - 0.12), (-d / 2 + 0.12, d / 2 - 0.12))]
    # C: pedestal
    mb.box((-0.38, -0.38, 0), (0.38, 0.38, 0.12), IK.STONE, skip=("z-",))
    mb.box((-0.3, -0.3, 0.12), (0.3, 0.3, 0.8), IK.BLOCK, skip=("z-", "z+"))
    mb.box((-0.38, -0.38, 0.8), (0.38, 0.38, 0.9), IK.STONE)
    mb.box((-0.27, -0.27, 0.9), (0.27, 0.27, 0.93), FELT, skip=("z-",))
    a, z0, z1 = 0.31, 0.9, 1.52
    for sx in (-1, 1):
        for sy in (-1, 1):
            mb.box((sx * a - 0.018, sy * a - 0.018, z0), (sx * a + 0.018, sy * a + 0.018, z1), IK.BRONZE, skip=("z-",))
    mb.box((-a - 0.02, -a - 0.02, z1), (a + 0.02, a + 0.02, z1 + 0.04), IK.BRONZE)
    mb.cylinder(0.05, z1 + 0.04, z1 + 0.1, 6, IK.BRONZE, r1=0.02)
    for n, (p0, p1, p2, p3) in (((0, 1, 0), ((-a, a, z0), (a, a, z0), (a, a, z1), (-a, a, z1))),
                                ((0, -1, 0), ((-a, -a, z0), (a, -a, z0), (a, -a, z1), (-a, -a, z1))),
                                ((1, 0, 0), ((a, -a, z0), (a, a, z0), (a, a, z1), (a, -a, z1))),
                                ((-1, 0, 0), ((-a, -a, z0), (-a, a, z0), (-a, a, z1), (-a, -a, z1)))):
        mb.face([p0, p1, p2, p3], GLASS, nrm=n)
    return [(0.93, (-0.2, 0.2), (-0.2, 0.2))]


def p_pipe(mb, z_top):
    """Tubo de luz de 0.4 m (vidrio MAT_Pipe_Glass con alma MAT_Pipe_Light_Core, emision 1.5): basa de piedra y
    hierro en el suelo, abrazaderas al pilar cada 1.6 m. Origen en el eje del tubo, en el suelo; el pilar a -Y."""
    mb.box((-0.34, -0.3, 0), (0.34, 0.3, 0.42), IK.STONE, skip=("z-",))
    mb.box((-0.3, -0.26, 0.42), (0.3, 0.26, 0.5), IK.IRON)
    mb.cylinder(0.2, 0.5, z_top, 12, GLASS, caps=False)
    mb.cylinder(0.075, 0.5, z_top, 8, "MAT_Pipe_Light_Core", caps=False)
    mb.cylinder(0.24, 0.5, 0.62, 12, IK.IRON, caps=True)
    z = 1.6
    while z < z_top - 0.4:
        mb.cylinder(0.225, z - 0.05, z + 0.05, 12, IK.IRON, caps=False)
        mb.box((-0.04, -0.3, z - 0.04), (0.04, -0.19, z + 0.04), IK.IRON, skip=("y-",))
        z += 1.6


def p_chandelier(mb, drop):
    """Corona de hierro de 1.4 m con 8 velas y 4 cadenas de 'drop' m hasta el techo (origen en el aro)."""
    n = 16
    r = 0.7
    pts = [(r * math.cos(2 * math.pi * i / n), r * math.sin(2 * math.pi * i / n), 0.0) for i in range(n)]
    for i in range(n):
        mb.rod(pts[i], pts[(i + 1) % n], 0.02, IK.IRON)
    for k in range(8):
        a = 2 * math.pi * k / 8
        x, y = r * math.cos(a), r * math.sin(a)
        mb.cylinder(0.05, 0.0, 0.03, 6, IK.IRON, center=(x, y))
        mb.cylinder(0.02, 0.03, 0.2, 6, IK.STONE_L, center=(x, y), caps=False)
        for b in (0.0, math.pi / 2):
            c, s = math.cos(b) * 0.02, math.sin(b) * 0.02
            mb.face([(x - c, y - s, 0.2), (x + c, y + s, 0.2), (x, y, 0.27)], IK.WARM, nrm=(-s, c, 0))
    for k in range(4):
        a = 2 * math.pi * k / 4 + math.pi / 4
        mb.rod((r * math.cos(a), r * math.sin(a), 0.0), (0, 0, drop * 0.35), 0.008, IK.IRON)
    mb.rod((0, 0, drop * 0.35), (0, 0, drop), 0.012, IK.IRON)


def p_coin_sack(mb):
    """Saco de monedas atado (cuero), 0.3 m."""
    ring = lambda r, z: [(r * math.cos(2 * math.pi * i / 8), r * math.sin(2 * math.pi * i / 8), z) for i in range(8)]  # noqa
    rs = [(0.1, 0.0), (0.15, 0.06), (0.15, 0.16), (0.08, 0.24), (0.04, 0.27), (0.07, 0.31)]
    rings = [ring(r, z) for r, z in rs]
    for a, b in zip(rings, rings[1:]):
        for i in range(8):
            j = (i + 1) % 8
            mb.face([a[i], a[j], b[j], b[i]], "MAT_Hide_R05")
    mb.ngon_fill(rings[0], "MAT_Hide_R05", flip=True)
    mb.ngon_fill(rings[-1], "MAT_Hide_R05")
    mb.cylinder(0.05, 0.25, 0.27, 8, IK.WOOD_L, caps=False)


PROPS = {"TES_Scale_Large": p_scale_large, "TES_Safe": p_safe, "TES_Coin_Sack": p_coin_sack}


def build_props(col):
    out = {}
    for n, fn in PROPS.items():
        if bpy.data.meshes.get(n) is not None:
            continue
        mb = K.MB()
        fn(mb)
        o = IK.to_obj(mb, n, col)
        o.data.name = n
        out[n] = IK.tris(o)
    shelves = {}
    for v in ("A", "B", "C"):
        n = f"TES_Vitrina_{v}"
        mb = K.MB()
        shelves[v] = p_vitrina(mb, v)
        o = IK.to_obj(mb, n, col)
        o.data.name = n
        out[n] = IK.tris(o)
    # esquirlas: misma forma, un material por tipo
    for tipo, mat in SHARD_MATS.items():
        n = f"TES_Shard_{tipo}"
        mb = K.MB()
        p_shard(mb)
        mb.mats = [mat]
        o = IK.to_obj(mb, n, col)
        o.data.name = n
        out[n] = IK.tris(o)
    for n in out:
        o = bpy.data.objects[n]
        o.location = (6100.0, 0.0, -50.0)
        o.hide_render = True
    return out, shelves


# --------------------------------------------------------------------------- arquitectura
def upper_floor(it, rng):
    g = "LEVEL_1"
    it.group(g)["hide_when"] = "jugador en la planta baja (corte isometrico: la galeria tapa la contaduria)"
    zs = SH
    rects = [(-W / 2, -D / 2, ARC_X1, GAL_Y), (ARC_X1, -D / 2, W / 2, STAIR_Y[1])]
    mb = K.MB()
    for x0, y0, x1, y1 in rects:
        mb.box((x0, y0, zs - 0.3), (x1, y1, zs - 0.14), IK.WOOD)
    it.unique(mb, "INT_Tesoreria_UpperSlab", g)
    for x0, y0, x1, y1 in rects:
        nx, ny = max(1, round((x1 - x0) / 2)), max(1, round((y1 - y0) / 2))
        for i in range(nx):
            for j in range(ny):
                mesh = "INT_Floor_Planks_B" if rng.random() < 0.2 else "INT_Floor_Planks"
                it.inst(mesh, M(x0 + i * (x1 - x0) / nx, y0 + j * (y1 - y0) / ny, zs, 0, (x1 - x0) / nx / 2,
                                (y1 - y0) / ny / 2), g)
    for k in range(12):                                     # vigas bajo el forjado, a lo largo de y
        x = -12.2 + 2.0 * k
        if x > ARC_X1 - 0.3:
            continue
        it.inst("INT_Beam_Straight", M(x, -D / 2, zs - 0.3, 90, (GAL_Y - 0.25 + D / 2) / 2), g)
    # balaustrada de la galeria (desde el despacho hasta el hueco de la escalera) y del hueco
    x0 = DESP_X
    L = ARC_X1 - x0
    m = round(L / 2)
    for k in range(m):
        it.inst("INT_Railing", M(x0 + k * L / m, GAL_Y - 0.14, zs, 0, L / m / 2), g)
    Ls = GAL_Y - STAIR_Y[1]
    it.inst("INT_Railing", M(ARC_X1 - 0.3, STAIR_Y[1], zs, 90, Ls / 2), g)
    it.colboxes += [((x0, -D / 2, zs - 0.3), (x1, y1, zs)) for (x0, _y0, x1, y1) in
                    ((-W / 2, 0, ARC_X1, GAL_Y), (ARC_X1, 0, W / 2, STAIR_Y[1]))]
    it.colboxes += [((x0, GAL_Y - 0.28, zs), (ARC_X1, GAL_Y, zs + 1.02)),
                    ((ARC_X1 - 0.44, STAIR_Y[1], zs), (ARC_X1 - 0.16, GAL_Y, zs + 1.02))]
    it.obstacles += [(1, x0, GAL_Y - 0.28, ARC_X1, GAL_Y), (1, ARC_X1 - 0.44, STAIR_Y[1], W / 2, GAL_Y)]
    # las dos regiones se solapan 1 m: con el margen del agente, dos rectangulos que solo se tocan quedan separados
    it.nav_regions += [(1, zs, -W / 2, -D / 2, ARC_X1, GAL_Y), (1, zs, ARC_X1 - 1.0, -D / 2, W / 2, STAIR_Y[1])]


def despacho(it):
    """Despacho del tesorero en el extremo -X de la galeria: tabique con puerta (x = -6.2) y frente sobre la arcada
    con ventana interior; los dos son muros cercanos -> WALL_Near_Despacho (dentro de LEVEL_1)."""
    g = "WALL_Near_Despacho"
    it.group(g).parent = it.group("LEVEL_1")
    it.group(g)["hide_when"] = "jugador dentro del despacho (o con LEVEL_1)"
    zs, h, t = SH, 3.2, 0.25
    mb = K.MB()
    # tabique (cara de la galeria a +X): hueco de puerta de 1.4 x 2.4
    mb.push(M(DESP_X, -D / 2, zs, 90))
    L = GAL_Y + D / 2
    u0, u1 = DESP_DOOR[0] + D / 2, DESP_DOOR[1] + D / 2
    mb.slab_holes([(0, 0), (L, 0), (L, h), (0, h)], [[(u0, 0), (u0, 2.4), (u1, 2.4), (u1, 0)]], 0.0, t, IK.STONE_L,
                  reveal_mat=IK.STONE)
    mb.box((u0 - 0.12, -0.05, 2.4), (u1 + 0.12, 0.0, 2.62), IK.WOOD, skip=("y+",))
    mb.pop()
    # frente sobre la arcada (cara a +Y), ventana interior de 1.2 x 1.2 con reja
    mb.push(M(-W / 2, GAL_Y - t, zs, 0))
    L2 = DESP_X - (-W / 2)
    wx0, wx1 = L2 / 2 - 0.6, L2 / 2 + 0.6
    mb.slab_holes([(0, 0), (L2, 0), (L2, h), (0, h)], [[(wx0, 1.0), (wx0, 2.2), (wx1, 2.2), (wx1, 1.0)]], 0.0, t,
                  IK.STONE_L, reveal_mat=IK.STONE)
    for k in range(1, 6):
        x = wx0 + 1.2 * k / 6
        mb.rod((x, t / 2, 1.0), (x, t / 2, 2.2), 0.012, IK.IRON)
    mb.box((wx0 - 0.08, t, 0.92), (wx1 + 0.08, t + 0.07, 1.0), IK.STONE, skip=("y-",))
    mb.pop()
    it.unique(mb, "INT_Tesoreria_DespachoWalls", g)
    # el tabique ocupa x en [DESP_X - t, DESP_X] (giro de 90: la y local va a -X)
    it.colboxes += [((DESP_X - t, -D / 2, zs), (DESP_X, DESP_DOOR[0], zs + h)),
                    ((DESP_X - t, DESP_DOOR[1], zs), (DESP_X, GAL_Y, zs + h)),
                    ((-W / 2, GAL_Y - t, zs), (DESP_X, GAL_Y, zs + h))]
    it.obstacles += [(1, DESP_X - t, -D / 2, DESP_X, DESP_DOOR[0]), (1, DESP_X - t, DESP_DOOR[1], DESP_X, GAL_Y),
                     (1, -W / 2, GAL_Y - t, DESP_X, GAL_Y)]


def arcade(it):
    """Arcada de 6 vanos (INT_Arch_3m) bajo el borde de la galeria; arcos hasta el forjado (4.1 m)."""
    for k in range(BAYS):
        it.inst("INT_Arch_3m", M(ARC_X0 + k * BAY_W, ARC_Y, 0, 0, BAY_W / 4.0, 1.0, (SH - 0.3) / IK.FH), "Shell")
        for xs in (ARC_X0 + k * BAY_W, ARC_X0 + (k + 1) * BAY_W - 0.5 * BAY_W / 4.0):
            it.colboxes.append(((xs, ARC_Y - 0.25, 0), (xs + 0.5 * BAY_W / 4.0, ARC_Y + 0.25, SH - 0.3)))
            it.obstacles.append((0, xs, ARC_Y - 0.25, xs + 0.5 * BAY_W / 4.0, ARC_Y + 0.25))
    return {"bays": BAYS, "bay_w": round(BAY_W, 3), "piers_x": [round(x, 2) for x in PIERS]}


def pipes(it):
    """4 tubos de luz por los pilares de la arcada, de la basa al techo (lo atraviesan 0.5 m)."""
    out = []
    for k, x in enumerate(PIPE_X):
        mb = K.MB()
        p_pipe(mb, H + 0.5)
        o = it.unique(mb, f"PIPE_Light_{k + 1:02d}", "Shell", M(x, PIPE_Y, 0.0), merge=False)
        o["pipe"] = "tubo de luz azul Tesoreria -> Faro (sube al tejado y sale por MARKER_PipeOutlet_TesoreriaMuralla_*)"
        it.colboxes.append(((x - 0.34, PIPE_Y - 0.3, 0), (x + 0.34, PIPE_Y + 0.3, H)))
        it.obstacles.append((0, x - 0.34, PIPE_Y - 0.3, x + 0.34, PIPE_Y + 0.3))
        out.append({"name": o.name, "x": round(x, 2), "y": round(PIPE_Y, 2), "tris": IK.tris(o)})
    return out


def stair(it):
    """Escalera de piedra de 2 m contra el muro +X: sube hacia -Y de y 2.4 (z 0) a y -4.2 (z 4.4) por el hueco del
    forjado; losa de 0.35 m bajo los peldanos (deja libre la ventana de la planta baja en y -3.6) y antepecho."""
    xa, xb = STAIR_X
    y0, y1 = STAIR_Y
    n = 22
    run, rise = y0 - y1, SH
    prof = []
    for i in range(n):
        ya = y0 - run * i / n
        prof += [(ya, rise * i / n), (ya, rise * (i + 1) / n)]
    prof += [(y1, rise), (y1, rise - 0.35), (y0 - 0.53, 0.0)]
    mb = K.MB()
    IK.prism(mb, prof, xa, xb, IK.STONE, axis="x")
    para = [(y0, 0.0), (y0, 1.0), (y1, rise + 1.0), (y1, rise - 0.35)]
    IK.prism(mb, para, xa - 0.25, xa, IK.STONE_L, axis="x")
    it.unique(mb, "INT_Tesoreria_Stair", "Shell")
    it.colprisms.append(([(y0, 0.0), (y1, rise), (y1, rise - 0.35), (y0 - 0.53, 0.0)], xa, xb, "x"))
    it.colboxes.append(((xa - 0.25, y1, 0), (xa, y0, rise + 1.0)))
    it.obstacles.append((0, xa - 0.25, y1, W / 2, y0))
    it.ramps.append((xa, xb, y1, y0, rise, 0.0))
    it.patches = getattr(it, "patches", []) + [(xa, xb, y0, y0 + 0.5, 0.0), (xa, xb, y1 - 0.5, y1, rise)]
    return {"width_m": round(xb - xa, 2), "run_m": round(run, 2), "rise_m": rise, "steps": n,
            "slope_deg": round(math.degrees(math.atan2(rise, run)), 1)}


def counters(it):
    """Dos mostradores contra el muro -X (tablero hacia +X = publico): modulo de ventanilla de cajero (1.2 m de luz)
    + modulo de reja de 1.6 m; murete de remate en el extremo -Y del segundo."""
    info = {}
    for k, y0 in ((1, C1_Y0), (2, C2_Y0)):
        it.inst("INT_Counter_Straight", M(COUNTER_X, y0, 0, 90), "Shell")
        it.inst("INT_Grille_Teller", M(COUNTER_X, y0, 1.1, 90), "Shell")
        it.inst("INT_Counter_Straight_B", M(COUNTER_X, y0 + 2.0, 0, 90, 0.8), "Shell")
        it.inst("INT_Grille", M(COUNTER_X, y0 + 2.0, 1.1, 90, 0.8), "Shell")
        y1 = y0 + 3.6
        it.colboxes.append(((COUNTER_X - 0.46, y0, 0), (COUNTER_X + 0.46, y1, 2.6)))
        it.obstacles.append((0, COUNTER_X - 0.46, y0, COUNTER_X + 0.46, y1))
        info[k] = {"y": [y0, y1], "ventanilla_y": [round(y0 + 0.4, 2), round(y0 + 1.6, 2)],
                   "npc": [round(c, 2) for c in NPC[k]]}
    return info


# --------------------------------------------------------------------------- mobiliario
def vitrinas(it, shelves, rng):
    out = []
    for i, (x, v, tipo) in enumerate(VITRINAS):
        o = it.inst(f"TES_Vitrina_{v}", M(x, VIT_Y, 0), "Furniture", name=f"TES_Vitrina_{i + 1:02d}_{tipo}")
        o["vitrina"] = tipo
        o["shard_type"] = tipo
        half = {"A": (0.8, 0.275), "B": (0.7, 0.35), "C": (0.38, 0.38)}[v]
        hgt = {"A": 2.1, "B": 1.12, "C": 1.62}[v]
        it.colboxes.append(((x - half[0], VIT_Y - half[1], 0), (x + half[0], VIT_Y + half[1], hgt)))
        it.obstacles.append((0, x - half[0], VIT_Y - half[1], x + half[0], VIT_Y + half[1]))
        n = 0
        for (z, (xa, xb), (ya, yb)) in shelves[v]:
            k = {"A": 5, "B": 12, "C": 7}[v]
            for j in range(k):
                px = x + xa + (xb - xa) * (j + 0.5) / k + rng.uniform(-0.03, 0.03)
                py = VIT_Y + rng.uniform(ya, yb)
                s = rng.uniform(0.7, 1.25) * (1.5 if v == "C" else 1.0)
                tilt = rng.uniform(-0.5, 0.5) if v != "A" else rng.uniform(-0.15, 0.15)
                mw = Matrix.Translation((px, py, z)) @ Matrix.Rotation(rng.uniform(0, math.pi), 4, "Z") @ \
                    Matrix.Rotation(tilt, 4, "X") @ Matrix.Diagonal((s, s, s, 1.0))
                sh = it.inst(f"TES_Shard_{tipo}", mw, "Furniture", name=f"TES_Shard_{tipo}_{i + 1:02d}_{n:02d}")
                sh["shard_type"] = tipo
                n += 1
        out.append({"vitrina": o.name, "variante": v, "tipo": tipo, "esquirlas": n, "x": round(x, 2)})
    return out


def furniture(it, rng):
    F, F1 = "Furniture", "Furniture_L1"
    it.group(F1).parent = it.group("LEVEL_1")
    zs = SH
    rows = []

    def put(mesh, mw, grp=F, obst=None, level=0, name=None):
        o = it.inst(mesh, mw, grp, name=name or f"PROP_{mesh}")
        if obst:
            lo, hi = obst
            it.colboxes.append((lo, hi))
            it.obstacles.append((level, lo[0], lo[1], hi[0], hi[1]))
        rows.append(mesh)
        return o
    # mostradores: balanza grande, libro, monedas, vela (mitad publica del tablero: x -11.2 .. -10.74)
    for k, y0 in ((1, C1_Y0), (2, C2_Y0)):
        put("TES_Scale_Large", M(COUNTER_X + 0.24, y0 + 2.8, 1.1, 90))
        put("BANK_Ledger_Open", M(COUNTER_X - 0.22, NPC[k][1] - 0.15, 1.1, 90))
        put("BANK_Coins", M(COUNTER_X + 0.25, y0 + 0.25, 1.1))
        put("BANK_Candle", M(COUNTER_X - 0.25, y0 + 3.4, 1.1))
    # contaduria bajo la galeria (muro del fondo -Y, entre las ventanas de x +-3 / +-9)
    for x in (-6.0, 0.0, 6.0):
        put("BANK_Shelf_Wall", M(x, -D / 2 + 0.21, 0, 0), obst=((x - 0.9, -D / 2, 0), (x + 0.9, -D / 2 + 0.42, 2.2)))
    put("BANK_Desk", M(-2.6, -4.3, 0, 0), obst=((-3.4, -4.7, 0), (-1.8, -3.9, 0.8)))
    put("BANK_Stool", M(-2.6, -5.0, 0), obst=((-2.8, -5.2, 0), (-2.4, -4.8, 0.67)))
    put("BANK_Ledger_Open", M(-2.4, -4.3, 0.79, -12))
    put("BANK_Candle", M(-3.1, -4.5, 0.79))
    for x, y in ((3.6, -5.6), (4.4, -5.6), (8.6, -5.7)):
        put("BANK_Strongbox", M(x, y, 0, 0), obst=((x - 0.36, y - 0.23, 0), (x + 0.36, y + 0.23, 0.45)))
    for x, y in ((3.2, -4.9), (3.55, -4.75), (9.2, -5.2), (-7.6, -5.9), (-7.3, -6.05)):
        put("TES_Coin_Sack", M(x, y, 0, rng.uniform(0, 360)))
    put("BANK_Strongbox", M(-8.3, -5.9, 0, 0), obst=((-8.66, -6.13, 0), (-7.94, -5.67, 0.45)))
    # vestibulo: banco de espera frente a los mostradores (de cara a -X), alfombra en el eje de la puerta
    for y in (1.2, 4.6):
        put("BANK_Bench", M(-6.4, y, 0, 90), obst=((-6.62, y - 1.0, 0), (-6.16, y + 1.0, 0.92)))
    put("BANK_Rug", M(0.0, 3.4, 0, 90, 1.2, 1.4))
    # lamparas: pilar sin tubo (x -9.17), muro -X (sobre el paso del personal), muros del fondo bajo la galeria
    put("BANK_Sconce", M(PIERS[0], ARC_Y + 0.25, 2.6, 0))
    put("BANK_Sconce", M(-W / 2, 2.5, 2.8, -90))
    for x in (-6.0, 6.0):
        put("BANK_Sconce", M(x, -D / 2, 2.5, 0))
    # coronas colgadas del techo (vestibulo)
    for x in (-4.0, 4.5):
        put("TES_Chandelier", M(x, 2.8, 6.3))
    # planta alta: despacho (caja fuerte contra el fondo, mesa de cara a la camara, estanteria contra -X)
    put("BANK_Rug", M(-9.8, -4.0, zs), grp=F1)
    put("TES_Safe", M(-8.0, -D / 2 + 0.45, zs, 0), grp=F1, obst=((-8.55, -D / 2, zs), (-7.45, -D / 2 + 0.9, zs + 1.7)), level=1)
    put("BANK_Desk", M(-10.6, -3.6, zs, 0), grp=F1, obst=((-11.4, -4.0, zs), (-9.8, -3.2, zs + 0.8)), level=1)
    put("BANK_Chair", M(-10.6, -4.4, zs, 0), grp=F1, obst=((-10.85, -4.65, zs), (-10.35, -4.15, zs + 1.0)), level=1)
    put("BANK_Ledger_Open", M(-10.4, -3.6, zs + 0.79, 10), grp=F1)
    put("BANK_Candle", M(-11.1, -3.4, zs + 0.79), grp=F1)
    put("TES_Coin_Sack", M(-9.95, -3.5, zs + 0.79, 30), grp=F1)
    put("BANK_Shelf_Wall", M(-W / 2 + 0.21, -5.6, zs, -90), grp=F1, obst=((-W / 2, -6.5, zs), (-W / 2 + 0.42, -4.7, zs + 2.2)), level=1)
    put("BANK_Sconce", M(-12.0, -D / 2, zs + 2.2, 0), grp=F1)
    # planta alta: archivo de la galeria (entre las ventanas de x 0, +-5, +-10) y dos bancos mirando al vestibulo
    for x in (-2.5, 2.5, 7.5):
        put("BANK_Shelf_Wall", M(x, -D / 2 + 0.21, zs, 0), grp=F1, obst=((x - 0.9, -D / 2, zs), (x + 0.9, -D / 2 + 0.42, zs + 2.2)), level=1)
    for x in (0.0, 5.0):
        put("BANK_Bench", M(x, -2.55, zs, 180), grp=F1, obst=((x - 1.0, -2.8, zs), (x + 1.0, -2.3, zs + 0.92)), level=1)
    for x in (-5.0, 5.0):
        put("BANK_Sconce", M(x - 2.5, -D / 2, zs + 2.2, 0), grp=F1)
    return rows


def lights(it):
    L = it.light
    flame, day, blue = "#FFA650", "#FFE6C4", "#8FD0FF"
    L("LIGHT_Lamp_Pier", (PIERS[0], ARC_Y + 0.6, 2.75), flame, 0.7, 6.0)
    L("LIGHT_Lamp_Staff", (-W / 2 + 0.4, 2.5, 2.95), flame, 0.6, 5.0)
    for i, x in enumerate((-6.0, 6.0)):
        L(f"LIGHT_Lamp_Back_{i + 1:02d}", (x, -D / 2 + 0.4, 2.65), flame, 0.6, 5.5)
    for i, x in enumerate((-4.0, 4.5)):
        L(f"LIGHT_Chandelier_{i + 1:02d}", (x, 2.8, 6.45), flame, 1.0, 9.0)
    for i, (k, y0) in enumerate(((1, C1_Y0), (2, C2_Y0))):
        L(f"LIGHT_Candle_{i + 1:02d}", (COUNTER_X - 0.25, y0 + 3.4, 1.35), flame, 0.35, 2.8)
    L("LIGHT_Candle_Contaduria", (-3.1, -4.5, 1.05), flame, 0.35, 2.8)
    L("LIGHT_Candle_Despacho", (-11.1, -3.4, SH + 1.05), flame, 0.35, 2.8)
    L("LIGHT_Lamp_Despacho", (-12.0, -D / 2 + 0.4, SH + 2.35), flame, 0.5, 4.5)
    for i, x in enumerate((-7.5, 2.5)):
        L(f"LIGHT_Lamp_Gallery_{i + 1:02d}", (x, -D / 2 + 0.4, SH + 2.35), flame, 0.5, 5.0)
    wins = [(-9.0, -D / 2 + 0.6, 2.1), (3.0, -D / 2 + 0.6, 2.1), (-W / 2 + 0.6, 1.4, 2.1), (W / 2 - 0.6, -3.6, 2.1),
            (-7.6, D / 2 - 0.6, 2.0), (7.6, D / 2 - 0.6, 2.0), (0.0, -D / 2 + 0.6, 6.7), (-10.0, -D / 2 + 0.6, 6.7),
            (-W / 2 + 0.6, 4.4, 6.7), (W / 2 - 0.6, 0.4, 6.7)]
    for i, p in enumerate(wins):
        L(f"LIGHT_Window_{i + 1:02d}", p, day, 0.45, 5.5, kind="omni_window")
    L("LIGHT_Pipes_Glow", (0.5 * (PIPE_X[1] + PIPE_X[2]), PIPE_Y + 0.8, 3.2), blue, 0.45, 8.0, kind="omni_magic")


def markers(it):
    it.entry_markers(inward_yaw_deg=180.0, exit_yaw_deg=0.0, spawn_dist=1.6)
    it.marker("MARKER_NPC_Slot_01", (NPC[1][0], NPC[1][1], 0.0), -90.0, npc="Tesorero",
              note="detras del mostrador 1 (Vender), mirando al publico (+X) y a la camara")
    it.marker("MARKER_NPC_Slot_02", (NPC[2][0], NPC[2][1], 0.0), -90.0, npc="Cambista",
              note="detras del mostrador 2 (Cambio): propuesta, el pedido solo nombra al Tesorero")
    it.marker("MARKER_Interact_Tesoreria_Vender", (COUNTER_X + 1.0, TELLER[1], 0.0), 90.0, tipo="tesoreria_vender",
              accion="vender esquirlas a precio fijo")
    it.marker("MARKER_Interact_Tesoreria_Cambio", (COUNTER_X + 1.0, TELLER[2], 0.0), 90.0, tipo="tesoreria_cambio",
              accion="cambiar plata por oro (1 de oro = 100 de plata)")


def ceiling(it):
    """Techo de vigas a 8.8 m (CEILING) con un paso que no cruce ningun tubo (>= 0.5 m entre ejes)."""
    best = None
    for m in range(9, 15):
        cs = [max(-W / 2 + 0.15, min(W / 2 - 0.15, -W / 2 + W * i / m)) for i in range(m + 1)]
        gap = min(abs(c - x) for c in cs for x in PIPE_X)
        if best is None or gap > best[0]:
            best = (gap, m)
    every = W / best[1]
    it.ceiling(span_axis="y", every=every)
    it.groups["CEILING"]["hide_when"] = "siempre dentro (los tubos lo atraviesan: su tramo de arriba sigue en Shell)"
    return {"beams": best[1] + 1, "spacing_m": round(every, 2), "min_gap_to_pipe_m": round(best[0], 2)}


def build(col, world_rot_deg, seed=2901):
    rng = random.Random(seed)
    it = IK.Interior("Tesoreria", (W, D, H), "piedra", seed, world_rot_deg, DOOR, col)
    it.shell(openings=openings(), storeys=2, ceiling=False)
    info_ceiling = ceiling(it)
    it.nav_regions.append((0, 0.0, -W / 2, -D / 2, W / 2, D / 2))
    info = {"storey_m": SH, "ceiling": info_ceiling}
    upper_floor(it, rng)
    despacho(it)
    info["arcade"] = arcade(it)
    info["pipes"] = pipes(it)
    info["stair"] = stair(it)
    info["counters"] = counters(it)
    shelves = {v: p for v, p in it_shelves.items()}
    info["vitrinas"] = vitrinas(it, shelves, rng)
    info["furniture"] = furniture(it, rng)
    lights(it)
    markers(it)
    return it, info


it_shelves = {}


def build_all_props(col):
    """Props propios (balanza, caja fuerte, vitrinas, esquirlas, corona) + materiales de esquirla."""
    mats = shard_materials()
    out, shelves = build_props(col)
    it_shelves.update(shelves)
    for drop_name, drop in (("TES_Chandelier", 2.5),):
        if bpy.data.meshes.get(drop_name) is None:
            mb = K.MB()
            p_chandelier(mb, drop)
            o = IK.to_obj(mb, drop_name, col)
            o.data.name = drop_name
            o.location = (6100.0, 0.0, -50.0)
            o.hide_render = True
            out[drop_name] = IK.tris(o)
    return out, mats
