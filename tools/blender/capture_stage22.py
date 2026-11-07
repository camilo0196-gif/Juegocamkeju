"""
CONCORDIA - capturas de la etapa 22 (E9, Conexiones).
  puente_iso      Puente 01 (diagonal NE) con la escalinata monumental NE, CAM_Iso ortho 34
  puente_calle    Puente 01 desde la orilla del Cauce, ojo a 1.7 m (arco rebajado, dovelas, sillares, pretiles)
  arco_iso        Arco 06 sobre la Ronda r150 entre los barrios 2 y 4, CAM_Iso ortho 30
  arco_calle      Arco 06 desde la calle, ojo a 1.7 m (altura libre 5 m, linterna de esquirla en la clave)
  terraza_calle   una STAIRS_Terrace de 2.5 m de la Morada SE a altura de personaje
  kit             la fila del kit: BRIDGE_Stone_5m/6m, ARCH_Street_4m/5m/6m, RAIL_Stone_3m (+ Patch, Low)
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
BLEND = os.path.join(REPO, "blender", f"{C.BLEND_BASENAME}_v22.blend")
OUT = os.path.join(REPO, "docs", "captures")
ONLY = set(sys.argv[sys.argv.index("--") + 1:]) if "--" in sys.argv else set()


def P(n):
    return os.path.join(OUT, f"stage22_{n}.png")


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
    b = bpy.data.objects["MARKER_Bridge_01"].matrix_world
    if want("puente_iso"):
        cam = K.iso_at(cam_iso, tuple(b @ Vector((0, 3.0, 0.0))), 34.0)
        cam.data.clip_end = 5000
        K.render(scene, cam, P("puente_iso"))
        K.annotate(scene, cam, P("puente_iso"), "BRIDGE_Stone_6m en MARKER_Bridge_01 (diagonal NE) - calzada +0.4 m, "
                   "rampa lejana de 2.5 m hasta el rellano de la escalinata monumental - CAM_Iso ortho 34",
                   [("MARKER_Bridge_01", tuple(b.translation)),
                    ("STAIRS_Monumental", tuple(bpy.data.objects["MARKER_Stairs_Monumental_Morada_NE"].matrix_world.translation))])
    if want("puente_calle"):
        cam = K.new_cam("TMP_b", lens=24)
        K.look_at(cam, b @ Vector((10.5, -2.9, 1.2)), b @ Vector((0.0, -0.5, -0.7)))      # orilla 5.9 + 1.7
        K.render(scene, cam, P("puente_calle"))
        K.annotate(scene, cam, P("puente_calle"), "Puente 01 desde la orilla del Cauce (ojo a 1.7 m sobre la orilla): arco "
                   "rebajado, dovelas con clave, estribos con sillares, imposta, pretil de 0.9 m con remiendos", [])
    a = bpy.data.objects["MARKER_Bridge_06"].matrix_world
    deck = 6.4
    if want("arco_iso"):
        keep = {n.replace("MARKER_Bld_", "") for n in eval(bpy.data.objects["MARKER_Bridge_06"]["between"])}
        hidden = []
        for r in bpy.data.objects:
            if r.parent is None and r.type == "EMPTY" and r.get("building") and r.name not in keep and \
                    (r.matrix_world.translation - a.translation).length < 22.0:
                for o in [r] + list(r.children_recursive):
                    if not o.hide_render:
                        o.hide_render = True
                        hidden.append(o)
        cam = K.iso_at(cam_iso, tuple(a @ Vector((0, 0, -3.0))), 30.0)
        cam.data.clip_end = 5000
        K.render(scene, cam, P("arco_iso"))
        K.annotate(scene, cam, P("arco_iso"), "ARCH_Street_6m en MARKER_Bridge_06 (Ronda r150): une RAZ_B02_Casa_03 y "
                   "RAZ_B04_Casa_01 (otras casas cercanas ocultas) - CAM_Iso ortho 30", [("MARKER_Bridge_06", tuple(a.translation))])
        for o in hidden:
            o.hide_render = False
    if want("arco_calle"):
        cam = K.new_cam("TMP_a", lens=20)
        dg = bpy.context.evaluated_depsgraph_get()
        best = None
        for dx in (-9.0, 9.0, -8.0, 8.0):                    # punto de la calle con suelo libre (sin casa encima)
            p = a @ Vector((dx, 0.6, 0.0))
            hit, loc, _n, _i, ob, _m = scene.ray_cast(dg, Vector((p.x, p.y, p.z + 40)), Vector((0, 0, -1)))
            if hit and ob.name.startswith(("TRN_", "STR_")):
                best = (dx, loc)
                break
        dx, loc = best
        K.look_at(cam, Vector((loc.x, loc.y, loc.z + 1.7)), a @ Vector((0.0, 0.0, -deck + 4.4)))
        K.render(scene, cam, P("arco_calle"))
        K.annotate(scene, cam, P("arco_calle"), "Arco 06 desde la calle (ojo a 1.7 m): 5 m de altura libre, paso alto a la "
                   "planta 2, pretiles RAIL_Stone_3m, linterna de esquirla en la clave", [])
    if want("terraza_calle"):
        t = next(o for o in bpy.data.objects if o.name.startswith("STAIRS_Terrace_2.5m_") and "Morada_SE" in o.name
                 and o.type == "MESH" and not o.name.endswith(("_LOD1", "_LOD2", "-colonly")))
        m = t.matrix_world
        cam = K.new_cam("TMP_t", lens=30)
        K.look_at(cam, m @ Vector((-5.0, 5.0, 1.2)), m @ Vector((0.0, 0.8, -0.5)))
        K.render(scene, cam, P("terraza_calle"))
        K.annotate(scene, cam, P("terraza_calle"), f"{t.name}: escalera de terraza de 2.5 m (7 x 0.143 / 0.30), zancas "
                   "con albardilla, boceles y un peldano de otra piedra (ojo a 1.7 m en la terraza baja)", [])
    if want("kit"):
        root = bpy.data.objects["KIT_Conexiones"].matrix_world.translation
        cam = K.iso_at(cam_iso, tuple(root + Vector((26.0, 0.0, 3.0))), 64.0)
        cam.data.clip_end = 5000
        K.render(scene, cam, P("kit"))
        labs = [(o.name, tuple(o.matrix_world @ Vector((0, 0, 1.0)))) for o in bpy.data.objects["KIT_Conexiones"].children
                if o.type == "MESH" and not o.name.endswith(("_LOD1", "_LOD2"))]
        K.annotate(scene, cam, P("kit"), "Kit de conexiones (fila del kit): puentes 5/6 m, arcos de calle 4/5/6 m, pretiles 3 m", labs)


if __name__ == "__main__":
    main()
