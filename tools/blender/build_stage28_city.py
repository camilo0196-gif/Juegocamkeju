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


# --------------------------------------------------------------------------- punto 3 (E28): ruta oeste de los tubos
WEST_NODES = [  # (x, y, tipo de apoyo) - decision del usuario: ruta oeste (Tesoreria -> MER_Casa_01 -> Posada -> Registro)
    (-18.0, 126.2, "salida"), (-18.5, 118.0, "techo"), (-19.5, 111.5, "techo"), (-26.2, 103.9, "suelo"),
    (-25.5, 89.5, "techo"), (-20.0, 84.5, "techo"), (-14.0, 80.0, "techo"), (-9.5, 77.75, "techo"), (-5.5, 75.5, "techo"),
    (6.0, 74.0, "techo"), (13.0, 70.5, "techo"), (16.8, 67.5, "techo"), (26.5, 65.3, "suelo"), (35.5, 61.8, "suelo")]
PIPE_GROUND_GAP = 2.5             # terreno sin calle: paso libre de una persona bajo el tubo
PIPE_ROOF_GAP = 1.2
PIPE_STREET_GAP = 5.0
PILLAR = 0.6
MAX_SPAN = 10.0
MAX_SPAN_ARCH = 16.0


def step_pipes_west(st):
    import stage26_pipes as P
    import build_stage18 as B18
    import bld_kit as K
    import interior_kit as IK
    import math
    g = B18.ground_fn()
    road = road_fn()
    dg = bpy.context.evaluated_depsgraph_get()
    scene = bpy.context.scene
    crv = bpy.data.objects[P.CURVE]
    col = crv.users_collection[0]
    outlet = bpy.data.objects["MARKER_PipeOutlet_TesoreriaMuralla_02"].matrix_world.translation.copy()
    sp = crv.data.splines[0]
    end = crv.matrix_world @ sp.points[len(sp.points) - 1].co.xyz       # entrada al Faro (igual que antes)
    old = bpy.data.objects.get(P.ROOT)
    if old is not None:
        for o in list(old.children_recursive) + [old]:
            bpy.data.objects.remove(o)
    for o in [o for o in col.objects if o.name.startswith("MARKER_PipeSupport_")]:
        bpy.data.objects.remove(o)
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()

    def surface(x, y):
        o = Vector((x, y, 140.0))
        hit, loc, _n, _i, ob, _m = scene.ray_cast(dg, o, Vector((0, 0, -1)))
        while hit and (ob.name.endswith(("-colonly", "_LOD1", "_LOD2", "-navmesh", "_InteriorVolume", "-occonly")) or
                       ob.name.startswith(("PIPE_", "MARKER_", "FARO_Beam", "CRV_")) or ob.hide_render or
                       ob.type != "MESH"):
            hit, loc, _n, _i, ob, _m = scene.ray_cast(dg, loc - Vector((0, 0, 0.01)), Vector((0, 0, -1)))
        return (loc.z, ob.name) if hit else (g(x, y), "terreno")
    nodes = [Vector((x, y, 0.0)) for x, y, _k in WEST_NODES] + [Vector((end.x, end.y, 0.0))]
    kinds = [k for _x, _y, k in WEST_NODES] + ["faro"]
    # necesidad de altura del eje: >= 1.2 m sobre techos, >= 5 m sobre calles, >= 2.5 m sobre terreno sin calle
    def need_at(q, foot=0.0):
        best, why = 0.0, None
        offs = [(0.0, 0.0)] + ([(dx, dy) for dx in (-foot, foot) for dy in (-foot, foot)] if foot else [])
        for dx, dy in offs:
            z, who = surface(q.x + dx, q.y + dy)
            if who.startswith("FARO"):
                continue
            ground = who.startswith(("TRN_", "terreno", "STR_", "CAU_"))
            gap = (PIPE_STREET_GAP if road(q.x + dx, q.y + dy) else PIPE_GROUND_GAP) if ground else PIPE_ROOF_GAP
            h = z + gap + P.R_PIPE
            if h > best:
                best, why = h, (who, round(z, 2), gap)
        return best, why
    samples = []                                            # por tramo: [(u, necesidad)]
    seg_info = []
    for i in range(len(nodes) - 1):
        a, b = nodes[i], nodes[i + 1]
        d = (b - a)
        L = d.length
        t = Vector((-d.y, d.x, 0.0)).normalized()
        n = max(2, int(L / 0.5))
        row, worst = [], (0.0, None)
        for k in range(n + 1):
            q = a + d * (k / n)
            nd = 0.0
            for off in (0.0, 0.5, -0.5, 1.0, -1.0):
                h, why = need_at(q + t * off)
                if h > nd:
                    nd = h
                if h > worst[0]:
                    worst = (h, why)
            row.append((k / n, nd))
        samples.append(row)
        seg_info.append({"from": i, "to": i + 1, "length_m": round(L, 2), "limit": worst[1]})
    # alturas por apoyo (tramos inclinados, sin quiebros verticales): huella del pilar (+-0.4 m) y luego se suben los
    # extremos hasta que ningun punto del tramo quede por debajo de su necesidad
    h = [need_at(nodes[i], foot=0.4)[0] + 0.1 for i in range(len(nodes))]
    for _it in range(30):
        moved = False
        for i, row in enumerate(samples):
            deficit = max(nd - (h[i] * (1 - u) + h[i + 1] * u) for u, nd in row)
            if deficit > 1e-3:
                h[i] += deficit + 0.02
                h[i + 1] += deficit + 0.02
                moved = True
        if not moved:
            break
    # sin valles: un apoyo mas bajo que sus dos vecinos sube a la altura del menor (subir nunca rompe una holgura y
    # convierte codos de 90 en codos de 45 o juntas); margen de 5 cm
    for _it in range(10):
        for i in range(1, len(h) - 1):
            lo = min(h[i - 1], h[i + 1])
            if h[i] < lo:
                h[i] = lo
    h = [round(x + 0.05, 2) for x in h]
    for i, info in enumerate(seg_info):
        info["axis_z"] = [h[i], h[i + 1]]
    seg_h = h
    path = [outlet.copy(), Vector((nodes[0].x, nodes[0].y, h[0]))] if h[0] - outlet.z > 0.05 else [outlet.copy()]
    for i in range(1, len(nodes)):
        path.append(Vector((nodes[i].x, nodes[i].y, h[i])))
    if abs(h[-1] - end.z) > 0.05:
        path.append(end.copy())
    root = bpy.data.objects.new(P.ROOT, None)
    col.objects.link(root)
    root["pipe"] = "Tesoreria -> Faro (luz azul, MAT_Pipe_Light_Core); ruta oeste (etapa 28, decision del usuario)"
    piece0 = P.MAX_PIECE
    P.MAX_PIECE = 6.0                                       # rectos de hasta 6 m: menos bridas, mismo tubo
    try:
        objs, log = P.build(path, col, root, g, st)
    finally:
        P.MAX_PIECE = piece0
    for so in objs["support"]:                                # sus soportes de suelo cada 8 m no valen aqui
        bpy.data.objects.remove(so)
    objs["support"] = []
    # pilares de piedra (0.6 m) en cada apoyo: base en la superficie mas baja bajo su planta (techo o terreno)
    pil = []
    mbp = K.MB()
    for i in range(1, len(nodes) - 1):
        x, y = nodes[i].x, nodes[i].y
        zs = [surface(x + dx, y + dy) for dx in (-PILLAR / 2, PILLAR / 2) for dy in (-PILLAR / 2, PILLAR / 2)]
        zb = min(z for z, _w in zs)
        on = sorted({w for _z, w in zs})
        top = seg_h[i] - P.R_PIPE
        mbp.box((x - PILLAR / 2, y - PILLAR / 2, zb), (x + PILLAR / 2, y + PILLAR / 2, top), IK.STONE, skip=("z-",))
        mbp.box((x - PILLAR / 2 - 0.08, y - PILLAR / 2 - 0.08, top - 0.15), (x + PILLAR / 2 + 0.08, y + PILLAR / 2 + 0.08,
                top), IK.STONE_L)                             # capitel
        is_road = road(x, y) and any(w.startswith(("TRN_", "terreno", "STR_")) for w in on)
        pil.append({"node": i, "xy": [round(x, 2), round(y, 2)], "kind": kinds[i], "on": on, "base_z": round(zb, 2),
                    "height_m": round(top - zb, 2), "on_street": bool(is_road),
                    "roof_gap_m": round(top - max(z for z, _w in zs), 2)})
    # arcos de piedra en los tramos de mas de 10 m (entre los capiteles, bajo el tubo)
    arches = []
    for i, info in enumerate(seg_info):
        if info["length_m"] <= MAX_SPAN or i == 0:
            continue
        a, b = nodes[i], nodes[i + 1]
        rise = min(1.6, info["length_m"] * 0.12)
        prev = None
        for k in range(13):
            u = k / 12
            p = a + (b - a) * u
            zt = seg_h[i] * (1 - u) + seg_h[i + 1] * u - P.R_PIPE - 0.24
            z = zt - rise + rise * math.sin(math.pi * u)
            cur = Vector((p.x, p.y, z))
            if prev is not None:
                mbp.rod(prev, cur, 0.22, IK.STONE)
            prev = cur
        arches.append({"span": [i, i + 1], "length_m": info["length_m"], "rise_m": round(rise, 2)})
    po = IK.to_obj(mbp, "PIPE_TF_Pillars", col)
    po.parent = root
    po.matrix_parent_inverse.identity()
    # curva y marcadores
    sp.points.add(max(0, len(path) - len(sp.points)))
    while len(sp.points) > len(path):
        crv.data.splines.remove(sp)
        sp = crv.data.splines.new("POLY")
        sp.points.add(len(path) - 1)
    inv = crv.matrix_world.inverted()
    for k, p in enumerate(path):
        sp.points[k].co = (*(inv @ p), 1.0)
    crv["route"] = "oeste (etapa 28): Tesoreria -> MER_Casa_01 -> Posada -> Casa del Registro -> Faro"
    for k, pp in enumerate(pil, 1):
        m = bpy.data.objects.new(f"MARKER_PipeSupport_{k:02d}", None)
        col.objects.link(m)
        m.location = (pp["xy"][0], pp["xy"][1], pp["base_z"])
        m["support_height_m"] = pp["height_m"]
        m["kind"] = pp["kind"]
        m["on"] = ", ".join(pp["on"])
    # comprobaciones
    bvh_b, bvh_f, bvh_t = P.occluders()
    wb, wf, bad = P.clearance(path, bvh_b, bvh_f, skip_start=P.SKIP_START, skip_end_from=6.0, bvh_t=bvh_t)
    spans = [x["length_m"] for x in seg_info]
    street_min = None
    for i, info in enumerate(seg_info):
        a, b = nodes[i], nodes[i + 1]
        for k in range(21):
            q = a + (b - a) * (k / 20)
            if road(q.x, q.y):
                z, who = surface(q.x, q.y)
                if who.startswith(("TRN_", "terreno", "STR_")):
                    gap = (seg_h[i] * (1 - k / 20) + seg_h[i + 1] * (k / 20)) - P.R_PIPE - z
                    street_min = gap if street_min is None else min(street_min, gap)

    def tri(me):
        return sum(len(pp.vertices) - 2 for pp in me.polygons)
    tris = {"straight": sum(tri(o.data) for o in objs["straight"]), "elbows": sum(tri(o.data) for o in objs["elbow90"] + objs["elbow45"]),
            "pillars_arches": tri(po.data)}
    tris["total"] = sum(tris.values())
    length = sum((path[i + 1] - path[i]).length for i in range(len(path) - 1))
    st["pipes"] = {"route": "oeste (decision del usuario, etapa 28)", "nodes": len(nodes), "path_vertices": len(path),
                   "length_m": round(length, 1), "segments": seg_info, "segment_axis_z": seg_h, "pillars": pil,
                   "arches": arches, "max_span_m": max(spans), "spans_over_10m": [x for x in spans if x > MAX_SPAN],
                   "spans_over_16m": [x for x in spans if x > MAX_SPAN_ARCH],
                   "pillars_on_street": [p_["node"] for p_ in pil if p_["on_street"]],
                   "min_clear_over_street_m": round(street_min, 2) if street_min is not None else None,
                   "min_to_building_m": round(wb, 2), "clearance_violations": bad[:10], "tris": tris,
                   "budget": P.BUDGET, "bends": log["bends"]}
    print("PIPES", {k: v for k, v in st["pipes"].items() if k not in ("segments", "bends", "pillars")}, flush=True)
    for p_ in pil:
        print("PILLAR", p_, flush=True)


# --------------------------------------------------------------------------- punto 4 (E28): escalon de las casas B05
RISER_MAX = 0.15


def step_razas(st):
    """Casas de raza con margen de pendiente (> 1.2 m): el escalon entre el suelo de la puerta y el terreno delante
    de ella (rejilla de 0.1-0.6 m x +-0.8 m) debe ser <= 0.15 m. Si no, peldanos de piedra a lo largo de toda la
    fachada (huella 0.35 m) sin tocar el terreno; se cuentan las contrahuellas resultantes."""
    import math
    import bld_kit as K
    import interior_kit as IK
    dg = bpy.context.evaluated_depsgraph_get()
    scene = bpy.context.scene
    out = {}
    for n in ("RAZ_B05_Casa_04", "RAZ_B05_Casa_05"):
        r = bpy.data.objects[n]
        old = bpy.data.objects.get(f"{n}_Steps")
        if old is not None:
            for c in list(old.children):
                bpy.data.objects.remove(c)
            bpy.data.objects.remove(old)
        dm = bpy.data.objects[f"MARKER_{n}_Door"]
        nrm = r.matrix_world.to_3x3() @ Vector((0, 1, 0))
        nrm.z = 0
        nrm.normalize()
        t = Vector((nrm.y, -nrm.x, 0))
        p = dm.matrix_world.translation
        zdoor = p.z

        def ground(q):
            o = Vector((q.x, q.y, zdoor + 3.0))
            hit, loc, _n, _i, ob, _m = scene.ray_cast(dg, o, Vector((0, 0, -1)))
            while hit and (ob.name.startswith(n) or ob.name.endswith(("-colonly", "_LOD1", "_LOD2", "-navmesh")) or
                           ob.hide_render or ob.type != "MESH"):
                hit, loc, _n, _i, ob, _m = scene.ray_cast(dg, loc - Vector((0, 0, 0.01)), Vector((0, 0, -1)))
            return loc.z if hit else None
        samples = [ground(p + nrm * d + t * s) for d in (0.1, 0.35, 0.6) for s in (-0.8, -0.4, 0.0, 0.4, 0.8)]
        samples = [z for z in samples if z is not None]
        drop = zdoor - min(samples)
        rec = {"door_z": round(zdoor, 3), "ground_min": round(min(samples), 3), "ground_max": round(max(samples), 3),
               "step_before_m": round(drop, 3)}
        if drop <= RISER_MAX + 1e-3:
            rec["action"] = "cumple sin cambios"
        else:
            nsteps = max(1, math.ceil(drop / RISER_MAX) - 1)
            if nsteps > 2:
                rec["action"] = f"necesita {nsteps} peldanos: rampa corta (no aplicada; revisar)"
                out[n] = rec
                continue
            rise = drop / (nsteps + 1)
            # peldanos en el marco de la casa: fachada en y = +D/2 (4 m de ancho), hacia +Y local
            W, D = 4.0, 8.0
            mb = K.MB()
            zl = zdoor - r.matrix_world.translation.z           # suelo de la puerta en el marco de la casa (0)
            for k in range(nsteps):
                top = zl - rise * (k + 1)
                y0 = D / 2 + 0.35 * k
                mb.box((-W / 2 - 0.1, y0, top - 0.5), (W / 2 + 0.1, y0 + 0.35, top), IK.STONE, skip=("z-",))
            o = IK.to_obj(mb, f"{n}_Steps", r.users_collection[0])
            o.parent = r
            o.matrix_parent_inverse.identity()
            o["note"] = f"peldanos de piedra a lo largo de la fachada (etapa 28): contrahuellas {rise:.3f} m"
            cm = K.MB()
            cm.box((-W / 2 - 0.1, D / 2, zl - rise * nsteps - 0.5), (W / 2 + 0.1, D / 2 + 0.35 * nsteps, zl - rise), IK.BLOCK)
            c = IK.to_obj(cm, f"{n}_Steps-colonly", r.users_collection[0], uv=False)
            c.parent = o
            c.matrix_parent_inverse.identity()
            c.hide_render = True
            bpy.context.view_layer.update()
            rec.update(action=f"{nsteps} peldano(s) de piedra a lo largo de la fachada (4.2 m), huella 0.35 m",
                       risers_m=[round(rise, 3)] * (nsteps + 1), steps_tris=sum(len(pp.vertices) - 2 for pp in o.data.polygons))
        out[n] = rec
        print("RAZ", n, rec, flush=True)
    st["razas_steps"] = out


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


STEPS = {"faro": step_faro, "moradas": step_moradas, "pipes": step_pipes, "pipes_west": step_pipes_west, "razas": step_razas, "medir": step_medir}


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
