"""
CONCORDIA - Etapa 23 (E10): viviendas de las Moradas. concordia_v22.blend -> concordia_v23.blend (guardada antes)
+ export/godot/moradas_NE.glb, _NO, _SE, _SO + docs/reports/stage23_moradas.json

1. Plan de secciones: cada casa parte de su seccion por defecto (cubierta alta del lado de la muralla) y una prueba
   de rayos con volumenes envolventes busca las puertas que CAM_Iso no veria por culpa de casas de OTRA terraza;
   la casa que tapa baja el lado que da a esas puertas (y, si no basta, una planta o la pendiente).
2. Mallas por (tipo, variante, fachada, seccion), instanciadas en los marcadores; LOD1 (0.5) y LOD2 (caja con tejado).
3. Puertas DOOR_Morada (pintura por instancia), placa, MARKER_Lantern + LANTERN_Shard, MARKER_Morada_Door y
   MARKER_TrophyCase; comprobacion final con las mallas reales y exportacion por conjunto.
"""

import json
import math
import os
import random
import sys
from collections import Counter, defaultdict

import bpy  # noqa: I001
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import concordia_const as C  # noqa: E402
import bld_kit as K  # noqa: E402
import concordia_buildings as B  # noqa: E402
import stage13_portal as P13  # noqa: E402
import stage21_razas as R  # noqa: E402
import stage23_moradas as M  # noqa: E402
import lod_utils as LU  # noqa: E402

REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
SRC = os.path.join(REPO, "blender", f"{C.BLEND_BASENAME}_v22.blend")
OUT = os.path.join(REPO, "blender", f"{C.BLEND_BASENAME}_v23.blend")
REPORT = os.path.join(REPO, "docs", "reports", "stage23_moradas.json")
EXP = os.path.join(REPO, "export", "godot")
SEED = 2301
SETS = ("NE", "NO", "SO", "SE")


def tris(o):
    return sum(len(p.vertices) - 2 for p in o.data.polygons) if o and o.type == "MESH" else 0


def tris_me(me):
    return sum(len(p.vertices) - 2 for p in me.polygons)


def save():
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)


def ensure_col(name, parent=None):
    c = bpy.data.collections.get(name)
    if c is None:
        c = bpy.data.collections.new(name)
        (parent or bpy.context.scene.collection).children.link(c)
    return c


# --------------------------------------------------------------------------- plan y oclusion
def default_plan(tipo, v, facing):
    low = "back" if facing == "out" else "front"         # cubierta alta del lado de la muralla
    if tipo == "habitacion":
        return {"floors": 3, "roof": "lean", "low_side": low}
    if tipo == "casa_pequena":
        return {"floors": 1, "roof": "lean" if v < 2 else "gable", "low_side": low}
    return {"floors": 2, "roof": "gable", "low_side": None, "pitch": 32.0}


def remedy(tipo, plan):
    """Siguiente paso para bajar el lado de la casa que tapa; None si ya no se puede."""
    p = dict(plan)
    if p["roof"] == "lean" and p["low_side"] != "back":
        p["low_side"] = "back"
        return p, "lado trasero bajo"
    if tipo == "habitacion" and p["floors"] == 3:
        p["floors"] = 2
        return p, "2 plantas"
    if tipo == "casa_pequena" and p["roof"] == "gable":
        p.update(roof="lean", low_side="back")
        return p, "a un agua con el lado trasero bajo"
    if tipo == "casa_grande" and p["roof"] == "gable":
        p.update(roof="catslide", pitch=28.0)
        return p, "faldon trasero largo (3.8 m)"
    return None, None


def proxy_polys(h):
    """Poligonos (mundo) de la envolvente de una casa."""
    from mathutils.geometry import tessellate_polygon
    mw = h["mw"]
    out = []
    profs, boxes = M.proxy_parts(h["tipo"], h["plan"])
    for prof, x0, x1 in profs:
        tri = tessellate_polygon([[Vector((y, z, 0)) for y, z in prof]])
        for x in (x0, x1):
            for t in tri:
                out.append([mw @ Vector((x, prof[i][0], prof[i][1])) for i in t])
        for i in range(len(prof)):
            j = (i + 1) % len(prof)
            out.append([mw @ Vector((x0, prof[i][0], prof[i][1])), mw @ Vector((x0, prof[j][0], prof[j][1])),
                        mw @ Vector((x1, prof[j][0], prof[j][1])), mw @ Vector((x1, prof[i][0], prof[i][1]))])
    for lo, hi in boxes:
        c = [Vector((x, y, z)) for x in (lo[0], hi[0]) for y in (lo[1], hi[1]) for z in (lo[2], hi[2])]
        for f in ((0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)):
            out.append([mw @ c[i] for i in f])
    return out


def door_targets(h):
    """Puntos de las puertas que miran a la camara (a 1 m de altura, 0.35 m por delante)."""
    cb = B.iso_cam_back()
    cxy = Vector((cb.x, cb.y, 0)).normalized()
    n = (h["mw"].to_3x3() @ Vector((0, 1, 0))).normalized()
    if n.dot(cxy) < -0.05:
        return []
    return [(h["mw"] @ Vector((x, M.YF + 0.35, f * M.FH + 1.0)), (x, f)) for x, f in M.doors_of(h["tipo"], h["v"], h["plan"])]


def occlusion(houses, polys_fn):
    """[(casa, puerta, casa_que_tapa)] con rayos hacia CAM_Iso contra las envolventes / mallas de todas las casas."""
    verts, faces, owner = [], [], []
    for k, h in enumerate(houses):
        for poly in polys_fn(h):
            i0 = len(verts)
            verts += [tuple(p) for p in poly]
            faces.append(list(range(i0, i0 + len(poly))))
            owner.append(k)
    bvh = BVHTree.FromPolygons(verts, faces, epsilon=1e-6)
    d = B.iso_cam_back().normalized()
    res, n_t = [], 0
    for k, h in enumerate(houses):
        for p, door in door_targets(h):
            n_t += 1
            o = p.copy()
            for _ in range(8):
                loc, _n, idx, dist = bvh.ray_cast(o, d, 400.0)
                if loc is None:
                    break
                if owner[idx] == k:
                    o = loc + d * 0.02
                    continue
                res.append((k, door, owner[idx]))
                break
    return res, n_t


def plan_sets(houses, st):
    """Ajusta los planes hasta que ninguna casa de otra terraza tape una puerta (o se agoten los remedios)."""
    log = []
    for it in range(6):
        blocked, n_t = occlusion(houses, proxy_polys)
        other = [(a, door, b) for a, door, b in blocked if houses[a]["terraza"] != houses[b]["terraza"]]
        log.append({"iter": it, "door_targets": n_t, "blocked_other_terrace": len(other),
                    "blocked_same_terrace": len(blocked) - len(other)})
        if not other:
            break
        changed = False
        for b in sorted({b for _a, _d, b in other}):
            h = houses[b]
            p, why = remedy(h["tipo"], h["plan"])
            if p is not None:
                h["plan"] = p
                h.setdefault("remedies", []).append(why)
                changed = True
        if not changed:
            break
    st["occlusion_plan"] = log
    return log


# --------------------------------------------------------------------------- mallas
_CACHE, _LODS = {}, {}


def mb_mesh(name, mb, uv=True):
    mb.finish()
    old = bpy.data.meshes.get(name)
    if old is not None:
        bpy.data.meshes.remove(old)
    me = bpy.data.meshes.new(name)
    mb.bm.to_mesh(me)
    for n in mb.mats:
        me.materials.append(bpy.data.materials[n])
    mb.bm.free()
    if uv:
        tmp = bpy.data.objects.new("TMP_uv", me)
        bpy.context.scene.collection.objects.link(tmp)
        B.box_uv(tmp)
        bpy.data.objects.remove(tmp)
    return me


def plan_key(plan):
    return f"f{plan['floors']}{plan['roof'][0]}{(plan['low_side'] or 'n')[0]}{int(plan.get('pitch', 0))}"


def house_meshes(tipo, v, facade, plan, col):
    key = (tipo, v, facade, plan_key(plan))
    if key in _CACHE:
        return _CACHE[key]
    base = f"MOR_{tipo}_v{v}_{facade[-1]}_{plan_key(plan)}"
    body, roof, cm = K.MB(), K.MB(), K.MB()
    rng = random.Random(f"{SEED}-{base}")
    info = M.BUILDERS[tipo](body, roof, cm, v, facade, plan, rng)
    lmb = K.MB()
    M.lod2(lmb, tipo, plan, info)
    meb, mer = mb_mesh(f"{base}_Body", body), mb_mesh(f"{base}_Roof", roof)
    mec = mb_mesh(f"{base}-colonly", cm, uv=False)
    me2 = mb_mesh(f"{base}_LOD2", lmb, uv=False)
    tmpb = bpy.data.objects.new("TMP_avg_b", meb)
    tmpr = bpy.data.objects.new("TMP_avg_r", mer)
    flat = LU.flat_material(f"MAT_LOD2_{base}", LU.average_color([tmpb, tmpr]))
    bpy.data.objects.remove(tmpb)
    bpy.data.objects.remove(tmpr)
    me2.materials.clear()
    me2.materials.append(flat)
    lod1 = {}
    for part, me in (("Body", meb), ("Roof", mer)):
        tmp = bpy.data.objects.new(f"TMPL_{base}_{part}", me)
        col.objects.link(tmp)
        P13.lods(tmp, col, (("LOD1", 0.5),))
        o = bpy.data.objects[f"{tmp.name}_LOD1"]
        o.data.name = f"{base}_{part}_LOD1"
        lod1[part] = o.data
        bpy.data.objects.remove(o)
        bpy.data.objects.remove(tmp)
    _CACHE[key] = {"Body": meb, "Roof": mer, "col": mec, "LOD2": me2, "Body_LOD1": lod1["Body"],
                   "Roof_LOD1": lod1["Roof"], "info": info, "base": base}
    return _CACHE[key]


def shared(name, fn):
    me = bpy.data.meshes.get(name)
    if me is None:
        mb = K.MB()
        fn(mb)
        me = mb_mesh(name, mb)
    return me


def obj(name, me, col, parent, local=Matrix.Identity(4), hide=False):
    o = bpy.data.objects.new(name, me)
    col.objects.link(o)
    o.parent = parent
    o.matrix_parent_inverse = Matrix.Identity(4)
    o.matrix_basis = local
    if hide:
        o.hide_render = True
        o.hide_set(True)
    return o


def empty(name, col, parent, loc, **props):
    e = bpy.data.objects.new(name, None)
    e.empty_display_type = "SINGLE_ARROW"
    e.empty_display_size = 0.5
    col.objects.link(e)
    e.parent = parent
    e.matrix_parent_inverse = Matrix.Identity(4)
    e.location = loc
    for k, val in props.items():
        e[k] = val
    return e


# --------------------------------------------------------------------------- casas
def collect(key):
    mk = sorted(bpy.data.collections[f"MARKERS_Morada_{key}"].objects, key=lambda o: o.name)
    rows = defaultdict(list)
    for m in mk:
        a = math.atan2(m.matrix_world.translation.y, m.matrix_world.translation.x)
        rows[m["terraza"]].append((a, m))
    houses = []
    si = SETS.index(key)
    for t, row in sorted(rows.items()):
        row.sort(key=lambda r: r[0])
        for i, (_a, m) in enumerate(row):
            tipo = m["tipo"]
            v = (i + 2 * t + si) % 4
            facing = "out" if "muralla" in str(m.get("door_side", "")) else "in"
            houses.append({"marker": m, "mw": m.matrix_world.copy(), "tipo": tipo, "v": v, "terraza": t,
                           "facade": M.FACADES[(2 * i + t + si) % 3], "paint_i": (5 * i + t + si) % 6,
                           "number": f"{key}-{t}{i + 1:02d}", "facing": facing, "plan": default_plan(tipo, v, facing)})
    return houses


def build_house(h, key, col, pcol):
    m = h["marker"]
    nnn = m.name.split("_")[-1]
    name = f"Morada_{key}_{nnn}"
    root = bpy.data.objects.new(name, None)
    col.objects.link(root)
    root.matrix_world = h["mw"]
    for k_, v_ in (("marker", m.name), ("tipo", h["tipo"]), ("variant", h["v"]), ("facade", h["facade"]),
                   ("terraza", h["terraza"]), ("section", plan_key(h["plan"])), ("house_number", h["number"])):
        root[k_] = v_
    root["remedies"] = ", ".join(h.get("remedies", [])) or "-"
    ms = house_meshes(h["tipo"], h["v"], h["facade"], h["plan"], col)
    objs = {"Body": obj(f"{name}_Body", ms["Body"], col, root), "Roof": obj(f"{name}_Roof", ms["Roof"], col, root)}
    for part in ("Body_LOD1", "Roof_LOD1"):
        objs[part] = obj(f"{name}_{part}", ms[part], col, root, hide=True)
    objs["LOD2"] = obj(f"{name}_LOD2", ms["LOD2"], col, root, hide=True)
    c = obj(f"{name}-colonly", ms["col"], col, root)
    c.hide_render = True
    c.display_type = "WIRE"
    door_me = shared("DOOR_Morada", M.door_mesh)
    lan_me = shared("LANTERN_Shard", M.lantern_mesh)
    plate_me = bpy.data.meshes.get("PLATE_Morada")
    if plate_me is None:
        plate_me = bpy.data.meshes.new("PLATE_Morada")
        M.plate_mesh(plate_me)
        plate_me.materials.append(bpy.data.materials[M.PLATE])
    paints = list(M.PAINTS)
    extras = []
    for i, (x, f) in enumerate(M.doors_of(h["tipo"], h["v"], h["plan"]), 1):
        z = f * M.FH
        d = obj(f"DOOR_Morada_{key}_{nnn}_{i}", door_me, col, root, Matrix.Translation((x, M.YF, z)))
        paint = paints[(h["paint_i"] + i) % len(paints)] if h["tipo"] == "habitacion" else paints[h["paint_i"]]
        slot = next(k for k, s in enumerate(d.material_slots) if s.material and s.material.name.startswith("MAT_Door_Paint"))
        d.material_slots[slot].link = "OBJECT"
        d.material_slots[slot].material = bpy.data.materials[paint]
        d["paint_material"] = paint
        d["paint_param"] = "material_override de la hoja (ranura de pintura): textura por instancia"
        d["house_number"] = f"{h['number']}" + (f".{i}" if h["tipo"] == "habitacion" else "")
        d["lantern"] = f == 0
        pl = obj(f"PLATE_Morada_{key}_{nnn}_{i}", plate_me, col, d, Matrix.Translation((0.0, 0.1, 2.62)))
        pl["decal"] = "numero de la casa (0.3 x 0.2 m, UV 0..1)"
        lm = empty(f"MARKER_Lantern_{key}_{nnn}_{i}", col, d, (0.85, 0.02, 2.05), door=d.name,
                   note="soporte del farol (LANTERN_Shard); parametrizable en Godot")
        lm.empty_display_type = "PLAIN_AXES"
        extras += [d, pl]
        if f == 0:
            extras.append(obj(f"LANTERN_Shard_{key}_{nnn}_{i}", lan_me, col, lm))
        empty(f"MARKER_Morada_Door_{key}_{nnn}_{i}", col, root, (x, M.YF + 0.3, z), house=name, door=d.name,
              floor=f, interior="propio (escena aparte)", axis="+Y fuera")
        if h["tipo"] == "habitacion" or i == 1:
            tc = empty(f"MARKER_TrophyCase_{key}_{nnn}_{i}", col, root, (x if h["tipo"] == "habitacion" else -x * 0.5,
                                                                         M.YF - 2.0, z + 1.0), house=name)
            tc.empty_display_type = "CUBE"
    h.update(root=root, objs=objs, extras=extras, name=name)
    return root


def remove_house(h):
    r = h["root"]
    for o in list(r.children_recursive) + [r]:
        bpy.data.objects.remove(o)


def real_polys_factory():
    cache = {}

    def fn(h):
        out = []
        for o in [h["objs"]["Body"], h["objs"]["Roof"]]:
            mw = o.matrix_world
            me = o.data
            key = me.name
            if key not in cache:
                cache[key] = [[me.vertices[i].co.copy() for i in p.vertices] for p in me.polygons]
            out += [[mw @ c for c in poly] for poly in cache[key]]
        return out
    return fn


def main():
    st = {"budgets": M.BUDGET}
    bpy.ops.wm.open_mainfile(filepath=SRC)
    save()
    st["saved_before"] = os.path.relpath(OUT, REPO)
    B.ensure_materials()
    st["materials"] = M.ensure_materials()
    top = ensure_col("BLD_MORADAS")
    for o in list(top.all_objects):
        bpy.data.objects.remove(o)
    import stage11_godot as G
    st["sets"] = {}
    for key in SETS:
        col = ensure_col(f"BLD_MORADAS_{key}", top)
        houses = collect(key)
        sst = {"houses": len(houses), "types": dict(Counter(h["tipo"] for h in houses))}
        plan_sets(houses, sst)
        for h in houses:
            build_house(h, key, col, col)
        bpy.context.view_layer.update()
        real_log = []
        for it in range(4):
            blocked, n_t = occlusion(houses, real_polys_factory())
            occ = sorted({b for a, _d, b in blocked if houses[a]["terraza"] != houses[b]["terraza"]})
            real_log.append({"iter": it, "blocked_other_terrace": sum(1 for a, _d, b in blocked
                                                                      if houses[a]["terraza"] != houses[b]["terraza"]),
                             "occluders": [houses[b]["name"] for b in occ]})
            redo = []
            for b in occ:
                p, why = remedy(houses[b]["tipo"], houses[b]["plan"])
                if p is not None:
                    houses[b]["plan"] = p
                    houses[b].setdefault("remedies", []).append(why + " (malla real)")
                    redo.append(b)
            if not redo:
                break
            for b in redo:
                remove_house(houses[b])
                build_house(houses[b], key, col, col)
            bpy.context.view_layer.update()
        sst["occlusion_real_iterations"] = real_log
        blocked, n_t = occlusion(houses, real_polys_factory())
        other = [(houses[a]["name"], door, houses[b]["name"]) for a, door, b in blocked
                 if houses[a]["terraza"] != houses[b]["terraza"]]
        same = [(houses[a]["name"], door, houses[b]["name"]) for a, door, b in blocked
                if houses[a]["terraza"] == houses[b]["terraza"]]
        sst["occlusion_final_real_meshes"] = {"door_targets_facing_camera": n_t, "blocked_by_other_terrace": len(other),
                                              "blocked_by_same_terrace_neighbour": len(same),
                                              "examples_other": other[:6], "examples_same": same[:6]}
        # triangulos medidos
        t0 = sum(tris(h["objs"]["Body"]) + tris(h["objs"]["Roof"]) for h in houses)
        tx = sum(tris(o) for h in houses for o in h["extras"] if o.type == "MESH")
        t1 = sum(tris(h["objs"]["Body_LOD1"]) + tris(h["objs"]["Roof_LOD1"]) for h in houses)
        t2 = sum(tris(h["objs"]["LOD2"]) for h in houses)
        per = defaultdict(list)
        for h in houses:
            per[h["tipo"]].append(tris(h["objs"]["Body"]) + tris(h["objs"]["Roof"]) +
                                  sum(tris(o) for o in h["extras"] if o.type == "MESH"))
        sst.update({"units_doors": sum(len(M.doors_of(h["tipo"], h["v"], h["plan"])) for h in houses),
                    "tris_LOD0_houses": t0, "tris_LOD0_doors_plates_lanterns": tx, "tris_LOD0_total": t0 + tx,
                    "tris_LOD1": t1, "tris_LOD2": t2, "lod1_ratio": round(t1 / t0, 3), "lod2_ratio": round(t2 / t0, 3),
                    "per_type_max": {k: max(v) for k, v in per.items()},
                    "per_type_ok": {k: max(v) <= M.BUDGET[k] for k, v in per.items()},
                    "remedies": dict(Counter(", ".join(h.get("remedies", [])) or "-" for h in houses)),
                    "sections": dict(Counter(f"{h['tipo']}:{plan_key(h['plan'])}" for h in houses)),
                    "per_terrace": {t: [f"{h['tipo'][:4]}v{h['v']}{h['facade'][-1]}" for h in houses if h["terraza"] == t]
                                    for t in sorted({h["terraza"] for h in houses})}})
        objs = []
        for h in houses:
            objs += [h["root"]] + list(h["root"].children_recursive)
        path = os.path.join(EXP, f"moradas_{key}.glb")
        size = G.export_glb(list(dict.fromkeys(objs)), path)
        sst["export"] = {"file": os.path.relpath(path, REPO), "mb": round(size / 2 ** 20, 2), **G.glb_info(path)}
        st["sets"][key] = sst
        print(key, json.dumps({k: sst[k] for k in ("houses", "units_doors", "tris_LOD0_total", "tris_LOD2", "lod1_ratio",
                                                    "lod2_ratio", "per_type_max", "remedies", "occlusion_plan",
                                                    "occlusion_final_real_meshes")}, default=str)[:1400], flush=True)
    st["unique_meshes"] = len(_CACHE)
    st["totals"] = {k: sum(s[k] for s in st["sets"].values()) for k in ("houses", "units_doors", "tris_LOD0_total",
                                                                        "tris_LOD2")}
    for o in bpy.data.objects:
        if o.name.endswith(("_LOD1", "_LOD2")):
            o.hide_render = True
            o.hide_set(True)
    save()
    with open(REPORT, "w") as fh:
        json.dump(st, fh, indent=1, ensure_ascii=False, default=str)
    print("saved:", OUT, "unique meshes", len(_CACHE), st["totals"])
    print(json.dumps(st["materials"], default=str)[:600])
    _ = R


if __name__ == "__main__":
    main()
