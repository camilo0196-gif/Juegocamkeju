"""
CONCORDIA - inventario de las exportaciones .glb (sin Blender ni Godot: lee el JSON del glTF).
Por archivo: tamano, fecha, nodos, mallas, triangulos, materiales, imagenes, sufijos de importacion de Godot
(-colonly, -convcolonly, -navmesh, -occonly...), LODs (_LOD0/_LOD1/_LOD2), claves de extras y prefijos de nodos.
python3 tools/inventario_glb.py [carpeta] > docs/reports/inventario_glb.md
"""

import datetime
import json
import os
import re
import struct
import sys
from collections import Counter

SUFFIXES = ("-colonly", "-convcolonly", "-col", "-convcol", "-navmesh", "-occonly", "-occ", "-noimp", "-rigid",
            "-loop", "-cycle")


def read_gltf(path):
    with open(path, "rb") as fh:
        data = fh.read(20)
        _magic, _ver, _ln = struct.unpack("<III", data[:12])
        cl, _ct = struct.unpack("<II", data[12:20])
        js = json.loads(fh.read(cl))
    return js


def tri_count(js, mesh):
    n = 0
    for p in mesh.get("primitives", []):
        mode = p.get("mode", 4)
        if mode != 4:
            continue
        if "indices" in p:
            n += js["accessors"][p["indices"]]["count"] // 3
        else:
            n += js["accessors"][p["attributes"]["POSITION"]]["count"] // 3
    return n


def info(path):
    js = read_gltf(path)
    nodes = js.get("nodes", [])
    names = [n.get("name", "") for n in nodes]
    suf = Counter()
    for nm in names:
        for s in SUFFIXES:
            if nm.endswith(s) or (s + ".") in nm:
                suf[s] += 1
                break
    lods = Counter(m.group(1) for nm in names for m in [re.search(r"_(LOD\d)\b", nm)] if m)
    extras = Counter(k for n in nodes for k in (n.get("extras") or {}).keys())
    prefixes = Counter(nm.split("_")[0] if "_" in nm else nm for nm in names)
    # triangulos por instancia de nodo (una malla usada por varios nodos cuenta varias veces)
    tris_inst = sum(tri_count(js, js["meshes"][n["mesh"]]) for n in nodes if "mesh" in n)
    tris_unique = sum(tri_count(js, m) for m in js.get("meshes", []))
    scene = js["scenes"][js.get("scene", 0)]
    roots = [nodes[i].get("name") for i in scene.get("nodes", [])]
    st = os.stat(path)
    return {
        "archivo": os.path.basename(path), "kb": round(st.st_size / 1024, 1),
        "fecha": datetime.datetime.fromtimestamp(st.st_mtime).strftime("%Y-%m-%d %H:%M"),
        "nodos": len(nodes), "mallas": len(js.get("meshes", [])), "tris_mallas_unicas": tris_unique,
        "tris_instancias": tris_inst, "materiales": len(js.get("materials", [])), "imagenes": len(js.get("images", [])),
        "skins": len(js.get("skins", [])), "animaciones": [a.get("name") for a in js.get("animations", [])],
        "sufijos": dict(suf), "lods": dict(lods), "extras": dict(extras),
        "raices": roots[:12] + (["..."] if len(roots) > 12 else []), "n_raices": len(roots),
        "prefijos": dict(prefixes.most_common(14)),
    }


def main():
    folder = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), "..", "export", "godot")
    rows = [info(os.path.join(folder, f)) for f in sorted(os.listdir(folder)) if f.endswith(".glb")]
    if "--json" in sys.argv:
        print(json.dumps(rows, indent=1, ensure_ascii=False))
        return
    print("| archivo | KB | fecha | nodos | mallas | tris (unicas / instancias) | mat | img | sufijos | LODs | extras |")
    print("|---|---|---|---|---|---|---|---|---|---|---|")
    for r in rows:
        print(f"| {r['archivo']} | {r['kb']} | {r['fecha']} | {r['nodos']} | {r['mallas']} | "
              f"{r['tris_mallas_unicas']:,} / {r['tris_instancias']:,} | {r['materiales']} | {r['imagenes']} | "
              f"{', '.join(f'{k} {v}' for k, v in r['sufijos'].items()) or '-'} | "
              f"{', '.join(f'{k} {v}' for k, v in sorted(r['lods'].items())) or '-'} | "
              f"{', '.join(sorted(r['extras'])) or '-'} |")
    for r in rows:
        print(f"\n### {r['archivo']}\nraices ({r['n_raices']}): {', '.join(map(str, r['raices']))}\n"
              f"prefijos: {r['prefijos']}" + (f"\nanimaciones: {r['animaciones']}" if r['animaciones'] else ""))


if __name__ == "__main__":
    main()
