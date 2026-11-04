"""
CONCORDIA - capturas de verificacion de la etapa 02 (terreno TRN_City).

Abre concordia_v02.blend, asigna materiales TEMPORALES de verificacion (no se
guardan) y renderiza con Cycles CPU. Genera ademas el perfil (corte) con
matplotlib a partir de raycasts sobre la malla real.

Material "clay" de verificacion: gris neutro + curvas de nivel cada 0.5 m
(en cotas x.25 / x.75 para no coincidir con los planos de terraza) y muros de
contencion (retaining_mask) en gris oscuro.
Material "masks": R = retaining_mask, G = dirt_mask, B = stone_mask (emision).

Uso:
    python tools/blender/capture_stage02.py [--only iso,top,masks,iso_nw,iso_se,eye_nw,eye_n,profile]
"""

import argparse
import os
import sys
from math import radians

import bpy
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Euler, Vector
from mathutils.bvhtree import BVHTree

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import concordia_const as C  # noqa: E402
import terrain_profile as T  # noqa: E402

REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
DEFAULT_BLEND = os.path.join(REPO, "blender", f"{C.BLEND_BASENAME}_v02.blend")
DEFAULT_OUT = os.path.join(REPO, "docs", "captures")
TAG = "stage02"
SAMPLES = 32
OVERVIEW_ORTHO = 460.0
TOP_ORTHO = 440.0
EYE = 1.7
PROFILE_VEXAG = 4.0
ALL = ("iso", "top", "masks", "iso_nw", "iso_se", "eye_nw", "eye_n", "profile")


def parse_args():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    p = argparse.ArgumentParser()
    p.add_argument("--blend", default=DEFAULT_BLEND)
    p.add_argument("--out", default=DEFAULT_OUT)
    p.add_argument("--only", default=",".join(ALL))
    return p.parse_args(argv)


# ---------------------------------------------------------------------------
# Materiales temporales
# ---------------------------------------------------------------------------
def clay_material():
    m = bpy.data.materials.new("TMP_clay")
    m.use_nodes = True
    nt = m.node_tree
    N, L = nt.nodes, nt.links
    bsdf = N["Principled BSDF"]
    bsdf.inputs["Roughness"].default_value = 0.95
    geo = N.new("ShaderNodeNewGeometry")
    sep = N.new("ShaderNodeSeparateXYZ")
    L.new(geo.outputs["Position"], sep.inputs[0])

    def math(op, a, b=None):
        n = N.new("ShaderNodeMath")
        n.operation = op
        for i, v in enumerate((a, b)):
            if v is None:
                continue
            if isinstance(v, (int, float)):
                n.inputs[i].default_value = v
            else:
                L.new(v, n.inputs[i])
        return n.outputs[0]

    f = math("FRACT", math("DIVIDE", math("SUBTRACT", sep.outputs["Z"], 0.25), 0.5))
    d = math("MINIMUM", f, math("SUBTRACT", 1.0, f))
    line = math("LESS_THAN", d, 0.035)
    # sin curvas en zonas casi planas (< 0.8 grados): ahi la linea se ensancha metros
    nsep = N.new("ShaderNodeSeparateXYZ")
    L.new(geo.outputs["Normal"], nsep.inputs[0])
    line = math("MULTIPLY", line, math("LESS_THAN", nsep.outputs["Z"], 0.9999))
    attr = N.new("ShaderNodeAttribute")
    attr.attribute_type = "GEOMETRY"
    attr.attribute_name = "retaining_mask"
    base = N.new("ShaderNodeMix")
    base.data_type = "RGBA"
    base.inputs["A"].default_value = (0.50, 0.49, 0.46, 1)
    base.inputs["B"].default_value = (0.16, 0.15, 0.14, 1)
    L.new(attr.outputs["Fac"], base.inputs["Factor"])
    mix = N.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    L.new(line, mix.inputs["Factor"])
    L.new(base.outputs["Result"], mix.inputs["A"])
    mix.inputs["B"].default_value = (0.05, 0.05, 0.05, 1)
    L.new(mix.outputs["Result"], bsdf.inputs["Base Color"])
    return m


def mask_material():
    m = bpy.data.materials.new("TMP_masks")
    m.use_nodes = True
    nt = m.node_tree
    N, L = nt.nodes, nt.links
    for n in list(N):
        if n.type != "OUTPUT_MATERIAL":
            N.remove(n)
    out = N["Material Output"]
    comb = N.new("ShaderNodeCombineXYZ")
    for i, name in enumerate(("retaining_mask", "dirt_mask", "stone_mask")):
        a = N.new("ShaderNodeAttribute")
        a.attribute_type = "GEOMETRY"
        a.attribute_name = name
        L.new(a.outputs["Fac"], comb.inputs[i])
    em = N.new("ShaderNodeEmission")
    L.new(comb.outputs[0], em.inputs["Color"])
    L.new(em.outputs[0], out.inputs["Surface"])
    return m


def set_material(obj, mat):
    obj.data.materials.clear()
    obj.data.materials.append(mat)


# ---------------------------------------------------------------------------
# Render
# ---------------------------------------------------------------------------
def setup_render(scene):
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = SAMPLES
    scene.cycles.use_denoising = True
    scene.render.image_settings.file_format = "PNG"
    world = bpy.data.worlds.new("TMP_world")
    world.use_nodes = True
    bg = world.node_tree.nodes["Background"]
    bg.inputs["Color"].default_value = (0.55, 0.57, 0.60, 1)
    bg.inputs["Strength"].default_value = 0.55
    scene.world = world
    sun = bpy.data.objects.new("TMP_sun", bpy.data.lights.new("TMP_sun", "SUN"))
    sun.data.energy = 3.8
    sun.data.angle = radians(1.5)
    sun.rotation_euler = Euler((radians(55), 0, radians(-45)))   # luz desde el SO, 35 grados
    scene.collection.objects.link(sun)


def render(scene, cam, path, view="AgX"):
    scene.camera = cam
    scene.view_settings.view_transform = view
    scene.render.filepath = path
    bpy.ops.render.render(write_still=True)
    print("render:", path)


def new_cam(name, ortho=None, lens=24.0):
    data = bpy.data.cameras.new(name)
    if ortho:
        data.type = "ORTHO"
        data.ortho_scale = ortho
    else:
        data.lens = lens
    data.clip_start, data.clip_end = 0.1, 3000.0
    cam = bpy.data.objects.new(name, data)
    bpy.context.scene.collection.objects.link(cam)
    return cam


def look_at(cam, eye, target):
    cam.location = Vector(eye)
    cam.rotation_euler = (Vector(target) - cam.location).to_track_quat("-Z", "Y").to_euler()


def iso_at(cam_iso, target, ortho):
    """Copia temporal de CAM_Iso con otro objetivo / escala (misma rotacion)."""
    cam = new_cam("TMP_iso", ortho=ortho)
    cam.rotation_euler = cam_iso.rotation_euler.copy()
    d = cam.rotation_euler.to_matrix() @ Vector((0, 0, -1))
    cam.location = Vector(target) - d * C.CAM_ISO_DISTANCE
    return cam


def annotate(scene, cam, path, title, labels, legend=None):
    from PIL import Image, ImageDraw, ImageFont
    img = Image.open(path).convert("RGB")
    d = ImageDraw.Draw(img)
    W, H = img.size
    font = ImageFont.truetype("DejaVuSans-Bold.ttf", 24)
    small = ImageFont.truetype("DejaVuSans.ttf", 21)
    for text, pt in labels:
        p = world_to_camera_view(scene, cam, Vector(pt))
        if not (0 <= p.x <= 1 and 0 <= p.y <= 1 and p.z > 0):
            continue
        px, py = p.x * W, (1 - p.y) * H
        d.ellipse([px - 5, py - 5, px + 5, py + 5], outline=(255, 255, 255), width=3)
        tx, ty = px + 12, py - 34
        bb = d.textbbox((tx, ty), text, font=font)
        if bb[2] > W - 10:
            tx = px - 12 - (bb[2] - bb[0])
            bb = d.textbbox((tx, ty), text, font=font)
        d.rectangle([bb[0] - 5, bb[1] - 3, bb[2] + 5, bb[3] + 3], fill=(0, 0, 0))
        d.text((tx, ty), text, fill=(255, 255, 255), font=font)
    d.rectangle([0, 0, W, 40], fill=(0, 0, 0))
    d.text((12, 8), title, fill=(255, 255, 255), font=small)
    if legend:
        y = H - 12 - 28 * len(legend)
        for txt in legend:
            bb = d.textbbox((12, y), txt, font=small)
            d.rectangle([bb[0] - 6, bb[1] - 3, bb[2] + 6, bb[3] + 3], fill=(0, 0, 0))
            d.text((12, y), txt, fill=(255, 255, 255), font=small)
            y += 28
    img.save(path)


def zlab(x, y):
    return (x, y, T.height(x, y))


def sector_labels():
    out = [("Plaza +8.0", zlab(0, 0))]
    for key, (name, ang, _h, _r) in C.DISTRICTS_CARDINAL.items():
        x, y, _ = C.polar(ang, 130)
        out.append((f"{name}", zlab(x, y)))
    for key, (name, ang, _h, _r) in C.MORADAS.items():
        x, y, _ = C.polar(ang, 150)
        out.append((f"{name}", zlab(x, y)))
    return out


# ---------------------------------------------------------------------------
# Perfil (corte) con matplotlib
# ---------------------------------------------------------------------------
def profile_plot(obj, path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    bvh = BVHTree.FromObject(obj, bpy.context.evaluated_depsgraph_get())

    def zat(x, y):
        hit = bvh.ray_cast(Vector((x, y, 100.0)), Vector((0, 0, -1)))
        return hit[0].z if hit[0] else float("nan")

    def radial(ang, r0=0.0, r1=C.TERRAIN_RADIUS - 0.01, step=0.05):
        rs, zs = [], []
        r = r0
        while r <= r1:
            x, y, _ = C.polar(ang, r)
            rs.append(r)
            zs.append(zat(x, y))
            r += step
        return rs, zs

    fig = plt.figure(figsize=(19.2, 12.0), dpi=100)
    gs = fig.add_gridspec(3, 3, height_ratios=[1.35, 1.0, 1.0], hspace=0.45, wspace=0.28)
    ax = fig.add_subplot(gs[0, :])
    for ang, lab, col in ((90.0, "Mercado (N, 90°) - cardinal", "#3a3a3a"),
                          (45.0, "Morada NE (45°) - diagonal", "#9a5b2a")):
        rs, zs = radial(ang)
        ax.plot(rs, zs, color=col, lw=1.6, label=lab)
    for z, t in ((8.0, "plaza +8.0 (centro)"), (6.0, "DATUM +6.0"), (4.5, "+4.5"), (9.5, "+9.5"), (0.0, "yermo 0")):
        ax.axhline(z, color="#999", lw=0.6, ls="--")
        ax.text(1, z + 0.12, t, fontsize=8, color="#555")
    for r in (60, 90, 95, 105, 119, 133, 147, 161, 175, 165, 185, 189, 196, 204, 212):
        ax.axvline(r, color="#ccc", lw=0.5, zorder=0)
        ax.text(r, -1.15, str(r), fontsize=7, ha="center", color="#666")
    ax.set_xlim(0, 213)
    ax.set_ylim(-1.4, 11)
    ax.set_ylabel("Z absoluto (m)")
    ax.set_title(f"Corte radial desde el centro (raycast sobre TRN_City). Exageracion vertical x{PROFILE_VEXAG:.0f}",
                 fontsize=11)
    ax.legend(loc="lower center", fontsize=9)
    ax.set_aspect(PROFILE_VEXAG)   # aspect = longitud de 1 m vertical / 1 m horizontal

    # Detalles 1:1
    def detail(axd, ang, r0, r1, title):
        rs, zs = radial(ang, r0, r1, 0.005)
        axd.plot(rs, zs, color="#9a5b2a", lw=1.6)
        axd.set_aspect("equal")
        axd.set_title(title, fontsize=10)
        axd.grid(True, color="#ddd", lw=0.5)
        axd.set_xlabel("r (m)")

    detail(fig.add_subplot(gs[1, 0]), 45.0, 116.5, 121.5, "Salto de terraza r=119 (1:1), cara 80°")
    detail(fig.add_subplot(gs[1, 1]), 45.0, 200.5, 207.5, "Pie de muralla diagonal r=204 (1:1)")
    detail(fig.add_subplot(gs[1, 2]), 90.0, 182.0, 199.0, "Terraplen cardinal 185-196 (1:1)")

    # Corte circunferencial (lateral) a r=150 y r=185: bordes entre sectores
    axc = fig.add_subplot(gs[2, :])
    for R, col in ((120.0, "#6b8e23"), (150.0, "#3a3a3a"), (185.0, "#9a5b2a")):
        angs = [a * 0.05 for a in range(0, int(90 / 0.05) + 1)]
        xs, zs = [], []
        for a in angs:
            x, y, _ = C.polar(a, R)
            xs.append(a)
            zs.append(zat(x, y))
        axc.plot(xs, zs, color=col, lw=1.4, label=f"r = {R:.0f} m")
    for a in (0, 25, 45, 65, 90):
        axc.axvline(a, color="#ccc", lw=0.5)
    axc.set_xlim(0, 90)
    axc.set_xlabel("angulo (grados): 0 Oficios (E) -> 45 Morada NE -> 90 Mercado (N); bordes de sector en 25 y 65")
    axc.set_ylabel("Z (m)")
    axc.set_title("Corte lateral (arco) - transicion entre sectores en 6 m de arco", fontsize=10)
    axc.legend(fontsize=9)
    axc.grid(True, color="#eee", lw=0.5)
    fig.savefig(path)
    print("profile:", path)


# ---------------------------------------------------------------------------
def main():
    args = parse_args()
    only = set(args.only.split(","))
    bpy.ops.wm.open_mainfile(filepath=args.blend)
    scene = bpy.context.scene
    scene.render.resolution_x, scene.render.resolution_y = C.RENDER_RES
    os.makedirs(args.out, exist_ok=True)
    setup_render(scene)
    trn = bpy.data.objects["TRN_City"]
    cam_iso = bpy.data.objects[C.CAM_ISO_NAME]
    clay, masks = clay_material(), mask_material()
    set_material(trn, clay)
    P = lambda name: os.path.join(args.out, f"{TAG}_{name}.png")  # noqa: E731
    gates = [(n.replace("MARKER_", ""), tuple(bpy.data.objects[n].location)) for n in C.GATES]
    legend_clay = ["Material de verificacion: gris + curvas de nivel cada 0.5 m (cotas x.25/x.75)",
                   "Gris oscuro = retaining_mask (caras de muro 80°)"]

    if "iso" in only:
        cam = iso_at(cam_iso, C.CAM_ISO_TARGET, OVERVIEW_ORTHO)
        render(scene, cam, P("iso_overview"))
        annotate(scene, cam, P("iso_overview"),
                 f"TRN_City - CAM_Iso (X54.736 Z45), ortho TEMPORAL {OVERVIEW_ORTHO:.0f}",
                 sector_labels() + gates, legend_clay)
    if "top" in only:
        cam = new_cam("TMP_top", ortho=TOP_ORTHO)
        cam.location = (0, 0, 400)
        cam.rotation_euler = (0, 0, 0)
        render(scene, cam, P("top"))
        annotate(scene, cam, P("top"), f"TRN_City - cenital (Norte arriba), ortho {TOP_ORTHO:.0f}",
                 sector_labels() + gates, legend_clay)
    if "masks" in only:
        set_material(trn, masks)
        cam = new_cam("TMP_top_m", ortho=TOP_ORTHO)
        cam.location = (0, 0, 400)
        render(scene, cam, P("top_masks"), view="Standard")
        annotate(scene, cam, P("top_masks"), "Mascaras de vertice (cenital): R = retaining_mask, G = dirt_mask, B = stone_mask",
                 [], ["Rojo/blanco: muros de contencion | Verde: tierra | Azul: piedra (plaza, base muralla, roca del talud)",
                      "(colores de depuracion, no son materiales del juego)"])
        set_material(trn, clay)
    if "iso_nw" in only:
        tgt = zlab(*C.polar(135, 150)[:2])
        cam = iso_at(cam_iso, tgt, C.CAM_ISO_ORTHO_SCALE)
        render(scene, cam, P("iso120_morada_NW"))
        labs = [(f"terraza {k} +{4.5 + k - 1:.1f}", zlab(*C.polar(135, 105 + 14 * (k - 0.5))[:2]))
                for k in range(1, 7)]
        annotate(scene, cam, P("iso120_morada_NW"),
                 "CAM_Iso a escala de juego (ortho 120) sobre Morada NO: los muros miran a la camara",
                 labs, legend_clay)
    if "iso_se" in only:
        tgt = zlab(*C.polar(315, 150)[:2])
        cam = iso_at(cam_iso, tgt, C.CAM_ISO_ORTHO_SCALE)
        render(scene, cam, P("iso120_morada_SE"))
        labs = [(f"terraza {k} +{4.5 + k - 1:.1f}", zlab(*C.polar(315, 105 + 14 * (k - 0.5))[:2]))
                for k in range(1, 7)]
        annotate(scene, cam, P("iso120_morada_SE"),
                 "CAM_Iso a escala de juego (ortho 120) sobre Morada SE: los muros dan la espalda a la camara",
                 labs, legend_clay)
    if "eye_nw" in only:
        cam = new_cam("TMP_eye_nw", lens=24)
        ex, ey, _ = C.polar(135, 127)
        tx, ty, _ = C.polar(135, 190)
        look_at(cam, (ex, ey, T.height(ex, ey) + EYE), (tx, ty, 8.5))
        render(scene, cam, P("eye_morada_NW"))
        annotate(scene, cam, P("eye_morada_NW"),
                 "Altura de personaje (1.7 m) en terraza 2 de Morada NO (r=127, +5.5), mirando hacia la muralla",
                 [(f"salto r={R:.0f}", zlab(*C.polar(135, R)[:2])) for R in (133, 147, 161, 175)])
    if "eye_n" in only:
        cam = new_cam("TMP_eye_n", lens=24)
        ex, ey, _ = C.polar(80, 150)
        tx, ty, _ = C.polar(62, 168)
        look_at(cam, (ex, ey, T.height(ex, ey) + EYE), (tx, ty, 7.0))
        render(scene, cam, P("eye_borde_Mercado_MoradaNE"))
        annotate(scene, cam, P("eye_borde_Mercado_MoradaNE"),
                 "Altura de personaje en Mercado (r=150, ang 80, +4.8) mirando al borde con Morada NE (mezcla de 6 m)",
                 [("Morada NE terraza 4 +7.5", zlab(*C.polar(55, 154)[:2])),
                  ("Morada NE terraza 5 +8.5", zlab(*C.polar(55, 168)[:2])),
                  ("borde 65 grados", zlab(*C.polar(65, 160)[:2]))])
    if "profile" in only:
        profile_plot(trn, P("profile"))
    # Nada se guarda: el .blend queda intacto.


if __name__ == "__main__":
    main()
