"""
CONCORDIA - Etapa 13: el Portal y sus elementos. concordia_v12.blend -> concordia_v13.blend (guardada antes de
empezar) + export/godot/concordia_portal.glb + docs/reports/stage13_portal.json.
Los marcadores de prueba de la etapa 03 (TRN_Runestones, TRN_DescentPedestals) se mueven a LEGACY_PLACEHOLDERS
(ocultos, fuera de los exports): los sustituyen las piezas nuevas.
"""

import json
import math
import os
import random
import sys

import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import concordia_const as C  # noqa: E402
import stage13_portal as P  # noqa: E402

REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
SRC = os.path.join(REPO, "blender", f"{C.BLEND_BASENAME}_v12.blend")
OUT = os.path.join(REPO, "blender", f"{C.BLEND_BASENAME}_v13.blend")
REPORT = os.path.join(REPO, "docs", "reports", "stage13_portal.json")
BUDGET = {"arch": 12000, "runestone": 400, "pedestal": 300}


def save():
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)


def main():
    st = {}
    bpy.ops.wm.open_mainfile(filepath=SRC)
    save()
    st["saved_before"] = os.path.relpath(OUT, REPO)
    st["materials"] = P.ensure_materials()
    col = bpy.data.collections["BLD_PORTAL"]
    for o in list(col.objects):
        bpy.data.objects.remove(o)
    leg = bpy.data.collections.get("LEGACY_PLACEHOLDERS") or bpy.data.collections.new("LEGACY_PLACEHOLDERS")
    if leg.name not in bpy.context.scene.collection.children:
        bpy.context.scene.collection.children.link(leg)
    for n in ("TRN_Runestones", "TRN_DescentPedestals"):
        o = bpy.data.objects.get(n)
        if o:
            for c in list(o.users_collection):
                c.objects.unlink(o)
            leg.objects.link(o)
            o.hide_render = True
            o.hide_set(True)
    leg.hide_render = True
    st["legacy_moved"] = ["TRN_Runestones", "TRN_DescentPedestals"]
    rng = random.Random(P.SEED)
    arch, rep = P.build_arch(col, rng)
    rep["lods"] = P.lods(arch, col)
    rep["ok"] = rep["tris"] <= BUDGET["arch"]
    st["arch"] = rep
    veil = P.build_veil(col)
    st["veil"] = {"tris": P.tris(veil), "size_m": [round(veil.dimensions.x, 2), round(veil.dimensions.z, 2)],
                  "material": "MAT_Portal_Veil", "uv": veil["uv"]}
    cols = []
    cols.append(P.cylinder_col("PORTAL_Pedestal-colonly", 6.35, 8.4, P.Z_TOP, 32, col))
    for sx, tag in ((1, "E"), (-1, "W")):
        cols.append(P.cylinder_col(f"PORTAL_Pillar_{tag}-colonly", 1.3, P.Z_STEP, P.Z_TOP + P.Z_SPRING, 16, col,
                                   loc=(sx * P.PIER_X, 0, 0)))
    stones = {}
    for i in range(1, 8):
        mk = bpy.data.objects[f"MARKER_Runestone_{i:02d}"]
        o = P.build_runestone(f"PORTAL_Runestone_{i:02d}", mk, i, col)
        stones[o.name] = {"tris": P.tris(o), "lods": P.lods(o, col), "ok": P.tris(o) <= BUDGET["runestone"],
                          "location": [round(c, 3) for c in o.matrix_world.translation]}
        c = P.cylinder_col(f"{o.name}-colonly", 0.32, 0.0, 0.8, 8, col)
        c.matrix_world = o.matrix_world.copy()
    st["runestones"] = stones
    peds = {}
    for i in range(1, 22):
        mk = bpy.data.objects[f"MARKER_Descent_Pedestal_{i:02d}"]
        o = P.build_pedestal(f"PORTAL_DescentPedestal_{i:02d}", mk, i, col)
        peds[o.name] = {"tris": P.tris(o), "lods": P.lods(o, col), "ok": P.tris(o) <= BUDGET["pedestal"],
                        "floor": o.get("floor"), "location": [round(c, 3) for c in o.matrix_world.translation]}
        c = P.cylinder_col(f"{o.name}-colonly", 0.62, 0.0, 0.5, 12, col)
        c.matrix_world = o.matrix_world.copy()
    st["descent_pedestals"] = peds
    ar = P.build_atrio_runes(col)
    st["atrio_runes"] = {"tris": P.tris(ar), "radius_m": 14.85}
    st["collision"] = [o.name for o in col.objects if o.name.endswith("-colonly")]
    st["over_budget"] = ([arch.name] if not rep["ok"] else []) + [k for k, v in {**stones, **peds}.items() if not v["ok"]]
    st["totals"] = {"tris_LOD0": sum(P.tris(o) for o in col.objects if o.type == "MESH" and not o.name.endswith(
        ("-colonly", "_LOD1", "_LOD2")))}
    # export
    import stage11_godot as G
    objs = [o for o in col.objects]
    path = os.path.join(REPO, "export", "godot", "concordia_portal.glb")
    size = G.export_glb(objs, path)
    st["export"] = {"file": os.path.relpath(path, REPO), "mb": round(size / 2 ** 20, 2), **G.glb_info(path)}
    save()
    with open(REPORT, "w") as fh:
        json.dump(st, fh, indent=1, ensure_ascii=False, default=str)
    print("saved:", OUT)
    print(json.dumps({"arch": rep, "veil": st["veil"], "over": st["over_budget"], "totals": st["totals"],
                      "export": st["export"],
                      "stone_tris": sorted({v["tris"] for v in stones.values()}),
                      "ped_tris": sorted({v["tris"] for v in peds.values()})}, default=str))


if __name__ == "__main__":
    main()
