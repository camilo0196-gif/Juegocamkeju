"""
CONCORDIA - Etapa 26 (E8, punto 5 autorizado): casas que faltan en los barrios de las Razas.

Solo dentro del sector Sur (+-25 grados, r 60-185). Permitido por el usuario en esta etapa:
  a) recolocar/compactar edificios de Razas dentro del sector;
  b) dividir parcelas de 8 x 8 en 2 casas adosadas de 4 x 8 (cada una con su puerta, hasta 3 plantas, techo y color
     distintos);
  c) usar ambos lados de los anillos r 100 y r 150.
Prohibido: parcelas sobre calles, plazas, escalinatas o puentes; tapar puertas. Meta 6 casas por barrio (minimo 5).

Orden aplicado: (b) dividir las parcelas de 8 x 8 de B05 y B06 (sus unicas casas); huecos nuevos de 4 x 8 (rejilla
de 1 m, frente a calle a <= 3.5 m, desnivel <= 2.5 m cubierto por el zocalo) y parejas adosadas en ellos; (c) los
huecos al otro lado del anillo r 100 cuentan para el barrio mas cercano que necesite casas (<= 40 m). (a) no se
aplica: los unicos bloques que se podrian mover son las Casas de Raza (20 x 16) y las plazuelas, que son fijas.
B05 (pieles y madera) usa yurtas pequenas (r 1.85 m) en las parcelas de 4 x 8.
"""

import math
import random

import bpy
from mathutils import Matrix, Vector

BARRIO_KEY = {1: "R01", 2: "R02", 3: "R03", 4: "R04", 5: "R05", 6: "R06"}
TARGET, MINIMUM = 6, 5


def _count(b):
    return sum(1 for o in bpy.data.objects if o.parent is None and o.type == "EMPTY" and o.name.startswith(f"RAZ_B{b:02d}_Casa_"))


def _next_name(b):
    i = 1
    while bpy.data.objects.get(f"MARKER_Bld_RAZ_B{b:02d}_Casa_{i:02d}") is not None:
        i += 1
    return f"RAZ_B{b:02d}_Casa_{i:02d}"


def _marker(name, mw, g, b, extra):
    col = next(o for o in bpy.data.objects if o.name.startswith("MARKER_Bld_RAZ_B0")).users_collection[0]
    m = bpy.data.objects.new(f"MARKER_Bld_{name}", None)
    col.objects.link(m)
    m.empty_display_type = "ARROWS"
    c = mw.translation
    zs = [g(*(mw @ Vector((x, y, 0))).xy) for x in (-2, 0, 2) for y in (-4, 0, 4)]
    m.matrix_world = Matrix.Translation((c.x, c.y, max(zs))) @ mw.to_3x3().to_4x4()
    for k, v in {"footprint": "4x8", "footprint_w": 4.0, "footprint_d": 8.0, "door_direction": "+Y", "interior": False,
                 "type": "house", "label": "Casa", "district": "Razas", "pad_z": round(max(zs), 3), "shape": "rect",
                 "decor": True, "barrio": b, "added_stage": 26, **extra}.items():
        m[k] = v
    bpy.context.view_layer.update()
    return m


def small_yurt(name, marker, rng, pitch):
    """Yurta de 4 x 8: r 1.85 m en la mitad delantera (puerta a +Y), LOD1/LOD2, colision y marcador de puerta."""
    import concordia_buildings as B
    import bld_kit as K
    import build_stage16 as B16
    import build_stage19 as B19
    import lod_utils as LU
    import stage13_portal as P13
    import stage21_razas as R
    col = bpy.data.collections["BLD_RAZAS"]
    root = B16.new_root(name, marker, col, "Casa (yurta)")
    if "landmark" in root:
        del root["landmark"]
    root["building"] = True
    root["footprint_w"], root["footprint_d"] = 4.0, 8.0
    root["race_preset"] = "R05"
    root["floors"] = 1
    body, roof = K.MB(), K.MB()
    cy = 1.6
    zc, dloc = R.yurt(body, roof, 0.0, cy, 1.85, 3.0, pitch, rng, door=(math.pi / 2, 1.0), n=12, detail=0, patches=1)
    bo = B16.mesh_obj(body, f"{name}_Body", col, root)
    ro = B16.mesh_obj(roof, f"{name}_Roof", col, root)
    P13.lods(bo, col, (("LOD1", 0.5),))
    P13.lods(ro, col, (("LOD1", 0.5),))
    LU.massing_spec(f"{name}_Body_LOD2", [("cyl", 0.0, cy, 1.85, 0.0, 3.0, 8), ("cone", 0.0, cy, 2.2, 2.9, zc + 0.4, 8)],
                    [bo, ro], col, root)
    B16.door_marker(name, col, root, dloc)
    pe = bpy.data.objects.new(f"{name}_Props", None)
    col.objects.link(pe)
    pe.parent = root
    B19.box_collider(f"{name}-colonly", col, root, [((-1.6, cy - 1.6, 0), (1.6, cy + 1.6, 3.0))])
    _ = B
    return root


def build(name, b, marker, floors, g, rng):
    import build_stage25 as B25
    if BARRIO_KEY[b] == "R05":
        return small_yurt(name, marker, rng, rng.choice((24.0, 28.0, 32.0)))
    rows = []
    B25.build_race_house(name, BARRIO_KEY[b], marker, floors, g, rows)
    return bpy.data.objects[name]


def doors_ok(root, radius=45.0):
    """Puertas a <= radius de la casa nueva: ninguna tapada por ella; y la suya visible."""
    import build_stage26 as S26
    bvh, owner = S26.city_bvh()
    c = root.matrix_world.translation
    bad = []
    for dm in bpy.data.objects:
        if not (dm.type == "EMPTY" and dm.name.startswith("MARKER_") and "_Door" in dm.name and "alias_of" not in dm
                and not dm.name.startswith("MARKER_Bld_") and dm.parent is not None):
            continue
        if (dm.matrix_world.translation - c).length > radius:
            continue
        r = dm
        while r.parent is not None:
            r = r.parent
        n = (dm.matrix_world.to_3x3() @ Vector((0, 1, 0))).normalized()
        cxy = Vector((S26.CAM_BACK.x, S26.CAM_BACK.y, 0)).normalized()
        if n.dot(cxy) < -0.05:
            continue
        ok, _h, by = S26.door_visible(dm, bvh, owner, r.name)
        if not ok and (r.name == root.name or root.name in by):
            bad.append((dm.name, by))
    return bad


def place(name, b, mw, g, rng, floors_choice, extra, log):
    """Construye con las plantas pedidas; si tapa una puerta (o la suya queda tapada), baja de plantas; si no basta,
    la quita."""
    import build_stage25 as B25
    m = _marker(name, mw, g, b, extra)
    for floors in floors_choice:
        root = build(name, b, m, floors, g, random.Random(rng.random()))
        bpy.context.view_layer.update()
        bad = doors_ok(root)
        if not bad:
            log.append({"name": name, "barrio": b, "floors": root.get("floors", floors),
                        "center": [round(m.matrix_world.translation.x, 1), round(m.matrix_world.translation.y, 1)],
                        "height_m": B25.height_now(root), **extra})
            return root
        B25.remove_tree(root)
        if BARRIO_KEY[b] == "R05":
            break
    bpy.data.objects.remove(m)
    log.append({"name": name, "barrio": b, "rejected": "tapa una puerta o queda tapada", "doors": bad, **extra})
    return None


def split_existing(name, b, g, rng, log):
    """(b) Parcela de 8 x 8 -> 2 adosadas de 4 x 8 (izquierda / derecha), plantas distintas y otro tono."""
    import build_stage25 as B25
    m = bpy.data.objects[f"MARKER_Bld_{name}"]
    mw = m.matrix_world.copy()
    B25.remove_tree(bpy.data.objects[name])
    bpy.data.objects.remove(m)
    bpy.context.view_layer.update()
    names = [f"RAZ_B{b:02d}_Casa_01", None]
    out = []
    for k, dx in enumerate((-2.0, 2.0)):
        nm = names[k] or _next_name(b)
        fl = (3, 2, 1) if k == 0 else (2, 1)
        r = place(nm, b, mw @ Matrix.Translation((dx, 0, 0)), g, rng, fl,
                  {"adosada": True, "split_from": f"{name} (8x8)", "pair_side": "izq" if k == 0 else "der"}, log)
        out.append(r)
    differentiate(out[0], out[1], b)
    return out


def differentiate(r1, r2, b):
    """Adosadas: si las dos cubiertas llevan el mismo tono, la segunda pasa al otro tono del preset."""
    import stage21_razas as R
    if r1 is None or r2 is None or BARRIO_KEY[b] == "R05":
        return False

    def mats(r, part):
        o = bpy.data.objects.get(f"{r.name}_{part}")
        return {s.material.name for s in o.material_slots if s.material} if o else set()
    p = R.RACE_PRESETS[BARRIO_KEY[b]]
    a, bm = p["roof_mat"], p["roof_mat_b"]
    m1, m2 = mats(r1, "Roof"), mats(r2, "Roof")
    if (a in m1) != (a in m2) or (bm in m1) != (bm in m2):
        return False
    for part in ("Roof", "Roof_LOD1"):
        o = bpy.data.objects.get(f"{r2.name}_{part}")
        if o is None:
            continue
        for sl in o.material_slots:
            if sl.material and sl.material.name in (a, bm):
                sl.material = bpy.data.materials[bm if sl.material.name == a else a]
    r2["roof_tone"] = "cambiado para distinguirla de su adosada"
    return True


def pair_lots(grid, lot, taken):
    """Parcela de 4 x 8 adosada a 'lot' (a +-4 m en su eje x local, mismo giro)."""
    c = Vector(lot["center"])
    rm = Matrix.Rotation(lot["theta"], 2)
    for dx in (4.0, -4.0):
        c2 = c + rm @ Vector((dx, 0.0))
        if any((c2 - Vector(t["center"])).length < 4.0 for t in taken):
            continue
        r = grid.rect_ok(c2, lot["theta"], 4.0, 8.0, margin=0.15, max_slope=2.5, front_need=0.3)
        if r:
            r.update(w=4.0, d=8.0, pair_of=tuple(lot["center"]))
            return r
    return None


def step(st):
    import build_stage18 as B18
    import build_stage25 as B25
    import stage25_lots as LOTS
    g = B18.ground_fn()
    rng = random.Random(2601)
    before = {b: _count(b) for b in range(1, 7)}
    log = []
    # (b) dividir las parcelas de 8 x 8 de los barrios que no llegan
    for b, name in ((5, "RAZ_B05_Casa_01"), (6, "RAZ_B06_Casa_01")):
        split_existing(name, b, g, rng, log)
    # huecos de 4 x 8 y sus parejas adosadas
    grid = LOTS.Grid(270.0, 25.0, 60.0, 185.0)
    cen = B25.barrio_centroids()
    lots = grid.search(4.0, 8.0, (0.0, -90.0), max_n=120, front_need=0.3, max_slope=2.5, margin=0.15)
    allots = list(lots)
    for lot in lots:
        p = pair_lots(grid, lot, allots)
        if p:
            allots.append(p)
    need = {b: max(0, TARGET - _count(b)) for b in range(1, 7)}
    assigned = []
    unused = []
    for lot in sorted(allots, key=lambda lt: min((Vector(lt["center"]) - cen[b].xy).length for b in cen)):
        c = Vector(lot["center"])
        cands = sorted(((c - cen[b].xy).length, b) for b in cen if need[b] > 0)
        if cands and cands[0][0] <= 40.0:
            b = cands[0][1]
            need[b] -= 1
            assigned.append((lot, b))
        else:
            near = min(cen, key=lambda bb: (c - cen[bb].xy).length)
            unused.append({"center": [round(c.x, 1), round(c.y, 1)], "nearest": near,
                           "dist_m": round((c - cen[near].xy).length, 1)})
    built = {}
    for lot, b in assigned:
        c = Vector(lot["center"])
        mw = Matrix.Translation((c.x, c.y, 0.0)) @ Matrix.Rotation(lot["theta"], 4, "Z")
        across = abs(math.hypot(c.x, c.y) - 100.0) < 25 and (math.hypot(c.x, c.y) > 100) != (cen[b].xy.length > 100)
        extra = {"adosada": "pair_of" in lot, "lot_slope_m": lot["slope"], "across_ring_r100": bool(across)}
        fl = (2, 1) if "pair_of" in lot else (3, 2, 1)
        r = place(_next_name(b), b, mw, g, rng, fl, extra, log)
        built[tuple(round(x, 2) for x in lot["center"])] = r
        if "pair_of" in lot:
            differentiate(built.get(tuple(round(x, 2) for x in lot["pair_of"])), r, b)
    after = {b: _count(b) for b in range(1, 7)}
    st["razas"] = {"before": before, "after": after, "target": TARGET, "minimum": MINIMUM,
                   "below_target": {f"B{b:02d}": after[b] for b in after if after[b] < TARGET},
                   "below_minimum": {f"B{b:02d}": {"have": after[b], "missing_for_5": MINIMUM - after[b],
                                                   "missing_for_6": TARGET - after[b]} for b in after if after[b] < MINIMUM},
                   "houses": log, "lots_found_4x8": len(lots), "pairs_found": len(allots) - len(lots),
                   "unused_lots": unused,
                   "rules": "sector Sur +-25 grados, r 60-185; 4 x 8 + 0.15 m de margen sin calle, plaza, escalinata, "
                            "puente ni objeto; frente a calle a <= 3.5 m; desnivel <= 2.5 m (zocalo); asignacion al barrio "
                            "mas cercano que necesite casas (<= 40 m); (a) compactar no se aplica (ver docstring)"}
    print("razas", before, after, flush=True)
