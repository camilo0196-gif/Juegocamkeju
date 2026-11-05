"""
CONCORDIA - etapa 11: preparacion para Godot 4 (a partir de concordia_v10.blend).

 1. Limpieza: vertices duplicados (0.001 m), caras degeneradas, geometria suelta, caras interiores, caras de apoyo
    ocultas (base de piezas apoyadas), normales recalculadas; rotacion/escala aplicadas en mallas no instanciadas.
 2. Chunks 50 x 50 m: TRN_City_Chunk_X_Y_LODk y TRN_Exterior_Chunk_X_Y_LODk (indice global X, Y = 0..16, el
    Portal en 8_8; mismo indice en ciudad y exterior). Presupuesto 35.000 / 8.000 tris (incluye acantilados y
    rocas del chunk); decimate planar solo si se pasa. Bordes de chunk bloqueados en todos los LODs.
 3. LOD1 50 % / LOD2 15 % (decimate collapse) con la silueta bloqueada: vertices de borde + aristas vivas
    (> 40 grados: coronas y pies de muros, bordes de terraza, cresta del talud).
 4. Colision: TRN_City_Chunk_X_Y-colonly (copia del LOD1: sin surcos ni bombeo), piezas con convex hull por
    parte o malla reducida (-colonly). Muralla: la del kit (caja conica por modulo, cilindro por torre).
 5. Navegacion: TRN_NavMesh_<Distrito>-navmesh (heightfield 0.75 m sobre calles, plazas, plazoletas, escaleras y
    puentes; fuera cauce, taludes, terrazas, parcelas y jardines).
 6. Occluders: <pieza>-occonly en el kit de muralla.
 7. Marcadores: todos los Empties MARKER_* -> concordia_markers.glb (con propiedades como extras).
"""

import csv
import json
import os
import sys
from collections import Counter, defaultdict
from math import floor, radians

import bmesh
import bpy
import numpy as np
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import concordia_const as C  # noqa: E402

REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
CS = C.CHUNK_SIZE
IDX_OFF = 8                                    # indice global: X = floor((x + 25) / 50) + 8
LODS = {"LOD1": 0.50, "LOD2": 0.15}
SIL_ANGLE = 40.0                               # aristas vivas bloqueadas en los LODs
MERGE_DIST = 0.001
PLANAR_ANGLE = 1.0
NAV_STEP = 0.75
NAV_MAX_DZ = 0.60                              # desnivel max. entre esquinas (escaleras de terraza ~0.5 m por metro; muros de 1 m no pasan)
NAV_MAX_SLOPE = 40.0
NAV_CLEAR = 2.1                                # galibo bajo puentes/arcos para la segunda capa
HULL_RATIO_MAX = 1.35
DISTRICTS = ("plaza", "mercado", "oficios", "clases", "razas", "moradas")
SECTOR_GROUP = {"plaza": "plaza", "landmarks": "plaza", "sector_mercado": "mercado", "sector_oficios": "oficios",
                "sector_clases": "clases", "sector_razas": "razas", "sector_moradas": "moradas"}
STRUCT_COLS = ("STREETS", "PLAZA", "MORADAS", "CAUCE")
NO_COLLISION_MATS = {"MAT_Water", "MAT_Void", "MAT_Shard_Blue"}
NAV_STRUCT_PREFIX = ("TRN_StairPass", "TRN_Escalinata", "TRN_TerraceStairs", "TRN_LateralStairs", "TRN_Bridge",
                     "TRN_Atrio", "CAU_Muelle", "TRN_Pad_")      # basamentos: explanadas (huella del edificio pendiente)
NAV_CONNECT_M = 3.0                            # suelo comun junto a escaleras y puentes = transitable (enlace)
NAV_MIN_ISLAND_M2 = 10.0


def gidx(v):
    return int(floor((v + CS / 2) / CS)) + IDX_OFF


def ensure_collection(name, parent=None):
    col = bpy.data.collections.get(name)
    if col is None:
        col = bpy.data.collections.new(name)
        (parent or bpy.context.scene.collection).children.link(col)
    for o in list(col.objects):
        me = o.data
        bpy.data.objects.remove(o)
        if me is not None and getattr(me, "users", 1) == 0:
            bpy.data.meshes.remove(me)
    return col


def remove_collection_tree(name):
    col = bpy.data.collections.get(name)
    if col is None:
        return 0
    n = 0
    for c in [col] + list(col.children_recursive):
        for o in list(c.objects):
            me = o.data if o.type == "MESH" else None
            bpy.data.objects.remove(o)
            if me is not None and me.users == 0:
                bpy.data.meshes.remove(me)
            n += 1
    for c in list(col.children_recursive) + [col]:
        bpy.data.collections.remove(c)
    return n


def tris(me):
    return sum(len(p.vertices) - 2 for p in me.polygons)


# ---------------------------------------------------------------------------
# 1. limpieza
# ---------------------------------------------------------------------------
def clean_mesh(me, terrain=False, seat_bottom=False):
    bm = bmesh.new()
    bm.from_mesh(me)
    nv0, nf0 = len(bm.verts), len(bm.faces)
    bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=MERGE_DIST)
    merged = nv0 - len(bm.verts)
    bmesh.ops.dissolve_degenerate(bm, edges=bm.edges[:], dist=1e-5)
    loose_e = [e for e in bm.edges if not e.link_faces]
    bmesh.ops.delete(bm, geom=loose_e, context="EDGES")
    loose_v = [v for v in bm.verts if not v.link_faces]
    bmesh.ops.delete(bm, geom=loose_v, context="VERTS")
    interior = [f for f in bm.faces if all(len(e.link_faces) > 2 for e in f.edges)]
    bmesh.ops.delete(bm, geom=interior, context="FACES")
    hidden = []
    if seat_bottom and bm.verts:
        zmin = min(v.co.z for v in bm.verts)
        hidden = [f for f in bm.faces if f.normal.z < -0.98 and all(v.co.z < zmin + 0.02 for v in f.verts)]
        bmesh.ops.delete(bm, geom=hidden, context="FACES_ONLY")
        bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context="VERTS")
    before = {f.index: f.normal.copy() for f in bm.faces}
    bm.faces.ensure_lookup_table()
    flipped = 0
    if terrain:
        down = [f for f in bm.faces if f.normal.z < -0.3]
        if down:
            bmesh.ops.reverse_faces(bm, faces=down)
        flipped = len(down)
    else:
        for f in bm.faces:
            f.tag = False
        bm.normal_update()
        ref = [f.normal.copy() for f in bm.faces]
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
        bm.normal_update()
        flipped = sum(1 for f, n in zip(bm.faces, ref) if f.normal.dot(n) < -0.5)
    _ = before
    bm.to_mesh(me)
    nf1 = len(bm.faces)
    bm.free()
    me.update()
    return {"merged_verts": merged, "faces_before": nf0, "faces_after": nf1, "interior_faces": len(interior),
            "hidden_bottom_faces": len(hidden), "flipped_normals": flipped}


def cleanup(stats):
    skip_cols = ("TERRAIN_CHUNKS", "EXTERIOR_CHUNKS", "MATERIAL_LIBRARY", "STREETS_AXES", "WALL_KIT_LODS")
    done = set()
    rep = {"meshes": 0, "merged_verts": 0, "interior_faces": 0, "hidden_bottom_faces": 0, "flipped_normals": 0,
           "transforms_applied": 0, "instanced_kept": 0}
    per = {}
    for o in bpy.data.objects:
        if o.type != "MESH" or not o.users_collection:
            continue
        cn = o.users_collection[0].name
        if cn.startswith(skip_cols) or o.name.endswith("-colonly"):
            continue
        me = o.data
        # rotacion / escala aplicadas en mallas propias; las instancias del kit conservan su matriz
        if me.users == 1:
            loc, rot, scl = o.matrix_world.decompose()
            if rot.angle > 1e-6 or (scl - Vector((1, 1, 1))).length > 1e-6:
                me.transform(Matrix.LocRotScale(None, rot, scl))
                o.matrix_world = Matrix.Translation(loc)
                rep["transforms_applied"] += 1
        else:
            rep["instanced_kept"] += 1
        if me.name in done:
            continue
        done.add(me.name)
        terrain = o.name in ("TRN_City", "TRN_Exterior")
        seat = cn in ("WALL_KIT", "EXTERIOR") and not terrain or o.name.startswith(
            ("TRN_PlazaParcel", "TRN_Pad_", "TRN_Buttresses", "TRN_Parapets", "TRN_Runestones", "TRN_DescentPed",
             "TRN_PortalPed", "EXT_Rock"))
        r = clean_mesh(me, terrain=terrain, seat_bottom=seat)
        rep["meshes"] += 1
        for k in ("merged_verts", "interior_faces", "hidden_bottom_faces", "flipped_normals"):
            rep[k] += r[k]
        if any(r[k] for k in ("merged_verts", "interior_faces", "hidden_bottom_faces", "flipped_normals")):
            per[o.name] = r
    rep["changed"] = per
    stats["cleanup"] = rep


# ---------------------------------------------------------------------------
# 2-3. chunks y LODs
# ---------------------------------------------------------------------------
def bisect_grid(bm, rmax):
    lines = [CS * k + CS / 2 for k in range(-9, 9)]
    for axis in (0, 1):
        for c in lines:
            if abs(c) > rmax:
                continue
            co, no = [0.0, 0.0, 0.0], [0.0, 0.0, 0.0]
            co[axis], no[axis] = c, 1.0
            bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], dist=1e-5,
                                   plane_co=co, plane_no=no)
    bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 3])


def split_by_chunk(src_obj, name_fmt, col, keep_groups=False, rmax=420.0):
    """Corta una copia por la rejilla y crea un objeto por chunk (origen en el centro del chunk)."""
    bm = bmesh.new()
    bm.from_mesh(src_obj.data)
    bm.transform(src_obj.matrix_world)
    bisect_grid(bm, rmax)
    me_b = bpy.data.meshes.new("TMP_bisect")
    bm.to_mesh(me_b)
    bm.free()
    cen = np.zeros(len(me_b.polygons) * 3, dtype=np.float32)
    me_b.polygons.foreach_get("center", cen)
    cen = cen.reshape(-1, 3)
    gi = np.floor((cen[:, 0] + CS / 2) / CS).astype(int) + IDX_OFF
    gj = np.floor((cen[:, 1] + CS / 2) / CS).astype(int) + IDX_OFF
    out = {}
    for key in sorted(set(zip(gi.tolist(), gj.tolist()))):
        keep = np.nonzero((gi == key[0]) & (gj == key[1]))[0]
        bm = bmesh.new()
        bm.from_mesh(me_b)
        bm.faces.ensure_lookup_table()
        ks = set(keep.tolist())
        bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.index not in ks], context="FACES")
        if not keep_groups:
            dl = bm.verts.layers.deform.active
            if dl is not None:
                bm.verts.layers.deform.remove(dl)
        cx, cy = (key[0] - IDX_OFF) * CS, (key[1] - IDX_OFF) * CS
        for v in bm.verts:
            v.co.x -= cx
            v.co.y -= cy
        name = name_fmt.format(x=key[0], y=key[1])
        me = bpy.data.meshes.new(name)
        bm.to_mesh(me)
        bm.free()
        for m in src_obj.data.materials:
            me.materials.append(m)
        o = bpy.data.objects.new(name, me)
        o.location = (cx, cy, 0.0)
        o["chunk"] = [key[0], key[1]]
        col.objects.link(o)
        out[key] = o
    bpy.data.meshes.remove(me_b)
    return out


def lock_set(me, sil=True):
    bm = bmesh.new()
    bm.from_mesh(me)
    lock = {v.index for v in bm.verts if v.is_boundary}
    nb = len(lock)
    if sil:
        lim = radians(SIL_ANGLE)
        for e in bm.edges:
            if len(e.link_faces) == 2 and e.calc_face_angle(0.0) > lim:
                lock.update(v.index for v in e.verts)
    bm.free()
    return sorted(lock), nb


def make_lod(src, name, ratio, col, lock):
    me = src.data.copy()
    me.name = name
    obj = bpy.data.objects.new(name, me)
    obj.matrix_world = src.matrix_world
    col.objects.link(obj)
    g = obj.vertex_groups.new(name="lod_lock")
    g.add(lock, 1.0, "REPLACE")
    m = obj.modifiers.new("lod", "DECIMATE")
    m.decimate_type = "COLLAPSE"
    m.ratio = ratio
    m.vertex_group = "lod_lock"
    m.invert_vertex_group = True
    m.vertex_group_factor = 1000.0
    dg = bpy.context.evaluated_depsgraph_get()
    new = bpy.data.meshes.new_from_object(obj.evaluated_get(dg))
    obj.modifiers.clear()
    old = obj.data
    obj.data = new
    new.name = name
    bpy.data.meshes.remove(old)
    obj.vertex_groups.clear()
    for k, v in src.items():
        obj[k] = v
    return obj


def boundary_keys(o):
    mw = o.matrix_world
    bm = bmesh.new()
    bm.from_mesh(o.data)
    s = {tuple(round(c, 3) for c in (mw @ v.co)) for v in bm.verts if v.is_boundary}
    bm.free()
    return s


def planar_if_over(o, budget):
    t0 = tris(o.data)
    if t0 <= budget:
        return None
    m = o.modifiers.new("planar", "DECIMATE")
    m.decimate_type = "DISSOLVE"
    m.angle_limit = radians(PLANAR_ANGLE)
    m.delimit = {"MATERIAL", "SEAM"}
    dg = bpy.context.evaluated_depsgraph_get()
    new = bpy.data.meshes.new_from_object(o.evaluated_get(dg))
    o.modifiers.clear()
    old = o.data
    o.data = new
    bpy.data.meshes.remove(old)
    bm = bmesh.new()
    bm.from_mesh(o.data)
    bmesh.ops.triangulate(bm, faces=bm.faces[:])
    bm.to_mesh(o.data)
    bm.free()
    return {"before": t0, "after": tris(o.data)}


def silhouette_error(o0, o2, step=1.0):
    """|dz| entre LOD0 y LOD2 muestreando desde arriba (la silueta isometrica depende de la altura)."""
    b0 = BVHTree.FromObject(o0, bpy.context.evaluated_depsgraph_get())
    b2 = BVHTree.FromObject(o2, bpy.context.evaluated_depsgraph_get())
    xs = np.arange(-CS / 2 + step / 2, CS / 2, step)
    errs = []
    down = Vector((0, 0, -1))
    for x in xs:
        for y in xs:
            p = Vector((x, y, 500.0))
            h0 = b0.ray_cast(p, down)
            h2 = b2.ray_cast(p, down)
            if h0[0] is not None and h2[0] is not None:
                errs.append(abs(h0[0].z - h2[0].z))
    if not errs:
        return None
    e = np.array(errs)
    return {"p50": round(float(np.median(e)), 3), "p99": round(float(np.percentile(e, 99)), 3),
            "max": round(float(e.max()), 3), "samples": len(e)}


def face_districts(master):
    """Distrito por cara de la maestra (vertex groups de sector)."""
    me = master.data
    names = {g.index: SECTOR_GROUP[g.name] for g in master.vertex_groups if g.name in SECTOR_GROUP}
    vd = [None] * len(me.vertices)
    for v in me.vertices:
        for g in v.groups:
            if g.group in names and g.weight > 0.5:
                vd[v.index] = names[g.group]
                break
    out = []
    cen = []
    for p in me.polygons:
        c = Counter(vd[i] for i in p.vertices if vd[i])
        out.append(c.most_common(1)[0][0] if c else None)
        cen.append(tuple(p.center))
    return out, np.array(cen)


def chunk_district_map(master):
    fd, cen = face_districts(master)
    gi = np.floor((cen[:, 0] + CS / 2) / CS).astype(int) + IDX_OFF
    gj = np.floor((cen[:, 1] + CS / 2) / CS).astype(int) + IDX_OFF
    cnt = defaultdict(Counter)
    for a, b, d in zip(gi.tolist(), gj.tolist(), fd):
        cnt[(a, b)][d] += 1
    res = {}
    for k, c in cnt.items():
        cc = Counter({d: n for d, n in c.items() if d})
        res[k] = cc.most_common(1)[0][0] if cc else None
    known = {k: d for k, d in res.items() if d}
    for k, d in res.items():
        if d is None:
            nk = min(known, key=lambda q: (q[0] - k[0]) ** 2 + (q[1] - k[1]) ** 2)
            res[k] = known[nk]
    return res


def city_chunks(stats):
    master = bpy.data.objects["TRN_City"]
    for old in ("TERRAIN_CHUNKS_LOD0", "TERRAIN_CHUNKS_LOD1", "TERRAIN_CHUNKS_LOD2"):
        remove_collection_tree(old)
    terrain = bpy.data.collections["TERRAIN"]
    cols = {k: ensure_collection(f"GODOT_CITY_{k}", terrain) for k in ("LOD0", "LOD1", "LOD2", "COL")}
    dmap = chunk_district_map(master)
    lod0 = split_by_chunk(master, "TRN_City_Chunk_{x}_{y}_LOD0", cols["LOD0"])
    rows, opt, seams, sil = {}, {}, [0, 0], {}
    for key, o in lod0.items():
        o["district"] = dmap.get(key, "plaza")
        o.data.color_attributes.active_color_name = "mask_pack"
        r = planar_if_over(o, C.CHUNK_TRI_BUDGET_CITY)
        if r:
            opt[o.name] = r
        lock, nb = lock_set(o.data)
        b0 = boundary_keys(o)
        row = {"LOD0": tris(o.data), "locked_verts": len(lock), "boundary_verts": nb}
        base = o.name[:-5]
        lods = {}
        for lod, ratio in LODS.items():
            lo = make_lod(o, f"{base}_{lod}", ratio, cols[lod], lock)
            lo.data.color_attributes.active_color_name = "mask_pack"
            row[lod] = tris(lo.data)
            seams[1] += 1
            seams[0] += int(b0.issubset(boundary_keys(lo)))
            lods[lod] = lo
        # colision: copia del LOD1 (sin surcos ni bombeo), sin materiales ni atributos
        cme = lods["LOD1"].data.copy()
        cme.name = f"{base}-colonly"
        cme.materials.clear()
        for an in [a.name for a in cme.color_attributes]:
            cme.color_attributes.remove(cme.color_attributes[an])
        while cme.uv_layers:
            cme.uv_layers.remove(cme.uv_layers[0])
        co = bpy.data.objects.new(f"{base}-colonly", cme)
        co.matrix_world = o.matrix_world
        co["district"] = o["district"]
        cols["COL"].objects.link(co)
        row["colonly"] = tris(cme)
        rows[base] = row
        if key in ((8, 8), (10, 10), (7, 5), (12, 8)):
            sil[base] = silhouette_error(o, lods["LOD2"])
    l0 = [r["LOD0"] for r in rows.values()]
    stats["city_chunks"] = {
        "count": len(rows), "budget": C.CHUNK_TRI_BUDGET_CITY, "planar_optimized": opt or "ninguno",
        "lod0": {"max": max(l0), "avg": round(sum(l0) / len(l0)), "total": sum(l0)},
        "lod1_total": sum(r["LOD1"] for r in rows.values()), "lod2_total": sum(r["LOD2"] for r in rows.values()),
        "lod2_ratio_real": round(sum(r["LOD2"] for r in rows.values()) / sum(l0), 3),
        "colonly_total": sum(r["colonly"] for r in rows.values()),
        "seams_ok": f"{seams[0]} / {seams[1]} LODs conservan todos los vertices de borde del LOD0",
        "silhouette_error_LOD2_m": sil, "per_chunk": rows,
        "districts": dict(Counter(o["district"] for o in lod0.values()))}
    return lod0, dmap, cols


def exterior_chunks(stats, dmap):
    ext = bpy.data.objects["TRN_Exterior"]
    for old in ("EXTERIOR_CHUNKS_LOD0", "EXTERIOR_CHUNKS_LOD1", "EXTERIOR_CHUNKS_LOD2"):
        remove_collection_tree(old)
    parent = bpy.data.collections["EXTERIOR"]
    cols = {k: ensure_collection(f"GODOT_EXT_{k}", parent) for k in ("LOD0", "LOD1", "LOD2", "CLIFF")}
    lod0 = split_by_chunk(ext, "TRN_Exterior_Chunk_{x}_{y}_LOD0", cols["LOD0"])
    cliffs = split_by_chunk(bpy.data.objects["EXT_Cliffs"], "EXT_Cliffs_Chunk_{x}_{y}_LOD0", cols["CLIFF"])
    rocks = defaultdict(list)
    for o in parent.objects:
        if o.name.startswith("EXT_Rock_"):
            c = o.matrix_world @ (sum((Vector(b) for b in o.bound_box), Vector()) / 8)
            rocks[(gidx(c.x), gidx(c.y))].append(o)
    rows = {}
    for key in sorted(set(lod0) | set(cliffs)):
        row = {}
        tot = 0
        for src, tag in ((lod0.get(key), "terrain"), (cliffs.get(key), "cliffs")):
            if src is None:
                continue
            src.data.color_attributes.active_color_name = "mask_pack" if "mask_pack" in src.data.color_attributes \
                else src.data.color_attributes.active_color_name
            lock, _nb = lock_set(src.data)
            base = src.name[:-5]
            row[tag] = {"LOD0": tris(src.data)}
            tot += tris(src.data)
            for lod, ratio in LODS.items():
                lo = make_lod(src, f"{base}_{lod}", ratio, cols[lod], lock)
                row[tag][lod] = tris(lo.data)
        rt = sum(tris(o.data) for o in rocks.get(key, []))
        row["rocks"] = [o.name for o in rocks.get(key, [])]
        row["total_LOD0"] = tot + rt
        rows[f"{key[0]}_{key[1]}"] = row
    over = {k: r["total_LOD0"] for k, r in rows.items() if r["total_LOD0"] > C.CHUNK_TRI_BUDGET_EXTERIOR}
    stats["exterior_chunks"] = {"count": len(rows), "budget": C.CHUNK_TRI_BUDGET_EXTERIOR,
                                "max_total_LOD0": max(r["total_LOD0"] for r in rows.values()),
                                "over_budget": over or "ninguno", "per_chunk": rows}
    return cols, rocks


# ---------------------------------------------------------------------------
# 4. colision de piezas
# ---------------------------------------------------------------------------
def part_collision(o, col):
    """-colonly por pieza: convex hull por parte suelta si el casco no infla el volumen (> 35 %), si no malla
    reducida (planar 10 grados)."""
    bm = bmesh.new()
    bm.from_mesh(o.data)
    mats = o.data.materials
    drop = [f for f in bm.faces if mats and f.material_index < len(mats) and mats[f.material_index]
            and mats[f.material_index].name in NO_COLLISION_MATS]
    bmesh.ops.delete(bm, geom=drop, context="FACES")
    parts = []
    seen = set()
    for f in bm.faces:
        if f.index in seen:
            continue
        stack, comp = [f], []
        seen.add(f.index)
        while stack:
            g = stack.pop()
            comp.append(g)
            for e in g.edges:
                for h in e.link_faces:
                    if h.index not in seen:
                        seen.add(h.index)
                        stack.append(h)
        parts.append(comp)
    out = bmesh.new()
    nh = nt = 0
    for comp in parts:
        verts = list({v for f in comp for v in f.verts})
        sub = bmesh.new()
        vm = {v: sub.verts.new(v.co) for v in verts}
        for f in comp:
            try:
                sub.faces.new([vm[v] for v in f.verts])
            except ValueError:
                pass
        closed = all(e.is_manifold for e in sub.edges)
        vol = abs(sub.calc_volume()) if closed else 0.0
        hull = bmesh.new()
        hv = [hull.verts.new(v.co) for v in sub.verts]
        res = bmesh.ops.convex_hull(hull, input=hv)
        bmesh.ops.delete(hull, geom=list({g for g in res["geom_interior"] + res["geom_unused"]
                                          if isinstance(g, bmesh.types.BMVert)}), context="VERTS")
        hvol = abs(hull.calc_volume()) if hull.faces else 0.0
        use_hull = closed and vol > 1e-4 and hvol / vol <= HULL_RATIO_MAX
        src = hull if use_hull else sub
        if not use_hull:
            bmesh.ops.dissolve_limit(sub, angle_limit=radians(10.0), verts=sub.verts[:], edges=sub.edges[:])
        m2 = {v: out.verts.new(v.co) for v in src.verts}
        for f in src.faces:
            try:
                out.faces.new([m2[v] for v in f.verts])
            except ValueError:
                pass
        nh += int(use_hull)
        nt += int(not use_hull)
        sub.free()
        hull.free()
    bm.free()
    if not out.faces:
        out.free()
        return None
    bmesh.ops.triangulate(out, faces=out.faces[:])
    base = o.name[:-4] if o.name.endswith("-col") else o.name
    me = bpy.data.meshes.new(base + "-colonly")
    out.to_mesh(me)
    out.free()
    co = bpy.data.objects.new(base + "-colonly", me)
    co.matrix_world = o.matrix_world
    col.objects.link(co)
    return co, {"parts": len(parts), "hull": nh, "reduced": nt, "tris": tris(me)}


def structures(stats, dmap):
    """Piezas de STREETS / PLAZA / MORADAS / CAUCE: '-col' (trimesh de la malla visible) -> malla limpia +
    '-colonly' simple. Distrito por el centro de la pieza."""
    colc = ensure_collection("GODOT_STRUCT_COL")
    rows = {}
    objs = []
    for cn in STRUCT_COLS:
        for o in list(bpy.data.collections[cn].objects):
            if o.type != "MESH" or o.name.endswith("-colonly"):
                continue
            if o.name.endswith("-col"):
                o.name = o.name[:-4]
                o.data.name = o.name
            objs.append(o)
    for o in objs:
        c = o.matrix_world @ (sum((Vector(b) for b in o.bound_box), Vector()) / 8)
        o["district"] = dmap.get((gidx(c.x), gidx(c.y)), "plaza")
        mats = {m.name for m in o.data.materials if m}
        if mats and mats <= NO_COLLISION_MATS or o.name.endswith("_Repair"):
            rows[o.name] = {"district": o["district"], "tris": tris(o.data), "collision": None}
            continue
        r = part_collision(o, colc)
        if r:
            r[0]["district"] = o["district"]
        rows[o.name] = {"district": o["district"], "tris": tris(o.data), "collision": r[1] if r else None}
    stats["structures"] = {"count": len(rows), "per_object": rows,
                           "collision_tris": sum(v["collision"]["tris"] for v in rows.values() if v["collision"])}
    return objs, colc


# ---------------------------------------------------------------------------
# 5. navmesh
# ---------------------------------------------------------------------------
def nav_mesh(stats, dmap):
    """Heightfield de 0.75 m: rayos cenitales contra toda la geometria solida; un nodo es transitable si la primera
    cara que toca es de calle / plaza / plazoleta / escalera / puente con pendiente <= 40 grados. Segunda capa bajo
    puentes y arcos (galibo >= 2.1 m). Celdas con 4 esquinas transitables y desnivel <= 0.45 m."""
    bm = bmesh.new()
    walk = []
    master = bpy.data.objects["TRN_City"]
    me = master.data

    def corner(name):
        a = me.color_attributes.get(name)
        v = np.zeros(len(me.loops) * 4, dtype=np.float32)
        a.data.foreach_get("color", v)
        return v.reshape(-1, 4)[:, 0]
    road, slab, ct = corner("road_mask"), corner("slab_ring_id"), corner("cobble_type")
    ret = corner("retaining_mask")
    ls = np.zeros(len(me.polygons), dtype=np.int64)
    me.polygons.foreach_get("loop_start", ls)
    ctf = np.rint(ct[ls] * 8).astype(int)
    road_f = (road[ls] > 0.5) & (ctf != 7)
    slab_f = slab[ls] > 0.01
    ret_f = ret[ls] > 0.5
    city_walk = (road_f | slab_f) & ~ret_f
    ter = corner("terraza_id")[ls] > 0.01
    gar = corner("garden_mask")[ls] > 0.01
    gi_t = master.vertex_groups["talud"].index
    talv = np.zeros(len(me.vertices), dtype=bool)
    for v in me.vertices:
        if any(g.group == gi_t for g in v.groups):
            talv[v.index] = True
    talf = np.array([all(talv[i] for i in p.vertices) for p in me.polygons])
    city_ground = ~city_walk & ~ret_f & (ctf == 0) & ~ter & ~gar & ~talf
    tmp = bmesh.new()
    tmp.from_mesh(me)
    tmp.transform(master.matrix_world)
    ground = []
    for f in tmp.faces:
        walk.append(bool(city_walk[f.index]))
        ground.append(bool(city_ground[f.index]))
    off = len(tmp.faces)
    tmp_me = bpy.data.meshes.new("TMP_nav_city")
    tmp.to_mesh(tmp_me)
    tmp.free()
    bm.from_mesh(tmp_me)
    bpy.data.meshes.remove(tmp_me)
    src_objs = []
    boxes = []
    for cn in STRUCT_COLS + ("WALL_LAYOUT",):
        for o in bpy.data.collections[cn].objects:
            if o.type != "MESH" or o.name.endswith("-colonly"):
                continue
            mats = {m.name for m in o.data.materials if m}
            if mats and mats <= {"MAT_Water", "MAT_Shard_Blue"}:
                continue
            src_objs.append(o)
    for o in src_objs:
        t = bmesh.new()
        t.from_mesh(o.data)
        t.transform(o.matrix_world)
        w = o.name.startswith(NAV_STRUCT_PREFIX)
        if w:
            for f in t.faces:                      # huella real (centros y vertices) para el enlace
                boxes.append(tuple(f.calc_center_median())[:2])
                boxes.extend(tuple(v.co)[:2] for v in f.verts)
        for f in t.faces:
            walk.append(w)
            ground.append(False)
        tm = bpy.data.meshes.new("TMP_nav_obj")
        t.to_mesh(tm)
        t.free()
        bm.from_mesh(tm)
        bpy.data.meshes.remove(tm)
    _ = off
    bm.faces.ensure_lookup_table()
    normals = [f.normal.z for f in bm.faces]
    bvh = BVHTree.FromBMesh(bm)
    walk = np.array(walk)
    ground = np.array(ground)
    nz_min = np.cos(radians(NAV_MAX_SLOPE))
    R = 200.0
    xs = np.arange(-R, R + 1e-6, NAV_STEP)
    down = Vector((0, 0, -1))
    layers = [dict(), dict()]                       # (i, j) -> z
    nx = len(xs)
    foot = np.zeros((nx, nx), dtype=bool)
    if boxes:
        pts = np.array(boxes)
        ii = np.clip(np.rint((pts[:, 0] + R) / NAV_STEP).astype(int), 0, nx - 1)
        jj = np.clip(np.rint((pts[:, 1] + R) / NAV_STEP).astype(int), 0, nx - 1)
        foot[ii, jj] = True
        k = int(np.ceil(NAV_CONNECT_M / NAV_STEP))
        dil = foot.copy()
        for di in range(-k, k + 1):
            for dj in range(-k, k + 1):
                if di * di + dj * dj <= k * k:
                    dil |= np.roll(np.roll(foot, di, 0), dj, 1)
        foot = dil

    def in_box(x, y):
        return bool(foot[int(round((x + R) / NAV_STEP)), int(round((y + R) / NAV_STEP))])
    for i, x in enumerate(xs):
        for j, y in enumerate(xs):
            if x * x + y * y > (C.WALL_RADIUS - 2.0) ** 2:
                continue
            # todas las superficies de la vertical (de arriba abajo)
            p = Vector((x, y, 60.0))
            hits = []
            for _ in range(10):
                h = bvh.ray_cast(p, down, 200.0)
                if h[0] is None:
                    break
                hits.append((h[0].z, h[2], normals[h[2]]))
                p = h[0] + Vector((0, 0, -0.002))
            ceiling = None                             # techo encima (None = cielo)
            L = 0
            for z, fi, nz in hits:
                if nz > 0:                             # cara hacia arriba: suelo candidato
                    clear = ceiling is None or ceiling - z >= NAV_CLEAR
                    ok = clear and nz >= nz_min and (walk[fi] or (ground[fi] and in_box(x, y)))
                    if ok and L < 2:
                        layers[L][(i, j)] = z
                        L += 1
                ceiling = z                            # todo lo que quede debajo esta bajo esta superficie
                if L >= 2:
                    break
    # nodos -> vertices
    out = bmesh.new()
    vid = {}

    def node(i, j, z):
        k = (i, j, round(z, 2))
        if k not in vid:
            vid[k] = out.verts.new((xs[i], xs[j], z + 0.05))
        return vid[k]
    nfaces = 0
    face_keys = set()
    for L in range(2):
        for (i, j), z0 in layers[L].items():
            quad = [(i, j), (i + 1, j), (i + 1, j + 1), (i, j + 1)]
            zs = []
            for q in quad:
                cand = [lay[q] for lay in layers if q in lay]
                best = min(cand, key=lambda z: abs(z - z0)) if cand else None
                if best is None or abs(best - z0) > NAV_MAX_DZ:
                    zs = None
                    break
                zs.append(best)
            if zs is None or max(zs) - min(zs) > NAV_MAX_DZ:
                continue
            key = (i, j, round(sum(zs) / 4, 1))
            if key in face_keys:
                continue
            face_keys.add(key)
            try:
                out.faces.new([node(q[0], q[1], z) for q, z in zip(quad, zs)])
                nfaces += 1
            except ValueError:
                pass
    bm.free()
    bmesh.ops.remove_doubles(out, verts=out.verts[:], dist=0.01)
    cells = len(out.faces)
    bmesh.ops.dissolve_limit(out, angle_limit=radians(1.0), verts=out.verts[:], edges=out.edges[:])
    bmesh.ops.triangulate(out, faces=out.faces[:])
    # componentes conexas
    comp_sizes = []
    seen = set()
    out.faces.ensure_lookup_table()
    comp_area, id_of = {}, {}
    for f in out.faces:
        if f.index in seen:
            continue
        stack, area, members = [f], 0.0, []
        seen.add(f.index)
        while stack:
            g = stack.pop()
            members.append(g.index)
            area += g.calc_area()
            for e in g.edges:
                for h in e.link_faces:
                    if h.index not in seen:
                        seen.add(h.index)
                        stack.append(h)
        for k in members:
            comp_area[k] = area
            id_of[k] = len(comp_sizes)
        comp_sizes.append(area)
    comp_sizes.sort(reverse=True)
    small = [f for f in out.faces if comp_area[f.index] < NAV_MIN_ISLAND_M2]
    dropped = len({id_of[f.index] for f in small})
    bmesh.ops.delete(out, geom=small, context="FACES")
    full = bpy.data.meshes.new("TMP_navmesh")
    out.to_mesh(full)
    out.free()
    # reparto por distrito (cara -> chunk -> distrito); las regiones vecinas comparten vertices de borde
    navcol = ensure_collection("GODOT_NAVMESH")
    cen = np.zeros(len(full.polygons) * 3, dtype=np.float32)
    full.polygons.foreach_get("center", cen)
    cen = cen.reshape(-1, 3)
    dist = [dmap.get((gidx(c[0]), gidx(c[1])), "plaza") for c in cen]
    per = {}
    for d in DISTRICTS:
        idx = {k for k, dd in enumerate(dist) if dd == d}
        if not idx:
            continue
        b2 = bmesh.new()
        b2.from_mesh(full)
        b2.faces.ensure_lookup_table()
        bmesh.ops.delete(b2, geom=[f for f in b2.faces if f.index not in idx], context="FACES")
        name = f"TRN_NavMesh_{d.capitalize()}-navmesh"
        m2 = bpy.data.meshes.new(name)
        b2.to_mesh(m2)
        b2.free()
        o = bpy.data.objects.new(name, m2)
        o["district"] = d
        navcol.objects.link(o)
        per[name] = {"tris": tris(m2), "area_m2": round(sum(p.area for p in m2.polygons), 1)}
    bpy.data.meshes.remove(full)
    tot_area = sum(comp_sizes)
    stats["navmesh"] = {"grid_m": NAV_STEP, "cells": cells, "layer2_nodes": len(layers[1]),
                        "area_m2": round(tot_area, 1), "components": len(comp_sizes),
                        "largest_component_pct": round(100 * comp_sizes[0] / tot_area, 1) if comp_sizes else 0,
                        "islands_dropped_lt_10m2": dropped,
                        "components_kept": len(comp_sizes) - dropped,
                        "islands_kept_10_to_200m2": sum(1 for a in comp_sizes if NAV_MIN_ISLAND_M2 <= a < 200),
                        "arch_bridges": "fuera de la navmesh: sus tableros (+10.4) no llegan a ninguna superficie "
                                        "transitable; la calle de debajo si esta (segunda capa)",
                        "per_district": per}
    return navcol


# ---------------------------------------------------------------------------
# 6. occluders del kit
# ---------------------------------------------------------------------------
def wall_occluders(stats):
    kit = bpy.data.collections["WALL_KIT"]
    col = ensure_collection("GODOT_OCCLUDERS", kit)
    rows = {}
    for o in list(kit.objects):
        if not o.name.endswith("-colonly"):
            continue
        piece = o.name[:-8]
        bm = bmesh.new()
        bm.from_mesh(o.data)
        res = bmesh.ops.convex_hull(bm, input=bm.verts[:])
        bmesh.ops.delete(bm, geom=list({g for g in res["geom_interior"] + res["geom_unused"]
                                        if isinstance(g, bmesh.types.BMVert)}), context="VERTS")
        c = sum((v.co for v in bm.verts), Vector()) / max(1, len(bm.verts))
        for v in bm.verts:                       # 8 % hacia dentro: nunca tapa lo que asoma por los bordes
            d = v.co - c
            v.co = c + Vector((d.x * 0.92, d.y * 0.92, 0.0)) + Vector((0, 0, v.co.z - c.z)) * 0.92
        name = f"{piece}-occonly"
        me = bpy.data.meshes.new(name)
        bm.to_mesh(me)
        bm.free()
        oc = bpy.data.objects.new(name, me)
        oc.matrix_world = o.matrix_world
        col.objects.link(oc)
        rows[name] = tris(me)
    stats["occluders"] = {"wall_kit": rows,
                          "manzanas": "no generados: aun no hay edificios; un occluder de manzana taparia el "
                                      "suelo visible desde la camara isometrica (pendiente de los edificios)"}
    return col


# ---------------------------------------------------------------------------
# 7. marcadores
# ---------------------------------------------------------------------------
def markers(stats, csv_path):
    empties = [o for o in bpy.data.objects if o.type == "EMPTY" and o.name.startswith("MARKER_")]
    rows = []
    fam = Counter()
    for o in sorted(empties, key=lambda e: e.name):
        p = o.matrix_world.translation
        rz = o.matrix_world.to_euler().z
        f = o.name.split("_")[1] if "_" in o.name else o.name
        fam[f] += 1
        props = {k: (v if isinstance(v, (int, float, str)) else str(list(v)) if hasattr(v, "__len__") else str(v))
                 for k, v in o.items()}
        rows.append({"name": o.name, "family": f, "x": round(p.x, 3), "y": round(p.y, 3), "z": round(p.z, 3),
                     "rot_z_deg": round(np.degrees(rz), 2),
                     "godot_x": round(p.x, 3), "godot_y": round(p.z, 3), "godot_z": round(-p.y, 3),
                     "props": json.dumps(props, ensure_ascii=False)})
    with open(csv_path, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    stats["markers"] = {"count": len(rows), "families": dict(sorted(fam.items())),
                        "csv": os.path.relpath(csv_path, REPO)}
    return empties, rows


# ---------------------------------------------------------------------------
# export
# ---------------------------------------------------------------------------
def export_glb(objs, path):
    for o in bpy.context.view_layer.objects:
        o.select_set(False)
    for o in objs:
        o.hide_set(False)
        o.select_set(True)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    bpy.ops.export_scene.gltf(filepath=path, export_format="GLB", use_selection=True, export_yup=True,
                              export_apply=True, export_normals=True, export_texcoords=True,
                              export_vertex_color="NAME", export_vertex_color_name="mask_pack",
                              export_all_vertex_colors=False, export_active_vertex_color_when_no_material=False,
                              export_extras=True, export_materials="EXPORT", export_image_format="AUTO",
                              export_keep_originals=True)
    return os.path.getsize(path)


def glb_info(path):
    import struct
    with open(path, "rb") as fh:
        data = fh.read()
    ln = struct.unpack("<I", data[12:16])[0]
    g = json.loads(data[20:20 + ln])
    t = 0
    for m in g.get("meshes", []):
        for pr in m["primitives"]:
            if "indices" in pr:
                t += g["accessors"][pr["indices"]]["count"] // 3
            else:
                t += g["accessors"][pr["attributes"]["POSITION"]]["count"] // 3
    imgs = [i.get("uri", "(embebida)") for i in g.get("images", [])]
    return {"nodes": len(g.get("nodes", [])), "meshes": len(g.get("meshes", [])), "tris": t,
            "materials": len(g.get("materials", [])), "images": len(imgs),
            "images_external": sum(1 for u in imgs if u != "(embebida)"),
            "colliders": sum(1 for n in g.get("nodes", []) if n.get("name", "").endswith("-colonly")),
            "navmesh": sum(1 for n in g.get("nodes", []) if n.get("name", "").endswith("-navmesh")),
            "occluders": sum(1 for n in g.get("nodes", []) if n.get("name", "").endswith("-occonly")),
            "empties": sum(1 for n in g.get("nodes", []) if "mesh" not in n)}
