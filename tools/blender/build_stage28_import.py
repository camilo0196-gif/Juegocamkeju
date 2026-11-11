"""
CONCORDIA - Etapa 28: importacion de props CC0 aprobados (Quaternius Fantasy Props MegaKit, Avramania "Low Poly
Medieval" en Sketchfab) a la coleccion BLD_PROPS_INT de blender/concordia_props_v01.blend (despues de
build_stage28_props.py). Primer lote: Mercado (Posada, Casa del Registro, Gran Subasta).

Por asset: importar glTF -> unir en una malla -> escala real (ver SCALE) -> origen en la base (centro x/y, z min = 0) ->
+Y al frente -> materiales de Concordia (MAT_MAP; *_Vertex por el color de vertice) -> UV de caja -> si pasa de 1,700
triangulos, decimar a <= 1,500 y hornear el normal map (1K) del original sobre la version decimada (UV propia
'UVBake'; material derivado <MAT>__N_<prop> que solo anade ese normal) -> -colonly de caja si va en el suelo.
Los ficheros descargados viven fuera del repo (scratchpad); el repo guarda solo el script, el informe y la licencia.
python build_stage28_import.py -- <dir_quaternius_glTF> [<dir_avramania>]
"""

import json
import math
import os
import sys

import bpy
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import concordia_buildings as B  # noqa: E402

REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
BLEND = os.path.join(REPO, "blender", "concordia_props_v01.blend")
EXP_DIR = os.path.join(REPO, "export", "godot")
REPORT = os.path.join(REPO, "docs", "reports", "stage28_props_import.json")
TEX = os.path.join(REPO, "textures", "props")
ORIGINS = {"mercado": Vector((6000.0, -14.0, 0.0)), "oficios": Vector((6000.0, -34.0, 0.0)),
           "clases": Vector((6000.0, -54.0, 0.0))}
STEP = 2.6
SMALL_MAX_M = 0.6                 # pequeno: lado mayor <= 0.6 m
BUDGET = {"pequeno": 500, "mediano": 1500}
NORMAL_RES = {"pequeno": 512, "mediano": 1024}
Q_URL = "https://quaternius.com/packs/fantasypropsmegakit.html"
Q_OGA = "https://opengameart.org/content/fantasy-props-megakit"

# materiales de Quaternius -> Concordia
MAT_MAP = {"MI_Trim_Furniture": "MAT_Wood_Dark", "MI_Trim_Metal": "MAT_Iron_Black", "MI_Trim_Props": "MAT_Limestone_Light",
           "MI_Page_Empty": "MAT_Hide_R05", "MI_Trim_Cloth": "MAT_Cloth_Patch_B", "MI_Trim_Metal_Vertex": "MAT_Bronze_Aged"}

# (nombre en Concordia, fuente, fichero/uid, uso, escala o medida objetivo, cambios de material por asset)
MERCADO = [
    ("PROP_Q_Table_Large", "q", "Table_Large", "Posada: mesa larga", None, {}),
    ("PROP_Q_Chair_1", "q", "Chair_1", "Posada / Registro: silla", None, {}),
    ("PROP_Q_Bench", "q", "Bench", "Posada: banco", None, {}),
    ("PROP_Q_Stool", "q", "Stool", "Posada: taburete", None, {}),
    ("PROP_Q_Barrel_Holder", "q", "Barrel_Holder", "Posada: barril en soporte", None, {}),
    ("PROP_Q_Mug", "q", "Mug", "Posada: jarra", None, {}),
    ("PROP_Q_Table_Plate", "q", "Table_Plate", "Posada: plato", None, {"MI_Trim_Metal": "MAT_Bronze_Aged"}),
    ("PROP_Q_Table_Knife", "q", "Table_Knife", "Posada: cuchillo", None, {}),
    ("PROP_Q_Table_Fork", "q", "Table_Fork", "Posada: tenedor", None, {}),
    ("PROP_Q_Table_Spoon", "q", "Table_Spoon", "Posada: cuchara", None, {}),
    ("PROP_Q_Candle_1", "q", "Candle_1", "Posada / Registro: vela", None, {}),
    ("PROP_Q_CandleStick", "q", "CandleStick", "Posada / Registro: candelero", None, {"MI_Trim_Metal": "MAT_Bronze_Aged"}),
    ("PROP_Q_Chandelier", "q", "Chandelier", "Posada: lampara de techo", None, {}),
    ("PROP_Q_Workbench_Drawers", "q", "Workbench_Drawers", "Registro: cajonera del escritorio", None, {}),
    ("PROP_Q_Shelf_Simple", "q", "Shelf_Simple", "Registro: estante", None, {}),
    ("PROP_Q_BookGroup_Medium_1", "q", "BookGroup_Medium_1", "Registro: libros en estante", None, {}),
    ("PROP_Q_BookStand", "q", "BookStand", "Registro: atril", None, {}),
    ("PROP_Q_Scroll_1", "q", "Scroll_1", "Registro: pergamino", None, {}),
    ("PROP_Q_Scroll_2", "q", "Scroll_2", "Registro: pergamino abierto", None, {}),
    ("PROP_Q_Book_Stack_1", "q", "Book_Stack_1", "Registro: pila de libros", None, {}),
    ("PROP_Q_Book_Stack_2", "q", "Book_Stack_2", "Registro: pila de libros con cierre", None, {}),
    ("PROP_Q_Chest_Wood", "q", "Chest_Wood", "Gran Subasta: arcon de lotes", ("width", 1.0), {}),
    ("PROP_Q_Coin_Pile", "q", "Coin_Pile", "Gran Subasta: monedas", None, {}),
    ("PROP_Q_Pouch_Large", "q", "Pouch_Large", "Gran Subasta: bolsa de monedas", None,
     {"MI_Trim_Metal": "MAT_Bronze_Aged", "MI_Trim_Props_Vertex": "MAT_Hide_R05"}),
    ("PROP_Q_Bag", "q", "Bag", "Gran Subasta / puestos: saco", None, {"MI_Trim_Cloth": "MAT_Cloth_Patch_A"}),
]
AVRAMANIA = [  # uid de Sketchfab (licencia comprobada en cada descarga)
    ("PROP_AV_Village_Hearth", "av", "1b9b17a3cb0f44dd9141e70fba061c71", "Posada: hogar", None, {"_furniture": True}),
    ("PROP_AV_Potcrane", "av", "d041cc0462ab4da6be30fff811765685", "Posada: pescante del hogar", None, {"_furniture": True}),
    ("PROP_AV_Bed", "av", "24704040010a42ceaeffb1631ed1ae9b", "Posada: cama", None, {"_furniture": True}),
    ("PROP_AV_Table", "av", "bd0ad320c35249b9b1a37e2adc061bb9", "Registro: mesa del escritorio", None, {"_furniture": True}),
    ("PROP_AV_Apple", "av", "64e25ccc90c84e3b8c2ad02dd39150ba", "puestos: manzanas", None, {}),
    ("PROP_AV_Carrot", "av", "3f3b24dd3bf24ce49b518bfbd5ec93df", "puestos: zanahorias", None, {}),
    ("PROP_AV_Onion", "av", "a8a9568469524a548ca730b1058de3ef", "puestos: cebollas", None, {}),
    ("PROP_AV_Loaf", "av", "fe8f28bcadaf44a7836e12fe30f9a3dd", "puestos: pan", None, {}),
    ("PROP_AV_Cheese_Wheel", "av", "c66175e51d044dfda9e6edff21d4d38a", "puestos: queso", None, {}),
    ("PROP_AV_Grapes", "av", "cc950686a4dc4ac89edda92b21afca11", "puestos: uvas", None, {}),
    ("PROP_AV_Grain_Sack", "av", "7db2a14529fd4e1f9391c68337f71eac", "puestos: saco de grano", None, {}),
]
OFICIOS = [
    ("PROP_Q_Whetstone", "q", "Whetstone", "Forja: piedra de afilar", None, {}),
    ("PROP_AV_Water_Trough", "av", "2ba720b8921543b69edad075b9d7c5c5", "Forja: pilon de temple", None, {"_furniture": True}),
    ("PROP_Q_Peg_Rack", "q", "Peg_Rack", "Forja / Reparaciones: colgador de herramientas", None, {}),
    ("PROP_AV_Hammer", "av", "34e64ec1bab74f3b921d3078cecd06dc", "Forja / Reparaciones: martillo", None, {"_furniture": True}),
    ("PROP_Q_Workbench", "q", "Workbench", "Carpinteria: banco de carpintero", None, {}),
    ("PROP_AV_Woodpile", "av", "e06f39a8521d4a728f6de1a399e2097a", "Carpinteria: lena", None, {"_furniture": True}),
    ("PROP_AV_Village_Ladder", "av", "b5ee3e7fbb0049059bf23a6724eebc1b", "Carpinteria: escalera de mano", None,
     {"_furniture": True}),
    ("PROP_AV_Cauldron", "av", "eb4311e2df0549d5a5a26edc313c38c4", "Alquimia: caldero", None, {"_furniture": True}),
    ("PROP_Q_Potion_1", "q", "Potion_1", "Alquimia: pocion", None, {}),
    ("PROP_Q_Potion_2", "q", "Potion_2", "Alquimia: pocion", None, {}),
    ("PROP_Q_Potion_4", "q", "Potion_4", "Alquimia: pocion", None, {}),
    ("PROP_AV_Roll", "av", "9cd0c6d36336456e86c2a79e968e47b6", "Hornos: panecillo", None, {}),
    ("PROP_AV_Herb_Bundle", "av", "41ec7f9ddd8c4e999449b5e746790fe4", "Herbolarios: manojo de hierbas", None, {}),
    ("PROP_AV_Pottedplant", "av", "82f2cac9741c467c844c9c5b62ab6050", "Herbolarios: maceta", None, {}),
    ("PROP_AV_Pot", "av", "fa90afdde3e541458de26d42e1323d7d", "Herbolarios: tiesto", None, {"_furniture": True}),
    ("PROP_Q_Pickaxe_Bronze", "q", "Pickaxe_Bronze", "Mineros: pico", None, {}),
    ("PROP_AV_Shovel", "av", "7decd7f6750644fab34f3f54cd9a6a89", "Mineros: pala", None, {"_furniture": True}),
    ("PROP_AV_Rocks", "av", "7aa298b830fc4d6eafa1980adfe0f5cf", "Mineros: mineral", None, {}),
    ("PROP_AV_Lantern", "av", "8a3dc887ea9d48c19ad48469ba11e753", "Mineros: farol", None, {"_furniture": True}),
    ("PROP_Q_Bucket_Wooden_1", "q", "Bucket_Wooden_1", "Pescadores: cubo", None, {}),
    ("PROP_Q_Rope_2", "q", "Rope_2", "Pescadores: cuerda", None, {}),
    ("PROP_AV_Crossbow", "av", "0daff83382444c95b022de235cea1ceb", "Cazadores: ballesta", None, {"_furniture": True}),
    ("PROP_AV_Arrow", "av", "cc820300ee694dd5aae898a87ccc6c67", "Cazadores: flecha", None, {"_furniture": True}),
    ("PROP_AV_Axe", "av", "b8142e327147499a83add0dfcb1a32d9", "Reparaciones: hacha", None, {"_furniture": True}),
    ("PROP_AV_Handaxe", "av", "f12b9a6915a34c59bf4ea3d5634a03f5", "Reparaciones: hachuela", None, {"_furniture": True}),
    ("PROP_Q_Chain_Coil", "q", "Chain_Coil", "Reparaciones: rollo de cadena", None, {}),
]
CLASES = [
    ("PROP_AV_Pew", "av", "ba2de923a54547beaddc1f49e000b3d3", "Clases: banco con respaldo", None, {"_furniture": True}),
    ("PROP_AV_Rack", "av", "3ced62581eb84f9a914cb1d120d2d519", "Clases: armero", None, {"_furniture": True}),
    ("PROP_Q_WeaponStand", "q", "WeaponStand", "Clases: armero grande", None, {}),
    ("PROP_AV_Chest", "av", "94a5f575c311487b8fbd6091b09abd94", "Clases: arcon", None, {"_furniture": True}),
    ("PROP_AV_Shield_Round", "av", "b0f1cb5493bd4af8a829c49816a1cf79", "Clases: escudo redondo", None, {"_furniture": True}),
    ("PROP_Q_Shield_Wooden", "q", "Shield_Wooden", "Clases: escudo de madera", None, {}),
    ("PROP_AV_Armingsword", "av", "b935b180c92c4fe79c067113d8929cb4", "Clases: espada", None, {"_furniture": True}),
    ("PROP_AV_Shortsword", "av", "0be8094364f4482f9ddad92236514b96", "Clases: espada corta", None, {"_furniture": True}),
    ("PROP_AV_Dagger", "av", "78265b91861e406ea62acaa67b78d60b", "Clases: daga", None, {"_furniture": True}),
    ("PROP_AV_Staff", "av", "3b71fc881aaf4602ad53605474baf0ff", "Clases: baston", None, {"_furniture": True}),
    ("PROP_AV_Rug", "av", "3899142ec92c46059d35fc0fa1a0bd41", "Clases: esterilla", None, {"_furniture": True}),
    ("PROP_Q_Shelf_Arch", "q", "Shelf_Arch", "Casa de Reposicion: estante de arco", None, {}),
    ("PROP_Q_SmallBottles_1", "q", "SmallBottles_1", "Casa de Reposicion: frascos", None, {}),
]
BATCH_TITLES = {"mercado": "Mercado (Posada, Casa del Registro, Gran Subasta)", "oficios": "Oficios (talleres y gremios)",
                "clases": "Clases (8 salones y Casa de Reposicion)"}
ON_TABLE = ("Potion", "Roll", "Herb_Bundle", "Rocks", "Dagger", "SmallBottles", "Arrow", "Hammer", "Mug", "Plate", "Knife", "Fork", "Spoon", "Candle", "Scroll", "Book_Stack", "Coin", "Pouch", "Apple",
            "Carrot", "Onion", "Loaf", "Cheese", "Grapes", "BookGroup")


PALETTE_TARGETS = ["MAT_Wood_Dark", "MAT_Wood_Light", "MAT_Iron_Black", "MAT_Bronze_Aged", "MAT_Limestone_Worn",
                   "MAT_Limestone_Light", "MAT_Hide_R05", "MAT_Felt_R05", "MAT_Straw", "MAT_Herb_Green", "MAT_Leaf_Old",
                   "MAT_Cloth_Patch_A", "MAT_Cloth_Patch_B", "MAT_Cloth_Patch_C", "MAT_Roof_Tile_Ocher", "MAT_Ash_Gray"]
FURNITURE_TARGETS = ["MAT_Wood_Dark", "MAT_Wood_Light", "MAT_Iron_Black", "MAT_Limestone_Worn", "MAT_Limestone_Light",
                     "MAT_Ash_Gray", "MAT_Straw", "MAT_Cloth_Patch_A", "MAT_Cloth_Patch_B", "MAT_Cloth_Patch_C",
                     "MAT_Hide_R05", "MAT_Bronze_Aged"]
SRC_BLEND = os.path.join(REPO, "blender", "concordia_v26.blend")
_AVG = {}


def ensure_mats(names):
    miss = [n for n in names if bpy.data.materials.get(n) is None]
    if miss:
        with bpy.data.libraries.load(SRC_BLEND, link=False) as (df, dt):
            dt.materials = [m for m in df.materials if m in miss]


def avg_color(mname):
    """Color medio del albedo de un material de Concordia (o su Base Color)."""
    if mname in _AVG:
        return _AVG[mname]
    import numpy as np
    m = bpy.data.materials[mname]
    bsdf = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    col = None
    for lk in m.node_tree.links:
        if lk.to_socket == bsdf.inputs["Base Color"]:
            nd = lk.from_node
            while nd.type != "TEX_IMAGE" and nd.inputs and any(i.links for i in nd.inputs):
                nd = next(i.links[0].from_node for i in nd.inputs if i.links)
            if nd.type == "TEX_IMAGE" and nd.image:
                px = np.array(nd.image.pixels[:]).reshape(-1, 4)[:, :3]
                col = px[:: max(1, len(px) // 20000)].mean(axis=0)
    if col is None:
        col = np.array(bsdf.inputs["Base Color"].default_value[:3])
    _AVG[mname] = col
    return col


def palette_remap(ob, cands=None):
    """Avramania: cada cara toma el color de la paleta en su UV y pasa al material de Concordia mas cercano."""
    import numpy as np
    me = ob.data
    img = None
    for s in ob.material_slots:
        if s.material and s.material.use_nodes:
            img = next((n.image for n in s.material.node_tree.nodes if n.type == "TEX_IMAGE" and n.image), img)
    slot_cols = []
    for sl in ob.material_slots:
        bsdf = next((n for n in sl.material.node_tree.nodes if n.type == "BSDF_PRINCIPLED"), None) if sl.material else None
        slot_cols.append(np.array(bsdf.inputs["Base Color"].default_value[:3]) if bsdf else np.array((0.5, 0.5, 0.5)))
    if img is not None:
        W, H = img.size
        px = np.array(img.pixels[:]).reshape(H, W, 4)[:, :, :3]
    uvl = me.uv_layers.active.data if me.uv_layers else None
    targets, face_t, cols = [], [], {}
    ref = {m: avg_color(m) for m in (cands or PALETTE_TARGETS)}
    for p in me.polygons:
        if img is None or uvl is None:                  # sin paleta: color base del material de la cara
            c = slot_cols[p.material_index] if p.material_index < len(slot_cols) else np.array((0.5, 0.5, 0.5))
        else:
            u = sum(uvl[li].uv[0] for li in p.loop_indices) / len(p.loop_indices)
            v = sum(uvl[li].uv[1] for li in p.loop_indices) / len(p.loop_indices)
            c = px[min(H - 1, max(0, int(v * H))), min(W - 1, max(0, int((u % 1.0) * W)))]
        key = tuple(round(float(x), 2) for x in c)
        if key not in cols:
            cols[key] = min(ref, key=lambda m: float(((ref[m] - c) ** 2).sum()))
        t = cols[key]
        if t not in targets:
            targets.append(t)
        face_t.append(targets.index(t))
    me.materials.clear()
    for t in targets:
        me.materials.append(bpy.data.materials[t])
    for p, i in zip(me.polygons, face_t):
        p.material_index = i
    return ["mdvl_palette" if img is not None else "colores de material"], targets, {str(k): v for k, v in cols.items()}


def tris(o):
    return sum(len(p.vertices) - 2 for p in o.data.polygons)


def import_one(path):
    before = set(bpy.data.objects)
    if path.endswith((".gltf", ".glb")):
        bpy.ops.import_scene.gltf(filepath=path)
    else:
        raise RuntimeError(f"formato no admitido: {path}")
    new = [o for o in bpy.data.objects if o not in before]
    meshes = [o for o in new if o.type == "MESH"]
    # restos en algunos glb de Sketchfab: mallas sin material (p. ej. un Icosphere suelto) si hay otras con material
    if any(o.material_slots and any(s.material for s in o.material_slots) for o in meshes):
        junk = [o for o in meshes if not any(s.material for s in o.material_slots)]
        meshes = [o for o in meshes if o not in junk]
    for o in meshes:                                        # mallas con esqueleto: se quedan en la pose de reposo
        for m in [m for m in o.modifiers if m.type == "ARMATURE"]:
            o.modifiers.remove(m)
    for o in meshes:
        o.data = o.data.copy()
        mw = o.matrix_world.copy()
        o.parent = None
        o.matrix_world = mw
    bpy.ops.object.select_all(action="DESELECT")
    for o in meshes:
        o.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    if len(meshes) > 1:
        bpy.ops.object.join()
    ob = bpy.context.view_layer.objects.active
    keep = ob.name
    for o in [x for x in bpy.data.objects if x not in before and x.name != keep]:
        bpy.data.objects.remove(o)
    return ob


def normalize(ob, fit):
    vs = [v.co for v in ob.data.vertices]
    lo = Vector((min(v.x for v in vs), min(v.y for v in vs), min(v.z for v in vs)))
    hi = Vector((max(v.x for v in vs), max(v.y for v in vs), max(v.z for v in vs)))
    s = 1.0
    if fit:
        kind, val = fit
        s = val / max(hi.x - lo.x, hi.y - lo.y) if kind == "width" else val / (hi.z - lo.z)
    c = Vector(((lo.x + hi.x) / 2, (lo.y + hi.y) / 2, lo.z))
    ob.data.transform(Matrix.Scale(s, 4) @ Matrix.Translation(-c))
    ob.data.update()
    return s


def remap(ob, overrides):
    """Materiales de origen -> Concordia; los *_Vertex se reparten por la luminancia del color de vertice."""
    me = ob.data
    src = [s.material.name if s.material else "" for s in ob.material_slots]
    col = me.color_attributes.active_color if me.color_attributes else None
    targets = []
    face_t = []
    # *_Vertex: cada color distinto (un libro, una tapa) recibe un material de Concordia por turno; lo claro = papel
    keys = {}
    if col is not None:
        for p in me.polygons:
            sname = src[p.material_index] if p.material_index < len(src) else ""
            if sname.split(".")[0].endswith("_Vertex"):
                li = p.loop_indices[0]
                c = col.data[li].color if col.domain == "CORNER" else col.data[me.loops[li].vertex_index].color
                keys.setdefault(p.index, tuple(round(x, 2) for x in c[:3]))
    uniq = sorted(set(keys.values()), key=lambda c: 0.3 * c[0] + 0.59 * c[1] + 0.11 * c[2])
    cyc = ["MAT_Hide_R05", "MAT_Cloth_Patch_C", "MAT_Felt_R05", "MAT_Cloth_Patch_A"]
    cmap = {}
    for i, c in enumerate(uniq):
        lum = 0.3 * c[0] + 0.59 * c[1] + 0.11 * c[2]
        cmap[c] = "MAT_Limestone_Light" if lum > 0.55 else cyc[i % len(cyc)]
    for p in me.polygons:
        sname = src[p.material_index] if p.material_index < len(src) else ""
        base = sname.split(".")[0]
        t = overrides.get(base) or MAT_MAP.get(base)
        if t is None and p.index in keys:
            t = cmap[keys[p.index]]
        if t is None:
            t = "MAT_Wood_Light" if "wood" in base.lower() else "MAT_Wood_Dark"
        if t not in targets:
            targets.append(t)
        face_t.append(targets.index(t))
    me.materials.clear()
    for t in targets:
        me.materials.append(bpy.data.materials[t])
    for p, i in zip(me.polygons, face_t):
        p.material_index = i
    for a in list(me.color_attributes):
        me.color_attributes.remove(a)
    return src, targets


def bake_normal(high, low, name, res=1024):
    """Normal map en espacio tangente del original sobre la version decimada (1K o 512), UV 'UVBake'."""
    os.makedirs(TEX, exist_ok=True)
    uv = low.data.uv_layers.new(name="UVBake")
    low.data.uv_layers.active = uv
    bpy.ops.object.select_all(action="DESELECT")
    low.select_set(True)
    bpy.context.view_layer.objects.active = low
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.smart_project(angle_limit=math.radians(66), island_margin=0.02)
    bpy.ops.object.mode_set(mode="OBJECT")
    tag = "1k" if res >= 1024 else f"{res}"
    for old in (f"{name}_normal_1k.png", f"{name}_normal_512.png"):
        if os.path.exists(os.path.join(TEX, old)):
            os.remove(os.path.join(TEX, old))
    img = bpy.data.images.new(f"{name}_normal_{tag}", res, res, alpha=False)
    img.colorspace_settings.name = "Non-Color"
    path = os.path.join(TEX, f"{name}_normal_{tag}.png")
    # materiales derivados: Concordia + nodo de imagen activo para el horneado
    new_mats = []
    for i, slot in enumerate(low.material_slots):
        base = slot.material
        mname = f"{base.name.split('__')[0]}__N_{name[5:]}"
        old = bpy.data.materials.get(mname)
        if old is not None:
            old.name = f"{mname}__old"                    # restos de una pasada anterior (sin usuarios al guardar)
        m = base.copy()
        m.name = mname
        nt = m.node_tree
        tex = nt.nodes.new("ShaderNodeTexImage")
        tex.image = img
        tex.name = "BakeNormal"
        uvn = nt.nodes.new("ShaderNodeUVMap")
        uvn.uv_map = "UVBake"
        nt.links.new(uvn.outputs["UV"], tex.inputs["Vector"])
        nt.nodes.active = tex
        slot.material = m
        new_mats.append((m, tex))
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = 4
    bpy.ops.object.select_all(action="DESELECT")
    high.select_set(True)
    low.select_set(True)
    bpy.context.view_layer.objects.active = low
    bpy.ops.object.bake(type="NORMAL", use_selected_to_active=True, cage_extrusion=0.02, margin=8,
                        normal_space="TANGENT")
    img.filepath_raw = path
    img.file_format = "PNG"
    img.save()
    for m, tex in new_mats:
        nt = m.node_tree
        bsdf = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
        nm = nt.nodes.new("ShaderNodeNormalMap")
        nm.uv_map = "UVBake"
        nt.links.new(tex.outputs["Color"], nm.inputs["Color"])
        for lk in list(bsdf.inputs["Normal"].links):
            nt.links.remove(lk)
        nt.links.new(nm.outputs["Normal"], bsdf.inputs["Normal"])
        m["note"] = f"{m.name.split('__')[0]} + normal map horneado de {name} (decimado)"
    low.data.uv_layers.active = low.data.uv_layers[0]
    low.data.uv_layers[0].active_render = True
    return os.path.relpath(path, REPO)


def collider(ob, col):
    vs = [v.co for v in ob.data.vertices]
    lo = Vector((min(v.x for v in vs), min(v.y for v in vs), 0.0))
    hi = Vector((max(v.x for v in vs), max(v.y for v in vs), max(v.z for v in vs)))
    c = [(lo.x, lo.y, lo.z), (hi.x, lo.y, lo.z), (hi.x, hi.y, lo.z), (lo.x, hi.y, lo.z),
         (lo.x, lo.y, hi.z), (hi.x, lo.y, hi.z), (hi.x, hi.y, hi.z), (lo.x, hi.y, hi.z)]
    me = bpy.data.meshes.new(f"{ob.name}-colonly")
    me.from_pydata(c, [], [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)])
    o = bpy.data.objects.new(f"{ob.name}-colonly", me)
    col.objects.link(o)
    o.parent = ob
    o.hide_render = True
    return o


def size_class(ob):
    d = ob.dimensions
    return "pequeno" if max(d.x, d.y, d.z) <= SMALL_MAX_M else "mediano"


def run_batch(batch, items, qdir, avdir, avmeta, col, tmp, st):
    for o in [o for o in col.objects if o.get("prop_batch") == batch or
              (batch == "mercado" and o.get("prop_source", "").startswith(("Quaternius", "Avramania"))
               and not o.get("prop_batch"))]:
        mes = [c.data for c in o.children if c.type == "MESH"] + [o.data]
        for c in list(o.children):
            bpy.data.objects.remove(c)
        bpy.data.objects.remove(o)
        for me in mes:                                      # sin esto la malla nueva saldria como PROP_x.001
            if me is not None and me.users == 0:
                bpy.data.meshes.remove(me)
    for me in [m for m in bpy.data.meshes if m.users == 0 and m.name.startswith(("PROP_Q_", "PROP_AV_"))]:
        bpy.data.meshes.remove(me)
    rep = {"batch": BATCH_TITLES[batch], "props": {}, "skipped": [], "budget": BUDGET, "small_max_m": SMALL_MAX_M}
    objs = []
    for idx, (name, srcname, key, use, fit, over) in enumerate(items):
        if srcname == "q":
            path = os.path.join(qdir, f"{key}.gltf")
            meta = {"author": "Quaternius", "url": Q_URL, "mirror": Q_OGA, "license": "CC0 1.0 (License_Standard.txt)",
                    "pack": "Fantasy Props MegaKit (Standard)", "file": f"Exports/glTF/{key}.gltf"}
        else:
            m = avmeta.get(key)
            if not m or not m.get("file") or not m.get("page_checked"):
                rep["skipped"].append({"name": name, "reason": "sin descarga o sin licencia CC0 comprobada en la pagina"})
                continue
            path = os.path.join(avdir, m["file"])
            meta = {"author": "Avramania", "url": m["url"], "license": m["license"], "license_checked": m["checked"],
                    "page_license_text": m.get("page_license_text"), "file": m["file"], "sketchfab_name": m["name"]}
        ob = import_one(path)
        ob.name = name
        ob.data.name = name
        t0 = tris(ob)
        scale = normalize(ob, fit)
        if srcname == "av":
            src, targets, pal = palette_remap(ob, FURNITURE_TARGETS if over.get("_furniture") else None)
        else:
            src, targets = remap(ob, over)
            pal = None
        B.box_uv(ob)
        cls = size_class(ob)
        budget = BUDGET[cls]
        info = {"use": use, "source": srcname, "key": key, **meta, "tris_original": t0, "scale": round(scale, 3),
                "size_class": cls, "budget": budget,
                "src_materials": sorted(set(s.split(".")[0] for s in src)), "materials": targets}
        if pal:
            info["palette_map"] = pal
        if t0 > budget:
            high = ob.copy()
            high.data = ob.data.copy()
            tmp.objects.link(high)
            bpy.context.view_layer.objects.active = ob
            k = 0
            while tris(ob) > budget and k < 6:
                mod = ob.modifiers.new("dec", "DECIMATE")
                mod.ratio = (budget - 20) / tris(ob)
                bpy.ops.object.modifier_apply(modifier=mod.name)
                k += 1
            info["normal_map"] = bake_normal(high, ob, name, NORMAL_RES[cls])
            zmin = min(v.co.z for v in ob.data.vertices)          # el decimado puede despegar la base del suelo
            if abs(zmin) > 1e-4:
                ob.data.transform(Matrix.Translation((0, 0, -zmin)))
                ob.data.update()
            info["normal_res"] = NORMAL_RES[cls]
            info["decimated_to"] = tris(ob)
            info["materials"] = [s.material.name for s in ob.material_slots]
            bpy.data.objects.remove(high)
        for c in list(ob.users_collection):
            c.objects.unlink(ob)
        col.objects.link(ob)
        r, c_ = divmod(idx, 7)
        ob.location = ORIGINS[batch] + Vector((c_ * STEP, -r * STEP, 0.0))
        ob["prop_source"] = f"{meta['author']} (CC0)"
        ob["prop_batch"] = batch
        ob["prop_note"] = use
        ob["prop_tris"] = tris(ob)
        ob["prop_url"] = meta["url"]
        info["tris"] = tris(ob)
        dims = ob.dimensions
        info["size_m"] = [round(dims.x, 3), round(dims.y, 3), round(dims.z, 3)]
        vz = min(v.co.z for v in ob.data.vertices)
        info["origin_at_base"] = abs(vz) < 1e-3
        info["ok"] = info["tris"] <= budget and info["origin_at_base"] and all(
            mm.split("__")[0] in PALETTE_TARGETS + FURNITURE_TARGETS + ["MAT_Felt_R05", "MAT_Bronze_Aged"]
            for mm in info["materials"])
        if not any(k_ in key or k_ in name for k_ in ON_TABLE) and cls == "mediano":
            objs.append(collider(ob, col))
            info["colonly"] = True
        objs.append(ob)
        rep["props"][name] = info
        print("PROP", batch, name, t0, "->", info["tris"], cls, info["ok"], info["materials"], flush=True)
    rep["total_tris"] = sum(v["tris"] for v in rep["props"].values())
    rep["all_ok"] = all(v["ok"] for v in rep["props"].values())
    import stage11_godot as G
    exp = os.path.join(EXP_DIR, f"props_int_{batch}.glb")
    size = G.export_glb(objs, exp)
    rep["export"] = {"file": os.path.relpath(exp, REPO), "mb": round(size / 2 ** 20, 3), **G.glb_info(exp)}
    st.setdefault("batches", {})[batch] = rep
    return rep


def main():
    args = sys.argv[sys.argv.index("--") + 1:]
    qdir, avdir = args[0], args[1]
    batches = args[2:] or ["mercado"]
    with open(os.path.join(avdir, "licenses.json")) as fh:
        avmeta = json.load(fh)
    bpy.ops.wm.open_mainfile(filepath=BLEND)
    col = bpy.data.collections["BLD_PROPS_INT"]
    ensure_mats(PALETTE_TARGETS + ["MAT_Hide_R05", "MAT_Felt_R05", "MAT_Bronze_Aged"])
    tmp = bpy.data.collections.new("TMP_IMPORT")
    bpy.context.scene.collection.children.link(tmp)
    lc = bpy.context.view_layer.layer_collection.children[tmp.name]
    bpy.context.view_layer.active_layer_collection = lc
    st = {}
    if os.path.exists(REPORT):
        with open(REPORT) as fh:
            st = json.load(fh)
        if "batches" not in st:
            st = {}
    st["blend"] = os.path.relpath(BLEND, REPO)
    lists = {"mercado": MERCADO + AVRAMANIA, "oficios": OFICIOS, "clases": CLASES}
    for b in batches:
        rep = run_batch(b, lists[b], qdir, avdir, avmeta, col, tmp, st)
        print("BATCH", b, rep["total_tris"], "ok", rep["all_ok"], rep["export"]["mb"], "skipped", rep["skipped"], flush=True)
    bpy.data.collections.remove(tmp)
    bpy.data.orphans_purge(do_local_ids=True, do_linked_ids=True, do_recursive=True)   # restos de los glTF importados
    bpy.ops.file.make_paths_relative()
    bpy.ops.wm.save_as_mainfile(filepath=BLEND, compress=True)
    with open(REPORT, "w") as fh:
        json.dump(st, fh, indent=1, ensure_ascii=False)


if __name__ == "__main__":
    main()
