"""
CONCORDIA - Etapa 16: hitos NO y SE de la plaza.

  SANTUARIO DEL RETORNO (MARKER_Santuario, pad 16 x 12): capilla esbelta tipo Sainte-Chapelle en caliza clara
    (MAT_Limestone_Light), nave de 9 m a los hombros, cubierta a dos aguas de teja ocre (cumbrera 14 m) con flecha,
    5 ventanales de 1.4 x 6 m en el lado trasero y 4 (2+2) en el delantero, contrafuertes con pinaculos, puerta de doble
    hoja bajo un porche de hastial (gablete) a +Y, rosetones en los hastiales, farolillos de esquirla, SANTUARIO_Well.
  SALON DE LAS HAZANAS (MARKER_SalonHazanas, pad 42 x 16): nave larga tipo Westminster Hall en piedra gris, muros de
    8 m, cumbrera 15 m, contrafuertes cada 6 m, 6 ventanas altas por lado, cabezas de los pares (hammerbeam) vistas
    bajo los aleros, hastial transversal a +Y con gran portal en arco y ventanal alto, 10 nichos con estatuas sin
    rostro (props instanciados) y placas de bronce junto a la puerta, linterna de cumbrera.

Convencion de marcos de muro: frame(side) -> Matrix; en ese marco u = a lo largo del muro, y = 0 en la cara
exterior y +y hacia fuera, z = altura sobre el pad. +Y local del edificio = door_direction (hacia la plaza).
"""

import math
import os
import random

import bpy  # noqa: I001  (bpy antes que bmesh con el modulo pip)
import bmesh
from mathutils import Matrix, Vector

import bld_kit as K
import stage13_portal as P13

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))

SEED_SANT, SEED_SALON = 1601, 1602
M_LIGHT = "MAT_Limestone_Light"
M_STONE = "MAT_Limestone_Worn"
M_GRAY = "MAT_Wall_Gray"
M_GLASS = "MAT_Stained_Glass_Blue"
M_BRONZE = "MAT_Bronze_Aged"
M_WOOD, M_IRON, M_ROOF, M_ROOF_B = K.M_WOOD, K.M_IRON, K.M_ROOF, K.M_ROOF_B
M_REPAIR, M_SHARD, M_WATER = K.M_REPAIR, K.M_SHARD, "MAT_Water"


# ---------------------------------------------------------------------------
# materiales
# ---------------------------------------------------------------------------
def _lin(c):
    return ((c + 0.055) / 1.055) ** 2.4 if c > 0.04045 else c / 12.92


def ensure_materials():
    out = {}
    if M_LIGHT not in bpy.data.materials:
        import numpy as np
        from PIL import Image
        src = bpy.data.materials[M_STONE]
        img = src.node_tree.nodes["Albedo"].image
        a = np.asarray(Image.open(bpy.path.abspath(img.filepath)).convert("RGB")).astype(np.float32) / 255.0
        # aclarar conservando el detalle: "screen" hacia el blanco (k = 0.62) y algo menos de saturacion
        b = 1.0 - (1.0 - a) * 0.62
        g = b.mean(axis=2, keepdims=True)
        b = g + (b - g) * 0.8
        d = os.path.join(REPO, "textures", "concordia", M_LIGHT)
        os.makedirs(d, exist_ok=True)
        p = os.path.join(d, "concordia_limestone_light_albedo.png")
        Image.fromarray((np.clip(b, 0, 1) * 255 + 0.5).astype(np.uint8)).save(p, optimize=True)
        m = src.copy()
        m.name = M_LIGHT
        im = bpy.data.images.load(p, check_existing=True)
        im.colorspace_settings.name = "sRGB"
        m.node_tree.nodes["Albedo"].image = im
        m["note"] = ("MAT_Limestone_Worn con albedo aclarado y horneado (media sRGB %.3f -> %.3f); mismo ORM y normal"
                     % (float(a.mean()), float(b.mean())))
        out[M_LIGHT] = {"albedo": os.path.relpath(p, REPO), "mean_srgb_before": round(float(a.mean()), 3),
                        "mean_srgb_after": round(float(b.mean()), 3)}
    if M_GLASS not in bpy.data.materials:
        m = bpy.data.materials.new(M_GLASS)
        m.use_nodes = True
        bs = m.node_tree.nodes["Principled BSDF"]
        bs.inputs["Base Color"].default_value = (_lin(0.31), _lin(0.50), _lin(0.68), 1)      # #4F7FAE
        bs.inputs["Roughness"].default_value = 0.18
        bs.inputs["Emission Color"].default_value = (_lin(0.49), _lin(0.71), _lin(0.90), 1)  # #7DB4E6 azul palido
        bs.inputs["Emission Strength"].default_value = 0.6
        m["note"] = "vitral azul palido, emision baja 0.6 (opaco: el interior va aparte)"
        out[M_GLASS] = "creado"
    if M_BRONZE not in bpy.data.materials:
        m = bpy.data.materials.new(M_BRONZE)
        m.use_nodes = True
        bs = m.node_tree.nodes["Principled BSDF"]
        bs.inputs["Base Color"].default_value = (_lin(0.451), _lin(0.391), _lin(0.298), 1)  # #73644C bronce viejo (sat 0.34)
        bs.inputs["Metallic"].default_value = 0.85
        bs.inputs["Roughness"].default_value = 0.5
        m["note"] = "bronce envejecido (placas del Salon), sin textura"
        out[M_BRONZE] = "creado"
    return out


# ---------------------------------------------------------------------------
# utilidades de geometria
# ---------------------------------------------------------------------------
def frame(side, X, Y):
    if side == "+Y":
        return Matrix.Translation((0, Y, 0))
    if side == "-Y":
        return Matrix.Translation((0, -Y, 0)) @ Matrix.Rotation(math.pi, 4, "Z")
    if side == "+X":
        return Matrix.Translation((X, 0, 0)) @ Matrix.Rotation(-math.pi / 2, 4, "Z")
    return Matrix.Translation((-X, 0, 0)) @ Matrix.Rotation(math.pi / 2, 4, "Z")


def frame_rot(side):
    return {"+Y": 0.0, "-Y": math.pi, "+X": -math.pi / 2, "-X": math.pi / 2}[side]


def pointed(x0, x1, zs, n=5):
    """Arco apuntado equilatero de (x0, zs) a (x1, zs) pasando por la clave (flecha 0.866 * luz)."""
    w = x1 - x0
    pts = [(x1 + w * math.cos(math.pi - (math.pi / 3) * i / n), zs + w * math.sin(math.pi - (math.pi / 3) * i / n))
           for i in range(n + 1)]
    pts += [(x0 + w * math.cos((math.pi / 3) * (1 - i / n)), zs + w * math.sin((math.pi / 3) * (1 - i / n)))
            for i in range(1, n + 1)]
    return pts


def lancet(uc, w, z0, ztop, n=5):
    """Hueco apuntado de luz w, alfeizar z0 y clave ztop: poligono X-Z."""
    zs = ztop - 0.866 * w
    return [(uc - w / 2, z0)] + pointed(uc - w / 2, uc + w / 2, zs, n) + [(uc + w / 2, z0)]


def circle(uc, zc, r, n=16):
    return [(uc + r * math.cos(2 * math.pi * i / n), zc + r * math.sin(2 * math.pi * i / n)) for i in range(n)]


def _area(poly):
    return 0.5 * sum(poly[i][0] * poly[(i + 1) % len(poly)][1] - poly[(i + 1) % len(poly)][0] * poly[i][1]
                     for i in range(len(poly)))


def with_door(x0, x1, door, top_right_to_left):
    """Contorno de muro con una puerta que llega al suelo: la puerta se empalma en el borde inferior."""
    return [(x0, 0.0)] + door + [(x1, 0.0)] + top_right_to_left


def plate(mb, outer, holes, t, mat, reveal_mat=None, back=True):
    """Muro en el marco actual: cara exterior en y = 0, interior en y = -t, con huecos (poligonos convexos X-Z).
    Todas las caras se orientan explicitamente (no depende del recalculo de normales)."""
    for yy, s in ((0.0, 1), (-t, -1)):
        if s < 0 and not back:
            continue
        es = []
        for poly in [outer] + holes:
            vs = [mb.bm.verts.new(mb.M @ Vector((x, yy, z))) for x, z in poly]
            es += [mb.bm.edges.new((vs[i], vs[(i + 1) % len(vs)])) for i in range(len(vs))]
        r = bmesh.ops.triangle_fill(mb.bm, use_beauty=True, use_dissolve=False, edges=es)
        tgt = (mb.M.to_3x3() @ Vector((0, s, 0))).normalized()
        for f in [g for g in r["geom"] if isinstance(g, bmesh.types.BMFace)]:
            f.material_index = mb.mi(mat)
            f.normal_update()
            if f.normal.dot(tgt) < 0:
                f.normal_flip()
    for poly, is_hole in [(outer, False)] + [(h, True) for h in holes]:
        sg = (1.0 if _area(poly) > 0 else -1.0) * (-1.0 if is_hole else 1.0)
        n = len(poly)
        for i in range(n):
            (xa, za), (xb, zb) = poly[i], poly[(i + 1) % n]
            nx, nz = sg * (zb - za), -sg * (xb - xa)
            mb.face([(xa, 0.0, za), (xb, 0.0, zb), (xb, -t, zb), (xa, -t, za)],
                    (reveal_mat or mat) if is_hole else mat, nrm=(nx, 0, nz))


def rod_path(mb, pts2d, y, r, mat, closed=False):
    """Varillas (tracerias, molduras) siguiendo una polilinea del plano X-Z a profundidad y."""
    n = len(pts2d)
    for i in range(n if closed else n - 1):
        (xa, za), (xb, zb) = pts2d[i], pts2d[(i + 1) % n]
        mb.rod((xa, y, za), (xb, y, zb), r, mat)


def tri_face(mb, a, b, c, mat, nrm):
    mb.face([a, b, c], mat, nrm=nrm)


def wedge_top(mb, u0, u1, y0, y1, z0, z1, mat):
    """Remate inclinado (vierteaguas) de un contrafuerte: de (y1, z0) delante a (y0, z1) atras."""
    mb.face([(u0, y1, z0), (u1, y1, z0), (u1, y0, z1), (u0, y0, z1)], mat, nrm=(0, 1, 1))
    tri_face(mb, (u0, y1, z0), (u0, y0, z1), (u0, y0, z0), mat, (-1, 0, 0))
    tri_face(mb, (u1, y1, z0), (u1, y0, z0), (u1, y0, z1), mat, (1, 0, 0))


def pinnacle(mb, u, y, z0, s, h_shaft, h_spire, mat):
    mb.box((u - s / 2, y - s / 2, z0), (u + s / 2, y + s / 2, z0 + h_shaft), mat, skip=("z-",))
    top = (u, y, z0 + h_shaft + h_spire)
    c = [(u - s / 2, y - s / 2), (u + s / 2, y - s / 2), (u + s / 2, y + s / 2), (u - s / 2, y + s / 2)]
    for i in range(4):
        (xa, ya), (xb, yb) = c[i], c[(i + 1) % 4]
        mx, my = (xa + xb) / 2 - u, (ya + yb) / 2 - y
        tri_face(mb, (xa, ya, z0 + h_shaft), (xb, yb, z0 + h_shaft), top, mat, (mx, my, 0.4))


def window_fill(mb, uc, w, z0, ztop, y_glass, lights, mat_tr, r_tr=0.045, rose=True, bars=0, glass=None, arc_n=3):
    """Vitral + traceria dentro de un hueco apuntado: parteluces, arcos de cada luz, oculo en la cabeza y barras de
    hierro (saddle bars). glass: material del vidrio (por defecto el vitral azul)."""
    poly = lancet(uc, w, z0, ztop)
    mb.face([(x, y_glass, z) for x, z in poly], glass or M_GLASS, nrm=(0, 1, 0))
    zs = ztop - 0.866 * w
    y = y_glass + r_tr + 0.005
    if lights > 1:
        lw = w / lights
        for k in range(1, lights):
            u = uc - w / 2 + lw * k
            mb.box((u - r_tr * 1.4, y_glass, z0), (u + r_tr * 1.4, y_glass + 2 * r_tr + 0.01, zs), mat_tr, skip=("y-",))
        for k in range(lights):
            a, b = uc - w / 2 + lw * k, uc - w / 2 + lw * (k + 1)
            rod_path(mb, pointed(a, b, zs, n=arc_n), y, r_tr, mat_tr)
        if rose:
            apex_sub = zs + 0.866 * lw
            zc = (apex_sub + ztop) / 2 - 0.02
            rr = min(0.3 * w / 2 * 1.5, (ztop - apex_sub) * 0.38)
            rod_path(mb, circle(uc, zc, rr, n=8), y, r_tr, mat_tr, closed=True)
    for k in range(bars):
        z = z0 + (zs - z0) * (k + 1) / (bars + 1)
        mb.box((uc - w / 2, y_glass + 0.02, z - 0.012), (uc + w / 2, y_glass + 0.05, z + 0.012), M_IRON, skip=("x-", "x+"))
    # alfeizar
    mb.box((uc - w / 2 - 0.08, -0.02, z0 - 0.14), (uc + w / 2 + 0.08, 0.12, z0), mat_tr)


def rose_fill(mb, uc, zc, r, y_glass, mat_tr, spokes=8, r_tr=0.05):
    mb.face([(x, y_glass, z) for x, z in circle(uc, zc, r, 16)], M_GLASS, nrm=(0, 1, 0))
    y = y_glass + r_tr + 0.005
    ri = r * 0.32
    rod_path(mb, circle(uc, zc, ri, spokes), y, r_tr, mat_tr, closed=True)
    for k in range(spokes):
        a = 2 * math.pi * k / spokes
        mb.rod((uc + ri * math.cos(a), y, zc + ri * math.sin(a)), (uc + r * math.cos(a), y, zc + r * math.sin(a)), r_tr,
               mat_tr)
    rod_path(mb, circle(uc, zc, r + 0.06, 16), 0.04, 0.07, mat_tr, closed=True)     # moldura exterior


def door_leaves(mb, w, ztop, y0, y1, straps=3):
    """Puerta de doble hoja apuntada en madera oscura con bisagras de banda y aldabas de hierro."""
    zs = ztop - 0.866 * w
    pts = pointed(-w / 2, w / 2, zs, n=6)
    g = 0.006
    left = [(-w / 2, 0.0)] + [(min(x, -g), z) for x, z in pts[:7]] + [(-g, 0.0)]
    right = [(g, 0.0)] + [(max(x, g), z) for x, z in pts[6:]] + [(w / 2, 0.0)]
    for poly in (left, right):
        mb.prism(poly, y0, y1, M_WOOD)
    for s in (-1, 1):
        for k in range(straps):
            z = 0.45 + (zs - 0.6) * k / max(1, straps - 1)
            x0, x1 = (-w / 2 + 0.03, -0.12) if s < 0 else (0.12, w / 2 - 0.03)
            mb.box((x0, y1, z - 0.05), (x1, y1 + 0.018, z + 0.05), M_IRON, skip=("y-",))
        cx = s * 0.22
        ring = [(cx - 0.09, 1.25), (cx, 1.16), (cx + 0.09, 1.25), (cx, 1.34)]
        rod_path(mb, ring, y1 + 0.04, 0.012, M_IRON, closed=True)


def buttress(mb, u, w, d, z1, d2, z2, mat, cap_h=0.5):
    """Contrafuerte de dos cuerpos con vierteaguas: (0..d) hasta z1, (0..d2) hasta z2. Devuelve la cara superior."""
    mb.box((u - w / 2, 0.0, 0.0), (u + w / 2, d, z1), mat, skip=("y-", "z+"))
    wedge_top(mb, u - w / 2, u + w / 2, d2, d, z1, z1 + cap_h, mat)
    mb.box((u - w / 2, 0.0, z1), (u + w / 2, d2, z2), mat, skip=("y-", "z-", "z+"))
    wedge_top(mb, u - w / 2, u + w / 2, 0.0, d2, z2, z2 + cap_h, mat)
    return z2 + cap_h


def buttress_niche(mb, u, w, d, z1, d2, z2, mat, back_mat, nw=0.78, nz0=1.4, ntop=4.0, cap_h=0.45, t=0.42):
    """Contrafuerte con hornacina rehundida en su cara frontal (nada sobresale del contrafuerte). Devuelve el apoyo
    de la estatua."""
    mb.box((u - w / 2, 0.0, 0.0), (u + w / 2, d - t, z1), mat, skip=("y-", "y+", "z+"))
    mb.push(Matrix.Translation((0, d, 0)))
    hole = lancet(u, nw, nz0, ntop)
    plate(mb, [(u - w / 2, 0), (u + w / 2, 0), (u + w / 2, z1), (u - w / 2, z1)], [hole], t, mat, back=False)
    mb.face([(x, -t + 0.02, z) for x, z in hole], back_mat, nrm=(0, 1, 0))
    mb.box((u - nw / 2 - 0.05, -0.06, nz0 - 0.12), (u + nw / 2 + 0.05, 0.08, nz0), mat)
    rod_path(mb, pointed(u - nw / 2 - 0.1, u + nw / 2 + 0.1, ntop + 0.12 - 0.866 * (nw + 0.2), 3), 0.03, 0.045, mat)
    mb.pop()
    wedge_top(mb, u - w / 2, u + w / 2, d2, d, z1, z1 + cap_h, mat)
    mb.box((u - w / 2, 0.0, z1), (u + w / 2, d2, z2), mat, skip=("y-", "z-", "z+"))
    wedge_top(mb, u - w / 2, u + w / 2, 0.0, d2, z2, z2 + cap_h, mat)
    return (u, d - t + 0.24, nz0)


def stone_patches(mb, spots, rng, n):
    """2-4 parches de MAT_Stone_Repair (1.5 cm por delante) en zonas libres: spots = [(frame, u0, u1, z0, z1)]."""
    done = []
    for _ in range(n):
        fr, u0, u1, z0, z1 = rng.choice(spots)
        pw, ph = rng.uniform(0.7, 1.3), rng.uniform(0.5, 0.9)
        cx = rng.uniform(u0 + pw / 2, u1 - pw / 2)
        cz = rng.uniform(z0 + ph / 2, z1 - ph / 2)
        poly = []
        for i in range(6):
            a = 2 * math.pi * i / 6 + rng.uniform(-0.25, 0.25)
            poly.append((cx + math.cos(a) * pw / 2 * rng.uniform(0.8, 1.0), cz + math.sin(a) * ph / 2 * rng.uniform(0.8, 1.0)))
        mb.push(fr)
        mb.prism(poly, 0.0, 0.015, M_REPAIR)
        mb.pop()
        done.append((round(cx, 2), round(cz, 2)))
    return done


def tile_slope(mb, x0, x1, y_e, y_r, z_e, z_r, rng, seg=3.0, toneB=0.18, th=0.06, skip_row=None):
    """Vertiente de tejas por hiladas (como bld_kit) con paso de segmento configurable."""
    L = math.hypot(y_r - y_e, z_r - z_e)
    n = max(1, int(L / K.TILE_COURSE))
    nx = max(1, int(round((x1 - x0) / seg)))
    down = 1.0 if y_e > y_r else -1.0
    for i in range(n):
        t0, t1 = i / n, min(1.0, (i + 1) / n + 0.06)
        ya, za = y_e + (y_r - y_e) * t0, z_e + (z_r - z_e) * t0
        yb, zb = y_e + (y_r - y_e) * t1, z_e + (z_r - z_e) * t1
        if skip_row and skip_row(ya, yb):
            continue
        for k in range(nx):
            xa = x0 + (x1 - x0) * k / nx
            xb = x0 + (x1 - x0) * (k + 1) / nx
            mat = M_ROOF_B if rng.random() < toneB else M_ROOF
            lift = th * (1 if i % 2 else 0.6)
            mb.face([(xa, ya, za + lift), (xb, ya, za + lift), (xb, yb, zb + th * 0.3), (xa, yb, zb + th * 0.3)], mat,
                    nrm=(0, down * 0.3, 1))
            mb.face([(xa, ya, za), (xb, ya, za), (xb, ya, za + lift), (xa, ya, za + lift)], mat, nrm=(0, down, 0))


def roof_repairs(mb, x0, x1, hy, z_e, z_r, rng, n, avoid=None):
    """Remiendos de teja de otro tono (MAT_Roof_Tile_Ocher_B) 2 cm por encima de la vertiente."""
    out = []
    for _ in range(n):
        for _try in range(20):
            sgn = rng.choice((-1, 1))
            t0 = rng.uniform(0.15, 0.6)
            t1 = t0 + rng.uniform(0.15, 0.3)
            xa = rng.uniform(x0 + 0.5, x1 - 2.0)
            xb = xa + rng.uniform(0.8, 1.6)
            if avoid and avoid(xa, xb, sgn):
                continue
            break
        ya, yb = sgn * hy * (1 - t0), sgn * hy * (1 - t1)
        za, zb = z_e + (z_r - z_e) * t0 + 0.11, z_e + (z_r - z_e) * t1 + 0.11
        mb.face([(xa, ya, za), (xb, ya, za), (xb, yb, zb), (xa, yb, zb)], M_ROOF_B, nrm=(0, 0.3 * sgn, 1))
        out.append([round(xa, 2), round(xb, 2), sgn])
    return out


def plinth(mb, u0, u1, h, d, mat):
    mb.box((u0, 0.0, 0.0), (u1, d, h), mat, skip=("y-", "z-"))


def niche(mb, u, z0, y_face, w=0.95, h=2.55, d=0.42, mat=M_STONE, back=M_GRAY):
    """Hornacina-tabernaculo adosada: repisa con mensula, jambas, fondo, dosel con gablete. Devuelve el punto de apoyo
    de la estatua en el marco actual."""
    y0 = y_face
    mb.box((u - w / 2, y0, z0 - 0.22), (u + w / 2, y0 + d, z0), mat, skip=("y-",))
    mb.box((u - w / 3, y0, z0 - 0.55), (u + w / 3, y0 + d * 0.7, z0 - 0.22), mat, skip=("y-", "z+"))
    for s in (-1, 1):
        a = u + s * (w / 2 - 0.07)
        mb.box((a - 0.07, y0, z0), (a + 0.07, y0 + d, z0 + h), mat, skip=("y-", "z-", "z+"))
    mb.box((u - w / 2 + 0.14, y0, z0), (u + w / 2 - 0.14, y0 + 0.03, z0 + h), back, skip=("y-", "z-", "z+"))
    zc = z0 + h
    mb.box((u - w / 2 - 0.05, y0, zc), (u + w / 2 + 0.05, y0 + d + 0.05, zc + 0.24), mat, skip=("y-",))
    mb.prism([(u - w / 2 - 0.05, zc + 0.24), (u + w / 2 + 0.05, zc + 0.24), (u, zc + 0.85)], y0 + d - 0.12, y0 + d + 0.05,
             mat)
    # intrados apuntado bajo el dosel
    rod_path(mb, pointed(u - w / 2 + 0.14, u + w / 2 - 0.14, zc - 0.58, n=3), y0 + d - 0.05, 0.045, mat)
    return (u, y0 + 0.2, z0)


# ---------------------------------------------------------------------------
# props compartidos
# ---------------------------------------------------------------------------
def _shared_mesh(name, build, uv):
    me = bpy.data.meshes.get(name)
    if me is not None:
        bpy.data.meshes.remove(me)
    mb = K.MB()
    build(mb)
    mb.finish()
    me = bpy.data.meshes.new(name)
    mb.bm.to_mesh(me)
    mb.bm.free()
    for n in mb.mats:
        me.materials.append(bpy.data.materials[n])
    tmp = bpy.data.objects.new("TMP_uv", me)
    bpy.context.scene.collection.objects.link(tmp)
    uv(tmp)
    bpy.data.objects.remove(tmp)
    return me


def _ring_frustum(mb, cx, cy, r0, r1, z0, z1, n, mat, sy=1.0, cap_top=False):
    lo = [(cx + r0 * math.cos(2 * math.pi * i / n), cy + r0 * sy * math.sin(2 * math.pi * i / n), z0) for i in range(n)]
    hi = [(cx + r1 * math.cos(2 * math.pi * i / n), cy + r1 * sy * math.sin(2 * math.pi * i / n), z1) for i in range(n)]
    for i in range(n):
        j = (i + 1) % n
        a = 2 * math.pi * (i + 0.5) / n
        q = [lo[i], lo[j], hi[i]] if r1 < 1e-6 else [lo[i], lo[j], hi[j], hi[i]]
        mb.face(q, mat, nrm=(math.cos(a), math.sin(a), (r0 - r1) / max(1e-3, z1 - z0)))
    if cap_top:
        mb.face(hi, mat, nrm=(0, 0, 1))


def statue(mb, variant):
    """Estatua de piedra sin rostro (silueta): tunica, hombros, cabeza lisa; A = espada apoyada, B = baculo y capucha."""
    s = M_STONE
    _ring_frustum(mb, 0, 0, 0.31, 0.22, 0.0, 1.22, 8, s, sy=0.72)
    _ring_frustum(mb, 0, 0, 0.22, 0.25, 1.22, 1.48, 8, s, sy=0.72)
    _ring_frustum(mb, 0, 0, 0.25, 0.08, 1.48, 1.6, 8, s, sy=0.72)
    mb.face([(0.31 * math.cos(2 * math.pi * i / 8), 0.31 * 0.72 * math.sin(2 * math.pi * i / 8), 0.0) for i in range(8)][::-1],
            s, nrm=(0, 0, -1))
    if variant == "A":
        _ring_frustum(mb, 0, 0.01, 0.08, 0.115, 1.6, 1.74, 6, s)
        _ring_frustum(mb, 0, 0.01, 0.115, 0.08, 1.74, 1.88, 6, s, cap_top=True)
        for sx in (-1, 1):
            mb.rod((sx * 0.22, 0.0, 1.45), (sx * 0.05, 0.2, 1.02), 0.055, s)
        mb.box((-0.03, 0.2, 0.12), (0.03, 0.25, 0.92), s, skip=("z-",))
        mb.box((-0.17, 0.19, 0.92), (0.17, 0.26, 0.98), s)
        mb.box((-0.03, 0.2, 0.98), (0.03, 0.25, 1.12), s, skip=("z-",))
    else:
        _ring_frustum(mb, 0, -0.02, 0.15, 0.13, 1.56, 1.8, 6, s)
        _ring_frustum(mb, 0, -0.02, 0.13, 0.02, 1.8, 1.98, 6, s)
        mb.rod((0.24, 0.0, 1.45), (0.24, 0.16, 1.02), 0.055, s)
        mb.rod((-0.24, 0.0, 1.45), (-0.06, 0.2, 1.25), 0.055, s)
        mb.rod((0.24, 0.2, 0.02), (0.24, 0.2, 1.9), 0.035, s)
        mb.box((0.18, 0.15, 1.86), (0.3, 0.25, 1.98), s)


def plaque(mb):
    """Placa de bronce 0.6 x 0.85 con marco en relieve y 4 lineas de letra (los nombres van dentro, despues)."""
    b = M_BRONZE
    mb.box((-0.3, 0.0, 0.0), (0.3, 0.03, 0.85), b, skip=("y-",))
    for z0, z1 in ((0.0, 0.05), (0.8, 0.85)):
        mb.box((-0.3, 0.03, z0), (0.3, 0.05, z1), b, skip=("y-", "x-", "x+"))
    for x0, x1 in ((-0.3, -0.25), (0.25, 0.3)):
        mb.box((x0, 0.03, 0.05), (x1, 0.05, 0.8), b, skip=("y-", "z-", "z+"))
    for k in range(4):
        z = 0.2 + 0.14 * k
        mb.box((-0.19, 0.03, z), (0.19 - 0.05 * (k % 2), 0.042, z + 0.035), b, skip=("y-",))


# ---------------------------------------------------------------------------
# SANTUARIO DEL RETORNO
# ---------------------------------------------------------------------------
class S:
    FW, FD = 16.0, 12.0
    X, Y = 7.5, 5.4              # caras exteriores de los muros (los contrafuertes llegan a 8.0 / 6.0)
    T = 0.6
    H = 9.0                      # hombros (alero)
    RIDGE = 14.0
    PAR_H = 0.6
    BW, BD, BD2 = 0.55, 0.6, 0.35
    BAYS = (-5.86, -3.0, 0.0, 3.0, 5.86)
    BUTT = (-7.225, -4.5, -1.5, 1.5, 4.5, 7.225)
    WIN_W, WIN_Z0, WIN_TOP = 1.4, 2.3, 8.3
    DOOR_W, DOOR_TOP = 1.8, 3.6
    PORTAL_W, PORTAL_TOP, PORTAL_H, WIMP_TOP = 2.3, 3.99, 4.4, 6.3
    OCULUS_Z, OCULUS_R = 7.95, 0.55
    ROSE_Z, ROSE_R = 11.0, 1.5
    FLECHE_X = 4.5
    EAVE_Y = 5.05                # linea de alero tras el antepecho


def santuario_body(rng):
    mb = K.MB()
    L = M_LIGHT
    X, Y, T, H = S.X, S.Y, S.T, S.H
    info = {}
    # muros largos (entre los hastiales)
    for side in ("+Y", "-Y"):
        fr = frame(side, X, Y)
        mb.push(fr)
        holes = []
        top = [(X - T, H + S.PAR_H), (-X + T, H + S.PAR_H)]
        outer = [(-X + T, 0), (X - T, 0)] + top
        for u in S.BAYS:
            if side == "+Y" and u == 0.0:
                outer = with_door(-X + T, X - T, lancet(0.0, S.DOOR_W, 0.0, S.DOOR_TOP), top)
                holes.append(circle(0.0, S.OCULUS_Z, S.OCULUS_R, 12))
                continue
            holes.append(lancet(u, S.WIN_W, S.WIN_Z0, S.WIN_TOP))
        plate(mb, outer, holes, T, L)
        for u in S.BAYS:
            if side == "+Y" and u == 0.0:
                continue
            window_fill(mb, u, S.WIN_W, S.WIN_Z0, S.WIN_TOP, -T * 0.6, 2, L, bars=6)
        if side == "+Y":
            rose_fill(mb, 0.0, S.OCULUS_Z, S.OCULUS_R, -T * 0.6, L, spokes=6, r_tr=0.035)
        # cornisa del antepecho y zocalo
        mb.box((-X - 0.02, 0.0, H - 0.18), (X + 0.02, 0.12, H), L, skip=("y-",))
        mb.box((-X + T, -0.3, H + S.PAR_H), (X - T, 0.04, H + S.PAR_H + 0.08), L)
        plinth(mb, -X - 0.08, X + 0.08, 0.5, 0.08, L)
        # contrafuertes con pinaculo
        for u in S.BUTT:
            zt = buttress(mb, u, S.BW, S.BD, 4.2, S.BD2, H - 0.2, L, cap_h=0.35)
            pinnacle(mb, u, S.BD2 / 2, zt - 0.05, 0.34, 0.9, 1.3, L)
        mb.pop()
    # hastiales con rosetones y 2 lancetas
    for side in ("+X", "-X"):
        fr = frame(side, X, Y)
        mb.push(fr)
        apex = S.RIDGE + 0.35
        outer = [(-Y, 0), (Y, 0), (Y, H + S.PAR_H), (0, apex), (-Y, H + S.PAR_H)]
        holes = [circle(0.0, S.ROSE_Z, S.ROSE_R, 16), lancet(-1.8, 1.0, 3.0, 7.6), lancet(1.8, 1.0, 3.0, 7.6)]
        plate(mb, outer, holes, T, L)
        rose_fill(mb, 0.0, S.ROSE_Z, S.ROSE_R, -T * 0.6, L)
        for u in (-1.8, 1.8):
            window_fill(mb, u, 1.0, 3.0, 7.6, -T * 0.6, 1, L, rose=False, bars=4)
        # albardilla de los faldones del hastial y remate
        for s in (-1, 1):
            mb.rod((s * (Y + 0.05), 0.0 - T / 2, H + S.PAR_H + 0.1), (0.0, -T / 2, apex + 0.12), 0.24, L)
        pinnacle(mb, 0.0, -T / 2, apex + 0.1, 0.4, 0.5, 1.2, L)
        mb.box((-Y - 0.02, 0.0, H - 0.18), (Y + 0.02, 0.12, H), L, skip=("y-",))
        plinth(mb, -Y, Y, 0.5, 0.08, L)
        for u in (-(Y - S.BW / 2), Y - S.BW / 2):
            zt = buttress(mb, u, S.BW, 0.5, 4.2, 0.3, H - 0.2, L, cap_h=0.3)
            pinnacle(mb, u, 0.15, zt - 0.05, 0.3, 0.8, 1.1, L)
        mb.pop()
    # porche: bloque de portada con gablete entre los contrafuertes centrales (+Y)
    fr = frame("+Y", X, Y + 0.6)
    mb.push(fr)
    pw = 1.5 - S.BW / 2
    plate(mb, with_door(-pw, pw, lancet(0.0, S.PORTAL_W, 0.0, S.PORTAL_TOP), [(pw, S.PORTAL_H), (-pw, S.PORTAL_H)]), [],
          0.6, L, back=False)
    mb.box((-pw - 0.04, -0.6, S.PORTAL_H), (pw + 0.04, 0.06, S.PORTAL_H + 0.14), L)
    mb.prism([(-pw, S.PORTAL_H + 0.14), (pw, S.PORTAL_H + 0.14), (0.0, S.WIMP_TOP)], -0.45, 0.0, L)
    for s in (-1, 1):
        mb.rod((s * (pw + 0.05), -0.2, S.PORTAL_H + 0.16), (0.0, -0.2, S.WIMP_TOP + 0.1), 0.15, L)
    pinnacle(mb, 0.0, -0.2, S.WIMP_TOP + 0.05, 0.26, 0.3, 0.8, L)
    rod_path(mb, pointed(-S.PORTAL_W / 2 - 0.12, S.PORTAL_W / 2 + 0.12, S.PORTAL_TOP + 0.14 - 0.866 * (S.PORTAL_W + 0.24), 5),
             0.05, 0.07, L)
    mb.pop()
    mb.push(frame("+Y", X, Y))
    door_leaves(mb, S.DOOR_W, S.DOOR_TOP, -0.42, -0.3)
    mb.pop()
    # remiendos de piedra bajo los ventanales (zonas libres)
    spots = []
    for side in ("+Y", "-Y"):
        for u in S.BAYS:
            if side == "+Y" and u == 0.0:
                continue
            spots.append((frame(side, X, Y), u - 0.9, u + 0.9, 0.6, 2.05))
    for side in ("+X", "-X"):
        spots.append((frame(side, X, Y), -4.6, -2.6, 0.6, 2.8))
        spots.append((frame(side, X, Y), 2.6, 4.6, 0.6, 2.8))
    info["stone_patches"] = stone_patches(mb, spots, rng, rng.randint(2, 4))
    mb.finish()
    return mb, info


def santuario_roof(rng):
    mb = K.MB()
    X, Y, H = S.X, S.Y, S.H
    hy = S.EAVE_Y
    rise = S.RIDGE - H
    hx = X - S.T / 2
    for sgn in (-1, 1):
        tile_slope(mb, -hx, hx, sgn * hy, 0.0, H, S.RIDGE, rng, seg=3.6)
        mb.face([(-hx, sgn * hy, H), (-hx, 0, S.RIDGE), (hx, 0, S.RIDGE), (hx, sgn * hy, H)], M_WOOD, nrm=(0, 0, -1))
    mb.box((-hx, -0.13, S.RIDGE - 0.02), (hx, 0.13, S.RIDGE + 0.16), M_ROOF_B)
    rep = roof_repairs(mb, -hx, hx, hy, H, S.RIDGE, rng, rng.randint(2, 4),
                       avoid=lambda a, b, s: abs((a + b) / 2 - S.FLECHE_X) < 1.6)
    # flecha: base forrada de plomo, linterna de 8 postes (2 de reemplazo con flejes), aguja y esquirla
    fx = S.FLECHE_X
    z_b = S.RIDGE + 0.5
    mb.box((fx - 0.55, -0.55, S.RIDGE - 0.8), (fx + 0.55, 0.55, z_b), M_IRON, skip=("z-",))
    n, r = 8, 0.6
    z_p1 = z_b + 1.6
    replaced = sorted(rng.sample(range(n), 2))
    for i in range(n):
        a = 2 * math.pi * (i + 0.5) / n
        x, y = fx + r * math.cos(a), r * math.sin(a)
        if i in replaced:
            mb.box((x - 0.085, y - 0.085, z_b), (x + 0.085, y + 0.085, z_p1), M_WOOD, skip=("z-", "z+"))
            for zz in (z_b + 0.35, z_p1 - 0.35):
                mb.box((x - 0.1, y - 0.1, zz - 0.04), (x + 0.1, y + 0.1, zz + 0.04), M_IRON, skip=("z-", "z+"))
        else:
            mb.rod((x, y, z_b), (x, y, z_p1), 0.06, M_WOOD)
    _ring_frustum(mb, fx, 0.0, 0.8, 0.8, z_p1, z_p1 + 0.18, n, M_IRON, cap_top=False)
    mb.face([(fx + 0.8 * math.cos(2 * math.pi * i / n), 0.8 * math.sin(2 * math.pi * i / n), z_p1) for i in range(n)][::-1],
            M_IRON, nrm=(0, 0, -1))
    z_sp = z_p1 + 0.18
    apex = S.RIDGE + 5.0
    _ring_frustum(mb, fx, 0.0, 0.7, 0.0, z_sp, apex, n, M_IRON)
    sh = [(fx + 0.09 * math.cos(math.pi / 2 * i), 0.09 * math.sin(math.pi / 2 * i), apex + 0.25) for i in range(4)]
    for i in range(4):
        j = (i + 1) % 4
        mb.face([sh[i], sh[j], (fx, 0, apex + 0.55)], M_SHARD, nrm=(sh[i][0] + sh[j][0] - 2 * fx, sh[i][1] + sh[j][1], 0.3))
        mb.face([sh[j], sh[i], (fx, 0, apex - 0.02)], M_SHARD, nrm=(sh[i][0] + sh[j][0] - 2 * fx, sh[i][1] + sh[j][1], -0.3))
    mb.finish()
    return mb, {"pitch_deg": round(math.degrees(math.atan2(rise, hy)), 1), "roof_repairs": rep,
                "fleche": {"x": fx, "apex_z": apex, "finial_top_z": round(apex + 0.55, 2), "replaced_posts": replaced}}


def well(mb):
    """SANTUARIO_Well: pozo de 2 m de diametro, brocal de caliza clara, agua a -0.5, armadura de hierro con polea."""
    L = M_LIGHT
    n = 16
    _ring_frustum(mb, 0, 0, 1.0, 1.0, 0.0, 0.78, n, L)
    _ring_frustum(mb, 0, 0, 1.06, 1.06, 0.78, 0.92, n, L)
    oc = [(1.06 * math.cos(2 * math.pi * i / n), 1.06 * math.sin(2 * math.pi * i / n)) for i in range(n)]
    ic = [(0.74 * math.cos(2 * math.pi * i / n), 0.74 * math.sin(2 * math.pi * i / n)) for i in range(n)]
    for i in range(n):
        j = (i + 1) % n
        mb.face([(*oc[i], 0.92), (*oc[j], 0.92), (*ic[j], 0.92), (*ic[i], 0.92)], L, nrm=(0, 0, 1))
        mb.face([(*oc[i], 0.78), (*oc[j], 0.78), (1.0 * math.cos(2 * math.pi * j / n), 1.0 * math.sin(2 * math.pi * j / n), 0.78),
                 (1.0 * math.cos(2 * math.pi * i / n), 1.0 * math.sin(2 * math.pi * i / n), 0.78)], L, nrm=(0, 0, -1))
    # pared interior del pozo (hacia dentro) hasta -1.6
    lo = [(0.74 * math.cos(2 * math.pi * i / n), 0.74 * math.sin(2 * math.pi * i / n), -1.6) for i in range(n)]
    hi = [(x, y, 0.92) for x, y in ic]
    for i in range(n):
        j = (i + 1) % n
        a = 2 * math.pi * (i + 0.5) / n
        mb.face([lo[i], lo[j], hi[j], hi[i]], L, nrm=(-math.cos(a), -math.sin(a), 0))
    mb.face([(x, y, -0.5) for x, y in ic], M_WATER, nrm=(0, 0, 1))
    for sx in (-1, 1):
        mb.box((sx * 0.92 - 0.04, -0.04, 0.92), (sx * 0.92 + 0.04, 0.04, 2.25), M_IRON, skip=("z-",))
    mb.rod((-0.96, 0.0, 2.15), (0.96, 0.0, 2.15), 0.035, M_IRON)
    rod_path(mb, [(0.18 * math.cos(2 * math.pi * i / 8), 2.0 + 0.18 * math.sin(2 * math.pi * i / 8)) for i in range(8)],
             0.0, 0.02, M_IRON, closed=True)
    mb.rod((0.18, 0.0, 2.0), (0.18, 0.0, 1.05), 0.008, M_WOOD)
    _ring_frustum(mb, 0.18, 0.0, 0.13, 0.16, 0.75, 1.05, 8, M_WOOD)


# ---------------------------------------------------------------------------
# SALON DE LAS HAZANAS
# ---------------------------------------------------------------------------
class H:
    FW, FD = 42.0, 16.0
    X, Y = 20.2, 7.1             # caras exteriores (contrafuertes hasta 21.0 / 8.0)
    T = 0.9
    WALL = 8.0
    RIDGE = 15.0
    EAVE_OV = 0.85
    BW, BD, BD2 = 1.2, 0.9, 0.6
    BUTT = (-15.0, -9.0, -3.0, 3.0, 9.0, 15.0)
    CORNER_U = 19.6
    WINS = (-17.3, -12.0, -6.0, 6.0, 12.0, 17.3)
    WIN_W, WIN_Z0, WIN_TOP = 1.8, 3.2, 7.4
    # hastial transversal (+Y)
    FX = 3.6
    F_EAVE = 10.0
    F_PITCH = 50.0
    DOOR_W, DOOR_TOP = 3.2, 6.0
    PORTAL_W = 4.0
    BIGWIN_W, BIGWIN_Z0, BIGWIN_TOP = 2.4, 8.2, 12.6
    END_WIN_W, END_WIN_Z0, END_WIN_TOP = 3.0, 4.8, 11.3
    TURRET = (3.6, 4.5, 12.5, 14.0)
    LANTERN_R = 1.1

    @classmethod
    def slope(cls):
        return (cls.RIDGE - cls.WALL) / cls.Y

    @classmethod
    def f_apex(cls):
        return cls.F_EAVE + cls.FX * math.tan(math.radians(cls.F_PITCH))


def hammer_end(mb, u, replaced=False):
    """Cabeza de par (hammerbeam) vista bajo el alero, en el marco del muro: viga volada, tornapuntas curvo, pendolon
    corto al alero. Las de reemplazo: escuadria lisa con flejes de hierro."""
    W = M_WOOD
    s = H.slope()
    tip = H.EAVE_OV - 0.08
    z0, z1 = 6.55, 6.92
    if replaced:
        mb.box((u - 0.19, -0.05, z0), (u + 0.19, tip, z1), W, skip=("y-",))
        for yy in (0.25, tip - 0.2):
            mb.box((u - 0.21, yy - 0.05, z0 - 0.02), (u + 0.21, yy + 0.05, z1 + 0.02), M_IRON, skip=("y-", "y+"))
    else:
        mb.box((u - 0.19, -0.05, z0 + 0.12), (u + 0.19, tip, z1), W, skip=("y-",))
        mb.box((u - 0.19, -0.05, z0), (u + 0.19, tip - 0.25, z0 + 0.12), W, skip=("y-", "z+"))
        mb.face([(u - 0.19, tip - 0.25, z0), (u + 0.19, tip - 0.25, z0), (u + 0.19, tip, z0 + 0.12), (u - 0.19, tip, z0 + 0.12)],
                W, nrm=(0, 1, -1))
    mb.rod((u, 0.3, 6.1), (u, 0.62, z0 + 0.02), 0.08, W)
    z_sof = H.WALL - (tip - 0.05) * s - 0.06
    mb.rod((u, tip - 0.1, z1), (u, tip - 0.1, z_sof), 0.07, W)


def salon_body(rng):
    mb = K.MB()
    G, ST = M_GRAY, M_STONE
    X, Y, T, WALL = H.X, H.Y, H.T, H.WALL
    s = H.slope()
    info = {"hammer_ends": [], "replaced_hammer_ends": []}
    statue_slots = []
    plaque_slots = []
    beam_slots = []
    for side in ("+Y", "-Y"):
        fr = frame(side, X, Y)
        mb.push(fr)
        holes = [lancet(u, H.WIN_W, H.WIN_Z0, H.WIN_TOP) for u in H.WINS]
        top = [(X - T, WALL), (-X + T, WALL)]
        outer = [(-X + T, 0), (X - T, 0)] + top
        if side == "+Y":
            outer = with_door(-X + T, X - T, lancet(0.0, H.DOOR_W, 0.0, H.DOOR_TOP), top)
        plate(mb, outer, holes, T, G, reveal_mat=ST)
        for u in H.WINS:
            window_fill(mb, u, H.WIN_W, H.WIN_Z0, H.WIN_TOP, -T * 0.6, 2, ST, bars=4)
            rod_path(mb, pointed(u - H.WIN_W / 2 - 0.14, u + H.WIN_W / 2 + 0.14, H.WIN_TOP + 0.16 - 0.866 * (H.WIN_W + 0.28), 4),
                     0.05, 0.07, ST)
        plinth(mb, -X - 0.1, X + 0.1, 0.8, 0.1, ST)
        # durmiente (wall plate) bajo el alero
        segs = [(-X + 0.1, -4.6), (4.6, X - 0.1)] if side == "+Y" else [(-X + 0.1, X - 0.1)]
        for a, b in segs:
            mb.box((a, -0.02, 7.58), (b, 0.15, 7.78), M_WOOD, skip=("y-",))
        # contrafuertes cada 6 m + esquinas
        for u in H.BUTT + (-H.CORNER_U, H.CORNER_U):
            if side == "+Y" and abs(u) == 3.0:
                continue
            if abs(u) == 9.0:
                statue_slots.append((side, buttress_niche(mb, u, H.BW, H.BD, 5.2, H.BD2, 5.9, G, G)))
            else:
                buttress(mb, u, H.BW, H.BD, 5.2, H.BD2, 5.9, G, cap_h=0.45)
            if abs(u) < H.CORNER_U:
                beam_slots.append((side, u))
        # canecillos: colas de par cada 1.5 m bajo el alero
        u = -X + 0.9
        while u < X - 0.8:
            near_beam = any(abs(u - b) < 0.55 for b in H.BUTT)
            if not near_beam and not (side == "+Y" and abs(u) < 4.8):
                mb.rod((u, -0.02, 7.8), (u, H.EAVE_OV - 0.05, WALL - (H.EAVE_OV - 0.05) * s - 0.1), 0.065, M_WOOD)
            u += 1.5
        mb.pop()
    # cabezas de par sobre los contrafuertes (2 de reemplazo)
    rep = set(rng.sample(range(len(beam_slots)), 2))
    for k, (side, u) in enumerate(beam_slots):
        mb.push(frame(side, X, Y))
        hammer_end(mb, u, replaced=k in rep)
        mb.pop()
        info["hammer_ends"].append([side, u])
        if k in rep:
            info["replaced_hammer_ends"].append([side, u])
    # hastiales extremos (+X / -X)
    for side in ("+X", "-X"):
        fr = frame(side, X, Y)
        mb.push(fr)
        outer = [(-Y, 0), (Y, 0), (Y, WALL + 0.35), (0, H.RIDGE + 0.35), (-Y, WALL + 0.35)]
        win = lancet(0.0, H.END_WIN_W, H.END_WIN_Z0, H.END_WIN_TOP)
        plate(mb, outer, [win], T, G, reveal_mat=ST)
        window_fill(mb, 0.0, H.END_WIN_W, H.END_WIN_Z0, H.END_WIN_TOP, -T * 0.6, 3, ST, bars=6)
        rod_path(mb, pointed(-H.END_WIN_W / 2 - 0.16, H.END_WIN_W / 2 + 0.16,
                             H.END_WIN_TOP + 0.18 - 0.866 * (H.END_WIN_W + 0.32), 5), 0.05, 0.08, ST)
        for sg in (-1, 1):
            mb.rod((sg * (Y + 0.1), -T / 2, WALL + 0.3), (0.0, -T / 2, H.RIDGE + 0.45), 0.3, ST)
        pinnacle(mb, 0.0, -T / 2, H.RIDGE + 0.5, 0.5, 0.7, 1.4, ST)
        plinth(mb, -Y, Y, 0.8, 0.1, ST)
        for u in (-(Y - 0.6), Y - 0.6):
            buttress(mb, u, H.BW, 0.8, 3.6, 0.5, 5.6, G, cap_h=0.45)
        for u in (-4.2, 4.2):
            statue_slots.append((side, niche(mb, u, 2.0, 0.0, mat=ST, back=G)))
        mb.pop()
    # vano central trasero: arcada ciega de dos lancetas
    mb.push(frame("-Y", X, Y))
    for u in (-1.0, 1.0):
        rod_path(mb, lancet(u, 1.2, 3.6, 7.0)[1:-1], 0.04, 0.06, ST)
        mb.box((u - 0.68, -0.02, 3.46), (u + 0.68, 0.12, 3.6), ST)
    mb.pop()
    # hastial transversal de la portada (+Y): placa delantera, mejillas sobre la cubierta, torrecillas
    FX, FE, FA = H.FX, H.F_EAVE, H.f_apex()
    mb.push(frame("+Y", X, H.FD / 2))
    p_out = lancet(0.0, H.PORTAL_W, 0.0, H.DOOR_TOP + 0.69)
    outer = with_door(-FX, FX, p_out, [(FX, FE + 0.3), (0, FA + 0.3), (-FX, FE + 0.3)])
    bw = lancet(0.0, H.BIGWIN_W, H.BIGWIN_Z0, H.BIGWIN_TOP)
    nholes = [lancet(u, 0.85, 2.0, 4.9) for u in (-2.8, 2.8)]
    plate(mb, outer, [bw] + nholes, T, G, reveal_mat=ST, back=False)
    for u, hpoly in zip((-2.8, 2.8), nholes):
        mb.face([(x, -0.5, z) for x, z in hpoly], G, nrm=(0, 1, 0))
        mb.box((u - 0.5, -0.06, 1.86), (u + 0.5, 0.08, 2.0), ST)
        rod_path(mb, pointed(u - 0.53, u + 0.53, 4.9 + 0.12 - 0.866 * 1.06, 3), 0.03, 0.05, ST)
        statue_slots.append(("+Y_front", (u, -0.25, 2.0)))
        plaque_slots.append(("+Y_front", (u, 0.0, 0.75)))
    window_fill(mb, 0.0, H.BIGWIN_W, H.BIGWIN_Z0, H.BIGWIN_TOP, -T * 0.55, 3, ST, bars=5)
    for w_, top_, yy, rr in ((H.PORTAL_W + 0.3, H.DOOR_TOP + 0.69 + 0.26, 0.06, 0.1),
                             (H.BIGWIN_W + 0.3, H.BIGWIN_TOP + 0.26, 0.05, 0.08)):
        rod_path(mb, pointed(-w_ / 2, w_ / 2, top_ - 0.866 * w_, 5), yy, rr, ST)
    # friso entre portal y ventanal
    mb.box((-FX + 0.1, -0.02, 7.3), (FX - 0.1, 0.1, 7.55), ST, skip=("y-",))
    for sg in (-1, 1):
        mb.rod((sg * (FX + 0.05), -0.3, FE + 0.4), (0.0, -0.3, FA + 0.42), 0.26, ST)
    pinnacle(mb, 0.0, -0.3, FA + 0.45, 0.44, 0.6, 1.3, ST)
    mb.pop()
    # mejillas: triangulos de piedra entre la cubierta principal y el alero del hastial (x = +-[3.0, 3.6])
    y_back = (H.RIDGE - FE) / s
    for sg in (-1, 1):
        x0, x1 = sorted((sg * (FX - 0.6), sg * FX))
        poly = [(Y, WALL), (Y, FE), (y_back, FE)]
        bm_ = mb
        for x, nx in ((x0, -1), (x1, 1)):
            bm_.face([(x, p[0], p[1]) for p in poly], G, nrm=(nx, 0, 0))
        bm_.face([(x0, Y, FE), (x1, Y, FE), (x1, y_back, FE), (x0, y_back, FE)], G, nrm=(0, 0, 1))
        bm_.face([(x0, y_back, FE), (x1, y_back, FE), (x1, Y, WALL), (x0, Y, WALL)], G, nrm=(0, -1, -s))
    # torrecillas a los lados del hastial
    t0, t1, th, tc = H.TURRET
    for sg in (-1, 1):
        a, b = sorted((sg * t0, sg * t1))
        mb.box((a, Y, 0.0), (b, H.FD / 2, th), ST, skip=("z-", "z+"))
        cx, cy = (a + b) / 2, (Y + H.FD / 2) / 2
        mb.box((a - 0.06, Y - 0.06, th), (b + 0.06, H.FD / 2 + 0.06, th + 0.2), ST)
        c = [(a, Y), (b, Y), (b, H.FD / 2), (a, H.FD / 2)]
        for i in range(4):
            (xa, ya), (xb, yb) = c[i], c[(i + 1) % 4]
            tri_face(mb, (xa, ya, th + 0.2), (xb, yb, th + 0.2), (cx, cy, tc), ST, ((xa + xb) / 2 - cx, (ya + yb) / 2 - cy, 0.3))
    # puerta
    mb.push(frame("+Y", X, Y))
    door_leaves(mb, H.DOOR_W, H.DOOR_TOP, -0.55, -0.42, straps=4)
    mb.pop()
    spots = []
    for side in ("+Y", "-Y"):
        for u in H.WINS:
            spots.append((frame(side, X, Y), u - 1.3, u + 1.3, 1.0, 2.9))
    info["stone_patches"] = stone_patches(mb, spots, rng, rng.randint(2, 4))
    mb.finish()
    return mb, info, statue_slots, plaque_slots


def salon_roof(rng):
    mb = K.MB()
    X, Y, WALL, R = H.X, H.Y, H.WALL, H.RIDGE
    s = H.slope()
    ov = H.EAVE_OV
    hy = Y + ov
    z_e = WALL - ov * s
    hx = X - 0.3
    FX, FE, FA = H.FX, H.F_EAVE, H.f_apex()
    y_v_out = (R - FE) / s
    y_v_in = (R - FA) / s
    # vertiente -Y completa; +Y en tres tramos (el central sin las hiladas que quedan bajo el tejado transversal)
    tile_slope(mb, -hx, hx, -hy, 0.0, z_e, R, rng, seg=3.4)
    tile_slope(mb, -hx, -FX, hy, 0.0, z_e, R, rng, seg=3.4)
    tile_slope(mb, FX, hx, hy, 0.0, z_e, R, rng, seg=3.4)
    tile_slope(mb, -FX, FX, hy, 0.0, z_e, R, rng, seg=3.6, skip_row=lambda ya, yb: min(ya, yb) > y_v_out + 0.05)
    for sgn in (-1, 1):
        mb.face([(-hx, sgn * hy, z_e), (-hx, 0, R), (hx, 0, R), (hx, sgn * hy, z_e)], M_WOOD, nrm=(0, 0, -1))
        segs = [(-hx, -H.TURRET[1]), (H.TURRET[1], hx)] if sgn > 0 else [(-hx, hx)]
        for a, b in segs:
            mb.box((a, sgn * hy - 0.03, z_e - 0.2), (b, sgn * hy + 0.03, z_e), M_WOOD)
    mb.box((-hx, -0.14, R - 0.02), (hx, 0.14, R + 0.16), M_ROOF_B)
    # tejado transversal (dos faldones con limahoya exacta sobre la cubierta principal)
    for sg in (-1, 1):
        pts = [(sg * FX, Y, FE), (0.0, Y, FA), (0.0, y_v_in, FA), (sg * FX, y_v_out, FE)]
        mb.face([(x, y, z + 0.05) for x, y, z in pts], M_ROOF, nrm=(sg, 0, 1))
        mb.face([(x, y, z + 0.02) for x, y, z in pts][::-1], M_WOOD, nrm=(-sg, 0, -1))
    mb.box((-0.12, y_v_in, FA - 0.02), (0.12, Y, FA + 0.15), M_ROOF_B)
    rep = roof_repairs(mb, -hx, hx, hy, z_e, R, rng, rng.randint(2, 4),
                       avoid=lambda a, b, sg: (sg > 0 and max(abs(a), abs(b)) < 5.0) or min(abs(a), abs(b)) < 1.6)
    # linterna de cumbrera (louvre) hexagonal
    r = H.LANTERN_R
    z0 = R - (r + 0.15) * s - 0.2
    z1 = R + 1.0
    _ring_frustum(mb, 0, 0, r + 0.15, r + 0.15, z0, z1, 6, M_IRON)
    mb.face([((r + 0.15) * math.cos(math.pi / 3 * i), (r + 0.15) * math.sin(math.pi / 3 * i), z1) for i in range(6)],
            M_IRON, nrm=(0, 0, 1))
    z2 = z1 + 1.6
    pts = [(r * math.cos(math.pi / 3 * i), r * math.sin(math.pi / 3 * i)) for i in range(6)]
    for i in range(6):
        mb.rod((pts[i][0], pts[i][1], z1), (pts[i][0], pts[i][1], z2), 0.08, M_WOOD)
        j = (i + 1) % 6
        for k in range(3):
            zz = z1 + 0.35 + 0.42 * k
            mb.rod((pts[i][0] * 0.95, pts[i][1] * 0.95, zz), (pts[j][0] * 0.95, pts[j][1] * 0.95, zz + 0.1), 0.035, M_WOOD)
    _ring_frustum(mb, 0, 0, r + 0.35, 0.0, z2, z2 + 1.4, 6, M_IRON)
    mb.face([((r + 0.35) * math.cos(math.pi / 3 * i), (r + 0.35) * math.sin(math.pi / 3 * i), z2) for i in range(6)][::-1],
            M_IRON, nrm=(0, 0, -1))
    mb.rod((0, 0, z2 + 1.35), (0, 0, z2 + 2.2), 0.04, M_IRON)
    mb.finish()
    return mb, {"pitch_main_deg": round(math.degrees(math.atan(s)), 1), "pitch_cross_deg": H.F_PITCH,
                "cross_gable_apex_z": round(FA, 2), "valley": [[FX, round(y_v_out, 2), FE], [0, round(y_v_in, 2), round(FA, 2)]],
                "lantern_top_z": round(z2 + 2.2, 2), "roof_repairs": rep}


def box_col(name, col, hx, hy, h):
    m = K.MB()
    m.box((-hx, -hy, 0.0), (hx, hy, h), M_GRAY)
    me = bpy.data.meshes.new(name)
    m.bm.to_mesh(me)
    m.bm.free()
    o = bpy.data.objects.new(name, me)
    col.objects.link(o)
    o.display_type = "WIRE"
    o.hide_render = True
    return o


_ = (P13, random)
