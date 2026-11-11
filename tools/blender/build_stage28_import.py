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
EXP = os.path.join(REPO, "export", "godot", "props_int_mercado.glb")
REPORT = os.path.join(REPO, "docs", "reports", "stage28_props_import.json")
TEX = os.path.join(REPO, "textures", "props")
ORIGIN = Vector((6000.0, -14.0, 0.0))
STEP = 2.6
DECIMATE_OVER = 1700
DECIMATE_TO = 1500
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
ON_TABLE = ("Mug", "Plate", "Knife", "Fork", "Spoon", "Candle", "Scroll", "Book_Stack", "Coin", "Pouch", "Apple",
            "Carrot", "Onion", "Loaf", "Cheese", "Grapes", "BookGroup")


PALETTE_TARGETS = ["MAT_Wood_Dark", "MAT_Wood_Light", "MAT_Iron_Black", "MAT_Bronze_Aged", "MAT_Limestone_Worn",
                   "MAT_Limestone_Light", "MAT_Hide_R05", "MAT_Felt_R05", "MAT_Straw", "MAT_Herb_Green", "MAT_Leaf_Old",
                   "MAT_Cloth_Patch_A", "MAT_Cloth_Patch_B", "MAT_Cloth_Patch_C", "MAT_Roof_Tile_Ocher", "MAT_Ash_Gray"]
FURNITURE_TARGETS = ["MAT_Wood_Dark", "MAT_Wood_Light", "MAT_Iron_Black", "MAT_Limestone_Worn", "MAT_Limestone_Light",
                     "MAT_Ash_Gray", "MAT_Straw", "MAT_Cloth_Patch_A", "MAT_Cloth_Patch_B", "MAT_Cloth_Patch_C",
                     "MAT_Hide_R05"]
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
    W, H = img.size
    px = np.array(img.pixels[:]).reshape(H, W, 4)[:, :, :3]
    uvl = me.uv_layers.active.data
    targets, face_t, cols = [], [], {}
    ref = {m: avg_color(m) for m in (cands or PALETTE_TARGETS)}
    for p in me.polygons:
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
    return ["mdvl_palette"], targets, {str(k): v for k, v in cols.items()}


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


def bake_normal(high, low, name):
    """Normal map en espacio tangente del original sobre la version decimada, 1K, UV 'UVBake'."""
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
    img = bpy.data.images.new(f"{name}_normal_1k", 1024, 1024, alpha=False)
    img.colorspace_settings.name = "Non-Color"
    path = os.path.join(TEX, f"{name}_normal_1k.png")
    # materiales derivados: Concordia + nodo de imagen activo para el horneado
    new_mats = []
    for i, slot in enumerate(low.material_slots):
        base = slot.material
        m = base.copy()
        m.name = f"{base.name}__N_{name[5:]}"
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


def main():
    args = sys.argv[sys.argv.index("--") + 1:]
    qdir = args[0]
    avdir = args[1] if len(args) > 1 else None
    avmeta = {}
    if avdir and os.path.exists(os.path.join(avdir, "licenses.json")):
        with open(os.path.join(avdir, "licenses.json")) as fh:
            avmeta = json.load(fh)
    bpy.ops.wm.open_mainfile(filepath=BLEND)
    col = bpy.data.collections["BLD_PROPS_INT"]
    ensure_mats(PALETTE_TARGETS + ["MAT_Hide_R05", "MAT_Felt_R05"])
    tmp = bpy.data.collections.new("TMP_IMPORT")
    bpy.context.scene.collection.children.link(tmp)
    lc = bpy.context.view_layer.layer_collection.children[tmp.name]
    bpy.context.view_layer.active_layer_collection = lc
    for o in [o for o in col.objects if o.get("prop_source", "").startswith(("Quaternius", "Avramania"))]:
        for c in list(o.children):
            bpy.data.objects.remove(c)
        bpy.data.objects.remove(o)
    rep = {"blend": os.path.relpath(BLEND, REPO), "batch": "Mercado (Posada, Casa del Registro, Gran Subasta)",
           "props": {}, "skipped": []}
    items = MERCADO + (AVRAMANIA if avdir else [])
    objs = []
    for idx, (name, srcname, key, use, fit, over) in enumerate(items):
        if srcname == "q":
            path = os.path.join(qdir, f"{key}.gltf")
            meta = {"author": "Quaternius", "url": Q_URL, "mirror": Q_OGA, "license": "CC0 1.0 (License_Standard.txt)",
                    "pack": "Fantasy Props MegaKit (Standard)", "file": f"Exports/glTF/{key}.gltf"}
        else:
            m = avmeta.get(key)
            if not m:
                rep["skipped"].append({"name": name, "reason": "sin descarga de Sketchfab"})
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
        info = {"use": use, "source": srcname, "key": key, **meta, "tris_original": t0, "scale": round(scale, 3),
                "src_materials": sorted(set(s.split(".")[0] for s in src)), "materials": targets}
        if pal:
            info["palette_map"] = pal
        if t0 > DECIMATE_OVER:
            high = ob.copy()
            high.data = ob.data.copy()
            tmp.objects.link(high)
            mod = ob.modifiers.new("dec", "DECIMATE")
            mod.ratio = (DECIMATE_TO - 20) / t0
            bpy.context.view_layer.objects.active = ob
            bpy.ops.object.modifier_apply(modifier=mod.name)
            k = 0
            while tris(ob) > DECIMATE_TO and k < 5:
                mod = ob.modifiers.new("dec", "DECIMATE")
                mod.ratio = (DECIMATE_TO - 20) / tris(ob)
                bpy.ops.object.modifier_apply(modifier=mod.name)
                k += 1
            info["normal_map"] = bake_normal(high, ob, name)
            info["decimated_to"] = tris(ob)
            info["materials"] = [s.material.name for s in ob.material_slots]
            bpy.data.objects.remove(high)
        for c in list(ob.users_collection):
            c.objects.unlink(ob)
        col.objects.link(ob)
        r, c_ = divmod(idx, 7)
        ob.location = ORIGIN + Vector((c_ * STEP, -r * STEP, 0.0))
        ob["prop_source"] = f"{meta['author']} (CC0)"
        ob["prop_note"] = use
        ob["prop_tris"] = tris(ob)
        ob["prop_url"] = meta["url"]
        info["tris"] = tris(ob)
        dims = ob.dimensions
        info["size_m"] = [round(dims.x, 3), round(dims.y, 3), round(dims.z, 3)]
        if not any(k_ in key or k_ in name for k_ in ON_TABLE):
            objs.append(collider(ob, col))
            info["colonly"] = True
        objs.append(ob)
        rep["props"][name] = info
        print("PROP", name, t0, "->", info["tris"], info["materials"], flush=True)
    bpy.data.collections.remove(tmp)
    rep["total_tris"] = sum(v["tris"] for v in rep["props"].values())
    import stage11_godot as G
    size = G.export_glb(objs, EXP)
    rep["export"] = {"file": os.path.relpath(EXP, REPO), "mb": round(size / 2 ** 20, 3), **G.glb_info(EXP)}
    bpy.ops.file.make_paths_relative()
    bpy.ops.wm.save_as_mainfile(filepath=BLEND, compress=True)
    with open(REPORT, "w") as fh:
        json.dump(rep, fh, indent=1, ensure_ascii=False)
    print("TOTAL", rep["total_tris"], rep["export"], "skipped", rep["skipped"])


if __name__ == "__main__":
    main()
