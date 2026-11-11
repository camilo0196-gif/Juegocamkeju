"""
CONCORDIA - PJ2: atlas 1K compartido por la ropa del Sanador y el cabello (MAT_Sanador_Atlas).
  uv_pack(objs)       UV por objeto (smart project) reescalado a metros (pelo x1,5) y empaquetado conjunto: densidad
                      de texel uniforme; los patrones usan atributos (pu, pv, pa, pb), no la orientacion del UV
  rasterize(objs)     clase, objeto, posicion, atributos de patron y AO por texel (relleno de triangulos en UV)
  paint(...)          albedo (RGBA, alfa = recorte del pelo), normal (OpenGL) desde un mapa de alturas, ORM y emision
                      (solo el cristal): lino crema-gris con remiendos cosidos y bordado de hojas en las orillas, lana
                      verde-gris, cuero, vendas, vidrio con tintura, corcho, hierro, cordon, pelo ceniza con mechones,
                      trenza, cristal #8FD0FF
  atlas_material()    Principled + alfa recortada (Round -> glTF MASK) + emision 1,0 + ORM (grupo glTF Material Output)
Paleta: saturacion <= 0,345 en todo salvo el cristal (tono 201, dentro de 185-215).
"""

import math
import os

import bpy
import numpy as np

import pj2_geo as G

RES = 1024
SRGB = {
    G.LINEN: "#BDB6A6", G.WOOL: "#6E7468", G.LEATHER: "#6B5A4B", G.BOOT: "#584A3E", G.WRAP: "#A19A8B",
    G.GLASS: "#A9B4AD", G.METAL: "#6E6C67", G.CRYSTAL: "#8FD0FF", G.HAIR: "#BAB7AE", G.CORD: "#5C5145",
    G.BRAID: "#B3B0A7", G.HAIRCAP: "#B5B2A9", G.CORK: "#8C7A63", G.LIQUID: "#5E6650",
}
ROUGH = {G.LINEN: 0.86, G.WOOL: 0.95, G.LEATHER: 0.62, G.BOOT: 0.58, G.WRAP: 0.9, G.GLASS: 0.18, G.METAL: 0.45,
         G.CRYSTAL: 0.12, G.HAIR: 0.55, G.CORD: 0.8, G.BRAID: 0.55, G.HAIRCAP: 0.55, G.CORK: 0.85, G.LIQUID: 0.2}
METAL_V = {G.METAL: 0.75}
PATCH_A, PATCH_B, STITCH = "#A69D8B", "#C9C3B4", "#6E675A"
EMB_LEAF, EMB_LEAF2, EMB_LINE = "#7D8871", "#9A8C6C", "#8C8573"
WOOL_EMB = "#9D9C89"


def hx(h):
    return np.array([int(h[i:i + 2], 16) / 255 for i in (1, 3, 5)], dtype=np.float32)


# ---------------------------------------------------------------------------------------------------------- UV
def uv_pack(objs, hair_scale=1.8, margin=0.004):
    for o in objs:
        me = o.data
        if not me.uv_layers:
            me.uv_layers.new(name="UVMap")
        bpy.ops.object.select_all(action="DESELECT")
        o.select_set(True)
        bpy.context.view_layer.objects.active = o
        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.select_all(action="SELECT")
        bpy.ops.uv.smart_project(angle_limit=math.radians(60), island_margin=0.0, scale_to_bounds=False)
        bpy.ops.object.mode_set(mode="OBJECT")
        # a metros
        a3 = sum(p.area for p in me.polygons)
        uv = me.uv_layers.active.data
        a2 = 0.0
        for p in me.polygons:
            pts = [uv[li].uv for li in p.loop_indices]
            a2 += abs(sum(pts[i].x * pts[i - 1].y - pts[i - 1].x * pts[i].y for i in range(len(pts)))) / 2
        s = math.sqrt(a3 / max(a2, 1e-9)) * (hair_scale if o.name.startswith("Hair") else 1.0)
        for d in uv:
            d.uv = d.uv * s
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.select_all(action="SELECT")
    bpy.ops.uv.pack_islands(rotate=True, scale=True, margin_method="FRACTION", margin=margin, shape_method="CONCAVE")
    bpy.ops.object.mode_set(mode="OBJECT")
    # densidad resultante (texeles por metro)
    out = {}
    for o in objs:
        me = o.data
        uv = me.uv_layers.active.data
        a3 = sum(p.area for p in me.polygons)
        a2 = 0.0
        for p in me.polygons:
            pts = [uv[li].uv for li in p.loop_indices]
            a2 += abs(sum(pts[i].x * pts[i - 1].y - pts[i - 1].x * pts[i].y for i in range(len(pts)))) / 2
        out[o.name] = {"texeles_por_metro": round(math.sqrt(a2 / a3) * RES, 1), "area_m2": round(a3, 3),
                       "ocupacion_atlas": round(a2, 4)}
    return out


# --------------------------------------------------------------------------------------------------- raster
def rasterize(objs, ao_by_obj):
    """Rellena por texel: obj (0 = vacio), cls, pu, pv, pa, pb, ao, z (altura del mundo)."""
    H = W = RES
    obj = np.zeros((H, W), np.int16)
    cls = np.zeros((H, W), np.int16)
    ch = {k: np.zeros((H, W), np.float32) for k in ("pu", "pv", "pa", "pb", "ao", "z")}
    for oi, o in enumerate(objs, start=1):
        me = o.data
        me.calc_loop_triangles()
        uv = me.uv_layers.active.data
        at = {k: me.attributes[k].data for k in ("pu", "pv", "pa", "pb")}
        cl = me.attributes["cls"].data
        ao = ao_by_obj[o.name]
        for lt in me.loop_triangles:
            L = lt.loops
            P = np.array([[uv[l].uv.x * W - 0.5, (1 - uv[l].uv.y) * H - 0.5] for l in L], np.float64)
            x0, x1 = int(max(0, math.floor(P[:, 0].min()))), int(min(W - 1, math.ceil(P[:, 0].max())))
            y0, y1 = int(max(0, math.floor(P[:, 1].min()))), int(min(H - 1, math.ceil(P[:, 1].max())))
            if x1 < x0 or y1 < y0:
                continue
            ys, xs = np.mgrid[y0:y1 + 1, x0:x1 + 1]
            (ax, ay), (bx, by), (cx, cy) = P
            den = (by - cy) * (ax - cx) + (cx - bx) * (ay - cy)
            if abs(den) < 1e-12:
                continue
            w0 = ((by - cy) * (xs - cx) + (cx - bx) * (ys - cy)) / den
            w1 = ((cy - ay) * (xs - cx) + (ax - cx) * (ys - cy)) / den
            w2 = 1 - w0 - w1
            m = (w0 >= -1e-4) & (w1 >= -1e-4) & (w2 >= -1e-4)
            if not m.any():
                continue
            yy, xx = ys[m], xs[m]
            ww = np.stack([w0[m], w1[m], w2[m]], 1)
            obj[yy, xx] = oi
            cls[yy, xx] = cl[lt.polygon_index].value
            for k in ("pu", "pv", "pa", "pb"):
                vals = np.array([at[k][l].value for l in L])
                ch[k][yy, xx] = ww @ vals
            vids = lt.vertices
            ch["ao"][yy, xx] = ww @ np.array([ao[v] for v in vids])
            ch["z"][yy, xx] = ww @ np.array([me.vertices[v].co.z for v in vids])
    return obj, cls, ch


def dilate(arrs, mask, iters=6):
    """Extiende los valores de los texeles ocupados a sus vecinos vacios (margen de las islas)."""
    ok = mask.copy()
    for _ in range(iters):
        grow = ~ok & (np.roll(ok, 1, 0) | np.roll(ok, -1, 0) | np.roll(ok, 1, 1) | np.roll(ok, -1, 1))
        if not grow.any():
            break
        for a in arrs:
            src = None
            for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                sh_ok = np.roll(np.roll(ok, dy, 0), dx, 1)
                sh = np.roll(np.roll(a, dy, 0), dx, 1)
                take = grow & sh_ok
                if src is None:
                    src = take.copy()
                    a[take] = sh[take]
                else:
                    t2 = take & ~src
                    a[t2] = sh[t2]
                    src |= take
        ok |= grow
    return ok


# ---------------------------------------------------------------------------------------------------- ruido
def hash2(ix, iy, seed):
    h = (ix * 374761393 + iy * 668265263 + seed * 2147483647) & 0xFFFFFFFF
    h = ((h ^ (h >> 13)) * 1274126177) & 0xFFFFFFFF
    return ((h ^ (h >> 16)) & 0xFFFF) / 65535.0


def vnoise(x, y, seed=0):
    ix, iy = np.floor(x).astype(np.int64), np.floor(y).astype(np.int64)
    fx, fy = x - ix, y - iy
    sx, sy = fx * fx * (3 - 2 * fx), fy * fy * (3 - 2 * fy)
    a, b = hash2(ix, iy, seed), hash2(ix + 1, iy, seed)
    c, d = hash2(ix, iy + 1, seed), hash2(ix + 1, iy + 1, seed)
    return (a * (1 - sx) + b * sx) * (1 - sy) + (c * (1 - sx) + d * sx) * sy


def fbm(x, y, seed=0, oct=4):
    s, a, f, n = 0.0, 0.5, 1.0, 0.0
    for o in range(oct):
        s = s + a * vnoise(x * f, y * f, seed + o * 17)
        n += a
        a *= 0.5
        f *= 2.03
    return s / n


def texel_noise(scale, seed, oct=3):
    yy, xx = np.mgrid[0:RES, 0:RES].astype(np.float32)
    return fbm(xx / scale, yy / scale, seed, oct)


# --------------------------------------------------------------------------------------------------- pintado
def leaf_border(pu, pv, band=(0.014, 0.064)):
    """Bordado de hojas sencillo junto a una orilla: dos lineas de hilo y hojas alternas a lo largo de pu (5 cm)."""
    v0, v1 = band
    mid = (v0 + v1) / 2
    line = (np.abs(pv - v0) < 0.0028) | (np.abs(pv - v1) < 0.0028)
    stem = np.abs(pv - mid) < 0.0016
    per = 0.07
    k = np.floor(pu / per)
    lu = pu - (k + 0.5) * per
    lv = pv - mid
    ang = np.where(k % 2 == 0, 0.7, -0.7)
    ca, sa = np.cos(ang), np.sin(ang)
    x = lu * ca + lv * sa
    y = -lu * sa + lv * ca
    leaf = (x / 0.016) ** 2 + (y / 0.0075) ** 2 < 1.0
    leaf2 = ((lu - per / 2 * 0.0) / 0.004) ** 2 + ((lv) / 0.004) ** 2 < 1.0
    inband = (pv > v0 - 0.004) & (pv < v1 + 0.004)
    return line & inband, (stem & inband), (leaf & inband), (leaf2 & inband), k


def strands(pu, pv, freq, seed):
    """Mechones: lineas de pu constante (ruido 1D en pu, estirado en pv)."""
    a = fbm(pu * freq, pv * 3.0, seed, 3)
    b = vnoise(pu * freq * 3.1, pv * 1.5, seed + 5)
    return 0.65 * a + 0.35 * b


def paint(obj, cls, ch, out_dir, prefix, tpm=250.0, seed=11):
    rng = np.random.default_rng(seed)
    occ = obj > 0
    rep = {}
    pu, pv, pa, pb, ao = ch["pu"], ch["pv"], ch["pa"], ch["pb"], ch["ao"]
    col = np.zeros((RES, RES, 3), np.float32)
    for c, h in SRGB.items():
        col[cls == c] = hx(h)
    alpha = np.ones((RES, RES), np.float32)
    height = np.zeros((RES, RES), np.float32)
    n_lo, n_mid, n_hi = texel_noise(60, seed), texel_noise(14, seed + 1), texel_noise(2.5, seed + 2, 2)
    lin = cls == G.LINEN
    wool = cls == G.WOOL
    leath = np.isin(cls, (G.LEATHER, G.BOOT))
    # variacion general
    col *= (0.93 + 0.14 * n_lo)[..., None]
    # lino: trama fina + remiendos cosidos
    col[lin] *= (0.96 + 0.08 * n_hi[lin])[:, None]
    height[lin] += 0.25 * n_hi[lin]
    patches = 0
    lin_idx = np.argwhere(lin)
    tries = 0
    while patches < 12 and tries < 400 and len(lin_idx):
        tries += 1
        y, x = lin_idx[rng.integers(len(lin_idx))]
        w, h = int(rng.uniform(0.06, 0.11) * tpm), int(rng.uniform(0.05, 0.09) * tpm)   # remiendos de 5-11 cm
        y0, x0 = y - h // 2, x - w // 2
        if y0 < 0 or x0 < 0 or y0 + h >= RES or x0 + w >= RES:
            continue
        win_o = obj[y0:y0 + h, x0:x0 + w]
        win_c = cls[y0:y0 + h, x0:x0 + w]
        if not ((win_c == G.LINEN).all() and (win_o == win_o[0, 0]).all()):
            continue
        if (pv[y0:y0 + h, x0:x0 + w] < 0.09).any():               # no sobre el bordado
            continue
        tone = hx(PATCH_A if patches % 2 == 0 else PATCH_B)
        sl = (slice(y0, y0 + h), slice(x0, x0 + w))
        col[sl] = tone * (0.95 + 0.1 * n_hi[sl])[..., None]
        height[sl] += 0.35
        # puntadas: borde discontinuo 2 texeles por dentro
        yy, xx = np.mgrid[0:h, 0:w]
        ring = ((yy == 2) | (yy == h - 3) | (xx == 2) | (xx == w - 3)) & (((yy + xx) % 4) < 2)
        st = np.zeros((h, w, 3), np.float32) + hx(STITCH)
        sub = col[sl]
        sub[ring] = st[ring]
        col[sl] = sub
        hsub = height[sl]
        hsub[ring] -= 0.5
        height[sl] = hsub
        lin[sl] = lin[sl]
        patches += 1
    rep["remiendos"] = patches
    # bordado de hojas en las orillas (lino: dobladillos de falda y mangas; lana: borde de la esclavina)
    for mask, leafc, linec in ((lin, (EMB_LEAF, EMB_LEAF2), EMB_LINE), (wool, (WOOL_EMB, WOOL_EMB), WOOL_EMB)):
        line, stem, leaf, dot, k = leaf_border(pu, pv)
        sel = mask & (pv < 0.08)
        for m, colr, hgt in ((line, linec, 0.4), (stem, linec, 0.3)):
            mm = sel & m
            col[mm] = hx(colr)
            height[mm] += hgt
        mm = sel & leaf
        alt = (k % 2 == 0)
        col[mm & alt] = hx(leafc[0])
        col[mm & ~alt] = hx(leafc[1])
        height[mm] += 0.6
        rep.setdefault("texeles_bordado", 0)
        rep["texeles_bordado"] += int((sel & (leaf | line | stem)).sum())
    # lana: pelusa
    col[wool] *= (0.92 + 0.16 * n_mid[wool])[:, None]
    height[wool] += 0.4 * n_mid[wool]
    # cuero: grano y rozaduras
    gr = texel_noise(4, seed + 3, 2)
    col[leath] *= (0.9 + 0.2 * gr[leath])[:, None]
    scuff = (texel_noise(9, seed + 4) > 0.68) & leath
    col[scuff] = col[scuff] * 1.12
    height[leath] += 0.3 * gr[leath]
    # vendas: bandas diagonales
    wr = cls == G.WRAP
    band = np.mod(pu[wr] * 0.8 + pv[wr], 0.03) < 0.004
    c2 = col[wr]
    c2[band] *= 0.8
    col[wr] = c2
    h2 = height[wr]
    h2[band] -= 0.5
    height[wr] = h2
    # vidrio: brillo vertical; tintura oscura; corcho con poros
    gl = cls == G.GLASS
    col[gl] *= (0.9 + 0.2 * (np.mod(pa[gl], 1.0) < 0.12))[:, None]
    # pelo: mechones, raices mas oscuras, alfa recortado en los bordes de las cards
    for c, freq in ((G.HAIR, 110.0), (G.HAIRCAP, 120.0)):
        m = cls == c
        if not m.any():
            continue
        s = strands(pu[m], pv[m], freq, seed + 7)
        s = np.clip((s - 0.5) * 1.6 + 0.5, 0, 1)
        col[m] = col[m] * (0.7 + 0.45 * s)[:, None]
        height[m] += 1.0 * s
        if c == G.HAIR:
            edge = np.minimum(pa[m], 1 - pa[m])                   # 0 en el borde de la card
            tip = pb[m]
            thr = 0.35 + 0.5 * np.clip(0.18 - edge, 0, 1) / 0.18 * 0.6 + 0.25 * np.clip(tip - 0.75, 0, 1) / 0.25
            alpha[m] = (s > thr * 0.85).astype(np.float32)
            col[m] *= (0.92 + 0.08 * np.clip(tip * 2, 0, 1))[:, None]
        else:
            fr = pv[m]                                             # flequillo en la linea del pelo
            alpha[m] = np.where(fr < 0.006, (s > 0.45 - fr * 40).astype(np.float32), 1.0)
    br = cls == G.BRAID
    if br.any():
        a = np.mod(pa[br], 1.0)
        side = a < 0.5
        ph = np.mod(pv[br] / 0.026 + np.where(side, a, 1 - a) + np.where(side, 0.5, 0.0), 1.0)
        lobe = np.sin(np.pi * ph)
        s = strands(pu[br] + ph * 0.01, pv[br], 260.0, seed + 9)
        col[br] = col[br] * (0.62 + 0.38 * lobe)[:, None] * (0.85 + 0.25 * s)[:, None]
        height[br] += 1.2 * lobe + 0.3 * s
    # AO en el albedo: nada (va al ORM); recorte de saturacion (salvo el cristal)
    col = np.clip(col, 0, 1)
    mx, mn = col.max(axis=2, keepdims=True), col.min(axis=2, keepdims=True)
    sat = (mx - mn) / np.maximum(mx, 1e-6)
    lim = (cls != G.CRYSTAL)[..., None] & (sat > 0.345)
    k = np.where(lim, 0.345 / np.maximum(sat, 1e-6), 1.0)
    rep["texeles_saturacion_recortada"] = int(lim.sum())
    col = mx - (mx - col) * k
    # margen de las islas
    alpha[~occ] = 0.0
    zz = ch["z"]
    dil = dilate([col[..., 0], col[..., 1], col[..., 2], height, ao, alpha, zz], occ, iters=6)
    alpha[~dil] = 0.0
    rgba = np.dstack([col, alpha])
    # normal desde alturas, solo entre texeles del mismo objeto
    # mismo objeto y misma isla (texeles vecinos a menos de 1,5 cm de altura en el mundo)
    same_x = (obj == np.roll(obj, -1, 1)) & (np.abs(zz - np.roll(zz, -1, 1)) < 0.015)
    same_y = (obj == np.roll(obj, -1, 0)) & (np.abs(zz - np.roll(zz, -1, 0)) < 0.015)
    gx = np.where(same_x, np.roll(height, -1, 1) - height, 0.0)
    gy = np.where(same_y, np.roll(height, -1, 0) - height, 0.0)
    k_n = 0.9
    gx, gy = np.clip(gx, -0.8, 0.8), np.clip(gy, -0.8, 0.8)
    nx_, ny_ = -gx * k_n, gy * k_n                          # filas hacia abajo = -v
    nz_ = np.ones_like(nx_)
    ln = np.sqrt(nx_ ** 2 + ny_ ** 2 + nz_ ** 2)
    nrm = np.dstack([nx_ / ln, ny_ / ln, nz_ / ln]) * 0.5 + 0.5
    nrm[~dil] = (0.5, 0.5, 1.0)
    # ORM
    rough = np.zeros((RES, RES), np.float32) + 0.8
    met = np.zeros((RES, RES), np.float32)
    for c, r in ROUGH.items():
        rough[cls == c] = r
    for c, m_ in METAL_V.items():
        met[cls == c] = m_
    rough += 0.05 * (n_mid - 0.5)
    dilate([rough, met], occ, iters=6)
    orm = np.dstack([np.clip(0.25 + 0.75 * ao, 0, 1), np.clip(rough, 0, 1), met])
    em = np.zeros((RES, RES, 3), np.float32)
    em[cls == G.CRYSTAL] = hx(SRGB[G.CRYSTAL])
    from PIL import Image
    os.makedirs(out_dir, exist_ok=True)
    paths = {}

    rep["alfa_cero_dentro_de_islas_no_pelo"] = int(((alpha < 0.5) & occ & ~np.isin(cls, (G.HAIR, G.HAIRCAP))).sum())

    def save(arr, name, mode):
        p = os.path.join(out_dir, f"{prefix}_{name}.png")
        Image.fromarray((np.clip(arr, 0, 1) * 255 + 0.5).astype(np.uint8), mode).save(p)
        paths[name] = p
    save(rgba, "albedo_1k", "RGBA")
    save(nrm, "normal_1k", "RGB")
    save(orm, "orm_1k", "RGB")
    save(em, "emision_1k", "RGB")
    # comprobaciones
    cr = cls == G.CRYSTAL
    s_ok = sat[..., 0][occ & ~cr & (mx[..., 0] > 0.15)]
    rep["saturacion_max_sin_cristal"] = round(float(np.minimum(s_ok, 0.345).max()), 3) if s_ok.size else 0
    rep["texeles_ocupados"] = int(occ.sum())
    rep["texeles_cristal"] = int(cr.sum())
    rep["alfa_recortado_texeles"] = int(((alpha < 0.5) & occ).sum())
    return paths, rep


def atlas_material(paths, name="MAT_Sanador_Atlas"):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    m.use_backface_culling = False
    try:
        m.surface_render_method = "DITHERED"
    except Exception:
        pass
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    bs = nt.nodes.new("ShaderNodeBsdfPrincipled")
    nt.links.new(bs.outputs["BSDF"], out.inputs["Surface"])

    def tex(key, data):
        t = nt.nodes.new("ShaderNodeTexImage")
        t.image = bpy.data.images.load(paths[key], check_existing=True)
        t.image.colorspace_settings.name = "Non-Color" if data else "sRGB"
        return t
    ta = tex("albedo_1k", False)
    nt.links.new(ta.outputs["Color"], bs.inputs["Base Color"])
    rd = nt.nodes.new("ShaderNodeMath")
    rd.operation = "ROUND"
    nt.links.new(ta.outputs["Alpha"], rd.inputs[0])
    nt.links.new(rd.outputs[0], bs.inputs["Alpha"])
    tn = tex("normal_1k", True)
    nm = nt.nodes.new("ShaderNodeNormalMap")
    nt.links.new(tn.outputs["Color"], nm.inputs["Color"])
    nt.links.new(nm.outputs["Normal"], bs.inputs["Normal"])
    to = tex("orm_1k", True)
    sp = nt.nodes.new("ShaderNodeSeparateColor")
    nt.links.new(to.outputs["Color"], sp.inputs["Color"])
    nt.links.new(sp.outputs["Green"], bs.inputs["Roughness"])
    nt.links.new(sp.outputs["Blue"], bs.inputs["Metallic"])
    ng = bpy.data.node_groups.get("glTF Material Output")
    if ng is None:
        ng = bpy.data.node_groups.new("glTF Material Output", "ShaderNodeTree")
        ng.interface.new_socket("Occlusion", in_out="INPUT", socket_type="NodeSocketFloat")
    g = nt.nodes.new("ShaderNodeGroup")
    g.node_tree = ng
    nt.links.new(sp.outputs["Red"], g.inputs["Occlusion"])
    te = tex("emision_1k", False)
    nt.links.new(te.outputs["Color"], bs.inputs["Emission Color"])
    bs.inputs["Emission Strength"].default_value = 1.0
    return m
