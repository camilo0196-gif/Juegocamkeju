"""
CONCORDIA - Etapa 26 (E3, punto 8 aprobado): tubos de luz Tesoreria -> Faro sobre CRV_LightPipe_Tesoreria_Faro.

- Primer punto de la curva = MARKER_PipeOutlet_TesoreriaMuralla_02 (salida real de la azotea, +9.6 m sobre el pad):
  se comprueba con un rayo contra la cubierta de la Tesoreria y se deja provisional = false.
- Trazado: la polilinea de 105 puntos se simplifica (Ramer-Douglas-Peucker, 0.5 m) a tramos rectos; en cada quiebro:
  >= 60 grados -> codo de 90 (PIPE_Light_Elbow, radio 0.8 m); 30-60 -> codo de 45 (PIPE_Light_Elbow45, mitad del de 90
  cortada y tapada, misma malla y materiales); < 30 -> junta (los dos rectos se encuentran; la brida tapa la cuna).
- Rectos: PIPE_Light_Straight (2 m) instanciado y estirado en su eje hasta 4 m por pieza (una sola malla compartida).
- Soportes: PIPE_Light_Support cada 8 m de recorrido (fuera de la azotea de salida y del tramo vertical del Faro),
  escalado en Z desde la superficie de abajo (suelo o cubierta) hasta la cara inferior del tubo.
- Holguras: eje del tubo a >= 1.23 m (1 m + radio 0.23) de cualquier edificio (techos y chimeneas incluidos) y a
  >= 0.3 m del Faro salvo en la entrada final; si falla, la curva sube hasta 14 m sobre la calle.
- Presupuesto: <= 8,000 triangulos (rectos + codos + soportes). Material emisivo MAT_Pipe_Light_Core (nucleo).
"""

import math

import bmesh
import bpy
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

CURVE = "CRV_LightPipe_Tesoreria_Faro"
ROOT = "PIPES_Tesoreria_Faro"
R_PIPE = 0.23
R_BEND = 0.8
MAX_PIECE = 4.0
SUPPORT_EVERY = 8.0
BUDGET = 8000
CLEAR_BLD = 1.0 + R_PIPE
CLEAR_FARO = 0.3
SKIP_START = 0.5                 # la boca esta en la azotea: 0.5 m de arranque
OWN = "TesoreriaMuralla"         # el tubo sale de su azotea y cruza su almenara: solo se exige que no la toque
CLEAR_OWN = R_PIPE + 0.02            # 2 cm de aire (regla de la casa)


def rdp(pts, eps):
    if len(pts) < 3:
        return pts
    a, b = pts[0], pts[-1]
    ab = b - a
    dmax, idx = 0.0, 0
    for i in range(1, len(pts) - 1):
        ap = pts[i] - a
        d = (ap - ab * (ap.dot(ab) / ab.length_squared)).length if ab.length > 1e-9 else ap.length
        if d > dmax:
            dmax, idx = d, i
    if dmax > eps:
        return rdp(pts[:idx + 1], eps)[:-1] + rdp(pts[idx:], eps)
    return [a, b]


def elbow45_mesh():
    me = bpy.data.meshes.get("PIPE_Light_Elbow45")
    if me is not None:
        return me
    src = bpy.data.objects["PIPE_Light_Elbow"].data
    bm = bmesh.new()
    bm.from_mesh(src)
    c = Vector((0.0, R_BEND, 0.0))
    n = Vector((math.cos(math.radians(45)), math.sin(math.radians(45)), 0.0))
    geom = bm.verts[:] + bm.edges[:] + bm.faces[:]
    res = bmesh.ops.bisect_plane(bm, geom=geom, plane_co=c, plane_no=n, clear_outer=True)
    cut_edges = [e for e in res["geom_cut"] if isinstance(e, bmesh.types.BMEdge)]
    if cut_edges:
        bmesh.ops.holes_fill(bm, edges=cut_edges, sides=0)
    bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 4])
    me = bpy.data.meshes.new("PIPE_Light_Elbow45")
    bm.to_mesh(me)
    bm.free()
    for m in src.materials:
        me.materials.append(m)
    me["kit_piece"] = True
    me["bend"] = "45 grados, radio 0.8 m (mitad de PIPE_Light_Elbow, etapa 26)"
    return me


def occluders():
    """Edificios (cuerpo, cubierta, props) y el Faro aparte."""
    skip = ("-colonly", "_LOD1", "_LOD2", "-navmesh", "-occonly", "_InteriorVolume")
    vb, fb, vf, ff, vt, ft = [], [], [], [], [], []
    for o in bpy.data.objects:
        if o.type != "MESH" or o.name.endswith(skip) or o.hide_render:
            continue
        r = o
        while r.parent is not None:
            r = r.parent
        cols = {c.name for c in o.users_collection}
        if cols & {"BLD_KIT", "BLD_PIPES", "BLD_PROPS_LIBRARY", "WALL_KIT", "WALL_KIT_LODS", "BLD_KIT_SHEET",
                   "BLD_KIT_TEST", "MATERIAL_LIBRARY"}:
            continue
        if not any(c.startswith(("BLD_", "WALL_LAYOUT")) for c in cols) and r.name != "FARO":
            continue
        if o.name == "FARO_Beam":
            continue
        tv, tf = (vf, ff) if r.name == "FARO" else ((vt, ft) if r.name == OWN else (vb, fb))
        mw = o.matrix_world
        b = len(tv)
        tv += [mw @ v.co for v in o.data.vertices]
        tf += [[b + i for i in p.vertices] for p in o.data.polygons]
    return (BVHTree.FromPolygons(vb, fb, epsilon=1e-6), BVHTree.FromPolygons(vf, ff, epsilon=1e-6),
            BVHTree.FromPolygons(vt, ft, epsilon=1e-6))


def clearance(path, bvh_b, bvh_f, skip_start=1.5, skip_end_from=None, bvh_t=None):
    """Distancia minima del eje a edificios y al Faro, muestreando cada 0.25 m."""
    worst_b, worst_f, bad = 1e9, 1e9, []
    s_acc = 0.0
    total = sum((path[i + 1] - path[i]).length for i in range(len(path) - 1))
    for i in range(len(path) - 1):
        a, b = path[i], path[i + 1]
        L = (b - a).length
        n = max(1, int(L / 0.25))
        for k in range(n + 1):
            s = s_acc + L * k / n
            p = a + (b - a) * (k / n)
            if s < skip_start:
                continue
            db = bvh_b.find_nearest(p, 10.0)[3]
            db = 10.0 if db is None else db
            df = bvh_f.find_nearest(p, 10.0)[3]
            df = 10.0 if df is None else df
            end_zone = skip_end_from is not None and s > total - skip_end_from
            dt = bvh_t.find_nearest(p, 10.0)[3] if bvh_t is not None else None
            if dt is not None and dt < CLEAR_OWN:
                bad.append((round(s, 1), tuple(round(c, 1) for c in p), "toca la Tesoreria", round(dt, 2)))
            worst_b = min(worst_b, db)
            if not end_zone:
                worst_f = min(worst_f, df)
            if db < CLEAR_BLD or (not end_zone and df < CLEAR_FARO):
                bad.append((round(s, 1), tuple(round(c, 1) for c in p), round(db, 2), round(df, 2)))
        s_acc += L
    return worst_b, worst_f, bad


def frame(x_axis, up=Vector((0, 0, 1))):
    x = x_axis.normalized()
    y = up.cross(x)
    if y.length < 1e-6:
        y = Vector((0, 1, 0)).cross(x)
    y.normalize()
    z = x.cross(y)
    return Matrix((x, y, z)).transposed()


def place(name, me, col, parent, mw):
    o = bpy.data.objects.new(name, me)
    col.objects.link(o)
    o.parent = parent
    o.matrix_world = mw
    return o


def build(path, col, root, g, st):
    straight = bpy.data.objects["PIPE_Light_Straight"].data
    elbow90 = bpy.data.objects["PIPE_Light_Elbow"].data
    elbow45 = elbow45_mesh()
    n = len(path)
    dirs = [(path[i + 1] - path[i]).normalized() for i in range(n - 1)]
    fittings = {}
    for i in range(1, n - 1):
        a, b = dirs[i - 1], dirs[i]
        ang = math.degrees(a.angle(b))
        if ang >= 60:
            fittings[i] = (90, R_BEND * math.tan(math.radians(45)), elbow90, ang)
        elif ang >= 30:
            fittings[i] = (45, R_BEND * math.tan(math.radians(22.5)), elbow45, ang)
        else:
            fittings[i] = (0, 0.0, None, ang)
    objs = {"straight": [], "elbow90": [], "elbow45": [], "support": []}
    log = {"bends": []}
    # codos
    for i, (kind, t, me, ang) in fittings.items():
        log["bends"].append({"at": [round(c, 2) for c in path[i]], "angle": round(ang, 1),
                             "piece": {90: "codo 90", 45: "codo 45", 0: "junta"}[kind]})
        if not kind:
            continue
        a, b = dirs[i - 1], dirs[i]
        y = (b - a * b.dot(a))
        y = y.normalized() if y.length > 1e-6 else a.orthogonal().normalized()
        z = a.cross(y)
        rot = Matrix((a, y, z)).transposed().to_4x4()
        inlet = path[i] - a * t
        nm = f"PIPE_TF_Elbow{kind}_{len(objs[f'elbow{kind}']) + 1:02d}"
        objs[f"elbow{kind}"].append(place(nm, me, col, root, Matrix.Translation(inlet) @ rot))
    # rectos entre puertos
    for i in range(n - 1):
        a = path[i] + dirs[i] * (fittings[i][1] if i in fittings else 0.0)
        b = path[i + 1] - dirs[i] * (fittings[i + 1][1] if (i + 1) in fittings else 0.0)
        L = (b - a).length
        if L < 0.05:
            continue
        k = max(1, math.ceil(L / MAX_PIECE))
        seg = L / k
        rot = frame(dirs[i]).to_4x4()
        for j in range(k):
            p = a + dirs[i] * (seg * j)
            mw = Matrix.Translation(p) @ rot @ Matrix.Diagonal((seg / 2.0, 1.0, 1.0, 1.0))
            objs["straight"].append(place(f"PIPE_TF_Straight_{len(objs['straight']) + 1:02d}", straight, col, root, mw))
    # soportes cada 8 m (tramos casi horizontales), fuera de la salida y del descenso al Faro
    sup = bpy.data.objects["PIPE_Light_Support"].data
    h_sup = 9.228
    total = sum((path[i + 1] - path[i]).length for i in range(n - 1))
    s_acc = 0.0
    next_s = SUPPORT_EVERY
    dg = bpy.context.evaluated_depsgraph_get()
    scene = bpy.context.scene
    rows = []
    for i in range(n - 1):
        a, b = path[i], path[i + 1]
        L = (b - a).length
        horiz = abs(dirs[i].z) < 0.7                     # todo tramo no vertical (incluida la bajada al Faro)
        while next_s <= s_acc + L:
            p = a + (b - a) * ((next_s - s_acc) / L)
            if horiz and 2.0 < next_s < total - 2.0:
                o = p - Vector((0, 0, R_PIPE + 0.05))
                hit, loc, _nr, _ix, ob, _m = scene.ray_cast(dg, o, Vector((0, 0, -1)), distance=40.0)
                while hit and (ob.name.endswith(("-colonly", "_LOD1", "_LOD2", "-navmesh", "_InteriorVolume")) or
                               ob.name.startswith("PIPE_") or ob.hide_render):
                    hit, loc, _nr, _ix, ob, _m = scene.ray_cast(dg, loc - Vector((0, 0, 0.01)), Vector((0, 0, -1)), distance=40.0)
                if hit and ("Water" in ob.name or ob.name.startswith("CAU_Water")):
                    moved = False
                    for dsh in (0.75, -0.75, 1.5, -1.5, 2.25, -2.25, 3.0, -3.0):
                        q = p + dirs[i] * dsh
                        h2 = scene.ray_cast(dg, q - Vector((0, 0, R_PIPE + 0.05)), Vector((0, 0, -1)), distance=40.0)
                        if h2[0] and "Water" not in h2[4].name and not h2[4].name.endswith(("-colonly", "_LOD1", "_LOD2")):
                            p, hit, loc, ob, moved = q, True, h2[1], h2[4], True
                            break
                    if not moved:
                        rows.append({"s_m": round(next_s, 1), "skipped": "cae en el agua del Cauce"})
                        next_s += SUPPORT_EVERY
                        continue
                zb = loc.z if hit else g(p.x, p.y)
                hgt = (p.z - R_PIPE) - zb
                yaw = math.atan2(dirs[i].y, dirs[i].x) - math.pi / 2
                mw = (Matrix.Translation((p.x, p.y, zb)) @ Matrix.Rotation(yaw, 4, "Z") @
                      Matrix.Diagonal((1.0, 1.0, hgt / h_sup, 1.0)))
                so = place(f"PIPE_TF_Support_{len(objs['support']) + 1:02d}", sup, col, root, mw)
                so["stands_on"] = ob.name if hit else "terreno"
                so["height_m"] = round(hgt, 2)
                objs["support"].append(so)
                rows.append({"s_m": round(next_s, 1), "xy": [round(p.x, 1), round(p.y, 1)], "height_m": round(hgt, 2),
                             "on": ob.name if hit else "terreno"})
            next_s += SUPPORT_EVERY
        s_acc += L
    log["supports"] = rows
    return objs, log


def tris_me(me):
    return sum(len(p.vertices) - 2 for p in me.polygons)


def step(st):
    import build_stage18 as B18
    g = B18.ground_fn()
    crv = bpy.data.objects[CURVE]
    col = crv.users_collection[0]
    # 1) primer punto = salida real de la azotea
    outlet = bpy.data.objects["MARKER_PipeOutlet_TesoreriaMuralla_02"].matrix_world.translation.copy()
    sp = crv.data.splines[0]
    p0 = crv.matrix_world @ sp.points[0].co.xyz
    dg = bpy.context.evaluated_depsgraph_get()
    hit, loc, _n, _i, ob, _m = bpy.context.scene.ray_cast(dg, outlet + Vector((0, 0, 0.3)), Vector((0, 0, -1)), distance=3.0)
    while hit and ob.name.endswith(("-colonly", "_LOD1", "_LOD2")):
        hit, loc, _n, _i, ob, _m = bpy.context.scene.ray_cast(dg, loc - Vector((0, 0, 0.01)), Vector((0, 0, -1)), distance=3.0)
    if (p0 - outlet).length > 0.01:
        sp.points[0].co = (*(crv.matrix_world.inverted() @ outlet), 1.0)
    crv["provisional_first_point"] = False
    if "provisional" in crv:
        del crv["provisional"]
    mk = bpy.data.objects.get("MARKER_PipeOutlet_TesoreriaMuralla")
    if mk is not None:
        mk["provisional"] = False
    first = {"outlet": [round(c, 2) for c in outlet], "curve_first_point_before": [round(c, 2) for c in p0],
             "moved_m": round((p0 - outlet).length, 3), "roof_below": ob.name if hit else None,
             "outlet_over_roof_m": round(outlet.z - loc.z, 2) if hit else None,
             "note": "el primer punto ya estaba en la salida real desde la etapa 18; provisional = false"}
    # 2) trazado simplificado y holguras (subiendo si hace falta)
    pts = [crv.matrix_world @ p.co.xyz for p in sp.points]
    path = rdp(pts, 0.5)
    bvh_b, bvh_f, bvh_t = occluders()
    street = [g(p.x, p.y) for p in path]
    raise_log = []
    lift = 0.0
    while True:
        test = [path[0]] + [p + Vector((0, 0, lift)) for p in path[1:-3]] + path[-3:]
        wb, wf, bad = clearance(test, bvh_b, bvh_f, skip_start=SKIP_START, skip_end_from=6.0, bvh_t=bvh_t)
        h_over = max(p.z - z for p, z in zip(test[1:-3], street[1:-3]))
        raise_log.append({"lift_m": lift, "max_over_street_m": round(h_over, 2), "min_to_building_m": round(wb, 2),
                          "min_to_faro_m": round(wf, 2), "violations": len(bad), "examples": bad[:4]})
        if not bad or h_over + 0.5 > 14.0:
            break
        lift += 0.5
    path = test
    if lift:
        # la subida necesita un tramo vertical en la salida y en la llegada (los codos de 90 se anaden solos)
        path = [path[0], path[0] + Vector((0, 0, lift))] + path[1:]
    # 3) piezas
    old = bpy.data.objects.get(ROOT)
    if old is not None:
        for o in list(old.children_recursive) + [old]:
            bpy.data.objects.remove(o)
    root = bpy.data.objects.new(ROOT, None)
    col.objects.link(root)
    root["pipe"] = "Tesoreria -> Faro (luz azul, MAT_Pipe_Light_Core)"
    objs, log = build(path, col, root, g, st)
    # 4) marcadores de soporte = soportes colocados
    for o in [o for o in col.objects if o.name.startswith("MARKER_PipeSupport_")]:
        bpy.data.objects.remove(o)
    for k, so in enumerate(objs["support"], 1):
        m = bpy.data.objects.new(f"MARKER_PipeSupport_{k:02d}", None)
        col.objects.link(m)
        m.location = so.matrix_world.translation
        m["piece"] = so.name
        m["support_height_m"] = so["height_m"]
    t = {"straight": len(objs["straight"]) * tris_me(objs["straight"][0].data) if objs["straight"] else 0,
         "elbow90": len(objs["elbow90"]) * tris_me(bpy.data.objects["PIPE_Light_Elbow"].data),
         "elbow45": len(objs["elbow45"]) * tris_me(elbow45_mesh()),
         "support": len(objs["support"]) * tris_me(bpy.data.objects["PIPE_Light_Support"].data)}
    t["total"] = sum(t.values())
    length = sum((path[i + 1] - path[i]).length for i in range(len(path) - 1))
    st["pipes"] = {"first_point": first, "path_vertices": len(path), "length_m": round(length, 1),
                   "pieces": {k: len(v) for k, v in objs.items()}, "tris": t, "budget": BUDGET,
                   "ok_budget": t["total"] <= BUDGET, "raise": raise_log, "lift_applied_m": lift,
                   "clearance_ok": not raise_log[-1]["violations"], "bends": log["bends"], "supports": log["supports"],
                   "max_piece_m": MAX_PIECE}
    print("pipes", st["pipes"]["pieces"], t, raise_log[-1], flush=True)
