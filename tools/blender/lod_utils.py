"""
CONCORDIA - LOD2 de lejos (decision D, etapa 17/18): un solo material de color plano por edificio (el color medio
del LOD0, ponderado por area) y una malla que no se rompe al diezmar: envolvente por voxeles (Remesh) del LOD0 y
luego Decimate hasta el objetivo. Para edificios hechos a mano (los del kit ya tienen su LOD2 simplificado).
"""

import os

import bpy
from mathutils import Vector

REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
_tex = {}


def _lin(c):
    return ((c + 0.055) / 1.055) ** 2.4 if c > 0.04045 else c / 12.92


def _srgb(c):
    c = max(0.0, min(1.0, c))
    return 1.055 * c ** (1 / 2.4) - 0.055 if c > 0.0031308 else 12.92 * c


def material_linear_color(m):
    """Color medio (lineal) que da el material: media de su albedo x factor, o el color plano."""
    if m is None or not m.use_nodes:
        return (0.5, 0.5, 0.5)
    nt = m.node_tree
    b = next((n for n in nt.nodes if n.type == "BSDF_PRINCIPLED"), None)
    img = next((n.image for n in nt.nodes if n.type == "TEX_IMAGE" and n.name == "Albedo" and n.image), None)
    fac = next((n.inputs["B"].default_value[:3] for n in nt.nodes if n.type == "MIX"), (1.0, 1.0, 1.0))
    if img is not None:
        p = bpy.path.abspath(img.filepath)
        if p not in _tex:
            import numpy as np
            from PIL import Image
            a = np.asarray(Image.open(p).convert("RGB").resize((128, 128))).astype("float32") / 255.0
            lin = np.where(a > 0.04045, ((a + 0.055) / 1.055) ** 2.4, a / 12.92)
            _tex[p] = tuple(float(v) for v in lin.reshape(-1, 3).mean(0))
        return tuple(c * f for c, f in zip(_tex[p], fac))
    if b is not None:
        bc = b.inputs["Base Color"].default_value[:3]
        if b.inputs["Emission Strength"].default_value > 0.5:      # lo emisivo se ve mas claro de lejos
            ec = b.inputs["Emission Color"].default_value[:3]
            return tuple(min(1.0, 0.5 * x + 0.5 * y) for x, y in zip(bc, ec))
        return tuple(bc)
    return (0.5, 0.5, 0.5)


def average_color(objs):
    """Color medio ponderado por area de las caras (lineal) de una lista de objetos."""
    acc, tot = Vector((0, 0, 0)), 0.0
    for o in objs:
        mats = [s.material for s in o.material_slots]
        for p in o.data.polygons:
            a = p.area
            m = mats[p.material_index] if p.material_index < len(mats) else None
            acc += Vector(material_linear_color(m)) * a
            tot += a
    return tuple(acc / max(tot, 1e-9))


def flat_material(name, lin_rgb):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*lin_rgb, 1.0)
    b.inputs["Roughness"].default_value = 0.85
    m["note"] = "LOD2: color plano = media del LOD0 (sRGB #%02X%02X%02X)" % tuple(int(round(_srgb(c) * 255)) for c in lin_rgb)
    return m


def flat_lod2(name, src_objs, col, parent, target_tris, voxel=0.35, mat_name=None):
    """Crea <name> (LOD2) a partir de los LOD0 src_objs (mismo espacio que el padre): une, Remesh por voxeles,
    Decimate al objetivo y un solo material plano. Sustituye un objeto <name> anterior."""
    old = bpy.data.objects.get(name)
    if old is not None:
        me = old.data
        bpy.data.objects.remove(old)
        if me.users == 0:
            bpy.data.meshes.remove(me)
    import bmesh
    bm = bmesh.new()
    inv = parent.matrix_world.inverted() if parent else None
    for o in src_objs:
        t = bmesh.new()
        t.from_mesh(o.data)
        t.transform((inv @ o.matrix_world) if inv else o.matrix_world)
        tm = bpy.data.meshes.new("TMP_l2")
        t.to_mesh(tm)
        t.free()
        bm.from_mesh(tm)
        bpy.data.meshes.remove(tm)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new(name, me)
    col.objects.link(o)
    o.parent = parent
    rm = o.modifiers.new("vox", "REMESH")
    rm.mode = "VOXEL"
    rm.voxel_size = voxel
    rm.use_smooth_shade = False
    dg = bpy.context.evaluated_depsgraph_get()
    new = bpy.data.meshes.new_from_object(o.evaluated_get(dg))
    o.modifiers.clear()
    o.data = new
    bpy.data.meshes.remove(me)
    n0 = sum(len(p.vertices) - 2 for p in o.data.polygons)
    dm = o.modifiers.new("dec", "DECIMATE")
    dm.decimate_type = "COLLAPSE"
    dm.ratio = min(1.0, target_tris / max(1, n0))
    dg = bpy.context.evaluated_depsgraph_get()
    new2 = bpy.data.meshes.new_from_object(o.evaluated_get(dg))
    o.modifiers.clear()
    old_me = o.data
    o.data = new2
    bpy.data.meshes.remove(old_me)
    o.data.name = name
    col_lin = average_color(src_objs)
    mat = flat_material(mat_name or f"MAT_LOD2_{name.split('_LOD2')[0].split('_Body')[0]}", col_lin)
    o.data.materials.clear()
    o.data.materials.append(mat)
    o.hide_render = True
    o["lod"] = 2
    o["lod2_method"] = f"remesh voxel {voxel} m + decimate; material plano {mat.name}"
    return o, sum(len(p.vertices) - 2 for p in o.data.polygons), mat.name, mat["note"]
