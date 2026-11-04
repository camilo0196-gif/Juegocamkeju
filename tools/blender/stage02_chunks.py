"""
CONCORDIA - Etapa 02d: version para Godot del terreno (chunks de 50 m + LODs) y export .glb.

- La malla MAESTRA TRN_City (1 m) NO se toca ni se exporta.
- Rejilla de chunks de 50 x 50 m centrada en el origen (el Portal cae en el centro de un
  chunk y los ejes de las avenidas en el centro de una columna/fila de chunks).
- Se corta la copia por las lineas de chunk (bisect), se reparte cada cara por su centro.
- Presupuesto: 35.000 tris por chunk en la ciudad. Se mide LOD0 ANTES de optimizar y solo
  se optimiza (decimate planar) un chunk si se pasa.
- LOD1 = 50 %, LOD2 = 15 % (decimate collapse) con los vertices del borde del chunk
  bloqueados: los chunks vecinos encajan sin grietas aunque esten en LODs distintos.
- Export: export/godot/concordia_terrain.glb (chunks LOD0/1/2) y
          export/godot/concordia_terrain_structures.glb (pretiles, escaleras, contrafuertes,
          escalinatas). COLOR_0 = mask_pack.
"""

import os
import sys
from math import floor, radians

import bpy  # noqa: I001
import bmesh

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import concordia_const as C  # noqa: E402

LODS = {"LOD0": 1.0, "LOD1": 0.50, "LOD2": 0.15}
PLANAR_ANGLE = 1.0          # grados, solo si un chunk supera el presupuesto


def chunk_idx(v):
    return int(floor((v + C.CHUNK_SIZE / 2) / C.CHUNK_SIZE))


def chunk_name(i, j, lod):
    return f"TRN_CityChunk_x{i + 4}_y{j + 4}_{lod}"


def ensure_collection(name, parent):
    col = bpy.data.collections.get(name)
    if col is None:
        col = bpy.data.collections.new(name)
        parent.children.link(col)
    col.hide_viewport = False          # visibles mientras se generan y exportan
    col.hide_render = False
    for o in list(col.objects):
        me = o.data
        bpy.data.objects.remove(o)
        if me and me.users == 0:
            bpy.data.meshes.remove(me)
    return col


def bisected_copy(master):
    bm = bmesh.new()
    bm.from_mesh(master.data)
    lines = [C.CHUNK_SIZE * k + C.CHUNK_SIZE / 2 for k in range(-5, 5)]
    for axis in (0, 1):
        for c in lines:
            if abs(c) > C.TERRAIN_RADIUS:
                continue
            co = [0.0, 0.0, 0.0]
            no = [0.0, 0.0, 0.0]
            co[axis], no[axis] = c, 1.0
            bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], dist=1e-5,
                                   plane_co=co, plane_no=no)
    bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 3])
    me = bpy.data.meshes.new("TMP_bisected")
    bm.to_mesh(me)
    bm.free()
    return me


def tri_count(obj):
    return len(obj.data.polygons)


def make_lod(src, name, ratio, col):
    obj = bpy.data.objects.new(name, src.data.copy())
    obj.data.name = name
    obj.location = src.location
    col.objects.link(obj)
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bnd = [v.index for v in bm.verts if v.is_boundary]
    bm.free()
    g = obj.vertex_groups.new(name="lod_lock")
    g.add(bnd, 1.0, "REPLACE")
    m = obj.modifiers.new("lod", "DECIMATE")
    m.decimate_type = "COLLAPSE"
    m.ratio = ratio
    m.vertex_group = "lod_lock"
    m.invert_vertex_group = True
    m.vertex_group_factor = 1000.0
    dg = bpy.context.evaluated_depsgraph_get()
    new = bpy.data.meshes.new_from_object(obj.evaluated_get(dg))
    old = obj.data
    obj.modifiers.clear()
    obj.data = new
    new.name = name
    bpy.data.meshes.remove(old)
    obj.vertex_groups.remove(obj.vertex_groups["lod_lock"])
    return obj


def boundary_key_set(obj):
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    s = {(round(v.co.x, 4), round(v.co.y, 4), round(v.co.z, 4)) for v in bm.verts if v.is_boundary}
    bm.free()
    return s


def export_glb(objs, path):
    for o in bpy.context.view_layer.objects:
        o.select_set(False)
    for o in objs:
        o.select_set(True)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    bpy.ops.export_scene.gltf(filepath=path, export_format="GLB", use_selection=True, export_yup=True,
                              export_apply=True, export_vertex_color="NAME", export_vertex_color_name="mask_pack",
                              export_all_vertex_colors=False, export_active_vertex_color_when_no_material=False,
                              export_extras=True, export_image_format="NONE")
    return os.path.getsize(path)


def verify_glb(path):
    """Reimporta el .glb en una escena temporal y cuenta mallas, triangulos y COLOR_0."""
    tmp = bpy.data.scenes.new("TMP_verify")
    win_scene = bpy.context.window.scene if bpy.context.window else None
    if bpy.context.window:
        bpy.context.window.scene = tmp
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    new = [o for o in bpy.data.objects if o not in before]
    meshes = [o for o in new if o.type == "MESH"]
    empties = sum(1 for o in new if o.type == "EMPTY")
    tris = sum(sum(len(p.vertices) - 2 for p in o.data.polygons) for o in meshes)
    with_color = sum(1 for o in meshes if len(o.data.color_attributes) > 0)
    for o in new:
        me = o.data if o.type == "MESH" else None
        bpy.data.objects.remove(o)
        if me and me.users == 0:
            bpy.data.meshes.remove(me)
    if bpy.context.window and win_scene:
        bpy.context.window.scene = win_scene
    bpy.data.scenes.remove(tmp)
    return {"objects": len(meshes), "empties": empties, "tris": tris, "meshes_with_color0": with_color}


def build(scene, stats, export_dir, extra_exports=None):
    master = bpy.data.objects["TRN_City"]
    terrain = bpy.data.collections["TERRAIN"]
    cols = {lod: ensure_collection(f"TERRAIN_CHUNKS_{lod}", terrain) for lod in LODS}
    mat = master.data.materials[0] if master.data.materials else None

    me_b = bisected_copy(master)
    face_chunk = {}
    for p in me_b.polygons:
        c = p.center
        face_chunk.setdefault((chunk_idx(c.x), chunk_idx(c.y)), []).append(p.index)
    lod0 = {}
    for (i, j), faces in sorted(face_chunk.items()):
        keep = set(faces)
        bm = bmesh.new()
        bm.from_mesh(me_b)
        bm.faces.ensure_lookup_table()
        kill = [f for f in bm.faces if f.index not in keep]
        bmesh.ops.delete(bm, geom=kill, context="FACES")
        # los vertex groups de la maestra no viajan al chunk (Godot no los usa y sus indices
        # sin nombre se confundirian con el grupo de bloqueo de los LODs)
        dl = bm.verts.layers.deform.active
        if dl is not None:
            bm.verts.layers.deform.remove(dl)
        cx, cy = i * C.CHUNK_SIZE, j * C.CHUNK_SIZE
        for v in bm.verts:
            v.co.x -= cx
            v.co.y -= cy
        name = chunk_name(i, j, "LOD0")
        me = bpy.data.meshes.new(name)
        bm.to_mesh(me)
        bm.free()
        obj = bpy.data.objects.new(name, me)
        obj.location = (cx, cy, 0.0)
        obj["chunk"] = [i, j]
        cols["LOD0"].objects.link(obj)
        lod0[(i, j)] = obj
    bpy.data.meshes.remove(me_b)

    # --- medicion ANTES de optimizar
    before = {chunk_name(i, j, "LOD0"): tri_count(o) for (i, j), o in lod0.items()}
    vals = sorted(before.values())
    heaviest = sorted(before.items(), key=lambda kv: -kv[1])[:8]
    over = [n for n, t in before.items() if t > C.CHUNK_TRI_BUDGET_CITY]
    optimized = {}
    for n in over:                                    # solo los que se pasan
        o = bpy.data.objects[n]
        m = o.modifiers.new("planar", "DECIMATE")
        m.decimate_type = "DISSOLVE"
        m.angle_limit = radians(PLANAR_ANGLE)
        dg = bpy.context.evaluated_depsgraph_get()
        new = bpy.data.meshes.new_from_object(o.evaluated_get(dg))
        old = o.data
        o.modifiers.clear()
        o.data = new
        bpy.data.meshes.remove(old)
        bm = bmesh.new()
        bm.from_mesh(o.data)
        bmesh.ops.triangulate(bm, faces=bm.faces[:])
        bm.to_mesh(o.data)
        bm.free()
        optimized[n] = {"before": before[n], "after": tri_count(o)}

    # --- LODs
    lods = {}
    seam_ok = 0
    for (i, j), o in lod0.items():
        b0 = boundary_key_set(o)
        row = {"LOD0": tri_count(o)}
        for lod, ratio in LODS.items():
            if lod == "LOD0":
                continue
            lo = make_lod(o, chunk_name(i, j, lod), ratio, cols[lod])
            row[lod] = tri_count(lo)
            seam_ok += int(b0.issubset({(round(v.co.x, 4), round(v.co.y, 4), round(v.co.z, 4))
                                        for v in lo.data.vertices}))
        lods[chunk_name(i, j, "")[:-1]] = row
    for col in cols.values():
        for o in col.objects:
            if mat and not o.data.materials:
                o.data.materials.append(mat)
            o.data.color_attributes.active_color_name = "mask_pack"

    # --- export
    chunk_objs = [o for col in cols.values() for o in col.objects]
    struct_objs = [o for cname in ("MORADAS", "STREETS") for o in bpy.data.collections[cname].objects
                   if o.type == "MESH"]
    p1 = os.path.join(export_dir, "concordia_terrain.glb")
    p2 = os.path.join(export_dir, "concordia_terrain_structures.glb")
    s1 = export_glb(chunk_objs, p1)
    s2 = export_glb(struct_objs, p2)
    v1, v2 = verify_glb(p1), verify_glb(p2)
    extra = {}
    for fname, cnames in (extra_exports or {}).items():
        objs = [o for cn in cnames for o in bpy.data.collections[cn].all_objects if o.type in ("MESH", "EMPTY")]
        pth = os.path.join(export_dir, fname)
        extra[fname] = {"bytes": export_glb(objs, pth), "objects_in": len(objs), "verify": verify_glb(pth)}
    for col in cols.values():                         # fuera del render de verificacion
        col.hide_render = True
        col.hide_viewport = True

    t_lod = {lod: [r[lod] for r in lods.values()] for lod in LODS}
    stats["chunks"] = {
        "grid": "50 x 50 m centrada en el origen (indices x0..x8 / y0..y8, x4_y4 = Portal)",
        "count": len(lod0),
        "budget_city_per_chunk": C.CHUNK_TRI_BUDGET_CITY,
        "lod0_before": {"avg": round(sum(vals) / len(vals)), "max": vals[-1], "min": vals[0],
                        "total": sum(vals), "heaviest": heaviest, "over_budget": over},
        "optimized": optimized or "ninguno (ningun chunk supera 35.000)",
        "lod_tris": {lod: {"avg": round(sum(v) / len(v)), "max": max(v), "total": sum(v)} for lod, v in t_lod.items()},
        "lod_ratio_real": {lod: round(sum(t_lod[lod]) / sum(t_lod["LOD0"]), 3) for lod in LODS},
        "seams_locked_chunks": f"{seam_ok} / {2 * len(lod0)} (LOD1+LOD2 conservan todos los vertices del borde)",
        "per_chunk": lods,
        "export": {"terrain_glb": os.path.relpath(p1, os.path.join(HERE, "..", "..")), "terrain_bytes": s1,
                   "structures_glb": os.path.relpath(p2, os.path.join(HERE, "..", "..")), "structures_bytes": s2,
                   "verify_terrain": v1, "verify_structures": v2, "extra": extra},
    }
    return stats["chunks"]
