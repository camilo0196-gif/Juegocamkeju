"""
CONCORDIA - Etapa 29: interior del Santuario del Retorno (int_santuario.glb). Todo hecho a mano (regla del usuario:
el Santuario no usa assets descargados ni IA). Funcion: punto de reaparicion tras morir; sereno y legible.

Referencia: interior de la Sainte-Chapelle (nave alta y estrecha, vitrales azules muy altos, columnas esbeltas,
techo azul con estrellas). Se copia la verticalidad, los vitrales y la luz azul filtrada.

Marco centrado del Santuario_InteriorVolume: x en [-6.9, 6.9], y en [-4.8, 4.8], muros de 9.0 m; +Y = fachada de la
plaza (puerta en x = 0). Giro del edificio -135: CAM_Iso mira a lo largo de -Y, asi que el unico muro cercano es la
fachada (+Y); el muro -Y con sus 5 ventanales queda de cara a la camara.
  - Muros con los huecos del exterior (SANTUARIO_Body): 5 ventanales de 1.4 x 6.0 m por el lado -Y y 4 + una ventana
    alta sobre la puerta en +Y; 2 ventanas y el oculo de 3 m en cada hastial. Vitral MAT_Stained_Glass_Blue
    (emision 0.6) con traceria de piedra (parteluz, dos luces y un circulo en la cabeza).
  - Contrafuertes interiores entre ventanales (pilar y tres columnillas hasta el arranque, 9.0 m).
  - Boveda de crucería simple sobre los 9 m, en CEILING (oculto en CAM_Iso), por debajo de la cubierta exterior: la
    clave se busca contra la malla de SANTUARIO_Roof (rayos hacia arriba) con 0.12 m de holgura.
  - Pozo (SANTUARIO_Well del master, sin 'provisional'), agua oscura MAT_Water, un solo farol de esquirla encima.
  - Cuidador (MARKER_NPC_Slot_01) junto al pozo, mesa con 3 raciones y 3 antorchas, 8 bancos de madera.
  - MARKER_Respawn delante del pozo, visible desde CAM_Iso.
"""

import math
import os
import random

import bpy
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

import bld_kit as K
import interior_kit as IK
import stage27_banco as SB

W, D, H = 13.8, 9.6, 9.0
DOOR = (0.0, D / 2)
T = 0.4
WIN_X = (-5.86, -3.0, 0.0, 3.0, 5.86)           # ventanales de los muros largos (centros, exterior)
WIN_W, WIN_Z0, WIN_Z1 = 1.4, 2.3, 8.3
DOOR_WIN = (0.0, 1.1, 7.4, 8.5)                 # ventana alta sobre la puerta: x, ancho, z0, z1
END_WIN_Y = (-1.8, 1.8)                         # ventanas de los hastiales: ancho 1.0, z 3.0-7.6
END_W, END_Z0, END_Z1 = 1.0, 3.0, 7.6
OCULUS = (11.0, 1.5)                            # centro z y radio del oculo del hastial (exterior: 3 x 3 m)
PIER_X = (-6.9, -4.43, -1.5, 1.5, 4.43, 6.9)    # contrafuertes interiores (bordes de los tramos de boveda)
PIER_D = 0.45
CLEAR = 0.12                                    # holgura minima boveda - cubierta
WELL_R = 1.06
NPC = (1.55, -0.35)                             # Cuidador junto al pozo, de cara a la camara (+Y)
TABLE = (2.65, -0.75)
RESPAWN = (0.0, 2.05)
BENCHES = [(sx * x, sy * 2.65) for sx in (-1, 1) for x in (3.3, 5.3) for sy in (-1, 1)]
STARS = "MAT_Vault_Stars"
GLASS = "MAT_Stained_Glass_Blue"
SPRING = H


def M(x, y, z=0.0, yaw=0.0, sx=1.0, sy=1.0, sz=1.0):
    return SB.M(x, y, z, yaw, sx, sy, sz)


# --------------------------------------------------------------------------- boveda contra la cubierta
def roof_underside(roof_obj, xs, ys):
    """z de la cara inferior de la cubierta (primer impacto hacia arriba desde z = 8.9) en una rejilla; None si no
    hay cubierta encima."""
    me = roof_obj.data
    bvh = BVHTree.FromPolygons([v.co.copy() for v in me.vertices], [list(p.vertices) for p in me.polygons], epsilon=0.0)
    out = {}
    for x in xs:
        for y in ys:
            loc, _n, _i, _d = bvh.ray_cast(Vector((x, y, SPRING - 0.1)), Vector((0, 0, 1)), 30.0)
            out[(round(x, 3), round(y, 3))] = loc.z if loc else None
    return out


def profile(h, sag_ratio=0.06):
    """Perfil apuntado de la boveda en (y, z): dos arcos de la imposta (+-D/2, 9.0) a la clave (0, 9 + h) con flecha
    sag_ratio * cuerda (curvos hacia arriba); devuelve z(y)."""
    a = D / 2
    L = math.hypot(a, h)
    s = sag_ratio * L
    R = (L * L / 4 + s * s) / (2 * s)
    # arco derecho: cuerda de (a, 0) a (0, h); centro a distancia R - s de su punto medio, hacia dentro (abajo)
    mx, mz = a / 2, h / 2
    ux, uz = -a / L, h / L                                   # direccion de la cuerda
    nx, nz = -uz, ux                                         # normal; hacia arriba-fuera si nz > 0
    if nz < 0:
        nx, nz = -nx, -nz
    cx, cz = mx - nx * (R - s), mz - nz * (R - s)

    def z(y):
        yy = abs(y)
        dz = R * R - (yy - cx) ** 2
        return SPRING + cz + math.sqrt(max(dz, 0.0))
    return z


def fit_vault(roof_obj, h_max=5.0):
    """Clave mas alta (<= 14 m) con la boveda (y sus nervios) por debajo de la cara inferior de la cubierta menos
    CLEAR en todos los puntos; tambien comprueba la boveda pedida (clave 14 m, arranque vertical)."""
    # rejilla de 0.1 m: los cabios de madera de la cubierta (MAT_Wood_Dark) quedan entre muestras de 0.4 m
    xs = [round(-W / 2 + 0.005 + 0.1 * i, 3) for i in range(int(W / 0.1))] + [W / 2 - 0.005]
    ys = sorted(set([round(-4.79 + 0.05 * i, 3) for i in range(192)] + [round(-D / 2 + D * i / 24, 3) for i in range(1, 24)]))
    under = roof_underside(roof_obj, xs, ys)
    lim = {}
    for (x, y), z in under.items():
        if z is not None:
            lim[y] = min(lim.get(y, 99.0), z)
    res = {"cubierta_muestras": len(under), "cubierta_sin_impacto": sum(1 for z in under.values() if z is None)}
    # boveda pedida: apuntada de clave 14 m con arranque vertical (dos arcos con el centro en la imposta)
    a, h = D / 2, 5.0
    yc = (a * a - h * h) / (2 * a)
    R = a - yc
    worst = min(lim[y] - (SPRING + math.sqrt(max(R * R - (abs(y) - yc) ** 2, 0.0))) for y in lim)
    res["boveda_14m_arranque_vertical"] = {"holgura_min_m": round(worst, 3), "choca": worst < CLEAR}
    best = None
    hh = h_max
    while hh > 1.0:
        zf = profile(hh)
        gap = min(lim[y] - zf(y) for y in lim)
        if gap >= CLEAR:
            best = (hh, gap)
            break
        hh -= 0.05
    if best is None:
        raise RuntimeError("la boveda no cabe bajo la cubierta")
    res["clave_m"] = round(SPRING + best[0], 2)
    res["holgura_min_m"] = round(best[1], 3)
    res["perfil"] = "dos arcos apuntados de flecha 0.06 x cuerda (la cubierta es a dos aguas de 45 grados)"
    return best[0], res, lim


# --------------------------------------------------------------------------- materiales
def vault_material(repo):
    """Plementeria azul oscura con estrellas de bronce palido (no emisiva; saturacion <= 0.35 salvo el tono 214)."""
    from PIL import Image, ImageDraw
    path = os.path.join(repo, "textures", "concordia", STARS, "vault_stars_1k.png")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    rng = random.Random(2902)
    img = Image.new("RGB", (1024, 1024), (46, 64, 87))                 # #2E4057 (h 214, s 0.47, v 0.34)
    d = ImageDraw.Draw(img)
    for _ in range(9000):                                               # grano de pintura
        x, y = rng.randrange(1024), rng.randrange(1024)
        c = rng.randint(-7, 7)
        d.point((x, y), fill=(46 + c, 64 + c, 87 + c))
    for _ in range(7):                                                  # estrellas de 8 puntas (1 m = textura)
        cx, cy, r = rng.randrange(60, 964), rng.randrange(60, 964), rng.uniform(16, 26)
        pts = []
        for k in range(16):
            rr = r if k % 2 == 0 else r * 0.38
            a = math.pi * k / 8
            pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
        d.polygon(pts, fill=(201, 185, 138))                            # #C9B98A (s 0.31)
    img.save(path)
    m = bpy.data.materials.get(STARS) or bpy.data.materials.new(STARS)
    m.use_nodes = True
    N = m.node_tree.nodes
    b = N["Principled BSDF"]
    tex = N.new("ShaderNodeTexImage")
    tex.image = bpy.data.images.load(path)
    m.node_tree.links.new(tex.outputs["Color"], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = 0.85
    m["note"] = "boveda del Santuario: azul oscuro con estrellas de bronce palido (Sainte-Chapelle), 1K, sin emision"
    return os.path.relpath(path, repo)


# --------------------------------------------------------------------------- props a mano (+Y = frente)
def p_table(mb):
    mb.box((-0.45, -0.3, 0.74), (0.45, 0.3, 0.79), IK.WOOD)
    for x in (-0.4, 0.4):
        for y in (-0.25, 0.25):
            mb.box((x - 0.03, y - 0.03, 0), (x + 0.03, y + 0.03, 0.74), IK.WOOD, skip=("z-", "z+"))
    mb.box((-0.4, -0.26, 0.6), (0.4, -0.24, 0.66), IK.WOOD)


def p_ration(mb):
    """Racion: hogaza y cuna de queso sobre un pano (0.3 x 0.22 m)."""
    mb.face([(-0.16, -0.12, 0.004), (0.16, -0.12, 0.004), (0.16, 0.12, 0.004), (-0.16, 0.12, 0.004)], IK.CLOTH[1],
            nrm=(0, 0, 1))
    rs = [(0.07, 0.0), (0.09, 0.03), (0.08, 0.07), (0.04, 0.095)]
    rings = [[(-0.04 + r * math.cos(2 * math.pi * i / 8), r * 0.75 * math.sin(2 * math.pi * i / 8), z) for i in range(8)]
             for r, z in rs]
    for a, b in zip(rings, rings[1:]):
        for i in range(8):
            j = (i + 1) % 8
            mb.face([a[i], a[j], b[j], b[i]], "MAT_Straw")
    mb.ngon_fill(rings[-1], "MAT_Straw")
    mb.face([(0.06, -0.06, 0.004), (0.14, -0.02, 0.004), (0.14, -0.02, 0.05), (0.06, -0.06, 0.05)], IK.STONE_L, nrm=(0.4, -1, 0))
    mb.face([(0.06, -0.06, 0.05), (0.14, -0.02, 0.05), (0.07, 0.04, 0.05)], IK.STONE_L, nrm=(0, 0, 1))
    mb.face([(0.14, -0.02, 0.004), (0.07, 0.04, 0.004), (0.07, 0.04, 0.05), (0.14, -0.02, 0.05)], IK.STONE_L, nrm=(1, 0.8, 0))


def p_torch(mb):
    """Antorcha apagada tumbada (0.55 m): mango de madera, cabeza envuelta en trapo y pez."""
    mb.rod((-0.27, 0, 0.022), (0.17, 0, 0.022), 0.02, IK.WOOD, caps=True)
    mb.rod((0.12, 0, 0.032), (0.28, 0, 0.032), 0.032, IK.CLOTH[2], caps=True)
    mb.rod((0.2, 0, 0.034), (0.27, 0, 0.034), 0.034, IK.ASH, caps=True)


def p_candelabrum(mb):
    """Candelero de pie de hierro (1.5 m) con tres velas (cara +Y)."""
    mb.cylinder(0.18, 0.0, 0.04, 8, IK.IRON, r1=0.12)
    mb.cylinder(0.022, 0.04, 1.3, 6, IK.IRON, caps=False)
    mb.rod((-0.22, 0, 1.3), (0.22, 0, 1.3), 0.015, IK.IRON)
    for x in (-0.22, 0.0, 0.22):
        mb.cylinder(0.045, 1.3, 1.33, 6, IK.IRON, center=(x, 0))
        mb.cylinder(0.02, 1.33, 1.5, 6, IK.STONE_L, center=(x, 0), caps=False)
        for a in (0.0, math.pi / 2):
            c, s = math.cos(a) * 0.018, math.sin(a) * 0.018
            mb.face([(x - c, -s, 1.5), (x + c, s, 1.5), (x, 0, 1.57)], IK.WARM, nrm=(-s, c, 0))


PROPS = {"SAN_Table": p_table, "SAN_Ration": p_ration, "SAN_Torch": p_torch, "SAN_Candelabrum": p_candelabrum}


def build_props(col):
    out = {}
    for n, fn in PROPS.items():
        if bpy.data.meshes.get(n) is not None:
            continue
        mb = K.MB()
        fn(mb)
        o = IK.to_obj(mb, n, col)
        o.data.name = n
        o.location = (6300.0, 0.0, -50.0)
        o.hide_render = True
        out[n] = IK.tris(o)
    return out


# --------------------------------------------------------------------------- muros
def lancet(x0, x1, z0, z1):
    """Hueco de ventanal: rectangulo con cabeza apuntada (dos arcos de radio = ancho)."""
    w = x1 - x0
    zs = z1 - w * 0.866                     # arranque del arco apuntado equilatero
    pts = [(x0, z0), (x1, z0), (x1, zs)]
    n = 6
    for i in range(1, n + 1):                # arco derecho: centro en (x0, zs)
        a = math.radians(60.0 * i / n)
        pts.append((x0 + w * math.cos(a), zs + w * math.sin(a)))
    for i in range(1, n):                    # arco izquierdo: centro en (x1, zs)
        a = math.radians(120.0 + 60.0 * i / n)
        pts.append((x1 + w * math.cos(a), zs + w * math.sin(a)))
    pts.append((x0, zs))
    return pts, zs


def tracery(mb, x0, x1, z0, z1, depth):
    """Vitral a media profundidad del muro con parteluz, dos luces apuntadas, circulo en la cabeza y plomos."""
    w = x1 - x0
    hole, zs = lancet(x0, x1, z0, z1)
    yv = -depth / 2
    # vitral (una cara hacia la sala): poligono del hueco
    mb.push(Matrix.Translation((0, 0, 0)))
    vs = [(x, yv, z) for x, z in hole]
    mb.ngon_fill(vs, GLASS, flip=True)
    mb.pop()
    xm = (x0 + x1) / 2
    mb.box((xm - 0.05, yv - 0.06, z0), (xm + 0.05, yv + 0.06, zs + 0.15), IK.STONE)         # parteluz
    for xa, xb in ((x0, xm - 0.05), (xm + 0.05, x1)):                                      # arcos de las dos luces
        c = (xa + xb) / 2
        r = (xb - xa) / 2
        pts = [(c + r * math.cos(math.pi * i / 6), zs - 0.35 + r * math.sin(math.pi * i / 6)) for i in range(7)]
        for p, q in zip(pts, pts[1:]):
            mb.rod((p[0], yv, p[1]), (q[0], yv, q[1]), 0.035, IK.STONE)
    cz, cr = zs + w * 0.3, w * 0.2                                                          # circulo de la cabeza
    ring = [(xm + cr * math.cos(2 * math.pi * i / 10), cz + cr * math.sin(2 * math.pi * i / 10)) for i in range(10)]
    for i in range(10):
        p, q = ring[i], ring[(i + 1) % 10]
        mb.rod((p[0], yv, p[1]), (q[0], yv, q[1]), 0.03, IK.STONE)
    z = z0 + 0.6
    while z < zs - 0.4:                                                                      # plomos
        mb.rod((x0, yv + 0.02, z), (x1, yv + 0.02, z), 0.008, IK.IRON)
        z += 0.6


def long_wall(it, side):
    """Muro largo (+Y o -Y) con sus ventanales (y la puerta en +Y), zocalo-banco y imposta; los contrafuertes."""
    sgn = 1 if side == "+Y" else -1
    grp = "WALL_Near_A" if side == "+Y" else "Shell"
    mb = K.MB()
    # marco del muro: x a lo largo, y local 0 = cara de la sala, hacia -y local = fuera
    if sgn > 0:
        mb.push(Matrix.Translation((W / 2, D / 2, 0)) @ Matrix.Rotation(math.pi, 4, "Z"))
    else:
        mb.push(Matrix.Translation((-W / 2, -D / 2, 0)))
    holes = []
    wins = []
    for x in WIN_X:
        if sgn > 0 and x == 0.0:
            continue
        u = (x + W / 2) if sgn < 0 else (W / 2 - x)
        x0, x1 = u - WIN_W / 2, u + WIN_W / 2
        holes.append(lancet(x0, x1, WIN_Z0, WIN_Z1)[0])
        wins.append((x0, x1, WIN_Z0, WIN_Z1))
    if sgn > 0:
        u = W / 2 - DOOR[0]
        holes.append([(u - 0.8, 0.0), (u + 0.8, 0.0), (u + 0.8, 3.2), (u, 3.75), (u - 0.8, 3.2)])
        dx, dw, dz0, dz1 = DOOR_WIN
        holes.append(lancet(u - dw / 2, u + dw / 2, dz0, dz1)[0])
        wins.append((u - dw / 2, u + dw / 2, dz0, dz1))
    mb.slab_holes([(0, 0), (W, 0), (W, H), (0, H)], holes, -T, 0.0, IK.STONE_L, reveal_mat=IK.STONE)
    for (x0, x1, z0, z1) in wins:
        tracery(mb, x0, x1, z0, z1, T)
        mb.box((x0 - 0.1, 0.0, z0 - 0.12), (x1 + 0.1, 0.1, z0), IK.STONE, skip=("y-",))      # alfeizar
    # zocalo-banco de piedra (0.45 m) y imposta bajo los ventanales (2.1 m), fuera de los huecos de la puerta
    spans = [(0.0, W)]
    if sgn > 0:
        u = W / 2 - DOOR[0]
        spans = [(0.0, u - 0.8), (u + 0.8, W)]
    for a, b in spans:
        mb.box((a, 0.0, 0.0), (b, 0.38, 0.45), IK.STONE, skip=("y-", "z-"))
        mb.box((a, 0.0, 2.0), (b, 0.08, 2.12), IK.STONE, skip=("y-",))
    if sgn > 0:                                                                               # puerta: hoja y jambas
        u = W / 2 - DOOR[0]
        mb.box((u - 0.78, -T + 0.12, 0.0), (u + 0.78, -T + 0.18, 3.2), IK.WOOD, skip=("z-",))
        for z in (0.4, 1.6, 2.8):
            mb.box((u - 0.74, -T + 0.18, z), (u + 0.74, -T + 0.2, z + 0.1), IK.IRON, skip=("y-",))
    mb.pop()
    it.unique(mb, f"INT_Santuario_Wall{side}", grp)
    # contrafuertes interiores (pilar + 3 columnillas + capitel) en este muro
    mb = K.MB()
    yw = sgn * D / 2
    for x in PIER_X:
        xa, xb = max(-W / 2, x - 0.32), min(W / 2, x + 0.32)
        y0, y1 = (yw - sgn * PIER_D, yw) if sgn > 0 else (yw, yw - sgn * PIER_D)
        mb.box((xa, min(y0, y1), 0.0), (xb, max(y0, y1), SPRING - 0.25), IK.STONE_L, skip=("z-",))
        yf = yw - sgn * (PIER_D + 0.06)
        for dx in (-0.16, 0.0, 0.16):
            xc = min(max(x + dx, -W / 2 + 0.07), W / 2 - 0.07)
            mb.rod((xc, yf, 0.45), (xc, yf, SPRING - 0.25), 0.055, IK.STONE)
        mb.box((xa - 0.04, min(y0, y1) - 0.1, SPRING - 0.25), (xb + 0.04, max(y0, y1) + 0.1, SPRING), IK.STONE)
        it.colboxes.append(((xa, min(y0, y1), 0), (xb, max(y0, y1), SPRING)))
        it.obstacles.append((0, xa, min(y0, y1) - 0.06, xb, max(y0, y1) + 0.06))
    it.unique(mb, f"INT_Santuario_Piers{side}", grp)
    # colision del muro (sin hueco de puerta en -Y)
    if sgn > 0:
        u0, u1 = DOOR[0] - 0.8, DOOR[0] + 0.8
        it.colboxes += [((-W / 2, D / 2, 0), (u0, D / 2 + T, H)), ((u1, D / 2, 0), (W / 2, D / 2 + T, H)),
                        ((u0, D / 2, 3.2), (u1, D / 2 + T, H))]
    else:
        it.colboxes.append(((-W / 2, -D / 2 - T, 0), (W / 2, -D / 2, H)))
    if sgn > 0:                                    # zocalo-banco: sin obstaculo en el hueco de la puerta
        it.obstacles += [(0, -W / 2, yw - 0.42, DOOR[0] - 0.8, yw), (0, DOOR[0] + 0.8, yw - 0.42, W / 2, yw)]
    else:
        it.obstacles.append((0, -W / 2, yw, W / 2, yw + 0.42))
    return len(wins)


def end_wall(it, side):
    """Hastial (-X o +X) hasta la imposta: dos ventanas apuntadas de 1.0 x 4.6 m como el exterior."""
    sgn = 1 if side == "+X" else -1
    mb = K.MB()
    if sgn > 0:
        mb.push(Matrix.Translation((W / 2, -D / 2, 0)) @ Matrix.Rotation(math.pi / 2, 4, "Z"))
    else:
        mb.push(Matrix.Translation((-W / 2, D / 2, 0)) @ Matrix.Rotation(-math.pi / 2, 4, "Z"))
    holes, wins = [], []
    for y in END_WIN_Y:
        u = (y + D / 2) if sgn > 0 else (D / 2 - y)
        x0, x1 = u - END_W / 2, u + END_W / 2
        holes.append(lancet(x0, x1, END_Z0, END_Z1)[0])
        wins.append((x0, x1, END_Z0, END_Z1))
    mb.slab_holes([(0, 0), (D, 0), (D, H), (0, H)], holes, -T, 0.0, IK.STONE_L, reveal_mat=IK.STONE)
    for (x0, x1, z0, z1) in wins:
        tracery(mb, x0, x1, z0, z1, T)
    mb.box((0.0, 0.0, 0.0), (D, 0.38, 0.45), IK.STONE, skip=("y-", "z-"))
    mb.box((0.0, 0.0, 2.0), (D, 0.08, 2.12), IK.STONE, skip=("y-",))
    mb.pop()
    it.unique(mb, f"INT_Santuario_Wall{side}", "Shell")
    x = sgn * W / 2
    it.colboxes.append(((min(x, x + sgn * T), -D / 2, 0), (max(x, x + sgn * T), D / 2, H)))
    it.obstacles.append((0, x - 0.42 if sgn > 0 else x, -D / 2, x if sgn > 0 else x + 0.42, D / 2))


# --------------------------------------------------------------------------- boveda (CEILING)
def vault(it, h, zf):
    """Plementeria (cañon apuntado a lo largo de x), nervios fajones en los contrafuertes, diagonales por tramo y
    espinazo; timpanos de los hastiales con el oculo. Todo por encima de 9.0 m -> CEILING."""
    g = "CEILING"
    ny = 24
    ys = [-D / 2 + D * i / ny for i in range(ny + 1)]
    mb = K.MB()
    for xa, xb in zip(PIER_X, PIER_X[1:]):
        for ya, yb in zip(ys, ys[1:]):
            mb.face([(xa, ya, zf(ya)), (xb, ya, zf(ya)), (xb, yb, zf(yb)), (xa, yb, zf(yb))], STARS, nrm=(0, 0, -1))
    it.unique(mb, "INT_Santuario_VaultWebs", g)
    mb = K.MB()
    r = 0.09
    for x in PIER_X:                                                        # fajones
        xc = min(max(x, -W / 2 + 0.12), W / 2 - 0.12)
        pts = [(xc, y, zf(y) - r * 1.45 - 0.01) for y in ys]          # seccion girada: la esquina no asoma
        for p, q in zip(pts, pts[1:]):
            mb.rod(p, q, r, IK.STONE_L)
    for xa, xb in zip(PIER_X, PIER_X[1:]):                                  # diagonales
        for s in (1, -1):
            n = 16
            pts = []
            for i in range(n + 1):
                t = i / n
                x = xa + (xb - xa) * t
                y = s * (-D / 2 + D * t)
                pts.append((x, y, zf(y) - r * 0.8 * 1.45 - 0.01))
            for p, q in zip(pts, pts[1:]):
                mb.rod(p, q, r * 0.8, IK.STONE_L)
        mb.cylinder(0.16, zf(0.0) - 0.22, zf(0.0) - 0.02, 8, IK.BRONZE, center=((xa + xb) / 2, 0.0))   # clave
    mb.rod((-W / 2 + 0.1, 0.0, zf(0.0) - 0.07), (W / 2 - 0.1, 0.0, zf(0.0) - 0.07), 0.06, IK.STONE_L)  # espinazo
    it.unique(mb, "INT_Santuario_VaultRibs", g)
    # timpanos: muro bajo el perfil de la boveda en x = +-W/2, con el oculo
    oz, orad = OCULUS
    while orad > 0.6 and oz + orad + 0.25 > zf(orad * 0.7):
        orad -= 0.05
    for sgn in (1, -1):
        mb = K.MB()
        prof = [(u, zf(u - D / 2)) for u in [D * i / ny for i in range(ny + 1)]]
        poly = [(0.0, SPRING)] + [(u, z) for u, z in prof[1:-1]] + [(D, SPRING)]
        ring = [(D / 2 + orad * math.cos(2 * math.pi * i / 16), oz + orad * math.sin(2 * math.pi * i / 16)) for i in range(16)]
        if sgn > 0:
            mb.push(Matrix.Translation((W / 2, -D / 2, 0)) @ Matrix.Rotation(math.pi / 2, 4, "Z"))
        else:
            mb.push(Matrix.Translation((-W / 2, D / 2, 0)) @ Matrix.Rotation(-math.pi / 2, 4, "Z"))
        mb.slab_holes(poly, [ring], -T, 0.0, IK.STONE_L, reveal_mat=IK.STONE)
        vs = [(x, -T / 2, z) for x, z in ring]
        mb.ngon_fill(vs, GLASS, flip=True)
        for i in range(8):                                                # radios de la rosa
            a = 2 * math.pi * i / 8
            mb.rod((D / 2, -T / 2, oz), (D / 2 + orad * math.cos(a), -T / 2, oz + orad * math.sin(a)), 0.03, IK.STONE)
        mb.pop()
        it.unique(mb, f"INT_Santuario_Tympanum{'+X' if sgn > 0 else '-X'}", g)
    it.groups[g]["hide_when"] = "siempre dentro (todo lo que esta por encima de la imposta de 9.0 m)"
    return {"oculo_radio_m": round(orad, 2)}


# --------------------------------------------------------------------------- pozo, mobiliario, luces, marcadores
def well(it):
    """SANTUARIO_Well del master (malla tal cual, sin la propiedad provisional) y farol de esquirla colgado encima."""
    src = bpy.data.objects.get("SRC_SANTUARIO_Well")
    if src is None:
        raise RuntimeError("falta SANTUARIO_Well del master")
    o = bpy.data.objects.new("SANTUARIO_Well", src.data)
    it.col.objects.link(o)
    o.parent = it.group("Furniture")
    o.matrix_parent_inverse = Matrix.Identity(4)
    o.matrix_basis = Matrix.Identity(4)
    o["merge"] = False
    o["note"] = "pozo del Santuario (etapa 26), colocado en el interior (etapa 29); ya no es provisional"
    vs = [v.co for v in src.data.vertices]
    top = max(v.z for v in vs)
    mb = K.MB()
    K.lantern_shard(mb)
    lan = it.unique(mb, "SANTUARIO_ShardLantern", "Furniture", M(0.0, -0.5, top + 0.55), merge=False)
    lan["note"] = "unico farol de esquirla (#8FD0FF) de la sala, colgado sobre el pozo"
    mb = K.MB()
    mb.rod((0.0, -0.5, top + 0.55), (0.0, -0.5, top), 0.012, IK.IRON)
    mb.rod((0.0, -0.5, top), (0.0, 0.0, top), 0.012, IK.IRON)
    it.unique(mb, "SANTUARIO_LanternHook", "Furniture", merge=False)
    it.colboxes.append(((-WELL_R, -WELL_R, 0), (WELL_R, WELL_R, 1.0)))
    it.obstacles.append((0, -WELL_R, -WELL_R, WELL_R, WELL_R))
    return {"well_top_m": round(top, 2), "well_mats": [m.name for m in src.data.materials], "tris": IK.tris(o)}


def furniture(it):
    rows = []

    def put(mesh, mw, obst=None, name=None):
        o = it.inst(mesh, mw, "Furniture", name=name or f"PROP_{mesh}")
        if obst:
            lo, hi = obst
            it.colboxes.append((lo, hi))
            it.obstacles.append((0, lo[0], lo[1], hi[0], hi[1]))
        rows.append(mesh)
        return o
    for x, y in BENCHES:                         # bancos a lo largo de y, de cara al pasillo central
        yaw = 90.0 if x > 0 else -90.0
        put("BANK_Bench", M(x, y, 0, yaw), obst=((x - 0.26, y - 1.0, 0), (x + 0.26, y + 1.0, 0.92)))
    tx, ty = TABLE
    put("SAN_Table", M(tx, ty, 0, 0), obst=((tx - 0.45, ty - 0.3, 0), (tx + 0.45, ty + 0.3, 0.8)))
    for i, dx in enumerate((-0.28, 0.0, 0.28)):
        put("SAN_Ration", M(tx + dx, ty + 0.08, 0.79, 8 * i), name=f"SAN_Ration_{i + 1:02d}")
    for i, dy in enumerate((-0.2, -0.13, -0.06)):
        put("SAN_Torch", M(tx + 0.05 * i, ty + dy, 0.79, 4 - 3 * i), name=f"SAN_Torch_{i + 1:02d}")
    for x in (-5.8, 5.8):                        # candeleros contra el muro del fondo
        put("SAN_Candelabrum", M(x, -D / 2 + 0.7, 0.0), obst=((x - 0.25, -D / 2 + 0.45, 0), (x + 0.25, -D / 2 + 0.95, 1.6)))
    return rows


def lights(it, top):
    L = it.light
    for i, x in enumerate((-5.8, 5.8)):
        L(f"LIGHT_Candelabrum_{i + 1:02d}", (x, -D / 2 + 0.7, 1.6), "#FFA650", 0.45, 4.0)
    cool = "#DCE4EC"                              # luz de dia filtrada (fria, sin ser azul magico)
    for i, x in enumerate(WIN_X):
        L(f"LIGHT_Window_S_{i + 1:02d}", (x, -D / 2 + 0.8, 5.5), cool, 0.4, 6.5, kind="omni_window")
    for i, x in enumerate((-5.86, 5.86)):
        L(f"LIGHT_Window_N_{i + 1:02d}", (x, D / 2 - 0.8, 5.5), cool, 0.35, 6.0, kind="omni_window")
    L("LIGHT_Shard_Well", (0.0, 0.0, top + 0.3), "#8FD0FF", 0.5, 5.0, kind="omni_magic")


def markers(it):
    it.entry_markers(inward_yaw_deg=180.0, exit_yaw_deg=0.0, spawn_dist=1.4)
    it.marker("MARKER_Respawn", (RESPAWN[0], RESPAWN[1], 0.0), 0.0, tipo="respawn",
              note="reaparicion tras morir: delante del pozo, mirando a la salida (+Y) y a la camara")
    it.marker("MARKER_NPC_Slot_01", (NPC[0], NPC[1], 0.0), 0.0, npc="Cuidador",
              note="junto al pozo, de cara a la reaparicion y a la camara")
    it.marker("MARKER_Interact_Santuario_Kit", (TABLE[0], TABLE[1] + 0.9, 0.0), 180.0, tipo="santuario_kit",
              accion="kit minimo gratis (3 raciones, 3 antorchas): propuesta, el pedido no nombra la interaccion")


def build(col, world_rot_deg, repo, roof_obj, seed=2902):
    it = IK.Interior("Santuario", (W, D, H), "piedra", seed, world_rot_deg, DOOR, col)
    it.shell(storeys=1, ceiling=False, skip_sides=("-Y", "+Y", "-X", "+X"))
    it.log["near_walls"] = {"WALL_Near_A": "+Y"}
    it.nav_regions.append((0, 0.0, -W / 2, -D / 2, W / 2, D / 2))
    h, vinfo, _lim = fit_vault(roof_obj)
    zf = profile(h)
    info = {"vault": vinfo, "vault_texture": vault_material(repo)}
    info["windows"] = {"-Y": long_wall(it, "-Y"), "+Y": long_wall(it, "+Y")}
    end_wall(it, "-X")
    end_wall(it, "+X")
    info["vault"].update(vault(it, h, zf))
    info["well"] = well(it)
    info["furniture"] = furniture(it)
    lights(it, info["well"]["well_top_m"])
    markers(it)
    return it, info, zf


# --------------------------------------------------------------------------- informe y capturas
def build_report(col, src, B):
    repo = B.REPO
    props = B.collection("BLD_INT_PROPS_SAN")
    rep = {"source": src, "props_tris": build_props(props)}
    roof = bpy.data.objects["SRC_SANTUARIO_Roof"]
    it, info, zf = build(col, src["rot_deg"], repo, roof)
    rep.update(info)
    rep["size_check"] = B.size_check(it, src)
    figure = [(RESPAWN[0] + dx, RESPAWN[1], z) for z in (0.3, 0.9, 1.4, 1.75) for dx in (-0.15, 0.15)]
    npc = [(NPC[0] + dx, NPC[1], z) for z in (0.6, 1.0, 1.4, 1.75) for dx in (-0.15, 0.15)]
    top = info["well"]["well_top_m"]
    targets = {
        "Reaparicion (MARKER_Respawn)": (figure + [(RESPAWN[0], RESPAWN[1], 0.02)], ()),
        "Cuidador": (npc, ()),
        "Mesa del kit": ([(TABLE[0] + dx, TABLE[1] + dy, 0.82) for dx in (-0.3, 0.0, 0.3) for dy in (-0.15, 0.15)],
                         ("SAN_", "PROP_SAN")),
        "Pozo (agua y brocal)": ([(0.0, 0.0, 0.5), (0.5, 0.5, 0.9), (-0.5, 0.5, 0.9), (0.0, -0.6, 0.9)], ("SANTUARIO_Well",)),
        "Farol de esquirla": ([(0.0, 0.0, top + 0.3)], ("SANTUARIO_ShardLantern", "SANTUARIO_LanternHook")),
        "Ventanales del fondo": ([(x, -D / 2 + 0.05, z) for x in WIN_X for z in (3.0, 5.0, 7.0)], ("INT_Santuario_Wall-Y",)),
    }
    hide_sets = {"CAM_Iso (WALL_Near_A y CEILING ocultos)": (("WALL_Near_A", "WALL_Near_B", "CEILING"), list(targets))}
    keys = {"spawn": (0.0, D / 2 - 1.4, 0.0), "reaparicion": (RESPAWN[0], RESPAWN[1], 0.0),
            "cuidador_frente": (NPC[0], NPC[1] + 0.9, 0.0), "mesa_kit": (TABLE[0], TABLE[1] + 0.9, 0.0),
            "pozo_oeste": (-1.6, 0.0, 0.0), "pozo_sur": (0.0, -1.6, 0.0), "fondo_oeste": (-4.3, -3.3, 0.0),
            "fondo_este": (4.3, -3.3, 0.0), "bancos_oeste": (-4.3, 2.65, 0.0), "bancos_este": (4.3, 2.65, 0.0)}
    B.finish(it, "santuario", rep, keys, hide_sets, targets)
    # el exterior (solo para la comprobacion y la captura de seccion) se cuelga del marco DESPUES de exportar
    for o in bpy.data.collections["SRC_SANTUARIO_EXT"].objects:
        o.parent = it.frame
        o.matrix_parent_inverse = Matrix.Identity(4)
    # comprobacion final de la boveda ya unida contra la cubierta
    rep["vault"]["comprobacion_final"] = vault_clearance(it, roof, bpy.data.objects.get("SRC_SANTUARIO_Body"))
    return it, rep


def vault_clearance(it, roof, body=None):
    """Distancia vertical minima de los vertices del grupo CEILING a la cara inferior de la cubierta. Los timpanos
    (|x| > 6.9: grueso del muro del hastial, 0.4 m) quedan fuera del vuelo de la cubierta (x +-7.2) y se comprueban
    contra el cuerpo del exterior (SANTUARIO_Body: deben quedar dentro del hastial, por debajo de su remate)."""
    def bvh_of(o):
        me = o.data
        return BVHTree.FromPolygons([v.co.copy() for v in me.vertices], [list(p.vertices) for p in me.polygons], epsilon=0.0)
    rb = bvh_of(roof)
    bb = bvh_of(body) if body is not None else None
    worst, n, ends, ends_ok = 99.0, 0, 0, 0
    for o in it.groups["CEILING"].children_recursive:
        if o.type != "MESH":
            continue
        for v in o.data.vertices:
            p = o.matrix_basis @ v.co
            if abs(p.x) > W / 2 + 0.01:
                ends += 1
                if bb is not None:
                    loc, _n, _i, _d = bb.ray_cast(p, Vector((0, 0, 1)), 30.0)
                    ends_ok += 1 if loc is not None else 0
                continue
            loc, _n, _i, _d = rb.ray_cast(p, Vector((0, 0, 1)), 30.0)
            n += 1
            if loc is None:
                worst = -1.0
                continue
            worst = min(worst, loc.z - p.z)
    return {"vertices_boveda": n, "holgura_min_m": round(worst, 3), "ok": worst >= CLEAR - 1e-3,
            "timpanos_vertices_en_el_grueso_del_hastial": ends, "timpanos_bajo_el_hastial_exterior": ends_ok}


def captures(scene, C):
    """Capturas: iso, a 1.7 m desde la puerta, la reaparicion, la boveda desde abajo y la seccion contra la cubierta."""
    import capture_stage27 as C27
    root = bpy.data.objects["INT_Santuario"]
    fm = bpy.data.objects["INT_Santuario_Frame"].matrix_world
    C27.only_collections({"INT_SANTUARIO"})
    tmp = C27.lights_from_empties(root) + C.mannequins(root)
    lab = [("Reaparicion", fm @ Vector((RESPAWN[0], RESPAWN[1], 2.2))), ("Cuidador", fm @ Vector((NPC[0], NPC[1], 2.1))),
           ("Pozo y farol", fm @ Vector((0.0, -0.4, 3.4))), ("Mesa: 3 raciones, 3 antorchas", fm @ Vector((TABLE[0], TABLE[1], 1.3)))]
    if C.want("santuario_iso"):
        C27.set_hidden(root, ("WALL_Near_A", "WALL_Near_B", "CEILING"))
        cam = C27.iso_cam(fm @ Vector((0.0, -0.8, 3.0)), 17.0)
        C.shot(scene, cam, "santuario_iso", "Santuario del Retorno (13.8 x 9.6 x 9 m) en CAM_Iso: fachada y boveda ocultas",
               lab)
        C27.set_hidden(root, ("WALL_Near_A", "WALL_Near_B", "CEILING"), False)
    if C.want("santuario_calle"):
        C.eye(scene, fm, (0.6, 4.0, 1.7), (-0.6, -4.4, 3.6), 16, "santuario_calle",
              "Santuario a 1.7 m desde la puerta: pozo con su farol, ventanales y bancos")
    if C.want("santuario_boveda"):
        C.eye(scene, fm, (-1.0, 3.6, 1.7), (0.4, -1.5, 11.0), 14, "santuario_boveda",
              "Boveda (CEILING) vista desde abajo: nervios de piedra y plementeria azul con estrellas")
    if C.want("santuario_seccion"):
        for o in bpy.data.collections["SRC_SANTUARIO_EXT"].objects:
            o.hide_render = False
        bpy.data.collections["SRC_SANTUARIO_EXT"].hide_render = False
        cam = C27.K.new_cam("TMP_sec", ortho=13.0)
        cam.data.clip_start = 40.0
        cam.data.clip_end = 120.0
        C27.K.look_at(cam, fm @ Vector((-40.0, 0.0, 9.5)), fm @ Vector((0.0, 0.0, 9.5)))
        C.shot(scene, cam, "santuario_seccion", "Seccion por x = 0 (la camara recorta lo que esta delante): cubierta "
               "exterior SANTUARIO_Roof y boveda interior (CEILING)", [])
        bpy.data.collections["SRC_SANTUARIO_EXT"].hide_render = True
    for o in tmp:
        bpy.data.objects.remove(o)
