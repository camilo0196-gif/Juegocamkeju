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


# ---------------------------------------------------------------------------
# LOD2 por volumetria (massing): para edificios con cubiertas abiertas de una cara (el Remesh por voxeles no las
# cierra y el diezmado las borra). Volumenes cerrados simples con las cotas reales del edificio.
# ---------------------------------------------------------------------------
def _gable(mb, x0, x1, y_e, z_e, z_r, mat, axis="x"):
    """Prisma de cubierta a dos aguas cerrado: alero a +-y_e (z_e), cumbrera z_r sobre y = 0 (axis x)."""
    if axis == "x":
        poly = [(-y_e, z_e), (y_e, z_e), (0.0, z_r)]
        a = [(x0, y, z) for y, z in poly]
        b = [(x1, y, z) for y, z in poly]
    else:
        poly = [(-y_e, z_e), (y_e, z_e), (0.0, z_r)]
        a = [(y, x0, z) for y, z in poly]
        b = [(y, x1, z) for y, z in poly]
    mb.face(a, mat, nrm=(-1, 0, 0) if axis == "x" else (0, -1, 0))
    mb.face(b, mat, nrm=(1, 0, 0) if axis == "x" else (0, 1, 0))
    for i in range(3):
        j = (i + 1) % 3
        mid = [(a[i][k] + a[j][k]) / 2 for k in range(3)]
        n = (0, mid[1], mid[2] - (z_e + z_r) / 2) if axis == "x" else (mid[0], 0, mid[2] - (z_e + z_r) / 2)
        mb.face([a[i], a[j], b[j], b[i]], mat, nrm=n)


def _cone(mb, cx, cy, r, z0, z1, n, mat):
    pts = [(cx + r * __import__("math").cos(2 * 3.14159265 * i / n), cy + r * __import__("math").sin(2 * 3.14159265 * i / n),
            z0) for i in range(n)]
    for i in range(n):
        j = (i + 1) % n
        mb.face([pts[i], pts[j], (cx, cy, z1)], mat, nrm=(pts[i][0] + pts[j][0] - 2 * cx, pts[i][1] + pts[j][1] - 2 * cy, r))
    mb.face(pts[::-1], mat, nrm=(0, 0, -1))


def massing(kind, mb, m="MAT_LOD2_TMP"):
    if kind == "SANTUARIO":
        mb.box((-7.5, -5.4, 0.0), (7.5, 5.4, 9.6), m)
        _gable(mb, -7.2, 7.2, 5.05, 9.0, 14.0, m)
        for x in (-7.6, 7.6):
            _gable(mb, x - 0.3, x + 0.3, 5.4, 9.6, 14.35, m)
        mb.box((4.0, -0.5, 13.0), (5.0, 0.5, 16.6), m)
        _cone(mb, 4.5, 0.0, 0.7, 16.6, 19.5, 6, m)
        for x in (-7.2, -4.5, -1.5, 1.5, 4.5, 7.2):
            for y in (-5.7, 5.7):
                mb.box((x - 0.25, y - 0.3, 0.0), (x + 0.25, y + 0.3, 9.2), m)
                _cone(mb, x, y, 0.25, 9.2, 11.3, 4, m)
    elif kind == "SALON_HAZANAS":
        mb.box((-20.2, -7.1, 0.0), (20.2, 7.1, 8.0), m)
        _gable(mb, -20.2, 20.2, 7.95, 7.16, 15.0, m)
        mb.box((-3.6, 7.1, 0.0), (3.6, 8.0, 10.3), m)
        _gable(mb, 5.07, 8.0, 3.6, 10.0, 14.29, m, axis="y")
        for sx in (-1, 1):
            a, b = sorted((sx * 3.6, sx * 4.5))
            mb.box((a, 7.1, 0.0), (b, 8.0, 12.7), m)
            _cone(mb, (a + b) / 2, 7.55, 0.6, 12.7, 14.0, 4, m)
        mb.box((-1.25, -1.25, 13.6), (1.25, 1.25, 16.6), m)
        _cone(mb, 0.0, 0.0, 1.45, 16.6, 18.0, 6, m)
        for x in (-15.0, -9.0, -3.0, 3.0, 9.0, 15.0, -19.6, 19.6):
            for y in (-7.55, 7.55):
                if y > 0 and abs(x) == 3.0:
                    continue
                mb.box((x - 0.6, y - 0.45, 0.0), (x + 0.6, y + 0.45, 6.3), m)
    elif kind == "TesoreriaMuralla":
        mb.box((-14.0, -9.0, 0.0), (14.0, 5.4, 9.3), m)
        mb.box((-14.0, 5.4, 4.8), (14.0, 8.7, 9.3), m)
        for k in range(8):
            u = -14.0 + 0.6 + (28.0 - 1.2) * k / 7
            mb.box((u - 0.5, 7.9, 0.0), (u + 0.5, 8.9, 4.8), m)
        for x in [-13.4 + 1.2 * i for i in range(23)]:
            mb.box((x - 0.3, 7.9, 9.3), (x + 0.3, 8.7, 10.1), m)
        mb.box((-14.0, -9.0, 9.3), (-9.6, -4.6, 18.1), m)
    elif kind == "GranSubasta":
        _gable(mb, -20.6, 20.6, 8.5, 4.57, 10.4, m)
        import math as _m
        for k in range(11):
            x = -19.7 + 39.4 * k / 10
            for y in (-7.7, 7.7):
                mb.box((x - 0.2, y - 0.2, 0.0), (x + 0.2, y + 0.2, 4.8), m)
        mb.box((-19.9, -7.85, 3.35), (19.9, -3.75, 3.5), m)
        mb.box((-19.9, 3.75, 3.35), (19.9, 7.85, 3.5), m)
        mb.box((-2.5, -1.5, 0.0), (2.5, 1.5, 0.8), m)
        _ = _m
    else:
        raise KeyError(kind)


def massing_lod2(kind, name, src_objs, col, parent):
    """LOD2 = volumetria cerrada (massing) con un material plano (color medio del LOD0)."""
    import bld_kit as K
    old = bpy.data.objects.get(name)
    if old is not None:
        me = old.data
        bpy.data.objects.remove(old)
        if me.users == 0:
            bpy.data.meshes.remove(me)
    col_lin = average_color(src_objs)
    mat = flat_material(f"MAT_LOD2_{kind}", col_lin)
    mb = K.MB()
    massing(kind, mb, mat.name)
    mb.finish()
    me = bpy.data.meshes.new(name)
    mb.bm.to_mesh(me)
    mb.bm.free()
    me.materials.append(mat)
    o = bpy.data.objects.new(name, me)
    col.objects.link(o)
    o.parent = parent
    o.hide_render = True
    o["lod"] = 2
    o["lod2_method"] = f"volumetria cerrada (massing) con material plano {mat.name}"
    return o, sum(len(p.vertices) - 2 for p in o.data.polygons), mat.name, mat["note"]


def massing_spec(name, spec, src_objs, col, parent, mat_name=None):
    """LOD2 por volumetria a partir de una lista de primitivas cerradas:
    ("box", lo, hi) | ("gable", x0, x1, y_half, z_eave, z_ridge, y_center) | ("cone", cx, cy, r, z0, z1, n) |
    ("cyl", cx, cy, r, z0, z1, n). Un material plano (color medio del LOD0)."""
    import bld_kit as K
    from mathutils import Matrix
    old = bpy.data.objects.get(name)
    if old is not None:
        me = old.data
        bpy.data.objects.remove(old)
        if me.users == 0:
            bpy.data.meshes.remove(me)
    mat = flat_material(mat_name or f"MAT_LOD2_{name.replace('_Body_LOD2', '')}", average_color(src_objs))
    m = mat.name
    mb = K.MB()
    for p in spec:
        if p[0] == "box":
            mb.box(p[1], p[2], m)
        elif p[0] == "gable":
            _, x0, x1, yh, ze, zr, yc = p
            mb.push(Matrix.Translation((0, yc, 0)))
            _gable(mb, x0, x1, yh, ze, zr, m)
            mb.pop()
        elif p[0] == "cone":
            _, cx, cy, r, z0, z1, n = p
            _cone(mb, cx, cy, r, z0, z1, n, m)
        elif p[0] == "cyl":
            _, cx, cy, r, z0, z1, n = p
            mb.cylinder(r, z0, z1, n, m, caps=True, center=(cx, cy))
    mb.finish()
    me = bpy.data.meshes.new(name)
    mb.bm.to_mesh(me)
    mb.bm.free()
    me.materials.append(mat)
    o = bpy.data.objects.new(name, me)
    col.objects.link(o)
    o.parent = parent
    o.hide_render = True
    o["lod"] = 2
    o["lod2_method"] = f"volumetria (massing) con material plano {mat.name}"
    return o, sum(len(p.vertices) - 2 for p in o.data.polygons), mat.name, mat["note"]
