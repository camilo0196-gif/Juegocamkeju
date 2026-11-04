"""
CONCORDIA - capturas de verificacion de la etapa 02 (v2: muros laterales, plazoletas,
escalinatas, pretiles, material con borde + AO).

Renderiza con Cycles CPU usando los MATERIALES REALES (MAT_Terrain_City, MAT_Stone_Limestone);
solo la luz y el cielo son temporales (no se guardan). Los chunks de Godot estan ocultos;
se renderiza la malla maestra.

Uso:
    python tools/blender/capture_stage02.py [--only iso,top,masks,moradas,eye_lat,eye_gate,eye_esc,profile]
"""

import argparse
import os
import sys
from math import cos, radians, sin

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
ALL = ("iso", "top", "masks", "moradas", "eye_lat", "eye_gate", "eye_esc", "profile")
STRUCT_COLS = ("MORADAS", "STREETS")


def parse_args():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    p = argparse.ArgumentParser()
    p.add_argument("--blend", default=DEFAULT_BLEND)
    p.add_argument("--out", default=DEFAULT_OUT)
    p.add_argument("--only", default=",".join(ALL))
    return p.parse_args(argv)


def setup_render(scene):
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = SAMPLES
    scene.cycles.use_denoising = True
    scene.render.image_settings.file_format = "PNG"
    scene.render.resolution_x, scene.render.resolution_y = C.RENDER_RES
    world = bpy.data.worlds.new("TMP_world")
    world.use_nodes = True
    bg = world.node_tree.nodes["Background"]
    bg.inputs["Color"].default_value = (0.60, 0.63, 0.68, 1)
    bg.inputs["Strength"].default_value = 1.0
    scene.world = world
    sun = bpy.data.objects.new("TMP_sun", bpy.data.lights.new("TMP_sun", "SUN"))
    sun.data.energy = 3.0
    sun.data.angle = radians(2.0)
    sun.rotation_euler = Euler((radians(55), 0, radians(-45)))   # desde el SO, 35 grados
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
    font = ImageFont.truetype("DejaVuSans-Bold.ttf", 22)
    small = ImageFont.truetype("DejaVuSans.ttf", 20)
    for text, pt in labels:
        p = world_to_camera_view(scene, cam, Vector(pt))
        if not (0 <= p.x <= 1 and 0 <= p.y <= 1 and p.z > 0):
            continue
        px, py = p.x * W, (1 - p.y) * H
        d.ellipse([px - 5, py - 5, px + 5, py + 5], outline=(255, 255, 255), width=3)
        tx, ty = px + 12, py - 32
        bb = d.textbbox((tx, ty), text, font=font)
        if bb[2] > W - 10:
            tx = px - 12 - (bb[2] - bb[0])
            bb = d.textbbox((tx, ty), text, font=font)
        d.rectangle([bb[0] - 5, bb[1] - 3, bb[2] + 5, bb[3] + 3], fill=(0, 0, 0))
        d.text((tx, ty), text, fill=(255, 255, 255), font=font)
    d.rectangle([0, 0, W, 38], fill=(0, 0, 0))
    d.text((12, 8), title, fill=(255, 255, 255), font=small)
    if legend:
        y = H - 10 - 27 * len(legend)
        for txt in legend:
            bb = d.textbbox((12, y), txt, font=small)
            d.rectangle([bb[0] - 6, bb[1] - 3, bb[2] + 6, bb[3] + 3], fill=(0, 0, 0))
            d.text((12, y), txt, fill=(255, 255, 255), font=small)
            y += 27
    img.save(path)


def zlab(x, y, dz=0.0):
    return (x, y, T.height(x, y) + dz)


def pol(ang, r):
    return C.polar(ang, r)[:2]


def sector_labels():
    out = [("Plaza +8.0", zlab(0, 0))]
    for _k, (name, ang, _h, _r) in C.DISTRICTS_CARDINAL.items():
        out.append((name, zlab(*pol(ang + 12, 130))))
    for _k, (name, ang, _h, _r) in C.MORADAS.items():
        out.append((name, zlab(*pol(ang, 150))))
    return out


# ---------------------------------------------------------------------------
def visible_lateral(phi):
    """Borde lateral cuya cara mira a la camara (camara en el SE)."""
    best = None
    for side in (-1, 1):
        tb = phi + side * C.MORADA_HALF_ANGLE
        e = (cos(radians(tb)), sin(radians(tb)))
        n = (-e[1], e[0]) if side > 0 else (e[1], -e[0])
        score = n[0] * 1.0 + n[1] * -1.0
        if best is None or score > best[0]:
            best = (score, side, tb, e, n)
    return best


def morada_capture(scene, cam_iso, key, phi, P):
    _s, _side, tb, e, n = visible_lateral(phi)
    a = 172.0
    cx, cy = a * e[0] - 14.0 * n[0], a * e[1] - 14.0 * n[1]     # 14 m dentro de la Morada
    cam = iso_at(cam_iso, (cx, cy, T.height(cx, cy)), C.ISO_CHECK_ORTHO)
    path = P(f"iso45_{key}")
    render(scene, cam, path)
    labs = []
    for k in (4, 5, 6):
        r = C.TERRACE_START_R + C.TERRACE_DEPTH * (k - 0.5)
        x, y = r * e[0] - 10 * n[0], r * e[1] - 10 * n[1]
        labs.append((f"terraza {k} +{T.terrace_level(k):.1f}", zlab(x, y)))
    x, y = 170.05 * e[0] + 1.5 * n[0], 170.05 * e[1] + 1.5 * n[1]
    labs.append(("contrafuerte (muro 4 m)", zlab(x, y)))
    x, y = 162.0 * e[0] + 2.0 * n[0], 162.0 * e[1] + 2.0 * n[1]
    labs.append(("escalera 2.5 m", zlab(x, y)))
    annotate(scene, cam, path, f"{key}: CAM_Iso a ortho {C.ISO_CHECK_ORTHO:.0f} (escala de juego), "
             f"borde lateral a {tb % 360:.0f} grados", labs,
             ["Pretil 0.6 m en bordes de terraza, 0.9 m en muros > 3 m; contrafuertes cada 8 m entre escaleras",
              "Material del juego (MAT_Terrain_City + MAT_Stone_Limestone); luz de prueba desde el SO"])


def profile_plot(scene, path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    dg = bpy.context.evaluated_depsgraph_get()
    verts, polys = [], []
    objs = [bpy.data.objects["TRN_City"]] + [o for c in STRUCT_COLS for o in bpy.data.collections[c].objects]
    for o in objs:
        ev = o.evaluated_get(dg)
        me = ev.to_mesh()
        mw = o.matrix_world
        off = len(verts)
        verts += [mw @ v.co for v in me.vertices]
        polys += [[off + i for i in p.vertices] for p in me.polygons]
        ev.to_mesh_clear()
    bvh = BVHTree.FromPolygons(verts, polys)

    def zat(x, y):
        hit = bvh.ray_cast(Vector((x, y, 100.0)), Vector((0, 0, -1)))
        return hit[0].z if hit[0] else float("nan")

    def line(p0, p1, step):
        p0, p1 = Vector(p0), Vector(p1)
        L = (p1 - p0).length
        n = max(2, int(L / step))
        xs, zs = [], []
        for i in range(n + 1):
            q = p0.lerp(p1, i / n)
            xs.append(L * i / n)
            zs.append(zat(q.x, q.y))
        return xs, zs

    fig = plt.figure(figsize=(19.2, 13.5), dpi=100)
    gs = fig.add_gridspec(3, 3, height_ratios=[1.4, 1.0, 1.0], hspace=0.5, wspace=0.25)
    ax = fig.add_subplot(gs[0, :])
    for ang, lab, col in ((90.0, "Mercado: eje de la avenida (90°)", "#1f4e79"),
                          (75.0, "Mercado fuera del eje (75°)", "#3a3a3a"),
                          (40.0, "Morada NE fuera de la calle (40°) + pretiles", "#9a5b2a")):
        xs, zs = line((0, 0), pol(ang, C.TERRAIN_RADIUS - 0.01), 0.05)
        ax.plot(xs, zs, color=col, lw=1.4, label=lab)
    for z, t in ((8.0, "plaza +8.0"), (6.0, "DATUM +6.0"), (4.5, "+4.5"), (9.5, "+9.5"), (0.0, "yermo 0")):
        ax.axhline(z, color="#999", lw=0.6, ls="--")
        ax.text(1, z + 0.12, t, fontsize=8, color="#555")
    for r in (60, 90, 105, 119, 133, 147, 150, 161, 165, 175, 176, 189, 196, 204, 212):
        ax.axvline(r, color="#ddd", lw=0.5, zorder=0)
        ax.text(r, -1.15, str(r), fontsize=7, ha="center", color="#666")
    ax.set_xlim(0, 213)
    ax.set_ylim(-1.4, 11.2)
    ax.set_aspect(PROFILE_VEXAG)
    ax.set_ylabel("Z (m)")
    ax.set_title(f"Cortes radiales (raycast sobre terreno + estructuras). Exageracion vertical x{PROFILE_VEXAG:.0f}",
                 fontsize=11)
    ax.legend(loc="lower center", fontsize=9)

    def detail(axd, p0, p1, title, xlabel):
        xs, zs = line(p0, p1, 0.01)
        axd.plot(xs, zs, color="#9a5b2a", lw=1.5)
        axd.set_aspect("equal")
        axd.set_title(title, fontsize=10)
        axd.grid(True, color="#e5e5e5", lw=0.5)
        axd.set_xlabel(xlabel)

    tb = 25.0                                   # borde Morada NE / Oficios
    e = Vector((cos(radians(tb)), sin(radians(tb))))
    n_card = Vector((e.y, -e.x))
    c = e * 170.05                              # contrafuerte en r = 170.05
    detail(fig.add_subplot(gs[1, 0]), c - n_card * 4, c + n_card * 5,
           "Muro lateral r=170 (1:1): Morada +8.5 | Oficios +4.5", "m (Morada -> Oficios)")
    a = radians(45.0)
    ed = Vector((cos(a), sin(a)))
    detail(fig.add_subplot(gs[1, 1]), ed * 93.0, ed * 107.0, "Escalinata NE en el eje (1:1)", "m desde r=93")
    detail(fig.add_subplot(gs[1, 2]), (5.0, 186.0), (25.0, 186.0), "Borde de plazoleta Mercado u=186 (1:1)", "x (m)")

    axc = fig.add_subplot(gs[2, :])
    for R, col in ((120.0, "#6b8e23"), (150.0, "#3a3a3a"), (185.0, "#9a5b2a")):
        angs = [i * 0.02 for i in range(0, int(90 / 0.02) + 1)]
        zs = [zat(*pol(aa, R)) for aa in angs]
        axc.plot(angs, zs, color=col, lw=1.3, label=f"r = {R:.0f} m")
    for aa in (0, 25, 45, 65, 90):
        axc.axvline(aa, color="#ccc", lw=0.5)
    axc.set_xlim(0, 90)
    axc.set_xlabel("angulo: 0 Oficios (E) -> 45 Morada NE -> 90 Mercado (N). Bordes en 25 y 65 (muros, sin mezcla)")
    axc.set_ylabel("Z (m)")
    axc.set_title("Corte lateral (arco): muros de contencion verticales entre sectores (picos = pretiles)", fontsize=10)
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
    os.makedirs(args.out, exist_ok=True)
    setup_render(scene)
    cam_iso = bpy.data.objects[C.CAM_ISO_NAME]
    trn = bpy.data.objects["TRN_City"]
    P = lambda name: os.path.join(args.out, f"{TAG}_{name}.png")  # noqa: E731
    gates = [(n.replace("MARKER_", ""), tuple(bpy.data.objects[n].location)) for n in C.GATES]
    legend = ["Material del juego: tierra / suciedad / piedra / muro segun mascaras x (AO + borde)",
              "Piedra clara: pretiles, escaleras, contrafuertes, escalinatas"]

    if "iso" in only:
        cam = iso_at(cam_iso, C.CAM_ISO_TARGET, OVERVIEW_ORTHO)
        render(scene, cam, P("iso_overview"))
        annotate(scene, cam, P("iso_overview"), f"TRN_City v2 - CAM_Iso (X54.736 Z45), ortho TEMPORAL {OVERVIEW_ORTHO:.0f}",
                 sector_labels() + gates, legend)
    if "top" in only:
        cam = new_cam("TMP_top", ortho=TOP_ORTHO)
        cam.location = (0, 0, 400)
        render(scene, cam, P("top"))
        annotate(scene, cam, P("top"), f"TRN_City v2 - cenital (Norte arriba), ortho {TOP_ORTHO:.0f}",
                 sector_labels() + gates, legend)
    if "masks" in only:
        mm = bpy.data.materials.new("TMP_masks")
        mm.use_nodes = True
        N, L = mm.node_tree.nodes, mm.node_tree.links
        for nd in list(N):
            if nd.type != "OUTPUT_MATERIAL":
                N.remove(nd)
        comb = N.new("ShaderNodeCombineXYZ")
        for i, name in enumerate(("retaining_mask", "dirt_mask", "stone_mask")):
            a = N.new("ShaderNodeVertexColor")
            a.layer_name = name
            bw = N.new("ShaderNodeRGBToBW")
            L.new(a.outputs["Color"], bw.inputs[0])
            L.new(bw.outputs[0], comb.inputs[i])
        em = N.new("ShaderNodeEmission")
        L.new(comb.outputs[0], em.inputs["Color"])
        L.new(em.outputs[0], N["Material Output"].inputs["Surface"])
        real = trn.data.materials[0]
        trn.data.materials[0] = mm
        hidden = [o for c in STRUCT_COLS for o in bpy.data.collections[c].objects]
        for o in hidden:
            o.hide_render = True
        cam = new_cam("TMP_top_m", ortho=TOP_ORTHO)
        cam.location = (0, 0, 400)
        render(scene, cam, P("top_masks"), view="Standard")
        annotate(scene, cam, P("top_masks"), "Mascaras (cenital): R = retaining_mask, G = dirt_mask, B = stone_mask",
                 [], ["Rojo/magenta: caras de muro | Verde: tierra | Azul: piedra (plaza, base muralla, talud)",
                      "(colores de depuracion, no son materiales del juego)"])
        trn.data.materials[0] = real
        for o in hidden:
            o.hide_render = False
    if "moradas" in only:
        for key, phi in T.DIAGONAL_ANGLE.items():
            morada_capture(scene, cam_iso, key, phi, P)
    if "eye_lat" in only:
        tb = 25.0
        e = Vector((cos(radians(tb)), sin(radians(tb))))
        n_card = Vector((e.y, -e.x))
        eye = e * 176.0 + n_card * 9.0
        tgt = e * 166.0 + n_card * 0.5
        cam = new_cam("TMP_eye_lat", lens=24)
        look_at(cam, (eye.x, eye.y, T.height(eye.x, eye.y) + EYE), (tgt.x, tgt.y, 7.0))
        render(scene, cam, P("eye_muro_lateral_NE"))
        annotate(scene, cam, P("eye_muro_lateral_NE"),
                 "Altura de personaje en Oficios (r=176, a 9 m del muro) mirando el muro lateral de Morada NE",
                 [("escalera (rellano +8.5)", (*(e * 166.5 + n_card * 1.5), 8.6)),
                  ("contrafuerte", (*(e * 170.05 + n_card * 1.4), 6.0)),
                  ("pretil 0.9 m", (*(e * 172.0 - n_card * 0.2), 9.3))])
    if "eye_gate" in only:
        cam = new_cam("TMP_eye_gate", lens=24)
        ex, ey = 27.0, 172.0                     # fuera del eje, en la rampa 175-196 / plano 165-175
        look_at(cam, (ex, ey, T.height(ex, ey) + EYE), (4.0, 192.0, 5.6))
        render(scene, cam, P("eye_plazoleta_N"))
        annotate(scene, cam, P("eye_plazoleta_N"),
                 "Altura de personaje en Mercado fuera del eje (x=27, y=172) mirando la plazoleta de la Puerta Norte",
                 [("plazoleta +6.0 (30 x 20 m)", (0.0, 186.0, 6.0)), ("MARKER_Gate_N", (0.0, 200.0, 6.0)),
                  ("borde de plazoleta: 1.4 m en u=176", (15.2, 177.0, 5.4)),
                  ("rampa del eje 150-176", (0.0, 165.0, T.height(0.0, 165.0)))])
    if "eye_esc" in only:
        a = radians(45.0)
        ed = Vector((cos(a), sin(a)))
        nd = Vector((-ed.y, ed.x))
        eye = ed * 91.0
        cam = new_cam("TMP_eye_esc", lens=24)
        look_at(cam, (eye.x, eye.y, C.DATUM + EYE), (*(ed * 112.0), 4.8))
        render(scene, cam, P("eye_escalinata_NE"))
        annotate(scene, cam, P("eye_escalinata_NE"),
                 "Altura de personaje en la zona de hitos (r=91, +6.0) mirando la escalinata NE",
                 [("descanso 2 m (+5.25)", (*(ed * 100.0), 5.25)),
                  ("pasamanos 0.9 m", (*(ed * 97.0 + nd * 3.2), 6.45)),
                  ("terraza 1 +4.5", (*(ed * 110.0), 4.5))])
    if "profile" in only:
        profile_plot(scene, P("profile"))


if __name__ == "__main__":
    main()
