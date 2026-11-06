"""
CONCORDIA - etapa 17, pendiente D: manchas de material en LOD2. CAM_Iso a ortho 45 y 120 (1920 px de ancho),
LOD0 frente a LOD2 de cada edificio, recortado al edificio. Escribe docs/captures/stage17_lod2_test.png y
docs/reports/stage17_lod2_test.json (diferencia media y % de pixeles que cambian mas de 25/255).
"""

import json
import os
import sys

import bpy
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import concordia_const as C  # noqa: E402
import capture_stage02 as K  # noqa: E402

REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
BLEND = os.path.join(REPO, "blender", f"{C.BLEND_BASENAME}_v17.blend")
SP = os.environ.get("LOD_TMP", os.path.join(REPO, "docs", "captures", "_lod_tmp"))
BUILDINGS = [("TEST_Casa_12x9", ("TEST_Casa_12x9_Body", "TEST_Casa_12x9_Roof")),
             ("SANTUARIO", ("SANTUARIO_Body", "SANTUARIO_Roof")),
             ("SALON_HAZANAS", ("SALON_HAZANAS_Body", "SALON_HAZANAS_Roof")),
             ("FARO", ("FARO_Body",)), ("OBELISK", ("OBELISK_Body",)), ("PORTAL_Arch", ("PORTAL_Arch",))]
SCALES = (45.0, 120.0)


def show(names, lod):
    for n in names:
        for suf in ("", "_LOD1", "_LOD2"):
            o = bpy.data.objects.get(n + suf)
            if o:
                o.hide_render = (suf != ("" if lod == 0 else "_LOD2"))


def border(scene, cam, objs, pad=0.02):
    xs, ys = [], []
    for o in objs:
        for b in o.bound_box:
            p = world_to_camera_view(scene, cam, o.matrix_world @ Vector(b))
            xs.append(p.x)
            ys.append(p.y)
    r = scene.render
    r.use_border, r.use_crop_to_border = True, True
    r.border_min_x, r.border_max_x = max(0, min(xs) - pad), min(1, max(xs) + pad)
    r.border_min_y, r.border_max_y = max(0, min(ys) - pad), min(1, max(ys) + pad)


def main():
    import numpy as np
    from PIL import Image, ImageDraw, ImageFont
    os.makedirs(SP, exist_ok=True)
    bpy.ops.wm.open_mainfile(filepath=BLEND)
    scene = bpy.context.scene
    K.setup_render(scene)
    for o in list(bpy.data.collections["WALL_KIT"].all_objects):
        o.hide_render = True
    for o in bpy.data.objects:
        if o.name.endswith(("-colonly", "_LOD1", "_LOD2", "-navmesh", "-occonly", "_InteriorVolume")):
            o.hide_render = True
    cam_iso = bpy.data.objects[C.CAM_ISO_NAME]
    res, rows = {}, []
    for root_name, parts in BUILDINGS:
        root = bpy.data.objects[root_name]
        objs = [bpy.data.objects[n] for n in parts]
        c = sum((o.matrix_world @ (sum((Vector(b) for b in o.bound_box), Vector()) / 8) for o in objs), Vector()) / len(objs)
        row = []
        res[root_name] = {}
        for sc in SCALES:
            cam = K.iso_at(cam_iso, tuple(c), sc)
            cam.data.clip_end = 5000
            scene.camera = cam
            bpy.context.view_layer.update()
            border(scene, cam, objs)
            imgs = []
            for lod in (0, 2):
                show(parts, lod)
                p = os.path.join(SP, f"{root_name}_o{int(sc)}_lod{lod}.png")
                K.render(scene, cam, p)
                imgs.append(np.asarray(Image.open(p).convert("RGB")).astype(np.int16))
            show(parts, 0)
            d = np.abs(imgs[0] - imgs[1]).max(axis=2)
            res[root_name][f"ortho_{int(sc)}"] = {"px": list(imgs[0].shape[:2][::-1]),
                                                   "mean_diff": round(float(d.mean()), 2),
                                                   "pct_px_over_25": round(100 * float((d > 25).mean()), 2),
                                                   "pct_px_over_50": round(100 * float((d > 50).mean()), 2)}
            row.append([Image.fromarray(i.astype(np.uint8)) for i in imgs])
            bpy.data.objects.remove(cam)
        rows.append((root_name, row))
        _ = root
    scene.render.use_border = False
    # hoja: por edificio, [LOD0 | LOD2] a ortho 45 y [LOD0 | LOD2] a ortho 120 (x3, vecino mas proximo, para verlo)
    f = ImageFont.truetype("DejaVuSans.ttf", 18)
    tiles = []
    for name, row in rows:
        a45 = row[0]
        a120 = [im.resize((im.width * 3, im.height * 3), Image.NEAREST) for im in row[1]]
        h = max(a45[0].height, a120[0].height) + 30
        w = sum(i.width for i in a45) + sum(i.width for i in a120) + 60
        t = Image.new("RGB", (w, h), (25, 25, 25))
        d = ImageDraw.Draw(t)
        x = 10
        for lab, im in zip(("LOD0 o45", "LOD2 o45", "LOD0 o120 (x3)", "LOD2 o120 (x3)"), a45 + a120):
            t.paste(im, (x, 28))
            d.text((x, 4), f"{name} {lab}", fill=(255, 255, 255), font=f)
            x += im.width + 12
        tiles.append(t)
    W = max(t.width for t in tiles)
    sheet = Image.new("RGB", (W, sum(t.height for t in tiles)), (25, 25, 25))
    y = 0
    for t in tiles:
        sheet.paste(t, (0, y))
        y += t.height
    out = os.path.join(REPO, "docs", "captures", "stage17_lod2_test.png")
    sheet.save(out)
    with open(os.path.join(REPO, "docs", "reports", "stage17_lod2_test.json"), "w") as fh:
        json.dump(res, fh, indent=1)
    print(json.dumps(res))


if __name__ == "__main__":
    main()
