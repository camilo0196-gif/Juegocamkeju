"""
CONCORDIA - etapa 05: planificador 2D de calles y parcelas de los 4 distritos cardinales.
Python puro + numpy (sin bpy). Determinista (semilla 11).

Entrada : raster de obstaculos de la escena (stage05_obstacles.py; 1 = estructura, 2 = cara de muro).
Salida  : dict 'layout' con calles (ejes + ancho), plazas, parcelas (MARKER_Bld_*), zonas y
          marcadores auxiliares. stage05_streets.py lo aplica a TRN_City.

Sistema local de cada distrito: u = radial (desde el centro hacia la puerta), v = tangencial
(+v = antihorario). Mundo: x = u cos(phi) - v sin(phi), y = u sin(phi) + v cos(phi).

Reglas de colocacion
- Cada parcela da su fachada (+Y local del marcador) a una calle o plaza; retranqueo SETBACK
  entre el borde de la calle y la parcela, y TRAUFGASSE entre parcelas (callejon de goteo).
- Nada puede pisar celdas de obstaculo (dilatadas OBST_CLEAR), otras calles, plazas o parcelas.
- La puerta queda a menos de DOOR_DZ_MAX de la cota de la calle de enfrente (ver report).
"""

import hashlib
import random
from math import atan2, ceil, cos, degrees, hypot, pi, radians, sin, sqrt

import numpy as np

import concordia_const as C
import terrain_profile as T

# ---------------------------------------------------------------------------
# Parametros (los del pedido arriba; los artisticos abajo)
# ---------------------------------------------------------------------------
SEED = 11
N_CLASES = 8
N_RAZAS = 6

AVENUE_W = 10.0
DIAG_W = 6.0
RING1_R, RING1_W = 100.0, 8.0
RING2_R, RING2_W = 150.0, 6.0
MERCADO_STREET_W = 10.0              # "calles de 10 m con toldos" -> tramos de anillo del Mercado
WOBBLE_M = (1.0, 2.0)                # curvas suaves de los anillos (amplitud)
ALLEY_W = (4.0, 5.0)
ALLEY_BLIND_FRAC = 0.15
PLAZOLETA_D = 30.0
PLAZOLETA_U = C.CARD_EMBANK_END - PLAZOLETA_D / 2      # 181: borde exterior en r=196 (pie de muralla)
AXIS_BAND_U0 = C.AXIS_DESCENT[0] - 1.0                 # 89: la banda del eje empieza aqui (terrain_profile)
FOUNTAIN_D, FOUNTAIN_R = 22.0, 105.0
ARMAS = (50.0, 40.0)                 # tangencial x radial
RAZA_BARRIO = 35.0
RAZA_HOUSE = 20.0, 16.0
PLAZUELA_D = 10.0
HOUSE_W, HOUSE_D = (8.0, 12.0), (8.0, 10.0)
HOUSES_PER_BARRIO = (6, 10)
STALLS = 14
STALL = 3.0

SETBACK = 0.6                        # calle -> parcela (franja de borde marcado)
TRAUFGASSE = 0.6                     # parcela -> parcela
OBST_CLEAR = 1.0                     # holgura a estructuras existentes
DOOR_DZ_MAX = 0.35
PLAN_CELL = 0.25
EXTENT = C.TERRAIN_GRID_SIZE / 2.0
DISTRICT_R = (C.PLAZA_RADIUS, 194.0)

DISTRICT_AXIS = {"Oficios": 0.0, "Mercado": 90.0, "Clases": 180.0, "Razas": 270.0}
DISTRICT_KEY = {"Oficios": "OFI", "Mercado": "MER", "Clases": "CLA", "Razas": "RAZ"}
DIAG_LANDMARK = {45.0: "Faro", 135.0: "Santuario", 225.0: "Obelisco", 315.0: "SalonHazanas"}


def rng_for(*key):
    h = hashlib.sha1(("|".join(map(str, (SEED,) + key))).encode()).hexdigest()
    return random.Random(int(h[:12], 16))


# ---------------------------------------------------------------------------
# Geometria
# ---------------------------------------------------------------------------
def to_world(u, v, phi):
    a = radians(phi)
    return (u * cos(a) - v * sin(a), u * sin(a) + v * cos(a))


def to_local(x, y, phi):
    a = radians(phi)
    return (x * cos(a) + y * sin(a), -x * sin(a) + y * cos(a))


def rect_poly(c, ang, w, d):
    """Rectangulo: centro c, +Y local apunta al angulo 'ang' (grados, mundo), w a lo largo de X local."""
    a = radians(ang)
    fx, fy = cos(a), sin(a)
    rx, ry = sin(a), -cos(a)
    hw, hd = w / 2.0, d / 2.0
    return [(c[0] + sx * hw * rx + sy * hd * fx, c[1] + sx * hw * ry + sy * hd * fy)
            for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))]


def circle_poly(c, R, step=0.5):
    n = max(24, int(ceil(2 * pi * R / step)))
    return [(c[0] + R * cos(2 * pi * i / n), c[1] + R * sin(2 * pi * i / n)) for i in range(n)]


def polyline_len(pts):
    return sum(hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(pts, pts[1:]))


def resample(pts, step):
    out = [pts[0]]
    acc = 0.0
    for a, b in zip(pts, pts[1:]):
        L = hypot(b[0] - a[0], b[1] - a[1])
        t = step - acc
        while t <= L:
            out.append((a[0] + (b[0] - a[0]) * t / L, a[1] + (b[1] - a[1]) * t / L))
            t += step
        acc = (acc + L) % step
    if hypot(out[-1][0] - pts[-1][0], out[-1][1] - pts[-1][1]) > 1e-6:
        out.append(pts[-1])
    return out


def frame_at(pts, s):
    """Punto, tangente y normal izquierda a la distancia s sobre la polilinea."""
    acc = 0.0
    for a, b in zip(pts, pts[1:]):
        L = hypot(b[0] - a[0], b[1] - a[1])
        if acc + L >= s or b is pts[-1]:
            t = 0.0 if L == 0 else min(1.0, max(0.0, (s - acc) / L))
            tx, ty = (b[0] - a[0]) / L, (b[1] - a[1]) / L
            return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t), (tx, ty), (-ty, tx)
        acc += L
    raise ValueError


# ---------------------------------------------------------------------------
# Raster de planificacion
# ---------------------------------------------------------------------------
class Grid:
    FREE, OBST, STEEP = 0, -1, -2

    def __init__(self, obstacle_codes, obst_cell):
        self.cell = PLAN_CELL
        self.n = int(round(2 * EXTENT / self.cell))
        k = int(round(obst_cell / self.cell))
        up = np.repeat(np.repeat(obstacle_codes, k, axis=0), k, axis=1)
        self.lab = np.zeros((self.n, self.n), dtype=np.int32)
        self.lab[up == 2] = self.STEEP
        self.lab[up == 1] = self.OBST
        self.raw_obst = self.lab.copy()
        c = -EXTENT + self.cell * (np.arange(self.n) + 0.5)
        self.c = c
        # dilatacion de obstaculos (holgura) -> mascara aparte
        self.blocked = self._dilate(self.lab < 0, OBST_CLEAR)

    def _dilate(self, m, r):
        k = int(ceil(r / self.cell))
        out = m.copy()
        for dj in range(-k, k + 1):
            for di in range(-k, k + 1):
                if di * di + dj * dj <= k * k:
                    out |= np.roll(np.roll(m, dj, 0), di, 1)
        return out

    def window(self, xmin, xmax, ymin, ymax):
        i0 = max(0, int((xmin + EXTENT) / self.cell) - 1)
        i1 = min(self.n, int((xmax + EXTENT) / self.cell) + 2)
        j0 = max(0, int((ymin + EXTENT) / self.cell) - 1)
        j1 = min(self.n, int((ymax + EXTENT) / self.cell) + 2)
        X, Y = np.meshgrid(self.c[i0:i1], self.c[j0:j1])
        return (slice(j0, j1), slice(i0, i1)), X, Y

    def poly_mask(self, poly, grow=0.0):
        xs = [p[0] for p in poly]
        ys = [p[1] for p in poly]
        sl, X, Y = self.window(min(xs) - grow, max(xs) + grow, min(ys) - grow, max(ys) + grow)
        inside = np.zeros(X.shape, dtype=bool)
        n = len(poly)
        for i in range(n):
            x1, y1 = poly[i]
            x2, y2 = poly[(i + 1) % n]
            cond = (y1 > Y) != (y2 > Y)
            with np.errstate(divide="ignore", invalid="ignore"):
                xint = (x2 - x1) * (Y - y1) / (y2 - y1) + x1
            inside ^= cond & (X < xint)
        if grow > 0.0:
            d = np.full(X.shape, 1e9)
            for i in range(n):
                d = np.minimum(d, _seg_dist(X, Y, poly[i], poly[(i + 1) % n]))
            inside |= d <= grow
        return sl, inside

    def capsule_mask(self, pts, halfw):
        hw = np.asarray(halfw if hasattr(halfw, "__len__") else [halfw] * len(pts), dtype=float)
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        g = float(hw.max())
        sl, X, Y = self.window(min(xs) - g, max(xs) + g, min(ys) - g, max(ys) + g)
        m = np.zeros(X.shape, dtype=bool)
        for k in range(len(pts) - 1):
            d, t = _seg_dist(X, Y, pts[k], pts[k + 1], with_t=True)
            m |= d <= hw[k] + (hw[k + 1] - hw[k]) * t
        return sl, m

    def circle_mask(self, c, R):
        sl, X, Y = self.window(c[0] - R, c[0] + R, c[1] - R, c[1] + R)
        return sl, (X - c[0]) ** 2 + (Y - c[1]) ** 2 <= R * R

    def free(self, sl, m, allow=()):
        lab = self.lab[sl][m]
        if self.blocked[sl][m].any():
            return False
        ok = lab == 0
        for a in allow:
            ok |= lab == a
        return bool(ok.all())

    def paint(self, sl, m, fid, over=False):
        sub = self.lab[sl]
        if over:
            sub[m & (sub >= 0)] = fid
        else:
            sub[m & (sub == 0)] = fid

    def at(self, x, y):
        i = int((x + EXTENT) / self.cell)
        j = int((y + EXTENT) / self.cell)
        if 0 <= i < self.n and 0 <= j < self.n:
            return int(self.lab[j, i])
        return self.OBST


def _seg_dist(X, Y, a, b, with_t=False):
    ax, ay = a
    bx, by = b
    dx, dy = bx - ax, by - ay
    L2 = dx * dx + dy * dy
    if L2 == 0:
        t = np.zeros_like(X)
    else:
        t = np.clip(((X - ax) * dx + (Y - ay) * dy) / L2, 0.0, 1.0)
    d = np.hypot(X - (ax + t * dx), Y - (ay + t * dy))
    return (d, t) if with_t else d


def in_district(x, y, phi, margin=0.0):
    r = hypot(x, y)
    if r < DISTRICT_R[0] or r > DISTRICT_R[1]:
        return False
    u, v = to_local(x, y, phi)
    return u > 0 and abs(v) <= u * np.tan(radians(C.CARDINAL_HALF_ANGLE)) - margin


# ---------------------------------------------------------------------------
# Planificador
# ---------------------------------------------------------------------------
class Planner:
    def __init__(self, obstacle_codes, obst_cell):
        self.g = Grid(obstacle_codes, obst_cell)
        self.features = {}          # fid -> dict
        self.next_id = 1
        self.roads = []
        self.plazas = []
        self.parcels = []
        self.zones = []
        self.markers = []
        self.report = {"unplaced": [], "door_dz": []}

    # -- registro -------------------------------------------------------------
    def _add(self, kind, d):
        fid = self.next_id
        self.next_id += 1
        d["fid"] = fid
        d["kind"] = kind
        self.features[fid] = d
        return fid

    def add_road(self, name, district, rtype, pts, halfw, priority, over=True, extra=None):
        pts = [tuple(p) for p in pts]
        hw = list(halfw) if hasattr(halfw, "__len__") else [halfw] * len(pts)
        d = {"name": name, "district": district, "type": rtype, "pts": pts, "halfw": hw,
             "width": round(2 * max(hw), 2), "priority": priority, "length_m": round(polyline_len(pts), 1)}
        if extra:
            d.update(extra)
        fid = self._add("road", d)
        sl, m = self.g.capsule_mask(pts, hw)
        self.g.paint(sl, m, fid, over=over)
        self.roads.append(d)
        return d

    def add_plaza(self, name, district, ptype, poly, surface, extra=None, circle=None):
        d = {"name": name, "district": district, "type": ptype, "poly": [tuple(p) for p in poly],
             "surface": surface}
        if circle:
            d["circle"] = {"c": circle[0], "R": circle[1]}
        if extra:
            d.update(extra)
        fid = self._add("plaza", d)
        if circle:
            sl, m = self.g.circle_mask(*circle)
        else:
            sl, m = self.g.poly_mask(poly)
        self.g.paint(sl, m, fid, over=True)
        self.plazas.append(d)
        return d

    def add_zone(self, name, district, ztype, poly, surface, paint=True, extra=None):
        d = {"name": name, "district": district, "type": ztype, "poly": [tuple(p) for p in poly],
             "surface": surface}
        if extra:
            d.update(extra)
        fid = self._add("zone", d)
        if paint:
            sl, m = self.g.poly_mask(poly)
            self.g.paint(sl, m, fid)
        self.zones.append(d)
        return d

    # -- comprobacion de parcelas --------------------------------------------
    def rect_ok(self, poly, district, region=None, allow=()):
        sl, m = self.g.poly_mask(poly, grow=TRAUFGASSE)
        if not self.g.free(sl, m, allow):
            return False
        if allow:                                   # la parcela en si no puede pisar nada
            sl, m = self.g.poly_mask(poly)
            if not self.g.free(sl, m):
                return False
        phi = DISTRICT_AXIS[district]
        for x, y in poly:
            if not in_district(x, y, phi):
                return False
            if region is not None and not point_in_poly(x, y, region):
                return False
        return True

    def front_feature(self, door, fwd):
        for dist in (SETBACK + 0.3, SETBACK + 0.8, SETBACK + 1.5):
            f = self.g.at(door[0] + fwd[0] * dist, door[1] + fwd[1] * dist)
            if f > 0 and self.features[f]["kind"] in ("road", "plaza"):
                return f, dist
        return None, None

    def commit_parcel(self, name, district, btype, label, c, ang, w, d, interior, extra=None, shape="rect"):
        poly = rect_poly(c, ang, w, d) if shape == "rect" else circle_poly(c, w / 2.0)
        a = radians(ang)
        fwd = (cos(a), sin(a))
        door = (c[0] + fwd[0] * d / 2.0, c[1] + fwd[1] * d / 2.0)
        f, dist = self.front_feature(door, fwd)
        z_pad = T.height(*door)
        z_front = T.height(door[0] + fwd[0] * dist, door[1] + fwd[1] * dist) if f else None
        p = {"name": name, "district": district, "type": btype, "label": label, "center": c, "angle": ang,
             "w": w, "d": d, "interior": interior, "door": door, "poly": poly, "shape": shape,
             "front": self.features[f]["name"] if f else None, "z_door_base": round(z_pad, 3),
             "door_dz_to_front": round(z_pad - z_front, 3) if f else None}
        if extra:
            p.update(extra)
        fid = self._add("parcel", p)
        sl, m = self.g.poly_mask(poly) if shape == "rect" else self.g.circle_mask(c, w / 2.0)
        self.g.paint(sl, m, fid)
        self.parcels.append(p)
        return p

    def try_frontage(self, front, side, s_pref, w, d, district, s_range=None, region=None, shape="rect",
                     extra_setbacks=(0.0, 0.5, 1.0, 1.5), step=1.0, max_tries=200, check_dz=True):
        """Busca posicion junto a una polilinea 'front' (calle con halfw, o borde de plaza con 0).
        side +1 = a la izquierda del sentido de la polilinea. Devuelve (centro, angulo) o None."""
        pts, hw = front["pts"], front.get("halfw", [0.0] * len(front["pts"]))
        L = polyline_len(pts)
        lo, hi = s_range if s_range else (0.0, L)
        lo, hi = max(lo, w / 2), min(hi, L - w / 2)
        if hi < lo:
            return None
        s_pref = min(max(s_pref, lo), hi)
        offs = [0.0]
        for k in range(1, max_tries):
            offs += [k * step, -k * step]
        for ds in offs:
            s = s_pref + ds
            if s < lo or s > hi:
                continue
            p, t, nl = frame_at(pts, s)
            h = _hw_at(pts, hw, s)
            nx, ny = nl[0] * side, nl[1] * side
            if h > 0.0:
                f_front = self.g.at(*p)
            else:
                f_front = self.g.at(p[0] - nx * 0.4, p[1] - ny * 0.4)
            allow = (f_front,) if f_front > 0 else ()
            for eb in extra_setbacks:
                off = h + SETBACK + eb + d / 2.0
                c = (p[0] + nx * off, p[1] + ny * off)
                ang = degrees(atan2(-ny, -nx))
                poly = rect_poly(c, ang, w, d) if shape == "rect" else circle_poly(c, w / 2.0)
                if not self.rect_ok(poly, district, region, allow):
                    continue
                if check_dz:
                    door = (c[0] - nx * d / 2.0, c[1] - ny * d / 2.0)
                    f, dist = self.front_feature(door, (-nx, -ny))
                    if f is None:
                        continue
                    zf = T.height(door[0] - nx * dist, door[1] - ny * dist)
                    if abs(T.height(*door) - zf) > DOOR_DZ_MAX:
                        continue
                return c, ang
        return None

    def place(self, name, district, btype, label, w, d, interior, candidates, extra=None, shape="rect",
              region=None):
        for cand in candidates:
            front, side, s_pref = cand[:3]
            s_range = cand[3] if len(cand) > 3 else None
            r = self.try_frontage(front, side, s_pref, w, d, district, s_range, region, shape)
            if r:
                return self.commit_parcel(name, district, btype, label, r[0], r[1], w, d, interior, extra, shape)
        # respaldo: cualquier fachada libre del distrito (anillos, callejones, banda del eje)
        phi = DISTRICT_AXIS[district]
        fronts = [x for x in self.roads if x["district"] == district and x["type"] in ("ring", "alley", "avenue")]
        fronts += [band_front(phi, 1), band_front(phi, -1)]
        for fr in fronts:
            L = polyline_len(fr["pts"])
            for side in (1, -1):
                for s0 in np.arange(w / 2 + 1, L - w / 2, 3.0):
                    r = self.try_frontage(fr, side, float(s0), w, d, district, (s0 - 0.01, s0 + 0.01), region,
                                          shape, max_tries=1)
                    if r:
                        p = self.commit_parcel(name, district, btype, label, r[0], r[1], w, d, interior, extra, shape)
                        p["placed_by"] = "fallback"
                        return p
        self.report["unplaced"].append({"name": name, "district": district, "w": w, "d": d})
        return None

    def rollback(self, mark):
        """Deshace todo lo creado con fid >= mark (borra celdas y registros)."""
        ids = [f for f in self.features if f >= mark]
        if not ids:
            return
        sub = self.g.lab
        sub[sub >= mark] = 0
        for f in ids:
            d = self.features.pop(f)
            for lst in (self.roads, self.plazas, self.parcels, self.zones):
                if d in lst:
                    lst.remove(d)
        self.next_id = mark

    def marker(self, name, loc, ang, props):
        self.markers.append({"name": name, "loc": loc, "angle": ang, "props": props})


def _hw_at(pts, hw, s):
    acc = 0.0
    for k, (a, b) in enumerate(zip(pts, pts[1:])):
        L = hypot(b[0] - a[0], b[1] - a[1])
        if acc + L >= s:
            t = 0.0 if L == 0 else (s - acc) / L
            return hw[k] + (hw[k + 1] - hw[k]) * t
        acc += L
    return hw[-1]


def point_in_poly(x, y, poly):
    c = False
    n = len(poly)
    for i in range(n):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % n]
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
            c = not c
    return c


def s_of_u(front, u, phi):
    """Distancia sobre una polilinea radial cuyo primer punto esta en u0."""
    u0, _ = to_local(*front["pts"][0], phi)
    return u - u0


def s_of_theta(front, theta_local_deg, phi):
    """Distancia sobre un anillo (polilinea CCW) hasta el angulo local dado (0 = eje)."""
    pts = front["pts"]
    best, acc, sbest = 1e9, 0.0, 0.0
    for a, b in zip(pts, pts[1:]):
        th = degrees(atan2(*reversed(to_local(*a, phi))))
        if abs(th - theta_local_deg) < best:
            best, sbest = abs(th - theta_local_deg), acc
        acc += hypot(b[0] - a[0], b[1] - a[1])
    return sbest


# ---------------------------------------------------------------------------
# Red de calles
# ---------------------------------------------------------------------------
def wobble(name, theta_deg):
    r = rng_for("wobble", name)
    a1 = r.uniform(*WOBBLE_M) * 0.7
    a2 = r.uniform(*WOBBLE_M) * 0.3
    p1, p2 = r.uniform(0, 2 * pi), r.uniform(0, 2 * pi)
    k1, k2 = r.choice((5, 6, 7)), r.choice((13, 15, 17))
    t = radians(theta_deg)
    return a1 * sin(k1 * t + p1) + a2 * sin(k2 * t + p2)


def ring_polyline(P, name, R, phi, halfw):
    """Tramo del anillo dentro del distrito, desde el eje hacia cada lado hasta topar con obstaculos."""
    g = P.g

    def ok(th):
        r = R + wobble(name, phi + th)
        x, y = to_world(r * cos(radians(th)), r * sin(radians(th)), phi)
        sl, m = g.circle_mask((x, y), halfw + 0.5)
        return not g.blocked[sl][m].any() and in_district(x, y, phi, margin=-halfw), (x, y)

    side_pts = {}
    for sgn in (-1, 1):
        pts = []
        th = 0.0
        while abs(th) <= C.CARDINAL_HALF_ANGLE:
            good, p = ok(th)
            if not good:
                break
            pts.append(p)
            th += sgn * 0.25
        side_pts[sgn] = pts
    pts = list(reversed(side_pts[-1])) + side_pts[1][1:]
    return pts


def build_streets(P):
    tan_h = np.tan(radians(C.CARDINAL_HALF_ANGLE))
    for dist, phi in DISTRICT_AXIS.items():
        key = DISTRICT_KEY[dist]
        # avenida axial: 10 m (r 60..89) y banda del eje de 30 m (r >= 89, frontal empedrado)
        us = [C.PLAZA_RADIUS - 0.5] + [float(u) for u in range(62, int(PLAZOLETA_U - PLAZOLETA_D / 2) + 2, 2)]
        pts = [to_world(u, 0.0, phi) for u in us]
        P.add_road(f"STR_{key}_Avenue", dist, "avenue", pts, AVENUE_W / 2, priority=10,
                   extra={"carriage_w": AVENUE_W, "u_range": [us[0], us[-1]]})
        # banda del eje (30 m, terreno de la etapa 02): frente empedrado a ambos lados de la avenida
        ub0, ub1 = AXIS_BAND_U0, PLAZOLETA_U
        P.add_plaza(f"PLZ_{key}_AxisFrontage", dist, "axis_frontage",
                    local_rect(phi, ub0, ub1, -T.HALF_BAND, T.HALF_BAND), "cobble",
                    extra={"u_range": [ub0, ub1], "note": "banda del eje de la etapa 02 (30 m); avenida de 10 m en el centro"})
        # plazoleta frente a la puerta sellada (30 m de diametro, borde exterior en el pie de muralla)
        c = to_world(PLAZOLETA_U, 0.0, phi)
        P.add_plaza(f"PLZ_{key}_Plazoleta", dist, "plazoleta", circle_poly(c, PLAZOLETA_D / 2), "flagstone",
                    circle=(c, PLAZOLETA_D / 2), extra={"gate": f"MARKER_Gate_{'ENWS'[int(phi // 90)]}"})
        # tramo de la avenida dentro de la plazoleta hasta la puerta (para la mascara de desgaste)
        pts = [to_world(u, 0.0, phi) for u in (PLAZOLETA_U - PLAZOLETA_D / 2, C.CARD_EMBANK_END)]
        P.add_road(f"STR_{key}_GateApproach", dist, "avenue", pts, AVENUE_W / 2, priority=9, over=False)
    for dist, phi in DISTRICT_AXIS.items():
        key = DISTRICT_KEY[dist]
        for R, W, tag in ((RING1_R, RING1_W, "Ring100"), (RING2_R, RING2_W, "Ring150")):
            w = MERCADO_STREET_W if dist == "Mercado" else W
            pts = ring_polyline(P, f"{tag}", R, phi, w / 2)
            P.add_road(f"STR_{key}_{tag}", dist, "ring", pts, w / 2, priority=8,
                       extra={"radius_nominal": R, "awnings": dist == "Mercado"})
    # calles diagonales (plaza -> hito -> escalinata de la Morada), rodeando el basamento del hito
    for phi, lm in DIAG_LANDMARK.items():
        build_diagonal(P, phi, lm)


def landmark_extent(P, phi):
    """(u_min, u_max, v_abs_max) de las celdas de estructura cerca del eje diagonal en r 60..94."""
    g = P.g
    sl, X, Y = g.window(-100, 100, -100, 100)
    A = radians(phi)
    U = X * cos(A) + Y * sin(A)
    V = -X * sin(A) + Y * cos(A)
    m = (g.raw_obst[sl] == Grid.OBST) & (U > C.PLAZA_RADIUS + 0.5) & (U < C.DIAG_LANDMARK_END - 1) & (np.abs(V) < 30)
    if not m.any():
        return None
    return float(U[m].min()), float(U[m].max()), float(np.abs(V[m]).max())


def build_diagonal(P, phi, lm):
    """Calle diagonal de 6 m: plaza (r=60) -> fachada del hito; detras del hito -> escalinata de la Morada.
    El basamento del hito no se rodea con calle: la zona de hitos (r 60-95) ya es llana y transitable."""
    hw = DIAG_W / 2
    ext = landmark_extent(P, phi)
    u_end = T.ESC_U0 - 0.3
    name = f"STR_DIAG_{int(phi):03d}_{lm}"
    if ext is None:
        P.add_road(name, "Diagonal", "diagonal", [to_world(u, 0, phi) for u in (C.PLAZA_RADIUS - 0.5, u_end)], hw, 7)
        return
    u0, u1, _va = ext
    ua, ub = u0 - 0.6, u1 + 0.6
    P.add_road(name + "_In", "Diagonal", "diagonal",
               [to_world(u, 0, phi) for u in (C.PLAZA_RADIUS - 0.5, ua)], hw, 7, extra={"ends_at": lm})
    if u_end - ub > 3.0:
        P.add_road(name + "_Out", "Diagonal", "diagonal",
                   [to_world(u, 0, phi) for u in (ub, u_end)], hw, 7, extra={"from": lm})


def road(P, name):
    for r in P.roads:
        if r["name"] == name:
            return r
    raise KeyError(name)


def plaza(P, name):
    for p in P.plazas:
        if p["name"] == name:
            return p
    raise KeyError(name)


def perimeter_front(poly):
    """Borde de plaza como 'calle' de ancho 0 (CCW -> exterior a la derecha: side = -1)."""
    pts = list(poly) + [poly[0]]
    area = sum(a[0] * b[1] - b[0] * a[1] for a, b in zip(pts, pts[1:]))
    if area < 0:
        pts = list(reversed(pts))
    return {"pts": pts, "halfw": [0.0] * len(pts)}


def local_rect(phi, u0, u1, v0, v1):
    return [to_world(u, v, phi) for u, v in ((u0, v0), (u1, v0), (u1, v1), (u0, v1))]


# ---------------------------------------------------------------------------
# Distritos
# ---------------------------------------------------------------------------
def av_front(P, key, phi, u0, u1):
    a = road(P, f"STR_{key}_Avenue")
    return a, s_of_u(a, (u0 + u1) / 2, phi), (s_of_u(a, u0, phi), s_of_u(a, u1, phi))


def band_front(phi, sgn):
    """Borde de la banda del eje (|v| = 15) como frente de ancho 0, sentido +u.
    side = sgn -> la parcela queda en el lado v*sgn > 15 (fuera de la banda)."""
    pts = [to_world(u, sgn * T.HALF_BAND, phi) for u in np.arange(AXIS_BAND_U0, PLAZOLETA_U + 0.1, 1.0)]
    return {"pts": pts, "halfw": [0.0] * len(pts), "u0": AXIS_BAND_U0}


def bf(phi, sgn, u, u_lo, u_hi):
    f = band_front(phi, sgn)
    return (f, sgn, u - AXIS_BAND_U0, (u_lo - AXIS_BAND_U0, u_hi - AXIS_BAND_U0))


def ring_s(P, key, tag, th, phi):
    r = road(P, f"STR_{key}_{tag}")
    return r, s_of_theta(r, th, phi)


def build_mercado(P):
    D, phi, key = "Mercado", DISTRICT_AXIS["Mercado"], "MER"
    c = to_world(FOUNTAIN_R, 0.0, phi)
    P.add_plaza("PLZ_MER_FuenteMercado", D, "fountain_square", circle_poly(c, FOUNTAIN_D / 2), "flagstone",
                circle=(c, FOUNTAIN_D / 2))
    P.marker("MARKER_Prop_FuenteMercado", c, phi + 180.0, {"type": "fountain", "district": D,
                                                           "plaza_d_m": FOUNTAIN_D})
    av, sm, _ = av_front(P, key, phi, 0, 0)
    sA = (s_of_u(av, 62, phi), s_of_u(av, 88.5, phi))
    r1o = lambda th: (road(P, "STR_MER_Ring100"), -1, s_of_theta(road(P, "STR_MER_Ring100"), th, phi))  # noqa: E731
    r2o = lambda th: (road(P, "STR_MER_Ring150"), -1, s_of_theta(road(P, "STR_MER_Ring150"), th, phi))  # noqa: E731
    r2i = lambda th: (road(P, "STR_MER_Ring150"), 1, s_of_theta(road(P, "STR_MER_Ring150"), th, phi))  # noqa: E731
    P.place("MARKER_Bld_Posada", D, "posada", "Posada", 20, 16, True,
            [(av, -1, s_of_u(av, 76, phi), sA)], extra={"service": "posada", "group_board": True})
    P.place("MARKER_Bld_CasaRegistro", D, "registro", "Casa del Registro", 14, 12, True,
            [(av, 1, s_of_u(av, 76, phi), sA)], extra={"service": "registro"})
    P.place("MARKER_Bld_TesoreriaMuralla", D, "tesoreria", "Tesoreria de la Muralla", 28, 18, True,
            [bf(phi, 1, 125, 107, 143)], extra={"service": "tesoreria"})
    P.place("MARKER_Bld_Banco", D, "banco", "Banco", 24, 20, True,
            [bf(phi, -1, 125, 107, 143)], extra={"service": "banco"})
    P.place("MARKER_Bld_GranSubasta", D, "subasta", "Gran Subasta", 40, 16, True,
            [r2o(-14.0), r2o(14.0), r2i(-14.0)], extra={"service": "subasta"})
    # Plaza de Provisiones: plaza 30 x 18 frente al anillo 150 (lado exterior, +v)
    prov = None
    rr = road(P, "STR_MER_Ring150")
    for th in [13.0 + k * sg for k in range(0, 10) for sg in (1, -1)]:
        s = s_of_theta(rr, th, phi)
        p, t, nl = frame_at(rr["pts"], s)
        h = _hw_at(rr["pts"], rr["halfw"], s)
        nx, ny = -nl[0], -nl[1]
        cc = (p[0] + nx * (h + 9.1), p[1] + ny * (h + 9.1))
        ang = degrees(atan2(-ny, -nx))
        poly = rect_poly(cc, ang, 30.0, 18.0)
        if P.rect_ok(poly, D, allow=(rr["fid"],)):
            prov = P.add_plaza("PLZ_MER_PlazaProvisiones", D, "market_square", poly, "cobble",
                               extra={"stalls": STALLS})
            build_stalls(P, cc, ang)
            break
    if prov is None:
        P.report["unplaced"].append({"name": "PLZ_MER_PlazaProvisiones", "district": D})
    return {"ring_out": r1o}


def build_stalls(P, c, ang):
    """14 puestos de 3x3 en 2 filas de 7 enfrentadas a un pasillo central de 4 m."""
    a = radians(ang)
    fx, fy = cos(a), sin(a)
    rx, ry = sin(a), -cos(a)
    k = 0
    for row, sgn in ((0, 1), (1, -1)):
        off = sgn * (2.0 + STALL / 2)               # pasillo de 4 m en el centro
        for i in range(7):
            k += 1
            t = (i - 3) * (STALL + 1.0)
            cx = c[0] + rx * t + fx * off
            cy = c[1] + ry * t + fy * off
            face = ang + (180.0 if sgn > 0 else 0.0)    # el frente mira al pasillo
            P.commit_parcel(f"MARKER_Bld_PuestoProvisiones_{k:02d}", "Mercado", "stall", f"Puesto {k}",
                            (cx, cy), face, STALL, STALL, False, extra={"service": "provisiones",
                                                                         "has_service": True})


def build_oficios(P):
    D, phi, key = "Oficios", DISTRICT_AXIS["Oficios"], "OFI"
    av = road(P, "STR_OFI_Avenue")
    sA = (s_of_u(av, 62, phi), s_of_u(av, 88.5, phi))
    r1 = road(P, "STR_OFI_Ring100")
    r2 = road(P, "STR_OFI_Ring150")
    s1 = lambda th: s_of_theta(r1, th, phi)  # noqa: E731
    s2 = lambda th: s_of_theta(r2, th, phi)  # noqa: E731
    # reserva del Cauce: llega al desague del bastion k=46 (345 grados); corredor radial de 6 m
    th_c = 46 * 7.5 - 360.0                      # -15 grados (local = mundo en Oficios)
    cauce = [to_world(rr * cos(radians(th_c)), rr * sin(radians(th_c)), phi) for rr in (152.0, 196.0)]
    a = radians(th_c)
    nx, ny = -sin(a), cos(a)
    poly = [(cauce[0][0] - nx * 3, cauce[0][1] - ny * 3), (cauce[1][0] - nx * 3, cauce[1][1] - ny * 3),
            (cauce[1][0] + nx * 3, cauce[1][1] + ny * 3), (cauce[0][0] + nx * 3, cauce[0][1] + ny * 3)]
    P.add_zone("ZONE_OFI_CauceReserva", D, "cauce_reserve", poly, "earth",
               extra={"note": "corredor reservado para el Cauce (Prompt 7); llega al desague del bastion k=46"})
    P.marker("MARKER_CauceReserve_Outlet", cauce[1], th_c, {"type": "cauce_reserve", "drain_slot": 46,
                                                            "width_m": 6.0})
    P.place("MARKER_Bld_CasaReparaciones", D, "reparaciones", "Casa de Reparaciones", 16, 10, True,
            [(av, 1, s_of_u(av, 75, phi), sA)], extra={"service": "reparaciones", "open_structure": True})
    P.place("MARKER_Bld_Taller_JoyeriaTallado", D, "taller", "Joyeria y Tallado", 16, 12, True,
            [(av, -1, s_of_u(av, 75, phi), sA)], extra={"service": "joyeria_tallado"})
    P.place("MARKER_Bld_Taller_GranForja", D, "taller", "Gran Forja", 26, 16, True,
            [bf(phi, -1, 125, 107, 143)], extra={"service": "forja", "open_foundry": True,
                                                 "foundry_yard_m": "10x16 (extremo exterior)"})
    P.place("MARKER_Bld_CrisolPiedras", D, "crisol", "Crisol de las Piedras", 22, 22, True,
            [bf(phi, 1, 125, 107, 143)], shape="circle", extra={"service": "crisol", "diameter_m": 22})
    place_with_yard(P, D, "MARKER_Bld_Gremio_Herbolarios", "gremio", "Gremio de Herbolarios", 22, 12,
                    {"service": "gremio_herbolarios", "herb_terraces": "ZONE_OFI_TerrazasHierbas (3 escalones)"},
                    "ZONE_OFI_TerrazasHierbas", "herb_terraces", 9.0,
                    [(r2, -1, s2(18.5)), (r2, -1, s2(10.0)), (r2, -1, s2(-18.5))],
                    zone_extra={"steps": 3, "step_rise_m": 0.3})
    # Gremio de Cazadores + campo de tiro: una sola huella 20 x 24.6 (14 + 0.6 + 10) que luego se divide
    caz = None
    dd = 14 + TRAUFGASSE + 10
    cands = [(r1, -1, s1(9.0)), (r1, -1, s1(-9.0)), (r2, 1, s2(9.0)), (r2, 1, s2(-9.0))]
    fr_all = [x for x in P.roads if x["district"] == D and x["type"] in ("ring", "alley")]
    for fr in fr_all:
        Lf = polyline_len(fr["pts"])
        cands += [(fr, sd, float(s0)) for sd in (1, -1) for s0 in np.arange(10.0, Lf - 10.0, 4.0)]
    cands += [(band_front(phi, sg), sg, float(u - AXIS_BAND_U0)) for sg in (1, -1) for u in range(100, 176, 4)]
    for fr, side, s0 in cands:
        res = P.try_frontage(fr, side, s0, 20, dd, D, max_tries=2)
        if res:
            c, ang = res
            a = radians(ang)
            fx, fy = cos(a), sin(a)
            cb = (c[0] + fx * (dd - 14) / 2, c[1] + fy * (dd - 14) / 2)
            caz = P.commit_parcel("MARKER_Bld_Gremio_Cazadores", D, "gremio", "Gremio de Cazadores", cb, ang, 20, 14,
                                  True, extra={"service": "gremio_cazadores", "range": "ZONE_OFI_CampoTiro 20x10"})
            cr = (c[0] - fx * (dd - 10) / 2, c[1] - fy * (dd - 10) / 2)
            z = P.add_zone("ZONE_OFI_CampoTiro", D, "archery_range", rect_poly(cr, ang, 20, 10), "earth")
            z["parent"] = caz["name"]
            P.marker("MARKER_ArcheryRange_Targets", (cr[0] - fx * 4.0, cr[1] - fy * 4.0), ang + 180.0,
                     {"type": "archery_targets", "district": D, "range_m": "20x10", "targets": 4})
            break
    if caz is None:
        P.report["unplaced"].append({"name": "MARKER_Bld_Gremio_Cazadores+CampoTiro", "district": D})
    P.place("MARKER_Bld_Taller_Alquimia", D, "taller", "Alquimia", 16, 12, True,
            [(r1, 1, s1(12.0)), (r1, 1, s1(-12.0))], extra={"service": "alquimia"})
    P.place("MARKER_Bld_Taller_Sastreria", D, "taller", "Sastreria", 16, 12, True,
            [(r1, -1, s1(18.0)), (r1, -1, s1(-18.0))], extra={"service": "sastreria"})
    P.place("MARKER_Bld_Taller_Hornos", D, "taller", "Hornos de Concordia", 16, 12, True,
            [(r1, -1, s1(-18.0)), (r1, -1, s1(18.0))], extra={"service": "hornos"})
    P.place("MARKER_Bld_Taller_Carpinteria", D, "taller", "Carpinteria", 16, 12, True,
            [(r2, 1, s2(-17.0)), (r2, 1, s2(17.0))], extra={"service": "carpinteria"})
    # junto al Cauce (lado -v del distrito): Pescadores y Curtiduria a ambos lados del corredor
    P.place("MARKER_Bld_Gremio_Pescadores", D, "gremio", "Gremio de Pescadores", 18, 14, True,
            [(r2, -1, s2(th_c + 4.6)), (r2, -1, s2(th_c + 6.0))], extra={"service": "gremio_pescadores",
                                                                         "next_to": "ZONE_OFI_CauceReserva"})
    P.place("MARKER_Bld_Taller_Curtiduria", D, "taller", "Curtiduria", 16, 12, True,
            [(r2, -1, s2(th_c - 4.2)), (r2, -1, s2(th_c - 6.0))], extra={"service": "curtiduria",
                                                                         "next_to": "ZONE_OFI_CauceReserva"})
    P.place("MARKER_Bld_Gremio_Mineros", D, "gremio", "Gremio de Mineros", 18, 14, True,
            [(r2, -1, s2(8.0)), (r2, -1, s2(18.0))], extra={"service": "gremio_mineros"})


def place_with_yard(P, D, name, btype, label, w, d, extra, zname, ztype, zd, cands, zone_extra=None):
    """Parcela + zona detras (huella conjunta w x (d + 0.6 + zd)), probando candidatos y luego cualquier fachada."""
    phi = DISTRICT_AXIS[D]
    dd = d + TRAUFGASSE + zd
    cands = list(cands)
    for fr in [x for x in P.roads if x["district"] == D and x["type"] in ("ring", "alley")]:
        Lf = polyline_len(fr["pts"])
        cands += [(fr, sd, float(s0)) for sd in (1, -1) for s0 in np.arange(w / 2 + 1, Lf - w / 2 - 1, 4.0)]
    cands += [(band_front(phi, sg), sg, float(u - AXIS_BAND_U0)) for sg in (1, -1) for u in range(100, 176, 4)]
    for fr, side, s0 in cands:
        res = P.try_frontage(fr, side, s0, w, dd, D, max_tries=3)
        if not res:
            continue
        c, ang = res
        a = radians(ang)
        fx, fy = cos(a), sin(a)
        cb = (c[0] + fx * (dd - d) / 2, c[1] + fy * (dd - d) / 2)
        p = P.commit_parcel(name, D, btype, label, cb, ang, w, d, True, extra=extra)
        cz = (c[0] - fx * (dd - zd) / 2, c[1] - fy * (dd - zd) / 2)
        z = P.add_zone(zname, D, ztype, rect_poly(cz, ang, w, zd), "earth", extra=zone_extra)
        z["parent"] = name
        return p, z
    P.report["unplaced"].append({"name": f"{name}+{zname}", "district": D})
    return None, None


def add_behind_zone(P, parcel, name, ztype, w, d, surface, extra=None, report=True):
    a = radians(parcel["angle"])
    fx, fy = cos(a), sin(a)
    c0 = parcel["center"]
    off = parcel["d"] / 2 + TRAUFGASSE + d / 2
    c = (c0[0] - fx * off, c0[1] - fy * off)
    poly = rect_poly(c, parcel["angle"], w, d)
    if P.rect_ok(poly, parcel["district"]):
        z = P.add_zone(name, parcel["district"], ztype, poly, surface, extra=extra)
        z["parent"] = parcel["name"]
        return z
    if report:
        P.report["unplaced"].append({"name": name, "district": parcel["district"]})
    return None


def add_side_zone(P, parcel, name, ztype, w, d, surface, report=True):
    a = radians(parcel["angle"])
    rx, ry = sin(a), -cos(a)
    fx, fy = cos(a), sin(a)
    c0 = parcel["center"]
    for sgn in (1, -1):
        off = parcel["w"] / 2 + TRAUFGASSE + w / 2
        c = (c0[0] + sgn * rx * off - fx * (parcel["d"] - d) / 2, c0[1] + sgn * ry * off - fy * (parcel["d"] - d) / 2)
        poly = rect_poly(c, parcel["angle"], w, d)
        if P.rect_ok(poly, parcel["district"]):
            z = P.add_zone(name, parcel["district"], ztype, poly, surface)
            z["parent"] = parcel["name"]
            return z
    if report:
        P.report["unplaced"].append({"name": name, "district": parcel["district"]})
    return None


def build_clases(P):
    D, phi, key = "Clases", DISTRICT_AXIS["Clases"], "CLA"
    av = road(P, "STR_CLA_Avenue")
    r1 = road(P, "STR_CLA_Ring100")
    r2 = road(P, "STR_CLA_Ring150")
    # Plaza de las Armas entre los dos anillos, centrada en el eje (50 tangencial x 40 radial)
    u_in = RING1_R + RING1_W / 2 - 0.5
    u_out = u_in + ARMAS[1]
    poly = local_rect(phi, u_in, u_out, -ARMAS[0] / 2, ARMAS[0] / 2)
    armas = P.add_plaza("PLZ_CLA_PlazaArmas", D, "training_square", poly, "cobble+tamped_earth",
                        extra={"size_m": "50x40", "u_range": [u_in, u_out]})
    # 6 zonas de maniquies (3 por lado de la avenida), tierra apisonada
    k = 0
    du = ARMAS[1] / 3
    for sgn in (1, -1):
        for i in range(3):
            k += 1
            ua, ub = u_in + i * du + 1.0, u_in + (i + 1) * du - 1.0
            va, vb = sorted((sgn * 8.0, sgn * (ARMAS[0] / 2 - 2.0)))
            zp = local_rect(phi, ua, ub, va, vb)
            P.add_zone(f"ZONE_CLA_Maniquies_{k:02d}", D, "training_dummies", zp, "tamped_earth", paint=False)
            cu, cv = (ua + ub) / 2, (va + vb) / 2
            P.marker(f"MARKER_TrainingZone_{k:02d}", to_world(cu, cv, phi), phi + 180.0 if sgn > 0 else phi,
                     {"type": "training_dummies", "district": D, "footprint": f"{ub - ua:.1f}x{vb - va:.1f}",
                      "dummies": 4})
    P.place("MARKER_Bld_CasaReposicion", D, "reposicion", "Casa de Reposicion", 24, 12, True,
            [(av, 1, s_of_u(av, 76, phi), (s_of_u(av, 62, phi), s_of_u(av, 88.5, phi))),
             (av, -1, s_of_u(av, 76, phi), (s_of_u(av, 62, phi), s_of_u(av, 88.5, phi)))],
            extra={"service": "reposicion"})
    # salones de clase en abanico: lados de la plaza (miran a la plaza) y anillo 150 exterior (miran a la plaza)
    pf = perimeter_front(poly)
    slots = []
    Lp = polyline_len(pf["pts"])
    # puntos de los lados laterales de la plaza (|v| = 25): localizar por muestreo
    for frac_u in (0.27, 0.73):
        for sgn in (1, -1):
            target = to_world(u_in + frac_u * ARMAS[1], sgn * ARMAS[0] / 2, phi)
            slots.append((pf, -1, nearest_s(pf["pts"], target)))
    for th in (12.5, -12.5, 20.0, -20.0, 6.5, -6.5):
        slots.append((r2, -1, s_of_theta(r2, th, phi)))
    for th in (13.0, -13.0, 19.0, -19.0):
        slots.append((r1, 1, s_of_theta(r1, th, phi)))
    placed = 0
    for i in range(N_CLASES):
        ok = None
        while slots and ok is None:
            fr, side, s0 = slots.pop(0)
            r = P.try_frontage(fr, side, s0, 18, 14, D, (s0 - 6, s0 + 6) if fr is pf else None)
            if r:
                ok = P.commit_parcel(f"MARKER_Bld_SalonClase_{i + 1:02d}", D, "class_hall", f"Salon de clase {i + 1}",
                                     r[0], r[1], 18, 14, True, extra={"service": "clase", "class_slot": i + 1})
        if ok is None:
            P.report["unplaced"].append({"name": f"MARKER_Bld_SalonClase_{i + 1:02d}", "district": D})
        else:
            placed += 1
    P.report["clases_placed"] = placed
    _ = Lp, armas


def nearest_s(pts, p):
    best, sb, acc = 1e9, 0.0, 0.0
    for a, b in zip(pts, pts[1:]):
        L = hypot(b[0] - a[0], b[1] - a[1])
        for t in np.linspace(0, 1, max(2, int(L * 2))):
            q = (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)
            d = hypot(q[0] - p[0], q[1] - p[1])
            if d < best:
                best, sb = d, acc + L * t
        acc += L
    return sb


def polar_block(phi, sgn, r0, r1, v_band, th_out=None, th_in=None, step=1.0):
    """Bloque limitado por dos arcos (r0, r1), la linea |v| = v_band (o el angulo th_in) y el borde
    lateral (o el angulo th_out). Poligono en coordenadas de mundo."""
    th_max = C.CARDINAL_HALF_ANGLE + 0.5 if th_out is None else th_out

    def th_lo(r):
        return degrees(np.arcsin(min(1.0, v_band / r))) if th_in is None else th_in
    pts = []
    n0 = max(4, int((th_max - th_lo(r0)) * radians(1) * r0 / step))
    for k in range(n0 + 1):
        t = th_lo(r0) + (th_max - th_lo(r0)) * k / n0
        pts.append((r0 * cos(radians(t)), sgn * r0 * sin(radians(t))))
    n1 = max(4, int((th_max - th_lo(r1)) * radians(1) * r1 / step))
    for k in range(n1, -1, -1):
        t = th_lo(r1) + (th_max - th_lo(r1)) * k / n1
        pts.append((r1 * cos(radians(t)), sgn * r1 * sin(radians(t))))
    return [to_world(u, v, phi) for u, v in pts]


def razas_slots(phi):
    """Bloques candidatos de ~35 x 35 m para los barrios (arcos entre anillos), en orden de preferencia.
    Los bordes se meten 2.5 m dentro de las calles que los limitan: las celdas de calle ya bloquean y
    asi las casas pueden dar fachada a esas calles sin salirse del bloque."""
    vb = T.HALF_BAND - 1.0
    e1 = RING1_R + RING1_W / 2 - 2.5
    i2 = RING2_R - RING2_W / 2 + 2.5
    e2 = RING2_R + RING2_W / 2 - 2.5
    u_out = WALL_LANE_R - WALL_LANE_W / 2 + 2.0
    out = []
    for sgn in (1, -1):
        out.append(("B", sgn, polar_block(phi, sgn, e1, i2, vb)))
    for sgn in (1, -1):
        out.append(("C", sgn, polar_block(phi, sgn, e2, u_out, vb)))
    for sgn in (1, -1):
        out.append(("A", sgn, polar_block(phi, sgn, 62.0, RING1_R - RING1_W / 2 + 2.5, AVENUE_W / 2 - 1.0)))
    return out


def poly_centroid(poly):
    a = cx = cy = 0.0
    n = len(poly)
    for i in range(n):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % n]
        cr = x1 * y2 - x2 * y1
        a += cr
        cx += (x1 + x2) * cr
        cy += (y1 + y2) * cr
    a *= 0.5
    return (cx / (6 * a), cy / (6 * a))


def build_razas(P):
    D, phi = "Razas", DISTRICT_AXIS["Razas"]
    slots = razas_slots(phi)
    made = []
    for b in range(N_RAZAS):
        res = None
        while slots and not (res and res.get("placed")):
            tag, sgn, region = slots.pop(0)
            res = build_barrio(P, b + 1, tag, sgn, region)
        if not (res and res.get("placed")):
            P.report["unplaced"].append({"name": f"Barrio_Raza_{b + 1:02d}", "district": D})
        made.append(res)
    P.report["razas_barrios"] = made


def build_barrio(P, idx, tag, sgn, region):
    """Barrio de raza en un bloque entre calles: plazuela de 10 m abierta a una calle (ensanche),
    Casa de Raza (20 x 16) mirando a la plazuela y 6-10 casas en las fachadas del bloque."""
    D, phi = "Razas", DISTRICT_AXIS["Razas"]
    r = rng_for("barrio", idx)
    g = P.g
    cen0 = poly_centroid(region)
    xs = [p[0] for p in region]
    ys = [p[1] for p in region]
    R = PLAZUELA_D / 2
    cands = []
    for x in np.arange(min(xs), max(xs), 1.5):
        for y in np.arange(min(ys), max(ys), 1.5):
            if not point_in_poly(x, y, region):
                continue
            sl, m = g.circle_mask((x, y), R + 1.2)
            lab = g.lab[sl][m]
            if g.blocked[sl][m].any():
                continue
            ids = set(int(i) for i in np.unique(lab) if i > 0)
            if not ids or any(P.features[i]["kind"] not in ("road",) for i in ids):
                continue                                   # debe abrirse a una calle (y solo a calles)
            sl2, m2 = g.circle_mask((x, y), R - 0.5)
            if (g.lab[sl2][m2] != 0).any():
                continue
            cands.append((hypot(x - cen0[0], y - cen0[1]), (float(x), float(y))))
    cands.sort()
    casa = pz = None
    for _dist, cen in cands[:150]:
        mark = P.next_id
        pz = P.add_plaza(f"PLZ_RAZ_Plazuela_{idx:02d}", D, "plazuela", circle_poly(cen, R), "cobble",
                         circle=(cen, R), extra={"barrio": idx})
        a_rad = degrees(atan2(cen[1], cen[0]))
        for k in range(4):
            a_out = radians(a_rad + 90.0 * k)
            front = {"pts": [(cen[0] + cos(a_out) * R - sin(a_out) * t, cen[1] + sin(a_out) * R + cos(a_out) * t)
                             for t in (-12.0, 12.0)], "halfw": [0.0, 0.0]}
            res = None
            for eb in (0.0, 1.0, 2.0):
                res = P.try_frontage(front, -1, 12.0, RAZA_HOUSE[0], RAZA_HOUSE[1], D, (10.0, 14.0), region,
                                     extra_setbacks=(eb,), step=0.5, max_tries=5)
                if res:
                    break
            if res:
                casa = P.commit_parcel(f"MARKER_Bld_CasaRaza_{idx:02d}", D, "race_house", f"Casa de Raza {idx}",
                                       res[0], res[1], RAZA_HOUSE[0], RAZA_HOUSE[1], True,
                                       extra={"service": "casa_raza", "barrio": idx, "race_slot": idx})
                break
        if casa:
            break
        P.rollback(mark)
        pz = None
    if casa is None:
        return {"barrio": idx, "slot": tag, "placed": False}
    cen = pz["circle"]["c"]
    feat = r.choice(("fountain", "tree"))
    P.marker(f"MARKER_Prop_Plazuela_{idx:02d}", cen, phi, {"type": feat, "district": D, "barrio": idx})
    pf = perimeter_front(circle_poly(cen, R, step=1.0))
    alleys = []
    target = r.randint(*HOUSES_PER_BARRIO)
    fronts = [(rd, s) for rd in P.roads if rd["district"] == D and rd["type"] in ("ring", "alley", "avenue")
              for s in (1, -1)]
    fronts += [(band_front(phi, sg), sg) for sg in (1, -1)] + [(pf, -1)]
    fronts = [(a, sd) for a in alleys for sd in (1, -1)] + fronts
    n = fill_houses(P, D, fronts, target, r, region, prefix=f"MARKER_Bld_RAZ_B{idx:02d}_Casa")
    return {"barrio": idx, "slot": tag, "side": sgn, "houses": n, "target": target, "placed": True,
            "casa_raza": casa["name"], "plazuela_feature": feat, "alleys": len(alleys), "region": region}


def poly_edge_dist(x, y, poly):
    d = 1e9
    n = len(poly)
    for i in range(n):
        (ax, ay), (bx, by) = poly[i], poly[(i + 1) % n]
        dx, dy = bx - ax, by - ay
        t = max(0.0, min(1.0, ((x - ax) * dx + (y - ay) * dy) / (dx * dx + dy * dy)))
        d = min(d, hypot(x - ax - t * dx, y - ay - t * dy))
    return d


def _dir_world(du, dv, phi):
    x, y = to_world(du, dv, phi)
    L = hypot(x, y)
    return (x / L, y / L)


def march_alley(P, start, direction, w, start_in, rng, max_len=60.0, bends=True, step=1.0, free_start=0.0):
    """Avanza desde 'start' hasta entrar en otra calle/plaza (callejon pasante). Gira suavemente
    (curvas de 15-30 grados, ref. Cesky Krumlov) y esquiva obstaculos hasta +-50 grados."""
    g = P.g
    pts = [start]
    x, y = start
    head0 = atan2(direction[1], direction[0])
    head = head0
    next_bend = rng.uniform(8, 15)
    s = 0.0
    left_origin = False
    while s < max_len:
        if bends and s >= next_bend:
            head = head0 + radians(rng.uniform(-20, 20))
            next_bend += rng.uniform(8, 15)
        moved = False
        sgn = rng.choice((1, -1))
        for dh in (0, 15, -15, 30, -30):
            hh = head + radians(dh * sgn)
            if abs(hh - head0) > radians(35):
                continue
            nx, ny = x + cos(hh) * step, y + sin(hh) * step
            f = g.at(nx, ny)
            if not left_origin and (f == start_in or (f > 0 and P.features[f]["kind"] in ("road", "plaza")
                                                       and s < 3.0)):
                x, y = nx, ny
                pts.append((x, y))
                moved = True
                break
            if f > 0 and f != start_in and P.features[f]["kind"] in ("road", "plaza") and left_origin:
                pts.append((nx + cos(hh) * 1.0, ny + sin(hh) * 1.0))
                return simplify(pts) if len(pts) >= 3 else None
            sl, m = g.circle_mask((nx, ny), w / 2 + 0.4)
            sub = g.lab[sl][m]
            blk = (g.raw_obst[sl][m] < 0).any() if s < free_start else g.blocked[sl][m].any()
            if blk or ((sub > 0).any() and not _only_roads(P, sub, start_in)):
                continue
            left_origin = True
            x, y, head = nx, ny, hh
            pts.append((x, y))
            moved = True
            break
        if not moved:
            return None
        s += step
    return None


def _only_roads(P, sub, start_in):
    ids = set(int(i) for i in np.unique(sub) if i > 0)
    return all(i == start_in or P.features[i]["kind"] in ("road", "plaza") for i in ids)


def simplify(pts, tol=0.05):
    out = [pts[0]]
    for i in range(1, len(pts) - 1):
        a, b, c = out[-1], pts[i], pts[i + 1]
        cr = (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])
        if abs(cr) > tol:
            out.append(b)
    out.append(pts[-1])
    return out


def build_alleys(P, D):
    """Callejones de 4-5 m que cruzan las manzanas entre calles (seed 11); 15 % se cortan (ciegos)."""
    phi = DISTRICT_AXIS[D]
    key = DISTRICT_KEY[D]
    r = rng_for("alleys", D)
    made = []
    band = plaza(P, f"PLZ_{key}_AxisFrontage")
    sources = [(x, x["fid"], x["halfw"]) for x in P.roads if x["district"] == D and x["type"] == "ring"]
    sources += [(band_front(phi, sg), band["fid"], None) for sg in (1, -1)]
    for src, fid, hw in sources:
        L = polyline_len(src["pts"])
        last = {1: -1e9, -1: -1e9}
        s = r.uniform(4, 9)
        while s < L - 4:
            p, t, nl = frame_at(src["pts"], s)
            h = _hw_at(src["pts"], hw, s) if hw else 0.0
            for side in (1, -1):
                if hw is None and side != (1 if to_local(*p, phi)[1] > 0 else -1):
                    continue                       # banda: solo hacia fuera de la banda
                if s - last[side] < 26.0:
                    continue
                w = r.uniform(*ALLEY_W)
                nx, ny = nl[0] * side, nl[1] * side
                start = (p[0] + nx * (h - 0.5), p[1] + ny * (h - 0.5))
                pts = march_alley(P, start, (nx, ny), w, fid, r, max_len=55.0)
                if pts and polyline_len(pts) > 8.0:
                    made.append(P.add_road(f"STR_{key}_Callejon_{len(made) + 1:02d}", D, "alley", pts, w / 2, 3,
                                           over=False, extra={"blind": False}))
                    last[side] = s
            s += r.uniform(5, 9)
    return made


def connect_lane_to_link(P, ln, links):
    if end_connected(P, ln):
        return
    e = ln["pts"][-1]
    best = None
    for lk in links:
        c = lk["circle"]["c"]
        d = hypot(c[0] - e[0], c[1] - e[1])
        if lk["district"] == ln["district"] and d < 22.0 and (best is None or d < best[0]):
            best = (d, lk)
    if best is None:
        return
    c = best[1]["circle"]["c"]
    d = ((c[0] - e[0]) / best[0], (c[1] - e[1]) / best[0])
    tail = march_alley(P, e, d, WALL_LANE_W - 0.5, ln["fid"], rng_for("lanetail", ln["name"]), max_len=26.0,
                       bends=False, free_start=26.0)
    if tail:
        ln["pts"] = ln["pts"] + tail[1:]
        ln["halfw"] = [ln["halfw"][0]] * len(ln["pts"])
        sl, m = P.g.capsule_mask(ln["pts"], ln["halfw"][0])
        P.g.paint(sl, m, ln["fid"])
        ln["length_m"] = round(polyline_len(ln["pts"]), 1)


def trim_to_last_junction(P, a):
    """Corta el callejon tras su ultimo cruce con otra calle (sin contar la banda de salida)."""
    g = P.g
    start = g.at(*a["pts"][0])
    pts = resample(a["pts"], 1.0)
    last = None
    for i, p in enumerate(pts):
        if i < 4:
            continue
        sl, m = g.circle_mask(p, a["halfw"][0] + 1.0)
        ids = set(int(k) for k in np.unique(g.lab[sl][m]) if k > 0) - {a["fid"], start}
        if any(P.features[k]["kind"] in ("road", "plaza") for k in ids):
            last = i
    if last is None or last >= len(pts) - 2:
        return
    sl, m = g.capsule_mask(a["pts"], a["halfw"][0])
    sub = g.lab[sl]
    sub[m & (sub == a["fid"])] = 0
    a["pts"] = simplify(pts[:last + 2])
    a["halfw"] = [a["halfw"][0]] * len(a["pts"])
    a["length_m"] = round(polyline_len(a["pts"]), 1)
    sl, m = g.capsule_mask(a["pts"], a["halfw"][0])
    g.paint(sl, m, a["fid"])


def end_connected(P, a):
    """True si el extremo final del callejon toca otra calle/plaza distinta de la de salida."""
    g = P.g
    e = a["pts"][-1]
    sl, m = g.circle_mask(e, a["halfw"][-1] + 1.0)
    ids = set(int(i) for i in np.unique(g.lab[sl][m]) if i > 0) - {a["fid"]}
    start = g.at(*a["pts"][0])
    ids.discard(start)
    return any(P.features[i]["kind"] in ("road", "plaza") for i in ids)


def make_blind(P, alleys, D, quota=None):
    """Cierra callejones (corte al 55-70 % de su longitud) hasta 'quota' ciegos en el distrito."""
    r = rng_for("blind", D)
    for a in alleys:
        a["blind"] = not end_connected(P, a)
    have = sum(1 for a in alleys if a["blind"])
    n = max(0, (quota if quota is not None else int(round(ALLEY_BLIND_FRAC * len(alleys)))) - have)
    pool = [a for a in alleys if not a["blind"] and not a.get("lane") and not a.get("stair_link")
            and not a.get("barrio")]
    pick = r.sample(pool, min(n, len(pool))) if n else []
    for a in pick:
        L = polyline_len(a["pts"])
        cut = L * r.uniform(0.55, 0.7)
        pts = cut_polyline(a["pts"], cut)
        # repintar: borrar celdas del tramo eliminado
        g = P.g
        sl, m = g.capsule_mask(a["pts"], a["halfw"][0])
        sub = g.lab[sl]
        sub[m & (sub == a["fid"])] = 0
        a["pts"] = pts
        a["halfw"] = [a["halfw"][0]] * len(pts)
        a["blind"] = True
        a["length_m"] = round(polyline_len(pts), 1)
        sl, m = g.capsule_mask(pts, a["halfw"][0])
        g.paint(sl, m, a["fid"])
    return sum(1 for a in alleys if a["blind"])


def cut_polyline(pts, s_cut):
    out = [pts[0]]
    acc = 0.0
    for a, b in zip(pts, pts[1:]):
        L = hypot(b[0] - a[0], b[1] - a[1])
        if acc + L >= s_cut:
            t = (s_cut - acc) / L
            out.append((a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t))
            return out
        out.append(b)
        acc += L
    return out


def fill_houses(P, D, fronts, target, r, region=None, prefix=None):
    """Casas de decoracion (8x8 a 12x10, interior=false) a lo largo de las fachadas disponibles."""
    n = 0
    prefix = prefix or f"MARKER_Bld_{DISTRICT_KEY[D]}_Casa"
    for fr, side in fronts:
        L = polyline_len(fr["pts"])
        s = r.uniform(0.5, 3.0)
        while s < L and (target is None or n < target):
            res = None
            for k in range(3):                     # tamano aleatorio; si no cabe, se prueba mas pequeno
                w = r.uniform(*HOUSE_W) if k == 0 else (HOUSE_W[0] + (HOUSE_W[1] - HOUSE_W[0]) * (0.4 if k == 1 else 0.0))
                d = r.uniform(*HOUSE_D) if k == 0 else HOUSE_D[0]
                w, d = round(w * 2) / 2, round(d * 2) / 2
                res = P.try_frontage(fr, side, s + w / 2, w, d, D, (s + w / 2 - 0.01, s + w / 2 + 0.01), region,
                                     extra_setbacks=(0.0, 0.5, 1.0), max_tries=1)
                if res:
                    break
            if res:
                n += 1
                P.commit_parcel(f"{prefix}_{n:02d}", D, "house", "Casa", res[0], res[1], w, d, False,
                                extra={"decor": True})
                s += w + r.uniform(TRAUFGASSE, 1.4)
            else:
                s += 1.0
        if target is not None and n >= target:
            break
    return n


def add_mercado_awnings(P):
    k = 0
    for p in P.parcels:
        if p["district"] != "Mercado" or p["type"] == "stall" or not p["front"]:
            continue
        fr = next((x for x in P.roads if x["name"] == p["front"]), None)
        if fr is None or fr["type"] not in ("ring", "avenue"):
            continue
        k += 1
        P.marker(f"MARKER_Awning_{k:02d}", p["door"], p["angle"],
                 {"type": "awning", "district": "Mercado", "width_m": p["w"], "depth_m": 2.5, "parcel": p["name"]})
    return k


def add_patches(P):
    """8 parches remendados con otra piedra (sobre calles anchas y avenidas)."""
    r = rng_for("patches")
    cands = [x for x in P.roads if x["type"] in ("avenue", "ring")]
    out = []
    tries = 0
    while len(out) < 8 and tries < 400:
        tries += 1
        rd = r.choice(cands)
        L = polyline_len(rd["pts"])
        s = r.uniform(4, L - 4)
        p, t, nl = frame_at(rd["pts"], s)
        h = min(_hw_at(rd["pts"], rd["halfw"], s), 4.0)
        off = r.uniform(-h + 1.8, h - 1.8)
        c = (p[0] + nl[0] * off, p[1] + nl[1] * off)
        if any(hypot(c[0] - q["center"][0], c[1] - q["center"][1]) < 25 for q in out):
            continue
        if P.g.at(*c) != rd["fid"]:
            continue
        w, d = r.uniform(2.0, 3.6), r.uniform(1.4, 2.6)
        ang = degrees(atan2(t[1], t[0])) + r.uniform(-25, 25)
        poly = rect_poly(c, ang, w, d)
        # esquinas irregulares
        poly = [(x + r.uniform(-0.25, 0.25), y + r.uniform(-0.25, 0.25)) for x, y in poly]
        sl, m = P.g.poly_mask(poly)
        if not (P.g.lab[sl][m] == rd["fid"]).all():
            continue
        out.append({"name": f"PATCH_{len(out) + 1:02d}", "road": rd["name"], "district": rd["district"],
                    "center": c, "poly": poly, "dz": round(r.choice((-1, 1)) * r.uniform(0.008, 0.015), 3)})
    return out


def add_ruts(P):
    """Surcos de carreta en Oficios: 2 surcos (ancho de via 1.5 m) por sentido en avenida y anillos."""
    out = []
    for rd in P.roads:
        if rd["district"] != "Oficios" or rd["type"] not in ("avenue", "ring"):
            continue
        lanes = (-2.5, 2.5) if rd["type"] == "avenue" else (0.0,)
        for lane in lanes:
            for off in (-0.75, 0.75):
                pts = resample(rd["pts"], 2.0)
                o = lane + off
                line = []
                for i, p in enumerate(pts):
                    a = pts[max(0, i - 1)]
                    b = pts[min(len(pts) - 1, i + 1)]
                    tx, ty = b[0] - a[0], b[1] - a[1]
                    L = hypot(tx, ty)
                    line.append((p[0] - ty / L * o, p[1] + tx / L * o))
                # recortar dentro de la plazoleta / fuera del distrito
                line = [q for q in line if P.g.at(*q) == rd["fid"]]
                if len(line) > 3:
                    out.append({"road": rd["name"], "offset_m": o, "pts": line})
    return out


def stair_links(P, stairs):
    """Pequenos rellanos (r = 2 m) en el lado cardinal de cada escalera lateral (stage02): destino de
    callejones -> escalinatas entre barrios (ref. Mala Strana)."""
    edges = {f"{k}{s:+d}": (k, s, tb, e, n) for k, s, tb, e, n in T.lateral_edges()}
    out = []
    W = C.LATERAL_STAIR_WIDTH
    for st in stairs:
        k, side, tb, e, n_card = edges[st["edge"]]
        a_s = st["r_station"]
        a_top = a_s - W / 2
        if st["side_low"] == "cardinal":
            a, t = a_top - st["run_m"] - 2.4, 2.6
            nn = n_card
        else:
            a, t = a_s, 2.6
            nn = n_card
        p = (e[0] * a + nn[0] * t, e[1] * a + nn[1] * t)
        th = T.angle_deg(*p)
        D = {"Oficios": "Oficios", "Mercado": "Mercado", "Clases": "Clases", "Razas": "Razas"}[T.nearest_cardinal(th)]
        name = f"PLZ_StairLink_{st['edge'].replace('+', 'p').replace('-', 'm')}_{int(a_s)}"
        g = P.g
        sl, m = g.circle_mask(p, 2.0)
        if (g.raw_obst[sl][m] < 0).mean() > 0.3:
            continue
        d = P.add_plaza(name, D, "stair_link", circle_poly(p, 2.0), "cobble", circle=(p, 2.0),
                        extra={"stair": st["edge"], "r_station": a_s, "side_low": st["side_low"]})
        out.append(d)
    return out


def build_link_alleys(P, links):
    made = []
    for lk in links:
        D = lk["district"]
        phi = DISTRICT_AXIS[D]
        r = rng_for("link", lk["name"])
        c = lk["circle"]["c"]
        u, v = to_local(*c, phi)
        rad = (c[0] / hypot(*c), c[1] / hypot(*c))
        tg = _dir_world(0.0, -1.0 if v > 0 else 1.0, phi)
        dirs = [tg, (-rad[0], -rad[1]), rad]
        for a in (35.0, -35.0, 55.0, -55.0):         # diagonales hacia el anillo mas cercano
            ca, sa = cos(radians(a)), sin(radians(a))
            dirs.append((tg[0] * ca - tg[1] * sa, tg[0] * sa + tg[1] * ca))
        w = r.uniform(*ALLEY_W)
        best = None
        for d in dirs:
            pts = march_alley(P, c, d, w, lk["fid"], r, max_len=70.0, bends=False, free_start=5.0)
            if pts and (best is None or polyline_len(pts) < polyline_len(best)):
                best = pts
        if best:
            made.append(P.add_road(f"STR_{DISTRICT_KEY[D]}_CallejonEscalera_{len(made) + 1:02d}", D, "alley",
                                   best, w / 2, 3, over=False, extra={"blind": False, "stair_link": lk["name"]}))
    return made


WALL_LANE_R, WALL_LANE_W = 186.0, 4.5     # callejon de ronda (deja libre el pomerium r 188-196 y las escaleras de la muralla)


def build_wall_lanes(P):
    """Callejon de ronda por cada lado de cada distrito: arco a r=187.5 desde la banda del eje hacia el
    borde lateral, hasta topar con obstaculos; se remata hacia la escalera lateral mas cercana."""
    out = []
    hw = WALL_LANE_W / 2
    for D, phi in DISTRICT_AXIS.items():
        key = DISTRICT_KEY[D]
        band = plaza(P, f"PLZ_{key}_AxisFrontage")
        for sgn, tag in ((1, "L"), (-1, "R")):
            r = rng_for("lane", D, tag)
            th = degrees(np.arcsin((T.HALF_BAND - 3.0) / WALL_LANE_R))
            pts = []
            while th <= C.CARDINAL_HALF_ANGLE:
                rr = WALL_LANE_R + 0.6 * wobble("lane" + D + tag, phi + sgn * th)
                p = to_world(rr * cos(radians(th)), sgn * rr * sin(radians(th)), phi)
                sl, m = P.g.circle_mask(p, hw + 0.3)
                if P.g.blocked[sl][m].any():
                    break
                lab = P.g.lab[sl][m]
                if ((lab > 0) & (lab != band["fid"])).any() and len(pts) > 6:
                    pts.append(p)                      # ya toca otra calle (callejon de escalera)
                    break
                pts.append(p)
                th += 0.4
            if len(pts) < 8:
                continue
            d = (pts[-1][0] - pts[-2][0], pts[-1][1] - pts[-2][1])
            Ld = hypot(*d)
            tail = march_alley(P, pts[-1], (d[0] / Ld, d[1] / Ld), WALL_LANE_W, -999, r, max_len=25.0, bends=False)
            blind = tail is None
            if tail:
                pts += tail[1:]
            out.append(P.add_road(f"STR_{key}_CallejonRonda_{tag}", D, "alley", pts, hw, 4, over=False,
                                  extra={"blind": blind, "lane": True}))
    return out


def plan(obstacle_codes, obst_cell, stairs=()):
    P = Planner(obstacle_codes, obst_cell)
    P.add_plaza("PLZ_Portal", "Plaza", "portal_plaza", circle_poly((0.0, 0.0), C.PLAZA_RADIUS),
                "existing", circle=((0.0, 0.0), C.PLAZA_RADIUS))
    build_streets(P)
    # escalinatas entre barrios: callejones desde las escaleras laterales (antes que las parcelas)
    lanes = build_wall_lanes(P)
    build_mercado(P)
    build_oficios(P)
    build_clases(P)
    build_razas(P)
    links = stair_links(P, stairs)
    link_alleys = build_link_alleys(P, links) + lanes
    for ln in lanes:
        connect_lane_to_link(P, ln, links)
    alleys = {}
    for D in ("Mercado", "Oficios", "Clases", "Razas"):
        alleys[D] = build_alleys(P, D) + [a for a in link_alleys if a["district"] == D]
    for ln in lanes:
        trim_to_last_junction(P, ln)
    for D in alleys:                                   # callejones de barrio (Razas) tambien cuentan
        alleys[D] += [a for a in P.roads if a["district"] == D and a.get("barrio") and a not in alleys[D]]
    total = sum(len(a) for a in alleys.values())
    target = int(round(ALLEY_BLIND_FRAC * total))
    natural = {D: sum(1 for a in al if not end_connected(P, a)) for D, al in alleys.items()}
    extra = max(0, target - sum(natural.values()))
    quotas = dict(natural)
    order = sorted(alleys, key=lambda D: -len(alleys[D]))
    k = 0
    while extra > 0 and k < 100:
        D = order[k % len(order)]
        quotas[D] += 1
        extra -= 1
        k += 1
    blind = {D: make_blind(P, a, D, quotas[D]) for D, a in alleys.items()}
    for b in P.report.get("razas_barrios", []):
        if b and b.get("placed"):
            reg = b["region"]
            have = sum(1 for p in P.parcels if p["type"] == "house" and point_in_poly(*p["center"], reg))
            if have < b["target"]:
                fr = [(rd, sd) for rd in P.roads if rd["district"] == "Razas" for sd in (1, -1)]
                fr += [(band_front(DISTRICT_AXIS["Razas"], sg), sg) for sg in (1, -1)]
                fr += [(perimeter_front(pz["poly"]), -1) for pz in P.plazas if pz.get("barrio") == b["barrio"]]
                b["houses_topup"] = fill_houses(P, "Razas", fr, b["target"] - have, rng_for("topup", b["barrio"]),
                                                reg, prefix=f"MARKER_Bld_RAZ_B{b['barrio']:02d}_CasaB")
    houses = {}
    for D in ("Mercado", "Oficios", "Clases", "Razas"):
        r = rng_for("houses", D)
        fronts = [(rd, s) for rd in P.roads if rd["district"] == D for s in (1, -1)]
        fronts += [(perimeter_front(pz["poly"]), -1) for pz in P.plazas if pz["district"] == D
                   and pz["type"] in ("fountain_square", "market_square", "training_square")]
        houses[D] = fill_houses(P, D, fronts, None, r)
    for b in P.report.get("razas_barrios", []):
        if b and b.get("placed"):
            reg = b.pop("region")
            b["houses_in_block"] = sum(1 for p in P.parcels if p["type"] == "house" and p["district"] == "Razas"
                                       and point_in_poly(p["center"][0], p["center"][1], reg))
    awnings = add_mercado_awnings(P)
    patches = add_patches(P)
    ruts = add_ruts(P)
    lay = {"roads": P.roads, "plazas": P.plazas, "parcels": P.parcels, "zones": P.zones, "markers": P.markers,
           "patches": patches, "ruts": ruts}
    rep = P.report
    rep["alleys"] = {D: {"count": len(a) + 0, "blind": blind[D]} for D, a in alleys.items()}
    alley_all = [x for x in P.roads if x["type"] == "alley"]
    rep["alleys_total"] = {"count": len(alley_all), "blind": sum(1 for x in alley_all if x.get("blind")),
                           "width_m": [round(min(x["width"] for x in alley_all), 2),
                                       round(max(x["width"] for x in alley_all), 2)] if alley_all else None}
    rep["stair_links"] = {"count": len(links), "connected": len(link_alleys)}
    rep["decor_houses_frontage"] = houses
    rep["awnings"] = awnings
    rep["parcels_by_district"] = {}
    for p in P.parcels:
        dd = rep["parcels_by_district"].setdefault(p["district"], {"total": 0, "interior": 0, "decor": 0})
        dd["total"] += 1
        dd["interior" if p["interior"] else "decor"] += 1
    dzs = [abs(p["door_dz_to_front"]) for p in P.parcels if p["door_dz_to_front"] is not None]
    rep["door_dz_max"] = round(max(dzs), 3) if dzs else None
    rep["no_front"] = [p["name"] for p in P.parcels if p["front"] is None]
    return lay, rep, P
