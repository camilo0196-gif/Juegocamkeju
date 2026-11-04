"""
CONCORDIA - Etapa 01: escena base.

Crea una escena limpia (metrica, escala 1.0), las Collections vacias, la camara
isometrica CAM_Iso y los Empties de las 4 puertas. Guarda concordia_v01.blend.

Uso (Blender como modulo o binario):
    python  tools/blender/stage01_scene_base.py [--out blender/concordia_v01.blend]
    blender -b -P tools/blender/stage01_scene_base.py -- [--out ...]
"""

import argparse
import os
import sys
from math import radians

import bpy
from mathutils import Euler, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import concordia_const as C  # noqa: E402

REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
DEFAULT_OUT = os.path.join(REPO, "blender", f"{C.BLEND_BASENAME}_v01.blend")

GATE_EMPTY_TYPE = "ARROWS"
GATE_EMPTY_SIZE = 3.0
GATE_COLLECTION = "WALL_LAYOUT"


def parse_args():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    p = argparse.ArgumentParser()
    p.add_argument("--out", default=DEFAULT_OUT)
    return p.parse_args(argv)


def reset_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    # Purga total de datos huerfanos
    bpy.ops.outliner.orphans_purge(do_local_ids=True, do_linked_ids=True, do_recursive=True)
    scene = bpy.context.scene
    scene.name = "Concordia"
    us = scene.unit_settings
    us.system = C.UNIT_SYSTEM
    us.scale_length = C.UNIT_SCALE
    us.length_unit = "METERS"
    us.mass_unit = "KILOGRAMS"
    scene.render.resolution_x, scene.render.resolution_y = C.RENDER_RES
    scene.render.resolution_percentage = 100
    # Sin ficheros .blend1 de respaldo junto al versionado manual
    bpy.context.preferences.filepaths.save_version = 0
    return scene


def make_collections(scene):
    cols = {}
    for name in C.COLLECTIONS:
        col = bpy.data.collections.new(name)
        scene.collection.children.link(col)
        cols[name] = col
    return cols


def make_iso_camera(scene):
    cam_data = bpy.data.cameras.new(C.CAM_ISO_NAME)
    cam_data.type = "ORTHO"
    cam_data.ortho_scale = C.CAM_ISO_ORTHO_SCALE
    cam_data.clip_start, cam_data.clip_end = C.CAM_ISO_CLIP
    cam_data.sensor_fit = "AUTO"
    cam = bpy.data.objects.new(C.CAM_ISO_NAME, cam_data)
    rot = Euler((radians(C.CAM_ISO_ROT_X), 0.0, radians(C.CAM_ISO_ROT_Z)), "XYZ")
    cam.rotation_euler = rot
    view_dir = rot.to_matrix() @ Vector((0.0, 0.0, -1.0))
    cam.location = Vector(C.CAM_ISO_TARGET) - view_dir * C.CAM_ISO_DISTANCE
    scene.collection.objects.link(cam)  # en la raiz: herramienta, no pieza del juego
    scene.camera = cam
    return cam


def make_gate_markers(cols):
    out = []
    for name, (angle, label) in C.GATES.items():
        e = bpy.data.objects.new(name, None)
        e.empty_display_type = GATE_EMPTY_TYPE
        e.empty_display_size = GATE_EMPTY_SIZE
        e.location = C.polar(angle, C.GATE_RADIUS, C.GATE_Z)
        # Eje local +X apunta hacia fuera de la ciudad (radial)
        e.rotation_euler = (0.0, 0.0, radians(angle))
        e["gate_name"] = label
        e["angle_deg"] = angle
        cols[GATE_COLLECTION].objects.link(e)
        out.append(e)
    return out


def report(scene):
    print("=== CONCORDIA stage01 report ===")
    us = scene.unit_settings
    print(f"units: system={us.system} scale_length={us.scale_length} length={us.length_unit}")
    print("collections:", [(c.name, len(c.all_objects)) for c in scene.collection.children])
    cam = bpy.data.objects[C.CAM_ISO_NAME]
    r = cam.rotation_euler
    print(f"{cam.name}: type={cam.data.type} ortho_scale={cam.data.ortho_scale} "
          f"rot=({r.x * 57.29577951308232:.3f}, {r.y * 57.29577951308232:.3f}, "
          f"{r.z * 57.29577951308232:.3f}) loc={tuple(round(v, 3) for v in cam.location)} "
          f"active={scene.camera == cam}")
    for name in C.GATES:
        o = bpy.data.objects[name]
        x, y, z = o.location
        print(f"{name}: loc=({x:.3f}, {y:.3f}, {z:.3f}) r={(x * x + y * y) ** 0.5:.3f} "
              f"collection={o.users_collection[0].name} label={o['gate_name']}")
    print("objects total:", len(bpy.data.objects), "meshes:", len(bpy.data.meshes))


def main():
    args = parse_args()
    scene = reset_scene()
    cols = make_collections(scene)
    make_iso_camera(scene)
    make_gate_markers(cols)
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=args.out, compress=False)
    report(scene)
    print("saved:", args.out)


if __name__ == "__main__":
    main()
