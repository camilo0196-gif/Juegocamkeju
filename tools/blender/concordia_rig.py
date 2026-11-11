"""
CONCORDIA - esqueleto comun de todas las razas (SkeletonProfileHumanoid de Godot 4.7, 56 huesos, verificado en
https://docs.godotengine.org/en/stable/classes/class_skeletonprofilehumanoid.html y scene/resources/
skeleton_profile.cpp) + huesos extra sin mapear (Godot los ignora al retargetear):
  Weapon_R / Weapon_L (ranuras en las manos), Back_Slot (espalda), Head_Top (efectos)   -> sin deformacion
  Hair_01..04 (trenza), Skirt_Front_01..03 y Skirt_Back_01..03 (dobladillo, SpringBoneSimulator3D) -> deforman
Root no deforma: 70 huesos, 65 de deformacion.

Convencion: pose T, de cara a -Y, objeto armature sin transformacion (rotacion 0, escala 1); la cola de cada hueso
es la cabeza de su hijo (o del hijo designado en el perfil: Hips->Spine, UpperChest->Neck, Hand->MiddleProximal,
Foot->Toes), asi el +Y local apunta al hijo. Roll: el Z local hacia delante (-Y) salvo en huesos que ya apuntan
hacia delante (pies, dedos del pie, ojos, mandibula, ranuras), cuyo Z mira hacia arriba (+Z).

build(joints, extra, name)        crea el armature desde articulaciones (cabeza, cola) en metros
auto_weights(body_parts, arm)     pesos automaticos (calor de huesos) sobre el cuerpo unido, devueltos por pieza
clean_joints(...)                 limpieza en hombros, codos, munecas, cadera, rodillas y tobillos
limit_normalize(obj, 4)           max. 4 influencias por vertice y suma 1
"""

import math

import bmesh
import bpy
from mathutils import Vector
from mathutils.kdtree import KDTree

PROFILE = [  # (nombre, padre) en el orden del perfil de Godot
    ("Root", None), ("Hips", "Root"), ("Spine", "Hips"), ("Chest", "Spine"), ("UpperChest", "Chest"),
    ("Neck", "UpperChest"), ("Head", "Neck"), ("LeftEye", "Head"), ("RightEye", "Head"), ("Jaw", "Head")]
for S in ("Left", "Right"):
    PROFILE += [(f"{S}Shoulder", "UpperChest"), (f"{S}UpperArm", f"{S}Shoulder"), (f"{S}LowerArm", f"{S}UpperArm"),
                (f"{S}Hand", f"{S}LowerArm"), (f"{S}ThumbMetacarpal", f"{S}Hand"),
                (f"{S}ThumbProximal", f"{S}ThumbMetacarpal"), (f"{S}ThumbDistal", f"{S}ThumbProximal")]
    for F in ("Index", "Middle", "Ring", "Little"):
        PROFILE += [(f"{S}{F}Proximal", f"{S}Hand"), (f"{S}{F}Intermediate", f"{S}{F}Proximal"),
                    (f"{S}{F}Distal", f"{S}{F}Intermediate")]
for S in ("Left", "Right"):
    PROFILE += [(f"{S}UpperLeg", "Hips"), (f"{S}LowerLeg", f"{S}UpperLeg"), (f"{S}Foot", f"{S}LowerLeg"),
                (f"{S}Toes", f"{S}Foot")]
assert len(PROFILE) == 56
EXTRA = [("Weapon_R", "RightHand", False), ("Weapon_L", "LeftHand", False), ("Back_Slot", "UpperChest", False),
         ("Head_Top", "Head", False), ("Hair_01", "Head", True), ("Hair_02", "Hair_01", True),
         ("Hair_03", "Hair_02", True), ("Hair_04", "Hair_03", True)]
for P_ in ("Front", "Back"):
    EXTRA += [(f"Skirt_{P_}_01", "Hips", True), (f"Skirt_{P_}_02", f"Skirt_{P_}_01", True),
              (f"Skirt_{P_}_03", f"Skirt_{P_}_02", True)]
NON_DEFORM = {"Root", "Weapon_R", "Weapon_L", "Back_Slot", "Head_Top"}
FORWARD_BONES = ("Foot", "Toes", "Eye", "Jaw", "Weapon", "Head_Top", "Back_Slot")
# huesos que la limpieza / los pesos automaticos no deben recibir del calor (se pesan aparte)
NO_HEAT = ("Hair_", "Skirt_", "LeftEye", "RightEye", "Jaw")


def mpfb_positions(J, extra):
    """Cabeza / cola de cada hueso de Godot desde las articulaciones del rig 'default' de MPFB (pose T)."""
    V = lambda n, k=0: Vector(J[n][k])  # noqa: E731
    pos = {}
    pos["Root"] = (Vector((0, 0, 0)), Vector((0, 0, 0.12)))
    hip_y = (V("upperleg01.L").y + V("upperleg01.R").y) / 2
    hips = Vector((0, hip_y, V("upperleg01.L").z - 0.03))
    pos["Hips"] = (hips, V("spine04"))
    pos["Spine"] = (V("spine04"), V("spine02"))
    pos["Chest"] = (V("spine02"), V("spine01"))
    pos["UpperChest"] = (V("spine01"), V("neck01"))
    pos["Neck"] = (V("neck01"), V("head"))
    pos["Head"] = (V("head"), V("head", 1))
    pos["Jaw"] = (V("jaw"), V("jaw", 1))
    for S, s in (("Left", "L"), ("Right", "R")):
        pos[f"{S}Eye"] = (V(f"eye.{s}"), V(f"eye.{s}") + Vector((0, -0.03, 0)))
        pos[f"{S}Shoulder"] = (V(f"clavicle.{s}"), V(f"upperarm01.{s}"))
        pos[f"{S}UpperArm"] = (V(f"upperarm01.{s}"), V(f"lowerarm01.{s}"))
        pos[f"{S}LowerArm"] = (V(f"lowerarm01.{s}"), V(f"wrist.{s}"))
        pos[f"{S}Hand"] = (V(f"wrist.{s}"), V(f"finger3-1.{s}"))
        for F, k in (("Thumb", 1), ("Index", 2), ("Middle", 3), ("Ring", 4), ("Little", 5)):
            names = ("Metacarpal", "Proximal", "Distal") if F == "Thumb" else ("Proximal", "Intermediate", "Distal")
            for i, nm in enumerate(names):
                pos[f"{S}{F}{nm}"] = (V(f"finger{k}-{i + 1}.{s}"), V(f"finger{k}-{i + 1}.{s}", 1))
        pos[f"{S}UpperLeg"] = (V(f"upperleg01.{s}"), V(f"lowerleg01.{s}"))
        pos[f"{S}LowerLeg"] = (V(f"lowerleg01.{s}"), V(f"foot.{s}"))
        pos[f"{S}Foot"] = (V(f"foot.{s}"), V(f"toe3-1.{s}"))
        pos[f"{S}Toes"] = (V(f"toe3-1.{s}"), V(f"toe3-3.{s}", 1))
        palm = (V(f"wrist.{s}") + V(f"finger3-1.{s}")) / 2 + Vector((0, 0, -0.022))
        pos[f"Weapon_{s}"] = (palm, palm + Vector((0, -0.10, 0)))
    pos.update(extra)
    return pos


def build(pos, name="PJ_Rig", col=None):
    arm_data = bpy.data.armatures.new(name)
    arm_data.display_type = "STICK"
    arm = bpy.data.objects.new(name, arm_data)
    (col or bpy.context.scene.collection).objects.link(arm)
    for o in bpy.context.view_layer.objects:
        o.select_set(False)
    bpy.context.view_layer.objects.active = arm
    arm.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")
    eb = arm_data.edit_bones
    for nm, par in PROFILE + [(e[0], e[1]) for e in EXTRA]:
        b = eb.new(nm)
        h, t = pos[nm]
        b.head, b.tail = Vector(h), Vector(t)
        if par:
            b.parent = eb[par]
        d = (b.tail - b.head).normalized()
        if any(k in nm for k in FORWARD_BONES) and abs(d.y) > 0.5:
            b.align_roll(Vector((0, 0, 1)))
        else:
            b.align_roll(Vector((0, -1, 0)))
        b.use_connect = False
        b.use_deform = nm not in NON_DEFORM
    bpy.ops.object.mode_set(mode="OBJECT")
    return arm


def check_convention(arm):
    """+Y del hueso hacia el hijo designado (angulo), transformacion del objeto y numero de huesos."""
    designated = {"Hips": "Spine", "UpperChest": "Neck", "LeftHand": "LeftMiddleProximal",
                  "RightHand": "RightMiddleProximal", "Root": "Hips"}
    worst, n = 0.0, 0
    for b in arm.data.bones:
        kids = list(b.children)
        if not kids:
            continue
        tgt = designated.get(b.name)
        ch = next((c for c in kids if c.name == tgt), None) if tgt else (kids[0] if len(kids) == 1 else None)
        if ch is None:
            continue
        y = (b.tail_local - b.head_local).normalized()
        to = ch.head_local - b.head_local
        if to.length < 1e-6:
            continue
        worst = max(worst, math.degrees(y.angle(to.normalized())))
        n += 1
    mw = arm.matrix_world
    return {"huesos": len(arm.data.bones), "deformacion": sum(1 for b in arm.data.bones if b.use_deform),
            "angulo_max_y_hacia_hijo_grados": round(worst, 4), "pares_comprobados": n,
            "objeto_identidad": mw == mw.Identity(4)}


def join_copies(parts, name):
    objs = []
    for o in parts:
        c = o.copy()
        c.data = o.data.copy()
        c.modifiers.clear()
        bpy.context.scene.collection.objects.link(c)
        objs.append(c)
    for o in bpy.context.view_layer.objects:
        o.select_set(False)
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.join()
    j = objs[0]
    j.name = name
    bm = bmesh.new()
    bm.from_mesh(j.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    bm.to_mesh(j.data)
    bm.free()
    for g in list(j.vertex_groups):
        j.vertex_groups.remove(g)
    return j


def auto_weights(parts, arm):
    """Calor de huesos (pesos automaticos de Blender) sobre el cuerpo unido sin costuras, sin los huesos que se pesan
    aparte (pelo, falda, ojos, mandibula)."""
    body = join_copies(parts, "TMP_RigBody")
    saved = {}
    for b in arm.data.bones:
        saved[b.name] = b.use_deform
        if b.name.startswith(NO_HEAT):
            b.use_deform = False
    for o in bpy.context.view_layer.objects:
        o.select_set(False)
    body.select_set(True)
    arm.select_set(True)
    bpy.context.view_layer.objects.active = arm
    bpy.ops.object.parent_set(type="ARMATURE_AUTO")
    for b in arm.data.bones:
        b.use_deform = saved[b.name]
    body.parent = None
    for m in list(body.modifiers):
        body.modifiers.remove(m)
    return body


def weights_of(o):
    names = {g.index: g.name for g in o.vertex_groups}
    return [{names[e.group]: e.weight for e in v.groups if e.weight > 1e-5} for v in o.data.vertices]


def set_weights(o, W, clear=True):
    if clear:
        for g in list(o.vertex_groups):
            if not g.name.startswith("HIDE_"):
                o.vertex_groups.remove(g)
    groups = {}
    for i, w in enumerate(W):
        for n, x in w.items():
            if n not in groups:
                groups[n] = o.vertex_groups.get(n) or o.vertex_groups.new(name=n)
            groups[n].add([i], x, "REPLACE")


def limit_normalize(W, k=4):
    out = []
    for w in W:
        top = sorted(w.items(), key=lambda t: -t[1])[:k]
        s = sum(x for _n, x in top)
        out.append({n: x / s for n, x in top} if s > 1e-8 else {})
    return out


def smoothstep(a, b, x):
    t = max(0.0, min(1.0, (x - a) / (b - a)))
    return t * t * (3 - 2 * t)


def joint_blend(co, W, arm, parent, child, width, radius):
    """Codos, rodillas, munecas, tobillos: en la zona de la articulacion los pesos de padre e hijo se rehacen como
    una transicion suave a lo largo del eje del hijo (sin aplastar el volumen)."""
    bc = arm.data.bones[child]
    J = bc.head_local
    d = (bc.tail_local - bc.head_local).normalized()
    n = 0
    for i, c in enumerate(co):
        r = c - J
        t = r.dot(d)
        if abs(t) > width * 1.6:
            continue
        if (r - d * t).length > radius:
            continue
        w = W[i]
        pair = w.get(parent, 0.0) + w.get(child, 0.0)
        if pair < 0.5:
            continue
        s = smoothstep(-width, width, t)
        w[parent], w[child] = pair * (1 - s), pair * s
        n += 1
    return n


def region_smooth(co, W, adj, center, radius, bones, iters=6, k=0.5):
    """Hombros y cadera: suavizado de los pesos de 'bones' entre vecinos dentro de la esfera (quita picos)."""
    ids = [i for i, c in enumerate(co) if (c - center).length < radius]
    for _ in range(iters):
        new = {}
        for i in ids:
            nb = adj[i]
            if not nb:
                continue
            avg = {b: sum(W[j].get(b, 0.0) for j in nb) / len(nb) for b in bones}
            new[i] = {b: W[i].get(b, 0.0) * (1 - k) + avg[b] * k for b in bones}
        for i, ws in new.items():
            rest = 1.0 - sum(W[i].get(b, 0.0) for b in bones)
            for b, x in ws.items():
                W[i][b] = x
            tot = sum(ws.values())
            if tot > 1e-6 and rest < 1.0:
                sc = (1.0 - max(rest, 0.0)) / tot
                for b in bones:
                    W[i][b] *= sc
    return len(ids)


def clean_joints(body, arm):
    co = [v.co.copy() for v in body.data.vertices]
    adj = {i: [] for i in range(len(co))}
    for e in body.data.edges:
        a, b = e.vertices
        adj[a].append(b)
        adj[b].append(a)
    W = weights_of(body)
    rep = {}
    for S in ("Left", "Right"):
        rep[f"codo_{S}"] = joint_blend(co, W, arm, f"{S}UpperArm", f"{S}LowerArm", 0.045, 0.07)
        rep[f"muneca_{S}"] = joint_blend(co, W, arm, f"{S}LowerArm", f"{S}Hand", 0.025, 0.05)
        rep[f"rodilla_{S}"] = joint_blend(co, W, arm, f"{S}UpperLeg", f"{S}LowerLeg", 0.055, 0.09)
        rep[f"tobillo_{S}"] = joint_blend(co, W, arm, f"{S}LowerLeg", f"{S}Foot", 0.035, 0.07)
        sh = arm.data.bones[f"{S}UpperArm"].head_local
        rep[f"hombro_{S}"] = region_smooth(co, W, adj, sh, 0.15,
                                           ["UpperChest", "Chest", f"{S}Shoulder", f"{S}UpperArm"], iters=14)
        hp = arm.data.bones[f"{S}UpperLeg"].head_local
        rep[f"cadera_{S}"] = region_smooth(co, W, adj, hp, 0.17, ["Hips", "Spine", f"{S}UpperLeg"], iters=14)
    W = limit_normalize(W, 4)
    set_weights(body, W)
    return rep


def copy_weights_to_parts(body, parts):
    """Pesos del cuerpo unido a cada pieza por coincidencia exacta de vertices (costuras con los mismos pesos)."""
    kd = KDTree(len(body.data.vertices))
    for v in body.data.vertices:
        kd.insert(v.co, v.index)
    kd.balance()
    W = weights_of(body)
    worst = 0.0
    for o in parts:
        Wp = []
        for v in o.data.vertices:
            _c, i, d = kd.find(o.matrix_world @ v.co)
            worst = max(worst, d)
            Wp.append(dict(W[i]))
        set_weights(o, Wp)
    return worst


def transfer_from(body, target, only=None, mapping="POLYINTERP_NEAREST"):
    """Pesos del cuerpo a una prenda (transferencia por cara mas cercana) y luego limite 4 + normalizado."""
    for g in list(target.vertex_groups):
        if not g.name.startswith("HIDE_"):
            target.vertex_groups.remove(g)
    for g in body.vertex_groups:
        if only is None or g.name in only:
            target.vertex_groups.new(name=g.name)
    m = target.modifiers.new("DT", "DATA_TRANSFER")
    m.object = body
    m.use_vert_data = True
    m.data_types_verts = {"VGROUP_WEIGHTS"}
    m.vert_mapping = mapping
    m.layers_vgroup_select_src = "ALL"
    m.layers_vgroup_select_dst = "NAME"
    for o in bpy.context.view_layer.objects:
        o.select_set(False)
    bpy.context.view_layer.objects.active = target
    target.select_set(True)
    bpy.ops.object.modifier_move_to_index(modifier=m.name, index=0)
    bpy.ops.object.modifier_apply(modifier=m.name)
    W = limit_normalize(weights_of(target), 4)
    if only is not None:
        W = [{n: x for n, x in w.items() if n in only} for w in W]
        W = limit_normalize(W, 4)
    set_weights(target, W)


def bind(obj, arm):
    """Armature como primer modificador (antes de las mascaras HIDE_*), objeto emparentado sin transformacion."""
    mw = obj.matrix_world.copy()
    obj.parent = arm
    obj.matrix_parent_inverse = arm.matrix_world.inverted()
    obj.matrix_world = mw
    m = obj.modifiers.get("Armature") or obj.modifiers.new("Armature", "ARMATURE")
    m.object = arm
    m.use_vertex_groups = True
    for o in bpy.context.view_layer.objects:
        o.select_set(False)
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.modifier_move_to_index(modifier=m.name, index=0)


def stats(objs):
    mx, unw, nv = 0, 0, 0
    for o in objs:
        for v in o.data.vertices:
            k = sum(1 for g in v.groups if g.weight > 1e-5 and not o.vertex_groups[g.group].name.startswith("HIDE_"))
            mx = max(mx, k)
            unw += k == 0
            nv += 1
    return {"max_influencias": mx, "vertices_sin_peso": unw, "vertices": nv}
