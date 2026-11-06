"""
CONCORDIA - Etapa 20 (E7): distrito de las Clases. concordia_v19.blend -> concordia_v20.blend (guardada antes)
+ export/godot/concordia_clases.glb + docs/reports/stage20_clases.json + docs/captures/stage20_presets.png

Uso: python build_stage20.py [N_CLASES]   (por defecto stage20_clases.N_CLASES = 8)
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
import stage16_landmarks as L  # noqa: E402
import stage19_oficios as O  # noqa: E402
import stage20_clases as CL  # noqa: E402
import build_stage16 as B16  # noqa: E402
import build_stage18 as B18  # noqa: E402
import build_stage19 as B19  # noqa: E402
import lod_utils as LU  # noqa: E402

REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
SRC = os.path.join(REPO, "blender", f"{C.BLEND_BASENAME}_v19.blend")
OUT = os.path.join(REPO, "blender", f"{C.BLEND_BASENAME}_v20.blend")
REPORT = os.path.join(REPO, "docs", "reports", "stage20_clases.json")
SEED = 2001
BUDGET = {"salon": 5000, "dummy": 600, "reposicion": 5000}
tris = B18.tris


def save():
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)


def empty(name, col, parent, loc, **props):
    e = bpy.data.objects.new(name, None)
    e.empty_display_type = "PLAIN_AXES"
    e.empty_display_size = 0.3
    col.objects.link(e)
    e.parent = parent
    e.location = loc
    for k, v in props.items():
        e[k] = v
    return e


def banner_mesh(key):
    name = f"BANNER_{key}"
    me = bpy.data.meshes.get(name)
    if me is None:
        bm = CL.banner()
        me = bpy.data.meshes.new(name)
        bm.to_mesh(me)
        bm.free()
        me.materials.append(bpy.data.materials[f"MAT_Banner_{key}"])
    return me


def pole_mesh():
    return B19.shared("BANNER_Pole", lambda mb: (mb.rod((-1.45, 0.0, 0.0), (1.45, 0.0, 0.0), 0.04, K.M_IRON),
                                                 [O.bulb(mb, s * 1.5, 0.0, 0.0, 0.07, "MAT_Bronze_Aged") for s in (-1, 1)],
                                                 [mb.rod((s * 1.2, 0.0, 0.0), (s * 1.2, -0.45, 0.25), 0.025, K.M_IRON) for s in (-1, 1)]))


def build_salon(i, key, col, pcol, st):
    m = bpy.data.objects[f"MARKER_Bld_SalonClase_{i:02d}"]
    name = f"SalonClase_{i:02d}"
    root = B16.new_root(name, m, col, m["label"])
    root["class_preset"] = key
    root["class_index"] = i
    rng = random.Random(B.rng_for(name, SEED))
    bmb, rmb, info, mass, ridge = CL.salon_meshes(rng, key)
    body = B16.mesh_obj(bmb, f"{name}_Body", col, root)
    roof = B16.mesh_obj(rmb, f"{name}_Roof", col, root)
    lods = {"LOD1": P13.lods(body, col, (("LOD1", 0.5),))["LOD1"] + P13.lods(roof, col, (("LOD1", 0.5),))["LOD1"]}
    o2, n2, _, note = LU.massing_spec(f"{name}_Body_LOD2", mass + [("gable_y", -CL.SAL.D / 2 - 0.4, CL.SAL.YF + 0.25, 9.5, 6.75,
                                                                     ridge)], [body, roof], col, root)
    lods["LOD2"], lods["LOD2_material"] = n2, note
    dm = B16.door_marker(name, col, root, info["door"])
    (cx, cy), (sx, sy, sz) = info["interior"]
    iv = B16.interior(name, col, root, sx / 2, sy / 2, sz, {})
    iv.location = (cx, cy, 0.0)
    # estandartes (objetos aparte: textura por clase) y barras
    S = CL.SAL
    bm_ = banner_mesh(key)
    pole = pole_mesh()
    banners = []
    for tag, loc, rz in (("Front", (0.0, S.YF + 0.14, info["banner_front_top"]), 0.0),
                         ("Back", (0.0, -S.D / 2 - 0.08, info["banner_back_top"]), math.pi)):
        b = bpy.data.objects.new(f"{name}_Banner_{tag}", bm_)
        col.objects.link(b)
        b.parent = root
        b.location = loc
        b.rotation_euler = (0, 0, rz)
        b["class_preset"] = key
        b["swap_texture"] = f"MAT_Banner_{key} (UV 0..1)"
        p = bpy.data.objects.new(f"{name}_BannerPole_{tag}", pole)
        col.objects.link(p)
        p.parent = root
        p.location = (loc[0], loc[1] + (0.04 if rz == 0 else -0.04), loc[2] + 0.05)
        p.rotation_euler = (0, 0, rz)
        banners.append(b)
    # slots de props de clase y 2 props del preset
    pe = B19.props_empty(root, pcol)
    slots = []
    for k, (x, y) in enumerate(S.SLOTS, 1):
        slots.append(empty(f"MARKER_ClassProp_Slot_{i:02d}_{k:02d}", col, root, (x, y, 0.85), slot=k, salon=name,
                           class_preset=key, note="soporte para un objeto de clase (libros, armas, simbolos)"))
    props = []
    for k, kind in enumerate(CL.CLASS_PRESETS[key]["props"]):
        me = B19.shared(f"CLASSPROP_{kind}", lambda mb, kind=kind: CL.class_prop(mb, kind))
        o = bpy.data.objects.new(f"{name}_Prop_{kind}", me)
        pcol.objects.link(o)
        o.parent = pe
        o.matrix_world = root.matrix_world @ Matrix.Translation(slots[k].location)
        o["slot"] = slots[k].name
        props.append(o)
    colo = B19.box_collider(f"{name}-colonly", col, root, [((-9, -7, 0), (9, S.YP, S.H)), ((-9, S.YP, 0), (9, S.YF, 0.45))] +
                            [((x - 0.35, S.YF - 0.85, 0), (x + 0.35, S.YF - 0.15, S.H)) for x in S.COLS])
    t = {"Body": tris(body), "Roof": tris(roof), "banners": sum(tris(b) for b in banners), "props": sum(tris(o) for o in props)}
    t["total"] = t["Body"] + t["Roof"] + t["banners"] + 2 * tris(bpy.data.objects[f"{name}_BannerPole_Front"])
    st.setdefault("salones", {})[name] = {
        "preset": key, "marker": m.name, "tris": t, "budget": BUDGET["salon"], "ok": t["total"] <= BUDGET["salon"],
        "lods": lods, "ridge_m": info["ridge_m"], "finial": CL.CLASS_PRESETS[key]["finial"],
        "banner_color": CL.CLASS_PRESETS[key]["color"], "props": [o.name for o in props], "slots": [s.name for s in slots],
        "door_marker": dm.name, "collision": colo.name, "iso_blocks": B18.iso_check(root, [body, roof]),
        "footprint_check": B16.check_footprint(body, 9.0, 7.0)}
    return root


def build_plaza(col, pcol, st):
    g = B18.ground_fn()
    root = bpy.data.objects.new("PlazaArmas", None)
    col.objects.link(root)
    root["note"] = "props de la Plaza de las Armas (suelo ya en el terreno)"
    dmesh = {v: B19.shared(f"DUMMY_Straw_{v}", lambda mb, v=v: CL.dummy_straw(mb, v)) for v in "ABC"}
    tmesh = B19.shared("PROP_Target", O.target)
    pmesh = B19.shared("PROP_TestPost", CL.test_post)
    dummies, targets, posts = [], [], []
    k = 0
    for z in (1, 2, 4, 5):
        mk = bpy.data.objects[f"MARKER_TrainingZone_{z:02d}"]
        c = mk.matrix_world.translation
        for j, dx in enumerate((-3.5, 0.0, 3.5)):
            k += 1
            x, y = c.x + dx, c.y + (1.5 if j % 2 else -1.5)
            v = "ABC"[(k - 1) % 3]
            o = bpy.data.objects.new(f"DUMMY_Straw_{k:02d}", dmesh[v])
            col.objects.link(o)
            o.parent = root
            face = math.atan2(-y, 0.0) - math.pi / 2          # que miren al eje de la avenida
            o.matrix_world = Matrix.Translation((x, y, g(x, y))) @ Matrix.Rotation(face, 4, "Z")
            o["variant"] = f"DUMMY_Straw_{v}"
            o["static"] = True
            empty(f"MARKER_DamageNumber_{k:02d}", col, o, (0.0, 0.0, 1.45), purpose="numero de dano (pecho del maniqui)")
            dummies.append(o)
    k = 0
    for z in (3, 6):
        mk = bpy.data.objects[f"MARKER_TrainingZone_{z:02d}"]
        c = mk.matrix_world.translation
        for dy in (-6.0, -3.0, 0.0, 3.0, 6.0):
            k += 1
            x, y = c.x - 4.0, c.y + dy
            o = bpy.data.objects.new(f"PlazaArmas_Target_{k:02d}", tmesh)
            col.objects.link(o)
            o.parent = root
            o.matrix_world = Matrix.Translation((x, y, g(x, y))) @ Matrix.Rotation(-math.pi / 2, 4, "Z")
            targets.append(o)
    k = 0
    for x in (-110.0, -118.0, -126.0, -134.0):
        for y in (-6.5, 6.5):
            k += 1
            o = bpy.data.objects.new(f"PlazaArmas_TestPost_{k:02d}", pmesh)
            col.objects.link(o)
            o.parent = root
            o.matrix_world = Matrix.Translation((x, y, g(x, y)))
            posts.append(o)
    doors = [o.matrix_world.translation for o in bpy.data.objects if o.name.startswith("MARKER_SalonClase_") and
             o.name.endswith("_Door")]

    def gap(x, y):
        if (x < -142.0 or x > -105.0) and abs(y) < 6.5:
            return True
        return any(math.hypot(x - d.x, y - d.y) < 4.6 for d in doors)
    fm = K.MB()
    n_posts = CL.fence(fm, [(-143.5, -25.0), (-103.5, -25.0), (-103.5, 25.0), (-143.5, 25.0)], g, gap)
    fence = B19.mb_object(fm, "PlazaArmas_Fence", col, root)
    fence.matrix_world = Matrix.Identity(4)
    st["plaza"] = {"dummies": len(dummies), "dummy_variants_tris": {v: sum(len(p.vertices) - 2 for p in me.polygons)
                                                                     for v, me in dmesh.items()},
                   "dummy_budget": BUDGET["dummy"], "targets": len(targets), "test_posts": len(posts),
                   "fence_posts": n_posts, "fence_tris": tris(fence), "damage_markers": len(dummies),
                   "layout": "maniquies en las zonas 1, 2, 4 y 5 (3 por zona); blancos en las zonas 3 y 6 (5 por zona, "
                             "mirando al centro); postes a los lados de la avenida; valla con huecos en la avenida y "
                             "delante de las puertas de los salones 01 y 02"}
    return root


def build_reposicion(col, pcol, st):
    name = "CasaReposicion"
    root, objs, rep = B19.kit(name, 2, col, pcol, tipo_techo="gable", estilo="timber", module_w=4.0,
                              opts={"no_buttress": True, "side_detail": {"back": 1, "left": 1, "right": 1}, "roof_seg": 4.5})
    W, D = rep["footprint"]
    dx = rep["door_local"][0]
    pe = B19.props_empty(root, pcol)
    rack = B19.shared("PROP_ArmorRack", CL.armor_rack)
    swb = B19.shared("PROP_SwordBoard", CL.sword_board)
    boots = B19.shared("PROP_BootCrate", lambda mb: CL.boot_crate(mb, False))
    cloaks = B19.shared("PROP_CloakCrate", lambda mb: CL.boot_crate(mb, True))
    mw = root.matrix_world
    items = []
    xs = [x for x in (-10.0, -7.0, 7.0, 10.0) if abs(x - dx) > 2.0]
    for k, x in enumerate(xs, 1):
        items.append(B19.prop(f"{name}_Prop_ArmorRack_{k:02d}", rack, pcol, pe, mw @ Matrix.Translation((x, D / 2 + 0.55, 0))))
    sx = dx + 3.2 if dx < 0 else dx - 3.2
    items.append(B19.prop(f"{name}_Prop_SwordBoard_01", swb, pcol, pe, mw @ Matrix.Translation((sx, D / 2 + 0.02, 1.0))))
    for k, (x, me) in enumerate(((dx - 1.6, boots), (dx + 1.6, cloaks), (dx + 2.5, boots)), 1):
        items.append(B19.prop(f"{name}_Prop_Crate_{k:02d}", me, pcol, pe, mw @ Matrix.Translation((x, D / 2 + 0.5, 0))))
    # lado que ve la camara (-X): otra percha, espadas y capas
    side = Matrix.Translation((-W / 2, 0, 0)) @ Matrix.Rotation(math.pi / 2, 4, "Z")
    items.append(B19.prop(f"{name}_Prop_ArmorRack_Side", rack, pcol, pe, mw @ side @ Matrix.Translation((-2.0, 0.55, 0))))
    items.append(B19.prop(f"{name}_Prop_SwordBoard_Side", swb, pcol, pe, mw @ side @ Matrix.Translation((1.5, 0.02, 1.0))))
    items.append(B19.prop(f"{name}_Prop_Crate_Side", cloaks, pcol, pe, mw @ side @ Matrix.Translation((3.6, 0.5, 0))))
    sign = next((c for c in root.children_recursive if "SIGN_Hanging" in c.name), None)
    if sign is not None:
        sign.data = B19.shared("SIGN_Hanging_Patch", CL.sign_patch)
        sign.name = f"{name}_Prop_SIGN_Hanging_Patch"
    colo = B19.box_collider(f"{name}-colonly", col, root, [((-W / 2, -D / 2, 0), (W / 2, D / 2, rep["eave_height_m"]))])
    B19.finish_kit(name, root, objs, rep, st, colo, extra={"props_tris": sum(tris(o) for o in items),
                                                         "props": [o.name for o in items]})
    st[name]["budget"] = BUDGET["reposicion"]
    st[name]["ok"] = st[name]["tris"]["total_with_extras"] <= BUDGET["reposicion"]
    return root


def presets_sheet(keys):
    from PIL import Image, ImageDraw, ImageFont
    f = ImageFont.truetype("DejaVuSans-Bold.ttf", 22)
    fs = ImageFont.truetype("DejaVuSans.ttf", 17)
    W = 240
    im = Image.new("RGB", (W * len(keys), 700), (28, 28, 28))
    d = ImageDraw.Draw(im)
    for i, k in enumerate(keys):
        p = CL.CLASS_PRESETS[k]
        tex = Image.open(os.path.join(REPO, "textures", "concordia", "MAT_Banner",
                                      f"concordia_banner_{k.lower()}_albedo.png")).resize((180, 360))
        im.paste(tex, (i * W + 30, 50))
        d.text((i * W + 30, 12), k, fill=(255, 255, 255), font=f)
        for j, line in enumerate((f"color {p['color']} (s {CL.preset_saturation(k):.2f})", f"remate: {p['finial']}",
                                  f"props: {p['props'][0]}", f"       {p['props'][1]}", f"emblema: {p['emblem']}")):
            d.text((i * W + 12, 430 + 26 * j), line, fill=(220, 220, 220), font=fs)
    path = os.path.join(REPO, "docs", "captures", "stage20_presets.png")
    im.save(path)
    return path


def main():
    n = int(sys.argv[sys.argv.index("--") + 1]) if "--" in sys.argv else CL.N_CLASES
    st = {"N_CLASES": n}
    bpy.ops.wm.open_mainfile(filepath=SRC)
    save()
    st["saved_before"] = os.path.relpath(OUT, REPO)
    parcels = sorted(o.name for o in bpy.data.objects if o.name.startswith("MARKER_Bld_SalonClase_"))
    if n > len(parcels):
        raise SystemExit(f"N_CLASES = {n} > {len(parcels)} parcelas MARKER_Bld_SalonClase_*")
    keys = list(CL.CLASS_PRESETS)[:n]
    B.ensure_materials()
    O.ensure_materials()
    st["materials"] = CL.ensure_materials(keys)
    col = bpy.data.collections["BLD_CLASES"]
    pcol = bpy.data.collections["BLD_PROPS"]
    for o in list(col.all_objects):
        bpy.data.objects.remove(o)
    roots = [build_salon(i, k, col, pcol, st) for i, k in enumerate(keys, 1)]
    st["parcels_unused"] = parcels[n:]
    roots.append(build_plaza(col, pcol, st))
    roots.append(build_reposicion(col, pcol, st))
    for k in range(1, 13):
        name = f"CLA_Casa_{k:02d}"
        rng = random.Random(B.rng_for(name, SEED))
        pisos = rng.choice((2, 3))
        if k in (1, 2):
            pisos = 2                       # junto a la plaza, en la avenida Oeste: a 3 plantas tapaban el Faro
        root, objs, rep = B19.kit(name, pisos, col, pcol, tipo_techo=rng.choice(("gable", "gable_front", "hip")),
                                  estilo=rng.choice(("stone", "stone", "timber")),
                                  opts={"no_buttress": True, "side_detail": {"back": 1}, "roof_seg": 3.5})
        W, D = rep["footprint"]
        colo = B19.box_collider(f"{name}-colonly", col, root, [((-W / 2, -D / 2, 0), (W / 2, D / 2, rep["eave_height_m"]))])
        B19.finish_kit(name, root, objs, rep, st.setdefault("casas", {}), colo)
        roots.append(root)
    st["presets_sheet"] = os.path.relpath(presets_sheet(keys), REPO)
    st["presets"] = {k: CL.CLASS_PRESETS[k] for k in keys}
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
    for r in roots:
        objs += [r] + list(r.children_recursive)
    path = os.path.join(REPO, "export", "godot", "concordia_clases.glb")
    size = G.export_glb(list(dict.fromkeys(objs)), path)
    st["export"] = {"file": os.path.relpath(path, REPO), "mb": round(size / 2 ** 20, 2), **G.glb_info(path)}
    for o in bpy.data.objects:
        if o.name.endswith(("_LOD1", "_LOD2")):
            o.hide_set(True)
    save()
    with open(REPORT, "w") as fh:
        json.dump(st, fh, indent=1, ensure_ascii=False, default=str)
    print("saved:", OUT)
    for k, v in st["salones"].items():
        print(k, v["preset"], v["tris"]["total"], v["ok"], v["iso_blocks"], v["footprint_check"]["over_y_m"], v["lods"]["LOD2"])
    print("plaza", json.dumps(st["plaza"])[:400])
    v = st["CasaReposicion"]
    print("reposicion", v["tris"], v["ok"], v["floors"], (v.get("iso_rule") or {}).get("history"), v["footprint_ground_check"])
    for k, v in st["casas"].items():
        print(k, v["floors"], v["tris"]["total_body_roof"], (v.get("iso_rule") or {}).get("history"))
    print(json.dumps({k: (v["axis_pct"], v.get("best_lane_pct")) for k, v in st["faro_visibility"].items()}, ensure_ascii=False))
    print(json.dumps(st["export"], default=str)[:300])
    print(json.dumps(st["materials"], ensure_ascii=False)[:600])
    _ = bmesh


if __name__ == "__main__":
    main()
