"""
CONCORDIA - ajustes de importacion repetibles: reescribe la seccion [params] de los .import (Godot 4.7.2).
Valores verificados en la documentacion oficial 4.7 (docs/reference/godot47/class_resourceimporterscene.txt y
class_resourceimportertexture.txt) y en los .import que genera el propio motor.

Escenas (.glb, importer "scene"):
  nodes/root_scale = 1.0, nodes/apply_root_scale = true      (metros, sin escalar)
  nodes/use_name_suffixes = true, nodes/use_node_type_suffixes = true   (-colonly, -navmesh, -occonly)
  meshes/ensure_tangents = true                                (normal maps)
  meshes/generate_lods = false                                 (usamos _LOD1 / _LOD2 propios)
  meshes/create_shadow_meshes = true                           (sombra de malla activada)
  meshes/light_baking = 1 (Static); interiores: 2 (Static Lightmaps, genera UV2) solo con --lightmaps
  import_script/path = res://tools/post_import.gd
Texturas (importer "texture"):
  compress/mode = 2 (VRAM Compressed), mipmaps/generate = true
  compress/normal_map = 1 (Enable, RGTC) en las que algun material usa como normalTexture; 0 (Detect) en el resto
  process/normal_map_invert_y = false (las normales salen de Blender en convencion OpenGL, la de Godot)

python3 godot_concordia/tools/import_settings.py [--lightmaps]
Despues: godot --headless --path godot_concordia --import  (reimporta lo que cambio)
"""

import json
import os
import re
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.path.abspath(os.path.join(HERE, ".."))
ASSETS = os.path.join(PROJECT, "assets")

SCENE = {
    "nodes/root_scale": "1.0", "nodes/apply_root_scale": "true", "nodes/use_name_suffixes": "true",
    "nodes/use_node_type_suffixes": "true", "meshes/ensure_tangents": "true", "meshes/generate_lods": "false",
    "meshes/create_shadow_meshes": "true", "meshes/light_baking": "1",
    "import_script/path": '"res://tools/post_import.gd"',
}
TEXTURE = {"compress/mode": "2", "mipmaps/generate": "true", "process/normal_map_invert_y": "false"}


def normal_textures():
    """Rutas (res://) de las imagenes usadas como normalTexture en algun material de algun .glb."""
    out = set()
    for dp, _dn, fs in os.walk(ASSETS):
        for f in fs:
            if not f.endswith(".glb"):
                continue
            p = os.path.join(dp, f)
            with open(p, "rb") as fh:
                head = fh.read(20)
                ln = struct.unpack_from("<I", head, 12)[0]
                js = json.loads(fh.read(ln))
            imgs = js.get("images", [])
            texs = js.get("textures", [])
            for m in js.get("materials", []):
                nt = m.get("normalTexture")
                if nt is None:
                    continue
                src = texs[nt["index"]].get("source")
                uri = imgs[src].get("uri") if src is not None and src < len(imgs) else None
                if uri:
                    full = os.path.normpath(os.path.join(dp, uri.replace("%20", " ")))
                    out.add(os.path.relpath(full, PROJECT))
    return out


def set_params(path, values):
    txt = open(path).read()
    if "[params]" not in txt:
        return False
    head, params = txt.split("[params]", 1)
    lines = params.strip("\n").split("\n")
    keys = {ln.split("=", 1)[0]: i for i, ln in enumerate(lines) if "=" in ln}
    changed = False
    for k, v in values.items():
        new = f"{k}={v}"
        if k in keys:
            if lines[keys[k]] != new:
                lines[keys[k]] = new
                changed = True
        else:
            lines.append(new)
            changed = True
    if changed:
        open(path, "w").write(head + "[params]\n\n" + "\n".join(l for l in lines if l.strip()) + "\n")
    return changed


def main():
    lm = "--lightmaps" in sys.argv
    normals = normal_textures()
    stats = {"escenas": 0, "texturas": 0, "normales": 0, "cambiados": 0}
    for dp, _dn, fs in os.walk(ASSETS):
        for f in fs:
            if not f.endswith(".import"):
                continue
            p = os.path.join(dp, f)
            txt = open(p).read()
            imp = re.search(r'^importer="(\w+)"', txt, re.M)
            imp = imp.group(1) if imp else ""
            if imp == "scene":
                vals = dict(SCENE)
                if lm and os.path.basename(dp) == "glb" and "interiors" in dp:
                    vals["meshes/light_baking"] = "2"
                stats["escenas"] += 1
            elif imp == "texture":
                vals = dict(TEXTURE)
                rel = os.path.relpath(p[:-len(".import")], PROJECT)
                is_n = rel in normals
                vals["compress/normal_map"] = "1" if is_n else "0"
                stats["texturas"] += 1
                stats["normales"] += is_n
            else:
                continue
            stats["cambiados"] += set_params(p, vals)
    print(json.dumps(stats))


if __name__ == "__main__":
    main()
