"""
CONCORDIA - Etapa 24 (E11): preparacion de todos los edificios para Godot 4 y verificacion final.
concordia_v23.blend -> concordia_v24.blend (version final) + export/godot/bld_*.glb + docs/reports/stage24_godot.json

1. Limpieza de mallas (vertices duplicados, caras degeneradas, caras duplicadas o internas, normales de las partes
   cerradas), escalas aplicadas, origen en el centro de la base (raiz = marcador).
2. Estructura por edificio: <N>_Body, <N>_Roof, <N>_Props, <N>-colonly; interior=true -> MARKER_<N>_Door y
   <N>_InteriorVolume. Se completa lo que falte y se informa.
3. LOD1 (0.5) / LOD2 (0.15; en las Moradas caja con tejado): ratios medidos, se rehace el LOD2 si pasa de 0.2.
4. Triangulos por edificio, distrito y ciudad (LOD0 y LOD2).
5. Materiales: solo MAT_* de Concordia, nodos exportables; emisivos -> emissiveFactor en el glb.
6. bld_portal, bld_mercado, bld_oficios, bld_clases, bld_razas, bld_moradas_NE/NO/SE/SO, bld_kit, bld_props (.glb, +Y).
7. Navegacion: ningun edificio sobre la malla de navegacion (se recorta), puertas, plazas y escaleras sobre ella.
Verificacion: puertas visibles desde CAM_Iso, huellas +-0.2 m, edificios no identicos, color magico solo #8FD0FF.
"""

import colorsys
import hashlib
import json
import math
import os
import sys
from collections import Counter, defaultdict

import bpy  # noqa: I001
import bmesh
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import concordia_const as C  # noqa: E402
import concordia_buildings as B  # noqa: E402
import lod_utils as LU  # noqa: E402
import stage11_godot as G  # noqa: E402
import stage13_portal as P13  # noqa: E402

REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
SRC = os.path.join(REPO, "blender", f"{C.BLEND_BASENAME}_v23.blend")
OUT = os.path.join(REPO, "blender", f"{C.BLEND_BASENAME}_v24.blend")
REPORT = os.path.join(REPO, "docs", "reports", "stage24_godot.json")
EXP = os.path.join(REPO, "export", "godot")
DISTRICT_COLS = {"BLD_PORTAL": "portal", "BLD_MERCADO": "mercado", "BLD_OFICIOS": "oficios", "BLD_CLASES": "clases",
                 "BLD_RAZAS": "razas", "BLD_MORADAS_NE": "moradas_NE", "BLD_MORADAS_NO": "moradas_NO",
                 "BLD_MORADAS_SE": "moradas_SE", "BLD_MORADAS_SO": "moradas_SO"}
FILES = ("portal", "mercado", "oficios", "clases", "razas", "moradas_NE", "moradas_NO", "moradas_SE", "moradas_SO")
SUPERSEDED = ("concordia_clases.glb", "concordia_mercado.glb", "concordia_oficios.glb", "concordia_razas.glb",
              "concordia_portal.glb", "concordia_faro.glb", "concordia_santuario.glb", "concordia_salon_hazanas.glb",
              "concordia_obelisk.glb", "concordia_conexiones.glb", "moradas_NE.glb", "moradas_NO.glb", "moradas_SE.glb",
              "moradas_SO.glb")
MAGIC = (0x8F / 255, 0xD0 / 255, 0xFF / 255)
NATURAL_WARM = {"MAT_Window_Warm": "luz calida de ventana (natural, aprobada E3)",
                "MAT_Embers": "brasas (natural; excepcion de saturacion pendiente de confirmar)"}
ALLOWED_NODES = {"OUTPUT_MATERIAL", "BSDF_PRINCIPLED", "TEX_IMAGE", "UVMAP", "MAPPING", "SEPARATE_COLOR", "NORMAL_MAP",
                 "MIX", "GROUP"}
CAM_BACK = None


def tris(o):
    return sum(len(p.vertices) - 2 for p in o.data.polygons) if o is not None and o.type == "MESH" else 0


def save():
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)


def srgb(c):
    return c * 12.92 if c <= 0.0031308 else 1.055 * c ** (1 / 2.4) - 0.055


def hexc(rgb):
    return "#%02X%02X%02X" % tuple(int(round(min(1, max(0, v)) * 255)) for v in rgb)


# --------------------------------------------------------------------------- registro
def district_of_point(p):
    """Distrito por posicion (para las conexiones): Moradas por sector diagonal fuera de r 95; plaza dentro."""
    r = math.hypot(p.x, p.y)
    a = math.degrees(math.atan2(p.y, p.x)) % 360
    if r < 94.0:
        return "portal"
    for key, phi in (("moradas_NE", 45), ("moradas_NO", 135), ("moradas_SO", 225), ("moradas_SE", 315)):
        if abs((a - phi + 180) % 360 - 180) < 22.5 and r >= 94.0:
            return key if r > 106.0 else "portal"
    for key, phi in (("oficios", 0), ("mercado", 90), ("clases", 180), ("razas", 270)):
        if abs((a - phi + 180) % 360 - 180) <= 45:
            return key
    return "portal"


def registry(st):
    """Edificios: raiz EMPTY con hijo <N>_Body (o el Portal agrupado). Devuelve {nombre: info}."""
    out = {}
    # el Portal: un solo edificio con raiz PORTAL en MARKER_Portal_Center
    if bpy.data.objects.get("PORTAL") is None:
        pc = bpy.data.objects["MARKER_Portal_Center"].matrix_world.translation
        root = bpy.data.objects.new("PORTAL", None)
        bpy.data.collections["BLD_PORTAL"].objects.link(root)
        root.location = (pc.x, pc.y, pc.z)
        root["landmark"] = "Portal (arco, pilares, velo, pedestal, piedras runicas y pedestales de descenso)"
        root["interior"] = False
        rinv = Matrix.Translation((pc.x, pc.y, pc.z)).inverted()     # la matriz de la raiz aun no esta evaluada
        for o in list(bpy.data.collections["BLD_PORTAL"].objects):
            if o.parent is None and o.name.startswith("PORTAL_") and o is not root:
                mw = o.matrix_world.copy()
                o.parent = root
                o.matrix_parent_inverse = Matrix.Identity(4)
                o.matrix_basis = rinv @ mw
        bpy.context.view_layer.update()
        st.setdefault("fixes", []).append("PORTAL: raiz unica creada en MARKER_Portal_Center para las 120 piezas sueltas")
    for cname, dist in DISTRICT_COLS.items():
        col = bpy.data.collections[cname]
        for r in col.objects:
            if r.parent is not None or r.type != "EMPTY":
                continue
            if r.name == "PORTAL" or bpy.data.objects.get(f"{r.name}_Body") is not None:
                out[r.name] = {"root": r, "district": dist}
    return out


def parts(name, r):
    ch = {c.name: c for c in r.children_recursive}
    marker = bpy.data.objects.get(str(r.get("marker", "")))
    interior = bool(r.get("interior", marker.get("interior", False) if marker else False))
    doors = [o for n, o in ch.items() if n.startswith("MARKER_") and ("_Door" in n) and o.type == "EMPTY"
             and "alias_of" not in o]
    ivol = [o for n, o in ch.items() if n.endswith("_InteriorVolume")]
    return {"Body": ch.get(f"{name}_Body"), "Roof": ch.get(f"{name}_Roof"), "Props": ch.get(f"{name}_Props"),
            "col": [o for n, o in ch.items() if n.endswith("-colonly")],
            "Body_LOD1": ch.get(f"{name}_Body_LOD1"), "Roof_LOD1": ch.get(f"{name}_Roof_LOD1"),
            "LOD2": [o for n, o in ch.items() if n.endswith("_LOD2")],
            "doors": doors, "ivol": ivol, "interior": interior or bool(ivol), "marker": marker,
            "props": [o for o in ch.values() if "_Prop_" in o.name and o.type == "MESH"]}


# --------------------------------------------------------------------------- limpieza
def clean_mesh(me):
    """Une vertices (0.1 mm), quita caras degeneradas, duplicadas y pares internos (caras coincidentes opuestas que
    tras unir quedan dentro de un volumen), vertices sueltos, y recalcula normales de las partes cerradas."""
    bm = bmesh.new()
    bm.from_mesh(me)
    v0, f0 = len(bm.verts), len(bm.faces)
    bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=1e-4)
    bmesh.ops.dissolve_degenerate(bm, dist=1e-5, edges=bm.edges[:])
    deg = [f for f in bm.faces if f.calc_area() < 1e-8]
    if deg:
        bmesh.ops.delete(bm, geom=deg, context="FACES")
    seen, dup, internal = {}, [], []
    for f in bm.faces:
        key = tuple(sorted(v.index for v in f.verts))
        if key in seen:
            g = seen[key]
            if f.normal.dot(g.normal) > 0.99:
                dup.append(f)
            elif all(len(e.link_faces) >= 3 for e in f.edges):
                internal += [f, g]
        else:
            seen[key] = f
    kill = list(dict.fromkeys(dup + internal))
    if kill:
        bmesh.ops.delete(bm, geom=kill, context="FACES")
    loose = [v for v in bm.verts if not v.link_faces]
    if loose:
        bmesh.ops.delete(bm, geom=loose, context="VERTS")
    # normales: islas cerradas
    seenf, closed = set(), []
    for f in bm.faces:
        if f in seenf:
            continue
        comp, stck = [], [f]
        seenf.add(f)
        while stck:
            g = stck.pop()
            comp.append(g)
            for e in g.edges:
                for h in e.link_faces:
                    if h not in seenf:
                        seenf.add(h)
                        stck.append(h)
        if all(len(e.link_faces) == 2 for g in comp for e in g.edges):
            closed.extend(comp)
    flipped = 0
    if closed:
        before = {f.index: f.normal.copy() for f in closed}
        bmesh.ops.recalc_face_normals(bm, faces=closed)
        flipped = sum(1 for f in closed if f.normal.dot(before.get(f.index, f.normal)) < 0)
    bm.to_mesh(me)
    me.update()
    out = {"verts_merged": v0 - len(bm.verts), "faces_removed": f0 - len(bm.faces), "dup": len(dup),
           "internal": len(internal), "deg": len(deg), "flipped": flipped}
    bm.free()
    return out


def cleanup(objs, st):
    seen = set()
    tot = Counter()
    for o in objs:
        if o.type != "MESH" or o.data.name in seen or o.name.endswith("-navmesh"):
            continue
        seen.add(o.data.name)
        if o.data.users > 0 and o.data.library is None:
            r = clean_mesh(o.data)
            tot.update(r)
    st["cleanup"] = {"meshes": len(seen), **dict(tot)}
    # escalas aplicadas (instancias escaladas -> malla propia)
    scaled = []
    for o in objs:
        if o.type == "MESH" and any(abs(s - 1.0) > 1e-4 for s in o.scale):
            me = o.data.copy()
            me.name = f"{o.name}_mesh"
            me.transform(Matrix.Diagonal((*o.scale, 1.0)))
            o.data = me
            o.scale = (1.0, 1.0, 1.0)
            scaled.append(o.name)
    st["scale_applied"] = scaled


# --------------------------------------------------------------------------- estructura y LOD
def box_collider_from(name, r, objs, col):
    pts = []
    inv = r.matrix_world.inverted()
    for o in objs:
        if o is None:
            continue
        mw = inv @ o.matrix_world
        pts += [mw @ Vector(c) for c in o.bound_box]
    lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co = Vector((lo.x + (v.co.x + 0.5) * (hi.x - lo.x), lo.y + (v.co.y + 0.5) * (hi.y - lo.y),
                       lo.z + (v.co.z + 0.5) * (hi.z - lo.z)))
    me = bpy.data.meshes.new(f"{name}-colonly")
    bm.to_mesh(me)
    bm.free()
    c = bpy.data.objects.new(f"{name}-colonly", me)
    col.objects.link(c)
    c.parent = r
    c.hide_render = True
    return c


def ensure_structure(name, info, st):
    r = info["root"]
    p = parts(name, r)
    col = r.users_collection[0]
    fixes = []
    if p["Props"] is None:
        e = bpy.data.objects.new(f"{name}_Props", None)
        col.objects.link(e)
        e.parent = r
        fixes.append("Props vacio creado")
    if not p["col"]:
        box_collider_from(name, r, [p["Body"], p["Roof"]] if p["Body"] else list(r.children), col)
        fixes.append("colision de caja creada")
    else:
        # colision simple: ninguna -colonly con mas de 400 triangulos (sin detalles)
        for c in p["col"]:
            if tris(c) > 400:
                st.setdefault("collision_heavy", []).append((c.name, tris(c)))
    if p["Body"] is not None and p["Body_LOD1"] is None:
        P13.lods(p["Body"], col, (("LOD1", 0.5),))
        fixes.append("Body_LOD1 creado")
    if p["Roof"] is not None and p["Roof_LOD1"] is None:
        P13.lods(p["Roof"], col, (("LOD1", 0.5),))
        fixes.append("Roof_LOD1 creado")
    p = parts(name, r)
    if p["Body"] is not None and not p["LOD2"]:
        P13.lods(p["Body"], col, (("LOD2", 0.15),))
        fixes.append("LOD2 creado (diezmado 0.15)")
    if fixes:
        st.setdefault("structure_fixes", {})[name] = fixes
    return parts(name, r)


def lod_stats(name, p, moradas):
    t0 = tris(p["Body"]) + tris(p["Roof"])
    t1 = tris(p["Body_LOD1"]) + tris(p["Roof_LOD1"])
    t2 = sum(tris(o) for o in p["LOD2"])
    return t0, t1, t2


def redo_lod2(name, p, col):
    """LOD2 por encima del 20 %: un solo objeto diezmado al 15 % del cuerpo + cubierta, color plano."""
    src = [o for o in (p["Body"], p["Roof"]) if o is not None]
    t0 = sum(tris(o) for o in src)
    for o in p["LOD2"]:
        me = o.data
        bpy.data.objects.remove(o)
        if me.users == 0:
            bpy.data.meshes.remove(me)
    bm = bmesh.new()
    r = src[0].parent
    inv = r.matrix_world.inverted()
    for o in src:
        tmp = o.data.copy()
        tmp.transform(inv @ o.matrix_world)
        bm.from_mesh(tmp)
        bpy.data.meshes.remove(tmp)
    me = bpy.data.meshes.new(f"{name}_LOD2")
    bm.to_mesh(me)
    bm.free()
    flat = LU.flat_material(f"MAT_LOD2_{name}", LU.average_color(src))
    me.materials.clear()
    me.materials.append(flat)
    for poly in me.polygons:
        poly.material_index = 0
    o = bpy.data.objects.new(f"{name}_Body_LOD2", me)
    col.objects.link(o)
    o.parent = r
    m = o.modifiers.new("lod", "DECIMATE")
    m.ratio = max(0.02, 0.15 * t0 / max(1, tris(o)))
    dg = bpy.context.evaluated_depsgraph_get()
    new = bpy.data.meshes.new_from_object(o.evaluated_get(dg))
    o.modifiers.clear()
    old = o.data
    o.data = new
    new.name = o.name
    bpy.data.meshes.remove(old)
    o.hide_render = True
    return o


# --------------------------------------------------------------------------- materiales
def material_audit(objs, st):
    used = {}
    for o in objs:
        if o.type == "MESH":
            for s in o.material_slots:
                if s.material is not None:
                    used[s.material.name] = s.material
    rows, bad_nodes, not_concordia, emissive, magic_bad, sat_bad = {}, [], [], {}, [], []
    for n, m in sorted(used.items()):
        if not n.startswith("MAT_"):
            not_concordia.append(n)
        nodes = [nd.type for nd in m.node_tree.nodes] if m.use_nodes else []
        odd = sorted(set(nodes) - ALLOWED_NODES)
        mix_ok = all(nd.blend_type == "MULTIPLY" for nd in m.node_tree.nodes if nd.type == "MIX") if m.use_nodes else True
        if odd or not mix_ok:
            bad_nodes.append((n, odd, "MIX no-multiply" if not mix_ok else ""))
        b = next((nd for nd in m.node_tree.nodes if nd.type == "BSDF_PRINCIPLED"), None) if m.use_nodes else None
        es = float(b.inputs["Emission Strength"].default_value) if b else 0.0
        ec = tuple(srgb(c) for c in b.inputs["Emission Color"].default_value[:3]) if b else (0, 0, 0)
        base = tuple(srgb(c) for c in LU.material_linear_color(m))
        s_, h_ = colorsys.rgb_to_hsv(*base)[1], colorsys.rgb_to_hsv(*base)[0] * 360
        row = {"base": hexc(base), "sat": round(s_, 3), "hue": round(h_, 1)}
        if b is not None:
            row["alpha"] = round(float(b.inputs["Alpha"].default_value), 2)
        if es > 0 and max(ec) > 0:
            row["emission"] = hexc(ec)
            row["emission_strength"] = round(es, 2)
            emissive[n] = row
            eh = colorsys.rgb_to_hsv(*ec)[0] * 360
            es_ = colorsys.rgb_to_hsv(*ec)[1]
            is_magic = abs(ec[0] - MAGIC[0]) < 0.02 and abs(ec[1] - MAGIC[1]) < 0.02 and abs(ec[2] - MAGIC[2]) < 0.02
            if not is_magic and n not in NATURAL_WARM:
                magic_bad.append((n, row["emission"], round(eh, 1), round(es_, 2)))
        if s_ > 0.35 and not (185 <= h_ <= 215) and not n.startswith("MAT_LOD2_"):
            sat_bad.append((n, row["base"], row["sat"], row["hue"]))
        rows[n] = row
    st["materials"] = {"count": len(used), "not_concordia": not_concordia, "non_exportable_nodes": bad_nodes,
                       "emissive": emissive, "emission_not_8FD0FF": magic_bad, "saturation_over_035": sat_bad,
                       "list": rows}
    return used


def glb_material_check(path, emissive_names):
    import struct
    with open(path, "rb") as fh:
        data = fh.read()
    ln = struct.unpack("<I", data[12:16])[0]
    g = json.loads(data[20:20 + ln])
    mats = {m.get("name"): m for m in g.get("materials", [])}
    miss = [n for n in emissive_names if n in mats and not mats[n].get("emissiveFactor")]
    exts = sorted({e for m in mats.values() for e in m.get("extensions", {})})
    up = "Y"
    return {"materials": len(mats), "emissive_without_emissiveFactor": miss, "extensions": exts, "up_axis": up}


def fixes_extra(reg, st):
    out = {}
    # color magico: el vitral emitia #7DB5E5; se pasa a #8FD0FF (misma fuerza 0.6)
    m = bpy.data.materials.get("MAT_Stained_Glass_Blue")
    if m is not None:
        b = next(nd for nd in m.node_tree.nodes if nd.type == "BSDF_PRINCIPLED")
        b.inputs["Emission Color"].default_value = (0.2747, 0.6308, 1.0, 1.0)          # #8FD0FF lineal
        m["note"] = "vitral azul palido, emision #8FD0FF 0.6 (etapa 24: antes #7DB5E5)"
        out["MAT_Stained_Glass_Blue"] = "emision #7DB5E5 -> #8FD0FF"
    # Moradas: InteriorVolume y MARKER_<N>_Door (alias de la puerta de planta baja; se conservan los de la E10)
    n_iv = 0
    for name, info in reg.items():
        if not name.startswith("Morada_"):
            continue
        r = info["root"]
        col = r.users_collection[0]
        if bpy.data.objects.get(f"{name}_InteriorVolume") is None:
            yb = -2.0 if r["tipo"] == "casa_grande" else -5.0
            fl = {"habitacion": 3, "casa_pequena": 1, "casa_grande": 2}[r["tipo"]]
            bm = bmesh.new()
            bmesh.ops.create_cube(bm, size=1.0)
            lo, hi = Vector((-2.75, yb + 0.3, 0.0)), Vector((2.75, 2.7, fl * 3.2 - 0.3))
            for v in bm.verts:
                v.co = Vector((lo.x + (v.co.x + 0.5) * (hi.x - lo.x), lo.y + (v.co.y + 0.5) * (hi.y - lo.y),
                               lo.z + (v.co.z + 0.5) * (hi.z - lo.z)))
            me = bpy.data.meshes.new(f"{name}_InteriorVolume")
            bm.to_mesh(me)
            bm.free()
            iv = bpy.data.objects.new(f"{name}_InteriorVolume", me)
            col.objects.link(iv)
            iv.parent = r
            iv.display_type = "WIRE"
            iv.hide_render = True
            iv["note"] = "volumen del interior (el interior de cada vivienda se carga aparte, E10)"
            n_iv += 1
        if bpy.data.objects.get(f"MARKER_{name}_Door") is None:
            src = next((c for c in r.children if c.name.startswith("MARKER_Morada_Door_") and c.get("floor", 0) == 0), None)
            if src is not None:
                e = bpy.data.objects.new(f"MARKER_{name}_Door", None)
                e.empty_display_type = "SINGLE_ARROW"
                col.objects.link(e)
                e.parent = r
                e.matrix_parent_inverse = Matrix.Identity(4)
                e.matrix_basis = src.matrix_basis.copy()
                e["alias_of"] = src.name
        info["p"] = parts(name, r)
    out["moradas_interior_volumes"] = n_iv
    # LOD1 al 50 %: los del ensamblador (reconstruccion con menos detalle) que se salen de 0.42-0.58 se rehacen
    redo = []
    for name, info in reg.items():
        p = info["p"]
        for part in ("Body", "Roof"):
            o0, o1 = p[part], p[f"{part}_LOD1"]
            if o0 is None or o1 is None or not tris(o0):
                continue
            r1 = tris(o1) / tris(o0)
            if not 0.42 <= r1 <= 0.58:
                me = o1.data
                bpy.data.objects.remove(o1)
                if me.users == 0:
                    bpy.data.meshes.remove(me)
                P13.lods(o0, info["root"].users_collection[0], (("LOD1", 0.5),))
                redo.append(f"{name}_{part} ({r1:.2f})")
        info["p"] = parts(name, info["root"])
    out["lod1_regenerated"] = redo
    st["fixes_extra"] = out


# --------------------------------------------------------------------------- verificaciones
def world_polys(objs):
    verts, faces, owner = [], [], []
    for k, (tag, o) in enumerate(objs):
        mw = o.matrix_world
        me = o.data
        base = len(verts)
        verts += [mw @ v.co for v in me.vertices]
        for p in me.polygons:
            faces.append([base + i for i in p.vertices])
            owner.append(tag)
    return BVHTree.FromPolygons(verts, faces, epsilon=1e-6), owner


def door_visibility(reg, st):
    occ = []
    for name, info in reg.items():
        p = info["p"]
        for o in (p["Body"], p["Roof"]):
            if o is not None and o.type == "MESH":
                occ.append((name, o))
    bvh, owner = world_polys(occ)
    d = CAM_BACK
    cxy = Vector((d.x, d.y, 0)).normalized()
    res = {"doors": 0, "facing_camera": 0, "back_facing": 0, "blocked": [], "blocked_by_district": Counter()}
    for name, info in reg.items():
        for dm in info["p"]["doors"]:
            res["doors"] += 1
            mw = dm.matrix_world
            n = (mw.to_3x3() @ Vector((0, 1, 0))).normalized()
            if n.dot(cxy) < -0.05:
                res["back_facing"] += 1
                continue
            res["facing_camera"] += 1
            hidden, by = 0, None
            for h in (0.3, 1.1, 2.0):
                o = mw.translation + n * 0.35 + Vector((0, 0, h))
                for _ in range(10):
                    loc, _n, idx, _dist = bvh.ray_cast(o, d, 500.0)
                    if loc is None:
                        break
                    if owner[idx] == name:
                        o = loc + d * 0.02
                        continue
                    hidden += 1
                    by = owner[idx]
                    break
            if hidden >= 2:                                      # se ve menos de 2 de los 3 puntos de la puerta
                res["blocked"].append({"door": dm.name, "building": name, "by": by, "district": info["district"],
                                       "same_row": bool(name.startswith("Morada_") and by.startswith("Morada_") and
                                                        bpy.data.objects[name]["terraza"] == bpy.data.objects[by]["terraza"])})
                res["blocked_by_district"][info["district"]] += 1
    res["blocked_by_district"] = dict(res["blocked_by_district"])
    st["door_visibility"] = {k: (v if k != "blocked" else v[:60]) for k, v in res.items()}
    st["door_visibility"]["blocked_total"] = len(res["blocked"])
    st["door_visibility"]["criterion"] = "puerta visible si se ven >= 2 de sus 3 puntos (0.3, 1.1, 2.0 m) desde CAM_Iso"
    st["door_visibility"]["blocked_same_row_moradas"] = sum(1 for b in res["blocked"] if b["same_row"])
    st["door_visibility"]["blocked_list"] = res["blocked"]
    return res


def footprints(reg, st):
    import build_stage18 as B18
    out, bad = {}, []
    for name, info in reg.items():
        p, r = info["p"], info["root"]
        m = p["marker"]
        fw = r.get("footprint_w") or (m.get("footprint_w") if m else None)
        fd = r.get("footprint_d") or (m.get("footprint_d") if m else None)
        if not fw or p["Body"] is None or name == "PORTAL":
            continue
        g = B18.ground_footprint(p["Body"], float(fw) / 2, float(fd) / 2)
        ox, oy = g.get("over_x_m", 0.0), g.get("over_y_m", 0.0)
        out[name] = [ox, oy]
        if max(ox, oy) > 0.2 + 1e-3:
            bad.append((name, ox, oy, f"{fw}x{fd}"))
    st["footprints"] = {"checked": len(out), "over_0.2": bad}
    return bad


def geom_hash(objs):
    h = hashlib.sha1()
    for o in objs:
        if o is None:
            continue
        for v in o.data.vertices:
            h.update(("%.3f,%.3f,%.3f;" % tuple(v.co)).encode())
    return h.hexdigest()[:16]


def identical(reg, st):
    groups = defaultdict(list)
    for name, info in reg.items():
        p = info["p"]
        if p["Body"] is None:
            continue
        key = geom_hash([p["Body"], p["Roof"]])
        groups[key].append(name)
    dups = [v for v in groups.values() if len(v) > 1]
    non_mor = [v for v in dups if not any(n.startswith("Morada_") for n in v)]
    # Moradas: vecinos de fila identicos (misma malla y misma fachada) -> no deberia haber ninguno
    neigh = []
    for key in ("NE", "NO", "SO", "SE"):
        rows = defaultdict(list)
        for name, info in reg.items():
            if name.startswith(f"Morada_{key}_"):
                r = info["root"]
                rows[r["terraza"]].append((math.atan2(r.matrix_world.translation.y, r.matrix_world.translation.x), name))
        for t, row in rows.items():
            row.sort()
            for (a0, n0), (a1, n1) in zip(row, row[1:]):
                p0, p1 = reg[n0]["p"], reg[n1]["p"]
                if p0["Body"].data == p1["Body"].data and p0["Roof"].data == p1["Roof"].data:
                    neigh.append((n0, n1))
    seeds = Counter(f"{info['root'].get('seed', '')}|{name}" for name, info in reg.items())
    st["identical"] = {"groups_non_moradas": non_mor,
                       "moradas_instanced_variants": len({geom_hash([reg[n]['p']['Body'], reg[n]['p']['Roof']])
                                                          for n in reg if n.startswith('Morada_')}),
                       "moradas_identical_neighbours": neigh,
                       "seeds_note": "rng_for(nombre, semilla): el nombre entra en la semilla, cada edificio tiene la suya",
                       "unique_seed_keys": len(seeds) == len(reg)}
    return non_mor, neigh


# --------------------------------------------------------------------------- navegacion
def footprint_rects(reg):
    """Rectangulos de suelo (marco de la raiz) de cada edificio que no se puede atravesar: huella del marcador
    recortada al cuerpo a nivel de suelo; sin huella, la caja de su colision por debajo de 2 m."""
    rects = []
    for name, info in reg.items():
        r, p = info["root"], info["p"]
        if name in ("PORTAL", "GranSubasta"):                 # monumento abierto / pabellon abierto: transitables
            continue
        m = p["marker"]
        if name.startswith("Morada_"):
            yb = -2.0 if r["tipo"] == "casa_grande" else -5.0
            rects.append((name, r.matrix_world.copy(), (-3.0, yb, 3.0, 3.0)))
            if r["tipo"] == "casa_grande":
                rects.append((name, r.matrix_world.copy(), (-3.0, -5.0, 3.0, -2.0)))
            continue
        rinv = r.matrix_world.inverted()
        src = p["Body"] if p["Body"] is not None else (p["col"][0] if p["col"] else None)
        if src is None:
            continue
        mw = rinv @ src.matrix_world
        pts = [mw @ v.co for v in src.data.vertices]
        pts = [q for q in pts if q.z < 2.0] or pts
        x0, x1 = min(q.x for q in pts), max(q.x for q in pts)
        y0, y1 = min(q.y for q in pts), max(q.y for q in pts)
        fw = r.get("footprint_w") or (m.get("footprint_w") if m else None)
        fd = r.get("footprint_d") or (m.get("footprint_d") if m else None)
        if fw:
            hx, hy = float(fw) / 2, float(fd) / 2
            x0, x1, y0, y1 = max(-hx, x0), min(hx, x1), max(-hy, y0), min(hy, y1)
        rects.append((name, r.matrix_world.copy(), (x0 + 0.05, y0 + 0.05, x1 - 0.05, y1 - 0.05)))
    return rects


def carve_navmesh(reg, st):
    """Quita de la malla de navegacion las caras cuyo centro cae dentro de una huella; las caras que la cruzan se
    cortan por los lados de la huella antes de decidir."""
    from mathutils import kdtree
    rects = footprint_rects(reg)
    navs = [o for o in bpy.data.objects if o.name.endswith("-navmesh") and o.name.startswith("TRN_NavMesh_")]
    rep = {}
    for nav in navs:
        mw = nav.matrix_world
        bm = bmesh.new()
        bm.from_mesh(nav.data)
        bm.transform(mw)
        bm.faces.ensure_lookup_table()
        area0 = sum(f.calc_area() for f in bm.faces)
        cen = [f.calc_center_median() for f in bm.faces]
        kd = kdtree.KDTree(len(cen))
        for i, c in enumerate(cen):
            kd.insert(c, i)
        kd.balance()
        faces = list(bm.faces)
        removed, hit, cut = 0.0, Counter(), 0
        for name, rm, (x0, y0, x1, y1) in rects:
            rinv = rm.inverted()

            def inside(q, m=0.0):
                lq = rinv @ q
                return x0 + m < lq.x < x1 - m and y0 + m < lq.y < y1 - m and -1.5 < lq.z < 2.5
            c = rm @ Vector(((x0 + x1) / 2, (y0 + y1) / 2, 0))
            rad = math.hypot(x1 - x0, y1 - y0) / 2
            cand = [faces[i] for _co, i, _d in kd.find_range(c, rad + 30) if faces[i].is_valid]
            cand = [f for f in cand if inside(f.calc_center_median()) or any(inside(v.co, 0.02) for v in f.verts)]
            if not cand:
                continue
            partial = [f for f in cand if not all(inside(v.co, -0.01) for v in f.verts)]
            if partial:
                cut += len(partial)
                for (px, py, nx, ny) in ((x0, 0, 1, 0), (x1, 0, -1, 0), (0, y0, 0, 1), (0, y1, 0, -1)):
                    live = [f for f in cand if f.is_valid]
                    if not live:
                        break
                    co = rm @ Vector((px if nx else 0, py if ny else 0, 0))
                    no = (rm.to_3x3() @ Vector((nx, ny, 0))).normalized()
                    geom = list({e for f in live for e in f.edges}) + live + list({v for f in live for v in f.verts})
                    r_ = bmesh.ops.bisect_plane(bm, geom=geom, plane_co=co, plane_no=no, dist=1e-4)
                    new = {g for g in r_["geom"] if isinstance(g, bmesh.types.BMFace)}
                    new |= {f for g in r_["geom_cut"] if isinstance(g, bmesh.types.BMEdge) for f in g.link_faces}
                    cand = list(new | {f for f in live if f.is_valid})
            kill = [f for f in cand if f.is_valid and inside(f.calc_center_median())]
            if kill:
                removed += sum(f.calc_area() for f in kill)
                hit[name] += len(kill)
                bmesh.ops.delete(bm, geom=kill, context="FACES")
        loose = [v for v in bm.verts if not v.link_faces]
        if loose:
            bmesh.ops.delete(bm, geom=loose, context="VERTS")
        bm.transform(mw.inverted())
        bm.to_mesh(nav.data)
        bm.free()
        rep[nav.name] = {"area_m2": round(area0, 1), "removed_m2": round(removed, 2), "faces_cut": cut,
                         "buildings_invading": dict(hit)}
    st["navmesh_carve"] = {"rects": len(rects), **rep}
    return rep


def nav_checks(reg, st):
    navs = [o for o in bpy.data.objects if o.name.endswith("-navmesh") and o.name.startswith("TRN_NavMesh_")]
    verts, faces = [], []
    for nav in navs:
        mw = nav.matrix_world
        b = len(verts)
        verts += [mw @ v.co for v in nav.data.vertices]
        faces += [[b + i for i in p.vertices] for p in nav.data.polygons]
    bvh = BVHTree.FromPolygons(verts, faces, epsilon=1e-6)

    def on_nav(p, tol=1.6, dz=1.3):
        loc, _n, _i, dist = bvh.find_nearest(p, tol + dz)
        return loc is not None and (loc.xy - p.xy).length <= tol and abs(loc.z - p.z) <= dz

    doors_ok, doors_bad, links = 0, [], []
    for name, info in reg.items():
        for dm in info["p"]["doors"]:
            mw = dm.matrix_world
            n = (mw.to_3x3() @ Vector((0, 1, 0))).normalized()
            p = mw.translation + n * 0.8
            if p.z - info["root"].matrix_world.translation.z > 2.5:   # puertas de galeria (planta alta)
                continue
            if on_nav(p):
                doors_ok += 1
            else:
                doors_bad.append(dm.name)
                loc, _n, _i, dist = bvh.find_nearest(p, 15.0)
                if loc is not None:
                    r = info["root"]
                    for tag, q in (("Start", loc), ("End", p)):
                        e = bpy.data.objects.new(f"NAVLINK_{dm.name[7:]}_{tag}", None)
                        e.empty_display_type = "SPHERE"
                        e.empty_display_size = 0.3
                        r.users_collection[0].objects.link(e)
                        e.parent = r
                        e.matrix_parent_inverse = Matrix.Identity(4)
                        e.location = r.matrix_world.inverted() @ q
                        e["navigation_link"] = "NavigationLink3D: Start en la malla, End delante de la puerta"
                    links.append((dm.name, round((loc - p).length, 2)))
    plazas = [o for o in bpy.data.objects if o.name.startswith(("MARKER_Prop_Plazuela_", "MARKER_TrainingZone_",
                                                                "MARKER_Portal_Center", "MARKER_Prop_FuenteMercado"))]
    plaza_bad = []
    for o in plazas:
        c = o.matrix_world.translation
        rr = 10.0 if o.name == "MARKER_Portal_Center" else 3.5          # el centro del Portal es el pedestal
        pts = [c + Vector((math.cos(a) * rr, math.sin(a) * rr, 0)) for a in (0, 1.57, 3.14, 4.71)]
        if sum(on_nav(q, 1.0, 1.5) for q in pts) < 3:
            plaza_bad.append(o.name)
    stairs_bad, n_st = [], 0
    for o in bpy.data.objects:
        if o.name.startswith(("MARKER_Stairs_", "MARKER_Escalinata_")) and o.type == "EMPTY":
            n_st += 1
            mw = o.matrix_world
            d = (mw.to_3x3() @ Vector((0, 1, 0))).normalized()
            top = mw.translation - d * 1.2
            if not on_nav(top, 2.0, 1.6):
                stairs_bad.append(o.name)
    st["navigation"] = {"ground_doors_on_navmesh": doors_ok, "ground_doors_off_navmesh": doors_bad[:40],
                        "ground_doors_off_count": len(doors_bad), "nav_links_added": links, "plazas_checked": len(plazas),
                        "plazas_off_navmesh": plaza_bad, "stairs_checked": n_st, "stairs_top_off_navmesh": stairs_bad[:30],
                        "stairs_off_count": len(stairs_bad)}


# --------------------------------------------------------------------------- exportacion
def file_objects(reg, conex):
    files = defaultdict(list)
    for name, info in reg.items():
        files[info["district"]] += [info["root"]] + list(info["root"].children_recursive)
    # extras de distrito: raices que no son edificios (puestos, fuente, plazuelas, plaza de las armas, tablon...)
    for cname, dist in DISTRICT_COLS.items():
        for r in bpy.data.collections[cname].objects:
            if r.parent is None and r.name not in reg:
                files[dist] += [r] + list(r.children_recursive)
    for o in conex:
        files[district_of_point(o.matrix_world.translation)] += [o] + list(o.children_recursive)
    return files


def props_library(st):
    col = bpy.data.collections.get("BLD_PROPS_LIBRARY") or bpy.data.collections.new("BLD_PROPS_LIBRARY")
    if col.name not in bpy.context.scene.collection.children:
        bpy.context.scene.collection.children.link(col)
    for o in list(col.objects):
        bpy.data.objects.remove(o)
    meshes = {}
    srcs = list(bpy.data.collections["BLD_PROPS"].objects)
    srcs += [o for o in bpy.data.objects if o.type == "MESH" and o.data.name in ("DOOR_Morada", "LANTERN_Shard",
                                                                               "PLATE_Morada")]
    for o in srcs:
        if o.type == "MESH" and o.data.name not in meshes:
            meshes[o.data.name] = o.data
    root = bpy.data.objects.new("PROPS_Library", None)
    col.objects.link(root)
    root.location = (3000.0, 1200.0, 0.0)
    for i, (n, me) in enumerate(sorted(meshes.items())):
        o = bpy.data.objects.new(f"PROP_{n}", me)
        col.objects.link(o)
        o.parent = root
        o.location = ((i % 12) * 4.0, (i // 12) * 4.0, 0.0)
    st["props_library"] = {"unique_meshes": len(meshes), "tris": sum(len(m.polygons) for m in meshes.values())}
    return [root] + list(root.children)


def main():
    global CAM_BACK
    st = {}
    bpy.ops.wm.open_mainfile(filepath=SRC)
    save()
    st["saved_before"] = os.path.relpath(OUT, REPO)
    CAM_BACK = B.iso_cam_back().normalized()
    reg = registry(st)
    st["buildings"] = len(reg)
    conex = [o for o in bpy.data.objects if o.parent is None and o.type == "EMPTY" and
             (o.name.startswith(("MARKER_Bridge_", "MARKER_Stairs_", "MARKER_Escalinata_"))) and
             any(c.type == "MESH" for c in o.children)]
    # 1. limpieza (todas las mallas de edificios, conexiones, kit y props)
    objs = []
    for info in reg.values():
        objs += [info["root"]] + list(info["root"].children_recursive)
    for o in conex:
        objs += list(o.children_recursive)
    objs += list(bpy.data.collections["BLD_KIT"].all_objects) + list(bpy.data.collections["BLD_PROPS"].objects)
    objs = list(dict.fromkeys(objs))
    cleanup(objs, st)
    print("cleanup", st["cleanup"], len(st["scale_applied"]), flush=True)
    # 2-3. estructura, LOD, presupuesto
    per_b, per_d = {}, defaultdict(lambda: Counter())
    redone = []
    for name, info in reg.items():
        info["p"] = ensure_structure(name, info, st)
    fixes_extra(reg, st)
    for name, info in reg.items():
        p = info["p"]
        t0, t1, t2 = lod_stats(name, p, name.startswith("Morada_"))
        if t0 and t2 / t0 > 0.20 and not name.startswith("Morada_"):
            redo_lod2(name, p, info["root"].users_collection[0])
            redone.append(name)
            p = parts(name, info["root"])
            t0, t1, t2 = lod_stats(name, p, False)
        info["p"] = p
        extra = sum(tris(o) for o in info["root"].children_recursive if o.type == "MESH" and not o.hide_render and
                    o not in (p["Body"], p["Roof"]) and not o.name.endswith(("-colonly", "_LOD1", "_LOD2")))
        per_b[name] = {"district": info["district"], "LOD0_body_roof": t0, "LOD0_props_extras": extra, "LOD1": t1,
                       "LOD2": t2, "lod1_ratio": round(t1 / t0, 3) if t0 else None,
                       "lod2_ratio": round(t2 / t0, 3) if t0 else None, "has_roof": p["Roof"] is not None,
                       "interior": p["interior"], "doors": len(p["doors"]), "interior_volume": bool(p["ivol"]),
                       "door_marker_named": bpy.data.objects.get(f"MARKER_{name}_Door") is not None or
                       any(d.name.startswith("MARKER_") for d in p["doors"]),
                       "colliders": len(p["col"])}
        d = per_d[info["district"]]
        d["buildings"] += 1
        d["LOD0"] += t0 + extra
        d["LOD2"] += t2
    st["lod2_redone"] = redone
    st["per_building"] = per_b
    st["per_district"] = {k: dict(v) for k, v in per_d.items()}
    st["city"] = {"LOD0": sum(v["LOD0"] for v in per_d.values()), "LOD2": sum(v["LOD2"] for v in per_d.values()),
                  "buildings": len(reg)}
    missing = {n: [k for k in ("Roof",) if not v["has_roof"]] for n, v in per_b.items() if not v["has_roof"]}
    st["no_roof"] = sorted(missing)
    st["interior_missing"] = sorted(n for n, v in per_b.items() if v["interior"] and (not v["doors"] or not v["interior_volume"]))
    print("structure", st.get("structure_fixes", {}) and len(st["structure_fixes"]), "redone", len(redone), st["city"],
          flush=True)
    # verificaciones
    door_visibility(reg, st)
    footprints(reg, st)
    identical(reg, st)
    # 7. navegacion
    carve_navmesh(reg, st)
    nav_checks(reg, st)
    print("nav", json.dumps(st["navmesh_carve"], default=str)[:900], json.dumps(st["navigation"])[:600], flush=True)
    # 5-6. materiales y exportacion
    files = file_objects(reg, conex)
    kit = [o for o in bpy.data.collections["BLD_KIT"].all_objects
           if not (o.name.startswith("Gremio_Cazadores") or (o.parent and o.parent.name.startswith("Gremio_Cazadores")))]
    files["kit"] = kit
    files["props"] = props_library(st)
    all_exp = [o for v in files.values() for o in v]
    used = material_audit(all_exp, st)
    emissive_names = list(st["materials"]["emissive"])
    for o in bpy.data.objects:
        if o.name.endswith(("_LOD1", "_LOD2")):
            o.hide_render = True
    for f in SUPERSEDED:
        p = os.path.join(EXP, f)
        if os.path.exists(p):
            os.remove(p)
    st["superseded_removed"] = list(SUPERSEDED)
    st["exports"] = {}
    for key, objs_ in files.items():
        path = os.path.join(EXP, f"bld_{key}.glb")
        size = G.export_glb(list(dict.fromkeys(objs_)), path)
        st["exports"][f"bld_{key}.glb"] = {"mb": round(size / 2 ** 20, 2), **G.glb_info(path),
                                          **glb_material_check(path, emissive_names)}
        print("export", key, st["exports"][f"bld_{key}.glb"]["mb"], st["exports"][f"bld_{key}.glb"]["tris"], flush=True)
    # terrenos con la malla de navegacion recortada
    def col_objs(prefix):
        return [o for c in bpy.data.collections if c.name.startswith(prefix) for o in c.objects]
    city = col_objs("GODOT_CITY_")
    sobjs = [o for cn in G.STRUCT_COLS for o in bpy.data.collections[cn].objects
             if o.type == "MESH" and not o.name.endswith("-colonly")]
    scol = col_objs("GODOT_STRUCT_COL")
    nav = col_objs("GODOT_NAVMESH")
    for d in G.DISTRICTS:
        objs_ = [o for o in city + sobjs + scol + nav if o.get("district") == d]
        p = os.path.join(EXP, f"concordia_terrain_{d}.glb")
        st["exports"][os.path.basename(p)] = {"mb": round(G.export_glb(objs_, p) / 2 ** 20, 2), **G.glb_info(p)}
    p = os.path.join(EXP, "concordia_markers.glb")
    mk = [o for o in bpy.data.objects if o.type == "EMPTY" and o.name.startswith("MARKER_") and o.parent is None]
    st["exports"]["concordia_markers.glb"] = {"mb": round(G.export_glb(mk, p) / 2 ** 20, 2), **G.glb_info(p)}
    for o in bpy.data.objects:
        if o.name.endswith(("_LOD1", "_LOD2")):
            o.hide_set(True)
    save()
    with open(REPORT, "w") as fh:
        json.dump(st, fh, indent=1, ensure_ascii=False, default=str)
    print("saved:", OUT)
    for k in ("cleanup", "scale_applied", "structure_fixes", "lod2_redone", "per_district", "city", "no_roof",
              "interior_missing", "footprints", "identical", "collision_heavy"):
        print(k, json.dumps(st.get(k), default=str)[:700])
    dv = st["door_visibility"]
    print("doors", {k: dv[k] for k in ("doors", "facing_camera", "back_facing", "blocked_total", "blocked_by_district")})
    m = st["materials"]
    print("materials", m["count"], "not_concordia", m["not_concordia"], "nodes", m["non_exportable_nodes"][:6],
          "emission_not_8FD0FF", m["emission_not_8FD0FF"], "sat", m["saturation_over_035"][:8])
    print("exports", {k: (v["mb"], v.get("tris"), v.get("emissive_without_emissiveFactor")) for k, v in st["exports"].items()})
    _ = used


if __name__ == "__main__":
    main()
