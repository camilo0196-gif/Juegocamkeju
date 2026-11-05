"""
CONCORDIA - capturas de la etapa 10 (texturas Poly Haven).
  materiales            esfera de 1.6 m + plano de 4 x 4 m por material (UV de mundo), CAM_Iso
  iso_ciudad            CAM_Iso ortho 460
  iso_exterior_taludes  CAM_Iso ortho 90 en el SE: talud (roca + ceniza), foso (Ash_Gray), suelo exterior (Ash_Ground)
  iso_exterior_sector   CAM_Iso ortho 260: banda de transicion dentada en el exterior
  muralla_torre         CAM_Iso ortho 30 sobre la torre k=40: teja, madera (cadalsos), hierro
  muralla_puerta_sur    CAM_Iso ortho 40 sobre la Puerta Sur por fuera: hojas de hierro, madera, muralla gris
  mascaras_cenital      diagnostico 2D (PIL): clases por cara y caras protegidas tenidas por mascaras (debe ser 0)
  iso_talud_interior    CAM_Iso ortho 70 sobre la zona interior con mas roca junto a calles
Uso: python capture_stage10.py [-- nombre1,nombre2]
"""

import os
import sys
from math import cos, radians, sin

import bpy
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import concordia_const as C  # noqa: E402
import capture_stage02 as K  # noqa: E402

REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
BLEND = os.path.join(REPO, "blender", f"{C.BLEND_BASENAME}_v10.blend")
OUT = os.path.join(REPO, "docs", "captures")


def pol(a, r, z=0.0):
    return (r * cos(radians(a)), r * sin(radians(a)), z)


def face_classes(me):
    import stage10_apply as AP
    A = AP.mesh_arrays(me)
    mats = [m.name for m in me.materials]
    mi = np.zeros(A["nf"], dtype=np.int64)
    me.polygons.foreach_get("material_index", mi)
    names = np.array(mats)[mi]
    rock = AP.face_max(me, AP.corner_attr(me, "rock_mask"))
    ash = AP.face_max(me, AP.corner_attr(me, "ash_mask"))
    road = AP.face_max(me, AP.corner_attr(me, "road_mask"))
    slab = AP.face_max(me, AP.corner_attr(me, "slab_ring_id"))
    ret = AP.face_max(me, AP.corner_attr(me, "retaining_mask"))
    return A, names, rock, ash, road, slab, ret


def mask_diagnostic(path):
    from PIL import Image, ImageDraw, ImageFont
    me = bpy.data.objects["TRN_City"].data
    A, names, rock, ash, road, slab, ret = face_classes(me)
    cen = A["cen"]
    r = np.hypot(cen[:, 0], cen[:, 1])
    prot = ((road > 0.5) & (slab <= 0.01)) | (slab > 0.01) | ((ret > 0.5) & (r < C.WALL_BASE_R[1]))
    col = {"MAT_Cobble_Concordia": (70, 70, 74), "MAT_Stone_Repair": (120, 100, 80), "MAT_Plaza_Slab": (215, 210, 200),
           "MAT_Plaza_Slab_Travertino": (235, 225, 200), "MAT_Limestone_Worn": (255, 255, 255),
           "MAT_Wall_Gray": (40, 60, 90), "MAT_Ground_Cracked": (190, 170, 130), "MAT_Ash_Gray": (240, 150, 40),
           "MAT_Rock_Gray": (200, 30, 30)}
    S, half = 4, 212                                     # 4 px/m
    W = 2 * half * S
    img = Image.new("RGB", (W, W), (20, 20, 20))
    px = ((cen[:, 0] + half) * S).astype(int)
    py = ((half - cen[:, 1]) * S).astype(int)
    a = np.asarray(img).copy()
    ok = (px >= 0) & (px < W) & (py >= 0) & (py < W)
    for n, c in col.items():
        m = ok & (names == n)
        for dx in (0, 1, 2, 3):
            for dy in (0, 1, 2, 3):
                a[np.clip(py[m] + dy, 0, W - 1), np.clip(px[m] + dx, 0, W - 1)] = c
    bad = ok & prot & ((rock > 0) | (ash > 0) | np.isin(names, ["MAT_Rock_Gray", "MAT_Ash_Gray", "MAT_Ground_Cracked"]))
    img = Image.fromarray(a)
    d = ImageDraw.Draw(img)
    for x, y in zip(px[bad], py[bad]):
        d.ellipse([x - 6, y - 6, x + 6, y + 6], outline=(255, 0, 255), width=3)
    f = ImageFont.truetype("DejaVuSans.ttf", 30)
    legend = [("calle (adoquin)", col["MAT_Cobble_Concordia"]), ("remiendo", col["MAT_Stone_Repair"]),
              ("plaza / travertino", col["MAT_Plaza_Slab"]), ("muro de contencion", col["MAT_Limestone_Worn"]),
              ("suelo ciudad", col["MAT_Ground_Cracked"]), ("ceniza (ash_mask)", col["MAT_Ash_Gray"]),
              ("roca (rock_mask)", col["MAT_Rock_Gray"]), ("cauce", col["MAT_Wall_Gray"]),
              (f"protegidas tenidas por mascara: {int(bad.sum())}", (255, 0, 255))]
    d.rectangle([0, 0, W, 50], fill=(0, 0, 0))
    d.text((14, 10), "TRN_City - material por cara (cenital, Norte arriba, 4 px/m)", fill=(255, 255, 255), font=f)
    y = W - 20 - 42 * len(legend)
    for t, c in legend:
        d.rectangle([14, y + 4, 44, y + 34], fill=c)
        bb = d.textbbox((56, y), t, font=f)
        d.rectangle([bb[0] - 4, bb[1] - 3, bb[2] + 4, bb[3] + 3], fill=(0, 0, 0))
        d.text((56, y), t, fill=(255, 255, 255), font=f)
        y += 42
    img.save(path)
    # zona interior con mas roca a menos de 3 m de una calle
    rk = np.nonzero((names == "MAT_Rock_Gray") & (r < 185))[0]
    best = None
    if len(rk):
        cx = np.round(cen[rk, 0] / 40) * 40
        cy = np.round(cen[rk, 1] / 40) * 40
        keys, cnt = np.unique(np.stack([cx, cy], 1), axis=0, return_counts=True)
        best = tuple(keys[np.argmax(cnt)])
    return int(bad.sum()), best


def main():
    only = set(sys.argv[sys.argv.index("--") + 1].split(",")) if "--" in sys.argv else None
    bpy.ops.wm.open_mainfile(filepath=BLEND)
    scene = bpy.context.scene
    K.setup_render(scene)
    for o in list(bpy.data.collections["WALL_KIT"].all_objects):
        o.hide_render = True
    for o in list(bpy.data.collections["WALL_LAYOUT"].objects):
        if o.name.endswith("-colonly"):
            o.hide_render = True
    cam_iso = bpy.data.objects[C.CAM_ISO_NAME]
    P = lambda n: os.path.join(OUT, f"stage10_{n}.png")  # noqa: E731

    def want(n):
        return only is None or n in only
    if want("materiales"):
        import stage10_apply as AP
        names = AP.MATERIALS
        cells = [(n, 1000 + (i % 5) * 7.0, 1000 - (i // 5) * 7.0) for i, n in enumerate(names)]
        cx = sum(c[1] for c in cells) / len(cells)
        cy = sum(c[2] for c in cells) / len(cells)
        rx, ry = scene.render.resolution_x, scene.render.resolution_y
        scene.render.resolution_x, scene.render.resolution_y = 2400, 1800
        cam = K.iso_at(cam_iso, (cx, cy, 0.0), 44.0)
        K.render(scene, cam, P("materiales"))
        K.annotate(scene, cam, P("materiales"), "Materiales de Concordia - esfera 1.6 m + plano 4 x 4 m (UV de mundo, "
                   "escala real) - CAM_Iso", [(n[4:], (x - 2.0, y + 2.0, 0.0)) for n, x, y in cells])
        scene.render.resolution_x, scene.render.resolution_y = rx, ry
    if want("iso_ciudad"):
        cam = K.iso_at(cam_iso, C.CAM_ISO_TARGET, 460.0)
        K.render(scene, cam, P("iso_ciudad"))
        K.annotate(scene, cam, P("iso_ciudad"), "Concordia con texturas Poly Haven - CAM_Iso, ortho TEMPORAL 460", [])
    if want("iso_exterior_taludes"):
        cam = K.iso_at(cam_iso, pol(-45, 214, 0.0), 90.0)
        K.render(scene, cam, P("iso_exterior_taludes"))
        K.annotate(scene, cam, P("iso_exterior_taludes"),
                   "Exterior SE: talud (Rock_Gray + Ash_Gray), foso (Ash_Gray), suelo (Ash_Ground) - ortho 90",
                   [("talud", pol(-45, 207, 3.0)), ("foso", pol(-45, 217, -1.2)), ("Ash_Ground", pol(-45, 232, 0.3)),
                    ("muralla", pol(-45, 200, 12.0))])
    if want("iso_exterior_sector"):
        cam = K.iso_at(cam_iso, pol(-45, 280, 0.0), 260.0)
        cam.data.clip_end = 3000
        K.render(scene, cam, P("iso_exterior_sector"))
        K.annotate(scene, cam, P("iso_exterior_sector"), "Exterior SE - transiciones dentadas entre Ash_Ground, "
                   "Ash_Gray (dunas, foso) y Rock_Gray - ortho 260", [])
    if want("muralla_torre"):
        cam = K.iso_at(cam_iso, pol(300, 203, 9.0), 30.0)
        K.render(scene, cam, P("muralla_torre"))
        K.annotate(scene, cam, P("muralla_torre"), "Torre k=40 por fuera: teja (roof_09), madera (weathered_planks), "
                   "hierro (metal_plate_02), muralla (castle_wall_slates) - ortho 30", [])
    if want("muralla_puerta_sur"):
        cam = K.iso_at(cam_iso, pol(270, 204, 5.0), 40.0)
        K.render(scene, cam, P("muralla_puerta_sur"))
        K.annotate(scene, cam, P("muralla_puerta_sur"), "Puerta Sur por fuera: hojas de hierro, cadalsos de madera, "
                   "muralla gris - ortho 40", [])
    best = None
    if want("mascaras_cenital") or want("iso_talud_interior"):
        bad, best = mask_diagnostic(P("mascaras_cenital"))
        print("mask diagnostic: protected faces tinted =", bad, "best inner rock zone", best)
    if want("iso_talud_interior") and best is not None:
        bx, by = best
        cam = K.iso_at(cam_iso, (bx, by, 4.0), 70.0)
        K.render(scene, cam, P("iso_talud_interior"))
        K.annotate(scene, cam, P("iso_talud_interior"), f"Taludes interiores con roca junto a calles ({bx:.0f}, {by:.0f}) "
                   "- la roca no invade calles, terrazas ni muros - ortho 70", [])


if __name__ == "__main__":
    main()
