"""
CONCORDIA - Etapa 21 (E8): barrios de las razas. concordia_v20.blend -> concordia_v21.blend (guardada antes)
+ export/godot/concordia_razas.glb + docs/reports/stage21_razas.json

Uso: python build_stage21.py [N_RAZAS]   (por defecto stage21_razas.N_RAZAS = 6)

Por barrio: CasaRaza_xx (20 x 16, preset de la raza), RAZ_Bxx_Casa_yy en sus parcelas (assembler + preset) y la
plazuela (fuente pequena o arbol viejo + 4 bancos). Solo se usan parcelas existentes (no se inventan).
"""

import json
import math
import os
import random
import sys

import bpy  # noqa: I001
import bmesh
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import concordia_const as C  # noqa: E402
import bld_kit as K  # noqa: E402
import concordia_buildings as B  # noqa: E402
import stage13_portal as P13  # noqa: E402
import stage18_mercado as M  # noqa: E402
import stage19_oficios as O  # noqa: E402
import stage20_clases as CL  # noqa: E402
import stage21_razas as R  # noqa: E402
import build_stage16 as B16  # noqa: E402
import build_stage18 as B18  # noqa: E402
import build_stage19 as B19  # noqa: E402
import lod_utils as LU  # noqa: E402

REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
SRC = os.path.join(REPO, "blender", f"{C.BLEND_BASENAME}_v20.blend")
OUT = os.path.join(REPO, "blender", f"{C.BLEND_BASENAME}_v21.blend")
REPORT = os.path.join(REPO, "docs", "reports", "stage21_razas.json")
SEED = 2101
BUDGET = {"casa_raza": 6000, "house": 2500, "house_3f": 4000}
REQUESTED_HOUSES = (6, 10)
tris = B18.tris
SIDES = {"front": (0, 1), "back": (0, -1), "right": (1, 0), "left": (-1, 0)}
# niveles de ahorro: (module_w, roof_seg, detalle de los lados que ve la camara, detalle de los que no ve)
TIERS = [(None, 3.5, 0, 1), (3.6, 4.5, 0, 1), (4.0, 5.5, 1, 2), (4.5, 6.5, 1, 2)]


def save():
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)


def empty(name, col, parent, loc, **props):
    e = bpy.data.objects.new(name, None)
    e.empty_display_type = "SINGLE_ARROW"
    e.empty_display_size = 0.8
    col.objects.link(e)
    e.parent = parent
    e.location = loc
    for k, v in props.items():
        e[k] = v
    return e


def cam_dir_xy():
    b = B.iso_cam_back()
    return Vector((b.x, b.y)).normalized()


def visible_sides(rot_z):
    bxy = cam_dir_xy()
    rm = Matrix.Rotation(rot_z, 2)
    return {s: (rm @ Vector(n)).dot(bxy) > 0.05 for s, n in SIDES.items()}


def flag_angle():
    """Giro en Z para que la cara +Y de banderas y estandartes exentos mire hacia CAM_Iso."""
    bxy = cam_dir_xy()
    return math.atan2(-bxy.x, bxy.y)


def remove_tree(root):
    for o in list(root.children_recursive) + [root]:
        me = o.data if o.type == "MESH" else None
        bpy.data.objects.remove(o)
        if me is not None and me.users == 0:
            bpy.data.meshes.remove(me)


def skirt(mb, W, D, depth=0.6, out=0.08):
    """Faldon bajo rasante alrededor de la base (parcelas en cuesta): 8 cm fuera del muro, sin coplanarias."""
    hw, hd = W / 2 + out, D / 2 + out
    for lo, hi in (((-hw, -hd, -depth), (hw, -hd + 0.3, 0.02)), ((-hw, hd - 0.3, -depth), (hw, hd, 0.02)),
                   ((-hw, -hd + 0.3, -depth), (-hw + 0.3, hd - 0.3, 0.02)), ((hw - 0.3, -hd + 0.3, -depth), (hw, hd - 0.3, 0.02))):
        mb.box(lo, hi, K.M_GRAY, skip=("z-",))


def merge(obj, fn):
    mb = K.MB()
    fn(mb)
    M.merge_mb_into(obj, mb)
    mb.bm.free()


def ground_gap(root, W, D, g):
    """Cuanto queda el terreno por debajo de la base en el perimetro (m; >0 = hueco que cubre el faldon)."""
    mw = root.matrix_world
    z0 = mw.translation.z
    worst = 0.0
    for t in [i / 8 for i in range(9)]:
        for lp in ((-W / 2 + W * t, D / 2 + 0.1), (-W / 2 + W * t, -D / 2 - 0.1), (W / 2 + 0.1, -D / 2 + D * t),
                   (-W / 2 - 0.1, -D / 2 + D * t)):
            p = mw @ Vector((lp[0], lp[1], 0))
            worst = max(worst, z0 - g(p.x, p.y))
    return round(worst, 3)


# --------------------------------------------------------------------------- edificios del assembler con preset
def kit_race(name, key, marker, pisos, budget_fn, col, pcol, rng, g, plan_edit=None, extras=None, max_rise=7.5):
    """Assembler con el preset de la raza; prueba niveles de ahorro hasta entrar en presupuesto (budget_fn(plantas)).
    extras(root, objs, rep, key) anade torrecillas, banderas... y devuelve los triangulos que suma."""
    p = R.RACE_PRESETS[key]
    rot = marker.matrix_world.to_euler().z
    vis = visible_sides(rot)
    wall = rng.choice(p["wall"])
    table = R.roof_table(key)
    swap = rng.random() < 0.34                         # otro tono de tejado en una de cada tres casas
    if swap:
        table[K.M_ROOF], table[K.M_ROOF_B] = p["roof_mat_b"], p["roof_mat"]
    log = []
    for ti, (mw, seg, dv, dh) in enumerate(TIERS):
        sd = {s: (dv if vis[s] else dh) for s in SIDES}
        sd["front"] = min(sd["front"], 0 if ti < 3 else 1)
        opts = {"side_detail": sd, "roof_seg": seg, "wall_mat": wall, "door_scale": p["door_scale"], "no_buttress": True,
                "pitch": p["pitch"], "gable_mat": p["gable"], "max_rise": max_rise}
        root, objs, rep = B19.kit(name, pisos, col, pcol, marker=marker, tipo_techo=p["roof"], estilo=p["style"],
                                  module_w=mw, opts=opts, plan_edit=plan_edit)
        for k in ("Body", "Roof", "Body_LOD1", "Roof_LOD1", "Body_LOD2", "Roof_LOD2"):
            R.remap_materials(objs[k], table)
        W, D = rep["footprint"]
        gap = ground_gap(root, W, D, g)
        depth = max(0.6, gap + 0.2)                     # el faldon siempre llega 20 cm bajo el punto mas bajo
        merge(objs["Body"], lambda mb: skirt(mb, W, D, depth))
        merge(objs["Body_LOD1"], lambda mb: skirt(mb, W, D, depth))
        glazed = 0
        if p.get("glass"):
            glazed = R.glaze(objs["Body"], p["glass"]) + R.glaze(objs["Body_LOD1"], p["glass"])
        ex = extras(root, objs, rep, key) if extras else {}
        for k in ("Body", "Roof", "Body_LOD1", "Roof_LOD1"):
            B.box_uv(objs[k])
        t = tris(objs["Body"]) + tris(objs["Roof"]) + ex.get("tris", 0)
        bud = budget_fn(rep["floors"])
        log.append({"tier": ti, "floors": rep["floors"], "tris": t, "budget": bud})
        if t <= bud or ti == len(TIERS) - 1:
            rep["race"] = {"preset": key, "wall": wall, "skirt_depth_m": round(depth, 2), "roof_tone_swapped": swap, "tier": ti, "tiers_tried": log,
                           "side_detail": sd, "glass_panes": glazed, **{k: v for k, v in ex.items() if k != "tris"}}
            rep["tris_total"] = t
            return root, objs, rep
        remove_tree(root)
    raise RuntimeError(name)


def r04_turret(root, objs, rep, r, lantern, rng):
    """Torrecilla conica en la esquina trasera del lado contrario a la puerta (R04), en LOD0, LOD1 y LOD2."""
    W, D = rep["footprint"]
    dx = (rep["door_local"] or [0.0])[0]
    sx = -1.0 if dx > 0 else 1.0
    x, y = sx * (W / 2 - r + 0.15), -(D / 2 - r + 0.15)
    eave = rep["eave_height_m"]
    rise = rep["ridge_height_m"] - eave
    z_top = eave + (0.8 if lantern else 1.0)
    cone_h = rise + (0.6 if lantern else 1.5)
    p = R.RACE_PRESETS["R04"]
    apex = None
    for (bk, rk, det, n) in (("Body", "Roof", 0, 14), ("Body_LOD1", "Roof_LOD1", 1, 10), ("Body_LOD2", "Roof_LOD2", 1, 6)):
        bmb, rmb = K.MB(), K.MB()
        a = R.turret(bmb, rmb, x, y, r, z_top, cone_h, p["trim"], p["roof_mat"], glass=p["glass"], lantern=lantern, n=n,
                     detail=det)
        apex = apex or a
        M.merge_mb_into(objs[bk], bmb)
        M.merge_mb_into(objs[rk], rmb)
        bmb.bm.free()
        rmb.bm.free()
    return {"turret": {"center": [round(x, 2), round(y, 2)], "r": r, "apex_m": round(apex, 2), "lantern": lantern}}


def house_extras(rng):
    def fn(root, objs, rep, key):
        if key == "R04" and rng.random() < 0.6:
            return r04_turret(root, objs, rep, 1.3, False, rng)
        return {}
    return fn


# --------------------------------------------------------------------------- bandera y estandarte
def flag_top(rep, key):
    W, D = rep["footprint"]
    eave, ridge = rep["eave_height_m"], rep["ridge_height_m"]
    roof = R.RACE_PRESETS[key]["roof"]
    if roof == "gable":
        return (W / 2 - 1.2, 0.0, ridge + 0.05)
    if roof == "hip":
        return (max(0.0, (W - D) / 2), 0.0, ridge + 0.05)
    if roof == "spire":
        return (0.0, 0.0, ridge - 0.1)          # el mastil sustituye al remate del vertice
    if roof == "flat":
        return (W / 2 - 0.45, D / 2 - 0.45, eave + 0.9)
    return (0.0, 0.0, ridge)


def add_flag(name, key, root, col, base_local, pole_h=3.6):
    pole = B19.shared("RACE_FlagPole", lambda mb: R.flag_pole(mb, pole_h))
    po = bpy.data.objects.new(f"{name}_FlagPole", pole)
    col.objects.link(po)
    po.parent = root
    po.location = base_local
    fm = R.flag_mesh(f"RACE_Flag_{key}")
    if not fm.materials:
        fm.materials.append(bpy.data.materials[f"MAT_Banner_{key}"])
    fo = bpy.data.objects.new(f"{name}_Flag", fm)
    col.objects.link(fo)
    fo.parent = root
    bpy.context.view_layer.update()
    top = root.matrix_world @ Vector((base_local[0], base_local[1], base_local[2] + pole_h - 0.05))
    fo.matrix_world = Matrix.Translation(top) @ Matrix.Rotation(flag_angle(), 4, "Z") @ Matrix.Translation((0.06, 0, 0))
    fo["race_preset"] = key
    fo["swap_texture"] = f"MAT_Banner_{key} (UV recortada al simbolo)"
    return po, fo


def banner_obj(name, key, length, w=1.8, tip=0.45):
    mname = f"BANNER_{key}_{int(round(length * 100))}"
    me = bpy.data.meshes.get(mname)
    if me is None:
        bm = CL.banner(w=w, h=length, tip=tip)
        me = bpy.data.meshes.new(mname)
        bm.to_mesh(me)
        bm.free()
        me.materials.append(bpy.data.materials[f"MAT_Banner_{key}"])
    return me


def add_facade_banner(name, key, root, col, x, y, top, length):
    me = banner_obj(name, key, length)
    b = bpy.data.objects.new(f"{name}_Banner", me)
    col.objects.link(b)
    b.parent = root
    b.location = (x, y, top)
    b["race_preset"] = key
    b["swap_texture"] = f"MAT_Banner_{key} (UV 0..1)"
    pole = B19.shared("RACE_BannerPole", lambda mb: R.banner_pole(mb, 1.8))
    po = bpy.data.objects.new(f"{name}_BannerPole", pole)
    col.objects.link(po)
    po.parent = root
    po.location = (x, y + 0.04, top + 0.05)
    return b, po


# --------------------------------------------------------------------------- casas de la raza
def build_casa_kit(i, key, col, pcol, st, g):
    m = bpy.data.objects[f"MARKER_Bld_CasaRaza_{i:02d}"]
    name = f"CasaRaza_{i:02d}"
    rng = random.Random(B.rng_for(name, SEED))
    lantern_rng = random.Random(B.rng_for(name + "t", SEED))

    def extras(root, objs, rep, k):
        ex = {}
        if k == "R04":
            ex.update(r04_turret(root, objs, rep, 2.3, True, lantern_rng))
        return ex
    root, objs, rep = kit_race(name, key, m, 3, lambda f: BUDGET["casa_raza"] - 160, col, pcol, rng, g,
                               plan_edit=R.solid_above_door, extras=extras, max_rise=9.5)
    W, D = rep["footprint"]
    ds = R.RACE_PRESETS[key]["door_scale"]
    dx = rep["door_local"][0]
    eave = rep["eave_height_m"]
    door_top = min(2.35 * ds, K.FLOOR_H - 0.25) + 0.24
    top = eave - 0.35
    length = round(min(5.0, top - door_top - 0.45), 2)
    ban, bpole = add_facade_banner(name, key, root, col, dx, D / 2 + 0.3, top, length)
    fpole, flag = add_flag(name, key, root, col, flag_top(rep, key))
    spawn = empty(f"MARKER_RaceSpawn_{i:02d}", col, root, (dx, D / 2 + 3.0, 0.0), race_preset=key, race_slot=i,
                  door_of=name, note="aparicion de los personajes de la raza, delante de la puerta (+Y hacia fuera)")
    colo = B19.box_collider(f"{name}-colonly", col, root, [((-W / 2, -D / 2, 0), (W / 2, D / 2, eave))])
    root["race_preset"] = key
    extra_t = tris(ban) + tris(flag) + tris(bpole) + tris(fpole)
    B18._finish_kit(name, root, objs, rep, st, colo, extra={
        "banner": ban.name, "banner_size_m": [1.8, length], "flag": flag.name, "spawn_marker": spawn.name,
        "race": rep["race"], "banner_flag_tris": extra_t})
    s = st[name]
    s["tris"]["total_with_extras"] = s["tris"]["total_body_roof"] + extra_t
    s["budget"] = BUDGET["casa_raza"]
    s["ok"] = s["tris"]["total_with_extras"] <= BUDGET["casa_raza"]
    s["iso_blocks"] = B18.iso_check(root, [objs["Body"], objs["Roof"]])
    s["door_scale"] = ds
    return root


class YURT:
    MAIN = (-3.0, 0.6, 6.8)          # (cx, cy, r) yurta grande con la puerta a +Y
    ANNEX = ((6.6, -3.4, 3.0), (7.4, 4.6, 2.2))
    WALL_H = 3.6
    PITCH = 28.0


def build_casa_yurt(i, key, col, pcol, st):
    m = bpy.data.objects[f"MARKER_Bld_CasaRaza_{i:02d}"]
    name = f"CasaRaza_{i:02d}"
    root = B16.new_root(name, m, col, "Casa de la Raza (yurtas)")
    root["race_preset"] = key
    rng = random.Random(B.rng_for(name, SEED))
    p = R.RACE_PRESETS[key]
    ds = p["door_scale"]
    Y = YURT
    meshes = {}
    for tag, det, n in (("", 0, 20), ("_LOD1", 1, 12)):
        body, roof = K.MB(), K.MB()
        cx, cy, r = Y.MAIN
        zc, dloc = R.yurt(body, roof, cx, cy, r, Y.WALL_H, Y.PITCH, random.Random(rng.random()), door=(math.pi / 2, ds),
                          n=n, detail=det, patches=3)
        crowns = [(cx, cy, zc)]
        for k, (ax, ay, ar) in enumerate(Y.ANNEX):
            z2, _ = R.yurt(body, roof, ax, ay, ar, Y.WALL_H - 0.6, Y.PITCH + 4, random.Random(rng.random()),
                           door=(math.pi / 2, ds) if k == 1 else None, n=max(8, n - 6), detail=det, patches=1)
            crowns.append((ax, ay, z2))
        if det == 0:
            # pasarela cubierta entre la yurta grande y el anexo 1, y vigas de repuesto apoyadas
            body.box((3.2, -3.0, 0.0), (4.2, -1.6, 0.18), K.M_GRAY, skip=("z-",))
            for xx in (3.3, 4.1):
                body.rod((xx, -2.3, 0.18), (xx, -2.3, 2.8), 0.08, R.WOOD_LIGHT)
            body.box((3.0, -3.0, 2.8), (4.4, -1.6, 2.95), R.HIDE)
            for k in range(3):
                body.rod((-9.0 + k * 0.5, 4.5, 0.05), (-8.6 + k * 0.5, 5.6, 1.8), 0.07, R.WOOD_LIGHT if k else WOOD_REPAIR)
        if dloc is not None and not tag:
            meshes["door"] = dloc
            meshes["crowns"] = crowns
        meshes[tag] = (body, roof)
    body = B16.mesh_obj(meshes[""][0], f"{name}_Body", col, root)
    roof = B16.mesh_obj(meshes[""][1], f"{name}_Roof", col, root)
    b1 = B16.mesh_obj(meshes["_LOD1"][0], f"{name}_Body_LOD1", col, root)
    r1 = B16.mesh_obj(meshes["_LOD1"][1], f"{name}_Roof_LOD1", col, root)
    for o in (b1, r1):
        o.hide_render = True
        o.hide_set(True)
    mass = []
    cx, cy, r = Y.MAIN
    for (x, y, rr), (_, _, zc), wh in zip([Y.MAIN] + list(Y.ANNEX), meshes["crowns"], [Y.WALL_H] + [Y.WALL_H - 0.6] * 2):
        mass += [("cyl", x, y, rr, 0.0, wh, 10), ("cone", x, y, rr + 0.45, wh - 0.12, zc + 0.5, 10)]
    o2, n2, _, note = LU.massing_spec(f"{name}_Body_LOD2", mass, [body, roof], col, root)
    dl = meshes["door"]
    dm = B16.door_marker(name, col, root, dl)
    iv = B16.interior(name, col, root, r * 0.7, r * 0.7, Y.WALL_H, {})
    iv.location = (cx, cy, 0.0)
    # estandarte en mastil exento junto a la puerta y bandera sobre la corona
    mast = B19.shared("RACE_BannerMast", lambda mb: R.banner_mast(mb, 6.5, 1.2))
    mo = bpy.data.objects.new(f"{name}_BannerMast", mast)
    col.objects.link(mo)
    mo.parent = root
    mo.location = (cx + 2.6, cy + r + 0.3, 0.0)
    ban = bpy.data.objects.new(f"{name}_Banner", banner_obj(name, key, 4.2))
    col.objects.link(ban)
    ban.parent = root
    ban.location = (cx + 2.6, cy + r + 0.38, 6.1)
    ban["race_preset"] = key
    ban["swap_texture"] = f"MAT_Banner_{key} (UV 0..1)"
    crx, cry, crz = meshes["crowns"][0]
    fpole, flag = add_flag(name, key, root, col, (crx, cry, crz + 0.7))
    spawn = empty(f"MARKER_RaceSpawn_{i:02d}", col, root, (dl[0], dl[1] + 2.6, 0.0), race_preset=key, race_slot=i,
                  door_of=name, note="aparicion de los personajes de la raza, delante de la puerta (+Y hacia fuera)")
    boxes = [((x - rr * 0.85, y - rr * 0.85, 0), (x + rr * 0.85, y + rr * 0.85, wh))
             for (x, y, rr), wh in zip([Y.MAIN] + list(Y.ANNEX), [Y.WALL_H] + [Y.WALL_H - 0.6] * 2)]
    colo = B19.box_collider(f"{name}-colonly", col, root, boxes)
    lods = {"LOD1": tris(b1) + tris(r1), "LOD2": n2, "LOD2_material": note}
    extra_t = tris(ban) + tris(flag) + tris(mo) + tris(fpole)
    t = {"Body": tris(body), "Roof": tris(roof)}
    t["total_body_roof"] = t["Body"] + t["Roof"]
    t["total_with_extras"] = t["total_body_roof"] + extra_t
    st[name] = {"marker": m.name, "tris": t, "budget": BUDGET["casa_raza"], "ok": t["total_with_extras"] <= BUDGET["casa_raza"],
                "lods": lods, "roof": "yurt", "door_scale": ds, "door_local": [round(c, 2) for c in dl],
                "yurts": {"main": {"center": list(Y.MAIN[:2]), "r": Y.MAIN[2], "wall_h": Y.WALL_H, "crown_z": round(crz, 2)},
                          "annexes": [{"center": [a[0], a[1]], "r": a[2]} for a in Y.ANNEX]},
                "banner": ban.name, "banner_size_m": [1.8, 4.2], "flag": flag.name, "spawn_marker": spawn.name,
                "door_marker": dm.name, "interior": iv.name, "collision": colo.name,
                "iso_blocks": B18.iso_check(root, [body, roof]),
                "footprint_check": B16.check_footprint(body, 10.0, 8.0),
                "footprint_ground_check": B18.ground_footprint(body, 10.0, 8.0)}
    return root


WOOD_REPAIR = "MAT_Wood_Dark"     # viga de repuesto (otro tono) junto a la yurta


# --------------------------------------------------------------------------- casas y plazuelas
def build_houses(b, key, col, pcol, st, g):
    names = sorted(o.name for o in bpy.data.objects if o.name.startswith(f"MARKER_Bld_RAZ_B{b:02d}_Casa_"))
    roots = []
    for mn in names:
        name = mn.replace("MARKER_Bld_", "")
        rng = random.Random(B.rng_for(name, SEED))
        pisos = rng.choice((2, 2, 3))
        root, objs, rep = kit_race(name, key, bpy.data.objects[mn], pisos,
                                   lambda f: BUDGET["house_3f"] if f >= 3 else BUDGET["house"], col, pcol, rng, g,
                                   extras=house_extras(rng))
        W, D = rep["footprint"]
        colo = B19.box_collider(f"{name}-colonly", col, root, [((-W / 2, -D / 2, 0), (W / 2, D / 2, rep["eave_height_m"]))])
        root["race_preset"] = key
        B18._finish_kit(name, root, objs, rep, st, colo, extra={"race": rep["race"]})
        s = st[name]
        s["tris"]["total_with_extras"] = rep["tris_total"]
        s["budget"] = BUDGET["house_3f"] if rep["floors"] >= 3 else BUDGET["house"]
        s["ok"] = rep["tris_total"] <= s["budget"]
        s["door_scale"] = R.RACE_PRESETS[key]["door_scale"]
        roots.append(root)
    return roots


def terrain_material(x, y):
    sc = bpy.context.scene
    dg = bpy.context.evaluated_depsgraph_get()
    hit, loc, nrm, idx, ob, _ = sc.ray_cast(dg, Vector((x, y, 200.0)), Vector((0, 0, -1)))
    while hit and not ob.name.startswith("TRN_City_Chunk") or (hit and ob.name.endswith(("-colonly", "_LOD1", "_LOD2"))):
        hit, loc, nrm, idx, ob, _ = sc.ray_cast(dg, loc - Vector((0, 0, 0.01)), Vector((0, 0, -1)))
    if not hit:
        return None
    me = ob.data
    if idx < len(me.polygons) and me.polygons[idx].material_index < len(me.materials):
        return me.materials[me.polygons[idx].material_index].name
    return None


def build_plazuela(i, key, col, pcol, st, g):
    mk = bpy.data.objects[f"MARKER_Prop_Plazuela_{i:02d}"]
    c = mk.matrix_world.translation
    kind = mk["type"]
    name = f"Plazuela_{i:02d}"
    root = bpy.data.objects.new(name, None)
    col.objects.link(root)
    root.location = (c.x, c.y, g(c.x, c.y))
    root["race_preset"] = key
    root["type"] = kind
    mats = {terrain_material(c.x + rr * math.cos(a), c.y + rr * math.sin(a)) for rr in (0.0, 3.0, 4.6)
            for a in (0, 1.6, 3.1, 4.7)}
    paved = any(m and ("Cobble" in m or "Slab" in m) for m in mats)
    items = []
    disc = None
    if not paved:
        dmb = K.MB()
        R.paving_disc(dmb, g, c.x, c.y)
        disc = B19.mb_object(dmb, f"{name}_Paving", col, root)
        disc.matrix_world = Matrix.Identity(4)
    rng = random.Random(B.rng_for(name, SEED))
    if kind == "fountain":
        me = B19.shared("PLAZUELA_Fountain", R.fountain_small)
    else:
        me = B19.shared(f"PLAZUELA_OldTree_{i:02d}", lambda mb: R.old_tree(mb, rng))
    centre = bpy.data.objects.new(f"{name}_{'Fountain' if kind == 'fountain' else 'OldTree'}", me)
    col.objects.link(centre)
    centre.parent = root
    centre.matrix_world = Matrix.Translation((c.x, c.y, g(c.x, c.y))) @ Matrix.Rotation(rng.uniform(0, 6.28), 4, "Z")
    items.append(centre)
    bm = B19.shared("PLAZUELA_Bench", R.bench)
    pe = bpy.data.objects.new(f"{name}_Props", None)
    pcol.objects.link(pe)
    pe.parent = root
    a0 = rng.uniform(0, math.pi / 2)
    benches = []
    for k in range(4):
        a = a0 + math.pi / 2 * k + math.pi / 4
        x, y = c.x + 3.7 * math.cos(a), c.y + 3.7 * math.sin(a)
        o = B19.prop(f"{name}_Prop_Bench_{k + 1:02d}", bm, pcol, pe,
                     Matrix.Translation((x, y, g(x, y))) @ Matrix.Rotation(a + math.pi / 2, 4, "Z"))
        benches.append(o)
    rr = 1.7 if kind == "fountain" else 1.55
    colo = B19.box_collider(f"{name}-colonly", col, root, [((-rr, -rr, -0.4), (rr, rr, 0.6 if kind == "fountain" else 0.5))])
    colo.matrix_world = Matrix.Translation((c.x, c.y, g(c.x, c.y)))
    if kind != "fountain":
        tb = B19.box_collider(f"{name}_Trunk-colonly", col, root, [((-0.6, -0.6, 0), (0.6, 0.6, 4.0))])
        tb.matrix_world = Matrix.Translation((c.x, c.y, g(c.x, c.y)))
    st[name] = {"marker": mk.name, "type": kind, "diameter_m": 10.0, "terrain_materials": sorted(m for m in mats if m),
                "paving_added": disc is not None, "paving_tris": tris(disc) if disc else 0,
                "centre_piece": centre.name, "centre_tris": tris(centre), "benches": len(benches),
                "bench_tris": tris(benches[0]), "bench_radius_m": 3.7}
    return root


def barrio_colors(roots):
    """Color medio (sRGB) de muros y tejados de un barrio: lo que distingue los barrios desde CAM_Iso."""
    def srgb(c):
        return c * 12.92 if c <= 0.0031308 else 1.055 * c ** (1 / 2.4) - 0.055
    out = {}
    for part in ("Body", "Roof"):
        objs = [o for r in roots for o in r.children if o.name.endswith(f"_{part}") and o.type == "MESH"]
        lin = LU.average_color(objs)
        s = tuple(srgb(c) for c in lin)
        sat, hue = R.saturation_hue(s)
        out[part] = {"hex": "#%02X%02X%02X" % tuple(int(round(v * 255)) for v in s), "saturation": round(sat, 3),
                     "hue": round(hue, 1)}
    return out


def main():
    n = int(sys.argv[sys.argv.index("--") + 1]) if "--" in sys.argv else R.N_RAZAS
    st = {"N_RAZAS": n, "budgets": BUDGET}
    bpy.ops.wm.open_mainfile(filepath=SRC)
    save()
    st["saved_before"] = os.path.relpath(OUT, REPO)
    casas = sorted(o.name for o in bpy.data.objects if o.name.startswith("MARKER_Bld_CasaRaza_"))
    if n > len(casas):
        raise SystemExit(f"N_RAZAS = {n} > {len(casas)} parcelas MARKER_Bld_CasaRaza_*")
    keys = list(R.RACE_PRESETS)[:n]
    B.ensure_materials()
    O.ensure_materials()
    st["materials"] = R.ensure_materials(keys)
    col = bpy.data.collections["BLD_RAZAS"]
    pcol = bpy.data.collections["BLD_PROPS"]
    for o in list(col.all_objects):
        bpy.data.objects.remove(o)
    g = B18.ground_fn()
    roots_all = []
    st["barrios"] = {}
    for i, key in enumerate(keys, 1):
        bst = {}
        if R.RACE_PRESETS[key]["roof"] == "yurt":
            casa = build_casa_yurt(i, key, col, pcol, bst)
        else:
            casa = build_casa_kit(i, key, col, pcol, bst, g)
        houses = build_houses(i, key, col, pcol, bst, g)
        plz = build_plazuela(i, key, col, pcol, bst, g)
        roots = [casa] + houses
        for r in roots:
            W, D = float(r.get("footprint_w", 20.0)), float(r.get("footprint_d", 16.0))
            bst[r.name]["ground_gap_m"] = ground_gap(r, W, D, g)
        n_h = len(houses)
        p = R.RACE_PRESETS[key]
        st["barrios"][f"B{i:02d}"] = {
            "preset": key, "material": p["material"], "roof": p["roof"], "pitch": p["pitch"], "door_scale": p["door_scale"],
            "reference": p["ref"], "banner_color": p["color"], "symbol": p["symbol"],
            "houses_built": n_h, "houses_requested": list(REQUESTED_HOUSES),
            "houses_missing_parcels": max(0, REQUESTED_HOUSES[0] - n_h),
            "colors": barrio_colors(roots), "buildings": bst}
        roots_all += roots + [plz]
    st["parcels_unused_casas"] = casas[n:]
    for o in bpy.data.objects:
        if o.name.endswith(("_LOD1", "_LOD2")):
            o.hide_render = True
            o.hide_set(True)
    bpy.context.view_layer.update()
    import build_stage17 as B17
    with open(os.path.join(REPO, "docs", "reports", "stage15_faro.json")) as fh:
        tgt = Vector(json.load(fh)["visibility"]["target"])
    B17.faro_visibility(st, tgt)
    import stage11_godot as G
    objs = []
    for r in roots_all:
        objs += [r] + list(r.children_recursive)
    path = os.path.join(REPO, "export", "godot", "concordia_razas.glb")
    size = G.export_glb(list(dict.fromkeys(objs)), path)
    st["export"] = {"file": os.path.relpath(path, REPO), "mb": round(size / 2 ** 20, 2), **G.glb_info(path)}
    for o in bpy.data.objects:
        if o.name.endswith(("_LOD1", "_LOD2")):
            o.hide_set(True)
    save()
    with open(REPORT, "w") as fh:
        json.dump(st, fh, indent=1, ensure_ascii=False, default=str)
    print("saved:", OUT)
    for bk, bv in st["barrios"].items():
        print(bk, bv["preset"], bv["roof"], "casas", bv["houses_built"], json.dumps(bv["colors"]))
        for k, v in bv["buildings"].items():
            if k.startswith("Plazuela"):
                print("   ", k, v["type"], "paving" if v["paving_added"] else "ya pavimentada", v["centre_tris"], v["terrain_materials"])
                continue
            t = v["tris"]
            print("   ", k, v.get("floors"), t.get("total_with_extras"), v.get("budget"), v.get("ok"),
                  "tier", (v.get("race") or {}).get("tier"), "gap", v.get("ground_gap_m"),
                  "fp", (v.get("footprint_ground_check") or {}).get("over_x_m"), (v.get("footprint_ground_check") or {}).get("over_y_m"),
                  "iso", (v.get("iso_rule") or {}).get("history") if isinstance(v.get("iso_rule"), dict) else v.get("iso_blocks"))
    print(json.dumps({k: (v["axis_pct"], v.get("best_lane_pct")) for k, v in st["faro_visibility"].items()}, ensure_ascii=False))
    print(json.dumps(st["export"], default=str)[:300])
    print(json.dumps(st["materials"], ensure_ascii=False, default=str)[:1500])
    _ = (bmesh, P13)


if __name__ == "__main__":
    main()
