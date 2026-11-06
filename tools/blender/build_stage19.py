"""
CONCORDIA - Etapa 19 (E6): distrito Este (Oficios). concordia_v18.blend -> concordia_v19.blend (guardada antes)
+ export/godot/concordia_oficios.glb (+ concordia_gremio_cazadores_sin_parcela.glb) + docs/reports/stage19_oficios.json

Kit (fit_iso_height) + extras: Gremio de Mineros, Pescadores, Cazadores (sin parcela), Gran Forja, Curtiduria,
Sastreria, Carpinteria (+ WATERWHEEL aparte), OFI_Casa_01/02.
A mano (stage19_oficios): Herbolarios, Alquimia, Hornos, Joyeria y Tallado, Crisol de las Piedras (+ CRISOL_FloatStone),
Casa de Reparaciones.
"""

import json
import math
import os
import random
import sys

import bpy  # noqa: I001
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import concordia_const as C  # noqa: E402
import bld_kit as K  # noqa: E402
import concordia_buildings as B  # noqa: E402
import stage13_portal as P13  # noqa: E402
import stage16_landmarks as L  # noqa: E402
import stage18_mercado as M  # noqa: E402
import stage19_oficios as O  # noqa: E402
import build_stage16 as B16  # noqa: E402
import build_stage18 as B18  # noqa: E402
import lod_utils as LU  # noqa: E402

REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
SRC = os.path.join(REPO, "blender", f"{C.BLEND_BASENAME}_v18.blend")
OUT = os.path.join(REPO, "blender", f"{C.BLEND_BASENAME}_v19.blend")
REPORT = os.path.join(REPO, "docs", "reports", "stage19_oficios.json")
SEED = 1901
BUDGET = {"Gremio_Mineros": 5000, "Gremio_Herbolarios": 6000, "Gremio_Cazadores": 5000, "Gremio_Pescadores": 5000,
          "Taller_GranForja": 8000, "Taller_Curtiduria": 5000, "Taller_Sastreria": 5000, "Taller_Carpinteria": 6000,
          "Taller_Alquimia": 5000, "Taller_Hornos": 4000, "Taller_JoyeriaTallado": 3000, "CrisolPiedras": 9000,
          "CasaReparaciones": 3500}
tris = B18.tris


def save():
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)


def mk(name):
    return bpy.data.objects[f"MARKER_Bld_{name}"]


def mb_object(mb, name, col, parent, mw=None):
    o = B.to_object(mb, name, col)
    mb.bm.free()
    o.parent = parent
    if mw is not None:
        o.matrix_world = mw
    B.box_uv(o)
    return o


def props_empty(root, pcol):
    pe = next((c for c in root.children if c.name.endswith("_Props")), None)
    if pe is None:
        pe = bpy.data.objects.new(f"{root.name}_Props", None)
        pcol.objects.link(pe)
        pe.parent = root
    return pe


def prop(name, me, pcol, parent, mw):
    o = bpy.data.objects.new(name, me)
    pcol.objects.link(o)
    o.parent = parent
    o.matrix_world = mw
    return o


def shared(name, fn):
    return bpy.data.meshes.get(name) or L._shared_mesh(name, fn, B.box_uv)


def box_collider(name, col, root, boxes, mw=None):
    m = K.MB()
    for lo, hi in boxes:
        m.box(lo, hi, "MAT_Wall_Gray")
    o = B18.collider(m, name, col, root)
    if mw is not None:
        o.matrix_world = mw
    return o


def kit(name, pisos, col, pcol, marker=None, footprint=None, loc_local=(0, 0, 0), **kw):
    """fit_iso_height con el marcador o con una huella distinta dentro de su parcela (loc_local en el marco del
    marcador)."""
    m = marker if marker is not None else mk(name)
    if footprint is None:
        root, objs, rep = B.fit_iso_height(name, pisos, marker=m, seed=SEED, collection=col, props_collection=pcol, **kw)
    else:
        mw = m.matrix_world @ Matrix.Translation(loc_local)
        root, objs, rep = B.fit_iso_height(name, pisos, footprint=footprint, location=tuple(mw.translation),
                                           rot_z=m.matrix_world.to_euler().z, seed=SEED, collection=col,
                                           props_collection=pcol, interior=bool(m.get("interior", True)), **kw)
        root["marker"] = m.name
        rep["marker"] = m.name
        rep["note_footprint"] = f"huella {footprint} dentro de la parcela {m['footprint']} (desplazada {tuple(loc_local)})"
    return root, objs, rep


def finish_kit(name, root, objs, rep, st, colo, extra=None):
    B18._finish_kit(name, root, objs, rep, st, colo, extra=extra)
    st[name]["budget"] = BUDGET.get(name)
    tot = st[name]["tris"]["total_body_roof"] + sum(v for k, v in (extra or {}).items() if k.endswith("_tris"))
    st[name]["tris"]["total_with_extras"] = tot
    st[name]["ok"] = tot <= BUDGET[name] if name in BUDGET else None


def custom(name, fn, col, st, extra_mass=None, rng=None):
    """Edificio hecho a mano en su marcador: Body, Roof, LOD1 (diezmado), LOD2 (volumetria), puerta, interior."""
    m = mk(name)
    root = B16.new_root(name, m, col, m["label"])
    rng = rng or random.Random(B.rng_for(name, SEED))
    body_mb, roof_mb, info, mass = fn(rng)
    body = B16.mesh_obj(body_mb, f"{name}_Body", col, root)
    roof = B16.mesh_obj(roof_mb, f"{name}_Roof", col, root)
    lods = {"LOD1": P13.lods(body, col, (("LOD1", 0.5),))["LOD1"] + P13.lods(roof, col, (("LOD1", 0.5),))["LOD1"]}
    o2, n2, _, note = LU.massing_spec(f"{name}_Body_LOD2", mass, [body, roof], col, root)
    lods["LOD2"], lods["LOD2_material"] = n2, note
    dm = iv = None
    if m.get("interior", True) and info.get("door") is not None:
        dm = B16.door_marker(name, col, root, info["door"])
        (cx, cy), (sx, sy, sz) = info["interior"]
        iv = B16.interior(name, col, root, sx / 2, sy / 2, sz, {})
        iv.location = (cx, cy, 0.0)
    t = {"Body": tris(body), "Roof": tris(roof)}
    t["total"] = t["Body"] + t["Roof"]
    st[name] = {"marker": m.name, "tris": t, "budget": BUDGET.get(name), "ok": t["total"] <= BUDGET.get(name, 1e9),
                "lods": lods, "info": {k: v for k, v in info.items() if k not in ("interior",)},
                "door_marker": dm.name if dm else None, "interior": [iv.name, list(iv["interior_size_m"])] if iv else None,
                "iso_blocks": B18.iso_check(root, [body, roof]),
                "footprint_check": B16.check_footprint(body, float(m["footprint_w"]) / 2, float(m["footprint_d"]) / 2)}
    return root, body, roof, info


# ---------------------------------------------------------------------------
def build_all(col, pcol, kitcol, st):
    roots = []
    # 1. Gremio de Mineros: bocamina, vagonetas, carriles, pico dorado y castillete
    name = "Gremio_Mineros"
    root, objs, rep = kit(name, 2, col, pcol, tipo_techo="gable", estilo="stone", module_w=3.6,
                          opts={"no_buttress": True, "side_detail": {"back": 1, "left": 1, "right": 1}, "roof_seg": 5.0})
    W, D = rep["footprint"]
    dx = rep["door_local"][0]
    eb, er = K.MB(), K.MB()
    info = O.mineros_extras(eb, er, W, D, dx, rep["ridge_height_m"])
    M.merge_mb_into(objs["Body"], eb)
    M.merge_mb_into(objs["Roof"], er)
    B.box_uv(objs["Body"])
    B.box_uv(objs["Roof"])
    pe = props_empty(root, pcol)
    rm = K.MB()
    n_sl = O.rails(rm, 5.5)
    rails = mb_object(rm, f"{name}_Prop_Rails", pcol, pe, root.matrix_world @ Matrix.Translation((dx, D / 2 - 0.3, 0)))
    cart = shared("PROP_MineCart", O.mine_cart)
    carts = [prop(f"{name}_Prop_MineCart_{k:02d}", cart, pcol, pe,
                  root.matrix_world @ Matrix.Translation((dx, D / 2 + y, 0.15)) @ Matrix.Rotation(math.pi / 2, 4, "Z"))
             for k, y in enumerate((1.0, 3.6), 1)]
    colo = box_collider(f"{name}-colonly", col, root, [((-W / 2, -D / 2, 0), (W / 2, D / 2, rep["eave_height_m"]))])
    finish_kit(name, root, objs, rep, st, colo, extra={**info, "rails_sleepers": n_sl, "carts": len(carts),
                                                       "rails_tris": tris(rails), "carts_tris": tris(carts[0]) * 2})
    roots.append(root)

    # 2. Gremio de Herbolarios (invernadero)
    r, b, rf, info = custom("Gremio_Herbolarios", O.herbolarios, col, st)
    st["Gremio_Herbolarios"]["collision"] = box_collider(
        "Gremio_Herbolarios-colonly", col, r, [((-8, -5.0, 0), (8, 2.2, 3.2)), ((-11, 2.6, 0), (11, 4.4, 0.75))]).name
    roots.append(r)

    # 3. Gremio de Pescadores: redes, barcas en el muelle existente (CAU_Muelle_Pescadores)
    name = "Gremio_Pescadores"
    root, objs, rep = kit(name, 2, col, pcol, tipo_techo="gable", estilo="timber", module_w=3.6,
                          opts={"no_buttress": True, "side_detail": {"back": 1, "left": 1, "right": 1}, "roof_seg": 5.0,
                                "eave": 0.7})
    W, D = rep["footprint"]
    pe = props_empty(root, pcol)
    net = shared("PROP_NetFrame", O.net_frame)
    nets = [prop(f"{name}_Prop_Net_{k:02d}", net, pcol, pe,
                 root.matrix_world @ Matrix.Translation((-W / 2 - 1.2, y, 0)) @ Matrix.Rotation(math.pi / 2, 4, "Z"))
            for k, y in enumerate((-4.0, 0.0, 4.0), 1)]
    boatm = shared("PROP_Boat_4m", O.boat)
    import bmesh
    from mathutils.bvhtree import BVHTree
    cw = bpy.data.objects["CAU_Water"]
    tb = bmesh.new()
    tb.from_mesh(cw.data)
    tb.transform(cw.matrix_world)
    wbvh = BVHTree.FromBMesh(tb)
    tb.free()

    def g(x, y):                                     # cota de la lamina de agua (no la del lecho)
        h = wbvh.ray_cast(Vector((x, y, 100.0)), Vector((0, 0, -1)))
        return h[0].z if h[0] else 4.3
    boats = []
    for k, mn in enumerate(("MARKER_Mooring_01", "MARKER_Mooring_03"), 1):
        mo = bpy.data.objects[mn]
        a = math.radians(mo["angle"])
        d = Vector((math.cos(a), math.sin(a), 0))
        p = mo.matrix_world.translation + d * 1.3
        zw = g(p.x, p.y)
        boats.append(prop(f"{name}_Prop_Boat_{k:02d}", boatm, pcol, pe,
                          Matrix.Translation((p.x, p.y, zw - 0.12)) @ Matrix.Rotation(a + math.pi / 2, 4, "Z")))
    colo = box_collider(f"{name}-colonly", col, root, [((-W / 2, -D / 2, 0), (W / 2, D / 2, rep["eave_height_m"]))])
    finish_kit(name, root, objs, rep, st, colo, extra={"nets": len(nets), "boats": [b_.name for b_ in boats],
                                                       "nets_tris": tris(nets[0]) * 3, "boats_tris": tris(boats[0]) * 2,
                                                       "pier": "CAU_Muelle_Pescadores (etapa 07, 8 x 3) reutilizado"})
    roots.append(root)

    # 5. La Gran Forja: edificio de 16 x 16 + patio de fundicion 10 x 16 en el extremo exterior
    name = "Taller_GranForja"
    m = mk(name)
    ex = m.matrix_world.to_3x3() @ Vector((1, 0, 0))
    sgn = 1 if ex.dot(m.matrix_world.translation.normalized()) > 0 else -1
    root, objs, rep = kit(name, 1, col, pcol, footprint=(16.0, 16.0), loc_local=(-sgn * 5.0, 0, 0), tipo_techo="gable",
                          estilo="stone", module_w=4.0, opts={"no_buttress": True, "side_detail": {"back": 1}, "roof_seg": 4.5})
    eb = K.MB()
    O.chimney_tall(eb, sgn * 6.9, -4.5, 0.0, 14.0)
    M.merge_mb_into(objs["Body"], eb)
    B.box_uv(objs["Body"])
    ym = K.MB()
    x0, x1 = (3.0, 13.0) if sgn > 0 else (-13.0, -3.0)
    yinfo = O.forja_yard(ym, x0, x1, 8.0, random.Random(SEED))
    yard = mb_object(ym, f"{name}_Yard", col, root, m.matrix_world.copy())
    pe = props_empty(root, pcol)
    anv = shared("PROP_Anvil", O.anvil)
    anvils = [prop(f"{name}_Prop_Anvil_{k:02d}", anv, pcol, pe, m.matrix_world @ Matrix.Translation((x, y, 0)))
              for k, (x, y) in enumerate(yinfo["anvils"], 1)]
    stm = bpy.data.objects.new("MARKER_GranForja_Steam", None)
    col.objects.link(stm)
    stm.parent = root
    stm.matrix_world = m.matrix_world @ Matrix.Translation(yinfo["steam"])
    stm["godot"] = "vapor del abrevadero de temple (particulas)"
    colo = box_collider(f"{name}-colonly", col, root, [((-8, -8, 0), (8, 8, rep["eave_height_m"]))])
    box_collider(f"{name}_Yard-colonly", col, root, [((x0, -8, 0), (x1, -7.6, 1.0)), ((x0, 7.6, 0), (x1, 8, 1.0)),
                                                       (((x0 + x1) / 2 - 1.2, -1.2, 0), ((x0 + x1) / 2 + 1.2, 1.2, 1.9))],
                 m.matrix_world.copy())
    finish_kit(name, root, objs, rep, st, colo, extra={"chimney_m": 14.0, "yard_tris": tris(yard), "anvils": len(anvils),
                                                       "anvils_tris": tris(anvils[0]) * 3, "yard_side": "+X" if sgn > 0 else "-X",
                                                       "steam_marker": stm.name, "embers": "MAT_Embers (1.5, natural)"})
    roots.append(root)

    # 6. Curtiduria: casa 16 x 7 atras, patio delante con 4 tinas y 2 bastidores
    name = "Taller_Curtiduria"
    m = mk(name)
    root, objs, rep = kit(name, 2, col, pcol, footprint=(16.0, 7.0), loc_local=(0, -2.5, 0), tipo_techo="gable",
                          estilo="timber", module_w=4.0, opts={"no_buttress": True, "side_detail": {"back": 1}, "roof_seg": 4.0})
    ym = K.MB()
    O.vats(ym, (-5.4, -1.8, 1.8, 5.4), 3.4)
    yard = mb_object(ym, f"{name}_Yard", col, root, m.matrix_world.copy())
    pe = props_empty(root, pcol)
    hr = shared("PROP_HideRack", O.hide_rack)
    racks = [prop(f"{name}_Prop_HideRack_{k:02d}", hr, pcol, pe,
                  m.matrix_world @ Matrix.Translation((x, 5.4, 0)) @ Matrix.Rotation(rz, 4, "Z"))
             for k, (x, rz) in enumerate(((-7.2, math.pi / 2), (7.2, -math.pi / 2)), 1)]
    colo = box_collider(f"{name}-colonly", col, root, [((-8, -3.5, 0), (8, 3.5, rep["eave_height_m"]))])
    finish_kit(name, root, objs, rep, st, colo, extra={"vats": 4, "yard_tris": tris(yard), "racks": len(racks),
                                                       "racks_tris": tris(racks[0]) * 2})
    roots.append(root)

    # 7. Sastreria: planta baja cerrada + planta alta abierta de telares con balcones y telas colgadas
    name = "Taller_Sastreria"
    root, objs, rep = kit(name, 1, col, pcol, tipo_techo="flat", estilo="guild", module_w=4.0,
                          opts={"no_buttress": True, "side_detail": {"back": 1}})
    W, D = rep["footprint"]
    eb, er = K.MB(), K.MB()
    z0 = rep["eave_height_m"] + 0.12
    top = O.loggia(eb, er, W, D, z0, 3.0, random.Random(SEED + 3))
    rng = random.Random(SEED + 4)
    for side in ("+Y", "-Y", "+X", "-X"):
        eb.push(L.frame(side, W / 2, D / 2))
        half = W / 2 if side in ("+Y", "-Y") else D / 2
        eb.box((-half + 0.4, 0.0, z0 - 0.1), (half - 0.4, 0.8, z0 + 0.02), K.M_WOOD)
        eb.box((-half + 0.4, 0.72, z0 + 0.85), (half - 0.4, 0.8, z0 + 0.95), K.M_WOOD)
        O.hanging_cloths(eb, 2 * half - 1.0, 0.82, z0 + 0.95, rng, n=4 if side in ("+Y", "-Y") else 3)
        eb.pop()
    M.merge_mb_into(objs["Body"], eb)
    M.merge_mb_into(objs["Roof"], er)
    B.box_uv(objs["Body"])
    B.box_uv(objs["Roof"])
    colo = box_collider(f"{name}-colonly", col, root, [((-W / 2, -D / 2, 0), (W / 2, D / 2, z0 + 3.0))])
    finish_kit(name, root, objs, rep, st, colo, extra={"open_loom_floor_z": round(z0, 2), "ridge_m": round(top, 2), "looms": 2})
    st[name]["iso_blocks_full"] = B18.iso_check(root, [objs["Body"], objs["Roof"]])
    roots.append(root)

    # 8. Carpinteria: entramado (vigas vistas), rueda hidraulica aparte (WATERWHEEL), sierra y troncos
    name = "Taller_Carpinteria"
    root, objs, rep = kit(name, 2, col, pcol, tipo_techo="gable", estilo="timber", module_w=4.0,
                          opts={"no_buttress": True, "side_detail": {"back": 1}, "roof_seg": 4.0})
    W, D = rep["footprint"]
    wm = bpy.data.objects["MARKER_Cauce_WaterWheel"]
    wz = float(wm["water_z"]) + 3.5 / 2 - 0.3
    wme = bpy.data.meshes.get("WATERWHEEL_3p5") or L._shared_mesh("WATERWHEEL_3p5", O.waterwheel, B.box_uv)
    wheel = bpy.data.objects.new(f"{name}_WATERWHEEL", wme)
    col.objects.link(wheel)
    wheel.parent = root
    wl = wm.matrix_world.translation
    wheel.matrix_world = Matrix.Translation((wl.x, wl.y, wz)) @ wm.matrix_world.to_3x3().to_4x4()
    wheel["animate"] = "giro sobre su eje Y local (eje hacia la Carpinteria)"
    wheel["diameter_m"] = 3.5
    ax = K.MB()
    p0 = Vector((wl.x, wl.y, wz))
    dirv = (wm.matrix_world.to_3x3() @ Vector((0, 1, 0))).normalized()     # eje de la rueda, hacia la Carpinteria
    p1 = p0 + dirv * 3.2
    ax.rod(tuple(p0 + dirv * 0.6), tuple(p1), 0.1, K.M_IRON)
    ax.box((p1.x - 0.4, p1.y - 0.4, wz - 0.5), (p1.x + 0.4, p1.y + 0.4, wz + 0.3), K.M_STONE)
    axle = mb_object(ax, f"{name}_Axle", col, root)
    axle.matrix_world = Matrix.Identity(4)
    pe = props_empty(root, pcol)
    lp = shared("PROP_LogPile", lambda mb: O.log_pile(mb, 4.0, 0.28, 3))
    saw = shared("PROP_FrameSaw", lambda mb: (mb.box((-1.2, -0.3, 0.7), (1.2, 0.3, 0.78), K.M_WOOD),
                                             [mb.rod((x, y, 0.0), (x * 0.9, 0.0, 0.75), 0.04, K.M_WOOD)
                                              for x in (-1.0, 1.0) for y in (-0.35, 0.35)],
                                             mb.box((-0.9, -0.02, 0.8), (0.9, 0.02, 1.9), K.M_WOOD, skip=("y-", "y+")),
                                             mb.box((-0.75, -0.005, 0.85), (0.75, 0.005, 1.85), K.M_IRON)))
    logs = prop(f"{name}_Prop_LogPile", lp, pcol, pe, root.matrix_world @ Matrix.Translation((W / 2 - 2.5, D / 2 + 1.6, 0)))
    sw = prop(f"{name}_Prop_FrameSaw", saw, pcol, pe, root.matrix_world @ Matrix.Translation((-W / 2 + 2.5, D / 2 + 1.6, 0)))
    colo = box_collider(f"{name}-colonly", col, root, [((-W / 2, -D / 2, 0), (W / 2, D / 2, rep["eave_height_m"]))])
    finish_kit(name, root, objs, rep, st, colo, extra={"waterwheel": wheel.name, "waterwheel_tris": tris(wheel),
                                                       "axle_tris": tris(axle), "logs_tris": tris(logs), "saw_tris": tris(sw),
                                                       "wheel_center_world": [round(c, 2) for c in p0]})
    roots.append(root)

    # 9-13 hechos a mano
    r, b, rf, info = custom("Taller_Alquimia", O.alquimia, col, st)
    for k, (x, y, z) in enumerate(info["chimneys"], 1):
        e = bpy.data.objects.new(f"MARKER_Alquimia_Smoke_{k:02d}", None)
        col.objects.link(e)
        e.parent = r
        e.location = (x, y, z)
        e["godot"] = "humo de color (particulas)"
    box_collider("Taller_Alquimia-colonly", col, r, [((-3.25, -2.75, 0), (3.25, 3.75, 12.8))])
    roots.append(r)
    r, b, rf, info = custom("Taller_Hornos", O.hornos, col, st)
    box_collider("Taller_Hornos-colonly", col, r, [((-7, -5, 0), (-1, 1, 3.9))])
    roots.append(r)
    r, b, rf, info = custom("Taller_JoyeriaTallado", O.joyeria, col, st)
    st["Taller_JoyeriaTallado"]["note"] = "10 x 10 (prompt) dentro de la parcela 16 x 12 del marcador, alineado al frente"
    pe = props_empty(r, pcol)
    mg = shared("PROP_Magnifier", O.magnifier)
    mags = []
    for k, (side, u) in enumerate(info["magnifiers"], 1):
        fr = Matrix.Translation((0, info["off_y"], 0)) @ L.frame(side, 5.0, 5.0)
        mags.append(prop(f"Taller_JoyeriaTallado_Prop_Lupa_{k:02d}", mg, pcol, pe,
                         r.matrix_world @ fr @ Matrix.Translation((u, -0.12, 2.0))))
    lan = prop("Taller_JoyeriaTallado_Prop_LANTERN_Shard", B.prop_mesh("LANTERN_Shard"), pcol, pe,
               r.matrix_world @ Matrix.Translation((-1.3, info["off_y"] + 5.0, 2.7)))
    st["Taller_JoyeriaTallado"]["props"] = {"lupas": len(mags), "lupas_tris": tris(mags[0]) * len(mags), "farolillo": lan.name}
    box_collider("Taller_JoyeriaTallado-colonly", col, r, [((-5, -4, 0), (5, 6, 6.6))])
    roots.append(r)
    r, b, rf, info = custom("CrisolPiedras", O.crisol, col, st)
    rng = random.Random(SEED + 11)
    stones = []
    for k in range(7):
        me = L._shared_mesh(f"CRISOL_FloatStone_{k + 1:02d}", lambda mb: O.float_stone(mb, rng), B.box_uv)
        o = bpy.data.objects.new(f"CRISOL_FloatStone_{k + 1:02d}", me)
        col.objects.link(o)
        o.parent = r
        a = 2 * math.pi * k / 7
        rr = 0.4 + 0.8 * (k % 3) / 2
        o.location = (rr * math.cos(a), rr * math.sin(a), 2.4 + 0.35 * k)
        o.rotation_euler = (rng.uniform(-0.4, 0.4), rng.uniform(-0.4, 0.4), rng.uniform(0, math.pi))
        o["animate"] = "flotar y girar sobre el cuenco"
        stones.append(o)
    st["CrisolPiedras"]["float_stones"] = {"count": len(stones), "tris_each": [tris(s) for s in stones]}
    c = P13.cylinder_col("CrisolPiedras-colonly", 11.0, 0.0, 8.0, 16, col)
    c.parent = r
    roots.append(r)
    r, b, rf, info = custom("CasaReparaciones", O.reparaciones, col, st)
    pe = props_empty(r, pcol)
    racks = [prop(f"CasaReparaciones_Prop_TOOL_Rack_{k:02d}", B.prop_mesh("TOOL_Rack"), pcol, pe,
                  r.matrix_world @ Matrix.Translation(p)) for k, p in enumerate(info["tool_racks"], 1)]
    st["CasaReparaciones"]["props"] = {"tool_racks": len(racks), "tris": tris(racks[0]) * 2}
    box_collider("CasaReparaciones-colonly", col, r, [((-8, -5, 0), (8, -4.5, 4.3)), ((-8, -4.5, 0), (-7.5, 0, 3.8)),
                                                       ((7.5, -4.5, 0), (8, 0, 3.8))])
    roots.append(r)

    # casas decorativas
    for k in (1, 2):
        name = f"OFI_Casa_{k:02d}"
        rng = random.Random(B.rng_for(name, SEED))
        root, objs, rep = kit(name, rng.choice((2, 3)), col, pcol, tipo_techo=rng.choice(("gable", "gable_front")),
                              estilo=rng.choice(("timber", "stone")), opts={"no_buttress": True, "side_detail": {"back": 1}})
        W, D = rep["footprint"]
        colo = box_collider(f"{name}-colonly", col, root, [((-W / 2, -D / 2, 0), (W / 2, D / 2, rep["eave_height_m"]))])
        finish_kit(name, root, objs, rep, st.setdefault("casas", {}), colo)
        roots.append(root)
    return roots


def build_cazadores(kitcol, pcol, st):
    """Gremio de Cazadores SIN PARCELA (no hay MARKER_Bld_Gremio_Cazadores): casa 20 x 14 + campo de tiro 20 x 10,
    montado en la zona del kit hasta que se decida su sitio."""
    name = "Gremio_Cazadores"
    tmp = bpy.data.objects.new("TMP_marker_cazadores", None)
    kitcol.objects.link(tmp)
    tmp.location = (3200.0, 1250.0, 0.0)
    tmp["footprint"], tmp["footprint_w"], tmp["footprint_d"], tmp["interior"] = "20x14", 20.0, 14.0, True
    bpy.context.view_layer.update()
    root, objs, rep = B.build_building(name, pisos=2, marker=tmp, tipo_techo="gable", estilo="timber", seed=SEED,
                                       collection=kitcol, props_collection=pcol, module_w=4.0,
                                       opts={"no_buttress": True, "side_detail": {"back": 1, "left": 1, "right": 1},
                                             "roof_seg": 5.0, "eave": 0.8})
    bpy.data.objects.remove(tmp)
    root["placement"] = "PENDIENTE: no existe MARKER_Bld_Gremio_Cazadores en el archivo"
    W, D = rep["footprint"]
    pe = props_empty(root, pcol)
    ant = shared("PROP_Antlers", O.antlers)
    antl = [prop(f"{name}_Prop_Antlers_{k:02d}", ant, pcol, pe, root.matrix_world @ mw_) for k, mw_ in enumerate((
        Matrix.Translation((rep["door_local"][0], D / 2 + 0.02, 3.0)),
        Matrix.Translation((W / 2 + 0.02, 0.0, rep["eave_height_m"] + 1.2)) @ Matrix.Rotation(-math.pi / 2, 4, "Z"),
        Matrix.Translation((-W / 2 - 0.02, 0.0, rep["eave_height_m"] + 1.2)) @ Matrix.Rotation(math.pi / 2, 4, "Z")), 1)]
    hr = shared("PROP_HideRack", O.hide_rack)
    racks = [prop(f"{name}_Prop_HideRack_{k:02d}", hr, pcol, pe, root.matrix_world @ Matrix.Translation((x, D / 2 + 1.5, 0)))
             for k, x in enumerate((-7.0, -4.8, 4.8), 1)]
    tg = shared("PROP_Target", O.target)
    targets = [prop(f"{name}_Prop_Target_{k:02d}", tg, pcol, pe,
                    root.matrix_world @ Matrix.Translation((-8.0 + 3.2 * k, -D / 2 - 9.0, 0)))
               for k in range(6)]
    fm = K.MB()
    y0, y1 = -D / 2 - 10.0, -D / 2
    for x in (-10.0, 10.0):
        fm.box((x - 0.06, y0, 0.0), (x + 0.06, y1, 0.08), K.M_WOOD)
        for y in [y0 + 2.5 * i for i in range(5)]:
            fm.box((x - 0.07, y - 0.07, 0.0), (x + 0.07, y + 0.07, 1.1), K.M_WOOD, skip=("z-",))
        fm.box((x - 0.04, y0, 0.95), (x + 0.04, y1, 1.03), K.M_WOOD, skip=("y-", "y+"))
    fm.box((-10.0, y0 - 0.04, 0.95), (10.0, y0 + 0.04, 1.03), K.M_WOOD, skip=("x-", "x+"))
    fm.box((-9.0, y1 - 1.6, 0.9), (9.0, y1 - 1.45, 1.0), K.M_WOOD)
    fence = mb_object(fm, f"{name}_Range", kitcol, root, root.matrix_world.copy())
    t = {"Body": tris(objs["Body"]), "Roof": tris(objs["Roof"]), "props": sum(tris(o) for o in antl + racks + targets),
         "range": tris(fence)}
    t["total"] = t["Body"] + t["Roof"] + t["props"] + t["range"]
    st[name] = {"placement": root["placement"], "kit_location": [3200.0, 1250.0], "tris": t, "budget": BUDGET[name],
                "ok": t["total"] <= BUDGET[name], "floors": rep["floors"], "antlers": len(antl), "hide_racks": len(racks),
                "targets": len(targets), "range_m": "20 x 10 (detras de la casa)"}
    return root


def main():
    st = {}
    bpy.ops.wm.open_mainfile(filepath=SRC)
    save()
    st["saved_before"] = os.path.relpath(OUT, REPO)
    B.ensure_materials()
    st["materials"] = O.ensure_materials()
    col = bpy.data.collections["BLD_OFICIOS"]
    pcol = bpy.data.collections["BLD_PROPS"]
    kitcol = bpy.data.collections["BLD_KIT"]
    for o in list(col.all_objects):
        bpy.data.objects.remove(o)
    roots = build_all(col, pcol, kitcol, st)
    caz = build_cazadores(kitcol, pcol, st)
    for o in bpy.data.objects:
        if o.name.endswith(("_LOD1", "_LOD2")):
            o.hide_render = True
            o.hide_set(True)
    bpy.context.view_layer.update()
    import build_stage17 as B17
    with open(os.path.join(REPO, "docs", "reports", "stage15_faro.json")) as fh:
        tgt = Vector(json.load(fh)["visibility"]["target"])
    B17.faro_visibility(st, tgt)
    import stage11_godot as G
    objs = []
    for r in roots:
        objs += [r] + list(r.children_recursive)
    path = os.path.join(REPO, "export", "godot", "concordia_oficios.glb")
    size = G.export_glb(list(dict.fromkeys(objs)), path)
    st["export"] = {"file": os.path.relpath(path, REPO), "mb": round(size / 2 ** 20, 2), **G.glb_info(path)}
    path2 = os.path.join(REPO, "export", "godot", "concordia_gremio_cazadores_sin_parcela.glb")
    G.export_glb([caz] + list(caz.children_recursive), path2)
    for o in bpy.data.objects:
        if o.name.endswith(("_LOD1", "_LOD2")):
            o.hide_set(True)
    save()
    with open(REPORT, "w") as fh:
        json.dump(st, fh, indent=1, ensure_ascii=False, default=str)
    print("saved:", OUT)
    for k, v in st.items():
        if isinstance(v, dict) and isinstance(v.get("tris"), dict):
            fl = v.get("floors")
            ir = v.get("iso_rule")
            hist = ir.get("history") if isinstance(ir, dict) else None
            print(k, "tris", v["tris"].get("total_with_extras", v["tris"].get("total", v["tris"].get("total_body_roof"))),
                  "budget", v.get("budget"), "ok", v.get("ok"), "floors", fl, "iso", hist or v.get("iso_blocks"),
                  "fp", (v.get("footprint_ground_check") or v.get("footprint_check") or {}).get("over_y_m"))
    for k, v in st.get("casas", {}).items():
        print(k, v["floors"], v["tris"]["total_body_roof"], (v.get("iso_rule") or {}).get("history"))
    print(json.dumps({k: (v["axis_pct"], v.get("best_lane_pct")) for k, v in st["faro_visibility"].items()}, ensure_ascii=False))
    print(json.dumps(st["export"], default=str)[:300])


if __name__ == "__main__":
    main()
