"""
CONCORDIA - capturas de los props hechos a mano (etapa 28) sobre blender/concordia_props_v01.blend.
  props_ia_iso      los 4 objetos de la lista de IA en CAM_Iso, con triangulos
  props_ia_cerca    los 4 de cerca (2 x 2 en una imagen, a la altura de los ojos de un personaje que los mira)
  props_triviales   los 14 triviales en CAM_Iso, con triangulos
  props_mercado_q   props del Mercado importados de Quaternius (CAM_Iso, triangulos)
  props_mercado_av  props del Mercado importados de Avramania (CAM_Iso, triangulos)
`-- nombre ...` para repetir solo algunas.
"""

import os
import sys

import bpy
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import capture_stage02 as K  # noqa: E402
import interior_kit as IK  # noqa: E402
import props_mano as PM  # noqa: E402

REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
BLEND = os.path.join(REPO, "blender", "concordia_props_v01.blend")
OUT = os.path.join(REPO, "docs", "captures")
ONLY = set(sys.argv[sys.argv.index("--") + 1:]) if "--" in sys.argv else set()
CLOSE = {  # (ojo relativo al origen del prop, objetivo relativo, lente)
    "PROP_Loom": ((1.6, 2.6, 1.7), (0.0, 0.0, 0.95), 30),
    "PROP_Forge_Bellows": ((1.1, 1.9, 1.5), (0.0, 0.0, 0.65), 32),
    "PROP_Dress_Form": ((1.3, 2.6, 1.55), (0.0, 0.0, 0.95), 35),
    "PROP_Miner_Helmet": ((0.35, 0.55, 0.42), (0.0, 0.03, 0.09), 40),
}


def P(n):
    return os.path.join(OUT, f"stage28_{n}.png")


def want(n):
    return not ONLY or n in ONLY


def floor(col):
    me = bpy.data.meshes.new("TMP_floor")
    s = 60.0
    me.from_pydata([(-s, -s, 0), (s, -s, 0), (s, s, 0), (-s, s, 0)], [], [(0, 1, 2, 3)])
    o = bpy.data.objects.new("TMP_floor", me)
    o.location = (6005.0, -5.0, -0.001)
    m = bpy.data.materials.get("MAT_Limestone_Worn")
    me.materials.append(m)
    col.objects.link(o)
    import concordia_buildings as B
    B.box_uv(o)
    return o


def iso_cam(target, ortho):
    cam = K.new_cam("TMP_iso", ortho=ortho)
    cam.data.clip_end = 3000
    K.look_at(cam, Vector(target) + IK.CAM_BACK * 300.0, Vector(target))
    return cam


def main():
    from PIL import Image
    bpy.ops.wm.open_mainfile(filepath=BLEND)
    scene = bpy.context.scene
    K.setup_render(scene)
    scene.cycles.samples = 48
    floor(scene.collection)
    for o in bpy.data.objects:
        if o.name.endswith("-colonly"):
            o.hide_render = True
    props = {n: bpy.data.objects[n] for n in PM.PROPS}
    imported = {o.name: o for o in bpy.data.objects if o.type == "MESH" and
                str(o.get("prop_source", "")).startswith(("Quaternius", "Avramania"))}

    def lab(names):
        return [(f"{n[5:]} ({props[n]['prop_tris']})", props[n].location + Vector((0, 0, props[n].dimensions.z + 0.15)))
                for n in names]
    if want("props_ia_iso"):
        c = sum((props[n].location for n in PM.AI_FOUR), Vector()) / 4
        cam = iso_cam(c + Vector((0, 0, 0.7)), 9.5)
        K.render(scene, cam, P("props_ia_iso"))
        K.annotate(scene, cam, P("props_ia_iso"), "Los 4 objetos de la lista de IA, hechos a mano (CAM_Iso; triangulos)",
                   lab(PM.AI_FOUR))
        bpy.data.objects.remove(cam)
    if want("props_ia_cerca"):
        tiles = []
        res = scene.render.resolution_x, scene.render.resolution_y
        for n in PM.AI_FOUR:
            eye, tgt, lens = CLOSE[n]
            o = props[n].location
            cam = K.new_cam("TMP_close", lens=lens)
            K.look_at(cam, o + Vector(eye), o + Vector(tgt))
            path = P(f"tmp_{n}")
            K.render(scene, cam, path)
            K.annotate(scene, cam, path, f"{n} - {props[n]['prop_note']} ({props[n]['prop_tris']} tris)", [])
            tiles.append(path)
            bpy.data.objects.remove(cam)
        w, h = res[0] // 2, res[1] // 2
        sheet = Image.new("RGB", res)
        for i, p in enumerate(tiles):
            sheet.paste(Image.open(p).resize((w, h)), ((i % 2) * w, (i // 2) * h))
            os.remove(p)
        sheet.save(P("props_ia_cerca"))
    sheets = [(f"props_{b}_{src}", b, pre, f"{b.capitalize()} - {lab} (CC0)")
              for b in ("mercado", "oficios", "clases")
              for src, pre, lab in (("q", "PROP_Q_", "Quaternius Fantasy Props MegaKit"),
                                    ("av", "PROP_AV_", "Avramania Low Poly Medieval"))]
    for key, batch, pre, title in sheets:
        if not want(key):
            continue
        sel = [o for n, o in sorted(imported.items()) if n.startswith(pre) and o.get("prop_batch") == batch]
        if not sel:
            continue
        c = sum((o.location for o in sel), Vector()) / len(sel)
        span = max(max(abs(o.location.x - c.x), abs(o.location.y - c.y)) for o in sel)
        cam = iso_cam(c + Vector((0, 0, 0.5)), max(8.0, span * 2.6))
        K.render(scene, cam, P(key))
        K.annotate(scene, cam, P(key), f"{title}: materiales de Concordia; triangulos",
                   [(f"{o.name[len(pre):]} ({o['prop_tris']})", o.location + Vector((0, 0, o.dimensions.z + 0.1)))
                    for o in sel])
        bpy.data.objects.remove(cam)
    if want("props_triviales"):
        rest = [n for n in PM.PROPS if n not in PM.AI_FOUR]
        c = sum((props[n].location for n in rest), Vector()) / len(rest)
        cam = iso_cam(c + Vector((0, 0, 0.5)), 15.0)
        K.render(scene, cam, P("props_triviales"))
        K.annotate(scene, cam, P("props_triviales"), "14 props triviales hechos a mano (CAM_Iso; triangulos)", lab(rest))
        bpy.data.objects.remove(cam)


if __name__ == "__main__":
    main()
