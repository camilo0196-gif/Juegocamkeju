"""
CONCORDIA - etapa 10 (Blender): materiales con texturas reales de Poly Haven, mascaras nuevas y asignacion por cara.

Materiales (todos glTF): UV Map 'UVWorld' -> Mapping (escala real, KHR_texture_transform) -> Image Texture
  albedo (ajuste Hue/Sat/Value ya horneado) -> Base Color   [telas: Mix Multiply con el color base = baseColorFactor]
  ORM (R AO, G rough, B metal) -> Separate Color -> Roughness / Metallic / grupo 'glTF Material Output'.Occlusion
  normal GL -> Normal Map -> Normal
Mascaras (CORNER, BYTE_COLOR):
  TRN_City     rock_mask (taludes >= ~35 grados con ruido, fuera de calles/terrazas/muros), ash_mask (talud exterior)
  TRN_Exterior moat_mask (depresion Z < 0 pegada al talud, r 204-224, conexa)
  mask_pack (COLOR_0) reempaquetado: ver README_masks.txt
Asignacion por cara con umbral + banda de transicion de 1-2 celdas (dentado por ruido) entre materiales naturales.
Nunca se toca la geometria (solo material_index, atributos de color y nombre de la capa UV).
"""

import json
import os
import sys
from collections import Counter
from math import acos, degrees, hypot

import bmesh
import bpy
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import concordia_const as C  # noqa: E402
import stage09_materials as SM  # noqa: E402
import stage10_polyhaven as PH  # noqa: E402

REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
UV_NAME = "UVWorld"
SEED = 1010
PROCEDURAL = ("MAT_Shard_Blue", "MAT_Wall_Runes", "MAT_Water")
MATERIALS = [n for n in SM.MATS] + ["MAT_Ash_Ground"]
CITY_SLOTS = ["MAT_Ground_Cracked", "MAT_Limestone_Worn", "MAT_Cobble_Concordia", "MAT_Plaza_Slab",
              "MAT_Plaza_Slab_Travertino", "MAT_Wall_Gray", "MAT_Ash_Gray", "MAT_Stone_Repair", "MAT_Rock_Gray"]
EXT_SLOTS = ["MAT_Ash_Ground", "MAT_Ash_Gray", "MAT_Rock_Gray"]
CITY_NATURAL = ("MAT_Ground_Cracked", "MAT_Ash_Gray", "MAT_Rock_Gray")
EXT_NATURAL = tuple(EXT_SLOTS)
ROCK_SLOPE_DEG, ROCK_SLOPE_NOISE = 35.0, 7.0       # roca desde ~35 grados, +-7 de ruido
ROCK_NOISE_M = 6.0
RETAIN_REPAIR_FRAC, RETAIN_REPAIR_M = 0.18, 2.2     # parches de MAT_Stone_Repair en los muros de contencion
DITHER = {"city": 2.5, "exterior": 7.0}             # escala del ruido de la banda (m)
DITHER_P = (0.5, 0.22)                              # prob. de cambio en la celda 1 y 2 de la banda
MOAT_R = (204.0, 224.0)


# ---------------------------------------------------------------------------
# ruido de valor 2D (vectorizado, con semilla)
# ---------------------------------------------------------------------------
def _hash(ix, iy, seed):
    h = (ix * 374761393 + iy * 668265263 + seed * 144269) & 0xFFFFFFFF
    h = ((h ^ (h >> 13)) * 1274126177) & 0xFFFFFFFF
    return ((h ^ (h >> 16)) & 0xFFFF) / 65535.0


def value_noise(x, y, scale, seed, octaves=3):
    x, y = np.asarray(x, float) / scale, np.asarray(y, float) / scale
    tot, amp, norm = 0.0, 1.0, 0.0
    for o in range(octaves):
        ix, iy = np.floor(x).astype(np.int64), np.floor(y).astype(np.int64)
        fx, fy = x - ix, y - iy
        sx, sy = fx * fx * (3 - 2 * fx), fy * fy * (3 - 2 * fy)
        s = seed + 31 * o
        a, b = _hash(ix, iy, s), _hash(ix + 1, iy, s)
        c, d = _hash(ix, iy + 1, s), _hash(ix + 1, iy + 1, s)
        tot = tot + amp * ((a * (1 - sx) + b * sx) * (1 - sy) + (c * (1 - sx) + d * sx) * sy)
        norm += amp
        amp *= 0.5
        x, y = x * 2.03, y * 2.03
    return tot / norm


# ---------------------------------------------------------------------------
# texturas procedurales -> PNG (Shard_Blue, Wall_Runes, Water)
# ---------------------------------------------------------------------------
def bake_procedural():
    from PIL import Image
    import material_library as ML
    SM.setup_res()
    out = {}
    names = list(SM.MATS)
    for name in PROCEDURAL:
        i = names.index(name)
        fn, ns, (r0, r1), _met, _ref, _use = SM.MATS[name]
        rng = np.random.default_rng(SM.SEED * 100 + i)          # misma semilla que la etapa 09
        res = fn(rng)
        alb, h, rough = res[:3]
        alb = SM.cap_saturation(np.clip(alb, 0, 1), SM.SAT_CAP.get(name, SM.SAT_DEFAULT))
        rough = np.clip(rough, 0, 1)
        lo, hi = float(rough.min()), float(rough.max())
        rough = r0 + (rough - lo) / max(1e-6, hi - lo) * (r1 - r0) if hi > lo else np.full_like(rough, r0)
        p = PH.paths(name)
        os.makedirs(p["dir"], exist_ok=True)
        Image.fromarray((np.clip(alb, 0, 1) * 255 + 0.5).astype(np.uint8)).save(p["albedo"], optimize=True)
        Image.fromarray(ML.normal_gl(h, ns)).save(p["normal"], optimize=True)
        PH.write_orm(p["orm"], rough.shape, None, rough, None)
        e = {"albedo": os.path.relpath(p["albedo"], REPO), "normal": os.path.relpath(p["normal"], REPO),
             "orm": os.path.relpath(p["orm"], REPO), "res": list(rough.shape[::-1]), "kind": "procedural (PNG)"}
        if len(res) > 3:
            Image.fromarray((np.clip(res[3], 0, 1) * 255 + 0.5).astype(np.uint8), "L").save(p["emission"], optimize=True)
            e["emission"] = os.path.relpath(p["emission"], REPO)
        out[name] = e
        print("procedural", name, e, flush=True)
    return out


# ---------------------------------------------------------------------------
# materiales
# ---------------------------------------------------------------------------
def gltf_output_group():
    ng = bpy.data.node_groups.get("glTF Material Output")
    if ng is None:
        ng = bpy.data.node_groups.new("glTF Material Output", "ShaderNodeTree")
        ng.interface.new_socket("Occlusion", in_out="INPUT", socket_type="NodeSocketFloat")
    return ng


def lin(hexs):
    c = PH.srgb(hexs)
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def material_spec(name, ph, proc):
    if name in PROCEDURAL:
        e = proc[name]
        _fn, _ns, rr, met, ref, use = SM.MATS[name]
        return {"albedo": e["albedo"], "orm": e["orm"], "normal": e["normal"], "emission": e.get("emission"),
                "uv_scale": (1.0, 1.0), "kind": "procedural", "ref": ref, "use": use, "rough": rr}
    key = "MAT_Cloth" if name.startswith("MAT_Cloth_Patch") else name
    e = ph[key]
    s = {"albedo": e["albedo"], "orm": e["orm"], "normal": e["normal"], "uv_scale": tuple(e["uv_scale"]),
         "kind": "polyhaven", "asset": e["asset"], "dims": e["dimensions_m"], "res": e["resolution"],
         "hsv": e["hue_saturation_value"]}
    if key == "MAT_Cloth":
        s["base_factor"] = PH.CLOTH_VARIANTS[name]
    return s


def build_material(name, spec):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    N, L = m.node_tree.nodes, m.node_tree.links
    for n in list(N):
        N.remove(n)
    for k in list(m.keys()):
        del m[k]
    out = N.new("ShaderNodeOutputMaterial")
    out.location = (600, 0)
    b = N.new("ShaderNodeBsdfPrincipled")
    b.location = (250, 0)
    L.new(b.outputs["BSDF"], out.inputs["Surface"])
    uv = N.new("ShaderNodeUVMap")
    uv.uv_map = UV_NAME
    uv.location = (-1000, 0)
    vec = uv.outputs["UV"]
    if spec["uv_scale"] != (1.0, 1.0):
        mp = N.new("ShaderNodeMapping")
        mp.vector_type = "POINT"
        mp.location = (-800, 0)
        mp.inputs["Scale"].default_value = (spec["uv_scale"][0], spec["uv_scale"][1], 1.0)
        L.new(uv.outputs["UV"], mp.inputs["Vector"])
        vec = mp.outputs["Vector"]

    def img(rel, label, non_color, y):
        im = bpy.data.images.load(os.path.join(REPO, rel), check_existing=True)
        im.colorspace_settings.name = "Non-Color" if non_color else "sRGB"
        t = N.new("ShaderNodeTexImage")
        t.name = t.label = label
        t.image = im
        t.location = (-550, y)
        L.new(vec, t.inputs["Vector"])
        return t
    alb = img(spec["albedo"], "Albedo", False, 300)
    col = alb.outputs["Color"]
    if "base_factor" in spec:
        mix = N.new("ShaderNodeMix")
        mix.data_type = "RGBA"
        mix.blend_type = "MULTIPLY"
        mix.location = (-150, 300)
        mix.inputs["Factor"].default_value = 1.0
        L.new(col, mix.inputs["A"])
        f = lin(spec["base_factor"]) / max(1e-4, float(lin("#B8B8B8").mean()))
        mix.inputs["B"].default_value = (*np.clip(f, 0, 1), 1.0)
        col = mix.outputs["Result"]
        m["base_color_factor_srgb"] = spec["base_factor"]
    L.new(col, b.inputs["Base Color"])
    orm = img(spec["orm"], "ORM", True, 0)
    sep = N.new("ShaderNodeSeparateColor")
    sep.location = (-250, 0)
    L.new(orm.outputs["Color"], sep.inputs["Color"])
    L.new(sep.outputs["Green"], b.inputs["Roughness"])
    L.new(sep.outputs["Blue"], b.inputs["Metallic"])
    g = N.new("ShaderNodeGroup")
    g.node_tree = gltf_output_group()
    g.location = (250, -450)
    L.new(sep.outputs["Red"], g.inputs["Occlusion"])
    nt = img(spec["normal"], "Normal", True, -300)
    nm = N.new("ShaderNodeNormalMap")
    nm.uv_map = UV_NAME
    nm.location = (-200, -300)
    L.new(nt.outputs["Color"], nm.inputs["Color"])
    L.new(nm.outputs["Normal"], b.inputs["Normal"])
    if name == "MAT_Shard_Blue":
        b.inputs["Emission Color"].default_value = C.hex_to_linear_rgba(SM.SHARD_HEX)
        b.inputs["Emission Strength"].default_value = SM.EMISSION[name]
    if name == "MAT_Wall_Runes":
        em = img(spec["emission"], "Emission", False, -650)
        mix = N.new("ShaderNodeMix")
        mix.data_type = "RGBA"
        mix.blend_type = "MULTIPLY"
        mix.inputs["Factor"].default_value = 1.0
        L.new(em.outputs["Color"], mix.inputs["A"])
        mix.inputs["B"].default_value = C.hex_to_linear_rgba(SM.SHARD_HEX)
        L.new(mix.outputs["Result"], b.inputs["Emission Color"])
        b.inputs["Emission Strength"].default_value = SM.EMISSION[name]
        m["emission_strength"] = SM.EMISSION[name]
    m["textures"] = {"albedo": spec["albedo"], "orm": spec["orm"], "normal": spec["normal"]}
    m["uv"] = f"{UV_NAME}: proyeccion planar en mundo, escala {spec['uv_scale']} (1 tile = ancho real del asset)"
    if spec["kind"] == "polyhaven":
        m["poly_haven_asset"] = spec["asset"]
        m["poly_haven_license"] = "CC0"
        m["texture_width_m"] = spec["dims"][0]
        m["hue_saturation_value"] = json.dumps(spec["hsv"])
    else:
        m["procedural"] = spec["ref"]
    return m


def rename_kit_uv(stats):
    """Las piezas del kit de muralla tienen UV local 'UVMap' (1 m = 1 tile): solo se renombra a 'UVWorld'."""
    n = 0
    for me in bpy.data.meshes:
        if len(me.uv_layers) == 1 and me.uv_layers[0].name == "UVMap":
            me.uv_layers[0].name = UV_NAME
            n += 1
    stats["uv_renamed_UVMap_to_UVWorld"] = n


# ---------------------------------------------------------------------------
# utilidades de malla
# ---------------------------------------------------------------------------
def corner_attr(me, name):
    a = me.color_attributes.get(name)
    if a is None:
        return None
    v = np.zeros(len(me.loops) * 4, dtype=np.float32)
    a.data.foreach_get("color", v)
    return v.reshape(-1, 4)[:, 0]


def face_first(me, arr):
    ls = np.zeros(len(me.polygons), dtype=np.int64)
    me.polygons.foreach_get("loop_start", ls)
    return arr[ls] if arr is not None else np.zeros(len(me.polygons), dtype=np.float32)


def face_max(me, arr):
    """Maximo por cara de un atributo por esquina."""
    nf = len(me.polygons)
    ls = np.zeros(nf, dtype=np.int64)
    lt = np.zeros(nf, dtype=np.int64)
    me.polygons.foreach_get("loop_start", ls)
    me.polygons.foreach_get("loop_total", lt)
    if arr is None:
        return np.zeros(nf, dtype=np.float32)
    return np.maximum.reduceat(arr, ls) if nf else arr


def mesh_arrays(me):
    nf, nl, nv = len(me.polygons), len(me.loops), len(me.vertices)
    ls = np.zeros(nf, dtype=np.int64)
    lt = np.zeros(nf, dtype=np.int64)
    me.polygons.foreach_get("loop_start", ls)
    me.polygons.foreach_get("loop_total", lt)
    lv = np.zeros(nl, dtype=np.int64)
    me.loops.foreach_get("vertex_index", lv)
    lf = np.repeat(np.arange(nf), lt)
    cen = np.zeros(nf * 3, dtype=np.float32)
    me.polygons.foreach_get("center", cen)
    nor = np.zeros(nf * 3, dtype=np.float32)
    me.polygons.foreach_get("normal", nor)
    return {"nf": nf, "nv": nv, "ls": ls, "lt": lt, "lv": lv, "lf": lf, "cen": cen.reshape(-1, 3),
            "nor": nor.reshape(-1, 3)}


def face_neighbors(A):
    """Vecinas por vertice compartido: lista CSR (indptr, indices)."""
    lv, lf, nv = A["lv"], A["lf"], A["nv"]
    order = np.argsort(lv, kind="stable")
    v_sorted, f_sorted = lv[order], lf[order]
    vptr = np.searchsorted(v_sorted, np.arange(nv + 1))
    nbrs = [None] * A["nf"]
    for f in range(A["nf"]):
        s = set()
        for li in range(A["ls"][f], A["ls"][f] + A["lt"][f]):
            v = lv[li]
            s.update(f_sorted[vptr[v]:vptr[v + 1]].tolist())
        s.discard(f)
        nbrs[f] = s
    return nbrs


def write_corner_mask(me, A, name, face_val, zero_faces=None):
    """Mascara por esquina = media por vertice de las caras (suave), con 0 forzado en las caras protegidas."""
    nv = A["nv"]
    acc = np.zeros(nv)
    cnt = np.zeros(nv)
    fv = face_val.astype(float)[A["lf"]]
    np.add.at(acc, A["lv"], fv)
    np.add.at(cnt, A["lv"], 1)
    vval = acc / np.maximum(cnt, 1)
    c = vval[A["lv"]]
    if zero_faces is not None:
        c[zero_faces[A["lf"]]] = 0.0
    if name in me.color_attributes:
        me.color_attributes.remove(me.color_attributes[name])
    a = me.color_attributes.new(name=name, type="BYTE_COLOR", domain="CORNER")
    flat = np.repeat(c[:, None], 4, axis=1)
    flat[:, 3] = 1.0
    a.data.foreach_set("color", flat.ravel().astype(np.float32))
    return c


def write_pack(me, chans):
    if "mask_pack" in me.color_attributes:
        me.color_attributes.remove(me.color_attributes["mask_pack"])
    a = me.color_attributes.new(name="mask_pack", type="BYTE_COLOR", domain="CORNER")
    a.data.foreach_set("color", np.stack(chans, 1).astype(np.float32).ravel())
    me.color_attributes.active_color_name = "mask_pack"
    me.color_attributes.render_color_index = me.color_attributes.find("mask_pack")


def dither(A, nbrs, mat, natural_idx, scale, seed):
    """Banda de transicion de 1-2 celdas entre materiales naturales, dentada por ruido (no una linea recta)."""
    nat = np.isin(mat, natural_idx)
    d1 = {}
    for f in np.nonzero(nat)[0]:
        m0 = mat[f]
        c = Counter(mat[g] for g in nbrs[f] if nat[g] and mat[g] != m0)
        if c:
            d1[f] = c.most_common(1)[0][0]
    d2 = {}
    for f, tgt in d1.items():
        for g in nbrs[f]:
            if nat[g] and g not in d1 and g not in d2 and mat[g] == mat[f]:
                d2[g] = tgt
    cen = A["cen"]
    n = value_noise(cen[:, 0], cen[:, 1], scale, seed) * 0.75 + 0.25 * value_noise(cen[:, 0], cen[:, 1],
                                                                                    scale / 4.0, seed + 7, 1)
    new = mat.copy()
    changed = 0
    for band, p in ((d1, DITHER_P[0]), (d2, DITHER_P[1])):
        for f, tgt in band.items():
            v = n[f] if mat[f] < tgt else 1.0 - n[f]
            if v > 1.0 - p:
                new[f] = tgt
                changed += 1
    return new, {"band1_faces": len(d1), "band2_faces": len(d2), "faces_switched": changed}


# ---------------------------------------------------------------------------
# TRN_City
# ---------------------------------------------------------------------------
def city(obj, mats, stats):
    me = obj.data
    A = mesh_arrays(me)
    nf = A["nf"]
    ret = face_max(me, corner_attr(me, "retaining_mask"))
    slab = face_max(me, corner_attr(me, "slab_ring_id"))
    trav = face_first(me, corner_attr(me, "travertine_band"))
    road = face_max(me, corner_attr(me, "road_mask"))
    ctype = np.rint(face_first(me, corner_attr(me, "cobble_type")) * 8).astype(int)
    ter = face_max(me, corner_attr(me, "terraza_id"))
    gar = face_max(me, corner_attr(me, "garden_mask"))
    cen = A["cen"]
    r = np.hypot(cen[:, 0], cen[:, 1])
    slope = np.degrees(np.arccos(np.clip(A["nor"][:, 2], -1, 1)))
    gi = obj.vertex_groups["talud"].index
    in_tal = np.zeros(A["nv"], dtype=bool)
    for v in me.vertices:
        for g in v.groups:
            if g.group == gi:
                in_tal[v.index] = True
    talf = np.ones(nf, dtype=bool)
    np.logical_and.at(talf, A["lf"], in_tal[A["lv"]])
    # clases protegidas (no se tinen nunca)
    is_ret = (ret > 0.5) & (r < C.WALL_BASE_R[1])
    is_slab = slab > 0.01
    is_canal = ctype == 7
    is_road = (road > 0.5) & ~is_slab
    is_pad = (ctype > 0) & ~is_road
    protected = is_ret | is_slab | is_canal | is_road | is_pad | (ter > 0.01) | (gar > 0.01)
    nbrs = face_neighbors(A)
    near_prot = protected.copy()
    for f in np.nonzero(protected)[0]:
        for g in nbrs[f]:
            near_prot[g] = True
    # rock_mask: pendiente >= 35 +- 7 grados (ruido), solo caras naturales sin contacto con lo protegido
    thr = ROCK_SLOPE_DEG + ROCK_SLOPE_NOISE * (2 * value_noise(cen[:, 0], cen[:, 1], ROCK_NOISE_M, SEED + 1) - 1)
    rock = (~near_prot) & (slope >= thr)
    ash = (~protected) & (talf | (r >= C.WALL_BASE_R[1])) & ~rock
    write_corner_mask(me, A, "rock_mask", rock, protected)
    write_corner_mask(me, A, "ash_mask", ash, protected)
    # asignacion por umbral
    idx = {n: i for i, n in enumerate(CITY_SLOTS)}
    mat = np.full(nf, idx["MAT_Ground_Cracked"])
    mat[ash] = idx["MAT_Ash_Gray"]
    mat[rock] = idx["MAT_Rock_Gray"]
    mat[is_road] = idx["MAT_Cobble_Concordia"]
    mat[is_road & (ctype == 2)] = idx["MAT_Stone_Repair"]
    mat[is_road & (ctype == 4)] = idx["MAT_Plaza_Slab"]
    mat[is_canal] = idx["MAT_Wall_Gray"]
    mat[is_slab] = idx["MAT_Plaza_Slab"]
    mat[is_slab & (trav > 0.5)] = idx["MAT_Plaza_Slab_Travertino"]
    mat[is_ret] = idx["MAT_Limestone_Worn"]
    # parches de remiendo en los muros de contencion (Moradas y terrazas): manchas de ~2 m
    nz = value_noise(cen[:, 0] + cen[:, 2], cen[:, 1] - cen[:, 2], RETAIN_REPAIR_M, SEED + 3, 2)
    ret_idx = np.nonzero(is_ret)[0]
    if len(ret_idx):
        cut = np.quantile(nz[ret_idx], 1.0 - RETAIN_REPAIR_FRAC)
        rep = is_ret & (nz >= cut)
        mat[rep] = idx["MAT_Stone_Repair"]
    else:
        rep = is_ret & False
    base = mat.copy()
    mat, dstats = dither(A, nbrs, mat, [idx[n] for n in CITY_NATURAL], DITHER["city"], SEED + 5)
    me.materials.clear()
    for n in CITY_SLOTS:
        me.materials.append(mats[n])
    me.polygons.foreach_set("material_index", mat.astype(np.int32))
    # COLOR_0: R retaining, G road, B rock, A ash
    lret = corner_attr(me, "retaining_mask")
    lroad = corner_attr(me, "road_mask")
    lrock = corner_attr(me, "rock_mask")
    lash = corner_attr(me, "ash_mask")
    write_pack(me, [lret, lroad, lrock, lash])
    # QA: ninguna mascara natural ni material natural en lo protegido
    nat_idx = [idx[n] for n in CITY_NATURAL]
    rock_c = face_max(me, lrock)
    ash_c = face_max(me, lash)
    qa = {"protected_faces": int(protected.sum()),
          "protected_with_rock_mask": int((protected & (rock_c > 0)).sum()),
          "protected_with_ash_mask": int((protected & (ash_c > 0)).sum()),
          "protected_with_natural_material": int((protected & np.isin(mat, nat_idx)).sum()),
          "road_faces_not_road_material": int((is_road & ~np.isin(mat, [idx["MAT_Cobble_Concordia"],
                                                                         idx["MAT_Stone_Repair"],
                                                                         idx["MAT_Plaza_Slab"]])).sum()),
          "plaza_faces_not_slab": int((is_slab & ~np.isin(mat, [idx["MAT_Plaza_Slab"],
                                                                idx["MAT_Plaza_Slab_Travertino"]])).sum()),
          "retaining_faces_not_limestone_or_repair": int((is_ret & ~np.isin(mat, [idx["MAT_Limestone_Worn"],
                                                                                   idx["MAT_Stone_Repair"]])).sum())}
    stats["city"] = {"faces": nf, "rock_faces": int(rock.sum()), "ash_faces": int(ash.sum()),
                     "rock_inside_wall": int((rock & (r < C.WALL_BASE_R[0])).sum()),
                     "rock_on_exterior_talud": int((rock & (talf | (r >= C.WALL_BASE_R[1]))).sum()),
                     "retaining_faces": int(is_ret.sum()), "retaining_repair_faces": int(rep.sum()),
                     "retaining_repair_pct": round(100.0 * rep.sum() / max(1, is_ret.sum()), 1),
                     "dither": dstats, "qa": qa,
                     "assign_threshold": {n: int((base == i).sum()) for n, i in idx.items()},
                     "assign_final": {n: int((mat == i).sum()) for n, i in idx.items()}}
    return {"rock": rock, "ash": ash, "protected": protected, "mat": mat, "slots": CITY_SLOTS, "cen": cen,
            "is_road": is_road, "is_slab": is_slab, "is_ret": is_ret}


# ---------------------------------------------------------------------------
# TRN_Exterior
# ---------------------------------------------------------------------------
def exterior(obj, mats, stats):
    me = obj.data
    A = mesh_arrays(me)
    nf = A["nf"]
    cen = A["cen"]
    r = np.hypot(cen[:, 0], cen[:, 1])
    rock = face_first(me, corner_attr(me, "rock_mask")) > 0.5
    dune = face_first(me, corner_attr(me, "dune_mask")) > 0.5
    nbrs = face_neighbors(A)
    # foso: depresion real Z < 0 conexa con el pie del talud, r 204-224
    cand = (cen[:, 2] < 0.0) & (r <= MOAT_R[1])
    seeds = [f for f in np.nonzero(cand & (r < 214.0))[0]]
    moat = np.zeros(nf, dtype=bool)
    moat[seeds] = True
    stack = list(seeds)
    while stack:
        f = stack.pop()
        for g in nbrs[f]:
            if cand[g] and not moat[g]:
                moat[g] = True
                stack.append(g)
    write_corner_mask(me, A, "moat_mask", moat)
    idx = {n: i for i, n in enumerate(EXT_SLOTS)}
    mat = np.full(nf, idx["MAT_Ash_Ground"])
    mat[dune | moat] = idx["MAT_Ash_Gray"]
    mat[rock] = idx["MAT_Rock_Gray"]
    base = mat.copy()
    mat, dstats = dither(A, nbrs, mat, list(idx.values()), DITHER["exterior"], SEED + 9)
    me.materials.clear()
    for n in EXT_SLOTS:
        me.materials.append(mats[n])
    me.polygons.foreach_set("material_index", mat.astype(np.int32))
    # COLOR_0: R ash_dark, G dune|moat (grava MAT_Ash_Gray), B rock, A ash
    lash = corner_attr(me, "ash_mask")
    ldark = corner_attr(me, "ash_dark_mask")
    lrock = corner_attr(me, "rock_mask")
    ldune = corner_attr(me, "dune_mask")
    lmoat = corner_attr(me, "moat_mask")
    write_pack(me, [ldark, np.maximum(ldune, lmoat), lrock, lash])
    stats["exterior"] = {"faces": nf, "moat_faces": int(moat.sum()),
                         "moat_r_range": [round(float(r[moat].min()), 1), round(float(r[moat].max()), 1)] if moat.any() else None,
                         "moat_z_min": round(float(cen[moat, 2].min()), 2) if moat.any() else None,
                         "dune_faces": int(dune.sum()), "rock_faces": int(rock.sum()), "dither": dstats,
                         "assign_threshold": {n: int((base == i).sum()) for n, i in idx.items()},
                         "assign_final": {n: int((mat == i).sum()) for n, i in idx.items()}}
    return {"moat": moat, "mat": mat, "cen": cen}


# ---------------------------------------------------------------------------
def library(col_name="MATERIAL_LIBRARY"):
    """Esfera de 1.6 m sobre un plano de 4 x 4 m por material (UV de mundo, como en el juego)."""
    col = bpy.data.collections.get(col_name)
    if col is None:
        col = bpy.data.collections.new(col_name)
        bpy.context.scene.collection.children.link(col)
    for o in list(col.objects):
        me = o.data
        bpy.data.objects.remove(o)
        if me and me.users == 0:
            bpy.data.meshes.remove(me)
    import stage09_apply as AP9
    objs, cells = [], []
    for i, n in enumerate(MATERIALS):
        cx, cy = 1000 + (i % 5) * 7.0, 1000 - (i // 5) * 7.0
        bm = bmesh.new()
        bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=2.0)
        me = bpy.data.meshes.new(f"MATLIB_{n}_Plane")
        bm.to_mesh(me)
        bm.free()
        p = bpy.data.objects.new(f"MATLIB_{n}_Plane", me)
        p.location = (cx, cy, 0.0)
        bm = bmesh.new()
        bmesh.ops.create_uvsphere(bm, u_segments=48, v_segments=24, radius=0.8)
        me2 = bpy.data.meshes.new(f"MATLIB_{n}_Sphere")
        bm.to_mesh(me2)
        bm.free()
        me2.shade_smooth()
        s = bpy.data.objects.new(f"MATLIB_{n}_Sphere", me2)
        s.location = (cx + 0.6, cy + 0.6, 0.8)
        for o in (p, s):
            col.objects.link(o)
        bpy.context.view_layer.update()
        for o in (p, s):
            AP9.world_uv(o)
            o.data.materials.append(bpy.data.materials[n])
            objs.append(o)
        cells.append((n, cx, cy))
    return col, objs, cells


def texture_memory(mat_names):
    """VRAM real de las imagenes usadas (Godot 4, VRAM Compressed escritorio, con mipmaps x4/3)."""
    rows, seen = [], set()
    for n in mat_names:
        m = bpy.data.materials[n]
        for node in m.node_tree.nodes:
            if node.type != "TEX_IMAGE" or node.image is None:
                continue
            im = node.image
            path = bpy.path.abspath(im.filepath)
            if path in seen:
                continue
            seen.add(path)
            w, h = im.size
            role = node.label
            bpp = {"Normal": 1.0}.get(role, 0.5)          # BC5 (RGTC) normal, BC1 (DXT1) albedo / ORM / emision
            rows.append({"file": os.path.relpath(path, REPO), "role": role, "px": [w, h],
                         "vram_mb": round(w * h * bpp * 4 / 3 / 2 ** 20, 2),
                         "vram_bc7_mb": round(w * h * 1.0 * 4 / 3 / 2 ** 20, 2),
                         "rgba8_mb": round(w * h * 4 * 4 / 3 / 2 ** 20, 2),
                         "disk_mb": round(os.path.getsize(path) / 2 ** 20, 2)})
    tot = {k: round(sum(r[k] for r in rows), 1) for k in ("vram_mb", "vram_bc7_mb", "rgba8_mb", "disk_mb")}
    return {"images": rows, "count": len(rows), "totals": tot,
            "assumption": "Godot 4 importacion 'VRAM Compressed' (escritorio): albedo/ORM/emision BC1 0.5 B/px, "
                          "normal BC5 1 B/px, mipmaps x4/3; vram_bc7_mb = peor caso con calidad alta (BC7) en todo"}


def build(stats):
    with open(PH.SIDECAR) as fh:
        ph = json.load(fh)
    proc = bake_procedural()
    stats["procedural_png"] = proc
    rock_choice = ph["_rock_test"]
    stats["rock_test"] = rock_choice
    old_images = {im.name for im in bpy.data.images}
    mats = {}
    for n in MATERIALS:
        spec = material_spec(n, ph, proc)
        mats[n] = build_material(n, spec)
    for im in list(bpy.data.images):
        if im.name in old_images and im.users == 0:
            bpy.data.images.remove(im)
    rename_kit_uv(stats)
    c = city(bpy.data.objects["TRN_City"], mats, stats)
    e = exterior(bpy.data.objects["TRN_Exterior"], mats, stats)
    stats["materials"] = {n: {k: v for k, v in material_spec(n, ph, proc).items() if k != "hsv"} for n in MATERIALS}
    stats["texture_memory"] = texture_memory(MATERIALS)
    return mats, c, e
