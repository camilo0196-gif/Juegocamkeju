"""
CONCORDIA - PJ1: cuerpo base del elfo masculino (blender/elfo_v01.blend). Base MakeHuman via MPFB 2.0.18 (assets
CC0); proporciones, cara, orejas y texturas propias de Concordia.

Pasos (python build_pj1_elfo.py -- <paso> ...):
  medir    humano de referencia (mismos macros, sin rasgos elficos) y elfo; compara proporciones y guarda el json
  cuerpo   elfo completo: pose T, proxy 1591, ojos, orejas, piezas, HIDE_*, normales continuas -> elfo_v01.blend
  piel     horneado de la piel (pj1_piel.py) a 1K en dos tonos + ojos; materiales
  exportar export/godot/pj_elfo_cuerpo.glb y docs/reports/pj1_elfo_cuerpo.json
Orden completo: -- medir cuerpo piel exportar
Normas: 1,85 m, de cara a -Y, metros, origen en el suelo entre los pies, transformaciones aplicadas.
"""

import json
import math
import os
import sys

import bpy
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import pj_mpfb as MP  # noqa: E402

REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
BLEND = os.path.join(REPO, "blender", "elfo_v01.blend")
REPORT = os.path.join(REPO, "docs", "reports", "pj1_elfo_cuerpo.json")
HEIGHT = 1.85

MACRO = {"gender": 1.0, "age": 0.5, "muscle": 0.62, "weight": 0.30, "proportions": 1.0, "height": 0.7,
         "cupsize": 0.5, "firmness": 0.5}
# rasgos elficos de Concordia (pesos calibrados con el paso 'medir': hombros -8 %, piernas +6 %, 8 cabezas)
ELF = {
    "torso/measure-shoulder-dist-decr": 0.7,
    "legs/measure-upperleg-height-incr": 0.36, "legs/measure-lowerleg-height-incr": 0.36,
    "neck/measure-neck-height-incr": 0.45, "neck/neck-scale-vert-incr": 0.2, "neck/neck-scale-horiz-decr": 0.25,
    "head/head-scale-horiz-decr": 0.1, "head/head-oval": 0.5,
    "cheek/*-cheek-bones-incr": 0.8, "cheek/*-cheek-volume-decr": 0.5, "cheek/*-cheek-inner-decr": 0.3,
    "eyes/*-eye-corner1-up": 0.6, "eyes/*-eye-eyefold-angle-up": 0.5, "eyes/*-eye-height2-decr": 0.3,
    "nose/nose-scale-horiz-decr": 0.4, "nose/nose-volume-decr": 0.4, "nose/nose-point-width-decr": 0.5,
    "nose/nose-scale-depth-decr": 0.2,
    "chin/chin-width-decr": 0.35, "chin/chin-prominent-incr": 0.25, "chin/chin-triangle": 0.3,
    "mouth/mouth-scale-horiz-decr": 0.2, "mouth/mouth-upperlip-volume-decr": 0.4,
    "mouth/mouth-lowerlip-volume-decr": 0.45, "chin/chin-bones-incr": 0.3,
    "ears/*-ear-shape-pointed": 1.0, "ears/*-ear-scale-vert-incr": 0.6, "ears/*-ear-rot-backward": 0.6,
    "ears/*-ear-flap-decr": 0.5, "ears/*-ear-lobe-decr": 0.6,
    "hands/*-hand-fingers-length-incr": 1.0, "hands/*-hand-fingers-diameter-decr": 0.5,
    "legs/*-lowerleg-scale-horiz-decr": 0.2, "legs/*-upperleg-scale-horiz-decr": 0.15,
    "legs/*-lowerleg-fat-decr": 0.4, "legs/*-upperleg-fat-decr": 0.4,
}


def target_names(d):
    """'carpeta/nombre' -> nombre suelto (MPFB busca por nombre); '*' se expande a l / r en create_base."""
    return {k.split("/")[-1]: v for k, v in d.items()}


def collection(name):
    c = bpy.data.collections.get(name) or bpy.data.collections.new(name)
    if c.name not in bpy.context.scene.collection.children:
        bpy.context.scene.collection.children.link(c)
    return c


def make_human(targets, tag, col, eyes=False, all_joints=False):
    """Humano MPFB en T -> (malla base evaluada 'HI_', proxy 1591 evaluado, ojos, articulaciones). Se borran los
    objetos de MPFB; quedan mallas simples sin modificadores."""
    bm, loaded = MP.create_base(MACRO, target_names(targets))
    joints = MP.tpose_base(bm, joints_wanted=None if all_joints else MP.JOINTS)
    px = MP.add_proxy(bm)
    ey = MP.add_eyes(bm) if eyes else None
    bpy.context.view_layer.update()
    hi = MP.evaluated_copy(bm, f"HI_{tag}", col)
    for g in bm.vertex_groups:
        hi.vertex_groups.new(name=g.name) if hi.vertex_groups.get(g.name) is None else None
    lo = MP.evaluated_copy(px, f"LO_{tag}", col)
    ex = MP.evaluated_copy(ey, f"EY_{tag}", col) if ey else None
    for o in [o for o in bpy.data.objects if o not in (hi, lo, ex)]:
        bpy.data.objects.remove(o, do_unlink=True)
    return hi, lo, ex, joints, loaded


def normalize(objs, joints, ref):
    """Pies en z=0, punto medio de los tobillos en x=y=0 y altura total HEIGHT (medida en 'ref' sin orejas)."""
    vs = [ref.matrix_world @ v.co for v in ref.data.vertices]
    zmin, zmax = min(v.z for v in vs), max(v.z for v in vs)
    fl, fr = Vector(joints["foot.L"][0]), Vector(joints["foot.R"][0])
    off = Vector(((fl.x + fr.x) / 2, (fl.y + fr.y) / 2, zmin))
    s = HEIGHT / (zmax - zmin)
    for o in objs:
        if o is None:
            continue
        me = o.data
        mw = o.matrix_world.copy()
        for v in me.vertices:
            v.co = ((mw @ v.co) - off) * s
        o.matrix_world = o.matrix_world.Identity(4)
        me.update()
    return {k: (tuple((Vector(h) - off) * s), tuple((Vector(t) - off) * s)) for k, (h, t) in joints.items()}, s


def measure(hi, lo, J):
    """Medidas sobre la malla final (1,85 m). Barbilla = punto mas bajo del perfil medio por delante del cuello."""
    vs = [v.co for v in lo.data.vertices]
    top = max(v.z for v in vs)
    neck = Vector(J["neck01"][0])
    hv = [v.co for v in hi.data.vertices]
    # barbilla: perfil medio (|x| < 4 mm) en franjas de 4 mm bajando desde la boca; el borde inferior de la barbilla
    # es la ultima franja antes de que el punto mas adelantado salte hacia atras mas de 1,5 cm (debajo de la mandibula)
    mid = [v for v in hv if abs(v.x) < 0.004]
    zh = Vector(J["head"][0]).z
    prev, chin = None, None
    z = zh - 0.03
    while z > neck.z - 0.05:
        b = [v for v in mid if z - 0.004 < v.z <= z]
        if b:
            f = min(b, key=lambda v: v.y)
            if prev is not None and f.y - prev.y > 0.015:
                chin = prev
                break
            prev = f
        z -= 0.004
    head_h = top - chin.z
    ua = Vector(J["upperarm01.L"][0]), Vector(J["upperarm01.R"][0])
    hip = (Vector(J["upperleg01.L"][0]).z + Vector(J["upperleg01.R"][0]).z) / 2
    head_j = Vector(J["head"][0]).z
    return {"altura_m": round(top, 4), "cabeza_m": round(head_h, 4), "cabezas": round(top / head_h, 2),
            "barbilla_z": round(chin.z, 4), "hombros_biacromial_m": round((ua[0] - ua[1]).length, 4),
            "cadera_z": round(hip, 4), "base_cuello_z": round(neck.z, 4),
            "pierna_m": round(hip, 4), "torso_m": round(neck.z - hip, 4),
            "pierna_torso": round(hip / (neck.z - hip), 4), "cuello_m": round(head_j - neck.z, 4),
            "tris_lo": sum(len(p.vertices) - 2 for p in lo.data.polygons)}


def step_medir():
    col = collection("PJ_MEDIR")
    out = {}
    for tag, t in (("REF", {}), ("ELF", ELF)):
        hi, lo, _e, J, loaded = make_human(t, tag, col)
        J, s = normalize([hi, lo], J, lo)
        out[tag] = measure(hi, lo, J)
        out[tag]["escala"] = round(s, 4)
        print("MEDIDA", tag, json.dumps(out[tag]), flush=True)
        for o in (hi, lo):
            bpy.data.objects.remove(o, do_unlink=True)
    r, e = out["REF"], out["ELF"]
    cmp = {"hombros_biacromial": round(e["hombros_biacromial_m"] / r["hombros_biacromial_m"] - 1, 4),
           "pierna_torso": round(e["pierna_torso"] / r["pierna_torso"] - 1, 4),
           "cuello": round(e["cuello_m"] / r["cuello_m"] - 1, 4)}
    print("COMPARA", json.dumps(cmp), flush=True)
    out["comparacion_elfo_vs_referencia"] = cmp
    with open(os.path.join(os.path.dirname(REPORT), "pj1_elfo_referencia.json"), "w") as fh:
        json.dump(out, fh, indent=1)
    c = bpy.data.collections.get("PJ_MEDIR")
    if c:
        bpy.data.collections.remove(c)


def transfer_groups(src, dst, names=None):
    """Pesos de los grupos de 'src' (malla base de MPFB) a 'dst' (proxy) por cara mas cercana interpolada."""
    for g in src.vertex_groups:
        if (names is None or g.name in names) and dst.vertex_groups.get(g.name) is None:
            dst.vertex_groups.new(name=g.name)
    m = dst.modifiers.new("DT", "DATA_TRANSFER")
    m.object = src
    m.use_vert_data = True
    m.data_types_verts = {"VGROUP_WEIGHTS"}
    m.vert_mapping = "POLYINTERP_NEAREST"
    m.layers_vgroup_select_src = "ALL"
    m.layers_vgroup_select_dst = "NAME"
    for o in bpy.context.view_layer.objects:
        o.select_set(False)
    bpy.context.view_layer.objects.active = dst
    dst.select_set(True)
    bpy.ops.object.modifier_apply(modifier=m.name)


EAR_LEN = 0.13          # lobulo -> punta (m), pedido 12-14 cm
EAR_BACK = 27.0         # grados hacia atras desde la vertical (vista lateral), pedido 25-30
EAR_OUT = 12.0          # grados de apertura hacia fuera (para que se lean de frente)


def group_weights(o, name):
    gi = o.vertex_groups[name].index
    return {v.index: next((g.weight for g in v.groups if g.group == gi), 0.0) for v in o.data.vertices}


def subdivide_ears(lo):
    """Un nivel de subdivision en las caras de las orejas (el proxy trae 23 vertices por oreja) con suavizado de los
    vertices nuevos; las caras de la union que quedan con 5-6 lados se rehacen en quads (y algun triangulo)."""
    import bmesh
    w = group_weights(lo, "ears")
    bm = bmesh.new()
    bm.from_mesh(lo.data)
    bm.verts.ensure_lookup_table()
    faces = [f for f in bm.faces if all(w[v.index] > 0.3 for v in f.verts)]
    edges = list({e for f in faces for e in f.edges})
    before = len(bm.faces)
    res = bmesh.ops.subdivide_edges(bm, edges=edges, cuts=1, use_grid_fill=True, quad_corner_type="INNER_VERT",
                                    smooth=0.6, use_smooth_even=True)
    new = [g for g in res["geom_inner"] if isinstance(g, bmesh.types.BMVert)]
    bmesh.ops.smooth_vert(bm, verts=new, factor=0.4, use_axis_x=True, use_axis_y=True, use_axis_z=True)
    ngons = [f for f in bm.faces if len(f.verts) > 4]
    if ngons:
        tri = bmesh.ops.triangulate(bm, faces=ngons)
        bmesh.ops.join_triangles(bm, faces=tri["faces"], angle_face_threshold=math.radians(60),
                                 angle_shape_threshold=math.radians(60))
    from collections import Counter
    kinds = Counter(len(f.verts) for f in bm.faces)
    bm.to_mesh(lo.data)
    bm.free()
    lo.data.update()
    return {"caras_antes": before, "caras_despues": sum(kinds.values()), "lados": dict(kinds)}


def cup_ears(lo, ear_info, depth=0.003):
    """Concha de la oreja: los vertices de la cara exterior que no estan en el borde se hunden hacia el craneo; el
    borde (helix) queda como un reborde. Borde = vertices cuya normal ya no mira hacia fuera (|n.x| < 0,55)."""
    import bmesh
    w = group_weights(lo, "ears")
    lo.data.update()
    bm = bmesh.new()
    bm.from_mesh(lo.data)
    bm.normal_update()
    rim = {v.index for v in bm.verts if w[v.index] > 0.5 and abs(v.normal.x) < 0.55}
    n = 0
    for v in bm.verts:
        if w[v.index] <= 0.5 or v.index in rim:
            continue
        sx = 1.0 if v.co.x > 0 else -1.0
        if v.normal.x * sx < 0.55:
            continue
        inf = ear_info["L" if sx > 0 else "R"]
        t = max(0.0, min(1.0, (v.co - Vector(inf["lobulo"])).dot(Vector(inf["eje"])) / EAR_LEN))
        fade = 1.0 - max(0.0, min(1.0, (t - 0.35) / 0.3))          # sin concha en el tercio de la punta (fina)
        near_rim = any(e.other_vert(v).index in rim for e in v.link_edges)
        v.co.x -= sx * depth * (0.5 if near_rim else 1.0) * w[v.index] * fade
        n += 1
    bm.to_mesh(lo.data)
    bm.free()
    lo.data.update()
    return {"vertices_hundidos": n, "vertices_borde": len(rim)}


def ear_displacement(lo):
    """Desplazamiento por vertice del proxy para alargar cada oreja: la punta va a lobulo + EAR_LEN en la direccion
    pedida; el resto se mueve con t^2 (t = posicion a lo largo de la oreja) y nada en la union con el craneo."""
    w = group_weights(lo, "ears")
    disp = {}
    info = {}
    for sx in (1.0, -1.0):
        ids = [i for i, x in w.items() if x > 0.01 and lo.data.vertices[i].co.x * sx > 0]
        full = [i for i in ids if w[i] > 0.5]
        co = {i: lo.data.vertices[i].co.copy() for i in ids}
        L = min((co[i] for i in full), key=lambda c: c.z)
        T0 = max((co[i] for i in full), key=lambda c: c.z)
        a0 = (T0 - L)
        n0 = a0.length
        a0.normalize()
        b, o_ = math.radians(EAR_BACK), math.radians(EAR_OUT)
        d = Vector((sx * math.sin(o_), math.sin(b) * math.cos(o_), math.cos(b) * math.cos(o_)))
        T = L + d * EAR_LEN
        D = T - T0
        x_att = min(abs(co[i].x) for i in full)
        wv = d.cross(Vector((sx, 0.0, 0.0))).normalized()      # anchura de la oreja (en su plano)
        for i in ids:
            t = max(0.0, min(1.0, (co[i] - L).dot(a0) / n0))
            f = max(0.0, min(1.0, (abs(co[i].x) - x_att) / 0.004))
            p1 = co[i] + D * (t * t) * f * w[i]
            # perfil de hoja: algo mas ancha a media altura y afilada en la punta
            rel = p1 - L
            t1 = max(0.0, min(1.0, rel.dot(d) / EAR_LEN))
            k = max(0.0, min(1.0, (t1 - 0.68) / 0.32))
            sc = (1.0 + 0.22 * math.sin(math.pi * t1)) * (1.0 - 0.85 * k * k * (3 - 2 * k))
            lat = rel.dot(wv)
            p2 = p1 + wv * lat * (sc - 1.0) * f * w[i]
            disp[i] = p2 - co[i]
        info["L" if sx > 0 else "R"] = {"lobulo": tuple(round(c, 4) for c in L), "eje": tuple(round(c, 4) for c in d), "punta_original": tuple(round(c, 4) for c in T0),
                                        "largo_original_m": round(n0, 4)}
    # transicion suave: dos anillos de piel alrededor de la oreja acompanan parte del movimiento (sin pliegues)
    adj = {}
    for e in lo.data.edges:
        a, b = e.vertices
        adj.setdefault(a, []).append(b)
        adj.setdefault(b, []).append(a)
    for k in (0.45, 0.2):
        ring = {}
        for i in list(disp):
            for j in adj.get(i, []):
                if j not in disp and w.get(j, 0) <= 0.01:
                    ring.setdefault(j, []).append(disp[i])
        for j, ds in ring.items():
            disp[j] = sum(ds, Vector()) / len(ds) * k
    return disp, info


def apply_lo_disp_to_hi(lo, orig, disp, hi, radius=0.05):
    """Lleva el mismo desplazamiento a la malla base (para el horneado del normal map): cada vertice de 'hi' cerca de
    las orejas toma el desplazamiento interpolado de la cara del proxy original mas cercana."""
    from mathutils.bvhtree import BVHTree
    from mathutils.interpolate import poly_3d_calc
    polys = [list(p.vertices) for p in lo.data.polygons]
    tree = BVHTree.FromPolygons(orig, polys)
    cs = [orig[i] for i in disp]
    lo_b = Vector([min(c[k] for c in cs) - radius for k in range(3)])
    hi_b = Vector([max(c[k] for c in cs) + radius for k in range(3)])
    n = 0
    for v in hi.data.vertices:
        c = v.co
        if not all(lo_b[k] <= c[k] <= hi_b[k] for k in range(3)):
            continue
        loc, _nrm, fi, _dist = tree.find_nearest(c)
        if fi is None:
            continue
        vids = polys[fi]
        ws = poly_3d_calc([orig[i] for i in vids], loc)
        dd = sum((disp.get(i, Vector()) * wk for i, wk in zip(vids, ws)), Vector())
        if dd.length > 1e-6:
            v.co = c + dd
            n += 1
    hi.data.update()
    return n


def measure_ears(lo, ids_by_side):
    out = {}
    for side, ids in ids_by_side.items():
        cs = [lo.data.vertices[i].co for i in ids]
        L, T = min(cs, key=lambda c: c.z), max(cs, key=lambda c: c.z)
        v = T - L
        out[side] = {"largo_m": round(v.length, 4),
                     "inclinacion_atras_grados": round(math.degrees(math.atan2(v.y, v.z)), 1),
                     "apertura_fuera_grados": round(math.degrees(math.atan2(abs(v.x), math.hypot(v.y, v.z))), 1),
                     "punta_z": round(T.z, 4), "grosor_m": None}
    return out


PART_ORDER = ("Head", "Torso", "Arms", "Hands", "Legs", "Feet")
HEAD_GROUPS = ("head", "jaw", "neck01", "neck02", "neck03", "ears", "eye.", "oris", "levator", "orbicularis", "oculi",
               "risorius", "special0", "tongue")


def classify_faces(lo, J):
    """Pieza de cada cara: manos y brazos por planos perpendiculares al brazo en T (muneca, articulacion del
    hombro), pies por el plano del tobillo, piernas bajo la entrepierna, cabeza por pesos de cabeza y cuello."""
    me = lo.data
    wrist_x = abs(J["wrist.L"][0][0]) - 0.012
    sh_x = abs(J["upperarm01.L"][0][0]) + 0.01
    ankle_z = J["foot.L"][0][2] + 0.015
    crotch_z = min(v.co.z for v in me.vertices if abs(v.co.x) < 0.003 and v.co.z > 0.5)
    hg = [g.index for g in lo.vertex_groups if g.name.startswith(HEAD_GROUPS)]
    headw = {v.index: sum(g.weight for g in v.groups if g.group in hg) for v in me.vertices}
    arm_z = J["upperarm01.L"][0][2]
    out = []
    for p in me.polygons:
        c = p.center
        if abs(c.x) > wrist_x and c.z > arm_z - 0.25:
            k = "Hands"
        elif abs(c.x) > sh_x and c.z > arm_z - 0.25:
            k = "Arms"
        elif c.z < ankle_z:
            k = "Feet"
        elif c.z < crotch_z:
            k = "Legs"
        elif sum(headw[i] for i in p.vertices) / len(p.vertices) > 0.5:
            k = "Head"
        else:
            k = "Torso"
        out.append(k)
    return out, {"muneca_x": round(wrist_x, 4), "hombro_x": round(sh_x, 4), "tobillo_z": round(ankle_z, 4),
                 "entrepierna_z": round(crotch_z, 4)}


def find_seam(bm, axis, center, target, region, band=0.06):
    """Costura cerrada sobre aristas reales alrededor de un miembro: ciclo de coste minimo (longitud por
    (1 + (distancia al plano / 4 cm)^2)) que da una vuelta al eje. Se corta el anillo en el angulo pi y, para cada arista
    que cruza el corte, Dijkstra sin aristas del corte da el camino que rodea el miembro."""
    import heapq
    ax = Vector(axis).normalized()
    u = ax.orthogonal().normalized()
    w = ax.cross(u)
    C = Vector(center)
    vs = {v.index: v for v in bm.verts if region(v.co) and abs(v.co.dot(ax) - target) < band}

    def ang(v):
        r = v.co - C
        return math.atan2(r.dot(w), r.dot(u))

    th = {i: ang(v) for i, v in vs.items()}
    adj, cut = {i: [] for i in vs}, []
    for e in bm.edges:
        a, b = e.verts[0].index, e.verts[1].index
        if a not in vs or b not in vs:
            continue
        dm = abs(((vs[a].co + vs[b].co) / 2).dot(ax) - target)
        cost = e.calc_length() * (1.0 + (dm / 0.04) ** 2)
        if abs(th[a] - th[b]) > math.pi:
            cut.append((a, b, cost, e.index))
        else:
            adj[a].append((b, cost, e.index))
            adj[b].append((a, cost, e.index))
    best = None
    for a, b, c0, ei in cut:
        dist, prev = {a: 0.0}, {}
        pq = [(0.0, a)]
        while pq:
            d, x = heapq.heappop(pq)
            if d > dist.get(x, 1e9) or x == b:
                continue
            for y, c, ej in adj[x]:
                nd = d + c
                if nd < dist.get(y, 1e9):
                    dist[y], prev[y] = nd, (x, ej)
                    heapq.heappush(pq, (nd, y))
        if b not in dist:
            continue
        tot = dist[b] + c0
        if best is None or tot < best[0]:
            path, x = [ei], b
            while x != a:
                x, ej = prev[x]
                path.append(ej)
            best = (tot, path)
    if best is None:
        return None
    ids = set(best[1])
    hv = [bm.edges[k].verts[t].co.dot(ax) for k in ids for t in (0, 1)]
    mean = sum(hv) / len(hv)
    sd = (sum((x - mean) ** 2 for x in hv) / len(hv)) ** 0.5
    return (best[0], ids, round(mean, 4), round(sd, 4))


def seam_loops(lo, J, cuts):
    """Costuras sobre bucles reales de aristas: munecas, hombros, tobillos, muslos y base del cuello."""
    import bmesh
    bm = bmesh.new()
    bm.from_mesh(lo.data)
    bm.edges.ensure_lookup_table()
    arm_z = J["upperarm01.L"][0][2]
    neck_z = J["neck01"][0][2]
    found, edges = {}, set()
    for sx, sd in ((1, "L"), (-1, "R")):
        specs = {
            f"muneca_{sd}": ((sx, 0, 0), J["wrist.L" if sx > 0 else "wrist.R"][0], cuts["muneca_x"],
                             lambda c, sx=sx: c.x * sx > 0.5),
            f"hombro_{sd}": ((sx, 0, 0), J["upperarm01.L" if sx > 0 else "upperarm01.R"][0], cuts["hombro_x"],
                             lambda c, sx=sx: c.x * sx > 0.1 and c.z > arm_z - 0.3),
            f"tobillo_{sd}": ((0, 0, 1), J["foot.L" if sx > 0 else "foot.R"][0], cuts["tobillo_z"],
                              lambda c, sx=sx: c.x * sx > 0.01 and c.z < 0.4),
            f"muslo_{sd}": ((0, 0, 1), J["upperleg01.L" if sx > 0 else "upperleg01.R"][0], cuts["entrepierna_z"] - 0.01,
                            lambda c, sx=sx: c.x * sx > 0.0005 and 0.6 < c.z < 1.15),
        }
        for k, (ax, ctr, tg, rg) in specs.items():
            found[k] = find_seam(bm, ax, ctr, tg, rg)
    found["cuello"] = find_seam(bm, (0, 0, 1), J["neck01"][0], neck_z + 0.01,
                                lambda c: abs(c.x) < 0.11 and 1.45 < c.z < 1.72)
    rep = {}
    for k, b in found.items():
        if b:
            edges.update(b[1])
            rep[k] = {"aristas": len(b[1]), "posicion": abs(b[2]), "desviacion": b[3]}
        else:
            rep[k] = None
    # componentes de caras separadas por las costuras
    bm.faces.ensure_lookup_table()
    comp = [-1] * len(bm.faces)
    n = 0
    for f0 in bm.faces:
        if comp[f0.index] >= 0:
            continue
        stack = [f0]
        comp[f0.index] = n
        while stack:
            f = stack.pop()
            for e in f.edges:
                if e.index in edges:
                    continue
                for g in e.link_faces:
                    if comp[g.index] < 0:
                        comp[g.index] = n
                        stack.append(g)
        n += 1
    bm.free()
    return comp, rep


def split_parts(lo, J, col):
    """Normales suaves del cuerpo entero guardadas como normales personalizadas (continuas en las costuras); las
    caras se reparten en 6 objetos con vertices coincidentes en los bordes y grupo HIDE_<pieza>."""
    me = lo.data
    for p in me.polygons:
        p.use_smooth = True
    me.update()
    vn = [v.normal.copy() for v in me.vertices]
    me.normals_split_custom_set_from_vertices(vn)
    parts, cuts = classify_faces(lo, J)
    comp, cuts["costuras_bucle"] = seam_loops(lo, J, cuts)
    from collections import Counter
    votes = {}
    for c, k in zip(comp, parts):
        votes.setdefault(c, Counter())[k] += 1
    parts = [votes[c].most_common(1)[0][0] for c in comp]      # cada componente entera a la pieza mayoritaria
    for k in PART_ORDER:
        me.materials.append(bpy.data.materials.get(f"TMP_{k}") or bpy.data.materials.new(f"TMP_{k}"))
    for p, k in zip(me.polygons, parts):
        p.material_index = PART_ORDER.index(k)
    for o in bpy.context.view_layer.objects:
        o.select_set(False)
    bpy.context.view_layer.objects.active = lo
    lo.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.mesh.separate(type="MATERIAL")
    bpy.ops.object.mode_set(mode="OBJECT")
    objs = {}
    for o in list(bpy.context.selected_objects):
        k = o.data.materials[o.data.polygons[0].material_index].name[4:]
        o.name = o.data.name = f"PJ_Elfo_{k}"
        o["pj_part"] = k
        o.data.materials.clear()
        objs[k] = o
    for k, o in objs.items():
        # solo se conservan los grupos de huesos (para el rig) y el HIDE de la pieza
        for g in list(o.vertex_groups):
            if g.name in ("HelperGeometry", "JointCubes", "Left", "Mid", "Right", "body") or "joint" in g.name \
                    or g.name.startswith(("helper", "tights", "skirt", "hair", "Detail", "nipple", "lips", "fingernails",
                                          "toenails", "scalp", "genitals")):
                o.vertex_groups.remove(g)
        if k != "Head":
            hg = o.vertex_groups.new(name=f"HIDE_{k}")
            hg.add([v.index for v in o.data.vertices], 1.0, "REPLACE")
    for k in PART_ORDER:
        m = bpy.data.materials.get(f"TMP_{k}")
        if m and m.users == 0:
            bpy.data.materials.remove(m)
    return objs, cuts


def seam_check(objs):
    """Vertices de borde de cada pieza que no coinciden con un vertice de otra pieza (debe ser 0) y diferencia
    maxima de normal personalizada entre los dos lados de la costura (grados)."""
    import bmesh
    from mathutils.kdtree import KDTree
    allv = []
    for k, o in objs.items():
        o.data.update()
        ns = {}
        for li, l in enumerate(o.data.loops):
            ns.setdefault(l.vertex_index, o.data.corner_normals[li].vector.copy())
        bm = bmesh.new()
        bm.from_mesh(o.data)
        for v in bm.verts:
            if v.is_boundary:
                allv.append((k, v.co.copy(), ns[v.index]))
        bm.free()
    kd = KDTree(len(allv))
    for i, (_k, c, _n) in enumerate(allv):
        kd.insert(c, i)
    kd.balance()
    lonely, worst = 0, 0.0
    for k, c, n in allv:
        others = [allv[i] for _c, i, d in kd.find_range(c, 1e-5) if allv[i][0] != k]
        if not others:
            lonely += 1
        for _k2, _c2, n2 in others:
            worst = max(worst, math.degrees(n.angle(n2, 0.0)))
    return {"vertices_de_borde": len(allv), "sin_pareja": lonely, "dif_normal_max_grados": round(worst, 3)}


def step_cuerpo(work):
    col = collection("PJ_ELFO")
    hi, lo, ey, J, loaded = make_human(ELF, "Elfo", col, eyes=True)
    J, s = normalize([hi, lo, ey], J, lo)
    transfer_groups(hi, lo)
    # orejas
    ear_sub = subdivide_ears(lo)
    print("OREJA_SUB", json.dumps(ear_sub), flush=True)
    orig = [v.co.copy() for v in lo.data.vertices]
    disp, ear_info = ear_displacement(lo)
    for i, d in disp.items():
        lo.data.vertices[i].co += d
    lo.data.update()
    n_hi = apply_lo_disp_to_hi(lo, orig, disp, hi)
    ear_cup = cup_ears(lo, ear_info)
    print("OREJA_CONCHA", json.dumps(ear_cup), flush=True)
    w = group_weights(lo, "ears")
    ears = measure_ears(lo, {"L": [i for i, x in w.items() if x > 0.5 and lo.data.vertices[i].co.x > 0],
                             "R": [i for i, x in w.items() if x > 0.5 and lo.data.vertices[i].co.x < 0]})
    print("OREJAS", json.dumps(ears), "hi_movidos", n_hi, flush=True)
    meas = measure(hi, lo, J)
    import bmesh
    bm_ = bmesh.new()
    bm_.from_mesh(lo.data)
    open_edges = sum(1 for v in bm_.verts if v.is_boundary)       # bordes propios del proxy (ojos, boca)
    bm_.free()
    objs, cuts = split_parts(lo, J, col)
    seams = seam_check(objs)
    seams["bordes_propios_del_proxy"] = open_edges
    print("COSTURAS", json.dumps(seams), json.dumps(cuts), flush=True)
    ey.name = ey.data.name = "PJ_Elfo_Eyes"
    ey["pj_part"] = "Eyes"
    hi.name = hi.data.name = "HI_Elfo_hornear"
    hi.hide_render = True
    hc = collection("PJ_HORNEO_alta")        # malla base de MPFB deformada igual: solo para hornear, no se exporta
    for c in list(hi.users_collection):
        c.objects.unlink(hi)
    hc.objects.link(hi)
    hc.hide_viewport = True
    tris = {k: sum(len(p.vertices) - 2 for p in o.data.polygons) for k, o in objs.items()}
    tris["Eyes"] = sum(len(p.vertices) - 2 for p in ey.data.polygons)
    print("TRIS", json.dumps(tris), sum(tris.values()), flush=True)
    print("MEDIDAS", json.dumps(meas), flush=True)
    bpy.context.scene["pj1_datos"] = json.dumps({"joints": J, "escala": s, "targets": loaded, "orejas": ears,
                                                  "orejas_origen": ear_info,
                                                  "orejas_subdivision": ear_sub, "orejas_concha": ear_cup, "cortes": cuts, "costuras": seams,
                                                  "tris": tris, "medidas": meas})
    bpy.ops.wm.save_as_mainfile(filepath=work)


def step_piel(work):
    """Horneado de la piel (pj1_piel) y materiales: MAT_Elfo_Piel (tono A, asignado), MAT_Elfo_Piel_B (tono B,
    usuario falso para cambiarlo), MAT_Elfo_Ojos."""
    import pj1_piel as PL
    bpy.ops.wm.open_mainfile(filepath=work)
    d = json.loads(bpy.context.scene["pj1_datos"])
    parts = [bpy.data.objects[f"PJ_Elfo_{k}"] for k in PART_ORDER]
    hi, ey = bpy.data.objects["HI_Elfo_hornear"], bpy.data.objects["PJ_Elfo_Eyes"]
    tex_dir = os.path.join(REPO, "textures", "personajes", "elfo")
    paths, rep = PL.bake_all(parts, hi, ey, d["joints"], tex_dir, "elfo_m")
    ma = PL.skin_material("MAT_Elfo_Piel", paths["albedo_A"], paths["normal"], paths["orm"])
    mb = PL.skin_material("MAT_Elfo_Piel_B", paths["albedo_B"], paths["normal"], paths["orm"])
    mb.use_fake_user = True
    me = PL.skin_material("MAT_Elfo_Ojos", paths["ojos"], None, None)
    for o in parts:
        o.data.materials.clear()
        o.data.materials.append(ma)
    ey.data.materials.clear()
    ey.data.materials.append(me)
    for p in ey.data.polygons:
        p.use_smooth = True
    d["texturas"] = {k: os.path.relpath(v, REPO) for k, v in paths.items()}
    d["texturas_informe"] = rep
    bpy.context.scene["pj1_datos"] = json.dumps(d)
    print("PIEL", json.dumps(rep), flush=True)
    bpy.ops.outliner.orphans_purge(do_recursive=True)
    bpy.ops.wm.save_as_mainfile(filepath=work)


def step_exportar(work):
    """glb del cuerpo (6 piezas + ojos) para Godot y el informe json."""
    from collections import Counter
    bpy.ops.wm.open_mainfile(filepath=work)
    d = json.loads(bpy.context.scene["pj1_datos"])
    objs = [bpy.data.objects[f"PJ_Elfo_{k}"] for k in PART_ORDER] + [bpy.data.objects["PJ_Elfo_Eyes"]]
    for o in bpy.context.view_layer.objects:
        o.select_set(False)
    for o in objs:
        o.select_set(True)
    glb = os.path.join(REPO, "export", "godot", "pj_elfo_cuerpo.glb")
    bpy.ops.export_scene.gltf(filepath=glb, export_format="GLB", use_selection=True, export_yup=True,
                              export_apply=True, export_extras=True, export_image_format="AUTO",
                              export_vertex_color="NONE")
    caras = Counter()
    for o in objs[:-1]:
        caras.update(len(p.vertices) for p in o.data.polygons)
    ref = {}
    rp = os.path.join(os.path.dirname(REPORT), "pj1_elfo_referencia.json")
    if os.path.exists(rp):
        ref = json.load(open(rp))
    tris = d["tris"]
    body = sum(v for k, v in tris.items() if k != "Eyes")
    rep = {
        "archivo": os.path.relpath(work, REPO), "glb": os.path.relpath(glb, REPO),
        "glb_kb": round(os.path.getsize(glb) / 1024, 1),
        "base": "MakeHuman (MPFB 2.0.18, assets de sistema CC0): malla base + proxy male1591 + ojos low-poly",
        "macros": MACRO, "targets": d["targets"],
        "medidas": d["medidas"], "referencia_humana_y_comparacion": ref,
        "orejas": d["orejas"], "orejas_subdivision": d["orejas_subdivision"], "orejas_concha": d["orejas_concha"],
        "tris_por_objeto": tris, "tris_cuerpo_con_cabeza": body, "tris_total_con_ojos": body + tris["Eyes"],
        "presupuesto_cuerpo": 4500, "caras_por_lados_cuerpo": dict(caras),
        "costuras": d["costuras"], "cortes": d["cortes"],
        "materiales": ["MAT_Elfo_Piel (tono A, asignado)", "MAT_Elfo_Piel_B (tono B, sin asignar)", "MAT_Elfo_Ojos"],
        "texturas": d.get("texturas"), "texturas_informe": d.get("texturas_informe"),
        "orientacion": "de cara a -Y en Blender (+Z en Godot), metros, origen en el suelo entre los pies, pose T",
        "grupos_HIDE": {k: f"HIDE_{k}" for k in PART_ORDER if k != "Head"},
    }
    os.makedirs(os.path.dirname(REPORT), exist_ok=True)
    with open(REPORT, "w") as fh:
        json.dump(rep, fh, indent=1, ensure_ascii=False)
    print("EXPORT", rep["glb_kb"], "KB", json.dumps(rep["caras_por_lados_cuerpo"]), flush=True)


def step_articulaciones():
    """Todas las articulaciones del rig 'default' de MPFB ajustado al elfo (pose T), normalizadas igual que el
    cuerpo (pies en z = 0, 1,85 m): base para colocar el esqueleto de Godot (concordia_rig.py)."""
    col = collection("PJ_ART")
    hi, lo, _e, J, _l = make_human(ELF, "Art", col, all_joints=True)
    J, s = normalize([hi, lo], J, lo)
    path = os.path.join(os.path.dirname(REPORT), "pj1_elfo_articulaciones.json")
    with open(path, "w") as fh:
        json.dump({"escala": s, "huesos": len(J), "articulaciones": J}, fh, indent=0)
    print("ARTICULACIONES", len(J), path, flush=True)


def arg_after(steps, k):
    i = steps.index(k) + 1
    return steps[i] if i < len(steps) and steps[i].endswith(".blend") else BLEND


def main():
    steps = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else ["cuerpo"]
    bpy.ops.wm.read_factory_settings(use_empty=True)
    if not MP.enable():
        raise RuntimeError("MPFB no se pudo activar")
    if "medir" in steps:
        step_medir()
    if "cuerpo" in steps:
        step_cuerpo(arg_after(steps, "cuerpo"))
    if "piel" in steps:
        step_piel(arg_after(steps, "piel"))
    if "articulaciones" in steps:
        step_articulaciones()
    if "exportar" in steps:
        step_exportar(arg_after(steps, "exportar"))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        import traceback
        traceback.print_exc()
        sys.stdout.flush()
        os._exit(1)
    sys.stdout.flush()
    os._exit(0)
