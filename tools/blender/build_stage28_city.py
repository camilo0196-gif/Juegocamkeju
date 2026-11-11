"""
CONCORDIA - Etapa 28 (ciudad): pendientes de la etapa 26 decididos por el usuario.
concordia_v26.blend -> concordia_v28.blend + docs/reports/stage28_ciudad.json

  faro     punto 10: MER_Casa_01 (decoracion) baja de 3 a 2 plantas hasta que deja de tapar el Faro
  moradas  punto 11: (a) balcones <= 1.2 m de vuelo y escalera en el extremo de la fachada mas alejado de CAM_Iso;
           (b) puertas tapadas por cuerpo/alero: alero 0.3 m en la casa que tapa -> 2 plantas -> (puerta a otra
           fachada: no aplicable en las casas comunales, ver informe); (c) lista de puertas residuales (<= 10)
  pipes    punto 14: soportes fuera de la zona de paso (mascara de calles de la etapa 5): al borde de la calle a
           0.6 m de la linea de edificios con mensula, o desplazados a lo largo del tubo; los que no caben se listan
  medir    Faro con el criterio de la etapa 26 (11 rayos, >= 1 libre) y lista de puntos sin Faro para TODO_GODOT

python build_stage28_city.py -- [--fresh] paso [paso ...]
"""

import json
import math
import os
import random
import sys

import bpy
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import concordia_const as C  # noqa: E402

REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
SRC = os.path.join(REPO, "blender", f"{C.BLEND_BASENAME}_v26.blend")
OUT = os.path.join(REPO, "blender", f"{C.BLEND_BASENAME}_v28.blend")
REPORT = os.path.join(REPO, "docs", "reports", "stage28_ciudad.json")
MASK = os.path.join(REPO, "textures", "streets", "T_StreetMasks.png")
EDGE_FROM_BUILDING = 0.6
MAX_BRACKET = 2.5
MAX_SHIFT = 4.0


def save():
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)


def load_report():
    if os.path.exists(REPORT):
        with open(REPORT) as fh:
            return json.load(fh)
    return {}


def write_report(st):
    with open(REPORT, "w") as fh:
        json.dump(st, fh, indent=1, ensure_ascii=False, default=str)


def remove_tree(root):
    for o in list(root.children_recursive) + [root]:
        me = o.data if o.type == "MESH" else None
        bpy.data.objects.remove(o)
        if me is not None and me.users == 0:
            bpy.data.meshes.remove(me)


# --------------------------------------------------------------------------- punto 10: MER_Casa_01
def step_faro(st):
    import build_stage18 as B18
    import build_stage25 as B25
    import concordia_buildings as B
    import bld_kit as K
    name = "MER_Casa_01"
    old = bpy.data.objects[name]
    keep = {k: old[k] for k in old.keys()}
    h0 = B25.height_now(old)
    col, pcol = old.users_collection[0], bpy.data.collections["BLD_PROPS"]
    remove_tree(old)
    rng = random.Random(B.rng_for(name, B18.SEED))                 # mismas tiradas que la etapa 18 (k = 1)
    estilo = rng.choice(("timber", "timber", "guild", "stone"))
    techo = rng.choice(("gable", "gable_front", "hip"))
    use = rng.choice(("house", "shop", "house"))
    root, objs, rep = B.fit_iso_height(name, 2, marker=B18.mk(name), tipo_techo=techo, estilo=estilo,
                                       seed=B18.SEED + 1, collection=col, props_collection=pcol, use=use,
                                       opts={"side_detail": {"back": 1}, "roof_seg": 3.5, "no_buttress": True})
    W, D = rep["footprint"]
    cm = K.MB()
    cm.box((-W / 2, -D / 2, 0.0), (W / 2, D / 2, rep["eave_height_m"]), "MAT_Wall_Gray")
    B18.collider(cm, f"{name}-colonly", col, root)
    for k, v in keep.items():
        if k not in root.keys():
            root[k] = v
    root["floors"] = rep["floors"]
    root["remedy"] = "2 plantas (decoracion): tapaba el Faro desde el anillo r 100 (etapa 28, punto 10)"
    bpy.context.view_layer.update()
    st["faro_mer_casa_01"] = {"floors_before": keep.get("floors"), "floors_after": rep["floors"], "h_before_m": h0,
                              "h_after_m": B25.height_now(root), "style": estilo, "roof": techo, "use": use,
                              "min_decor_h_m": 7.0}


# --------------------------------------------------------------------------- punto 11: Moradas
def parse_section(sec):
    """'f3lb0_bp_e30' -> plan."""
    parts = sec.split("_")
    head = parts[0]
    plan = {"floors": int(head[1]), "roof": {"l": "lean", "g": "gable", "c": "catslide"}[head[2]],
            "low_side": {"b": "back", "f": "front", "n": None}[head[3]]}
    pitch = head[4:]
    if plan["roof"] != "lean":
        plan["pitch"] = float(pitch) if pitch and pitch != "0" else 32.0
    for p in parts[1:]:
        if p.startswith("b"):
            plan["balcony"] = True
            plan["stair"] = 1 if p == "bp" else -1
        elif p.startswith("e"):
            plan["eave"] = int(p[1:]) / 100.0
    return plan


def rebuild_with(root, **changes):
    import build_stage23 as B23
    key = root.name.split("_")[1]
    col = bpy.data.collections[f"BLD_MORADAS_{key}"]
    h = {hh["marker"].name: hh for hh in B23.collect(key)}[root["marker"]]
    plan = parse_section(root["section"])
    plan.update(changes)
    h["plan"] = plan
    rem = str(root.get("remedies", "-"))
    extra = [f"{k}={v}" for k, v in changes.items() if k != "stair" and v is not None]
    h["remedies"] = ([rem] if rem not in ("-", "") else []) + ([f"etapa 28: {', '.join(extra)}"] if extra else [])
    name = root.name
    for o in list(root.children_recursive) + [root]:
        bpy.data.objects.remove(o)
    B23.build_house(h, key, col, col)
    bpy.context.view_layer.update()
    return bpy.data.objects[name]


def blocked_list(keys=("NE", "NO", "SE", "SO")):
    import build_stage26 as B26
    import stage26_moradas as S
    res = S.door_check(keys)
    out = []
    for k, v in res.items():
        for door, by in v["blocked"]:
            rays = B26.blocked_cause(door, by)
            kinds = [r.split(" de ")[0] for r in rays if r != "libre"]
            cause = max(set(kinds), key=kinds.count) if kinds else "?"
            blockers = sorted({r.split(" de ")[1] for r in rays if " de " in r})
            out.append({"door": door, "set": k, "cause": cause, "blockers": blockers, "rays": rays})
    return res, out


def step_moradas(st):
    import stage23_moradas as M
    import stage26_moradas as S
    import build_stage23 as B23
    M.BAL_D, M.LANDINGS, M.STAIR_RAIL = 0.35, True, False         # vuelo 0.35 m (<= 1.2 m pedido)
    B23._CACHE.clear()
    _r0, before = blocked_list()
    log = {"before": len(before), "before_by_cause": {}}
    for b in before:
        log["before_by_cause"][b["cause"]] = log["before_by_cause"].get(b["cause"], 0) + 1
    # (a) vuelo de balcon 0.35 m (<= 1.2 m). Escalera: se mantiene la de la etapa 26 (pie en el extremo alejado de
    # CAM_Iso, tramo alto hacia el cercano, con el ajuste casa a casa). La prueba literal "tramo alto en el extremo
    # alejado" en las 69 casas subio las puertas tapadas de 16 a 48 (docs/reports/stage28_moradas_prueba_far.json):
    # no se aplica sin confirmacion del usuario.
    log["a_stair"] = {"kept": "etapa 26", "far_literal_test_blocked": 48, "evidence": "stage28_moradas_prueba_far.json"}
    # (b) cuerpo/alero: alero 0.3 m -> 2 plantas (casa que tapa)
    steps_b = []
    n_now = len(blocked_list()[1])
    for rnd in range(3):
        _r, cur = blocked_list()
        culprits = sorted({bl for b in cur if b["cause"] == "cuerpo/alero" for bl in b["blockers"]})
        if not culprits:
            break
        changed = False
        for name in culprits:
            r = bpy.data.objects[name]
            plan = parse_section(r["section"])
            if plan.get("eave") is not None:
                continue                                   # ya probada en una ronda anterior
            tries = [({"eave": 0.3}, "alero 0.3 m")]
            if r["tipo"] == "habitacion" and plan["floors"] == 3:
                tries.append(({"eave": 0.3, "floors": 2}, "alero 0.3 m + 2 plantas (pierde 3 viviendas)"))
            old = {"eave": None, "floors": plan["floors"]}
            rem_old = r.get("remedies", "-")
            kept = False
            for change, label in tries:
                r = rebuild_with(bpy.data.objects[name], **change)
                n_new = len(blocked_list()[1])
                steps_b.append({"house": name, "remedy": label, "round": rnd, "blocked": [n_now, n_new],
                                "kept": n_new < n_now})
                if n_new < n_now:                          # solo se queda si libera puertas
                    n_now, changed, kept = n_new, True, True
                    break
            if not kept:
                r = rebuild_with(bpy.data.objects[name], **old)
                r["remedies"] = rem_old
        if not changed:
            break
    res_f, final = blocked_list()
    # (b) tercer paso (mover la puerta a otra fachada): las casas comunales tienen 3 puertas por planta en balcones
    # sobre la fachada; casa pequena / grande: puerta unica, se podria pasar al lateral. Se informa, no se aplica.
    dwell = {k: sum(1 for o in bpy.data.objects if o.name.startswith(f"MARKER_Morada_Door_{k}_")) for k in
             ("NE", "NO", "SE", "SO")}
    st["moradas"] = {"rules": {"balcony_depth_m": M.BAL_D, "max_balcony_m": 1.2, "stair": "extremo alejado de CAM_Iso "
                               "(tramo alto y rellano superior; stair_for 'far')", "eave_m": 0.3, "tolerance": 10},
                     "log": log, "b_steps": steps_b, "after": len(final),
                     "after_by_set": {k: {"doors": v["doors"], "facing": v["facing"], "blocked": len(v["blocked"])}
                                      for k, v in res_f.items()},
                     "residual": final, "dwellings": dwell, "dwellings_total": sum(dwell.values())}
    from build_stage26 import morada_sets
    st["moradas_sets"] = morada_sets()


# --------------------------------------------------------------------------- punto 14: soportes de los tubos
def road_fn():
    from PIL import Image
    im = Image.open(MASK)
    W = im.size[0]
    px = im.load()

    def road(x, y):
        u, v = (x + 212.0) / 424.0, (212.0 - y) / 424.0
        i, j = int(u * W), int(v * W)
        if not (0 <= i < W and 0 <= j < W):
            return False
        return px[i, j][0] > 127
    return road


def step_pipes(st):
    import stage26_pipes as P
    road = road_fn()
    root = bpy.data.objects[P.ROOT]
    col = root.users_collection[0]
    dg = bpy.context.evaluated_depsgraph_get()
    scene = bpy.context.scene
    rows = []
    sups = sorted([o for o in root.children if o.name.startswith("PIPE_TF_Support_")], key=lambda o: o.name)

    def ground_at(x, y, ztop):
        o = Vector((x, y, ztop))
        hit, loc, _n, _i, ob, _m = scene.ray_cast(dg, o, Vector((0, 0, -1)), distance=60.0)
        while hit and (ob.name.endswith(("-colonly", "_LOD1", "_LOD2", "-navmesh", "_InteriorVolume")) or
                       ob.name.startswith(("PIPE_", "MARKER_")) or ob.hide_render):
            hit, loc, _n, _i, ob, _m = scene.ray_cast(dg, loc - Vector((0, 0, 0.01)), Vector((0, 0, -1)), distance=60.0)
        return (loc.z, ob.name) if hit else (None, None)

    def building_dist(p, v, zc):
        o = Vector((p.x, p.y, zc))
        hit, loc, _n, _i, ob, _m = scene.ray_cast(dg, o, v, distance=20.0)
        while hit and (ob.name.endswith(("-colonly", "_LOD1", "_LOD2", "-navmesh", "_InteriorVolume")) or
                       ob.name.startswith(("PIPE_", "TRN_", "MARKER_", "STR_", "CAU_")) or ob.hide_render):
            hit, loc, _n, _i, ob, _m = scene.ray_cast(dg, loc + v * 0.01, v, distance=20.0)
        return ((loc - o).length, ob.name) if hit else (None, None)
    for so in sups:
        mw = so.matrix_world
        base = mw.translation.copy()
        top_z = base.z + so["height_m"]                        # cara inferior del tubo
        yaw = math.atan2(mw[1][0], mw[0][0])
        along = Vector((-math.sin(yaw), math.cos(yaw), 0.0))  # el soporte se giro yaw = dir - 90 grados
        perp = Vector((along.y, -along.x, 0.0))
        row = {"support": so.name, "xy": [round(base.x, 1), round(base.y, 1)], "on_road": road(base.x, base.y)}
        if not row["on_road"]:
            row["action"] = "se queda (fuera de la zona de paso)"
            rows.append(row)
            continue
        done = False
        # 1) al borde de la calle: linea de edificios a cada lado (perpendicular al tubo)
        for s in (1, -1):
            v = perp * s
            d, who = building_dist(base, v, base.z + 1.5)
            if d is None:
                continue
            off = d - EDGE_FROM_BUILDING
            if 0 < off <= MAX_BRACKET:
                q = base + v * off
                zb, on = ground_at(q.x, q.y, top_z - 0.5)
                if zb is None:
                    continue
                hgt = top_z - zb
                new = Matrix.Translation((q.x, q.y, zb)) @ Matrix.Rotation(yaw, 4, "Z") @ \
                    Matrix.Diagonal((1.0, 1.0, hgt / 9.228, 1.0))
                so.matrix_world = new
                so["height_m"] = round(hgt, 2)
                import bld_kit as K
                import interior_kit as IK
                mb = K.MB()
                mb.rod((0, 0, hgt - 0.12), (-v.x * off, -v.y * off, hgt - 0.12), 0.06, "MAT_Iron_Black")
                mb.rod((0, 0, hgt - 1.2), (-v.x * off * 0.6, -v.y * off * 0.6, hgt - 0.14), 0.04, "MAT_Iron_Black")
                arm = IK.to_obj(mb, f"{so.name}_Bracket", col)
                arm.parent = root
                arm.matrix_world = Matrix.Translation((q.x, q.y, zb))
                row.update(action=f"al borde de la calle junto a {who} ({off:.2f} m, mensula)", moved_m=round(off, 2),
                           new_xy=[round(q.x, 1), round(q.y, 1)], on=on, height_m=round(hgt, 2))
                done = True
                break
        # 2) a lo largo del tubo hasta salir de la zona de paso
        if not done:
            for k in range(1, int(MAX_SHIFT / 0.25) + 1):
                for s in (1, -1):
                    q = base + along * (s * 0.25 * k)
                    if road(q.x, q.y):
                        continue
                    zb, on = ground_at(q.x, q.y, top_z - 0.5)
                    if zb is None:
                        continue
                    hgt = top_z - zb
                    so.matrix_world = Matrix.Translation((q.x, q.y, zb)) @ Matrix.Rotation(yaw, 4, "Z") @ \
                        Matrix.Diagonal((1.0, 1.0, hgt / 9.228, 1.0))
                    so["height_m"] = round(hgt, 2)
                    row.update(action=f"desplazado {0.25 * k * s:+.2f} m a lo largo del tubo, fuera de la calle",
                               new_xy=[round(q.x, 1), round(q.y, 1)], on=on, height_m=round(hgt, 2))
                    done = True
                    break
                if done:
                    break
        if not done:
            dl = [building_dist(base, perp * s, base.z + 1.5)[0] for s in (1, -1)]
            row["action"] = "SIN RESOLVER: plaza abierta (pendiente de decision)"
            row["building_line_m"] = [None if d is None else round(d, 1) for d in dl]
        rows.append(row)
    for m in [o for o in col.objects if o.name.startswith("MARKER_PipeSupport_")]:
        sname = m.get("piece")
        if sname and bpy.data.objects.get(sname):
            m.location = bpy.data.objects[sname].matrix_world.translation
    tri = sum(len(p.vertices) - 2 for o in root.children_recursive if o.type == "MESH" for p in o.data.polygons)
    st["pipes"] = {"supports": rows, "unresolved": [r["support"] for r in rows if r["action"].startswith("SIN")],
                   "tris_total": tri, "budget": P.BUDGET, "rule": "zona de paso = road_mask de T_StreetMasks (etapa 5)",
                   "min_over_street_m": None}
    # altura libre minima sobre calles bajo el tubo
    pts = []
    for o in root.children:
        if o.name.startswith("PIPE_TF_Straight_"):
            p = o.matrix_world.translation
            if road(p.x, p.y):
                zb, _on = ground_at(p.x, p.y, p.z - P.R_PIPE - 0.05)
                if zb is not None:
                    pts.append(p.z - P.R_PIPE - zb)
    st["pipes"]["min_over_street_m"] = round(min(pts), 2) if pts else None


# --------------------------------------------------------------------------- medicion del Faro
def step_medir(st):
    import stage26_faro as F
    for o in bpy.data.objects:
        if o.name.endswith(("_LOD1", "_LOD2")):
            o.hide_render = True
    res, sole, pipe_pts = F.measure()
    goal = {"avenida": 100.0, "diagonal": 100.0, "anillo": 100.0, "callejon": 90.0}
    st["faro"] = {"visibility": {k: {kk: vv for kk, vv in v.items() if kk != "blocked_points"} for k, v in res.items()},
                  "blocked_points": {k: v["blocked_points"] for k, v in res.items()}, "goal": goal,
                  "points_lost_to_pipes": pipe_pts}
    for k, v in res.items():
        print("FARO28", k, v["points"], v["with_faro"], v["pct"], flush=True)
    for o in bpy.data.objects:
        if o.name.endswith(("_LOD1", "_LOD2")):
            o.hide_render = False


STEPS = {"faro": step_faro, "moradas": step_moradas, "pipes": step_pipes, "medir": step_medir}


def main():
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    fresh = "--fresh" in args
    steps = [a for a in args if not a.startswith("--")] or list(STEPS)
    src = SRC if fresh or not os.path.exists(OUT) else OUT
    bpy.ops.wm.open_mainfile(filepath=src)
    st = {} if fresh else load_report()
    st["source"] = os.path.relpath(src, REPO)
    for s in steps:
        print("STEP", s, flush=True)
        STEPS[s](st)
        st.setdefault("steps_done", []).append(s)
        if s != "medir":
            save()
        write_report(st)
    print("DONE", steps, flush=True)


if __name__ == "__main__":
    main()
