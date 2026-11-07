"""
CONCORDIA - capturas de la etapa 23 (E10, Moradas).
  conjunto_NE/NO/SO/SE  isometrica de cada conjunto (CAM_Iso ortho 140): comprobacion de techos escalonados
  terraza_iso           una terraza completa (Morada NO, terraza 6: 18 casas) en isometrica
  terraza_calle         la misma terraza desde su calle de servicio, ojo a 1.7 m
  puerta                detalle de DOOR_Morada (pintura, placa, farol) en una casa de la terraza
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
BLEND = os.path.join(REPO, "blender", f"{C.BLEND_BASENAME}_v23.blend")
OUT = os.path.join(REPO, "docs", "captures")
ONLY = set(sys.argv[sys.argv.index("--") + 1:]) if "--" in sys.argv else set()
PHI = {"NE": 45.0, "NO": 135.0, "SO": 225.0, "SE": 315.0}
ROW = ("NO", 6)


def P(n):
    return os.path.join(OUT, f"stage23_{n}.png")


def want(n):
    return not ONLY or n in ONLY


def houses(key, t=None):
    out = [o for o in bpy.data.objects if o.name.startswith(f"Morada_{key}_") and o.type == "EMPTY" and o.parent is None
           and (t is None or o.get("terraza") == t)]
    return sorted(out, key=lambda o: math.atan2(o.matrix_world.translation.y, o.matrix_world.translation.x))


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
    for key, phi in PHI.items():
        n = f"conjunto_{key}"
        if not want(n):
            continue
        a = math.radians(phi)
        cam = K.iso_at(cam_iso, (147 * math.cos(a), 147 * math.sin(a), 8.0), 140.0)
        cam.data.clip_end = 5000
        K.render(scene, cam, P(n))
        hs = houses(key)
        labs = [(f"T{t}", tuple(houses(key, t)[len(houses(key, t)) // 2].matrix_world @ Vector((0, 0, 12))))
                for t in range(1, 7) if houses(key, t)]
        K.annotate(scene, cam, P(n), f"Morada {key}: {len(hs)} casas en 6 terrazas, techos escalonados (ninguna puerta "
                   "tapada por casas de otra terraza desde CAM_Iso) - ortho 140", labs)
        bpy.data.objects.remove(cam)
    key, t = ROW
    row = houses(key, t)
    if want("terraza_iso"):
        c = sum((h.matrix_world.translation for h in row), Vector()) / len(row)
        cam = K.iso_at(cam_iso, (c.x, c.y, c.z + 5.0), 118.0)
        cam.data.clip_end = 5000
        K.render(scene, cam, P("terraza_iso"))
        labs = [(f"{h['tipo'][:4]} v{h['variant']}{h['facade'][-1]}", tuple(h.matrix_world @ Vector((0, 0, 11.5))))
                for h in row[::2]]
        K.annotate(scene, cam, P("terraza_iso"), f"Morada {key}, terraza {t}: {len(row)} casas (habitacion / pequena / "
                   "grande; 4 variantes x 3 fachadas) - CAM_Iso ortho 118", labs)
    mid = row[len(row) // 2]
    mw = mid.matrix_world
    if want("terraza_calle"):
        cam = K.new_cam("TMP_c", lens=20)
        K.look_at(cam, mw @ Vector((-9.0, 6.9, 1.7)), mw @ Vector((7.0, 2.5, 3.6)))
        K.render(scene, cam, P("terraza_calle"))
        K.annotate(scene, cam, P("terraza_calle"), f"Morada {key}, terraza {t}, desde la calle de servicio (ojo a 1.7 m): "
                   "galerias corridas y escaleras de las casas comunales, patios, balcones, puertas DOOR_Morada", [])
    if want("puerta"):
        h = next(o for o in row if o["tipo"] == "casa_pequena")
        hw_ = h.matrix_world
        d = next(o for o in h.children if o.name.startswith("DOOR_Morada_"))
        dl = d.location
        cam = K.new_cam("TMP_d", lens=35)
        K.look_at(cam, hw_ @ Vector((dl.x + 1.6, 7.6, 1.6)), hw_ @ Vector((dl.x, 3.0, 1.4)))
        K.render(scene, cam, P("puerta"))
        K.annotate(scene, cam, P("puerta"), f"{d.name}: pintura {d['paint_material']} (por instancia), placa de numero "
                   f"0.3 x 0.2 m ({d['house_number']}), MARKER_Lantern + LANTERN_Shard", [])


if __name__ == "__main__":
    main()
