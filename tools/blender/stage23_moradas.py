"""
CONCORDIA - Etapa 23 (E10): viviendas de las 4 Moradas (parcelas 6 x 10 m en MARKER_Morada_<conjunto>_NNN).

Referencias: Cesky Krumlov y Toledo (casas apretadas y escalonadas), Mont-Saint-Michel (casas pegadas a un muro en
pendiente), Mala Strana (escaleras y galerias entre niveles).

Marco local de la parcela = el del marcador: centro de la parcela, +Y hacia la puerta (calle), x en [-3, 3],
y en [-5, 5]; la fachada esta retranqueada 2 m (y = 3) como en la etapa 06.

Tipos (propiedad 'tipo' del marcador):
  habitacion    casa comunal de 3 plantas (modulo de 6 m = una unidad), 3 puertas por planta, galerias corridas de
                madera y escalera exterior de dos tramos, <= 1,500 triangulos por modulo (con puertas y faroles)
  casa_pequena  una planta, patio delantero con muro bajo, cubierta a un agua o a dos aguas, chimenea, <= 2,000
  casa_grande   dos plantas, jardin trasero con muro, balcon, chimenea, cubierta a dos aguas, <= 3,500

Secciones escalonadas: el lado de la casa que mira a las puertas de la terraza vecina (desde CAM_Iso) se mantiene
bajo; build_stage23 decide la seccion de cada casa con una prueba de rayos (proxies) antes de construir.
Puerta exterior = objeto aparte DOOR_Morada (pintura por instancia, MARKER_Lantern + LANTERN_Shard, placa de numero
de 0.3 x 0.2 m); MARKER_Morada_Door delante de cada puerta y MARKER_TrophyCase dentro.
"""

import math
import random

from mathutils import Matrix, Vector

import bld_kit as K

FH = 3.2                         # altura de planta
YF = 3.0                         # fachada (retranqueo 2 m)
W = 6.0
HW = W / 2 - 0.005
ST, LIGHT, WOOD, IRON = "MAT_Limestone_Worn", "MAT_Limestone_Light", K.M_WOOD, K.M_IRON
WARM, SHARD, GRAY = K.M_WARM, K.M_SHARD, K.M_GRAY
WOOD_L = "MAT_Wood_Light"
LEAF, HERB = "MAT_Leaf_Old", "MAT_Herb_Green"
FACADES = ("MAT_Facade_Earth_A", "MAT_Facade_Earth_B", "MAT_Facade_Earth_C")
FACADE_FACTORS = {"MAT_Facade_Earth_A": (1.0, 0.89, 0.72), "MAT_Facade_Earth_B": (0.98, 0.84, 0.76),
                  "MAT_Facade_Earth_C": (0.90, 0.90, 0.81)}
PAINTS = {"MAT_Door_Paint_01": (0.62, 0.70, 0.60), "MAT_Door_Paint_02": (0.60, 0.70, 0.80),
          "MAT_Door_Paint_03": (0.72, 0.60, 0.56), "MAT_Door_Paint_04": (0.55, 0.50, 0.46),
          "MAT_Door_Paint_05": (0.76, 0.71, 0.61), "MAT_Door_Paint_06": (0.66, 0.62, 0.70)}
PLATE = "MAT_Door_NumberPlate"
BUDGET = {"habitacion": 1500, "casa_pequena": 2000, "casa_grande": 3500}
TYPES = ("habitacion", "casa_pequena", "casa_grande")


# --------------------------------------------------------------------------- materiales
def ensure_materials():
    import bpy
    out = {}
    for name, fac in FACADE_FACTORS.items():
        if name not in bpy.data.materials:
            _tint(LIGHT, name, fac, "fachada de las Moradas (tono tierra), caliza clara x baseColorFactor")
            out[name] = {"src": LIGHT, "baseColorFactor": fac}
    for name, fac in PAINTS.items():
        if name not in bpy.data.materials:
            _tint(WOOD_L, name, fac, "pintura de puerta (madera clara x baseColorFactor); en Godot se cambia por "
                                    "instancia (material_override)")
            out[name] = {"src": WOOD_L, "baseColorFactor": fac}
    if PLATE not in bpy.data.materials:
        m = bpy.data.materials.new(PLATE)
        m.use_nodes = True
        b = m.node_tree.nodes["Principled BSDF"]
        b.inputs["Base Color"].default_value = (0.69, 0.65, 0.56, 1)        # #D9D3C4 esmalte claro (decal encima)
        b.inputs["Roughness"].default_value = 0.4
        m["note"] = "placa de numero: plano 0.3 x 0.2 m con UV 0..1 para el decal del numero"
        out[PLATE] = {"color": "#D9D3C4"}
    return out


def _tint(src, name, fac, note):
    import bpy
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


# --------------------------------------------------------------------------- utilidades de geometria
def prism_yz(mb, prof, x0, x1, mat):
    """Perfil (y, z) extruido entre x0 y x1; tapas teseladas (perfiles concavos)."""
    _prism(mb, prof, x0, x1, mat, lambda a, b, s: (s, a, b))


def prism_xz(mb, prof, y0, y1, mat):
    """Perfil (x, z) extruido entre y0 e y1."""
    _prism(mb, prof, y0, y1, mat, lambda a, b, s: (a, s, b))


def _prism(mb, prof, s0, s1, mat, co):
    from mathutils.geometry import tessellate_polygon
    pts = []
    for p in prof:
        if not pts or abs(pts[-1][0] - p[0]) > 1e-6 or abs(pts[-1][1] - p[1]) > 1e-6:
            pts.append(p)
    if len(pts) > 2 and abs(pts[0][0] - pts[-1][0]) < 1e-6 and abs(pts[0][1] - pts[-1][1]) < 1e-6:
        pts.pop()
    mi = mb.mi(mat)
    tri = tessellate_polygon([[Vector((a, b, 0.0)) for a, b in pts]])
    caps = [[mb.v(co(a, b, s)) for a, b in pts] for s in (s0, s1)]
    for k, vs in enumerate(caps):
        for t in tri:
            try:
                f = mb.bm.faces.new([vs[i] for i in (t if k else t[::-1])])
                f.material_index = mi
            except ValueError:
                pass
    a, b = caps
    for i in range(len(pts)):
        j = (i + 1) % len(pts)
        try:
            f = mb.bm.faces.new([a[i], a[j], b[j], b[i]])
            f.material_index = mi
        except ValueError:
            pass


def window(mb, face_y, sgn, x, z0, w, h, shutters=True, mat_glass=WARM):
    """Ventana sin hueco (cristal 1.5 cm por delante), alfeizar y dintel de piedra, contraventanas."""
    y = face_y + sgn * 0.015
    mb.face([(x - w / 2, y, z0), (x + w / 2, y, z0), (x + w / 2, y, z0 + h), (x - w / 2, y, z0 + h)], mat_glass,
            nrm=(0, sgn, 0))
    ya, yb = sorted((face_y, face_y + sgn * 0.08))
    mb.box((x - w / 2 - 0.08, ya, z0 - 0.08), (x + w / 2 + 0.08, yb, z0), ST, skip=("y-",) if sgn > 0 else ("y+",))
    mb.box((x - w / 2 - 0.06, ya, z0 + h), (x + w / 2 + 0.06, yb, z0 + h + 0.14), ST, skip=("y-",) if sgn > 0 else ("y+",))
    if shutters:
        ys = face_y + sgn * 0.03
        for s in (-1, 1):
            xa, xb = sorted((x + s * w / 2, x + s * (w / 2 + w / 2 - 0.02)))
            mb.face([(xa, ys, z0), (xb, ys, z0), (xb, ys, z0 + h), (xa, ys, z0 + h)], WOOD, nrm=(0, sgn, 0))


def chimney(mb, x, y, z_base, top):
    mb.box((x - 0.32, y - 0.32, z_base), (x + 0.32, y + 0.32, top), ST, skip=("z-",))
    mb.box((x - 0.4, y - 0.4, top), (x + 0.4, y + 0.4, top + 0.12), LIGHT)
    mb.box((x - 0.12, y - 0.12, top + 0.12), (x + 0.12, y + 0.12, top + 0.4), GRAY, skip=("z-",))


def roof_lean(mb, x0, x1, y_low, z_low, y_high, z_high, rng, tone, hi_over=0.25, cap=True):
    """Cubierta a un agua de y_low (alero) a y_high (cumbrera), con aleros, sofito, tabica y caballete."""
    L = y_high - y_low
    sl = (z_high - z_low) / L
    d = 1 if y_high > y_low else -1
    ye, ze = y_low - d * 0.4, z_low - 0.4 * abs(sl)
    yh, zh = y_high + d * hi_over, z_high + hi_over * abs(sl)
    m0, m1 = K.M_ROOF, K.M_ROOF_B
    K.M_ROOF, K.M_ROOF_B = (m1, m0) if tone else (m0, m1)
    try:
        K._course_slope(mb, x0 - 0.3, x1 + 0.3, ye, yh, ze, zh, rng, detail=0)
    finally:
        K.M_ROOF, K.M_ROOF_B = m0, m1
    mb.face([(x0 - 0.3, ye, ze - 0.02), (x1 + 0.3, ye, ze - 0.02), (x1 + 0.3, yh, zh - 0.02), (x0 - 0.3, yh, zh - 0.02)],
            WOOD, nrm=(0, 0, -1))
    ya, yb = sorted((ye, ye + d * 0.05))
    mb.box((x0 - 0.3, ya, ze - 0.18), (x1 + 0.3, yb, ze), WOOD)
    if cap:
        ya, yb = sorted((yh - d * 0.3, yh + (0.12 if hi_over == 0 else 0.0)))
        mb.box((x0 - 0.3, ya, zh - 0.04), (x1 + 0.3, yb, zh + 0.14), K.M_ROOF_B if tone else K.M_ROOF)
    for x in (x0 - 0.3, x1 + 0.3):
        mb.rod((x, ye, ze + 0.03), (x, yh, zh + 0.03), 0.05, WOOD)

    def z_at(y):
        return z_low + (y - y_low) * sl
    return z_at


def roof_gable_x(mb, yb, yf, z_eave, pitch, rng, tone, body=None, facade=None):
    """Dos aguas con cumbrera paralela a la fachada (a lo largo de x) sobre y in [yb, yf]."""
    D = yf - yb
    ym = (yb + yf) / 2
    m0, m1 = K.M_ROOF, K.M_ROOF_B
    K.M_ROOF, K.M_ROOF_B = (m1, m0) if tone else (m0, m1)
    mb.push(Matrix.Translation((0, ym, z_eave)))
    try:
        rise = K.roof_gable(mb, W - 0.01, D, pitch=pitch, eave=0.35, rng=rng, detail=0, repairs=rng.randint(1, 2))
    finally:
        K.M_ROOF, K.M_ROOF_B = m0, m1
        mb.pop()
    if body is not None:
        body.push(Matrix.Translation((0, ym, z_eave)))
        K.gable_walls(body, W - 0.01, D, rise, t=0.3, mat=facade)
        body.pop()

    def z_at(y):
        return z_eave + rise * (1 - abs(y - ym) / (D / 2))
    return z_at, rise


# --------------------------------------------------------------------------- secciones
def section(tipo, plan):
    """Alturas (z_front, z_back) del cuerpo y del alero/cumbrera segun el plan de la casa.
    plan: {'floors', 'low_side' ('front' | 'back' | None), 'roof' ('lean' | 'gable')}."""
    f = plan["floors"]
    top = f * FH
    if plan["roof"] == "gable":
        return top, top
    low = plan["low_side"]
    if tipo == "habitacion":
        hi, lo = (top - 0.55 if low == "back" else top + 0.6), (FH + 0.4 if low == "back" else top)
        # la fachada (front) lleva las puertas de todas las plantas: nunca baja
        return (hi if low == "back" else top), (lo if low == "back" else hi)
    hi, lo = top + 1.1, top - 0.1
    return (lo, hi) if low == "front" else (hi, lo)


def building_y(tipo):
    return (-2.0 if tipo == "casa_grande" else -5.0), YF


# --------------------------------------------------------------------------- puerta (objeto aparte)
def door_mesh(mb):
    """DOOR_Morada: marco de piedra, hoja (material de pintura en la ranura 1), umbral. Origen en el suelo, en el
    plano de la fachada, +Y hacia fuera; hueco 1.0 x 2.2 m."""
    mb.box((-0.64, 0.0, 0.0), (-0.5, 0.07, 2.36), ST, skip=("y-", "z-"))
    mb.box((0.5, 0.0, 0.0), (0.64, 0.07, 2.36), ST, skip=("y-", "z-"))
    mb.box((-0.7, 0.0, 2.2), (0.7, 0.09, 2.45), ST, skip=("y-",))
    mb.box((-0.5, 0.0, 0.0), (0.5, 0.025, 2.2), "MAT_Door_Paint_01", skip=("y-", "z-", "x-", "x+", "z+"))
    mb.box((0.32, 0.025, 1.0), (0.4, 0.06, 1.12), IRON, skip=("y-", "z-"))                 # tirador
    mb.box((-0.6, 0.0, -0.05), (0.6, 0.3, 0.06), ST, skip=("z-", "y-"))


def plate_mesh(me):
    """Placa de numero: plano de 0.3 x 0.2 m, UV 0..1 (decal), mirando a +Y."""
    import bmesh
    bm = bmesh.new()
    uv = bm.loops.layers.uv.new("UVWorld")
    vs = [bm.verts.new(c) for c in ((-0.15, 0, -0.1), (0.15, 0, -0.1), (0.15, 0, 0.1), (-0.15, 0, 0.1))]
    f = bm.faces.new(vs)
    for lp, u in zip(f.loops, ((0, 0), (1, 0), (1, 1), (0, 1))):
        lp[uv].uv = u
    f.normal_update()
    if f.normal.y < 0:
        f.normal_flip()
    bm.to_mesh(me)
    bm.free()


def lantern_mesh(mb):
    """LANTERN_Shard (version ligera ~40 tris): brazo, sombrerete, base y esquirla azul. Sale hacia +Y."""
    mb.box((-0.025, 0.0, 0.0), (0.025, 0.42, 0.05), IRON, skip=("y-",))
    mb.box((-0.11, 0.27, -0.05), (0.11, 0.49, 0.0), IRON)
    mb.box((-0.12, 0.26, -0.4), (0.12, 0.5, -0.35), IRON)
    cy = 0.38
    top, bot = (0, cy, -0.07), (0, cy, -0.33)
    ring = [(0.07 * math.cos(a), cy + 0.07 * math.sin(a), -0.2) for a in [i * math.pi / 2 for i in range(4)]]
    for i in range(4):
        j = (i + 1) % 4
        mb.face([ring[i], ring[j], top], SHARD)
        mb.face([ring[j], ring[i], bot], SHARD)


# --------------------------------------------------------------------------- tipos
def doors_of(tipo, v, plan):
    """[(x, planta)] de las puertas exteriores."""
    if tipo == "habitacion":
        return [(x, f) for f in range(plan["floors"]) for x in (-2.0, 0.0, 2.0)]
    if tipo == "casa_pequena":
        return [((-1.2 if v % 2 else 1.2), 0)]
    return [((0.9 if v // 2 else -0.9), 0)]


def habitacion(body, roof, cm, v, facade, plan, rng):
    yb, yf = building_y("habitacion")
    zf, zb = section("habitacion", plan)
    prism_yz(body, [(yb, -0.6), (yf, -0.6), (yf, zf), (yb, zb)], -HW, HW, facade)
    prism_yz(cm, [(yb, -0.6), (yf, -0.6), (yf, zf), (yb, zb)], -HW, HW, GRAY)
    floors = plan["floors"]
    # zocalo y cornisas de planta en la fachada
    body.box((-HW, yf, -0.1), (HW, yf + 0.05, 0.55), ST, skip=("y-", "z-"))
    for f in range(1, floors):
        body.box((-HW, yf, f * FH - 0.12), (HW, yf + 0.06, f * FH + 0.02), ST, skip=("y-",))
    # ventanas en la trasera (solo donde la trasera tiene altura); la fachada lleva las 3 puertas por planta
    nb = max(1, int((zb - 0.4) // FH))
    for f in range(nb):
        for x in (-1.6, 1.6):
            window(body, yb, -1, x, f * FH + 1.2, 0.6, 0.9, shutters=(v % 2 == 0))
    # galerias corridas de madera (plantas 2 y 3) con mensulas y barandilla
    gal_d = 1.2
    for f in range(1, floors):
        z = f * FH
        body.box((-HW, yf, z - 0.14), (HW, yf + gal_d, z), WOOD_L)
        cm.box((-HW, yf, z - 0.14), (HW, yf + gal_d, z), GRAY)
        for x in (-2.6, 0.0, 2.6):
            body.rod((x, yf, z - 0.9), (x, yf + gal_d - 0.1, z - 0.14), 0.05, WOOD)
        yr = yf + gal_d - 0.06
        if v // 2 == 0:
            for x in (-2.9, -1.45, 0.0, 1.45, 2.9):
                body.box((x - 0.04, yr - 0.04, z), (x + 0.04, yr + 0.04, z + 1.0), WOOD, skip=("z-", "z+"))
            body.box((-HW, yr - 0.05, z + 0.95), (HW, yr + 0.05, z + 1.05), WOOD)
            body.box((-HW, yr - 0.02, z + 0.12), (HW, yr + 0.02, z + 0.2), WOOD, skip=("x-", "x+"))
        else:
            body.box((-HW, yr - 0.03, z + 0.1), (HW, yr + 0.03, z + 0.85), WOOD_L, skip=("x-", "x+"))
            body.box((-HW, yr - 0.06, z + 0.85), (HW, yr + 0.06, z + 0.98), WOOD)
        cm.box((-HW, yr - 0.05, z), (HW, yr + 0.05, z + 1.05), GRAY)
    # escalera exterior de dos tramos (en la franja y 4.2-5.0), lado segun variante
    if floors > 1:
        s = 1 if v % 2 == 0 else -1
        y0, y1 = yf + gal_d, 4.98
        n, run = 12, 2.75
        x_foot = s * 2.95
        up = -s                                                   # un solo sentido: diagonal a lo largo de la fachada
        for k in range(floors - 1):
            z0 = k * FH
            xa = x_foot + up * k * (run + 0.25)
            prof = [(xa, z0 - 0.25)]
            for i in range(n):
                xi = xa + up * run * i / n
                prof += [(xi, z0 + FH * i / n), (xi, z0 + FH * (i + 1) / n)]
            xe = xa + up * run
            prof += [(xe, z0 + FH), (xe, z0 + FH - 0.25)]
            if k == 0:
                prof.append((xa + up * 0.3, z0 - 0.25))
            prism_xz(body, prof, y0, y1, WOOD_L if k else ST)
            body.rod((xa, y1 - 0.03, z0 + 0.95), (xe, y1 - 0.03, z0 + FH + 0.95), 0.035, WOOD)
            prism_xz(cm, [(xa, z0 - 0.25), (xe, z0 + FH - 0.02), (xe, z0 + FH - 0.3), (xa, z0 - 0.3)], y0, y1, GRAY)
            if k < floors - 2:                                   # rellano junto a la galeria entre tramos
                xl0, xl1 = sorted((xe, xe + up * 0.25))
                body.box((xl0, y0, z0 + FH - 0.14), (xl1, y1, z0 + FH), WOOD_L)
                cm.box((xl0, y0, z0 + FH - 0.14), (xl1, y1, z0 + FH), GRAY)

    # cubierta: a un agua, la cumbrera en el lado alto (hiladas de un solo tramo: presupuesto del modulo)
    seg0 = K.TILE_SEG
    K.TILE_SEG = 7.0
    try:
        if zf >= zb:
            z_at = roof_lean(roof, -HW, HW, yb, zb, yf, zf, rng, v % 2)
        else:
            z_at = roof_lean(roof, -HW, HW, yf, zf, yb, zb, rng, v % 2)
    finally:
        K.TILE_SEG = seg0
    if plan["low_side"] != "back":
        # la seccion escalonada (trasera baja) va pegada a la linea de vision de CAM_Iso: sin chimenea (el pedido no
        # la exige en la casa comunal); en las demas, chimenea en la mitad delantera
        cx = (-1.8, 1.8, -0.6, 0.6)[v]
        cy = yf - 1.2
        chimney(roof, cx, cy, z_at(cy) - 0.4, max(zf, zb) + 1.1)
    return {"z_front": zf, "z_back": zb, "yb": yb, "yf": yf}


def casa_pequena(body, roof, cm, v, facade, plan, rng):
    yb, yf = building_y("casa_pequena")
    zf, zb = section("casa_pequena", plan)
    if plan["roof"] == "gable":
        zf = zb = FH
        prism_yz(body, [(yb, -0.6), (yf, -0.6), (yf, zf), (yb, zb)], -HW, HW, facade)
        z_at, rise = roof_gable_x(roof, yb, yf, FH, 30.0, rng, v % 2, body=body, facade=facade)
        ztop = FH + rise
        prism_yz(cm, [(yb, -0.6), (yf, -0.6), (yf, FH), ((yb + yf) / 2, ztop), (yb, FH)], -HW, HW, GRAY)
    else:
        prism_yz(body, [(yb, -0.6), (yf, -0.6), (yf, zf), (yb, zb)], -HW, HW, facade)
        prism_yz(cm, [(yb, -0.6), (yf, -0.6), (yf, zf), (yb, zb)], -HW, HW, GRAY)
        z_at = (roof_lean(roof, -HW, HW, yb, zb, yf, zf, rng, v % 2) if zf >= zb else
                roof_lean(roof, -HW, HW, yf, zf, yb, zb, rng, v % 2))
        ztop = max(zf, zb)
    body.box((-HW, yf, -0.1), (HW, yf + 0.05, 0.5), ST, skip=("y-", "z-"))
    dx = doors_of("casa_pequena", v, plan)[0][0]
    for x in (-dx * 0.2 - math.copysign(1.0, dx) * 0.9, -dx * 1.1):
        if abs(x) < 2.6:
            window(body, yf, 1, x, 1.0, 0.8, 1.05)
    window(body, yb, -1, 0.0, 1.1, 0.7, 0.9, shutters=v // 2 == 1)
    # patio delantero con muro bajo (puerta del patio delante de la puerta)
    hwall = 0.9 if v // 2 == 0 else 1.1
    mat = ST if v // 2 == 0 else LIGHT
    gate = (dx - 0.65, dx + 0.65)
    for xa, xb in ((-HW, gate[0]), (gate[1], HW)):
        if xb - xa > 0.05:
            body.box((xa, 4.75, -0.2), (xb, 4.98, hwall), mat, skip=("z-",))
            body.box((xa - 0.02, 4.72, hwall), (xb + 0.02, 5.0, hwall + 0.07), LIGHT)
            cm.box((xa, 4.75, -0.2), (xb, 4.98, hwall), GRAY)
    for x in (-HW + 0.12, HW - 0.12):
        body.box((x - 0.12, yf, -0.2), (x + 0.12, 4.75, hwall), mat, skip=("z-",))
        cm.box((x - 0.12, yf, -0.2), (x + 0.12, 4.75, hwall), GRAY)
    for x in gate:                                                          # pilares de la cancela
        body.box((x - 0.14, 4.72, -0.2), (x + 0.14, 5.0, hwall + 0.25), LIGHT, skip=("z-",))
    # banco y maceta en el patio
    bx = -dx * 1.4
    body.box((bx - 0.6, 3.25, 0.0), (bx + 0.6, 3.6, 0.45), WOOD_L, skip=("z-",))
    mx = bx + 1.25 if abs(bx + 1.25) < 2.6 else bx - 1.25
    body.cylinder(0.22, 0.0, 0.45, 6, ST, r1=0.28, caps=True, center=(mx, 4.35))            # maceta
    import stage21_razas as R
    R.blob(body, mx, 4.35, 0.75, 0.3, 0.3, HERB, rng, seg=5, rings=1)
    cx = (-1.6, 1.6, 1.0, -1.0)[v]
    cy = yf - 1.5
    chimney(roof, cx, cy, z_at(cy) - 0.4, ztop + 0.9)
    return {"z_front": zf, "z_back": zb, "yb": yb, "yf": yf, "ztop": ztop}


def casa_grande(body, roof, cm, v, facade, plan, rng):
    yb, yf = building_y("casa_grande")
    floors = plan["floors"]
    top = floors * FH
    pitch = plan.get("pitch", 32.0)
    if plan["roof"] == "catslide":
        # Mont-Saint-Michel: faldon trasero largo que baja hasta 3.8 m (no tapa las puertas de la terraza vecina)
        ym = (yb + yf) / 2
        rise = (yf - ym) * math.tan(math.radians(pitch))
        zr, zbk = top + rise, FH + 0.6
        prof = [(yb, -0.6), (yf, -0.6), (yf, top), (ym, zr), (yb, zbk)]
        prism_yz(body, prof, -HW, HW, facade)
        prism_yz(cm, prof, -HW, HW, GRAY)
        roof_lean(roof, -HW, HW, yf, top, ym, zr, rng, v % 2, hi_over=0.0)
        roof_lean(roof, -HW, HW, yb, zbk, ym, zr, rng, v % 2, hi_over=0.0, cap=False)

        def z_at(y):
            return zr - (zr - top) * (y - ym) / (yf - ym) if y >= ym else zr - (zr - zbk) * (ym - y) / (ym - yb)
    else:
        prism_yz(body, [(yb, -0.6), (yf, -0.6), (yf, top), (yb, top)], -HW, HW, facade)
        z_at, rise = roof_gable_x(roof, yb, yf, top, pitch, rng, v % 2, body=body, facade=facade)
        prism_yz(cm, [(yb, -0.6), (yf, -0.6), (yf, top), ((yb + yf) / 2, top + rise), (yb, top)], -HW, HW, GRAY)
    body.box((-HW, yf, -0.1), (HW, yf + 0.05, 0.6), ST, skip=("y-", "z-"))
    body.box((-HW, yf, FH - 0.12), (HW, yf + 0.06, FH + 0.03), ST, skip=("y-",))
    for x in (-HW + 0.15, HW - 0.15):                                       # esquinas de sillares
        body.box((x - 0.18, yf - 0.02, 0.0), (x + 0.18, yf + 0.04, top), LIGHT, skip=("y-", "z-"))
    dx = doors_of("casa_grande", v, plan)[0][0]
    window(body, yf, 1, -dx * 1.9 if abs(dx * 1.9) < 2.4 else -dx, 1.0, 0.8, 1.2)
    window(body, yf, 1, -dx * 1.9 if abs(dx * 1.9) < 2.4 else -dx, FH + 1.0, 0.8, 1.2)
    # balcon de la planta 2 con puerta-ventana
    bx = dx
    window(body, yf, 1, bx, FH + 0.1, 0.9, 2.0, shutters=True)
    if v % 2 == 0:
        body.box((bx - 1.2, yf, FH - 0.12), (bx + 1.2, yf + 0.9, FH + 0.02), WOOD_L)
        for x in (bx - 1.15, bx - 0.4, bx + 0.4, bx + 1.15):
            body.box((x - 0.035, yf + 0.82, FH), (x + 0.035, yf + 0.88, FH + 1.0), WOOD, skip=("z-", "z+"))
        body.box((bx - 1.2, yf + 0.8, FH + 0.95), (bx + 1.2, yf + 0.9, FH + 1.05), WOOD)
        for x in (bx - 1.0, bx + 1.0):
            body.rod((x, yf, FH - 0.8), (x, yf + 0.8, FH - 0.12), 0.05, WOOD)
    else:
        body.box((bx - 1.2, yf, FH - 0.18), (bx + 1.2, yf + 0.8, FH), ST)
        body.box((bx - 1.2, yf + 0.65, FH), (bx + 1.2, yf + 0.8, FH + 0.95), ST, skip=("z-",))
        body.box((bx - 1.25, yf + 0.62, FH + 0.95), (bx + 1.25, yf + 0.83, FH + 1.05), LIGHT)
        for x in (bx - 0.9, bx + 0.9):
            body.prism([(x - 0.12, FH - 0.18), (x + 0.12, FH - 0.18), (x, FH - 0.7)], yf, yf + 0.6, ST)
    cm.box((bx - 1.2, yf, FH - 0.18), (bx + 1.2, yf + 0.9, FH + 1.05), GRAY)
    window(body, yb, -1, 0.0, 1.0, 0.8, 1.1)
    if plan["roof"] != "catslide":
        window(body, yb, -1, -1.4 if v // 2 else 1.4, FH + 1.0, 0.8, 1.1)
    # jardin trasero con muro (1.8 m) y arbol o arbustos
    zw = 1.8
    for lo, hi in (((-HW, -5.0, -0.3), (HW, -4.75, zw)), ((-HW, -4.75, -0.3), (-HW + 0.25, yb, zw)),
                   ((HW - 0.25, -4.75, -0.3), (HW, yb, zw))):
        body.box(lo, hi, ST if v % 2 else LIGHT, skip=("z-",))
        body.box((lo[0] - 0.03, lo[1] - 0.03, zw), (hi[0] + 0.03, hi[1] + 0.03, zw + 0.08), LIGHT)
        cm.box(lo, hi, GRAY)
    tx, ty = (-1.4 if v // 2 else 1.4), -3.5
    if v in (0, 3):
        body.cylinder(0.14, 0.0, 2.2, 6, WOOD, r1=0.1, caps=False, center=(tx, ty))
        import stage21_razas as R
        R.blob(body, tx, ty, 3.0, 1.4, 1.0, LEAF, rng, seg=6, rings=2)
    else:
        import stage21_razas as R
        for k in range(3):
            R.blob(body, tx + (k - 1) * 0.9, ty + rng.uniform(-0.3, 0.3), 0.45, 0.5, 0.45, HERB, rng, seg=5, rings=1)
    cx = (1.9, -1.9, 1.9, -1.9)[v]
    cyc = yf - 0.6                      # en el faldon delantero, baja: no corta la linea de vision de la terraza vecina
    chimney(roof, cx, cyc, z_at(cyc) - 0.4, top + rise + 0.45)
    return {"z_front": top, "z_back": (FH + 0.6) if plan["roof"] == "catslide" else top, "yb": yb, "yf": yf,
            "ztop": top + rise, "catslide": plan["roof"] == "catslide"}


BUILDERS = {"habitacion": habitacion, "casa_pequena": casa_pequena, "casa_grande": casa_grande}


def lod2(mb, tipo, plan, info):
    """LOD2 (~10 %): caja con tejado (losa con vuelos), chimenea y las piezas que cambian la silueta (galerias y
    escalera, balcon, muros de patio y de jardin); un material plano."""
    yb, yf = info["yb"], info["yf"]
    zf, zb = info["z_front"], info["z_back"]
    if plan["roof"] == "gable":
        zt = info["ztop"]
        prism_yz(mb, [(yb, -0.3), (yf, -0.3), (yf, zf), ((yb + yf) / 2, zt), (yb, zb)], -HW, HW, GRAY)
        ym = (yb + yf) / 2
        for ya, za in ((yb - 0.35, zb - 0.2), (yf + 0.35, zf - 0.2)):
            prism_yz(mb, [(ya, za), (ym, zt + 0.05), (ym, zt + 0.2), (ya, za + 0.15)], -HW - 0.3, HW + 0.3, GRAY)
    elif info.get("catslide"):
        ym = (yb + yf) / 2
        zt = info["ztop"]
        prism_yz(mb, [(yb, -0.3), (yf, -0.3), (yf, zf), (ym, zt), (yb, zb)], -HW, HW, GRAY)
        for ya, za in ((yb - 0.35, zb - 0.2), (yf + 0.35, zf - 0.2)):
            prism_yz(mb, [(ya, za), (ym, zt + 0.05), (ym, zt + 0.2), (ya, za + 0.15)], -HW - 0.3, HW + 0.3, GRAY)
    else:
        prism_yz(mb, [(yb, -0.3), (yf, -0.3), (yf, zf), (yb, zb)], -HW, HW, GRAY)
        sl = (zf - zb) / (yf - yb)
        prism_yz(mb, [(yb - 0.4, zb - 0.4 * sl), (yf + 0.3, zf + 0.3 * sl), (yf + 0.3, zf + 0.3 * sl + 0.18),
                      (yb - 0.4, zb - 0.4 * sl + 0.18)], -HW - 0.3, HW + 0.3, GRAY)
    zc = max(zf, zb, info.get("ztop", 0.0))
    mb.box((-0.3, (yb + yf) / 2 - 0.3, zc - 0.5), (0.3, (yb + yf) / 2 + 0.3, zc + 0.8), GRAY)
    if tipo == "habitacion" and plan["floors"] > 1:
        for f in range(1, plan["floors"]):
            mb.box((-HW, yf, f * FH - 0.15), (HW, yf + 1.2, f * FH + 1.0), GRAY)
        mb.box((-HW, yf + 1.2, 0.0), (HW, 4.98, (plan["floors"] - 1) * FH), GRAY)
    if tipo == "casa_pequena":
        mb.box((-HW, 4.75, 0.0), (HW, 4.98, 1.0), GRAY)
    if tipo == "casa_grande":
        mb.box((-1.2, yf, FH - 0.15), (1.2, yf + 0.9, FH + 1.0), GRAY)
        mb.box((-HW, -5.0, 0.0), (HW, -4.75, 1.85), GRAY)


def proxy_parts(tipo, plan):
    """Envolventes (cajas y prismas) en coordenadas locales para la prueba de oclusion: [(perfil yz, x0, x1)] y
    cajas [(lo, hi)]."""
    yb, yf = building_y(tipo)
    profs, boxes = [], []
    if tipo == "casa_grande" and plan["roof"] == "catslide":
        top = plan["floors"] * FH
        ym = (yb + yf) / 2
        rise = (yf - ym) * math.tan(math.radians(plan.get("pitch", 32.0)))
        profs.append(([(yb - 0.4, FH + 0.4), (yb, -0.6), (yf, -0.6), (yf + 0.4, top - 0.25), (ym, top + rise + 0.2)],
                      -HW - 0.3, HW + 0.3))
        boxes.append(((-HW, -5.0, 0.0), (HW, yb, 1.9)))
        boxes.append(((-1.3, yf, FH - 0.2), (1.3, yf + 0.9, FH + 1.05)))
    elif tipo == "casa_grande":
        top = plan["floors"] * FH
        rise = (yf - yb) / 2 * math.tan(math.radians(plan.get("pitch", 32.0)))
        profs.append(([(yb - 0.35, top - 0.2), (yb, -0.6), (yf, -0.6), (yf + 0.35, top - 0.2), ((yb + yf) / 2, top + rise)],
                      -HW - 0.35, HW + 0.35))
        boxes.append(((-HW, -5.0, 0.0), (HW, yb, 1.9)))
        boxes.append(((-1.3, yf, FH - 0.2), (1.3, yf + 0.9, FH + 1.05)))
    elif tipo == "casa_pequena" and plan["roof"] == "gable":
        rise = (yf - yb) / 2 * math.tan(math.radians(30.0))
        profs.append(([(yb - 0.35, FH - 0.2), (yb, -0.6), (yf, -0.6), (yf + 0.35, FH - 0.2), ((yb + yf) / 2, FH + rise)],
                      -HW - 0.35, HW + 0.35))
    else:
        zf, zb = section(tipo, plan)
        sl = (zf - zb) / (yf - yb)
        profs.append(([(yb - 0.4, zb - 0.4 * sl), (yb, -0.6), (yf, -0.6), (yf + 0.4, zf + 0.4 * sl)], -HW - 0.3, HW + 0.3))
    if tipo == "habitacion" and plan["floors"] > 1:
        boxes.append(((-HW, yf, FH - 0.15), (HW, yf + 1.2, (plan["floors"] - 1) * FH + 1.05)))
        boxes.append(((-HW, yf + 1.2, 0.0), (HW, 4.98, (plan["floors"] - 1) * FH + 1.0)))
    if tipo == "casa_pequena":
        boxes.append(((-HW, 4.72, 0.0), (HW, 5.0, 1.2)))
    return profs, boxes


_ = random
