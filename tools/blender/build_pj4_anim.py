"""
CONCORDIA - PJ4: animaciones propias del Sanador hechas a mano sobre el esqueleto del elfo (PJ3).
Parte de blender/elfo_v03.blend (no se modifica) y guarda blender/elfo_v04.blend.
  30 fps, sin movimiento de raiz (Root fijo; la cadera solo baja en vertical para apoyar pies y rodillas),
  nombres claros; las ciclicas acaban en -loop para que Godot las marque como bucle (documentacion 4.7,
  "Animation loop (-loop, -cycle)").
    Heal_Cast_Single  0,9 s  extiende la mano derecha con el baston al frente, pulso y vuelve
    Heal_Channel-loop 1,5 s  brazos abiertos hacia fuera, postura serena, balanceo ligero (cierra en bucle)
    Heal_Cast_Area    1,2 s  brazos arriba y despues abajo como una onda
    Revive            2,0 s  se arrodilla y apoya la mano izquierda sobre el objetivo (acaba de rodillas)
  Cada animacion: Action con fake user y rango de fotogramas manual (frame_start = 1).
  Poses clave con los giros en ejes de mundo del PJ3 (build_pj3_rig.rot_world) desde el reposo, gestos amplios
  para leerse desde la camara isometrica; la falda se coloca en cada clave (fit_skirt, como en PJ3).
  Export: export/godot/pj_elfo_sanador_anim.glb (cuerpo, ropa, pelo, esqueleto y SOLO estas 4 animaciones, por
  pistas NLA). Informe: docs/reports/pj4_anim.json. Capturas: python capture_pj4.py
python build_pj4_anim.py
"""

import json
import math
import os
import sys
import traceback

import bpy
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build_pj3_rig as P3  # noqa: E402

REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
SRC = os.path.join(REPO, "blender", "elfo_v03.blend")
DST = os.path.join(REPO, "blender", "elfo_v04.blend")
REPORT = os.path.join(REPO, "docs", "reports", "pj4_anim.json")
GLB = os.path.join(REPO, "export", "godot", "pj_elfo_sanador_anim.glb")
FPS = 30

FINGERS = ("Index", "Middle", "Ring", "Little")


def grip_r(k=1.0):
    """mano derecha cerrada sobre el asta del baston (Weapon_R)"""
    s = []
    for f in FINGERS:
        s += [(f"Right{f}Proximal", "LOCALZ", 62 * k), (f"Right{f}Intermediate", "LOCALZ", 75 * k),
              (f"Right{f}Distal", "LOCALZ", 40 * k)]
    return s + [("RightThumbProximal", "LOCALX", 25 * k), ("RightThumbDistal", "LOCALZ", 25 * k)]


def soft_l(k=1.0):
    """mano izquierda relajada (dedos algo curvados); k < 0 la abre"""
    s = []
    for f in FINGERS:
        s += [(f"Left{f}Proximal", "LOCALZ", -14 * k), (f"Left{f}Intermediate", "LOCALZ", -18 * k),
              (f"Left{f}Distal", "LOCALZ", -10 * k)]
    return s


def stand():
    """reposo del Sanador: brazos abajo, baston vertical en la derecha (codo adelantado)"""
    return (P3.A_DOWN(76) + [("Spine", "X", 2), ("RightUpperArm", "X", -8), ("RightLowerArm", "X", -68),
                             ("LeftLowerArm", "X", -14)] + grip_r() + soft_l()
            + [("STAFF", None, (-0.08, -0.12, 1.0))])                       # baston casi vertical


def cast_extend(push=0.0):
    """brazo derecho estirado al frente y algo arriba, baston apuntando al frente; push: impulso del pulso"""
    up = 0.18 + 0.05 * push
    return ([("Spine", "X", 7 + push), ("Chest", "X", 3), ("Head", "X", -5), ("Spine", "Z", -6),
             ("LeftUpperArm", "Y", 70), ("LeftUpperArm", "X", 22), ("LeftLowerArm", "X", -25)]
            + grip_r() + soft_l(-0.5)
            + [("AIMDIR", "RightUpperArm", (-0.12, -1.0, up)), ("AIMDIR", "RightLowerArm", (-0.05, -1.0, up + 0.05)),
               ("STAFF", None, (-0.05, -1.0, 0.55 + 0.1 * push))])


def channel(sway=0.0, lift=0.0):
    """brazos abiertos hacia fuera y algo adelante, palmas hacia arriba; sway: balanceo lateral (-1..1)"""
    return ([("Spine", "Y", 3 * sway), ("Spine", "X", -3), ("Chest", "X", -2), ("Head", "X", 4),
             ("Head", "Y", -2 * sway),
             ("LeftUpperArm", "Y", 28 - 6 * lift), ("RightUpperArm", "Y", -28 + 6 * lift),
             ("LeftUpperArm", "Z", -38), ("RightUpperArm", "Z", 38),
             ("LeftLowerArm", "Z", -18), ("RightLowerArm", "Z", 18),
             ("LeftLowerArm", "LOCALY", -70), ("RightLowerArm", "LOCALY", 70)]   # palmas arriba
            + grip_r() + soft_l(-0.6) + [("STAFF", None, (-0.25, -0.1, 1.0))])


def area_up(k=1.0):
    return ([("Spine", "X", -7 * k), ("Chest", "X", -4 * k), ("Head", "X", -16 * k),
             ("LeftUpperArm", "Y", -72 * k), ("RightUpperArm", "Y", 72 * k),
             ("LeftUpperArm", "Z", -14), ("RightUpperArm", "Z", 14),
             ("LeftLowerArm", "Z", -8), ("RightLowerArm", "Z", 8)]
            + grip_r() + soft_l(-0.8) + [("STAFF", None, (-0.1, 0.0, 1.0))])


def area_down(k=1.0):
    knee = [("LeftUpperLeg", "X", -14 * k), ("LeftLowerLeg", "X", 28 * k), ("LeftFoot", "X", -14 * k),
            ("RightUpperLeg", "X", -14 * k), ("RightLowerLeg", "X", 28 * k), ("RightFoot", "X", -14 * k)]
    return (knee + [("Spine", "X", 14 * k), ("Chest", "X", 5 * k), ("Head", "X", 8 * k),
                    ("LeftUpperArm", "Y", 38), ("RightUpperArm", "Y", -38),
                    ("LeftUpperArm", "Z", -32), ("RightUpperArm", "Z", 32),
                    ("LeftLowerArm", "Z", -6), ("RightLowerArm", "Z", 6)]
            + grip_r() + soft_l(-0.8) + [("STAFF", None, (-0.3, -1.0, -0.15))])     # la punta barre hacia abajo


KNEEL_LEGS = [("RightUpperLeg", "X", 2), ("RightLowerLeg", "X", 92), ("RightFoot", "X", 40),
              ("LeftUpperLeg", "X", -88), ("LeftLowerLeg", "X", 86)]


def revive_half():
    return ([("LeftUpperLeg", "X", -48), ("LeftLowerLeg", "X", 58), ("LeftFoot", "X", -10),
             ("RightUpperLeg", "X", 8), ("RightLowerLeg", "X", 62), ("RightFoot", "X", 22),
             ("Spine", "X", 10), ("Head", "X", 8)]
            + P3.A_DOWN(70) + [("RightLowerArm", "X", -60), ("LeftLowerArm", "X", -20)] + grip_r() + soft_l()
            + [("STAFF", None, (-0.1, -0.15, 1.0))])


def revive_kneel(reach=0.0, press=0.0):
    """de rodillas (rodilla derecha en el suelo); reach 0..1: la mano izquierda va al objetivo tendido delante
    (0,15 m a su izquierda, 0,6 m al frente, a 0,12 m del suelo); press: empuja un poco (pulso de la habilidad)"""
    spec = (KNEEL_LEGS
            + [("Spine", "X", 16 + 16 * reach + 3 * press), ("Chest", "X", 4 + 6 * reach),
               ("Head", "X", 12 + 14 * reach),
               ("RightUpperArm", "Y", -70), ("RightLowerArm", "X", -62),
               ("LeftUpperArm", "Y", 76), ("LeftLowerArm", "X", -20)]
            + grip_r() + soft_l(-1.0 * reach) + [("STAFF", None, (-0.1, 0.1, 1.0))])
    if reach > 0:
        tgt = (0.15, -0.62, 0.12 - 0.03 * press)
        spec += [("AIMAT", "LeftUpperArm", tgt), ("AIMAT", "LeftLowerArm", tgt), ("AIMDIR", "LeftHand", (0.0, -0.6, -1.0))]
    return spec


ANIMS = [
    # nombre, ultimo fotograma (duracion = (ultimo - 1) / 30), claves [(fotograma, pose)], fotogramas de captura
    ("Heal_Cast_Single", 28, [(1, stand()), (8, stand() + [("RightUpperArm", "X", 14), ("Spine", "Z", 5)]),
                               (14, cast_extend()), (19, cast_extend(push=3.0)), (28, stand())], (8, 14, 19)),
    ("Heal_Channel-loop", 46, [(1, channel(0, 0)), (12, channel(1, 1)), (23, channel(0, 0.3)), (35, channel(-1, 1)),
                               (46, channel(0, 0))], (1, 12, 35)),
    ("Heal_Cast_Area", 37, [(1, stand()), (11, area_up()), (16, area_up(1.08)), (24, area_down()),
                            (29, area_down(0.7)), (37, stand())], (11, 24, 29)),
    ("Revive", 61, [(1, stand()), (14, revive_half()), (28, revive_kneel(0.0)), (42, revive_kneel(1.0)),
                    (52, revive_kneel(1.0, press=1.0)), (61, revive_kneel(1.0))], (14, 28, 42)),
]


def pose_from(arm, spec, ground_objs):
    """rotaciones (ejes de mundo / locales) -> apoyo en vertical (Hips) -> orientaciones a puntos del mundo
    ("AIMDIR" direccion desde la cabeza del hueso, "AIMAT" punto) -> baston ("STAFF": la +Y de Weapon_R apunta a esa
    direccion girando la mano derecha) -> falda"""
    for pb in arm.pose.bones:
        pb.rotation_mode = "QUATERNION"
        pb.matrix_basis = Matrix.Identity(4)
    bpy.context.view_layer.update()
    late = []
    for b, ax, d in spec:
        if b in ("AIMDIR", "AIMAT", "STAFF"):
            late.append((b, ax, d))
        else:
            P3.rot_world(arm, b, ax, d)
    z = P3.eval_min_z(ground_objs)
    hips = arm.pose.bones["Hips"]
    hips.matrix = Matrix.Translation((0, 0, -z)) @ hips.matrix          # apoyo en vertical, Root quieto
    bpy.context.view_layer.update()
    for kind, bone, v in late:
        if kind == "AIMDIR":
            P3.aim(arm, bone, arm.pose.bones[bone].head + Vector(v).normalized())
        elif kind == "AIMAT":
            P3.aim(arm, bone, Vector(v))
        else:
            staff_dir(arm, Vector(v))
    skirt = P3.fit_skirt(arm)
    return {b.name: (b.rotation_quaternion.copy(), b.location.copy()) for b in arm.pose.bones}, round(z, 3), skirt


def staff_dir(arm, want):
    w = arm.pose.bones["Weapon_R"]
    cur = (w.matrix.to_3x3() @ Vector((0, 1, 0))).normalized()
    q = cur.rotation_difference(want.normalized())
    hb = arm.pose.bones["RightHand"]
    h = hb.head.copy()
    hb.matrix = Matrix.Translation(h) @ q.to_matrix().to_4x4() @ Matrix.Translation(-h) @ hb.matrix
    bpy.context.view_layer.update()


def build_action(arm, name, last, keys, ground_objs):
    act = bpy.data.actions.new(name)
    act.use_fake_user = True
    arm.animation_data_create()
    arm.animation_data.action = act
    prev = {}
    info = []
    for frame, spec in keys:
        vals, z, skirt = pose_from(arm, spec, ground_objs)
        for pb in arm.pose.bones:
            if pb.name == "Root":
                continue                                                # sin claves en la raiz
            q, loc = vals[pb.name]
            if pb.name in prev:
                q.make_compatible(prev[pb.name])                        # sin saltos de signo entre claves
            prev[pb.name] = q.copy()
            pb.rotation_quaternion = q
            pb.location = loc
            pb.keyframe_insert("rotation_quaternion", frame=frame, group=pb.name)
            pb.keyframe_insert("location", frame=frame, group=pb.name)
        info.append({"fotograma": frame, "cadera_bajada_m": z})
    act.use_frame_range = True
    act.frame_start = 1
    act.frame_end = last
    act.use_cyclic = name.endswith("-loop")
    return act, info


def main():
    bpy.ops.wm.open_mainfile(filepath=SRC)
    sc = bpy.context.scene
    sc.render.fps = FPS
    sc.render.fps_base = 1.0
    arm = bpy.data.objects["PJ_Elfo_Rig"]
    meshes = [o for o in bpy.data.objects if o.type == "MESH" and any(
        m.type == "ARMATURE" and m.object == arm for m in o.modifiers)]
    ground = [bpy.data.objects[n] for n in P3.BODY + ("Boots",) if n in bpy.data.objects]
    rep = {"fps": FPS, "animaciones": {}}
    for name, last, keys, shots in ANIMS:
        act, info = build_action(arm, name, last, keys, ground)
        rep["animaciones"][name] = {"fotogramas": [1, last], "duracion_s": round((last - 1) / FPS, 3),
                                    "bucle": name.endswith("-loop"), "claves": info, "capturas": list(shots)}
        print("ANIM", name, last, flush=True)
    # pistas NLA (una por animacion) para exportar solo estas 4
    arm.animation_data.action = None
    for t in list(arm.animation_data.nla_tracks):
        arm.animation_data.nla_tracks.remove(t)
    for name, last, keys, shots in ANIMS:
        tr = arm.animation_data.nla_tracks.new()
        tr.name = name
        tr.strips.new(name, 1, bpy.data.actions[name])
        tr.mute = True
    for pb in arm.pose.bones:
        pb.matrix_basis = Matrix.Identity(4)
    sc.frame_start, sc.frame_end = 1, 61
    sc["pj4_datos"] = json.dumps({n: [1, l] for n, l, _k, _s in ANIMS})
    bpy.ops.wm.save_as_mainfile(filepath=DST)
    # export (mascaras HIDE_* silenciadas solo durante la exportacion, como en PJ3)
    muted = []
    for o in meshes:
        if o.animation_data:
            for fc in o.animation_data.drivers:
                if fc.data_path.startswith("modifiers[") and not fc.mute:
                    fc.mute = True
                    muted.append(fc)
        for m in o.modifiers:
            if m.type == "MASK":
                m.show_viewport = m.show_render = False
    bpy.context.view_layer.update()
    for o in bpy.context.view_layer.objects:
        o.select_set(False)
    for o in [arm] + meshes:
        o.select_set(True)
    bpy.ops.export_scene.gltf(filepath=GLB, export_format="GLB", use_selection=True, export_yup=True,
                              export_apply=True, export_extras=True, export_image_format="AUTO",
                              export_vertex_color="NONE", export_animations=True,
                              export_animation_mode="NLA_TRACKS", export_force_sampling=True,
                              export_anim_slide_to_zero=True)
    rep["glb"] = {"archivo": os.path.relpath(GLB, REPO), "kb": round(os.path.getsize(GLB) / 1024, 1)}
    rep["blend"] = os.path.relpath(DST, REPO)
    json.dump(rep, open(REPORT, "w"), indent=1, ensure_ascii=False)
    print("GLB", json.dumps(rep["glb"]), flush=True)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        traceback.print_exc()
        sys.stdout.flush()
        os._exit(1)
    sys.stdout.flush()
    os._exit(0)
