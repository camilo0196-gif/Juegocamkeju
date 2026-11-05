"""
CONCORDIA - etapa 08: terreno exterior de ceniza (r = 212 .. 400). v07 -> v08. Coleccion EXTERIOR.

Ref. Bardenas Reales (forma del relieve: badlands, cauces secos, mesetas y cabezos de arenisca) con color
gris ceniza. Sin senderos, puentes ni rampas: las 4 puertas dan al talud de TRN_City (+6 -> 0, r 204-212) y
a montones de ceniza acumulada.

Malla TRN_Exterior: anillos polares (1.5 m hasta r=230, 3 m despues); el primer anillo son exactamente los
vertices del borde de TRN_City (r=212, z=0): costura sin huecos.
Relieve: foso seco r 212-222 (fondo -1.5, relleno de ceniza); base 0 + ruido grande (80 m, +-3) + medio
(15 m, +-0.6) con amplitud minima junto a la muralla y creciente hacia fuera; dunas bajas (0.5-2 m) contra
la muralla; cauce seco (15-25 m x 4-6 m, meandros, orillas erosionadas); 6 crateres (10-30 m); 17 cabezos
de roca estratificada (6-20 m, mallas EXT_Rock_*); acantilados cerrados r 380-400 (25-40 m, EXT_Cliffs).
Mascaras: ash_mask, ash_dark_mask, rock_mask (+ mask_pack RGBA = ash, ash_dark, rock, dune para COLOR_0).
"""

import os
import random
import sys
from math import atan2, ceil, cos, degrees, exp, floor, hypot, pi, radians, sin, sqrt

import bmesh
import bpy
import numpy as np
from mathutils import Vector, noise

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import concordia_const as C  # noqa: E402
import stage02_chunks as CH  # noqa: E402

SEED = 808
R_IN = C.TERRAIN_RADIUS            # 212
R_MOAT = (212.0, 222.0)
MOAT_BOTTOM = -1.5
R_OUT = 400.0
CLIFF_R = (380.0, 400.0)
CLIFF_H = (25.0, 40.0)
NOISE_BIG = (80.0, 3.0)
NOISE_MED = (15.0, 0.6)
AMP_RAMP = (222.0, 300.0)         # amplitud del ruido: minima junto a la muralla -> completa
AMP_MIN = 0.25
MEAN_RISE = 2.5                   # subida media hacia el borde (capas de relieve)
DUNE_BAND = (212.5, 250.0)
DUNE_H = (0.5, 2.0)
GATE_HEAP_H = 2.0
WASH_W = (15.0, 25.0)
WASH_D = (4.0, 6.0)
N_ROCKS = 17
ROCK_H = (6.0, 20.0)
N_CRATERS = 6
CRATER_D = (10.0, 30.0)
STRATA_STEP = 1.2                 # escalonado suave del relieve alto (estratos de Bardenas)
DS_NEAR, DS_FAR = 1.5, 3.0
ASH = "#6F6F6F"
ASH_DARK = "#4F4F4F"
ASH_LIGHT = "#828282"
ROCK = "#5E5E5E"
ROCK_LIGHT = "#747474"


def nz(x, y, scale, seed):
    return noise.noise(Vector((x / scale + seed * 0.731, y / scale - seed * 0.377, seed * 0.113)),
                       noise_basis="PERLIN_NEW")


def smooth(e0, e1, x):
    t = max(0.0, min(1.0, (x - e0) / (e1 - e0)))
    return t * t * (3 - 2 * t)


# ---------------------------------------------------------------------------
# Rasgos
# ---------------------------------------------------------------------------
def wash_path():
    """Cauce seco: de los acantilados del NO (150 grados) a los del SE (-40 grados) bordeando la ciudad."""
    rng = random.Random(SEED)
    p1, p2 = rng.uniform(0, 6.28), rng.uniform(0, 6.28)
    pts = []
    for i in range(0, 381):
        t = i / 380.0
        th = radians(150.0 - 190.0 * t)
        base = 300.0 + 32.0 * sin(3.1 * th + p1) + 12.0 * sin(7.3 * th + p2)
        # extremos: entra y sale por los acantilados
        r = base + (392.0 - base) * (1 - smooth(0.0, 0.12, t)) + (392.0 - base) * smooth(0.88, 1.0, t)
        pts.append((r * cos(th), r * sin(th)))
    cum = [0.0]
    for a, b in zip(pts, pts[1:]):
        cum.append(cum[-1] + hypot(b[0] - a[0], b[1] - a[1]))
    return np.asarray(pts), np.asarray(cum)


def features():
    rng = random.Random(SEED + 1)
    wp, wc = wash_path()

    def wash_dist(x, y):
        d = np.hypot(wp[:, 0] - x, wp[:, 1] - y)
        i = int(np.argmin(d))
        return float(d[i]), float(wc[i])
    rocks, craters = [], []
    tries = 0
    while len(rocks) < N_ROCKS and tries < 5000:
        tries += 1
        r = rng.uniform(245, 365)
        th = rng.uniform(0, 360)
        x, y = r * cos(radians(th)), r * sin(radians(th))
        rb = rng.uniform(5.0, 11.0)
        if wash_dist(x, y)[0] < WASH_W[1] / 2 + rb + 8:
            continue
        if any(hypot(x - o["x"], y - o["y"]) < rb + o["rb"] + 22 for o in rocks):
            continue
        rocks.append({"x": x, "y": y, "rb": rb, "h": rng.uniform(*ROCK_H), "seed": rng.randint(0, 10 ** 6),
                      "mesa": rng.random() < 0.35})
    tries = 0
    while len(craters) < N_CRATERS and tries < 5000:
        tries += 1
        r = rng.uniform(240, 360)
        th = rng.uniform(0, 360)
        x, y = r * cos(radians(th)), r * sin(radians(th))
        D = rng.uniform(*CRATER_D)
        if wash_dist(x, y)[0] < WASH_W[1] / 2 + D / 2 + 6:
            continue
        if any(hypot(x - o["x"], y - o["y"]) < o["rb"] + D / 2 + 12 for o in rocks):
            continue
        if any(hypot(x - o["x"], y - o["y"]) < (o["D"] + D) / 2 + 15 for o in craters):
            continue
        craters.append({"x": x, "y": y, "D": D})
    return {"wash": (wp, wc), "wash_dist": wash_dist, "rocks": rocks, "craters": craters}


class Relief:
    def __init__(self, F):
        self.F = F
        self.wp, self.wc = F["wash"]

    def base(self, x, y):
        r = hypot(x, y)
        amp = AMP_MIN + (1 - AMP_MIN) * smooth(*AMP_RAMP, r)
        z = amp * (NOISE_BIG[1] * nz(x, y, NOISE_BIG[0], 1) + NOISE_MED[1] * nz(x, y, NOISE_MED[0], 2))
        # carcavas (badlands): surcos de pequena escala en las laderas
        g = 1.0 - abs(nz(x, y, 22.0, 3))
        z -= amp * 0.7 * max(0.0, g - 0.75) * 4.0
        z += MEAN_RISE * smooth(222.0, 380.0, r)
        # estratos: escalonado parcial de las partes altas
        if z > 0.5:
            q = floor(z / STRATA_STEP) * STRATA_STEP + STRATA_STEP * smooth(0.65, 1.0, (z % STRATA_STEP) / STRATA_STEP)
            z = z + 0.45 * (q - z)
        return z

    def height(self, x, y):
        r = hypot(x, y)
        z = self.base(x, y)
        # foso seco
        moat = smooth(R_MOAT[0], R_MOAT[0] + 2.5, r) * (1 - smooth(R_MOAT[1] - 2.5, R_MOAT[1], r))
        z = z * smooth(R_MOAT[0], R_MOAT[1] + 6, r) + MOAT_BOTTOM * moat
        dune = self.dune(x, y)
        z += dune
        # cauce seco
        d, s = self.F["wash_dist"](x, y)
        hw = 0.5 * (WASH_W[0] + (WASH_W[1] - WASH_W[0]) * (0.5 + 0.5 * sin(s / 37.0)))
        depth = WASH_D[0] + (WASH_D[1] - WASH_D[0]) * (0.5 + 0.5 * nz(s, 0, 60.0, 4))
        bank = hw + 3.0 + 2.5 * nz(x, y, 9.0, 5)               # orilla erosionada irregular
        if d < bank + 6:
            core = 1.0 - smooth(hw * 0.55, bank, d)
            z -= depth * core + 0.8 * max(0.0, nz(x, y, 4.0, 6)) * (1 - smooth(bank, bank + 6, d)) * (d > hw * 0.5)
        # crateres
        for c in self.F["craters"]:
            dd = hypot(x - c["x"], y - c["y"])
            R = c["D"] / 2
            if dd < R * 1.6:
                bowl = 0.17 * c["D"] * max(0.0, 1 - (dd / R) ** 2)
                rim = 0.06 * c["D"] * exp(-((dd - R) / (0.22 * R)) ** 2)
                z += rim - bowl
        # acantilados: el suelo sube hacia la base del muro de roca
        z += 4.0 * smooth(CLIFF_R[0] - 25, CLIFF_R[0] + 2, r)
        return z

    def dune(self, x, y):
        r = hypot(x, y)
        if r > DUNE_BAND[1] + 5:
            return 0.0
        th = atan2(y, x)
        # crestas alargadas paralelas a la muralla (viento de fuera), altura 0.5-2 m
        crest = 0.5 + 0.5 * sin((r - 212.0) / 5.5 * 2 * pi + 3.0 * nz(x, y, 40.0, 7))
        h = DUNE_H[0] + (DUNE_H[1] - DUNE_H[0]) * (0.5 + 0.5 * nz(x, y, 30.0, 8))
        fade = smooth(DUNE_BAND[0], DUNE_BAND[0] + 2.0, r) * (1 - smooth(DUNE_BAND[1] - 15, DUNE_BAND[1], r))
        z = h * crest ** 1.6 * fade
        # montones de ceniza frente a cada puerta (sin camino)
        for g in (0.0, 90.0, 180.0, 270.0):
            da = abs(((degrees(th) - g + 180) % 360) - 180) * radians(1) * r
            z += GATE_HEAP_H * exp(-(da / 9.0) ** 2) * exp(-((r - 216.0) / 6.0) ** 2)
        return z


# ---------------------------------------------------------------------------
# Malla polar
# ---------------------------------------------------------------------------
def ring_radii():
    rr = list(np.arange(R_IN + 1.0, 230.0, DS_NEAR)) + list(np.arange(231.0, R_OUT + 0.01, DS_FAR))
    return [float(r) for r in rr]


def city_boundary():
    me = bpy.data.objects["TRN_City"].data
    bm = bmesh.new()
    bm.from_mesh(me)
    pts = [(v.co.x, v.co.y) for v in bm.verts if v.is_boundary and hypot(v.co.x, v.co.y) > R_IN - 0.5]
    bm.free()
    pts.sort(key=lambda p: atan2(p[1], p[0]))
    return pts


def build_mesh(relief, col, stats):
    inner = city_boundary()
    rings = [[(x, y, 0.0) for x, y in inner]]
    for k, r in enumerate(ring_radii()):
        ds = DS_NEAR if r < 230 else DS_FAR
        n = max(24, int(round(2 * pi * r / ds)))
        off = (0.5 if k % 2 else 0.0) * 2 * pi / n
        ring = []
        for i in range(n):
            a = -pi + off + 2 * pi * i / n
            x, y = r * cos(a), r * sin(a)
            ring.append((x, y, relief.height(x, y)))
        rings.append(ring)
    verts, faces = [], []
    starts = []
    for ring in rings:
        starts.append(len(verts))
        verts += ring
    for k in range(len(rings) - 1):
        A, B = rings[k], rings[k + 1]
        a0, b0 = starts[k], starts[k + 1]
        na, nb = len(A), len(B)
        angA = [atan2(p[1], p[0]) for p in A]
        angB = [atan2(p[1], p[0]) for p in B]
        # arranque comun cerca de -pi
        i = j = 0
        steps = 0
        while steps < na + nb:
            ia, ja = i % na, j % nb
            ia1, ja1 = (i + 1) % na, (j + 1) % nb
            ta = angA[ia1] + (2 * pi if ia1 == 0 else 0.0)
            tb = angB[ja1] + (2 * pi if ja1 == 0 else 0.0)
            if (i < na and (j >= nb or ta <= tb)):
                faces.append((a0 + ia, a0 + ia1, b0 + ja))
                i += 1
            else:
                faces.append((a0 + ia, b0 + ja1, b0 + ja))
                j += 1
            steps += 1
    me = bpy.data.meshes.new("TRN_Exterior")
    me.from_pydata(verts, [], faces)
    me.validate(clean_customdata=False)
    me.update()
    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    for f in bm.faces:
        if f.normal.z < 0:
            f.normal_flip()
    bm.to_mesh(me)
    bm.free()
    me.shade_smooth()
    obj = bpy.data.objects.new("TRN_Exterior", me)
    col.objects.link(obj)
    zs = [v[2] for v in verts]
    stats["exterior_mesh"] = {"rings": len(rings), "verts": len(verts), "tris": len(me.polygons),
                              "z_min": round(min(zs), 2), "z_max": round(max(zs), 2),
                              "seam_verts_with_TRN_City": len(inner)}
    return obj


# ---------------------------------------------------------------------------
# Roca: acantilados y cabezos estratificados
# ---------------------------------------------------------------------------
def rock_material(name, hex0):
    if name in bpy.data.materials:
        bpy.data.materials.remove(bpy.data.materials[name])
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    N, L = m.node_tree.nodes, m.node_tree.links
    b = N["Principled BSDF"]
    a = N.new("ShaderNodeVertexColor")
    a.layer_name = "strata_tone"
    L.new(a.outputs["Color"], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = 0.95
    m["note"] = "gris de estratos en COLOR_0 (strata_tone); sin verde ni ocre"
    return m


def tone(hexa, k):
    c = C.hex_to_linear_rgba(hexa)
    return (c[0] * k, c[1] * k, c[2] * k, 1.0)


def strata_object(name, rings_by_level, col, mat, tones):
    """rings_by_level: lista de anillos (mismo numero de puntos) de abajo a arriba; cierra la tapa."""
    verts, faces, tcol = [], [], []
    n = len(rings_by_level[0])
    for lvl, ring in enumerate(rings_by_level):
        verts += ring
        tcol += [tones[lvl % len(tones)]] * n
    for lvl in range(len(rings_by_level) - 1):
        a, b = lvl * n, (lvl + 1) * n
        for i in range(n):
            j = (i + 1) % n
            faces.append((a + i, a + j, b + j, b + i))
    top = len(rings_by_level) - 1
    faces.append(tuple(top * n + i for i in range(n)))
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    me.validate()
    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.triangulate(bm, faces=bm.faces[:], quad_method="BEAUTY", ngon_method="BEAUTY")
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    bm.to_mesh(me)
    bm.free()
    attr = me.color_attributes.new("strata_tone", "BYTE_COLOR", "POINT")
    flat = []
    for c in tcol[:len(me.vertices)]:
        flat.extend(c)
    attr.data.foreach_set("color", flat)
    pk = me.color_attributes.new("mask_pack", "BYTE_COLOR", "POINT")
    pk.data.foreach_set("color", [v for _ in range(len(me.vertices)) for v in (0.0, 0.0, 1.0, 0.0)])
    me.color_attributes.active_color_name = "mask_pack"
    me.materials.append(mat)
    me.update()
    obj = bpy.data.objects.new(name, me)
    col.objects.link(obj)
    return obj


def build_rocks(relief, col, mat, stats):
    out = []
    for k, R in enumerate(relief.F["rocks"]):
        rng = random.Random(R["seed"])
        n = 24
        base = []
        for i in range(n):
            a = 2 * pi * i / n
            rr = R["rb"] * (1 + 0.28 * nz(cos(a) * 3, sin(a) * 3, 1.0, R["seed"] % 97) + rng.uniform(-0.06, 0.06))
            base.append((R["x"] + rr * cos(a), R["y"] + rr * sin(a)))
        zg = min(relief.height(x, y) for x, y in base) - 1.0
        layers = max(4, int(round(R["h"] / rng.uniform(1.6, 2.6))))
        th = R["h"] / layers
        rings = []
        for j in range(layers + 1):
            t = j / layers
            if R["mesa"]:
                s = 1.0 - 0.18 * t                      # meseta: paredes casi verticales
            else:
                s = 1.0 - 0.62 * t ** 1.4               # cabezo: se afina hacia arriba
            s *= rng.uniform(0.95, 1.03)
            z0 = zg + j * th
            ring_lo = [(R["x"] + (x - R["x"]) * s, R["y"] + (y - R["y"]) * s, z0) for x, y in base]
            if j > 0:
                # repisa: el estrato inferior sobresale un poco (horizontal)
                s2 = s * rng.uniform(0.9, 0.97)
                rings.append([(R["x"] + (x - R["x"]) * s2, R["y"] + (y - R["y"]) * s2, z0) for x, y in base])
            rings.append(ring_lo)
        tones = [tone(ROCK, 1.0), tone(ROCK, 1.0), tone(ROCK_LIGHT, 1.0), tone(ROCK_LIGHT, 1.0)]
        o = strata_object(f"EXT_Rock_{k + 1:02d}", rings, col, mat, tones)
        out.append({"name": o.name, "height_m": round(R["h"], 1), "base_radius_m": round(R["rb"], 1),
                    "layers": layers, "form": "meseta" if R["mesa"] else "cabezo", "tris": len(o.data.polygons),
                    "r": round(hypot(R["x"], R["y"]), 1)})
    stats["exterior_rocks"] = out
    return out


def build_cliffs(relief, col, mat, stats):
    """Muro de roca cerrado r 380-400: perfil escalonado (estratos) con altura 25-40 m segun el angulo."""
    n = 720
    nstr = 9
    rings_by_level = [[] for _ in range(2 * nstr + 2)]
    hs = []
    for i in range(n):
        a = 2 * pi * i / n
        H = CLIFF_H[0] + (CLIFF_H[1] - CLIFF_H[0]) * (0.5 + 0.5 * nz(cos(a) * 4, sin(a) * 4, 1.0, 11))
        hs.append(H)
        r0 = CLIFF_R[0] + 2.0 * nz(cos(a) * 9, sin(a) * 9, 1.0, 12)
        x0, y0 = r0 * cos(a), r0 * sin(a)
        zb = relief.height(x0, y0) - 1.5
        r, z = r0, zb
        lvl = 0
        rings_by_level[lvl].append((r * cos(a), r * sin(a), z))
        lvl += 1
        for k in range(nstr):
            dz = H / nstr * (0.8 + 0.4 * (0.5 + 0.5 * nz(a * 10, k, 1.0, 13)))
            z = min(zb + H, z + dz)
            rings_by_level[lvl].append((r * cos(a), r * sin(a), z))
            lvl += 1
            r = r + 0.4 + 1.0 * (0.5 + 0.5 * nz(a * 7, k, 1.0, 14))        # repisa (retranqueo)
            rings_by_level[lvl].append((r * cos(a), r * sin(a), z))
            lvl += 1
        rings_by_level[lvl].append(((CLIFF_R[1] + 2) * cos(a), (CLIFF_R[1] + 2) * sin(a), z))
    verts, faces, tcol = [], [], []
    L = len(rings_by_level)
    for lvl, ring in enumerate(rings_by_level):
        verts += ring
        tcol += [tone(ROCK_LIGHT if (lvl // 2) % 2 else ROCK, 1.0)] * n
    for lvl in range(L - 1):
        a, b = lvl * n, (lvl + 1) * n
        for i in range(n):
            j = (i + 1) % n
            faces.append((a + i, a + j, b + j, b + i))
    me = bpy.data.meshes.new("EXT_Cliffs")
    me.from_pydata(verts, [], faces)
    me.validate()
    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.triangulate(bm, faces=bm.faces[:])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    # las normales deben mirar hacia la ciudad (hacia dentro / arriba)
    for f in bm.faces:
        c = f.calc_center_median()
        if f.normal.z < -0.1 or (abs(f.normal.z) < 0.5 and f.normal.x * c.x + f.normal.y * c.y > 0):
            f.normal_flip()
    bm.to_mesh(me)
    bm.free()
    attr = me.color_attributes.new("strata_tone", "BYTE_COLOR", "POINT")
    flat = []
    for c in tcol:
        flat.extend(c)
    attr.data.foreach_set("color", flat)
    pk = me.color_attributes.new("mask_pack", "BYTE_COLOR", "POINT")
    pk.data.foreach_set("color", [v for _ in range(len(me.vertices)) for v in (0.0, 0.0, 1.0, 0.0)])
    me.color_attributes.active_color_name = "mask_pack"
    me.materials.append(mat)
    obj = bpy.data.objects.new("EXT_Cliffs", me)
    col.objects.link(obj)
    stats["exterior_cliffs"] = {"r": list(CLIFF_R), "height_m": [round(min(hs), 1), round(max(hs), 1)],
                                "strata": nstr, "segments": n, "tris": len(me.polygons), "closed": True}
    return obj


# ---------------------------------------------------------------------------
# Mascaras y material
# ---------------------------------------------------------------------------
def write_masks(obj, relief, stats):
    me = obj.data
    nv = len(me.vertices)
    co = [v.co.copy() for v in me.vertices]
    slope = [0.0] * nv
    me.calc_loop_triangles()
    for v in me.vertices:
        slope[v.index] = degrees(np.arccos(max(-1.0, min(1.0, v.normal.z))))
    ash, dark, rock, dune = [0.0] * nv, [0.0] * nv, [0.0] * nv, [0.0] * nv
    for i, c in enumerate(co):
        x, y, z = c.x, c.y, c.z
        b = relief.base(x, y) + MEAN_RISE * 0.0
        dep = max(0.0, (relief.base(x, y) + 4.0 * smooth(CLIFF_R[0] - 25, CLIFF_R[0] + 2, hypot(x, y))) - z)
        d_rock = min([hypot(x - R["x"], y - R["y"]) - R["rb"] for R in relief.F["rocks"]] + [1e9])
        rk = max(smooth(30.0, 45.0, slope[i]), 1.0 - smooth(0.0, 4.0, d_rock),
                 smooth(CLIFF_R[0] - 4, CLIFF_R[0] + 1, hypot(x, y)))
        dn = relief.dune(x, y)
        dark[i] = max(0.0, min(1.0, dep / 3.0 + (0.35 if z < -0.8 else 0.0)))
        rock[i] = rk
        dune[i] = max(0.0, min(1.0, dn / 1.5))
        ash[i] = max(0.0, 1.0 - rk)
        _ = b
    nl = len(me.loops)
    lv = [0] * nl
    me.loops.foreach_get("vertex_index", lv)

    def put(name, vals, domain="CORNER"):
        if name in me.color_attributes:
            me.color_attributes.remove(me.color_attributes[name])
        a = me.color_attributes.new(name=name, type="BYTE_COLOR", domain="CORNER")
        flat = []
        for li in range(nl):
            v = vals[lv[li]]
            flat.extend((v, v, v, 1.0))
        a.data.foreach_set("color", flat)
    put("ash_mask", ash)
    put("ash_dark_mask", dark)
    put("rock_mask", rock)
    pk = me.color_attributes.new(name="mask_pack", type="BYTE_COLOR", domain="CORNER")
    flat = []
    for li in range(nl):
        k = lv[li]
        flat.extend((ash[k], dark[k], rock[k], dune[k]))
    pk.data.foreach_set("color", flat)
    me.color_attributes.active_color_name = "mask_pack"
    stats["exterior_masks"] = {"mask_pack": "RGBA = ash, ash_dark, rock, dune (mas claro)",
                               "verts_rock_gt_0_5": sum(1 for v in rock if v > 0.5),
                               "verts_dark_gt_0_5": sum(1 for v in dark if v > 0.5)}


def ash_material():
    name = "MAT_Exterior_Ash"
    if name in bpy.data.materials:
        bpy.data.materials.remove(bpy.data.materials[name])
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    N, L = m.node_tree.nodes, m.node_tree.links
    b = N["Principled BSDF"]
    b.inputs["Roughness"].default_value = 0.97

    def attr(nm):
        a = N.new("ShaderNodeVertexColor")
        a.layer_name = nm
        bw = N.new("ShaderNodeRGBToBW")
        L.new(a.outputs["Color"], bw.inputs[0])
        return bw.outputs[0]

    def mix(fac, a, b2):
        n = N.new("ShaderNodeMix")
        n.data_type = "RGBA"
        L.new(fac, n.inputs["Factor"])
        for sock, val in (("A", a), ("B", b2)):
            if isinstance(val, str):
                n.inputs[sock].default_value = C.hex_to_linear_rgba(val)
            else:
                L.new(val, n.inputs[sock])
        return n.outputs["Result"]
    pk = N.new("ShaderNodeVertexColor")
    pk.layer_name = "mask_pack"
    sep = N.new("ShaderNodeSeparateColor")
    L.new(pk.outputs["Color"], sep.inputs[0])
    c = mix(sep.outputs["Alpha"] if "Alpha" in sep.outputs else sep.outputs[2], ASH, ASH_LIGHT)
    c = mix(attr("ash_dark_mask"), c, ASH_DARK)
    c = mix(attr("rock_mask"), c, ROCK)
    L.new(c, b.inputs["Base Color"])
    m["note"] = "solo grises: #6F6F6F base, #4F4F4F depresiones, #828282 dunas, #5E5E5E roca"
    return m


def dune_light(obj):
    """El canal A (dunas) no sale por SeparateColor: se copia a un atributo propio para la vista previa."""
    me = obj.data
    pk = me.color_attributes["mask_pack"]
    nl = len(me.loops)
    v = [0.0] * (nl * 4)
    pk.data.foreach_get("color", v)
    a = me.color_attributes.new(name="dune_mask", type="BYTE_COLOR", domain="CORNER")
    flat = []
    for li in range(nl):
        d = v[li * 4 + 3]
        flat.extend((d, d, d, 1.0))
    a.data.foreach_set("color", flat)
    me.color_attributes.active_color_name = "mask_pack"


def ash_material_v2():
    name = "MAT_Exterior_Ash"
    m = ash_material()
    N, L = m.node_tree.nodes, m.node_tree.links
    b = N["Principled BSDF"]
    # reconstruye: base -> dunas (claro) -> depresiones (oscuro) -> roca
    for n in list(N):
        if n.type in ("VERTEX_COLOR", "SEPARATE_COLOR", "MIX", "RGBTOBW"):
            N.remove(n)

    def attr(nm):
        a = N.new("ShaderNodeVertexColor")
        a.layer_name = nm
        bw = N.new("ShaderNodeRGBToBW")
        L.new(a.outputs["Color"], bw.inputs[0])
        return bw.outputs[0]

    def mix(fac, a, b2):
        n = N.new("ShaderNodeMix")
        n.data_type = "RGBA"
        L.new(fac, n.inputs["Factor"])
        for sock, val in (("A", a), ("B", b2)):
            if isinstance(val, str):
                n.inputs[sock].default_value = C.hex_to_linear_rgba(val)
            else:
                L.new(val, n.inputs[sock])
        return n.outputs["Result"]
    c = mix(attr("dune_mask"), ASH, ASH_LIGHT)
    c = mix(attr("ash_dark_mask"), c, ASH_DARK)
    c = mix(attr("rock_mask"), c, ROCK)
    L.new(c, b.inputs["Base Color"])
    _ = name
    return m


# ---------------------------------------------------------------------------
# Chunks + export
# ---------------------------------------------------------------------------
def chunks(obj, col_parent, export_path, extra_objs, stats):
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    lines = [C.CHUNK_SIZE * k + C.CHUNK_SIZE / 2 for k in range(-9, 9)]
    for axis in (0, 1):
        for c in lines:
            co = [0.0, 0.0, 0.0]
            no = [0.0, 0.0, 0.0]
            co[axis], no[axis] = c, 1.0
            bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], dist=1e-5,
                                   plane_co=co, plane_no=no)
    bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 3])
    me_b = bpy.data.meshes.new("TMP_ext_bisected")
    bm.to_mesh(me_b)
    bm.free()
    cols = {lod: CH.ensure_collection(f"EXTERIOR_CHUNKS_{lod}", col_parent) for lod in ("LOD0", "LOD1", "LOD2")}
    face_chunk = {}
    for p in me_b.polygons:
        c = p.center
        face_chunk.setdefault((CH.chunk_idx(c.x), CH.chunk_idx(c.y)), []).append(p.index)
    mat = obj.data.materials[0] if obj.data.materials else None
    per = {}
    for (i, j), fs in sorted(face_chunk.items()):
        keep = set(fs)
        bm = bmesh.new()
        bm.from_mesh(me_b)
        bm.faces.ensure_lookup_table()
        bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.index not in keep], context="FACES")
        name = f"TRN_ExteriorChunk_x{i + 8}_y{j + 8}"
        me = bpy.data.meshes.new(name + "_LOD0")
        bm.to_mesh(me)
        bm.free()
        if mat and not me.materials:
            for mm in obj.data.materials:
                me.materials.append(mm)
        o0 = bpy.data.objects.new(name + "_LOD0", me)
        cols["LOD0"].objects.link(o0)
        row = {"LOD0": len(me.polygons)}
        for lod, ratio in (("LOD1", C.LOD_RATIOS["LOD1"]), ("LOD2", C.LOD_RATIOS["LOD2"])):
            lo = CH.make_lod(o0, f"{name}_{lod}", ratio, cols[lod])
            row[lod] = len(lo.data.polygons)
        per[name] = row
    bpy.data.meshes.remove(me_b)
    objs = [o for c in cols.values() for o in c.objects] + list(extra_objs)
    for o in objs:
        if o.type == "MESH":
            o.data.color_attributes.active_color_name = "mask_pack"
    size = CH.export_glb(objs, export_path)
    l0 = [r["LOD0"] for r in per.values()]
    stats["exterior_chunks"] = {"count": len(per), "budget_exterior_per_chunk": C.CHUNK_TRI_BUDGET_EXTERIOR,
                                "lod0_max": max(l0), "lod0_avg": round(sum(l0) / len(l0)),
                                "over_budget": [n for n, r in per.items() if r["LOD0"] > C.CHUNK_TRI_BUDGET_EXTERIOR],
                                "lod_totals": {k: sum(r[k] for r in per.values()) for k in ("LOD0", "LOD1", "LOD2")},
                                "export": os.path.relpath(export_path, os.path.join(HERE, "..", "..")),
                                "bytes": size, "verify": CH.verify_glb(export_path)}
    for c in cols.values():
        c.hide_render = True
        c.hide_viewport = True


def build(scene, stats, export_dir=None):
    col = bpy.data.collections["EXTERIOR"]
    for o in list(col.all_objects):
        bpy.data.objects.remove(o)
    F = features()
    relief = Relief(F)
    obj = build_mesh(relief, col, stats)
    write_masks(obj, relief, stats)
    dune_light(obj)
    obj.data.materials.append(ash_material_v2())
    rmat = rock_material("MAT_Exterior_Rock", ROCK)
    rocks = build_rocks(relief, col, rmat, stats)
    cliffs = build_cliffs(relief, col, rmat, stats)
    stats["exterior_features"] = {
        "wash": {"width_m": list(WASH_W), "depth_m": list(WASH_D), "length_m": round(float(F["wash"][1][-1]), 1),
                 "from_to_deg": [150, -40]},
        "craters": [{"D_m": round(c["D"], 1), "r": round(hypot(c["x"], c["y"]), 1)} for c in F["craters"]],
        "rocks": len(F["rocks"]), "moat": {"r": list(R_MOAT), "bottom_z": MOAT_BOTTOM},
        "dunes": {"band_r": list(DUNE_BAND), "h_m": list(DUNE_H), "gate_heaps_m": GATE_HEAP_H},
        "no_paths": "sin senderos, puentes ni rampas (las puertas dan al talud + montones de ceniza)"}
    if export_dir:
        extra = [o for o in col.objects if o.name.startswith("EXT_")]
        chunks(obj, col, os.path.join(export_dir, "concordia_exterior.glb"), extra, stats)
    return obj
