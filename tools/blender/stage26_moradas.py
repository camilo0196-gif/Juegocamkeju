"""
CONCORDIA - Etapa 26 (E10, punto 2 aprobado): Moradas NE y SO sin galerias corridas.

Cada habitacion (casa comunal) de NE y SO pasa a UN balcon por puerta en las plantas 2 y 3 (1.5 x 0.6 m) y la
escalera exterior se orienta segun CAM_Iso (stair_side). Misma huella (6 x 10), misma altura y misma seccion;
tablas de dos tonos y una tabla de remiendo por casa. door_check() repite la prueba de puertas de la etapa 24
(3 alturas 0.3 / 1.1 / 2.0 m; tapada si se ocultan >= 2) sobre las 4 Moradas.
"""

import math

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree

CAM_BACK = Vector((0.577, -0.577, 0.577)).normalized()


def cam_x_sign(root):
    loc = root.matrix_world.inverted().to_3x3() @ CAM_BACK
    return 1 if loc.x > 0 else -1


def stair_for(root, mode):
    """mode 'far': el tramo alto y el rellano superior quedan en el extremo mas alejado de la camara (el pie de la
    escalera en el extremo cercano); 'near': al reves."""
    c = cam_x_sign(root)
    return c if mode == "far" else -c


def rebuild(keys=("NE", "SO"), mode="far"):
    import build_stage23 as B23
    out = []
    for key in keys:
        col = bpy.data.collections[f"BLD_MORADAS_{key}"]
        houses = {h["marker"].name: h for h in B23.collect(key)}
        for r in [o for o in col.objects if o.parent is None and o.type == "EMPTY" and o.name.startswith(f"Morada_{key}_")]:
            if r.get("tipo") != "habitacion":
                continue
            sec = r["section"]
            h = houses[r["marker"]]
            plan = {"floors": int(sec[1]), "roof": {"l": "lean", "g": "gable", "c": "catslide"}[sec[2]],
                    "low_side": {"b": "back", "f": "front", "n": None}[sec[3]]}
            pitch = sec[4:].split("_")[0]
            if plan["roof"] != "lean":
                plan["pitch"] = float(pitch) if pitch else 32.0
            plan.update(balcony=True, stair=stair_for(r, mode))
            h["plan"] = plan
            rem = str(r.get("remedies", "-"))
            h["remedies"] = ([rem] if rem not in ("-", "") else []) + ["balcon por puerta (etapa 26)"]
            for o in list(r.children_recursive) + [r]:
                bpy.data.objects.remove(o)
            B23.build_house(h, key, col, col)
            out.append(h["name"])
    bpy.context.view_layer.update()
    return out


def door_check(keys=("NE", "NO", "SE", "SO")):
    occ = []
    for key in keys:
        for r in bpy.data.collections[f"BLD_MORADAS_{key}"].objects:
            if r.parent is None and r.type == "EMPTY" and r.name.startswith("Morada_"):
                for part in ("Body", "Roof"):
                    o = bpy.data.objects.get(f"{r.name}_{part}")
                    if o is not None:
                        occ.append((r.name, o))
    verts, faces, owner = [], [], []
    for name, o in occ:
        mw = o.matrix_world
        b = len(verts)
        verts += [mw @ v.co for v in o.data.vertices]
        for p in o.data.polygons:
            faces.append([b + i for i in p.vertices])
            owner.append(name)
    bvh = BVHTree.FromPolygons(verts, faces, epsilon=1e-6)
    cxy = Vector((CAM_BACK.x, CAM_BACK.y, 0)).normalized()
    res = {k: {"doors": 0, "facing": 0, "blocked": []} for k in keys}
    for key in keys:
        for r in bpy.data.collections[f"BLD_MORADAS_{key}"].objects:
            if not (r.parent is None and r.type == "EMPTY" and r.name.startswith("Morada_")):
                continue
            for dm in [c for c in r.children if c.name.startswith("MARKER_Morada_Door_")]:
                res[key]["doors"] += 1
                mw = dm.matrix_world
                n = (mw.to_3x3() @ Vector((0, 1, 0))).normalized()
                if n.dot(cxy) < -0.05:
                    continue
                res[key]["facing"] += 1
                hidden, by = 0, None
                for hgt in (0.3, 1.1, 2.0):
                    o = mw.translation + n * 0.35 + Vector((0, 0, hgt))
                    for _ in range(10):
                        loc, _n, idx, _d = bvh.ray_cast(o, CAM_BACK, 500.0)
                        if loc is None:
                            break
                        if owner[idx] == r.name:
                            o = loc + CAM_BACK * 0.02
                            continue
                        hidden += 1
                        by = owner[idx]
                        break
                if hidden >= 2:
                    res[key]["blocked"].append((dm.name, by))
    return res


_ = math


def set_stair(root, s):
    """Reconstruye una habitacion con balcones con la escalera en el lado s (+1 / -1)."""
    import build_stage23 as B23
    key = root.name.split("_")[1]
    col = bpy.data.collections[f"BLD_MORADAS_{key}"]
    h = {hh["marker"].name: hh for hh in B23.collect(key)}[root["marker"]]
    sec = root["section"]
    plan = {"floors": int(sec[1]), "roof": {"l": "lean", "g": "gable", "c": "catslide"}[sec[2]],
            "low_side": {"b": "back", "f": "front", "n": None}[sec[3]], "balcony": True, "stair": s}
    pitch = sec[4:].split("_")[0]
    if plan["roof"] != "lean":
        plan["pitch"] = float(pitch) if pitch else 32.0
    h["plan"] = plan
    h["remedies"] = [str(root.get("remedies", "-"))]
    name = root.name
    for o in list(root.children_recursive) + [root]:
        bpy.data.objects.remove(o)
    B23.build_house(h, key, col, col)
    bpy.context.view_layer.update()
    return bpy.data.objects[name]


def greedy(keys=("NE", "SO"), rounds=3, log=None):
    """Cambia el lado de la escalera de una casa si baja el total de puertas tapadas (por casa que tapa)."""
    def total():
        r = door_check(keys)
        return sum(len(v["blocked"]) for v in r.values()), r
    best, res = total()
    hist = [best]
    for _ in range(rounds):
        improved = False
        culprits = sorted({b for v in res.values() for _d, b in v["blocked"]
                           if b and bpy.data.objects[b].get("tipo") == "habitacion"})
        for name in culprits:
            r = bpy.data.objects[name]
            s0 = int(r["section"].endswith("_bp")) * 2 - 1
            set_stair(r, -s0)
            t, res2 = total()
            if t < best:
                best, res, improved = t, res2, True
                hist.append(best)
            else:
                set_stair(bpy.data.objects[name], s0)
        if not improved:
            break
    if log is not None:
        log["greedy_history"] = hist
    return best, res
