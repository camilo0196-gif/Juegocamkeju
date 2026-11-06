"""
CONCORDIA - capturas de la etapa 18 (E5, Mercado).
  mercado_iso      distrito completo, CAM_Iso ortho 150
  tesoreria        primer plano 3/4 desde la avenida: porticada, balanzas, torre del reloj y salidas de tubos
  posada           desde la calle (ojo 1.7 m): entramado, balcones, chimenea, letrero con vela, Tablon de Grupos
  subasta          3/4 bajo el alero: galerias, tarima con campana, tableros de precios
  fuente           fuente con rebosadero hacia el manantial del Cauce
  puestos          puestos de la Plaza de Provisiones
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
BLEND = os.path.join(REPO, "blender", f"{C.BLEND_BASENAME}_v18.blend")
OUT = os.path.join(REPO, "docs", "captures")
ONLY = set(sys.argv[sys.argv.index("--") + 1:]) if "--" in sys.argv else set()


def P(n):
    return os.path.join(OUT, f"stage18_{n}.png")


def want(n):
    return not ONLY or n in ONLY


def frame_of(name):
    r = bpy.data.objects[name]
    mw = r.matrix_world
    return mw, (lambda x, y, z: mw @ Vector((x, y, z)))


def main():
    bpy.ops.wm.open_mainfile(filepath=BLEND)
    scene = bpy.context.scene
    K.setup_render(scene)
    for o in list(bpy.data.collections["WALL_KIT"].all_objects):
        o.hide_render = True
    for o in bpy.data.objects:
        if o.name.endswith(("-colonly", "_LOD1", "_LOD2", "-navmesh", "-occonly", "_InteriorVolume")):
            o.hide_render = True
    cam_iso = bpy.data.objects[C.CAM_ISO_NAME]
    if want("mercado_iso"):
        beam = bpy.data.objects.get("FARO_Beam")
        if beam:
            beam.hide_render = True             # el haz de 80 m cruza todo el encuadre: solo en esta captura
        cam = K.iso_at(cam_iso, (0.0, 128.0, 8.0), 150.0)
        cam.data.clip_end = 5000
        K.render(scene, cam, P("mercado_iso"))
        labs = []
        for n, lab in (("TesoreriaMuralla", "Tesoreria"), ("Banco", "Banco"), ("GranSubasta", "Gran Subasta"),
                       ("Posada", "Posada"), ("CasaRegistro", "Registro")):
            _, Lf = frame_of(n)
            labs.append((lab, tuple(Lf(0, 0, 8))))
        labs.append(("Fuente", tuple(bpy.data.objects["FuenteMercado"].matrix_world.translation)))
        labs.append(("Provisiones", tuple(bpy.data.objects["PuestoProvisiones_04"].matrix_world.translation)))
        K.annotate(scene, cam, P("mercado_iso"), "Distrito del Mercado - CAM_Iso ortho 150 (haz del Faro oculto en esta "
                   "captura)", labs)
        if beam:
            beam.hide_render = False
    if want("tesoreria"):
        _, Lf = frame_of("TesoreriaMuralla")
        cam = K.new_cam("TMP_t", lens=24)
        K.look_at(cam, Lf(14.0, 34.0, 9.0), Lf(-1.0, 4.0, 6.5))
        K.render(scene, cam, P("tesoreria"))
        K.annotate(scene, cam, P("tesoreria"), "Tesoreria de la Muralla: porticada de 7 arcos con columnas, trifore, "
                   "balanzas de bronce de 1.2 m, almenas, torre del reloj y 4 salidas de tubos (+9.6 m)",
                   [("balanza", tuple(Lf(1.9, 8.8, 6.2))), ("salida 02 -> Faro", tuple(Lf(-1.2, 6.6, 9.6)))])
    if want("posada"):
        _, Lf = frame_of("Posada")
        cam = K.new_cam("TMP_p", lens=24)
        K.look_at(cam, Lf(-21.0, 24.0, 4.0), Lf(0.5, 3.0, 6.0))       # desde la avenida, al NE de la fachada
        K.render(scene, cam, P("posada"))
        K.annotate(scene, cam, P("posada"), "Posada de Concordia (3 plantas): entramado, balcones, aleros de 0.9 m, "
                   "chimenea, letrero con vela y Tablon de Grupos",
                   [("Tablon de Grupos", tuple(bpy.data.objects["Posada_TablonGrupos"].matrix_world @ Vector((0, 0, 2.0))))])
    if want("subasta"):
        _, Lf = frame_of("GranSubasta")
        cam = K.new_cam("TMP_s", lens=20)
        K.look_at(cam, Lf(25.5, 2.5, 3.2), Lf(0.0, 0.0, 2.2))         # por la nave desde el hastial
        K.render(scene, cam, P("subasta"))
        K.annotate(scene, cam, P("subasta"), "Gran Subasta: halle de madera abierta, galerias a +3.5 m, tarima 5 x 3 con "
                   "campana de 1.2 m y 6 tableros de precios", [])
    if want("fuente"):
        f = bpy.data.objects["FuenteMercado"].matrix_world
        cam = K.new_cam("TMP_f", lens=24)
        K.look_at(cam, f @ Vector((-12.0, 14.0, 9.0)), f @ Vector((2.0, -3.0, 0.5)))
        K.render(scene, cam, P("fuente"))
        K.annotate(scene, cam, P("fuente"), "Fuente del Mercado (pila de 6 m, 4 canos, 8 bancos) y rebosadero "
                   "hacia el manantial del Cauce", [])
    if want("puestos"):
        a = bpy.data.objects["PuestoProvisiones_02"].matrix_world
        cam = K.new_cam("TMP_q", lens=24)
        K.look_at(cam, a @ Vector((4.0, 9.0, 4.5)), a @ Vector((-6.0, 0.0, 1.2)))
        K.render(scene, cam, P("puestos"))
        K.annotate(scene, cam, P("puestos"), "Plaza de Provisiones: 14 puestos instanciados (STALL_A..E), toldos "
                   "remendados, cajones de fruta y herramientas", [])


if __name__ == "__main__":
    main()
