"""
CONCORDIA - Etapa 04 (kit modular de muralla). Genera concordia_v04.blend desde v03.

Pasos: texturas (si faltan) -> kit + montaje (stage04_wall) -> comprobaciones -> export:
  export/godot/concordia_wall_kit.glb        piezas del kit (+ hijos -colonly)
  export/godot/concordia_wall_kit_lods.glb   LOD1 (50 %) y LOD2 (15 %) de cada pieza
  export/godot/concordia_wall_layout.glb     montaje: 48 slots + 48 modulos + escaleras + reja,
                                             mallas compartidas (instancias) y marcadores

Uso:
    python tools/blender/build_stage04.py [--in v03.blend] [--out v04.blend]
"""

import argparse
import json
import os
import sys
import time
from math import acos, cos, degrees, radians, sin, sqrt

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import concordia_const as C  # noqa: E402
import terrain_profile as T  # noqa: E402

REPO = os.path.abspath(os.path.join(HERE, "..", ".."))


def parse_args():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    p = argparse.ArgumentParser()
    p.add_argument("--in", dest="inp", default=os.path.join(REPO, "blender", f"{C.BLEND_BASENAME}_v03.blend"))
    p.add_argument("--out", default=os.path.join(REPO, "blender", f"{C.BLEND_BASENAME}_v04.blend"))
    p.add_argument("--report", default=os.path.join(REPO, "docs", "reports", "stage04_wall.json"))
    p.add_argument("--export-dir", default=os.path.join(REPO, "export", "godot"))
    return p.parse_args(argv)


def export(objs, path):
    for o in bpy.context.view_layer.objects:
        o.select_set(False)
    for o in objs:
        o.select_set(True)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    bpy.ops.export_scene.gltf(filepath=path, export_format="GLB", use_selection=True, export_yup=True,
                              export_apply=True, export_extras=True, export_image_format="AUTO",
                              export_vertex_color="NONE")
    return os.path.getsize(path)


def checks(stats):
    import stage04_wall as W
    out = {}
    lay = [o for o in bpy.data.collections["WALL_LAYOUT"].objects if o.type == "MESH" and not o.name.endswith("-colonly")]
    segA = [o for o in lay if o.name.startswith("WALL_Seg") and o.name.endswith("_A")]
    zmax = max((o.matrix_world @ v.co).z for o in segA for v in o.data.vertices)
    zwalk = WALK = W.WALK_Z + C.DATUM
    out["wall_top_abs_z"] = round(zmax, 3)
    out["wall_height_m"] = round(zmax - C.DATUM, 3)
    out["walkway_abs_z"] = round(WALK, 3)
    out["hourde_top_m"] = stats["wall_kit"]["WALL_Mod_C"]["z_max"]
    slots = stats["wall_layout"]["slots"]
    out["main_structures"] = sum(1 for s in slots if s["type"] in ("gate", "tower"))
    out["slots"] = len(slots)
    out["modules"] = len(stats["wall_layout"]["modules"])
    out["markers"] = sum(1 for o in bpy.data.collections["WALL_LAYOUT"].objects if o.name.startswith("MARKER_WallSlot_"))
    # puertas: ningun camino hacia fuera
    trn = bpy.data.objects["TRN_City"]
    me = trn.data
    gate_info = {}
    for k in (0, 12, 24, 36):
        a = radians(k * W.STEP_DEG)
        e = Vector((cos(a), sin(a), 0))
        tvec = Vector((-sin(a), cos(a), 0))
        walk_r, steep_min = 0.0, 90.0
        for p in me.polygons:
            c = p.center
            u = c.x * e.x + c.y * e.y
            v = c.x * tvec.x + c.y * tvec.y
            if 204.0 <= u <= 212.0 and abs(v) <= 16.0:
                s = degrees(acos(min(1.0, p.normal.z)))
                if s < C.STAIR_SLOPE:
                    walk_r = max(walk_r, u)
                if u > 206.0:
                    steep_min = min(steep_min, s)
        exterior = []
        for cn in ("STREETS", "MORADAS", "PLAZA"):
            for o in bpy.data.collections[cn].all_objects:
                if not (isinstance(o, bpy.types.Object) and o.type == "MESH"):
                    continue
                mw = o.matrix_world
                for vv in o.data.vertices:
                    w = mw @ vv.co
                    if w.x * e.x + w.y * e.y > 197.0 and abs(w.x * tvec.x + w.y * tvec.y) <= 20.0:
                        exterior.append(o.name)
                        break
        gate_info[f"k{k:02d}"] = {"walkable_ground_ends_r": round(walk_r, 2), "min_slope_beyond_r206": round(steep_min, 1),
                                  "city_pieces_beyond_r200": exterior}
    out["gates_no_exit_path"] = gate_info
    # runas a +4.5: altura sobre el terreno interior y visibilidad desde dentro y desde fuera
    lay_meshes = [o for o in bpy.data.collections["WALL_LAYOUT"].objects if o.type == "MESH"
                  and not o.name.endswith("-colonly")]
    others = [bpy.data.objects["TRN_City"]] + [o for cn in ("MORADAS", "STREETS", "PLAZA")
                                              for o in bpy.data.collections[cn].all_objects
                                              if isinstance(o, bpy.types.Object) and o.type == "MESH"]
    dg = bpy.context.evaluated_depsgraph_get()
    verts, polys = [], []
    for o in lay_meshes + others:
        ev = o.evaluated_get(dg)
        me2 = ev.to_mesh()
        mw = o.matrix_world
        off = len(verts)
        verts += [mw @ v.co for v in me2.vertices]
        polys += [[off + i for i in p_.vertices] for p_ in me2.polygons]
        ev.to_mesh_clear()
    bvh = BVHTree.FromPolygons(verts, polys)
    zr = C.DATUM + W.RUNE_Z
    clear, vis_in, vis_out, tot, hidden_in, hidden_out = [], 0, 0, 0, [], []
    for m in stats["wall_layout"]["modules"]:
        for f in (0.15, 0.3, 0.5, 0.7, 0.85):
            ang = radians((m["from_k"] + f) * W.STEP_DEG)
            e = Vector((cos(ang), sin(ang), 0))
            rc = C.WALL_RADIUS * cos(W.HALF) / cos(radians((f - 0.5) * W.STEP_DEG))
            p_in = e * (rc + W.Y_IN + W.RUNE_D - 0.02) + Vector((0, 0, zr))
            p_out = e * (rc + W.Y_OUT - W.RUNE_D + 0.02) + Vector((0, 0, zr))
            gx, gy = (e * (rc + W.Y_IN - 0.3)).xy
            clear.append(zr - W.RUNE_W / 2 - T.height(gx, gy))
            tot += 1
            ex, ey = (e * 182.0).xy
            eye_in = Vector((ex, ey, T.height(ex, ey) + 1.7))
            d = p_in - eye_in
            h = bvh.ray_cast(eye_in, d.normalized(), d.length - 0.05)
            vis_in += h[0] is None
            if h[0] is not None:
                hidden_in.append(m["from_k"])
            eo = e * 240.0
            eye_out = Vector((eo.x, eo.y, C.Z_EXTERIOR + 1.7))
            d = p_out - eye_out
            h = bvh.ray_cast(eye_out, d.normalized(), d.length - 0.05)
            vis_out += h[0] is None
            if h[0] is not None:
                hidden_out.append(m["from_k"])
    from collections import Counter
    out["rune_ring"] = {"z_rel_base": W.RUNE_Z, "z_abs": round(zr, 2), "faces": "interior y exterior de los 48 modulos",
                        "min_clearance_over_inner_ground_m": round(min(clear), 2),
                        "visible_from_inside": f"{vis_in}/{tot}", "visible_from_outside": f"{vis_out}/{tot}",
                        "hidden_inside_by_module": dict(Counter(hidden_in)),
                        "hidden_outside_by_module": dict(Counter(hidden_out)),
                        "viewers": "dentro: ojo a 1.7 m en r=182; fuera: ojo a 1.7 m sobre el yermo en r=240"}
    # camino de ronda: colision plana y continua por tramos (entre puertas)
    cols = [o for o in bpy.data.collections["WALL_LAYOUT"].objects if o.name.endswith("-colonly")]
    cv, cp = [], []
    for o in cols:
        mw = o.matrix_world
        off = len(cv)
        cv += [mw @ v.co for v in o.data.vertices]
        cp += [[off + i for i in p_.vertices] for p_ in o.data.polygons]
    cb = BVHTree.FromPolygons(cv, cp)
    zw = C.DATUM + W.WALK_Z
    tramos = {}
    for g in range(4):
        k0 = g * 12
        flat = blocked = gaps = 0
        zs = []
        for kk in range(12):
            k = k0 + kk
            for i in range(52):
                f = (i + 0.5) / 52
                ang = radians((k + f) * W.STEP_DEG)
                e = Vector((cos(ang), sin(ang), 0))
                rc = C.WALL_RADIUS * cos(W.HALF) / cos(radians((f - 0.5) * W.STEP_DEG))
                p = e * (rc + W.Y_IN + W.WALK_W / 2)
                hit = cb.ray_cast(Vector((p.x, p.y, zw + 30)), Vector((0, 0, -1)))
                if hit[0] is None:
                    gaps += 1
                elif abs(hit[0].z - zw) < 1e-3:
                    flat += 1
                    zs.append(hit[0].z)
                else:
                    blocked += 1
        joints = joint_gaps = 0
        for kk in range(1, 12):
            k = k0 + kk
            for df in (-0.02, 0.02):
                ang = radians(k * W.STEP_DEG) + df / C.WALL_RADIUS
                e = Vector((cos(ang), sin(ang), 0))
                p = e * (C.WALL_RADIUS + W.Y_IN + W.WALK_W / 2)
                hit = cb.ray_cast(Vector((p.x, p.y, zw + 30)), Vector((0, 0, -1)))
                joints += 1
                joint_gaps += hit[0] is None or abs(hit[0].z - zw) > 1e-3 and hit[0].z < zw
        tramos[f"k{k0:02d}-k{(k0 + 12) % 48:02d}"] = {"samples": flat + blocked + gaps, "flat_at_walkway": flat,
                                                     "blocked_by_gate_structures": blocked, "gaps": gaps,
                                                     "joint_checks_2cm": joints, "joint_gaps": joint_gaps}
    out["walkway_collision"] = tramos
    # oclusion en CAM_Iso: franja interior tapada por el muro de 15 m en los tramos que miran a la camara
    cam = bpy.data.objects[C.CAM_ISO_NAME]
    d = cam.rotation_euler.to_matrix() @ Vector((0, 0, -1))
    elev = degrees(acos(min(1.0, sqrt(d.x ** 2 + d.y ** 2))))
    hidden = W.WALL_H / (-(d.z) / sqrt(d.x ** 2 + d.y ** 2))      # alto / tan(elevacion)
    facing = [m["from_k"] for m in stats["wall_layout"]["modules"]
              if (cos(radians((m["from_k"] + 0.5) * W.STEP_DEG)) * -d.x + sin(radians((m["from_k"] + 0.5) * W.STEP_DEG)) * -d.y) > 0]
    out["iso_occlusion"] = {"camera_elevation_deg": round(elev, 2),
                            "ground_hidden_behind_15m_wall_m": round(hidden, 1),
                            "modules_between_camera_and_city": len(facing),
                            "note": "en esos tramos el muro tapa una franja interior; en Godot conviene recortarlo "
                                    "o difuminarlo cuando el jugador esta detras"}
    stats["wall_checks"] = out
    return out


def main():
    args = parse_args()
    if not os.path.exists(os.path.join(REPO, "textures", "wall", "T_Granite_Courses_albedo.png")):
        import wall_textures
        wall_textures.main()
    bpy.ops.wm.open_mainfile(filepath=args.inp)
    scene = bpy.context.scene
    stats = {"timings_s": {}}
    import stage04_wall
    t0 = time.time()
    stage04_wall.build(scene, stats)
    stats["timings_s"]["wall"] = round(time.time() - t0, 1)
    checks(stats)
    kit = [o for o in bpy.data.collections["WALL_KIT"].objects]
    lods = [o for o in bpy.data.collections["WALL_KIT_LODS"].objects]
    lay = [o for o in bpy.data.collections["WALL_LAYOUT"].objects]
    bpy.data.collections["WALL_KIT_LODS"].hide_render = False
    ex = {}
    for fname, objs in (("concordia_wall_kit.glb", kit), ("concordia_wall_kit_lods.glb", lods),
                        ("concordia_wall_layout.glb", lay)):
        ex[fname] = {"objects": len(objs), "bytes": export(objs, os.path.join(args.export_dir, fname))}
    bpy.data.collections["WALL_KIT_LODS"].hide_render = True
    stats["wall_export"] = ex
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.wm.save_as_mainfile(filepath=args.out, compress=True, relative_remap=True)
    bpy.ops.file.make_paths_relative()
    bpy.ops.wm.save_mainfile(compress=True)
    os.makedirs(os.path.dirname(args.report), exist_ok=True)
    with open(args.report, "w") as fh:
        json.dump(stats, fh, indent=1, ensure_ascii=False)
    print("saved:", args.out)


if __name__ == "__main__":
    main()
