"""
CONCORDIA - auditoria de materiales y memoria de texturas (etapa 17).
Lee blender/concordia_v17.blend y los .glb de export/godot. Escribe docs/reports/stage17_materials.json.
  - por material: grafo (tipos de nodo), color base / textura, emision (color y fuerza), alpha y modo de mezcla
  - comprobacion de paleta: nada saturado fuera del azul palido
  - comprobacion de export: solo Image Texture -> Principled BSDF o valores planos (+ Mix Multiply = baseColorFactor)
  - memoria de texturas de la ciudad (mismo criterio que la etapa 10) frente al limite de 220 MB
  - lo que de verdad sale en los .glb (baseColorFactor, emissiveFactor, KHR_materials_emissive_strength, alphaMode)
"""

import colorsys
import glob
import json
import os
import struct
import sys

import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
BLEND = os.path.join(REPO, "blender", "concordia_v17.blend")
OUT = os.path.join(REPO, "docs", "reports", "stage17_materials.json")
LIMIT_MB = 220.0
NEW = ["MAT_Roof_Tile_Ocher_B", "MAT_Window_Warm", "MAT_Portal_Veil", "MAT_Rune_Glow_12", "MAT_Rune_Glow_10",
       "MAT_Obelisk_Black", "MAT_Obelisk_Mark", "MAT_Obelisk_Mark_Lit", "MAT_Shard_Blue_E40", "MAT_Faro_Beam",
       "MAT_Pipe_Glass", "MAT_Pipe_Light_Core", "MAT_Limestone_Light", "MAT_Stained_Glass_Blue", "MAT_Bronze_Aged"]
OK_NODES = {"OUTPUT_MATERIAL", "BSDF_PRINCIPLED", "TEX_IMAGE", "UVMAP", "MAPPING", "SEPARATE_COLOR", "NORMAL_MAP",
            "GROUP", "MIX"}
BLUE_HUE = (185.0, 215.0)
SAT_MAX = 0.35


def srgb(c):
    c = max(0.0, min(1.0, c))
    return 1.055 * c ** (1 / 2.4) - 0.055 if c > 0.0031308 else 12.92 * c


def hexs(rgb):
    return "#%02X%02X%02X" % tuple(int(round(max(0, min(1, v)) * 255)) for v in rgb)


_mean = {}


def tex_mean(img):
    p = bpy.path.abspath(img.filepath)
    if p not in _mean:
        from PIL import Image
        import numpy as np
        a = np.asarray(Image.open(p).convert("RGB").resize((256, 256))).astype("float32") / 255.0
        _mean[p] = tuple(float(v) for v in a.reshape(-1, 3).mean(0))
    return _mean[p]


def palette_ok(rgb_srgb, what):
    h, s, v = colorsys.rgb_to_hsv(*rgb_srgb)
    hue = h * 360
    blue = BLUE_HUE[0] <= hue <= BLUE_HUE[1]
    return {"what": what, "hex": hexs(rgb_srgb), "hue": round(hue, 1), "sat": round(s, 3), "val": round(v, 3),
            "ok": blue or s <= SAT_MAX}


def audit(m):
    nt = m.node_tree
    b = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
    types = sorted({n.type for n in nt.nodes})
    rec = {"nodes": types, "export_graph_ok": set(types) <= OK_NODES}
    imgs = {n.name: n.image for n in nt.nodes if n.type == "TEX_IMAGE" and n.image}
    rec["textures"] = {k: os.path.relpath(bpy.path.abspath(v.filepath), REPO) for k, v in imgs.items()}
    factor = None
    for n in nt.nodes:
        if n.type == "MIX":
            rec["mix"] = {"blend": n.blend_type, "B": [round(c, 3) for c in n.inputs["B"].default_value[:3]]}
            factor = n.inputs["B"].default_value[:3]
            if n.blend_type != "MULTIPLY":
                rec["export_graph_ok"] = False
    bc = b.inputs["Base Color"]
    if "Albedo" in imgs:
        mean = tex_mean(imgs["Albedo"])
        if factor:
            mean = tuple(srgb(((mc + 0.055) / 1.055) ** 2.4 * f) for mc, f in zip(mean, factor))
        rec["base"] = {"texture_mean_srgb": hexs(mean), "factor": [round(f, 3) for f in factor] if factor else None}
        checks = [palette_ok(mean, "albedo medio")]
    else:
        lin = bc.default_value[:3]
        s = tuple(srgb(c) for c in lin)
        rec["base"] = {"flat_srgb": hexs(s)}
        checks = [palette_ok(s, "color base")]
    es = b.inputs["Emission Strength"].default_value
    ec = b.inputs["Emission Color"]
    if ec.is_linked:
        rec["emission"] = {"strength": es, "color": "textura " + ec.links[0].from_node.name}
    else:
        s = tuple(srgb(c) for c in ec.default_value[:3])
        rec["emission"] = {"strength": round(es, 3), "color": hexs(s)}
        if es > 0:
            checks.append(palette_ok(s, "emision"))
    rec["alpha"] = round(b.inputs["Alpha"].default_value, 3)
    rec["blend"] = getattr(m, "surface_render_method", getattr(m, "blend_method", "?"))
    rec["backface_culling"] = m.use_backface_culling
    rec["palette"] = checks
    rec["palette_ok"] = all(c["ok"] for c in checks)
    rec["users"] = m.users
    return rec


def glb_materials():
    out = {}
    for path in sorted(glob.glob(os.path.join(REPO, "export", "godot", "*.glb"))):
        with open(path, "rb") as fh:
            data = fh.read()
        ln = struct.unpack("<I", data[12:16])[0]
        g = json.loads(data[20:20 + ln])
        for mt in g.get("materials", []):
            n = mt.get("name")
            if n not in NEW or n in out:
                continue
            pbr = mt.get("pbrMetallicRoughness", {})
            out[n] = {"file": os.path.basename(path), "baseColorFactor": pbr.get("baseColorFactor"),
                      "baseColorTexture": "baseColorTexture" in pbr, "emissiveFactor": mt.get("emissiveFactor"),
                      "emissive_strength": mt.get("extensions", {}).get("KHR_materials_emissive_strength",
                                                                         {}).get("emissiveStrength"),
                      "emissiveTexture": "emissiveTexture" in mt, "alphaMode": mt.get("alphaMode", "OPAQUE"),
                      "doubleSided": mt.get("doubleSided", False)}
    return out


def memory():
    """Imagenes que usan los materiales MAT_* con usuarios (sin la biblioteca de muestras)."""
    seen = {}
    for m in bpy.data.materials:
        if not m.name.startswith("MAT_") or not m.use_nodes:
            continue
        used = any(o.type == "MESH" and any(s.material == m for s in o.material_slots) and not any(
            c.name.startswith("MATERIAL_LIBRARY") for c in o.users_collection) for o in bpy.data.objects)
        if not used:
            continue
        for n in m.node_tree.nodes:
            if n.type == "TEX_IMAGE" and n.image:
                p = os.path.relpath(bpy.path.abspath(n.image.filepath), REPO)
                if p in seen:
                    continue
                w, h = n.image.size
                bpp = 1.0 if n.name == "Normal" else 0.5
                seen[p] = {"role": n.name, "px": [w, h], "vram_mb": round(w * h * bpp * 4 / 3 / 2 ** 20, 2),
                           "material": m.name}
    total = round(sum(v["vram_mb"] for v in seen.values()), 1)
    return {"images": len(seen), "total_vram_mb": total, "limit_mb": LIMIT_MB, "ok": total <= LIMIT_MB,
            "criterion": "Godot 4 VRAM Compressed: albedo/ORM/emision BC1 0.5 B/px, normal BC5 1 B/px, mipmaps x4/3",
            "list": seen}


def main():
    bpy.ops.wm.open_mainfile(filepath=BLEND)
    st = {"materials": {}}
    for n in NEW:
        m = bpy.data.materials.get(n)
        st["materials"][n] = audit(m) if m else "NO EXISTE"
    # derivacion de MAT_Shard_Blue_E40
    a, b = bpy.data.materials["MAT_Shard_Blue"], bpy.data.materials["MAT_Shard_Blue_E40"]
    ba = next(n for n in a.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    bb = next(n for n in b.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    diff = []
    for inp in ba.inputs:
        if inp.name in bb.inputs and hasattr(inp, "default_value") and not inp.is_linked:
            va, vb = inp.default_value, bb.inputs[inp.name].default_value
            try:
                va, vb = tuple(va), tuple(vb)
            except TypeError:
                pass
            if va != vb:
                diff.append(inp.name)
    st["shard_e40_vs_shard"] = {"differs_in": diff,
                                "same_textures": sorted(n.image.name for n in a.node_tree.nodes if n.type == "TEX_IMAGE")
                                == sorted(n.image.name for n in b.node_tree.nodes if n.type == "TEX_IMAGE"),
                                "emission_strength": [ba.inputs["Emission Strength"].default_value,
                                                      bb.inputs["Emission Strength"].default_value],
                                "shard_blue_emission": audit(a)["emission"], "shard_blue_base": audit(a)["base"]}
    st["glb"] = glb_materials()
    st["memory"] = memory()
    with open(OUT, "w") as fh:
        json.dump(st, fh, indent=1, ensure_ascii=False)
    for n, r in st["materials"].items():
        if isinstance(r, str):
            print(n, r)
            continue
        print(f"{n:24s} graph_ok={r['export_graph_ok']} palette_ok={r['palette_ok']} base={r['base']} "
              f"em={r['emission']} a={r['alpha']} {r['blend']} " + " ".join(f"{c['what']}:{c['hex']} s{c['sat']} h{c['hue']}"
                                                                        for c in r["palette"]))
    print("E40:", st["shard_e40_vs_shard"])
    print("GLB:", json.dumps(st["glb"])[:3000])
    print("MEM:", {k: v for k, v in st["memory"].items() if k != "list"})


if __name__ == "__main__":
    main()
