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
    # runas en la hilada inferior: modulos donde el terreno interior las tapa
    buried = []
    for m in stats["wall_layout"]["modules"]:
        ang = (m["from_k"] + 0.5) * W.STEP_DEG
        x, y, _ = C.polar(ang, (C.WALL_RADIUS * cos(W.HALF)) + W.Y_IN - 0.15)
        zg = T.height(x, y)
        if zg > C.DATUM + W.RUNE_Z + W.RUNE_W / 2:
            buried.append({"module_from_k": m["from_k"], "ground_above_runes_m": round(zg - C.DATUM - W.RUNE_Z, 2)})
    out["rune_line_buried_modules"] = {"count": len(buried), "list": buried}
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
