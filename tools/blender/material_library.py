"""
CONCORDIA - biblioteca de materiales PBR procedurales (sin red: Poly Haven bloqueado).

Convencion (para sustituirlas por Poly Haven cambiando SOLO 3 imagenes):
  textures/lib/<Nombre>/T_<Nombre>_Albedo.png     color (sRGB)
  textures/lib/<Nombre>/T_<Nombre>_NormalGL.png   normal OpenGL (Y+, la de Godot)
  textures/lib/<Nombre>/T_<Nombre>_Roughness.png  rugosidad (gris lineal)
  Escala UV: 1 m = 1 tile (las piezas usan UV en metros).
  Material MAT_<...> con tres nodos de imagen llamados exactamente "Albedo", "NormalGL" y
  "Roughness"; el metalico es un valor fijo del material (solo hierro).

Uso: python tools/blender/material_library.py   -> genera las texturas (semilla fija).
"""

import os
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
LIB = os.path.join(REPO, "textures", "lib")
SEED = 21
N = 1024                                    # px por metro (1 m = 1 tile)

# nombre: (poly_haven_equivalente, metalico, descripcion)
SETS = {
    "WallGranite": ("(sillar de granito; ref. Avila)", 0.0, "muralla"),
    "WallPatch": ("Stone Wall 02 (mamposteria de remiendo)", 0.0, "parches de muralla"),
    "StoneBand": ("(caliza clara)", 0.0, "bandas de la puerta, arquivolta"),
    "RoofSlate": ("(pizarra)", 0.0, "techos conicos"),
    "RoofTileOchre": ("(teja curva ocre)", 0.0, "parches de tejado"),
    "WoodDark": ("(madera oscura)", 0.0, "vigas, cadalso, puertas"),
    "IronBlack": ("(hierro forjado)", 0.85, "hojas de la puerta, rejas"),
    "CobblestoneFloor001": ("Cobblestone Floor 001", 0.0, "terreno: pavimento de calles"),
    "SandstoneCracks": ("Sandstone Cracks", 0.0, "terreno: muros de contencion"),
    "RockBoulderCracked": ("Rock Boulder Cracked", 0.0, "terreno: roca del talud"),
    "RocksGround02": ("Rocks Ground 02", 0.0, "terreno: tierra con piedras"),
    "StoneWall02": ("Stone Wall 02", 0.0, "terreno: mamposteria"),
}


def paths(name):
    d = os.path.join(LIB, name)
    return {k: os.path.join(d, f"T_{name}_{k}.png") for k in ("Albedo", "NormalGL", "Roughness")}


# ---------------------------------------------------------------------------
def srgb(h):
    h = h.lstrip("#")
    return np.array([int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4)])


def fnoise(rng, n, scale_px, aniso=(1.0, 1.0)):
    """Ruido suave tileable 0..1 (filtro gaussiano en frecuencia; aniso estira x/y)."""
    w = rng.standard_normal((n, n))
    f = np.fft.fftfreq(n)
    fx, fy = np.meshgrid(f, f)
    g = np.exp(-((fx * aniso[0]) ** 2 + (fy * aniso[1]) ** 2) * (np.pi * scale_px) ** 2)
    o = np.real(np.fft.ifft2(np.fft.fft2(w) * g))
    o -= o.min()
    return o / max(o.max(), 1e-9)


def fbm(rng, n, scales, weights):
    acc = sum(w * fnoise(rng, n, s) for s, w in zip(scales, weights))
    acc -= acc.min()
    return acc / max(acc.max(), 1e-9)


def worley(rng, n, cells_x, cells_y=None, jitter=0.9):
    """Voronoi tileable: devuelve F1, F2 (en px) e id de celda."""
    cells_y = cells_y or cells_x
    cw, ch = n / cells_x, n / cells_y
    jx = rng.uniform(0.5 - jitter / 2, 0.5 + jitter / 2, (cells_y, cells_x))
    jy = rng.uniform(0.5 - jitter / 2, 0.5 + jitter / 2, (cells_y, cells_x))
    yy, xx = np.mgrid[0:n, 0:n].astype(np.float32)
    cx = np.floor(xx / cw).astype(int)
    cy = np.floor(yy / ch).astype(int)
    f1 = np.full((n, n), 1e9, np.float32)
    f2 = np.full((n, n), 1e9, np.float32)
    cid = np.zeros((n, n), int)
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            nx, ny = cx + dx, cy + dy
            wx, wy = nx % cells_x, ny % cells_y
            px = (nx + jx[wy, wx]) * cw
            py = (ny + jy[wy, wx]) * ch
            d = np.sqrt((xx - px) ** 2 + (yy - py) ** 2)
            ids = wy * cells_x + wx
            closer = d < f1
            f2 = np.where(closer, f1, np.minimum(f2, d))
            cid = np.where(closer, ids, cid)
            f1 = np.where(closer, d, f1)
    return f1, f2, cid


def normal_gl(h, strength):
    dx = (np.roll(h, -1, 1) - np.roll(h, 1, 1)) * 0.5 * strength
    dy = (np.roll(h, -1, 0) - np.roll(h, 1, 0)) * 0.5 * strength
    n = np.stack([-dx, dy, np.ones_like(h)], -1)            # OpenGL: +Y arriba
    n /= np.linalg.norm(n, axis=-1, keepdims=True)
    return ((n * 0.5 + 0.5) * 255).astype(np.uint8)


def save(name, alb, h, rough, nstrength):
    p = paths(name)
    os.makedirs(os.path.dirname(p["Albedo"]), exist_ok=True)
    Image.fromarray((np.clip(alb, 0, 1) * 255).astype(np.uint8)).save(p["Albedo"], optimize=True)
    Image.fromarray(normal_gl(h, nstrength)).save(p["NormalGL"], optimize=True)
    Image.fromarray((np.clip(rough, 0, 1) * 255).astype(np.uint8)).save(p["Roughness"], optimize=True)
    return p


def per_cell(ids, rng, lo, hi):
    vals = rng.uniform(lo, hi, ids.max() + 1)
    return vals[ids]


# ---------------------------------------------------------------------------
def ashlar(rng, courses, lens, mortar, bevel, base, var, speck, stain, chip=0.35):
    n = N
    h = np.zeros((n, n))
    ids = np.zeros((n, n), int)
    edge = np.zeros((n, n))
    ch = n // courses
    k = 0
    for c in range(courses):
        L = []
        while sum(L) < 1.0 - lens[1]:
            L.append(rng.uniform(*lens))
        L.append(1.0 - sum(L))
        if L[-1] < lens[0] * 0.5 and len(L) > 1:
            last = L.pop()
            L[-1] += last
        x0 = rng.uniform(0, 1)
        for ln in L:
            a, w = int(round(x0 * n)), max(2, int(round(ln * n)))
            cols = np.arange(a, a + w) % n
            X = np.broadcast_to(np.arange(w)[None, :], (ch, w))
            Y = np.broadcast_to(np.arange(ch)[:, None], (ch, w))
            d = np.minimum(np.minimum(X, w - 1 - X), np.minimum(Y, ch - 1 - Y)).astype(float)
            rows = slice(c * ch, (c + 1) * ch)
            edge[rows, cols] = d
            ids[rows, cols] = k
            k += 1
            x0 += ln
    m_px, b_px = mortar * n / 2, bevel * n
    nz = fnoise(rng, n, 8)
    d_eff = edge - chip * b_px * nz                          # bordes desconchados irregulares
    prof = np.clip((d_eff - m_px) / b_px, 0, 1)
    face = per_cell(ids, rng, 0.85, 1.0)
    h = prof * (face + 0.06 * fbm(rng, n, (3, 12, 40), (0.3, 0.4, 0.3)))
    tint = base[None, None, :] * (1 + per_cell(ids, rng, -var, var)[..., None])
    tint *= 1 + rng.uniform(-0.02, 0.02, (k, 3))[ids]
    st = fbm(rng, n, (60, 150), (0.5, 0.5))
    alb = tint * (1 - stain * (st[..., None] - 0.5))
    alb *= (1 - speck + 2 * speck * rng.random((n, n)))[..., None]
    mortar_col = base * 0.62
    alb = np.where((prof > 0.02)[..., None], alb * (0.9 + 0.1 * prof[..., None]), mortar_col)
    rough = np.where(prof > 0.02, 0.78 + per_cell(ids, rng, -0.06, 0.08) + 0.06 * (nz - 0.5), 0.95)
    return alb, h, rough


def granite_grain(rng, alb, amount):
    """Cristales de granito: puntos claros (feldespato) y oscuros (mica)."""
    r = rng.random((N, N))
    light = (r > 1 - amount * 0.5)
    dark = (r < amount * 0.6)
    g = fnoise(rng, N, 1.2)
    alb = np.where(light[..., None], alb * (1.18 + 0.1 * g[..., None]), alb)
    alb = np.where(dark[..., None], alb * 0.55, alb)
    return alb


def gen_wall_granite(rng):
    a, h, r = ashlar(rng, 2, (0.28, 0.62), 0.014, 0.03, srgb("#77716A"), 0.13, 0.04, 0.32, chip=0.7)
    a = granite_grain(rng, a, 0.12)
    h = h + 0.04 * fnoise(rng, N, 1.5)
    return a, h, r

def gen_stone_band(rng):
    a, h, r = ashlar(rng, 2, (0.45, 0.9), 0.009, 0.025, srgb("#C4B9A2"), 0.09, 0.05, 0.3, chip=0.45)
    pits = (rng.random((N, N)) < 0.004).astype(float)
    pits = np.clip(fnoise(rng, N, 0.8) * 0 + pits, 0, 1)
    h = h - 0.15 * pits + 0.05 * fnoise(rng, N, 2)
    a = a * (1 - 0.25 * pits[..., None])
    return a, h, r + 0.02

def rubble(rng, cells, base, mortar_hex, var, mortar_w, rough_base):
    f1, f2, cid = worley(rng, N, cells[0], cells[1], jitter=0.85)
    e = f2 - f1
    mw = mortar_w * N
    prof = np.clip((e - mw) / (0.04 * N), 0, 1) ** 0.6
    nz = fbm(rng, N, (4, 16, 50), (0.3, 0.4, 0.3))
    dome = np.clip(1 - f1 / (f2 + 1e-6), 0, 1)
    h = prof * (0.75 + 0.25 * dome + 0.08 * nz)
    tint = srgb(base)[None, None, :] * (1 + per_cell(cid, rng, -var, var)[..., None])
    tint *= 1 + rng.uniform(-0.04, 0.04, (cid.max() + 1, 3))[cid]
    alb = np.where((prof > 0.05)[..., None], tint * (0.88 + 0.14 * nz[..., None]),
                   srgb(mortar_hex) * (0.9 + 0.2 * nz[..., None]))
    rough = np.where(prof > 0.05, rough_base + per_cell(cid, rng, -0.05, 0.05), 0.96)
    return alb, h, rough


def gen_wall_patch(rng):
    return rubble(rng, (5, 6), "#A0957F", "#8F8676", 0.16, 0.012, 0.86)

def gen_stone_wall02(rng):
    return rubble(rng, (4, 5), "#8C877E", "#A8A091", 0.10, 0.012, 0.84)


def gen_roof_slate(rng):
    n = N
    rows = 4
    rh = n // rows
    h = np.zeros((n, n))
    ids = np.zeros((n, n), int)
    k = 0
    for r in range(rows):
        x = rng.uniform(0, 1)
        widths = []
        while sum(widths) < 1.0 - 0.3:
            widths.append(rng.uniform(0.16, 0.3))
        widths.append(1.0 - sum(widths))
        for wd in widths:
            a, w = int(x * n), max(2, int(wd * n))
            cols = np.arange(a, a + w) % n
            Y = np.arange(rh)[:, None] / rh
            X = np.arange(w)[None, :]
            gap = (np.minimum(X, w - 1 - X) > 3).astype(float)
            ramp = 0.35 + 0.65 * Y                            # mas grueso abajo (solape)
            h[r * rh:(r + 1) * rh, cols] = ramp * gap
            ids[r * rh:(r + 1) * rh, cols] = k
            k += 1
            x += wd
    nz = fbm(rng, n, (3, 10, 30), (0.3, 0.4, 0.3))
    h = h + 0.05 * nz
    base = srgb("#3E4046")
    tint = base[None, None, :] * (1 + per_cell(ids, rng, -0.12, 0.12)[..., None])
    alb = tint * (0.85 + 0.25 * nz[..., None]) * (0.75 + 0.25 * (h[..., None] > 0.2))
    rough = 0.5 + per_cell(ids, rng, -0.08, 0.12) + 0.1 * (nz - 0.5)
    return alb, h, rough


def gen_roof_tile(rng):
    n = N
    cols, rows = 5, 3
    yy, xx = np.mgrid[0:n, 0:n] / n
    row = np.floor(yy * rows)
    u = (xx * cols + 0.5 * (row % 2)) % 1.0
    col = np.floor(xx * cols + 0.5 * (row % 2)) % cols
    ry = (yy * rows) % 1.0
    rid = (row * cols + col).astype(int)
    barrel = np.sin(np.pi * u) ** 0.7
    gap = np.clip(np.minimum(u, 1 - u) / 0.04, 0, 1)
    overlap = np.clip((1 - ry) / 0.12, 0, 1)            # sombra del solape de la hilada de arriba
    h = gap * barrel * (0.45 + 0.55 * ry) + 0.05 * fbm(rng, n, (3, 12), (0.5, 0.5))
    nz = fbm(rng, n, (3, 12, 40), (0.3, 0.4, 0.3))
    tint = srgb("#A06E3E")[None, None, :] * (1 + per_cell(rid, rng, -0.22, 0.12)[..., None])
    tint *= 1 + rng.uniform(-0.06, 0.06, (rid.max() + 1, 3))[rid]
    soot = fbm(rng, n, (80, 200), (0.5, 0.5))
    alb = tint * (0.7 + 0.35 * barrel[..., None]) * (0.55 + 0.45 * overlap[..., None])
    alb *= (1 - 0.4 * (soot[..., None] - 0.45).clip(0)) * (0.92 + 0.12 * nz[..., None])
    alb = np.where((gap < 0.3)[..., None], alb * 0.35, alb)
    rough = 0.64 + per_cell(rid, rng, -0.06, 0.14) + 0.08 * (nz - 0.5)
    return alb, h, rough

def gen_wood(rng):
    n = N
    planks = 5
    ph = n // planks
    yy, xx = np.mgrid[0:n, 0:n].astype(float)
    pid = np.minimum((yy // ph).astype(int), planks - 1)
    shift = rng.uniform(0, 1, planks)[pid]
    joint_x = ((xx / n + shift) % 1.0)
    grain_n = fnoise(rng, n, 6, aniso=(0.08, 1.0))
    grain = 0.5 + 0.5 * np.sin((yy % ph) / ph * 2 * np.pi * rng.uniform(6, 9) + 10 * grain_n)
    gap = ((yy % ph) > 4) & (joint_x > 0.004)
    f1, _f2, _c = worley(rng, n, 3, 5, jitter=0.9)
    knot = np.clip(1 - f1 / (0.025 * n), 0, 1) ** 2
    h = gap * (0.8 + 0.12 * grain - 0.3 * knot)
    base = srgb("#4A3626")
    alb = base[None, None, :] * (0.75 + 0.35 * grain[..., None]) * (1 + per_cell(pid, rng, -0.12, 0.12)[..., None])
    alb *= (1 - 0.45 * knot[..., None])
    alb = np.where(gap[..., None], alb, base * 0.35)
    rough = 0.68 + 0.12 * grain_n + per_cell(pid, rng, -0.05, 0.05)
    return alb, h, rough


def gen_iron(rng):
    n = N
    f1, f2, cid = worley(rng, n, 14, 14, jitter=0.9)
    dent = (f1 / (f2 + 1e-6)) ** 2
    nz = fbm(rng, n, (2, 8, 40), (0.3, 0.4, 0.3))
    h = 0.6 * dent + 0.25 * nz
    rust = np.clip((fbm(rng, n, (20, 60), (0.6, 0.4)) - 0.66) * 5, 0, 1)
    alb = srgb("#242425")[None, None, :] * (0.8 + 0.4 * nz[..., None])
    alb = alb * (1 - rust[..., None]) + srgb("#4A2E20") * rust[..., None]
    rough = 0.55 + 0.18 * nz + 0.25 * rust
    return alb, h, rough

def gen_cobble(rng):
    f1, f2, cid = worley(rng, N, 9, 9, jitter=0.8)
    e = f2 - f1
    prof = np.clip((e - 0.008 * N) / (0.02 * N), 0, 1)
    dome = np.clip(1 - (f1 / (0.07 * N)) ** 2, 0, 1)
    nz = fbm(rng, N, (3, 12), (0.5, 0.5))
    h = prof * (0.5 + 0.5 * dome + 0.08 * nz)
    tint = srgb("#8D857A")[None, None, :] * (1 + per_cell(cid, rng, -0.15, 0.12)[..., None])
    alb = np.where((prof > 0.05)[..., None], tint * (0.85 + 0.2 * dome[..., None]), srgb("#5E564B"))
    rough = np.where(prof > 0.05, 0.72 + per_cell(cid, rng, -0.06, 0.08) - 0.1 * dome, 0.95)
    return alb, h, rough


def gen_sandstone(rng):
    yy = np.mgrid[0:N, 0:N][0] / N
    nz = fbm(rng, N, (4, 16, 60, 150), (0.2, 0.3, 0.3, 0.2))
    strata = 0.5 + 0.5 * np.sin(yy * 2 * np.pi * 6 + 5 * fnoise(rng, N, 40))
    f1, f2, _c = worley(rng, N, 4, 3, jitter=0.95)
    crack = np.clip(1 - (f2 - f1 + 6 * (fnoise(rng, N, 6) - 0.5)) / (0.01 * N), 0, 1)
    h = 0.55 + 0.2 * strata + 0.3 * nz - 0.7 * crack
    base = srgb("#B99C74")
    alb = base[None, None, :] * (0.78 + 0.18 * strata[..., None] + 0.2 * nz[..., None]) * (1 - 0.6 * crack[..., None])
    rough = 0.84 + 0.1 * nz
    return alb, h, rough

def gen_rock(rng):
    nz = fbm(rng, N, (3, 10, 32, 90, 200), (0.12, 0.2, 0.25, 0.25, 0.18))
    warp = fnoise(rng, N, 30)
    f1, f2, _c = worley(rng, N, 3, 4, jitter=0.95)
    crack = np.clip(1 - (f2 - f1 + 40 * (warp - 0.5)) / (0.012 * N), 0, 1)
    h = 1.4 * nz - 0.6 * crack
    cav = np.clip(0.5 - nz, 0, 1)
    alb = srgb("#77736B")[None, None, :] * (0.65 + 0.6 * nz[..., None]) * (1 - 0.55 * crack[..., None])
    alb *= 1 - 0.4 * cav[..., None]
    rough = 0.82 + 0.12 * (nz - 0.5)
    return alb, h, rough

def gen_ground(rng):
    nz = fbm(rng, N, (4, 20, 80), (0.3, 0.4, 0.3))
    patches = fbm(rng, N, (60, 160), (0.5, 0.5))
    f1, f2, cid = worley(rng, N, 16, 16, jitter=0.9)
    rad = per_cell(cid, rng, 0.008, 0.026) * N
    keep = per_cell(cid, rng, 0, 1) < 0.35
    stone = np.clip(1 - f1 / rad, 0, 1) * keep
    dome = np.sqrt(stone)
    grit = (rng.random((N, N)) < 0.02).astype(float)
    h = 0.35 * nz + 0.9 * dome
    earth = srgb("#76654F")[None, None, :] * (0.72 + 0.3 * nz[..., None]) * (0.85 + 0.3 * patches[..., None])
    earth *= (1 - 0.25 * grit[..., None])
    pebble = srgb("#7E776C")[None, None, :] * (1 + per_cell(cid, rng, -0.2, 0.15)[..., None])
    pebble *= (0.7 + 0.4 * dome[..., None])
    alb = np.where((stone > 0.03)[..., None], pebble, earth)
    rough = np.where(stone > 0.03, 0.72, 0.94)
    return alb, h, rough

GEN = {"WallGranite": (gen_wall_granite, 7.0), "WallPatch": (gen_wall_patch, 4.0), "StoneBand": (gen_stone_band, 3.0),
       "RoofSlate": (gen_roof_slate, 4.0), "RoofTileOchre": (gen_roof_tile, 4.0), "WoodDark": (gen_wood, 3.0),
       "IronBlack": (gen_iron, 2.0), "CobblestoneFloor001": (gen_cobble, 5.0), "SandstoneCracks": (gen_sandstone, 4.0),
       "RockBoulderCracked": (gen_rock, 7.0), "RocksGround02": (gen_ground, 4.0), "StoneWall02": (gen_stone_wall02, 4.0)}


def generate(names=None):
    out = {}
    for i, (name, (fn, ns)) in enumerate(GEN.items()):
        if names and name not in names:
            continue
        rng = np.random.default_rng(SEED * 100 + i)
        alb, h, rough = fn(rng)
        out[name] = save(name, alb, h, rough, ns)
        print(name, {k: os.path.getsize(v) for k, v in out[name].items()})
    return out


# ---------------------------------------------------------------------------
# Materiales Blender (requiere bpy)
# ---------------------------------------------------------------------------
def make_material(mat_name, tex_name, metallic=None):
    import bpy
    if mat_name in bpy.data.materials:
        bpy.data.materials.remove(bpy.data.materials[mat_name])
    m = bpy.data.materials.new(mat_name)
    m.use_nodes = True
    N_, L = m.node_tree.nodes, m.node_tree.links
    b = N_["Principled BSDF"]
    p = paths(tex_name)

    def img(key, non_color):
        im = bpy.data.images.load(p[key], check_existing=True)
        if non_color:
            im.colorspace_settings.name = "Non-Color"
        t = N_.new("ShaderNodeTexImage")
        t.name = t.label = key
        t.image = im
        return t
    L.new(img("Albedo", False).outputs["Color"], b.inputs["Base Color"])
    L.new(img("Roughness", True).outputs["Color"], b.inputs["Roughness"])
    nm = N_.new("ShaderNodeNormalMap")
    L.new(img("NormalGL", True).outputs["Color"], nm.inputs["Color"])
    L.new(nm.outputs["Normal"], b.inputs["Normal"])
    b.inputs["Metallic"].default_value = SETS[tex_name][1] if metallic is None else metallic
    m["texture_set"] = tex_name
    m["poly_haven_equivalent"] = SETS[tex_name][0]
    m["uv_scale"] = "1 m = 1 tile"
    m["godot_iso_fade"] = "admite fade por dithering (TRANSPARENCY_ALPHA_HASH / shader con discard), sin cambiar geometria"
    return m


if __name__ == "__main__":
    generate(sys.argv[1:] or None)
