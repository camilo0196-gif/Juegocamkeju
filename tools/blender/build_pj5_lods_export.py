"""
CONCORDIA - PJ5: LODs, exportacion y cierre del personaje (elfo + equipo inicial del Sanador).
Parte de blender/elfo_v04.blend (no se modifica) y guarda blender/concordia_personajes_master.blend (version en la
propiedad de escena "concordia_personajes_version").
  LOD0  las mallas de PJ1-PJ4 (<= 10.000 tris)
  LOD1  copia de cada pieza (<pieza>_LOD1) con Decimate (colapso) y simetria X; protegidos (peso 0 en el grupo
        LOD_decimar): bordes abiertos (costuras entre piezas), silueta de las orejas y dobladillo de la falda y de la
        tunica. Total <= 5.000 tris
  LOD2  UNA sola malla (PJ_Elfo_Sanador_LOD2) con el Sanador equipado: piel tapada por la ropa quitada (grupos HIDE_*
        de cada prenda), todo unido y diezmado <= 1.800 tris con las mismas protecciones (mas suaves);
        esqueleto simplificado: pesos solo en 24 huesos (cuerpo sin dedos, ojos, mandibula, pelo ni ranuras; falda
        en Skirt_Front_01 / Skirt_Back_01). Mismo armature (mismos nombres de hueso) para montarse en el mismo
        Skeleton3D
  Export (glTF 2.0 .glb, +Y arriba, export/godot/personajes/):
        personaje_elfo_base.glb (esqueleto + cuerpo modular + ojos + cabello, LOD0 y LOD1)
        elfo_sanador_<prenda>.glb (esqueleto + la prenda, LOD0 y LOD1): robe_top, skirt, hood, belt, boots, bracers
        elfo_sanador_lod2.glb (esqueleto + LOD2)
        elfo_sanador_anims.glb (esqueleto + las 4 animaciones propias, sin mallas)
  Informe: docs/reports/pj5_lods.json. Capturas: python capture_pj5.py
python build_pj5_lods_export.py
"""

import json
import math
import os
import sys
import traceback
from datetime import date

import bpy  # noqa: I001  (bpy antes que bmesh)
import bmesh

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
SRC = os.path.join(REPO, "blender", "elfo_v04.blend")
DST = os.path.join(REPO, "blender", "concordia_personajes_master.blend")
OUT = os.path.join(REPO, "export", "godot", "personajes")
REPORT = os.path.join(REPO, "docs", "reports", "pj5_lods.json")
VERSION = "1.0 (PJ5, %s)" % date.today().isoformat()

BODY = ["PJ_Elfo_Head", "PJ_Elfo_Torso", "PJ_Elfo_Arms", "PJ_Elfo_Hands", "PJ_Elfo_Legs", "PJ_Elfo_Feet"]
BASE = BODY + ["PJ_Elfo_Eyes", "Hair_Elf"]
GEAR = {"robe_top": "Robe_Top", "skirt": "Robe_Skirt", "hood": "Hood", "belt": "Belt_Pouches", "boots": "Boots",
        "bracers": "Bracers"}
ANIMS = ["Heal_Cast_Single", "Heal_Channel-loop", "Heal_Cast_Area", "Revive"]
LOD1_MAX = 5000
LOD2_MAX = 1800
SIMPLE = ["Root", "Hips", "Spine", "Chest", "UpperChest", "Neck", "Head",
          "LeftShoulder", "LeftUpperArm", "LeftLowerArm", "LeftHand",
          "RightShoulder", "RightUpperArm", "RightLowerArm", "RightHand",
          "LeftUpperLeg", "LeftLowerLeg", "LeftFoot", "LeftToes",
          "RightUpperLeg", "RightLowerLeg", "RightFoot", "RightToes",
          "Skirt_Front_01", "Skirt_Back_01"]
NO_SYM = {"Belt_Pouches", "Hair_Elf"}        # piezas asimetricas (bolsitas, trenza)
# reparto del LOD1: mas recorte en las manos (dedos: muchos tris y poca silueta) y en la piel que la ropa tapa;
# menos en la cara, los ojos y la ropa (lo que se ve en isometrica)
K_LOD1 = {"PJ_Elfo_Hands": 0.55, "PJ_Elfo_Torso": 0.7, "PJ_Elfo_Arms": 0.75, "PJ_Elfo_Legs": 0.7,
          "PJ_Elfo_Feet": 0.75, "PJ_Elfo_Head": 1.2, "PJ_Elfo_Eyes": 1.3, "Hair_Elf": 1.0, "Robe_Top": 1.2,
          "Robe_Skirt": 1.25, "Hood": 1.15, "Belt_Pouches": 0.9, "Boots": 1.05, "Bracers": 1.05}


def tris(o):
    """triangulos con SOLO el Decimate activo (las mascaras HIDE_* restarian la piel tapada y enganarian la busqueda)"""
    off = [m for m in o.modifiers if m.name != "LOD_Decimate" and m.show_viewport]
    for m in off:
        m.show_viewport = False
    dg = bpy.context.evaluated_depsgraph_get()
    ev = o.evaluated_get(dg)
    me = ev.to_mesh()
    n = sum(len(p.vertices) - 2 for p in me.polygons)
    ev.to_mesh_clear()
    for m in off:
        m.show_viewport = True
    return n


def tris_base(o):
    return sum(len(p.vertices) - 2 for p in o.data.polygons)


def protect_group(o, soft=0.0, edge_soft=None, face_soft=None):
    """grupo LOD_decimar: 1 = se puede simplificar; soft (0 = intocable) en orejas, dobladillos y en las costuras
    entre piezas del cuerpo (bordes abiertos de PJ_Elfo_*: si se movieran, se abririan grietas); los bordes de la ropa
    y del pelo llevan edge_soft (se pueden simplificar algo sin abrir nada)"""
    g = o.vertex_groups.get("LOD_decimar") or o.vertex_groups.new(name="LOD_decimar")
    bm = bmesh.new()
    bm.from_mesh(o.data)
    border = {v.index for e in bm.edges if e.is_boundary for v in e.verts}
    bm.free()
    mw = o.matrix_world
    zs = [(mw @ v.co).z for v in o.data.vertices]
    zmin = min(zs)
    name = o.get("lod_src", o.name)
    parts = o.get("lod_parts", "")
    hard = set()
    if name.startswith("PJ_Elfo_"):
        hard |= border
    face = set()
    if name == "PJ_Elfo_Head" or "PJ_Elfo_Head" in parts:
        hard |= {v.index for v in o.data.vertices if abs((mw @ v.co).x) > 0.075 and (mw @ v.co).z > 1.69}
        # cara (ojos, nariz, boca): delante de la cabeza (-Y), entre la barbilla y las cejas
        face = {v.index for v in o.data.vertices if 1.60 < (mw @ v.co).z < 1.80 and (mw @ v.co).y < -0.04
                and abs((mw @ v.co).x) < 0.06}
    if name in ("Robe_Skirt", "Robe_Top"):
        hard |= {i for i, z in enumerate(zs) if z < zmin + 0.08}
    if "Robe_Skirt" in parts:                    # LOD2: dobladillo = lo mas bajo de la falda (z < 0,33)
        hard |= {i for i, z in enumerate(zs) if 0.24 < z < 0.33}
    g.add(list(range(len(o.data.vertices))), 1.0, "REPLACE")
    soft_edges = border - hard
    if soft_edges and edge_soft is not None:
        g.add(list(soft_edges), edge_soft, "REPLACE")
    if face and face_soft is not None:
        g.add(list(face - hard), face_soft, "REPLACE")
    if hard:
        g.add(list(hard), soft, "REPLACE")
    return g, len(hard)


def add_decimate(o, ratio, sym=True):
    m = o.modifiers.get("LOD_Decimate") or o.modifiers.new("LOD_Decimate", "DECIMATE")
    m.decimate_type = "COLLAPSE"
    m.ratio = ratio
    m.use_collapse_triangulate = True
    m.use_symmetry = sym
    m.symmetry_axis = "X"
    m.vertex_group = "LOD_decimar"
    m.vertex_group_factor = 1.0
    i = o.modifiers.find("LOD_Decimate")
    if i > 0:
        o.modifiers.move(i, 0)                  # antes del Armature (se aplica en reposo)
    return m


def apply_mod(o, name):
    with bpy.context.temp_override(object=o, active_object=o, selected_objects=[o]):
        bpy.ops.object.modifier_apply(modifier=name)


def duplicate(o, name, coll):
    c = o.copy()
    c.data = o.data.copy()
    c.name = name
    c.data.name = name
    c["lod_src"] = o.name
    coll.objects.link(c)
    if o.animation_data and o.animation_data.drivers:
        pass                                    # los drivers de las mascaras se copian con el objeto
    return c


def rest(arm):
    if arm.animation_data:
        arm.animation_data.action = None
    for pb in arm.pose.bones:
        pb.location = (0, 0, 0)
        pb.rotation_quaternion = (1, 0, 0, 0)
        pb.scale = (1, 1, 1)
    bpy.context.view_layer.update()


def lod1(objs, coll):
    copies = []
    for o in objs:
        c = duplicate(o, o.name + "_LOD1", coll)
        protect_group(c, 0.0, edge_soft=0.15, face_soft=0.5)
        copies.append(c)
    muted = mute_masks(copies)                  # las mascaras HIDE_* van por drivers: fuera durante la busqueda
    lo, hi = 0.05, 1.0
    for _ in range(16):                         # busqueda binaria del ratio comun
        r = (lo + hi) / 2
        for c in copies:
            add_decimate(c, min(1.0, r * K_LOD1.get(c["lod_src"], 1.0)), c["lod_src"] not in NO_SYM)
        total = sum(tris(c) for c in copies)
        if total > LOD1_MAX - 150:
            hi = r
        else:
            lo = r
    for c in copies:
        add_decimate(c, min(1.0, lo * K_LOD1.get(c["lod_src"], 1.0)), c["lod_src"] not in NO_SYM)
        apply_mod(c, "LOD_Decimate")
        clean(c)
    for fc in muted:
        fc.mute = False
    for c in copies:
        for m in c.modifiers:
            if m.type == "MASK":
                m.show_viewport = m.show_render = True
    bpy.context.view_layer.update()
    return copies, lo


def remap_weights(o, arm, keep):
    """pesos de los huesos que no estan en keep -> al antecesor mas cercano que si esta (dedos -> mano, pelo ->
    cabeza, ojos -> cabeza, falda 02/03 -> 01); luego 4 influencias como maximo y normalizado"""
    bones = arm.data.bones
    target = {}
    for b in bones:
        p = b
        while p is not None and p.name not in keep:
            p = p.parent
        target[b.name] = p.name if p else "Hips"
    groups = {g.index: g.name for g in o.vertex_groups}
    acc = []
    for v in o.data.vertices:
        w = {}
        for ge in v.groups:
            gn = groups[ge.group]
            if gn not in target:
                continue
            t = target[gn]
            w[t] = w.get(t, 0.0) + ge.weight
        acc.append(w)
    for g in list(o.vertex_groups):
        if g.name in target:
            o.vertex_groups.remove(g)
    for k in keep:
        o.vertex_groups.new(name=k)
    for i, w in enumerate(acc):
        top = sorted(w.items(), key=lambda kv: -kv[1])[:4]
        s = sum(x for _k, x in top) or 1.0
        for k, x in top:
            o.vertex_groups[k].add([i], x / s, "REPLACE")
    return target


def lod2(arm, coll):
    parts = []
    hidden = {}
    for prenda in GEAR.values():
        spec = bpy.data.objects[prenda].get("oculta", "nada")
        if spec and spec != "nada":
            for item in spec.split(","):
                part, grp = item.split(":")
                hidden.setdefault("PJ_Elfo_" + part, []).append(grp)
    for name in BASE + list(GEAR.values()):
        o = bpy.data.objects[name]
        c = duplicate(o, name + "_L2tmp", coll)
        for m in list(c.modifiers):
            if m.type != "ARMATURE":
                c.modifiers.remove(m)
        if c.animation_data:
            for fc in list(c.animation_data.drivers):
                c.animation_data.drivers.remove(fc)
        # piel tapada por la ropa del Sanador: fuera
        groups = [c.vertex_groups.get(g) for g in hidden.get(name, [])]
        groups = [g for g in groups if g]
        if groups:
            gi = {g.index for g in groups}
            bm = bmesh.new()
            bm.from_mesh(c.data)
            dl = bm.verts.layers.deform.active
            kill = [v for v in bm.verts if dl and any(k in gi and w > 0.5 for k, w in v[dl].items())]
            bmesh.ops.delete(bm, geom=kill, context="VERTS")
            bm.to_mesh(c.data)
            bm.free()
        parts.append(c)
    with bpy.context.temp_override(active_object=parts[0], object=parts[0], selected_objects=parts,
                                   selected_editable_objects=parts):
        bpy.ops.object.join()
    o = parts[0]
    o.name = o.data.name = "PJ_Elfo_Sanador_LOD2"
    o["lod_src"] = "LOD2"
    o["lod_parts"] = ",".join(BASE + list(GEAR.values()))
    for k in list(o.keys()):
        if k in ("clase", "pj_prenda", "oculta", "oculta_motivo", "pj_part"):
            del o[k]
    bm = bmesh.new()
    bm.from_mesh(o.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.0005)     # costuras entre piezas del cuerpo
    bm.to_mesh(o.data)
    bm.free()
    for g in [g for g in o.vertex_groups if g.name.startswith("HIDE") or g.name == "LOD_decimar"]:
        o.vertex_groups.remove(g)
    protect_group(o, 0.25, edge_soft=0.3, face_soft=0.45)
    before = tris_base(o)
    lo, hi = 0.05, 1.0
    for _ in range(16):
        r = (lo + hi) / 2
        add_decimate(o, r, True)
        if tris(o) > LOD2_MAX - 40:
            hi = r
        else:
            lo = r
    add_decimate(o, lo, True)
    apply_mod(o, "LOD_Decimate")
    target = remap_weights(o, arm, SIMPLE)
    clean(o)
    return o, before, lo


def clean(o):
    """malla valida para el exportador: sin aristas ni vertices sueltos ni caras degeneradas; sin el grupo auxiliar"""
    g = o.vertex_groups.get("LOD_decimar")
    if g:
        o.vertex_groups.remove(g)
    bm = bmesh.new()
    bm.from_mesh(o.data)
    bmesh.ops.dissolve_degenerate(bm, dist=0.0001, edges=bm.edges)
    loose_e = [e for e in bm.edges if not e.link_faces]
    bmesh.ops.delete(bm, geom=loose_e, context="EDGES")
    loose_v = [v for v in bm.verts if not v.link_edges]
    bmesh.ops.delete(bm, geom=loose_v, context="VERTS")
    bm.to_mesh(o.data)
    bm.free()
    o.data.validate(clean_customdata=False)
    o.data.update()


def mute_masks(objs):
    muted = []
    for o in objs:
        if o.animation_data:
            for fc in o.animation_data.drivers:
                if fc.data_path.startswith("modifiers[") and not fc.mute:
                    fc.mute = True
                    muted.append(fc)
        for m in o.modifiers:
            if m.type == "MASK":
                m.show_viewport = m.show_render = False
    bpy.context.view_layer.update()
    return muted


def export(path, objs, arm, anims=False):
    for o in bpy.context.view_layer.objects:
        o.select_set(False)
    for o in [arm] + objs:
        o.hide_set(False)
        o.hide_viewport = False
        o.select_set(True)
    bpy.context.view_layer.objects.active = arm
    bpy.ops.export_scene.gltf(filepath=path, export_format="GLB", use_selection=True, export_yup=True,
                              export_apply=True, export_extras=True, export_image_format="AUTO",
                              export_vertex_color="NONE", export_animations=anims,
                              export_animation_mode="NLA_TRACKS", export_force_sampling=True,
                              export_anim_slide_to_zero=True, export_skins=True, export_def_bones=False)
    return {"archivo": os.path.relpath(path, REPO), "kb": round(os.path.getsize(path) / 1024, 1),
            "mallas": [o.name for o in objs]}


def main():
    bpy.ops.wm.open_mainfile(filepath=SRC)
    sc = bpy.context.scene
    arm = bpy.data.objects["PJ_Elfo_Rig"]
    rest(arm)
    rep = {"version": VERSION, "lod0": {}, "lod1": {}, "lod2": {}}
    lod0 = BASE + list(GEAR.values())
    for n in lod0:
        rep["lod0"][n] = tris_base(bpy.data.objects[n])
    rep["lod0_total"] = sum(rep["lod0"].values())
    c1 = bpy.data.collections.new("PJ_LOD1")
    sc.collection.children.link(c1)
    c2 = bpy.data.collections.new("PJ_LOD2")
    sc.collection.children.link(c2)
    copies, r1 = lod1([bpy.data.objects[n] for n in lod0], c1)
    for c in copies:
        rep["lod1"][c.name] = tris_base(c)
    rep["lod1_total"] = sum(rep["lod1"].values())
    rep["lod1_ratio"] = round(r1, 3)
    print("LOD1", rep["lod1_total"], flush=True)
    l2, before, r2 = lod2(arm, c2)
    rep["lod2"] = {"malla": l2.name, "tris": tris_base(l2), "tris_antes_de_diezmar": before, "ratio": round(r2, 3),
                   "materiales": [m.name for m in l2.data.materials if m],
                   "huesos_con_peso": sorted({g.name for g in l2.vertex_groups if any(
                       g.index in [ge.group for ge in v.groups] for v in l2.data.vertices)}),
                   "esqueleto_simplificado": SIMPLE}
    print("LOD2", rep["lod2"]["tris"], flush=True)
    # materiales: los que usan las mallas exportadas
    used = set()
    for o in [bpy.data.objects[n] for n in lod0] + copies + [l2]:
        used |= {m.name for m in o.data.materials if m}
    rep["materiales"] = sorted(used)
    sc["concordia_personajes_version"] = VERSION
    bpy.ops.wm.save_as_mainfile(filepath=DST)
    # --------------------------------------------------------------------------------------------- exportacion
    os.makedirs(OUT, exist_ok=True)
    allmesh = [bpy.data.objects[n] for n in lod0] + copies
    mute_masks(allmesh)
    lod1_of = {c["lod_src"]: c for c in copies}
    ex = {}
    ex["personaje_elfo_base.glb"] = export(os.path.join(OUT, "personaje_elfo_base.glb"),
                                           [bpy.data.objects[n] for n in BASE] + [lod1_of[n] for n in BASE], arm)
    for key, n in GEAR.items():
        fn = "elfo_sanador_%s.glb" % key
        ex[fn] = export(os.path.join(OUT, fn), [bpy.data.objects[n], lod1_of[n]], arm)
    ex["elfo_sanador_lod2.glb"] = export(os.path.join(OUT, "elfo_sanador_lod2.glb"), [l2], arm)
    # animaciones: solo el esqueleto y las 4 pistas NLA (sin mallas)
    for t in arm.animation_data.nla_tracks:
        t.mute = t.name not in ANIMS
    ex["elfo_sanador_anims.glb"] = export(os.path.join(OUT, "elfo_sanador_anims.glb"), [], arm, anims=True)
    rep["exportados"] = ex
    os.makedirs(os.path.dirname(REPORT), exist_ok=True)
    json.dump(rep, open(REPORT, "w"), indent=1, ensure_ascii=False)
    print("REPORT", json.dumps({k: rep[k] for k in ("lod0_total", "lod1_total")}), rep["lod2"]["tris"], flush=True)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        traceback.print_exc()
        sys.stdout.flush()
        os._exit(1)
    sys.stdout.flush()
    os._exit(0)
