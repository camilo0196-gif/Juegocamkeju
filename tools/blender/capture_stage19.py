"""
CONCORDIA - capturas de la etapa 19 (E6, Oficios): isometrica del distrito y una isometrica (direccion de CAM_Iso)
de cada edificio encuadrada en su rasgo distintivo. `-- nombre ...` para repetir solo algunas.
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
BLEND = os.path.join(REPO, "blender", f"{C.BLEND_BASENAME}_v19.blend")
OUT = os.path.join(REPO, "docs", "captures")
ONLY = set(sys.argv[sys.argv.index("--") + 1:]) if "--" in sys.argv else set()
SHOTS = [  # (raiz, ortho, alto del centro, titulo)
    ("Gremio_Mineros", 34, 5, "Gremio de Mineros: bocamina, vagonetas en carriles, pico dorado de 3 m y castillete en el tejado"),
    ("Gremio_Herbolarios", 32, 2, "Gremio de Herbolarios: invernadero de vidrio (alpha 0.35) y madera, terrazas de hierbas"),
    ("Gremio_Pescadores", 40, 3, "Gremio de Pescadores: redes en bastidores y 2 barcas de 4 m en el muelle del Cauce"),
    ("Taller_GranForja", 44, 6, "La Gran Forja: chimenea de 14 m, fundicion al aire libre con crisol, 3 yunques, brasas"),
    ("Taller_Curtiduria", 30, 3, "Curtiduria: 4 tinas de curtido y bastidores con pieles"),
    ("Taller_Sastreria", 30, 4, "Sastreria: planta alta abierta con telares y telas colgando de los balcones"),
    ("Taller_Carpinteria", 34, 4, "Carpinteria: entramado, rueda hidraulica de 3.5 m (WATERWHEEL aparte), sierra y troncos"),
    ("Taller_Alquimia", 30, 7, "Alquimia: torre de 4 plantas, ventanas redondas, alambiques en balcones, 2 chimeneas"),
    ("Taller_Hornos", 30, 3, "Hornos de Concordia: horno comunal con brasas y chimenea, cobertizo con mesas largas"),
    ("Taller_JoyeriaTallado", 24, 3, "Joyeria y Tallado: escaparates con lupas de bronce y farolillo de esquirla"),
    ("CrisolPiedras", 40, 5, "Crisol de las Piedras: tambor de 22 m, oculo de 3 m con luz azul, cuenco fundido y piedras flotantes"),
    ("CasaReparaciones", 28, 2, "Casa de Reparaciones: taller abierto con yunque, pared de herramientas y banco largo"),
    ("Gremio_Cazadores", 44, 2, "Gremio de Cazadores (SIN PARCELA, montado en la zona del kit): cornamentas, pieles y 6 blancos"),
]


def P(n):
    return os.path.join(OUT, f"stage19_{n}.png")


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
    beam = bpy.data.objects.get("FARO_Beam")
    if beam:
        beam.hide_render = True
    cam_iso = bpy.data.objects[C.CAM_ISO_NAME]
    if want("oficios_iso"):
        cam = K.iso_at(cam_iso, (128.0, 2.0, 8.0), 150.0)
        cam.data.clip_end = 5000
        K.render(scene, cam, P("oficios_iso"))
        labs = [(n.split("_")[-1], tuple(bpy.data.objects[n].matrix_world @ Vector((0, 0, 6)))) for n, *_ in SHOTS
                if n != "Gremio_Cazadores"]
        K.annotate(scene, cam, P("oficios_iso"), "Distrito Este (Oficios) - CAM_Iso ortho 150 (haz del Faro oculto)", labs)
    for name, ortho, zc, title in SHOTS:
        key = name.lower()
        if not want(key):
            continue
        r = bpy.data.objects[name]
        c = r.matrix_world.translation
        if name == "Gremio_Cazadores":
            c = r.matrix_world @ Vector((0, -6.0, 0))
        cam = K.iso_at(cam_iso, (c.x, c.y, c.z + zc), ortho)
        cam.data.clip_end = 5000
        K.render(scene, cam, P(key))
        K.annotate(scene, cam, P(key), title, [])
        bpy.data.objects.remove(cam)


if __name__ == "__main__":
    main()
