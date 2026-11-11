"""
CONCORDIA - PJ3: esqueleto del elfo (concordia_rig.py) y pesos de cuerpo, ropa del Sanador y pelo.
Parte de blender/elfo_v02.blend (no se modifica) y guarda blender/elfo_v03.blend.
  rig      70 huesos (56 del SkeletonProfileHumanoid + 14 extra), 65 de deformacion, objeto sin transformacion
  pesos    cuerpo: automaticos (calor de huesos) sobre el cuerpo unido + limpieza de articulaciones + max. 4;
           ropa: transferencia desde el cuerpo; falda: solo piernas + Skirt_*; pelo: Head + Hair_*; ojos rigidos
  poses    10 poses de prueba como acciones (POSE_01_T ... POSE_10_Caido); la falda se coloca en cada pose
           apuntando sus cadenas por delante / detras de las piernas (como lo haria la simulacion de muelles)
  export   export/godot/pj_elfo_rig.glb (cuerpo + ojos + ropa + pelo + esqueleto + 10 poses)
python build_pj3_rig.py
"""

import json
import math
import os
import sys

import bpy
from mathutils import Matrix, Quaternion, Vector
from mathutils.bvhtree import BVHTree

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import concordia_rig as R  # noqa: E402

REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
SRC = os.path.join(REPO, "blender", "elfo_v02.blend")
DST = os.path.join(REPO, "blender", "elfo_v03.blend")
JOINTS = os.path.join(REPO, "docs", "reports", "pj1_elfo_articulaciones.json")
REPORT = os.path.join(REPO, "docs", "reports", "pj3_rig.json")
BODY = ("Head", "Torso", "Arms", "Hands", "Legs", "Feet")
CLOTHES = ("Robe_Top", "Robe_Skirt", "Hood", "Belt_Pouches", "Boots", "Bracers")

# ------------------------------------------------------------------------------------------------ poses
# (hueso, eje del mundo, grados) en orden de padre a hijo. Ejes: el elfo mira a -Y, izquierda = +X.
#   brazo izq. abajo: +Y; brazo der. abajo: -Y; muslo adelante: -X; rodilla (tibia atras): +X;
#   columna adelante: +X; codo izq. adelante (brazo en T): -Z; der.: +Z; brazo colgando adelante: -X
A_DOWN = lambda a: [("LeftUpperArm", "Y", a), ("RightUpperArm", "Y", -a)]  # noqa: E731
POSES = [
    ("01_T", []),
    ("02_A", A_DOWN(45)),
    ("03_Caminar", A_DOWN(72) + [
        ("Spine", "Z", 4), ("LeftUpperLeg", "X", -26), ("LeftLowerLeg", "X", 6), ("LeftFoot", "X", -14),
        ("RightUpperLeg", "X", 16), ("RightLowerLeg", "X", 24), ("RightFoot", "X", 12),
        ("RightUpperArm", "X", -20), ("LeftUpperArm", "X", 18), ("LeftLowerArm", "X", -12),
        ("RightLowerArm", "X", -22)]),
    ("04_Correr", A_DOWN(74) + [
        ("Spine", "X", 10), ("Chest", "X", 4), ("Head", "X", -10),
        ("LeftUpperLeg", "X", -55), ("LeftLowerLeg", "X", 70), ("LeftFoot", "X", -10),
        ("RightUpperLeg", "X", 25), ("RightLowerLeg", "X", 95), ("RightFoot", "X", 25),
        ("RightUpperArm", "X", -45), ("LeftUpperArm", "X", 35),
        ("LeftLowerArm", "X", -85), ("RightLowerArm", "X", -90)]),
    ("05_Sentado", A_DOWN(78) + [
        ("Spine", "X", 4), ("LeftUpperLeg", "X", -88), ("RightUpperLeg", "X", -88),
        ("LeftLowerLeg", "X", 88), ("RightLowerLeg", "X", 88),
        ("LeftUpperArm", "X", -28), ("RightUpperArm", "X", -28),
        ("LeftLowerArm", "X", -55), ("RightLowerArm", "X", -55)]),
    ("06_Hechizo", [
        ("Spine", "X", -6), ("Head", "X", -12), ("LeftShoulder", "Y", -16), ("RightShoulder", "Y", 16),
        ("LeftUpperArm", "Y", -36), ("LeftUpperArm", "Z", -32), ("RightUpperArm", "Y", 36),
        ("RightUpperArm", "Z", 32), ("LeftLowerArm", "Z", -18), ("RightLowerArm", "Z", 18),
        ("LeftHand", "Y", -15), ("RightHand", "Y", 15)]),
    ("07_Rodillas", A_DOWN(76) + [
        ("Spine", "X", 6), ("RightUpperLeg", "X", 2), ("RightLowerLeg", "X", 92), ("RightFoot", "X", 40),
        ("LeftUpperLeg", "X", -88), ("LeftLowerLeg", "X", 86),
        ("LeftUpperArm", "X", -30), ("LeftLowerArm", "X", -50)]),
    ("08_Agachado", A_DOWN(70) + [
        ("LeftUpperLeg", "X", -100), ("RightUpperLeg", "X", -100), ("LeftUpperLeg", "Y", 8),
        ("RightUpperLeg", "Y", -8), ("LeftLowerLeg", "X", 132), ("RightLowerLeg", "X", 132),
        ("LeftFoot", "X", -32), ("RightFoot", "X", -32), ("Spine", "X", 28), ("Chest", "X", 10),
        ("Head", "X", -25), ("LeftUpperArm", "X", -45), ("RightUpperArm", "X", -45),
        ("LeftLowerArm", "X", -40), ("RightLowerArm", "X", -40)]),
    ("09_Golpe", A_DOWN(50) + [
        ("Spine", "X", -16), ("Chest", "X", -10), ("Spine", "Y", 8), ("Head", "X", -18), ("Head", "Z", 15),
        ("LeftUpperArm", "Z", 35), ("RightUpperArm", "Z", -45), ("LeftLowerArm", "Z", -30),
        ("RightLowerArm", "Z", 40), ("RightUpperLeg", "X", 22), ("RightLowerLeg", "X", 18),
        ("LeftLowerLeg", "X", 14), ("LeftUpperLeg", "X", -8)]),
    ("10_Caido", A_DOWN(30) + [
        ("Root", "X", -90), ("LeftUpperLeg", "Y", 10), ("RightUpperLeg", "Y", -6),
        ("RightUpperLeg", "LOCALX", -25), ("RightLowerLeg", "LOCALX", 40), ("Head", "LOCALY", 28),
        ("LeftLowerArm", "LOCALX", -20)]),
]
AX = {"X": Vector((1, 0, 0)), "Y": Vector((0, 1, 0)), "Z": Vector((0, 0, 1))}


def rot_world(arm, bone, axis, deg):
    pb = arm.pose.bones[bone]
    if axis.startswith("LOCAL"):
        ax = (pb.matrix.to_3x3() @ AX[axis[-1]]).normalized()
    else:
        ax = AX[axis]
    h = pb.head.copy()
    q = Quaternion(ax, math.radians(deg))
    pb.rotation_mode = "QUATERNION"
    pb.matrix = Matrix.Translation(h) @ q.to_matrix().to_4x4() @ Matrix.Translation(-h) @ pb.matrix
    bpy.context.view_layer.update()


def aim(arm, bone, target):
    pb = arm.pose.bones[bone]
    y = (pb.tail - pb.head).normalized()
    t = (Vector(target) - pb.head)
    if t.length < 1e-6:
        return
    q = y.rotation_difference(t.normalized())
    h = pb.head.copy()
    pb.matrix = Matrix.Translation(h) @ q.to_matrix().to_4x4() @ Matrix.Translation(-h) @ pb.matrix
    bpy.context.view_layer.update()


def eval_min_z(objs):
    dg = bpy.context.evaluated_depsgraph_get()
    zmin = 1e9
    for o in objs:
        ev = o.evaluated_get(dg)
        me = ev.to_mesh()
        for v in me.vertices:
            zmin = min(zmin, (ev.matrix_world @ v.co).z)
        ev.to_mesh_clear()
    return zmin


def fit_skirt(arm):
    """Cadenas de la falda (lo que hara SpringBoneSimulator3D con colisionadores en las piernas): si la rodilla o el
    tobillo mas adelantados (o mas retrasados, para el panel trasero) salen del vuelo de la falda, la cadena se tiende
    por un camino que pasa por delante de esa rodilla y de ese tobillo; si no, cuelga como en reposo."""
    hips = arm.pose.bones["Hips"]
    rh = (hips.matrix.to_3x3() @ hips.bone.matrix_local.to_3x3().inverted())
    fwd = (rh @ Vector((0, -1, 0))).normalized()
    down = (rh @ Vector((0, 0, -1))).normalized()
    h0 = hips.head.copy()
    knees = [arm.pose.bones[f"{s}LowerLeg"].head.copy() for s in ("Left", "Right")]
    ankles = [arm.pose.bones[f"{s}Foot"].head.copy() for s in ("Left", "Right")]
    res = {}
    for side, sg, rest_off in (("Front", 1, 0.06), ("Back", -1, 0.09)):
        k = max(knees, key=lambda p: sg * (p - h0).dot(fwd))
        a = max(ankles, key=lambda p: sg * (p - h0).dot(fwd))
        pk, pa = sg * (k - h0).dot(fwd), sg * (a - h0).dot(fwd)
        res[side] = {"rodilla_m": round(pk, 3), "tobillo_m": round(pa, 3)}
        if pk < rest_off and pa < rest_off + 0.04:
            continue
        k_t = k + fwd * sg * 0.10 - down * 0.02
        a_t = a + fwd * sg * 0.085
        b1 = arm.pose.bones[f"Skirt_{side}_01"]
        path = [b1.head.copy(), k_t, a_t, a_t + (a_t - k_t).normalized() * 1.0]
        seg = [(path[i], path[i + 1]) for i in range(3)]

        def at(dist):
            for p0, p1 in seg:
                L = (p1 - p0).length
                if dist <= L:
                    return p0 + (p1 - p0) * (dist / L)
                dist -= L
            return seg[-1][1]
        acc = 0.0
        for n in range(1, 4):
            pb = arm.pose.bones[f"Skirt_{side}_{n:02d}"]
            acc += pb.bone.length
            aim(arm, pb.name, at(acc))
        res[side]["tendida"] = True
    return res


def rot_axis(arm, bone, ax, deg):
    pb = arm.pose.bones[bone]
    h = pb.head.copy()
    q = Quaternion(ax, math.radians(deg))
    pb.rotation_mode = "QUATERNION"
    pb.matrix = Matrix.Translation(h) @ q.to_matrix().to_4x4() @ Matrix.Translation(-h) @ pb.matrix
    bpy.context.view_layer.update()


def apply_pose(arm, spec, body_objs):
    for pb in arm.pose.bones:
        pb.matrix_basis = Matrix.Identity(4)
    bpy.context.view_layer.update()
    for b, ax, d in spec:
        rot_world(arm, b, ax, d)
    info = fit_skirt(arm)
    z = eval_min_z(body_objs)
    root = arm.pose.bones["Root"]
    root.matrix = Matrix.Translation((0, 0, -z)) @ root.matrix
    bpy.context.view_layer.update()
    return info


def keyframe_pose(arm, name):
    act = bpy.data.actions.new(f"POSE_{name}")
    arm.animation_data_create()
    arm.animation_data.action = act
    for pb in arm.pose.bones:
        pb.rotation_mode = "QUATERNION"
        pb.keyframe_insert("rotation_quaternion", frame=1)
        pb.keyframe_insert("location", frame=1)
    act.use_fake_user = True
    return act


def penetration(skirt, legs_objs):
    """Vertices de la falda dentro de las piernas o las botas (posados), con las piernas completas (sin las
    mascaras HIDE_*: una malla abierta engana a la prueba dentro/fuera)."""
    import bmesh
    dg = bpy.context.evaluated_depsgraph_get()
    bm = bmesh.new()
    for o in legs_objs:
        ev = o.evaluated_get(dg)
        me = ev.to_mesh()
        me.transform(ev.matrix_world)
        bm.from_mesh(me)
        ev.to_mesh_clear()
    bm.normal_update()
    tree = BVHTree.FromBMesh(bm)
    bm.free()
    ev = skirt.evaluated_get(dg)
    me = ev.to_mesh()
    n = 0
    worst = 0.0
    for v in me.vertices:
        p = ev.matrix_world @ v.co
        loc, nrm, _i, d = tree.find_nearest(p, 0.03)
        if loc is not None and (p - loc).dot(nrm) < -0.002:
            n += 1
            worst = max(worst, d)
    ev.to_mesh_clear()
    return n, round(worst, 4)


def leg_probes(objs, arm):
    """Copias de piernas, pies y botas solo con el Armature (sin mascaras) para medir la falda."""
    out = []
    for o in objs:
        c = o.copy()
        c.data = o.data.copy()
        c.name = "TMP_probe_" + o.name
        for m in list(c.modifiers):
            if m.type != "ARMATURE":
                c.modifiers.remove(m)
        if c.animation_data:
            c.animation_data_clear()
        c.hide_render = True
        bpy.context.scene.collection.objects.link(c)
        out.append(c)
    return out


def skirt_weights(skirt, arm):
    """Falda: solo muslos (arriba) y cadenas Skirt_* (abajo). Panel por el signo de y respecto al centro."""
    hips = arm.data.bones["Hips"]
    cy = hips.head_local.y
    z_top = max(v.co.z for v in skirt.data.vertices)
    z_hem = min(v.co.z for v in skirt.data.vertices)
    W = []
    for v in skirt.data.vertices:
        c = v.co
        h = (z_top - c.z) / (z_top - z_hem)
        side = "Front" if c.y < cy else "Back"
        wl = R.smoothstep(-0.07, 0.07, c.x)
        w_leg = max(0.0, 1.0 - h * 3.2)
        w = {}
        if w_leg > 0:
            w["LeftUpperLeg"] = w_leg * wl
            w["RightUpperLeg"] = w_leg * (1 - wl)
        rest = 1.0 - w_leg
        s = h * 3
        mids = [0.5, 1.5, 2.5]
        hats = [max(0.0, 1.0 - abs(s - m)) for m in mids]
        if s <= 0.5:
            hats = [1.0, 0, 0]
        if s >= 2.5:
            hats = [0, 0, 1.0]
        tot = sum(hats) or 1.0
        for k in range(3):
            if hats[k] > 0:
                w[f"Skirt_{side}_{k + 1:02d}"] = rest * hats[k] / tot
        W.append(w)
    R.set_weights(skirt, R.limit_normalize(W, 4))


def hair_weights(hair, arm):
    bones = [arm.data.bones[f"Hair_{k:02d}"] for k in range(1, 5)]
    cls = hair.data.attributes["cls"].data
    braid_v = set()
    for p in hair.data.polygons:
        if cls[p.index].value in (11, 10):                # trenza y atadura
            braid_v.update(p.vertices)
    W = []
    for v in hair.data.vertices:
        c = v.co
        if v.index not in braid_v and c.z > bones[0].head_local.z - 0.03:
            W.append({"Head": 1.0})
            continue
        # posicion a lo largo de la cadena
        best = []
        for b in bones:
            a, t = b.head_local, b.tail_local
            d = t - a
            u = max(0.0, min(1.0, (c - a).dot(d) / d.length_squared))
            best.append(((a + d * u - c).length, b.name, u))
        best.sort()
        d0, n0, u0 = best[0]
        w = {n0: 1.0}
        k = int(n0[-2:])
        if u0 < 0.25 and k > 1:
            f = (0.25 - u0) / 0.5
            w = {n0: 1 - f, f"Hair_{k - 1:02d}": f}
        elif u0 > 0.75 and k < 4:
            f = (u0 - 0.75) / 0.5
            w = {n0: 1 - f, f"Hair_{k + 1:02d}": f}
        if k == 1 and u0 < 0.2:
            w = {"Head": 0.5, n0: 0.5}
        W.append(w)
    R.set_weights(hair, R.limit_normalize(W, 4))


def belt_weights(belt):
    W = []
    for v in belt.data.vertices:
        c = v.co
        if c.z < 1.04:                     # bolsitas y frascos colgando: algo de muslo del lado
            leg = "LeftUpperLeg" if c.x > 0 else "RightUpperLeg"
            W.append({"Hips": 0.75, leg: 0.25})
        else:
            W.append({"Hips": 0.85, "Spine": 0.15})
    R.set_weights(belt, W)


def main():
    bpy.ops.wm.open_mainfile(filepath=SRC)
    J = json.load(open(JOINTS))["articulaciones"]
    parts = {k: bpy.data.objects[f"PJ_Elfo_{k}"] for k in BODY}
    eyes = bpy.data.objects["PJ_Elfo_Eyes"]
    clothes = {k: bpy.data.objects[k] for k in CLOTHES}
    hair = bpy.data.objects["Hair_Elf"]
    rep = {}
    # posiciones de los huesos extra desde la geometria
    extra = {}
    cls = hair.data.attributes["cls"].data
    bv = sorted({v for p in hair.data.polygons if cls[p.index].value == 11 for v in p.vertices},
                key=lambda i: -hair.data.vertices[i].co.z)
    pts = [hair.data.vertices[i].co for i in bv]
    ztop, zbot = pts[0].z, pts[-1].z

    def braid_at(z):
        near = [p for p in pts if abs(p.z - z) < 0.03] or [min(pts, key=lambda p: abs(p.z - z))]
        return sum(near, Vector()) / len(near)
    zs = [ztop + (zbot - ztop) * k / 4 for k in range(5)]
    hp = [braid_at(z) for z in zs]
    hp[0] = Vector((0, hp[0].y - 0.01, ztop + 0.01))
    for k in range(4):
        extra[f"Hair_{k + 1:02d}"] = (hp[k], hp[k + 1])
    sk = clothes["Robe_Skirt"].data
    z_top = max(v.co.z for v in sk.vertices)
    z_hem = min(v.co.z for v in sk.vertices)
    for side, sign in (("Front", -1), ("Back", 1)):
        chain = []
        for k in range(4):
            z = z_top + (z_hem - z_top) * k / 3
            band = [v.co for v in sk.vertices if abs(v.co.z - z) < 0.06 and abs(v.co.x) < 0.06]
            y = (min if sign < 0 else max)(c.y for c in band)
            chain.append(Vector((0, y - sign * 0.03, z)))
        for k in range(3):
            extra[f"Skirt_{side}_{k + 1:02d}"] = (chain[k], chain[k + 1])
    torso_back = max(v.co.y for v in parts["Torso"].data.vertices if abs(v.co.x) < 0.04 and abs(v.co.z - 1.4) < 0.04)
    extra["Back_Slot"] = (Vector((0, torso_back + 0.06, 1.40)), Vector((0, torso_back + 0.06, 1.50)))
    top = max(v.co.z for v in parts["Head"].data.vertices)
    extra["Head_Top"] = (Vector((0, -0.03, top + 0.01)), Vector((0, -0.03, top + 0.09)))
    pos = R.mpfb_positions(J, extra)
    col = bpy.data.collections.new("PJ_RIG")
    bpy.context.scene.collection.children.link(col)
    arm = R.build(pos, "PJ_Elfo_Rig", col)
    rep["convencion"] = R.check_convention(arm)
    rep["huesos"] = [{"nombre": b.name, "padre": b.parent.name if b.parent else None, "deforma": b.use_deform,
                      "perfil_godot": b.name in dict(R.PROFILE)} for b in arm.data.bones]
    print("RIG", json.dumps(rep["convencion"]), flush=True)
    # pesos del cuerpo: automaticos + limpieza
    body = R.auto_weights([parts[k] for k in BODY], arm)
    rep["pesos_auto_grupos"] = len(body.vertex_groups)
    rep["limpieza"] = R.clean_joints(body, arm)
    rep["costuras_dist_max"] = R.copy_weights_to_parts(body, [parts[k] for k in BODY])
    # ojos rigidos
    R.set_weights(eyes, [{"LeftEye" if v.co.x > 0 else "RightEye": 1.0} for v in eyes.data.vertices])
    # ropa
    deform = [b.name for b in arm.data.bones if b.use_deform and not b.name.startswith(("Hair_", "Skirt_"))]
    for k in ("Robe_Top", "Hood", "Boots", "Bracers"):
        R.transfer_from(body, clothes[k], only=set(deform) - {"LeftEye", "RightEye", "Jaw"})
    belt_weights(clothes["Belt_Pouches"])
    skirt_weights(clothes["Robe_Skirt"], arm)
    hair_weights(hair, arm)
    for o in list(parts.values()) + [eyes] + list(clothes.values()) + [hair]:
        R.bind(o, arm)
    rep["pesos"] = R.stats(list(parts.values()) + [eyes] + list(clothes.values()) + [hair])
    bpy.data.objects.remove(body, do_unlink=True)
    print("PESOS", json.dumps(rep["pesos"]), json.dumps(rep["limpieza"]), flush=True)
    # poses de prueba (acciones) y penetracion de la falda
    ground = [parts[k] for k in BODY] + [clothes["Boots"]]
    legs = leg_probes([parts["Legs"], parts["Feet"], clothes["Boots"]], arm)
    rep["poses"] = {}
    for name, spec in POSES:
        info = apply_pose(arm, spec, ground)
        keyframe_pose(arm, name)
        n, w = penetration(clothes["Robe_Skirt"], legs)
        rep["poses"][name] = {"falda_vertices_dentro_de_piernas": n, "falda_penetracion_max_m": w, **info}
        print("POSE", name, n, w, flush=True)
    for c in legs:
        bpy.data.objects.remove(c, do_unlink=True)
    arm.animation_data.action = bpy.data.actions["POSE_01_T"]
    for pb in arm.pose.bones:
        pb.matrix_basis = Matrix.Identity(4)
    tris = {}
    for o in list(parts.values()) + [eyes] + list(clothes.values()) + [hair]:
        tris[o.name] = sum(len(p.vertices) - 2 for p in o.data.polygons)
    rep["tris"] = tris
    rep["tris_total"] = sum(tris.values())
    bpy.context.scene["pj3_datos"] = json.dumps({"poses": [p[0] for p in POSES]})
    bpy.ops.wm.save_as_mainfile(filepath=DST)
    # export: cuerpo completo (las mascaras HIDE_* se silencian solo durante la exportacion; en Godot la ropa se
    # pone y se quita en tiempo de juego)
    muted = []
    for o in parts.values():
        if o.animation_data:
            for fc in o.animation_data.drivers:
                if fc.data_path.startswith("modifiers[") and not fc.mute:
                    fc.mute = True
                    muted.append(fc)
        for m in o.modifiers:
            if m.type == "MASK":
                m.show_viewport = m.show_render = False
    bpy.context.view_layer.update()
    gl = os.path.join(REPO, "export", "godot", "pj_elfo_rig.glb")
    for o in bpy.context.view_layer.objects:
        o.select_set(False)
    for o in [arm] + list(parts.values()) + [eyes] + list(clothes.values()) + [hair]:
        o.select_set(True)
    bpy.ops.export_scene.gltf(filepath=gl, export_format="GLB", use_selection=True, export_yup=True,
                              export_apply=True, export_extras=True, export_image_format="AUTO",
                              export_vertex_color="NONE", export_animations=True,
                              export_animation_mode="ACTIONS", export_force_sampling=True)
    for fc in muted:
        fc.mute = False
    rep["glb"] = {"archivo": os.path.relpath(gl, REPO), "kb": round(os.path.getsize(gl) / 1024, 1)}
    with open(REPORT, "w") as fh:
        json.dump(rep, fh, indent=1, ensure_ascii=False)
    print("GLB", json.dumps(rep["glb"]), flush=True)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        import traceback
        traceback.print_exc()
        sys.stdout.flush()
        os._exit(1)
    sys.stdout.flush()
    os._exit(0)
