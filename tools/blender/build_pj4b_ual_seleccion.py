"""
CONCORDIA - PJ4b: seleccion de animaciones de la Universal Animation Library (Quaternius, Standard, CC0) para el
elfo Sanador, con los nombres finales, sobre los esqueletos ORIGINALES de la UAL (no se retargetea en Blender: lo
hace Godot con BoneMap + SkeletonProfileHumanoid).
  UAL 1 (rig DEF-*): Death_A (= Death01), Death_B (Death01 en espejo izquierda-derecha + otra cabeza y otros brazos),
         Idle_Loop, Walk_Loop, Walk_Formal_Loop, Jog_Fwd_Loop, Sprint_Loop, Sitting_*, Hit_Chest, Hit_Head,
         Spell_Simple_*
  UAL 2 (rig estilo Unreal): GetUp (= LayToIdle; si no enlaza con el final de Death_A se le anaden 6-8 fotogramas
         de transicion desde esa pose), GetUp_B (igual, desde el final de Death_B), Consume, Yes, Idle_No-loop (= Idle_No_Loop), Idle_FoldArms-loop (= Idle_FoldArms_Loop),
         Chest_Open, Hit_Knockback
  Espejo: en cada fotograma, matriz de cada hueso (espacio del armature) del hueso simetrico, reflejada en X
          (S M S) y corregida por la diferencia de reposo: T = S M_sim S (S R_sim S)^-1 R.
  Export: animations/ual/sanador_ual1_seleccion.glb y sanador_ual2_seleccion.glb (esqueleto + maniqui + solo las
          animaciones elegidas, por pistas NLA con su nombre final). Informe: docs/reports/pj4b_ual_seleccion.json.
  Capturas: docs/captures/pj4b_muertes_getup.png.
python build_pj4b_ual_seleccion.py
"""

import json
import math
import os
import sys
import traceback

import bpy
from mathutils import Matrix, Quaternion, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
UAL1 = os.path.join(REPO, "animations", "ual", "ual1", "AnimationLibrary_Godot_Standard.glb")
UAL2 = os.path.join(REPO, "animations", "ual", "ual2", "UAL2_Standard.glb")
OUT1 = os.path.join(REPO, "animations", "ual", "sanador_ual1_seleccion.glb")
OUT2 = os.path.join(REPO, "animations", "ual", "sanador_ual2_seleccion.glb")
REPORT = os.path.join(REPO, "docs", "reports", "pj4b_ual_seleccion.json")
CAPTURE = os.path.join(REPO, "docs", "captures", "pj4b_muertes_getup.png")
FPS = 30

SEL1 = {"Death_A": "Death01", "Idle_Loop": "Idle_Loop", "Walk_Loop": "Walk_Loop",
        "Walk_Formal_Loop": "Walk_Formal_Loop", "Jog_Fwd_Loop": "Jog_Fwd_Loop", "Sprint_Loop": "Sprint_Loop",
        "Sitting_Enter": "Sitting_Enter", "Sitting_Idle_Loop": "Sitting_Idle_Loop", "Sitting_Exit": "Sitting_Exit",
        "Sitting_Talking_Loop": "Sitting_Talking_Loop", "Hit_Chest": "Hit_Chest", "Hit_Head": "Hit_Head",
        "Spell_Simple_Enter": "Spell_Simple_Enter", "Spell_Simple_Idle_Loop": "Spell_Simple_Idle_Loop",
        "Spell_Simple_Shoot": "Spell_Simple_Shoot", "Spell_Simple_Exit": "Spell_Simple_Exit"}
SEL2 = {"GetUp": "LayToIdle", "Consume": "Consume", "Yes": "Yes", "Idle_No-loop": "Idle_No_Loop",
        "Idle_FoldArms-loop": "Idle_FoldArms_Loop", "Chest_Open": "Chest_Open", "Hit_Knockback": "Hit_Knockback"}
# huesos equivalentes UAL1 -> UAL2 (para medir el enlace Death -> GetUp y, si hace falta, la transicion)
PAIRS = {"DEF-hips": "pelvis", "DEF-spine.001": "spine_01", "DEF-spine.002": "spine_02", "DEF-spine.003": "spine_03",
         "DEF-neck": "neck_01", "DEF-head": "Head"}
for s1, s2 in (("L", "l"), ("R", "r")):
    PAIRS.update({f"DEF-shoulder.{s1}": f"clavicle_{s2}", f"DEF-upper_arm.{s1}": f"upperarm_{s2}",
                  f"DEF-forearm.{s1}": f"lowerarm_{s2}", f"DEF-hand.{s1}": f"hand_{s2}",
                  f"DEF-thigh.{s1}": f"thigh_{s2}", f"DEF-shin.{s1}": f"calf_{s2}", f"DEF-foot.{s1}": f"foot_{s2}",
                  f"DEF-toe.{s1}": f"ball_{s2}"})
S = Matrix.Diagonal((-1, 1, 1, 1))


def import_glb(path):
    before = set(bpy.data.objects)
    acts_before = set(bpy.data.actions)
    bpy.ops.import_scene.gltf(filepath=path)
    new = [o for o in bpy.data.objects if o not in before]
    arm = next(o for o in new if o.type == "ARMATURE")
    acts = {a.name: a for a in bpy.data.actions if a not in acts_before}
    return arm, new, acts


def find_action(acts, name):
    """el importador glTF de Blender 4.5 deja cada animacion con su nombre exacto"""
    return acts[name]


def frames(act):
    a, b = act.frame_range
    return int(round(a)), int(round(b))


def mirror_name(n):
    if n.endswith(".L"):
        return n[:-2] + ".R"
    if n.endswith(".R"):
        return n[:-2] + ".L"
    return n


def set_action(arm, act):
    arm.animation_data_create()
    arm.animation_data.action = act
    if hasattr(arm.animation_data, "action_slot") and act.slots:
        arm.animation_data.action_slot = act.slots[0]


def world_mats(arm):
    return {pb.name: pb.matrix.copy() for pb in arm.pose.bones}


def ordered(arm):
    out = []

    def walk(b):
        out.append(b.name)
        for c in b.children:
            walk(c)
    for b in arm.data.bones:
        if b.parent is None:
            walk(b)
    return out


def key_all(arm, frame):
    for pb in arm.pose.bones:
        pb.rotation_mode = "QUATERNION"
        pb.keyframe_insert("rotation_quaternion", frame=frame, group=pb.name)
        pb.keyframe_insert("location", frame=frame, group=pb.name)


def mirror_action(arm, src, name, tweak):
    """Death_B: espejo de src fotograma a fotograma + ajustes locales (cabeza, brazos) que entran a partir del 30 %"""
    rest = {b.name: b.matrix_local.copy() for b in arm.data.bones}
    corr = {n: (S @ rest[mirror_name(n)] @ S).inverted() @ rest[n] for n in rest}
    f0, f1 = frames(src)
    poses = {}
    for f in range(f0, f1 + 1):
        set_action(arm, src)
        bpy.context.scene.frame_set(f)
        bpy.context.view_layer.update()
        poses[f] = world_mats(arm)
    act = bpy.data.actions.new(name)
    act.use_fake_user = True
    set_action(arm, act)
    order = ordered(arm)
    prev = {}
    for f in range(f0, f1 + 1):
        M = poses[f]
        for pb in arm.pose.bones:
            pb.matrix_basis = Matrix.Identity(4)
        bpy.context.view_layer.update()
        for n in order:
            pb = arm.pose.bones[n]
            pb.rotation_mode = "QUATERNION"
            pb.matrix = S @ M[mirror_name(n)] @ S @ corr[n]
            bpy.context.view_layer.update()
        t = (f - f0) / max(f1 - f0, 1)
        w = max(0.0, min(1.0, (t - 0.3) / 0.3))
        w = w * w * (3 - 2 * w)
        for bone, axis, deg in tweak:
            pb = arm.pose.bones[bone]
            pb.rotation_quaternion = pb.rotation_quaternion @ Quaternion(Vector(axis), math.radians(deg * w))
        for pb in arm.pose.bones:
            q = pb.rotation_quaternion.copy()
            if pb.name in prev:
                q.make_compatible(prev[pb.name])
            pb.rotation_quaternion = q
            prev[pb.name] = q.copy()
        key_all(arm, f)
    act.use_frame_range = True
    act.frame_start, act.frame_end = f0, f1
    return act


def joint_positions(arm, names):
    return {n: (arm.matrix_world @ arm.pose.bones[n].head).copy() for n in names}


def link_check(a1, act1, a2, act2):
    """posicion de las articulaciones equivalentes al final de act1 (UAL1) y al principio de act2 (UAL2)"""
    set_action(a1, act1)
    bpy.context.scene.frame_set(frames(act1)[1])
    set_action(a2, act2)
    bpy.context.scene.frame_set(frames(act2)[0])
    bpy.context.view_layer.update()
    # act1 se evalua en su ultimo fotograma y act2 en el primero: hay que evaluar cada una por separado
    set_action(a1, act1)
    bpy.context.scene.frame_set(frames(act1)[1])
    bpy.context.view_layer.update()
    p1 = joint_positions(a1, PAIRS.keys())
    set_action(a2, act2)
    bpy.context.scene.frame_set(frames(act2)[0])
    bpy.context.view_layer.update()
    p2 = joint_positions(a2, PAIRS.values())
    d = {k: (p1[k] - p2[v]).length for k, v in PAIRS.items()}
    # orientacion del cuerpo en el mundo: direccion de la columna (cadera -> pecho) y linea de caderas (izq. -> der.)
    def body(arm, hips, top, l, r):
        P = lambda n: arm.matrix_world @ arm.pose.bones[n].head  # noqa: E731
        return (P(top) - P(hips)).normalized(), (P(r) - P(l)).normalized()
    set_action(a1, act1)
    bpy.context.scene.frame_set(frames(act1)[1])
    bpy.context.view_layer.update()
    s1, l1 = body(a1, "DEF-hips", "DEF-spine.003", "DEF-thigh.L", "DEF-thigh.R")
    set_action(a2, act2)
    bpy.context.scene.frame_set(frames(act2)[0])
    bpy.context.view_layer.update()
    s2, l2 = body(a2, "pelvis", "spine_03", "thigh_l", "thigh_r")
    ang = max(math.degrees(s1.angle(s2)), math.degrees(l1.angle(l2)))
    return {"media_m": round(sum(d.values()) / len(d), 3), "max_m": round(max(d.values()), 3),
            "peor": max(d, key=d.get), "giro_del_cuerpo_grados": round(ang, 1),
            "desplazamiento_cadera_m": round(d["DEF-hips"], 3)}


def add_transition(a1, death, a2, getup_src, name, n=7):
    """GetUp con n fotogramas de transicion: el fotograma 1 copia (en el rig de la UAL2) la pose final de death y el
    LayToIdle original empieza en el fotograma 1 + n"""
    f0, f1 = frames(getup_src)
    act = getup_src.copy()
    act.name = name
    act.use_fake_user = True
    fcs = act.fcurves if hasattr(act, "fcurves") else []
    for fc in fcs:
        for kp in fc.keyframe_points:
            kp.co.x += n
            kp.handle_left.x += n
            kp.handle_right.x += n
    # pose de partida en el rig 2: giro de mundo de cada hueso de la UAL1 aplicado al reposo del hueso de la UAL2
    set_action(a1, death)
    bpy.context.scene.frame_set(frames(death)[1])
    bpy.context.view_layer.update()
    W1 = {k: a1.matrix_world @ a1.pose.bones[k].matrix for k in PAIRS}
    R1 = {k: a1.matrix_world @ a1.data.bones[k].matrix_local for k in PAIRS}
    set_action(a2, act)
    bpy.context.scene.frame_set(f0 + n)
    bpy.context.view_layer.update()
    inv2 = a2.matrix_world.inverted()
    for n2 in ordered(a2):
        k = next((k for k, v in PAIRS.items() if v == n2), None)
        if k is None:
            continue
        rot = (W1[k].to_3x3() @ R1[k].to_3x3().inverted())
        R2 = a2.matrix_world @ a2.data.bones[n2].matrix_local
        M = Matrix.Translation(W1[k].translation) @ (rot @ R2.to_3x3()).to_4x4()
        pb = a2.pose.bones[n2]
        pb.rotation_mode = "QUATERNION"
        pb.matrix = inv2 @ M
        bpy.context.view_layer.update()
    for pb in a2.pose.bones:
        pb.keyframe_insert("rotation_quaternion", frame=f0, group=pb.name)
        pb.keyframe_insert("location", frame=f0, group=pb.name)
    act.use_frame_range = True
    act.frame_start, act.frame_end = f0, f1 + n
    return act


def export(path, arm, meshes, names):
    arm.animation_data.action = None
    for t in list(arm.animation_data.nla_tracks):
        arm.animation_data.nla_tracks.remove(t)
    for final, act in names.items():
        tr = arm.animation_data.nla_tracks.new()
        tr.name = final
        st = tr.strips.new(final, int(act.frame_range[0]), act)
        if hasattr(st, "action_slot") and act.slots:
            st.action_slot = act.slots[0]
    for pb in arm.pose.bones:
        pb.matrix_basis = Matrix.Identity(4)
    for o in bpy.context.view_layer.objects:
        o.select_set(False)
    for o in [arm] + meshes:
        o.select_set(True)
    bpy.ops.export_scene.gltf(filepath=path, export_format="GLB", use_selection=True, export_yup=True,
                              export_apply=False, export_animations=True, export_animation_mode="NLA_TRACKS",
                              export_force_sampling=True, export_anim_slide_to_zero=True, export_skins=True)
    return round(os.path.getsize(path) / 1024, 1)


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.fps = FPS
    a1, objs1, acts1 = import_glb(UAL1)
    a2, objs2, acts2 = import_glb(UAL2)
    for o in objs2:
        if o.parent is None:
            o.location.x += 0.0
    rep = {"acciones_importadas": {"ual1": sorted(acts1), "ual2": sorted(acts2)}}
    src1 = {final: find_action(acts1, n) for final, n in SEL1.items()}
    src2 = {final: find_action(acts2, n) for final, n in SEL2.items()}
    death = src1["Death_A"]
    # Death_B: espejo + otro giro de cabeza (gira hacia el otro lado y se inclina) y los brazos en otra posicion
    tweak = [("DEF-head", (0, 1, 0), 28), ("DEF-neck", (1, 0, 0), -8),
             ("DEF-upper_arm.L", (1, 0, 0), 25), ("DEF-upper_arm.R", (0, 0, 1), -20),
             ("DEF-forearm.L", (1, 0, 0), 30), ("DEF-forearm.R", (1, 0, 0), -15)]
    death_b = mirror_action(a1, death, "Death_B", tweak)
    sel1 = dict(src1)
    sel1["Death_B"] = death_b
    # GetUp: enlace con el final de las muertes
    link_a = link_check(a1, death, a2, src2["GetUp"])
    link_b = link_check(a1, death_b, a2, src2["GetUp"])
    rep["enlace_death_a_getup"] = link_a
    rep["enlace_death_b_getup"] = link_b
    sel2 = dict(src2)
    if link_a["media_m"] > 0.08 or link_a["giro_del_cuerpo_grados"] > 15:
        sel2["GetUp"] = add_transition(a1, death, a2, src2["GetUp"], "GetUp", n=7)
        rep["getup_transicion_fotogramas"] = 7
        rep["enlace_death_a_getup_con_transicion"] = link_check(a1, death, a2, sel2["GetUp"])
    else:
        rep["getup_transicion_fotogramas"] = 0
    # GetUp_B: el mismo LayToIdle, con la transicion desde el final de Death_B (espejo): ninguna muerte salta
    sel2["GetUp_B"] = add_transition(a1, death_b, a2, src2["GetUp"], "GetUp_B", n=7)
    rep["enlace_death_b_getup_b_con_transicion"] = link_check(a1, death_b, a2, sel2["GetUp_B"])
    rep["ual1"] = {k: {"origen": SEL1.get(k, "espejo de Death01"), "duracion_s": round((frames(a)[1] - frames(a)[0]) / FPS, 3)}
                   for k, a in sel1.items()}
    rep["ual2"] = {k: {"origen": SEL2.get(k, "LayToIdle + transicion desde Death_B"), "duracion_s": round((frames(a)[1] - frames(a)[0]) / FPS, 3)}
                   for k, a in sel2.items()}
    print("ENLACE", json.dumps({"A": link_a, "B": link_b, "transicion": rep["getup_transicion_fotogramas"]}), flush=True)
    capture(sc, a1, objs1, a2, objs2, death, death_b, sel2["GetUp"])
    rep["glb"] = {"ual1": {"archivo": os.path.relpath(OUT1, REPO), "kb": export(OUT1, a1, [o for o in objs1 if o.type == "MESH"], sel1)},
                  "ual2": {"archivo": os.path.relpath(OUT2, REPO), "kb": export(OUT2, a2, [o for o in objs2 if o.type == "MESH"], sel2)}}
    json.dump(rep, open(REPORT, "w"), indent=1, ensure_ascii=False)
    print("GLB", json.dumps(rep["glb"]), flush=True)


def capture(sc, a1, objs1, a2, objs2, death_a, death_b, getup):
    import capture_pj1 as C1
    C1.setup(sc, res=(560, 420))
    sc.cycles.samples = 12
    bpy.ops.mesh.primitive_plane_add(size=8, location=(0, 0, 0))
    floor = bpy.context.active_object
    paths, labels = [], []

    def show(objs):
        for o in objs1 + objs2:
            if o.type == "MESH":
                o.hide_render = o not in objs
        floor.hide_render = False
    shots = [("Death_A final", a1, death_a, "last", objs1), ("Death_B final", a1, death_b, "last", objs1),
             ("Death_B 40 %", a1, death_b, 0.4, objs1), ("GetUp inicio", a2, getup, "first", objs2),
             ("GetUp 35 %", a2, getup, 0.35, objs2), ("GetUp final", a2, getup, "last", objs2)]
    for label, arm, act, when, objs in shots:
        set_action(arm, act)
        f0, f1 = frames(act)
        f = f1 if when == "last" else f0 if when == "first" else int(round(f0 + (f1 - f0) * when))
        sc.frame_set(f)
        bpy.context.view_layer.update()
        show(objs)
        c = C1.cam(sc, Vector((3.2, -3.2, 2.6)), Vector((0, 0, 0.45)), ortho=2.9)
        paths.append(C1.shot(sc, c, CAPTURE.replace(".png", f"_{len(paths)}.png")))
        labels.append(f"{label} (f{f})")
    C1.sheet(paths, CAPTURE, labels=labels, cols=3)
    print("CAPTURA", CAPTURE, flush=True)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        traceback.print_exc()
        sys.stdout.flush()
        os._exit(1)
    sys.stdout.flush()
    os._exit(0)
