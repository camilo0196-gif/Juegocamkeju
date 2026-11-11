"""
CONCORDIA - capturas del PJ3 (esqueleto y pesos) sobre blender/elfo_v03.blend.
  poses_cuerpo   las 10 poses de prueba solo con el cuerpo (para juzgar los pesos de las articulaciones)
  poses_ropa     las 10 poses con la ropa del Sanador y el pelo
  articulaciones de cerca: codo (correr), rodilla (agachado), hombro (hechizo), cadera (sentado)
  esqueleto      huesos en pose T (frente y lado) sobre el cuerpo en gris
python capture_pj3.py <prefijo_salida> [nombres...]
"""

import os
import sys

import bpy
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import capture_pj1 as C1  # noqa: E402

REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
BLEND = os.path.join(REPO, "blender", "elfo_v03.blend")
CLOTH = ("Robe_Top", "Robe_Skirt", "Hood", "Belt_Pouches", "Boots", "Bracers", "Hair_Elf")


def set_pose(arm, name):
    arm.animation_data.action = bpy.data.actions[f"POSE_{name}"]
    bpy.context.scene.frame_set(1)
    bpy.context.view_layer.update()


def show_clothes(on):
    for n in CLOTH:
        o = bpy.data.objects[n]
        o.hide_render = not on
        o.hide_viewport = not on
    bpy.context.view_layer.update()


def bbox(objs):
    dg = bpy.context.evaluated_depsgraph_get()
    lo, hi = Vector((1e9,) * 3), Vector((-1e9,) * 3)
    for o in objs:
        if o.hide_render:
            continue
        ev = o.evaluated_get(dg)
        me = ev.to_mesh()
        for v in me.vertices:
            p = ev.matrix_world @ v.co
            lo = Vector(map(min, lo, p))
            hi = Vector(map(max, hi, p))
        ev.to_mesh_clear()
    return lo, hi


def seat(on, h=0.0):
    o = bpy.data.objects.get("TMP_Asiento")
    if on and o is None:
        me = bpy.data.meshes.new("TMP_Asiento")
        me.from_pydata([(x, y, z) for z in (0, 1) for y in (0, 1) for x in (0, 1)], [],
                       [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)])
        o = bpy.data.objects.new("TMP_Asiento", me)
        bpy.context.scene.collection.objects.link(o)
        m = bpy.data.materials.new("TMP_madera")
        m.use_nodes = True
        m.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.25, 0.2, 0.16, 1)
        me.materials.append(m)
    if o:
        o.hide_render = not on
        if on:
            o.scale = (0.5, 0.42, h)
            o.location = (-0.25, -0.30, 0.0)


def main():
    a = sys.argv[sys.argv.index("--") + 1:]
    pre, only = a[0], set(a[1:])
    bpy.ops.wm.open_mainfile(filepath=BLEND)
    scene = bpy.context.scene
    arm = bpy.data.objects["PJ_Elfo_Rig"]
    meshes = [o for o in bpy.data.objects if o.type == "MESH" and (o.get("pj_part") or o.get("pj_prenda"))]
    for o in bpy.data.objects:
        if o.type == "MESH" and o not in meshes:
            o.hide_render = True
    poses = [n[5:] for n in sorted(a.name for a in bpy.data.actions if a.name.startswith("POSE_"))]

    def want(n):
        return not only or n in only

    def pose_sheet(key, clothed):
        show_clothes(clothed)
        C1.setup(scene, (640, 820))
        ps, labs = [], []
        for n in poses:
            set_pose(arm, n)
            if n.endswith("Sentado"):
                # asiento bajo los muslos: altura = cara inferior de los muslos (cadera - radio del muslo)
                hip = arm.pose.bones["LeftUpperLeg"].head
                seat(True, h=max(0.05, hip.z - 0.085))
            else:
                seat(False)
            lo, hi = bbox(meshes)
            c = (lo + hi) / 2
            size = max(hi - lo)
            d = Vector((0.45, -1.0, 0.32)).normalized()
            cam = C1.cam(scene, c + d * (size * 1.35 + 0.35), c, lens=40)
            ps.append(C1.shot(scene, cam, f"{pre}_{key}_{n}.png"))
            labs.append(n.replace("_", " "))
        seat(False)
        C1.sheet(ps, f"{pre}_{key}.png", labs, cols=5)
        show_clothes(True)
    if want("poses_cuerpo"):
        pose_sheet("poses_cuerpo", False)
    if want("poses_ropa"):
        pose_sheet("poses_ropa", True)
    if want("articulaciones"):
        show_clothes(False)
        C1.setup(scene, (800, 800))
        shots = [("04_Correr", "LeftLowerArm", Vector((0.9, -0.6, 0.2)), "CODO (correr, 85 grados)"),
                 ("08_Agachado", "LeftLowerLeg", Vector((1.0, -0.6, 0.3)), "RODILLA (agachado, 132 grados)"),
                 ("06_Hechizo", "LeftUpperArm", Vector((0.5, -1.0, 0.3)), "HOMBRO (brazos levantados)"),
                 ("05_Sentado", "LeftUpperLeg", Vector((1.0, -0.8, 0.4)), "CADERA (sentado, 88 grados)")]
        ps = []
        for pose, bone, d, _t in shots:
            set_pose(arm, pose)
            p = arm.pose.bones[bone].head
            cam = C1.cam(scene, p + d.normalized() * 0.9, p, lens=45)
            ps.append(C1.shot(scene, cam, f"{pre}_art_{bone}.png"))
        C1.sheet(ps, f"{pre}_articulaciones.png", [s[3] for s in shots], cols=2)
        show_clothes(True)
    if want("esqueleto"):
        show_clothes(False)
        set_pose(arm, "01_T")
        for o in meshes:
            o.data.materials.clear() if False else None
        arm.data.display_type = "OCTAHEDRAL"
        # el armature no se renderiza: huesos como cilindros temporales
        mat = bpy.data.materials.new("TMP_hueso")
        mat.use_nodes = True
        mat.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.9, 0.55, 0.1, 1)
        mat2 = bpy.data.materials.new("TMP_extra")
        mat2.use_nodes = True
        mat2.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.2, 0.6, 0.95, 1)
        import bmesh
        for b in arm.data.bones:
            h, t = b.head_local, b.tail_local
            L = (t - h).length
            bm = bmesh.new()
            bmesh.ops.create_cone(bm, cap_ends=True, segments=6, radius1=max(0.004, L * 0.12), radius2=0.002,
                                  depth=L)
            me = bpy.data.meshes.new("TMP_b")
            bm.to_mesh(me)
            bm.free()
            o = bpy.data.objects.new("TMP_b_" + b.name, me)
            o.matrix_world = (arm.matrix_world @ b.matrix_local) @ __import__("mathutils").Matrix.Translation(
                (0, L / 2, 0)) @ __import__("mathutils").Matrix.Rotation(-1.5708, 4, "X")
            me.materials.append(mat if b.name in [p[0] for p in __import__("concordia_rig").PROFILE] else mat2)
            o.show_in_front = True
            bpy.context.scene.collection.objects.link(o)
        for o in meshes:
            if o.get("pj_part"):
                o.hide_render = False
                m = bpy.data.materials.new("TMP_vidrio")
                m.use_nodes = True
                bs = m.node_tree.nodes["Principled BSDF"]
                bs.inputs["Base Color"].default_value = (0.7, 0.7, 0.7, 1)
                bs.inputs["Alpha"].default_value = 0.25
                o.data.materials.clear()
                o.data.materials.append(m)
        C1.setup(scene, (900, 1100))
        ctr = Vector((0, 0, 0.93))
        ps = [C1.shot(scene, C1.cam(scene, ctr + d * 20, ctr, ortho=2.0), f"{pre}_sk{k}.png")
              for k, d in enumerate((Vector((0, -1, 0)), Vector((1, 0, 0))))]
        C1.sheet(ps, f"{pre}_esqueleto.png", ["ESQUELETO - FRENTE (naranja: perfil Godot; azul: extra)",
                                              "ESQUELETO - LADO"])


if __name__ == "__main__":
    main()
    os._exit(0)
