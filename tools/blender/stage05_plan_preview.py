"""
CONCORDIA - etapa 05: dibujo 2D del plan (calles + parcelas por distrito) sin Blender.

Uso: python stage05_plan_preview.py --obst obst.npz --out plan.png [--json layout.json]
"""

import argparse
import json
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import concordia_const as C  # noqa: E402
import stage05_layout as L  # noqa: E402

REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
DISTRICT_RGB = {"Mercado": (214, 160, 60), "Oficios": (190, 92, 60), "Clases": (120, 130, 160),
                "Razas": (110, 150, 80), "Diagonal": (150, 150, 150), "Plaza": (200, 200, 200)}


def shade(rgb, k):
    return tuple(int(max(0, min(255, c * k))) for c in rgb)


def draw_plan(lay, obst, out, scale=3.0, title=None, crop=None):
    E = L.EXTENT
    W = int(2 * E * scale)
    img = Image.new("RGB", (W, W), (236, 232, 224))
    d = ImageDraw.Draw(img, "RGBA")

    def px(p):
        return ((p[0] + E) * scale, (E - p[1]) * scale)
    if obst is not None:
        o = np.flipud(obst)
        big = np.asarray(Image.fromarray(o).resize((W, W), Image.NEAREST))
        ov = np.zeros((big.shape[0], big.shape[1], 4), np.uint8)
        ov[big == 1] = (40, 40, 40, 255)
        ov[big == 2] = (150, 70, 60, 200)
        img.paste(Image.fromarray(ov, "RGBA"), (0, 0), Image.fromarray(ov, "RGBA"))
    for z in lay["zones"]:
        rgb = DISTRICT_RGB.get(z["district"], (160, 160, 160))
        d.polygon([px(p) for p in z["poly"]], fill=shade(rgb, 1.25) + (150,), outline=shade(rgb, 0.6) + (255,))
    for r in sorted(lay["roads"], key=lambda r: r["priority"]):
        pts = [px(p) for p in r["pts"]]
        col = (128, 122, 112) if r["type"] != "alley" else (150, 142, 128)
        if r["type"] == "alley" and r.get("blind"):
            col = (170, 110, 100)
        for a, b, ha, hb in zip(pts, pts[1:], r["halfw"], r["halfw"][1:]):
            w = int(max(1, (ha + hb) * scale))
            d.line([a, b], fill=col, width=w)
        for p, h in zip(pts, r["halfw"]):
            d.ellipse([p[0] - h * scale, p[1] - h * scale, p[0] + h * scale, p[1] + h * scale], fill=col)
    for pz in lay["plazas"]:
        if pz["type"] == "portal_plaza":
            continue
        col = (178, 170, 156) if pz["type"] != "stair_link" else (90, 90, 90)
        d.polygon([px(p) for p in pz["poly"]], fill=col, outline=(90, 85, 80))
    for z in lay["zones"]:
        if z["type"] in ("training_dummies",):
            d.polygon([px(p) for p in z["poly"]], fill=(165, 130, 90, 170))
    for pa in lay["parcels"]:
        rgb = DISTRICT_RGB[pa["district"]]
        fill = shade(rgb, 0.85) if pa["interior"] else shade(rgb, 1.2)
        d.polygon([px(p) for p in pa["poly"]], fill=fill, outline=shade(rgb, 0.45))
        dx, dy = px(pa["door"])
        d.ellipse([dx - 2, dy - 2, dx + 2, dy + 2], fill=(20, 20, 20))
    for pt in lay.get("patches", []):
        d.polygon([px(p) for p in pt["poly"]], fill=(95, 95, 120))
    for rt in lay.get("ruts", []):
        d.line([px(p) for p in rt["pts"]], fill=(90, 70, 50), width=1)
    if title:
        f = ImageFont.truetype("DejaVuSans-Bold.ttf", 22)
        d.rectangle([0, 0, W, 34], fill=(0, 0, 0))
        d.text((10, 5), title, fill=(255, 255, 255), font=f)
    if crop:
        img = img.crop(crop)
    img.save(out)
    return img


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--obst", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--json")
    a = ap.parse_args()
    obst = np.load(a.obst)["codes"]
    with open(os.path.join(REPO, "docs", "reports", "stage02_terrain.json")) as fh:
        stairs = json.load(fh)["structures"]["stairs"]
    lay, rep, _P = L.plan(obst, 0.5, stairs)
    draw_plan(lay, obst, a.out, title="CONCORDIA - plan etapa 05 (preview)")
    print(json.dumps(rep, indent=1, ensure_ascii=False, default=str)[:6000])
    if a.json:
        with open(a.json, "w") as fh:
            json.dump(lay, fh, default=str)


if __name__ == "__main__":
    main()
