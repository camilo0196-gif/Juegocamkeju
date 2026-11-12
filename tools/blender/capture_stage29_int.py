"""
CONCORDIA - capturas de la etapa 29 (interiores unicos) sobre blender/concordia_interiors_unicos_v01.blend.
Por interior: <nombre>_iso (CAM_Iso con muros cercanos, techo y plantas altas ocultos), vistas a 1.7 m y las
particulares (planta alta, vitrinas, mostrador, boveda, seccion con la cubierta exterior). En los MARKER_NPC_Slot se
pone un maniqui provisional de 1.75 m (solo en la captura) para ver al NPC por la ventanilla.
Las luces son los Empties de 'Lights' convertidos en puntos de luz solo para la captura (Godot hornea las suyas).
python capture_stage29_int.py [-- nombre ...]
"""

import math
import os
import sys

import bpy
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import capture_stage02 as K  # noqa: E402
import capture_stage27 as C27  # noqa: E402

REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
BLEND = os.path.join(REPO, "blender", "concordia_interiors_unicos_v01.blend")
OUT = os.path.join(REPO, "docs", "captures")
ONLY = set(sys.argv[sys.argv.index("--") + 1:]) if "--" in sys.argv else set()
BASE_HIDE = ("WALL_Near_A", "WALL_Near_B", "CEILING")


def P(n):
    return os.path.join(OUT, f"stage29_{n}.png")


def want(n):
    return not ONLY or n in ONLY or n.split("_")[0] in ONLY


def mannequins(root):
    """Maniqui gris (cilindro + cabeza) en cada MARKER_NPC_Slot, solo para la captura."""
    made = []
    mat = bpy.data.materials.get("TMP_Maniqui") or bpy.data.materials.new("TMP_Maniqui")
    mat.use_nodes = True
    mat.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.42, 0.40, 0.37, 1)
    for e in root.children_recursive:
        if e.type == "EMPTY" and e.name.startswith("MARKER_NPC_Slot"):
            p = e.matrix_world.translation
            bpy.ops.mesh.primitive_cylinder_add(radius=0.2, depth=1.45, location=(p.x, p.y, p.z + 0.725), vertices=12)
            b = bpy.context.active_object
            bpy.ops.mesh.primitive_uv_sphere_add(radius=0.14, location=(p.x, p.y, p.z + 1.6), segments=12, ring_count=8)
            h = bpy.context.active_object
            for o in (b, h):
                o.data.materials.append(mat)
                o.name = "TMP_Maniqui"
                made.append(o)
    return made


def shot(scene, cam, name, title, labels=()):
    K.render(scene, cam, P(name))
    K.annotate(scene, cam, P(name), title, list(labels))
    bpy.data.objects.remove(cam)


def eye(scene, fm, frm, to, lens, name, title, labels=()):
    cam = K.new_cam("TMP_eye", lens=lens)
    K.look_at(cam, fm @ Vector(frm), fm @ Vector(to))
    shot(scene, cam, name, title, labels)


def tesoreria(scene):
    root = bpy.data.objects["INT_Tesoreria"]
    fm = bpy.data.objects["INT_Tesoreria_Frame"].matrix_world
    C27.only_collections({"INT_TESORERIA"})
    tmp = C27.lights_from_empties(root) + mannequins(root)
    up = ("LEVEL_1", "Furniture_L1", "WALL_Near_Despacho")
    lab = [("Tesorero (Vender)", fm @ Vector((-11.9, 3.7, 2.2))), ("Cambista (Cambio)", fm @ Vector((-11.9, -1.1, 2.2))),
           ("Tubos de luz", fm @ Vector((1.0, -1.3, 4.8))), ("Escalera", fm @ Vector((12.2, -0.5, 3.2))),
           ("Contaduria", fm @ Vector((-1.0, -5.5, 2.6)))]
    for x, t in ((-7.15, "Brillante"), (-3.12, "Opaca"), (0.92, "Madura"), (4.95, "Latente")):
        lab.append((f"Vitrina {t}", fm @ Vector((x, -0.45, 2.3))))
    if want("tesoreria_iso"):
        C27.set_hidden(root, BASE_HIDE + up)
        cam = C27.iso_cam(fm @ Vector((0.0, 0.0, 1.5)), 29.0)
        shot(scene, cam, "tesoreria_iso", "Tesoreria (26.4 x 13.6 x 8.8 m) en CAM_Iso, planta baja: muros cercanos, techo y "
             "LEVEL_1 ocultos", lab)
        C27.set_hidden(root, BASE_HIDE + up, False)
    if want("tesoreria_alta"):
        C27.set_hidden(root, BASE_HIDE + ("WALL_Near_Despacho",))
        cam = C27.iso_cam(fm @ Vector((-1.0, -3.0, 5.4)), 25.0)
        shot(scene, cam, "tesoreria_alta", "Tesoreria, planta alta (LEVEL_1): galeria, archivo y despacho con la caja "
             "fuerte (WALL_Near_Despacho oculto)",
             [("Caja fuerte", fm @ Vector((-8.0, -6.3, 6.6))), ("Despacho", fm @ Vector((-10.6, -3.0, 6.2))),
              ("Galeria", fm @ Vector((3.0, -2.6, 6.0)))])
        C27.set_hidden(root, BASE_HIDE + ("WALL_Near_Despacho",), False)
    C27.set_hidden(root, ("CEILING",), False)
    if want("tesoreria_calle"):
        eye(scene, fm, (2.0, 5.6, 1.7), (-8.5, -0.6, 1.9), 17, "tesoreria_calle",
            "Tesoreria a 1.7 m desde la puerta: mostradores con reja, vitrinas, arcada y tubos de luz")
    if want("tesoreria_mostrador"):
        eye(scene, fm, (-7.6, 5.4, 1.65), (-11.6, 3.4, 1.45), 30, "tesoreria_mostrador",
            "Mostrador 1 (Vender) a 1.7 m: el Tesorero (maniqui provisional) por la ventanilla de cajero, balanza grande")
    if want("tesoreria_vitrinas"):
        eye(scene, fm, (-1.1, 5.4, 2.0), (-1.1, -0.45, 0.9), 13, "tesoreria_vitrinas",
            "Vitrinas a 1.7 m: Brillante (armario), Opaca (mesa), Madura (pedestal, emisiva) y Latente (mesa)")
    for o in tmp:
        bpy.data.objects.remove(o)


def santuario(scene):
    import stage29_santuario as S
    S.captures(scene, sys.modules[__name__])


def main():
    bpy.ops.wm.open_mainfile(filepath=BLEND)
    scene = bpy.context.scene
    K.setup_render(scene)
    scene.cycles.samples = 48
    C27.interior_world(scene)
    if bpy.data.objects.get("INT_Tesoreria") and any(want(n) for n in ("tesoreria_iso", "tesoreria_alta", "tesoreria_calle",
                                                                         "tesoreria_mostrador", "tesoreria_vitrinas")):
        tesoreria(scene)
    if bpy.data.objects.get("INT_Santuario"):
        santuario(scene)
    _ = math


if __name__ == "__main__":
    main()
