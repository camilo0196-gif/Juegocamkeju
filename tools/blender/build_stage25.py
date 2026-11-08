"""
CONCORDIA - Etapa 25 (E12): decisiones del usuario sobre las pendientes.
concordia_v24.blend -> concordia_v25.blend (version final) + docs/reports/stage25_decisiones.json
+ pipeline de Godot de la etapa 24 sobre el resultado (docs/reports/stage25_godot.json, export/godot/bld_*.glb)

1. MAT_Embers: unica excepcion calida. El cuenco del Crisol (no es fundicion ni horno) pasa a MAT_Crisol_Molten
   (emision #8FD0FF): el Crisol es un edificio magico.
2. Gremio de Cazadores dentro de la ciudad (opcion elegida por el usuario): casa 12 x 8 en el hueco libre del sector
   Este y campo de tiro 14 x 8 con valla de 1.2 m paralelo a la muralla.
3. Razas: casas nuevas de 8 x 8 en los huecos libres del sector Sur (sin calles, escalinatas ni puentes), hasta 3
   plantas si no tapan el Faro.
5. Faro: escalera de ajuste (a) 2 plantas, (b) cubierta plana con pretil, (c) 1 planta y media (5.5 m) solo en los
   edificios en que la escalera deja de tapar; el resto se informa.
"""

import json
import math
import os
import random
import sys
from collections import defaultdict

import bpy  # noqa: I001
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import concordia_const as C  # noqa: E402
import bld_kit as K  # noqa: E402
import concordia_buildings as B  # noqa: E402
import stage21_razas as R  # noqa: E402
import stage25_lots as LOTS  # noqa: E402
import stage25_faro as F  # noqa: E402

REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
SRC = os.path.join(REPO, "blender", f"{C.BLEND_BASENAME}_v24.blend")
OUT = os.path.join(REPO, "blender", f"{C.BLEND_BASENAME}_v25.blend")
REPORT = os.path.join(REPO, "docs", "reports", "stage25_decisiones.json")
CAZ_HOUSE = (12.0, 8.0)
CAZ_RANGE = (14.0, 8.0)
# edificios en que la escalera del Faro deja de tapar (simulacion sobre v24): nombre -> paso
FARO_CAPS = {"Morada_NO_033": "a", "Morada_NO_002": "a", "Morada_SE_023": "a", "Morada_SE_036": "a", "Morada_SE_004": "a",
             "RAZ_B01_Casa_01": "c", "RAZ_B01_Casa_02": "c", "RAZ_B02_Casa_02": "c"}
BARRIO_KEY = {1: "R01", 2: "R02", 3: "R03", 4: "R04", 5: "R05", 6: "R06"}


def save():
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)


def remove_tree(root):
    for o in list(root.children_recursive) + [root]:
        me = o.data if o.type == "MESH" else None
        bpy.data.objects.remove(o)
        if me is not None and me.users == 0:
            bpy.data.meshes.remove(me)


def height_now(r):
    inv = r.matrix_world.inverted()
    hs = [(inv @ (o.matrix_world @ Vector(c))).z for o in [r] + list(r.children_recursive)
          if o.type == "MESH" and not o.name.endswith(F.SKIP_SUFFIX) for c in o.bound_box]
    return round(max(hs), 2) if hs else 0.0


# --------------------------------------------------------------------------- 1. brasas
def embers(st):
    name = "MAT_Crisol_Molten"
    if name not in bpy.data.materials:
        m = bpy.data.materials.new(name)
        m.use_nodes = True
        b = m.node_tree.nodes["Principled BSDF"]
        b.inputs["Base Color"].default_value = (0.040, 0.047, 0.058, 1)       # #39404A piedra fundida oscura
        b.inputs["Roughness"].default_value = 0.6
        b.inputs["Emission Color"].default_value = (0.2747, 0.6308, 1.0, 1)  # #8FD0FF
        b.inputs["Emission Strength"].default_value = 1.2
        m["note"] = "cuenco del Crisol: piedra fundida magica, emision #8FD0FF 1.2 (etapa 25: antes MAT_Embers)"
    changed = []
    for o in bpy.data.objects:
        if o.type == "MESH" and o.name.startswith("CrisolPiedras"):
            for i, mm in enumerate(o.data.materials):
                if mm is not None and mm.name == "MAT_Embers":
                    o.data.materials[i] = bpy.data.materials[name]
                    changed.append(o.name)
    st["embers"] = {"crisol_bowl": "MAT_Embers -> MAT_Crisol_Molten (#8FD0FF 1.2)", "objects": changed,
                    "allowed": ["Taller_GranForja (fundicion)", "Taller_Hornos", "chimeneas de Posada y Forja"]}


# --------------------------------------------------------------------------- 2. cazadores
def fence_range(mb, w, d, n_targets):
    """Campo de tiro: valla de madera de 1.2 m (postes cada 2 m, 2 travesanos) con entrada en el lado +Y."""
    hw, hd = w / 2, d / 2
    edges = [((-hw, -hd), (hw, -hd)), ((hw, -hd), (hw, hd)), ((-hw, hd), (-hw, -hd)), ((-hw, hd), (-1.0, hd)),
             ((1.0, hd), (hw, hd))]
    for (x0, y0), (x1, y1) in edges:
        L = math.hypot(x1 - x0, y1 - y0)
        n = max(1, int(round(L / 2.0)))
        for k in range(n + 1):
            x = x0 + (x1 - x0) * k / n
            y = y0 + (y1 - y0) * k / n
            mb.box((x - 0.07, y - 0.07, -0.3), (x + 0.07, y + 0.07, 1.2), K.M_WOOD, skip=("z-",))
        for z in (0.55, 1.08):
            mb.rod((x0, y0, z), (x1, y1, z), 0.04, K.M_WOOD)
    mb.box((-hw + 0.5, hd - 1.6, 0.85), (hw - 0.5, hd - 1.45, 0.95), K.M_WOOD)       # mostrador de tiro


def cazadores(st, g):
    import build_stage19 as B19
    import build_stage21 as B21
    import stage19_oficios as O
    old = bpy.data.objects.get("Gremio_Cazadores")
    if old is not None:
        remove_tree(old)
    grid = LOTS.Grid(0.0, 25.0, 60.0, 185.0)
    house = grid.search(*CAZ_HOUSE, (120.0, 0.0), max_n=1, front_need=0.3, max_slope=1.2, margin=0.3)
    rng_ = grid.search(*CAZ_RANGE, (165.0, 50.0), max_n=1, front_need=0.0, max_slope=0.6, margin=0.3)
    if not house or not rng_:
        st["cazadores"] = {"placed": False, "reason": "sin hueco"}
        return None
    h, r_ = house[0], rng_[0]
    hc = Vector(h["center"])
    rm = Matrix.Rotation(h["theta"], 2)
    zs = [g(*(hc + rm @ Vector((x, y)))) for x in (-6, 0, 6) for y in (-4, 0, 4)]
    m = bpy.data.objects.new("MARKER_Bld_Gremio_Cazadores", None)
    next(o for o in bpy.data.objects if o.name.startswith("MARKER_Bld_Gremio_") and o is not m).users_collection[0].objects.link(m)
    m.empty_display_type = "ARROWS"
    m.location = (hc.x, hc.y, max(zs))
    m.rotation_euler = (0, 0, h["theta"])
    for k, v in {"footprint": "12x8", "footprint_w": 12.0, "footprint_d": 8.0, "door_direction": "+Y", "interior": True,
                 "type": "gremio", "district": "Oficios", "pad_z": round(max(zs), 3), "added_stage": 25,
                 "note": "casa reducida a 12x8 (decision del usuario): no hay hueco de 20x14 en el sector Este"}.items():
        m[k] = v
    bpy.context.view_layer.update()
    col, pcol = bpy.data.collections["BLD_OFICIOS"], bpy.data.collections["BLD_PROPS"]
    root, objs, rep = B.fit_iso_height("Gremio_Cazadores", 2, marker=m, seed=1901, collection=col, props_collection=pcol,
                                       tipo_techo="gable", estilo="timber", module_w=4.0,
                                       opts={"no_buttress": True, "side_detail": {"back": 1}, "roof_seg": 4.0, "eave": 0.6})
    W, D = rep["footprint"]
    gap = B21.ground_gap(root, W, D, g)
    B21.merge(objs["Body"], lambda mb: B21.skirt(mb, W, D, max(0.6, gap + 0.2)))
    B.box_uv(objs["Body"])
    pe = B19.props_empty(root, pcol)
    ant = B19.shared("PROP_Antlers", O.antlers)
    hr = B19.shared("PROP_HideRack", O.hide_rack)
    mw = root.matrix_world
    props = [B19.prop("Gremio_Cazadores_Prop_Antlers_01", ant, pcol, pe,
                      mw @ Matrix.Translation((rep["door_local"][0], D / 2 + 0.02, 3.0))),
             B19.prop("Gremio_Cazadores_Prop_Antlers_02", ant, pcol, pe,
                      mw @ Matrix.Translation((W / 2 + 0.02, 0.0, rep["eave_height_m"] + 1.0)) @ Matrix.Rotation(-math.pi / 2, 4, "Z")),
             B19.prop("Gremio_Cazadores_Prop_HideRack_01", hr, pcol, pe,
                      mw @ Matrix.Translation((-W / 2 + 1.2, D / 2 + 0.9, 0)))]
    # campo de tiro 14 x 8, paralelo a la muralla
    rc = Vector(r_["center"])
    rz = min(g(*(rc + Matrix.Rotation(r_["theta"], 2) @ Vector((x, y)))) for x in (-7, 0, 7) for y in (-4, 0, 4))
    fm = K.MB()
    fence_range(fm, *CAZ_RANGE, 4)
    rng_obj = B19.mb_object(fm, "Gremio_Cazadores_Range", col, root)
    rng_obj.matrix_world = Matrix.Translation((rc.x, rc.y, rz)) @ Matrix.Rotation(r_["theta"], 4, "Z")
    tg = B19.shared("PROP_Target", O.target)
    rmw = rng_obj.matrix_world
    targets = [B19.prop(f"Gremio_Cazadores_Prop_Target_{k:02d}", tg, pcol, pe,
                        rmw @ Matrix.Translation((-4.5 + 3.0 * k, -CAZ_RANGE[1] / 2 + 1.0, 0)))
               for k in range(4)]
    rmk = bpy.data.objects.new("MARKER_Cazadores_Range", None)
    col.objects.link(rmk)
    rmk.parent = root
    rmk.matrix_world = rmw.copy()
    rmk["range_m"] = "14x8"
    rmk["fence_m"] = 1.2
    colo = B19.box_collider("Gremio_Cazadores-colonly", col, root, [((-W / 2, -D / 2, 0), (W / 2, D / 2, rep["eave_height_m"]))])
    rcol = B19.box_collider("Gremio_Cazadores_Range-colonly", col, rng_obj,
                            [((-7.07, -4.07, 0), (7.07, -3.93, 1.2)), ((6.93, -4.0, 0), (7.07, 4.0, 1.2)),
                             ((-7.07, -4.0, 0), (-6.93, 4.0, 1.2)), ((-7.0, 3.93, 0), (-1.0, 4.07, 1.2)),
                             ((1.0, 3.93, 0), (7.0, 4.07, 1.2))])
    st["cazadores"] = {"placed": True, "option": "elegida por el usuario: casa 12x8 + campo 14x8 junto a la muralla",
                       "house_center": [round(hc.x, 2), round(hc.y, 2)], "house_rot_deg": round(math.degrees(h["theta"]), 1),
                       "house_r_m": round(hc.length, 1), "range_center": [round(rc.x, 2), round(rc.y, 2)],
                       "range_rot_deg": round(math.degrees(r_["theta"]), 1), "range_r_m": round(rc.length, 1),
                       "distance_house_range_m": round((rc - hc).length, 1), "floors": rep["floors"],
                       "slope_m": h["slope"], "targets": len(targets), "props": len(props),
                       "collision": [colo.name, rcol.name], "ground_gap_m": gap}
    return root


# --------------------------------------------------------------------------- 3 y 5. razas y Faro
STEP_C_H = 5.5


def preset_patch(key, step, D, ridge_target=STEP_C_H):
    """Cambios temporales del preset para la escalera del Faro."""
    p = R.RACE_PRESETS[key]
    saved = {k: p[k] for k in ("roof", "pitch")}
    if step == "b":
        p["roof"] = "flat"
    elif step == "c":
        # 1 planta y media: una planta con la cubierta del preset rebajada hasta 5.5 m de altura total
        if p["roof"] in ("gable", "hip", "spire"):
            p["pitch"] = max(8.0, math.degrees(math.atan2(max(0.3, ridge_target - K.FLOOR_H), D / 2)))
            if p["roof"] == "spire":
                p["roof"] = "hip"
        else:
            p["roof"] = "flat"
    return saved


def clamp_ground(objs, hx, hy, zmax=2.2, tol=0.19):
    """Al bajar de plantas el ensamblador puede dejar una jardinera o contraventana lateral unos cm fuera de la
    tolerancia de huella (+-0.2 m por debajo de 2.2 m): se recoge hasta el limite. Devuelve lo maximo movido (m)."""
    moved = 0.0
    for k in ("Body", "Body_LOD1"):
        o = objs.get(k)
        if o is None:
            continue
        for v in o.data.vertices:
            if v.co.z >= zmax:
                continue
            for ax, h in ((0, hx), (1, hy)):
                lim = h + tol
                if abs(v.co[ax]) > lim:
                    moved = max(moved, abs(v.co[ax]) - lim)
                    v.co[ax] = math.copysign(lim, v.co[ax])
        o.data.update()
    return round(moved, 3)


def build_race_house(name, key, marker, step, g, st_list):
    """Casa de raza del ensamblador con la escalera del Faro: None (3 o las plantas del sorteo), a, b, c."""
    import build_stage21 as B21
    col, pcol = bpy.data.collections["BLD_RAZAS"], bpy.data.collections["BLD_PROPS"]
    old = bpy.data.objects.get(name)
    if old is not None:
        remove_tree(old)
    rng = random.Random(B.rng_for(name, B21.SEED))
    pisos = rng.choice((2, 2, 3))
    if marker.get("added_stage") == 25:
        pisos = 3
    if step in ("a", "b"):
        pisos = min(pisos, 2)
    elif step == "c":
        pisos = 1
    elif step == "p1":                                    # etapa 26: 1 planta con la cubierta del preset
        pisos = 1
    elif isinstance(step, int):                           # etapa 26: plantas fijadas (casas adosadas)
        pisos, step = step, None
    target = STEP_C_H
    rng_state = rng.getstate()
    for _try in range(4):
        rng.setstate(rng_state)
        saved = preset_patch(key, step, float(marker["footprint_d"]), target)
        try:
            root, objs, rep = B21.kit_race(name, key, marker, pisos, lambda f: 4000 if f >= 3 else 2500, col, pcol, rng,
                                           g, extras=B21.house_extras(rng))
        finally:
            R.RACE_PRESETS[key].update(saved)
        bpy.context.view_layer.update()
        h = height_now(root)
        if step != "c" or h <= STEP_C_H + 0.05:
            break
        # alero, caballete y grosor de la cubierta suman sobre la pendiente: se corrige con lo que sobra
        target -= h - STEP_C_H
        remove_tree(root)
    W, D = rep["footprint"]
    clamped = clamp_ground(objs, float(marker["footprint_w"]) / 2, float(marker["footprint_d"]) / 2)
    B21.B19.box_collider(f"{name}-colonly", col, root, [((-W / 2, -D / 2, 0), (W / 2, D / 2, rep["eave_height_m"]))])
    if clamped:
        root["footprint_clamped_m"] = clamped
    root["race_preset"] = key
    root["faro_step"] = step or "-"
    root["floors"] = rep["floors"]
    st_list.append({"name": name, "floors": rep["floors"], "roof": rep["roof"], "tris": rep.get("tris_total"),
                    "faro_step": step or "-"})
    return root


def yurt_house(name, marker, st_list, step=None):
    """Casa de raza R05 (yurta) de 8 x 8: yurta r 3.4 con puerta (escala 1.3), zocalo, colision e interior."""
    import build_stage16 as B16
    import build_stage19 as B19
    import lod_utils as LU
    import stage13_portal as P13
    col = bpy.data.collections["BLD_RAZAS"]
    old = bpy.data.objects.get(name)
    if old is not None:
        remove_tree(old)
    root = B16.new_root(name, marker, col, "Casa (yurta)")
    root["building"] = True
    root["footprint_w"], root["footprint_d"] = 8.0, 8.0
    root["race_preset"] = "R05"
    root["floors"] = 1
    if "landmark" in root:
        del root["landmark"]
    rng = random.Random(B.rng_for(name, 2501))
    body, roof = K.MB(), K.MB()
    wall_h, pitch = (3.6, 30.0) if step != "c" else (2.9, 20.0)       # paso c: muro 2.9 m y cono de 20 grados
    zc, dloc = R.yurt(body, roof, 0.0, -0.3, 3.4, wall_h, pitch, rng, door=(math.pi / 2, 1.3), n=16, detail=0, patches=2)
    bo = B16.mesh_obj(body, f"{name}_Body", col, root)
    ro = B16.mesh_obj(roof, f"{name}_Roof", col, root)
    P13.lods(bo, col, (("LOD1", 0.5),))
    P13.lods(ro, col, (("LOD1", 0.5),))
    LU.massing_spec(f"{name}_Body_LOD2", [("cyl", 0.0, -0.3, 3.4, 0.0, wall_h, 10),
                                          ("cone", 0.0, -0.3, 3.85, wall_h - 0.12, zc + 0.5, 10)],
                    [bo, ro], col, root)
    B16.door_marker(name, col, root, dloc)
    iv = B16.interior(name, col, root, 2.3, 2.3, 3.4, {})
    iv.location = (0.0, -0.3, 0.0)
    pe = bpy.data.objects.new(f"{name}_Props", None)
    col.objects.link(pe)
    pe.parent = root
    B19.box_collider(f"{name}-colonly", col, root, [((-2.9, -3.2, 0), (2.9, 2.6, wall_h))])
    root["faro_step"] = step or "-"
    st_list.append({"name": name, "floors": 1, "roof": "yurt", "faro_step": step or "-"})
    return root


def barrio_centroids():
    cen = {}
    for b in range(1, 7):
        pts = [o.matrix_world.translation for o in bpy.data.objects if o.parent is None and o.type == "EMPTY" and
               (o.name.startswith(f"RAZ_B{b:02d}_Casa_") or o.name in (f"CasaRaza_{b:02d}", f"Plazuela_{b:02d}"))]
        cen[b] = sum(pts, Vector()) / len(pts)
    return cen


def razas_lots(st, g):
    grid = LOTS.Grid(270.0, 25.0, 60.0, 185.0)
    lots = grid.search(8.0, 8.0, (0.0, -120.0), max_n=60, front_need=0.3, max_slope=1.2, margin=0.3)
    cen = barrio_centroids()
    have = {b: sum(1 for o in bpy.data.objects if o.parent is None and o.type == "EMPTY" and
                   o.name.startswith(f"RAZ_B{b:02d}_Casa_")) for b in range(1, 7)}
    need = {b: max(0, 6 - have[b]) for b in range(1, 7)}
    assign = defaultdict(list)
    unused = []
    for lot in sorted(lots, key=lambda lt: min((Vector(lt["center"]) - cen[b].xy).length for b in cen)):
        c = Vector(lot["center"])
        best = sorted(((c - cen[b].xy).length, b) for b in cen if need[b] > len(assign[b]))
        if best and best[0][0] <= 40.0:
            assign[best[0][1]].append(lot)
        else:
            near = min(cen, key=lambda b: (c - cen[b].xy).length)
            unused.append({"center": [round(c.x, 1), round(c.y, 1)], "nearest_barrio": near,
                           "dist_m": round((c - cen[near].xy).length, 1),
                           "why": "barrio ya en el minimo" if need[near] <= len(assign[near]) else "a mas de 40 m"})
    built = []
    for b, ls in sorted(assign.items()):
        for lot in ls:
            idx = 1
            while bpy.data.objects.get(f"MARKER_Bld_RAZ_B{b:02d}_Casa_{idx:02d}") is not None:
                idx += 1
            name = f"RAZ_B{b:02d}_Casa_{idx:02d}"
            c = Vector(lot["center"])
            rm = Matrix.Rotation(lot["theta"], 2)
            zs = [g(*(c + rm @ Vector((x, y)))) for x in (-4, 0, 4) for y in (-4, 0, 4)]
            m = bpy.data.objects.new(f"MARKER_Bld_{name}", None)
            next(o for o in bpy.data.objects if o.name.startswith("MARKER_Bld_RAZ_B0") and o is not m).users_collection[0].objects.link(m)
            m.empty_display_type = "ARROWS"
            m.location = (c.x, c.y, max(zs))
            m.rotation_euler = (0, 0, lot["theta"])
            for k, v in {"footprint": "8x8", "footprint_w": 8.0, "footprint_d": 8.0, "door_direction": "+Y",
                         "interior": False, "type": "house", "label": "Casa", "district": "Razas",
                         "pad_z": round(max(zs), 3), "shape": "rect", "decor": True, "barrio": b, "added_stage": 25,
                         "lot_slope_m": lot["slope"]}.items():
                m[k] = v
            bpy.context.view_layer.update()
            built.append((name, b, m))
    st["razas"] = {"need_before": need, "lots_found": len(lots), "assigned": {b: len(v) for b, v in assign.items()},
                   "unused_lots": unused,
                   "missing_after": {f"B{b:02d}": need[b] - len(assign[b]) for b in need if need[b] - len(assign[b]) > 0},
                   "search": "rejilla de 1 m, sector Sur +-25 grados, r 60-185; parcela 8x8 + 0.3 m de margen, sin calle, "
                             "plaza, escalinata, puente ni objeto; desnivel <= 1.2 m (faldon); frente a calle a <= 3.5 m"}
    return built


def faro_round(st, it, built, steps):
    res, bl = F.measure()
    out = {k: {"pct": v["pct"], "points": v["points"]} for k, v in res.items()}
    st.setdefault("faro_rounds", []).append({"round": it, "visibility": out,
                                             "new_or_capped_blocking": sorted(n for n in bl if n in steps or n in built)})
    return res, bl


def main():
    st = {}
    bpy.ops.wm.open_mainfile(filepath=SRC)
    save()
    st["saved_before"] = os.path.relpath(OUT, REPO)
    import build_stage18 as B18
    g = B18.ground_fn()
    embers(st)
    caz = cazadores(st, g)
    print("cazadores", st["cazadores"], flush=True)
    # 5. escalera del Faro en los 8 edificios en que funciona
    before = {n: height_now(bpy.data.objects[n]) for n in FARO_CAPS}
    capped = []
    import build_stage23 as B23
    for name, step in FARO_CAPS.items():
        if name.startswith("Morada_"):
            key = name.split("_")[1]
            r = bpy.data.objects[name]
            sec = r["section"]
            houses = {h["marker"].name: h for h in B23.collect(key)}
            h = houses[r["marker"]]
            plan = {"floors": 2, "roof": {"l": "lean", "g": "gable", "c": "catslide"}[sec[2]],
                    "low_side": {"b": "back", "f": "front", "n": None}[sec[3]]}
            if plan["roof"] != "lean":
                plan["pitch"] = float(sec[4:]) if sec[4:] else 32.0
            h["plan"] = plan
            h["remedies"] = ["Faro: 2 plantas"]
            remove_tree(r)
            col = bpy.data.collections[f"BLD_MORADAS_{key}"]
            B23.build_house(h, key, col, col)
            capped.append({"name": name, "step": step, "floors": 2})
        else:
            b = int(name[5:7])
            build_race_house(name, BARRIO_KEY[b], bpy.data.objects[f"MARKER_Bld_{name}"], step, g, capped)
    bpy.context.view_layer.update()
    # 3. razas
    built = razas_lots(st, g)
    new_rows = []
    for name, b, m in built:
        if BARRIO_KEY[b] == "R05":
            yurt_house(name, m, new_rows)
        else:
            build_race_house(name, BARRIO_KEY[b], m, None, g, new_rows)
    bpy.context.view_layer.update()
    print("razas", st["razas"], [r_["name"] for r_ in new_rows], flush=True)
    # Faro: las casas nuevas suben a 3 plantas solo si no tapan; si tapan, escalera a -> b -> c
    steps = {r_["name"]: None for r_ in new_rows}
    for it in range(4):
        res, bl = faro_round(st, it, set(steps), FARO_CAPS)
        todo = [n for n in steps if n in bl and steps[n] != "c"]
        if not todo:
            break
        for n in todo:
            m = bpy.data.objects[f"MARKER_Bld_{n}"]
            b = int(n[5:7])
            if BARRIO_KEY[b] == "R05":
                steps[n] = "c"                                   # yurta: a y b no aplican
                yurt_house(n, m, [], "c")
            else:
                steps[n] = {None: "a", "a": "b", "b": "c"}[steps[n]]
                build_race_house(n, BARRIO_KEY[b], m, steps[n], g, [])
        bpy.context.view_layer.update()
    # puntos de calle que tapan SOLO las casas nuevas (si es 0, no quitan visibilidad: otros ya tapan esas visuales)
    F.POINTS.clear()
    res, bl = F.measure()
    newset = set(steps)
    sole = [p for p in F.POINTS if p["roots"] and set(p["roots"]) <= newset]
    st["faro_final_stage25"] = {k: {"pct": v["pct"], "points": v["points"], "visible": v["visible"]} for k, v in res.items()}
    st["razas"]["points_blocked_only_by_new_houses"] = [{"kind": p["kind"], "street": p["street"],
                                                        "roots": p["roots"]} for p in sole]
    st["razas"]["new_still_blocking"] = sorted(n for n in steps if n in bl)
    st["faro_caps"] = [{"name": n, "step": s, "h_before": before[n],
                        "h_after": height_now(bpy.data.objects[n])} for n, s in FARO_CAPS.items()]
    st["razas"]["new_houses"] = [{"name": n, "barrio": int(n[5:7]), "faro_step": s or "-",
                                  "floors": bpy.data.objects[n].get("floors", 1),
                                  "height_m": height_now(bpy.data.objects[n])} for n, s in steps.items()]
    save()
    with open(REPORT, "w") as fh:
        json.dump(st, fh, indent=1, ensure_ascii=False, default=str)
    print("saved:", OUT, flush=True)
    _ = caz


if __name__ == "__main__":
    main()
