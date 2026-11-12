"""
CONCORDIA - Etapa 29: interiores unicos (Tesoreria de la Muralla, Santuario del Retorno, ...).
-> blender/concordia_interiors_unicos_v01.blend, export/godot/int_<nombre>.glb, docs/reports/stage29_<nombre>.json

Kit, convenciones y comprobaciones de las etapas 27-28: tamano = InteriorVolume (+-0.2 m en planta), triangulos
<= 40,000, rayos desde CAM_Iso a lo importante (muros cercanos, techo y plantas superiores ocultos segun el estado),
malla de navegacion (celda 0.25 m) conectada desde el spawn, pasos >= 1.2 m, escaleras <= 35 grados, un solo azul
#8FD0FF por sala. Datos del edificio (volumen, giro, puerta) desde el master de la ciudad (concordia_v28).
python build_stage29_int.py [-- tesoreria santuario]
"""

import json
import math
import os
import random
import sys

import bpy
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import interior_kit as IK  # noqa: E402
import stage27_banco as SB  # noqa: E402
import build_stage27 as B27  # noqa: E402
import build_stage28_int as B28  # noqa: E402

REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
SRC = os.path.join(REPO, "blender", "concordia_v28.blend")
OUT = os.path.join(REPO, "blender", "concordia_interiors_unicos_v01.blend")
EXP = os.path.join(REPO, "export", "godot")
REPORTS = os.path.join(REPO, "docs", "reports")
EXT_KEEP = ("SANTUARIO_Well", "SANTUARIO_Roof", "SANTUARIO_Body")    # piezas del exterior que se usan
EXTRA_MATS = ["MAT_Pipe_Glass", "MAT_Pipe_Light_Core", "MAT_Felt_R05", "MAT_Hide_R05", "MAT_Stained_Glass_Blue",
              "MAT_Water", "MAT_Straw", "MAT_Roof_Tile_Ocher", "MAT_Roof_Tile_Ocher_B"]
BUILDINGS = {  # nombre: (raiz del edificio, volumen interior, marcador de la puerta)
    "tesoreria": ("TesoreriaMuralla", "TesoreriaMuralla_InteriorVolume", "MARKER_TesoreriaMuralla_Door"),
    "santuario": ("SANTUARIO", "Santuario_InteriorVolume", "MARKER_Santuario_Door"),
}
ONLY = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else list(BUILDINGS)


def collection(name):
    c = bpy.data.collections.get(name) or bpy.data.collections.new(name)
    if c.name not in bpy.context.scene.collection.children:
        bpy.context.scene.collection.children.link(c)
    return c


def source():
    """Materiales y datos de cada edificio desde el master de la ciudad (sin guardar nada en el)."""
    names = [n for b in BUILDINGS.values() for n in b]
    with bpy.data.libraries.load(SRC, link=False) as (df, dt):
        dt.materials = [m for m in df.materials if m in B27.MATS + EXTRA_MATS]
        dt.objects = [o for o in df.objects if o in names or o in EXT_KEEP]
    info = {}
    for key, (root, vol, door) in BUILDINGS.items():
        r, iv, dm = bpy.data.objects[root], bpy.data.objects[vol], bpy.data.objects[door]
        vs = [v.co for v in iv.data.vertices]
        lo = [min(v[i] for v in vs) for i in range(3)]
        hi = [max(v[i] for v in vs) for i in range(3)]
        c = Vector(((lo[0] + hi[0]) / 2 + iv.location.x, (lo[1] + hi[1]) / 2 + iv.location.y, 0.0))
        info[key] = {"iv_size": [round(hi[i] - lo[i], 3) for i in range(3)],
                     "iv_center_local": [round(c.x, 3), round(c.y, 3)],
                     "rot_deg": round(math.degrees(r.rotation_euler.z), 3),     # leccion 1: rotation_euler
                     "door_local": [round(x, 3) for x in dm.location],
                     "door_in_frame": [round(dm.location.x - c.x, 3), round(min(dm.location.y - c.y, (hi[1] - lo[1]) / 2), 3)]}
    well = bpy.data.objects.get("SANTUARIO_Well")
    if well is not None:
        info["santuario"]["well_source"] = {k: str(well[k]) for k in well.keys() if not k.startswith("_")}
    ext = collection("SRC_SANTUARIO_EXT")
    ext.hide_render = True
    for n in ("SANTUARIO_Roof", "SANTUARIO_Body"):
        o = bpy.data.objects.get(n)
        if o is None:
            continue
        # al marco local del edificio (= marco centrado del interior: el volumen esta en el origen del Santuario);
        # matrix_world llega sin evaluar al anexar (leccion 1): se usan los datos guardados
        rel = o.matrix_parent_inverse @ o.matrix_basis if o.parent else o.matrix_basis
        o.data = o.data.copy()
        o.data.transform(rel)
        o.parent = None
        o.matrix_basis = rel.inverted() @ rel
        o.name = "SRC_" + n
        o.data.name = "SRC_" + n
        ext.objects.link(o)
    for o in list(bpy.data.objects):
        if o.name.startswith("SRC_SANTUARIO_") and o.name != "SRC_SANTUARIO_Well":
            continue
        if o.name == "SANTUARIO_Well":
            o.name = "SRC_SANTUARIO_Well"
            o.data.name = "SRC_SANTUARIO_Well"
            o.location = (6200.0, 0.0, -50.0)
            o.hide_render = True
            continue
        me = o.data if o.type == "MESH" else None
        bpy.data.objects.remove(o)
        if me is not None and me.users == 0:
            bpy.data.meshes.remove(me)
    return info


def group_of(o, it):
    return B28.group_of(o, it)


def finish(it, key, rep, keys, hide_sets, targets, budget=40000, levels=None):
    """Rayos (antes de unir), union de grupos, colision, navegacion, pasillos, triangulos, exportacion."""
    rep["near_walls"] = it.log.get("near_walls")
    rep["caras_coplanarias_suelo_quitadas"] = 0
    rep["cam_local"] = it.log.get("cam_local")
    rep["rays_cam_iso"] = {}
    for state, (hide, names) in hide_sets.items():
        tg = {n: targets[n] for n in names}
        rep["rays_cam_iso"][state] = B28.ray_vis(it, tg, hide=hide)
    for g in list(it.groups):
        if g not in ("Furniture", "Furniture_L1", "Lights", "Markers"):
            it.realize(g)
    rep["caras_coplanarias_suelo_quitadas"] = it.log.get("caras_coplanarias_suelo", 0)
    it.collider()
    nav = it.navmesh(cell=0.25)
    rep["navmesh"] = B27.nav_reach(it, nav, keys)
    rep["corridors_1.2m"] = {}
    for lv, (zmin, zmax, start) in (levels or {0: (-1, 0.5, keys["spawn"])}).items():
        kk = {k: v for k, v in keys.items() if zmin <= v[2] < zmax}
        rep["corridors_1.2m"][f"nivel_{lv}"] = B27.clearance_check(it, kk, lv, start)
    objs = it.all_objects()
    t = B27.tri_count(objs)
    rep["tris"] = {"total": t, "budget": budget, "ok": t <= budget,
                   "by_group": {g: B27.tri_count([o for o in objs if group_of(o, it) == g]) for g in it.groups}}
    rep["markers"] = {e.name: {k: e[k] for k in e.keys() if k not in ("axis",) and not k.startswith("_")}
                      for e in it.groups["Markers"].children}
    rep["lights"] = {e.name: [e["light_color"], e["light_energy"], e["light_range"]] for e in it.groups["Lights"].children}
    rep["blue_lights"] = sum(1 for e in it.groups["Lights"].children if e["light_color"].upper() == "#8FD0FF")
    rep["hideable_groups"] = {g: e.get("hide_when", "") for g, e in it.groups.items() if e.get("hide_when") or g in
                              ("WALL_Near_A", "WALL_Near_B", "CEILING")}
    import stage11_godot as G
    bpy.context.view_layer.update()
    path = os.path.join(EXP, f"int_{key}.glb")
    size = G.export_glb(objs, path)
    rep["export"] = {"file": os.path.relpath(path, REPO), "mb": round(size / 2 ** 20, 3), **G.glb_info(path)}
    bad = [o.name for o in objs if "." in o.name.rsplit("_", 1)[-1] and o.name[-4:-3] == "." and o.name[-3:].isdigit()]
    rep["export"]["nombres_con_sufijo_blender"] = bad
    # leccion 15: exportado con nombres limpios; en el .blend se les anade el sufijo del interior para dejar libres
    # los nombres al siguiente (Blender exige nombres unicos en todo el archivo)
    for o in objs:
        if not o.name.startswith("INT_"):
            o.name = f"{o.name}__{key}"
    return rep


def size_check(it, src):
    iv = src["iv_size"]
    d = [round(abs(a - b), 3) for a, b in zip((it.W, it.D, it.H), iv)]
    return {"interior_m": [it.W, it.D, it.H], "interior_volume_m": iv, "diff_m": d,
            "ok_planta": d[0] <= 0.2 and d[1] <= 0.2}


# --------------------------------------------------------------------------- Tesoreria
def tesoreria(col, src):
    import stage29_tesoreria as T
    props = collection("BLD_INT_PROPS_TES")
    rep = {"source": src}
    rep["props_tris"], rep["shard_materials"] = T.build_all_props(props)
    it, info = T.build(col, src["rot_deg"])
    rep.update(info)
    rep["size_check"] = size_check(it, src)
    npc = lambda p: [(p[0], p[1] + dy, z) for z in (0.6, 1.0, 1.4, 1.75) for dy in (-0.2, 0.0, 0.2)]  # noqa: E731
    targets = {
        "Tesorero": (npc(T.NPC[1]), ()),
        "Cambista": (npc(T.NPC[2]), ()),
        "Mostrador_1_Vender": ([(T.COUNTER_X + 0.47, T.C1_Y0 + d, 0.6) for d in (0.5, 1.5, 2.5, 3.3)] +
                               [(T.COUNTER_X + 0.25, T.C1_Y0 + d, 1.13) for d in (0.5, 1.5, 2.5, 3.3)], ("Counter",)),
        "Mostrador_2_Cambio": ([(T.COUNTER_X + 0.47, T.C2_Y0 + d, 0.6) for d in (0.5, 1.5, 2.5, 3.3)] +
                               [(T.COUNTER_X + 0.25, T.C2_Y0 + d, 1.13) for d in (0.5, 1.5, 2.5, 3.3)], ("Counter",)),
        "Tubos_de_luz": ([(x, T.PIPE_Y + 0.2, z) for x in T.PIPE_X for z in (1.5, 3.5, 5.5, 7.5)], ("PIPE_Light",)),
    }
    for v in info["vitrinas"]:
        o = bpy.data.objects[v["vitrina"]]
        pts = [tuple(c.matrix_basis.translation + Vector((0, 0, 0.08))) for c in it.groups["Furniture"].children
               if c.name.startswith(f"TES_Shard_{v['tipo']}_{v['vitrina'].split('_')[2]}_")]
        targets[f"Vitrina_{v['tipo']}"] = (pts, ("TES_Vitrina", "TES_Shard"))
        _ = o
    safe = next(o for o in it.groups["Furniture_L1"].children if o.name.startswith("PROP_TES_Safe"))
    sp = safe.matrix_basis.translation
    targets["Caja_fuerte"] = ([(sp.x + dx, sp.y + 0.42, sp.z + z) for dx in (-0.3, 0.0, 0.3) for z in (0.5, 1.0, 1.4)],
                              ("TES_Safe",))
    targets["Despacho_mesa"] = ([(-10.6 + dx, -3.6 + 0.42, T.SH + z) for dx in (-0.5, 0.0, 0.5) for z in (0.5, 0.85)], ("BANK_Desk",))
    base = ("WALL_Near_A", "WALL_Near_B", "CEILING")
    ground = ["Tesorero", "Cambista", "Mostrador_1_Vender", "Mostrador_2_Cambio", "Tubos_de_luz"] + \
        [f"Vitrina_{v['tipo']}" for v in info["vitrinas"]]
    hide_sets = {
        "planta_baja (LEVEL_1 oculto)": (base + ("LEVEL_1", "Furniture_L1", "WALL_Near_Despacho"), ground),
        "planta_baja con LEVEL_1 visible (estricto)": (base + ("WALL_Near_Despacho",), ground),
        "planta_alta (despacho, WALL_Near_Despacho oculto)": (base + ("WALL_Near_Despacho",), ["Caja_fuerte", "Despacho_mesa"]),
    }
    D, SH = T.D, T.SH
    keys = {"spawn": (0.0, D / 2 - 1.6, 0.0), "mostrador_1_publico": (T.COUNTER_X + 1.0, T.TELLER[1], 0.0),
            "mostrador_2_publico": (T.COUNTER_X + 1.0, T.TELLER[2], 0.0), "tesorero": (T.NPC[1][0], T.NPC[1][1], 0.0),
            "cambista": (T.NPC[2][0], T.NPC[2][1], 0.0)}
    for v in info["vitrinas"]:
        keys[f"vitrina_{v['tipo'].lower()}"] = (v["x"], T.VIT_Y + 0.9, 0.0)
    keys.update({"contaduria": (-1.0, -3.5, 0.0), "pie_escalera": (12.2, 3.2, 0.0),
                 "galeria": (2.5, -3.6, SH), "despacho": (-9.0, -3.0, SH), "caja_fuerte": (-8.0, -5.5, SH)})
    levels = {0: (-1, 0.5, keys["spawn"]), 1: (0.5, 99, (12.2, -5.5, SH))}
    finish(it, "tesoreria", rep, keys, hide_sets, targets, levels=levels)
    return it, rep


def main():
    # archivo nuevo en cada ejecucion (volver a cargar materiales sobre uno existente los duplicaria): para la
    # entrega se ejecuta con todos los interiores de la etapa
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.wm.save_as_mainfile(filepath=OUT)
    src = source()
    kit = collection("BLD_INT_KIT")
    IK.build_kit(kit)
    for o in kit.objects:
        o.location.z -= 50.0
        o.hide_render = True
    props = collection("BLD_INT_PROPS")
    SB.build_props(props, random.Random(2701))
    out = {}
    for k, key in enumerate(ONLY):
        col = collection(f"INT_{key.upper()}")
        fn = {"tesoreria": tesoreria, "santuario": santuario}[key]
        it, rep = fn(col, src[key])
        it.root.location = (-400.0 - 60.0 * list(BUILDINGS).index(key), 0.0, 0.0)
        with open(os.path.join(REPORTS, f"stage29_{key}.json"), "w") as fh:
            json.dump(rep, fh, indent=1, ensure_ascii=False, default=str)
        out[key] = {k2: rep.get(k2) for k2 in ("tris", "size_check", "navmesh", "corridors_1.2m", "rays_cam_iso", "stair",
                                               "export", "blue_lights")}
        print("INT", key, json.dumps(out[key], default=str)[:6000], flush=True)
    bpy.ops.file.make_paths_relative()
    bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)


def santuario(col, src):
    import stage29_santuario as S
    return S.build_report(col, src, sys.modules[__name__])


if __name__ == "__main__":
    main()
