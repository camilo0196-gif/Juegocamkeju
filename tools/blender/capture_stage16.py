"""
CONCORDIA - capturas de la etapa 16 (Santuario del Retorno y Salon de las Hazanas).
  santuario_iso      CAM_Iso ortho 30
  santuario_calle    desde la plaza (+Y), ojo a 1.7 m
  santuario_pozo     SANTUARIO_Well (modelo aparte para el interior) con el edificio oculto
  salon_iso          CAM_Iso ortho 54 (el juego ve la trasera: la puerta mira a la plaza, lejos de la camara)
  salon_iso_frente   isometrica girada 180 grados SOLO para ver la portada (no es la camara del juego)
  salon_calle        desde la plaza (+Y), ojo a 1.7 m
"""

import math
import os
import sys

import bpy
from mathutils import Euler, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import concordia_const as C  # noqa: E402
import capture_stage02 as K  # noqa: E402

REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
BLEND = os.path.join(REPO, "blender", f"{C.BLEND_BASENAME}_v16.blend")
OUT = os.path.join(REPO, "docs", "captures")


ONLY = set(sys.argv[sys.argv.index("--") + 1:]) if "--" in sys.argv else set()


def P(n):
    return os.path.join(OUT, f"stage16_{n}.png")


def want(n):
    return not ONLY or n in ONLY


def _only(fn):
    def w(scene, cam, path, *a, **k):
        if want(os.path.basename(path)[len("stage16_"):-4]):
            return fn(scene, cam, path, *a, **k)
    return w


def main():
    K.render, K.annotate = _only(K.render), _only(K.annotate)
    bpy.ops.wm.open_mainfile(filepath=BLEND)
    scene = bpy.context.scene
    K.setup_render(scene)
    for o in list(bpy.data.collections["WALL_KIT"].all_objects):
        o.hide_render = True
    for o in bpy.data.objects:
        if o.name.endswith(("-colonly", "_LOD1", "_LOD2", "-navmesh", "-occonly", "_InteriorVolume")):
            o.hide_render = True
    cam_iso = bpy.data.objects[C.CAM_ISO_NAME]
    # ---------------- Santuario
    r = bpy.data.objects["SANTUARIO"]
    mw = r.matrix_world
    c = mw.translation
    fwd = (mw.to_3x3() @ Vector((0, 1, 0))).normalized()
    side = (mw.to_3x3() @ Vector((1, 0, 0))).normalized()
    cam = K.iso_at(cam_iso, (c.x, c.y, c.z + 8.5), 40.0)
    K.render(scene, cam, P("santuario_iso"))
    K.annotate(scene, cam, P("santuario_iso"), "Santuario del Retorno - CAM_Iso ortho 40: caliza clara, 4+5 ventanales "
               "de 1.4 x 6 m, cumbrera 14 m, flecha con esquirla", [
                   ("puerta + gablete", tuple(mw @ Vector((0, 6.0, 5.0)))),
                   ("flecha", tuple(mw @ Vector((4.5, 0, 18.5)))),
                   ("hastial con roseton (de canto en iso)", tuple(mw @ Vector((-7.6, 0, 11.0))))])
    cam = K.new_cam("TMP_sc", lens=22)
    eye = c + fwd * 21.0 + side * 3.0 + Vector((0, 0, 1.7))
    K.look_at(cam, eye, c + Vector((0, 0, 7.5)))
    K.render(scene, cam, P("santuario_calle"))
    K.annotate(scene, cam, P("santuario_calle"), "Santuario desde la plaza, ojo a 1.7 m: puerta de doble hoja bajo el "
               "gablete, farolillos de esquirla, vitrales azules (emision 0.6)", [])
    hid = [o for o in r.children_recursive if o.name.startswith(("SANTUARIO_Body", "SANTUARIO_Roof"))]
    for o in hid:
        o.hide_render = True
    w = bpy.data.objects["SANTUARIO_Well"]
    wc = w.matrix_world.translation
    cam = K.new_cam("TMP_well", lens=40)
    K.look_at(cam, wc + fwd * 3.6 + side * 2.0 + Vector((0, 0, 2.4)), wc + Vector((0, 0, 0.9)))
    K.render(scene, cam, P("santuario_pozo"))
    K.annotate(scene, cam, P("santuario_pozo"), "SANTUARIO_Well: pozo de 2 m de diametro (modelo aparte para el "
               "interior; aqui con el edificio oculto)", [])
    for o in hid:
        o.hide_render = False
    # ---------------- Salon
    r = bpy.data.objects["SALON_HAZANAS"]
    mw = r.matrix_world
    c = mw.translation
    fwd = (mw.to_3x3() @ Vector((0, 1, 0))).normalized()
    side = (mw.to_3x3() @ Vector((1, 0, 0))).normalized()
    cam = K.iso_at(cam_iso, (c.x, c.y, c.z + 6.0), 54.0)
    K.render(scene, cam, P("salon_iso"))
    K.annotate(scene, cam, P("salon_iso"), "Salon de las Hazanas - CAM_Iso ortho 54 (camara del juego: se ve la "
               "fachada trasera; la portada mira a la plaza)", [
                   ("cabezas de par", tuple(mw @ Vector((9.0, -7.9, 6.8)))),
                   ("linterna", tuple(mw @ Vector((0, 0, 18.0)))),
                   ("hornacina", tuple(mw @ Vector((-21.2, -4.2, 3.0))))])
    cam = K.new_cam("TMP_iso_r", ortho=54.0)
    e = cam_iso.rotation_euler.copy()
    cam.rotation_euler = Euler((e.x, e.y, e.z + math.pi), e.order)
    d = cam.rotation_euler.to_matrix() @ Vector((0, 0, -1))
    cam.location = Vector((c.x, c.y, c.z + 6.0)) - d * C.CAM_ISO_DISTANCE
    cam.data.clip_end = 5000
    K.render(scene, cam, P("salon_iso_frente"))
    K.annotate(scene, cam, P("salon_iso_frente"), "Salon - isometrica girada 180 grados SOLO para ver la portada "
               "(no es la camara del juego)", [
                   ("portal + ventanal", tuple(mw @ Vector((0, 8.0, 9.5)))),
                   ("placas de bronce", tuple(mw @ Vector((2.8, 8.0, 1.2)))),
                   ("hornacinas", tuple(mw @ Vector((9.0, 8.2, 3.5))))])
    cam = K.new_cam("TMP_lc", lens=18)
    eye = c + fwd * 27.0 + side * 6.0 + Vector((0, 0, 1.7))
    K.look_at(cam, eye, c + fwd * 4.0 + Vector((0, 0, 7.5)))
    K.render(scene, cam, P("salon_calle"))
    K.annotate(scene, cam, P("salon_calle"), "Salon desde la plaza, ojo a 1.7 m: hastial con portal en arco, ventanal "
               "alto, hornacinas con estatuas sin rostro y placas de bronce", [])


if __name__ == "__main__":
    main()
