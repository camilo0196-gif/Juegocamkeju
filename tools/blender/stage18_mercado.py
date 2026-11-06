"""
CONCORDIA - Etapa 18 (E5): distrito del Mercado. Piezas singulares hechas a mano (los edificios corrientes salen
del kit con concordia_buildings.build_building / fit_iso_height, ver build_stage18.py).

  tesoreria_meshes   Tesoreria de la Muralla (28 x 18): Palazzo Pubblico de Siena - porticada de 7 arcos con
                     columnas, trifore, almenas guelfas, torre del reloj, 2 balanzas de bronce de 1.2 m y 4 salidas
                     de tubos de luz en la azotea (+9.6 m)
  subasta_meshes     Gran Subasta (40 x 16): halle de madera abierta, galerias laterales a +3.5 m, tarima 5 x 3 con
                     campana de 1.2 m y 6 tableros de precios
  stall              STALL_A..E (3 x 3): toldos de tela remendada, cajones de fruta, herramientas
  fountain           Fuente del Mercado: pila de 6 m, 4 canos, 8 bancos, rebosadero hacia el manantial del Cauce
  banco_extras       Banco: puerta de hierro, candado de 1 m, almohadillado de bloques pesados
  tablon / candle_sign / registro_props
Marco local de cada edificio: +Y = fachada de la puerta (door_direction), base a z = 0 sobre el pad.
"""

import math
import random

import bpy  # noqa: F401,I001
from mathutils import Matrix, Vector

import bld_kit as K
import stage16_landmarks as L

ST, LIGHT, GRAY = "MAT_Limestone_Worn", "MAT_Limestone_Light", "MAT_Wall_Gray"
WOOD, IRON, BRONZE = K.M_WOOD, K.M_IRON, "MAT_Bronze_Aged"
WARM, CORE, WATER = "MAT_Window_Warm", "MAT_Pipe_Light_Core", "MAT_Water"
CLOTH = K.M_CLOTH


def semi(x0, x1, zs, n=8):
    """Arco de medio punto de (x0, zs) a (x1, zs)."""
    r = (x1 - x0) / 2
    c = (x0 + x1) / 2
    return [(c - r * math.cos(math.pi * i / n), zs + r * math.sin(math.pi * i / n)) for i in range(n + 1)]


def arcade_outline(x0, x1, arches, top_rl):
    """Contorno de muro con varios arcos que llegan al suelo: arches = [(xa, xb, z_arranque)] ordenados."""
    pts = [(x0, 0.0)]
    for xa, xb, zs in arches:
        pts += [(xa, 0.0)] + semi(xa, xb, zs) + [(xb, 0.0)]
    return pts + [(x1, 0.0)] + top_rl


def rect(xc, zc, w, h):
    return [(xc - w / 2, zc - h / 2), (xc + w / 2, zc - h / 2), (xc + w / 2, zc + h / 2), (xc - w / 2, zc + h / 2)]


def barred_rect_fill(mb, xc, zc, w, h, y_glass=-0.3, glass=WARM, bars=3):
    mb.face([(x, y_glass, z) for x, z in rect(xc, zc, w, h)], glass, nrm=(0, 1, 0))
    for i in range(bars):
        x = xc - w / 2 + w * (i + 1) / (bars + 1)
        mb.box((x - 0.02, y_glass + 0.04, zc - h / 2), (x + 0.02, y_glass + 0.08, zc + h / 2), IRON, skip=("z-", "z+"))
    mb.box((xc - w / 2 - 0.08, -0.02, zc - h / 2 - 0.12), (xc + w / 2 + 0.08, 0.1, zc - h / 2), ST)


def merlons(mb, u0, u1, z0, z1, t, skip=None, mat=ST):
    """Almenas guelfas (rectas) sobre un muro del marco actual (cara exterior y = 0, espesor t). Centros en 0.6 + 1.2 k
    -> huecos (almenaras) en los multiplos de 1.2."""
    k0 = int(math.ceil((u0 + 0.3 - 0.6) / 1.2))
    k1 = int(math.floor((u1 - 0.3 - 0.6) / 1.2))
    n = 0
    for k in range(k0, k1 + 1):
        u = 0.6 + 1.2 * k
        if skip and skip(u):
            continue
        mb.box((u - 0.3, -t, z0), (u + 0.3, 0.0, z1), mat, skip=("z-",))
        n += 1
    return n


# ---------------------------------------------------------------------------
# TESORERIA DE LA MURALLA
# ---------------------------------------------------------------------------
class TES:
    W, D, T = 28.0, 18.0, 0.8
    YF = 8.7                       # cara de la porticada (las columnas llegan a 9.0)
    YP = 5.4                       # muro del fondo de la porticada
    F1, F2, PAR, MER = 4.8, 8.8, 9.3, 10.1
    BAY, ARCH_W, ARCH_S = 3.8, 2.8, 3.1
    WIN_W, WIN_Z0, WIN_TOP = 2.0, 5.6, 8.0
    OUTLET_X = (-3.6, -1.2, 1.2, 3.6)
    OUTLET_Y, OUTLET_Z = 6.6, 9.6
    TOWER = (-14.0, -9.6, -9.0, -4.6)      # x0, x1, y0, y1
    TOWER_TOP, CROWN = 17.0, 18.1
    CLOCK_Z, CLOCK_R = 15.6, 0.85
    SCALES_X = (-1.9, 1.9)


def scale_bronze(mb, u, z0, y0):
    """Balanza de bronce de 1.2 m (mensula, fiel, cruz y dos platillos colgados), en el marco de un muro."""
    b = BRONZE
    yc = y0 + 0.28
    mb.box((u - 0.12, y0, z0), (u + 0.12, y0 + 0.3, z0 + 0.12), b, skip=("y-",))
    mb.rod((u, yc, z0 + 0.12), (u, yc, z0 + 1.2), 0.035, b)
    mb.rod((u - 0.5, yc, z0 + 1.08), (u + 0.5, yc, z0 + 1.08), 0.025, b)
    tip = [(u, yc, z0 + 1.2), (u - 0.05, yc, z0 + 1.32), (u + 0.05, yc, z0 + 1.32)]
    L.tri_face(mb, *tip, b, (0, 1, 0))
    for s in (-1, 1):
        x = u + s * 0.5
        zp = z0 + 0.6
        for dx in (-0.14, 0.14):
            mb.rod((x, yc, z0 + 1.08), (x + dx, yc, zp + 0.08), 0.008, b)
        L._ring_frustum(mb, x, yc, 0.08, 0.2, zp - 0.04, zp + 0.08, 8, b)
        mb.face([(x + 0.08 * math.cos(2 * math.pi * i / 8), yc + 0.08 * math.sin(2 * math.pi * i / 8), zp - 0.04)
                 for i in range(8)][::-1], b, nrm=(0, 0, -1))


def clock_face(mb, u, z, y, r, hour_angle, minute_angle):
    """Esfera de reloj en el marco actual (cara hacia +Y): disco claro, aro y manecillas de hierro, 4 marcas."""
    mb.face([(u + r * math.cos(2 * math.pi * i / 16), y, z + r * math.sin(2 * math.pi * i / 16)) for i in range(16)],
            LIGHT, nrm=(0, 1, 0))
    L.rod_path(mb, L.circle(u, z, r + 0.04, 12), y + 0.02, 0.04, IRON, closed=True)
    for k in range(4):
        a = math.pi / 2 * k
        mb.rod((u + 0.72 * r * math.cos(a), y + 0.02, z + 0.72 * r * math.sin(a)),
               (u + 0.92 * r * math.cos(a), y + 0.02, z + 0.92 * r * math.sin(a)), 0.03, IRON)
    for ang, ln, w in ((hour_angle, 0.5, 0.035), (minute_angle, 0.8, 0.025)):
        mb.rod((u, y + 0.04, z), (u + ln * r * math.sin(ang), y + 0.04, z + ln * r * math.cos(ang)), w, IRON)


def tesoreria_meshes(rng):
    T = TES
    body, roof = K.MB(), K.MB()
    hw, hd = T.W / 2, T.D / 2
    info = {}
    centers = [T.BAY * k for k in range(-3, 4)]
    # porticada: muro de fachada con 7 arcos de medio punto y 7 trifore
    body.push(Matrix.Translation((0, T.YF, 0)))
    arches = [(c - T.ARCH_W / 2, c + T.ARCH_W / 2, T.ARCH_S) for c in centers]
    outer = arcade_outline(-hw, hw, arches, [(hw, T.PAR), (-hw, T.PAR)])
    holes = [L.lancet(c, T.WIN_W, T.WIN_Z0, T.WIN_TOP) for c in centers]
    L.plate(body, outer, holes, T.T, ST)
    for c in centers:
        L.window_fill(body, c, T.WIN_W, T.WIN_Z0, T.WIN_TOP, -T.T * 0.55, 3, ST, rose=False, glass=WARM, arc_n=2)
        L.rod_path(body, semi(c - T.ARCH_W / 2 - 0.16, c + T.ARCH_W / 2 + 0.16, T.ARCH_S, 8), 0.04, 0.07, ST)
    for c in centers[:-1]:                                  # columnas adosadas a los pilares
        u = c + T.BAY / 2
        body.box((u - 0.32, -0.3, 0.0), (u + 0.32, 0.25, 0.22), ST, skip=("z-",))
        L._ring_frustum(body, u, 0.0, 0.24, 0.21, 0.22, T.ARCH_S - 0.25, 8, ST)
        body.box((u - 0.33, -0.3, T.ARCH_S - 0.25), (u + 0.33, 0.27, T.ARCH_S), ST)
    for u in T.SCALES_X:
        scale_bronze(body, u, 5.55, 0.0)
    body.box((-hw - 0.12, -0.02, T.F2 - 0.2), (hw + 0.12, 0.15, T.F2), ST, skip=("y-",))
    body.box((-hw, -0.02, T.F1 - 0.15), (hw, 0.1, T.F1), ST, skip=("y-",))
    body.pop()
    # muro del fondo de la porticada (puerta + 2 ventanas enrejadas) y techo de la porticada
    xi = hw - T.T
    body.push(Matrix.Translation((0, T.YP, 0)))
    door = L.lancet(0.0, 2.0, 0.0, 3.6)
    L.plate(body, L.with_door(-xi, xi, door, [(xi, T.F1), (-xi, T.F1)]),
            [rect(u, 2.0, 1.2, 1.6) for u in (-7.6, 7.6)], 0.6, ST, back=False)
    for u in (-7.6, 7.6):
        barred_rect_fill(body, u, 2.0, 1.2, 1.6)
    L.door_leaves(body, 2.0, 3.6, -0.45, -0.33, straps=3)
    body.pop()
    body.face([(-xi, T.YP, T.F1), (xi, T.YP, T.F1), (xi, T.YF - T.T, T.F1), (-xi, T.YF - T.T, T.F1)], ST, nrm=(0, 0, -1))
    # fondo (-Y): 5 ventanas arriba, 4 enrejadas abajo
    body.push(L.frame("-Y", hw, hd))
    holes = [L.lancet(u, 1.4, 5.6, 7.8) for u in (-10, -5, 0, 5, 10)] + [rect(u, 2.1, 1.0, 1.4) for u in (-9, -3, 3, 9)]
    L.plate(body, [(-hw, 0), (hw, 0), (hw, T.PAR), (-hw, T.PAR)], holes, T.T, ST)
    for u in (-10, -5, 0, 5, 10):
        L.window_fill(body, u, 1.4, 5.6, 7.8, -T.T * 0.55, 2, ST, rose=False, glass=WARM, arc_n=2)
    for u in (-9, -3, 3, 9):
        barred_rect_fill(body, u, 2.1, 1.0, 1.4, y_glass=-T.T * 0.55)
    body.box((-hw - 0.12, -0.02, T.F2 - 0.2), (hw + 0.12, 0.15, T.F2), ST, skip=("y-",))
    L.plinth(body, -hw - 0.05, hw + 0.05, 0.6, 0.06, GRAY)
    body.pop()
    # costados: arco de paso a la porticada, 3 ventanas arriba, 2 enrejadas abajo
    for side, sg in (("+X", -1), ("-X", 1)):          # u = sg * y
        body.push(L.frame(side, hw, hd))
        ua, ub = sorted((sg * -(hd - T.T), sg * (T.YF - T.T)))
        uc = sg * 6.65
        top = [(ub, T.PAR), (ua, T.PAR)]
        outer = arcade_outline(ua, ub, [(uc - 1.0, uc + 1.0, 2.2)], top)
        ups = [sg * y for y in (-5.0, -1.0, 3.0)]
        downs = [sg * y for y in (-5.0, 0.0)]
        L.plate(body, outer, [L.lancet(u, 1.4, 5.6, 7.8) for u in ups] + [rect(u, 2.1, 1.0, 1.4) for u in downs], T.T, ST)
        for u in ups:
            L.window_fill(body, u, 1.4, 5.6, 7.8, -T.T * 0.55, 2, ST, rose=False, glass=WARM, arc_n=2)
        for u in downs:
            barred_rect_fill(body, u, 2.1, 1.0, 1.4, y_glass=-T.T * 0.55)
        body.box((ua - 0.12, -0.02, T.F2 - 0.2), (ub + 0.12, 0.15, T.F2), ST, skip=("y-",))
        L.plinth(body, ua, ub, 0.6, 0.06, GRAY)
        body.pop()
    # almenas (sin las de la esquina de la torre)
    tx0, tx1, ty0, ty1 = T.TOWER
    in_tower = lambda x, y: tx0 - 0.3 <= x <= tx1 + 0.3 and ty0 - 0.3 <= y <= ty1 + 0.3  # noqa: E731
    nm = 0
    body.push(Matrix.Translation((0, T.YF, 0)))
    nm += merlons(body, -hw, hw, T.PAR, T.MER, T.T)
    body.pop()
    body.push(L.frame("-Y", hw, hd))
    nm += merlons(body, -hw, hw, T.PAR, T.MER, T.T, skip=lambda u: in_tower(-u, -hd))
    body.pop()
    for side, sg, X in (("+X", -1, hw), ("-X", 1, -hw)):
        body.push(L.frame(side, hw, hd))
        ua, ub = sorted((sg * -(hd - T.T), sg * (T.YF - T.T)))
        nm += merlons(body, ua, ub, T.PAR, T.MER, T.T, skip=lambda u, X=X, sg=sg: in_tower(X, sg * u))
        body.pop()
    info["merlons"] = nm
    # torre del reloj (esquina trasera izquierda), desde el antepecho
    tw = tx1 - tx0
    body.box((tx0, ty0, T.PAR), (tx1, ty1, T.TOWER_TOP), ST, skip=("z-", "z+"))
    body.box((tx0 - 0.2, ty0 - 0.2, T.TOWER_TOP), (tx1 + 0.2, ty1 + 0.2, T.TOWER_TOP + 0.3), ST)
    cx, cy = (tx0 + tx1) / 2, (ty0 + ty1) / 2
    for side, sg in (("+X", 1), ("-X", -1), ("+Y", 1), ("-Y", -1)):
        if side in ("+X", "-X"):
            fr = Matrix.Translation((cx + sg * tw / 2, cy, 0)) @ Matrix.Rotation(-sg * math.pi / 2, 4, "Z")
        else:
            fr = Matrix.Translation((cx, cy + sg * tw / 2, 0)) @ Matrix.Rotation(0 if sg > 0 else math.pi, 4, "Z")
        body.push(fr)
        clock_face(body, 0.0, T.CLOCK_Z, 0.01, T.CLOCK_R, math.radians(300), math.radians(60))
        for z in (11.0, 13.0):
            body.face([(-0.12, 0.01, z - 0.6), (0.12, 0.01, z - 0.6), (0.12, 0.01, z + 0.6), (-0.12, 0.01, z + 0.6)], IRON,
                      nrm=(0, 1, 0))
        for k in range(3):
            u = -tw / 2 + 0.55 + k * (tw - 1.1) / 2
            body.box((u - 0.3, -0.5, T.TOWER_TOP + 0.3), (u + 0.3, 0.2, T.CROWN), ST, skip=("z-",))
        body.pop()
    # remiendos
    spots = [(L.frame("-Y", hw, hd), -12.0, 12.0, 0.8, 1.3), (Matrix.Translation((0, T.YF, 0)), -13.5, -12.9, 4.9, 5.5)]
    info["stone_patches"] = L.stone_patches(body, [spots[0]], rng, rng.randint(2, 4))
    body.finish()
    # azotea (Roof): losa a +8.8 y 4 salidas de tubos de luz con boca a +9.6
    roof.face([(-xi, -(hd - T.T), T.F2), (xi, -(hd - T.T), T.F2), (xi, T.YF - T.T, T.F2), (-xi, T.YF - T.T, T.F2)], GRAY,
              nrm=(0, 0, 1))
    roof.box((tx0, ty0, T.TOWER_TOP + 0.3 - 0.01), (tx1, ty1, T.TOWER_TOP + 0.31), GRAY, skip=("z-",))
    outlets = []
    for x in T.OUTLET_X:
        y = T.OUTLET_Y
        roof.box((x - 0.45, y - 0.45, T.F2), (x + 0.45, y + 0.45, 9.15), ST, skip=("z-",))
        L._ring_frustum(roof, x, y, 0.2, 0.2, 9.15, T.OUTLET_Z - 0.06, 8, IRON)
        L._ring_frustum(roof, x, y, 0.27, 0.27, T.OUTLET_Z - 0.06, T.OUTLET_Z, 8, IRON)
        roof.face([(x + 0.27 * math.cos(2 * math.pi * i / 8), y + 0.27 * math.sin(2 * math.pi * i / 8), T.OUTLET_Z)
                   for i in range(8)], CORE, nrm=(0, 0, 1))
        outlets.append((x, y, T.OUTLET_Z))
    roof.finish()
    info["outlets_local"] = outlets
    info["door_local"] = (0.0, T.YP, 0.0)
    info["interior"] = {"center": (0.0, (-(hd - T.T) + T.YP) / 2), "size": (2 * xi, T.YP + hd - T.T, T.F2)}
    return body, roof, info


# ---------------------------------------------------------------------------
# GRAN SUBASTA (halle de madera abierta)
# ---------------------------------------------------------------------------
class SUB:
    W, D = 40.0, 16.0
    YO, YI = 7.7, 3.9               # filas de postes exterior / interior
    NX = 11
    Z_GAL, Z_EAVE, Z_INNER, RIDGE = 3.5, 4.8, 7.4, 10.4
    EAVE_OV = 0.8


def sub_xs():
    return [-19.7 + 39.4 * k / (SUB.NX - 1) for k in range(SUB.NX)]


def bell(mb, x, y, z_top, h=1.2):
    """Campana de bronce de h m (perfil girado de 8 lados) colgada de z_top, con badajo."""
    prof = [(0.12, 0.0), (0.26, -0.12), (0.33, -0.45), (0.4, -0.85), (0.55, -1.1), (0.6, -h)]
    for (r0, z0), (r1, z1) in zip(prof[:-1], prof[1:]):
        L._ring_frustum(mb, x, y, r1, r0, z_top + z1, z_top + z0, 8, BRONZE)
    mb.face([(x + 0.12 * math.cos(2 * math.pi * i / 8), y + 0.12 * math.sin(2 * math.pi * i / 8), z_top) for i in range(8)],
            BRONZE, nrm=(0, 0, 1))
    mb.rod((x, y, z_top), (x, y, z_top - h + 0.15), 0.03, IRON)
    mb.box((x - 0.07, y - 0.07, z_top - h + 0.05), (x + 0.07, y + 0.07, z_top - h + 0.2), IRON)


def price_board(mb, w=1.6, h=1.0, rng=None):
    """Tablero de precios: tabla oscura con marco y 4 lineas de tiza (caliza clara). Cara hacia +Y."""
    mb.box((-w / 2, 0.0, 0.0), (w / 2, 0.05, h), WOOD, skip=("y-",))
    for z0, z1 in ((0.0, 0.06), (h - 0.06, h)):
        mb.box((-w / 2 - 0.03, 0.05, z0), (w / 2 + 0.03, 0.08, z1), WOOD, skip=("y-",))
    rng = rng or random.Random(0)
    for k in range(4):
        z = 0.2 + 0.18 * k
        ln = rng.uniform(0.5, 1.2)
        mb.face([(-w / 2 + 0.15, 0.052, z), (-w / 2 + 0.15 + ln, 0.052, z), (-w / 2 + 0.15 + ln, 0.052, z + 0.04),
                 (-w / 2 + 0.15, 0.052, z + 0.04)], LIGHT, nrm=(0, 1, 0))


def subasta_meshes(rng):
    S = SUB
    body, roof = K.MB(), K.MB()
    xs = sub_xs()
    col = K.MB()                       # colision (cajas)
    for x in xs:
        for y, top in ((S.YO, S.Z_EAVE), (-S.YO, S.Z_EAVE), (S.YI, S.Z_INNER), (-S.YI, S.Z_INNER)):
            body.box((x - 0.28, y - 0.28, 0.0), (x + 0.28, y + 0.28, 0.4), ST, skip=("z-",))
            body.box((x - 0.15, y - 0.15, 0.4), (x + 0.15, y + 0.15, top), WOOD, skip=("z-", "z+"))
            col.box((x - 0.2, y - 0.2, 0.0), (x + 0.2, y + 0.2, top), WOOD)
    # carreras (vigas largas)
    for y, z in ((S.YO, S.Z_EAVE), (-S.YO, S.Z_EAVE), (S.YI, S.Z_INNER), (-S.YI, S.Z_INNER)):
        body.box((-19.9, y - 0.17, z), (19.9, y + 0.17, z + 0.32), WOOD)
    # cerchas: tirante entre postes interiores, pendolon y tornapuntas; vigas de las galerias
    for x in xs:
        body.box((x - 0.14, -S.YI, S.Z_INNER + 0.05), (x + 0.14, S.YI, S.Z_INNER + 0.3), WOOD, skip=("y-", "y+"))
        body.rod((x, 0.0, S.Z_INNER + 0.3), (x, 0.0, S.RIDGE - 0.2), 0.09, WOOD)
        for sg in (-1, 1):
            body.rod((x, sg * (S.YI - 0.1), S.Z_INNER - 1.1), (x, sg * (S.YI - 1.2), S.Z_INNER + 0.1), 0.07, WOOD)
            body.rod((x, 0.0, S.RIDGE - 1.2), (x, sg * 2.0, S.Z_INNER + 0.32 + (S.RIDGE - S.Z_INNER) * 0.35), 0.06, WOOD)
            ya, yb = sorted((sg * S.YI, sg * S.YO))
            body.box((x - 0.12, ya, S.Z_GAL - 0.3), (x + 0.12, yb, S.Z_GAL - 0.1), WOOD)
    # galerias laterales a +3.5: tablero, barandilla al lado de la nave y al exterior, escalera al oeste
    for sg in (-1, 1):
        y0, y1 = sorted((sg * (S.YI - 0.15), sg * (S.YO + 0.15)))
        body.box((-19.9, y0, S.Z_GAL - 0.1), (19.9, y1, S.Z_GAL), WOOD)
        col.box((-19.9, y0, S.Z_GAL - 0.1), (19.9, y1, S.Z_GAL), WOOD)
        for yr in (sg * (S.YI - 0.1), sg * (S.YO + 0.05)):
            for zr in (S.Z_GAL + 1.0, S.Z_GAL + 0.5):
                body.box((-19.9, yr - 0.04, zr - 0.04), (19.9, yr + 0.04, zr + 0.04), WOOD, skip=("x-", "x+"))
            for k in range(20):
                x = -19.0 + 2.0 * k
                if any(abs(x - xp) < 0.4 for xp in xs):
                    continue
                body.box((x - 0.04, yr - 0.04, S.Z_GAL), (x + 0.04, yr + 0.04, S.Z_GAL + 1.0), WOOD, skip=("z-", "z+"))
        # escalera recta en el pasillo lateral, en el extremo oeste (sube hacia +x)
        n = 14
        yc = sg * (S.YI + S.YO) / 2
        for i in range(n):
            x0 = -18.9 + i * 0.32
            z = S.Z_GAL * (i + 1) / n
            body.box((x0, yc - 0.6, z - 0.06), (x0 + 0.34, yc + 0.6, z), WOOD)
        for yy in (yc - 0.62, yc + 0.62):
            body.rod((-18.9, yy, 0.05), (-18.9 + n * 0.32, yy, S.Z_GAL), 0.06, WOOD)
        col.box((-18.9, yc - 0.6, 0.0), (-18.9 + n * 0.32, yc + 0.6, S.Z_GAL * 0.5), WOOD)
    # tarima 5 x 3 con peldanos y campana en su soporte
    body.box((-2.5, -1.5, 0.0), (2.5, 1.5, 0.8), WOOD, skip=("z-",))
    col.box((-2.5, -1.5, 0.0), (2.5, 1.5, 0.8), WOOD)
    for k in range(3):
        body.box((-1.0, 1.5 + 0.3 * (2 - k), 0.0), (1.0, 1.5 + 0.3 * (3 - k), 0.27 * (k + 1)), WOOD, skip=("z-",))
    for sx in (-0.95, 0.95):
        body.box((sx - 0.09, -0.09, 0.8), (sx + 0.09, 0.09, 3.3), WOOD, skip=("z-",))
        body.rod((sx, 0.0, 2.6), (sx * 0.45, 0.0, 3.2), 0.05, WOOD)
    body.box((-1.2, -0.1, 3.2), (1.2, 0.1, 3.42), WOOD)
    bell(body, 0.0, 0.0, 3.2)
    # 6 tableros de precios en los postes interiores (mirando a la nave)
    picks = [xs[2], xs[5], xs[8]]
    for sg in (-1, 1):
        for x in picks:
            body.push(Matrix.Translation((x, sg * (S.YI - 0.16), 1.9)) @ Matrix.Rotation(0 if sg < 0 else math.pi, 4, "Z"))
            price_board(body, rng=rng)
            body.pop()
    body.finish()
    # cubierta de teja (+ tablero inferior de madera, visto desde dentro)
    s = (S.RIDGE - (S.Z_EAVE + 0.32)) / S.YO
    hy = S.YO + S.EAVE_OV
    z_e = S.Z_EAVE + 0.32 - S.EAVE_OV * s
    hx = 20.0 + 0.6
    for sgn in (-1, 1):
        L.tile_slope(roof, -hx, hx, sgn * hy, 0.0, z_e, S.RIDGE, rng, seg=4.2)
        roof.face([(-hx, sgn * hy, z_e - 0.02), (-hx, 0, S.RIDGE - 0.02), (hx, 0, S.RIDGE - 0.02), (hx, sgn * hy, z_e - 0.02)],
                  WOOD, nrm=(0, 0, -1))
        roof.box((-hx, sgn * hy - 0.03, z_e - 0.22), (hx, sgn * hy + 0.03, z_e), WOOD)
        for x in (-hx, hx):
            roof.rod((x, sgn * hy, z_e), (x, 0.0, S.RIDGE + 0.08), 0.07, WOOD)
    roof.box((-hx, -0.14, S.RIDGE - 0.02), (hx, 0.14, S.RIDGE + 0.15), K.M_ROOF_B)
    rep = L.roof_repairs(roof, -hx, hx, hy, z_e, S.RIDGE, rng, rng.randint(2, 4))
    roof.finish()
    col.finish()
    return body, roof, col, {"roof_repairs": rep, "pitch_deg": round(math.degrees(math.atan(s)), 1)}


# ---------------------------------------------------------------------------
# PUESTOS STALL_A..E (3 x 3, frente +Y)
# ---------------------------------------------------------------------------
def _awning_slope(mb, y_back, z_back, y_front, z_front, cloth, patch, rng, hw=1.6, val=True):
    q = [(-hw, y_back, z_back), (hw, y_back, z_back), (hw, y_front, z_front), (-hw, y_front, z_front)]
    mb.face(q, cloth, nrm=(0, 0.3, 1))
    if val:
        n = 6
        for i in range(n):
            x0, x1 = -hw + 2 * hw * i / n, -hw + 2 * hw * (i + 1) / n
            mb.face([(x0, y_front, z_front), (x1, y_front, z_front), ((x0 + x1) / 2, y_front, z_front - 0.22)], cloth,
                    nrm=(0, 1, 0))
    a = rng.uniform(0.15, 0.5)
    x0 = rng.uniform(-hw + 0.2, hw - 0.9)
    t0, t1 = a, a + rng.uniform(0.2, 0.3)
    p = lambda t, x: (x, y_back + (y_front - y_back) * t, z_back + (z_front - z_back) * t + 0.012)  # noqa: E731
    mb.face([p(t0, x0), p(t0, x0 + 0.6), p(t1, x0 + 0.6), p(t1, x0)], patch, nrm=(0, 0.3, 1))


def _counter(mb, y0=0.6, y1=1.35, h=0.95):
    mb.box((-1.3, y0, 0.0), (1.3, y1, h), WOOD, skip=("z-",))
    mb.box((-1.4, y0 - 0.08, h), (1.4, y1 + 0.08, h + 0.05), WOOD)


def _posts(mb, zf, zb):
    for x in (-1.4, 1.4):
        for y, z in ((1.35, zf), (-1.35, zb)):
            mb.box((x - 0.05, y - 0.05, 0.0), (x + 0.05, y + 0.05, z), WOOD, skip=("z-",))


def _tools(mb, y, z, rng, n=3):
    for i in range(n):
        x = -0.9 + i * 0.9 + rng.uniform(-0.1, 0.1)
        mb.rod((x, y, z), (x, y, z - 0.75), 0.018, WOOD)
        kind = i % 3
        if kind == 0:
            mb.box((x - 0.1, y - 0.02, z - 0.85), (x + 0.1, y + 0.02, z - 0.72), IRON)      # azada
        elif kind == 1:
            mb.box((x - 0.03, y - 0.01, z - 1.05), (x + 0.12, y + 0.01, z - 0.75), IRON)     # sierra
        else:
            L.tri_face(mb, (x, y, z - 0.7), (x + 0.16, y, z - 0.78), (x, y, z - 0.9), IRON, (0, 1, 0))  # hacha


def stall(mb, variant, rng):
    """5 variantes; tela A/B/C rotando, remiendo de otra tela."""
    v = "ABCDE".index(variant)
    cloth, patch = CLOTH[v % 3], CLOTH[(v + 1) % 3]
    if variant == "A":                        # fruta: toldo inclinado, 2 cajones en el mostrador + 1 en el suelo
        _posts(mb, 2.25, 2.6)
        _counter(mb)
        _awning_slope(mb, -1.5, 2.6, 1.9, 2.2, cloth, patch, rng)
        for x in (-0.6, 0.6):
            mb.push(Matrix.Translation((x, 0.97, 1.0)))
            K.crate(mb, fruit=True, rng=rng)
            mb.pop()
        mb.push(Matrix.Translation((1.0, 1.75, 0.0)) @ Matrix.Rotation(0.3, 4, "Z"))
        K.crate(mb, fruit=True, rng=rng)
        mb.pop()
    elif variant == "B":                      # toldo a dos aguas, tonel y sacos
        _posts(mb, 2.4, 2.4)
        _counter(mb)
        _awning_slope(mb, 0.0, 2.85, 1.8, 2.3, cloth, patch, rng)
        _awning_slope(mb, 0.0, 2.85, -1.8, 2.3, cloth, patch, rng, val=False)
        mb.push(Matrix.Translation((-0.9, -0.6, 0.0)))
        K.barrel(mb, n=8)
        mb.pop()
        for x in (0.2, 0.7):
            mb.box((x - 0.2, 0.75, 1.0), (x + 0.2, 1.15, 1.35), CLOTH[2], skip=("z-",))
    elif variant == "C":                      # herramientas colgadas, cortina lateral
        _posts(mb, 2.25, 2.6)
        _counter(mb)
        _awning_slope(mb, -1.5, 2.6, 1.9, 2.2, cloth, patch, rng)
        mb.face([(-1.45, -1.35, 0.4), (-1.45, 1.3, 0.4), (-1.45, 1.3, 2.25), (-1.45, -1.35, 2.6)], patch, nrm=(-1, 0, 0))
        mb.box((-1.4, -1.25, 2.1), (1.4, -1.15, 2.18), WOOD, skip=("x-", "x+"))
        _tools(mb, -1.2, 2.1, rng)
        mb.push(Matrix.Translation((0.5, 0.97, 1.0)))
        K.crate(mb, fruit=False, s=0.45, rng=rng)
        mb.pop()
    elif variant == "D":                      # estantes al fondo con cajones
        _posts(mb, 2.25, 2.6)
        _counter(mb, h=0.85)
        _awning_slope(mb, -1.5, 2.6, 1.9, 2.2, cloth, patch, rng)
        for z in (0.6, 1.3):
            mb.box((-1.3, -1.3, z), (1.3, -0.85, z + 0.05), WOOD)
        for x, z in ((-0.8, 0.65), (0.0, 1.35), (0.8, 0.65)):
            mb.push(Matrix.Translation((x, -1.07, z)))
            K.crate(mb, fruit=(x == 0.0), s=0.4, rng=rng)
            mb.pop()
    else:                                     # E: mostrador escalonado, cestas, herramientas al frente
        _posts(mb, 2.3, 2.6)
        _counter(mb, y0=0.9, y1=1.35, h=0.7)
        mb.box((-1.3, 0.3, 0.0), (1.3, 0.9, 1.05), WOOD, skip=("z-",))
        _awning_slope(mb, -1.5, 2.6, 1.9, 2.25, cloth, patch, rng)
        for x in (-0.8, 0.0, 0.8):
            L._ring_frustum(mb, x, 1.12, 0.17, 0.22, 0.7, 0.92, 6, WOOD)
        mb.box((-1.4, 1.3, 2.05), (1.4, 1.38, 2.12), WOOD, skip=("x-", "x+"))
        _tools(mb, 1.34, 2.05, rng, n=2)


# ---------------------------------------------------------------------------
# FUENTE DEL MERCADO
# ---------------------------------------------------------------------------
def fountain(mb, ground_z, outlet_dir_local, bench_skip_deg=None):
    """Pila de 6 m (r 3.0), fuste con taza y 4 canos, 8 bancos a r 6.5 y rebosadero hacia outlet_dir_local
    (vector 2D) hasta la distancia de la direccion. ground_z(x, y) -> z local del suelo."""
    n = 32
    R, Ri, H = 3.0, 2.68, 0.62
    L._ring_frustum(mb, 0, 0, R, R - 0.04, 0.0, H, n, ST)
    ring_o = [(R * math.cos(2 * math.pi * i / n), R * math.sin(2 * math.pi * i / n)) for i in range(n)]
    ring_i = [(Ri * math.cos(2 * math.pi * i / n), Ri * math.sin(2 * math.pi * i / n)) for i in range(n)]
    for i in range(n):
        j = (i + 1) % n
        mb.face([(*ring_o[i], H), (*ring_o[j], H), (*ring_i[j], H), (*ring_i[i], H)], LIGHT, nrm=(0, 0, 1))
        a = 2 * math.pi * (i + 0.5) / n
        mb.face([(*ring_i[i], H), (*ring_i[j], H), (*ring_i[j], 0.12), (*ring_i[i], 0.12)], ST,
                nrm=(-math.cos(a), -math.sin(a), 0))
    mb.face([(x, y, 0.48) for x, y in ring_i], WATER, nrm=(0, 0, 1))
    # fuste octogonal, taza y remate
    L._ring_frustum(mb, 0, 0, 0.5, 0.42, 0.12, 2.1, 8, ST)
    L._ring_frustum(mb, 0, 0, 0.45, 1.0, 2.1, 2.4, 12, LIGHT)
    mb.face([(1.0 * math.cos(2 * math.pi * i / 12), 1.0 * math.sin(2 * math.pi * i / 12), 2.4) for i in range(12)], WATER,
            nrm=(0, 0, 1))
    L._ring_frustum(mb, 0, 0, 0.22, 0.0, 2.4, 3.0, 6, LIGHT)
    # 4 canos de bronce y sus chorros (cintas de agua de doble cara)
    for k in range(4):
        a = math.pi / 4 + k * math.pi / 2
        d = Vector((math.cos(a), math.sin(a), 0))
        p0 = d * 0.45 + Vector((0, 0, 1.55))
        p1 = d * 0.95 + Vector((0, 0, 1.5))
        mb.rod(tuple(p0), tuple(p1), 0.05, BRONZE)
        side = Vector((-d.y, d.x, 0)) * 0.05
        pts = [p1 + d * (0.55 * t) + Vector((0, 0, -0.98 * t * t)) for t in (0.0, 0.33, 0.66, 1.0)]
        for qa, qb in zip(pts[:-1], pts[1:]):
            q = [qa - side, qa + side, qb + side, qb - side]
            mb.face([tuple(v) for v in q], WATER, nrm=(0, 0, 1))
            mb.face([tuple(v) for v in q][::-1], WATER, nrm=(0, 0, -1))
    # 8 bancos de piedra a r 6.5 (tangentes)
    benches = []
    for k in range(8):
        a = math.radians(22.5 + 45 * k)
        if bench_skip_deg is not None and abs(((math.degrees(a) - bench_skip_deg + 180) % 360) - 180) < 12:
            continue
        c = Vector((6.5 * math.cos(a), 6.5 * math.sin(a), 0))
        z0 = ground_z(c.x, c.y)
        mb.push(Matrix.Translation((c.x, c.y, z0)) @ Matrix.Rotation(a + math.pi / 2, 4, "Z"))
        for x in (-0.75, 0.75):
            mb.box((x - 0.12, -0.18, 0.0), (x + 0.12, 0.18, 0.4), ST, skip=("z-",))
        mb.box((-1.0, -0.24, 0.4), (1.0, 0.24, 0.5), LIGHT)
        mb.pop()
        benches.append(round(math.degrees(a), 1))
    # rebosadero: labio en el borde y canalillo de piedra hasta el manantial
    dv = Vector((outlet_dir_local[0], outlet_dir_local[1], 0))
    dist = dv.length
    dv.normalize()
    nv = Vector((-dv.y, dv.x, 0))
    lip_c = dv * R
    mb.push(Matrix.Translation((lip_c.x, lip_c.y, 0)) @ Matrix.Rotation(math.atan2(dv.y, dv.x), 4, "Z"))
    mb.box((-0.05, -0.32, H - 0.1), (0.45, 0.32, H - 0.02), LIGHT)
    mb.pop()
    segs = max(4, int((dist - R) / 1.2))
    prev = None
    for i in range(segs + 1):
        t = R + 0.3 + (dist - R - 0.3) * i / segs
        c = dv * t
        zg = ground_z(c.x, c.y)
        if i == 0:
            zg = min(zg, 0.0)
        cur = (c, zg)
        if prev is not None:
            (ca, za), (cb, zb) = prev, cur
            wh = 0.2
            water = [ca - nv * wh, ca + nv * wh, cb + nv * wh, cb - nv * wh]
            mb.face([(v.x, v.y, z) for v, z in zip(water, (za - 0.04, za - 0.04, zb - 0.04, zb - 0.04))], WATER,
                    nrm=(0, 0, 1))
            for s in (-1, 1):
                o0, o1 = s * wh, s * (wh + 0.14)
                a0, a1, b0, b1 = ca + nv * o0, ca + nv * o1, cb + nv * o0, cb + nv * o1
                mb.face([(a0.x, a0.y, za + 0.12), (b0.x, b0.y, zb + 0.12), (b1.x, b1.y, zb + 0.12),
                         (a1.x, a1.y, za + 0.12)], ST, nrm=(0, 0, 1))
                mb.face([(a0.x, a0.y, za - 0.05), (b0.x, b0.y, zb - 0.05), (b0.x, b0.y, zb + 0.12),
                         (a0.x, a0.y, za + 0.12)], ST, nrm=(-s * nv.x, -s * nv.y, 0))
                mb.face([(a1.x, a1.y, za + 0.12), (b1.x, b1.y, zb + 0.12), (b1.x, b1.y, zb - 0.05),
                         (a1.x, a1.y, za - 0.05)], ST, nrm=(s * nv.x, s * nv.y, 0))
        prev = cur
    return {"benches_deg": benches, "overflow_m": round(dist - R, 2), "overflow_dir": [round(dv.x, 3), round(dv.y, 3)]}


# ---------------------------------------------------------------------------
# piezas sueltas: tablon de grupos, letrero con vela, banco, registro
# ---------------------------------------------------------------------------
def tablon(mb, rng):
    """Tablon de Grupos: tablero de 3 x 2 m sobre dos postes, con tejadillo, ganchos y avisos. Cara +Y."""
    for x in (-1.6, 1.6):
        mb.box((x - 0.09, -0.09, 0.0), (x + 0.09, 0.09, 3.0), WOOD, skip=("z-",))
    mb.box((-1.5, -0.04, 0.7), (1.5, 0.04, 2.7), WOOD)
    for z0, z1 in ((0.65, 0.75), (2.65, 2.75)):
        mb.box((-1.55, 0.04, z0), (1.55, 0.09, z1), WOOD, skip=("y-",))
    L.tri_face(mb, (-1.8, -0.3, 3.0), (1.8, -0.3, 3.0), (0.0, -0.3, 3.45), WOOD, (0, -1, 0))
    mb.face([(-1.8, 0.35, 2.95), (1.8, 0.35, 2.95), (1.8, -0.35, 3.25), (-1.8, -0.35, 3.25)], K.M_ROOF, nrm=(0, 0.6, 1))
    for r, z in enumerate((2.35, 1.85, 1.35)):
        for k in range(6):
            x = -1.25 + k * 0.5
            mb.rod((x, 0.04, z), (x, 0.16, z + 0.06), 0.012, IRON)
            if rng.random() < 0.6:
                w, h = rng.uniform(0.25, 0.4), rng.uniform(0.3, 0.42)
                mb.face([(x - w / 2, 0.05, z - h), (x + w / 2, 0.05, z - h), (x + w / 2, 0.05, z - 0.02),
                         (x - w / 2, 0.05, z - 0.02)], LIGHT, nrm=(0, 1, 0))


def candle_sign(mb):
    """Letrero colgante del kit + vela encendida en un platillo de hierro sobre el brazo (llama: MAT_Window_Warm 1.0)."""
    K.sign_hanging(mb)
    y = 0.62
    L._ring_frustum(mb, 0.0, y, 0.06, 0.06, 0.06, 0.08, 6, IRON, cap_top=True)
    L._ring_frustum(mb, 0.0, y, 0.025, 0.022, 0.08, 0.26, 6, LIGHT)
    pts = [(0.018 * math.cos(2 * math.pi * i / 4), y + 0.018 * math.sin(2 * math.pi * i / 4), 0.29) for i in range(4)]
    for i in range(4):
        j = (i + 1) % 4
        mb.face([pts[i], pts[j], (0.0, y, 0.36)], WARM, nrm=(pts[i][0] + pts[j][0], pts[i][1] + pts[j][1] - 2 * y, 0.4))
        mb.face([pts[j], pts[i], (0.0, y, 0.27)], WARM, nrm=(pts[i][0] + pts[j][0], pts[i][1] + pts[j][1] - 2 * y, -0.4))


def book_sign(mb):
    """Letrero del Registro: brazo de hierro con un libro abierto colgado (tapas de madera, hojas claras). Sale a +Y."""
    mb.box((-0.03, 0.0, 0.0), (0.03, 1.0, 0.06), IRON)
    mb.rod((0, 0.0, -0.45), (0, 0.55, 0.0), 0.02, IRON)
    for y in (0.35, 0.85):
        mb.box((-0.01, y - 0.01, -0.22), (0.01, y + 0.01, 0.0), IRON, skip=("z-", "z+"))
    for s in (-1, 1):
        mb.face([(0.0, 0.25, -0.8), (0.0, 0.95, -0.8), (s * 0.28, 0.95, -0.22), (s * 0.28, 0.25, -0.22)], WOOD,
                nrm=(s, 0, -0.5))
        mb.face([(0.0, 0.28, -0.76), (s * 0.25, 0.28, -0.26), (s * 0.25, 0.92, -0.26), (0.0, 0.92, -0.76)], LIGHT,
                nrm=(-s, 0, 0.5))


def notice_board(mb, rng, w=1.3, h=1.0):
    """Tablon de avisos de fachada (cara +Y): marco de madera y papeles."""
    mb.box((-w / 2, 0.0, 0.0), (w / 2, 0.05, h), WOOD, skip=("y-",))
    mb.box((-w / 2 - 0.05, 0.0, h), (w / 2 + 0.05, 0.25, h + 0.06), WOOD)
    for _ in range(5):
        pw, ph = rng.uniform(0.2, 0.32), rng.uniform(0.25, 0.38)
        x, z = rng.uniform(-w / 2 + 0.2, w / 2 - 0.2), rng.uniform(0.2, h - 0.2)
        mb.face([(x - pw / 2, 0.055, z - ph / 2), (x + pw / 2, 0.055, z - ph / 2), (x + pw / 2, 0.055, z + ph / 2),
                 (x - pw / 2, 0.055, z + ph / 2)], LIGHT, nrm=(0, 1, 0))


def banco_extras(mb, door_x, door_w, door_h, y_face, W, rng):
    """Banco: hoja de hierro negro (con bandas y clavos) delante de la puerta del kit, candado de 1 m, y tres hiladas
    de sillares almohadillados en la planta baja de la fachada (Porta Nigra)."""
    y = y_face
    mb.box((door_x - door_w / 2, y - 0.17, 0.0), (door_x + door_w / 2, y - 0.1, door_h), IRON, skip=("y-",))
    for z in (0.35, 0.95, 1.55, 2.1):
        mb.box((door_x - door_w / 2, y - 0.1, z - 0.05), (door_x + door_w / 2, y - 0.07, z + 0.05), IRON, skip=("y-",))
    # candado de 1 m: cuerpo, arco y ojo
    cx, cz = door_x, 0.9
    mb.box((cx - 0.35, y - 0.07, cz - 0.3), (cx + 0.35, y + 0.18, cz + 0.3), IRON, skip=("y-",))
    arc = [(cx - 0.22 + 0.44 * (1 - math.cos(math.pi * i / 6)) / 2, cz + 0.3 + 0.38 * math.sin(math.pi * i / 6)) for i in range(7)]
    L.rod_path(mb, arc, y + 0.06, 0.045, IRON)
    mb.face([(cx - 0.05, y + 0.181, cz - 0.15), (cx + 0.05, y + 0.181, cz - 0.15), (cx + 0.05, y + 0.181, cz),
             (cx - 0.05, y + 0.181, cz)], WOOD, nrm=(0, 1, 0))
    # almohadillado: sillares de 2 x 0.9 en tres hiladas, salvo delante de la puerta
    n = 0
    for k, z in enumerate((0.0, 0.95, 1.9)):
        off = 0.0 if k % 2 == 0 else 1.0
        x = -W / 2 + off
        while x < W / 2 - 0.2:
            x1 = min(x + 1.95, W / 2)
            if not (x1 > door_x - door_w / 2 - 0.3 and x < door_x + door_w / 2 + 0.3):
                mb.box((x + 0.03, y, z + 0.03), (x1 - 0.03, y + 0.07, z + 0.9), LIGHT, skip=("y-",))
                n += 1
            x += 2.0
    return n


def merge_mb_into(obj, mb):
    """Anade la geometria de un MB al objeto (mismo espacio local), mapeando materiales por nombre."""
    import bmesh
    me = obj.data
    names = [m.name for m in me.materials]
    for n in mb.mats:
        if n not in names:
            me.materials.append(bpy.data.materials[n])
            names.append(n)
    remap = {i: names.index(n) for i, n in enumerate(mb.mats)}
    for f in mb.bm.faces:
        f.material_index = remap[f.material_index]
    tmp = bpy.data.meshes.new("TMP_merge")
    mb.bm.to_mesh(tmp)
    bm = bmesh.new()
    bm.from_mesh(me)
    bm.from_mesh(tmp)
    bm.to_mesh(me)
    bm.free()
    bpy.data.meshes.remove(tmp)
