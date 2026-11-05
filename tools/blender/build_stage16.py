"""
CONCORDIA - Etapa 16: Santuario del Retorno (NO) y Salon de las Hazanas (SE).
concordia_v15.blend -> concordia_v16.blend (guardada antes de empezar)
+ export/godot/concordia_santuario.glb + export/godot/concordia_salon_hazanas.glb + docs/reports/stage16_landmarks.json

Ademas: se repite la visibilidad de la cima del Faro (ya hay dos edificios altos) y se mide cuanta calle/plaza tapan
estos dos edificios desde CAM_Iso.
"""

import json
import math
import os
import random
import sys

import bpy  # noqa: I001
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import concordia_const as C  # noqa: E402
import stage13_portal as P13  # noqa: E402
import stage16_landmarks as L  # noqa: E402

REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
SRC = os.path.join(REPO, "blender", f"{C.BLEND_BASENAME}_v15.blend")
OUT = os.path.join(REPO, "blender", f"{C.BLEND_BASENAME}_v16.blend")
REPORT = os.path.join(REPO, "docs", "reports", "stage16_landmarks.json")
BUDGET = {"SANTUARIO": 8000, "SALON_HAZANAS": 14000}


def save():
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)


def tris(o):
    return sum(len(p.vertices) - 2 for p in o.data.polygons)


def mesh_obj(mb, name, col, root):
    import concordia_buildings as B
    o = B.to_object(mb, name, col)
    mb.bm.free()
    o.parent = root
    B.box_uv(o)
    return o


def interior(name, col, root, hx, hy, h, extra):
    import bmesh
    me = bpy.data.meshes.new(f"{name}_InteriorVolume")
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co = Vector((v.co.x * 2 * hx, v.co.y * 2 * hy, (v.co.z + 0.5) * h))
    bm.to_mesh(me)
    bm.free()
    iv = bpy.data.objects.new(f"{name}_InteriorVolume", me)
    col.objects.link(iv)
    iv.parent = root
    iv.display_type = "WIRE"
    iv.hide_render = True
    iv["interior_size_m"] = [round(2 * hx, 2), round(2 * hy, 2), round(h, 2)]
    for k, v in extra.items():
        iv[k] = v
    return iv


def door_marker(name, col, root, loc):
    dm = bpy.data.objects.new(f"MARKER_{name}_Door", None)
    dm.empty_display_type = "SINGLE_ARROW"
    dm.empty_display_size = 1.0
    col.objects.link(dm)
    dm.parent = root
    dm.location = loc
    dm["door_of"] = name
    dm["axis"] = "+Y hacia fuera (hacia la plaza)"
    return dm


def new_root(name, marker, col, label):
    root = bpy.data.objects.new(name, None)
    col.objects.link(root)
    root.matrix_world = marker.matrix_world.copy()
    root["landmark"] = label
    root["marker"] = marker.name
    return root


def clear(prefixes):
    for o in [o for o in bpy.data.objects if o.name.startswith(prefixes)]:
        bpy.data.objects.remove(o)


def place_props(items, props_root, col):
    """items: (nombre, malla compartida, frame, (u, y, z), rot_extra)"""
    objs = []
    for name, me, fr, p, rz in items:
        o = bpy.data.objects.new(name, me)
        col.objects.link(o)
        o.parent = props_root
        rot = math.atan2(fr[1][0], fr[0][0])
        o.location = fr @ Vector(p)
        o.rotation_euler = (0, 0, rot + rz)
        objs.append(o)
    return objs


def check_footprint(o, hx, hy):
    """Extension de la malla (local) frente al footprint; la cubierta puede volar sobre el borde."""
    xs = [v.co.x for v in o.data.vertices]
    ys = [v.co.y for v in o.data.vertices]
    return {"x": [round(min(xs), 3), round(max(xs), 3)], "y": [round(min(ys), 3), round(max(ys), 3)],
            "over_x_m": round(max(0.0, max(xs) - hx, -hx - min(xs)), 3),
            "over_y_m": round(max(0.0, max(ys) - hy, -hy - min(ys)), 3)}


# ---------------------------------------------------------------------------
def build_santuario(col, pcol, st):
    import concordia_buildings as B
    clear(("SANTUARIO", "MARKER_Santuario_Door", "Santuario_InteriorVolume"))
    mk = bpy.data.objects["MARKER_Santuario"]
    root = new_root("SANTUARIO", mk, col, "Santuario del Retorno")
    rng = random.Random(B.rng_for("Santuario", L.SEED_SANT))
    body_mb, binfo = L.santuario_body(rng)
    body = mesh_obj(body_mb, "SANTUARIO_Body", col, root)
    roof_mb, rinfo = L.santuario_roof(rng)
    roof = mesh_obj(roof_mb, "SANTUARIO_Roof", col, root)
    lods = {"Body": P13.lods(body, col), "Roof": P13.lods(roof, col)}
    # pozo (modelo aparte, colocado provisionalmente en el centro de la nave)
    me = L._shared_mesh("SANTUARIO_Well", L.well, B.box_uv)
    wo = bpy.data.objects.new("SANTUARIO_Well", me)
    col.objects.link(wo)
    wo.parent = root
    wo["note"] = "modelo aparte para el interior; colocado provisionalmente en el centro de la nave"
    # props: farolillos de esquirla a los lados de la portada (sobre los contrafuertes centrales)
    pr = bpy.data.objects.new("SANTUARIO_Props", None)
    pcol.objects.link(pr)
    pr.parent = root
    lan = B.prop_mesh("LANTERN_Shard")
    fr = L.frame("+Y", L.S.X, L.S.Y)
    props = place_props([(f"SANTUARIO_Prop_LANTERN_Shard_{i:02d}", lan, fr, (u, L.S.BD, 3.3), 0.0)
                         for i, u in enumerate((-1.5, 1.5))], pr, pcol)
    dm = door_marker("Santuario", col, root, (0.0, L.S.FD / 2, 0.0))
    iv = interior("Santuario", col, root, L.S.X - L.S.T, L.S.Y - L.S.T, L.S.H,
                  {"note": "nave hasta los hombros (9 m); la cubierta interior sube hasta 14 m"})
    colo = L.box_col("SANTUARIO-colonly", col, L.S.FW / 2, L.S.FD / 2, L.S.H + L.S.PAR_H)
    colo.parent = root
    t = {"Body": tris(body), "Roof": tris(roof), "Props": sum(tris(o) for o in props), "Well": tris(wo)}
    t["total"] = t["Body"] + t["Roof"] + t["Props"] + t["Well"]
    st["SANTUARIO"] = {
        "marker": mk.name, "location": [round(c, 3) for c in mk.matrix_world.translation],
        "rot_z_deg": round(math.degrees(mk.matrix_world.to_euler().z) % 360, 1),
        "door_world_dir": [round(c, 3) for c in (mk.matrix_world.to_3x3() @ Vector((0, 1, 0)))],
        "tris": t, "budget": BUDGET["SANTUARIO"], "ok": t["total"] <= BUDGET["SANTUARIO"], "lods": lods,
        "dims": {"footprint": [L.S.FW, L.S.FD], "walls_outer": [2 * L.S.X, 2 * L.S.Y], "shoulders_m": L.S.H,
                 "parapet_top_m": L.S.H + L.S.PAR_H, "ridge_m": L.S.RIDGE, "roof_pitch_deg": rinfo["pitch_deg"],
                 "fleche_apex_m": rinfo["fleche"]["apex_z"], "finial_top_m": rinfo["fleche"]["finial_top_z"],
                 "windows": "9 x (1.4 x 6.0) en los lados largos (4 delante + 5 detras) + 4 lancetas 1.0 x 4.6 + "
                            "2 rosetones 3.0 + oculo 1.1 sobre la puerta",
                 "door": f"{L.S.DOOR_W} x {L.S.DOOR_TOP} doble hoja"},
        "repairs": {"stone_patches": binfo["stone_patches"], "roof_tile_patches": rinfo["roof_repairs"],
                    "replaced_beams": f"postes {rinfo['fleche']['replaced_posts']} de la linterna de la flecha"},
        "footprint_check_body": check_footprint(body, L.S.FW / 2, L.S.FD / 2),
        "door_marker": [dm.name, list(dm.location)], "interior": [iv.name, list(iv["interior_size_m"])],
        "collision": colo.name, "props": [o.name for o in props], "well": wo.name}
    return root


def build_salon(col, pcol, st):
    import concordia_buildings as B
    clear(("SALON_HAZANAS", "MARKER_SalonHazanas_Door", "SalonHazanas_InteriorVolume", "SALON_Statue", "SALON_Plaque"))
    mk = bpy.data.objects["MARKER_SalonHazanas"]
    root = new_root("SALON_HAZANAS", mk, col, "Salon de las Hazanas")
    rng = random.Random(B.rng_for("SalonHazanas", L.SEED_SALON))
    body_mb, binfo, statue_slots, plaque_slots = L.salon_body(rng)
    body = mesh_obj(body_mb, "SALON_HAZANAS_Body", col, root)
    roof_mb, rinfo = L.salon_roof(rng)
    roof = mesh_obj(roof_mb, "SALON_HAZANAS_Roof", col, root)
    lods = {"Body": P13.lods(body, col), "Roof": P13.lods(roof, col)}
    pr = bpy.data.objects.new("SALON_HAZANAS_Props", None)
    pcol.objects.link(pr)
    pr.parent = root
    me_a = L._shared_mesh("SALON_Statue_A", lambda mb: L.statue(mb, "A"), B.box_uv)
    me_b = L._shared_mesh("SALON_Statue_B", lambda mb: L.statue(mb, "B"), B.box_uv)
    me_p = L._shared_mesh("SALON_Plaque", L.plaque, B.box_uv)

    def fr_of(key):
        if key == "+Y_front":
            return L.frame("+Y", L.H.X, L.H.FD / 2)
        return L.frame(key, L.H.X, L.H.Y)
    items = []
    for i, (key, p) in enumerate(statue_slots, 1):
        items.append((f"SALON_HAZANAS_Prop_Statue_{i:02d}", me_a if i % 2 else me_b, fr_of(key), p, 0.0))
    for i, (key, p) in enumerate(plaque_slots, 1):
        items.append((f"SALON_HAZANAS_Prop_Plaque_{i:02d}", me_p, fr_of(key), p, 0.0))
    props = place_props(items, pr, pcol)
    dm = door_marker("SalonHazanas", col, root, (0.0, L.H.FD / 2, 0.0))
    iv = interior("SalonHazanas", col, root, L.H.X - L.H.T, L.H.Y - L.H.T, L.H.WALL,
                  {"note": "nave hasta el alero (8 m); la armadura de vigas (hammerbeam) sube hasta 15 m",
                   "chiefs_niches_and_names": "en el interior, etapa posterior"})
    colo = L.box_col("SALON_HAZANAS-colonly", col, L.H.FW / 2, L.H.FD / 2, L.H.WALL)
    colo.parent = root
    t_props = sum(tris(o) for o in props)
    t = {"Body": tris(body), "Roof": tris(roof), "Props": t_props}
    t["total"] = t["Body"] + t["Roof"] + t["Props"]
    st["SALON_HAZANAS"] = {
        "marker": mk.name, "location": [round(c, 3) for c in mk.matrix_world.translation],
        "rot_z_deg": round(math.degrees(mk.matrix_world.to_euler().z) % 360, 1),
        "door_world_dir": [round(c, 3) for c in (mk.matrix_world.to_3x3() @ Vector((0, 1, 0)))],
        "tris": t, "budget": BUDGET["SALON_HAZANAS"], "ok": t["total"] <= BUDGET["SALON_HAZANAS"], "lods": lods,
        "props_unique_meshes": {m.name: sum(len(p.vertices) - 2 for p in m.polygons) for m in (me_a, me_b, me_p)},
        "dims": {"footprint": [L.H.FW, L.H.FD], "walls_outer": [2 * L.H.X, 2 * L.H.Y], "walls_m": L.H.WALL,
                 "ridge_m": L.H.RIDGE, "roof": rinfo, "buttresses_every_m": 6.0,
                 "windows_per_side": len(L.H.WINS), "window": f"{L.H.WIN_W} x {L.H.WIN_TOP - L.H.WIN_Z0}",
                 "portal": f"{L.H.DOOR_W} x {L.H.DOOR_TOP} (arquivolta {L.H.PORTAL_W})",
                 "big_window": f"{L.H.BIGWIN_W} x {round(L.H.BIGWIN_TOP - L.H.BIGWIN_Z0, 2)}",
                 "cross_gable": f"{2 * L.H.FX} m de ancho, alero {L.H.F_EAVE}, clave {round(L.H.f_apex(), 2)}"},
        "niches": [[k, [round(c, 2) for c in p]] for k, p in statue_slots],
        "hammer_ends": binfo["hammer_ends"],
        "repairs": {"stone_patches": binfo["stone_patches"], "roof_tile_patches": rinfo["roof_repairs"],
                    "replaced_beams": binfo["replaced_hammer_ends"]},
        "footprint_check_body": check_footprint(body, L.H.FW / 2, L.H.FD / 2),
        "door_marker": [dm.name, list(dm.location)], "interior": [iv.name, list(iv["interior_size_m"])],
        "collision": colo.name, "props": len(props)}
    return root


# ---------------------------------------------------------------------------
def walk_cells(cell=1.0, R=200):
    """Celdas de 1 m de calle/plaza transitables (road_mask o slab_ring_id) fuera de parcelas, pads y edificios:
    prueba orientada en el marco local de cada obstaculo (el AABB mundial de un pad girado 45 grados tapaba la plaza)."""
    import numpy as np
    me = bpy.data.objects["TRN_City"].data

    def corner(n):
        a = me.color_attributes.get(n)
        v = np.zeros(len(me.loops) * 4, dtype=np.float32)
        a.data.foreach_get("color", v)
        return v.reshape(-1, 4)[:, 0]
    ls = np.zeros(len(me.polygons), dtype=np.int64)
    me.polygons.foreach_get("loop_start", ls)
    road, slab = corner("road_mask")[ls], corner("slab_ring_id")[ls]
    cen = np.zeros(len(me.polygons) * 3, dtype=np.float32)
    me.polygons.foreach_get("center", cen)
    cen = cen.reshape(-1, 3)
    ok = (road > 0.5) | (slab > 0.01)
    n = int(2 * R / cell) + 1
    g = np.zeros((n, n), dtype=bool)
    ii = np.clip(((cen[ok, 0] + R) / cell).astype(int), 0, n - 1)
    jj = np.clip(((cen[ok, 1] + R) / cell).astype(int), 0, n - 1)
    g[ii, jj] = True
    import bmesh
    bm = bmesh.new()
    for o in bpy.data.collections["PLAZA"].objects:
        if o.type == "MESH" and o.name.startswith(("TRN_PlazaParcel", "TRN_Pad_", "TRN_PortalPedestal", "TRN_Atrio")) \
                and not o.name.endswith("-colonly"):
            t = bmesh.new()
            t.from_mesh(o.data)
            t.transform(o.matrix_world)
            tm = bpy.data.meshes.new("TMP_obst")
            t.to_mesh(tm)
            t.free()
            bm.from_mesh(tm)
            bpy.data.meshes.remove(tm)
    obst = BVHTree.FromBMesh(bm)
    bm.free()
    return g, cell, R, obst


def iso_occlusion(roots, st):
    """Celdas de calle/plaza (1 m) a < 45 m de cada edificio tapadas desde CAM_Iso (rayo hacia la camara desde 1.0 m
    sobre el suelo, solo contra el propio edificio)."""
    import build_stage15 as B15
    import bmesh
    cam = bpy.data.objects[C.CAM_ISO_NAME]
    back = -(cam.matrix_world.to_3x3() @ Vector((0, 0, -1))).normalized()
    g, cell, R, obst = walk_cells()
    gb = B15.city_bvh()
    out = {}
    dg = bpy.context.evaluated_depsgraph_get()

    def blocked(p):
        """Punto sobre una parcela/pad (rayo vertical contra sus mallas)."""
        return obst.ray_cast(Vector((p.x, p.y, 200.0)), Vector((0, 0, -1)))[0] is not None
    for root in roots:
        bm = bmesh.new()
        for o in root.children_recursive:
            if o.type != "MESH" or o.hide_render or o.name.endswith(("_LOD1", "_LOD2", "-colonly")):
                continue
            me = o.evaluated_get(dg).to_mesh()
            tmp = bmesh.new()
            tmp.from_mesh(me)
            tmp.transform(o.matrix_world)
            tm = bpy.data.meshes.new("TMP_occ")
            tmp.to_mesh(tm)
            tmp.free()
            bm.from_mesh(tm)
            bpy.data.meshes.remove(tm)
            o.evaluated_get(dg).to_mesh_clear()
        bvh = BVHTree.FromBMesh(bm)
        bm.free()
        c = root.matrix_world.translation
        inv_r = root.matrix_world.inverted()
        hidden, total = [], 0
        for i in range(g.shape[0]):
            x = -R + (i + 0.5) * cell
            if abs(x - c.x) > 45:
                continue
            for j in range(g.shape[1]):
                y = -R + (j + 0.5) * cell
                if abs(y - c.y) > 45 or not g[i, j]:
                    continue
                p = Vector((x, y, B15.ground_at(gb, x, y) + 1.0))
                if blocked(p):
                    continue
                total += 1
                if bvh.ray_cast(p, back, 200.0)[0] is not None:
                    hidden.append(p)
        loc = [inv_r @ p for p in hidden]
        rc = [math.hypot(p.x, p.y) for p in hidden]
        out[root.name] = {"walkable_cells_within_45m": total, "hidden_m2": len(hidden),
                          "hidden_pct": round(100 * len(hidden) / max(1, total), 1),
                          "hidden_radius_from_plaza_center_m": [round(min(rc), 1), round(max(rc), 1)] if rc else None,
                          "hidden_side": ("delante (+Y, hacia la plaza)" if loc and sum(p.y for p in loc) / len(loc) > 0
                                          else "detras (-Y)") if loc else None,
                          "hidden_max_dist_from_building_m": round(max(abs(p.y) - (L.H.FD if "SALON" in root.name
                                                                                    else L.S.FD) / 2 for p in loc), 1)
                          if loc else None}
    st["iso_occlusion"] = out
    return out


def main():
    st = {}
    bpy.ops.wm.open_mainfile(filepath=SRC)
    save()
    st["saved_before"] = os.path.relpath(OUT, REPO)
    import concordia_buildings as B
    B.ensure_materials()
    st["materials"] = L.ensure_materials()
    col = bpy.data.collections["BLD_PORTAL"]
    pcol = bpy.data.collections["BLD_PROPS"]
    r1 = build_santuario(col, pcol, st)
    r2 = build_salon(col, pcol, st)
    for o in col.all_objects:
        if o.name.endswith(("_LOD1", "_LOD2")):
            o.hide_set(True)
    bpy.context.view_layer.update()
    iso_occlusion([r1, r2], st)
    # visibilidad del Faro con los dos edificios nuevos
    import build_stage15 as B15
    with open(os.path.join(REPO, "docs", "reports", "stage15_faro.json")) as fh:
        tgt = Vector(json.load(fh)["visibility"]["target"])
    vis = {}
    B15.visibility(tgt, stats=vis)
    st["faro_visibility_after"] = {k: {"pct": v["pct"], "samples": v["samples"], "blocked_by": v["blocked_by"]}
                                   for k, v in vis["visibility"]["per_street"].items()}
    import stage11_godot as G
    st["export"] = {}
    for root, fname in ((r1, "concordia_santuario.glb"), (r2, "concordia_salon_hazanas.glb")):
        objs = [root] + list(root.children_recursive)
        path = os.path.join(REPO, "export", "godot", fname)
        size = G.export_glb(objs, path)
        st["export"][fname] = {"mb": round(size / 2 ** 20, 2), **G.glb_info(path)}
    for o in col.all_objects:
        if o.name.endswith(("_LOD1", "_LOD2")):
            o.hide_set(True)
    save()
    with open(REPORT, "w") as fh:
        json.dump(st, fh, indent=1, ensure_ascii=False, default=str)
    print("saved:", OUT)
    for k in ("SANTUARIO", "SALON_HAZANAS"):
        print(k, json.dumps({kk: st[k][kk] for kk in ("tris", "ok", "lods", "footprint_check_body")}, default=str))
    print(json.dumps(st["iso_occlusion"]))
    print(json.dumps({k: (v["pct"], v["blocked_by"]) for k, v in st["faro_visibility_after"].items()}, ensure_ascii=False))
    print(json.dumps(st["export"], default=str)[:800])
    _ = Matrix


if __name__ == "__main__":
    main()
