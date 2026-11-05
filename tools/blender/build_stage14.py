"""
CONCORDIA - Etapa 14: Obelisco de los Pisos. concordia_v13.blend -> concordia_v14.blend (guardada antes de empezar)
+ export/godot/concordia_obelisk.glb + docs/reports/stage14_obelisk.json
"""

import json
import os
import sys

import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import concordia_const as C  # noqa: E402
import stage14_obelisk as O  # noqa: E402

REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
SRC = os.path.join(REPO, "blender", f"{C.BLEND_BASENAME}_v13.blend")
OUT = os.path.join(REPO, "blender", f"{C.BLEND_BASENAME}_v14.blend")
REPORT = os.path.join(REPO, "docs", "reports", "stage14_obelisk.json")
BUDGET_TOTAL, BUDGET_MARK = 6000, 20


def save():
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)


def tris(o):
    return sum(len(p.vertices) - 2 for p in o.data.polygons)


def main():
    st = {}
    bpy.ops.wm.open_mainfile(filepath=SRC)
    save()
    st["saved_before"] = os.path.relpath(OUT, REPO)
    st["materials"] = O.ensure_materials()
    import concordia_buildings as B
    col = bpy.data.collections["BLD_PORTAL"]
    for o in [o for o in col.objects if o.name.startswith("OBELISK")]:
        bpy.data.objects.remove(o)
    mk = bpy.data.objects["MARKER_Obelisco"]
    mw = mk.matrix_world.copy()
    root = bpy.data.objects.new("OBELISK", None)
    col.objects.link(root)
    root.matrix_world = mw
    root["landmark"] = "Obelisco de los Pisos"
    root["height_m"] = O.H_TOTAL

    def attach(o):
        o.parent = root
        o.matrix_parent_inverse = root.matrix_world.inverted()
        return o
    body = O.build_body(col, lod=0).to_object("OBELISK_Body", col)
    body.matrix_world = mw
    attach(body)
    B.box_uv(body)
    lod2 = O.build_body(col, lod=2).to_object("OBELISK_Body_LOD2", col)
    lod2.matrix_world = mw
    attach(lod2)
    B.box_uv(lod2)
    lod2.hide_render = True
    import stage13_portal as P
    lod1 = P.lods(body, col, (("LOD1", 0.5),))
    l1 = bpy.data.objects["OBELISK_Body_LOD1"]
    attach(l1)
    lanterns = [attach(o) for o in O.build_lanterns(col, mw)]
    marks = [attach(O.build_mark(n, col, mw)) for n in range(1, 101)]
    ref = O.Mesh()
    ref.face([(-0.05, 0, 0.3), (0.05, 0, 0.3), (0.05, 0, 0.4), (-0.05, 0, 0.4)], "MAT_Obelisk_Mark_Lit", (0, 1, 0))
    ro = ref.to_object("OBELISK_Mark_LitMaterialRef", col)
    ro.matrix_world = mw
    attach(ro)
    ro["note"] = "dentro del pedestal: solo para que el .glb incluya MAT_Obelisk_Mark_Lit"
    colo = attach(O.box_collider("OBELISK-colonly", col, mw))
    # comprobaciones
    names = [f"OBELISK_Mark_{i:03d}" for i in range(1, 101)]
    missing = [n for n in names if n not in bpy.data.objects]
    floors_ok = all(bpy.data.objects[n]["floor"] == i for i, n in enumerate(names, 1))
    slots = {(o["face"], o["row"], o["column"]) for o in marks}
    mark_tris = {o.name: tris(o) for o in marks}
    t_body, t_lan = tris(body), sum(tris(o) for o in lanterns)
    st.update({
        "body_tris": t_body, "lanterns_tris": t_lan, "total_without_marks": t_body + t_lan,
        "budget_total": BUDGET_TOTAL, "ok_total": t_body + t_lan <= BUDGET_TOTAL,
        "lods": {"LOD1": lod1["LOD1"], "LOD2": tris(lod2)},
        "marks": {"count": len(marks), "names_001_100": not missing, "missing": missing, "floor_props_match": floors_ok,
                  "unique_slots": len(slots), "tris_min_max": [min(mark_tris.values()), max(mark_tris.values())],
                  "over_20": [k for k, v in mark_tris.items() if v > BUDGET_MARK],
                  "order": "fila 0: 1-5 frente, 6-10 izquierda, 11-15 trasera, 16-20 derecha; fila 1: 21-40; ...; "
                           "fila 4: 81-100 (de abajo arriba)",
                  "rows_z_local": list(O.ROWS_Z)},
        "dims": {"pedestal": "5 x 5 x 1.5, 4 escalones", "shaft": "3.0 -> 1.8, z 1.5-22.5", "pyramidion_m": 2.5,
                 "total_m": O.H_TOTAL},
        "collision": colo.name, "location": [round(c, 3) for c in mw.translation]})
    import stage11_godot as G
    objs = [root] + [o for o in col.objects if o.name.startswith("OBELISK") and o is not root]
    path = os.path.join(REPO, "export", "godot", "concordia_obelisk.glb")
    size = G.export_glb(objs, path)
    st["export"] = {"file": os.path.relpath(path, REPO), "mb": round(size / 2 ** 20, 2), **G.glb_info(path)}
    save()
    with open(REPORT, "w") as fh:
        json.dump(st, fh, indent=1, ensure_ascii=False, default=str)
    print("saved:", OUT)
    print(json.dumps({k: st[k] for k in ("body_tris", "lanterns_tris", "total_without_marks", "ok_total", "lods",
                                         "marks", "export")}, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
