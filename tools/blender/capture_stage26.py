"""
CONCORDIA - capturas de la etapa 26 (E13).
  moradas_ne        CAM_Iso sobre una terraza de NE con un balcon por puerta (Morada_NE_013)
  moradas_so_calle  a 1.7 m en una terraza de SO mirando a los balcones y la escalera
  cazadores_acceso  CAM_Iso sobre el campo de tiro, la entrada norte con portillo y el camino a la calle
  razas_b05_b06     CAM_Iso sobre B05 y B06 (yurtas pequenas y adosadas)
  tubos             CAM_Iso sobre los tubos de luz Tesoreria -> Faro
  faro_haz          a 1.7 m en la avenida Este mirando al Faro y su haz
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
BLEND = os.path.join(REPO, "blender", f"{C.BLEND_BASENAME}_v26.blend")
OUT = os.path.join(REPO, "docs", "captures")
ONLY = set(sys.argv[sys.argv.index("--") + 1:]) if "--" in sys.argv else set()


def P(n):
    return os.path.join(OUT, f"stage26_{n}.png")


def want(n):
    return not ONLY or n in ONLY


def at(name, dz=4.0):
    p = bpy.data.objects[name].matrix_world.translation
    return (p.x, p.y, p.z + dz)


def street_eye(scene, x, y):
    dg = bpy.context.evaluated_depsgraph_get()
    hit, loc, _n, _i, _ob, _m = scene.ray_cast(dg, Vector((x, y, 120.0)), Vector((0, 0, -1)))
    while hit and _ob.name.endswith(("-colonly", "-navmesh", "_LOD1", "_LOD2")):
        hit, loc, _n, _i, _ob, _m = scene.ray_cast(dg, loc - Vector((0, 0, 0.01)), Vector((0, 0, -1)))
    return Vector((x, y, (loc.z if hit else 6.0) + 1.7))


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
    cam_iso = bpy.data.objects[C.CAM_ISO_NAME]
    pipes = bpy.data.objects["PIPES_Tesoreria_Faro"].children
    pc = sum((o.matrix_world.translation for o in pipes), Vector()) / max(1, len(pipes))
    iso = {"moradas_ne": (at("Morada_NE_013", 5.0), 45.0, "Morada NE: un balcon por puerta y escalera hacia la camara"),
           "cazadores_acceso": (at("Gremio_Cazadores_Range", 1.0), 42.0,
                                "Campo de tiro: entrada norte de 2 m con portillo y camino de adoquin hasta la calle"),
           "razas_b05_b06": ((0.0, -80.0, 6.0), 95.0, "Razas B05 (yurtas pequenas) y B06 (adosadas 4 x 8)"),
           "tubos": ((pc.x, pc.y, pc.z - 4.0), 120.0, "Tubos de luz Tesoreria -> Faro (123 m, 7,944 tris)")}
    if bpy.data.objects.get("FARO_Beam"):
        bpy.data.objects["FARO_Beam"].hide_render = True
    for n, (c, ortho, title) in iso.items():
        if not want(n):
            continue
        cam = K.iso_at(cam_iso, c, ortho)
        cam.data.clip_end = 5000
        K.render(scene, cam, P(n))
        K.annotate(scene, cam, P(n), f"{title} - CAM_Iso ortho {ortho:.0f}", [])
        bpy.data.objects.remove(cam)
    if want("moradas_so_calle"):
        r = bpy.data.objects["Morada_SO_035"]
        mw = r.matrix_world
        eye = mw @ Vector((-9.0, 7.0, 1.7))
        eye = street_eye(scene, eye.x, eye.y)
        cam = K.new_cam("TMP_so", lens=24)
        K.look_at(cam, eye, mw @ Vector((3.0, 3.5, 4.0)))
        K.render(scene, cam, P("moradas_so_calle"))
        K.annotate(scene, cam, P("moradas_so_calle"), "Morada SO a 1.7 m: balcones por puerta y escalera de dos tramos", [])
        bpy.data.objects.remove(cam)
    if want("faro_haz"):
        if bpy.data.objects.get("FARO_Beam"):
            bpy.data.objects["FARO_Beam"].hide_render = False
        eye = street_eye(scene, 112.0, 1.5)
        cam = K.new_cam("TMP_haz", lens=20)
        K.look_at(cam, eye, Vector((50.91, 50.91, 70.0)))
        K.render(scene, cam, P("faro_haz"))
        K.annotate(scene, cam, P("faro_haz"), "Faro y haz desde la avenida Este a 1.7 m (criterio nuevo: haz 60-120 m o cristal)", [])


if __name__ == "__main__":
    main()
