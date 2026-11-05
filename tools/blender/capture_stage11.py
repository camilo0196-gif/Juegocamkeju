"""
CONCORDIA - captura de la etapa 11: silueta de la ciudad con los chunks LOD0 frente a LOD2 (CAM_Iso, ortho 460).
Salida: docs/captures/stage11_lod0_vs_lod2.png (izquierda LOD0, derecha LOD2).
"""

import os
import sys

import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import concordia_const as C  # noqa: E402
import capture_stage02 as K  # noqa: E402

REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
MASTER = os.path.join(REPO, "blender", f"{C.BLEND_BASENAME}_master_v11.blend")
OUT = os.path.join(REPO, "docs", "captures")


def show_only(lod):
    keep_cols = {f"GODOT_CITY_{lod}", f"GODOT_EXT_{lod}", "WALL_LAYOUT", "STREETS", "PLAZA", "MORADAS", "CAUCE"}
    if lod == "LOD0":
        keep_cols.add("GODOT_EXT_CLIFF")
    for o in bpy.data.objects:
        if o.type not in ("MESH",):
            continue
        cn = o.users_collection[0].name if o.users_collection else ""
        o.hide_render = not (cn in keep_cols) or o.name.endswith(("-colonly", "-occonly", "-navmesh"))
    for c in bpy.data.collections:
        c.hide_render = False


def main():
    from PIL import Image, ImageDraw, ImageFont
    bpy.ops.wm.open_mainfile(filepath=MASTER)
    scene = bpy.context.scene
    K.setup_render(scene)
    cam_iso = bpy.data.objects[C.CAM_ISO_NAME]
    paths = []
    for lod in ("LOD0", "LOD2"):
        show_only(lod)
        cam = K.iso_at(cam_iso, C.CAM_ISO_TARGET, 460.0)
        p = os.path.join(OUT, f"stage11_tmp_{lod}.png")
        K.render(scene, cam, p)
        paths.append(p)
    a, b = (Image.open(p).convert("RGB") for p in paths)
    w, h = a.size
    out = Image.new("RGB", (w * 2 + 10, h + 50), (0, 0, 0))
    out.paste(a, (0, 50))
    out.paste(b, (w + 10, 50))
    d = ImageDraw.Draw(out)
    f = ImageFont.truetype("DejaVuSans.ttf", 30)
    d.text((14, 8), "LOD0 (452.076 tris de terreno)", fill=(255, 255, 255), font=f)
    d.text((w + 24, 8), "LOD2 (15 % + silueta bloqueada) - CAM_Iso ortho 460", fill=(255, 255, 255), font=f)
    out.save(os.path.join(OUT, "stage11_lod0_vs_lod2.png"))
    for p in paths:
        os.remove(p)


if __name__ == "__main__":
    main()
