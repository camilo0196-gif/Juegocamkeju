"""
CONCORDIA - Etapa 02: terreno base de la colina (TRN_City).  v2

Genera TRN_City (malla MAESTRA de 1 m) en la coleccion TERRAIN.

Pasos
 1. Grid 424 x 424 m, celdas de 1 m, centrado; se eliminan vertices con r > 212.
 2. Cortes (bmesh) donde el terreno tiene aristas vivas:
    - anillos de cada salto de terraza y del pie de muralla diagonal,
    - bordes laterales Morada/cardinal (linea superior + linea inferior del muro),
    - bordes de la banda del eje de cada avenida (plazoleta),
    - huella de la escalinata diagonal (rebaje bajo los peldanos).
 3. Altura h(x, y) de terrain_profile.py + ruido urbano de 5 cm p-p
    (sin ruido en la plaza, base de muralla, talud y a < 1.5 m de cualquier muro).
 4. Triangulacion fija (BEAUTY), normales hacia arriba.
 5. Vertex groups, color attributes (mascaras) y UV plana sin costuras.

Uso independiente:
    python tools/blender/stage02_terrain.py [--in ...v01.blend] [--out ...v02.blend]
(Normalmente se llama desde build_stage02.py.)
"""

import argparse
import json
import os
import sys
from math import acos, atan2, cos, degrees, radians, sin, sqrt

import bpy  # noqa: I001  (bpy debe importarse antes que bmesh en el modulo pip)
import bmesh
from mathutils import Vector, kdtree, noise

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import concordia_const as C  # noqa: E402
import terrain_profile as T  # noqa: E402

REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
DEFAULT_IN = os.path.join(REPO, "blender", f"{C.BLEND_BASENAME}_v01.blend")
DEFAULT_OUT = os.path.join(REPO, "blender", f"{C.BLEND_BASENAME}_v02.blend")
DEFAULT_REPORT = os.path.join(REPO, "docs", "reports", "stage02_terrain.json")

OBJ_NAME = "TRN_City"

# --- Parametros (semilla fija => regenerable) -------------------------------
SEED = 1977
NOISE_SCALE_1 = 12.0
NOISE_SCALE_2 = 4.0
NOISE_W2 = 0.30
NOISE_FADE_IN = (60.0, 64.0)        # sin ruido en la plaza
NOISE_FADE_OUT = (192.0, 196.0)     # sin ruido en la base de muralla ni el talud
NOISE_WALL_FADE = (0.3, 2.5)        # sin ruido junto a muros (aristas limpias, piezas a ras)
NOISE_SLOPE_FADE = (2.0, 3.5)       # grados de pendiente base: ruido completo -> sin ruido

RING_SNAP_EPS = 0.05
ON_RING_TOL = 1e-5
KNIFE_SNAP_EPS = 0.03
SNAP_OUTER_BOUNDARY = True

RETAIN_MIN_SLOPE = 70.0
SHARP_ANGLE = 40.0             # aristas vivas (grados entre caras)
STONE_SLOPE = (25.0, 35.0)
DIRT_FOOT_DIST = 2.0
DIRT_NOISE_SCALE = 25.0

BASE_ROW = 0.6                      # fila de vertices a 0.6 m del pie de cada muro (banda de AO limpia)
LAT_D_MAX = T.face_run(C.Z_MORADAS_MAX - C.Z_CARDINAL_END)   # 0.88 m

VGROUPS = ("plaza", "landmarks", "sector_mercado", "sector_oficios", "sector_clases",
           "sector_razas", "sector_moradas", "terraza_id", "talud", "base_muralla")
CARD_VG = {"Mercado": "sector_mercado", "Oficios": "sector_oficios",
           "Clases": "sector_clases", "Razas": "sector_razas"}


def parse_args():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    p = argparse.ArgumentParser()
    p.add_argument("--in", dest="inp", default=DEFAULT_IN)
    p.add_argument("--out", default=DEFAULT_OUT)
    p.add_argument("--report", default=DEFAULT_REPORT)
    return p.parse_args(argv)


def rxy(co):
    return sqrt(co.x * co.x + co.y * co.y)


# ---------------------------------------------------------------------------
# 1. Grid
# ---------------------------------------------------------------------------
def build_grid(stats):
    cell = C.TERRAIN_CELL
    n = int(round(C.TERRAIN_GRID_SIZE / cell))
    half = C.TERRAIN_GRID_SIZE / 2.0
    bm = bmesh.new()
    rows = []
    for j in range(n + 1):
        y = -half + j * cell
        rows.append([bm.verts.new((-half + i * cell, y, 0.0)) for i in range(n + 1)])
    for j in range(n):
        a, b = rows[j], rows[j + 1]
        for i in range(n):
            bm.faces.new((a[i], a[i + 1], b[i + 1], b[i]))
    stats["grid_verts"] = len(bm.verts)
    stats["grid_faces"] = len(bm.faces)
    R2 = C.TERRAIN_RADIUS ** 2 + 1e-9
    kill = [v for v in bm.verts if v.co.x ** 2 + v.co.y ** 2 > R2]
    bmesh.ops.delete(bm, geom=kill, context="VERTS")
    stats["deleted_verts_r_gt_212"] = len(kill)

    n_wire = n_loose = 0

    def clean_loose():
        nonlocal n_wire, n_loose
        wire = [e for e in bm.edges if e.is_wire]
        bmesh.ops.delete(bm, geom=wire, context="EDGES")
        loose = [v for v in bm.verts if not v.link_edges]
        bmesh.ops.delete(bm, geom=loose, context="VERTS")
        n_wire += len(wire)
        n_loose += len(loose)

    clean_loose()
    bowtie = 0
    for _ in range(20):
        bad = [v for v in bm.verts if v.link_faces and not v.is_manifold]
        if not bad:
            break
        for v in bad:
            if not v.is_valid or v.is_manifold or not v.link_faces:
                continue
            f = max(v.link_faces, key=lambda f: rxy(f.calc_center_median()))
            bmesh.ops.delete(bm, geom=[f], context="FACES_ONLY")
            bowtie += 1
        clean_loose()
    stats["cleanup"] = {"bowtie_faces_removed": bowtie, "wire_edges": n_wire, "loose_verts": n_loose}
    if SNAP_OUTER_BOUNDARY:
        bverts = {v for e in bm.edges if e.is_boundary for v in e.verts}
        moved = 0.0
        for v in bverts:
            r = rxy(v.co)
            moved = max(moved, C.TERRAIN_RADIUS - r)
            v.co.x *= C.TERRAIN_RADIUS / r
            v.co.y *= C.TERRAIN_RADIUS / r
        stats["outer_boundary_snap"] = {"verts": len(bverts), "max_move_m": round(moved, 4)}
    return bm


# ---------------------------------------------------------------------------
# 2a. Anillos (circulos) de las terrazas
# ---------------------------------------------------------------------------
def in_ring_range(x, y):
    r = sqrt(x * x + y * y)
    return T.s_lateral(r, T.angle_deg(x, y)) >= -(LAT_D_MAX + 0.3)


def snap_band(bm, r_in, r_out, locked):
    on_in, on_out = set(), set()
    lo, hi = r_in - RING_SNAP_EPS, r_out + RING_SNAP_EPS
    for v in bm.verts:
        r = rxy(v.co)
        if lo <= r <= hi and in_ring_range(v.co.x, v.co.y):
            target = r_in if (r - r_in) <= (r_out - r) else r_out
            v.co.x *= target / r
            v.co.y *= target / r
            (on_in if target == r_in else on_out).add(v)
            locked.add(v)
    return on_in, on_out


def connect_sorted(bm, verts_sorted, max_gap=2.5):
    connected = missed = 0
    for a, b in zip(verts_sorted, verts_sorted[1:]):
        if (a.co.xy - b.co.xy).length > max_gap:
            continue
        if any(e.other_vert(a) is b for e in a.link_edges):
            continue
        common = set(a.link_faces) & set(b.link_faces)
        if not common:
            missed += 1
            continue
        bmesh.utils.face_split(next(iter(common)), a, b)
        connected += 1
    return connected, missed


def cut_ring(bm, R, ring, locked):
    crossing = []
    for e in bm.edges:
        a, b = e.verts
        da, db = rxy(a.co) - R, rxy(b.co) - R
        if abs(da) < ON_RING_TOL or abs(db) < ON_RING_TOL:
            continue
        if da * db < 0.0:
            crossing.append(e)
    for e in crossing:
        a, b = e.verts
        pa, pb = a.co.xy, b.co.xy
        d = pb - pa
        A, B, Cq = d.dot(d), 2.0 * pa.dot(d), pa.dot(pa) - R * R
        disc = max(B * B - 4.0 * A * Cq, 0.0)
        t = next((c for c in ((-B + sqrt(disc)) / (2 * A), (-B - sqrt(disc)) / (2 * A)) if 0.0 < c < 1.0), None)
        if t is None:
            continue
        p = pa + d * t
        if not in_ring_range(p.x, p.y):
            continue
        _ne, nv = bmesh.utils.edge_split(e, a, t)
        nv.co = (p.x * R / p.length, p.y * R / p.length, 0.0)
        ring.add(nv)
        locked.add(nv)
    verts = sorted(ring, key=lambda v: atan2(v.co.y, v.co.x))
    connected, missed = connect_sorted(bm, verts)
    return {"R": round(R, 4), "verts": len(ring), "new_edges": connected, "missed": missed}


# ---------------------------------------------------------------------------
# 2b. Cuchillo por polilinea (rectas y curvas abiertas)
# ---------------------------------------------------------------------------
def _seg_closest(p, a, b):
    ab = b - a
    L2 = ab.dot(ab)
    t = 0.0 if L2 == 0 else max(0.0, min(1.0, (p - a).dot(ab) / L2))
    q = a + ab * t
    return (p - q).length, q, t


def _seg_intersect(p, p2, a, b):
    """Interseccion de segmentos p-p2 y a-b. Devuelve (t_p, t_ab) o None."""
    r = p2 - p
    s = b - a
    den = r.x * s.y - r.y * s.x
    if abs(den) < 1e-12:
        return None
    q = a - p
    t = (q.x * s.y - q.y * s.x) / den
    u = (q.x * r.y - q.y * r.x) / den
    if 1e-6 < t < 1.0 - 1e-6 and -1e-9 <= u <= 1.0 + 1e-9:
        return t, u
    return None


def knife_polyline(bm, pts, locked, name="", snap_eps=KNIFE_SNAP_EPS):
    pts = [Vector(p) for p in pts]
    if len(pts) < 2:
        return {"name": name, "verts": 0}
    xs = [p.x for p in pts]
    ys = [p.y for p in pts]
    x0, x1, y0, y1 = min(xs) - 1.5, max(xs) + 1.5, min(ys) - 1.5, max(ys) + 1.5
    cells = {}
    for i in range(len(pts) - 1):
        a, b = pts[i], pts[i + 1]
        for cx in range(int(min(a.x, b.x) // 1) - 1, int(max(a.x, b.x) // 1) + 2):
            for cy in range(int(min(a.y, b.y) // 1) - 1, int(max(a.y, b.y) // 1) + 2):
                cells.setdefault((cx, cy), []).append(i)

    def near_segs(x, y):
        return cells.get((int(x // 1), int(y // 1)), ())

    on_line = {}
    for v in bm.verts:
        x, y = v.co.x, v.co.y
        if not (x0 <= x <= x1 and y0 <= y <= y1):
            continue
        best = None
        p = v.co.xy
        for i in near_segs(x, y):
            dist, q, t = _seg_closest(p, pts[i], pts[i + 1])
            if best is None or dist < best[0]:
                best = (dist, q, i + t)
        if best and best[0] < snap_eps:
            if v not in locked:
                v.co.x, v.co.y = best[1].x, best[1].y
            on_line[v] = best[2]
    hits = []
    for e in bm.edges:
        a, b = e.verts
        if a in on_line or b in on_line:
            continue
        ax, ay, bx, by = a.co.x, a.co.y, b.co.x, b.co.y
        if max(ax, bx) < x0 or min(ax, bx) > x1 or max(ay, by) < y0 or min(ay, by) > y1:
            continue
        cand = set(near_segs(ax, ay)) | set(near_segs(bx, by))
        for i in sorted(cand):
            res = _seg_intersect(a.co.xy, b.co.xy, pts[i], pts[i + 1])
            if res:
                hits.append((e, a, res[0], i + res[1]))
                break
    for e, a, t, param in hits:
        if not e.is_valid:
            continue
        p = a.co.xy.lerp(e.other_vert(a).co.xy, t)
        _ne, nv = bmesh.utils.edge_split(e, a, t)
        nv.co.x, nv.co.y = p.x, p.y
        on_line[nv] = param
    verts = sorted(on_line, key=lambda v: on_line[v])
    for v in verts:
        locked.add(v)
    connected, missed = connect_sorted(bm, verts)
    return {"name": name, "verts": len(verts), "new_edges": connected, "missed": missed}


def frame_pts(origin_deg, us, v):
    a = radians(origin_deg)
    cu, su = cos(a), sin(a)
    return [(u * cu - v * su, u * su + v * cu) for u in us]


def frange(a, b, step):
    n = max(1, int(round((b - a) / step)))
    return [a + (b - a) * i / n for i in range(n + 1)]


def lateral_polylines():
    """Linea superior (borde) y lineas inferiores (pie del muro) de cada borde lateral."""
    out = []
    jumps = T.terrace_jumps() + list(T.wall_step_rings())
    for key, side, tb, e, n in T.lateral_edges():
        a_list = frange(C.RING_DESCENT[1] - 1.0, C.WALL_BASE_R[1] + 1.0, 0.25)
        fine = []
        for R in jumps:
            fine += frange(R - 0.35, R + 0.35, 0.02)
        a_list = sorted(set(round(a, 4) for a in a_list + fine))
        out.append((f"lat_top_{key}_{side:+d}", [(a * e[0], a * e[1]) for a in (a_list[0], a_list[-1])]))
        cur, row, cur_sign = [], [], None
        for a in a_list:
            dz = T.lateral_dz(a, tb)
            d = T.face_run(dz)
            sign = 1.0 if dz >= 0 else -1.0          # dz>=0: pie del muro en el lado cardinal
            px = a * e[0] + sign * d * n[0]
            py = a * e[1] + sign * d * n[1]
            if cur_sign is not None and sign != cur_sign:
                out.append((f"lat_bot_{key}_{side:+d}", cur))
                out.append((f"lat_row_{key}_{side:+d}", row))
                cur, row = [], []
            cur.append((px, py))
            df = d + BASE_ROW
            row.append((a * e[0] + sign * df * n[0], a * e[1] + sign * df * n[1]))
            cur_sign = sign
        out.append((f"lat_bot_{key}_{side:+d}", cur))
        out.append((f"lat_row_{key}_{side:+d}", row))
    return out


def band_polylines():
    out = []
    u_list = frange(C.AXIS_DESCENT[0] - 1.0, C.AXIS_PLAZOLETA[1] + 1.0, 0.25)
    for key, phi in T.CARDINAL_ANGLE.items():
        for side in (-1, 1):
            out.append((f"band_top_{key}_{side:+d}", frame_pts(phi, (u_list[0], u_list[-1]), side * T.HALF_BAND)))
            cur, row, cur_sign = [], [], None
            for u in u_list:
                zb = T.prof_axis(u)
                v_edge = side * T.HALF_BAND
                x, y = frame_pts(phi, (u,), v_edge)[0]
                zo = T.prof_card(sqrt(x * x + y * y))
                dz = (zb - zo) if zb is not None else 0.0
                d = T.face_run(dz)
                sign = 1.0 if dz >= 0 else -1.0       # dz>=0 banda alta: pie fuera de la banda
                v = side * (T.HALF_BAND + sign * d)
                vr = side * (T.HALF_BAND + sign * (d + BASE_ROW))
                if cur_sign is not None and sign != cur_sign:
                    out.append((f"band_bot_{key}_{side:+d}", cur))
                    out.append((f"band_row_{key}_{side:+d}", row))
                    cur, row = [], []
                cur.append(frame_pts(phi, (u,), v)[0])
                row.append(frame_pts(phi, (u,), vr)[0])
                cur_sign = sign
            out.append((f"band_bot_{key}_{side:+d}", cur))
            out.append((f"band_row_{key}_{side:+d}", row))
    return out


def escalinata_polylines():
    out = []
    for key, phi in T.DIAGONAL_ANGLE.items():
        for u in (T.ESC_U0 - T.ESC_EDGE, T.ESC_U0, T.ESC_U1, T.ESC_U1 + T.ESC_EDGE):
            out.append((f"esc_u{u:.2f}_{key}", [frame_pts(phi, (u,), v)[0] for v in (-T.ESC_HALF_OUT - 1.5,
                                                                                    T.ESC_HALF_OUT + 1.5)]))
        for v in (-T.ESC_HALF_OUT, -T.ESC_HALF_W, T.ESC_HALF_W, T.ESC_HALF_OUT):
            out.append((f"esc_v{v:+.2f}_{key}", frame_pts(phi, (T.ESC_U0 - 1.5, T.ESC_U1 + 1.5), v)))
    return out


def insert_cuts(bm, stats):
    locked = set()
    rings = []
    for r_in, r_out in T.ring_pairs():
        on_in, on_out = snap_band(bm, r_in, r_out, locked)
        rings.append(cut_ring(bm, r_in, on_in, locked))
        rings.append(cut_ring(bm, r_out, on_out, locked))
    for R in T.terrace_jumps():                       # fila al pie de cada salto (lado bajo)
        rf = R - T.STEP_RUN / 2 - BASE_ROW
        on_f, _ = snap_band(bm, rf, rf, locked)
        rings.append(cut_ring(bm, rf, on_f, locked))
    knives = []
    for name, pts in lateral_polylines() + band_polylines() + escalinata_polylines():
        knives.append(knife_polyline(bm, pts, locked, name))
    stats["rings"] = rings
    stats["knives"] = {"count": len(knives), "verts": sum(k["verts"] for k in knives),
                       "missed": sum(k.get("missed", 0) for k in knives),
                       "worst": sorted(knives, key=lambda k: -k.get("missed", 0))[:3]}


# ---------------------------------------------------------------------------
# 3. Alturas + ruido
# ---------------------------------------------------------------------------
def wall_distance(x, y):
    """Distancia (m) al muro mas cercano, medida desde el borde de su cara (arista superior
    o inferior). Sirve para apagar el ruido junto a muros y piezas."""
    r = sqrt(x * x + y * y)
    th = T.angle_deg(x, y)
    d = 1e9
    if r > C.RING_DESCENT[1]:
        s = T.s_lateral(r, th)
        dz = T.prof_diag(r) - T.card_z(x, y, r, th)
        low_side = (dz >= 0 and s < 0) or (dz < 0 and s > 0)
        d = max(0.0, abs(s) - T.face_run(dz)) if low_side else abs(s)
        if s > -2.0:
            d = min([d] + [max(0.0, abs(r - R) - T.STEP_RUN / 2) for R in T.terrace_jumps()]
                    + [max(0.0, abs(r - C.WALL_BASE_R[1]) - T.WALL_STEP_RUN)])
    u, v = T.axis_frame(x, y, T.CARDINAL_ANGLE[T.nearest_cardinal(th)])
    if C.AXIS_DESCENT[0] - 2 <= u <= C.AXIS_PLAZOLETA[1] + 2:
        zb = T.prof_axis(u)
        db = T.face_run(zb - T.prof_card(r)) if zb is not None else 0.0
        d = min(d, max(0.0, abs(abs(v) - T.HALF_BAND) - db))
    ue, ve = T.axis_frame(x, y, T.DIAGONAL_ANGLE[T.nearest_diagonal(th)])
    if T.ESC_U0 - 2 <= ue <= T.ESC_U1 + 2 and abs(ve) <= T.ESC_HALF_OUT + 2:
        d = 0.0
    return d


def base_slope_deg(x, y, h=0.5):
    gx = (T.height(x + h, y) - T.height(x - h, y)) / (2 * h)
    gy = (T.height(x, y + h) - T.height(x, y - h)) / (2 * h)
    return degrees(atan2(sqrt(gx * gx + gy * gy), 1.0))


def noise_mask(x, y):
    r = sqrt(x * x + y * y)
    m = T.smoothstep(*NOISE_FADE_IN, r) * (1.0 - T.smoothstep(*NOISE_FADE_OUT, r))
    if m <= 0.0:
        return 0.0
    m *= T.smoothstep(*NOISE_WALL_FADE, wall_distance(x, y))
    if m <= 0.0:
        return 0.0
    # en rampas cerca del limite caminable el ruido se atenua (no debe sumar pendiente)
    return m * (1.0 - T.smoothstep(*NOISE_SLOPE_FADE, base_slope_deg(x, y)))


def apply_heights(bm, stats):
    off = Vector((SEED * 0.1371, SEED * 0.7313, SEED * 0.0193))
    raw, mask = {}, {}
    for v in bm.verts:
        m = noise_mask(v.co.x, v.co.y)
        if m > 0.0:
            p = Vector((v.co.x, v.co.y, 0.0))
            raw[v] = (noise.noise(p / NOISE_SCALE_1 + off, noise_basis="PERLIN_NEW")
                      + NOISE_W2 * noise.noise(p / NOISE_SCALE_2 - off, noise_basis="PERLIN_NEW"))
            mask[v] = m
    lo, hi = min(raw.values()), max(raw.values())
    mid, span = (lo + hi) / 2.0, (hi - lo)
    for v in bm.verts:
        z = T.height(v.co.x, v.co.y)
        if v in raw:
            z += mask[v] * (raw[v] - mid) / span * C.TERRAIN_NOISE_PP
        v.co.z = z
    stats["noise"] = {"seed": SEED, "pp_target_m": C.TERRAIN_NOISE_PP, "scales_m": [NOISE_SCALE_1, NOISE_SCALE_2],
                      "wall_fade_m": list(NOISE_WALL_FADE)}


# ---------------------------------------------------------------------------
# 5. Datos de vertice
# ---------------------------------------------------------------------------
def slope_deg(nz):
    return degrees(acos(max(-1.0, min(1.0, nz))))


def write_vertex_data(obj):
    me = obj.data
    nv = len(me.vertices)
    co = [v.co.copy() for v in me.vertices]
    rr = [rxy(c) for c in co]
    th = [T.angle_deg(c.x, c.y) for c in co]
    sl = [T.s_lateral(rr[i], th[i]) for i in range(nv)]

    vg = {name: obj.vertex_groups.new(name=name) for name in VGROUPS}
    for i in range(nv):
        r, diag = rr[i], sl[i] > 0.0
        if r <= C.PLAZA_RADIUS + 1e-6:
            vg["plaza"].add([i], 1.0, "REPLACE")
        if C.PLAZA_RADIUS < r <= C.DIAG_LANDMARK_END and diag:
            vg["landmarks"].add([i], 1.0, "REPLACE")
        if C.PLAZA_RADIUS < r < C.CARD_EMBANK_END and not diag:
            vg[CARD_VG[T.nearest_cardinal(th[i])]].add([i], 1.0, "REPLACE")
        if C.DIAG_LANDMARK_END < r < C.CARD_EMBANK_END and diag:
            vg["sector_moradas"].add([i], 1.0, "REPLACE")
        k = T.terrace_index(r)
        if k and diag:
            vg["terraza_id"].add([i], k / float(C.TERRACE_COUNT), "REPLACE")
        if C.WALL_BASE_R[0] <= r < C.WALL_BASE_R[1] - 1e-6:
            vg["base_muralla"].add([i], 1.0, "REPLACE")
        if r >= C.WALL_BASE_R[1] - 1e-6:
            vg["talud"].add([i], 1.0, "REPLACE")

    # caras de muro (cualquier cara >= 70 grados dentro de la ciudad)
    ret_face = [slope_deg(p.normal.z) >= RETAIN_MIN_SLOPE and rxy(p.center) < C.WALL_BASE_R[1] + 0.5
                for p in me.polygons]
    # pie de muro: vertices de caras de muro por debajo del centro de su cara
    base_pts = []
    for p in me.polygons:
        if ret_face[p.index]:
            zc = p.center.z
            for vi in p.vertices:
                if co[vi].z < zc - 0.05:
                    base_pts.append(co[vi])
    kd = kdtree.KDTree(len(base_pts))
    for i, c in enumerate(base_pts):
        kd.insert(c, i)
    kd.balance()

    vslope = [slope_deg(v.normal.z) for v in me.vertices]
    off = Vector((SEED * 0.311, SEED * 0.177, 3.7))
    stone_v, dirt_v = [0.0] * nv, [0.0] * nv
    for i in range(nv):
        r = rr[i]
        stone = max(1.0 if r <= C.PLAZA_RADIUS else 0.0,
                    1.0 if C.WALL_BASE_R[0] <= r < C.WALL_BASE_R[1] else 0.0,
                    T.smoothstep(*STONE_SLOPE, vslope[i]))
        foot = 0.0
        if base_pts:
            _c, _idx, dist = kd.find(co[i])
            if co[i].z <= _c.z + 0.1:
                foot = 1.0 - T.smoothstep(0.0, DIRT_FOOT_DIST, dist)
        n = noise.noise(Vector((co[i].x, co[i].y, 0.0)) / DIRT_NOISE_SCALE + off, noise_basis="PERLIN_NEW")
        dirt = max(0.0, min(1.0, 0.30 + 0.35 * n + 0.60 * foot))
        stone_v[i] = stone
        dirt_v[i] = dirt * (1.0 - stone)

    nl = len(me.loops)
    loop_v = [0] * nl
    me.loops.foreach_get("vertex_index", loop_v)
    loop_f = [0] * nl
    for p in me.polygons:
        for li in range(p.loop_start, p.loop_start + p.loop_total):
            loop_f[li] = p.index

    def color_attr(name, values):
        a = me.color_attributes.new(name=name, type="BYTE_COLOR", domain="CORNER")
        flat = []
        for val in values:
            flat.extend((val, val, val, 1.0))
        a.data.foreach_set("color", flat)

    color_attr("retaining_mask", [1.0 if ret_face[loop_f[li]] else 0.0 for li in range(nl)])
    color_attr("dirt_mask", [0.0 if ret_face[loop_f[li]] else dirt_v[loop_v[li]] for li in range(nl)])
    color_attr("stone_mask", [1.0 if ret_face[loop_f[li]] else stone_v[loop_v[li]] for li in range(nl)])
    me.color_attributes.active_color_name = "retaining_mask"

    uv = me.uv_layers.new(name="UVMap")
    half = C.TERRAIN_GRID_SIZE / 2.0
    flat = []
    for li in range(nl):
        c = co[loop_v[li]]
        flat.extend(((c.x + half) / C.TERRAIN_GRID_SIZE, (c.y + half) / C.TERRAIN_GRID_SIZE))
    uv.data.foreach_set("uv", flat)
    counts = {name: 0 for name in VGROUPS}
    idx = {vg[n].index: n for n in VGROUPS}
    for v in me.vertices:
        for g in v.groups:
            counts[idx[g.group]] += 1
    return {"retaining_faces": sum(ret_face), "vgroup_counts": counts}, ret_face


# ---------------------------------------------------------------------------
# QA de pendientes
# ---------------------------------------------------------------------------
MICRO_STEP = 0.10
WALKABLE = {"plaza", "descenso_60_90", "distrito_90_165", "plano_165_175", "rampa_175_196",
            "eje_90_150", "eje_rampa_150_176", "plazoleta_176_196", "hitos_90_95",
            "terrazas_105_189", "plataforma_189_196"}


def classify(x, y):
    r = sqrt(x * x + y * y)
    th = T.angle_deg(x, y)
    if r <= C.PLAZA_RADIUS:
        return "Plaza", "plaza"
    if r >= C.WALL_BASE_R[1]:
        return "Talud", "talud_204_212"
    if r <= C.RING_DESCENT[1]:
        sec = T.nearest_diagonal(th) if T.s_lateral(r, th) > 0 else T.nearest_cardinal(th)
        return sec, "descenso_60_90"
    s = T.s_lateral(r, th)
    dz = T.prof_diag(r) - T.card_z(x, y, r, th)
    d = T.face_run(dz)
    tol = 0.10
    in_strip = (-d - tol <= s <= tol) if dz >= 0 else (-tol <= s <= d + tol)
    if in_strip and abs(dz) > 0.005:
        return f"Borde_{T.nearest_cardinal(th)}_{T.nearest_diagonal(th)}", "muro_lateral"
    if s > 0:
        sec = T.nearest_diagonal(th)
        ue, ve = T.axis_frame(x, y, T.DIAGONAL_ANGLE[sec])
        if T.ESC_U0 - 0.5 <= ue <= T.ESC_U1 + 0.1 and abs(ve) <= T.ESC_HALF_OUT + 0.05:
            return sec, "bajo_escalinata"
        if any(abs(r - R) <= T.STEP_RUN / 2 + 0.06 for R in T.terrace_jumps()):
            return sec, "muro_terraza"
        w0, w1 = T.wall_step_rings()
        if w0 - 0.06 <= r <= w1 + 0.06:
            return sec, "muro_pie_muralla"
        if r <= C.DIAG_LANDMARK_END:
            return sec, "hitos_90_95"
        if r <= C.DIAG_RAMP_END:
            return sec, "rampa_95_105"
        if r <= C.TERRACE_END_R:
            return sec, "terrazas_105_189"
        if r <= C.WALL_BASE_R[0]:
            return sec, "plataforma_189_196"
        return sec, "base_muralla_196_204"
    sec = T.nearest_cardinal(th)
    u, v = T.axis_frame(x, y, T.CARDINAL_ANGLE[sec])
    zb = T.prof_axis(u) if u >= C.AXIS_DESCENT[0] - 1 else None
    if zb is not None:
        zo = T.prof_card(r)
        db = T.face_run(zb - zo)
        sb = T.HALF_BAND - abs(v)
        in_b = (-db - 0.10 <= sb <= 0.10) if zb >= zo else (-0.10 <= sb <= db + 0.10)
        if in_b and abs(zb - zo) > 0.005:
            return sec, "borde_eje"
        if sb > 0:
            if u <= C.AXIS_DESCENT[1]:
                return sec, "eje_90_150"
            if u <= C.AXIS_RAMP[1]:
                return sec, "eje_rampa_150_176"
            return sec, "plazoleta_176_196"
    if r <= C.CARD_SLOPE_END:
        return sec, "distrito_90_165"
    if r <= C.CARD_FLAT_END:
        return sec, "plano_165_175"
    if r <= C.CARD_EMBANK_END:
        return sec, "rampa_175_196"
    return sec, "base_muralla_196_204"


def slope_report(me):
    zones = {}
    bad_walk, micro = [], []
    for p in me.polygons:
        c = p.center
        s = slope_deg(p.normal.z)
        key = classify(c.x, c.y)
        if key[1] in WALKABLE and s > C.WALK_SLOPE_MAX:
            zs = [me.vertices[i].co.z for i in p.vertices]
            span = max(zs) - min(zs)
            if span <= C.TERRAIN_NOISE_PP:
                # desnivel <= 5 cm (tolerancia del suelo): cara diminuta en un cruce de cortes
                micro.append((key, round(c.x, 2), round(c.y, 2), round(s, 1), round(span, 3)))
                key = (key[0], "microirregularidad_le5cm")
            elif s <= C.STAIR_SLOPE:
                pass
            elif span < MICRO_STEP:
                # escalon < 10 cm (bordillo donde un muro pasa por desnivel 0): no es pendiente
                micro.append((key, round(c.x, 2), round(c.y, 2), round(s, 1), round(span, 3)))
                key = (key[0], "microbordillo_lt10cm")
            else:
                bad_walk.append((key, round(c.x, 2), round(c.y, 2), round(s, 1), round(span, 3)))
        zones.setdefault(key, []).append(s)
    table = {}
    for (sec, sub), vals in sorted(zones.items()):
        vals.sort()
        n = len(vals)
        table[f"{sec}/{sub}"] = {"faces": n, "max": round(vals[-1], 2), "p99": round(vals[int(0.99 * (n - 1))], 2),
                                 "mean": round(sum(vals) / n, 2), "gt5": sum(1 for v in vals if v > 5.0),
                                 "gt8": sum(1 for v in vals if v > 8.0)}
    per_sector = {}
    for key, d in table.items():
        sec, sub = key.split("/")
        if sub in WALKABLE:
            cur = per_sector.setdefault(sec, {"walk_max": 0.0, "walk_gt5": 0, "zone_of_max": ""})
            if d["max"] > cur["walk_max"]:
                cur["walk_max"], cur["zone_of_max"] = d["max"], sub
            cur["walk_gt5"] += d["gt5"]
    return table, per_sector, bad_walk, micro


def geometry_qa(bm, me):
    qa = {"verts": len(me.vertices), "tris": len(me.polygons),
          "all_tris": all(len(p.vertices) == 3 for p in me.polygons)}
    nz = [p.normal.z for p in me.polygons]
    qa["min_normal_z"] = round(min(nz), 4)
    qa["faces_normal_down_or_vertical"] = sum(1 for z in nz if z <= 0.0)
    qa["degenerate_faces_area_lt_1e-6"] = sum(1 for p in me.polygons if p.area < 1e-6)
    qa["min_face_area_m2"] = round(min(p.area for p in me.polygons), 6)
    qa["duplicate_verts_1e-4"] = len(bmesh.ops.find_doubles(bm, verts=bm.verts, dist=1e-4)["targetmap"])
    qa["non_manifold_edges"] = sum(1 for e in bm.edges if len(e.link_faces) > 2)
    qa["boundary_edges"] = sum(1 for e in bm.edges if e.is_boundary)
    qa["wire_edges"] = sum(1 for e in bm.edges if e.is_wire)
    zs = [v.co.z for v in me.vertices]
    qa["z_min"], qa["z_max"] = round(min(zs), 4), round(max(zs), 4)
    qa["r_max"] = round(max(rxy(v.co) for v in me.vertices), 4)
    dev = [v.co.z - T.height(v.co.x, v.co.y) for v in me.vertices]
    qa["noise_dev_min_m"], qa["noise_dev_max_m"] = round(min(dev), 4), round(max(dev), 4)
    return qa


def level_checks(obj):
    from mathutils.bvhtree import BVHTree
    bvh = BVHTree.FromObject(obj, bpy.context.evaluated_depsgraph_get())
    pts = [("plaza centro", 0, 0, 8.0), ("r90 Mercado (fuera eje)", 80, 90, 6.0),
           ("Mercado r170 fuera eje (plano 165-175)", 80, 170, 4.5),
           ("Mercado r196 fuera eje", 80, 196, 6.0), ("Mercado eje u150", 90, 150, 4.5),
           ("Mercado eje u176", 90, 176, 6.0), ("plazoleta Mercado u186", 90, 186, 6.0),
           ("plazoleta Mercado u186 v=+14", None, None, 6.0),
           ("Puerta N (marcador) r200", 90, 200, 6.0), ("hitos NE r92", 40, 92, 6.0),
           ("Morada NE r105 fuera escalinata", 40, 105, 4.5)]
    for k in range(1, 7):
        pts.append((f"terraza {k} NE (centro, fuera calle)", 40, C.TERRACE_START_R + C.TERRACE_DEPTH * (k - 0.5),
                    T.terrace_level(k)))
    pts += [("Morada NE r193", 40, 193, 9.5), ("talud r208 E", 0, 208, None)]
    out = []
    for name, ang, r, want in pts:
        if ang is None:
            x, y = 14.0, 186.0
        else:
            x, y, _ = C.polar(ang, r)
        hit = bvh.ray_cast(Vector((x, y, 100.0)), Vector((0, 0, -1)))
        z = hit[0].z if hit[0] else None
        exp = want if want is not None else T.height(x, y)
        out.append({"point": name, "z_mesh": None if z is None else round(z, 4), "z_expected": round(exp, 4),
                    "diff": None if z is None else round(z - exp, 4)})
    return out


# ---------------------------------------------------------------------------
def build(scene, stats):
    if OBJ_NAME in bpy.data.objects:
        bpy.data.objects.remove(bpy.data.objects[OBJ_NAME])
    if OBJ_NAME in bpy.data.meshes:
        bpy.data.meshes.remove(bpy.data.meshes[OBJ_NAME])
    bm = build_grid(stats)
    insert_cuts(bm, stats)
    apply_heights(bm, stats)
    bmesh.ops.triangulate(bm, faces=bm.faces[:], quad_method="BEAUTY", ngon_method="BEAUTY")
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    bm.normal_update()
    flipped = 0
    for f in bm.faces:
        if f.normal.z < 0.0:
            f.normal_flip()
            flipped += 1
    stats["faces_flipped_to_up"] = flipped
    me = bpy.data.meshes.new(OBJ_NAME)
    bm.to_mesh(me)
    me.update()
    me.shade_smooth()                                  # suave + aristas vivas en muros:
    me.set_sharp_from_angle(angle=radians(SHARP_ANGLE))  # el .glb solo parte vertices en los muros
    obj = bpy.data.objects.new(OBJ_NAME, me)
    bpy.data.collections["TERRAIN"].objects.link(obj)
    obj["generator"] = "tools/blender/stage02_terrain.py"
    obj["seed"] = SEED
    obj["role"] = "MASTER 1 m (no se exporta; ver TERRAIN_CHUNKS_LOD*)"
    obj["terraza_id_encoding"] = "weight = id / 6 (id 1..6, 0 = sin terraza)"
    vdata, _ret = write_vertex_data(obj)
    stats.update(vdata)
    stats["geometry"] = geometry_qa(bm, me)
    bm.free()
    table, per_sector, bad_walk, micro = slope_report(me)
    stats["slope_by_zone"] = table
    stats["slope_walkable_max_by_sector"] = per_sector
    stats["walkable_faces_gt8"] = {"count": len(bad_walk), "sample": bad_walk[:20]}
    stats["micro_steps_lt10cm"] = {"count": len(micro), "max_span_m": max([m[4] for m in micro], default=0.0),
                                   "sample": micro[:10]}
    stats["level_checks"] = level_checks(obj)
    return obj


def main():
    args = parse_args()
    bpy.ops.wm.open_mainfile(filepath=args.inp)
    stats = {}
    build(bpy.context.scene, stats)
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.wm.save_as_mainfile(filepath=args.out, compress=True)
    os.makedirs(os.path.dirname(args.report), exist_ok=True)
    with open(args.report, "w") as fh:
        json.dump(stats, fh, indent=1, ensure_ascii=False)
    print("saved:", args.out)


if __name__ == "__main__":
    main()
