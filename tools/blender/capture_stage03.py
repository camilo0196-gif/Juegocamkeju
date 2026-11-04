"""
CONCORDIA - capturas de verificacion de la etapa 03 (Plaza del Portal).

Materiales reales; luz y cielo temporales. Los volumenes del Faro (40 m) y del Obelisco
(25 m) se muestran como PROXIES TEMPORALES semitransparentes (no se guardan): sirven para
juzgar escala y oclusion, no son los edificios.

Uso:
    python tools/blender/capture_stage03.py [--only top,iso120,iso220,eye_n,masks]
"""

import argparse
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
import stage03_plaza as P3  # noqa: E402

REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
DEFAULT_BLEND = os.path.join(REPO, "blender", f"{C.BLEND_BASENAME}_v03.blend")
DEFAULT_OUT = os.path.join(REPO, "docs", "captures")
TAG = "stage03"
ALL = ("top", "iso120", "iso220", "eye_n", "masks")


def parse_args():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    p = argparse.ArgumentParser()
    p.add_argument("--blend", default=DEFAULT_BLEND)
    p.add_argument("--out", default=DEFAULT_OUT)
    p.add_argument("--only", default=",".join(ALL))
    return p.parse_args(argv)


def proxy_material():
    m = bpy.data.materials.new("TMP_proxy")
    m.use_nodes = True
    N, L = m.node_tree.nodes, m.node_tree.links
    b = N["Principled BSDF"]
    b.inputs["Base Color"].default_value = (0.55, 0.55, 0.58, 1)
    b.inputs["Alpha"].default_value = 0.35
    m.blend_method = "BLEND" if hasattr(m, "blend_method") else None
    return m


def add_proxies():
    col = bpy.data.collections.new("TMP_Proxies")
    bpy.context.scene.collection.children.link(col)
    mat = proxy_material()
    out = []
    for key in ("Faro", "Obelisco"):
        mk = bpy.data.objects["MARKER_" + key]
        h = mk["height_m"]
        if key == "Faro":
            bpy.ops.mesh.primitive_cylinder_add(vertices=32, radius=C.LANDMARK_PADS["Faro"][3][0] / 2,
                                                depth=h, location=(mk.location.x, mk.location.y, mk.location.z + h / 2))
        else:
            s = C.LANDMARK_PADS["Obelisco"][3][0]
            bpy.ops.mesh.primitive_cube_add(size=1, location=(mk.location.x, mk.location.y, mk.location.z + h / 2))
            o = bpy.context.active_object
            o.scale = (s, s, h)
            o.rotation_euler = (0, 0, radians(C.LANDMARK_PADS["Obelisco"][0]))
        o = bpy.context.active_object
        for c in o.users_collection:
            c.objects.unlink(o)
        col.objects.link(o)
        o.data.materials.append(mat)
        out.append((f"{key} {h:.0f} m (proxy temporal)", (mk.location.x, mk.location.y, mk.location.z + h)))
    return out


def overlay(scene, cam, path, circles=(), dots=()):
    """Dibuja circulos de referencia (r, etiqueta) y puntos de marcadores sobre la imagen."""
    from PIL import Image, ImageDraw, ImageFont
    img = Image.open(path).convert("RGB")
    d = ImageDraw.Draw(img)
    W, H = img.size
    font = ImageFont.truetype("DejaVuSans.ttf", 18)
    for R, label, col in circles:
        pts = []
        for i in range(0, 361, 3):
            x, y = R * cos(radians(i)), R * sin(radians(i))
            p = world_to_camera_view(scene, cam, Vector((x, y, P3.T.height(x, y) + 0.05)))
            pts.append((p.x * W, (1 - p.y) * H))
        for k in range(0, len(pts) - 1, 2):
            d.line([pts[k], pts[k + 1]], fill=col, width=3)
        lx, ly = pts[20]
        d.text((lx + 6, ly - 22), label, fill=col, font=font)
    for loc, col in dots:
        p = world_to_camera_view(scene, cam, Vector(loc))
        if 0 <= p.x <= 1 and 0 <= p.y <= 1:
            px, py = p.x * W, (1 - p.y) * H
            d.ellipse([px - 4, py - 4, px + 4, py + 4], fill=col, outline=(0, 0, 0))
    img.save(path)


def marker_dots():
    out = []
    for o in bpy.data.collections["PLAZA_MARKERS"].objects:
        n = o.name
        col = (255, 220, 60) if "Descent" in n else ((120, 255, 120) if "Runestone" in n else (255, 255, 255))
        out.append((tuple(o.location), col))
    return out


def main_labels():
    labs = [("Portal (pedestal r6, +8.9)", tuple(bpy.data.objects["MARKER_Portal_Center"].location))]
    for n, t in (("MARKER_Faro", "Torre del Faro"), ("MARKER_Santuario", "Santuario"),
                 ("MARKER_SalonHazanas", "Salon de las Hazanas"), ("MARKER_Obelisco", "Obelisco")):
        labs.append((t, tuple(bpy.data.objects[n].location)))
    labs.append(("Parcela 01", tuple(bpy.data.objects["MARKER_PlazaBuilding_01"].location)))
    return labs


def main():
    args = parse_args()
    only = set(args.only.split(","))
    bpy.ops.wm.open_mainfile(filepath=args.blend)
    scene = bpy.context.scene
    os.makedirs(args.out, exist_ok=True)
    K.setup_render(scene)
    cam_iso = bpy.data.objects[C.CAM_ISO_NAME]
    P = lambda name: os.path.join(args.out, f"{TAG}_{name}.png")  # noqa: E731
    circles = [(C.PLAZA_CLEAR_R[0], "r=15", (90, 200, 255)), (C.PLAZA_CLEAR_R[1], "r=48 zona despejada", (90, 200, 255)),
               (C.PLAZA_RADIUS, "r=60 borde de plaza", (255, 255, 255))]
    legend = ["Puntos: blancos = marcadores, amarillos = pedestales de descenso (21), verdes = piedras runicas (7)",
              "Lineas discontinuas azules: zona despejada r 15-48. Canales de luz azul #8FD0FF hacia el Faro (NE)"]

    if "top" in only:
        cam = K.new_cam("TMP_top", ortho=220.0)
        cam.location = (0, 0, 300)
        K.render(scene, cam, P("top"))
        overlay(scene, cam, P("top"), circles, marker_dots())
        K.annotate(scene, cam, P("top"), "Plaza del Portal - cenital (Norte arriba), ortho 220", main_labels(), legend)
    if "iso120" in only:
        cam = K.iso_at(cam_iso, (0.0, 0.0, C.Z_PLAZA), C.CAM_ISO_ORTHO_SCALE)
        K.render(scene, cam, P("iso120"))
        overlay(scene, cam, P("iso120"), circles[:2], marker_dots())
        K.annotate(scene, cam, P("iso120"), "Plaza del Portal - CAM_Iso tal cual (ortho 120)", main_labels()[:1],
                   legend)
    proxies = []
    if "iso220" in only or "eye_n" in only:
        proxies = add_proxies()
    if "iso220" in only:
        cam = K.iso_at(cam_iso, (0.0, 0.0, C.Z_PLAZA), 220.0)
        K.render(scene, cam, P("iso220_proxies"))
        K.annotate(scene, cam, P("iso220_proxies"), "Plaza + hitos - CAM_Iso, ortho TEMPORAL 220, con volumenes "
                   "futuros como proxies temporales", main_labels() + proxies,
                   ["Proxies grises semitransparentes: Faro 14 x 40 m y Obelisco 5 x 5 x 25 m (solo para juzgar "
                    "escala y oclusion)"])
    if "eye_n" in only:
        cam = K.new_cam("TMP_eye_n", lens=24)
        ex, ey = 0.0, C.PLAZA_RADIUS
        K.look_at(cam, (ex, ey, P3.T.height(ex, ey) + K.EYE), (0.0, 0.0, 9.6))
        K.render(scene, cam, P("eye_avenida_N"))
        K.annotate(scene, cam, P("eye_avenida_N"),
                   "Altura de personaje en la entrada de la avenida Norte (r=60) mirando al Portal",
                   main_labels() + proxies)
    if "masks" in only:
        trn = bpy.data.objects["TRN_City"]
        mm = bpy.data.materials.new("TMP_plaza_masks")
        mm.use_nodes = True
        N, L = mm.node_tree.nodes, mm.node_tree.links
        for nd in list(N):
            if nd.type != "OUTPUT_MATERIAL":
                N.remove(nd)

        def attr(name):
            a = N.new("ShaderNodeVertexColor")
            a.layer_name = name
            bw = N.new("ShaderNodeRGBToBW")
            L.new(a.outputs["Color"], bw.inputs[0])
            return bw.outputs[0]

        def math(op, a, b):
            n = N.new("ShaderNodeMath")
            n.operation = op
            for i, v in enumerate((a, b)):
                if isinstance(v, float):
                    n.inputs[i].default_value = v
                else:
                    L.new(v, n.inputs[i])
            return n.outputs[0]
        ring = math("ROUND", math("MULTIPLY", attr("slab_ring_id"), 10.0), 0.0)
        parity = math("MODULO", ring, 2.0)
        comb = N.new("ShaderNodeCombineXYZ")
        L.new(attr("travertine_band"), comb.inputs[0])
        L.new(math("MAXIMUM", math("MULTIPLY", parity, 0.5), attr("magic_glow_mask")), comb.inputs[1])
        L.new(attr("repair_mask"), comb.inputs[2])
        em = N.new("ShaderNodeEmission")
        L.new(comb.outputs[0], em.inputs["Color"])
        L.new(em.outputs[0], N["Material Output"].inputs["Surface"])
        trn.data.materials[0] = mm
        for c in ("MORADAS", "STREETS", "PLAZA"):
            for o in list(bpy.data.collections[c].all_objects):
                if isinstance(o, bpy.types.Object):
                    o.hide_render = True
        cam = K.new_cam("TMP_top_m", ortho=130.0)
        cam.location = (0, 0, 300)
        K.render(scene, cam, P("masks"), view="Standard")
        K.annotate(scene, cam, P("masks"), "Mascaras de la plaza (cenital, ortho 130), colores de depuracion", [],
                   ["Rojo = travertine_band | Verde = anillo par (slab_ring_id) y magic_glow_mask | Azul = repair_mask",
                    "(las piezas estan ocultas en esta vista)"])


if __name__ == "__main__":
    main()
