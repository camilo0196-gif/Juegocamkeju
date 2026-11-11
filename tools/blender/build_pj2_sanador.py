"""
CONCORDIA - PJ2: cabello del elfo y conjunto inicial del Sanador (CLASE_SANADOR, provisional), calidad normal.
Parte de blender/elfo_v01.blend (no se modifica) y guarda blender/elfo_v02.blend.
  piezas   Robe_Top, Robe_Skirt, Hood, Belt_Pouches, Boots, Bracers (coleccion CLASE_SANADOR) y Hair_Elf (PJ_CABELLO)
  atlas    un atlas 1K para ropa y pelo (albedo RGBA con alfa recortada, normal, ORM y emision del cristal)
  ocultar  grupos HIDE_* finos en el cuerpo; cada prenda tiene la propiedad 'oculta' con los grupos que tapa y en
           el cuerpo un modificador Mask por grupo cuya visibilidad sigue a la de la prenda (driver '1 - oculta')
  export   export/godot/pj_sanador_ropa.glb (ropa + pelo) y pj_elfo_sanador_equipado.glb (cuerpo con mascaras)
python build_pj2_sanador.py
"""

import json
import math
import os
import sys

import bpy
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import pj2_geo as G  # noqa: E402
import pj2_atlas as A  # noqa: E402

REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
SRC = os.path.join(REPO, "blender", "elfo_v01.blend")
DST = os.path.join(REPO, "blender", "elfo_v02.blend")
REPORT = os.path.join(REPO, "docs", "reports", "pj2_sanador.json")
TEX = os.path.join(REPO, "textures", "personajes", "sanador")
CLASE = "CLASE_SANADOR (provisional)"
BUDGET = {"ropa": 4000, "cabello": 1000}

P = {
    "robe_top_bottom": 1.06, "sleeve_cut_x": 0.50, "robe_off": 0.016, "pendant_z": 1.335,
    "skirt_top": 1.12, "hem_z": 0.25, "slit_z": 0.66, "skirt_margin": 0.028, "skirt_flare": 0.10, "body_cy": -0.02,
    "collar_z": 1.60, "cape_len_side": 0.19, "cape_len_front": 0.21, "cape_off": 0.012,
    "hood_w": 0.12, "hood_z0": 1.36, "hood_z1": 1.555, "hood_bulge": 0.06,
    "belt_z": 1.085, "belt_h": 0.045,
    "boot_top": 0.40, "boot_off": 0.008,
    "bracer_x0": 0.525, "bracer_x1": 0.728, "bracer_off": 0.006,
    "eye_z": 1.739, "cap_off": 0.007, "gather_z": 1.70, "n_cards": 20,
    "braid_z": [1.64, 1.58, 1.52, 1.46, 1.40, 1.34, 1.28, 1.22],
}
# que grupos del cuerpo tapa cada prenda (pieza del cuerpo -> grupo)
HIDES = {
    "Robe_Top": [("Torso", "HIDE_Torso_Sup"), ("Arms", "HIDE_Arms_Sup")],
    "Robe_Skirt": [("Torso", "HIDE_Torso_Inf"), ("Legs", "HIDE_Legs_Sup")],
    "Boots": [("Legs", "HIDE_Legs_Inf"), ("Feet", "HIDE_Feet")],
    "Bracers": [("Arms", "HIDE_Arms_Inf")],
    "Hood": [], "Belt_Pouches": [], "Hair_Elf": [],
}
WHY_NONE = {"Hood": "va encima de la tunica (no toca la piel)", "Belt_Pouches": "va encima de la tunica y la falda",
            "Hair_Elf": "el casquete flota 7-13 mm sobre el cuero cabelludo; ocultar la piel dejaria la cabeza "
                        "hueca al quitar el pelo"}


def collection(name, parent=None):
    c = bpy.data.collections.get(name) or bpy.data.collections.new(name)
    par = parent or bpy.context.scene.collection
    if c.name not in par.children:
        par.children.link(c)
    return c


def fix_normals(o, tree):
    """Normales hacia fuera: componentes cerradas con recalc; abiertas por mayoria (lejos del cuerpo)."""
    import bmesh
    bm = bmesh.new()
    bm.from_mesh(o.data)
    bm.faces.ensure_lookup_table()
    comp, n = {}, 0
    for f0 in bm.faces:
        if f0.index in comp:
            continue
        st = [f0]
        comp[f0.index] = n
        while st:
            f = st.pop()
            for e in f.edges:
                for g in e.link_faces:
                    if g.index not in comp:
                        comp[g.index] = n
                        st.append(g)
        n += 1
    flipped = 0
    for c in range(n):
        fs = [f for f in bm.faces if comp[f.index] == c]
        closed = all(not e.is_boundary for f in fs for e in f.edges)
        if closed:
            bmesh.ops.recalc_face_normals(bm, faces=fs)
            continue
        bmesh.ops.recalc_face_normals(bm, faces=fs)
        vote = 0.0
        for f in fs:
            cc = f.calc_center_median()
            loc, _nrm, _i, _d = tree.find_nearest(cc)
            if loc is not None:
                vote += f.normal.dot(cc - loc) * f.calc_area()
        if vote < 0:
            bmesh.ops.reverse_faces(bm, faces=fs)
            flipped += 1
    bm.to_mesh(o.data)
    bm.free()
    o.data.update()
    return flipped


def body_hide_groups(parts):
    """Grupos HIDE_* finos en el cuerpo (vertices tapados por cada prenda). Piernas: anillos en z 0,09 / 0,21 /
    0,40 / 0,52 / 0,63 / 0,71 / 0,84 ..."""
    rules = {
        "Torso": {"HIDE_Torso_Sup": lambda c: c.z >= 1.075, "HIDE_Torso_Inf": lambda c: c.z < 1.075},
        # anillos del brazo del proxy en |x| 0,20 / 0,34 / 0,45 / 0,56 / 0,745: el Mask quita toda cara que toque un
        # vertice oculto, asi que los limites van entre anillos (manga cortada en 0,50; venda desde 0,525)
        "Arms": {"HIDE_Arms_Sup": lambda c: abs(c.x) < 0.50, "HIDE_Arms_Inf": lambda c: abs(c.x) >= 0.60},
        "Legs": {"HIDE_Legs_Sup": lambda c: c.z > P["slit_z"] + 0.02,
                 "HIDE_Legs_Inf": lambda c: c.z < P["boot_top"] - 0.03},
    }
    out = {}
    for part, groups in rules.items():
        o = parts[part]
        for gname, fn in groups.items():
            g = o.vertex_groups.get(gname) or o.vertex_groups.new(name=gname)
            ids = [v.index for v in o.data.vertices if fn(v.co)]
            g.add(ids, 1.0, "REPLACE")
            out[gname] = len(ids)
    out["HIDE_Feet"] = len(parts["Feet"].data.vertices)
    return out


def hide_masks(parts, clothes):
    """Modificador Mask (invertido) por grupo tapado; su visibilidad = 1 - oculta de la prenda (driver)."""
    n = 0
    for cname, lst in HIDES.items():
        co = clothes[cname]
        co["oculta"] = ",".join(f"{p}:{g}" for p, g in lst) or "nada"
        if not lst:
            co["oculta_motivo"] = WHY_NONE[cname]
        for part, gname in lst:
            o = parts[part]
            m = o.modifiers.new(f"OCULTA_{gname}__{cname}", "MASK")
            m.vertex_group = gname
            m.invert_vertex_group = True
            for prop, src in (("show_viewport", "hide_viewport"), ("show_render", "hide_render")):
                fc = m.driver_add(prop)
                drv = fc.driver
                drv.type = "SCRIPTED"
                var = drv.variables.new()
                var.name = "h"
                var.type = "SINGLE_PROP"
                var.targets[0].id_type = "OBJECT"
                var.targets[0].id = co
                var.targets[0].data_path = src
                drv.expression = "1 - h"
            n += 1
    return n


def export_glb(objs, path):
    for o in bpy.context.view_layer.objects:
        o.select_set(False)
    for o in objs:
        o.select_set(True)
    bpy.ops.export_scene.gltf(filepath=path, export_format="GLB", use_selection=True, export_yup=True,
                              export_apply=True, export_extras=True, export_image_format="AUTO",
                              export_vertex_color="NONE")
    return round(os.path.getsize(path) / 1024, 1)


def glb_check(path):
    import struct
    with open(path, "rb") as fh:
        data = fh.read()
    ln = struct.unpack_from("<I", data, 12)[0]
    js = json.loads(data[20:20 + ln])
    return [{"nombre": m.get("name"), "alphaMode": m.get("alphaMode", "OPAQUE"), "alphaCutoff": m.get("alphaCutoff"),
             "doubleSided": m.get("doubleSided", False), "emissiveFactor": m.get("emissiveFactor"),
             "emissiveTexture": "emissiveTexture" in m, "normal": "normalTexture" in m,
             "occlusion": "occlusionTexture" in m} for m in js.get("materials", [])]


def main():
    bpy.ops.wm.open_mainfile(filepath=SRC)
    import build_pj1_elfo as B1
    d = json.loads(bpy.context.scene["pj1_datos"])
    J = d["joints"]
    parts = {k: bpy.data.objects[f"PJ_Elfo_{k}"] for k in B1.PART_ORDER}
    eyes = bpy.data.objects["PJ_Elfo_Eyes"]
    col = collection("CLASE_SANADOR")
    col["clase"] = CLASE
    hcol = collection("PJ_CABELLO")
    rep = {"clase": CLASE, "parametros": P}
    body_tree, _ = G.body_bvh(list(parts.values()))
    robe = G.build_robe_top(parts, J, B1.find_seam, P)
    robe_o = robe.to_object(col)
    skirt, rep["falda"], skirt_data = G.build_skirt(parts, J, P)
    skirt_o = skirt.to_object(col)
    hood, rep["esclavina"] = G.build_hood(parts, robe_o, J, P)
    hood_o = hood.to_object(col)
    belt, rep["cinturon"] = G.build_belt(parts, skirt_data, P)
    belt_o = belt.to_object(col)
    boots_o = G.boots_piece(parts, J, B1.find_seam, P).to_object(col)
    brac_o = G.build_bracers(parts, J, P).to_object(col)
    hair, rep["cabello"] = G.build_hair(parts, eyes, J, P, list(parts.values()) + [robe_o, hood_o, skirt_o])
    hair_o = hair.to_object(hcol)
    clothes = {o.name: o for o in (robe_o, skirt_o, hood_o, belt_o, boots_o, brac_o, hair_o)}
    rep["normales_invertidas"] = {k: fix_normals(o, body_tree) for k, o in clothes.items()}
    for o in clothes.values():
        o["clase"] = CLASE if o is not hair_o else "comun (elfo)"
        o["pj_prenda"] = o.name
    tris = {k: sum(len(p.vertices) - 2 for p in o.data.polygons) for k, o in clothes.items()}
    ropa = sum(v for k, v in tris.items() if k != "Hair_Elf")
    rep["tris_por_pieza"] = tris
    rep["tris_ropa"], rep["tris_cabello"] = ropa, tris["Hair_Elf"]
    rep["presupuesto"] = BUDGET
    print("TRIS", json.dumps(tris), "ropa", ropa, flush=True)
    # AO por vertice (rayos contra cuerpo + todas las piezas)
    import pj1_piel as PL
    allo = list(parts.values()) + [eyes] + list(clothes.values())
    ao = {}
    for k, o in clothes.items():
        ao[k] = PL.vertex_ao(o, [x for x in allo if x is not o], rays=20, dist=0.2)
    # atlas
    objs = list(clothes.values())
    rep["uv"] = A.uv_pack(objs)
    tpm = sum(v["texeles_por_metro"] for k, v in rep["uv"].items() if k != "Hair_Elf") / (len(objs) - 1)
    obj, cls, ch = A.rasterize(objs, ao)
    paths, rep["atlas"] = A.paint(obj, cls, ch, TEX, "sanador_atlas", tpm=tpm)
    mat = A.atlas_material(paths)
    for o in objs:
        o.data.materials.clear()
        o.data.materials.append(mat)
    mem = 0
    for k, p in paths.items():
        mem += 1024 * 1024 * 4 * 4 / 3
    rep["atlas_memoria_mb_sin_comprimir_con_mipmaps"] = round(mem / 2 ** 20, 1)
    rep["texturas"] = {k: os.path.relpath(v, REPO) for k, v in paths.items()}
    print("ATLAS", json.dumps(rep["atlas"]), flush=True)
    # ocultar el cuerpo
    rep["grupos_cuerpo"] = body_hide_groups(parts)
    rep["mascaras"] = hide_masks(parts, clothes)
    rep["oculta_por_prenda"] = {k: [f"{p}:{g}" for p, g in v] for k, v in HIDES.items()}
    rep["oculta_sin_grupos_motivo"] = WHY_NONE
    bpy.context.scene["pj2_datos"] = json.dumps({"tris": tris, "hides": rep["oculta_por_prenda"]})
    bpy.ops.outliner.orphans_purge(do_recursive=True)
    bpy.ops.wm.save_as_mainfile(filepath=DST)
    gd = os.path.join(REPO, "export", "godot")
    rep["glb_ropa"] = {"archivo": "export/godot/pj_sanador_ropa.glb",
                       "kb": export_glb(objs, os.path.join(gd, "pj_sanador_ropa.glb"))}
    rep["glb_ropa"]["materiales"] = glb_check(os.path.join(gd, "pj_sanador_ropa.glb"))
    rep["glb_equipado"] = {"archivo": "export/godot/pj_elfo_sanador_equipado.glb",
                           "kb": export_glb(objs + list(parts.values()) + [eyes],
                                            os.path.join(gd, "pj_elfo_sanador_equipado.glb"))}
    with open(REPORT, "w") as fh:
        json.dump(rep, fh, indent=1, ensure_ascii=False)
    print("GLB", json.dumps(rep["glb_ropa"]), flush=True)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        import traceback
        traceback.print_exc()
        sys.stdout.flush()
        os._exit(1)
    sys.stdout.flush()
    os._exit(0)
