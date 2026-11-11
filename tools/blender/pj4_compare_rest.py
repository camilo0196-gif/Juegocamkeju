"""
CONCORDIA - PJ4: compara la pose de reposo de la Universal Animation Library (UAL 1 y UAL 2 Standard, Quaternius,
CC0) con la del esqueleto del elfo (blender/elfo_v03.blend). NO retargetea (lo hace Godot con BoneMap +
SkeletonProfileHumanoid): solo mide para anotar en TODO_GODOT_personaje.txt los ajustes del importador.
No guarda ningun .blend.
  medidas  altura, cadera, angulo del brazo bajo la horizontal (T = 0, A ~ 45), codo, apertura de piernas, hacia
           donde mira (+Y / -Y de Blender), dedos, huesos, escala del objeto armature
  captura  docs/captures/pj4_reposo_ual_vs_elfo.png (frente y lado, las tres figuras a la misma escala)
python pj4_compare_rest.py
"""

import json
import math
import os
import sys

import bpy
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
BLEND = os.path.join(REPO, "blender", "elfo_v03.blend")
UAL = {
    "UAL1": os.path.join(REPO, "animations", "ual", "ual1", "AnimationLibrary_Godot_Standard.glb"),
    "UAL2": os.path.join(REPO, "animations", "ual", "ual2", "UAL2_Standard.glb"),
}
REPORT = os.path.join(REPO, "docs", "reports", "pj4_reposo_ual.json")
CAPTURE = os.path.join(REPO, "docs", "captures", "pj4_reposo_ual_vs_elfo.png")

# nombres equivalentes (perfil humanoide de Godot <- UAL1 Rigify <- UAL2 estilo Unreal)
MAP = {
    "Hips": ("DEF-hips", "pelvis"),
    "Head": ("DEF-head", "Head"),
    "LeftUpperArm": ("DEF-upper_arm.L", "upperarm_l"),
    "LeftLowerArm": ("DEF-forearm.L", "lowerarm_l"),
    "LeftHand": ("DEF-hand.L", "hand_l"),
    "LeftUpperLeg": ("DEF-thigh.L", "thigh_l"),
    "LeftLowerLeg": ("DEF-shin.L", "calf_l"),
    "LeftFoot": ("DEF-foot.L", "foot_l"),
    "LeftToes": ("DEF-toe.L", "ball_l"),
}


def world_heads(arm):
    mw = arm.matrix_world
    return {b.name: (mw @ b.head_local, mw @ b.tail_local) for b in arm.data.bones}


def measure(arm, names):
    h = world_heads(arm)
    def p(k):
        return h[names[k]][0]
    ua = p("LeftLowerArm") - p("LeftUpperArm")
    fa = p("LeftHand") - p("LeftLowerArm")
    th = p("LeftLowerLeg") - p("LeftUpperLeg")
    ft = p("LeftToes") - p("LeftFoot")
    zs = [v for pair in h.values() for v in (pair[0].z, pair[1].z)]
    top = max(zs)
    bottom = min(zs)
    horiz = Vector((ua.x, ua.y, 0)).length
    return {
        "huesos": len(arm.data.bones),
        "altura_esqueleto_m": round(top - bottom, 3),
        "cadera_z_m": round(p("Hips").z - bottom, 3),
        "brazo_bajo_horizontal_grados": round(math.degrees(math.atan2(-ua.z, horiz)), 1),
        "codo_grados": round(math.degrees(ua.angle(fa)), 1),
        "pierna_desde_vertical_grados": round(math.degrees(th.angle(Vector((0, 0, -1)))), 1),
        "lado_brazo_izquierdo": "+X" if ua.x > 0 else "-X",
        "mira_hacia": "-Y" if ft.y < 0 else "+Y",
        "escala_objeto": [round(v, 4) for v in arm.matrix_world.to_scale()],
        "dedos": sum(1 for b in arm.data.bones if any(k in b.name.lower() for k in ("index", "middle", "ring", "pinky", "thumb"))),
    }


def main():
    bpy.ops.wm.open_mainfile(filepath=BLEND)
    elf = next(o for o in bpy.data.objects if o.type == "ARMATURE")
    elf_names = {k: k for k in MAP}
    out = {"elfo": {"armature": elf.name, **measure(elf, elf_names)}}
    figures = {"elfo": [o for o in bpy.data.objects if o.type == "MESH" and not o.hide_render]}
    offset = 1.4
    for i, (key, path) in enumerate(UAL.items()):
        before = set(bpy.data.objects)
        bpy.ops.import_scene.gltf(filepath=path)
        new = [o for o in bpy.data.objects if o not in before]
        arm = next(o for o in new if o.type == "ARMATURE")
        for o in new:
            if o.parent is None:
                o.location.x += offset * (i + 1)
        bpy.context.view_layer.update()
        for o in new:
            if o.type == "ARMATURE" and o.animation_data:
                o.animation_data.action = None
        bpy.context.view_layer.update()
        idx = 0 if key == "UAL1" else 1
        names = {k: v[idx] for k, v in MAP.items()}
        out[key] = {"archivo": os.path.relpath(path, REPO), "armature": arm.name, **measure(arm, names),
                    "acciones": len([a for a in bpy.data.actions if a.name not in out.get("_acc", [])])}
        figures[key] = [o for o in new if o.type == "MESH"]
    # comparativa
    e = out["elfo"]
    for k in ("UAL1", "UAL2"):
        u = out[k]
        out[k]["diferencias_con_elfo"] = {
            "brazo_grados": round(u["brazo_bajo_horizontal_grados"] - e["brazo_bajo_horizontal_grados"], 1),
            "altura_relativa": round(u["altura_esqueleto_m"] / e["altura_esqueleto_m"], 3),
            "cadera_relativa": round(u["cadera_z_m"] / e["cadera_z_m"], 3),
            "misma_orientacion": u["mira_hacia"] == e["mira_hacia"],
        }
    os.makedirs(os.path.dirname(REPORT), exist_ok=True)
    json.dump(out, open(REPORT, "w"), indent=1)
    print("REPOSO", json.dumps(out, indent=1))
    render(figures)


def render(figures):
    sys.path.insert(0, HERE)
    import capture_pj1 as C1
    sc = bpy.context.scene
    C1.setup(sc, res=(1500, 900))
    sc.cycles.samples = 16
    for o in bpy.data.objects:
        if o.type == "MESH":
            o.hide_render = not any(o in v for v in figures.values())
    shots = []
    for tag, eye, tgt, scale in (("frente", (1.4, -9.0, 0.95), (1.4, 0, 0.95), 4.4),
                                 ("lado", (12.0, 0.0, 0.95), (0, 0, 0.95), 4.4)):
        c = C1.cam(sc, eye, tgt, ortho=scale)
        shots.append(C1.shot(sc, c, CAPTURE.replace(".png", "_%s.png" % tag)))
    C1.sheet(shots, CAPTURE, labels=["frente: elfo (PJ3) | UAL1 | UAL2 (reposo)", "lado"], cols=1)
    print("CAPTURA", CAPTURE)


if __name__ == "__main__":
    main()
