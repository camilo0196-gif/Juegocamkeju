"""
CONCORDIA - Etapa 12 (paso 1): kit modular de edificios + assembler + casa de prueba 12 x 9 m, 2 plantas.
concordia_master_v11.blend -> concordia_v12.blend (se guarda ANTES de empezar y otra vez al final).

Uso: python tools/blender/build_stage12.py
"""

import json
import math
import os
import random
import sys

import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bld_kit as K  # noqa: E402
import concordia_buildings as B  # noqa: E402
import concordia_const as C  # noqa: E402

REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
SRC = os.path.join(REPO, "blender", f"{C.BLEND_BASENAME}_master_v11.blend")
OUT = os.path.join(REPO, "blender", f"{C.BLEND_BASENAME}_v12.blend")
REPORT = os.path.join(REPO, "docs", "reports", "stage12_kit.json")
COLLECTIONS = ("BLD_KIT", "BLD_PORTAL", "BLD_MERCADO", "BLD_OFICIOS", "BLD_CLASES", "BLD_RAZAS", "BLD_MORADAS",
               "BLD_PROPS")
FACE_CAM = math.radians(-135.0)          # +Y del modulo hacia la camara isometrica (SE)
TEST_ROT = math.radians(-112.0)          # casa de prueba: fachada hacia la camara y un lateral visible
SHEET_WALLS = (3000.0, 1000.0)
SHEET_OTHER = (3000.0, 900.0)
SHEET_PROPS = (3000.0, 800.0)
LIFT = {"BALCONY_Wood": 1.2, "BALCONY_Stone": 1.2, "FLOOR_Edge": 1.0, "AWNING_Patch_A": 2.4, "AWNING_Patch_B": 2.4,
        "AWNING_Patch_C": 2.4, "SIGN_Hanging": 1.6, "LANTERN_Shard": 1.4}     # piezas que cuelgan: solo en la hoja
TEST_HOUSE = (3100.0, 1100.0)
BUDGET = {"wall": 250, "roof_per_3m": 400, "small": 1500}


def save(path):
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.wm.save_as_mainfile(filepath=path, compress=True)


def ensure_col(name, parent=None):
    col = bpy.data.collections.get(name)
    if col is None:
        col = bpy.data.collections.new(name)
        (parent or bpy.context.scene.collection).children.link(col)
    return col


def make_piece(name, fn, col, loc, budget=None, per_3m=None):
    mb = K.MB()
    fn(mb)
    mb.finish()
    o = B.to_object(mb, name, col)
    mb.bm.free()
    o.location = loc
    o.rotation_euler = (0, 0, FACE_CAM)
    B.box_uv(o)
    t = sum(len(p.vertices) - 2 for p in o.data.polygons)
    row = {"tris": t}
    if per_3m:
        row["tris_per_3m"] = round(t / per_3m, 1)
        row["ok"] = row["tris_per_3m"] <= BUDGET["roof_per_3m"]
    elif budget:
        row["budget"] = budget
        row["ok"] = t <= budget
    o["kit_piece"] = True
    o["tris"] = t
    return o, row


def kit_pieces():
    """(nombre, generador, grupo, presupuesto, modulos de 3 m)"""
    P = []
    for kind in K.WALL_KINDS:
        for var in K.VARIANTS:
            P.append((f"WALL_{kind}_3m_{var}",
                      (lambda k, v: (lambda mb: K.wall(mb, k, variant=v, rng=random.Random(B.stable(k, v)),
                                                       ground=k in ("Door", "Arch"))))(kind, var),
                      "walls", BUDGET["wall"], None))
    P += [
        ("CORNER_Post", lambda mb: K.corner_post(mb, 6.4, "timber"), "other", BUDGET["small"], None),
        ("CORNER_Quoin", lambda mb: K.corner_post(mb, 6.4, "stone", random.Random(3)), "other", BUDGET["small"], None),
        ("TIMBER_Overlay", lambda mb: K.timber_overlay(mb, 3.0, 3.2, 0.0, None, random.Random(1)), "other",
         BUDGET["small"], None),
        ("BUTTRESS_Stone", lambda mb: K.buttress(mb, 5.8), "other", BUDGET["small"], None),
        ("FLOOR_Edge", lambda mb: K.floor_edge(mb, 3.0, 0.0), "other", BUDGET["small"], None),
        ("ARCH_Span_3m", lambda mb: K.arch_span(mb, 3.0, 4.6), "other", BUDGET["small"], None),
        ("ARCH_Span_6m", lambda mb: K.arch_span(mb, 6.0, 6.6), "other", BUDGET["small"], None),
        ("STAIRS_Ext", lambda mb: K.stairs_ext(mb), "other", BUDGET["small"], None),
        ("BALCONY_Wood", lambda mb: K.balcony(mb, 3.0, 1.5, "wood"), "other", BUDGET["small"], None),
        ("BALCONY_Stone", lambda mb: K.balcony(mb, 3.0, 1.5, "stone"), "other", BUDGET["small"], None),
        ("ROOF_Gable_Tile", lambda mb: K.roof_gable(mb, 3.0, 6.0, rng=random.Random(4)), "other", None, 1),
        ("ROOF_Hip", lambda mb: K.roof_hip(mb, 6.0, 6.0, rng=random.Random(5)), "other", None, 2),
        ("ROOF_Conical", lambda mb: K.roof_conical(mb, 2.5, rng=random.Random(6)), "other", None, 2),
        ("ROOF_Flat_Parapet", lambda mb: K.roof_flat_parapet(mb, 6.0, 6.0), "other", None, 2),
        ("ROOF_Lean_To", lambda mb: K.roof_lean_to(mb, 3.0, 3.0, rng=random.Random(7)), "other", None, 1),
        ("CHIMNEY_A", lambda mb: K.chimney(mb, 1.8, True, random.Random(8)), "other", BUDGET["small"], None),
        ("CHIMNEY_B", lambda mb: K.chimney(mb, 1.8, False, random.Random(9)), "other", BUDGET["small"], None),
        ("DORMER_Window", lambda mb: K.dormer(mb, rng=random.Random(10)), "other", BUDGET["small"], None),
    ]
    for kind in ("AWNING_Patch_A", "AWNING_Patch_B", "AWNING_Patch_C", "SIGN_Hanging", "LANTERN_Shard",
                 "CRATE_Small", "CRATE_Fruit", "BARREL", "TOOL_Rack"):
        P.append((kind, (lambda k: (lambda mb: B.PROP_BUILDERS[k](mb, random.Random(B.stable(k)))))(kind),
                  "props", BUDGET["small"], None))
    return P


def ground(name, center, size, mat, col):
    import bmesh
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=size / 2)
    bm.to_mesh(me)
    bm.free()
    me.materials.append(bpy.data.materials[mat])
    o = bpy.data.objects.new(name, me)
    col.objects.link(o)
    o.location = center
    B.box_uv(o)
    return o


def main():
    stats = {}
    bpy.ops.wm.open_mainfile(filepath=SRC)
    save(OUT)                                         # version nueva ANTES de empezar
    stats["saved_before"] = os.path.relpath(OUT, REPO)
    cols = {n: ensure_col(n) for n in COLLECTIONS}
    stats["collections"] = list(COLLECTIONS)
    stats["materials_added"] = B.ensure_materials()
    kit = cols["BLD_KIT"]
    sheet_col = ensure_col("BLD_KIT_SHEET", kit)
    test_col = ensure_col("BLD_KIT_TEST", kit)
    pieces = {}
    walls_i = other_i = props_i = 0
    for name, fn, grp, budget, per3 in kit_pieces():
        if grp == "walls":
            col_i, row_i = walls_i % 6, walls_i // 6
            loc = (SHEET_WALLS[0] + col_i * 6.0, SHEET_WALLS[1] - row_i * 6.0, 0.0)
            walls_i += 1
        elif grp == "props":
            col_i, row_i = props_i % 5, props_i // 5
            loc = (SHEET_PROPS[0] + col_i * 3.0, SHEET_PROPS[1] - row_i * 3.0, LIFT.get(name, 0.0))
            props_i += 1
        else:
            col_i, row_i = other_i % 7, other_i // 7
            loc = (SHEET_OTHER[0] + col_i * 9.0, SHEET_OTHER[1] - row_i * 9.0, LIFT.get(name, 0.0))
            other_i += 1
        o, row = make_piece(name, fn, kit, loc, budget, per3)
        row["sheet"] = grp
        row["location"] = list(loc)
        pieces[name] = row
    stats["kit"] = pieces
    stats["kit_count"] = len(pieces)
    stats["kit_over_budget"] = [n for n, r in pieces.items() if not r.get("ok", True)]
    ground("BLD_SHEET_Ground_Walls", (SHEET_WALLS[0] + 15, SHEET_WALLS[1] - 6, -0.01), 50, "MAT_Plaza_Slab", sheet_col)
    ground("BLD_SHEET_Ground_Other", (SHEET_OTHER[0] + 27, SHEET_OTHER[1] - 14, -0.01), 80, "MAT_Plaza_Slab", sheet_col)
    ground("BLD_SHEET_Ground_Props", (SHEET_PROPS[0] + 6, SHEET_PROPS[1] - 3, -0.01), 24, "MAT_Plaza_Slab", sheet_col)
    # casa de prueba 12 x 9, 2 plantas, entramado, dos aguas; la puerta mira a la camara isometrica
    root, objs, rep = B.build_building("TEST_Casa_12x9", footprint=(12.0, 9.0), pisos=2, tipo_techo="gable",
                                       estilo="timber", seed=7, location=(TEST_HOUSE[0], TEST_HOUSE[1], 0.0),
                                       rot_z=TEST_ROT, collection=test_col, props_collection=test_col, use="shop")
    stats["test_house"] = rep
    g = ground("BLD_TEST_Ground", (TEST_HOUSE[0], TEST_HOUSE[1], -0.005), 40, "MAT_Ground_Cracked", test_col)
    street = ground("BLD_TEST_Street", (0, 0, 0), 1, "MAT_Cobble_Concordia", test_col)
    fwd = (math.cos(TEST_ROT + math.pi / 2), math.sin(TEST_ROT + math.pi / 2))
    street.location = (TEST_HOUSE[0] + fwd[0] * 8.5, TEST_HOUSE[1] + fwd[1] * 8.5, 0.002)
    street.rotation_euler = (0, 0, TEST_ROT)
    street.data.transform(__import__('mathutils').Matrix.Diagonal((30.0, 7.0, 1.0, 1.0)))
    B.box_uv(street)
    _ = g
    # comprobacion del lado de camara para la casa girada y para un marcador real de ejemplo
    stats["iso_rule"] = {"view_dir_xy": [round(c, 3) for c in B.iso_view_dir()[:2]],
                         "lado_mas_cercano_a_la_camara": "caras que miran al SE (+X y -Y del mundo)",
                         "regla": "puerta (+Y) mirando en la direccion de la vista (dot > 0.35) -> 2 plantas; si no, 3"}
    samples = {}
    for n in ("MARKER_Bld_Banco", "MARKER_Bld_Posada", "MARKER_Bld_MER_Casa_01", "MARKER_Morada_NE_001",
              "MARKER_Morada_SE_001"):
        m = bpy.data.objects.get(n)
        if m:
            mx, away = B.iso_max_floors(m.matrix_world.to_euler().z)
            samples[n] = {"rot_z_deg": round(math.degrees(m.matrix_world.to_euler().z), 1), "camera_side": away,
                          "max_floors": mx}
    stats["iso_rule"]["ejemplos"] = samples
    save(OUT)
    stats["saved"] = os.path.relpath(OUT, REPO)
    with open(REPORT, "w") as fh:
        json.dump(stats, fh, indent=1, ensure_ascii=False, default=str)
    print("saved:", OUT)
    print(json.dumps({"kit_over_budget": stats["kit_over_budget"], "test_house": rep}, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
