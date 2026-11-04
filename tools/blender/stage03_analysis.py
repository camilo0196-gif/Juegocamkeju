"""
CONCORDIA - Etapa 03: comprobaciones de la Plaza del Portal.

- zona despejada r 15..48: ningun vertice de pieza por encima del suelo.
- canales: a que profundidad queda la tira emisiva respecto al suelo.
- pendientes de la plaza tras las ondulaciones.
- cima del Faro (base + 40 m): visibilidad desde puntos de calle (altura de ojo 1.7 m)
  contra terreno + estructuras + piezas de la plaza (aun sin edificios).
- oclusion en CAM_Iso: que marcadores / puntos de calle quedan tapados por los volumenes
  futuros del Faro (40 m) y del Obelisco (25 m) (proxies temporales, no se guardan).
"""

import os
import sys
from math import acos, cos, degrees, radians, sin, sqrt

import bpy  # noqa: I001
from mathutils import Vector
from mathutils.bvhtree import BVHTree

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import concordia_const as C  # noqa: E402
import terrain_profile as T  # noqa: E402
import stage03_plaza as P3  # noqa: E402

EYE = 1.7


def world_bvh(objs):
    dg = bpy.context.evaluated_depsgraph_get()
    verts, polys = [], []
    for o in objs:
        ev = o.evaluated_get(dg)
        me = ev.to_mesh()
        mw = o.matrix_world
        off = len(verts)
        verts += [mw @ v.co for v in me.vertices]
        polys += [[off + i for i in p.vertices] for p in me.polygons]
        ev.to_mesh_clear()
    return BVHTree.FromPolygons(verts, polys)


def proxy_bvh(faro_top_z, obelisco_top_z):
    """Cilindro del Faro y prisma del Obelisco (solo para el analisis)."""
    verts, polys = [], []

    def add_prism(pts2d, z0, z1):
        off = len(verts)
        n = len(pts2d)
        for z in (z0, z1):
            verts.extend(Vector((x, y, z)) for x, y in pts2d)
        polys.append(list(range(off, off + n)))
        polys.append(list(range(off + 2 * n - 1, off + n - 1, -1)))
        for i in range(n):
            j = (i + 1) % n
            polys.append([off + i, off + j, off + n + j, off + n + i])

    fa, fr, _s, fd, _h = C.LANDMARK_PADS["Faro"]
    cx, cy, _ = C.polar(fa, fr)
    R = fd[0] / 2
    add_prism([(cx + R * cos(radians(i * 360 / 32)), cy + R * sin(radians(i * 360 / 32))) for i in range(32)],
              faro_top_z - 40.0, faro_top_z)
    oa, orr, _s, od, _h = C.LANDMARK_PADS["Obelisco"]
    ox, oy, _ = C.polar(oa, orr)
    h = od[0] / 2
    pts = P3.footprint_rect(oa, orr - h, orr + h, -h, h)
    add_prism(pts, obelisco_top_z - 25.0, obelisco_top_z)
    return BVHTree.FromPolygons(verts, polys)


def street_points(zfun):
    pts = []
    for key, a in T.CARDINAL_ANGLE.items():
        for u in range(62, 197, 4):
            x, y = P3.from_uv(u, 0.0, a)
            pts.append((f"avenida {key}", x, y))
    for key, a in T.DIAGONAL_ANGLE.items():
        for u in range(62, 197, 4):
            x, y = P3.from_uv(u, 0.0, a)
            pts.append((f"calle diagonal {key}", x, y))
    for R in (30.0, 100.0, 150.0, 185.0):
        for i in range(36):
            x, y, _ = C.polar(i * 10.0, R)
            pts.append((f"anillo r={R:.0f}", x, y))
    return [(n, x, y, zfun(x, y) + EYE) for n, x, y in pts]


def build(scene, stats):
    trn = bpy.data.objects["TRN_City"]
    plaza_meshes = [o for o in bpy.data.collections["PLAZA"].objects if o.type == "MESH"]
    structs = [o for cn in ("MORADAS", "STREETS") for o in bpy.data.collections[cn].objects if o.type == "MESH"]
    terr_bvh = world_bvh([trn])
    all_bvh = world_bvh([trn] + structs + plaza_meshes)

    def zt(x, y):
        hit = terr_bvh.ray_cast(Vector((x, y, 200.0)), Vector((0, 0, -1)))
        return hit[0].z if hit[0] else T.height(x, y)

    def ztop(x, y):
        hit = all_bvh.ray_cast(Vector((x, y, 200.0)), Vector((0, 0, -1)))
        return hit[0].z if hit[0] else zt(x, y)

    out = {}
    # --- zona despejada
    r0, r1 = P3.R_ATRIO_OUT + 0.01, C.PLAZA_CLEAR_R[1]
    offenders = {}
    for o in plaza_meshes + structs:
        if o.name == "TRN_LightCanals":
            continue
        n = 0
        mw = o.matrix_world
        for v in o.data.vertices:
            w = mw @ v.co
            r = sqrt(w.x * w.x + w.y * w.y)
            if r0 < r < r1 and w.z > zt(w.x, w.y) + 0.01:
                n += 1
        if n:
            offenders[o.name] = n
    out["clear_zone"] = {"range_r": [C.PLAZA_CLEAR_R[0], C.PLAZA_CLEAR_R[1]],
                         "note": f"de r=15 a {P3.R_ATRIO_OUT:.2f} estan los peldanos perimetrales del Atrio",
                         "objects_above_ground_between_r": [round(r0, 2), r1], "offenders": offenders}
    # --- canales: profundidad real bajo el suelo vecino
    can = bpy.data.objects["TRN_LightCanals"]
    deep = []
    for v in can.data.vertices:
        w = can.matrix_world @ v.co
        u, vv = P3.to_uv(w.x, w.y, P3.CANAL_AXIS)
        if P3.R_ATRIO_OUT + 0.5 < u < P3.FARO_R - 8:
            side = min(P3.CANAL_OFFSETS, key=lambda c: abs(vv - c))
            sx, sy = P3.from_uv(u, side + (0.25 if vv >= side else -0.25), P3.CANAL_AXIS)
            deep.append(zt(sx, sy) - w.z)
    out["canals_depth_below_floor_m"] = {"min": round(min(deep), 4), "max": round(max(deep), 4)}
    # --- pendientes de la plaza (fuera de los surcos)
    sl, groove, micro = [], [], []
    me = trn.data
    for p in me.polygons:
        c = p.center
        r = sqrt(c.x * c.x + c.y * c.y)
        if P3.R_ATRIO_OUT < r < C.PLAZA_RADIUS:
            s = degrees(acos(min(1.0, p.normal.z)))
            if P3.canal_distance(c.x, c.y) <= C.LIGHT_CANAL_WIDTH / 2 + 0.005:
                groove.append(s)
                continue
            if s > C.WALK_SLOPE_MAX:
                zs = [me.vertices[i].co.z for i in p.vertices]
                if max(zs) - min(zs) <= C.TERRAIN_NOISE_PP:
                    micro.append((round(s, 2), round(max(zs) - min(zs), 4), round(p.area, 4)))
                    continue
            sl.append(s)
    sl.sort()
    out["plaza_slope_deg"] = {"max": round(sl[-1], 2), "p99": round(sl[int(0.99 * (len(sl) - 1))], 2),
                              "faces": len(sl), "gt5": sum(1 for v in sl if v > C.WALK_SLOPE_MAX),
                              "micro_faces_gt5_span_le5cm": len(micro), "micro_sample": micro[:5],
                              "groove_wall_max": round(max(groove), 1) if groove else None}
    # --- Faro: visibilidad de la cima
    pads = stats.get("landmark_pads", {})
    faro_top = pads["Faro"]["top"] + 40.0
    obel_top = pads["Obelisco"]["top"] + 25.0
    fx, fy = pads["Faro"]["center"]
    target = Vector((fx, fy, faro_top))
    vis = {}
    for name, x, y, z in street_points(ztop):
        o = Vector((x, y, z))
        d = target - o
        hit = all_bvh.ray_cast(o, d.normalized(), d.length - 0.5)
        ok = hit[0] is None
        g = vis.setdefault(name, [0, 0])
        g[0] += int(ok)
        g[1] += 1
    tot = sum(v[1] for v in vis.values())
    ok_all = sum(v[0] for v in vis.values())
    out["faro_top_visibility"] = {"top_z": round(faro_top, 2), "visible": ok_all, "samples": tot,
                                  "by_group": {k: f"{v[0]}/{v[1]}" for k, v in vis.items()},
                                  "note": "sin edificios todavia; hay que repetirlo cuando existan"}
    # --- oclusion en la vista isometrica por los volumenes futuros
    pb = proxy_bvh(faro_top, obel_top)
    cam = bpy.data.objects[C.CAM_ISO_NAME]
    to_cam = -(cam.rotation_euler.to_matrix() @ Vector((0, 0, -1)))
    checks = [(o.name, o.location.copy()) for o in bpy.data.collections["PLAZA_MARKERS"].objects
              if o.name not in ("MARKER_Faro", "MARKER_Obelisco")]
    checks += [(n, bpy.data.objects[n].location.copy()) for n in C.GATES]
    for key, a in T.CARDINAL_ANGLE.items():
        for u in range(60, 200, 5):
            x, y = P3.from_uv(u, 0.0, a)
            checks.append((f"eje avenida {key} u={u}", Vector((x, y, zt(x, y) + 0.1))))
    for key, a in T.DIAGONAL_ANGLE.items():
        for u in range(60, 200, 5):
            x, y = P3.from_uv(u, 0.0, a)
            checks.append((f"eje calle {key} u={u}", Vector((x, y, ztop(x, y) + 0.1))))
    hidden = [n for n, p in checks if pb.ray_cast(p + to_cam * 0.05, to_cam)[0] is not None]
    out["iso_occlusion_by_future_volumes"] = {"proxies": "Faro cilindro 14 x 40 m, Obelisco 5 x 5 x 25 m",
                                              "checked": len(checks), "hidden": hidden}
    stats["plaza_checks"] = out
    return out
