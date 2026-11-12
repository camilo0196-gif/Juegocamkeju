"""
CONCORDIA - utilidades para los .glb exportados (sin bpy).

strip_embedded_images(path): con export_keep_originals el exportador de Blender escribe en cada imagen la ruta
original (uri) Y una copia incrustada (bufferView); Godot avisa ("Invalid image definition in glTF file using both
'uri' and 'bufferView'. 'uri' will take precedence") y el archivo pesa mas. Se quita la copia incrustada de las
imagenes que tienen uri y se reescribe el binario sin esos trozos (los bufferView restantes se renumeran).
"""

import json
import struct


def _pad(b, ch=b"\x00"):
    return b + ch * ((4 - len(b) % 4) % 4)


def strip_embedded_images(path):
    data = open(path, "rb").read()
    magic, ver, _length = struct.unpack("<III", data[:12])
    if magic != 0x46546C67:
        raise ValueError(f"{path}: no es GLB")
    jl, _jt = struct.unpack("<II", data[12:20])
    js = json.loads(data[20:20 + jl])
    rest = data[20 + jl:]
    binc = b""
    if len(rest) >= 8:
        bl, _bt = struct.unpack("<II", rest[:8])
        binc = rest[8:8 + bl]
    drop = set()
    for im in js.get("images", []):
        if "uri" in im and "bufferView" in im:
            drop.add(im.pop("bufferView"))
    if not drop:
        return 0
    used = set()
    for k in ("accessors", "images"):
        for e in js.get(k, []):
            if "bufferView" in e:
                used.add(e["bufferView"])
    for e in js.get("accessors", []):
        sp = e.get("sparse")
        if sp:
            used.add(sp["indices"]["bufferView"])
            used.add(sp["values"]["bufferView"])
    views = js.get("bufferViews", [])
    keep = [i for i in range(len(views)) if i in used or i not in drop]
    remap = {old: new for new, old in enumerate(keep)}
    newbin = b""
    newviews = []
    for old in keep:
        v = dict(views[old])
        if v.get("buffer", 0) == 0:
            chunk = binc[v.get("byteOffset", 0):v.get("byteOffset", 0) + v["byteLength"]]
            newbin = _pad(newbin)
            v["byteOffset"] = len(newbin)
            newbin += chunk
        newviews.append(v)
    js["bufferViews"] = newviews
    for k in ("accessors", "images"):
        for e in js.get(k, []):
            if "bufferView" in e:
                e["bufferView"] = remap[e["bufferView"]]
    for e in js.get("accessors", []):
        sp = e.get("sparse")
        if sp:
            sp["indices"]["bufferView"] = remap[sp["indices"]["bufferView"]]
            sp["values"]["bufferView"] = remap[sp["values"]["bufferView"]]
    newbin = _pad(newbin)
    if js.get("buffers"):
        js["buffers"][0]["byteLength"] = len(newbin)
    jb = _pad(json.dumps(js, separators=(",", ":")).encode("utf-8"), b" ")
    out = struct.pack("<III", 0x46546C67, ver, 12 + 8 + len(jb) + 8 + len(newbin))
    out += struct.pack("<II", len(jb), 0x4E4F534A) + jb + struct.pack("<II", len(newbin), 0x004E4942) + newbin
    open(path, "wb").write(out)
    return len(drop)
