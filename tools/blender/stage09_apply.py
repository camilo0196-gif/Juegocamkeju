"""
CONCORDIA - etapa 09 (Blender): crea los materiales glTF con las texturas de textures/concordia, UV de mundo
y asignacion por mascaras; reexporta chunks, muralla y una biblioteca de materiales. v08 -> v09.
"""

import os
import sys
from math import hypot

import bmesh
import bpy
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import concordia_const as C  # noqa: E402
import stage09_materials as SM  # noqa: E402

REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
UV_NAME = "UVWorld"
REMAP = {
    "MAT_Wall_Granite": "MAT_Wall_Gray", "MAT_Stone_Limestone": "MAT_Limestone_Worn",
    "MAT_Stone_Band": "MAT_Limestone_Worn", "MAT_Wall_Patch": "MAT_Stone_Repair", "MAT_Stone_Repair": "MAT_Stone_Repair",
    "MAT_Wall_Runes": "MAT_Wall_Runes", "MAT_Stone_Runestone": "MAT_Wall_Runes", "MAT_Wood_Dark": "MAT_Wood_Dark",
    "MAT_Iron_Black": "MAT_Iron_Black", "MAT_Magic_Glow25": "MAT_Shard_Blue", "MAT_Magic_ShardBlue": "MAT_Shard_Blue",
    "MAT_Roof_Slate": "MAT_Roof_Tile_Ocher", "MAT_Roof_TileOchre": "MAT_Roof_Tile_Ocher", "MAT_Water": "MAT_Water",
    "MAT_Exterior_Rock": "MAT_Rock_Gray", "MAT_Exterior_Ash": "MAT_Ash_Gray",
}
CITY_SLOTS = ["MAT_Ground_Cracked", "MAT_Limestone_Worn", "MAT_Cobble_Concordia", "MAT_Plaza_Slab",
              "MAT_Plaza_Slab_Travertino", "MAT_Wall_Gray", "MAT_Ash_Gray", "MAT_Stone_Repair"]
EXT_SLOTS = ["MAT_Ash_Gray", "MAT_Rock_Gray"]


_PH = None


def polyhaven_info():
    global _PH
    if _PH is None:
        try:
            import json
            with open(os.path.join(SM.OUT, "polyhaven.json")) as fh:
                _PH = json.load(fh)
        except OSError:
            _PH = {}
    return _PH


def make_material(name):
    fn, ns, (r0, r1), metallic, ref, use = SM.MATS[name]
    tmp = "NEW_" + name
    if tmp in bpy.data.materials:
        bpy.data.materials.remove(bpy.data.materials[tmp])
    m = bpy.data.materials.new(tmp)
    m.use_nodes = True
    N, L = m.node_tree.nodes, m.node_tree.links
    b = N["Principled BSDF"]
    uv = N.new("ShaderNodeUVMap")
    uv.uv_map = UV_NAME
    p = SM.tex_paths(name)
    vec = uv.outputs["UV"]
    ph = polyhaven_info().get(name)
    if ph:
        mp = N.new("ShaderNodeMapping")
        mp.vector_type = "POINT"
        mp.inputs["Scale"].default_value = (ph["uv_scale"][0], ph["uv_scale"][1], 1.0)
        L.new(uv.outputs["UV"], mp.inputs["Vector"])
        vec = mp.outputs["Vector"]
        m["poly_haven_asset"] = ph["asset"]
        m["poly_haven_license"] = "CC0"
        m["texture_dimensions_m"] = str(ph["dimensions_m"])

    def img(key, non_color):
        im = bpy.data.images.load(p[key], check_existing=True)
        if non_color:
            im.colorspace_settings.name = "Non-Color"
        t = N.new("ShaderNodeTexImage")
        t.name = t.label = key
        t.image = im
        L.new(vec, t.inputs["Vector"])
        return t
    L.new(img("Albedo", False).outputs["Color"], b.inputs["Base Color"])
    if metallic > 0.0:
        # glTF lee metal del canal B y rugosidad del G de la misma imagen: ORM empaquetado (R=1, G=rough, B=metal)
        import numpy as np
        from PIL import Image
        rough_img = np.asarray(Image.open(p["Roughness"]).convert("L"))
        orm = np.dstack([np.full_like(rough_img, 255), rough_img, np.full_like(rough_img, int(round(metallic * 255)))])
        p["ORM"] = p["Roughness"].replace("_Roughness.jpg", "_ORM.png")
        Image.fromarray(orm).save(p["ORM"], optimize=True)
        t = img("ORM", True)
        sep = N.new("ShaderNodeSeparateColor")
        L.new(t.outputs["Color"], sep.inputs["Color"])
        L.new(sep.outputs["Green"], b.inputs["Roughness"])
        L.new(sep.outputs["Blue"], b.inputs["Metallic"])
        m["orm"] = os.path.relpath(p["ORM"], REPO)
    else:
        L.new(img("Roughness", True).outputs["Color"], b.inputs["Roughness"])
    nm = N.new("ShaderNodeNormalMap")
    nm.uv_map = UV_NAME
    L.new(img("Normal", True).outputs["Color"], nm.inputs["Color"])
    L.new(nm.outputs["Normal"], b.inputs["Normal"])
    if metallic <= 0.0:
        b.inputs["Metallic"].default_value = 0.0
    if name == "MAT_Shard_Blue":
        b.inputs["Emission Color"].default_value = C.hex_to_linear_rgba(SM.SHARD_HEX)
        b.inputs["Emission Strength"].default_value = SM.EMISSION[name]
    if name == "MAT_Wall_Runes":
        em = img("Emission", False)
        mix = N.new("ShaderNodeMix")
        mix.data_type = "RGBA"
        mix.blend_type = "MULTIPLY"
        mix.inputs["Factor"].default_value = 1.0
        L.new(em.outputs["Color"], mix.inputs["A"])
        mix.inputs["B"].default_value = C.hex_to_linear_rgba(SM.SHARD_HEX)
        L.new(mix.outputs["Result"], b.inputs["Emission Color"])
        b.inputs["Emission Strength"].default_value = SM.EMISSION[name]
        m["emission_strength"] = SM.EMISSION[name]
        m["emission_note"] = "parametrizable: cambiar 'emission_strength' (y Emission Strength del BSDF); en Godot emission_energy_multiplier"
    m["textures"] = os.path.relpath(os.path.dirname(p["Albedo"]), REPO)
    m["uv"] = f"{UV_NAME}: proyeccion planar en mundo (caja), 1 m = 1 tile"
    m["poly_haven_ref"] = ref
    m["use"] = use
    m["roughness_range"] = f"{r0}-{r1}"
    return m


def world_uv(obj, name=UV_NAME):
    """UV de mundo por caja (eje dominante de la normal de cada cara). 1 m = 1 tile."""
    me = obj.data
    mw = obj.matrix_world
    nm = mw.to_3x3()
    if me.uv_layers:
        uv = me.uv_layers[0]
        uv.name = name
    else:
        uv = me.uv_layers.new(name=name)
    me.uv_layers.active_index = 0
    co = [mw @ v.co for v in me.vertices]
    flat = [0.0] * (len(me.loops) * 2)
    for p in me.polygons:
        n = nm @ p.normal
        ax = max(range(3), key=lambda i: abs(n[i]))
        for li in range(p.loop_start, p.loop_start + p.loop_total):
            c = co[me.loops[li].vertex_index]
            if ax == 2:
                u, v = c.x, c.y
            elif ax == 0:
                u, v = (c.y if n.x > 0 else -c.y), c.z
            else:
                u, v = (-c.x if n.y > 0 else c.x), c.z
            flat[li * 2], flat[li * 2 + 1] = u, v
    uv.data.foreach_set("uv", flat)


def loop_attr(me, name):
    a = me.color_attributes.get(name)
    if a is None:
        return None
    v = [0.0] * (len(me.loops) * 4)
    a.data.foreach_get("color", v)
    return v


def assign_city(obj, mats, stats):
    me = obj.data
    ret, slab, trav = loop_attr(me, "retaining_mask"), loop_attr(me, "slab_ring_id"), loop_attr(me, "travertine_band")
    road, ctype = loop_attr(me, "road_mask"), loop_attr(me, "cobble_type")
    me.materials.clear()
    for n in CITY_SLOTS:
        me.materials.append(mats[n])
    idx = {n: i for i, n in enumerate(CITY_SLOTS)}
    count = {n: 0 for n in CITY_SLOTS}
    vg = obj.vertex_groups.get("talud")
    talud_v = set()
    if vg is not None:
        gi = vg.index
        talud_v = {v.index for v in me.vertices if any(g.group == gi for g in v.groups)}
    for p in me.polygons:
        li = p.loop_start * 4
        c = p.center
        r = hypot(c.x, c.y)
        ct = round(ctype[li] * 8) if ctype else 0
        if ret and ret[li] > 0.5 and r < C.WALL_BASE_R[1]:
            n = "MAT_Limestone_Worn"
        elif slab and slab[li] > 0.01:
            n = "MAT_Plaza_Slab_Travertino" if trav and trav[li] > 0.5 else "MAT_Plaza_Slab"
        elif ct == 7:
            n = "MAT_Wall_Gray"
        elif road and road[li] > 0.5:
            n = {2: "MAT_Stone_Repair", 4: "MAT_Plaza_Slab"}.get(ct, "MAT_Cobble_Concordia")
        elif all(v in talud_v for v in p.vertices) or r >= C.WALL_BASE_R[1]:
            n = "MAT_Ash_Gray"
        else:
            n = "MAT_Ground_Cracked"
        p.material_index = idx[n]
        count[n] += 1
    stats["assign_TRN_City"] = count


def assign_exterior(obj, mats, stats):
    me = obj.data
    rock = loop_attr(me, "rock_mask")
    me.materials.clear()
    for n in EXT_SLOTS:
        me.materials.append(mats[n])
    cnt = [0, 0]
    for p in me.polygons:
        k = 1 if rock and rock[p.loop_start * 4] > 0.5 else 0
        p.material_index = k
        cnt[k] += 1
    stats["assign_TRN_Exterior"] = {"MAT_Ash_Gray (ash_mask)": cnt[0], "MAT_Rock_Gray (rock_mask)": cnt[1]}


def build(scene, stats, export_dir=None):
    mats = {n: make_material(n) for n in SM.MATS}
    # UV de mundo en todas las mallas no instanciadas (las piezas del kit de muralla conservan su UV local)
    uv_done, uv_skip = 0, 0
    for o in bpy.data.objects:
        if o.type != "MESH" or o.name.startswith(("TRN_CityChunk", "TRN_ExteriorChunk")):
            continue
        if o.data.users > 1 or o.users_collection and o.users_collection[0].name.startswith("WALL_KIT"):
            uv_skip += 1
            continue
        world_uv(o)
        uv_done += 1
    stats["uv_world"] = {"meshes": uv_done, "kept_local_uv (kit instanciado)": uv_skip}
    assign_city(bpy.data.objects["TRN_City"], mats, stats)
    assign_exterior(bpy.data.objects["TRN_Exterior"], mats, stats)
    # resto: reasignar por nombre
    unmapped = set()
    for o in bpy.data.objects:
        if o.type != "MESH" or o.name in ("TRN_City", "TRN_Exterior"):
            continue
        me = o.data
        for i, m in enumerate(me.materials):
            if m is None or m.name.startswith("NEW_") or m.name == "MAT_Void":
                continue
            tgt = REMAP.get(m.name)
            if tgt:
                me.materials[i] = mats[tgt]
            elif not m.name.startswith("TMP_"):
                unmapped.add(m.name)
    # borra los antiguos y renombra
    keep = {"MAT_Void"}
    for m in list(bpy.data.materials):
        if not m.name.startswith("NEW_") and m.name not in keep:
            bpy.data.materials.remove(m)
    for m in list(bpy.data.materials):
        if m.name.startswith("NEW_"):
            m.name = m.name[4:]
    stats["materials"] = {n: {"metallic": SM.MATS[n][3], "roughness": SM.MATS[n][2], "ref": SM.MATS[n][4],
                              "use": SM.MATS[n][5], "emission": SM.EMISSION.get(n)} for n in SM.MATS}
    stats["unmapped_old_materials"] = sorted(unmapped)
    return mats


def library_spheres(col_name="MATERIAL_LIBRARY"):
    col = bpy.data.collections.get(col_name)
    if col is None:
        col = bpy.data.collections.new(col_name)
        bpy.context.scene.collection.children.link(col)
    for o in list(col.objects):
        bpy.data.objects.remove(o)
    objs = []
    for i, n in enumerate(SM.MATS):
        bm = bmesh.new()
        bmesh.ops.create_uvsphere(bm, u_segments=48, v_segments=24, radius=0.5)
        me = bpy.data.meshes.new(f"MATLIB_{n}")
        bm.to_mesh(me)
        bm.free()
        me.shade_smooth()
        o = bpy.data.objects.new(f"MATLIB_{n}", me)
        o.location = (1000 + (i % 6) * 1.5, 1000 + (i // 6) * 1.5, 0.5)
        col.objects.link(o)
        world_uv(o)
        me.materials.append(bpy.data.materials[n])
        objs.append(o)
    return col, objs
