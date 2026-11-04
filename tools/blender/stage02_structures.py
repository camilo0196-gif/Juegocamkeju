"""
CONCORDIA - Etapa 02b: estructuras de contencion y escaleras sobre TRN_City.

Referencias: muros de contencion con contrafuertes y escaleras adosadas de
Toledo; escalinata monumental de peldanos bajos de Mala Strana (Praga).

Piezas (una malla por Morada y tipo, para pocas llamadas de dibujo):
  MORADAS/TRN_Parapets_<Morada>       pretiles 0.6 m (bordes de terraza) y 0.9 m (muros > 3 m)
  MORADAS/TRN_Buttresses_<Morada>     contrafuertes cada 8 m en muros laterales > 3 m
  MORADAS/TRN_LateralStairs_<Morada>  escaleras de 2.5 m cada 25 m en los bordes laterales
  STREETS/TRN_Escalinata_<Morada>     escalinata r 95..105 (6 m, 10 x 0.15 / 1.0, descanso 2 m)
                                      + pasamanos de piedra de 0.9 m
Todas con MAT_Stone_Limestone. La geometria se calcula con terrain_profile.py,
asi que encaja con el terreno sin depender de la malla.
"""

import os
import sys
from math import asin, ceil, cos, degrees, radians, sin

import bpy  # noqa: I001
import bmesh
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import concordia_const as C  # noqa: E402
import terrain_profile as T  # noqa: E402

MAT_STONE = "MAT_Stone_Limestone"
STONE_HEX = "#CFC6B2"            # caliza clara gastada (provisional)

# Parametros de diseno no fijados en el pedido (provisionales, ajustables)
STAIR_TREAD = 0.33               # huella escaleras laterales (2R + H = 0.63)
STAIR_RISER_TARGET = 0.15
STAIR_FIRST_OFFSET = 11.5        # primera escalera a r = 105 + 11.5 = 116.5 (rellano lejos de saltos)
BUTTRESS_WIDTH = 1.0
BUTTRESS_DEPTH_BASE = 1.2        # salida desde el pie del muro
BUTTRESS_DEPTH_TOP = 0.45
BUTTRESS_TOP_BELOW = 0.4         # remate por debajo de la coronacion del muro
EMBED = 0.25                     # empotrado de las piezas bajo el suelo
PARAPET_CHORD = 2.0              # longitud maxima de tramo recto en pretiles curvos
LAT_END = C.WALL_BASE_R[0]       # las piezas laterales terminan en la base de la muralla (r=196)


# ---------------------------------------------------------------------------
class MeshBuilder:
    def __init__(self):
        self.verts, self.faces = [], []

    def add(self, pts, faces):
        o = len(self.verts)
        self.verts += [tuple(p) for p in pts]
        self.faces += [tuple(o + i for i in f) for f in faces]

    def prism(self, profile, origin, p_dir, w_dir, w0, w1):
        """Extruye un poligono (p, z) entre w0 y w1 a lo largo de w_dir."""
        O, P, W = Vector(origin), Vector(p_dir), Vector(w_dir)
        n = len(profile)
        pts = []
        for w in (w0, w1):
            for p, z in profile:
                v = O + P * p + W * w
                pts.append((v.x, v.y, z))
        faces = [tuple(range(n)), tuple(range(2 * n - 1, n - 1, -1))]
        for i in range(n):
            j = (i + 1) % n
            faces.append((i, j, n + j, n + i))
        self.add(pts, faces)

    def strip(self, rings):
        """rings = lista de secciones (4 puntos cada una, mismo orden). Tubo cerrado."""
        pts = [p for ring in rings for p in ring]
        faces = []
        m = len(rings)
        for k in range(m - 1):
            a, b = 4 * k, 4 * (k + 1)
            for i in range(4):
                j = (i + 1) % 4
                faces.append((a + i, a + j, b + j, b + i))
        faces.append((3, 2, 1, 0))
        e = 4 * (m - 1)
        faces.append((e, e + 1, e + 2, e + 3))
        self.add(pts, faces)

    def to_object(self, name, collection, material):
        if not self.faces:
            return None
        bm = bmesh.new()
        vs = [bm.verts.new(p) for p in self.verts]
        for f in self.faces:
            try:
                bm.faces.new([vs[i] for i in f])
            except ValueError:
                pass
        bmesh.ops.triangulate(bm, faces=bm.faces[:], quad_method="BEAUTY", ngon_method="EAR_CLIP")
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
        zmin = min(v.co.z for v in bm.verts)
        cx = sum(v.co.x for v in bm.verts) / len(bm.verts)
        cy = sum(v.co.y for v in bm.verts) / len(bm.verts)
        for v in bm.verts:
            v.co -= Vector((cx, cy, zmin))
        # UV caja en metros (proyeccion por eje dominante de cada cara)
        uvl = bm.loops.layers.uv.new("UVMap")
        for f in bm.faces:
            n = f.normal
            ax = max(range(3), key=lambda i: abs(n[i]))
            for loop in f.loops:
                c = loop.vert.co + Vector((cx, cy, zmin))
                loop[uvl].uv = (c.x, c.y) if ax == 2 else ((c.y, c.z) if ax == 0 else (c.x, c.z))
        if name in bpy.data.objects:
            bpy.data.objects.remove(bpy.data.objects[name])
        me = bpy.data.meshes.new(name)
        bm.to_mesh(me)
        bm.free()
        for p in me.polygons:
            p.use_smooth = False
        me.materials.append(material)
        obj = bpy.data.objects.new(name, me)
        obj.location = (cx, cy, zmin)
        collection.objects.link(obj)
        return obj


def stone_material():
    if MAT_STONE in bpy.data.materials:
        return bpy.data.materials[MAT_STONE]
    m = bpy.data.materials.new(MAT_STONE)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = C.hex_to_linear_rgba(STONE_HEX)
    b.inputs["Roughness"].default_value = 0.85
    return m


# ---------------------------------------------------------------------------
# Utilidades del borde lateral
# ---------------------------------------------------------------------------
def edge_levels(a, tb):
    """(dz, z_alto, z_bajo, lado_alto) en la linea de borde a distancia a."""
    x, y = a * cos(radians(tb)), a * sin(radians(tb))
    zd = T.prof_diag(a)
    zc = T.card_z(x, y, a, tb % 360.0)
    dz = zd - zc
    return (dz, zd, zc, "diag") if dz >= 0 else (dz, zc, zd, "card")


def P(a, e, t, n):
    return Vector((a * e[0] + t * n[0], a * e[1] + t * n[1], 0.0))


def frange(a, b, step):
    n = max(1, int(round((b - a) / step)))
    return [a + (b - a) * i / n for i in range(n + 1)]


# ---------------------------------------------------------------------------
# Escaleras laterales
# ---------------------------------------------------------------------------
def build_lateral_stairs(mb, key, side, tb, e, n_card, report):
    W = C.LATERAL_STAIR_WIDTH
    gaps, footprints = [], []
    a_s = C.TERRACE_START_R + STAIR_FIRST_OFFSET
    while a_s + W / 2 <= LAT_END:
        dz, z_hi, _z_lo, hi_side = edge_levels(a_s, tb)
        if abs(dz) < C.LATERAL_MIN_WALL:
            a_s += C.LATERAL_STAIR_SPACING
            continue
        n_low = n_card if hi_side == "diag" else (-n_card[0], -n_card[1])
        a_top = a_s - W / 2

        def ground(a, t):
            p = P(a, e, t, n_low)
            return T.height(p.x, p.y)

        n = max(2, round(abs(dz) / STAIR_RISER_TARGET))
        for _ in range(6):
            a_bot = a_top - (n - 1) * STAIR_TREAD
            d_mid = T.face_run(edge_levels(a_bot, tb)[0])
            z_bot = ground(a_bot - 0.05, d_mid + W / 2)
            n = max(2, round((z_hi - z_bot) / STAIR_RISER_TARGET))
        a_bot = a_top - (n - 1) * STAIR_TREAD
        riser = (z_hi - z_bot) / n
        d_max = max(T.face_run(edge_levels(a, tb)[0]) for a in frange(a_bot, a_s + W / 2, 0.25))
        t_out = d_max + W
        z_floor = min(ground(a, t) for a in frange(a_bot - 0.3, a_s + W / 2, 0.5)
                      for t in (0.0, d_max, t_out)) - EMBED
        # rellano superior
        mb.prism([(0.0, z_floor), (t_out, z_floor), (t_out, z_hi), (0.0, z_hi)],
                 (0, 0, 0), (n_low[0], n_low[1], 0), (e[0], e[1], 0), a_top, a_s + W / 2)
        # peldanos (abrazan la cara inclinada del muro)
        for k in range(1, n):
            zk = z_bot + k * riser
            a0 = a_top - (n - k) * STAIR_TREAD
            a1 = a0 + STAIR_TREAD
            dzk, zh_k, zl_k, _ = edge_levels((a0 + a1) / 2, tb)
            dk = T.face_run(dzk)
            t_in = 0.0 if zh_k <= zl_k else max(0.0, dk * (zh_k - zk) / (zh_k - zl_k) - 0.03)
            t_in = min(t_in, dk)
            mb.prism([(t_in, z_floor), (t_out, z_floor), (t_out, zk), (t_in, zk)],
                     (0, 0, 0), (n_low[0], n_low[1], 0), (e[0], e[1], 0), a0, a1 + 0.002)
        gaps.append((a_top, a_s + W / 2))
        footprints.append((a_bot - 0.3, a_s + W / 2 + 0.3))
        report.append({"edge": f"{key}{side:+d}", "r_station": round(a_s, 2), "rise_m": round(z_hi - z_bot, 2),
                       "risers": n, "riser_m": round(riser, 3), "tread_m": STAIR_TREAD,
                       "run_m": round((n - 1) * STAIR_TREAD, 2), "side_low": "cardinal" if hi_side == "diag" else "morada",
                       "top_level": round(z_hi, 2)})
        a_s += C.LATERAL_STAIR_SPACING
    return gaps, footprints


# ---------------------------------------------------------------------------
# Pretiles laterales
# ---------------------------------------------------------------------------
def build_lateral_parapets(mb, tb, e, n_card, gaps, report):
    samples = frange(C.DIAG_LANDMARK_END, LAT_END, 0.05)
    pieces, cur = [], None

    def in_gap(a):
        return any(g0 <= a <= g1 for g0, g1 in gaps)

    for a in samples:
        dz, z_hi, _zl, hi_side = edge_levels(a, tb)
        ok = abs(dz) >= C.LATERAL_MIN_WALL and not in_gap(a)
        h = C.PARAPET_TALL_H if abs(dz) > C.LATERAL_TALL_WALL else C.PARAPET_LOW_H
        if ok and cur and cur["side"] == hi_side and cur["h"] == h and abs(z_hi - cur["zs"][-1]) < 0.05:
            cur["as"].append(a)
            cur["zs"].append(z_hi)
            continue
        if cur and len(cur["as"]) > 1:
            pieces.append(cur)
        cur = {"side": hi_side, "h": h, "as": [a], "zs": [z_hi]} if ok else None
    if cur and len(cur["as"]) > 1:
        pieces.append(cur)
    for pc in pieces:
        n_high = (-n_card[0], -n_card[1]) if pc["side"] == "diag" else n_card
        as_, zs = pc["as"], pc["zs"]
        idx = [0]
        acc = as_[0]
        for i, a in enumerate(as_):
            if a - acc >= PARAPET_CHORD:
                idx.append(i)
                acc = a
        if idx[-1] != len(as_) - 1:
            idx.append(len(as_) - 1)
        for i0, i1 in zip(idx, idx[1:]):
            zm = (zs[i0] + zs[i1]) / 2
            mb.prism([(0.0, zm - EMBED), (C.PARAPET_THICK, zm - EMBED), (C.PARAPET_THICK, zm + pc["h"]),
                      (0.0, zm + pc["h"])], (0, 0, 0), (n_high[0], n_high[1], 0), (e[0], e[1], 0),
                     as_[i0], as_[i1])
        report.append({"from_r": round(as_[0], 2), "to_r": round(as_[-1], 2), "h": pc["h"], "high_side": pc["side"]})


# ---------------------------------------------------------------------------
# Contrafuertes
# ---------------------------------------------------------------------------
def build_buttresses(mb, tb, e, n_card, footprints, report):
    """Contrafuertes cada BUTTRESS_SPACING en los tramos libres (sin escalera) del muro > 3 m."""
    tall = [a for a in frange(C.DIAG_LANDMARK_END, LAT_END, 0.05)
            if edge_levels(a, tb)[0] > C.LATERAL_TALL_WALL]
    if not tall:
        return
    clear = BUTTRESS_WIDTH / 2 + 0.5
    free = [(tall[0] + clear, LAT_END - 0.5 - BUTTRESS_WIDTH / 2)]
    for f0, f1 in sorted(footprints):
        nxt = []
        for g0, g1 in free:
            if f1 + clear <= g0 or f0 - clear >= g1:
                nxt.append((g0, g1))
                continue
            if f0 - clear > g0:
                nxt.append((g0, f0 - clear))
            if f1 + clear < g1:
                nxt.append((f1 + clear, g1))
        free = nxt
    for g0, g1 in free:
        L = g1 - g0
        if L < 0:
            continue
        n = int(L // C.BUTTRESS_SPACING) + 1
        mid = (g0 + g1) / 2
        for i in range(n):
            a = mid + (i - (n - 1) / 2) * C.BUTTRESS_SPACING
            dz, z_hi, z_lo, _hi = edge_levels(a, tb)
            if dz <= C.LATERAL_TALL_WALL:
                continue
            d = T.face_run(dz)
            t_top = d * BUTTRESS_TOP_BELOW / dz + BUTTRESS_DEPTH_TOP
            zt = z_hi - BUTTRESS_TOP_BELOW
            prof = [(0.0, z_lo - EMBED), (d + BUTTRESS_DEPTH_BASE, z_lo - EMBED),
                    (d + BUTTRESS_DEPTH_BASE, z_lo), (t_top, zt), (0.0, zt)]
            mb.prism(prof, (0, 0, 0), (n_card[0], n_card[1], 0), (e[0], e[1], 0),
                     a - BUTTRESS_WIDTH / 2, a + BUTTRESS_WIDTH / 2)
            report.append({"r": round(a, 2), "wall_h": round(dz, 2)})
    report.append({"free_spans_r": [[round(g0, 2), round(g1, 2)] for g0, g1 in free]})


# ---------------------------------------------------------------------------
# Pretiles de borde de terraza (arcos)
# ---------------------------------------------------------------------------
def build_ring_parapets(mb, phi, report):
    for j, R in enumerate(T.terrace_jumps(), start=1):
        r0 = R + T.STEP_RUN / 2
        r1 = r0 + C.PARAPET_THICK
        z = T.terrace_level(j + 1)
        gap = degrees(asin((C.DIAG_STREET_WIDTH / 2) / r0))
        for a0, a1 in ((phi - C.MORADA_HALF_ANGLE, phi - gap), (phi + gap, phi + C.MORADA_HALF_ANGLE)):
            n = max(1, ceil(radians(a1 - a0) * r0 / PARAPET_CHORD))
            rings = []
            for i in range(n + 1):
                th = radians(a0 + (a1 - a0) * i / n)
                c, s = cos(th), sin(th)
                rings.append([(r0 * c, r0 * s, z - EMBED), (r1 * c, r1 * s, z - EMBED),
                              (r1 * c, r1 * s, z + C.PARAPET_LOW_H), (r0 * c, r0 * s, z + C.PARAPET_LOW_H)])
            mb.strip(rings)
        report.append({"r": round(r0, 3), "level": z, "h": C.PARAPET_LOW_H, "street_gap_m": C.DIAG_STREET_WIDTH})


# ---------------------------------------------------------------------------
# Escalinata diagonal
# ---------------------------------------------------------------------------
def escalinata_profile():
    """[(u0, u1, z)] de cada huella / descanso, y la secuencia de contrahuellas."""
    n1 = C.ESC_RISERS // 2
    risers = [T.ESC_U0 + i * C.ESC_TREAD for i in range(n1)]
    start2 = risers[-1] + C.ESC_LANDING
    risers += [start2 + i * C.ESC_TREAD for i in range(C.ESC_RISERS - n1)]
    assert abs(risers[-1] - T.ESC_U1) < 1e-9, "la escalinata no cabe exactamente en 95..105"
    treads = []
    for k in range(1, len(risers)):
        treads.append((risers[k - 1], risers[k], C.DATUM - k * C.ESC_RISER))
    return risers, treads


def build_escalinata(mb, phi, report):
    risers, treads = escalinata_profile()
    a = radians(phi)
    e = (cos(a), sin(a), 0.0)
    nrm = (-sin(a), cos(a), 0.0)
    zf = C.Z_MORADAS_MIN - 0.5
    top = C.DATUM + 0.01
    prof = [(T.ESC_U0 - 0.1, zf), (T.ESC_U1, zf)]
    for u0, u1, z in reversed(treads):
        prof += [(u1, z), (u0, z)]
    prof += [(T.ESC_U0, top), (T.ESC_U0 - 0.1, top)]
    # limpia puntos repetidos consecutivos
    clean = [prof[0]]
    for p in prof[1:]:
        if abs(p[0] - clean[-1][0]) > 1e-9 or abs(p[1] - clean[-1][1]) > 1e-9:
            clean.append(p)
    mb.prism(clean, (0, 0, 0), e, nrm, -T.ESC_HALF_W, T.ESC_HALF_W)
    # pasamanos escalonados (0.9 m sobre cada huella)
    bal = [(T.ESC_U0 - 0.5, zf), (T.ESC_U1, zf)]
    for u0, u1, z in reversed(treads):
        bal += [(u1, z + C.ESC_BALUSTRADE_H), (u0, z + C.ESC_BALUSTRADE_H)]
    bal += [(T.ESC_U0, C.DATUM + C.ESC_BALUSTRADE_H), (T.ESC_U0 - 0.5, C.DATUM + C.ESC_BALUSTRADE_H)]
    for w0, w1 in ((T.ESC_HALF_W, T.ESC_HALF_OUT), (-T.ESC_HALF_OUT, -T.ESC_HALF_W)):
        mb.prism(bal, (0, 0, 0), e, nrm, w0, w1)
    report.update({"width_m": C.ESC_WIDTH, "risers": len(risers), "riser_m": C.ESC_RISER, "tread_m": C.ESC_TREAD,
                   "landing_m": C.ESC_LANDING, "riser_positions_r": risers,
                   "balustrade_h_m": C.ESC_BALUSTRADE_H})


# ---------------------------------------------------------------------------
def build(scene, stats):
    mat = stone_material()
    col_m = bpy.data.collections["MORADAS"]
    col_s = bpy.data.collections["STREETS"]
    out = {"objects": {}, "stairs": [], "buttresses": {}, "lateral_parapets": {}, "ring_parapets": {},
           "escalinata": {}, "lateral_wall_heights": {}}
    edges = T.lateral_edges()
    for key, phi in T.DIAGONAL_ANGLE.items():
        mb_par, mb_but, mb_sta, mb_esc = MeshBuilder(), MeshBuilder(), MeshBuilder(), MeshBuilder()
        for k2, side, tb, e, n_card in edges:
            if k2 != key:
                continue
            tag = f"{key}{side:+d}"
            gaps, fps = build_lateral_stairs(mb_sta, key, side, tb, e, n_card, out["stairs"])
            out["lateral_parapets"][tag] = []
            build_lateral_parapets(mb_par, tb, e, n_card, gaps, out["lateral_parapets"][tag])
            out["buttresses"][tag] = []
            build_buttresses(mb_but, tb, e, n_card, fps, out["buttresses"][tag])
            # alturas reales del muro lateral por terraza (min / max)
            hs = {}
            for a in frange(C.DIAG_LANDMARK_END, LAT_END, 0.25):
                k = T.terrace_index(a) or (0 if a < C.TERRACE_START_R else 7)
                dz = edge_levels(a, tb)[0]
                lo, hi = hs.get(k, (dz, dz))
                hs[k] = (min(lo, dz), max(hi, dz))
            out["lateral_wall_heights"][tag] = {str(k): [round(v[0], 2), round(v[1], 2)] for k, v in sorted(hs.items())}
        out["ring_parapets"][key] = []
        build_ring_parapets(mb_par, phi, out["ring_parapets"][key])
        out["escalinata"][key] = {}
        build_escalinata(mb_esc, phi, out["escalinata"][key])
        for name, mb, col in ((f"TRN_Parapets_{key}", mb_par, col_m), (f"TRN_Buttresses_{key}", mb_but, col_m),
                              (f"TRN_LateralStairs_{key}", mb_sta, col_m), (f"TRN_Escalinata_{key}", mb_esc, col_s)):
            obj = mb.to_object(name, col, mat)
            if obj:
                out["objects"][name] = {"tris": len(obj.data.polygons), "collection": col.name}
    stats["structures"] = out
    return out


if __name__ == "__main__":
    print("Usar build_stage02.py")
