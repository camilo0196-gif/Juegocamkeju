"""
CONCORDIA - capturas de la etapa 07 (Cauce, puentes, arcos, escalinatas).

  iso_cauce_oficios      CAM_Iso (ortho 110) sobre el tramo radial del Cauce en Oficios
  iso_cauce_detalle      CAM_Iso (ortho 35) puente + muelle de Pescadores + hueco de la rueda
  iso_cauce_arco         CAM_Iso (ortho 70) el arco r=89.5 (Mercado -> hitos NE -> Oficios)
  eye_cauce              altura de personaje en la orilla, mirando aguas abajo
  iso_arcos_razas        CAM_Iso (ortho 60) arcos entre barrios
  iso_escalinata         CAM_Iso (ortho 30) una escalinata hitos -> Moradas
  cenital_cauce          cenital (Norte arriba) del recorrido
"""

import json
import os
import sys
from math import atan2, cos, degrees, radians, sin

import bpy
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import concordia_const as C  # noqa: E402
import capture_stage02 as K  # noqa: E402
import stage07_cauce as M  # noqa: E402

REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
BLEND = os.path.join(REPO, "blender", f"{C.BLEND_BASENAME}_v07.blend")
REPORT = os.path.join(REPO, "docs", "reports", "stage07_cauce.json")
OUT = os.path.join(REPO, "docs", "captures")


def obj_loc(name):
    o = bpy.data.objects.get(name)
    return tuple(o.location) if o else None


def main():
    only = set(sys.argv[sys.argv.index("--") + 1].split(",")) if "--" in sys.argv else None
    bpy.ops.wm.open_mainfile(filepath=BLEND)
    scene = bpy.context.scene
    K.setup_render(scene)
    with open(REPORT) as fh:
        rep = json.load(fh)
    for o in list(bpy.data.collections["WALL_KIT"].all_objects):
        o.hide_render = True
    for o in list(bpy.data.collections["WALL_LAYOUT"].objects):
        if o.name.endswith("-colonly"):
            o.hide_render = True
    cam_iso = bpy.data.objects[C.CAM_ISO_NAME]
    canal = M.Canal()
    P = lambda n: os.path.join(OUT, f"stage07_{n}.png")  # noqa: E731

    def want(n):
        return only is None or n in only
    br = rep.get("bridges_cauce", [])
    blabels = [(f"{b['name'][7:]} ({b['width_m']:g} m)", tuple(b["loc"])) for b in br]
    if want("iso_cauce_oficios"):
        p, t, n, e, w = canal.at(canal.L - 60)
        cam = K.iso_at(cam_iso, (p[0], p[1], e), 110.0)
        K.render(scene, cam, P("iso_cauce_oficios"))
        K.annotate(scene, cam, P("iso_cauce_oficios"), "Cauce en Oficios - CAM_Iso ortho 110 (4 azudes de 0.3 m)",
                   blabels + [(f"azud {i + 1}", (wr["pt"][0], wr["pt"][1], wr["edge_after"]))
                              for i, wr in enumerate(rep.get("cauce_weirs_list", []))])
    if want("iso_cauce_detalle"):
        wl = obj_loc("MARKER_Cauce_WaterWheel")
        ml = obj_loc("MARKER_Muelle_Pescadores")
        tgt = ml or wl
        cam = K.iso_at(cam_iso, tgt, 38.0)
        K.render(scene, cam, P("iso_cauce_detalle"))
        lab = [("muelle 8x3 (Pescadores)", ml)] if ml else []
        lab += [(b, l) for b, l in blabels if (Vector(l) - Vector(tgt)).length < 25]
        K.annotate(scene, cam, P("iso_cauce_detalle"), "Cauce - detalle ortho 38", lab)
        if wl:
            cam = K.iso_at(cam_iso, wl, 30.0)
            K.render(scene, cam, P("iso_cauce_rueda"))
            K.annotate(scene, cam, P("iso_cauce_rueda"), "Carpinteria - hueco de 3 m para la rueda hidraulica (ortho 30)",
                       [("MARKER_Cauce_WaterWheel", wl)])
    if want("iso_cauce_arco"):
        p, t, n, e, w = canal.at(70.0)
        cam = K.iso_at(cam_iso, (p[0], p[1], e), 75.0)
        K.render(scene, cam, P("iso_cauce_arco"))
        K.annotate(scene, cam, P("iso_cauce_arco"), "Cauce - arco r=89.5 por la zona de hitos NE (ortho 75)", blabels)
    if want("eye_cauce"):
        s = canal.L - 95
        p, t, n, e, w = canal.at(s)
        q, *_ = canal.at(s + 30)
        eye = (p[0] + n[0] * 2.6, p[1] + n[1] * 2.6, e + K.EYE)
        cam = K.new_cam("TMP_eye_cauce", lens=20)
        K.look_at(cam, eye, (q[0], q[1], e - 0.5))
        K.render(scene, cam, P("eye_cauce"))
        K.annotate(scene, cam, P("eye_cauce"), "Altura de personaje en la orilla del Cauce, aguas abajo", [])
    if want("iso_arcos_razas"):
        arcs = rep.get("bridges_arcos", {}).get("built", [])
        if arcs:
            xs = [a["loc"][0] for a in arcs]
            ys = [a["loc"][1] for a in arcs]
            first = arcs[0]
            cam = K.iso_at(cam_iso, tuple(first["loc"]), 45.0)
            K.render(scene, cam, P("iso_arco_razas"))
            K.annotate(scene, cam, P("iso_arco_razas"), f"Arco entre barrios ({first['street_w_m']:g} m de calle, "
                       f"{first['clear_height_m']:g} m libres) - ortho 45",
                       [(a["name"][7:], tuple(a["loc"])) for a in arcs])
            cam = K.iso_at(cam_iso, (sum(xs) / len(xs), sum(ys) / len(ys), 6.0), 110.0)
            K.render(scene, cam, P("iso_arcos_razas"))
            K.annotate(scene, cam, P("iso_arcos_razas"), f"Razas - {len(arcs)} arcos entre barrios (ortho 110)",
                       [(a["name"][7:], tuple(a["loc"])) for a in arcs])
    if want("iso_escalinata"):
        esc = rep.get("escalinatas", [])
        if esc:
            e0 = next((e for e in esc if e["morada"] == "Morada_NW"), esc[0])
            cam = K.iso_at(cam_iso, tuple(e0["loc"]), 30.0)
            K.render(scene, cam, P("iso_escalinata"))
            K.annotate(scene, cam, P("iso_escalinata"), f"Escalinata hitos -> Moradas ({e0['morada']}, rampa de "
                       f"{e0['terrain_slope_deg']:g} grados) - 10 x 0.15 / 0.35 - ortho 30", [])
    if want("cenital_cauce"):
        cam = K.new_cam("TMP_top", ortho=200.0)
        cam.location = (95, 30, 400)
        rx, ry = scene.render.resolution_x, scene.render.resolution_y
        scene.render.resolution_x = scene.render.resolution_y = 1800
        K.render(scene, cam, P("cenital_cauce"))
        K.annotate(scene, cam, P("cenital_cauce"), "Cauce - cenital (Norte arriba): Fuente del Mercado -> alcantarilla 345",
                   blabels)
        scene.render.resolution_x, scene.render.resolution_y = rx, ry


if __name__ == "__main__":
    main()
