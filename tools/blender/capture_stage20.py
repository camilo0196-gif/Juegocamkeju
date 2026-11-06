"""
CONCORDIA - capturas de la etapa 20 (E7, Clases).
  clases_iso        distrito, CAM_Iso ortho 150 (haz del Faro oculto)
  plaza_armas       Plaza de las Armas, CAM_Iso ortho 64: maniquies, blancos, postes, valla
  salon_iso         Salon de clase 02 (fachada hacia la camara), CAM_Iso ortho 32
  salon_calle       Salon de clase 02 desde la plaza, ojo a 1.7 m: portico, estandarte, remate, props de clase
  reposicion        Casa de Reposicion "El Remiendo" desde la calle
"""

import os
import sys

import bpy
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import concordia_const as C  # noqa: E402
import capture_stage02 as K  # noqa: E402

REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
BLEND = os.path.join(REPO, "blender", f"{C.BLEND_BASENAME}_v20.blend")
OUT = os.path.join(REPO, "docs", "captures")
ONLY = set(sys.argv[sys.argv.index("--") + 1:]) if "--" in sys.argv else set()


def P(n):
    return os.path.join(OUT, f"stage20_{n}.png")


def want(n):
    return not ONLY or n in ONLY


def main():
    bpy.ops.wm.open_mainfile(filepath=BLEND)
    scene = bpy.context.scene
    K.setup_render(scene)
    for o in list(bpy.data.collections["WALL_KIT"].all_objects):
        o.hide_render = True
    for o in bpy.data.objects:
        if o.name.endswith(("-colonly", "_LOD1", "_LOD2", "-navmesh", "-occonly", "_InteriorVolume")):
            o.hide_render = True
    if bpy.data.objects.get("FARO_Beam"):
        bpy.data.objects["FARO_Beam"].hide_render = True
    cam_iso = bpy.data.objects[C.CAM_ISO_NAME]
    if want("clases_iso"):
        cam = K.iso_at(cam_iso, (-125.0, 0.0, 8.0), 150.0)
        cam.data.clip_end = 5000
        K.render(scene, cam, P("clases_iso"))
        labs = [(f"{o['class_preset']}", tuple(o.matrix_world @ Vector((0, 0, 10)))) for o in bpy.data.objects
                if o.name.startswith("SalonClase_") and o.type == "EMPTY" and "class_preset" in o]
        labs.append(("El Remiendo", tuple(bpy.data.objects["CasaReposicion"].matrix_world @ Vector((0, 0, 8)))))
        labs.append(("Plaza de las Armas", (-123.0, 0.0, 6.0)))
        K.annotate(scene, cam, P("clases_iso"), "Distrito de las Clases - CAM_Iso ortho 150: 8 salones (presets CLASE_01..08), "
                   "Plaza de las Armas y El Remiendo", labs)
    if want("plaza_armas"):
        cam = K.iso_at(cam_iso, (-123.0, 0.0, 6.0), 64.0)
        cam.data.clip_end = 5000
        K.render(scene, cam, P("plaza_armas"))
        K.annotate(scene, cam, P("plaza_armas"), "Plaza de las Armas (50 x 40): 12 maniquies DUMMY_Straw (3 variantes), "
                   "10 blancos, 8 postes de prueba y valla baja", [])
    r = bpy.data.objects["SalonClase_02"]
    mw = r.matrix_world
    if want("salon_iso"):
        cam = K.iso_at(cam_iso, tuple(mw @ Vector((0, 1.0, 6.0))), 32.0)
        cam.data.clip_end = 5000
        K.render(scene, cam, P("salon_iso"))
        K.annotate(scene, cam, P("salon_iso"), f"Salon de clase 02 ({r['class_preset']}) - plantilla: portico de 4 columnas, "
                   "fronton con remate, estandarte 2.5 x 6 m, 3 slots de props", [])
    if want("salon_calle"):
        cam = K.new_cam("TMP_s", lens=22)
        K.look_at(cam, mw @ Vector((5.0, 16.0, 1.7)), mw @ Vector((0.0, 4.0, 4.6)))
        K.render(scene, cam, P("salon_calle"))
        K.annotate(scene, cam, P("salon_calle"), f"Salon de clase 02 ({r['class_preset']}) desde la plaza: estandarte con "
                   "emblema (textura por clase), remate, props de clase en las peanas", [])
    if want("reposicion"):
        rr = bpy.data.objects["CasaReposicion"].matrix_world
        cam = K.new_cam("TMP_r", lens=22)
        # la fachada mira a una calle de ~10 m frente al Salon 06: camara pegada a la acera de enfrente
        cam.data.lens = 16
        K.look_at(cam, rr @ Vector((5.0, 10.8, 1.7)), rr @ Vector((-1.5, 4.0, 3.0)))
        K.render(scene, cam, P("reposicion"))
        K.annotate(scene, cam, P("reposicion"), "Casa de Reposicion \"El Remiendo\": perchas con armaduras remendadas, "
                   "espadas pulidas, cajones de botas y capas, letrero con parche cosido", [])


if __name__ == "__main__":
    main()
