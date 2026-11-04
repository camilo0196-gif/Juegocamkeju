"""
CONCORDIA - Etapa 02: terreno base de la colina (TRN_City).

Abre concordia_v01.blend, genera TRN_City en la coleccion TERRAIN y guarda
concordia_v02.blend. Ademas escribe docs/reports/stage02_terrain.json con el QA.

Pasos
 1. Grid 424 x 424 m, celdas de 1 m, centrado; se eliminan vertices con r > 212.
 2. Anillos de aristas (bmesh) en cada borde de terraza: dos anillos separados
    1.0 / tan(80) = 0.176 m, solo en sectores diagonales (+ zona de mezcla).
 3. Altura h(r, angulo) de terrain_profile.py + ruido urbano de 5 cm p-p.
 4. Triangulacion fija (BEAUTY), normales hacia arriba.
 5. Vertex groups, color attributes (mascaras) y UV plana sin costuras.

Uso:
    python tools/blender/stage02_terrain.py [--in ...v01.blend] [--out ...v02.blend]
"""

import argparse
import json
import os
import sys
from math import acos, atan2, degrees, radians, sqrt

import bpy  # noqa: I001  (bpy debe importarse antes que bmesh en el modulo pip)
import bmesh
from mathutils import Vector, noise

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
NOISE_SCALE_1 = 12.0          # m, octava principal (ondulacion suave del suelo viejo)
NOISE_SCALE_2 = 4.0           # m, octava fina
NOISE_W2 = 0.30
NOISE_FADE_IN = (60.0, 64.0)  # sin ruido en la plaza (plana)
NOISE_FADE_OUT = (192.0, 196.0)  # sin ruido en la base de muralla ni el talud

RING_SNAP_EPS = 0.05          # vertices a < 5 cm de un anillo se pegan a el
ON_RING_TOL = 1e-5            # tolerancia para considerar un vertice "sobre" el anillo
SNAP_OUTER_BOUNDARY = True    # borde exterior exactamente en r = 212 (Z = 0)

RETAIN_MIN_SLOPE = 70.0       # grados: cara de muro de contencion
STONE_SLOPE = (25.0, 35.0)    # rampa de pendiente para stone_mask (roca en talud)
DIRT_FOOT_DIST = 2.0          # m: tierra acumulada al pie de muros/terraplen
DIRT_NOISE_SCALE = 25.0

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
            bm.faces.new((a[i], a[i + 1], b[i + 1], b[i]))   # CCW visto desde +Z
    stats["grid_verts"] = len(bm.verts)
    stats["grid_faces"] = len(bm.faces)

    R2 = C.TERRAIN_RADIUS ** 2 + 1e-9
    kill = [v for v in bm.verts if v.co.x ** 2 + v.co.y ** 2 > R2]
    bmesh.ops.delete(bm, geom=kill, context="VERTS")
    stats["deleted_verts_r_gt_212"] = len(kill)

    # Limpieza: caras unidas solo por un vertice (bowtie), aristas sueltas, vertices sueltos
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
    bowtie_faces = 0
    for _ in range(20):
        bad = [v for v in bm.verts if v.link_faces and not v.is_manifold]
        if not bad:
            break
        for v in bad:
            if not v.is_valid or v.is_manifold or not v.link_faces:
                continue
            f = max(v.link_faces, key=lambda f: rxy(f.calc_center_median()))
            bmesh.ops.delete(bm, geom=[f], context="FACES_ONLY")
            bowtie_faces += 1
        clean_loose()
    stats["cleanup"] = {"bowtie_faces_removed": bowtie_faces, "wire_edges": n_wire,
                        "loose_verts": n_loose,
                        "non_manifold_verts_left": sum(1 for v in bm.verts if not v.is_manifold)}

    if SNAP_OUTER_BOUNDARY:
        bverts = {v for e in bm.edges if e.is_boundary for v in e.verts}
        moved = 0.0
        for v in bverts:
            r = rxy(v.co)
            k = C.TERRAIN_RADIUS / r
            moved = max(moved, C.TERRAIN_RADIUS - r)
            v.co.x *= k
            v.co.y *= k
        stats["outer_boundary_snap"] = {"verts": len(bverts), "max_move_m": round(moved, 4)}
    return bm


# ---------------------------------------------------------------------------
# 2. Anillos de aristas en los bordes de terraza
# ---------------------------------------------------------------------------
def in_ring_range(x, y, R):
    return T.diag_angular_distance(T.angle_deg(x, y)) <= T.ring_half_angle(R)


def snap_band(bm, r_in, r_out):
    """Pega a r_in / r_out los vertices de la banda [r_in-eps, r_out+eps]."""
    on_in, on_out = set(), set()
    lo, hi = r_in - RING_SNAP_EPS, r_out + RING_SNAP_EPS
    for v in bm.verts:
        r = rxy(v.co)
        if lo <= r <= hi and in_ring_range(v.co.x, v.co.y, r_in):
            target = r_in if (r - r_in) <= (r_out - r) else r_out
            k = target / r
            v.co.x *= k
            v.co.y *= k
            (on_in if target == r_in else on_out).add(v)
    return on_in, on_out


def cut_ring(bm, R, ring):
    """Divide las aristas que cruzan el circulo r=R y conecta los puntos por cara."""
    crossing = []
    for e in bm.edges:
        a, b = e.verts
        da, db = rxy(a.co) - R, rxy(b.co) - R
        if abs(da) < ON_RING_TOL or abs(db) < ON_RING_TOL:
            continue                       # un extremo ya esta en el anillo (pegado)
        if da * db < 0.0:
            crossing.append(e)
    for e in crossing:
        a, b = e.verts
        pa, pb = a.co.xy, b.co.xy
        d = pb - pa
        A = d.dot(d)
        B = 2.0 * pa.dot(d)
        Cq = pa.dot(pa) - R * R
        disc = max(B * B - 4.0 * A * Cq, 0.0)
        t = None
        for cand in ((-B + sqrt(disc)) / (2.0 * A), (-B - sqrt(disc)) / (2.0 * A)):
            if 0.0 < cand < 1.0:
                t = cand
                break
        if t is None:
            continue
        p = pa + d * t
        if not in_ring_range(p.x, p.y, R):
            continue
        _ne, nv = bmesh.utils.edge_split(e, a, t)
        k = R / p.length
        nv.co = (p.x * k, p.y * k, 0.0)
        ring.add(nv)

    verts = sorted(ring, key=lambda v: atan2(v.co.y, v.co.x))
    connected = missed = 0
    for a, b in zip(verts, verts[1:]):
        if (a.co.xy - b.co.xy).length > 2.5:          # hueco entre arcos (otro sector)
            continue
        if any(e.other_vert(a) is b for e in a.link_edges):
            continue
        common = set(a.link_faces) & set(b.link_faces)
        if not common:
            missed += 1
            continue
        bmesh.utils.face_split(next(iter(common)), a, b)
        connected += 1
    return {"R": round(R, 4), "ring_verts": len(ring), "new_edges": connected, "missed": missed}


def insert_rings(bm, stats):
    out = []
    for r_in, r_out in T.ring_pairs():
        on_in, on_out = snap_band(bm, r_in, r_out)
        out.append(cut_ring(bm, r_in, on_in))
        out.append(cut_ring(bm, r_out, on_out))
    stats["rings"] = out


# ---------------------------------------------------------------------------
# 3. Alturas + ruido
# ---------------------------------------------------------------------------
def noise_mask(r):
    return T.smoothstep(*NOISE_FADE_IN, r) * (1.0 - T.smoothstep(*NOISE_FADE_OUT, r))


def apply_heights(bm, stats):
    off = Vector((SEED * 0.1371, SEED * 0.7313, SEED * 0.0193))
    raw = {}
    for v in bm.verts:
        r = rxy(v.co)
        if noise_mask(r) > 0.0:
            p = Vector((v.co.x, v.co.y, 0.0))
            raw[v] = (noise.noise(p / NOISE_SCALE_1 + off, noise_basis="PERLIN_NEW")
                      + NOISE_W2 * noise.noise(p / NOISE_SCALE_2 - off, noise_basis="PERLIN_NEW"))
    lo, hi = min(raw.values()), max(raw.values())
    mid, span = (lo + hi) / 2.0, (hi - lo)
    for v in bm.verts:
        z = T.height(v.co.x, v.co.y)
        if v in raw:
            z += noise_mask(rxy(v.co)) * (raw[v] - mid) / span * C.TERRAIN_NOISE_PP
        v.co.z = z
    stats["noise"] = {"seed": SEED, "pp_target_m": C.TERRAIN_NOISE_PP,
                      "scales_m": [NOISE_SCALE_1, NOISE_SCALE_2]}


# ---------------------------------------------------------------------------
# 5. Datos de vertice
# ---------------------------------------------------------------------------
def slope_deg(nz):
    return degrees(acos(max(-1.0, min(1.0, nz))))


def is_retaining_face(r, th, slope):
    return (slope >= RETAIN_MIN_SLOPE and C.TERRACE_START_R - 1.0 <= r <= C.WALL_BASE_R[1] + 0.5
            and T.diag_weight(r, th) > 0.0)


def write_vertex_data(me):
    nv = len(me.vertices)
    co = [v.co.copy() for v in me.vertices]
    rr = [rxy(c) for c in co]
    th = [T.angle_deg(c.x, c.y) for c in co]
    wd = [T.diag_weight(rr[i], th[i]) if rr[i] > 1e-6 else 0.0 for i in range(nv)]

    # --- Vertex groups
    obj = bpy.data.objects[OBJ_NAME]
    vg = {name: obj.vertex_groups.new(name=name) for name in VGROUPS}
    tid_max = float(C.TERRACE_COUNT)
    for i in range(nv):
        r, w = rr[i], wd[i]
        if r <= C.PLAZA_RADIUS + 1e-6:
            vg["plaza"].add([i], 1.0, "REPLACE")
        if C.PLAZA_RADIUS < r <= C.DIAG_LANDMARK_END and w > 0.0:
            vg["landmarks"].add([i], w, "REPLACE")
        if C.PLAZA_RADIUS < r < C.CARD_EMBANK_END and w < 1.0:
            vg[CARD_VG[T.nearest_cardinal(th[i])]].add([i], 1.0 - w, "REPLACE")
        if C.DIAG_LANDMARK_END < r < C.CARD_EMBANK_END and w > 0.0:
            vg["sector_moradas"].add([i], w, "REPLACE")
        k = T.terrace_index(r)
        if k and w >= 0.5:
            vg["terraza_id"].add([i], k / tid_max, "REPLACE")
        if C.WALL_BASE_R[0] <= r < C.WALL_BASE_R[1] - 1e-6:
            vg["base_muralla"].add([i], 1.0, "REPLACE")
        if r >= C.WALL_BASE_R[1] - 1e-6:
            vg["talud"].add([i], 1.0, "REPLACE")

    # --- Mascaras por vertice
    vslope = [slope_deg(v.normal.z) for v in me.vertices]
    off = Vector((SEED * 0.311, SEED * 0.177, 3.7))
    jumps_in = [R - T.STEP_RUN / 2.0 for R in T.terrace_jumps()]
    stone_v, dirt_v = [0.0] * nv, [0.0] * nv
    for i in range(nv):
        r, w = rr[i], wd[i]
        stone = max(1.0 if r <= C.PLAZA_RADIUS else 0.0,
                    1.0 if C.WALL_BASE_R[0] <= r < C.WALL_BASE_R[1] else 0.0,
                    T.smoothstep(*STONE_SLOPE, vslope[i]))
        foot = 0.0
        for Rj in jumps_in:                       # pie de muros de terraza (lado bajo)
            dist = Rj - r
            if 0.0 <= dist <= DIRT_FOOT_DIST:
                foot = max(foot, w * (1.0 - T.smoothstep(0.0, DIRT_FOOT_DIST, dist)))
        dist = C.CARD_FLAT_END - r                # pie del terraplen cardinal
        if 0.0 <= dist <= DIRT_FOOT_DIST:
            foot = max(foot, (1.0 - w) * (1.0 - T.smoothstep(0.0, DIRT_FOOT_DIST, dist)))
        n = noise.noise(Vector((co[i].x, co[i].y, 0.0)) / DIRT_NOISE_SCALE + off,
                        noise_basis="PERLIN_NEW")
        dirt = max(0.0, min(1.0, 0.30 + 0.35 * n + 0.60 * foot))
        stone_v[i] = stone
        dirt_v[i] = dirt * (1.0 - stone)

    # --- Por cara
    npoly = len(me.polygons)
    ret_face = [False] * npoly
    for p in me.polygons:
        c = p.center
        ret_face[p.index] = is_retaining_face(rxy(c), T.angle_deg(c.x, c.y), slope_deg(p.normal.z))

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
        return a

    ret_vals = [1.0 if ret_face[loop_f[li]] else 0.0 for li in range(nl)]
    stone_vals = [1.0 if ret_face[loop_f[li]] else stone_v[loop_v[li]] for li in range(nl)]
    dirt_vals = [0.0 if ret_face[loop_f[li]] else dirt_v[loop_v[li]] for li in range(nl)]
    color_attr("retaining_mask", ret_vals)
    color_attr("dirt_mask", dirt_vals)
    color_attr("stone_mask", stone_vals)
    me.color_attributes.active_color_name = "retaining_mask"
    me.color_attributes.render_color_index = 0

    # --- UV plana normalizada 0..1 sobre los 424 m (una sola isla, sin costuras)
    uv = me.uv_layers.new(name="UVMap")
    half = C.TERRAIN_GRID_SIZE / 2.0
    flat = []
    for li in range(nl):
        c = co[loop_v[li]]
        flat.extend(((c.x + half) / C.TERRAIN_GRID_SIZE, (c.y + half) / C.TERRAIN_GRID_SIZE))
    uv.data.foreach_set("uv", flat)

    return {"retaining_faces": sum(ret_face), "vgroup_counts": {
        name: sum(1 for v in me.vertices if any(g.group == vg[name].index for g in v.groups))
        for name in VGROUPS}}, ret_face


# ---------------------------------------------------------------------------
# QA de pendientes
# ---------------------------------------------------------------------------
WALKABLE = {"plaza", "descenso_60_90", "distrito_90_185", "hitos_90_95",
            "terrazas_105_189", "plataforma_189_203"}
STAIRS = {"terraplen_185_196", "escalinata_95_105"}


BLEND_MARGIN = C.TERRAIN_CELL * 0.75   # media celda: caras que tocan la franja de mezcla


def blend_side(r, th):
    """'diag', 'card' o 'mix' segun la distancia en arco al borde de sector."""
    s = r * radians(C.MORADA_HALF_ANGLE - T.diag_angular_distance(th))
    lim = C.SECTOR_BLEND_WIDTH / 2.0 + BLEND_MARGIN
    return "diag" if s > lim else ("card" if s < -lim else "mix")


def classify(r, th, wd, retaining):
    if r <= C.PLAZA_RADIUS:
        return "Plaza", "plaza"
    if r >= C.WALL_BASE_R[1]:
        return "Talud", "talud_204_212"
    side = blend_side(r, th)
    if side == "diag":
        sec = T.nearest_diagonal(th)
        if retaining:
            return sec, "muro_contencion"
        if r <= C.RING_DESCENT[1]:
            return sec, "descenso_60_90"
        if r <= C.DIAG_LANDMARK_END:
            return sec, "hitos_90_95"
        if r <= C.DIAG_RAMP_END:
            return sec, "escalinata_95_105"
        if r <= C.TERRACE_END_R:
            return sec, "terrazas_105_189"
        return sec, "plataforma_189_203"
    if side == "card":
        sec = T.nearest_cardinal(th)
        if r <= C.RING_DESCENT[1]:
            return sec, "descenso_60_90"
        if r <= C.CARD_FLAT_END:
            return sec, "distrito_90_185"
        if r <= C.CARD_EMBANK_END:
            return sec, "terraplen_185_196"
        return sec, "base_muralla_196_204"
    if r <= C.RING_DESCENT[1]:
        return T.nearest_cardinal(th), "descenso_60_90"   # perfil comun: no hay mezcla real
    return f"Mezcla_{T.nearest_cardinal(th)}_{T.nearest_diagonal(th)}", (
        "muro_contencion" if retaining else "borde_lateral")


def slope_report(me, ret_face):
    zones = {}
    stretched = 0
    jumps = T.terrace_jumps()
    for p in me.polygons:
        c = p.center
        r, th = rxy(c), T.angle_deg(c.x, c.y)
        wd = T.diag_weight(r, th)
        s = slope_deg(p.normal.z)
        key = classify(r, th, wd, ret_face[p.index])
        zones.setdefault(key, []).append(s)
        if wd > 0.99 and any(abs(r - R) < 1.0 for R in jumps):
            zs = [me.vertices[i].co.z for i in p.vertices]
            if max(zs) - min(zs) > 0.3 and s < RETAIN_MIN_SLOPE:
                stretched += 1
    table = {}
    for (sec, sub), vals in sorted(zones.items()):
        vals.sort()
        n = len(vals)
        table[f"{sec}/{sub}"] = {
            "faces": n, "max": round(vals[-1], 2), "p99": round(vals[int(0.99 * (n - 1))], 2),
            "mean": round(sum(vals) / n, 2),
            "gt5": sum(1 for v in vals if v > C.WALK_SLOPE_MAX),
            "gt8": sum(1 for v in vals if v > C.STAIR_SLOPE)}
    per_sector = {}
    for key, d in table.items():
        sec, sub = key.split("/")
        if sub in WALKABLE:
            cur = per_sector.setdefault(sec, {"walk_max": 0.0, "walk_gt5": 0, "zone_of_max": ""})
            if d["max"] > cur["walk_max"]:
                cur["walk_max"], cur["zone_of_max"] = d["max"], sub
            cur["walk_gt5"] += d["gt5"]
    return table, per_sector, stretched


def geometry_qa(bm, me):
    qa = {}
    qa["verts"] = len(me.vertices)
    qa["tris"] = len(me.polygons)
    qa["all_tris"] = all(len(p.vertices) == 3 for p in me.polygons)
    nz = [p.normal.z for p in me.polygons]
    qa["min_normal_z"] = round(min(nz), 4)
    qa["faces_normal_down_or_vertical"] = sum(1 for z in nz if z <= 0.0)
    qa["degenerate_faces_area_lt_1e-6"] = sum(1 for p in me.polygons if p.area < 1e-6)
    qa["min_face_area_m2"] = round(min(p.area for p in me.polygons), 6)
    dbl = bmesh.ops.find_doubles(bm, verts=bm.verts, dist=1e-4)["targetmap"]
    qa["duplicate_verts_1e-4"] = len(dbl)
    qa["non_manifold_edges"] = sum(1 for e in bm.edges if len(e.link_faces) > 2)
    qa["boundary_edges"] = sum(1 for e in bm.edges if e.is_boundary)
    qa["wire_edges"] = sum(1 for e in bm.edges if e.is_wire)
    zs = [v.co.z for v in me.vertices]
    qa["z_min"], qa["z_max"] = round(min(zs), 4), round(max(zs), 4)
    rs = [rxy(v.co) for v in me.vertices]
    qa["r_max"] = round(max(rs), 4)
    # ruido real: desviacion respecto al perfil analitico
    dev = [v.co.z - T.height(v.co.x, v.co.y) for v in me.vertices]
    qa["noise_dev_min_m"], qa["noise_dev_max_m"] = round(min(dev), 4), round(max(dev), 4)
    return qa


def level_checks(obj):
    """Raycast vertical sobre la malla en puntos clave y compara con la cota pedida."""
    from mathutils.bvhtree import BVHTree
    bvh = BVHTree.FromObject(obj, bpy.context.evaluated_depsgraph_get())
    pts = [("plaza centro", 0, 0, 8.0), ("plaza borde r59.5 E", 0, 59.5, None),
           ("r90 Mercado", 90, 90, 6.0), ("Mercado r165", 90, 165, 4.5),
           ("Mercado r175", 90, 175, 4.5), ("Mercado r185", 90, 185, 4.5),
           ("Mercado r196", 90, 196, 6.0), ("Mercado r200 (puerta)", 90, 200, 6.0),
           ("hitos NE r92", 45, 92, 6.0), ("Morada NE r105", 45, 105, 4.5)]
    for k in range(1, 7):
        pts.append((f"terraza {k} NE (centro)", 45, C.TERRACE_START_R + C.TERRACE_DEPTH * (k - 0.5),
                    C.Z_MORADAS_MIN + (k - 1) * C.TERRACE_RISE))
    pts += [("Morada NE r200", 45, 200, 9.5), ("talud r208 E", 0, 208, None),
            ("borde r211.9 E", 0, 211.9, None)]
    out = []
    for name, ang, r, want in pts:
        x, y, _ = C.polar(ang, r)
        hit = bvh.ray_cast(Vector((x, y, 100.0)), Vector((0, 0, -1)))
        z = hit[0].z if hit[0] else None
        exp = want if want is not None else T.height(x, y)
        out.append({"point": name, "z_mesh": None if z is None else round(z, 4),
                    "z_expected": round(exp, 4), "diff": None if z is None else round(z - exp, 4)})
    return out


# ---------------------------------------------------------------------------
def main():
    args = parse_args()
    bpy.ops.wm.open_mainfile(filepath=args.inp)
    scene = bpy.context.scene
    if OBJ_NAME in bpy.data.objects:
        bpy.data.objects.remove(bpy.data.objects[OBJ_NAME])
    if OBJ_NAME in bpy.data.meshes:
        bpy.data.meshes.remove(bpy.data.meshes[OBJ_NAME])

    stats = {}
    bm = build_grid(stats)
    insert_rings(bm, stats)
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
    obj = bpy.data.objects.new(OBJ_NAME, me)
    bpy.data.collections["TERRAIN"].objects.link(obj)
    obj["generator"] = "tools/blender/stage02_terrain.py"
    obj["seed"] = SEED
    obj["terraza_id_encoding"] = "weight = id / 6 (id 1..6, 0 = sin terraza)"

    vdata, ret_face = write_vertex_data(me)
    stats.update(vdata)
    stats["geometry"] = geometry_qa(bm, me)
    table, per_sector, stretched = slope_report(me, ret_face)
    stats["stretched_step_faces"] = stretched
    stats["slope_by_zone"] = table
    stats["slope_walkable_max_by_sector"] = per_sector
    stats["level_checks"] = level_checks(obj)
    bm.free()

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    bpy.context.preferences.filepaths.save_version = 0      # sin .blend1
    bpy.ops.wm.save_as_mainfile(filepath=args.out, compress=True)
    os.makedirs(os.path.dirname(args.report), exist_ok=True)
    with open(args.report, "w") as fh:
        json.dump(stats, fh, indent=1, ensure_ascii=False)
    print(json.dumps({k: v for k, v in stats.items() if k not in ("slope_by_zone",)}, indent=1,
                     ensure_ascii=False))
    print("--- slope_by_zone (max / p99 / caras>5 / caras>8)")
    for k, d in table.items():
        print(f"{k:42s} {d['max']:6.2f} {d['p99']:6.2f} {d['gt5']:6d} {d['gt8']:6d}  n={d['faces']}")
    print("saved:", args.out)


if __name__ == "__main__":
    main()
