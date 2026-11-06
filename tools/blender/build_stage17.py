"""
CONCORDIA - Etapa 17: decisiones sobre el Faro (E3) y pendientes A-E.
concordia_v16.blend -> concordia_v17.blend (guardada antes de empezar)

  1. CRV_LightPipe_Tesoreria_Faro: primer punto provisional (MARKER_PipeOutlet_TesoreriaMuralla, provisional=true).
  2. Rampa del Faro: cartelas de piedra, barandilla continua (exterior + interior en el tramo separado), decorativa:
     sin navegacion y colision solo por debajo de 3 m.
  5. Los 4 canales de la torre arrancan donde acaban los 4 canales de la plaza (tolerancia 5 cm).
  A. Portal: pilares 2.0 x 2.0, luz 7.8, velo 7.8 x 11; todo dentro del pedestal (r <= 6.0).
  + auditoria de materiales nuevos y memoria de texturas, visibilidad del Faro desde las 8 calles.
Salidas: export/godot/concordia_faro.glb, concordia_portal.glb, docs/reports/stage17_decisions.json
"""

import json
import math
import os
import random
import sys

import bpy  # noqa: I001
import bmesh
from mathutils import Vector
from mathutils.bvhtree import BVHTree

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import concordia_const as C  # noqa: E402
import stage13_portal as P  # noqa: E402

REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
SRC = os.path.join(REPO, "blender", f"{C.BLEND_BASENAME}_v16.blend")
OUT = os.path.join(REPO, "blender", f"{C.BLEND_BASENAME}_v17.blend")
REPORT = os.path.join(REPO, "docs", "reports", "stage17_decisions.json")
TESORERIA_OUTLET_Z = 9.6


def save():
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)


def world_bvh(objs):
    bm = bmesh.new()
    for o in objs:
        t = bmesh.new()
        t.from_mesh(o.data)
        t.transform(o.matrix_world)
        me = bpy.data.meshes.new("TMP_bvh")
        t.to_mesh(me)
        t.free()
        bm.from_mesh(me)
        bpy.data.meshes.remove(me)
    b = BVHTree.FromBMesh(bm)
    bm.free()
    return b


# ---------------------------------------------------------------------------
def pipe_provisional(st):
    cu = bpy.data.objects["CRV_LightPipe_Tesoreria_Faro"]
    p0 = cu.data.splines[0].points[0].co
    cu["provisional_first_point"] = True
    cu["from_marker"] = "MARKER_Bld_TesoreriaMuralla"
    cu["first_point_note"] = (f"salida supuesta a +{TESORERIA_OUTLET_Z} m sobre el pad; en E5 la salida de tubos del "
                              "tejado de la Tesoreria debe quedar a 9.6 +- 0.5 m y este punto se mueve a la salida real")
    name = "MARKER_PipeOutlet_TesoreriaMuralla"
    e = bpy.data.objects.get(name)
    if e is None:
        e = bpy.data.objects.new(name, None)
        cu.users_collection[0].objects.link(e)
    e.empty_display_type = "SPHERE"
    e.empty_display_size = 0.4
    e.location = (p0.x, p0.y, p0.z)
    e["provisional"] = True
    e["curve"] = cu.name
    e["curve_point"] = 0
    e["target_outlet_z_over_pad_m"] = TESORERIA_OUTLET_Z
    e["tolerance_m"] = 0.5
    st["pipe"] = {"curve": cu.name, "first_point": [round(p0.x, 2), round(p0.y, 2), round(p0.z, 2)],
                  "marker": name, "provisional": True,
                  "tesoreria_marker": "MARKER_Bld_TesoreriaMuralla",
                  "pad_z": round(bpy.data.objects["MARKER_Bld_TesoreriaMuralla"].matrix_world.translation.z, 3)}


# ---------------------------------------------------------------------------
def canal_alignment(st):
    """Canales de TRN_LightCanals en el marco local del Faro frente a los arranques de los canales de la torre."""
    import stage15_faro as F
    fr = bpy.data.objects["FARO"]
    inv = fr.matrix_world.inverted()
    can = bpy.data.objects["TRN_LightCanals"]
    vs = [inv @ (can.matrix_world @ v.co) for v in can.data.vertices]
    near = [v for v in vs if v.y > 5.0 and v.y < 14.0 and abs(v.x) < 3.0]
    out = []
    starts = st["faro"]["channel_starts_local"]
    for xg in (-1.8, -0.6, 0.6, 1.8):
        pts = [v for v in near if abs(v.x - xg) < 0.15]
        cx = (min(v.x for v in pts) + max(v.x for v in pts)) / 2
        y_end = max(v.y for v in pts if v.y < 12.0) if pts else None
        y_min = min(v.y for v in pts)
        s = min(starts, key=lambda q: abs(q[0] - xg))
        out.append({"ground_canal_x": xg, "ground_centerline_x": round(cx, 3), "ground_y_range": [round(y_min, 2), round(y_end, 2)],
                    "tower_start_x": s[0], "tower_start_y": s[1], "tower_drop_x": s[2],
                    "lateral_offset_cm": round(abs(cx - s[0]) * 100, 1),
                    "start_on_canal": y_min - 0.05 <= s[1] <= y_end + 0.05,
                    "ok_5cm": abs(cx - s[0]) <= 0.05 and y_min - 0.05 <= s[1] <= y_end + 0.05})
    st["canal_alignment"] = out
    # el pozo de la puerta: el umbral tapa el final de los canales interiores
    st["canal_alignment_note"] = ("canales exteriores (+-1.8): la bajada de la torre cae sobre el canal; interiores (+-0.6): "
                                  "llegan al umbral de la puerta (+-1.45), la torre baja a x = +-1.55 junto a la portada "
                                  "y se une al canal con una L sobre el pavimento delante del umbral")
    _ = F


# ---------------------------------------------------------------------------
def rebuild_portal(st):
    col = bpy.data.collections["BLD_PORTAL"]
    for o in [o for o in col.objects if o.name.startswith(("PORTAL_Arch", "PORTAL_Veil", "PORTAL_Pillar_"))]:
        bpy.data.objects.remove(o)
    P.BOOL_LOG.clear()
    arch, rep = P.build_arch(col, random.Random(P.SEED))
    rep["lods"] = P.lods(arch, col)
    veil = P.build_veil(col)
    # colision de pilares: cajas 2.0 x 2.0 (antes cilindros r 1.3)
    cols = []
    for sx, tag in ((1, "E"), (-1, "W")):
        m = P.Mesh()
        P.box_grid(m, sx * P.PIER_X - P.PIER / 2, sx * P.PIER_X + P.PIER / 2, -P.DEPTH / 2, P.DEPTH / 2,
                   P.Z_STEP - P.Z_TOP, P.Z_SPRING, 1, 1, 1, P.STONE)
        o = m.to_object(f"PORTAL_Pillar_{tag}-colonly", col)
        o.data.materials.clear()
        o.location = (0, 0, P.Z_TOP)
        o.hide_render = True
        cols.append(o.name)
    # comprobacion: todo el arco (por encima del pedestal) dentro de r <= 6.0
    mw = arch.matrix_world
    rmax, worst = 0.0, None
    for v in arch.data.vertices:
        if v.co.z < 0.0:
            continue                                  # hilo emisivo que baja por el canto del pedestal (z < 0)
        r = math.hypot(v.co.x, v.co.y)
        if r > rmax:
            rmax, worst = r, tuple(round(c, 3) for c in v.co)
    corners = []
    for sx in (-1, 1):
        for sy in (-1, 1):
            x, y = sx * (P.PIER_X + P.PIER / 2), sy * P.DEPTH / 2
            corners.append([x, y, round(math.hypot(x, y), 3)])
    lintel = [P.PIER_X + P.PIER / 2 + P.LINTEL_OVER_X, P.DEPTH / 2 + P.LINTEL_OVER_Y]
    st["portal"] = {"clear_width_m": P.CLEAR, "pier_m": [P.PIER, P.DEPTH], "pier_center_x": P.PIER_X,
                    "pier_corners_xy_r": corners, "lintel_corner_r": round(math.hypot(*lintel), 3),
                    "max_vertex_radius_above_pedestal_m": round(rmax, 3), "worst_vertex": worst,
                    "ok_r_le_6": rmax <= 6.0 + 1e-3, "tris": rep["tris"], "lods": rep["lods"],
                    "carved_runes": rep.get("carved_runes"), "boolean": list(P.BOOL_LOG),
                    "veil_m": [round(veil.dimensions.x, 3), round(veil.dimensions.z, 3)], "pillar_colliders": cols}
    _ = mw
    import stage11_godot as G
    objs = [o for o in col.objects if o.name.startswith("PORTAL")]
    path = os.path.join(REPO, "export", "godot", "concordia_portal.glb")
    size = G.export_glb(objs, path)
    st["portal"]["export"] = {"mb": round(size / 2 ** 20, 2), **G.glb_info(path)}


# ---------------------------------------------------------------------------
def walkable_fn():
    import build_stage16 as B16
    g, cell, R, obst = B16.walk_cells()

    def f(x, y):
        i, j = int((x + R) / cell), int((y + R) / cell)
        if not (0 <= i < g.shape[0] and 0 <= j < g.shape[1] and g[i, j]):
            return False
        return obst.ray_cast(Vector((x, y, 200.0)), Vector((0, 0, -1)))[0] is None
    return f


def faro_visibility(st, target):
    import build_stage15 as B15
    streets, lanes = {}, {}
    for name, ang in (("Avenida Norte", 90), ("Avenida Sur", 270), ("Avenida Este", 0), ("Avenida Oeste", 180),
                      ("Diagonal NE (Faro)", 45), ("Diagonal NO (Santuario)", 135), ("Diagonal SO (Obelisco)", 225),
                      ("Diagonal SE (Salon)", 315)):
        a = math.radians(ang)
        n = (-math.sin(a), math.cos(a))
        for off in (-2.5, 0.0, 2.5):                     # eje y ambos lados de la calle de 6 m
            key = f"{name}|{off:+.1f}"
            streets[key] = [(r * math.cos(a) + off * n[0], r * math.sin(a) + off * n[1]) for r in range(62, 192, 4)]
            lanes.setdefault(name, []).append(key)
    for rr in (100, 150):
        streets[f"Ronda r{rr}"] = [(rr * math.cos(math.radians(a)), rr * math.sin(math.radians(a))) for a in range(0, 360, 6)]
    vis = {}
    B15.visibility(target, stats=vis, streets=streets, walkable=walkable_fn())
    per = vis["visibility"]["per_street"]
    out = {}
    for name, keys in lanes.items():
        lane = {k.split("|")[1]: {"samples": per[k]["samples"], "pct": per[k]["pct"], "blocked_by": per[k]["blocked_by"]}
                for k in keys}
        out[name] = {"axis_pct": lane["+0.0"]["pct"], "lanes": lane,
                     "best_lane_pct": max(v["pct"] for v in lane.values()),
                     "samples_axis": lane["+0.0"]["samples"]}
    for k, v in per.items():
        if "|" not in k:
            out[k] = {"axis_pct": v["pct"], "samples_axis": v["samples"], "blocked_by": v["blocked_by"]}
    st["faro_visibility"] = out
    st["faro_visibility_note"] = ("muestras cada 4 m (radiales, r 62-190) y cada 6 grados (rondas), solo sobre calle o "
                                  "plaza transitable (fuera de parcelas y pads); ojo a 1.7 m; objetivo: cima del cristal")


# ---------------------------------------------------------------------------
def palette_fix(st):
    """Paleta: nada saturado fuera del azul palido (saturacion <= 0.34). Mismo tono y valor."""
    import stage16_landmarks as L
    w = bpy.data.materials["MAT_Window_Warm"]
    b = next(n for n in w.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    b.inputs["Emission Color"].default_value = (0.4173, 0.2803, 0.1682, 1)
    w["note"] = "luz natural calida de ventana, emision 1.0, #AD9072 (sat 0.34); NO es color magico"
    m = bpy.data.materials["MAT_Bronze_Aged"]
    b = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    b.inputs["Base Color"].default_value = (L._lin(0.451), L._lin(0.391), L._lin(0.298), 1)
    st["palette_fix"] = {"MAT_Window_Warm": "emision #AD865D (sat 0.46) -> #AD9072 (sat 0.34)",
                         "MAT_Bronze_Aged": "base #735C38 (sat 0.51) -> #73644C (sat 0.34)"}
    import stage11_godot as G
    root = bpy.data.objects["SALON_HAZANAS"]
    path = os.path.join(REPO, "export", "godot", "concordia_salon_hazanas.glb")
    size = G.export_glb([root] + list(root.children_recursive), path)
    st["palette_fix"]["reexport"] = {"file": os.path.basename(path), "mb": round(size / 2 ** 20, 2)}


def main():
    st = {}
    bpy.ops.wm.open_mainfile(filepath=SRC)
    save()
    st["saved_before"] = os.path.relpath(OUT, REPO)
    pipe_provisional(st)
    import build_stage15 as B15
    st["faro"] = {}
    B15.build_faro(st["faro"], with_pipes=False)
    target = st["faro"].pop("target")
    B15.export_faro(st["faro"])
    canal_alignment(st)
    rebuild_portal(st)
    palette_fix(st)
    for o in bpy.data.objects:
        if o.name.endswith(("_LOD1", "_LOD2")):
            o.hide_set(True)
    faro_visibility(st, target)
    save()
    with open(REPORT, "w") as fh:
        json.dump(st, fh, indent=1, ensure_ascii=False, default=str)
    print("saved:", OUT)
    print(json.dumps({k: st["faro"].get(k) for k in ("tris", "ok", "lods", "boolean", "collision")}, default=str))
    print(json.dumps(st["canal_alignment"]))
    print(json.dumps({k: v for k, v in st["portal"].items() if k not in ("boolean", "export")}, default=str))
    print(json.dumps([b for b in st["portal"]["boolean"] if b["failed"]]))
    print(json.dumps({k: (v["axis_pct"], v.get("best_lane_pct"), v["samples_axis"],
                          v.get("blocked_by") or v["lanes"]["+0.0"]["blocked_by"]) for k, v in st["faro_visibility"].items()},
                     ensure_ascii=False))


if __name__ == "__main__":
    main()
