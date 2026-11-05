"""
CONCORDIA - Etapa 10 (texturas reales de Poly Haven, ORM, mascaras de taludes y foso, transiciones). v09 -> v10.

Antes: python tools/blender/stage10_polyhaven.py   (descarga originales + albedo ajustado + ORM + polyhaven.json)
Uso:   python tools/blender/build_stage10.py [--no-export]
No modifica ninguna version anterior del .blend.
"""

import argparse
import json
import os
import sys
import time

import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import concordia_const as C  # noqa: E402

REPO = os.path.abspath(os.path.join(HERE, "..", ".."))


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    p = argparse.ArgumentParser()
    p.add_argument("--in", dest="inp", default=os.path.join(REPO, "blender", f"{C.BLEND_BASENAME}_v09.blend"))
    p.add_argument("--out", default=os.path.join(REPO, "blender", f"{C.BLEND_BASENAME}_v10.blend"))
    p.add_argument("--report", default=os.path.join(REPO, "docs", "reports", "stage10_textures.json"))
    p.add_argument("--export-dir", default=os.path.join(REPO, "export", "godot"))
    p.add_argument("--no-export", action="store_true")
    a = p.parse_args(argv)
    assert os.path.abspath(a.out) != os.path.abspath(a.inp)
    stats = {"timings_s": {}}
    bpy.ops.wm.open_mainfile(filepath=a.inp)
    import stage10_apply as AP
    t0 = time.time()
    AP.build(stats)
    stats["timings_s"]["apply"] = round(time.time() - t0, 1)
    lib_col, lib_objs, cells = AP.library()
    stats["material_library"] = [c[0] for c in cells]
    if not a.no_export:
        import stage02_chunks as CH
        import stage08_exterior as X
        t0 = time.time()
        CH.build(bpy.context.scene, stats, a.export_dir,
                 {"concordia_plaza.glb": ["PLAZA"], "concordia_districts_markers.glb": ["MARKERS_DISTRICTS"],
                  "concordia_moradas_markers.glb": [f"MARKERS_Morada_{k}" for k in ("NE", "NO", "SO", "SE")],
                  "concordia_cauce.glb": ["CAUCE"]})
        col = bpy.data.collections["EXTERIOR"]
        X.chunks(bpy.data.objects["TRN_Exterior"], col, os.path.join(a.export_dir, "concordia_exterior.glb"),
                 [o for o in col.objects if o.name.startswith("EXT_")], stats)
        for fname, cname in (("concordia_wall_kit.glb", "WALL_KIT"), ("concordia_wall_layout.glb", "WALL_LAYOUT")):
            objs = [o for o in bpy.data.collections[cname].all_objects if o.type in ("MESH", "EMPTY")]
            stats.setdefault("wall_reexport", {})[fname] = CH.export_glb(objs, os.path.join(a.export_dir, fname))
        lods = [o for o in bpy.data.collections["WALL_KIT_LODS"].all_objects if o.type == "MESH"]
        stats["wall_reexport"]["concordia_wall_kit_lods.glb"] = CH.export_glb(
            lods, os.path.join(a.export_dir, "concordia_wall_kit_lods.glb"))
        # biblioteca de materiales: .gltf separado que referencia las texturas del repo (sin copiarlas)
        for o in bpy.context.view_layer.objects:
            o.select_set(False)
        for o in lib_objs:
            o.select_set(True)
        lib_dir = os.path.join(a.export_dir, "materials")
        os.makedirs(lib_dir, exist_ok=True)
        lib = os.path.join(lib_dir, "concordia_materials.gltf")
        bpy.ops.export_scene.gltf(filepath=lib, export_format="GLTF_SEPARATE", use_selection=True, export_yup=True,
                                  export_keep_originals=True, export_extras=True)
        stats["material_library_gltf"] = os.path.relpath(lib, REPO)
        stats["material_library_check"] = check_gltf(lib)
        stats["timings_s"]["export"] = round(time.time() - t0, 1)
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.wm.save_as_mainfile(filepath=a.out, compress=True)
    with open(a.report, "w") as fh:
        json.dump(stats, fh, indent=1, ensure_ascii=False, default=str)
    print("saved:", a.out)


def check_gltf(path):
    """Comprueba en el .gltf que cada material tiene baseColor, metallicRoughness = occlusion (ORM) y normal."""
    with open(path) as fh:
        g = json.load(fh)
    imgs = [im.get("uri") for im in g.get("images", [])]
    tex = g.get("textures", [])

    def uri(t):
        return imgs[tex[t["index"]]["source"]] if t else None
    out = {}
    for m in g.get("materials", []):
        pbr = m.get("pbrMetallicRoughness", {})
        bc, mr = pbr.get("baseColorTexture"), pbr.get("metallicRoughnessTexture")
        oc, nt = m.get("occlusionTexture"), m.get("normalTexture")
        out[m["name"]] = {"baseColor": uri(bc), "orm_shared": bool(mr and oc and uri(mr) == uri(oc)),
                          "normal": uri(nt), "baseColorFactor": pbr.get("baseColorFactor"),
                          "texture_transform": bool(bc and "KHR_texture_transform" in bc.get("extensions", {})),
                          "emissive_strength": m.get("extensions", {}).get("KHR_materials_emissive_strength")}
    return out


if __name__ == "__main__":
    main()
