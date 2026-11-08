"""
CONCORDIA - Etapa 26 (E13): decisiones del usuario sobre el balance de la etapa 25.
concordia_v25.blend -> concordia_v26.blend + docs/reports/stage26_decisiones.json

Pasos (en el orden pedido; cada uno abre v26 si ya existe, o v25 la primera vez / con --fresh, y guarda v26):
  moradas    punto 2: NE y SO, un balcon por puerta y escalera orientada a CAM_Iso; prueba de puertas de las 4 Moradas
  raza04     punto 3: RAZ_B02_Casa_04 a 1 planta (puerta de CasaRaza_02)
  cazadores  punto 4: entrada norte del campo de tiro con portillo, camino 8 x 2 m y malla de navegacion conectada
  razas      punto 5: casas adosadas 4 x 8 y huecos del sector Sur (stage26_razas.py)
  subasta    punto 9: Gran Subasta sin interior
  salon      punto 7: Salon de las Hazanas occludes_iso = true; pozo del Santuario provisional = true
  pipes      punto 8: tubos de luz Tesoreria -> Faro (stage26_pipes.py)
python build_stage26.py -- [--fresh] paso [paso ...]
"""

import json
import math
import os
import sys

import bpy
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import concordia_const as C  # noqa: E402

REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
SRC = os.path.join(REPO, "blender", f"{C.BLEND_BASENAME}_v25.blend")
OUT = os.path.join(REPO, "blender", f"{C.BLEND_BASENAME}_v26.blend")
REPORT = os.path.join(REPO, "docs", "reports", "stage26_decisiones.json")
CAM_BACK = Vector((0.577, -0.577, 0.577)).normalized()


def save():
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)


def load_report():
    if os.path.exists(REPORT):
        with open(REPORT) as fh:
            return json.load(fh)
    return {}


def write_report(st):
    with open(REPORT, "w") as fh:
        json.dump(st, fh, indent=1, ensure_ascii=False, default=str)


def tris(o):
    return sum(len(p.vertices) - 2 for p in o.data.polygons)


def remove_tree(root):
    for o in list(root.children_recursive) + [root]:
        me = o.data if o.type == "MESH" else None
        bpy.data.objects.remove(o)
        if me is not None and me.users == 0:
            bpy.data.meshes.remove(me)


def city_bvh():
    """Body y Roof (LOD0) de todos los edificios: para pruebas de puertas sueltas."""
    verts, faces, owner = [], [], []
    for o in bpy.data.objects:
        if o.type != "MESH" or not o.name.endswith(("_Body", "_Roof")) or o.hide_render:
            continue
        r = o
        while r.parent is not None:
            r = r.parent
        mw = o.matrix_world
        b = len(verts)
        verts += [mw @ v.co for v in o.data.vertices]
        for p in o.data.polygons:
            faces.append([b + i for i in p.vertices])
            owner.append(r.name)
    return BVHTree.FromPolygons(verts, faces, epsilon=1e-6), owner


def door_visible(dm, bvh, owner, own_name):
    """Criterio de la etapa 24: se ven >= 2 de 3 puntos (0.3 / 1.1 / 2.0 m, 0.35 m delante de la puerta)."""
    mw = dm.matrix_world
    n = (mw.to_3x3() @ Vector((0, 1, 0))).normalized()
    hidden, by = 0, []
    for h in (0.3, 1.1, 2.0):
        o = mw.translation + n * 0.35 + Vector((0, 0, h))
        for _ in range(10):
            loc, _n, idx, _d = bvh.ray_cast(o, CAM_BACK, 500.0)
            if loc is None:
                break
            if owner[idx] == own_name:
                o = loc + CAM_BACK * 0.02
                continue
            hidden += 1
            by.append(owner[idx])
            break
    return hidden < 2, hidden, by


# --------------------------------------------------------------------------- punto 2 y 6: Moradas
def morada_sets():
    """Triangulos por conjunto (LOD0 = cuerpo + cubierta + puertas, placas y faroles; LOD2) y presupuesto por casa."""
    import stage23_moradas as M
    out = {}
    for key in ("NE", "NO", "SE", "SO"):
        col = bpy.data.collections[f"BLD_MORADAS_{key}"]
        roots = [o for o in col.objects if o.parent is None and o.type == "EMPTY" and o.name.startswith("Morada_")]
        t0 = t2 = 0
        worst = {}
        over = []
        units = 0
        for r in roots:
            t = 0
            for c in r.children_recursive:
                if c.type != "MESH" or c.name.endswith(("-colonly", "_LOD1", "_LOD2")) or "InteriorVolume" in c.name:
                    continue
                if c.name in (f"{r.name}_Body", f"{r.name}_Roof") or c.name.startswith(("DOOR_", "PLATE_", "LANTERN_")):
                    t += tris(c)
            l2 = sum(tris(c) for c in r.children_recursive if c.type == "MESH" and c.name.endswith("_LOD2"))
            t0 += t
            t2 += l2
            tipo = r["tipo"]
            units += len([c for c in r.children if c.name.startswith("MARKER_Morada_Door_")])
            if t > worst.get(tipo, (0, ""))[0]:
                worst[tipo] = (t, r.name)
            if t > M.BUDGET[tipo]:
                over.append((r.name, tipo, t))
        out[key] = {"houses": len(roots), "dwellings": units, "LOD0": t0, "LOD2": t2,
                    "lod2_ratio": round(t2 / max(1, t0), 3), "max_per_type": worst, "over_budget": over,
                    "budget": dict(M.BUDGET), "ok": not over}
    return out


def blocked_cause(door, by):
    """'balcon/escalera' si la visual choca con madera delante de la fachada (y > 3.02 en la vecina); si no,
    'cuerpo/alero' (fachada o cubierta de una vecina)."""
    import stage26_moradas as S
    dm = bpy.data.objects[door]
    owner = dm.parent.name
    occ = []
    for key in ("NE", "NO", "SE", "SO"):
        for r in bpy.data.collections[f"BLD_MORADAS_{key}"].objects:
            if r.parent is None and r.type == "EMPTY":
                for part in ("Body", "Roof"):
                    o = bpy.data.objects.get(f"{r.name}_{part}")
                    if o is not None:
                        occ.append((r.name, part, o))
    verts, faces, own = [], [], []
    for nm, part, o in occ:
        mw = o.matrix_world
        b = len(verts)
        verts += [mw @ v.co for v in o.data.vertices]
        for p in o.data.polygons:
            faces.append([b + i for i in p.vertices])
            own.append((nm, part, o.data.materials[p.material_index].name if p.material_index < len(o.data.materials) else ""))
    bvh = BVHTree.FromPolygons(verts, faces, epsilon=1e-6)
    mw = dm.matrix_world
    n = (mw.to_3x3() @ Vector((0, 1, 0))).normalized()
    causes = []
    for h in (0.3, 1.1, 2.0):
        o = mw.translation + n * 0.35 + Vector((0, 0, h))
        for _ in range(10):
            loc, _n, idx, _d = bvh.ray_cast(o, S.CAM_BACK, 500.0)
            if loc is None:
                causes.append("libre")
                break
            if own[idx][0] == owner:
                o = loc + S.CAM_BACK * 0.02
                continue
            nm, part, mat = own[idx]
            lp = bpy.data.objects[nm].matrix_world.inverted() @ loc
            if part == "Roof" or "Facade" in mat or lp.y <= 3.02:
                causes.append(f"cuerpo/alero de {nm}")
            else:
                causes.append(f"balcon/escalera de {nm}")
            break
    return causes


def step_moradas(st):
    import stage23_moradas as M
    import stage26_moradas as S
    M.BAL_D, M.LANDINGS, M.STAIR_RAIL = 0.35, True, False
    import build_stage23 as B23
    before = S.door_check()
    # franja de la escalera 4.2-4.98 (0.78 m transitables); 4.4-4.98 tapa 1 puerta menos pero deja 0.58 m
    M.STAIR_Y0 = 4.2
    B23._CACHE.clear()
    S.rebuild(mode="near")
    log = {}
    best, _res = S.greedy(log=log)
    res_by_y0 = {"4.2 (aplicada)": (best, log), "4.4 (prueba aparte, etapa 26)": (15, "0.58 m de escalera: estrecha")}
    print("moradas", best, log, flush=True)
    final = S.door_check()
    flips = [o.name for o in bpy.data.objects if o.name.startswith("Morada_") and o.parent is None and
             str(o.get("section", "")).endswith(("_bp", "_bm")) and
             (int(o["section"].endswith("_bp")) * 2 - 1) != S.stair_for(o, "near")]
    blocked = []
    for k, v in final.items():
        for door, by in v["blocked"]:
            blocked.append({"door": door, "by": by, "set": k, "rays": blocked_cause(door, by)})
    st["moradas"] = {
        "design": {"balcony_m": [M.BAL_W, M.BAL_D], "balconies_per_habitacion": 6, "stair_strip_y": [M.STAIR_Y0, 4.98],
                   "stair_rule": "pie de la escalera en el extremo alejado de CAM_Iso; sube hacia el extremo cercano",
                   "stair_flipped_houses": flips, "landings": "rellano de llegada a 2 balcones (puertas x=0 planta 2 y x=-2s "
                   "planta 3)", "stair_handrail": "sin pasamanos en los tramos (tapaba puertas vecinas)",
                   "patch": "tablas de dos tonos y una tabla de remiendo por casa", "y0_tried": res_by_y0},
        "rebuilt": sorted(o.name for o in bpy.data.objects if o.name.startswith("Morada_") and o.parent is None and
                          str(o.get("section", "")).endswith(("_bp", "_bm"))),
        "doors_before": {k: {"doors": v["doors"], "facing": v["facing"], "blocked": len(v["blocked"])} for k, v in before.items()},
        "doors_after": {k: {"doors": v["doors"], "facing": v["facing"], "blocked": len(v["blocked"])} for k, v in final.items()},
        "blocked_after": blocked}
    st["moradas_sets"] = morada_sets()


# --------------------------------------------------------------------------- punto 3
def step_raza04(st):
    import build_stage18 as B18
    import build_stage25 as B25
    g = B18.ground_fn()
    name = "RAZ_B02_Casa_04"
    h0 = B25.height_now(bpy.data.objects[name])
    rows = []
    B25.build_race_house(name, "R02", bpy.data.objects[f"MARKER_Bld_{name}"], "p1", g, rows)
    r = bpy.data.objects[name]
    r["faro_step"] = "-"
    r["remedy"] = "1 planta: dejaba tapada la puerta de CasaRaza_02 (etapa 26)"
    bpy.context.view_layer.update()
    bvh, owner = city_bvh()
    ok, hidden, by = door_visible(bpy.data.objects["MARKER_CasaRaza_02_Door"], bvh, owner, "CasaRaza_02")
    st["raza04"] = {"name": name, "floors": r.get("floors"), "h_before": h0, "h_after": B25.height_now(r),
                    "CasaRaza_02_door_visible": ok, "hidden_points": hidden, "by": by, "build": rows}


# --------------------------------------------------------------------------- punto 9
def step_subasta(st):
    m = bpy.data.objects["MARKER_Bld_GranSubasta"]
    m["interior"] = False
    m["note"] = "pabellon abierto sin interior (confirmado por el usuario, etapa 26); se opera desde la tarima"
    r = bpy.data.objects["GranSubasta"]
    r["interior"] = False
    removed = []
    for o in list(r.children_recursive):
        if o.name.endswith("_InteriorVolume") or (o.name.startswith("MARKER_") and "_Door" in o.name):
            removed.append(o.name)
            bpy.data.objects.remove(o)
    st["subasta"] = {"marker_interior": False, "removed": removed}


# --------------------------------------------------------------------------- punto 7
def step_salon(st):
    out = {"objects": [], "materials": {}}
    for nm in ("SALON_HAZANAS_Body", "SALON_HAZANAS_Roof"):
        o = bpy.data.objects[nm]
        o["occludes_iso"] = True
        o["fade"] = "dither en Godot (distance_fade_mode PIXEL/OBJECT_DITHER o shader con alpha hash)"
        out["objects"].append(nm)
        for s in o.material_slots:
            m = s.material
            if m is None or m.name in out["materials"]:
                continue
            b = m.node_tree.nodes.get("Principled BSDF") if m.use_nodes else None
            alpha = round(b.inputs["Alpha"].default_value, 2) if b else 1.0
            extra = [n.type for n in m.node_tree.nodes
                     if n.type not in ("BSDF_PRINCIPLED", "OUTPUT_MATERIAL", "TEX_IMAGE", "MIX", "MIX_RGB", "TEX_COORD",
                                       "MAPPING", "NORMAL_MAP", "SEPARATE_COLOR", "UVMAP")
                     and not (n.type == "GROUP" and n.node_tree and n.node_tree.name == "glTF Material Output")] \
                if m.use_nodes else []
            out["materials"][m.name] = {"principled": b is not None, "alpha": alpha, "godot": "StandardMaterial3D",
                                        "blend": getattr(m, "surface_render_method", getattr(m, "blend_method", "?")),
                                        "other_nodes": extra,
                                        "dither_ok": b is not None and not extra}
    w = bpy.data.objects["SANTUARIO_Well"]
    w["provisional"] = True
    w["note"] = "provisional hasta la etapa de interiores (decision del usuario, etapa 26)"
    out["santuario_well_provisional"] = True
    st["salon"] = out


STEPS = {"moradas": step_moradas, "raza04": step_raza04, "subasta": step_subasta, "salon": step_salon}


def main():
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    fresh = "--fresh" in args
    steps = [a for a in args if not a.startswith("--")]
    src = SRC if fresh or not os.path.exists(OUT) else OUT
    bpy.ops.wm.open_mainfile(filepath=src)
    st = {} if fresh else load_report()
    st.setdefault("source_chain", []).append(os.path.relpath(src, REPO))
    for s in steps:
        if s in ("cazadores",):
            import stage26_cazadores as SC
            SC.step(st)
        elif s == "razas":
            import stage26_razas as SR
            SR.step(st)
        elif s == "pipes":
            import stage26_pipes as SP
            SP.step(st)
        else:
            STEPS[s](st)
        st.setdefault("steps_done", []).append(s)
        save()
        write_report(st)
        print("step done:", s, flush=True)
    _ = (Matrix, math)


if __name__ == "__main__":
    main()
