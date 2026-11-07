"""
CONCORDIA - capturas de la etapa 25 (E12): Cazadores dentro de la muralla, casas nuevas de las Razas y el Faro.
  cazadores        CAM_Iso sobre la casa 12 x 8 (117, -21)
  cazadores_campo  CAM_Iso sobre el campo de tiro 14 x 8 junto a la muralla
  razas_nuevas     CAM_Iso sobre el distrito Sur con las 3 casas nuevas y las 3 rebajadas por el Faro
  faro_calle       a 1.7 m en el anillo r 150 del Sur (punto que ve la galeria), mirando al Faro
  cazadores_campo_calle  a 1.7 m en el extremo norte (+X) del campo de tiro
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
BLEND = os.path.join(REPO, "blender", f"{C.BLEND_BASENAME}_v25.blend")
OUT = os.path.join(REPO, "docs", "captures")
ONLY = set(sys.argv[sys.argv.index("--") + 1:]) if "--" in sys.argv else set()


def P(n):
    return os.path.join(OUT, f"stage25_{n}.png")


def want(n):
    return not ONLY or n in ONLY


def center_of(name, dz=4.0):
    p = bpy.data.objects[name].matrix_world.translation
    return (p.x, p.y, p.z + dz)


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
    iso = {"cazadores": (center_of("Gremio_Cazadores", 3.0), 40.0,
                         "Gremio de Cazadores: casa 12 x 8, 2 plantas, en (117, -21) dentro de la muralla"),
           "cazadores_campo": (center_of("Gremio_Cazadores_Range", 1.0), 40.0,
                               "Campo de tiro 14 x 8 con valla de 1.2 m, paralelo a la muralla (r 169)"),
           "razas_nuevas": ((5.0, -128.0, 6.0), 110.0,
                            "Razas: casas nuevas B01_06, B04_06, B05_01 y rebajadas por el Faro B01_01, B01_02, B02_02")}
    for n, (c, ortho, title) in iso.items():
        if not want(n):
            continue
        cam = K.iso_at(cam_iso, c, ortho)
        cam.data.clip_end = 5000
        K.render(scene, cam, P(n))
        K.annotate(scene, cam, P(n), f"{title} - CAM_Iso ortho {ortho:.0f}", [])
        bpy.data.objects.remove(cam)
    if want("faro_calle"):
        # punto del anillo r 150 del Sur que ve la galeria del Faro (>= 2 de 6 visuales), el mas cercano a las casas
        # rebajadas RAZ_B01_Casa_01/02
        import stage25_faro as F
        bvh, _owner = F.occluders()
        g = F.ground_fn()
        ref = (bpy.data.objects["RAZ_B01_Casa_01"].matrix_world.translation.xy
               + bpy.data.objects["RAZ_B01_Casa_02"].matrix_world.translation.xy) / 2
        best = None
        for _kind, lst in F.streets().items():
            for sname, pts in lst:
                if sname != "STR_RAZ_Ring150":
                    continue
                for q in pts:
                    eye = Vector((q.x, q.y, g(q.x, q.y) + F.EYE))
                    seen = 0
                    for t in F.targets_for(eye):
                        dv = t - eye
                        if bvh.ray_cast(eye, dv.normalized(), dv.length - 0.05)[0] is None:
                            seen += 1
                    d = (eye.xy - ref).length
                    if seen >= 2 and (best is None or d < best[0]):
                        best = (d, eye)
        eye = best[1]
        cam = K.new_cam("TMP_faro", lens=28)
        K.look_at(cam, eye, Vector((50.91, 50.91, 30.0)))
        K.render(scene, cam, P("faro_calle"))
        K.annotate(scene, cam, P("faro_calle"),
                   f"Faro desde el anillo r 150 del Sur a 1.7 m ({eye.x:.0f}, {eye.y:.0f}); RAZ_B01_01/02 rebajadas a 5.5 m", [])
        bpy.data.objects.remove(cam)
    if want("cazadores_campo_calle"):
        rng_o = bpy.data.objects["Gremio_Cazadores_Range"]
        mw = rng_o.matrix_world
        eye = mw @ Vector((11.5, 2.5, 1.7))          # desde el extremo +X (suelo libre; ver seccion 15 del README)
        cam = K.new_cam("TMP_campo", lens=24)
        K.look_at(cam, eye, mw @ Vector((-1.0, -2.5, 0.8)))
        K.render(scene, cam, P("cazadores_campo_calle"))
        K.annotate(scene, cam, P("cazadores_campo_calle"),
                   "Campo de tiro de los Cazadores a 1.7 m desde el extremo norte: valla 1.2 m, mostrador y 4 dianas", [])


if __name__ == "__main__":
    main()
