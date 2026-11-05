"""
CONCORDIA - capturas de la etapa 13 (Portal).
  portal_iso          CAM_Iso ortho 46 sobre el Portal (velo, piedras, atrio de descenso)
  portal_avenida_n    a 1.7 m de altura en la avenida Norte (y = 46), mirando al Portal
  portal_runas        primer plano: cara S del pilar E (linea emisiva) y cara interior (runas talladas)
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
BLEND = os.path.join(REPO, "blender", f"{C.BLEND_BASENAME}_v13.blend")
OUT = os.path.join(REPO, "docs", "captures")


def ground_z(x, y):
    from mathutils.bvhtree import BVHTree
    o = bpy.data.objects["TRN_City"]
    b = BVHTree.FromObject(o, bpy.context.evaluated_depsgraph_get())
    h = b.ray_cast(Vector((x, y, 100)), Vector((0, 0, -1)))
    return h[0].z if h[0] else C.Z_PLAZA


def main():
    only = set(sys.argv[sys.argv.index("--") + 1].split(",")) if "--" in sys.argv else None
    bpy.ops.wm.open_mainfile(filepath=BLEND)
    scene = bpy.context.scene
    K.setup_render(scene)
    for o in list(bpy.data.collections["WALL_KIT"].all_objects):
        o.hide_render = True
    for o in bpy.data.objects:
        if o.name.endswith(("-colonly", "_LOD1", "_LOD2", "-navmesh", "-occonly")):
            o.hide_render = True
    cam_iso = bpy.data.objects[C.CAM_ISO_NAME]
    P = lambda n: os.path.join(OUT, f"stage13_{n}.png")  # noqa: E731

    def want(n):
        return only is None or n in only
    if want("portal_iso"):
        cam = K.iso_at(cam_iso, (0, 0, 12.0), 46.0)
        K.render(scene, cam, P("portal_iso"))
        K.annotate(scene, cam, P("portal_iso"), "PORTAL_Arch + PORTAL_Veil, piedras runicas y atrio de descenso - "
                   "CAM_Iso ortho 46", [("velo 8 x 11 m", (0, 0.3, 15.0)), ("runa 01", (0, 9, 9.6)),
                                        ("pedestal de descenso 01", (0, 13.5, 9.4))])
    if want("portal_avenida_n"):
        y = 46.0
        z = ground_z(0.0, y)
        cam = K.new_cam("TMP_eye", lens=20)
        K.look_at(cam, (1.2, y, z + 1.7), (0.0, 0.0, 14.0))
        K.render(scene, cam, P("portal_avenida_n"))
        K.annotate(scene, cam, P("portal_avenida_n"), f"Desde la avenida Norte a altura de personaje (y = {y:.0f} m, "
                   f"ojo a {z + 1.7:.1f} m)", [])
    if want("portal_runas"):
        cam = K.new_cam("TMP_runes", lens=32)
        K.look_at(cam, (2.3, -5.0, 8.9 + 3.6), (5.0, -1.1, 8.9 + 4.4))
        K.render(scene, cam, P("portal_runas"))
        K.annotate(scene, cam, P("portal_runas"), "Primer plano: linea de runas emisivas #8FD0FF (1.2) en la cara S "
                   "del pilar E y runas talladas 3 cm en la cara interior", [])


if __name__ == "__main__":
    main()
