"""
CONCORDIA - capturas de la etapa 06 (Moradas).

  iso_<Morada>       CAM_Iso (ortho 100) sobre cada Morada con volumenes provisionales de casa por tipo
                     (habitacion / casa_pequena / casa_grande) y la puerta marcada en blanco.
  iso_SE_puertas     detalle (ortho 40) de la Morada SE (puertas hacia la camara, tejados de la terraza
                     superior delante): comprobacion de oclusion.
  cenital_moradas    cenital (Norte arriba) de las 4 Moradas con parcelas por tipo.
Los volumenes solo existen durante la captura (no se guardan en el .blend).
"""

import json
import os
import sys
from math import cos, radians, sin

import bpy
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import concordia_const as C  # noqa: E402
import capture_stage02 as K  # noqa: E402
import stage06_moradas as M  # noqa: E402

REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
BLEND = os.path.join(REPO, "blender", f"{C.BLEND_BASENAME}_v06.blend")
LAYOUT = os.path.join(REPO, "docs", "reports", "stage06_layout.json")
OUT = os.path.join(REPO, "docs", "captures")
TYPE_RGB = {"habitacion": (205, 170, 120), "casa_pequena": (180, 120, 80), "casa_grande": (130, 80, 60)}


def mat(name, rgb, emit=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = tuple((c / 255) ** 2.2 for c in rgb) + (1,)
    if emit:
        b.inputs["Emission Color"].default_value = (1, 1, 1, 1)
        b.inputs["Emission Strength"].default_value = emit
    return m


def proxies(lays, setback, col):
    mats = {t: mat(f"TMP_{t}", c) for t, c in TYPE_RGB.items()}
    door_m = mat("TMP_door", (255, 255, 255), 1.5)
    objs = []
    for t in TYPE_RGB:
        sub = [dict(l, parcels=[p for p in l["parcels"] if p["tipo"] == t]) for l in lays]
        v, f, _o = M.proxy_mesh(sub, setback)
        me = bpy.data.meshes.new(f"TMP_proxy_{t}")
        me.from_pydata(v, [], f)
        me.materials.append(mats[t])
        o = bpy.data.objects.new(me.name, me)
        col.objects.link(o)
        objs.append(o)
    dv, df = [], []
    for l in lays:
        for p in l["parcels"]:
            a = radians(p["angle"])
            sgn = -1.0 if p["facing"] == "in" else 1.0
            r = p["rp"] + setback if p["facing"] == "in" else p["rp"] + M.PARCEL_D - setback
            e = Vector((cos(a), sin(a), 0))
            t = Vector((-sin(a), cos(a), 0))
            c = e * (r + sgn * 0.06) + Vector((0, 0, p["z"]))
            b = len(dv)
            for dz in (0.0, 2.2):
                for s in (-0.6, 0.6):
                    dv.append(tuple(c + t * s + Vector((0, 0, dz))))
            df.append((b, b + 1, b + 3, b + 2))
    me = bpy.data.meshes.new("TMP_doors")
    me.from_pydata(dv, [], df)
    me.materials.append(door_m)
    o = bpy.data.objects.new(me.name, me)
    col.objects.link(o)
    objs.append(o)
    return objs


def main():
    bpy.ops.wm.open_mainfile(filepath=BLEND)
    scene = bpy.context.scene
    K.setup_render(scene)
    with open(LAYOUT) as fh:
        data = json.load(fh)
    lays, setback = data["moradas"], data["setback"]
    for o in list(bpy.data.collections["WALL_KIT"].all_objects):
        o.hide_render = True
    for o in list(bpy.data.collections["WALL_LAYOUT"].objects):
        if o.name.endswith("-colonly"):
            o.hide_render = True
    col = bpy.data.collections.new("TMP_PROXIES")
    scene.collection.children.link(col)
    proxies(lays, setback, col)
    cam_iso = bpy.data.objects[C.CAM_ISO_NAME]
    P = lambda n: os.path.join(OUT, f"stage06_{n}.png")  # noqa: E731
    for l in lays:
        phi = l["phi"]
        tgt = (cos(radians(phi)) * 150, sin(radians(phi)) * 150, 8.0)
        cam = K.iso_at(cam_iso, tgt, 100.0)
        name = f"iso_{M.KEYS[l['key']]}"
        K.render(scene, cam, P(name))
        K.annotate(scene, cam, P(name),
                   f"Morada {M.KEYS[l['key']]} - CAM_Iso ortho 100 - {len(l['parcels'])} parcelas 6x10 "
                   f"(volumenes provisionales; puertas en blanco; puerta hacia la "
                   f"{'ciudad' if l['parcels'][0]['facing'] == 'in' else 'muralla'})", [],
                   ["claro = habitacion | medio = casa_pequena | oscuro = casa_grande (jardin al fondo)",
                    f"retranqueo de fachada aplicado: {setback:g} m"])
    se = [l for l in lays if l["key"] == "Morada_SE"][0]
    phi = se["phi"]
    cam = K.iso_at(cam_iso, (cos(radians(phi)) * 160, sin(radians(phi)) * 160, 9.0), 40.0)
    K.render(scene, cam, P("iso_SE_puertas"))
    K.annotate(scene, cam, P("iso_SE_puertas"), "Morada SE - detalle ortho 40: puertas (blanco) frente a tejados de la "
               "terraza superior", [])
    cam = K.new_cam("TMP_top", ortho=420.0)
    cam.location = (0, 0, 400)
    rx, ry = scene.render.resolution_x, scene.render.resolution_y
    scene.render.resolution_x = scene.render.resolution_y = 1800
    K.render(scene, cam, P("cenital_moradas"))
    K.annotate(scene, cam, P("cenital_moradas"), "Moradas - cenital (Norte arriba) con volumenes provisionales", [])
    scene.render.resolution_x, scene.render.resolution_y = rx, ry


if __name__ == "__main__":
    main()
