"""
CONCORDIA - texturas procedurales tileables para el kit de muralla (sin red: Poly Haven
esta bloqueado en este entorno). Se pueden sustituir por las CC0 de Poly Haven
(Stone Wall 02, Rock Boulder Cracked...) sin tocar la geometria: mismas UV (1 UV = 2 m).

Genera en textures/wall/ (PNG, normal en convencion OpenGL, Y+ como Godot):
  T_Granite_Courses_albedo/normal   sillares de granito en hiladas de 0.5 m (Avila), bisel 3 cm
  T_Patch_Stone_albedo/normal       piedra de remiendo: mamposteria mas pequena y clara
  T_Slate_albedo/normal             pizarra (Carcassonne)
  T_TileOchre_albedo                teja ocre desgastada (parches de tejado)
  T_Wood_Dark_albedo                madera oscura
  T_Runes_emission                  tira de runas (mascara de emision), 0.64 x 0.08 m por tile
"""

import os
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
OUT = os.path.join(REPO, "textures", "wall")
SEED = 21
TILE_M = 2.0                   # metros por tile (1 UV = 2 m)


def srgb(hexs):
    h = hexs.lstrip("#")
    return np.array([int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4)])


def tile_noise(rng, n, scale_px):
    """Ruido suave tileable (filtro gaussiano en frecuencia)."""
    w = rng.standard_normal((n, n))
    f = np.fft.fftfreq(n)
    fx, fy = np.meshgrid(f, f)
    g = np.exp(-(fx ** 2 + fy ** 2) * (np.pi * scale_px) ** 2)
    out = np.real(np.fft.ifft2(np.fft.fft2(w) * g))
    out -= out.min()
    return out / max(out.max(), 1e-9)


def normal_from_height(h, strength):
    dx = (np.roll(h, -1, axis=1) - np.roll(h, 1, axis=1)) * 0.5
    dy = (np.roll(h, -1, axis=0) - np.roll(h, 1, axis=0)) * 0.5
    nx = -dx * strength
    ny = dy * strength                     # OpenGL: +Y arriba (filas crecen hacia abajo)
    nz = np.ones_like(h)
    ln = np.sqrt(nx ** 2 + ny ** 2 + nz ** 2)
    n = np.stack([nx / ln, ny / ln, nz / ln], axis=-1)
    return ((n * 0.5 + 0.5) * 255).astype(np.uint8)


def save(arr, name):
    os.makedirs(OUT, exist_ok=True)
    p = os.path.join(OUT, name + ".png")
    Image.fromarray(arr).save(p, optimize=True)
    return p


def ashlar(n, courses, len_range, mortar_m, bevel_m, base_hex, tint_var, rng, speck=0.06):
    """Sillares por hiladas. Devuelve albedo (uint8) y altura (float)."""
    px = n / TILE_M
    h = np.zeros((n, n))
    alb = np.zeros((n, n, 3))
    base = srgb(base_hex)
    ch = n // courses
    mort = mortar_m * px
    bev = bevel_m * px
    yy = np.arange(ch)[:, None]
    for c in range(courses):
        lens = []
        while sum(lens) < TILE_M - len_range[1]:
            lens.append(rng.uniform(*len_range))
        lens.append(TILE_M - sum(lens))
        if lens[-1] < len_range[0] * 0.6:
            lens[-2] += lens[-1]
            lens.pop()
        offs = rng.uniform(0, TILE_M)
        x0 = offs
        for L in lens:
            a = int(round(x0 * px))
            w = int(round(L * px))
            cols = (np.arange(a, a + w) % n)
            xx = np.arange(w)[None, :]
            # distancia al borde del sillar (px) -> mortero + bisel
            X = np.broadcast_to(xx, (ch, w))
            Y = np.broadcast_to(yy, (ch, w))
            d = np.minimum(np.minimum(X, w - 1 - X), np.minimum(Y, ch - 1 - Y))
            prof = np.clip((d - mort / 2) / max(bev, 1), 0, 1)
            block_h = 0.85 + 0.15 * rng.random()
            tint = base * (1 + rng.uniform(-tint_var, tint_var)) * (1 + rng.uniform(-0.03, 0.03, 3))
            rows = slice(c * ch, (c + 1) * ch)
            h[rows, cols] = np.maximum(h[rows, cols], prof * block_h)
            alb[rows, cols] = np.where((prof > 0)[..., None], tint, base * 0.55)
            x0 += L
    n1 = tile_noise(rng, n, 6)
    n2 = rng.random((n, n))
    alb *= (0.9 + 0.2 * n1)[..., None]
    alb *= (1 - speck + 2 * speck * n2)[..., None]
    h = h + 0.05 * n1
    return (np.clip(alb, 0, 1) * 255).astype(np.uint8), h


def runes(w, hgt, rng):
    img = np.zeros((hgt, w), dtype=np.float32)
    glyph_w = hgt // 2
    from PIL import ImageDraw
    im = Image.fromarray(np.zeros((hgt, w), dtype=np.uint8))
    d = ImageDraw.Draw(im)
    lw = max(3, hgt // 16)
    for g in range(w // glyph_w):
        x0 = g * glyph_w + glyph_w * 0.25
        x1 = g * glyph_w + glyph_w * 0.75
        y0, y1 = hgt * 0.15, hgt * 0.85
        xm = (x0 + x1) / 2
        d.line([(xm, y0), (xm, y1)], fill=255, width=lw)            # estave
        for _ in range(rng.integers(1, 4)):
            ya = rng.uniform(y0, y1 - (y1 - y0) * 0.3)
            side = rng.choice([-1, 1])
            xe = xm + side * (x1 - x0) / 2
            d.line([(xm, ya), (xe, ya + rng.uniform(0.15, 0.35) * (y1 - y0))], fill=255, width=lw)
    img = np.asarray(im, dtype=np.uint8)
    return np.stack([img] * 3, axis=-1)


def main():
    rng = np.random.default_rng(SEED)
    out = {}
    a, h = ashlar(1024, 4, (0.55, 1.2), 0.015, 0.03, "#857F76", 0.06, rng)
    out["granite_albedo"] = save(a, "T_Granite_Courses_albedo")
    out["granite_normal"] = save(normal_from_height(h, 6.0), "T_Granite_Courses_normal")
    a, h = ashlar(512, 7, (0.18, 0.45), 0.02, 0.03, "#ADA38F", 0.10, rng, speck=0.04)
    out["patch_albedo"] = save(a, "T_Patch_Stone_albedo")
    out["patch_normal"] = save(normal_from_height(h, 4.0), "T_Patch_Stone_normal")
    a, h = ashlar(512, 10, (0.25, 0.35), 0.012, 0.01, "#3E4046", 0.08, rng, speck=0.02)
    out["slate_albedo"] = save(a, "T_Slate_albedo")
    out["slate_normal"] = save(normal_from_height(h, 3.0), "T_Slate_normal")
    a, _h = ashlar(512, 8, (0.22, 0.30), 0.02, 0.02, "#A06E3E", 0.12, rng, speck=0.03)
    out["tile_albedo"] = save(a, "T_TileOchre_albedo")
    n = 512
    grain = tile_noise(rng, n, 2)
    stripes = (np.sin(np.linspace(0, 2 * np.pi * 24, n))[None, :] * 0.5 + 0.5) * 0.15
    wood = srgb("#4A3626")[None, None, :] * (0.8 + 0.25 * grain[..., None] + stripes[..., None])
    out["wood_albedo"] = save((np.clip(wood, 0, 1) * 255).astype(np.uint8), "T_Wood_Dark_albedo")
    out["runes_emission"] = save(runes(1024, 128, rng), "T_Runes_emission")
    for k, v in out.items():
        print(k, os.path.relpath(v, REPO), os.path.getsize(v))
    return out


if __name__ == "__main__":
    sys.exit(0 if main() else 1)
