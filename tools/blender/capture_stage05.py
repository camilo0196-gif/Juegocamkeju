"""
CONCORDIA - capturas de la etapa 05 (calles y parcelas).

  cenital            render cenital del terreno (Norte arriba) + parcelas y calles coloreadas por distrito
  plan               plano 2D del trazado (sin render) con leyenda
  iso_<distrito>     CAM_Iso (ortho ISO_ORTHO) sobre cada distrito, con huellas temporales de las parcelas
                     (losas de 0.25 m color distrito; oscuras = interior, claras = decoracion). Las huellas
                     solo existen durante la captura: no se guardan en el .blend.
"""

import argparse
import json
import os
import sys
from math import cos, radians, sin

import bpy
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import concordia_const as C  # noqa: E402
import capture_stage02 as K  # noqa: E402
import stage05_layout as LY  # noqa: E402
import stage05_plan_preview as PV  # noqa: E402
import terrain_profile as T  # noqa: E402

REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
DEFAULT_BLEND = os.path.join(REPO, "blender", f"{C.BLEND_BASENAME}_v05.blend")
DEFAULT_LAYOUT = os.path.join(REPO, "docs", "reports", "stage05_layout.json")
DEFAULT_OUT = os.path.join(REPO, "docs", "captures")
TAG = "stage05"
ISO_ORTHO = 125.0
TOP_ORTHO = 420.0
ALL = ("cenital", "iso_Mercado", "iso_Oficios", "iso_Clases", "iso_Razas")
LABEL_TYPES = ("posada", "registro", "tesoreria", "banco", "subasta", "reparaciones", "taller", "crisol", "gremio",
               "reposicion", "race_house")


def parse_args():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    p = argparse.ArgumentParser()
    p.add_argument("--blend", default=DEFAULT_BLEND)
    p.add_argument("--layout", default=DEFAULT_LAYOUT)
    p.add_argument("--out", default=DEFAULT_OUT)
    p.add_argument("--only", default=",".join(ALL))
    return p.parse_args(argv)


def ghost_material(name, rgb, alpha=1.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (rgb[0] / 255) ** 2.2, (rgb[1] / 255) ** 2.2, (rgb[2] / 255) ** 2.2, 1
    b.inputs["Roughness"].default_value = 0.8
    return m


def ghosts(lay, col):
    mats = {}
    for d, rgb in PV.DISTRICT_RGB.items():
        mats[(d, True)] = ghost_material(f"TMP_ghost_{d}_int", PV.shade(rgb, 0.85))
        mats[(d, False)] = ghost_material(f"TMP_ghost_{d}_dec", PV.shade(rgb, 1.2))
    by_mat = {}
    for pa in lay["parcels"]:
        z = pa.get("pad_z")
        key = (pa["district"], bool(pa["interior"]))
        by_mat.setdefault(key, []).append(pa)
    objs = []
    for key, items in by_mat.items():
        verts, faces = [], []
        for pa in items:
            obj = bpy.data.objects.get(pa["name"])
            z = obj.location.z if obj else T.height(*pa["center"])
            h = 0.25 if pa["type"] != "stall" else 0.6
            poly = pa["poly"] if pa["shape"] == "rect" else LY.circle_poly(pa["center"], pa["w"] / 2, 1.0)
            n = len(poly)
            b0 = len(verts)
            verts += [(x, y, z - 0.05) for x, y in poly] + [(x, y, z + h) for x, y in poly]
            faces.append(tuple(range(b0 + n - 1, b0 - 1, -1)))
            faces.append(tuple(range(b0 + n, b0 + 2 * n)))
            for i in range(n):
                j = (i + 1) % n
                faces.append((b0 + i, b0 + j, b0 + n + j, b0 + n + i))
        me = bpy.data.meshes.new(f"TMP_ghost_{key[0]}_{key[1]}")
        me.from_pydata(verts, [], faces)
        me.materials.append(mats[key])
        o = bpy.data.objects.new(me.name, me)
        col.objects.link(o)
        objs.append(o)
    return objs


def project(scene, cam, p, W, H):
    q = world_to_camera_view(scene, cam, Vector(p))
    return (q.x * W, (1 - q.y) * H)


def main():
    args = parse_args()
    only = set(args.only.split(","))
    bpy.ops.wm.open_mainfile(filepath=args.blend)
    scene = bpy.context.scene
    os.makedirs(args.out, exist_ok=True)
    K.setup_render(scene)
    with open(args.layout) as fh:
        lay = json.load(fh)
    cam_iso = bpy.data.objects[C.CAM_ISO_NAME]
    P = lambda n: os.path.join(args.out, f"{TAG}_{n}.png")  # noqa: E731
    for o in list(bpy.data.collections["WALL_KIT"].all_objects):
        o.hide_render = True
    for o in list(bpy.data.collections["WALL_LAYOUT"].objects):
        if o.name.endswith("-colonly"):
            o.hide_render = True
    from PIL import Image, ImageDraw, ImageFont
    if "cenital" in only:
        cam = K.new_cam("TMP_top", ortho=TOP_ORTHO)
        cam.location = (0, 0, 400)
        rx, ry = scene.render.resolution_x, scene.render.resolution_y
        scene.render.resolution_x = scene.render.resolution_y = 2000
        K.render(scene, cam, P("cenital"))
        img = Image.open(P("cenital")).convert("RGBA")
        W, H = img.size
        ov = Image.new("RGBA", img.size, (0, 0, 0, 0))
        d = ImageDraw.Draw(ov)
        for r in lay["roads"]:
            rgb = PV.DISTRICT_RGB.get(r["district"], (150, 150, 150))
            pts = [project(scene, cam, (x, y, 0), W, H) for x, y in r["pts"]]
            wpx = max(1, int(2 * r["halfw"][0] / TOP_ORTHO * W))
            d.line(pts, fill=rgb + (70,), width=wpx)
        for pa in lay["parcels"]:
            rgb = PV.DISTRICT_RGB[pa["district"]]
            fill = PV.shade(rgb, 0.85) if pa["interior"] else PV.shade(rgb, 1.2)
            poly = pa["poly"] if pa["shape"] == "rect" else LY.circle_poly(pa["center"], pa["w"] / 2, 1.0)
            d.polygon([project(scene, cam, (x, y, 0), W, H) for x, y in poly], fill=fill + (215,),
                      outline=PV.shade(rgb, 0.4) + (255,))
        for z in lay["zones"]:
            rgb = PV.DISTRICT_RGB.get(z["district"], (160, 160, 160))
            d.polygon([project(scene, cam, (x, y, 0), W, H) for x, y in z["poly"]], outline=PV.shade(rgb, 0.5) + (255,))
        img = Image.alpha_composite(img, ov).convert("RGB")
        dd = ImageDraw.Draw(img)
        f = ImageFont.truetype("DejaVuSans-Bold.ttf", 22)
        for name, ang in (("MERCADO", 90.0), ("OFICIOS", 0.0), ("CLASES", 180.0), ("RAZAS", 270.0)):
            x, y = project(scene, cam, (cos(radians(ang)) * 128 - sin(radians(ang)) * 0, sin(radians(ang)) * 128, 0),
                           W, H)
            dd.text((x - 50, y - 12), name, fill=(255, 255, 255), font=f, stroke_width=3, stroke_fill=(0, 0, 0))
        img.save(P("cenital"))
        K.annotate(scene, cam, P("cenital"), "Etapa 05 - calles y parcelas por distrito (cenital, Norte arriba)", [],
                   ["Ocre = Mercado | Oxido = Oficios | Azul pizarra = Clases | Verde = Razas | Gris = diagonales",
                    "Parcela oscura = interior (servicio) | clara = decoracion | franja = calle del distrito"])
        scene.render.resolution_x, scene.render.resolution_y = rx, ry
        PV.draw_plan(lay, None, P("plan"), scale=4.0, title="Etapa 05 - plano del trazado (2D, Norte arriba)")
    gcol = bpy.data.collections.new("TMP_GHOSTS")
    scene.collection.children.link(gcol)
    gh = ghosts(lay, gcol)
    for D, phi in LY.DISTRICT_AXIS.items():
        tag = f"iso_{D}"
        if tag not in only:
            continue
        cx, cy = LY.to_world(130.0, 0.0, phi)
        cam = K.iso_at(cam_iso, (cx, cy, T.height(cx, cy)), ISO_ORTHO)
        K.render(scene, cam, P(tag))
        labels = []
        for pa in lay["parcels"]:
            if pa["district"] == D and pa["type"] in LABEL_TYPES:
                o = bpy.data.objects.get(pa["name"])
                z = (o.location.z if o else 6.0) + 0.3
                labels.append((pa["label"], (pa["center"][0], pa["center"][1], z)))
        for pz in lay["plazas"]:
            if pz["district"] == D and pz["type"] in ("fountain_square", "market_square", "training_square", "plazoleta"):
                c = pz["circle"]["c"] if "circle" in pz else LY.poly_centroid(pz["poly"])
                labels.append(({"fountain_square": "Fuente del Mercado", "market_square": "Plaza de Provisiones",
                                "training_square": "Plaza de las Armas", "plazoleta": "plazoleta 30 m"}[pz["type"]],
                               (c[0], c[1], T.height(*c) + 0.3)))
        K.annotate(scene, cam, P(tag), f"{D} - CAM_Iso ortho {ISO_ORTHO:g} - huellas temporales (oscuro = interior)",
                   labels)
    for o in gh:
        bpy.data.objects.remove(o)
    bpy.data.collections.remove(gcol)


if __name__ == "__main__":
    main()
