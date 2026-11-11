"""
CONCORDIA - copia las exportaciones de Blender al proyecto de Godot (godot_concordia/assets/) con MANIFEST (sha256).

Origen (del repositorio):  export/godot_v28/*.glb  (ciudad v28: prioridad)
                           export/godot/*.glb      (lo que no esta en godot_v28: exterior, muralla, interiores,
                                                    props de interior, personaje)
                           textures/**             (texturas externas de los .glb)
Destino:  assets/<tipo>/glb/<archivo>.glb  y  assets/textures/**
Los .glb apuntan a sus texturas con '../../textures/...': por eso cada .glb queda dos niveles por debajo de assets/
(assets/<tipo>/glb/), y las texturas en assets/textures/ (misma estructura que textures/ del repositorio).
Los binarios del proyecto NO van a git (estan ya en export/ y textures/ del repositorio): ver godot_concordia/.gitignore.

python3 godot_concordia/tools/sync_assets.py [--check]
  --check  solo compara con el MANIFEST y dice que cambiaria (no copia)
"""

import hashlib
import json
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.path.abspath(os.path.join(HERE, ".."))
REPO = os.path.abspath(os.path.join(PROJECT, ".."))
SOURCES = [os.path.join(REPO, "export", "godot_v28"), os.path.join(REPO, "export", "godot")]
TEXTURES = os.path.join(REPO, "textures")
ASSETS = os.path.join(PROJECT, "assets")
MANIFEST = os.path.join(ASSETS, "MANIFEST.txt")
TEX_EXT = (".png", ".jpg", ".jpeg", ".exr", ".webp")


def kind(name):
    n = name.lower()
    if n.startswith("concordia_terrain_"):
        return "terrain"
    if n.startswith("concordia_wall_"):
        return "wall"
    if n.startswith("concordia_markers"):
        return "markers"
    if n.startswith("int_"):
        return "interiors"
    if n.startswith(("props_", "bld_props")):
        return "props"
    if n.startswith("pj_"):
        return "characters"
    if n.startswith("bld_"):
        return "buildings"
    return "props"


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for ch in iter(lambda: fh.read(1 << 20), b""):
            h.update(ch)
    return h.hexdigest()


def plan():
    out = {}                                   # destino relativo -> origen absoluto
    for src in SOURCES:
        if not os.path.isdir(src):
            continue
        for f in sorted(os.listdir(src)):
            if not f.endswith(".glb"):
                continue
            dst = os.path.join(kind(f), "glb", f)
            out.setdefault(dst, os.path.join(src, f))           # godot_v28 primero: gana
    for dp, _dn, fs in os.walk(TEXTURES):
        for f in fs:
            if f.lower().endswith(TEX_EXT):
                p = os.path.join(dp, f)
                out[os.path.join("textures", os.path.relpath(p, TEXTURES))] = p
    return out


def main():
    check = "--check" in sys.argv
    old = {}
    if os.path.exists(MANIFEST):
        for line in open(MANIFEST):
            parts = line.rstrip("\n").split("  ")
            if len(parts) == 3 and len(parts[1]) == 64:
                old[parts[2]] = parts[1]
    rows, copied, same = [], 0, 0
    for dst, src in sorted(plan().items()):
        h = sha(src)
        full = os.path.join(ASSETS, dst)
        if old.get(dst) == h and os.path.exists(full):
            same += 1
        else:
            copied += 1
            if not check:
                os.makedirs(os.path.dirname(full), exist_ok=True)
                shutil.copy2(src, full)
        rows.append((os.path.getsize(src), h, dst, os.path.relpath(src, REPO)))
    stale = sorted(set(old) - {r[2] for r in rows})
    if not check:
        for dst in stale:
            p = os.path.join(ASSETS, dst)
            if os.path.exists(p):
                os.remove(p)
        with open(MANIFEST, "w") as fh:
            fh.write("CONCORDIA - assets del proyecto de Godot (copiados por tools/sync_assets.py; no van a git)\n")
            fh.write("bytes  sha256  destino (en assets/)  <-  origen (en el repositorio)\n\n")
            for size, h, dst, src in rows:
                fh.write(f"{size:>12}  {h}  {dst}  <-  {src}\n")
            fh.write(f"\nTotal: {len(rows)} archivos, {sum(r[0] for r in rows):,} bytes\n")
        with open(os.path.join(ASSETS, "manifest.json"), "w") as fh:
            json.dump({dst: {"sha256": h, "bytes": size, "origen": src} for size, h, dst, src in rows}, fh, indent=0)
    print(json.dumps({"archivos": len(rows), "copiados": copied, "iguales": same, "borrados": stale,
                      "glb": sum(1 for r in rows if r[2].endswith(".glb")),
                      "mb": round(sum(r[0] for r in rows) / 2 ** 20, 1), "solo_comprobar": check}))


if __name__ == "__main__":
    main()
