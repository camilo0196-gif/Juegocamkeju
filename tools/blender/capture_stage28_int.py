"""
CONCORDIA - capturas de la etapa 28 (vitrinas e interiores de las Moradas) sobre blender/concordia_moradas_int_v01.blend.
  vitrinas              las 3 vitrinas (LOD0) con sus slots, en CAM_Iso
  <plantilla>_iso       CAM_Iso con muros cercanos, techo y tabique/entreplanta ocultos
  <plantilla>_calle     a 1.7 m desde la puerta
  casa_grande_alta      CAM_Iso de la entreplanta (planta alta visible, techo oculto)
`-- nombre ...` para repetir solo algunas.
"""

import os
import sys

import bpy
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import capture_stage02 as K  # noqa: E402
import capture_stage27 as C27  # noqa: E402
import stage28_moradas_int as MI  # noqa: E402

REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
BLEND = os.path.join(REPO, "blender", "concordia_moradas_int_v01.blend")
OUT = os.path.join(REPO, "docs", "captures")
ONLY = set(sys.argv[sys.argv.index("--") + 1:]) if "--" in sys.argv else set()
VIEWS = {  # plantilla: (ortho iso, objetivo iso, ojo a 1.7 m, objetivo a 1.7 m, lente)
    "habitacion": (7.5, (0.0, -0.3, 0.8), (1.2, 2.2, 1.7), (-1.0, -1.8, 1.0), 20),
    "casa_pequena": (11.0, (0.0, -0.6, 0.8), (1.6, 0.9, 1.7), (-1.4, -3.4, 1.0), 18),
    "casa_grande": (13.0, (0.0, 0.0, 1.0), (2.6, 4.2, 1.7), (-1.5, -3.5, 1.2), 18),
}
TITLES = {"habitacion": "Habitacion 4 x 5 m (casa comunal)", "casa_pequena": "Casa pequena 6 x 8 m con patio",
          "casa_grande": "Casa grande 8 x 10 m, dos plantas"}


def P(n):
    return os.path.join(OUT, f"stage28_{n}.png")


def want(n):
    return not ONLY or n in ONLY


def labels_for(root, fm):
    out = []
    for e in root.children_recursive:
        n = e.name.split("__")[0]
        if e.type == "EMPTY" and n.startswith(("MARKER_TrophyCase", "MARKER_Interact_Chest", "MARKER_WorkStation",
                                               "MARKER_Garden", "MARKER_Reception")) and e.location.z < 1.0:
            lab = {"MARKER_TrophyCase": "Vitrina", "MARKER_TrophyCase_02": "Vitrina de mesa",
                   "MARKER_Interact_Chest": f"Baul ({e.get('slots')})", "MARKER_WorkStation_01": "Mesa de oficio 1",
                   "MARKER_WorkStation_02": "Mesa de oficio 2", "MARKER_Garden": "Jardin de hierbas",
                   "MARKER_Reception": "Sala para recibir"}.get(n)
            if lab:
                out.append((lab, e.matrix_world.translation + Vector((0, 0, 1.4))))
    return out


def main():
    bpy.ops.wm.open_mainfile(filepath=BLEND)
    scene = bpy.context.scene
    K.setup_render(scene)
    scene.cycles.samples = 48
    if want("vitrinas"):
        C27.only_collections({"BLD_TROPHY_CASES"})
        cam = C27.iso_cam((7002.5, 0.0, 0.8), 5.5)
        lab = [(f"{o['trophy_case']} ({sum(len(p.vertices) - 2 for p in o.data.polygons)} tris, {o['slots']} slots)",
                o.location + Vector((0, 0, 2.1))) for o in bpy.data.collections["BLD_TROPHY_CASES"].objects
               if o.get("trophy_case") and o.type == "MESH"]
        K.render(scene, cam, P("vitrinas"))
        K.annotate(scene, cam, P("vitrinas"), "Vitrina de trofeos: pared, mesa y nichos (un solo material; LOD1/LOD2 aparte)",
                   lab)
        bpy.data.objects.remove(cam)
    C27.interior_world(scene)
    for name, (ortho, tgt, eye, look, lens) in VIEWS.items():
        if not any(want(f"{name}_{v}") for v in ("iso", "calle", "alta")):
            continue
        C27.only_collections({f"INT_MORADA_{name.upper()}"})
        root = next(o for o in bpy.data.objects if str(o.get("interior_of", "")).lower() == f"morada_{name}")
        fm = next(c for c in root.children if c.name.endswith("_Frame")).matrix_world
        tmp = C27.lights_from_empties(root)
        hid = ("WALL_Near_A", "WALL_Near_B", "CEILING", "WALL_Near_Casa", "LEVEL_1", "Furniture_L1")
        C27.set_hidden(root, hid)
        if want(f"{name}_iso"):
            cam = C27.iso_cam(fm @ Vector(tgt), ortho)
            K.render(scene, cam, P(f"{name}_iso"))
            K.annotate(scene, cam, P(f"{name}_iso"), f"{TITLES[name]} en CAM_Iso: muros cercanos y techo ocultos",
                       labels_for(root, fm))
            bpy.data.objects.remove(cam)
        if name == "casa_grande" and want("casa_grande_alta"):
            C27.set_hidden(root, ("LEVEL_1", "Furniture_L1"), False)
            cam = C27.iso_cam(fm @ Vector((0.0, -2.5, 3.6)), 10.0)
            K.render(scene, cam, P("casa_grande_alta"))
            K.annotate(scene, cam, P("casa_grande_alta"), "Casa grande: entreplanta (dormitorio) con LEVEL_1 visible", [])
            bpy.data.objects.remove(cam)
        C27.set_hidden(root, hid, False)
        C27.set_hidden(root, ("WALL_Near_Casa",), True)
        if want(f"{name}_calle"):
            cam = K.new_cam("TMP_eye", lens=lens)
            K.look_at(cam, fm @ Vector(eye), fm @ Vector(look))
            K.render(scene, cam, P(f"{name}_calle"))
            K.annotate(scene, cam, P(f"{name}_calle"), f"{TITLES[name]} a 1.7 m", [])
            bpy.data.objects.remove(cam)
        for o in tmp:
            bpy.data.objects.remove(o)


if __name__ == "__main__":
    main()
