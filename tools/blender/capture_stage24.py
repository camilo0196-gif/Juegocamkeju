"""
CONCORDIA - capturas de la etapa 24 (E11, version final para Godot): 8 vistas.
  portal, mercado, oficios, clases, razas, morada_NO   CAM_Iso por distrito
  ciudad_iso                                          la ciudad completa en CAM_Iso
  ciudad_calle                                        a altura de personaje (1.7 m) en la avenida Sur hacia el Portal
`-- nombre ...` para repetir solo algunas.
"""

import math
import os
import sys

import bpy
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import concordia_const as C  # noqa: E402
import capture_stage02 as K  # noqa: E402

REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
BLEND = os.path.join(REPO, "blender", f"{C.BLEND_BASENAME}_v24.blend")
OUT = os.path.join(REPO, "docs", "captures")
ONLY = set(sys.argv[sys.argv.index("--") + 1:]) if "--" in sys.argv else set()
ISO = {  # nombre: (centro, ortho, titulo)
    "portal": ((0.0, 0.0, 8.0), 210.0, "Plaza del Portal: Portal, Obelisco, Faro, Santuario y Salon de las Hazanas"),
    "mercado": ((-5.0, 141.0, 6.0), 130.0, "Distrito Norte (Mercado)"),
    "oficios": ((137.0, 2.0, 6.0), 130.0, "Distrito Este (Oficios)"),
    "clases": ((-139.0, -1.0, 6.0), 130.0, "Distrito Oeste (Clases)"),
    "razas": ((0.0, -137.0, 6.0), 130.0, "Distrito Sur (Razas)"),
    "morada_NO": ((147 * math.cos(math.radians(135)), 147 * math.sin(math.radians(135)), 8.0), 140.0,
                  "Morada NO (72 casas en 6 terrazas)"),
    "ciudad_iso": ((0.0, 0.0, 6.0), 470.0, "Concordia completa (version final, etapa 24)"),
}


def P(n):
    return os.path.join(OUT, f"stage24_{n}.png")


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
    for n, (c, ortho, title) in ISO.items():
        if not want(n):
            continue
        cam = K.iso_at(cam_iso, c, ortho)
        cam.data.clip_end = 5000
        K.render(scene, cam, P(n))
        K.annotate(scene, cam, P(n), f"{title} - CAM_Iso ortho {ortho:.0f}", [])
        bpy.data.objects.remove(cam)
    if want("ciudad_calle"):
        dg = bpy.context.evaluated_depsgraph_get()
        p = Vector((1.5, -62.0, 0.0))
        hit, loc, _n, _i, _ob, _m = scene.ray_cast(dg, Vector((p.x, p.y, 60.0)), Vector((0, 0, -1)))
        eye = Vector((p.x, p.y, (loc.z if hit else 6.0) + 1.7))
        cam = K.new_cam("TMP_city", lens=22)
        K.look_at(cam, eye, Vector((0.0, 20.0, 9.0)))
        K.render(scene, cam, P("ciudad_calle"))
        K.annotate(scene, cam, P("ciudad_calle"), "Concordia a altura de personaje (1.7 m), avenida Sur hacia el Portal", [])


if __name__ == "__main__":
    main()
