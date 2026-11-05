"""
CONCORDIA - etapa 06: Moradas (viviendas de jugadores) en los 4 sectores diagonales. v05 -> v06.

Trazado por terraza (las 6 terrazas de la etapa 02: 14 m, salto de 1.0 m, r 105..189):
  [pretil 0.6 m del borde] -> calle de servicio (franja delantera) -> fila de parcelas 6 x 10 m
  apoyadas contra el muro de la terraza siguiente. Puerta (+Y del marcador) hacia la calle = hacia la
  ciudad (ref. Toledo / Cesky Krumlov: casas apretadas mirando a la ladera).
- Escaleras de 2.5 m cada 25 m (a +-25, +-50 m de arco del eje) en cada salto: la fila de parcelas de la
  terraza baja deja un pasaje de 2.5 + 2 x 0.3 m hasta la escalera (ref. Mont-Saint-Michel / Mala Strana).
- Calle de 6 m por el eje (desde la escalinata r=95..105 hasta r=189) con escalera de 6 m en cada salto.
- Pretiles de terraza rehechos con huecos en cada escalera.
- Tipos: habitacion / casa_pequena / casa_grande al 50 / 35 / 15 % (semilla por Morada).
  Jardin (garden_mask) en el fondo de las parcelas de casa_grande (6 x 3 m).
- Comprobacion de oclusion con CAM_Iso: volumenes provisionales de casa por tipo; si alguna puerta queda
  tapada por los tejados de otra fila, la casa se retrasa FRONT_SETBACK_EXTRA m dentro de su parcela
  (separacion entre filas +2 m) y se vuelve a medir.
"""

import os
import random
import sys
from math import asin, atan2, ceil, cos, degrees, hypot, pi, radians, sin, sqrt, tan

import bmesh
import bpy
import numpy as np
from mathutils import Matrix, Vector, noise
from mathutils.bvhtree import BVHTree

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import concordia_const as C  # noqa: E402
import stage02_structures as ST2  # noqa: E402
import stage02_terrain as S2  # noqa: E402
import stage05_streets as S5  # noqa: E402
import terrain_profile as T  # noqa: E402

# --- cifras del pedido ------------------------------------------------------
PARCEL_W, PARCEL_D = 6.0, 10.0
LANE_W_TARGET = 4.0
TYPES = (("habitacion", 0.50), ("casa_pequena", 0.35), ("casa_grande", 0.15))
SERVICE_STAIR_W = 2.5
SERVICE_STAIR_SPACING = 25.0
AXIS_STREET_W = 6.0
# --- parametros (no fijados en el pedido) -----------------------------------
SEED = 606
STAIR_RISERS = 7                  # 1.0 m / 7 = 0.143
STAIR_TREAD = 0.30                # 2R + H = 0.59
PASSAGE_MARGIN = 0.3              # holgura escalera <-> parcelas
LATERAL_MARGIN = 0.8              # parcelas a >= 0.8 m del borde lateral del sector
GARDEN_D = 3.0                    # jardin de casa_grande (fondo de la parcela)
PARAPET_GAP_MARGIN = 0.2
FRONT_SETBACK_EXTRA = 2.0         # remedio del pedido si los tejados tapan puertas
PARCEL_GAP = 0.02                 # junta minima entre parcelas contiguas (casas adosadas)
# volumenes provisionales para la comprobacion (no hay kit aun): alero / cumbrera sobre la plataforma
PROXY = {"habitacion": (3.2, 5.2), "casa_pequena": (4.5, 6.8), "casa_grande": (6.0, 8.6)}
DOOR_H = (0.3, 1.1, 2.0)          # puntos de muestreo en la puerta
COBBLE_GARDEN = 6
KEYS = {"Morada_NE": "NE", "Morada_NW": "NO", "Morada_SW": "SO", "Morada_SE": "SE"}
# lado de la puerta: "in" = calle delante (junto al pretil), puerta hacia la ciudad; "out" = calle detras
# (al pie del muro de la terraza superior), puerta hacia la muralla. La Morada SE se invierte para que sus
# puertas miren a CAM_Iso (con "in" las 72 daban la espalda a la camara).
FACING = {"Morada_NE": "in", "Morada_NW": "in", "Morada_SW": "in", "Morada_SE": "out"}
# escalinatas de la rampa hitos -> terraza 1 (etapa 07): arco en m a r = 100 desde el eje de cada Morada.
# En las Moradas "out" la fila de la terraza 1 deja hueco en esas posiciones.
ESC_ARCS = {"Morada_NE": (25.0, -25.0), "Morada_NW": (25.0, -25.0, 12.0), "Morada_SW": (25.0, -25.0),
            "Morada_SE": (25.0, -25.0, -12.0)}
ESC_GAP_HALF = 3.0 / 2 + 0.45 + 0.6


# ---------------------------------------------------------------------------
def to_world(u, v, phi):
    a = radians(phi)
    return (u * cos(a) - v * sin(a), u * sin(a) + v * cos(a))


def to_local(x, y, phi):
    a = radians(phi)
    return (x * cos(a) + y * sin(a), -x * sin(a) + y * cos(a))


def terrace_bands():
    """[(k, r_front, r_back, z)]: franja util de cada terraza (tras el pretil, hasta el pie del salto)."""
    J = T.terrace_jumps()
    out = []
    for k in range(1, C.TERRACE_COUNT + 1):
        rf = C.TERRACE_START_R if k == 1 else J[k - 2] + T.STEP_RUN / 2 + C.PARAPET_THICK
        rb = J[k - 1] - T.STEP_RUN / 2 if k < C.TERRACE_COUNT else C.TERRACE_END_R - T.STEP_RUN / 2
        out.append((k, rf, rb, T.terrace_level(k)))
    return out


def rect_at(phi_dir, rp, w, d):
    """Parcela con la fachada (lado delantero, hacia el centro) en el radio rp sobre la direccion phi_dir."""
    a = radians(phi_dir)
    e = (cos(a), sin(a))
    t = (-sin(a), cos(a))
    pts = []
    for s_t, s_r in ((-1, 0), (1, 0), (1, 1), (-1, 1)):
        r = rp + s_r * d
        pts.append((e[0] * r + t[0] * s_t * w / 2, e[1] * r + t[1] * s_t * w / 2))
    return pts


def poly_local_v(poly, phi):
    return [to_local(x, y, phi)[1] for x, y in poly]


def struct_hit(codes, poly, grow=0.3):
    """True si el poligono (crecido 'grow') pisa celdas de estructura del raster (0.5 m)."""
    import stage05_obstacles as OB
    n = codes.shape[0]
    xs = [p[0] for p in poly]
    ys = [p[1] for p in poly]
    i0 = max(0, int((min(xs) - grow + OB.EXTENT) / OB.CELL))
    i1 = min(n - 1, int((max(xs) + grow + OB.EXTENT) / OB.CELL))
    j0 = max(0, int((min(ys) - grow + OB.EXTENT) / OB.CELL))
    j1 = min(n - 1, int((max(ys) + grow + OB.EXTENT) / OB.CELL))
    import stage05_layout as L
    for j in range(j0, j1 + 1):
        y = -OB.EXTENT + OB.CELL * (j + 0.5)
        for i in range(i0, i1 + 1):
            if codes[j, i] != 1:
                continue
            x = -OB.EXTENT + OB.CELL * (i + 0.5)
            if L.point_in_poly(x, y, poly) or L.poly_edge_dist(x, y, poly) <= grow:
                return True
    return False


# ---------------------------------------------------------------------------
# Trazado
# ---------------------------------------------------------------------------
def stair_slots(R, phi):
    """Escaleras de servicio sobre el salto de radio R: arcos +-25, +-50 ... dentro del sector."""
    out = []
    half_arc = R * radians(C.MORADA_HALF_ANGLE) - LATERAL_MARGIN - SERVICE_STAIR_W / 2 - 1.0
    k = 1
    while k * SERVICE_STAIR_SPACING <= half_arc:
        for sg in (1, -1):
            out.append(phi + sg * degrees(k * SERVICE_STAIR_SPACING / R))
        k += 1
    return sorted(out)


def layout_morada(key, phi, codes):
    bands = terrace_bands()
    J = T.terrace_jumps()
    parcels, stairs, lanes, passages = [], [], [], []
    facing = FACING[key]
    slots_of = {j: stair_slots(J[j - 1], phi) for j in range(1, C.TERRACE_COUNT)}
    for k, rf, rb, z in bands:
        lane_w = rb - rf - PARCEL_D
        if facing == "in":
            rp = rf + lane_w                       # borde interior de la fila de parcelas
            lane = (rf, rp)
            pas_slots, pas_r = slots_of.get(k, []), (rp, rb)
        else:
            rp = rf + (0.12 if k > 1 else 0.0)     # separada del pretil
            lane = (rp + PARCEL_D, rb)
            lane_w = rb - lane[0]
            pas_slots, pas_r = slots_of.get(k - 1, []), (rf, rp + PARCEL_D)
        lanes.append({"name": f"STR_{KEYS[key]}_T{k}_Servicio", "terrace": k, "r0": lane[0], "r1": lane[1], "z": z,
                      "width_m": round(lane_w, 2), "facing": facing})
        if k < C.TERRACE_COUNT:
            R = J[k - 1]
            for a in slots_of[k]:
                stairs.append({"key": key, "jump": k, "R": R, "angle": a, "width": SERVICE_STAIR_W, "type": "servicio"})
            stairs.append({"key": key, "jump": k, "R": R, "angle": phi, "width": AXIS_STREET_W, "type": "eje"})
        # prohibidos (en angulo): eje y pasajes entre casas hasta / desde las escaleras
        forbid = []
        for a in pas_slots:
            half = degrees((SERVICE_STAIR_W / 2 + PASSAGE_MARGIN) / rp)
            forbid.append((a - half, a + half))
            passages.append({"terrace": k, "angle": a, "r0": pas_r[0], "r1": pas_r[1], "z": z,
                             "width": SERVICE_STAIR_W + 2 * PASSAGE_MARGIN})
        ax = degrees((AXIS_STREET_W / 2 + PASSAGE_MARGIN) / rp)
        forbid.append((phi - ax, phi + ax))
        if k == 1 and facing == "out":
            for arc in ESC_ARCS[key]:
                a_e = phi + degrees(arc / 100.0)
                h = degrees(ESC_GAP_HALF / rp)
                forbid.append((a_e - h, a_e + h))
                passages.append({"terrace": 1, "angle": a_e, "r0": rf, "r1": rp + PARCEL_D, "z": z,
                                 "width": 2 * ESC_GAP_HALF, "kind": "escalinata"})
        dth = degrees(2 * asin((PARCEL_W / 2) / rp)) + degrees(PARCEL_GAP / rp)
        row = []
        for sg in (1, -1):
            a = phi + sg * (ax + dth / 2)
            while abs(a - phi) <= C.MORADA_HALF_ANGLE:
                lo, hi = a - dth / 2, a + dth / 2
                clash = [f for f in forbid if not (hi <= f[0] or lo >= f[1])]
                if clash:
                    f = clash[0]
                    a = (f[1] + dth / 2) if sg > 0 else (f[0] - dth / 2)
                    continue
                poly = rect_at(a, rp, PARCEL_W, PARCEL_D)
                ok = True
                for x, y in poly:
                    r = hypot(x, y)
                    if T.s_lateral(r, T.angle_deg(x, y)) < LATERAL_MARGIN or abs(
                            ((T.angle_deg(x, y) - phi + 180) % 360) - 180) > C.MORADA_HALF_ANGLE:
                        ok = False
                        break
                if not ok:
                    break
                if struct_hit(codes, poly, 0.05):
                    a += sg * degrees(0.5 / rp)
                    continue
                row.append((a, poly))
                a += sg * dth
        row.sort(key=lambda t: t[0])
        for a, poly in row:
            parcels.append({"terrace": k, "angle": a, "rp": rp, "z": z, "poly": poly, "lane_w": lane_w,
                            "facing": facing})
    # tipos 50 / 35 / 15
    n = len(parcels)
    counts = [int(round(n * f)) for _t, f in TYPES]
    counts[0] = n - counts[1] - counts[2]
    bag = [t for (t, _f), c in zip(TYPES, counts) for _ in range(c)]
    random.Random(f"{SEED}-{key}").shuffle(bag)
    for i, p in enumerate(parcels):
        p["tipo"] = bag[i]
        p["name"] = f"MARKER_Morada_{KEYS[key]}_{i + 1:03d}"
        p["garden"] = p["tipo"] == "casa_grande"
    axis = {"name": f"STR_{KEYS[key]}_Eje", "r0": C.TERRACE_START_R, "r1": C.TERRACE_END_R, "width": AXIS_STREET_W}
    return {"key": key, "phi": phi, "parcels": parcels, "stairs": stairs, "lanes": lanes, "passages": passages,
            "axis": axis, "counts": dict(zip([t for t, _f in TYPES], counts))}


# ---------------------------------------------------------------------------
# Terreno
# ---------------------------------------------------------------------------
def arc_pts(r, a0, a1, step=0.5):
    n = max(2, int(ceil(radians(abs(a1 - a0)) * r / step)) + 1)
    return [(r * cos(radians(a0 + (a1 - a0) * i / (n - 1))), r * sin(radians(a0 + (a1 - a0) * i / (n - 1))))
            for i in range(n)]


def knife_lines(lays):
    lines = []
    for lay in lays:
        phi = lay["phi"]
        h = C.MORADA_HALF_ANGLE
        for ln in lay["lanes"]:
            rr = ln["r1"] if ln["facing"] == "in" else ln["r0"]
            lines.append(arc_pts(rr, phi - h, phi + h))                  # borde calle / fachadas
        for p in lay["parcels"]:
            lines.append(list(p["poly"]) + [p["poly"][0]])
            if p["garden"]:
                a = radians(p["angle"])
                e, t = (cos(a), sin(a)), (-sin(a), cos(a))
                r = p["rp"] + (PARCEL_D - GARDEN_D if p["facing"] == "in" else GARDEN_D)
                lines.append([(e[0] * r + t[0] * s, e[1] * r + t[1] * s) for s in (-PARCEL_W / 2, PARCEL_W / 2)])
        for v in (-AXIS_STREET_W / 2, AXIS_STREET_W / 2):
            lines.append([to_world(u, v, phi) for u in np.arange(C.TERRACE_START_R, C.TERRACE_END_R + 0.01, 0.5)])
        for ps in lay["passages"]:
            a = radians(ps["angle"])
            e, t = (cos(a), sin(a)), (-sin(a), cos(a))
            for s in (-ps["width"] / 2, ps["width"] / 2):
                lines.append([(e[0] * r + t[0] * s, e[1] * r + t[1] * s) for r in (ps["r0"], ps["r1"])])
    return lines


class Classifier:
    """Elemento de las Moradas que contiene (x, y): parcel / garden / lane / axis / passage / None."""

    def __init__(self, lays):
        self.lays = {l["key"]: l for l in lays}
        self.by_terrace = {}
        for l in lays:
            for p in l["parcels"]:
                self.by_terrace.setdefault((l["key"], p["terrace"]), []).append(p)

    def classify(self, x, y):
        r = hypot(x, y)
        if r < C.TERRACE_START_R - 1e-3 or r > C.TERRACE_END_R + 1e-3:
            return None, None, 0
        th = T.angle_deg(x, y)
        if T.s_lateral(r, th) <= 0.0:
            return None, None, 0
        key = T.nearest_diagonal(th)
        lay = self.lays[key]
        k = T.terrace_index(r) or (C.TERRACE_COUNT if r >= C.TERRACE_END_R - 1e-3 else 0)
        if not k:
            return None, None, 0
        band = terrace_bands()[k - 1]
        if not (band[1] - 0.45 <= r <= band[2] + 1e-3):
            return "terrace", None, k                   # cara del salto: no se toca
        u, v = to_local(x, y, lay["phi"])
        if abs(v) <= AXIS_STREET_W / 2 + 1e-3:
            return "axis", lay["axis"], k
        for p in self.by_terrace.get((key, k), ()):
            a = radians(p["angle"])
            pr = x * cos(a) + y * sin(a)
            pt = -x * sin(a) + y * cos(a)
            if abs(pt) <= PARCEL_W / 2 + 1e-3 and p["rp"] - 1e-3 <= pr <= p["rp"] + PARCEL_D + 1e-3:
                if p["garden"] and ((p["facing"] == "in" and pr >= p["rp"] + PARCEL_D - GARDEN_D - 1e-3)
                                    or (p["facing"] == "out" and pr <= p["rp"] + GARDEN_D + 1e-3)):
                    return "garden", p, k
                return "parcel", p, k
        for ps in lay["passages"]:
            if ps["terrace"] != k:
                continue
            a = radians(ps["angle"])
            pr = x * cos(a) + y * sin(a)
            pt = -x * sin(a) + y * cos(a)
            if abs(pt) <= ps["width"] / 2 + 1e-3 and ps["r0"] - 1e-3 <= pr <= ps["r1"] + 1e-3:
                return "passage", ps, k
        ln = lay["lanes"][k - 1]
        r_lo = ln["r0"] - (0.45 if ln["facing"] == "in" else 0.0)
        if r_lo - 1e-3 <= r <= ln["r1"] + 1e-3:
            return "lane", ln, k
        return "terrace", None, k


def apply_terrain(obj, lays, stats):
    me = obj.data
    bm = bmesh.new()
    bm.from_mesh(me)
    idx = S5.EdgeIndex(bm, r_min=100.0, r_max=192.0)
    locked = set()
    lines = knife_lines(lays)
    for pts in lines:
        S5.knife(bm, idx, pts, locked)
    bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 3], quad_method="BEAUTY",
                          ngon_method="BEAUTY")
    cl = Classifier(lays)
    moved = 0
    for v in bm.verts:
        kind, d, k = cl.classify(v.co.x, v.co.y)
        if kind in (None, "terrace"):
            continue
        z = T.terrace_level(k)
        if kind in ("lane", "axis", "passage"):
            z += 0.008 * noise.noise(Vector((v.co.x / 3.0, v.co.y / 3.0, 4.2)), noise_basis="PERLIN_NEW")
        v.co.z = z
        moved += 1
    bm.normal_update()
    bm.to_mesh(me)
    bm.free()
    me.update()
    me.set_sharp_from_angle(angle=radians(S2.SHARP_ANGLE))
    stats["moradas_terrain"] = {"knife_lines": len(lines), "verts_moved": moved, "tris_after": len(me.polygons)}
    return cl


def write_masks(obj, cl, stats):
    me = obj.data
    nl = len(me.loops)
    loop_f = [0] * nl
    for p in me.polygons:
        for li in range(p.loop_start, p.loop_start + p.loop_total):
            loop_f[li] = p.index
    fk = []
    for p in me.polygons:
        c = p.center
        kind, d, k = cl.classify(c.x, c.y)
        r = hypot(c.x, c.y)
        th = T.angle_deg(c.x, c.y)
        if k == 0 and T.s_lateral(r, th) > 0 and C.TERRACE_START_R <= r <= C.WALL_BASE_R[0]:
            k = T.terrace_index(r) or (C.TERRACE_COUNT if r >= C.TERRACE_END_R else 0)
        fk.append((kind, k, S2.slope_deg(p.normal.z)))

    def get(name):
        a = me.color_attributes[name]
        vals = [0.0] * (nl * 4)
        a.data.foreach_get("color", vals)
        return a, vals

    def put_new(name, per_face):
        if name in me.color_attributes:
            me.color_attributes.remove(me.color_attributes[name])
        a = me.color_attributes.new(name=name, type="BYTE_COLOR", domain="CORNER")
        flat = []
        for li in range(nl):
            v = per_face[loop_f[li]]
            flat.extend((v, v, v, 1.0))
        a.data.foreach_set("color", flat)

    vg = obj.vertex_groups.get("terraza_id")
    if vg is not None:                    # el nombre pasa al color de vertice pedido
        vg.name = "terraza_id_w"
    tid = [(k / float(C.TERRACE_COUNT)) if k else 0.0 for _kind, k, _s in fk]
    put_new("terraza_id", tid)
    put_new("garden_mask", [1.0 if kind == "garden" else 0.0 for kind, _k, _s in fk])
    # retaining_mask de nuevo en las Moradas (caras >= 70 grados), road_mask / cobble_type / wear / UVRoads
    ra, rv = get("retaining_mask")
    rm, rmv = get("road_mask")
    ct, ctv = get("cobble_type")
    wr, wrv = get("wear_mask")
    uv = me.uv_layers["UVRoads"]
    uvv = [0.0] * (nl * 2)
    uv.data.foreach_get("uv", uvv)
    n_ret = 0
    for li in range(nl):
        kind, k, s = fk[loop_f[li]]
        if not k:
            continue
        if s >= S2.RETAIN_MIN_SLOPE:
            rv[li * 4:li * 4 + 3] = [1.0, 1.0, 1.0]
            n_ret += 1
        if kind in ("lane", "axis", "passage"):
            w = 0.55 if kind == "axis" else 0.3
            rmv[li * 4:li * 4 + 3] = [1.0] * 3
            ctv[li * 4:li * 4 + 3] = [1 / 8.0] * 3
            wrv[li * 4:li * 4 + 3] = [w] * 3
            uvv[li * 2:li * 2 + 2] = [1.0, 1 + 0.99 * w]
        elif kind in ("parcel", "garden"):
            t = 5 if kind == "parcel" else COBBLE_GARDEN
            rmv[li * 4:li * 4 + 3] = [0.0] * 3
            ctv[li * 4:li * 4 + 3] = [t / 8.0] * 3
            wrv[li * 4:li * 4 + 3] = [0.0] * 3
            uvv[li * 2:li * 2 + 2] = [0.0, float(t)]
    ra.data.foreach_set("color", rv)
    rm.data.foreach_set("color", rmv)
    ct.data.foreach_set("color", ctv)
    wr.data.foreach_set("color", wrv)
    uv.data.foreach_set("uv", uvv)
    stats["moradas_masks"] = {
        "terraza_id": "valor = id / 6 (1..6; 0 = fuera de las terrazas), por cara",
        "garden_mask": "1 en el jardin de las parcelas casa_grande (fondo 6 x 3 m)",
        "cobble_type_6": "jardin (nuevo en la etapa 06)",
        "retaining_loops_morada": n_ret,
        "faces_by_kind": {kk: sum(1 for f in fk if f[0] == kk) for kk in ("lane", "axis", "passage", "parcel", "garden")},
    }


# ---------------------------------------------------------------------------
# Estructuras: escaleras de terraza y pretiles con huecos
# ---------------------------------------------------------------------------
def build_stairs(lays, stats):
    mat = ST2.stone_material()
    col = bpy.data.collections["MORADAS"]
    out = {}
    riser = C.TERRACE_RISE / STAIR_RISERS
    for lay in lays:
        key = lay["key"]
        name = f"TRN_TerraceStairs_{key}"
        if name in bpy.data.objects:
            bpy.data.objects.remove(bpy.data.objects[name])
        mb = ST2.MeshBuilder()
        for st in lay["stairs"]:
            a = radians(st["angle"])
            e = (cos(a), sin(a), 0.0)
            t = (-sin(a), cos(a), 0.0)
            R = st["R"]
            foot = R - T.STEP_RUN / 2
            z0 = T.terrace_level(st["jump"])
            zf = z0 - ST2.EMBED
            hw = st["width"] / 2
            for kk in range(1, STAIR_RISERS):
                zk = z0 + kk * riser
                p0 = foot - (STAIR_RISERS - kk) * STAIR_TREAD
                p1 = foot + (T.STEP_RUN if kk == STAIR_RISERS - 1 else 0.002)
                mb.prism([(p0, zf), (p1, zf), (p1, zk), (p0, zk)], (0, 0, 0), e, t, -hw, hw)
        obj = mb.to_object(name, col, mat)
        out[key] = {"object": name, "stairs": len(lay["stairs"]), "tris": len(obj.data.polygons) if obj else 0}
    stats["moradas_stairs"] = {"per_morada": out, "risers": STAIR_RISERS, "riser_m": round(riser, 3),
                               "tread_m": STAIR_TREAD, "run_m": round((STAIR_RISERS - 1) * STAIR_TREAD, 2),
                               "service_width_m": SERVICE_STAIR_W, "axis_width_m": AXIS_STREET_W,
                               "spacing_m": SERVICE_STAIR_SPACING}


def rebuild_parapets(lays, stats):
    """TRN_Parapets_<Morada>: pretiles laterales (como en la etapa 02) + pretiles de terraza con huecos
    en el eje (6 m) y en cada escalera de servicio."""
    mat = ST2.stone_material()
    col = bpy.data.collections["MORADAS"]
    edges = T.lateral_edges()
    rep = {}
    for lay in lays:
        key, phi = lay["key"], lay["phi"]
        name = f"TRN_Parapets_{key}"
        if name in bpy.data.objects:
            bpy.data.objects.remove(bpy.data.objects[name])
        mb = ST2.MeshBuilder()
        for k2, side, tb, e, n_card in edges:
            if k2 != key:
                continue
            gaps, _fps = ST2.build_lateral_stairs(ST2.MeshBuilder(), key, side, tb, e, n_card, [])
            ST2.build_lateral_parapets(mb, tb, e, n_card, gaps, [])
        rep[key] = []
        for j, R in enumerate(T.terrace_jumps(), start=1):
            r0 = R + T.STEP_RUN / 2
            r1 = r0 + C.PARAPET_THICK
            z = T.terrace_level(j + 1)
            holes = []
            for st in lay["stairs"]:
                if st["jump"] != j:
                    continue
                half = degrees((st["width"] / 2 + PARAPET_GAP_MARGIN) / r0)
                holes.append((st["angle"] - half, st["angle"] + half))
            holes.sort()
            spans, a = [], phi - C.MORADA_HALF_ANGLE
            for h0, h1 in holes:
                if h0 > a:
                    spans.append((a, h0))
                a = max(a, h1)
            spans.append((a, phi + C.MORADA_HALF_ANGLE))
            for a0, a1 in spans:
                if a1 - a0 <= 0.05:
                    continue
                n = max(1, ceil(radians(a1 - a0) * r0 / ST2.PARAPET_CHORD))
                rings = []
                for i in range(n + 1):
                    th = radians(a0 + (a1 - a0) * i / n)
                    c, s = cos(th), sin(th)
                    rings.append([(r0 * c, r0 * s, z - ST2.EMBED), (r1 * c, r1 * s, z - ST2.EMBED),
                                  (r1 * c, r1 * s, z + C.PARAPET_LOW_H), (r0 * c, r0 * s, z + C.PARAPET_LOW_H)])
                mb.strip(rings)
            rep[key].append({"r": round(r0, 3), "holes": len(holes)})
        obj = mb.to_object(name, col, mat)
        rep[key].append({"tris": len(obj.data.polygons)})
    stats["moradas_parapets"] = rep


# ---------------------------------------------------------------------------
# Marcadores
# ---------------------------------------------------------------------------
def make_markers(lays, setback, stats):
    root = bpy.data.collections["MORADAS"]
    out = {}
    for lay in lays:
        cname = f"MARKERS_Morada_{KEYS[lay['key']]}"
        col = bpy.data.collections.get(cname)
        if col is None:
            col = bpy.data.collections.new(cname)
            root.children.link(col)
        for o in list(col.objects):
            bpy.data.objects.remove(o)
        for p in lay["parcels"]:
            a = radians(p["angle"])
            rc = p["rp"] + PARCEL_D / 2
            e = bpy.data.objects.new(p["name"], None)
            e.empty_display_type = "ARROWS"
            e.empty_display_size = 2.0
            e.location = (cos(a) * rc, sin(a) * rc, p["z"])
            # +Y local -> puerta: hacia el centro ("in") o hacia la muralla ("out")
            e.rotation_euler = (0.0, 0.0, a + pi / 2 if p["facing"] == "in" else a - pi / 2)
            props = {"tipo": p["tipo"], "footprint": f"{PARCEL_W:g}x{PARCEL_D:g}", "footprint_w": PARCEL_W,
                     "footprint_d": PARCEL_D, "door_direction": "+Y", "interior": True, "terraza": p["terrace"],
                     "conjunto": lay["key"], "garden": bool(p["garden"]), "pad_z": round(p["z"], 3),
                     "front_street": f"STR_{KEYS[lay['key']]}_T{p['terrace']}_Servicio",
                     "door_side": "ciudad (hacia el centro)" if p["facing"] == "in" else "muralla (hacia fuera)",
                     "building_front_setback_m": float(setback),
                     "building_depth_m": float(PARCEL_D - setback - (GARDEN_D if p["garden"] else 0.0))}
            if p["garden"]:
                props["garden_m"] = f"{PARCEL_W:g}x{GARDEN_D:g} (fondo)"
            for kk, vv in props.items():
                e[kk] = vv
            col.objects.link(e)
        out[lay["key"]] = {"markers": len(lay["parcels"]), "collection": cname, "tipos": lay["counts"]}
    stats["moradas_markers"] = out


# ---------------------------------------------------------------------------
# Comprobacion de oclusion de puertas con CAM_Iso
# ---------------------------------------------------------------------------
def proxy_mesh(lays, setback):
    """Volumenes provisionales: caja + tejado a dos aguas (cumbrera paralela a la fachada)."""
    verts, faces, owner = [], [], []
    for li, lay in enumerate(lays):
        for pi_, p in enumerate(lay["parcels"]):
            eave, ridge = PROXY[p["tipo"]]
            a = radians(p["angle"])
            e = Vector((cos(a), sin(a), 0))
            t = Vector((-sin(a), cos(a), 0))
            g = GARDEN_D if p["garden"] else 0.0
            if p["facing"] == "in":
                r0, r1 = p["rp"] + setback, p["rp"] + PARCEL_D - g
            else:
                r0, r1 = p["rp"] + g, p["rp"] + PARCEL_D - setback
            rm = (r0 + r1) / 2
            z = p["z"]
            hw = PARCEL_W / 2 - 0.01
            P = [e * r0 - t * hw, e * r0 + t * hw, e * r1 + t * hw, e * r1 - t * hw]
            b = len(verts)
            for q in P:
                verts.append((q.x, q.y, z))
            for q in P:
                verts.append((q.x, q.y, z + eave))
            verts.append(tuple(e * rm - t * hw + Vector((0, 0, z + ridge))))
            verts.append(tuple(e * rm + t * hw + Vector((0, 0, z + ridge))))
            fs = [(0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7), (4, 5, 9, 8), (6, 7, 8, 9),
                  (5, 6, 9), (7, 4, 8), (3, 2, 1, 0)]
            for f in fs:
                faces.append(tuple(b + i for i in f))
                owner.append((li, pi_))
    return verts, faces, owner


def occlusion_check(lays, setback, cam_dir):
    verts, faces, owner = proxy_mesh(lays, setback)
    bvh_h = BVHTree.FromPolygons(verts, faces)
    trn = bpy.data.objects["TRN_City"]
    dg = bpy.context.evaluated_depsgraph_get()
    bvh_t = BVHTree.FromObject(trn, dg)
    to_cam = -Vector(cam_dir).normalized()
    res = {}
    hidden_list = []
    for li, lay in enumerate(lays):
        tot = vis = back = hid = part = 0
        for pi_, p in enumerate(lay["parcels"]):
            a = radians(p["angle"])
            sgn = -1.0 if p["facing"] == "in" else 1.0
            nrm = Vector((sgn * cos(a), sgn * sin(a), 0))     # normal de la fachada de la puerta
            tot += 1
            if nrm.dot(Vector((to_cam.x, to_cam.y, 0))) <= 0.05:
                back += 1                                # la puerta mira al lado contrario de la camara
                continue
            r0 = p["rp"] + setback if p["facing"] == "in" else p["rp"] + PARCEL_D - setback
            base = Vector((cos(a) * r0, sin(a) * r0, p["z"])) + nrm * 0.15
            blocked = 0
            for h in DOOR_H:
                o = base + Vector((0, 0, h))
                hit = bvh_h.ray_cast(o + to_cam * 0.05, to_cam, 400.0)
                ht = bvh_t.ray_cast(o + to_cam * 0.05, to_cam, 400.0)
                if (hit[0] is not None and owner[hit[2]] != (li, pi_)) or ht[0] is not None:
                    blocked += 1
            if blocked >= 2:
                hid += 1
                hidden_list.append(p["name"])
            else:
                vis += 1
                part += int(blocked == 1)
        res[lay["key"]] = {"parcels": tot, "doors_facing_camera": tot - back, "doors_away_from_camera": back,
                           "visible": vis, "visible_but_partly_covered": part, "hidden_by_roofs": hid,
                           "facing": lay["parcels"][0]["facing"] if lay["parcels"] else None}
    return res, hidden_list


def build(scene, stats, codes):
    lays = [layout_morada(k, phi, codes) for k, phi in T.DIAGONAL_ANGLE.items()]
    stats["moradas_layout"] = {
        l["key"]: {"parcels": len(l["parcels"]), "tipos": l["counts"],
                   "per_terrace": {k: sum(1 for p in l["parcels"] if p["terrace"] == k) for k in range(1, 7)},
                   "stairs_service": sum(1 for s in l["stairs"] if s["type"] == "servicio"),
                   "stairs_axis": sum(1 for s in l["stairs"] if s["type"] == "eje"),
                   "lane_widths_m": [ln["width_m"] for ln in l["lanes"]]} for l in lays}
    obj = bpy.data.objects["TRN_City"]
    cl = apply_terrain(obj, lays, stats)
    write_masks(obj, cl, stats)
    build_stairs(lays, stats)
    rebuild_parapets(lays, stats)
    cam = bpy.data.objects[C.CAM_ISO_NAME]
    cam_dir = cam.matrix_world.to_3x3() @ Vector((0, 0, -1))
    occ0, hid0 = occlusion_check(lays, 0.0, cam_dir)
    setback = 0.0
    stats["moradas_occlusion"] = {"cam_dir": [round(c, 3) for c in cam_dir], "proxy_heights_m": PROXY,
                                  "setback_0": occ0}
    if any(v["hidden_by_roofs"] for v in occ0.values()):
        setback = FRONT_SETBACK_EXTRA
        occ1, hid1 = occlusion_check(lays, setback, cam_dir)
        stats["moradas_occlusion"]["setback_2m"] = occ1
        stats["moradas_occlusion"]["still_hidden_sample"] = hid1[:20]
        occ4, _h4 = occlusion_check(lays, 2 * FRONT_SETBACK_EXTRA, cam_dir)
        stats["moradas_occlusion"]["setback_4m_info_no_aplicado"] = occ4
    stats["moradas_occlusion"]["applied_front_setback_m"] = setback
    make_markers(lays, setback, stats)
    return lays, setback
