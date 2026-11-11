"""
CONCORDIA - Etapa 28: props hechos a mano (props_mano.py) en la coleccion BLD_PROPS_INT.
-> blender/concordia_props_v01.blend, export/godot/props_int_mano.glb, docs/reports/stage28_props_mano.json

Comprueba por prop: <= 1,000 triangulos, origen en la base (z minimo = 0), solo materiales de Concordia; anota medidas,
materiales y una caja -colonly para los que van en el suelo. Hoja: los 4 de la lista de IA en la fila 0 y los 14
triviales debajo (filas de 5, paso 2.6 m) desde (6000, 0, 0).
"""

import json
import os
import random
import sys

import bpy
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import concordia_const as C  # noqa: E402
import bld_kit as K  # noqa: E402
import interior_kit as IK  # noqa: E402
import props_mano as PM  # noqa: E402

REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
SRC = os.path.join(REPO, "blender", f"{C.BLEND_BASENAME}_v26.blend")
OUT = os.path.join(REPO, "blender", "concordia_props_v01.blend")
EXP = os.path.join(REPO, "export", "godot", "props_int_mano.glb")
REPORT = os.path.join(REPO, "docs", "reports", "stage28_props_mano.json")
ORIGIN = Vector((6000.0, 0.0, 0.0))
STEP = 2.6
NO_COL = ("PROP_Miner_Helmet", "PROP_Auction_Gavel", "PROP_Ink_Seal", "PROP_Bench_Vise")  # van sobre mesas
MATS = ["MAT_Limestone_Worn", "MAT_Limestone_Light", "MAT_Wood_Dark", "MAT_Wood_Light", "MAT_Iron_Black",
        "MAT_Bronze_Aged", "MAT_Shard_Blue", "MAT_Ash_Gray", "MAT_Cloth_Patch_A", "MAT_Cloth_Patch_B",
        "MAT_Cloth_Patch_C"] + PM.MATS_EXTRA


def collection(name):
    c = bpy.data.collections.get(name) or bpy.data.collections.new(name)
    if c.name not in bpy.context.scene.collection.children:
        bpy.context.scene.collection.children.link(c)
    return c


def sheet_pos(name):
    keys = list(PM.PROPS)
    if name in PM.AI_FOUR:
        i = PM.AI_FOUR.index(name)
        return ORIGIN + Vector((i * STEP, 0.0, 0.0))
    j = [k for k in keys if k not in PM.AI_FOUR].index(name)
    return ORIGIN + Vector(((j % 5) * STEP, -STEP * (1 + j // 5), 0.0))


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    with bpy.data.libraries.load(SRC, link=False) as (df, dt):
        dt.materials = [m for m in df.materials if m in MATS]
    missing = [m for m in MATS if bpy.data.materials.get(m) is None]
    if missing:
        raise RuntimeError(f"faltan materiales: {missing}")
    col = collection("BLD_PROPS_INT")
    rep = {"source": os.path.relpath(SRC, REPO), "max_tris": PM.MAX_TRIS, "props": {}}
    objs = []
    for name, (fn, note) in PM.PROPS.items():
        rng = random.Random(f"{name}-2801")
        mb = K.MB()
        fn(mb, rng)
        o = IK.to_obj(mb, name, col)
        o.data.name = name
        zmin = min(v.co.z for v in o.data.vertices)
        if -0.03 < zmin < 0.0:          # pies de varilla que asoman bajo el suelo: se recortan al plano z = 0
            for v in o.data.vertices:
                v.co.z = max(v.co.z, 0.0)
            o.data.update()
        vs = [v.co for v in o.data.vertices]
        lo = Vector((min(v.x for v in vs), min(v.y for v in vs), min(v.z for v in vs)))
        hi = Vector((max(v.x for v in vs), max(v.y for v in vs), max(v.z for v in vs)))
        t = IK.tris(o)
        mats = sorted({o.data.materials[p.material_index].name for p in o.data.polygons})
        bad = [m for m in mats if m not in MATS]
        if t > PM.MAX_TRIS or bad or abs(lo.z) > 1e-3:
            raise RuntimeError(f"{name}: tris {t}, materiales ajenos {bad}, z min {lo.z:.4f}")
        o.location = sheet_pos(name)
        o["prop_source"] = "a mano (etapa 28, tools/blender/props_mano.py)"
        o["prop_note"] = note
        o["prop_tris"] = t
        objs.append(o)
        if name not in NO_COL:
            me = bpy.data.meshes.new(f"{name}-colonly")
            c = [(lo.x, lo.y, lo.z), (hi.x, lo.y, lo.z), (hi.x, hi.y, lo.z), (lo.x, hi.y, lo.z),
                 (lo.x, lo.y, hi.z), (hi.x, lo.y, hi.z), (hi.x, hi.y, hi.z), (lo.x, hi.y, hi.z)]
            me.from_pydata(c, [], [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)])
            cb = bpy.data.objects.new(f"{name}-colonly", me)
            col.objects.link(cb)
            cb.parent = o
            cb.hide_render = True
            objs.append(cb)
        rep["props"][name] = {"note": note, "tris": t, "size_m": [round(hi[i] - lo[i], 3) for i in range(3)],
                              "materials": mats, "colonly": name not in NO_COL,
                              "group": "IA -> a mano" if name in PM.AI_FOUR else "trivial"}
    rep["total_tris"] = sum(p["tris"] for p in rep["props"].values())
    import stage11_godot as G
    size = G.export_glb(objs, EXP)
    rep["export"] = {"file": os.path.relpath(EXP, REPO), "mb": round(size / 2 ** 20, 3), **G.glb_info(EXP)}
    bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
    os.makedirs(os.path.dirname(REPORT), exist_ok=True)
    with open(REPORT, "w") as fh:
        json.dump(rep, fh, indent=1, ensure_ascii=False)
    print("RESULT", json.dumps({k: (v["tris"], v["size_m"]) for k, v in rep["props"].items()}))
    print("TOTAL", rep["total_tris"], rep["export"])


if __name__ == "__main__":
    main()
