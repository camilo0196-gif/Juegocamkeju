"""
CONCORDIA - etapa 05: aplica el plan de calles y parcelas (stage05_layout.py) a TRN_City.

1. Cortes (cuchillo con indice espacial): bordes de calle + linea de hombro a SHOULDER m (borde marcado),
   contornos de parcelas, plazas, zonas, 8 parches y surcos de carreta (Oficios).
2. Alturas:
   - calles: perfil por eje (terreno de la etapa 02 muestreado cada 0.5 m), anclado a las superficies de
     mayor prioridad que cruza (banda del eje, plazas, calles mayores) y limitado a ROAD_SLOPE_MAX; seccion
     con bombeo de CROWN m, desniveles suaves de +-UNDUL m, parches +-1.5 cm, surcos de 3 cm.
   - plazas nuevas (Armas, Provisiones, plazuelas): plano de minimos cuadrados del terreno.
   - parcelas: plataforma plana a la cota de la calle frente a su puerta.
   - banda del eje, plazoletas, fuente del Mercado y reserva del Cauce: terreno de la etapa 02 (solo mascaras).
   Los vertices del hombro conservan su cota: la franja de SHOULDER m forma el borde marcado.
3. Mascaras (CORNER, BYTE_COLOR): road_mask, wear_mask, cobble_type (valor = tipo / 8) y UV 'UVRoads'
   (x = road_mask, y = cobble_type + 0.99 * wear) + textura cenital T_StreetMasks.png.
4. Marcadores: MARKERS_DISTRICTS/<distrito> con MARKER_Bld_* (+Y = fachada de la puerta) y auxiliares.
"""

import json
import os
import sys
from math import atan2, ceil, cos, degrees, hypot, pi, radians, sin, sqrt, tan

import bmesh
import bpy
import numpy as np
from mathutils import Vector, noise

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import concordia_const as C  # noqa: E402
import stage02_terrain as S2  # noqa: E402
import stage05_layout as L  # noqa: E402
import terrain_profile as T  # noqa: E402

REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
SHOULDER = 0.30
CROWN = 0.025
UNDUL = 0.012
UNDUL_SCALE = 4.0
RUT_DEPTH, RUT_HALF = 0.03, 0.125
ROAD_SLOPE_MAX = 4.5
SNAP = 0.03
EDGE_FREE = 3.0          # m: franja junto al borde de una plaza donde manda la calle que la cruza (rampa)
COBBLE = {"none": 0, "cobble": 1, "patch": 2, "tamped_earth": 3, "flagstone": 4, "pad": 5, "existing": 0}
SURFACE_OF = {"cobble": "cobble", "flagstone": "flagstone", "cobble+tamped_earth": "cobble", "earth": "tamped_earth",
              "existing": "none"}
PLANAR_PLAZAS = ("training_square", "market_square", "plazuela")
KEEP_PLAZAS = ("axis_frontage", "plazoleta", "fountain_square", "stair_link", "portal_plaza")
WEAR_K = {"avenue": 1.0, "ring": 0.8, "diagonal": 0.6, "alley": 0.45}
DISTRICT_COLLECTIONS = {"Mercado": "MARKERS_Mercado", "Oficios": "MARKERS_Oficios", "Clases": "MARKERS_Clases",
                        "Razas": "MARKERS_Razas"}


# ---------------------------------------------------------------------------
# Cuchillo con indice espacial (misma logica que stage02_terrain.knife_polyline)
# ---------------------------------------------------------------------------
class EdgeIndex:
    CELL = 2.0

    def __init__(self, bm, r_min=55.0, r_max=200.0):
        self.cv, self.ce = {}, {}
        for v in bm.verts:
            r = hypot(v.co.x, v.co.y)
            if r_min - 2 <= r <= r_max + 2:
                self.add_v(v)
        for e in bm.edges:
            a, b = e.verts
            if r_min - 2 <= hypot(a.co.x, a.co.y) <= r_max + 2:
                self.add_e(e)

    def key(self, x, y):
        return (int(x // self.CELL), int(y // self.CELL))

    def add_v(self, v):
        self.cv.setdefault(self.key(v.co.x, v.co.y), set()).add(v)

    def add_e(self, e):
        a, b = e.verts
        k0 = self.key(min(a.co.x, b.co.x), min(a.co.y, b.co.y))
        k1 = self.key(max(a.co.x, b.co.x), max(a.co.y, b.co.y))
        for i in range(k0[0], k1[0] + 1):
            for j in range(k0[1], k1[1] + 1):
                self.ce.setdefault((i, j), set()).add(e)

    def query(self, x0, x1, y0, y1):
        k0, k1 = self.key(x0, y0), self.key(x1, y1)
        vs, es = set(), set()
        for i in range(k0[0], k1[0] + 1):
            for j in range(k0[1], k1[1] + 1):
                vs |= self.cv.get((i, j), set())
                es |= self.ce.get((i, j), set())
        return [v for v in vs if v.is_valid], [e for e in es if e.is_valid]


def knife(bm, idx, pts, locked, snap_eps=SNAP):
    """Corta la polilinea pts (lista de (x, y)) sobre la malla. Devuelve los vertices sobre la linea,
    ordenados por su parametro a lo largo de la polilinea (se unen una sola vez, tambien en los quiebros)."""
    pts = [Vector((p[0], p[1])) for p in pts]
    if len(pts) < 2:
        return []
    on = {}
    for i in range(len(pts) - 1):
        a, b = pts[i], pts[i + 1]
        if (b - a).length < 1e-4:
            continue
        x0, x1 = min(a.x, b.x) - 1.6, max(a.x, b.x) + 1.6
        y0, y1 = min(a.y, b.y) - 1.6, max(a.y, b.y) + 1.6
        verts, edges = idx.query(x0, x1, y0, y1)
        for v in verts:
            if v in on:
                continue
            d, q, t = S2._seg_closest(v.co.xy, a, b)
            if d < snap_eps:
                if v not in locked:
                    v.co.x, v.co.y = q.x, q.y
                on[v] = i + t
        hits = []
        for e in edges:
            va, vb = e.verts
            if va in on or vb in on:
                continue
            res = S2._seg_intersect(va.co.xy, vb.co.xy, a, b)
            if res:
                hits.append((e, va, res[0], res[1]))
        for e, va, t, u in hits:
            if not e.is_valid:
                continue
            p = va.co.xy.lerp(e.other_vert(va).co.xy, t)
            ne, nv = bmesh.utils.edge_split(e, va, t)
            nv.co.x, nv.co.y = p.x, p.y
            idx.add_v(nv)
            idx.add_e(ne)
            idx.add_e(e)
            on[nv] = i + u
    seq = sorted(on, key=lambda v: on[v])
    for v in seq:
        locked.add(v)
    S2.connect_sorted(bm, seq)
    if len(seq) > 2 and (pts[0] - pts[-1]).length < 1e-6:          # contorno cerrado
        S2.connect_sorted(bm, [seq[-1], seq[0]])
    for v in seq:
        for e in v.link_edges:
            idx.add_e(e)
    return seq


# ---------------------------------------------------------------------------
# Geometria auxiliar
# ---------------------------------------------------------------------------
def offset_polyline(pts, off):
    out = []
    n = len(pts)
    for i in range(n):
        a = pts[max(0, i - 1)]
        b = pts[min(n - 1, i + 1)]
        tx, ty = b[0] - a[0], b[1] - a[1]
        Lt = hypot(tx, ty) or 1.0
        nx, ny = -ty / Lt, tx / Lt
        if 0 < i < n - 1:                    # inglete: corrige la longitud en los quiebros
            t1 = (pts[i][0] - a[0], pts[i][1] - a[1])
            t2 = (b[0] - pts[i][0], b[1] - pts[i][1])
            l1, l2 = hypot(*t1) or 1.0, hypot(*t2) or 1.0
            cosang = (t1[0] * t2[0] + t1[1] * t2[1]) / (l1 * l2)
            k = 1.0 / max(0.5, sqrt((1 + cosang) / 2))
        else:
            k = 1.0
        out.append((pts[i][0] + nx * off * k, pts[i][1] + ny * off * k))
    return out


def runs_where(pts, keep):
    out, cur = [], []
    for p, k in zip(pts, keep):
        if k:
            cur.append(p)
        else:
            if len(cur) >= 2:
                out.append(cur)
            cur = []
    if len(cur) >= 2:
        out.append(cur)
    return out


_POLY_CACHE = {}


def _poly_arrays(pts, cum):
    key = id(pts)
    hit = _POLY_CACHE.get(key)
    if hit is not None and hit[0] is pts:
        return hit[1]
    P0 = np.asarray(pts[:-1], dtype=float)
    D = np.asarray(pts[1:], dtype=float) - P0
    L2 = (D * D).sum(1)
    arr = (P0, D, L2, np.asarray(cum[:-1], dtype=float), np.sqrt(L2))
    _POLY_CACHE[key] = (pts, arr)
    return arr


def closest_on_polyline(pts, cum, p):
    """(distancia, s, indice de segmento) del punto mas cercano de la polilinea a p (vectorizado)."""
    P0, D, L2, C0, Ls = _poly_arrays(pts, cum)
    q = np.asarray(p, dtype=float) - P0
    t = np.clip((q * D).sum(1) / np.maximum(L2, 1e-12), 0.0, 1.0)
    d2 = ((q - D * t[:, None]) ** 2).sum(1)
    i = int(np.argmin(d2))
    return float(sqrt(d2[i])), float(C0[i] + t[i] * Ls[i]), i


def point_in_poly_tol(x, y, poly, tol=1e-3):
    if L.point_in_poly(x, y, poly):
        return True
    return L.poly_edge_dist(x, y, poly) <= tol


# ---------------------------------------------------------------------------
# Superficies
# ---------------------------------------------------------------------------
class Surfaces:
    """Altura de cada elemento del plan (calles, plazas, parcelas, zonas)."""

    def __init__(self, lay, P):
        self.lay, self.P = lay, P
        self.fid = {}
        for d in P.features.values():
            self.fid[d["fid"]] = d
        self.plane = {}
        self.road_prof = {}
        self.pad = {}
        self.zone_z = {}
        for pz in lay["plazas"]:
            if pz["type"] in PLANAR_PLAZAS:
                self.plane[pz["name"]] = fit_plane(pz)
        roads = sorted(lay["roads"], key=lambda r: -r["priority"])
        for rd in roads:
            self.road_prof[rd["name"]] = self.profile(rd)
        for z in lay["zones"]:
            if z["type"] == "archery_range":
                cx, cy = L.poly_centroid(z["poly"])
                self.zone_z[z["name"]] = ("flat", T.height(cx, cy))
            elif z["type"] == "herb_terraces":
                self.zone_z[z["name"]] = ("steps", z)
        for pa in lay["parcels"]:
            if pa["type"] == "stall":
                continue
            a = radians(pa["angle"])
            f = (cos(a), sin(a))
            q = (pa["door"][0] + f[0] * (L.SETBACK + 0.3), pa["door"][1] + f[1] * (L.SETBACK + 0.3))
            zf = self.surface_z(q[0], q[1], exclude_parcels=True)
            self.pad[pa["name"]] = zf if zf is not None else T.height(*pa["door"])

    # -- calle -------------------------------------------------------------
    def profile(self, rd):
        pts = L.resample(rd["pts"], 0.5)
        cum = [0.0]
        for a, b in zip(pts, pts[1:]):
            cum.append(cum[-1] + hypot(b[0] - a[0], b[1] - a[1]))
        z = np.array([T.height(*p) for p in pts])
        pin = np.zeros(len(pts), dtype=bool)
        for i, p in enumerate(pts):
            zz = self.higher_surface(p, rd)
            if zz is not None:
                z[i] = zz
                pin[i] = True
        # suavizado + limite de pendiente con anclajes fijos
        m = tan(radians(ROAD_SLOPE_MAX))
        ds = np.diff(np.array(cum))
        free = ~pin
        for _ in range(3):
            zs = z.copy()
            k = 6
            for i in range(len(z)):
                if free[i]:
                    a, b = max(0, i - k), min(len(z), i + k + 1)
                    zs[i] = z[a:b].mean()
            z = np.where(free, zs, z)
            for _ in range(2):
                for i in range(1, len(z)):
                    if free[i]:
                        z[i] = min(max(z[i], z[i - 1] - m * ds[i - 1]), z[i - 1] + m * ds[i - 1])
                for i in range(len(z) - 2, -1, -1):
                    if free[i]:
                        z[i] = min(max(z[i], z[i + 1] - m * ds[i]), z[i + 1] + m * ds[i])
        slope = np.degrees(np.arctan(np.abs(np.diff(z)) / np.maximum(ds, 1e-6))) if len(z) > 1 else np.zeros(1)
        return {"pts": pts, "cum": cum, "z": z, "pinned": int(pin.sum()), "slope_max": float(slope.max())}

    def higher_surface(self, p, rd):
        """Cota de una superficie de mayor prioridad que la calle rd en p (o None)."""
        x, y = p
        best = None
        for f in self.candidates(x, y):
            d = self.fid[f]
            if d is rd:
                continue
            if d["kind"] == "plaza":
                if d["type"] == "portal_plaza" and hypot(x, y) <= C.PLAZA_RADIUS:
                    return T.height(x, y)
                if self.depth_in_plaza(d, x, y) >= EDGE_FREE:
                    if d["type"] in PLANAR_PLAZAS:
                        return self.plane_z(d["name"], x, y)
                    if d["type"] in KEEP_PLAZAS:
                        best = T.height(x, y)
            elif d["kind"] == "road" and d["priority"] > rd["priority"] and d["name"] in self.road_prof:
                pr = self.road_prof[d["name"]]
                dd, _s, _i = closest_on_polyline(pr["pts"], pr["cum"], p)
                if dd <= d["halfw"][0] + 1e-3 and best is None:
                    best = self.road_center_z(d, x, y)
        return best

    def candidates(self, x, y, rad=1):
        g = self.P.g
        i = int((x + L.EXTENT) / g.cell)
        j = int((y + L.EXTENT) / g.cell)
        sub = g.lab[max(0, j - rad):j + rad + 1, max(0, i - rad):i + rad + 1]
        return [int(f) for f in np.unique(sub) if f > 0]

    def inside_plaza(self, d, x, y):
        if "circle" in d:
            c, R = d["circle"]["c"], d["circle"]["R"]
            return hypot(x - c[0], y - c[1]) <= R + 1e-3
        return point_in_poly_tol(x, y, d["poly"])

    def depth_in_plaza(self, d, x, y):
        """Distancia al borde (>0 dentro). La plaza del Portal solo cuenta su borde r = 60."""
        if "circle" in d:
            c, R = d["circle"]["c"], d["circle"]["R"]
            return R - hypot(x - c[0], y - c[1])
        if L.point_in_poly(x, y, d["poly"]):
            return L.poly_edge_dist(x, y, d["poly"])
        return -L.poly_edge_dist(x, y, d["poly"])

    def plane_z(self, name, x, y):
        a, b, c = self.plane[name]
        return a * x + b * y + c

    def road_center_z(self, rd, x, y):
        pr = self.road_prof[rd["name"]]
        d, s, _i = closest_on_polyline(pr["pts"], pr["cum"], (x, y))
        return float(np.interp(s, pr["cum"], pr["z"]))

    def road_z(self, rd, x, y):
        pr = self.road_prof[rd["name"]]
        d, s, _i = closest_on_polyline(pr["pts"], pr["cum"], (x, y))
        z = float(np.interp(s, pr["cum"], pr["z"]))
        hw = rd["halfw"][0]
        z += CROWN * max(0.0, 1.0 - (d / hw) ** 2)
        z += UNDUL * noise.noise(Vector((x / UNDUL_SCALE, y / UNDUL_SCALE, 7.3)), noise_basis="PERLIN_NEW")
        return z, d

    # -- consulta general ---------------------------------------------------
    def classify(self, x, y, exclude_parcels=False):
        """(tipo, elemento) del elemento de mayor prioridad que contiene (x, y)."""
        cands = [self.fid[f] for f in self.candidates(x, y, rad=2)]
        if not exclude_parcels:
            for d in cands:
                if d["kind"] == "parcel" and d["type"] != "stall":
                    if (d["shape"] == "circle" and hypot(x - d["center"][0], y - d["center"][1]) <= d["w"] / 2 + 1e-3) \
                            or (d["shape"] == "rect" and point_in_poly_tol(x, y, d["poly"])):
                        return "parcel", d
        for d in cands:
            if d["kind"] == "zone" and d["type"] in ("archery_range", "herb_terraces") and point_in_poly_tol(x, y, d["poly"]):
                return "zone", d
        best = None
        for d in cands:
            if d["kind"] == "road":
                pr = self.road_prof[d["name"]]
                dd, _s, _i = closest_on_polyline(pr["pts"], pr["cum"], (x, y))
                if dd <= d["halfw"][0] + 1e-3 and (best is None or d["priority"] > best["priority"]):
                    best = d
        for kind, types in (("plaza", PLANAR_PLAZAS), ("keep", KEEP_PLAZAS)):
            for d in cands:
                if d["kind"] == "plaza" and d["type"] in types and d["type"] != "portal_plaza" \
                        and self.inside_plaza(d, x, y):
                    if best is not None and self.depth_in_plaza(d, x, y) < EDGE_FREE:
                        return "road", best              # la calle cruza el borde de la plaza: rampa
                    return kind, d
        if best is not None:
            return "road", best
        for d in cands:
            if d["kind"] == "zone" and point_in_poly_tol(x, y, d["poly"]):
                return "zone_keep", d
        return None, None

    def surface_z(self, x, y, exclude_parcels=False):
        kind, d = self.classify(x, y, exclude_parcels)
        if kind is None:
            return None
        return self.z_of(kind, d, x, y)

    def z_of(self, kind, d, x, y):
        if kind == "parcel":
            return self.pad[d["name"]]
        if kind == "plaza":
            return self.plane_z(d["name"], x, y)
        if kind in ("keep", "zone_keep"):
            return T.height(x, y)
        if kind == "zone":
            mode, val = self.zone_z[d["name"]]
            if mode == "flat":
                return val
            return terrace_z(val, x, y)
        if kind == "road":
            return self.road_z(d, x, y)[0]
        return None


def fit_plane(pz):
    if "circle" in pz:
        c, R = pz["circle"]["c"], pz["circle"]["R"]
        pts = [(c[0] + rr * cos(a), c[1] + rr * sin(a)) for rr in (0, R * 0.5, R) for a in np.linspace(0, 2 * pi, 12)]
    else:
        xs = [p[0] for p in pz["poly"]]
        ys = [p[1] for p in pz["poly"]]
        pts = [(x, y) for x in np.linspace(min(xs), max(xs), 14) for y in np.linspace(min(ys), max(ys), 14)
               if L.point_in_poly(x, y, pz["poly"])]
    A = np.array([[x, y, 1.0] for x, y in pts])
    b = np.array([T.height(x, y) for x, y in pts])
    sol, *_ = np.linalg.lstsq(A, b, rcond=None)
    return tuple(float(v) for v in sol)


def terrace_z(z, x, y):
    """3 escalones planos a lo largo del fondo de la zona (de la fachada hacia atras)."""
    poly = z["poly"]
    p0, p1, p2, p3 = poly                       # rect_poly: (-x,-y), (+x,-y), (+x,+y), (-x,+y)
    fy = ((p3[0] - p0[0]), (p3[1] - p0[1]))
    Ld = hypot(*fy)
    t = ((x - p0[0]) * fy[0] + (y - p0[1]) * fy[1]) / (Ld * Ld)
    k = min(2, max(0, int(t * 3)))
    cx = p0[0] + (p1[0] - p0[0]) / 2 + fy[0] * (k + 0.5) / 3
    cy = p0[1] + (p1[1] - p0[1]) / 2 + fy[1] * (k + 0.5) / 3
    return T.height(cx, cy)


# ---------------------------------------------------------------------------
# Lineas de corte
# ---------------------------------------------------------------------------
def road_lines(rd, P):
    pts = L.resample(rd["pts"], 0.5)
    hw = rd["halfw"][0]
    out = []
    for off in (hw, -hw, hw + SHOULDER, -(hw + SHOULDER)):
        line = offset_polyline(pts, off)
        sgn = 1 if off > 0 else -1
        probe = offset_polyline(pts, off + sgn * 0.15)
        keep = []
        for q in probe:
            f = P.g.at(*q)
            d = P.features.get(f)
            keep.append(not (d and d["kind"] in ("road", "plaza") and d is not rd and d["type"] != "portal_plaza")
                        and hypot(*q) > C.PLAZA_RADIUS)
        for run in runs_where(line, keep):
            out.append((f"{rd['name']}_{'S' if abs(off) > hw else 'E'}{'+' if off > 0 else '-'}", run))
    # remates (semicirculo) en extremos libres
    for end in (0, -1):
        p = rd["pts"][end]
        q = rd["pts"][1 if end == 0 else -2]
        f_out = P.g.at(p[0] + (p[0] - q[0]) * 0.0, p[1])
        d = P.features.get(P.g.at(*p))
        dirx, diry = p[0] - q[0], p[1] - q[1]
        Ld = hypot(dirx, diry) or 1.0
        dirx, diry = dirx / Ld, diry / Ld
        tip = (p[0] + dirx * (hw + 0.2), p[1] + diry * (hw + 0.2))
        f_tip = P.features.get(P.g.at(*tip))
        if f_tip is not None and f_tip is not rd:
            continue
        if hypot(*p) < C.PLAZA_RADIUS + 1:
            continue
        base = atan2(diry, dirx)
        arc = [(p[0] + hw * cos(base + a), p[1] + hw * sin(base + a)) for a in np.linspace(-pi / 2, pi / 2, 13)]
        out.append((f"{rd['name']}_cap{end}", arc))
        _ = f_out, d
    return out


def outline(poly, closed=True):
    return list(poly) + ([poly[0]] if closed else [])


def grow_poly(poly, g):
    cx, cy = L.poly_centroid(poly)
    # rectangulos/convexos: desplazar cada arista hacia fuera
    out = []
    n = len(poly)
    area = sum(poly[i][0] * poly[(i + 1) % n][1] - poly[(i + 1) % n][0] * poly[i][1] for i in range(n))
    s = 1.0 if area > 0 else -1.0
    lines = []
    for i in range(n):
        a, b = poly[i], poly[(i + 1) % n]
        tx, ty = b[0] - a[0], b[1] - a[1]
        Lt = hypot(tx, ty) or 1.0
        nx, ny = s * ty / Lt, -s * tx / Lt
        lines.append(((a[0] + nx * g, a[1] + ny * g), (b[0] + nx * g, b[1] + ny * g)))
    for i in range(n):
        (a1, b1), (a2, b2) = lines[i - 1], lines[i]
        d1 = (b1[0] - a1[0], b1[1] - a1[1])
        d2 = (b2[0] - a2[0], b2[1] - a2[1])
        den = d1[0] * d2[1] - d1[1] * d2[0]
        if abs(den) < 1e-9:
            out.append(a2)
            continue
        t = ((a2[0] - a1[0]) * d2[1] - (a2[1] - a1[1]) * d2[0]) / den
        out.append((a1[0] + d1[0] * t, a1[1] + d1[1] * t))
    _ = cx, cy
    return out


def all_lines(lay, P):
    lines = []
    for rd in lay["roads"]:
        lines += [("road", n, pts) for n, pts in road_lines(rd, P)]
    for pz in lay["plazas"]:
        if pz["type"] in ("portal_plaza", "axis_frontage"):
            continue
        if "circle" in pz:
            c, R = pz["circle"]["c"], pz["circle"]["R"]
            ring = L.circle_poly(c, R, step=0.5)
            lines.append(("plaza", pz["name"], outline(ring)))
            if pz["type"] in PLANAR_PLAZAS:
                lines.append(("plaza_s", pz["name"] + "_S", outline(L.circle_poly(c, R + SHOULDER, step=0.5))))
        else:
            lines.append(("plaza", pz["name"], outline(pz["poly"])))
            if pz["type"] in PLANAR_PLAZAS:
                lines.append(("plaza_s", pz["name"] + "_S", outline(grow_poly(pz["poly"], SHOULDER))))
    for pa in lay["parcels"]:
        if pa["type"] == "stall":
            continue
        if pa["shape"] == "circle":
            lines.append(("parcel", pa["name"], outline(L.circle_poly(pa["center"], pa["w"] / 2, 0.5))))
            lines.append(("parcel_s", pa["name"] + "_S",
                          outline(L.circle_poly(pa["center"], pa["w"] / 2 + SHOULDER, 0.5))))
        else:
            lines.append(("parcel", pa["name"], outline(pa["poly"])))
            sh = outline(grow_poly(pa["poly"], SHOULDER))
            sh = L.resample(sh, 0.5)
            cx, cy = pa["center"]
            keep = []
            for q in sh:
                dx, dy = q[0] - cx, q[1] - cy
                Ld = hypot(dx, dy) or 1.0
                pr = (q[0] + dx / Ld * 0.45, q[1] + dy / Ld * 0.45)
                f = P.features.get(P.g.at(*pr))
                keep.append(not (f and f["kind"] in ("road", "plaza")))
            for k, run in enumerate(runs_where(sh, keep)):
                lines.append(("parcel_s", f"{pa['name']}_S{k}", run))
    for z in lay["zones"]:
        lines.append(("zone", z["name"], outline(z["poly"])))
        if z["type"] in ("archery_range", "herb_terraces"):
            lines.append(("zone_s", z["name"] + "_S", outline(grow_poly(z["poly"], SHOULDER))))
        if z["type"] == "herb_terraces":
            p0, p1, p2, p3 = z["poly"]
            for k in (1, 2):
                t = k / 3
                a = (p0[0] + (p3[0] - p0[0]) * t, p0[1] + (p3[1] - p0[1]) * t)
                b = (p1[0] + (p2[0] - p1[0]) * t, p1[1] + (p2[1] - p1[1]) * t)
                lines.append(("zone", f"{z['name']}_step{k}", [a, b]))
    for pt in lay["patches"]:
        lines.append(("patch", pt["name"], outline(pt["poly"])))
    for k, rt in enumerate(lay["ruts"]):
        pts = rt["pts"]
        for off, tag in ((0.0, "C"), (RUT_HALF, "+"), (-RUT_HALF, "-")):
            line = offset_polyline(pts, off) if off else pts
            lines.append(("rut_c" if tag == "C" else "rut", f"rut{k:02d}{tag}", line))
    return lines


# ---------------------------------------------------------------------------
# Construccion
# ---------------------------------------------------------------------------
def cut_and_lift(obj, lay, P, stats):
    me = obj.data
    bm = bmesh.new()
    bm.from_mesh(me)
    dl = bm.verts.layers.deform.active
    idx = EdgeIndex(bm)
    locked = set()
    lines = all_lines(lay, P)
    rut_center = set()
    counts = {}
    import time
    t0 = time.time()
    for k, (kind, name, pts) in enumerate(lines):
        vs = knife(bm, idx, pts, locked)
        counts[kind] = counts.get(kind, 0) + 1
        if k % 100 == 0:
            print(f"  knife {k}/{len(lines)} {time.time() - t0:.1f}s", flush=True)
        if kind == "rut_c":
            rut_center.update(vs)
    bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 3], quad_method="BEAUTY",
                          ngon_method="BEAUTY")
    surf = Surfaces(lay, P)
    bm.verts.index_update()
    moved = 0
    vinfo = {}
    patch_polys = [(pt["poly"], pt["dz"]) for pt in lay["patches"]]
    for v in bm.verts:
        x, y = v.co.x, v.co.y
        r = hypot(x, y)
        if r < C.PLAZA_RADIUS - 0.2 or r > C.WALL_BASE_R[0] + 1.0:
            continue
        kind, d = surf.classify(x, y)
        if kind is None:
            continue
        if kind == "road":
            z, dist = surf.road_z(d, x, y)
            for poly, dz in patch_polys:
                if point_in_poly_tol(x, y, poly):
                    z += dz
            if v in rut_center:
                z -= RUT_DEPTH
        elif kind in ("keep", "zone_keep"):
            vinfo[v.index] = (kind, d)
            if v in rut_center:
                v.co.z -= RUT_DEPTH
                moved += 1
            continue
        else:
            z = surf.z_of(kind, d, x, y)
        if z is None:
            continue
        v.co.z = z
        moved += 1
        vinfo[v.index] = (kind, d)
    _ = dl
    rut_center = [v for v in rut_center if v.is_valid]
    for v in rut_center:
        pass
    bm.normal_update()
    rut_idx = {v.index for v in rut_center}
    bm.to_mesh(me)
    bm.free()
    me.update()
    me.set_sharp_from_angle(angle=radians(S2.SHARP_ANGLE))
    surf.rut_idx = rut_idx
    stats["streets_terrain"] = {"knife_lines": counts, "lines_total": len(lines), "verts_moved": moved,
                                "tris_after": len(me.polygons), "rut_center_verts": len(rut_center)}
    surf.vinfo = {i: (k, d["name"]) for i, (k, d) in vinfo.items()}
    return surf


def face_classes(me, surf):
    """Clase de cada cara (por su centro): (road_mask, cobble_type, kind, feature)."""
    out = []
    patch = [pt["poly"] for pt in surf.lay["patches"]]
    for p in me.polygons:
        c = p.center
        r = hypot(c.x, c.y)
        if r < C.PLAZA_RADIUS - 0.2 or r > C.WALL_BASE_R[0] + 1.0:
            out.append((0.0, 0, None, None))
            continue
        kind, d = surf.classify(c.x, c.y)
        if kind is None:
            out.append((0.0, 0, None, None))
            continue
        if kind == "parcel":
            out.append((0.0, COBBLE["pad"], kind, d))
        elif kind in ("zone", "zone_keep"):
            ct = COBBLE["tamped_earth"]
            out.append((0.0, ct, kind, d))
        elif kind in ("plaza", "keep"):
            st = SURFACE_OF.get(d["surface"], "cobble")
            ct = COBBLE[st]
            if d["type"] == "training_square":
                ct = COBBLE["cobble"]
                for z in surf.lay["zones"]:
                    if z["type"] == "training_dummies" and point_in_poly_tol(c.x, c.y, z["poly"]):
                        ct = COBBLE["tamped_earth"]
                        break
            out.append((1.0, ct, kind, d))
        else:
            ct = COBBLE["cobble"]
            for poly in patch:
                if L.point_in_poly(c.x, c.y, poly):
                    ct = COBBLE["patch"]
                    break
            out.append((1.0, ct, kind, d))
    return out


def wear_values(me, surf):
    rng_off = Vector((3.1, 7.7, 1.3))
    w = [0.0] * len(me.vertices)
    for v in me.vertices:
        x, y = v.co.x, v.co.y
        r = hypot(x, y)
        if r < C.PLAZA_RADIUS - 0.2 or r > C.WALL_BASE_R[0] + 1.0:
            continue
        kind, d = surf.classify(x, y)
        if kind == "road":
            pr = surf.road_prof[d["name"]]
            dist, _s, _i = closest_on_polyline(pr["pts"], pr["cum"], (x, y))
            k = WEAR_K.get(d["type"], 0.5)
            base = k * max(0.0, 1.0 - (dist / d["halfw"][0]) ** 2) ** 0.7
        elif kind in ("plaza", "keep"):
            base = 0.35 if d["type"] != "axis_frontage" else 0.25
        else:
            continue
        n = noise.noise(Vector((x / 3.0, y / 3.0, 0.0)) + rng_off, noise_basis="PERLIN_NEW")
        w[v.index] = max(0.0, min(1.0, base * (0.85 + 0.3 * n)))
    return w


def write_masks(obj, surf, stats):
    me = obj.data
    fc = face_classes(me, surf)
    wear = wear_values(me, surf)
    nl = len(me.loops)
    loop_v = [0] * nl
    me.loops.foreach_get("vertex_index", loop_v)
    loop_f = [0] * nl
    for p in me.polygons:
        for li in range(p.loop_start, p.loop_start + p.loop_total):
            loop_f[li] = p.index
    for name in ("road_mask", "wear_mask", "cobble_type"):
        if name in me.color_attributes:
            me.color_attributes.remove(me.color_attributes[name])

    def put(name, vals):
        a = me.color_attributes.new(name=name, type="BYTE_COLOR", domain="CORNER")
        flat = []
        for val in vals:
            flat.extend((val, val, val, 1.0))
        a.data.foreach_set("color", flat)
    road = [fc[loop_f[i]][0] for i in range(nl)]
    ctype = [fc[loop_f[i]][1] for i in range(nl)]
    wr = [wear[loop_v[i]] * (1.0 if road[i] > 0 else 0.0) for i in range(nl)]
    put("road_mask", road)
    put("wear_mask", wr)
    put("cobble_type", [c / 8.0 for c in ctype])
    if "UVRoads" in me.uv_layers:
        me.uv_layers.remove(me.uv_layers["UVRoads"])
    uv = me.uv_layers.new(name="UVRoads")
    flat = []
    for i in range(nl):
        flat.extend((road[i], ctype[i] + 0.99 * wr[i]))
    uv.data.foreach_set("uv", flat)
    me.uv_layers.active_index = 0
    by_type = {}
    for f in fc:
        by_type[f[1]] = by_type.get(f[1], 0) + 1
    inv = {v: k for k, v in COBBLE.items() if k != "existing"}
    stats["street_masks"] = {
        "road_mask": "1 en calles, callejones y plazas empedradas (por cara)",
        "wear_mask": "0..1 desgaste (centro de calle, tipo de via)",
        "cobble_type": "valor = tipo / 8: 0 terreno, 1 adoquin, 2 parche, 3 tierra apisonada, 4 losas, 5 plataforma de parcela",
        "uv3_UVRoads": "x = road_mask; y = cobble_type + 0.99 * wear_mask",
        "faces_by_cobble_type": {inv.get(k, str(k)): n for k, n in sorted(by_type.items())},
    }
    return fc


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def slope_of(p):
    return degrees(atan2(sqrt(p.normal.x ** 2 + p.normal.y ** 2), abs(p.normal.z)))


def qa(obj, surf, fc, stats):
    """Pendientes de las superficies caminables (caras interiores: sus 3 vertices pertenecen al mismo
    elemento), escalones en los bordes marcados (caras mixtas) y surcos aparte."""
    me = obj.data
    vin = surf.vinfo
    per, edge_steps, rut_faces = {}, {}, 0
    big_steps = []
    over5 = []
    pad_slope = 0.0
    existing = 0
    ret = me.color_attributes.get("retaining_mask")
    retv = [0.0] * (len(me.loops) * 4)
    ret.data.foreach_get("color", retv)
    for p, (rm, ct, kind, d) in zip(me.polygons, fc):
        if kind is None:
            continue
        vs = list(p.vertices)
        if any(i in surf.rut_idx for i in vs):
            rut_faces += 1
            continue
        tags = [vin.get(i) for i in vs]
        s = slope_of(p)
        if kind in ("keep", "zone_keep") and (retv[p.loop_start * 4] > 0.5 or
                                              (s > 12.0 and all(t is not None and t[0] == kind for t in tags))):
            existing += 1                    # caras de muro / bordes de banda de la etapa 02, sin tocar
            continue
        if p.area < 0.005:
            continue                         # astillas de borde
        interior = all(t is not None and t == tags[0] for t in tags)
        dist = d["district"]
        if not interior:
            zs = [me.vertices[i].co.z for i in vs]
            e = edge_steps.setdefault(dist, {"faces": 0, "max_step_m": 0.0, "steps_gt_0_15": 0})
            e["faces"] += 1
            st = max(zs) - min(zs) - 1e-9
            # escalon = desnivel no explicado por la pendiente de la calle (aprox.: dz - 0.09 * span)
            span = max((me.vertices[a].co.xy - me.vertices[b].co.xy).length for a in vs for b in vs)
            step = max(0.0, st - tan(radians(ROAD_SLOPE_MAX)) * span)
            e["max_step_m"] = max(e["max_step_m"], round(step, 3))
            e["steps_gt_0_15"] += int(step > 0.15)
            if step > 0.3:
                big_steps.append((round(step, 2), d["name"], round(p.center.x, 1), round(p.center.y, 1),
                                  sorted(set(str(t[1]) if t else "terreno" for t in tags))))
            continue
        if kind in ("road", "plaza", "keep"):
            e = per.setdefault(dist, {"faces": 0, "max_deg": 0.0, "gt5": 0})
            e["faces"] += 1
            e["max_deg"] = max(e["max_deg"], s)
            if s > C.WALK_SLOPE_MAX:
                e["gt5"] += 1
                over5.append((d["name"], round(s, 2), round(p.center.x, 1), round(p.center.y, 1), round(p.area, 3)))
        if kind == "parcel":
            pad_slope = max(pad_slope, s)
    for v in per.values():
        v["max_deg"] = round(v["max_deg"], 2)
    over5.sort(key=lambda t: -t[1])
    prof = {n: {"slope_max_deg": round(p["slope_max"], 2), "pinned_samples": p["pinned"]}
            for n, p in surf.road_prof.items()}
    plinth = []
    for pa in surf.lay["parcels"]:
        if pa["type"] == "stall":
            continue
        zp = surf.pad[pa["name"]]
        zs = [T.height(x, y) for x, y in pa["poly"]] + [T.height(*pa["center"])]
        plinth.append((pa["name"], round(max(abs(zp - z) for z in zs), 3)))
    plinth.sort(key=lambda t: -t[1])
    stats["streets_qa"] = {
        "walk_surface_slope_by_district": per,
        "walk_faces_gt5_sample": over5[:25],
        "walk_faces_gt5_count": len(over5),
        "marked_edge_steps_by_district": edge_steps,
        "edge_steps_gt_0_3_sample": sorted(big_steps, key=lambda t: -t[0])[:30],
        "edge_steps_gt_0_3_count": len(big_steps),
        "rut_faces_excluded": rut_faces,
        "existing_retaining_faces_excluded": existing,
        "road_profile_slope_max_deg": round(max(p["slope_max"] for p in surf.road_prof.values()), 2),
        "road_profiles": prof,
        "parcel_pad_face_slope_max_deg": round(pad_slope, 3),
        "parcel_plinth_max_m": plinth[:12],
        "parcel_plinth_over_0_5m": sum(1 for _n, h in plinth if h > 0.5),
        "note": "caras interiores = sus 3 vertices en el mismo elemento; caras mixtas = borde marcado (escalon)",
    }


# ---------------------------------------------------------------------------
# Marcadores
# ---------------------------------------------------------------------------
def ensure_col(name, parent):
    col = bpy.data.collections.get(name)
    if col is None:
        col = bpy.data.collections.new(name)
        parent.children.link(col)
    for o in list(col.objects):
        bpy.data.objects.remove(o)
    return col


def make_markers(lay, surf, stats):
    root = bpy.data.collections["MARKERS_DISTRICTS"]
    cols = {d: ensure_col(n, root) for d, n in DISTRICT_COLLECTIONS.items()}
    cols["Diagonal"] = ensure_col("MARKERS_Streets", root)
    n_bld = 0

    def empty(name, loc, ang, props, col, size=1.0, typ="ARROWS"):
        if name in bpy.data.objects:
            bpy.data.objects.remove(bpy.data.objects[name])
        e = bpy.data.objects.new(name, None)
        e.empty_display_type = typ
        e.empty_display_size = size
        e.location = loc
        e.rotation_euler = (0.0, 0.0, radians(ang - 90.0))       # +Y local -> angulo 'ang'
        for k, v in props.items():
            e[k] = v
        col.objects.link(e)
        return e
    for pa in lay["parcels"]:
        if pa["type"] == "stall":
            z = surf.surface_z(*pa["center"], exclude_parcels=True) or T.height(*pa["center"])
        else:
            z = surf.pad[pa["name"]]
        props = {"footprint": f"{pa['w']:g}x{pa['d']:g}", "footprint_w": float(pa["w"]), "footprint_d": float(pa["d"]),
                 "door_direction": "+Y", "interior": bool(pa["interior"]), "type": pa["type"], "label": pa["label"],
                 "district": pa["district"], "pad_z": round(z, 3), "front_street": pa["front"] or "",
                 "shape": pa["shape"]}
        for k in ("service", "barrio", "race_slot", "class_slot", "open_foundry", "open_structure", "group_board",
                  "has_service", "decor", "next_to", "diameter_m", "range", "herb_terraces", "foundry_yard_m"):
            if k in pa:
                props[k] = pa[k] if not isinstance(pa[k], (list, tuple)) else str(pa[k])
        empty(pa["name"], (pa["center"][0], pa["center"][1], z), pa["angle"], props, cols[pa["district"]],
              size=min(pa["w"], pa["d"]) / 2)
        n_bld += 1
        if pa.get("group_board"):
            a = radians(pa["angle"])
            rx, ry = sin(a), -cos(a)
            loc = (pa["door"][0] + cos(a) * 1.2 + rx * (pa["w"] / 2 - 2.5), pa["door"][1] + sin(a) * 1.2 + ry * (pa["w"] / 2 - 2.5))
            zf = surf.surface_z(*loc) or z
            empty("MARKER_Prop_TablonGrupos", (loc[0], loc[1], zf), pa["angle"],
                  {"type": "group_board", "district": pa["district"], "parcel": pa["name"], "interactive": True},
                  cols[pa["district"]], 0.6, "SINGLE_ARROW")
    n_aux = 0
    for m in lay["markers"]:
        x, y = m["loc"]
        z = surf.surface_z(x, y) or T.height(x, y)
        d = m["props"].get("district", "Diagonal")
        empty(m["name"], (x, y, z), m["angle"], dict(m["props"]), cols.get(d, cols["Diagonal"]), 0.8, "PLAIN_AXES")
        n_aux += 1
    stats["district_markers"] = {"MARKER_Bld": n_bld, "aux": n_aux + 1,
                                 "convention": "+Y local = fachada de la puerta (Godot -Z); origen = centro de la huella a la cota de la plataforma"}


def street_objects(lay):
    """Ejes de calle como mallas de aristas (STR_*) en la coleccion STREETS (referencia / navegacion)."""
    col = bpy.data.collections["STREETS"]
    sub = bpy.data.collections.get("STREETS_AXES")
    if sub is None:
        sub = bpy.data.collections.new("STREETS_AXES")
        col.children.link(sub)
    for o in list(sub.objects):
        bpy.data.objects.remove(o)
    for rd in lay["roads"]:
        me = bpy.data.meshes.new(rd["name"])
        pts = [(p[0], p[1], T.height(*p) + 0.05) for p in rd["pts"]]
        me.from_pydata(pts, [(i, i + 1) for i in range(len(pts) - 1)], [])
        o = bpy.data.objects.new(rd["name"], me)
        o["width_m"] = rd["width"]
        o["type"] = rd["type"]
        o["district"] = rd["district"]
        o["blind"] = bool(rd.get("blind", False))
        sub.objects.link(o)
        o.hide_render = True
    sub.hide_render = True


def street_mask_texture(lay, P, path):
    """Textura cenital (0.25 m/px) para el shader de Godot: R calle, G desgaste aprox., B tipo/7, A parcela."""
    from PIL import Image
    g = P.g
    lab = g.lab
    n = g.n
    R = np.zeros((n, n), np.uint8)
    G = np.zeros((n, n), np.uint8)
    B = np.zeros((n, n), np.uint8)
    A = np.zeros((n, n), np.uint8)
    for fid, d in P.features.items():
        m = lab == fid
        if not m.any():
            continue
        if d["kind"] == "road":
            R[m] = 255
            B[m] = int(255 * COBBLE["cobble"] / 7)
            G[m] = int(255 * WEAR_K.get(d["type"], 0.5) * 0.7)
        elif d["kind"] == "plaza" and d["type"] != "portal_plaza":
            R[m] = 255
            B[m] = int(255 * COBBLE[SURFACE_OF.get(d["surface"], "cobble")] / 7)
            G[m] = 80
        elif d["kind"] == "parcel":
            A[m] = 255
            B[m] = int(255 * COBBLE["pad"] / 7)
        elif d["kind"] == "zone":
            B[m] = int(255 * COBBLE["tamped_earth"] / 7)
    img = np.flipud(np.dstack([R, G, B, A]))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    Image.fromarray(img, "RGBA").save(path)
    return {"path": os.path.relpath(path, REPO), "px": n, "m_per_px": g.cell,
            "mapping": "u = (x + 212) / 424, v = (212 - y) / 424 (x = Este, y = Norte en Blender)"}


def street_material(base_builder):
    """Envuelve stage02_shading.terrain_material: anade el empedrado (MAT_Cobble_Concordia) por road_mask."""
    import material_library as ML

    def build(plaza=False):
        m = base_builder(plaza=plaza)
        cob = ML.make_material("MAT_Cobble_Concordia", "CobblestoneFloor001")
        cob.use_fake_user = True
        cob["note"] = "material de referencia de calles (3 imagenes, 1 m = 1 tile); en TRN_City se mezcla por road_mask"
        N, Ln = m.node_tree.nodes, m.node_tree.links
        bsdf = N["Principled BSDF"]
        prev = bsdf.inputs["Base Color"].links[0].from_socket
        tc = N.new("ShaderNodeTexCoord")
        mp = N.new("ShaderNodeMapping")
        Ln.new(tc.outputs["Object"], mp.inputs["Vector"])
        tex = N.new("ShaderNodeTexImage")
        tex.image = cob.node_tree.nodes["Albedo"].image
        Ln.new(mp.outputs["Vector"], tex.inputs["Vector"])

        def attr(name):
            a = N.new("ShaderNodeVertexColor")
            a.layer_name = name
            bwn = N.new("ShaderNodeRGBToBW")
            Ln.new(a.outputs["Color"], bwn.inputs[0])
            return bwn.outputs[0]

        def mathn(op, a, b):
            n = N.new("ShaderNodeMath")
            n.operation = op
            for i, v in enumerate((a, b)):
                if isinstance(v, (int, float)):
                    n.inputs[i].default_value = v
                else:
                    Ln.new(v, n.inputs[i])
            return n.outputs[0]

        def mix(fac, a, b, blend="MIX"):
            n = N.new("ShaderNodeMix")
            n.data_type = "RGBA"
            n.blend_type = blend
            if isinstance(fac, float):
                n.inputs["Factor"].default_value = fac
            else:
                Ln.new(fac, n.inputs["Factor"])
            for sock, val in (("A", a), ("B", b)):
                if isinstance(val, str):
                    n.inputs[sock].default_value = C.hex_to_linear_rgba(val)
                else:
                    Ln.new(val, n.inputs[sock])
            return n.outputs["Result"]
        ct = mathn("ROUND", mathn("MULTIPLY", attr("cobble_type"), 8.0), 0.0)

        def is_t(k):
            return mathn("LESS_THAN", mathn("ABSOLUTE", mathn("SUBTRACT", ct, float(k)), 0.0), 0.5)
        road = attr("road_mask")
        wear = attr("wear_mask")
        aoa = N.new("ShaderNodeVertexColor")
        aoa.layer_name = "ao_edge"
        cob_col = mix(1.0, tex.outputs["Color"], "#B9AE98", "MULTIPLY")
        cob_col = mix(1.0, cob_col, aoa.outputs["Color"], "MULTIPLY")
        cob_col = mix(mathn("MULTIPLY", wear, 0.35), cob_col, "#D8CFBC")
        c = mix(road, prev, cob_col)
        c = mix(is_t(2), c, "#7D7A72")                        # parche de otra piedra (mas gris)
        c = mix(is_t(4), c, "#C9C0AC")                        # losas (plazoletas, fuente)
        c = mix(is_t(3), c, "#8B7457")                        # tierra apisonada
        c = mix(mathn("MULTIPLY", is_t(5), 0.55), c, "#B7A88C")   # plataforma de parcela (suelo preparado)
        c = mix(is_t(6), c, "#6E7449")                        # jardin (Moradas, etapa 06)
        c = mix(is_t(7), c, "#3B3A32")                        # lecho y muros del Cauce (etapa 07)
        # muros de contencion: piedra (StoneWall02, proyeccion de caja, 1 m = 1 tile) por retaining_mask
        wall = ML.make_material("MAT_StoneWall_Retaining", "StoneWall02")
        wall.use_fake_user = True
        tw = N.new("ShaderNodeTexImage")
        tw.image = wall.node_tree.nodes["Albedo"].image
        tw.projection = "BOX"
        tw.projection_blend = 0.2
        Ln.new(mp.outputs["Vector"], tw.inputs["Vector"])
        wall_col = mix(1.0, tw.outputs["Color"], "#C9BFA8", "MULTIPLY")
        wall_col = mix(1.0, wall_col, aoa.outputs["Color"], "MULTIPLY")
        c = mix(attr("retaining_mask"), c, wall_col)
        ao = None
        for lk in list(bsdf.inputs["Base Color"].links):
            ao = lk
        Ln.new(c, bsdf.inputs["Base Color"])
        _ = ao
        return m
    return build


def build(scene, stats, obst_codes, stairs):
    lay, rep, P = L.plan(obst_codes, 0.5, stairs)
    stats["layout_report"] = rep
    obj = bpy.data.objects["TRN_City"]
    surf = cut_and_lift(obj, lay, P, stats)
    # mascaras de las etapas anteriores sobre la nueva topologia
    me = obj.data
    for name in ("retaining_mask", "dirt_mask", "stone_mask", "slab_ring_id", "travertine_band", "repair_mask",
                 "magic_glow_mask", "ao_edge", "mask_pack"):
        if name in me.color_attributes:
            me.color_attributes.remove(me.color_attributes[name])
    while me.uv_layers:
        me.uv_layers.remove(me.uv_layers[0])
    obj.vertex_groups.clear()
    vdata, _ret = S2.write_vertex_data(obj)
    stats["vertex_data_rewritten"] = vdata
    import stage03_plaza as S3
    S3.write_plaza_masks(me, {})
    fc = write_masks(obj, surf, stats)
    qa(obj, surf, fc, stats)
    make_markers(lay, surf, stats)
    street_objects(lay)
    stats["street_mask_texture"] = street_mask_texture(lay, P, os.path.join(REPO, "textures", "streets",
                                                                            "T_StreetMasks.png"))
    return lay, rep, P, surf
