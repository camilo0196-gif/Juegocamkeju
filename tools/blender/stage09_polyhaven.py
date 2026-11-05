"""
CONCORDIA - etapa 09: texturas CC0 de Poly Haven (2K, Normal GL) en lugar de las procedurales.

Descarga Diffuse / nor_gl / Rough y las deja en textures/concordia/<MAT>/T_<..>_{Albedo,Normal,Roughness}.jpg
(misma convencion: el material no cambia). Ajustes para la paleta de Concordia:
  - albedo: desaturado / teñido hacia el color objetivo del material (sin colores saturados; ceniza y roca
    exterior en gris puro)
  - roughness: reescalada al rango del material (0.70-0.95)
  - normal GL: sin cambios
Escala: cada textura cubre 'dimensions' m reales (API de Poly Haven); se guarda en polyhaven.json y el material
usa un nodo Mapping (KHR_texture_transform en glTF) para que 1 m de mundo = 1 m de textura.
Licencia: CC0 (polyhaven.com/license).
"""

import io
import json
import os
import sys
import urllib.request

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import stage09_materials as SM  # noqa: E402

REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
API = "https://api.polyhaven.com"
RES = "2k"
# material: (asset id, color objetivo de la media del albedo, mezcla hacia gris 0..1)
ASSETS = {
    "MAT_Cobble_Concordia": ("cobblestone_floor_001", "#ADA393", 0.55),
    "MAT_Ground_Cracked": ("sandstone_cracks", "#A49A88", 0.6),
    "MAT_Rock_Gray": ("rock_boulder_cracked", "#6E6C69", 1.0),
    "MAT_Ash_Gray": ("rocks_ground_02", "#6F6F6F", 1.0),
    "MAT_Limestone_Worn": ("stone_wall_02", "#C3B9A8", 0.6),
}
SIDECAR = os.path.join(SM.OUT, "polyhaven.json")


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "concordia-texture-fetch/1.0"})
    with urllib.request.urlopen(req, timeout=120) as r:
        return r.read()


def fetch(asset):
    info = json.loads(get(f"{API}/info/{asset}"))
    files = json.loads(get(f"{API}/files/{asset}"))
    out = {}
    for key in ("Diffuse", "nor_gl", "Rough"):
        u = files[key][RES]["jpg"]["url"]
        out[key] = Image.open(io.BytesIO(get(u)))
        out[key + "_url"] = u
    return info, out


def adjust_albedo(img, target_hex, gray_mix):
    a = np.asarray(img.convert("RGB")).astype(np.float32) / 255.0
    lum = (a * np.array([0.2126, 0.7152, 0.0722])).sum(-1, keepdims=True)
    a = a * (1 - gray_mix) + lum * gray_mix
    tgt = SM.ML.srgb(target_hex)
    a = a * (tgt / np.maximum(a.reshape(-1, 3).mean(0), 1e-4))     # media -> color objetivo
    return np.clip(a, 0, 1)


def adjust_rough(img, r0, r1):
    r = np.asarray(img.convert("L")).astype(np.float32) / 255.0
    lo, hi = np.percentile(r, 1), np.percentile(r, 99)
    r = np.clip((r - lo) / max(1e-4, hi - lo), 0, 1)
    return r0 + r * (r1 - r0)


def main():
    side = {}
    for mat, (asset, tgt, gmix) in ASSETS.items():
        info, f = fetch(asset)
        p = SM.tex_paths(mat)
        os.makedirs(os.path.dirname(p["Albedo"]), exist_ok=True)
        alb = adjust_albedo(f["Diffuse"], tgt, gmix)
        sat_cap = SM.SAT_CAP.get(mat, SM.SAT_DEFAULT)
        alb = SM.cap_saturation(alb, sat_cap)
        Image.fromarray((alb * 255).astype(np.uint8)).save(p["Albedo"], quality=93)
        f["nor_gl"].convert("RGB").save(p["Normal"], quality=95)
        r0, r1 = SM.MATS[mat][2]
        rough = adjust_rough(f["Rough"], r0, r1)
        Image.fromarray((rough * 255).astype(np.uint8), "L").save(p["Roughness"], quality=93)
        dims = info.get("dimensions") or [1000, 1000]
        side[mat] = {"asset": asset, "name": info.get("name"), "authors": info.get("authors"), "license": "CC0",
                     "resolution": f["Diffuse"].size, "dimensions_m": [round(d / 1000.0, 3) for d in dims],
                     "uv_scale": [round(1000.0 / d, 5) for d in dims],
                     "files": {k: f[k + "_url"] for k in ("Diffuse", "nor_gl", "Rough")},
                     "albedo_target": tgt, "gray_mix": gmix, "roughness": [r0, r1],
                     "sat_p95_mean": [round(v, 3) for v in SM.saturation(alb)]}
        print(mat, side[mat]["dimensions_m"], side[mat]["sat_p95_mean"], flush=True)
    with open(SIDECAR, "w") as fh:
        json.dump(side, fh, indent=1, ensure_ascii=False)
    return side


if __name__ == "__main__":
    main()
