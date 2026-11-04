"""
CONCORDIA - Etapa 02c: material del terreno + mascara de borde + oclusion ambiental.

- edge_mask : 1 junto a la arista superior de cada muro (bordes que se oscurecen).
- AO        : horneada con Cycles en un atributo de color por esquina (distancia 3 m),
              con pretiles, escaleras y contrafuertes en escena (oscurece la base de los muros).
- ao_edge   : AO * (1 - EDGE_DARK * edge_mask)  -> multiplicador del color base.
- mask_pack : RGBA = (retaining, dirt, stone, ao_edge). Es el color activo que se
              exporta como COLOR_0 en el .glb (glTF solo exporta un color por vertice).
- MAT_Terrain_City: Principled BSDF; color = mezcla de tierra / suciedad / piedra / cara de
  muro segun las mascaras, multiplicado por ao_edge. (En Godot hara falta un shader que lea
  COLOR_0; los nodos de Blender no se exportan a glTF.)
"""

import os
import sys

import bpy  # noqa: I001
import bmesh  # noqa: F401
from mathutils import kdtree

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import concordia_const as C  # noqa: E402
import terrain_profile as T  # noqa: E402

MAT_TERRAIN = "MAT_Terrain_City"
# Colores provisionales (sRGB) dentro de la paleta descrita: tierra apisonada, suciedad,
# piedra de pavimento gastada y caliza de los muros.
COL_GROUND = "#9A8D76"
COL_DIRT = "#6F604C"
COL_STONE = "#A39A87"
COL_WALL = "#B3A994"

EDGE_WIDTH = 0.8          # m: oscurecimiento de la parte alta de la cara del muro
EDGE_DARK = 0.30
BASE_WIDTH = 0.6          # m: banda oscura al pie de cada muro (coincide con la fila BASE_ROW)
BASE_DARK = 0.45
AO_DISTANCE = 1.5         # m (solo terreno: las piezas tendran SSAO en Godot)
AO_SAMPLES = 32


def terrain_material():
    if MAT_TERRAIN in bpy.data.materials:
        bpy.data.materials.remove(bpy.data.materials[MAT_TERRAIN])
    m = bpy.data.materials.new(MAT_TERRAIN)
    m.use_nodes = True
    N, L = m.node_tree.nodes, m.node_tree.links
    bsdf = N["Principled BSDF"]
    bsdf.inputs["Roughness"].default_value = 0.92

    def attr(name):
        a = N.new("ShaderNodeVertexColor")
        a.layer_name = name
        return a.outputs["Color"]

    def mix(fac, a, b, blend="MIX"):
        n = N.new("ShaderNodeMix")
        n.data_type = "RGBA"
        n.blend_type = blend
        if isinstance(fac, float):
            n.inputs["Factor"].default_value = fac
        else:
            L.new(fac, n.inputs["Factor"])
        for sock, val in (("A", a), ("B", b)):
            if isinstance(val, str):
                n.inputs[sock].default_value = C.hex_to_linear_rgba(val)
            else:
                L.new(val, n.inputs[sock])
        return n.outputs["Result"]

    def bw(sock):
        n = N.new("ShaderNodeRGBToBW")
        L.new(sock, n.inputs[0])
        return n.outputs[0]

    c = mix(bw(attr("dirt_mask")), COL_GROUND, COL_DIRT)
    c = mix(bw(attr("stone_mask")), c, COL_STONE)
    c = mix(bw(attr("retaining_mask")), c, COL_WALL)
    c = mix(1.0, c, attr("ao_edge"), "MULTIPLY")
    L.new(c, bsdf.inputs["Base Color"])
    return m


def _kd(points):
    kd = kdtree.KDTree(max(1, len(points)))
    for i, c in enumerate(points):
        kd.insert(c, i)
    kd.balance()
    return kd


def edge_and_base(me):
    """edge: parte alta de las caras de muro. base: suelo al pie de los muros."""
    co = [v.co.copy() for v in me.vertices]
    tops, feet, wall_v = [], [], set()
    for p in me.polygons:
        if p.normal.z <= 0.342:                      # >= 70 grados
            zc = p.center.z
            for vi in p.vertices:
                wall_v.add(vi)
                (tops if co[vi].z > zc + 0.05 else feet).append(co[vi])
    kt, kf = _kd(tops), _kd(feet)
    edge, base = [], []
    for i, c in enumerate(co):
        e = 0.0
        if i in wall_v:
            _p, _i, dist = kt.find(c)
            e = 1.0 - T.smoothstep(0.0, EDGE_WIDTH, dist)
        b = 0.0
        pf, _i, dist = kf.find(c)
        if pf is not None and c.z <= pf.z + 0.1 and (i not in wall_v or c.z <= pf.z + 0.01):
            b = 1.0 - min(1.0, dist / BASE_WIDTH)      # lineal: exacto entre el pie y la fila a 0.6 m
        edge.append(e)
        base.append(b)
    return edge, base, len(tops), len(feet)


def bake_ao(scene, obj):
    me = obj.data
    if "ao_bake" in me.color_attributes:
        me.color_attributes.remove(me.color_attributes["ao_bake"])
    attr = me.color_attributes.new(name="ao_bake", type="BYTE_COLOR", domain="CORNER")
    me.color_attributes.active_color = attr
    if scene.world is None:
        scene.world = bpy.data.worlds.new("World")
    scene.world.light_settings.distance = AO_DISTANCE
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = AO_SAMPLES
    scene.render.bake.target = "VERTEX_COLORS"
    hidden = []
    for o in bpy.context.view_layer.objects:
        o.select_set(False)
        if o is not obj and o.type == "MESH" and not o.hide_render:
            o.hide_render = True
            hidden.append(o)
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.bake(type="AO", target="VERTEX_COLORS")
    for o in hidden:
        o.hide_render = False
    vals = [0.0] * (len(me.loops) * 4)
    me.color_attributes["ao_bake"].data.foreach_get("color", vals)
    ao_c = vals[0::4]
    me.color_attributes.remove(me.color_attributes["ao_bake"])
    # promedio por vertice: sin costuras de atributo (Decimate y glTF las tratan como cortes)
    nl = len(me.loops)
    loop_v = [0] * nl
    me.loops.foreach_get("vertex_index", loop_v)
    acc = [0.0] * len(me.vertices)
    cnt = [0] * len(me.vertices)
    for i in range(nl):
        acc[loop_v[i]] += ao_c[i]
        cnt[loop_v[i]] += 1
    return [acc[loop_v[i]] / cnt[loop_v[i]] for i in range(nl)]


def build(scene, stats):
    obj = bpy.data.objects["TRN_City"]
    me = obj.data
    edge_v, base_v, n_tops, n_feet = edge_and_base(me)
    ao = bake_ao(scene, obj)
    nl = len(me.loops)
    loop_v = [0] * nl
    me.loops.foreach_get("vertex_index", loop_v)

    def get(name):
        v = [0.0] * (nl * 4)
        me.color_attributes[name].data.foreach_get("color", v)
        return v[0::4]

    ret, dirt, stone = get("retaining_mask"), get("dirt_mask"), get("stone_mask")
    ao_edge = [max(0.0, min(1.0, ao[i] * (1.0 - EDGE_DARK * edge_v[loop_v[i]])
                            * (1.0 - BASE_DARK * base_v[loop_v[i]]))) for i in range(nl)]
    for name in ("ao_edge", "mask_pack"):
        if name in me.color_attributes:
            me.color_attributes.remove(me.color_attributes[name])
    a = me.color_attributes.new(name="ao_edge", type="BYTE_COLOR", domain="CORNER")
    flat = []
    for v in ao_edge:
        flat.extend((v, v, v, 1.0))
    a.data.foreach_set("color", flat)
    pk = me.color_attributes.new(name="mask_pack", type="BYTE_COLOR", domain="CORNER")
    flat = []
    for i in range(nl):
        flat.extend((ret[i], dirt[i], stone[i], ao_edge[i]))
    pk.data.foreach_set("color", flat)
    me.color_attributes.active_color_name = "mask_pack"
    me.color_attributes.render_color_index = me.color_attributes.find("mask_pack")
    mat = terrain_material()
    me.materials.clear()
    me.materials.append(mat)
    ao_sorted = sorted(ao)
    stats["shading"] = {"material": MAT_TERRAIN, "edge_top_verts": n_tops, "wall_foot_verts": n_feet,
                        "edge_width_m": EDGE_WIDTH, "edge_dark": EDGE_DARK, "base_width_m": BASE_WIDTH,
                        "base_dark": BASE_DARK, "ao_distance_m": AO_DISTANCE, "ao_samples": AO_SAMPLES,
                        "ao_bake_objects": "solo TRN_City (piezas ocultas durante el horneado)",
                        "ao_min": round(ao_sorted[0], 3), "ao_p05": round(ao_sorted[int(0.05 * nl)], 3),
                        "ao_median": round(ao_sorted[nl // 2], 3),
                        "colors_srgb": {"ground": COL_GROUND, "dirt": COL_DIRT, "stone": COL_STONE, "wall": COL_WALL},
                        "export_color_attribute": "mask_pack (R retaining, G dirt, B stone, A ao_edge)"}
    return stats["shading"]
