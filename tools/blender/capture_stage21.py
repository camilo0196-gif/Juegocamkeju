"""
CONCORDIA - capturas de la etapa 21 (E8, Razas).
  barrio_01..06   isometrica de cada barrio (direccion de CAM_Iso, misma escala ortho para los 6, haz del Faro oculto)
  comparacion     los 6 barrios lado a lado (3 x 2) con su preset: material, tejado, escala de puerta y colores
  razas_iso       el distrito entero, CAM_Iso ortho 150
`-- nombre ...` para repetir solo algunas (la comparacion se compone con las isometricas que haya en disco).
"""

import json
import os
import sys

import bpy
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import concordia_const as C  # noqa: E402
import capture_stage02 as K  # noqa: E402

REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
BLEND = os.path.join(REPO, "blender", f"{C.BLEND_BASENAME}_v21.blend")
OUT = os.path.join(REPO, "docs", "captures")
REPORT = os.path.join(REPO, "docs", "reports", "stage21_razas.json")
ONLY = set(sys.argv[sys.argv.index("--") + 1:]) if "--" in sys.argv else set()
ORTHO = 52.0


def P(n):
    return os.path.join(OUT, f"stage21_{n}.png")


def want(n):
    return not ONLY or n in ONLY


def barrio_roots(i):
    names = [f"CasaRaza_{i:02d}", f"Plazuela_{i:02d}"] + sorted(o.name for o in bpy.data.objects
                                                                 if o.name.startswith(f"RAZ_B{i:02d}_Casa_") and o.type == "EMPTY"
                                                                 and o.parent is None)
    return [bpy.data.objects[n] for n in names if n in bpy.data.objects]


def centre(roots):
    ps = [r.matrix_world.translation for r in roots]
    c = sum(ps, Vector()) / len(ps)
    return Vector((c.x, c.y, c.z + 4.0))


def comparison(st):
    from PIL import Image, ImageDraw, ImageFont
    f = ImageFont.truetype("DejaVuSans-Bold.ttf", 26)
    fs = ImageFont.truetype("DejaVuSans.ttf", 19)
    TW, TH, LH = 900, 506, 118
    sheet = Image.new("RGB", (TW * 3, (TH + LH) * 2 + 60), (26, 26, 26))
    d = ImageDraw.Draw(sheet)
    d.text((20, 14), "Barrios de las razas (E8) - CAM_Iso, misma escala (ortho %d) - silueta del tejado y color dominante" % ORTHO,
           fill=(255, 255, 255), font=f)
    for k in range(6):
        i = k + 1
        p = P(f"barrio_{i:02d}")
        if not os.path.exists(p):
            continue
        im = Image.open(p).convert("RGB")
        w, h = im.size
        im = im.crop((0, int(h * 0.04), w, h)).resize((TW, TH))
        x0, y0 = (k % 3) * TW, 60 + (k // 3) * (TH + LH)
        sheet.paste(im, (x0, y0))
        b = st["barrios"][f"B{i:02d}"]
        d.rectangle((x0, y0 + TH, x0 + TW - 1, y0 + TH + LH - 1), fill=(36, 36, 36))
        ban = os.path.join(REPO, "textures", "concordia", "MAT_Banner", f"concordia_banner_raza_{b['preset'].lower()}_albedo.png")
        if os.path.exists(ban):
            sheet.paste(Image.open(ban).convert("RGB").resize((50, 100)), (x0 + 12, y0 + TH + 9))
        d.text((x0 + 76, y0 + TH + 8), f"B{i:02d} - {b['preset']}: {b['material']}, tejado {b['roof']}"
               + (f" {b['pitch']:.0f} grados" if b['pitch'] else ""), fill=(255, 255, 255), font=fs)
        d.text((x0 + 76, y0 + TH + 36), f"puerta x{b['door_scale']}   casas {b['houses_built']} (parcelas)   simbolo {b['symbol']}",
               fill=(215, 215, 215), font=fs)
        cb, cr = b["colors"]["Body"], b["colors"]["Roof"]
        d.text((x0 + 76, y0 + TH + 64), "muros", fill=(215, 215, 215), font=fs)
        d.rectangle((x0 + 140, y0 + TH + 64, x0 + 190, y0 + TH + 86), fill=cb["hex"])
        d.text((x0 + 198, y0 + TH + 64), f"{cb['hex']} s{cb['saturation']:.2f}", fill=(215, 215, 215), font=fs)
        d.text((x0 + 400, y0 + TH + 64), "tejado", fill=(215, 215, 215), font=fs)
        d.rectangle((x0 + 472, y0 + TH + 64, x0 + 522, y0 + TH + 86), fill=cr["hex"])
        d.text((x0 + 530, y0 + TH + 64), f"{cr['hex']} s{cr['saturation']:.2f}", fill=(215, 215, 215), font=fs)
    sheet.save(P("comparacion"), optimize=True)
    return P("comparacion")


def main():
    with open(REPORT) as fh:
        st = json.load(fh)
    if ONLY == {"comparacion"}:
        print("render:", comparison(st))
        return
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
    for i in range(1, st["N_RAZAS"] + 1):
        n = f"barrio_{i:02d}"
        if not want(n):
            continue
        roots = barrio_roots(i)
        b = st["barrios"][f"B{i:02d}"]
        cam = K.iso_at(cam_iso, tuple(centre(roots)), ORTHO)
        cam.data.clip_end = 5000
        K.render(scene, cam, P(n))
        labs = [(f"Casa de la Raza {i} ({b['preset']})", tuple(bpy.data.objects[f"CasaRaza_{i:02d}"].matrix_world @
                                                                Vector((0, 0, 12))))]
        labs.append(("plazuela", tuple(bpy.data.objects[f"Plazuela_{i:02d}"].matrix_world.translation + Vector((0, 0, 3)))))
        sp = bpy.data.objects.get(f"MARKER_RaceSpawn_{i:02d}")
        if sp:
            labs.append(("spawn", tuple(sp.matrix_world.translation)))
        K.annotate(scene, cam, P(n), f"Barrio {i} - {b['preset']}: {b['material']}, tejado {b['roof']}, puerta x{b['door_scale']}, "
                   f"{b['houses_built']} casas en parcelas - CAM_Iso ortho {ORTHO:.0f}", labs)
        bpy.data.objects.remove(cam)
    if want("razas_iso"):
        cam = K.iso_at(cam_iso, (0.0, -125.0, 6.0), 150.0)
        cam.data.clip_end = 5000
        K.render(scene, cam, P("razas_iso"))
        labs = [(f"B{i:02d} {st['barrios'][f'B{i:02d}']['preset']}", tuple(bpy.data.objects[f"CasaRaza_{i:02d}"].matrix_world @
                                                                         Vector((0, 0, 12)))) for i in range(1, st["N_RAZAS"] + 1)]
        K.annotate(scene, cam, P("razas_iso"), "Distrito Sur (Razas) - CAM_Iso ortho 150: 6 barrios con presets R01..R06", labs)
    if want("comparacion"):
        print("render:", comparison(st))


if __name__ == "__main__":
    main()
