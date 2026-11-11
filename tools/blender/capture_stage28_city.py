"""
CONCORDIA - capturas de la ciudad en la etapa 28 (concordia_v28.blend).
  tubos            CAM_Iso sobre la ruta oeste completa de los tubos de luz
  tubos_posada     de cerca: pilares sobre el tejado de la Posada y el arco sobre la avenida
  tubos_registro   de cerca: pilares sobre la Casa del Registro y los dos pilares junto al canal
  razas_peldanos   RAZ_B05_Casa_04 y Casa_05: peldano de piedra a lo largo de la fachada
`-- nombre ...` para repetir solo algunas.
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
BLEND = os.path.join(REPO, "blender", f"{C.BLEND_BASENAME}_v28.blend")
OUT = os.path.join(REPO, "docs", "captures")
ONLY = set(sys.argv[sys.argv.index("--") + 1:]) if "--" in sys.argv else set()


def P(n):
    return os.path.join(OUT, f"stage28_{n}.png")


def want(n):
    return not ONLY or n in ONLY


def main():
    bpy.ops.wm.open_mainfile(filepath=BLEND)
    scene = bpy.context.scene
    K.setup_render(scene)
    for cn in ("WALL_KIT", "BLD_KIT", "BLD_KIT_SHEET", "BLD_KIT_TEST", "BLD_PROPS_LIBRARY", "MATERIAL_LIBRARY"):
        c = bpy.data.collections.get(cn)
        if c:
            c.hide_render = True
    for o in bpy.data.objects:
        if o.name.endswith(("-colonly", "_LOD1", "_LOD2", "-navmesh", "-occonly", "_InteriorVolume")):
            o.hide_render = True
    if bpy.data.objects.get("FARO_Beam"):
        bpy.data.objects["FARO_Beam"].hide_render = True
    cam_iso = bpy.data.objects[C.CAM_ISO_NAME]
    mk = {o.name: o.matrix_world.translation for o in bpy.data.objects if o.name.startswith("MARKER_PipeSupport_")}
    views = {"tubos": ((6.0, 90.0, 12.0), 95.0, "Tubos de luz Tesoreria -> Faro, ruta oeste: pilares en techos y en terreno "
                                                "sin calle, arcos en los tramos de mas de 10 m"),
             "tubos_posada": ((-12.0, 79.0, 20.0), 34.0, "Pilares sobre el tejado de la Posada y arco sobre la avenida "
                                                         "hasta la Casa del Registro"),
             "tubos_registro": ((22.0, 68.0, 14.0), 34.0, "Pilares sobre la Casa del Registro y los dos pilares junto al "
                                                          "canal hasta el Faro"),
             "razas_peldanos": ((17.0, -65.0, 8.0), 22.0, "RAZ_B05_Casa_04 (derecha) y Casa_05 (izquierda): peldano de "
                                                           "piedra a lo largo de la fachada")}
    for n, (c, ortho, title) in views.items():
        if not want(n):
            continue
        cam = K.iso_at(cam_iso, c, ortho)
        cam.data.clip_end = 5000
        K.render(scene, cam, P(n))
        labels = [(k.replace("MARKER_PipeSupport_", "S"), v + Vector((0, 0, 1.0))) for k, v in mk.items()] \
            if n.startswith("tubos") and n != "tubos" else []
        K.annotate(scene, cam, P(n), f"{title} - CAM_Iso ortho {ortho:.0f}", labels)
        bpy.data.objects.remove(cam)


if __name__ == "__main__":
    main()
