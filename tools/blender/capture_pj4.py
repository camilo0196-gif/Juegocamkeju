"""
CONCORDIA - capturas del PJ4 (animaciones del Sanador) sobre blender/elfo_v04.blend (no se guarda).
Tres fotogramas clave por animacion con la camara isometrica del juego (elevacion 35,26 grados, 45 grados de
azimut, ortografica), mirando al Sanador por delante y a su derecha (la mano del baston), y una vista frontal
pequena de referencia. Baston temporal (solo para la captura) en el hueso Weapon_R (+Y = eje del asta).
  docs/captures/pj4_<animacion>.png y docs/captures/pj4_animaciones.png (las cuatro juntas)
python capture_pj4.py
"""

import json
import math
import os
import sys

import bpy
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import capture_pj1 as C1  # noqa: E402

REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
BLEND = os.path.join(REPO, "blender", "elfo_v04.blend")
OUT = os.path.join(REPO, "docs", "captures")
REPORT = os.path.join(REPO, "docs", "reports", "pj4_anim.json")


def staff(arm):
    """asta de 1,7 m (r 2,2 cm) con un cristal #8FD0FF arriba, emparentada a Weapon_R"""
    bpy.ops.mesh.primitive_cylinder_add(radius=0.022, depth=1.65, vertices=12)
    st = bpy.context.active_object
    st.name = "TMP_Baston"
    m = bpy.data.materials.new("TMP_Madera")
    m.diffuse_color = (0.25, 0.17, 0.11, 1)
    m.use_nodes = True
    m.node_tree.nodes["Principled BSDF"].inputs[0].default_value = (0.25, 0.17, 0.11, 1)
    st.data.materials.append(m)
    bpy.ops.mesh.primitive_ico_sphere_add(radius=0.06, subdivisions=2)
    cr = bpy.context.active_object
    cr.name = "TMP_Cristal"
    mc = bpy.data.materials.new("TMP_Cristal")
    mc.use_nodes = True
    bs = mc.node_tree.nodes["Principled BSDF"]
    bs.inputs[0].default_value = (0.56, 0.82, 1.0, 1)
    bs.inputs["Emission Color"].default_value = (0.56, 0.82, 1.0, 1)
    bs.inputs["Emission Strength"].default_value = 2.0
    cr.data.materials.append(mc)
    bone = arm.data.bones["Weapon_R"]
    rest = arm.matrix_world @ bone.matrix_local                       # Y del hueso = eje del asta
    # el asta sube 0,8 m por encima de la mano y baja 0,85 m (la mano a media altura del baston)
    st.matrix_world = rest @ Matrix.Translation((0, 0.825 - 0.85, 0)) @ Matrix.Rotation(math.radians(90), 4, "X")
    cr.matrix_world = rest @ Matrix.Translation((0, 0.85, 0))
    for o in (st, cr):
        mw = o.matrix_world.copy()
        o.parent = arm
        o.parent_type = "BONE"
        o.parent_bone = "Weapon_R"
        o.matrix_world = mw
    return [st, cr]


def main():
    bpy.ops.wm.open_mainfile(filepath=BLEND)
    sc = bpy.context.scene
    arm = bpy.data.objects["PJ_Elfo_Rig"]
    for pb in arm.pose.bones:
        pb.matrix_basis = Matrix.Identity(4)
    bpy.context.view_layer.update()
    tmp = staff(arm)
    C1.setup(sc, res=(700, 800))
    sc.cycles.samples = 16
    bpy.ops.mesh.primitive_plane_add(size=6, location=(0, 0, 0))
    floor = bpy.context.active_object
    fm = bpy.data.materials.new("TMP_Suelo")
    fm.use_nodes = True
    fm.node_tree.nodes["Principled BSDF"].inputs[0].default_value = (0.42, 0.40, 0.37, 1)
    floor.data.materials.append(fm)
    rep = json.load(open(REPORT))
    arm.animation_data.action = None
    for t in arm.animation_data.nla_tracks:
        t.mute = True
    sheets = []
    for name, data in rep["animaciones"].items():
        arm.animation_data.action = bpy.data.actions[name]
        paths, labels = [], []
        for f in data["capturas"]:
            sc.frame_set(f)
            bpy.context.view_layer.update()
            # isometrica (35,26 grados de alto): el Sanador mira a -Y; camara a su derecha (-X) y algo delante
            hz = Vector((-1.0, -0.42, 0.0)).normalized()             # mas de lado: los gestos al frente no se acortan
            d = (hz * math.cos(math.radians(35.264)) + Vector((0, 0, math.sin(math.radians(35.264))))).normalized()
            c = C1.cam(sc, Vector((0, -0.2, 0.85)) + d * 12.0, (0, -0.2, 0.85), ortho=2.7)
            p = os.path.join(OUT, f"_tmp_pj4_{name}_{f}.png")
            paths.append(C1.shot(sc, c, p))
            labels.append(f"{name}  f{f} ({(f - 1) / 30:.2f} s)")
        out = os.path.join(OUT, f"pj4_{name.replace('-', '_')}.png")
        C1.sheet(paths, out, labels=labels, cols=3)
        sheets.append(out)
        print("CAPTURA", out, flush=True)
    from PIL import Image
    ims = [Image.open(p) for p in sheets]
    w, h = ims[0].size
    S = Image.new("RGB", (w, h * len(ims)))
    for i, im in enumerate(ims):
        S.paste(im, (0, i * h))
    S.save(os.path.join(OUT, "pj4_animaciones.png"))
    print("CAPTURA", os.path.join(OUT, "pj4_animaciones.png"), flush=True)


if __name__ == "__main__":
    main()
    sys.stdout.flush()
    os._exit(0)
