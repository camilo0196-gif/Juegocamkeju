"""
CONCORDIA - etapa 07: Cauce, puentes, arcos entre barrios y escalinatas. v06 -> v07.

Cauce (cauce_route.py): canal de 4 m x 1.2 m, orillas de piedra de 1 m, agua plana 0.4 m bajo el borde de
cada tramo (4 azudes de 0.3 m), escalones de acceso cada 20 m (contrahuella 0.15, huella 0.35), muelle 8x3
del Gremio de Pescadores, hueco de 3 m para la rueda de la Carpinteria y boca de alcantarilla con reja en la
cara interior de la muralla (345 grados).
Puentes: cada cruce del Cauce con una calle es un tramo de calle elevado 0.4 m (rampas <= 4.2 grados) con
pretiles de 0.9 m y bovedas de piedra; ancho 5-6 m. Arcos entre barrios (Razas): paso elevado sobre calles
de 4-6 m con 5 m de galibo libre y pretiles de 0.9 m.
Escalinatas: en la rampa de los hitos a las Moradas (r 95-105, 8.5-10 grados), contrahuella 0.15, huella 0.35.
Remiendos: el 20 % de los tramos de pretil (celdas de 2 m) con otra piedra (MAT_Stone_Repair).
"""

import json
import os
import random
import sys
from math import asin, atan2, ceil, cos, degrees, hypot, pi, radians, sin, sqrt, tan

import bmesh
import bpy
import numpy as np
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import cauce_route as CR  # noqa: E402
import concordia_const as C  # noqa: E402
import stage02_structures as ST2  # noqa: E402
import stage02_terrain as S2  # noqa: E402
import stage05_streets as S5  # noqa: E402
import terrain_profile as T  # noqa: E402

REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
SEED = 707
RISER, TREAD = 0.15, 0.35
BED_INSET = 0.15                     # pie del muro del canal (cara de 80 grados aprox.)
SHOULDER = 0.3
COPING_W, COPING_H = 0.5, 0.12
ACCESS_W = 1.2
BRIDGE_RISE = 0.4
BRIDGE_RAMP = 5.5                    # 0.4 / 5.5 = 4.2 grados
BRIDGE_DECK_T = 0.5
PARAPET_H, PARAPET_T = 0.9, 0.3
ARCH_CLEAR = 5.0
ARCH_DECK_T = 0.6
ARCH_DEPTH = 2.6                     # grosor del arco a lo largo de la calle
ARCH_PIER = 0.6
N_ARCHES = 7
N_ESC = 10
ESC_W = 3.0
REPAIR_FRAC = 0.20
COBBLE_CAUCE = 7
OPEN_R = 94.0
WATER_HEX = "#1A201F"                # oscuro y apagado (refleja el cielo solo por especular)
REPAIR_HEX = "#A39A88"


# ---------------------------------------------------------------------------
class Canal:
    def __init__(self):
        pts = CR.centerline(1.0)
        # tramo abierto desde el borde interior del anillo 100 del Mercado (r < 94): la vertiente llega
        # desde la Fuente por una mina enterrada bajo el anillo
        i0 = next(i for i, p in enumerate(pts) if hypot(*p) < OPEN_R)
        self.mine = pts[:i0 + 1]
        self.pts = pts[i0:]
        self.cum = CR.cumlen(self.pts)
        self.E, self.W = CR.edge_profile(self.pts)
        self.L = self.cum[-1]
        self.P0 = np.asarray(self.pts[:-1])
        self.D = np.asarray(self.pts[1:]) - self.P0
        self.L2 = (self.D * self.D).sum(1)

    def project(self, x, y):
        """(s, d, inside): s a lo largo del eje, d firmada (+ a la izquierda), inside = proyeccion no recortada."""
        q = np.array((x, y)) - self.P0
        traw = (q * self.D).sum(1) / self.L2
        t = np.clip(traw, 0.0, 1.0)
        d2 = ((q - self.D * t[:, None]) ** 2).sum(1)
        i = int(np.argmin(d2))
        cr = self.D[i, 0] * q[i, 1] - self.D[i, 1] * q[i, 0]
        d = sqrt(d2[i]) * (1 if cr >= 0 else -1)
        inside = not ((i == 0 and traw[i] < 0) or (i == len(self.L2) - 1 and traw[i] > 1))
        return self.cum[i] + t[i] * sqrt(self.L2[i]), d, inside

    def at(self, s):
        k = int(np.searchsorted(self.cum, s) - 1)
        k = max(0, min(len(self.pts) - 2, k))
        a, b = self.pts[k], self.pts[k + 1]
        t = (s - self.cum[k]) / max(1e-9, self.cum[k + 1] - self.cum[k])
        p = (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)
        L = hypot(b[0] - a[0], b[1] - a[1])
        tx, ty = (b[0] - a[0]) / L, (b[1] - a[1]) / L
        return p, (tx, ty), (-ty, tx), self.E[k], self.W[k]

    def edge_at(self, s):
        return self.at(s)[3]

    def offset_line(self, off, s0=0.0, s1=None, step=0.5):
        s1 = self.L if s1 is None else s1
        out = []
        s = s0
        while s <= s1 + 1e-9:
            p, t, n, _e, _w = self.at(min(s, self.L - 1e-6))
            out.append((p[0] + n[0] * off, p[1] + n[1] * off))
            s += step
        return out


# ---------------------------------------------------------------------------
# Cruces con calles -> puentes
# ---------------------------------------------------------------------------
def seg_intersect(a, b, c, d):
    r = (b[0] - a[0], b[1] - a[1])
    s = (d[0] - c[0], d[1] - c[1])
    den = r[0] * s[1] - r[1] * s[0]
    if abs(den) < 1e-12:
        return None
    q = (c[0] - a[0], c[1] - a[1])
    t = (q[0] * s[1] - q[1] * s[0]) / den
    u = (q[0] * r[1] - q[1] * r[0]) / den
    if 0 <= t <= 1 and 0 <= u <= 1:
        return t, u
    return None


def crossings(canal, roads):
    out = []
    for rd in roads:
        pts = rd["pts"]
        hits = []
        for i in range(len(pts) - 1):
            for j in range(len(canal.pts) - 1):
                r = seg_intersect(pts[i], pts[i + 1], canal.pts[j], canal.pts[j + 1])
                if r:
                    t, u = r
                    p = (pts[i][0] + (pts[i + 1][0] - pts[i][0]) * t, pts[i][1] + (pts[i + 1][1] - pts[i][1]) * t)
                    hits.append((canal.cum[j] + u * (canal.cum[j + 1] - canal.cum[j]), p, i))
        for s_c, p, i in hits:
            if s_c < 2.0:
                continue
            a, b = pts[i], pts[i + 1]
            L = hypot(b[0] - a[0], b[1] - a[1])
            out.append({"road": rd["name"], "road_type": rd["type"], "road_w": rd["width"], "s": s_c, "pt": p,
                        "dir": ((b[0] - a[0]) / L, (b[1] - a[1]) / L), "district": rd["district"]})
    out.sort(key=lambda c: c["s"])
    return out


# ---------------------------------------------------------------------------
# Terreno
# ---------------------------------------------------------------------------
def terrain_cut(obj, canal, extra_polys, esc_list, stats):
    me = obj.data
    bm = bmesh.new()
    bm.from_mesh(me)
    idx = S5.EdgeIndex(bm, r_min=80.0, r_max=200.0)
    locked = set()
    hw = CR.WIDTH / 2
    lines = []
    for off in (hw, -hw, hw - BED_INSET, -(hw - BED_INSET), CR.CORRIDOR_HALF, -CR.CORRIDOR_HALF,
                CR.CORRIDOR_HALF + SHOULDER, -(CR.CORRIDOR_HALF + SHOULDER)):
        lines.append(canal.offset_line(off))
    # cortes transversales en los azudes y en los extremos
    for w in CR.weirs(canal.pts, canal.E) + [{"s": 0.0}, {"s": canal.L - 0.01}]:
        p, t, n, _e, _w = canal.at(w["s"])
        lines.append([(p[0] + n[0] * o, p[1] + n[1] * o) for o in (-CR.CORRIDOR_HALF, CR.CORRIDOR_HALF)])
    for poly in extra_polys:
        lines.append(list(poly) + [poly[0]])
    for esc in esc_list:
        lines.append(list(esc["footprint"]) + [esc["footprint"][0]])
    for pts in lines:
        S5.knife(bm, idx, pts, locked)
    bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 3], quad_method="BEAUTY",
                          ngon_method="BEAUTY")
    moved = 0
    pits = [p for p in extra_polys if getattr(p, "kind", None) == "pit"]
    for v in bm.verts:
        x, y = v.co.x, v.co.y
        r = hypot(x, y)
        if 80.0 <= r <= 199.0:
            s, d, inside = canal.project(x, y)
            if inside and abs(d) <= CR.CORRIDOR_HALF + 1e-3:
                e = canal.edge_at(s)
                ad = abs(d)
                if ad <= hw - BED_INSET + 1e-3:
                    v.co.z = e - CR.DEPTH
                elif ad <= hw + 1e-3 and ad > hw - BED_INSET + 1e-3:
                    v.co.z = e if ad >= hw - 1e-3 else e - CR.DEPTH
                else:
                    v.co.z = e
                for pit in pits:
                    if pit.contains(x, y):
                        v.co.z = e - CR.DEPTH
                moved += 1
                continue
        for esc in esc_list:
            if esc["contains"](x, y):
                z_top = esc["profile_z"](x, y)
                if v.co.z > z_top - 0.2:
                    v.co.z = z_top - 0.2
                    moved += 1
                break
    bm.normal_update()
    bm.to_mesh(me)
    bm.free()
    me.update()
    me.set_sharp_from_angle(angle=radians(S2.SHARP_ANGLE))
    stats["cauce_terrain"] = {"knife_lines": len(lines), "verts_moved": moved, "tris_after": len(me.polygons)}


class Pit:
    """Hueco de la rueda hidraulica (rectangulo en coordenadas del canal: s0..s1, d0..d1)."""
    kind = "pit"

    def __init__(self, canal, s0, s1, d0, d1):
        self.canal, self.s0, self.s1, self.d0, self.d1 = canal, s0, s1, d0, d1
        pts = []
        for s, d in ((s0, d0), (s1, d0), (s1, d1), (s0, d1)):
            p, t, n, _e, _w = canal.at(s)
            pts.append((p[0] + n[0] * d, p[1] + n[1] * d))
        self.poly = pts

    def __iter__(self):
        return iter(self.poly)

    def __len__(self):
        return len(self.poly)

    def __getitem__(self, i):
        return self.poly[i]

    def contains(self, x, y):
        s, d, _in = self.canal.project(x, y)
        return self.s0 - 1e-3 <= s <= self.s1 + 1e-3 and min(self.d0, self.d1) - 1e-3 <= d <= max(self.d0, self.d1) + 1e-3


# ---------------------------------------------------------------------------
# Mallas
# ---------------------------------------------------------------------------
def material_water():
    name = "MAT_Water"
    if name in bpy.data.materials:
        bpy.data.materials.remove(bpy.data.materials[name])
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = C.hex_to_linear_rgba(WATER_HEX)
    b.inputs["Roughness"].default_value = 0.07
    b.inputs["IOR"].default_value = 1.33
    b.inputs["Specular IOR Level"].default_value = 0.35
    m["note"] = ("agua oscura y apagada: albedo casi negro, rugosidad 0.07; solo el especular refleja el azul "
                 "palido del cielo. En Godot: StandardMaterial3D o shader de agua sin emision.")
    return m


def material_repair():
    import material_library as ML
    m = ML.make_material("MAT_Stone_Repair", "WallPatch")
    m["note"] = "piedra de reparacion (20 % de los pretiles)"
    return m


def mb_object(mb, name, col, mat, extra_mats=()):
    obj = mb.to_object(name, col, mat)
    if obj:
        for m in extra_mats:
            obj.data.materials.append(m)
    return obj


def build_water(canal, col):
    """Lamina de agua por tramos (plana a 0.4 m bajo el borde) con saltos verticales en los azudes."""
    mb = ST2.MeshBuilder()
    hw = CR.WIDTH / 2 - 0.02
    s = 0.0
    prev = None
    while s <= canal.L + 1e-6:
        p, t, n, e, w = canal.at(min(s, canal.L - 1e-6))
        row = [(p[0] + n[0] * hw, p[1] + n[1] * hw, w), (p[0] - n[0] * hw, p[1] - n[1] * hw, w)]
        if prev is not None:
            if abs(prev[0][2] - w) > 1e-6:          # azud: cara vertical de caida
                top = [(r[0], r[1], prev[0][2]) for r in row]
                mb.add([prev[0], prev[1], row[1], row[0]], [(0, 1, 2, 3)])
                mb.add([prev[0], prev[1], top[1], top[0]], [(0, 1, 2, 3)])
                mb.add([top[0], top[1], row[1], row[0]], [(0, 1, 2, 3)])
            else:
                mb.add([prev[0], prev[1], row[1], row[0]], [(0, 1, 2, 3)])
        prev = row
        s += 1.0
    return mb_object(mb, "CAU_Water", col, material_water())


def build_banks(canal, col, mat, gaps, stats):
    """Albardilla de piedra a ambos lados (0.5 m x 0.12 m) salvo en puentes / muelle / rueda."""
    mb = ST2.MeshBuilder()
    hw = CR.WIDTH / 2

    def in_gap(s, side):
        return any(g0 <= s <= g1 and (sd == 0 or sd == side) for g0, g1, sd in gaps)
    n_seg = 0
    for side in (1, -1):
        s = 0.0
        while s < canal.L - 1e-6:
            s1 = min(canal.L, s + 2.0)
            if in_gap((s + s1) / 2, side):
                s = s1
                continue
            rings = []
            for ss in (s, s1):
                p, t, n, e, _w = canal.at(min(ss, canal.L - 1e-6))
                o0, o1 = side * hw, side * (hw + COPING_W)
                a0 = (p[0] + n[0] * o0, p[1] + n[1] * o0)
                a1 = (p[0] + n[0] * o1, p[1] + n[1] * o1)
                rings.append([(a0[0], a0[1], e - 0.25), (a1[0], a1[1], e - 0.25), (a1[0], a1[1], e + COPING_H),
                              (a0[0], a0[1], e + COPING_H)])
            mb.strip(rings)
            n_seg += 1
            s = s1
    obj = mb_object(mb, "CAU_Banks", col, mat)
    stats["cauce_banks"] = {"segments_2m": n_seg, "tris": len(obj.data.polygons)}
    return obj


def build_access_steps(canal, col, mat, avoid, stats):
    """Escalones de acceso al agua cada 20 m, alternando orilla: 2 contrahuellas de 0.15 + rellano."""
    mb = ST2.MeshBuilder()
    hw = CR.WIDTH / 2
    out = []
    s = 10.0
    side = 1
    k = 0
    while s < canal.L - 8.0:
        if any(a0 <= s <= a1 for a0, a1 in avoid):
            s += 2.0
            continue
        p, t, n, e, w = canal.at(s)
        k += 1
        tv, nv = Vector((t[0], t[1], 0)), Vector((n[0], n[1], 0))
        O = Vector((p[0], p[1], 0)) + nv * side * hw
        inward = -nv * side
        for j, (dz, depth) in enumerate(((RISER, TREAD), (2 * RISER, TREAD + 0.25))):
            z_top = e - dz
            d0 = 0.0 if j == 0 else TREAD
            d1 = d0 + depth
            prof = [(d0, e - CR.DEPTH - 0.05), (d1, e - CR.DEPTH - 0.05), (d1, z_top), (d0, z_top)]
            mb.prism(prof, tuple(O), tuple(inward), tuple(tv), -ACCESS_W / 2, ACCESS_W / 2)
        out.append({"name": f"MARKER_Cauce_Step_{k:02d}", "s": round(s, 1), "side": side,
                    "loc": (O.x + inward.x * 0.3, O.y + inward.y * 0.3, e - RISER), "angle": degrees(atan2(inward.y, inward.x))})
        side = -side
        s += CR.STEP_SPACING
    obj = mb_object(mb, "CAU_AccessSteps", col, mat)
    stats["cauce_access_steps"] = {"count": len(out), "riser_m": RISER, "tread_m": TREAD,
                                   "landing_above_water_m": round(CR.WATER_BELOW - 2 * RISER, 2),
                                   "tris": len(obj.data.polygons) if obj else 0}
    return out


def build_weirs(canal, col, mat, stats):
    mb = ST2.MeshBuilder()
    ws = CR.weirs(canal.pts, canal.E)
    hw = CR.WIDTH / 2
    for w in ws:
        p, t, n, e, _w = canal.at(w["s"])
        tv, nv = Vector((t[0], t[1], 0)), Vector((n[0], n[1], 0))
        crest = w["edge_before"] - CR.WATER_BELOW - 0.02
        prof = [(-0.5, w["edge_after"] - CR.DEPTH - 0.05), (0.0, w["edge_after"] - CR.DEPTH - 0.05),
                (0.0, crest), (-0.5, crest)]
        mb.prism(prof, (p[0], p[1], 0), tuple(tv), tuple(nv), -hw, hw)
    obj = mb_object(mb, "CAU_Weirs", col, mat)
    stats["cauce_weirs"] = {"count": len(ws), "drops_m": [w["drop"] for w in ws],
                            "at_s_m": [w["s"] for w in ws], "tris": len(obj.data.polygons) if obj else 0}
    return ws


def build_spring_head(canal, col, mat, void, stats):
    """Inicio del tramo abierto: muro de cabecera con boca (la mina viene de la Fuente del Mercado)."""
    p, t, n, e, w = canal.at(0.0)
    tv, nv = -Vector((t[0], t[1], 0)), Vector((n[0], n[1], 0))
    O = Vector((p[0], p[1], 0))
    mb = ST2.MeshBuilder()
    hw = CR.WIDTH / 2
    bed = e - CR.DEPTH
    mb.prism([(0.0, bed - 0.2), (0.6, bed - 0.2), (0.6, e + 0.6), (0.0, e + 0.6)], tuple(O), tuple(tv), tuple(nv),
             -(hw + 1.0), hw + 1.0)
    obj = mb_object(mb, "CAU_SpringHead", col, mat)
    mv = ST2.MeshBuilder()
    mv.prism([(-0.02, w - 0.05), (0.02, w - 0.05), (0.02, w + 0.55), (-0.02, w + 0.55)], tuple(O), tuple(tv),
             tuple(nv), -0.6, 0.6)
    mb_object(mv, "CAU_SpringHead_Mouth", col, void)
    stats["cauce_spring_head"] = {"open_from_r": OPEN_R, "buried_mine_m": round(CR.cumlen(canal.mine)[-1], 1),
                                  "tris": len(obj.data.polygons)}


def build_culvert(canal, col, mat, void, stats):
    """Boca de alcantarilla con reja en la cara interior de la muralla (fin del canal)."""
    p, t, n, e, w = canal.at(canal.L - 0.01)
    tv, nv = Vector((t[0], t[1], 0)), Vector((n[0], n[1], 0))
    O = Vector((p[0], p[1], 0))
    mb = ST2.MeshBuilder()
    hw = CR.WIDTH / 2
    bed = e - CR.DEPTH
    top = e + 0.9
    seg = 10
    # marco: pilastras y dintel en arco rebajado
    for sd in (-1, 1):
        mb.prism([(0.0, bed - 0.2), (0.5, bed - 0.2), (0.5, top), (0.0, top)], tuple(O), tuple(tv), tuple(nv),
                 sd * hw, sd * (hw + 0.5))
    arch = [(0.0, top + 0.5), (0.5, top + 0.5), (0.5, top), (0.0, top)]
    mb.prism(arch, tuple(O), tuple(tv), tuple(nv), -(hw + 0.5), hw + 0.5)
    obj = mb_object(mb, "CAU_Culvert", col, mat)
    # fondo oscuro + barrotes
    mv = ST2.MeshBuilder()
    mv.prism([(0.45, bed), (0.5, bed), (0.5, top), (0.45, top)], tuple(O), tuple(tv), tuple(nv), -hw, hw)
    vobj = mb_object(mv, "CAU_Culvert_Void", col, void)
    mg = ST2.MeshBuilder()
    nb = 9
    for i in range(nb):
        x = -hw + (i + 0.5) * (2 * hw / nb)
        mg.prism([(0.30, bed), (0.36, bed), (0.36, top), (0.30, top)], tuple(O), tuple(tv), tuple(nv), x - 0.03, x + 0.03)
    iron = bpy.data.materials.get("MAT_Iron_Black") or mat
    gobj = mb_object(mg, "CAU_Culvert_Grate", col, iron)
    stats["cauce_culvert"] = {"at_r": round(hypot(*p), 2), "opening_m": [CR.WIDTH, round(top - bed, 2)],
                              "grate_bars": nb, "tris": sum(len(o.data.polygons) for o in (obj, vobj, gobj) if o)}
    return O, tv


def build_muelle(canal, zone, col, mat, stats):
    """Muelle de 8 x 3 m: plataforma de piedra 0.2 m bajo el borde, entre la orilla y la zona del gremio."""
    c = np.mean(np.asarray(zone["poly"]), axis=0)
    s, d, _in = canal.project(*c)
    side = 1 if d > 0 else -1
    p, t, n, e, w = canal.at(s)
    tv, nv = Vector((t[0], t[1], 0)), Vector((n[0], n[1], 0))
    mb = ST2.MeshBuilder()
    z = e - 0.2
    mb.prism([(-4.0, e - CR.DEPTH - 0.05), (4.0, e - CR.DEPTH - 0.05), (4.0, z), (-4.0, z)], (p[0], p[1], 0),
             tuple(tv), tuple(nv), side * (CR.WIDTH / 2 - 0.6), side * (CR.WIDTH / 2 - 0.6 + 3.0))
    obj = mb_object(mb, "CAU_Muelle_Pescadores", col, mat)
    moor = []
    for k, ss in enumerate((-3.0, -1.0, 1.0, 3.0)):
        q = Vector((p[0], p[1], 0)) + tv * ss + nv * side * (CR.WIDTH / 2 - 0.45)
        moor.append({"name": f"MARKER_Mooring_{k + 1:02d}", "loc": (q.x, q.y, z), "angle": degrees(atan2(-nv.y * side, -nv.x * side))})
    stats["cauce_muelle"] = {"size_m": "8x3", "deck_z": round(z, 3), "over_water_m": 0.6, "mooring_posts": len(moor),
                             "s_m": round(s, 1)}
    return (s - 4.2, s + 4.2, side), moor, {"loc": (p[0] + nv.x * side * 3, p[1] + nv.y * side * 3, z),
                                            "angle": degrees(atan2(nv.y * side, nv.x * side))}


# ---------------------------------------------------------------------------
# Puentes y arcos
# ---------------------------------------------------------------------------
def add_parapets(mb, mbr, rng, O, ax, nv, s_list, z_list, half_w, stats_cnt):
    """Pretiles 0.9 m a ambos lados siguiendo el perfil (s, z); tramos de 2 m, 20 % con piedra de remiendo."""
    for side in (1, -1):
        for i in range(len(s_list) - 1):
            s0, s1 = s_list[i], s_list[i + 1]
            n = max(1, int(ceil((s1 - s0) / 2.0)))
            for k in range(n):
                a0 = s0 + (s1 - s0) * k / n
                a1 = s0 + (s1 - s0) * (k + 1) / n
                za = z_list[i] + (z_list[i + 1] - z_list[i]) * (a0 - s0) / max(1e-9, s1 - s0)
                zb = z_list[i] + (z_list[i + 1] - z_list[i]) * (a1 - s0) / max(1e-9, s1 - s0)
                target = mbr if rng.random() < REPAIR_FRAC else mb
                stats_cnt[0] += 1
                stats_cnt[1] += int(target is mbr)
                o0, o1 = side * (half_w - PARAPET_T), side * half_w
                ring0 = [tuple(O + ax * a0 + nv * o + Vector((0, 0, z))) for o, z in
                         ((o0, za - 0.1), (o1, za - 0.1), (o1, za + PARAPET_H), (o0, za + PARAPET_H))]
                ring1 = [tuple(O + ax * a1 + nv * o + Vector((0, 0, z))) for o, z in
                         ((o0, zb - 0.1), (o1, zb - 0.1), (o1, zb + PARAPET_H), (o0, zb + PARAPET_H))]
                target.strip([ring0, ring1])


def build_bridges(canal, cross, col, stone, repair, stats):
    rng = random.Random(f"{SEED}-bridges")
    out = []
    cnt = [0, 0]
    gaps = []
    for k, cx in enumerate(cross):
        width = max(5.0, min(6.0, cx["road_w"]))
        ax = Vector((cx["dir"][0], cx["dir"][1], 0)).normalized()
        nv = Vector((-ax.y, ax.x, 0))
        p, t, n, e, w = canal.at(cx["s"])
        ct = Vector((t[0], t[1], 0))
        sin_a = max(0.35, abs(ax.x * ct.y - ax.y * ct.x))         # seno del angulo calle / canal
        half_span = CR.CORRIDOR_HALF / sin_a
        O = Vector((cx["pt"][0], cx["pt"][1], 0))
        z_road = max(e + 0.1, T.height(*cx["pt"]))
        z_deck = z_road + BRIDGE_RISE
        s_list = [-(half_span + BRIDGE_RAMP), -half_span, half_span, half_span + BRIDGE_RAMP]
        z_list = [z_road, z_deck, z_deck, z_road]
        mb, mbr = ST2.MeshBuilder(), ST2.MeshBuilder()
        # tablero con rampas (perfil en s, extruido a lo ancho)
        prof = [(s_list[0], z_road - BRIDGE_DECK_T), (s_list[3], z_road - BRIDGE_DECK_T), (s_list[3], z_road),
                (s_list[2], z_deck), (s_list[1], z_deck), (s_list[0], z_road)]
        mb.prism(prof, tuple(O), tuple(ax), tuple(nv), -width / 2, width / 2)
        # boveda: timpanos con arco escarzano sobre el canal (de estribo a estribo)
        span = (CR.WIDTH / 2) / sin_a
        bed = e - CR.DEPTH
        spring = w - 0.1
        crown = z_deck - BRIDGE_DECK_T - 0.15
        arch = [(-half_span, bed - 0.2), (-half_span, z_deck - 0.05), (half_span, z_deck - 0.05), (half_span, bed - 0.2),
                (span, bed - 0.2), (span, spring)]
        segs = 12
        for i in range(1, segs):
            a = pi * i / segs
            arch.append((span * cos(a), spring + (crown - spring) * sin(a)))
        arch += [(-span, spring), (-span, bed - 0.2)]
        mb.prism(arch, tuple(O), tuple(ax), tuple(nv), -width / 2, width / 2)
        add_parapets(mb, mbr, rng, O + Vector((0, 0, 0.0)), ax, nv, s_list, z_list, width / 2, cnt)
        name = f"TRN_Bridge_{k + 1:02d}-col"
        obj = mb_object(mb, name, col, stone)
        robj = mb_object(mbr, f"TRN_Bridge_{k + 1:02d}_Repair", col, repair)
        total_len = s_list[3] - s_list[0]
        out.append({"name": f"MARKER_Bridge_{k + 1:02d}", "type": "cauce", "loc": (O.x, O.y, z_deck),
                    "angle": degrees(atan2(ax.y, ax.x)), "width_m": round(width, 2), "length_m": round(total_len, 2),
                    "deck_z": round(z_deck, 3), "road": cx["road"], "district": cx["district"],
                    "ramp_deg": round(degrees(atan2(BRIDGE_RISE, BRIDGE_RAMP)), 2),
                    "clear_over_water_m": round(crown - w, 2),
                    "tris": (len(obj.data.polygons) if obj else 0) + (len(robj.data.polygons) if robj else 0)})
        gaps.append((cx["s"] - half_span * sin_a - 0.5 - width / 2 / sin_a, cx["s"] + half_span * sin_a + 0.5 + width / 2 / sin_a, 0))
    stats["bridges_cauce"] = out
    return out, gaps, cnt


def barrio_of(name):
    import re
    m = re.search(r"_B(\d\d)_|CasaRaza_(\d\d)", name)
    return int(m.group(1) or m.group(2)) if m else None


def arch_candidates(lay, n):
    """Puntos de calles de Razas (4-6 m) con parcelas a ambos lados: arcos entre barrios."""
    import stage05_layout as L
    parcels = [p for p in lay["parcels"] if p["district"] == "Razas" and p["type"] != "stall"]
    cands = []
    for rd in lay["roads"]:
        if rd["district"] != "Razas" or not (4.0 <= rd["width"] <= 6.0) or rd["type"] not in ("alley", "ring"):
            continue
        pts = L.resample(rd["pts"], 2.0)
        hw = rd["width"] / 2
        for i in range(1, len(pts) - 1):
            a, b = pts[i - 1], pts[i + 1]
            tx, ty = b[0] - a[0], b[1] - a[1]
            Lt = hypot(tx, ty)
            nx, ny = -ty / Lt, tx / Lt
            sides = []
            for sg in (1, -1):
                q = (pts[i][0] + nx * sg * (hw + 1.5), pts[i][1] + ny * sg * (hw + 1.5))
                hit = next((p for p in parcels if L.point_in_poly(q[0], q[1], p["poly"])), None)
                sides.append(hit)
            if sides[0] and sides[1]:
                b0, b1 = barrio_of(sides[0]["name"]), barrio_of(sides[1]["name"])
                cands.append({"road": rd["name"], "pt": pts[i], "dir": (tx / Lt, ty / Lt), "w": rd["width"],
                              "between": [sides[0]["name"], sides[1]["name"]], "cross_barrio": b0 != b1,
                              "z": T.height(*pts[i])})
    cands.sort(key=lambda c: (not c["cross_barrio"], c["road"]))
    chosen = []
    for c in cands:
        if all(hypot(c["pt"][0] - o["pt"][0], c["pt"][1] - o["pt"][1]) > 12.0 for o in chosen):
            chosen.append(c)
        if len(chosen) >= n:
            break
    return chosen, len(cands)


def build_arches(lay, col, stone, repair, stats):
    rng = random.Random(f"{SEED}-arches")
    chosen, ncand = arch_candidates(lay, N_ARCHES)
    out = []
    cnt = [0, 0]
    for k, c in enumerate(chosen):
        ax = Vector((c["dir"][0], c["dir"][1], 0))         # a lo largo de la calle
        nv = Vector((-ax.y, ax.x, 0))                      # el paso elevado cruza la calle (eje nv)
        O = Vector((c["pt"][0], c["pt"][1], 0))
        span = c["w"] / 2 + 0.6                            # de retranqueo a retranqueo
        z0 = c["z"]
        spring = z0 + ARCH_CLEAR - 1.2
        crown = z0 + ARCH_CLEAR
        deck = crown + ARCH_DECK_T
        mb, mbr = ST2.MeshBuilder(), ST2.MeshBuilder()
        prof = [(-span - ARCH_PIER, z0 - 0.3), (-span, z0 - 0.3), (-span, spring)]
        segs = 14
        for i in range(1, segs):
            a = pi - pi * i / segs
            prof.append((span * cos(a), spring + (crown - spring) * sin(a)))
        prof += [(span, spring), (span, z0 - 0.3), (span + ARCH_PIER, z0 - 0.3), (span + ARCH_PIER, deck),
                 (-span - ARCH_PIER, deck)]
        mb.prism(prof, tuple(O), tuple(nv), tuple(ax), -ARCH_DEPTH / 2, ARCH_DEPTH / 2)
        add_parapets(mb, mbr, rng, O, nv, ax, [-span - ARCH_PIER, span + ARCH_PIER], [deck, deck], ARCH_DEPTH / 2, cnt)
        obj = mb_object(mb, f"TRN_ArchBridge_{k + 1:02d}-col", col, stone)
        robj = mb_object(mbr, f"TRN_ArchBridge_{k + 1:02d}_Repair", col, repair)
        out.append({"name": f"MARKER_Bridge_{len(stats.get('bridges_cauce', [])) + k + 1:02d}", "type": "arco",
                    "loc": (O.x, O.y, deck), "angle": degrees(atan2(nv.y, nv.x)),
                    "width_m": ARCH_DEPTH, "length_m": round(2 * (span + ARCH_PIER), 2), "deck_z": round(deck, 3),
                    "clear_height_m": round(crown - z0, 2), "street": c["road"], "street_w_m": c["w"],
                    "between": c["between"], "cross_barrio": c["cross_barrio"],
                    "tris": (len(obj.data.polygons) if obj else 0) + (len(robj.data.polygons) if robj else 0)})
    stats["bridges_arcos"] = {"built": out, "candidates": ncand}
    return out, cnt


# ---------------------------------------------------------------------------
# Escalinatas (rampa de los hitos a las Moradas)
# ---------------------------------------------------------------------------
def esc_sites(morada_lay):
    """10 escalinatas en la rampa r 95-105 (8.5-10 grados): posiciones de stage06_moradas.ESC_ARCS
    (en las Moradas con la puerta hacia la muralla la etapa 06 deja hueco en la fila de la terraza 1)."""
    import stage06_moradas as SM
    out = []
    for key, phi in T.DIAGONAL_ANGLE.items():
        for arc in SM.ESC_ARCS[key]:
            out.append((key, phi + degrees(arc / 100.0)))
    return out


def build_escalinatas(morada_lay, col, stone, repair, stats):
    rng = random.Random(f"{SEED}-esc")
    sites = esc_sites(morada_lay)
    n_r = int(round((C.DATUM - C.Z_MORADAS_MIN) / RISER))           # 10
    run = (n_r - 1) * TREAD                                           # 3.15
    u_top, u_bot = T.ESC_U0, T.ESC_U1                                 # 95, 105
    u_s0 = (u_top + u_bot) / 2 - run / 2                              # 98.43
    out, defs = [], []
    cnt = [0, 0]
    for k, (key, ang) in enumerate(sites):
        a = radians(ang)
        e = Vector((cos(a), sin(a), 0))
        nv = Vector((-sin(a), cos(a), 0))
        mb, mbr = ST2.MeshBuilder(), ST2.MeshBuilder()
        prof = [(u_top - 0.6, C.Z_MORADAS_MIN - 0.6), (u_bot + 0.4, C.Z_MORADAS_MIN - 0.6), (u_bot + 0.4, C.Z_MORADAS_MIN)]
        steps = [(u_s0 + i * TREAD, C.DATUM - (i + 1) * RISER) for i in range(n_r)]
        prof.append((steps[-1][0], C.Z_MORADAS_MIN))
        for i in range(n_r - 1, 0, -1):
            prof += [(steps[i][0], steps[i - 1][1]), (steps[i - 1][0], steps[i - 1][1])]
        prof += [(steps[0][0], C.DATUM), (u_top - 0.6, C.DATUM)]
        clean = [prof[0]]
        for q in prof[1:]:
            if abs(q[0] - clean[-1][0]) > 1e-9 or abs(q[1] - clean[-1][1]) > 1e-9:
                clean.append(q)
        mb.prism(clean, (0, 0, 0), tuple(e), tuple(nv), -ESC_W / 2, ESC_W / 2)
        # zancas / pretiles 0.9 m siguiendo la escalera
        s_list = [u_top - 0.6, u_s0, u_s0 + run + TREAD, u_bot + 0.4]
        z_list = [C.DATUM, C.DATUM, C.Z_MORADAS_MIN, C.Z_MORADAS_MIN]
        for side in (1, -1):
            for i in range(3):
                target = mbr if rng.random() < REPAIR_FRAC else mb
                cnt[0] += 1
                cnt[1] += int(target is mbr)
                o0, o1 = side * (ESC_W / 2), side * (ESC_W / 2 + 0.4)
                pr = [(s_list[i], min(z_list[i], z_list[i + 1]) - 0.8), (s_list[i + 1], min(z_list[i], z_list[i + 1]) - 0.8),
                      (s_list[i + 1], z_list[i + 1] + PARAPET_H), (s_list[i], z_list[i] + PARAPET_H)]
                target.prism(pr, (0, 0, 0), tuple(e), tuple(nv), min(o0, o1), max(o0, o1))
        obj = mb_object(mb, f"TRN_StairPass_{k + 1:02d}-col", col, stone)
        robj = mb_object(mbr, f"TRN_StairPass_{k + 1:02d}_Repair", col, repair)
        fp = [tuple(e * u + nv * v) [:2] for u, v in ((u_top - 0.6, -ESC_W / 2 - 0.45), (u_bot + 0.4, -ESC_W / 2 - 0.45),
                                                      (u_bot + 0.4, ESC_W / 2 + 0.45), (u_top - 0.6, ESC_W / 2 + 0.45))]

        def contains(x, y, a=a):
            u = x * cos(a) + y * sin(a)
            v = -x * sin(a) + y * cos(a)
            return u_top - 0.6 <= u <= u_bot + 0.4 and abs(v) <= ESC_W / 2 + 0.45

        def profile_z(x, y, a=a):
            u = x * cos(a) + y * sin(a)
            if u <= u_s0:
                return C.DATUM
            if u >= u_s0 + run + TREAD:
                return C.Z_MORADAS_MIN
            i = int((u - u_s0) / TREAD)
            return C.DATUM - (i + 1) * RISER
        defs.append({"footprint": fp, "contains": contains, "profile_z": profile_z})
        slope = degrees(atan2(T.height(*(e * 98.0)[:2]) - T.height(*(e * 102.0)[:2]), 4.0))
        out.append({"name": f"MARKER_Escalinata_{k + 1:02d}", "morada": key, "angle_deg": round(ang, 2),
                    "loc": tuple(e * u_s0 + Vector((0, 0, C.DATUM))), "heading": degrees(a),
                    "risers": n_r, "riser_m": RISER, "tread_m": TREAD, "width_m": ESC_W,
                    "terrain_slope_deg": round(slope, 2),
                    "tris": (len(obj.data.polygons) if obj else 0) + (len(robj.data.polygons) if robj else 0)})
    stats["escalinatas"] = out
    return out, defs, cnt


# ---------------------------------------------------------------------------
def repair_existing_parapets(repair, stats):
    """20 % de los tramos (celdas de 2 m) de los pretiles existentes pasan a MAT_Stone_Repair."""
    rng = random.Random(f"{SEED}-repair")
    tot = rep = 0
    names = [o.name for o in bpy.data.objects if o.type == "MESH" and (o.name.startswith("TRN_Parapets_")
                                                                         or o.name.startswith("TRN_Escalinata_"))]
    for nm in names:
        o = bpy.data.objects[nm]
        me = o.data
        if repair.name not in [m.name for m in me.materials if m]:
            me.materials.append(repair)
        ri = [m.name for m in me.materials].index(repair.name)
        cells = {}
        mw = o.matrix_world
        for p in me.polygons:
            c = mw @ p.center
            key = (int(c.x // 2.0), int(c.y // 2.0))
            if key not in cells:
                cells[key] = rng.random() < REPAIR_FRAC
            if cells[key]:
                p.material_index = ri
        tot += len(cells)
        rep += sum(cells.values())
    stats["repairs_existing"] = {"objects": names, "cells_2m": tot, "repaired": rep,
                                 "fraction": round(rep / max(1, tot), 3)}


def write_masks(obj, canal):
    me = obj.data
    nl = len(me.loops)
    loop_f = [0] * nl
    for p in me.polygons:
        for li in range(p.loop_start, p.loop_start + p.loop_total):
            loop_f[li] = p.index
    kinds = []
    for p in me.polygons:
        c = p.center
        r = hypot(c.x, c.y)
        if 80 <= r <= 199:
            s, d, inside = canal.project(c.x, c.y)
            if inside and abs(d) <= CR.CORRIDOR_HALF:
                kinds.append("bed" if abs(d) <= CR.WIDTH / 2 else "bank")
                continue
        kinds.append(None)
    for name, vals in (("road_mask", {"bed": 0.0, "bank": 1.0}), ("cobble_type", {"bed": COBBLE_CAUCE / 8, "bank": 4 / 8}),
                       ("wear_mask", {"bed": 0.0, "bank": 0.2})):
        a = me.color_attributes[name]
        v = [0.0] * (nl * 4)
        a.data.foreach_get("color", v)
        for li in range(nl):
            k = kinds[loop_f[li]]
            if k:
                v[li * 4:li * 4 + 3] = [vals[k]] * 3
        a.data.foreach_set("color", v)
    uv = me.uv_layers["UVRoads"]
    u = [0.0] * (nl * 2)
    uv.data.foreach_get("uv", u)
    for li in range(nl):
        k = kinds[loop_f[li]]
        if k == "bed":
            u[li * 2:li * 2 + 2] = [0.0, float(COBBLE_CAUCE)]
        elif k == "bank":
            u[li * 2:li * 2 + 2] = [1.0, 4.0 + 0.99 * 0.2]
    uv.data.foreach_set("uv", u)


def markers(col_c, col_s, items):
    for it, col in items:
        name = it["name"]
        if name in bpy.data.objects:
            bpy.data.objects.remove(bpy.data.objects[name])
        e = bpy.data.objects.new(name, None)
        e.empty_display_type = "ARROWS"
        e.empty_display_size = 1.5
        e.location = it["loc"]
        e.rotation_euler = (0, 0, radians(it.get("angle", 0.0) - 90.0))
        for k, v in it.items():
            if k in ("name", "loc"):
                continue
            e[k] = v if isinstance(v, (int, float, str, bool)) else str(v)
        col.objects.link(e)


def build(scene, stats):
    with open(os.path.join(REPO, "docs", "reports", "stage05_layout.json")) as fh:
        lay = json.load(fh)
    with open(os.path.join(REPO, "docs", "reports", "stage06_layout.json")) as fh:
        mlay = json.load(fh)
    canal = Canal()
    col = bpy.data.collections["CAUCE"]
    for o in list(col.all_objects):
        bpy.data.objects.remove(o)
    col_s = bpy.data.collections["STREETS"]
    for o in list(col_s.objects):
        if o.name.startswith(("TRN_ArchBridge_", "TRN_StairPass_")):
            bpy.data.objects.remove(o)
    stone = ST2.stone_material()
    repair = material_repair()
    void = bpy.data.materials.get("MAT_Void") or ST2.stone_material()
    stats["cauce"] = {"length_m": round(canal.L, 1), "width_m": CR.WIDTH, "depth_m": CR.DEPTH,
                      "water_below_edge_m": CR.WATER_BELOW, "edge_levels": sorted(set(canal.E), reverse=True),
                      "water_levels": sorted(set(round(w, 3) for w in canal.W), reverse=True),
                      "source": "Fuente del Mercado", "outlet": "alcantarilla con reja, cara interior de la muralla (345 grados)"}
    cross = crossings(canal, lay["roads"])
    # Carpinteria (rueda) y muelle
    carp = next((p for p in lay["parcels"] if p["name"] == "MARKER_Bld_Taller_Carpinteria"), None)
    muelle_zone = next((z for z in lay["zones"] if z["name"] == "ZONE_OFI_MuellePescadores"), None)
    extra_polys = []
    gaps = []
    wheel = None
    if carp:
        s, d, _in = canal.project(*carp["center"])
        side = 1 if d > 0 else -1
        pit = Pit(canal, s - 1.5, s + 1.5, side * CR.WIDTH / 2, side * CR.CORRIDOR_HALF)
        extra_polys.append(pit)
        gaps.append((s - 1.6, s + 1.6, side))
        p, t, n, e, w = canal.at(s)
        nv = Vector((n[0], n[1], 0)) * side
        wheel = {"name": "MARKER_Cauce_WaterWheel", "loc": (p[0] + nv.x * (CR.WIDTH / 2 + 0.5), p[1] + nv.y * (CR.WIDTH / 2 + 0.5), w),
                 "angle": degrees(atan2(nv.y, nv.x)), "type": "water_wheel", "parcel": carp["name"],
                 "gap_m": 3.0, "wheel_diameter_m": 3.6, "wheel_width_m": 1.0, "axis": "+Y local (hacia la Carpinteria)",
                 "water_z": round(w, 3)}
        stats["cauce_wheel_gap"] = {"s_m": round(s, 1), "width_m": 3.0, "side": side, "parcel": carp["name"]}
    # escalinatas (definen cortes del terreno)
    esc, esc_defs, cnt_e = build_escalinatas(mlay, col_s, stone, repair, stats)
    terrain_cut(bpy.data.objects["TRN_City"], canal, extra_polys, esc_defs, stats)
    write_masks(bpy.data.objects["TRN_City"], canal)
    build_water(canal, col)
    bridges, bgaps, cnt_b = build_bridges(canal, cross, col, stone, repair, stats)
    gaps += bgaps
    mz = moor = None
    if muelle_zone:
        mz, moor, muelle_marker = build_muelle(canal, muelle_zone, col, stone, stats)
        gaps.append(mz)
    build_banks(canal, col, stone, gaps, stats)
    weirs = build_weirs(canal, col, stone, stats)
    avoid = [(g0, g1) for g0, g1, _sd in gaps] + [(w["s"] - 3, w["s"] + 3) for w in weirs] + [(canal.L - 6, canal.L)]
    steps = build_access_steps(canal, col, stone, avoid, stats)
    build_culvert(canal, col, stone, void, stats)
    build_spring_head(canal, col, stone, void, stats)
    arches, cnt_a = build_arches(lay, col_s, stone, repair, stats)
    repair_existing_parapets(repair, stats)
    stats["repairs_new"] = {"parapet_segments": cnt_b[0] + cnt_a[0] + cnt_e[0],
                            "repaired": cnt_b[1] + cnt_a[1] + cnt_e[1],
                            "fraction": round((cnt_b[1] + cnt_a[1] + cnt_e[1]) / max(1, cnt_b[0] + cnt_a[0] + cnt_e[0]), 3)}
    # marcadores
    mcol = bpy.data.collections.get("CAUCE_MARKERS")
    if mcol is None:
        mcol = bpy.data.collections.new("CAUCE_MARKERS")
        col.children.link(mcol)
    p0, t0, n0, e0, w0 = canal.at(0.5)
    items = [({"name": "MARKER_Cauce_Source", "loc": (p0[0], p0[1], w0), "angle": degrees(atan2(t0[1], t0[0])),
               "type": "spring", "fountain": "MARKER_Prop_FuenteMercado"}, mcol)]
    pe, te, ne, ee, we = canal.at(canal.L - 0.5)
    items.append(({"name": "MARKER_Cauce_Outlet", "loc": (pe[0], pe[1], we), "angle": degrees(atan2(te[1], te[0])),
                   "type": "culvert", "drain": "WALL_Drain_Slot46"}, mcol))
    items += [(b, mcol) for b in bridges]
    items += [(a, mcol) for a in arches]
    items += [(s_, mcol) for s_ in steps]
    items += [(e_, mcol) for e_ in esc]
    if wheel:
        items.append((wheel, mcol))
    if moor:
        items += [(m, mcol) for m in moor]
        items.append(({"name": "MARKER_Muelle_Pescadores", **muelle_marker, "size_m": "8x3"}, mcol))
    markers(col, col_s, items)
    stats["cauce_markers"] = len(items)
    stats["bridges_total"] = {"cauce": len(bridges), "arcos": len(arches)}
    return canal
