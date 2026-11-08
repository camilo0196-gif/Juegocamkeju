"""
CONCORDIA - Etapa 26 (punto 1): visibilidad del Faro con el criterio nuevo para camara isometrica.

Desde cada punto de calle (ojo a 1.7 m, cada 10 m en avenidas, diagonales, anillos y callejones; los mismos puntos
que stage25_faro) se lanzan 11 rayos: 10 a puntos del haz FARO_Beam en su eje (z 60 a 120 m, equiespaciados) y 1 al
centro del cristal (FARO_Crystal). El punto cuenta como "con Faro" si al menos 1 rayo llega sin obstaculos.
Objetivo: 100 % en avenidas, diagonales y anillos; >= 90 % en callejones. Tambien se cuenta cuantos puntos ven el
cristal directamente y si los tubos de luz (PIPES_Tesoreria_Faro) bloquean algun punto que sin ellos se veria.

Para proponer bajadas (no se aplican sin confirmacion): por cada edificio de decoracion que bloquea, los puntos en
los que es el UNICO obstaculo de algun rayo y la altura a la que tendria que quedar para liberarlo (punto mas bajo en
que ese rayo cruza su caja, menos 0.3 m); minimo permitido 7 m (2 plantas).
"""

import math
from collections import Counter, defaultdict

import bpy
from mathutils import Vector

import stage25_faro as F25

BEAM_Z = [60.0 + 60.0 * k / 9 for k in range(10)]
MIN_DECOR_H = 7.0
DECOR = ("RAZ_B", "Morada_", "OFI_Casa", "CLA_Casa", "MER_Casa", "PuestoProvisiones", "Plazuela_")


def kind_of(name):
    return "decorativo" if name.startswith(DECOR) else "servicio"


def crystal_center():
    o = bpy.data.objects["FARO_Crystal"]
    bb = [o.matrix_world @ Vector(c) for c in o.bound_box]
    return sum(bb, Vector()) / 8


def targets():
    ax = F25.FARO_XY
    return [Vector((ax[0], ax[1], z)) for z in BEAM_Z] + [crystal_center()]


def ray_roots(bvh, owner, eye, t):
    """Raices de todo lo que corta la visual eye -> t."""
    dv = t - eye
    L = dv.length
    dn = dv / L
    o = eye.copy()
    travelled = 0.0
    roots = []
    for _ in range(16):
        loc, _n, idx, dist = bvh.ray_cast(o, dn, L - travelled - 0.05)
        if loc is None:
            break
        if owner[idx] not in roots:
            roots.append(owner[idx])
        travelled += dist + 0.02
        o = loc + dn * 0.02
        if travelled >= L - 0.1:
            break
    return roots


def is_pipe(root):
    return root.startswith(("PIPES_", "PIPE_TF_"))


def measure():
    bvh, owner = F25.occluders()
    g = F25.ground_fn()
    tg = targets()
    res = {}
    sole = defaultdict(lambda: {"points": set(), "rays": []})
    pipe_blocked_points = []
    for kind, lst in F25.streets().items():
        n = ok = crystal = ok_nopipe = 0
        by = Counter()
        blocked_pts = []
        for sname, pts in lst:
            for p in pts:
                if math.hypot(p.x - F25.FARO_XY[0], p.y - F25.FARO_XY[1]) < 12.0:
                    continue
                eye = Vector((p.x, p.y, g(p.x, p.y) + F25.EYE))
                n += 1
                rays = [ray_roots(bvh, owner, eye, t) for t in tg]
                vis = any(not r for r in rays)
                vis_np = any(all(is_pipe(x) for x in r) for r in rays)
                if vis:
                    ok += 1
                if vis_np:
                    ok_nopipe += 1
                if vis_np and not vis:
                    pipe_blocked_points.append({"kind": kind, "street": sname, "eye": [round(c, 1) for c in eye]})
                if not rays[-1]:
                    crystal += 1
                if not vis:
                    roots = sorted({x for r in rays for x in r})
                    blocked_pts.append({"street": sname, "eye": [round(c, 1) for c in eye], "roots": roots})
                    for x in roots:
                        by[x] += 1
                    key = (kind, sname, tuple(round(c, 1) for c in eye))
                    for r, t in zip(rays, tg):
                        if len(r) == 1 and F25.category(r[0]) == "edificio":
                            sole[r[0]]["points"].add(key)
                            sole[r[0]]["rays"].append((key, tuple(eye), tuple(t)))
        res[kind] = {"points": n, "with_faro": ok, "pct": round(100.0 * ok / max(1, n), 1),
                     "crystal_direct": crystal, "crystal_direct_pct": round(100.0 * crystal / max(1, n), 1),
                     "pct_without_pipes": round(100.0 * ok_nopipe / max(1, n), 1),
                     "blocked_by": by.most_common(15), "blocked_points": blocked_pts}
    return res, sole, pipe_blocked_points


def height(r):
    inv = r.matrix_world.inverted()
    hs = [(inv @ (o.matrix_world @ Vector(c))).z for o in [r] + list(r.children_recursive)
          if o.type == "MESH" and not o.name.endswith(F25.SKIP_SUFFIX) for c in o.bound_box]
    return round(max(hs), 2) if hs else None


def needed_height(root, rays):
    """Altura (sobre la base) a la que liberaria TODOS sus puntos: por punto, el mejor de sus rayos (el que cruza su
    caja mas alto); entre puntos, el mas exigente; menos 0.3 m."""
    mw = root.matrix_world
    inv = mw.inverted()
    pts = []
    for o in [root] + list(root.children_recursive):
        if o.type == "MESH" and not o.name.endswith(F25.SKIP_SUFFIX):
            m2 = inv @ o.matrix_world
            pts += [m2 @ Vector(c) for c in o.bound_box]
    if not pts:
        return None
    x0, x1 = min(p.x for p in pts) - 0.3, max(p.x for p in pts) + 0.3
    y0, y1 = min(p.y for p in pts) - 0.3, max(p.y for p in pts) + 0.3
    best = defaultdict(lambda: -1e9)
    for key, eye, t in rays:
        e, tt = inv @ Vector(eye), inv @ Vector(t)
        zmin = None
        for k in range(401):
            q = e + (tt - e) * (k / 400)
            if x0 <= q.x <= x1 and y0 <= q.y <= y1:
                zmin = q.z if zmin is None else min(zmin, q.z)
        if zmin is not None:
            best[key] = max(best[key], zmin)
    if not best:
        return None
    return round(min(best.values()) - 0.3, 2)


def proposal(sole, res, goal):
    """Tabla de bajadas propuestas (solo decoracion), ordenada por puntos que liberaria."""
    rows = []
    for name, d in sole.items():
        r = bpy.data.objects.get(name)
        if r is None:
            continue
        kinds = Counter(k for k, _s, _e in d["points"])
        below = [k for k in kinds if res[k]["pct"] < goal[k]]
        if not below:
            continue
        h_req = needed_height(r, d["rays"])
        rows.append({"name": name, "kind": kind_of(name), "points": len(d["points"]), "by_street_type": dict(kinds),
                     "streets": sorted({s for _k, s, _e in d["points"]}), "h_now": height(r), "h_needed": h_req,
                     "floors": r.get("floors"),
                     "feasible_at_7m": bool(kind_of(name) == "decorativo" and h_req is not None and h_req >= MIN_DECOR_H)})
    rows.sort(key=lambda x: -x["points"])
    return rows
