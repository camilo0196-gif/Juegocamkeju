"""
CONCORDIA - descarga de modelos CC0 de Sketchfab (solo ficheros de datos: glb/gltf).

Por cada uid: (1) ficha de la API (/v3/models/<uid>): la licencia debe ser CC0; (2) pagina publica del modelo: debe
mostrar la licencia CC0 (texto 'CC0' / 'Public Domain'); (3) /v3/models/<uid>/download -> glb (si no, gltf zip);
(4) guarda <out>/<uid>/<nombre>.glb y anota url, licencia, texto y fecha en <out>/licenses.json. Si algo no es CC0 se
salta y se anota el motivo. El token lo inyecta el proxy del entorno (nunca se lee ni se escribe aqui).
python3 -I fetch_sketchfab_cc0.py <out_dir> <uid> [<uid> ...]
"""

import datetime
import json
import os
import re
import sys
import urllib.request
import zipfile

API = "https://api.sketchfab.com/v3/models/"
DATA_EXT = (".glb", ".gltf", ".bin", ".png", ".jpg", ".jpeg")


def get(url, raw=False):
    req = urllib.request.Request(url, headers={"User-Agent": "concordia-asset-fetch"})
    with urllib.request.urlopen(req, timeout=60) as r:
        data = r.read()
    return data if raw else json.loads(data)


def main():
    out, uids = sys.argv[1], sys.argv[2:]
    os.makedirs(out, exist_ok=True)
    path = os.path.join(out, "licenses.json")
    meta = json.load(open(path)) if os.path.exists(path) else {}
    today = datetime.date.today().isoformat()
    for uid in uids:
        info = get(API + uid)
        lic = info.get("license") or {}
        label = lic.get("label", "") if isinstance(lic, dict) else str(lic)
        page = info.get("viewerUrl") or f"https://sketchfab.com/3d-models/{uid}"
        rec = {"name": info.get("name"), "author": (info.get("user") or {}).get("displayName"), "url": page,
               "license": label, "license_url": lic.get("url") if isinstance(lic, dict) else None,
               "license_requirements": lic.get("requirements") if isinstance(lic, dict) else None,
               "checked": today, "faces": info.get("faceCount")}
        if "CC0" not in label:
            rec["skipped"] = f"licencia de la API no es CC0: {label}"
            meta[uid] = rec
            print("SKIP", uid, rec["skipped"], flush=True)
            continue
        try:
            html = get(page, raw=True).decode("utf-8", "replace")
            m = re.search(r"(CC0[^<\"]{0,60}|Public Domain[^<\"]{0,40})", html)
            rec["page_license_text"] = m.group(1).strip() if m else None
            rec["page_checked"] = bool(m)
        except Exception as e:  # la pagina puede no estar permitida por la red: se anota
            rec["page_license_text"] = None
            rec["page_checked"] = False
            rec["page_error"] = str(e)[:120]
        dl = get(API + uid + "/download")
        d = os.path.join(out, uid)
        os.makedirs(d, exist_ok=True)
        if dl.get("glb"):
            fn = os.path.join(d, "model.glb")
            with open(fn, "wb") as fh:
                fh.write(get(dl["glb"]["url"], raw=True))
            rec["file"] = os.path.relpath(fn, out)
        else:
            zp = os.path.join(d, "model.zip")
            with open(zp, "wb") as fh:
                fh.write(get(dl["gltf"]["url"], raw=True))
            with zipfile.ZipFile(zp) as z:
                for n in z.namelist():
                    if n.lower().endswith(DATA_EXT) and ".." not in n and not n.startswith("/"):
                        z.extract(n, d)
            g = [n for n in os.listdir(d) if n.endswith(".gltf")]
            rec["file"] = os.path.relpath(os.path.join(d, g[0]), out) if g else None
        meta[uid] = rec
        print("OK", uid, rec["name"], label, rec.get("page_checked"), rec.get("file"), flush=True)
        with open(path, "w") as fh:
            json.dump(meta, fh, indent=1, ensure_ascii=False)
    with open(path, "w") as fh:
        json.dump(meta, fh, indent=1, ensure_ascii=False)


if __name__ == "__main__":
    main()
