"""
CONCORDIA - etapa 10: texturas CC0 de Poly Haven para todos los materiales (salvo Shard_Blue, Wall_Runes, Water,
que siguen procedurales y se hornean a PNG).

Por material:
  textures/concordia/polyhaven_src/<asset>/<asset>_<mapa>_<res>.jpg   originales SIN TOCAR (Diffuse, nor_gl, Rough, AO,
                                                                      Metal si existe)
  textures/concordia/<MAT>/concordia_<material>_albedo.png             albedo con el ajuste Hue/Saturation/Value horneado
  textures/concordia/<MAT>/concordia_<material>_orm.png                R = AO, G = roughness (reescalada), B = metal
  (normal: se usa el nor_gl original directamente)
Ajuste de color = el de un nodo Hue/Saturation de Blender (hue 0.5 = sin giro, saturation y value multiplicadores),
aplicado en sRGB; los valores se anotan en textures/concordia/polyhaven.json para poder rehacerlo.

Uso: python stage10_polyhaven.py [--rock-test-only]
"""

import colorsys
import io
import json
import os
import sys
import urllib.request

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
OUT = os.path.join(REPO, "textures", "concordia")
SRC = os.path.join(OUT, "polyhaven_src")
SIDECAR = os.path.join(OUT, "polyhaven.json")
API = "https://api.polyhaven.com"
UA = {"User-Agent": "concordia-texture-fetch/1.0"}
SAT_CAP_DEFAULT = 0.30

# material: asset, resolucion, color medio objetivo (sRGB), tope de saturacion p95, rango de roughness
ASSETS = {
    "MAT_Limestone_Worn": ("stone_wall_02", "2k", "#C3B9A8", 0.22, (0.75, 0.93)),
    "MAT_Cobble_Concordia": ("cobblestone_floor_001", "2k", "#ADA393", 0.24, (0.72, 0.94)),
    "MAT_Plaza_Slab": ("floor_tiles_02", "2k", "#B4ADA2", 0.16, (0.76, 0.94)),
    "MAT_Plaza_Slab_Travertino": ("marble_01", "2k", "#CFC5B0", 0.22, (0.74, 0.94)),
    "MAT_Wall_Gray": ("castle_wall_slates", "2k", "#8C8A85", 0.08, (0.78, 0.95)),
    "MAT_Ground_Cracked": ("sandstone_cracks", "2k", "#A49A88", 0.24, (0.80, 0.95)),
    "MAT_Ash_Gray": ("rocks_ground_02", "2k", "#6F6F6F", 0.0, (0.82, 0.95)),
    "MAT_Ash_Ground": ("dry_ground_01", "2k", "#6F6F6F", 0.0, (0.82, 0.95)),
    "MAT_Rock_Gray": (None, "2k", "#6E6C69", 0.0, (0.80, 0.95)),          # se decide con rock_test()
    "MAT_Stone_Repair": ("rustic_stone_wall", "2k", "#8C8478", 0.20, (0.80, 0.95)),
    "MAT_Wood_Dark": ("weathered_planks", "1k", "#4A3D31", 0.35, (0.72, 0.90)),
    "MAT_Roof_Tile_Ocher": ("roof_09", "1k", "#9A7E62", 0.40, (0.70, 0.90)),
    "MAT_Iron_Black": ("metal_plate_02", "1k", "#2E2D2B", 0.08, (0.33, 0.47)),
    "MAT_Cloth": ("hessian_380", "1k", "#B8B8B8", 0.0, (0.84, 0.95)),     # textura unica de A/B/C
}
# variantes de tela: color base (glTF baseColorFactor) sobre la textura desaturada
CLOTH_VARIANTS = {"MAT_Cloth_Patch_A": "#8A6A4A", "MAT_Cloth_Patch_B": "#6E6A4E", "MAT_Cloth_Patch_C": "#A49884"}
ROCK_CANDIDATES = ("rock_boulder_dry", "rock_boulder_cracked")      # preferido, respaldo
ROCK_WIDTH_OK = (1.5, 4.0)


def get(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=180) as r:
        return r.read()


def slug(mat):
    return mat[4:].lower()


def paths(mat):
    d = os.path.join(OUT, mat)
    s = slug(mat)
    return {"dir": d, "albedo": os.path.join(d, f"concordia_{s}_albedo.png"),
            "orm": os.path.join(d, f"concordia_{s}_orm.png"), "normal": os.path.join(d, f"concordia_{s}_normal.png"),
            "emission": os.path.join(d, f"concordia_{s}_emission.png")}


def fetch(asset, res):
    """Descarga (o reutiliza) los originales. Devuelve info, {mapa: ruta}, {mapa: url}."""
    info = json.loads(get(f"{API}/info/{asset}"))
    files = json.loads(get(f"{API}/files/{asset}"))
    d = os.path.join(SRC, asset)
    os.makedirs(d, exist_ok=True)
    out, urls = {}, {}
    for key in ("Diffuse", "nor_gl", "Rough", "AO", "Metal"):
        if key not in files:
            continue
        u = files[key][res]["jpg"]["url"]
        p = os.path.join(d, f"{asset}_{key}_{res}.jpg")
        if not os.path.exists(p):
            with open(p, "wb") as fh:
                fh.write(get(u))
        out[key], urls[key] = p, u
    return info, out, urls


# ---------------------------------------------------------------------------
# Hue / Saturation / Value (como el nodo de Blender) en numpy
# ---------------------------------------------------------------------------
def rgb_to_hsv(a):
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    mx, mn = a.max(-1), a.min(-1)
    d = mx - mn
    h = np.zeros_like(mx)
    m = d > 1e-6
    rc = np.where(m, (mx - r) / np.where(m, d, 1), 0)
    gc = np.where(m, (mx - g) / np.where(m, d, 1), 0)
    bc = np.where(m, (mx - b) / np.where(m, d, 1), 0)
    h = np.where(r == mx, bc - gc, np.where(g == mx, 2.0 + rc - bc, 4.0 + gc - rc))
    h = np.where(m, (h / 6.0) % 1.0, 0.0)
    s = np.where(mx > 1e-6, d / np.maximum(mx, 1e-6), 0.0)
    return np.stack([h, s, mx], -1)


def hsv_to_rgb(hsv):
    h, s, v = hsv[..., 0], hsv[..., 1], hsv[..., 2]
    i = np.floor(h * 6.0).astype(int) % 6
    f = h * 6.0 - np.floor(h * 6.0)
    p, q, t = v * (1 - s), v * (1 - s * f), v * (1 - s * (1 - f))
    sel = [np.stack(c, -1) for c in ((v, t, p), (q, v, p), (p, v, t), (p, q, v), (t, p, v), (v, p, q))]
    out = np.zeros(hsv.shape)
    for k in range(6):
        out = np.where((i == k)[..., None], sel[k], out)
    return out


def hue_sat_val(a, hue, sat, val):
    hsv = rgb_to_hsv(a)
    hsv[..., 0] = (hsv[..., 0] + hue - 0.5) % 1.0
    hsv[..., 1] = np.clip(hsv[..., 1] * sat, 0, 1)
    hsv[..., 2] = hsv[..., 2] * val
    return np.clip(hsv_to_rgb(hsv), 0, 1)


def srgb(hexs):
    hexs = hexs.lstrip("#")
    return np.array([int(hexs[i:i + 2], 16) / 255.0 for i in (0, 2, 4)])


def to_hex(c):
    return "#" + "".join(f"{int(round(float(x) * 255)):02X}" for x in np.clip(c, 0, 1))


def sat_stats(a):
    s = rgb_to_hsv(a[::8, ::8])[..., 1].ravel()
    return float(np.percentile(s, 95)), float(s.mean())


def fit_hsv(a, target_hex, cap):
    """Busca hue/sat/val para que la media del albedo vaya al color objetivo con saturacion p95 <= cap."""
    tgt = srgb(target_hex)
    th, ts, tv = colorsys.rgb_to_hsv(*tgt)
    small = a[::4, ::4]
    hue, sat, val = 0.5, 1.0, 1.0
    for _ in range(6):
        b = hue_sat_val(small, hue, sat, val)
        mh, ms, mv = colorsys.rgb_to_hsv(*b.reshape(-1, 3).mean(0))
        if ts > 0.02 and ms > 0.01:
            dh = ((th - mh + 0.5) % 1.0) - 0.5
            hue = 0.5 + ((hue - 0.5 + dh + 0.5) % 1.0) - 0.5
        hs = rgb_to_hsv(b)[..., 1]
        mean_s, p95 = float(hs.mean()), float(np.percentile(hs, 95))
        if cap <= 0.0 or ts <= 0.005:
            sat = 0.0
        else:
            k = ts / max(mean_s, 1e-4) if mean_s > 1e-4 else 1.0
            sat = sat * k
            if p95 * k > cap:
                sat = sat * cap / max(p95 * k, 1e-4)
        b = hue_sat_val(small, hue, sat, val)
        mv2 = float(rgb_to_hsv(b)[..., 2].mean())
        val = val * (tv / max(mv2, 1e-4))
    if sat == 0.0:
        hue = 0.5                      # sin saturacion el giro de tono no tiene efecto
    return round(float(hue), 4), round(float(sat), 4), round(float(val), 4)


def remap_rough(path, r0, r1, shape):
    r = np.asarray(Image.open(path).convert("L").resize(shape[::-1], Image.BILINEAR)).astype(np.float32) / 255.0
    lo, hi = np.percentile(r, 1), np.percentile(r, 99)
    return r0 + np.clip((r - lo) / max(1e-4, hi - lo), 0, 1) * (r1 - r0)


def write_orm(path, shape, ao=None, rough=None, metal=None):
    h, w = shape
    R = ao if ao is not None else np.ones((h, w))
    G = rough if rough is not None else np.full((h, w), 0.9)
    B = metal if metal is not None else np.zeros((h, w))
    img = np.dstack([R, G, B])
    Image.fromarray((np.clip(img, 0, 1) * 255 + 0.5).astype(np.uint8)).save(path, optimize=True)


def load_gray(path, shape):
    return np.asarray(Image.open(path).convert("L").resize(shape[::-1], Image.BILINEAR)).astype(np.float32) / 255.0


# ---------------------------------------------------------------------------
# Test de roca: desaturacion, tileable 3x3, ancho real
# ---------------------------------------------------------------------------
def seam_ratio(a):
    """|salto en el borde de repeticion| / |salto medio entre columnas o filas interiores| (1.0 = sin costura)."""
    L = (a * np.array([0.2126, 0.7152, 0.0722])).sum(-1)
    dx = np.abs(np.diff(L, axis=1)).mean()
    dy = np.abs(np.diff(L, axis=0)).mean()
    ex = np.abs(L[:, 0] - L[:, -1]).mean()
    ey = np.abs(L[0, :] - L[-1, :]).mean()
    return float(ex / dx), float(ey / dy)


def rock_test(out_png):
    res = {}
    tiles = []
    for asset in ROCK_CANDIDATES:
        info, f, urls = fetch(asset, "2k")
        a = np.asarray(Image.open(f["Diffuse"]).convert("RGB")).astype(np.float32) / 255.0
        w = round(info["dimensions"][0] / 1000.0, 3)
        sx, sy = seam_ratio(a)
        p95, mean_s = sat_stats(a)
        g = hue_sat_val(a[::2, ::2], 0.5, 0.0, 1.0)[..., 0]
        # contraste tras desaturar (desviacion de luminancia) y si queda algo de color (no debe)
        contrast = float(g.std())
        crit = {"desatura_a_gris": contrast >= 0.05,
                "tileable_3x3": max(sx, sy) <= 1.5,
                "ancho_1_5_a_4_m": ROCK_WIDTH_OK[0] <= w <= ROCK_WIDTH_OK[1]}
        res[asset] = {"width_m": w, "seam_ratio_x_y": [round(sx, 2), round(sy, 2)],
                      "sat_original_p95_mean": [round(p95, 3), round(mean_s, 3)],
                      "luminance_std_desaturated": round(contrast, 3), "criteria": crit, "pass": all(crit.values())}
        t = Image.fromarray((hue_sat_val(a[::4, ::4], 0.5, 0.0, 1.0) * 255).astype(np.uint8))
        tiles.append((asset, t))
    from PIL import ImageDraw
    T = tiles[0][1].size[0]
    sheet = Image.new("RGB", (len(tiles) * (3 * T + 20), 3 * T + 30), (30, 30, 30))
    d = ImageDraw.Draw(sheet)
    for k, (asset, t) in enumerate(tiles):
        x0 = k * (3 * T + 20)
        for i in range(3):
            for j in range(3):
                sheet.paste(t, (x0 + i * T, j * T))
        r = res[asset]
        d.text((x0 + 6, 3 * T + 8), f"{asset}  {r['width_m']} m  costura {r['seam_ratio_x_y']}  "
               f"{'PASA' if r['pass'] else 'NO PASA'}", fill=(255, 255, 255))
    sheet.save(out_png)
    chosen = ROCK_CANDIDATES[0] if res[ROCK_CANDIDATES[0]]["pass"] else ROCK_CANDIDATES[1]
    return chosen, res


# ---------------------------------------------------------------------------
def process(mat, asset, res, target, cap, rough_rng):
    info, f, urls = fetch(asset, res)
    p = paths(mat)
    os.makedirs(p["dir"], exist_ok=True)
    a = np.asarray(Image.open(f["Diffuse"]).convert("RGB")).astype(np.float32) / 255.0
    hue, sat, val = fit_hsv(a, target, cap)
    alb = hue_sat_val(a, hue, sat, val)
    Image.fromarray((alb * 255 + 0.5).astype(np.uint8)).save(p["albedo"], optimize=True)
    shape = alb.shape[:2]
    ao = load_gray(f["AO"], shape) if "AO" in f else None
    rough = remap_rough(f["Rough"], rough_rng[0], rough_rng[1], shape)
    metal = load_gray(f["Metal"], shape) if "Metal" in f else None
    write_orm(p["orm"], shape, ao, rough, metal)
    dims = info.get("dimensions") or [1000, 1000]
    p95, mean_s = sat_stats(alb)
    return {"asset": asset, "id": asset, "name": info.get("name"), "url": f"https://polyhaven.com/a/{asset}",
            "authors": list((info.get("authors") or {}).keys()), "license": "CC0 (https://polyhaven.com/license)",
            "resolution": res, "pixels": list(shape[::-1]),
            "dimensions_m": [round(d / 1000.0, 3) for d in dims], "uv_scale": [round(1000.0 / d, 5) for d in dims],
            "source_files": {k: os.path.relpath(v, REPO) for k, v in f.items()},
            "source_urls": urls,
            "albedo": os.path.relpath(p["albedo"], REPO), "orm": os.path.relpath(p["orm"], REPO),
            "normal": os.path.relpath(f["nor_gl"], REPO),
            "hue_saturation_value": {"hue": hue, "saturation": sat, "value": val, "fac": 1.0,
                                     "note": "nodo Hue/Saturation de Blender (hue 0.5 = sin giro), aplicado en sRGB "
                                             "y horneado en el albedo"},
            "albedo_target_mean": target, "albedo_result_mean": to_hex(alb.reshape(-1, 3).mean(0)),
            "sat_p95_mean": [round(p95, 3), round(mean_s, 3)], "sat_cap_p95": cap,
            "orm_channels": {"R": "AO de Poly Haven" if ao is not None else "1.0", "G": f"roughness {rough_rng}",
                             "B": "Metal de Poly Haven" if metal is not None else "0.0"}}


def main():
    rock_only = "--rock-test-only" in sys.argv
    os.makedirs(SRC, exist_ok=True)
    chosen, rt = rock_test(os.path.join(REPO, "docs", "captures", "stage10_rock_test_3x3.png"))
    print("rock test:", json.dumps(rt, ensure_ascii=False), "->", chosen, flush=True)
    if rock_only:
        return
    side = {"_rock_test": {"chosen": chosen, "candidates": rt}}
    for mat, (asset, res, target, cap, rr) in ASSETS.items():
        asset = asset or chosen
        side[mat] = process(mat, asset, res, target, cap, rr)
        print(mat, asset, side[mat]["hue_saturation_value"], side[mat]["albedo_result_mean"], side[mat]["sat_p95_mean"],
              flush=True)
    cloth = side["MAT_Cloth"]
    for v, hexs in CLOTH_VARIANTS.items():
        side[v] = dict(cloth, base_color_factor_srgb=hexs, shared_texture="MAT_Cloth")
    with open(SIDECAR, "w") as fh:
        json.dump(side, fh, indent=1, ensure_ascii=False)
    return side


if __name__ == "__main__":
    main()
