"""
CONCORDIA - Etapa 03: Plaza del Portal (solo terreno, pedestales, bases y marcadores).

Referencias
- Piazza del Campo (Siena): suelo de losas con bandas radiales claras de travertino que
  convergen en el centro; plaza abierta rodeada de edificios (proporcion: anillo de
  edificios de 12-16 m de fondo frente a un vacio de ~100 m).
- Torre de Hercules (A Coruna): torre de piedra maciza sobre un basamento en lo alto de
  la colina -> basamento circular de 14 m nivelado para la Torre del Faro.

Lo que hace
 1. TRN_City (malla maestra): cortes de anillos (cada 6 m) y de las 8 bandas de travertino
    para que las mascaras sean nitidas; ondulaciones de +-3 cm en el 20 % de las celdas
    de 2 m; remiendos; surcos de los 4 canales de luz (0.20 x 0.05 m).
    Mascaras (color por esquina): slab_ring_id, travertine_band, repair_mask, magic_glow_mask.
    UV2 "UVMasks" (para Godot): x = magic_glow_mask, y = ring_id + 16*travertine + 32*repair.
 2. Piezas (coleccion PLAZA): TRN_Atrio, TRN_PortalPedestal, TRN_Runestones,
    TRN_DescentPedestals, TRN_PlazaParcel_01..08, TRN_Pad_<Hito>, TRN_LightCanals.
 3. Marcadores (PLAZA/PLAZA_MARKERS): Empties. Su eje local +Y apunta al centro de la
    plaza (en Godot, -Z = "adelante" mira al Portal).
"""

import hashlib
import os
import sys
from math import atan2, ceil, cos, degrees, pi, radians, sin, sqrt

import bpy  # noqa: I001
import bmesh
from mathutils import Vector
from mathutils.bvhtree import BVHTree

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import concordia_const as C  # noqa: E402
import terrain_profile as T  # noqa: E402
import stage02_terrain as S2  # noqa: E402
import stage02_structures as ST  # noqa: E402

SEED = 3301
COL_PLAZA = "PLAZA"
COL_MARKERS = "PLAZA_MARKERS"
MAT_MAGIC = "MAT_Magic_ShardBlue"
MAT_RUNE = "MAT_Stone_Runestone"
RUNE_HEX = "#77746D"               # piedra gris oscura (provisional)
EMISSION_STRENGTH = 4.0

Z0 = C.Z_PLAZA
ATRIO_TOP = Z0 + C.ATRIO_RISE                   # 8.6
PED_TOP = Z0 + C.PORTAL_PEDESTAL_RISE           # 8.9
STEP_TREAD = 0.35
ATRIO_RISERS = 4                                # peldanos perimetrales del Atrio (no pedidos: acceso)
PED_RISERS = 2
R_ATRIO_OUT = C.ATRIO_R + (ATRIO_RISERS - 1) * STEP_TREAD     # 16.05
R_PED_OUT = C.PORTAL_PEDESTAL_R + (PED_RISERS - 1) * STEP_TREAD  # 6.35
LATHE_SEG = 128
SKIRT = 0.3

CANAL_AXIS = 45.0                               # del Portal al Faro por la calle diagonal NE
CANAL_OFFSETS = (-1.8, -0.6, 0.6, 1.8)          # m: dentro de la calle de 6 m, la banda de travertino en medio
CANAL_INSET = 0.01                              # pared del surco ~79 grados
CANAL_END = 0.02
CANAL_SNAP = 0.003

FIRST_RUNESTONE_DEG = 90.0                      # primera piedra al Norte, sentido horario
FIRST_PEDESTAL_DEG = 90.0                       # pedestal 01 (piso 1) al Norte, sentido horario
FIRST_BUILDING_DEG = 22.5                       # parcelas entre los 8 ejes, sentido antihorario
GLOW_PORTAL = (C.PORTAL_PEDESTAL_R, 24.0)       # degradado del Portal (m)
GLOW_CANAL = (0.10, 1.5)                        # degradado de los canales (m)


# ---------------------------------------------------------------------------
def frame(axis_deg):
    a = radians(axis_deg)
    return Vector((cos(a), sin(a), 0.0)), Vector((-sin(a), cos(a), 0.0))


def to_uv(x, y, axis_deg):
    return T.axis_frame(x, y, axis_deg)


def from_uv(u, v, axis_deg):
    e, n = frame(axis_deg)
    p = e * u + n * v
    return p.x, p.y


def u_at(R, v):
    return sqrt(max(0.0, R * R - v * v))


FARO_ANG, FARO_R = C.LANDMARK_PADS["Faro"][0], C.LANDMARK_PADS["Faro"][1]
FARO_RAD = C.LANDMARK_PADS["Faro"][3][0] / 2.0


def canal_u_range_terrain(c):
    u0 = u_at(R_ATRIO_OUT, c) - 0.05                        # bajo el ultimo peldano
    u1 = FARO_R - sqrt(FARO_RAD ** 2 - c * c) + 0.05        # bajo el basamento del Faro
    return u0, u1


def hash01(*key):
    h = hashlib.md5(("%d:" % SEED + ":".join(str(k) for k in key)).encode()).digest()
    return int.from_bytes(h[:4], "little") / 2 ** 32


def slab_cell(r, th):
    k = int(r // C.PLAZA_SLAB_RING)
    j = int((r - k * C.PLAZA_SLAB_RING) // C.PLAZA_BUMP_CELL)
    r_mid = k * C.PLAZA_SLAB_RING + (j + 0.5) * C.PLAZA_BUMP_CELL
    nseg = max(4, round(2 * pi * r_mid / C.PLAZA_BUMP_CELL))
    t = (th / 360.0) * nseg
    s = int(t) % nseg
    fu = (r - k * C.PLAZA_SLAB_RING - j * C.PLAZA_BUMP_CELL) / C.PLAZA_BUMP_CELL
    return (k, j, s), fu, t - int(t)


def band_distance(x, y):
    """Distancia a la banda radial mas cercana (semirrecta desde el centro)."""
    best = 1e9
    for a in C.PLAZA_BAND_ANGLES:
        u, v = to_uv(x, y, a)
        if u >= 0:
            best = min(best, abs(v))
    return best


def canal_distance(x, y):
    u, v = to_uv(x, y, CANAL_AXIS)
    if u < R_PED_OUT - 1 or u > FARO_R:
        return 1e9
    return min(abs(v - c) for c in CANAL_OFFSETS)


def in_canal_corridor(x, y, margin=0.5):
    u, v = to_uv(x, y, CANAL_AXIS)
    return u > 0 and abs(v) <= max(abs(c) for c in CANAL_OFFSETS) + C.LIGHT_CANAL_WIDTH / 2 + margin


def groove_offset(x, y):
    u, v = to_uv(x, y, CANAL_AXIS)
    hw = C.LIGHT_CANAL_WIDTH / 2
    depth = 0.0
    for c in CANAL_OFFSETS:
        dv = abs(v - c)
        if dv > hw:
            continue
        u0, u1 = canal_u_range_terrain(c)
        if u < u0 or u > u1:
            continue
        wv = 1.0 if dv <= hw - CANAL_INSET else (hw - dv) / CANAL_INSET
        wu = min(1.0, (u - u0) / CANAL_END, (u1 - u) / CANAL_END)
        depth = max(depth, wv * max(0.0, wu))
    return -C.LIGHT_CANAL_DEPTH * depth


def slab_offset(x, y):
    """Ondulaciones (+-3 cm en el 20 % de las celdas de 2 m) y remiendos."""
    r = sqrt(x * x + y * y)
    if r < R_ATRIO_OUT + 0.3 or r > C.PLAZA_RADIUS - 0.3:
        return 0.0, 0.0
    if in_canal_corridor(x, y) or band_distance(x, y) < 0.5:
        return 0.0, 0.0
    cell, fu, fv = slab_cell(r, T.angle_deg(x, y))
    w = sin(pi * fu) * sin(pi * fv)
    off, rep = 0.0, 0.0
    if hash01("bump", *cell) < C.PLAZA_BUMP_FRACTION:
        off += (1 if hash01("sign", *cell) < 0.5 else -1) * C.PLAZA_BUMP_AMP * w
    if hash01("repair", *cell) < C.PLAZA_REPAIR_FRACTION:
        rep = 1.0
        off += (1 if hash01("rsign", *cell) < 0.5 else -1) * C.PLAZA_REPAIR_AMP * min(1.0, 2.5 * w)
    return off, rep


def repair_cell(x, y):
    r = sqrt(x * x + y * y)
    if r < R_ATRIO_OUT or r > C.PLAZA_RADIUS:
        return 0.0
    cell, _fu, _fv = slab_cell(r, T.angle_deg(x, y))
    return 1.0 if hash01("repair", *cell) < C.PLAZA_REPAIR_FRACTION else 0.0


def glow_value(x, y):
    r = sqrt(x * x + y * y)
    g = 1.0 - T.smoothstep(*GLOW_PORTAL, r)
    d = canal_distance(x, y)
    if d < 1e8:
        g = max(g, 1.0 - T.smoothstep(*GLOW_CANAL, d))
    return g


# ---------------------------------------------------------------------------
# 1. Terreno de la plaza (sobre la malla maestra)
# ---------------------------------------------------------------------------
def circle_pts(R, step=0.25):
    n = max(16, int(ceil(2 * pi * R / step)))
    return [(R * cos(2 * pi * i / n), R * sin(2 * pi * i / n)) for i in range(n + 1)]


def plaza_terrain(obj, stats):
    me = obj.data
    bm = bmesh.new()
    bm.from_mesh(me)
    locked = set()
    knives = []
    k0 = int(ceil(R_ATRIO_OUT / C.PLAZA_SLAB_RING))
    for k in range(k0, int(C.PLAZA_RADIUS / C.PLAZA_SLAB_RING) + 1):
        R = k * C.PLAZA_SLAB_RING
        knives.append(S2.knife_polyline(bm, circle_pts(R), locked, f"ring_{R:.0f}"))
    hb = C.PLAZA_BAND_WIDTH / 2
    for a in C.PLAZA_BAND_ANGLES:
        for v in (-hb, hb):
            pts = [from_uv(u, v, a) for u in (R_ATRIO_OUT - 0.5, C.PLAZA_RADIUS + 0.3)]
            knives.append(S2.knife_polyline(bm, pts, locked, f"band_{a:.0f}_{v:+.1f}"))
    hw = C.LIGHT_CANAL_WIDTH / 2
    for c in CANAL_OFFSETS:
        u0, u1 = canal_u_range_terrain(c)
        for v in (c - hw, c - hw + CANAL_INSET, c + hw - CANAL_INSET, c + hw):
            pts = [from_uv(u, v, CANAL_AXIS) for u in (u0 - 0.02, u1 + 0.02)]
            knives.append(S2.knife_polyline(bm, pts, locked, f"canal_{c:+.1f}_v{v:+.2f}", snap_eps=CANAL_SNAP))
        for u in (u0, u0 + CANAL_END, u1 - CANAL_END, u1):
            pts = [from_uv(u, v, CANAL_AXIS) for v in (c - hw - 0.02, c + hw + 0.02)]
            knives.append(S2.knife_polyline(bm, pts, locked, f"canal_{c:+.1f}_u{u:.2f}", snap_eps=CANAL_SNAP))
    bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 3], quad_method="BEAUTY",
                          ngon_method="BEAUTY")
    moved = 0
    for v in bm.verts:
        x, y = v.co.x, v.co.y
        if x * x + y * y > (FARO_R + FARO_RAD + 2) ** 2:
            continue
        off, _rep = slab_offset(x, y)
        g = groove_offset(x, y)
        if off or g:
            v.co.z += off + g
            moved += 1
    bm.normal_update()
    bm.to_mesh(me)
    bm.free()
    me.update()
    me.set_sharp_from_angle(angle=radians(S2.SHARP_ANGLE))
    stats["plaza_terrain"] = {"knives": len(knives), "knife_verts": sum(k["verts"] for k in knives),
                              "knife_missed": sum(k.get("missed", 0) for k in knives), "verts_offset": moved,
                              "tris_after": len(me.polygons)}
    write_plaza_masks(me, stats)


def write_plaza_masks(me, stats):
    nl = len(me.loops)
    loop_v = [0] * nl
    me.loops.foreach_get("vertex_index", loop_v)
    face_vals = []
    for p in me.polygons:
        c = p.center
        r = sqrt(c.x * c.x + c.y * c.y)
        ring = int(r // C.PLAZA_SLAB_RING) + 1 if r < C.PLAZA_RADIUS else 0
        trav = 1.0 if r <= C.PLAZA_RADIUS and band_distance(c.x, c.y) <= C.PLAZA_BAND_WIDTH / 2 else 0.0
        rep = 0.0 if trav else repair_cell(c.x, c.y)
        face_vals.append((ring, trav, rep))
    glow_v = [glow_value(v.co.x, v.co.y) for v in me.vertices]
    loop_f = [0] * nl
    for p in me.polygons:
        for li in range(p.loop_start, p.loop_start + p.loop_total):
            loop_f[li] = p.index
    for name in ("slab_ring_id", "travertine_band", "repair_mask", "magic_glow_mask"):
        if name in me.color_attributes:
            me.color_attributes.remove(me.color_attributes[name])

    def put(name, vals):
        a = me.color_attributes.new(name=name, type="BYTE_COLOR", domain="CORNER")
        flat = []
        for val in vals:
            flat.extend((val, val, val, 1.0))
        a.data.foreach_set("color", flat)

    put("slab_ring_id", [face_vals[loop_f[i]][0] / 10.0 for i in range(nl)])
    put("travertine_band", [face_vals[loop_f[i]][1] for i in range(nl)])
    put("repair_mask", [face_vals[loop_f[i]][2] for i in range(nl)])
    put("magic_glow_mask", [glow_v[loop_v[i]] for i in range(nl)])
    if "UVMasks" in me.uv_layers:
        me.uv_layers.remove(me.uv_layers["UVMasks"])
    uv = me.uv_layers.new(name="UVMasks")
    flat = []
    for i in range(nl):
        ring, trav, rep = face_vals[loop_f[i]]
        flat.extend((glow_v[loop_v[i]], ring + 16 * trav + 32 * rep))
    uv.data.foreach_set("uv", flat)
    me.uv_layers.active_index = 0
    me.color_attributes.active_color_name = "mask_pack" if "mask_pack" in me.color_attributes else "retaining_mask"
    in_plaza = [fv for fv in face_vals if fv[0] > 0]
    stats["plaza_masks"] = {
        "slab_ring_id": "valor = anillo / 10 (anillo 1..10 = r 0-6 ... 54-60; 0 fuera)",
        "uv2_UVMasks": "x = magic_glow_mask; y = anillo + 16*travertino + 32*remiendo",
        "faces_plaza": len(in_plaza), "faces_travertine": sum(1 for f in in_plaza if f[1]),
        "faces_repair": sum(1 for f in in_plaza if f[2]),
    }


# ---------------------------------------------------------------------------
# 2. Piezas
# ---------------------------------------------------------------------------
def lathe(mb, profile, seg=LATHE_SEG, closed=True):
    """Revolucion de un perfil [(r, z)] (r = 0 => vertice en el eje). closed=False no une
    el ultimo punto con el primero."""
    rings = []
    verts = []
    for r, z in profile:
        if r < 1e-9:
            rings.append([len(verts)])
            verts.append((0.0, 0.0, z))
        else:
            idx = []
            for i in range(seg):
                a = 2 * pi * i / seg
                idx.append(len(verts))
                verts.append((r * cos(a), r * sin(a), z))
            rings.append(idx)
    faces = []
    n = len(rings)
    for k in range(n if closed else n - 1):
        A, B = rings[k], rings[(k + 1) % n]
        if len(A) == 1 and len(B) == 1:
            continue
        for i in range(seg):
            j = (i + 1) % seg
            if len(A) == 1:
                faces.append((A[0], B[i], B[j]))
            elif len(B) == 1:
                faces.append((A[i], A[j], B[0]))
            else:
                faces.append((A[i], A[j], B[j], B[i]))
    mb.add(verts, faces)


def atrio_object(col, mat, stats):
    lvl = []
    z_out = T.prof_common(R_ATRIO_OUT)
    riser = (ATRIO_TOP - z_out) / ATRIO_RISERS
    zb = z_out - 0.5
    # cara superior (sola, para cortar los surcos sin tocar el resto del solido)
    top = [(0.0, ATRIO_TOP)] + [(r, ATRIO_TOP) for r in (2.0, 4.0, R_PED_OUT, 8.0, 10.0, 12.0, 14.0,
                                                          C.ATRIO_R - CANAL_END, C.ATRIO_R)]
    mt = ST.MeshBuilder()
    lathe(mt, top, closed=False)
    bm = bmesh.new()
    vs = [bm.verts.new(p) for p in mt.verts]
    for f in mt.faces:
        bm.faces.new([vs[i] for i in f])
    locked = set()
    hw = C.LIGHT_CANAL_WIDTH / 2
    for c in CANAL_OFFSETS:
        ua, ub = u_at(R_PED_OUT + CANAL_END, c), u_at(C.ATRIO_R - CANAL_END, c)
        for v in (c - hw, c - hw + CANAL_INSET, c + hw - CANAL_INSET, c + hw):
            S2.knife_polyline(bm, [from_uv(u, v, CANAL_AXIS) for u in (ua - 0.01, ub + 0.01)], locked,
                              snap_eps=CANAL_SNAP)
        for u in (ua, ua + CANAL_END, ub - CANAL_END, ub):
            S2.knife_polyline(bm, [from_uv(u, v, CANAL_AXIS) for v in (c - hw - 0.02, c + hw + 0.02)], locked,
                              snap_eps=CANAL_SNAP)
    for v in bm.verts:
        u, w = to_uv(v.co.x, v.co.y, CANAL_AXIS)
        for c in CANAL_OFFSETS:
            ua, ub = u_at(R_PED_OUT + CANAL_END, c), u_at(C.ATRIO_R - CANAL_END, c)
            if abs(w - c) <= hw - CANAL_INSET + 1e-4 and ua + CANAL_END - 1e-4 <= u <= ub - CANAL_END + 1e-4:
                v.co.z -= C.LIGHT_CANAL_DEPTH
    # cuerpo: peldanos perimetrales + faldon (abierto arriba; lo cierra la cara superior)
    body = [(C.ATRIO_R, ATRIO_TOP)]
    for k in range(1, ATRIO_RISERS):
        z = ATRIO_TOP - k * riser
        r0 = C.ATRIO_R + (k - 1) * STEP_TREAD
        body += [(r0, z), (r0 + STEP_TREAD, z)]
        lvl.append((r0, r0 + STEP_TREAD, z))
    body += [(R_ATRIO_OUT, zb), (0.0, zb)]
    mbody = ST.MeshBuilder()
    lathe(mbody, body, closed=False)
    vs = [bm.verts.new(p) for p in mbody.verts]
    for f in mbody.faces:
        bm.faces.new([vs[i] for i in f])
    obj = bm_to_object(bm, "TRN_Atrio", col, mat)
    stats["atrio"] = {"top": round(ATRIO_TOP, 3), "radius": C.ATRIO_R, "risers": ATRIO_RISERS,
                      "riser_m": round(riser, 3), "tread_m": STEP_TREAD, "outer_r": R_ATRIO_OUT,
                      "tris": len(obj.data.polygons)}
    return obj, lvl, riser


def bm_to_object(bm, name, col, mat, origin=None):
    bmesh.ops.triangulate(bm, faces=bm.faces[:], quad_method="BEAUTY", ngon_method="EAR_CLIP")
    bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=1e-6)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    zmin = min(v.co.z for v in bm.verts)
    ox, oy = origin if origin else (0.0, 0.0)
    for v in bm.verts:
        v.co -= Vector((ox, oy, zmin))
    uvl = bm.loops.layers.uv.new("UVMap")
    for f in bm.faces:
        n = f.normal
        ax = max(range(3), key=lambda i: abs(n[i]))
        for loop in f.loops:
            c = loop.vert.co + Vector((ox, oy, zmin))
            loop[uvl].uv = (c.x, c.y) if ax == 2 else ((c.y, c.z) if ax == 0 else (c.x, c.z))
    if name in bpy.data.objects:
        bpy.data.objects.remove(bpy.data.objects[name])
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    for p in me.polygons:
        p.use_smooth = False
    me.materials.append(mat)
    obj = bpy.data.objects.new(name, me)
    obj.location = (ox, oy, zmin)
    col.objects.link(obj)
    return obj


def mb_to_object(mb, name, col, mat, origin=None):
    bm = bmesh.new()
    vs = [bm.verts.new(p) for p in mb.verts]
    for f in mb.faces:
        try:
            bm.faces.new([vs[i] for i in f])
        except ValueError:
            pass
    return bm_to_object(bm, name, col, mat, origin)


def pedestal_object(col, mat):
    z1 = PED_TOP - (PED_TOP - ATRIO_TOP) / PED_RISERS
    mb = ST.MeshBuilder()
    lathe(mb, [(0.0, PED_TOP), (C.PORTAL_PEDESTAL_R, PED_TOP), (C.PORTAL_PEDESTAL_R, z1), (R_PED_OUT, z1),
               (R_PED_OUT, ATRIO_TOP - 0.2), (0.0, ATRIO_TOP - 0.2)], seg=96)
    return mb_to_object(mb, "TRN_PortalPedestal", col, mat)


def prism_ring(mb, cx, cy, r_bot, r_top, z0, z1, seg, chamfer=0.0, rot=0.0):
    prof = [(0.0, z0), (r_bot, z0), (r_top, z1 - chamfer)]
    if chamfer:
        prof.append((r_top - chamfer, z1))
    prof.append((0.0, z1))
    base = len(mb.verts)
    m = ST.MeshBuilder()
    lathe(m, prof, seg=seg)
    a = radians(rot)
    ca, sa = cos(a), sin(a)
    mb.add([(cx + x * ca - y * sa, cy + x * sa + y * ca, z) for x, y, z in m.verts], m.faces)
    return base


def runestones(col, mat, markers):
    mb = ST.MeshBuilder()
    for i in range(C.RUNESTONE_COUNT):
        ang = FIRST_RUNESTONE_DEG - i * 360.0 / C.RUNESTONE_COUNT
        x, y, _ = C.polar(ang, C.RUNESTONE_R)
        prism_ring(mb, x, y, C.RUNESTONE_D / 2, C.RUNESTONE_D / 2 - 0.05, ATRIO_TOP - 0.1,
                   ATRIO_TOP + C.RUNESTONE_H, 8, chamfer=0.06, rot=ang + 22.5)
        markers.append((f"MARKER_Runestone_{i + 1:02d}", (x, y, ATRIO_TOP), ang, {"index": i + 1}))
    return mb_to_object(mb, "TRN_Runestones", col, mat)


def descent_pedestals(col, mat, markers):
    mb = ST.MeshBuilder()
    n = len(C.DESCENT_FLOORS)
    for i, floor in enumerate(C.DESCENT_FLOORS):
        ang = FIRST_PEDESTAL_DEG - i * 360.0 / n
        x, y, _ = C.polar(ang, C.DESCENT_PEDESTAL_R)
        prism_ring(mb, x, y, C.DESCENT_PEDESTAL_D / 2, C.DESCENT_PEDESTAL_D / 2, ATRIO_TOP - 0.1,
                   ATRIO_TOP + C.DESCENT_PEDESTAL_H, 12, chamfer=0.04)
        markers.append((f"MARKER_Descent_Pedestal_{i + 1:02d}", (x, y, ATRIO_TOP + C.DESCENT_PEDESTAL_H), ang,
                        {"floor": floor}))
    return mb_to_object(mb, "TRN_DescentPedestals", col, mat)


def terrain_sampler(obj):
    dg = bpy.context.evaluated_depsgraph_get()
    bvh = BVHTree.FromObject(obj, dg)

    def z(x, y):
        hit = bvh.ray_cast(Vector((x, y, 100.0)), Vector((0, 0, -1)))
        return hit[0].z if hit[0] else T.height(x, y)
    return z


def footprint_rect(ang, u0, u1, v0, v1):
    return [from_uv(u, v, ang) for u, v in ((u0, v0), (u1, v0), (u1, v1), (u0, v1))]


def footprint_samples(poly, step=0.5):
    xs = [p[0] for p in poly]
    ys = [p[1] for p in poly]

    def inside(x, y):
        c = False
        n = len(poly)
        for i in range(n):
            x1, y1 = poly[i]
            x2, y2 = poly[(i + 1) % n]
            if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
                c = not c
        return c
    out = []
    x = min(xs)
    while x <= max(xs):
        y = min(ys)
        while y <= max(ys):
            if inside(x, y):
                out.append((x, y))
            y += step
        x += step
    return out + list(poly)


def slab_from_poly(mb, poly, z_top, z_bot):
    n = len(poly)
    pts = [(x, y, z_bot) for x, y in poly] + [(x, y, z_top) for x, y in poly]
    faces = [tuple(range(n - 1, -1, -1)), tuple(range(n, 2 * n))]
    for i in range(n):
        j = (i + 1) % n
        faces.append((i, j, n + j, n + i))
    mb.add(pts, faces)


def parcels(col, mat, zfun, markers, stats):
    out = []
    W, D = C.PLAZA_BUILDING_SIZE
    r0 = C.PLAZA_BUILDING_BAND[0]
    for i in range(C.PLAZA_BUILDING_COUNT):
        ang = FIRST_BUILDING_DEG + i * 360.0 / C.PLAZA_BUILDING_COUNT
        poly = footprint_rect(ang, r0, r0 + D, -W / 2, W / 2)
        zs = [zfun(x, y) for x, y in footprint_samples(poly)]
        top, bot = max(zs) + 0.02, min(zs) - SKIRT
        mb = ST.MeshBuilder()
        slab_from_poly(mb, poly, top, bot)
        cx, cy = from_uv(r0 + D / 2, 0.0, ang)
        name = f"TRN_PlazaParcel_{i + 1:02d}"
        mb_to_object(mb, name, col, mat, origin=(cx, cy))
        fx, fy = from_uv(r0, 0.0, ang)
        markers.append((f"MARKER_PlazaBuilding_{i + 1:02d}", (fx, fy, top), ang,
                        {"parcel": name, "facade_w": W, "depth": D, "door_direction": "+Y"}))
        out.append({"name": name, "angle": ang, "r": [r0, r0 + D], "top": round(top, 3),
                    "rear_exposed_m": round(top - min(zs), 3)})
    stats["parcels"] = out


def landmark_pads(col, mat, zfun, markers, stats):
    out = {}
    for key, (ang, r, shape, dims, h) in C.LANDMARK_PADS.items():
        if shape == "circle":
            R = dims[0] / 2
            n = 32
            cx, cy = from_uv(r, 0.0, ang)
            poly = [(cx + R * cos(2 * pi * i / n), cy + R * sin(2 * pi * i / n)) for i in range(n)]
        else:
            w, d = dims                                 # w tangencial (fachada), d radial
            poly = footprint_rect(ang, r - d / 2, r + d / 2, -w / 2, w / 2)
            cx, cy = from_uv(r, 0.0, ang)
        zs = [zfun(x, y) for x, y in footprint_samples(poly)]
        top, bot = max(zs) + 0.05, min(zs) - SKIRT
        mb = ST.MeshBuilder()
        slab_from_poly(mb, poly, top, bot)
        mb_to_object(mb, f"TRN_Pad_{key}", col, mat, origin=(cx, cy))
        mname = {"Faro": "MARKER_Faro", "Santuario": "MARKER_Santuario", "SalonHazanas": "MARKER_SalonHazanas",
                 "Obelisco": "MARKER_Obelisco"}[key]
        props = {"pad": f"TRN_Pad_{key}", "shape": shape, "dims_m": list(dims), "door_direction": "+Y"}
        if h:
            props["height_m"] = h
        markers.append((mname, (cx, cy, top), ang, props))
        out[key] = {"center": [round(cx, 2), round(cy, 2)], "top": round(top, 3),
                    "terrain_min": round(min(zs), 3), "terrain_max": round(max(zs), 3),
                    "exposed_plinth_m": round(top - min(zs), 3), "future_height_m": h}
    stats["landmark_pads"] = out


def light_canals(col, mat, zfun, atrio_steps, atrio_riser, stats):
    mb = ST.MeshBuilder()
    hw = C.LIGHT_CANAL_WIDTH / 2 - CANAL_INSET
    eps = 0.003

    def strip(c, u_list, z_list):
        pts, faces = [], []
        for k, (u, z) in enumerate(zip(u_list, z_list)):
            for v in (c - hw, c + hw):
                x, y = from_uv(u, v, CANAL_AXIS)
                pts.append((x, y, z + eps))
            if k:
                b = 2 * k
                faces.append((b - 2, b - 1, b + 1, b))
        mb.add(pts, faces)

    def riser(c, R, z_hi, z_lo):
        u = u_at(R, c) + eps
        pts = []
        for v in (c - hw, c + hw):
            x, y = from_uv(u + eps, v, CANAL_AXIS)
            pts += [(x, y, z_lo), (x, y, z_hi)]
        mb.add(pts, [(0, 2, 3, 1)])

    length = 0.0
    for c in CANAL_OFFSETS:
        # Atrio (fondo del surco)
        ua, ub = u_at(R_PED_OUT + CANAL_END, c), u_at(C.ATRIO_R - CANAL_END, c)
        strip(c, [ua, ub], [ATRIO_TOP - C.LIGHT_CANAL_DEPTH] * 2)
        # borde superior y peldanos del Atrio (incrustaciones a ras)
        strip(c, [ub, u_at(C.ATRIO_R, c)], [ATRIO_TOP] * 2)
        z_prev = ATRIO_TOP
        for r0, r1, z in atrio_steps:
            riser(c, r0, z_prev, z)
            strip(c, [u_at(r0, c), u_at(r1, c)], [z, z])
            z_prev = z
        riser(c, R_ATRIO_OUT, z_prev, zfun(*from_uv(u_at(R_ATRIO_OUT, c) + 0.06, c, CANAL_AXIS)))
        # terreno: fondo del surco hasta el basamento del Faro
        u0, u1 = canal_u_range_terrain(c)
        us = S2.frange(u0, u1, 0.5)
        zs = [zfun(*from_uv(u, c, CANAL_AXIS)) for u in us]
        strip(c, us, zs)
        length += (u1 - ua)
    obj = mb_to_object(mb, "TRN_LightCanals", col, mat)
    stats["light_canals"] = {"count": len(CANAL_OFFSETS), "offsets_m": list(CANAL_OFFSETS),
                             "width_m": C.LIGHT_CANAL_WIDTH, "depth_m": C.LIGHT_CANAL_DEPTH,
                             "length_each_m": round(length / len(CANAL_OFFSETS), 2), "tris": len(obj.data.polygons)}


def magic_material():
    if MAT_MAGIC in bpy.data.materials:
        return bpy.data.materials[MAT_MAGIC]
    m = bpy.data.materials.new(MAT_MAGIC)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    col = C.hex_to_linear_rgba(C.MAGIC_BLUE_HEX)
    b.inputs["Base Color"].default_value = col
    b.inputs["Emission Color"].default_value = col
    b.inputs["Emission Strength"].default_value = EMISSION_STRENGTH
    b.inputs["Roughness"].default_value = 0.4
    return m


def rune_material():
    if MAT_RUNE in bpy.data.materials:
        return bpy.data.materials[MAT_RUNE]
    m = bpy.data.materials.new(MAT_RUNE)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = C.hex_to_linear_rgba(RUNE_HEX)
    b.inputs["Roughness"].default_value = 0.8
    return m


def make_markers(col, markers):
    for name, loc, ang, props in markers:
        if name in bpy.data.objects:
            bpy.data.objects.remove(bpy.data.objects[name])
        e = bpy.data.objects.new(name, None)
        e.empty_display_type = "ARROWS"
        e.empty_display_size = 1.0
        e.location = loc
        e.rotation_euler = (0.0, 0.0, radians(ang + 90.0))    # +Y local -> centro de la plaza
        for k, v in props.items():
            e[k] = v
        col.objects.link(e)


# ---------------------------------------------------------------------------
def build(scene, stats):
    trn = bpy.data.objects["TRN_City"]
    plaza_terrain(trn, stats)
    col = bpy.data.collections[COL_PLAZA]
    for o in list(col.objects):
        bpy.data.objects.remove(o)
    mcol = bpy.data.collections.get(COL_MARKERS)
    if mcol is None:
        mcol = bpy.data.collections.new(COL_MARKERS)
        col.children.link(mcol)
    for o in list(mcol.objects):
        bpy.data.objects.remove(o)
    stone = ST.stone_material()
    markers = [("MARKER_Portal_Center", (0.0, 0.0, PED_TOP), -90.0,
                {"pedestal_r": C.PORTAL_PEDESTAL_R, "arch_h_m": C.PORTAL_ARCH_H})]
    _atrio, steps, riser = atrio_object(col, stone, stats)
    pedestal_object(col, stone)
    runestones(col, rune_material(), markers)
    descent_pedestals(col, stone, markers)
    zfun = terrain_sampler(trn)
    parcels(col, stone, zfun, markers, stats)
    landmark_pads(col, stone, zfun, markers, stats)
    light_canals(col, magic_material(), zfun, steps, riser, stats)
    make_markers(mcol, markers)
    stats["plaza_objects"] = {o.name: len(o.data.polygons) for o in col.objects if o.type == "MESH"}
    stats["plaza_markers"] = len(markers)
    return stats
