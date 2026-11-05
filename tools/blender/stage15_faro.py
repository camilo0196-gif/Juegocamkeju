"""
CONCORDIA - etapa 15: Torre del Faro (MARKER_Faro, NE de la plaza). Coleccion BLD_PORTAL.

Referencias: Torre de Hercules (A Coruna: faro de piedra sobrio, rampa exterior en espiral de la torre romana) y
Torre del Mangia del Palazzo Pubblico de Siena (verticalidad y remate con galeria). Origen = centro de la base a la
cota del basamento (z 0 = +7.55 abs); +Y local = hacia la plaza (puerta). Angulos theta locales, 0 = +X local.

  zocalo    r 7.0, z 0-4, 6 contrafuertes, cornisa; puerta en arco (theta 90) a nivel de calle; escalera recta adosada
            atras (theta ~270) hasta la terraza del zocalo
  fuste     3 tramos con cornisas: r 5.5->5.0 (z 4-14), 4.7->4.2 (14-24), 3.9->3.5 (24-34)
  rampa     espiral pegada al fuste desde la terraza (z 4, theta 270) hasta la galeria (z 34, theta 90): 3.5 vueltas,
            1.4 m de ancho, barandilla de hierro; en la ultima vuelta se separa del fuste sobre mensulas para llegar
            por fuera del voladizo de la galeria
  canales   4 canales de luz de 20 x 5 cm en espiral (mismo paso que la rampa, desfasados 90 grados: nunca la cruzan),
            bajan por el fuste, cruzan la terraza, bajan por el zocalo y se unen en un anillo al pie que conecta con el
            canal de la plaza (theta 90, la puerta). Emision #8FD0FF 1.2
  galeria   z 34: suelo en voladizo r 4.4, parapeto con hueco de llegada de la rampa, 8 columnas, anillo superior
  FARO_Crystal  racimo de prismas hexagonales de 4 a 6 m (MAT_Shard_Blue_E40: mismas texturas, emision 4.0)
  FARO_Beam     cilindro abierto r 2 x 80 m, MAT_Faro_Beam (azul palido, alpha 0.3, aditivo en Godot), UV 0..1
"""

import math
import random

import bmesh
import bpy
from mathutils import Matrix, Vector

import stage13_portal as P13

SEED = 1515
ZOC_R, ZOC_H = 7.0, 4.0
SECTIONS = ((4.0, 14.0, 5.5, 5.0), (14.0, 24.0, 4.7, 4.2), (24.0, 34.0, 3.9, 3.5))
Z_GAL = 34.0
GAL_R = 4.4
RAMP_W = 1.4
RAMP_T0 = math.radians(270.0)
RAMP_TURNS = 3.5
PITCH = (Z_GAL - ZOC_H) / RAMP_TURNS
CH_W, CH_D = 0.20, 0.05
CH_PHASES = [math.radians(45 + 90 * k) for k in range(4)]   # angulo de cada canal a z = 4
CH_SEG_PER_TURN = 32
SEG = 32
CH_Z0 = ZOC_H + 0.18                 # arranque de los canales en el fuste
CH_Z1 = Z_GAL - 0.6
DOOR_T = math.radians(90.0)
STONE, BASE, WOOD, IRON = "MAT_Limestone_Worn", "MAT_Wall_Gray", "MAT_Wood_Dark", "MAT_Iron_Black"
GLOW = "MAT_Rune_Glow_12"


def r_shaft(z):
    for z0, z1, r0, r1 in SECTIONS:
        if z0 - 1e-6 <= z <= z1 + 1e-6:
            return r0 + (r1 - r0) * (z - z0) / (z1 - z0)
    return SECTIONS[-1][3] if z > Z_GAL else ZOC_R


def ramp_inner(z):
    base = r_shaft(z) - 0.1
    t = min(1.0, max(0.0, (z - 29.5) / 2.5))
    s = t * t * (3 - 2 * t)
    return base + s * max(0.0, GAL_R + 0.05 - base)


def ramp_z(theta):
    """Altura de la rampa del fuste en el angulo acumulado theta (desde RAMP_T0)."""
    return ZOC_H + PITCH * (theta - RAMP_T0) / (2 * math.pi)


def pol(r, t, z):
    return Vector((r * math.cos(t), r * math.sin(t), z))


# ---------------------------------------------------------------------------
def ensure_materials():
    out = {}
    if "MAT_Shard_Blue_E40" not in bpy.data.materials:
        m = bpy.data.materials["MAT_Shard_Blue"].copy()
        m.name = "MAT_Shard_Blue_E40"
        b = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
        b.inputs["Emission Strength"].default_value = 4.0
        m["note"] = "MAT_Shard_Blue (mismas texturas) con emision 4.0 para el cristal del Faro"
        out["MAT_Shard_Blue_E40"] = "creado"
    if "MAT_Faro_Beam" not in bpy.data.materials:
        m = bpy.data.materials.new("MAT_Faro_Beam")
        m.use_nodes = True
        b = m.node_tree.nodes["Principled BSDF"]
        c = P13._lin("#8FD0FF")
        b.inputs["Base Color"].default_value = (*c, 1)
        b.inputs["Emission Color"].default_value = (*c, 1)
        b.inputs["Emission Strength"].default_value = 1.5
        b.inputs["Alpha"].default_value = 0.3
        m.use_backface_culling = False
        try:
            m.surface_render_method = "BLENDED"
        except AttributeError:
            m.blend_method = "BLEND"
        m["note"] = "haz del Faro: azul palido, alpha 0.3; en Godot blend_mode = ADD y animacion por UV"
        out["MAT_Faro_Beam"] = "creado"
    if "MAT_Pipe_Glass" not in bpy.data.materials:
        m = bpy.data.materials.new("MAT_Pipe_Glass")
        m.use_nodes = True
        b = m.node_tree.nodes["Principled BSDF"]
        b.inputs["Base Color"].default_value = (*P13._lin("#C9DDE6"), 1)
        b.inputs["Roughness"].default_value = 0.08
        b.inputs["Alpha"].default_value = 0.35
        m.use_backface_culling = False
        try:
            m.surface_render_method = "BLENDED"
        except AttributeError:
            m.blend_method = "BLEND"
        out["MAT_Pipe_Glass"] = "creado"
    if "MAT_Pipe_Light_Core" not in bpy.data.materials:
        P13.glow_material("MAT_Pipe_Light_Core", 1.5)
        out["MAT_Pipe_Light_Core"] = "creado"
    return out


# ---------------------------------------------------------------------------
# cuerpo de piedra
# ---------------------------------------------------------------------------
def frustum(m, r0, r1, z0, z1, mat, n=SEG, caps=False, rings=1, inward=False):
    vs = []
    for k in range(rings + 1):
        z = z0 + (z1 - z0) * k / rings
        r = r0 + (r1 - r0) * k / rings
        vs.append([m.bm.verts.new(pol(r, 2 * math.pi * i / n, z)) for i in range(n)])
    idx = m.mi(mat)
    for k in range(rings):
        for i in range(n):
            j = (i + 1) % n
            q = (vs[k][i], vs[k][j], vs[k + 1][j], vs[k + 1][i])
            f = m.bm.faces.new(q[::-1] if inward else q)
            f.material_index = idx
    if caps:
        for ring, up in ((vs[0], False), (vs[-1], True)):
            f = m.bm.faces.new(ring if up else ring[::-1])
            f.material_index = idx
    return vs


def annulus(m, ri, ro, z, mat, up=True, n=SEG):
    a = [m.bm.verts.new(pol(ri, 2 * math.pi * i / n, z)) for i in range(n)]
    b = [m.bm.verts.new(pol(ro, 2 * math.pi * i / n, z)) for i in range(n)]
    idx = m.mi(mat)
    for i in range(n):
        j = (i + 1) % n
        q = (a[i], b[i], b[j], a[j]) if up else (a[j], b[j], b[i], a[i])
        f = m.bm.faces.new(q)
        f.material_index = idx


def ring_box(m, ri, ro, z0, z1, mat, n=SEG, t0=None, t1=None):
    """Anillo macizo (cornisa, parapeto); con t0/t1 solo el arco entre esos angulos."""
    if t0 is None:
        frustum(m, ro, ro, z0, z1, mat, n)
        frustum(m, ri, ri, z0, z1, mat, n, inward=True)
        annulus(m, ri, ro, z1, mat, True, n)
        annulus(m, ri, ro, z0, mat, False, n)
        return
    k = max(2, int(abs(t1 - t0) / (2 * math.pi) * n))
    pts = [t0 + (t1 - t0) * i / k for i in range(k + 1)]
    for a, b in zip(pts[:-1], pts[1:]):
        c = [pol(ri, a, z0), pol(ro, a, z0), pol(ro, b, z0), pol(ri, b, z0)]
        d = [pol(ri, a, z1), pol(ro, a, z1), pol(ro, b, z1), pol(ri, b, z1)]
        _hexa(m, c, d, mat)
    for t in (t0, t1):
        m_face(m, [pol(ri, t, z0), pol(ro, t, z0), pol(ro, t, z1), pol(ri, t, z1)], mat)


def m_face(m, cos, mat):
    vs = [m.bm.verts.new(c) for c in cos]
    f = m.bm.faces.new(vs)
    f.material_index = m.mi(mat)
    return f


def _hexa(m, c, d, mat, skip=()):
    """Hexaedro de 8 vertices: c = base (4), d = techo (4)."""
    F = {"bot": (c[3], c[2], c[1], c[0]), "top": (d[0], d[1], d[2], d[3]), "0": (c[0], c[1], d[1], d[0]),
         "1": (c[1], c[2], d[2], d[1]), "2": (c[2], c[3], d[3], d[2]), "3": (c[3], c[0], d[0], d[3])}
    for k, q in F.items():
        if k not in skip:
            m_face(m, list(q), mat)


def build_stone(rng):
    """Devuelve (zocalo: malla limpia para los Boolean, resto: fuste/cornisas/galeria, columnas, angulo llegada)."""
    # zocalo: nucleo macizo cerrado (destino de los Boolean) + cornisa cerrada aparte
    core = P13.Mesh()
    frustum(core, ZOC_R, ZOC_R, 0.0, ZOC_H, BASE, caps=True, rings=2)
    cornice = P13.Mesh()
    ring_box(cornice, ZOC_R + 0.002, ZOC_R + 0.25, ZOC_H - 0.35, ZOC_H, STONE)
    m = P13.Mesh()
    for k in range(8):
        t = math.radians(22.5 + 45 * k)
        if 240 <= math.degrees(t) % 360 <= 300:
            continue
        c = [pol(ZOC_R - 0.1, t - 0.06, 0), pol(ZOC_R + 0.9, t - 0.06, 0), pol(ZOC_R + 0.9, t + 0.06, 0),
             pol(ZOC_R - 0.1, t + 0.06, 0)]
        d = [pol(ZOC_R - 0.1, t - 0.06, 3.3), pol(ZOC_R + 0.15, t - 0.06, 3.3), pol(ZOC_R + 0.15, t + 0.06, 3.3),
             pol(ZOC_R - 0.1, t + 0.06, 3.3)]
        _hexa(m, c, d, BASE, skip=("bot",))
    m_rest = m
    m = m_rest
    # fuste por tramos (con los canales de luz integrados) + cornisas
    build_shaft_channels(m)
    for i, (z0, z1, r0, r1) in enumerate(SECTIONS):
        if i < 2:
            nz0, nz1, nr0, _ = SECTIONS[i + 1]
            ring_box(m, nr0 - 0.05, r1 + 0.4, z1 - 0.15, z1 + 0.35, STONE)
    # galeria
    ring_box(m, 0.0001, GAL_R, Z_GAL - 0.45, Z_GAL, STONE)          # forjado en voladizo
    t_arr = RAMP_T0 + RAMP_TURNS * 2 * math.pi
    gap = 0.38
    ring_box(m, GAL_R - 0.3, GAL_R, Z_GAL, Z_GAL + 1.1, STONE, n=SEG, t0=t_arr + gap, t1=t_arr + 2 * math.pi - gap)
    cols = [t_arr + gap + (2 * math.pi - 2 * gap) * (k + 0.5) / 8 for k in range(8)]
    for t in cols:
        c = pol(GAL_R - 0.45, t, 0)
        bm8 = [Vector((c.x + 0.22 * math.cos(2 * math.pi * i / 8), c.y + 0.22 * math.sin(2 * math.pi * i / 8), 0))
               for i in range(8)]
        lo = [m.bm.verts.new((p.x, p.y, Z_GAL)) for p in bm8]
        hi = [m.bm.verts.new((p.x, p.y, Z_GAL + 4.6)) for p in bm8]
        for i in range(8):
            j = (i + 1) % 8
            f = m.bm.faces.new((lo[i], lo[j], hi[j], hi[i]))
            f.material_index = m.mi(STONE)
    ring_box(m, GAL_R - 1.1, GAL_R + 0.15, Z_GAL + 4.6, Z_GAL + 5.25, STONE)
    ring_box(m, GAL_R - 1.0, GAL_R + 0.3, Z_GAL + 5.25, Z_GAL + 5.45, STONE)
    return core, cornice, m, cols, t_arr


def band_edges(theta_a, theta_b):
    """Bordes (z_lo, z_hi) de los canales en los dos lados de una columna [theta_a, theta_b]; mismo paso que la
    rampa, arranque a CH_Z0 en el angulo de cada canal y final a CH_Z1."""
    out = []
    for ph in CH_PHASES:
        d = (theta_a - ph) % (2 * math.pi)
        for n in range(int(RAMP_TURNS) + 2):
            ta = d + 2 * math.pi * n
            tb = ta + (theta_b - theta_a)
            za = CH_Z0 + PITCH * ta / (2 * math.pi)
            zb = CH_Z0 + PITCH * tb / (2 * math.pi)
            if zb < CH_Z0 - 1e-6 or za > CH_Z1 + 1e-6:
                continue
            if za > CH_Z1 - 1e-6 or zb > CH_Z1 + 1e-6:
                continue
            out.append(((za - CH_W / 2, za + CH_W / 2), (zb - CH_W / 2, zb + CH_W / 2)))
    out.sort(key=lambda e: e[0][0])
    return out


def _orient(f, n):
    f.normal_update()
    if f.normal.dot(n) < 0:
        f.normal_flip()


def build_shaft_channels(m, cols=CH_SEG_PER_TURN):
    """Fuste construido columna a columna: piedra entre canales, y en cada canal dos paredes de 5 cm y el fondo
    emisivo (sin Boolean). Columnas alineadas con el arranque de los canales (45 + 90 k grados)."""
    k_st, k_gl = m.mi(STONE), m.mi(GLOW)
    for i in range(cols):
        ta = 2 * math.pi * i / cols
        tb = 2 * math.pi * (i + 1) / cols
        bands = band_edges(ta, tb)
        for z0, z1, r0, r1 in SECTIONS:
            rz = lambda z: r0 + (r1 - r0) * (z - z0) / (z1 - z0)  # noqa: E731

            def P(t, z, inset=0.0):
                return pol(rz(z) - inset, t, z)
            # bandas recortadas al tramo
            bb = []
            for (la, ha), (lb, hb) in bands:
                la_, ha_ = max(z0, min(z1, la)), max(z0, min(z1, ha))
                lb_, hb_ = max(z0, min(z1, lb)), max(z0, min(z1, hb))
                if ha_ - la_ < 1e-4 and hb_ - lb_ < 1e-4:
                    continue
                bb.append(((la_, ha_), (lb_, hb_)))
            prev_a, prev_b = z0, z0
            for (la, ha), (lb, hb) in bb:
                radial = pol(1, (ta + tb) / 2, 0)
                if la - prev_a > 1e-5 or lb - prev_b > 1e-5:
                    f = m.bm.faces.new([m.bm.verts.new(P(ta, prev_a)), m.bm.verts.new(P(tb, prev_b)),
                                        m.bm.verts.new(P(tb, lb)), m.bm.verts.new(P(ta, la))])
                    f.material_index = k_st
                    _orient(f, radial)
                # pared inferior (mira arriba), pared superior (mira abajo), fondo emisivo (mira fuera)
                for (za, zb, up) in ((la, lb, 1), (ha, hb, -1)):
                    f = m.bm.faces.new([m.bm.verts.new(P(ta, za)), m.bm.verts.new(P(tb, zb)),
                                        m.bm.verts.new(P(tb, zb, CH_D)), m.bm.verts.new(P(ta, za, CH_D))])
                    f.material_index = k_st
                    _orient(f, Vector((0, 0, up)))
                f = m.bm.faces.new([m.bm.verts.new(P(ta, la, CH_D)), m.bm.verts.new(P(tb, lb, CH_D)),
                                    m.bm.verts.new(P(tb, hb, CH_D)), m.bm.verts.new(P(ta, ha, CH_D))])
                f.material_index = k_gl
                _orient(f, radial)
                prev_a, prev_b = ha, hb
            if z1 - prev_a > 1e-5 or z1 - prev_b > 1e-5:
                f = m.bm.faces.new([m.bm.verts.new(P(ta, prev_a)), m.bm.verts.new(P(tb, prev_b)),
                                    m.bm.verts.new(P(tb, z1)), m.bm.verts.new(P(ta, z1))])
                f.material_index = k_st
                _orient(f, pol(1, (ta + tb) / 2, 0))


def build_ramp(m, lod=0):
    """Rampa en espiral (losa con canto, cara inferior y barandilla) + mensulas en la ultima vuelta."""
    n_seg = int(RAMP_TURNS * (32 if lod == 0 else 16))
    t_tot = RAMP_TURNS * 2 * math.pi
    prev = None
    for k in range(n_seg + 1):
        th = RAMP_T0 + t_tot * k / n_seg
        z = ramp_z(th)
        ri = ramp_inner(z)
        ro = ri + RAMP_W
        cur = [pol(ri, th, z), pol(ro, th, z), pol(ro, th, z - 0.35), pol(ri, th, z - 0.35)]
        if prev is not None:
            a, b = prev, cur
            m_face(m, [a[0], a[1], b[1], b[0]], STONE)                      # pisada
            m_face(m, [a[1], a[2], b[2], b[1]], STONE)                      # canto exterior
            m_face(m, [a[2], a[3], b[3], b[2]], STONE)                      # cara inferior
            if z > 29.4:
                m_face(m, [a[3], a[0], b[0], b[3]], STONE)                  # canto interior (separada del fuste)
        prev = cur
        if lod == 0 and k % 3 == 0:
            p = pol(ro - 0.06, th, z)
            P13_box(m, p, 0.05, 1.05, IRON)
        if lod == 0 and z > 29.5 and k % 2 == 0 and ri > r_shaft(z) + 0.05:
            rs = r_shaft(z - 0.9)
            c = [pol(rs - 0.05, th - 0.02, z - 1.2), pol(ri + 0.3, th - 0.02, z - 0.35),
                 pol(ri + 0.3, th + 0.02, z - 0.35), pol(rs - 0.05, th + 0.02, z - 1.2)]
            d = [pol(rs - 0.05, th - 0.02, z - 0.35), pol(ri + 0.3, th - 0.02, z - 0.34),
                 pol(ri + 0.3, th + 0.02, z - 0.34), pol(rs - 0.05, th + 0.02, z - 0.35)]
            _hexa(m, c, d, STONE)
    if lod == 0:
        # pasamanos continuo
        for h in (1.05,):
            pts = []
            for k in range(n_seg + 1):
                th = RAMP_T0 + t_tot * k / n_seg
                z = ramp_z(th)
                pts.append(pol(ramp_inner(z) + RAMP_W - 0.06, th, z + h))
            for a, b in zip(pts[:-1], pts[1:]):
                d = b - a
                s = Vector((0, 0, 1)).cross(d).normalized() * 0.025
                up = Vector((0, 0, 0.025))
                m_face(m, [a - s + up, b - s + up, b + s + up, a + s + up], IRON)
                m_face(m, [a - s - up, a + s - up, b + s - up, b - s - up], IRON)
                m_face(m, [a + s - up, a + s + up, b + s + up, b + s - up], IRON)
                m_face(m, [a - s + up, a - s - up, b - s - up, b - s + up], IRON)


def P13_box(m, base, half, h, mat):
    c = [base + Vector((sx * half, sy * half, 0)) for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    d = [p + Vector((0, 0, h)) for p in c]
    _hexa(m, c, d, mat, skip=("bot",))


def build_stair(m):
    """Escalera recta adosada al zocalo (atras, theta ~270): del suelo a la terraza (+4 m), 20 x 0.2 / 0.3."""
    n, rise, tread, w = 20, 0.2, 0.3, 1.4
    y_in, y_out = -6.25, -6.25 - w
    x_top = -3.0
    prof = [(x_top - 0.6, ZOC_H)]
    for i in range(n):
        x = x_top + i * tread
        prof += [(x, ZOC_H - i * rise), (x, ZOC_H - (i + 1) * rise)]
    prof += [(x_top + n * tread, 0.0), (x_top - 0.6, 0.0)]
    # extrusion del perfil (x, z) entre y_out e y_in
    a = [m.bm.verts.new((x, y_out, z)) for x, z in prof]
    b = [m.bm.verts.new((x, y_in, z)) for x, z in prof]
    k = m.mi(STONE)
    for ring, flip in ((a, True), (b, False)):
        f = m.bm.faces.new(ring[::-1] if flip else ring)
        f.material_index = k
        bmesh.ops.triangulate(m.bm, faces=[f])
    for i in range(len(prof)):
        j = (i + 1) % len(prof)
        f = m.bm.faces.new((a[i], a[j], b[j], b[i]))
        f.material_index = k
    for i in range(0, n + 1, 4):
        x = x_top + min(i, n) * tread
        z = ZOC_H - min(i, n) * rise
        P13_box(m, Vector((x, y_out + 0.05, z)), 0.03, 1.0, IRON)


def door_cutter():
    """Hornacina de la puerta en arco (theta 90): 2.0 x 3.0 m, 0.7 de fondo."""
    me_list = []
    t = DOOR_T
    n = Vector((math.cos(t), math.sin(t), 0))
    right = Vector((0, 0, 1)).cross(n)
    poly = [(-1.0, -0.1), (1.0, -0.1)] + [(math.cos(a) * 1.0, 2.0 + math.sin(a) * 1.0)
                                          for a in [i * math.pi / 8 for i in range(9)]]
    bm = bmesh.new()
    c0 = n * ZOC_R
    lo = [bm.verts.new(c0 + right * u + Vector((0, 0, z)) - n * 0.7) for u, z in poly]
    hi = [bm.verts.new(c0 + right * u + Vector((0, 0, z)) + n * 0.6) for u, z in poly]
    bm.faces.new(lo)
    bm.faces.new(hi[::-1])
    for i in range(len(poly)):
        j = (i + 1) % len(poly)
        bm.faces.new((lo[i], lo[j], hi[j], hi[i]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    me = bpy.data.meshes.new("door_cut")
    bm.to_mesh(me)
    bm.free()
    P13.PROBES[me.name] = [(c0 + Vector((0, 0, 1.4)), n, 0.6)]
    me_list.append(me)
    return me_list


def door_frame(m):
    """Portada en arco que sobresale 0.3 m del zocalo (sin cortar el muro): jambas + rosca + umbral."""
    t = DOOR_T
    n = Vector((math.cos(t), math.sin(t), 0))
    right = Vector((0, 0, 1)).cross(n)
    c0 = n * (ZOC_R - 0.05)
    inner = [(-1.0, 0.0), (1.0, 0.0)] + [(math.cos(a) * 1.0, 2.0 + math.sin(a) * 1.0) for a in
                                         [i * math.pi / 8 for i in range(9)]]
    outer = [(-1.45, 0.0), (1.45, 0.0)] + [(math.cos(a) * 1.45, 2.0 + math.sin(a) * 1.45) for a in
                                           [i * math.pi / 8 for i in range(9)]]
    k = m.mi(STONE)
    # rosca: caras frontales entre contorno exterior e interior (por tramos del arco) + jambas
    for (ui0, zi0), (ui1, zi1), (uo0, zo0), (uo1, zo1) in zip(inner[1:-1], inner[2:], outer[1:-1], outer[2:]):
        pts = [Vector((ui0, 0, zi0)), Vector((ui1, 0, zi1)), Vector((uo1, 0, zo1)), Vector((uo0, 0, zo0))]
        for off, flip in ((0.35, False),):
            q = [c0 + right * p.x + Vector((0, 0, p.z)) + n * off for p in pts]
            f = m_face(m, q, STONE)
            _orient(f, n)
        for a, b in ((pts[0], pts[1]), (pts[3], pts[2])):
            q = [c0 + right * a.x + Vector((0, 0, a.z)), c0 + right * b.x + Vector((0, 0, b.z)),
                 c0 + right * b.x + Vector((0, 0, b.z)) + n * 0.35, c0 + right * a.x + Vector((0, 0, a.z)) + n * 0.35]
            f = m_face(m, q, STONE)
            mid = (q[0] + q[1]) / 2
            _orient(f, (mid - (c0 + Vector((0, 0, 2.0)))).normalized() * (1 if a in (pts[3],) else -1))
    for side in (-1, 1):
        u0, u1 = sorted((side * 1.0, side * 1.45))
        c = [c0 + right * u0, c0 + right * u1, c0 + right * u1 + n * 0.35, c0 + right * u0 + n * 0.35]
        d = [p + Vector((0, 0, 2.0)) for p in c]
        _hexa(m, c, d, STONE, skip=("bot",))
    # umbral
    c = [c0 + right * -1.45, c0 + right * 1.45, c0 + right * 1.45 + n * 0.6, c0 + right * -1.45 + n * 0.6]
    d = [p + Vector((0, 0, 0.12)) for p in c]
    _hexa(m, c, d, BASE, skip=("bot",))
    _ = k


def door_leaf(m):
    t = DOOR_T
    n = Vector((math.cos(t), math.sin(t), 0))
    right = Vector((0, 0, 1)).cross(n)
    c0 = n * (ZOC_R + 0.08)
    poly = [(-1.0, 0.0), (1.0, 0.0)] + [(math.cos(a) * 1.0, 2.0 + math.sin(a) * 1.0)
                                        for a in [i * math.pi / 8 for i in range(9)]]
    vs = [m.bm.verts.new(c0 + right * u + Vector((0, 0, z))) for u, z in poly]
    f = m.bm.faces.new(vs)
    f.material_index = m.mi(WOOD)
    f.normal_update()
    if f.normal.dot(n) < 0:
        f.normal_flip()
    bmesh.ops.triangulate(m.bm, faces=[f])
    for zz in (0.6, 1.8):
        a, b = c0 + n * 0.01 + right * -0.95 + Vector((0, 0, zz)), c0 + n * 0.01 + right * 0.95 + Vector((0, 0, zz))
        q = [a, b, b + Vector((0, 0, 0.08)), a + Vector((0, 0, 0.08))]
        g = m_face(m, q, IRON)
        g.normal_update()
        if g.normal.dot(n) < 0:
            g.normal_flip()


# ---------------------------------------------------------------------------
# canales de luz
# ---------------------------------------------------------------------------
def channel_paths():
    """Para cada canal: lista de tramos (tipo, puntos de superficie, normal) desde la galeria hasta el suelo."""
    paths = []
    for phase in CH_PHASES:
        segs = []
        t_tot = RAMP_TURNS * 2 * math.pi
        n = int(RAMP_TURNS * CH_SEG_PER_TURN)
        pts = []
        for k in range(n + 1):
            th = phase + t_tot * k / n
            z = ZOC_H + 0.18 + (Z_GAL - 0.9 - ZOC_H - 0.18) * k / n
            pts.append((th, z))
        for (ta, za), (tb, zb) in zip(pts[:-1], pts[1:]):
            segs.append(("shaft", ta, za, tb, zb))
        paths.append((phase, segs))
    return paths


def chord_cutter(pa, pb, n_out, width, depth, out, k):
    """Cortador prismatico a lo largo de la cuerda pa-pb sobre una superficie de normal n_out."""
    t = (pb - pa)
    L = t.length
    t.normalize()
    s = n_out.cross(t).normalized() * (width / 2)
    ext = t * 0.02
    a, b = pa - ext, pb + ext
    corners = [a - s, b - s, b + s, a + s]
    bm = bmesh.new()
    lo = [bm.verts.new(q - n_out * (depth + 0.0007 * (k % 7))) for q in corners]
    hi = [bm.verts.new(q + n_out * out) for q in corners]
    bm.faces.new(lo[::-1])
    bm.faces.new(hi)
    for i in range(4):
        j = (i + 1) % 4
        bm.faces.new((lo[i], lo[j], hi[j], hi[i]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    me = bpy.data.meshes.new("ch_cut")
    bm.to_mesh(me)
    bm.free()
    P13.PROBES[me.name] = [((pa + pb) / 2, n_out.copy(), depth * 0.6)]
    _ = L
    return me


def channel_cutters_and_strips(m_glow):
    """Cortadores (fuste, terraza, zocalo) + tiras emisivas en el fondo, y anillo al pie."""
    cutters = []
    k = 0
    for phase, segs in channel_paths():
        # (el tramo del fuste se construye con build_shaft_channels, sin cortes)
        # terraza del zocalo: radial desde el fuste hasta el borde (normal +Z)
        t = phase
        rs = SECTIONS[0][2]
        pa, pb = pol(rs - 0.05, t, ZOC_H), pol(ZOC_R + 0.3, t, ZOC_H)
        cutters.append(chord_cutter(pa, pb, Vector((0, 0, 1)), CH_W, CH_D, 0.5, k))
        k += 1
        s = pol(1, t + math.pi / 2, 0) * (CH_W / 2 * 0.96)
        za = ZOC_H - CH_D + 0.004
        f = m_face(m_glow, [pa - s + Vector((0, 0, za - ZOC_H)), pb - s + Vector((0, 0, za - ZOC_H)),
                            pb + s + Vector((0, 0, za - ZOC_H)), pa + s + Vector((0, 0, za - ZOC_H))], GLOW)
        f.normal_update()
        if f.normal.z < 0:
            f.normal_flip()
        # bajada vertical por el zocalo (y su cornisa) hasta el suelo
        nm = pol(1, t, 0)
        pa, pb = pol(ZOC_R, t, ZOC_H + 0.05), pol(ZOC_R, t, -0.05)
        cutters.append(chord_cutter(pa, pb, nm, CH_W, CH_D, 0.6, k))
        k += 1
        side = pol(1, t + math.pi / 2, 0) * (CH_W / 2 * 0.96)
        fa, fb = pol(ZOC_R - CH_D + 0.004, t, ZOC_H), pol(ZOC_R - CH_D + 0.004, t, 0.0)
        f = m_face(m_glow, [fa - side, fb - side, fb + side, fa + side], GLOW)
        f.normal_update()
        if f.normal.dot(nm) < 0:
            f.normal_flip()
    return cutters


def ground_ring(m_glow, ground_z):
    """Anillo emisivo al pie del zocalo (sobre el suelo de la plaza) + uniones con las 4 bajadas."""
    n = 64
    ri, ro = ZOC_R + 0.08, ZOC_R + 0.28
    for i in range(n):
        a, b = 2 * math.pi * i / n, 2 * math.pi * (i + 1) / n
        q = [pol(ri, a, ground_z(ri, a)), pol(ro, a, ground_z(ro, a)), pol(ro, b, ground_z(ro, b)),
             pol(ri, b, ground_z(ri, b))]
        f = m_face(m_glow, q, GLOW)
        f.normal_update()
        if f.normal.z < 0:
            f.normal_flip()
    for t in CH_PHASES:
        s = pol(1, t + math.pi / 2, 0) * 0.1
        a, b = pol(ZOC_R - CH_D, t, 0), pol(ri, t, 0)
        za, zb = ground_z(ZOC_R, t), ground_z(ri, t)
        q = [a - s + Vector((0, 0, za)), b - s + Vector((0, 0, zb)), b + s + Vector((0, 0, zb)),
             a + s + Vector((0, 0, za))]
        f = m_face(m_glow, q, GLOW)
        f.normal_update()
        if f.normal.z < 0:
            f.normal_flip()


# ---------------------------------------------------------------------------
# cristal y haz
# ---------------------------------------------------------------------------
def build_crystal(col, rng):
    m = P13.Mesh()
    k = m.mi("MAT_Shard_Blue_E40")
    prisms = [((0.0, 0.0), 6.0, 0.55, 0.0, 0.0)]
    for i in range(6):
        a = 2 * math.pi * i / 6 + rng.uniform(-0.2, 0.2)
        prisms.append(((0.75 * math.cos(a), 0.75 * math.sin(a)), rng.uniform(4.3, 5.4), rng.uniform(0.32, 0.42),
                       rng.uniform(0.18, 0.32), a))
    for i in range(5):
        a = 2 * math.pi * (i + 0.5) / 5 + rng.uniform(-0.2, 0.2)
        prisms.append(((1.3 * math.cos(a), 1.3 * math.sin(a)), rng.uniform(4.0, 4.6), rng.uniform(0.22, 0.3),
                       rng.uniform(0.35, 0.5), a))
    for (cx, cy), h, r, tilt, az in prisms:
        rot = Matrix.Rotation(az, 4, "Z") @ Matrix.Rotation(tilt, 4, "Y") @ Matrix.Rotation(-az, 4, "Z")
        base = Vector((cx, cy, Z_GAL - 0.2))
        body = h * 0.8
        ring0 = [base + rot @ Vector((r * math.cos(2 * math.pi * i / 6), r * math.sin(2 * math.pi * i / 6), 0))
                 for i in range(6)]
        ring1 = [base + rot @ Vector((r * 0.92 * math.cos(2 * math.pi * i / 6), r * 0.92 * math.sin(2 * math.pi * i / 6),
                                      body)) for i in range(6)]
        tip = base + rot @ Vector((0, 0, h))
        v0 = [m.bm.verts.new(p) for p in ring0]
        v1 = [m.bm.verts.new(p) for p in ring1]
        vt = m.bm.verts.new(tip)
        for i in range(6):
            j = (i + 1) % 6
            m.bm.faces.new((v0[i], v0[j], v1[j], v1[i])).material_index = k
            m.bm.faces.new((v1[i], v1[j], vt)).material_index = k
    o = m.to_object("FARO_Crystal", col)
    top = max(v.co.z for v in o.data.vertices)
    return o, top


def build_beam(col, z0, r=2.0, h=80.0, n=32):
    bm = bmesh.new()
    lo = [bm.verts.new(pol(r, 2 * math.pi * i / n, z0)) for i in range(n + 1)]
    hi = [bm.verts.new(pol(r, 2 * math.pi * i / n, z0 + h)) for i in range(n + 1)]
    uv = bm.loops.layers.uv.new("UVWorld")
    for i in range(n):
        f = bm.faces.new((lo[i], lo[i + 1], hi[i + 1], hi[i]))
        for lp, (u, v) in zip(f.loops, ((i / n, 0), ((i + 1) / n, 0), ((i + 1) / n, 1), (i / n, 1))):
            lp[uv].uv = (u, v)
    bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=1e-5)
    me = bpy.data.meshes.new("FARO_Beam")
    bm.to_mesh(me)
    bm.free()
    me.materials.append(bpy.data.materials["MAT_Faro_Beam"])
    o = bpy.data.objects.new("FARO_Beam", me)
    col.objects.link(o)
    o["no_collision"] = True
    o["uv"] = "u = 0..1 alrededor, v = 0..1 de abajo arriba (80 m) para animar en Godot"
    return o


# ---------------------------------------------------------------------------
# tubos de luz (kit) y curva
# ---------------------------------------------------------------------------
def pipe_section(m, path_pts, r_glass=0.2, r_core=0.11, n=12, collars=True):
    """Tubo a lo largo de una polilinea: nucleo emisivo + vidrio + collarines de hierro en los extremos."""
    frames = []
    for i, p in enumerate(path_pts):
        t = (path_pts[min(i + 1, len(path_pts) - 1)] - path_pts[max(i - 1, 0)]).normalized()
        a = Vector((0, 0, 1)) if abs(t.z) < 0.9 else Vector((1, 0, 0))
        u = a.cross(t).normalized()
        v = t.cross(u)
        frames.append((p, u, v))
    for r, mat in ((r_core, "MAT_Pipe_Light_Core"), (r_glass, "MAT_Pipe_Glass")):
        rings = [[m.bm.verts.new(p + (u * math.cos(2 * math.pi * k / n) + v * math.sin(2 * math.pi * k / n)) * r)
                  for k in range(n)] for p, u, v in frames]
        idx = m.mi(mat)
        for a, b in zip(rings[:-1], rings[1:]):
            for k in range(n):
                j = (k + 1) % n
                m.bm.faces.new((a[k], a[j], b[j], b[k])).material_index = idx
    if collars:
        for p, u, v in (frames[0], frames[-1]):
            t = u.cross(v)
            c0 = [p + (u * math.cos(2 * math.pi * k / n) + v * math.sin(2 * math.pi * k / n)) * (r_glass + 0.03)
                  - t * 0.06 for k in range(n)]
            c1 = [q + t * 0.12 for q in c0]
            a = [m.bm.verts.new(q) for q in c0]
            b = [m.bm.verts.new(q) for q in c1]
            idx = m.mi(IRON)
            for k in range(n):
                j = (k + 1) % n
                m.bm.faces.new((a[k], a[j], b[j], b[k])).material_index = idx


def build_pipe_kit(col, origin=(3000.0, 700.0, 0.0)):
    out = {}
    ox, oy, oz = origin
    m = P13.Mesh()
    pipe_section(m, [Vector((0, 0, 0)), Vector((1.0, 0, 0)), Vector((2.0, 0, 0))])
    o = m.to_object("PIPE_Light_Straight", col)
    o.location = (ox, oy, oz + 1.5)
    o["length_m"] = 2.0
    out[o.name] = o
    m = P13.Mesh()
    R = 0.8
    pts = [Vector((R * math.sin(a), R - R * math.cos(a), 0)) for a in [i * (math.pi / 2) / 8 for i in range(9)]]
    pipe_section(m, pts)
    o = m.to_object("PIPE_Light_Elbow", col)
    o.location = (ox + 4.0, oy, oz + 1.5)
    o["bend"] = "90 grados, radio 0.8 m"
    out[o.name] = o
    m = P13.Mesh()
    P13_box(m, Vector((0, 0, 0)), 0.09, 9.0 - 0.45, IRON)
    P13_box(m, Vector((0, 0, 0)), 0.2, 0.25, IRON)
    m_face(m, [Vector((-0.3, -0.06, 8.55)), Vector((0.3, -0.06, 8.55)), Vector((0.3, -0.06, 8.75)),
               Vector((-0.3, -0.06, 8.75))], IRON)
    m_face(m, [Vector((-0.3, 0.06, 8.75)), Vector((0.3, 0.06, 8.75)), Vector((0.3, 0.06, 8.55)),
               Vector((-0.3, 0.06, 8.55))], IRON)
    pipe_ring = [Vector((0.24 * math.cos(2 * math.pi * k / 10), 0, 9.0 + 0.24 * math.sin(2 * math.pi * k / 10)))
                 for k in range(10)]
    a = [m.bm.verts.new(p + Vector((0, -0.05, 0))) for p in pipe_ring]
    b = [m.bm.verts.new(p + Vector((0, 0.05, 0))) for p in pipe_ring]
    for k in range(10):
        j = (k + 1) % 10
        m.bm.faces.new((a[k], a[j], b[j], b[k])).material_index = m.mi(IRON)
    o = m.to_object("PIPE_Light_Support", col)
    o.location = (ox + 8.0, oy, oz)
    o["height_m"] = 9.0
    out[o.name] = o
    for o in out.values():
        o["kit_piece"] = True
        o["tris"] = sum(len(p.vertices) - 2 for p in o.data.polygons)
    return out
