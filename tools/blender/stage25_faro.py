"""
CONCORDIA - Etapa 25: visibilidad del Faro desde las calles (criterio del usuario, E12).

Puntos de calle cada 10 m a 1.7 m sobre el suelo en: 4 avenidas (+ accesos de puerta), 4 diagonales (r 62-190, eje),
2 anillos (r 100 y r 150, tramos de calle) y callejones. Objetivo: la galeria superior del Faro (ultimos 6 m de la
torre y el cristal): 3 puntos en el eje del cristal (z 42.0, 44.5, 47.0) y 3 en el borde de la galeria del lado del
observador (z 41.5, 44.0, 46.5, r 6.2). Un punto de calle ve el Faro si ve >= 2 de los 6.
Avenidas, diagonales y anillos: 100 %; callejones: >= 90 %.

measure() devuelve el porcentaje por tipo de calle y, para cada edificio que tapa, las calles y la altura maxima (sobre
su base) que dejaria pasar todas las visuales que corta.
"""

import math
from collections import Counter, defaultdict

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree

FARO_XY = (50.91, 50.91)
TARGET_AXIS_Z = (42.0, 44.5, 47.0)
TARGET_RING_Z = (41.5, 44.0, 46.5)
RING_R = 6.2
LANDMARKS = ("PORTAL", "OBELISK", "SANTUARIO", "SALON_HAZANAS", "FARO")
STEP = 10.0
EYE = 1.7
SKIP_SUFFIX = ("-colonly", "_LOD1", "_LOD2", "-navmesh", "-occonly", "_InteriorVolume")
SKIP_COLS = ("WALL_KIT", "WALL_KIT_LODS", "BLD_KIT", "BLD_KIT_SHEET", "BLD_KIT_TEST", "BLD_PROPS_LIBRARY",
             "MATERIAL_LIBRARY", "LEGACY_PLACEHOLDERS", "GODOT_CITY_LOD1", "GODOT_CITY_LOD2", "GODOT_CITY_COL",
             "GODOT_EXT_LOD1", "GODOT_EXT_LOD2", "GODOT_NAVMESH", "GODOT_OCCLUDERS", "GODOT_STRUCT_COL", "TERRAIN",
             "EXTERIOR")


def top_root(o):
    while o.parent is not None:
        o = o.parent
    return o


def category(root_name):
    n = root_name
    if n in LANDMARKS:
        return "hito"
    if n.startswith(("TRN_", "EXT_")):
        return "terreno"
    if n.startswith(("WALL_", "GATE_", "TOWER_", "BASTION_", "STAIR_Gate")):
        return "muralla"
    if n.startswith(("MARKER_Bridge", "MARKER_Stairs", "MARKER_Escalinata")):
        return "conexion"
    return "edificio"


def occluders():
    skip = set()
    for cn in SKIP_COLS:
        c = bpy.data.collections.get(cn)
        if c:
            skip |= {o.name for o in c.all_objects}
    verts, faces, owner = [], [], []
    dg = bpy.context.evaluated_depsgraph_get()
    for o in bpy.data.objects:
        if o.type != "MESH" or o.name in skip or o.name.endswith(SKIP_SUFFIX) or o.hide_render:
            continue
        r = top_root(o)
        if r.name == "FARO" or r.name in skip:
            continue
        if any(c.name in SKIP_COLS for c in o.users_collection):
            continue
        me = o.data
        mw = o.matrix_world
        b = len(verts)
        verts += [mw @ v.co for v in me.vertices]
        for p in me.polygons:
            faces.append([b + i for i in p.vertices])
            owner.append(r.name)
    # terreno de la ciudad (chunks LOD0)
    for o in bpy.data.collections["GODOT_CITY_LOD0"].objects:
        me = o.data
        mw = o.matrix_world
        b = len(verts)
        verts += [mw @ v.co for v in me.vertices]
        for p in me.polygons:
            faces.append([b + i for i in p.vertices])
            owner.append("TRN_City")
    _ = dg
    return BVHTree.FromPolygons(verts, faces, epsilon=1e-6), owner


def ground_fn():
    o = bpy.data.objects["TRN_City"]
    bvh = BVHTree.FromObject(o, bpy.context.evaluated_depsgraph_get())

    def g(x, y):
        h = bvh.ray_cast(Vector((x, y, 200)), Vector((0, 0, -1)))
        return h[0].z if h[0] else 6.0
    return g


def resample(pts, step):
    out = [pts[0]]
    acc = 0.0
    for a, b in zip(pts, pts[1:]):
        seg = (b - a).length
        t = step - acc
        while t <= seg:
            out.append(a + (b - a) * (t / seg))
            t += step
        acc = (acc + seg) % step
    return out


def chain(o):
    """Polilinea(s) de un objeto de eje de calle (malla de aristas)."""
    me = o.data
    mw = o.matrix_world
    adj = defaultdict(list)
    for e in me.edges:
        a, b = e.vertices
        adj[a].append(b)
        adj[b].append(a)
    seen, out = set(), []
    for start in [v for v in adj if len(adj[v]) == 1] + list(adj):
        if start in seen:
            continue
        path = [start]
        seen.add(start)
        cur = start
        while True:
            nxt = [n for n in adj[cur] if n not in seen]
            if not nxt:
                break
            cur = nxt[0]
            seen.add(cur)
            path.append(cur)
        if len(path) > 1:
            out.append([mw @ me.vertices[i].co for i in path])
    return out


def streets():
    out = defaultdict(list)          # tipo -> [(nombre, [puntos xy])]
    for o in bpy.data.collections["STREETS_AXES"].objects:
        t = o.get("type")
        if t == "diagonal":
            continue
        kind = {"avenue": "avenida", "ring": "anillo", "alley": "callejon"}.get(t)
        if kind is None:
            continue
        for ln in chain(o):
            out[kind].append((o.name, [Vector((p.x, p.y, 0)) for p in resample(ln, STEP)]))
    for name, ang in (("Diagonal NE", 45), ("Diagonal NO", 135), ("Diagonal SO", 225), ("Diagonal SE", 315)):
        a = math.radians(ang)
        out["diagonal"].append((name, [Vector((r * math.cos(a), r * math.sin(a), 0)) for r in range(62, 191, int(STEP))]))
    return out


def targets_for(eye):
    fx, fy = FARO_XY
    d = Vector((eye.x - fx, eye.y - fy, 0))
    d = d.normalized() if d.length > 1e-6 else Vector((1, 0, 0))
    pts = [Vector((fx, fy, z)) for z in TARGET_AXIS_Z]
    pts += [Vector((fx + d.x * RING_R, fy + d.y * RING_R, z)) for z in TARGET_RING_Z]
    return pts


POINTS = []


def measure(bvh=None, owner=None, need=2):
    if bvh is None:
        bvh, owner = occluders()
    g = ground_fn()
    res = {}
    blockers = defaultdict(lambda: {"streets": Counter(), "rays": [], "points": 0})
    for kind, lst in streets().items():
        n = ok = 0
        by = Counter()
        cat_by = Counter()
        for sname, pts in lst:
            for p in pts:
                if math.hypot(p.x - FARO_XY[0], p.y - FARO_XY[1]) < 12.0:
                    continue
                eye = Vector((p.x, p.y, g(p.x, p.y) + EYE))
                seen, hit_roots = 0, set()
                for t in targets_for(eye):
                    dv = t - eye
                    L = dv.length
                    dn = dv / L
                    o = eye.copy()
                    travelled = 0.0
                    blocked = False
                    for _ in range(12):
                        loc, _n, idx, dist = bvh.ray_cast(o, dn, L - travelled - 0.05)
                        if loc is None:
                            break
                        blocked = True
                        hit_roots.add(owner[idx])
                        travelled += dist + 0.02
                        o = loc + dn * 0.02
                        if travelled >= L - 0.1:
                            break
                    if not blocked:
                        seen += 1
                n += 1
                if seen >= need:
                    ok += 1
                else:
                    POINTS.append({"kind": kind, "street": sname, "eye": tuple(eye), "roots": sorted(hit_roots)})
                    cats = {category(r) for r in hit_roots}
                    for r in hit_roots:
                        by[r] += 1
                        if category(r) == "edificio":
                            b = blockers[r]
                            b["streets"][sname] += 1
                            b["points"] += 1
                            b["rays"].append((tuple(eye), [tuple(t) for t in targets_for(eye)]))
                    for c in cats:
                        cat_by[c] += 1
        res[kind] = {"points": n, "visible": ok, "pct": round(100.0 * ok / max(1, n), 1),
                     "blocked_by": by.most_common(12), "blocked_by_category": dict(cat_by)}
    return res, blockers


def required_height(root, rays):
    """Altura maxima sobre la base del edificio para que ninguna de sus visuales cortadas lo toque (se toma el punto
    mas bajo en que cada visual cruza la caja del edificio)."""
    mw = root.matrix_world
    inv = mw.inverted()
    pts = []
    for o in [root] + list(root.children_recursive):
        if o.type == "MESH" and not o.name.endswith(SKIP_SUFFIX):
            m2 = inv @ o.matrix_world
            pts += [m2 @ Vector(c) for c in o.bound_box]
    if not pts:
        return None
    x0, x1 = min(p.x for p in pts) - 0.3, max(p.x for p in pts) + 0.3
    y0, y1 = min(p.y for p in pts) - 0.3, max(p.y for p in pts) + 0.3
    hreq = 1e9
    for eye, tgts in rays:
        eye = inv @ Vector(eye)
        lows = []
        for t in tgts:
            t = inv @ Vector(t)
            zmin = None
            for k in range(0, 401):
                q = eye + (t - eye) * (k / 400)
                if x0 <= q.x <= x1 and y0 <= q.y <= y1:
                    zmin = q.z if zmin is None else min(zmin, q.z)
            if zmin is not None:
                lows.append(zmin)
        if lows:
            lows.sort()
            # para recuperar el punto basta con liberar >= 2 visuales: la 2a mas baja manda
            hreq = min(hreq, lows[min(1, len(lows) - 1)])
    return None if hreq > 1e8 else round(hreq - 0.3, 2)
