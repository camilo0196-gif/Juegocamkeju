"""
CONCORDIA - etapa 09: materiales glTF (Principled + Albedo / Normal GL / Roughness) con texturas tileables
2048 x 2048 (1 m = 1 tile) horneadas por codigo en textures/concordia/<MAT>/T_<MAT>_{Albedo,Normal,Roughness}.jpg.
Referencias Poly Haven (CC0): Cobblestone Floor 001, Sandstone Cracks, Rock Boulder Cracked, Rocks Ground 02,
Stone Wall 02 (no descargables desde aqui: se generan equivalentes con la misma convencion de 3 mapas).

Reglas: roughness 0.70-0.95 (agua 0.10, hierro 0.40); sin colores saturados salvo #8FD0FF; UV 'UVWorld' por
proyeccion planar en mundo (caja por normal dominante, 1 m = 1 tile) en las mallas no instanciadas; asignacion
por mascaras: retaining_mask -> MAT_Limestone_Worn, slab_ring_id -> MAT_Plaza_Slab(_Travertino),
road_mask -> MAT_Cobble_Concordia, ash_mask -> MAT_Ash_Gray.
"""

import colorsys
import os
import sys
from math import cos, radians, sin

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import material_library as ML  # noqa: E402

REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
OUT = os.path.join(REPO, "textures", "concordia")
RES = 2048
SEED = 909
SHARD_HEX = "#8FD0FF"

_fnoise_1024 = ML.fnoise


def _fnoise_scaled(rng, n, scale_px, aniso=(1.0, 1.0)):
    return _fnoise_1024(rng, n, scale_px * n / 1024.0, aniso)


def setup_res():
    ML.N = RES
    ML.fnoise = _fnoise_scaled


# ---------------------------------------------------------------------------
# Generadores (alb 0..1 sRGB, h altura, rough)
# ---------------------------------------------------------------------------
def g_limestone(rng):
    a, h, r = ML.rubble(rng, (3, 4), "#C8BEAD", "#A39A8A", 0.07, 0.006, 0.84)
    wear = ML.fbm(rng, RES, (6, 30, 120), (0.3, 0.4, 0.3))
    pits = (rng.random((RES, RES)) < 0.003).astype(float)
    a = a * (0.9 + 0.16 * wear[..., None]) * (1 - 0.25 * pits[..., None])
    h = h * 0.8 + 0.12 * wear - 0.1 * pits
    return a, h, r


def g_cobble(rng):
    f1, f2, cid = ML.worley(rng, RES, 7, 7, jitter=0.85)
    e = f2 - f1
    prof = np.clip((e - 0.009 * RES) / (0.02 * RES), 0, 1)
    dome = np.clip(1 - (f1 / (0.085 * RES)) ** 2, 0, 1)
    nz = ML.fbm(rng, RES, (3, 12, 40), (0.4, 0.4, 0.2))
    h = prof * (0.5 + 0.5 * dome + 0.08 * nz)
    tint = ML.srgb("#B6AC9B")[None, None, :] * (1 + ML.per_cell(cid, rng, -0.12, 0.08)[..., None])
    alb = np.where((prof > 0.05)[..., None], tint * (0.85 + 0.18 * dome[..., None]) * (0.92 + 0.1 * nz[..., None]),
                   ML.srgb("#4A443C") * (0.85 + 0.25 * nz[..., None]))
    rough = np.where(prof > 0.05, 0.74 + ML.per_cell(cid, rng, -0.03, 0.05) - 0.05 * dome, 0.94)
    return alb, h, rough


def _slabs(rng, base_hex, joint_hex, var, travertine=False):
    n = RES
    yy, xx = np.mgrid[0:n, 0:n] / n
    rows = 2
    row = np.floor(yy * rows)
    u = (xx * 2 + 0.5 * (row % 2)) % 1.0
    v = (yy * rows) % 1.0
    sid = (row * 2 + np.floor(xx * 2 + 0.5 * (row % 2)) % 2).astype(int)
    jw = 0.012
    joint = np.clip(np.minimum.reduce([u, 1 - u, v, 1 - v]) / jw, 0, 1)
    nz = ML.fbm(rng, n, (4, 20, 90), (0.3, 0.4, 0.3))
    h = joint * (0.85 + 0.1 * nz) - 0.04
    tint = ML.srgb(base_hex)[None, None, :] * (1 + ML.per_cell(sid, rng, -var, var)[..., None])
    alb = tint * (0.9 + 0.14 * nz[..., None])
    if travertine:
        pores = np.clip(1 - ML.fnoise(rng, n, 1.2, aniso=(0.25, 1.0)) * 2.4, 0, 1) ** 3
        veins = 0.5 + 0.5 * np.sin(yy * 2 * np.pi * 14 + 6 * ML.fnoise(rng, n, 30))
        alb = alb * (0.93 + 0.07 * veins[..., None]) * (1 - 0.3 * pores[..., None])
        h = h - 0.12 * pores
    alb = np.where((joint < 0.6)[..., None], ML.srgb(joint_hex) * (0.9 + 0.2 * nz[..., None]), alb)
    rough = np.where(joint < 0.6, 0.94, 0.78 + 0.08 * nz)
    return alb, h, rough


def g_plaza(rng):
    return _slabs(rng, "#CBC2B0", "#8C8476", 0.05)


def g_plaza_trav(rng):
    return _slabs(rng, "#DCD3C0", "#9A917F", 0.03, travertine=True)


def g_wall_gray(rng):
    a, h, r = ML.ashlar(rng, 2, (0.30, 0.65), 0.013, 0.03, ML.srgb("#8A8884"), 0.10, 0.04, 0.28, chip=0.6)
    a = ML.granite_grain(rng, a, 0.10)
    g = a.mean(axis=-1, keepdims=True)
    a = 0.8 * g + 0.2 * a                          # gris: desatura el granito
    return a, h + 0.04 * ML.fnoise(rng, RES, 1.5), r


def g_wood(rng):
    a, h, r = ML.gen_wood(rng)
    return a * 0.92, h, r


def g_roof(rng):
    a, h, r = ML.gen_roof_tile(rng)
    g = a.mean(axis=-1, keepdims=True)
    return 0.55 * a + 0.45 * g * ML.srgb("#B0905F") / ML.srgb("#B0905F").mean(), h, r


def g_iron(rng):
    a, h, r = ML.gen_iron(rng)
    g = a.mean(axis=-1, keepdims=True)
    return 0.6 * a + 0.4 * g, h, r


def _cloth(rng, base_hex, patch_hexes):
    n = RES
    yy, xx = np.mgrid[0:n, 0:n].astype(np.float32)
    weave = 0.5 + 0.25 * np.sin(xx * 2 * np.pi / 6) * np.sign(np.sin(yy * 2 * np.pi / 12)) \
        + 0.25 * np.sin(yy * 2 * np.pi / 6) * np.sign(np.sin(xx * 2 * np.pi / 12) + 1e-6)
    nz = ML.fbm(rng, n, (3, 20, 80), (0.3, 0.4, 0.3))
    alb = ML.srgb(base_hex)[None, None, :] * (0.82 + 0.25 * nz[..., None]) * (0.9 + 0.15 * weave[..., None])
    h = 0.35 * weave + 0.2 * nz
    stitch = np.zeros((n, n), np.float32)
    k = 0
    for _ in range(7):
        w = int(rng.uniform(0.15, 0.35) * n)
        hh = int(rng.uniform(0.12, 0.3) * n)
        x0, y0 = int(rng.uniform(0, n)), int(rng.uniform(0, n))
        col = ML.srgb(patch_hexes[k % len(patch_hexes)])
        k += 1
        ys = (np.arange(y0, y0 + hh) % n)[:, None]
        xs = (np.arange(x0, x0 + w) % n)[None, :]
        alb[ys, xs] = col * (0.85 + 0.2 * nz[ys, xs, None]) * (0.9 + 0.15 * weave[ys, xs, None])
        h[ys, xs] += 0.12
        # puntadas (borde discontinuo)
        for t in range(0, w, 14):
            for yy_ in (y0 + 6, y0 + hh - 6):
                stitch[yy_ % n, (x0 + t) % n:(x0 + t) % n + 6] = 1
        for t in range(0, hh, 14):
            for xx_ in (x0 + 6, x0 + w - 6):
                stitch[(y0 + t) % n:(y0 + t) % n + 6, xx_ % n] = 1
    alb = alb * (1 - 0.45 * stitch[..., None])
    h = h - 0.15 * stitch
    rough = 0.88 + 0.05 * nz
    return alb, h, rough


def g_cloth_a(rng):
    return _cloth(rng, "#6E5D4B", ("#8A7658", "#5A4C3F", "#7D7468"))


def g_cloth_b(rng):
    return _cloth(rng, "#8A7656", ("#6E5D4B", "#9B8B70", "#5F5850"))


def g_cloth_c(rng):
    return _cloth(rng, "#77716A", ("#8A7656", "#5E5148", "#9A9286"))


def g_ash(rng):
    n = RES
    nz = ML.fbm(rng, n, (2, 8, 40, 160), (0.2, 0.3, 0.3, 0.2))
    ripple = 0.5 + 0.5 * np.sin(np.mgrid[0:n, 0:n][0] / n * 2 * np.pi * 9 + 7 * ML.fnoise(rng, n, 60))
    grit = (rng.random((n, n)) < 0.01).astype(float)
    f1, f2, cid = ML.worley(rng, n, 22, 22, jitter=0.9)
    keep = ML.per_cell(cid, rng, 0, 1) < 0.12
    pebble = np.clip(1 - f1 / (0.01 * n), 0, 1) * keep
    h = 0.5 * nz + 0.15 * ripple + 0.6 * pebble
    g = 0.42 + 0.12 * nz + 0.03 * ripple - 0.1 * grit + 0.05 * pebble
    alb = np.repeat(g[..., None], 3, -1) * (ML.srgb("#6F6F6F") / 0.44)
    rough = 0.9 + 0.04 * nz - 0.06 * pebble
    return alb, h, rough


def g_ground(rng):
    a, h, r = ML.gen_sandstone(rng)
    g = a.mean(axis=-1, keepdims=True)
    tgt = ML.srgb("#A49A88")
    return (0.35 * a + 0.65 * g * tgt / tgt.mean()) * 0.95, h, r


def g_rock(rng):
    a, h, r = ML.gen_rock(rng)
    g = a.mean(axis=-1, keepdims=True)
    return np.repeat(g, 3, -1) * 0.95, h, r


def g_repair(rng):
    return ML.rubble(rng, (5, 6), "#9C9384", "#7F786C", 0.12, 0.012, 0.86)


def g_runes(rng):
    """Piedra oscura de la ranura + mascara de glifos (filas de 8 cm, tileable en X e Y)."""
    n = RES
    a, h, r = ML.rubble(rng, (6, 10), "#5F5D59", "#4A4845", 0.05, 0.01, 0.86)
    em = np.zeros((n, n), np.float32)
    row_h = n // 12                                   # ~8.3 cm por fila
    for rr in range(12):
        y0 = rr * row_h
        x = 0
        while x < n:
            gw = int(rng.uniform(0.035, 0.06) * n)
            for _ in range(rng.integers(2, 5)):
                ax, ay = x + rng.uniform(0, gw), y0 + rng.uniform(0.2, 0.8) * row_h
                bx, by = x + rng.uniform(0, gw), y0 + rng.uniform(0.2, 0.8) * row_h
                for t in np.linspace(0, 1, 40):
                    px, py = int(ax + (bx - ax) * t) % n, int(ay + (by - ay) * t) % n
                    em[max(0, py - 2):py + 3, max(0, px - 2):px + 3] = 1.0
            x += gw + int(rng.uniform(0.01, 0.025) * n)
    return a, h - 0.2 * em, r, em


def g_shard(rng):
    n = RES
    f1, f2, cid = ML.worley(rng, n, 6, 6, jitter=0.9)
    facet = ML.per_cell(cid, rng, 0.0, 1.0)
    h = 0.5 * facet + 0.2 * (f1 / (f2 + 1e-6))
    alb = ML.srgb(SHARD_HEX)[None, None, :] * (0.9 + 0.1 * facet[..., None])
    rough = 0.7 + 0.04 * facet
    return alb, h, rough


def g_water(rng):
    n = RES
    h = ML.fbm(rng, n, (6, 25, 90), (0.3, 0.4, 0.3))
    alb = np.ones((n, n, 3)) * ML.srgb("#1A201F")
    rough = np.full((n, n), 0.10)
    return alb, h, rough


# nombre: (generador, fuerza normal, (rough_min, rough_max), metalico, ref Poly Haven / nota, uso)
MATS = {
    "MAT_Limestone_Worn": (g_limestone, 5.0, (0.75, 0.93), 0.0, "Stone Wall 02 (caliza)", "calles, muros de contencion, edificios"),
    "MAT_Cobble_Concordia": (g_cobble, 6.0, (0.72, 0.94), 0.0, "Cobblestone Floor 001", "road_mask"),
    "MAT_Plaza_Slab": (g_plaza, 4.0, (0.76, 0.94), 0.0, "(losas)", "slab_ring_id"),
    "MAT_Plaza_Slab_Travertino": (g_plaza_trav, 4.0, (0.74, 0.94), 0.0, "(travertino)", "travertine_band"),
    "MAT_Wall_Gray": (g_wall_gray, 6.0, (0.78, 0.95), 0.0, "Stone Wall 02 (gris)", "muralla"),
    "MAT_Wood_Dark": (g_wood, 3.0, (0.72, 0.9), 0.0, "(madera)", "vigas, puertas"),
    "MAT_Roof_Tile_Ocher": (g_roof, 4.0, (0.7, 0.9), 0.0, "(teja)", "tejados"),
    "MAT_Iron_Black": (g_iron, 2.0, (0.33, 0.47), 0.6, "(hierro)", "rejas, herrajes"),
    "MAT_Cloth_Patch_A": (g_cloth_a, 2.0, (0.84, 0.95), 0.0, "(tela)", "toldos, puestos"),
    "MAT_Cloth_Patch_B": (g_cloth_b, 2.0, (0.84, 0.95), 0.0, "(tela)", "toldos, puestos"),
    "MAT_Cloth_Patch_C": (g_cloth_c, 2.0, (0.84, 0.95), 0.0, "(tela)", "toldos, puestos"),
    "MAT_Ash_Gray": (g_ash, 3.0, (0.82, 0.95), 0.0, "Rocks Ground 02 (ceniza)", "ash_mask"),
    "MAT_Shard_Blue": (g_shard, 2.0, (0.7, 0.75), 0.0, "(cristal de esquirla)", "emisivo 2.5"),
    "MAT_Wall_Runes": (g_runes, 3.0, (0.78, 0.92), 0.0, "(runas)", "emisivo 0.8 parametrizable"),
    "MAT_Water": (g_water, 1.5, (0.1, 0.1), 0.0, "(agua)", "Cauce"),
    # adicionales necesarios para cubrir todo el terreno y las piezas (fuera de la lista del pedido)
    "MAT_Ground_Cracked": (g_ground, 4.0, (0.8, 0.95), 0.0, "Sandstone Cracks", "suelo sin mascara (patios, plataformas)"),
    "MAT_Rock_Gray": (g_rock, 7.0, (0.8, 0.95), 0.0, "Rock Boulder Cracked", "taludes exteriores, cabezos, acantilados"),
    "MAT_Stone_Repair": (g_repair, 4.0, (0.8, 0.95), 0.0, "Stone Wall 02 (remiendo)", "20 % de los pretiles"),
}
EMISSION = {"MAT_Shard_Blue": 2.5, "MAT_Wall_Runes": 0.8}
SAT_CAP = {"MAT_Roof_Tile_Ocher": 0.40, "MAT_Wood_Dark": 0.35, "MAT_Shard_Blue": None, "MAT_Water": None}
SAT_DEFAULT = 0.30


def cap_saturation(alb, cap):
    """Mezcla hacia la luminancia hasta que el percentil 95 de saturacion HSV quede <= cap."""
    if cap is None:
        return alb
    lum = (alb * np.array([0.2126, 0.7152, 0.0722])).sum(-1, keepdims=True)
    k = 1.0
    for _ in range(12):
        test = lum + (alb - lum) * k
        if saturation(test)[0] <= cap:
            return test
        k *= 0.85
    return lum + (alb - lum) * k


def tex_paths(mat):
    d = os.path.join(OUT, mat)
    return {k: os.path.join(d, f"T_{mat[4:]}_{k}.jpg") for k in ("Albedo", "Normal", "Roughness", "Emission")}


def saturation(alb):
    m = alb.reshape(-1, 3)[::97]
    s = np.array([colorsys.rgb_to_hsv(*np.clip(c, 0, 1))[1] for c in m])
    return float(np.percentile(s, 95)), float(colorsys.rgb_to_hsv(*np.clip(m.mean(0), 0, 1))[1])


def bake_all(names=None):
    setup_res()
    out = {}
    for i, (name, spec) in enumerate(MATS.items()):
        if names and name not in names:
            continue
        fn, ns, (r0, r1), _met, _ref, _use = spec
        rng = np.random.default_rng(SEED * 100 + i)
        res = fn(rng)
        alb, h, rough = res[:3]
        alb = cap_saturation(np.clip(alb, 0, 1), SAT_CAP.get(name, SAT_DEFAULT))
        rough = np.clip(rough, 0, 1)
        lo, hi = float(rough.min()), float(rough.max())
        rough = r0 + (rough - lo) / max(1e-6, hi - lo) * (r1 - r0) if hi > lo else np.full_like(rough, r0)
        p = tex_paths(name)
        os.makedirs(os.path.dirname(p["Albedo"]), exist_ok=True)
        Image.fromarray((np.clip(alb, 0, 1) * 255).astype(np.uint8)).save(p["Albedo"], quality=93)
        Image.fromarray(ML.normal_gl(h, ns)).save(p["Normal"], quality=95)
        Image.fromarray((np.clip(rough, 0, 1) * 255).astype(np.uint8), "L").save(p["Roughness"], quality=93)
        info = {"res": RES, "rough": [round(float(rough.min()), 3), round(float(rough.max()), 3)],
                "sat_p95_mean": [round(v, 3) for v in saturation(alb)],
                "bytes": sum(os.path.getsize(p[k]) for k in ("Albedo", "Normal", "Roughness"))}
        if len(res) > 3:
            Image.fromarray((np.clip(res[3], 0, 1) * 255).astype(np.uint8), "L").save(p["Emission"], quality=93)
            info["bytes"] += os.path.getsize(p["Emission"])
        out[name] = info
        print(name, info, flush=True)
    return out


if __name__ == "__main__":
    bake_all(sys.argv[1:] or None)
