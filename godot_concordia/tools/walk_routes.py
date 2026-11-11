"""
CONCORDIA - rutas de la prueba de caminata (G3). Genera tools/walk_routes.json, que lee tools/walk_test.gd.

Fuentes:
  ../docs/reports/stage05_layout.json   calles (avenidas, rondas r100/r150, diagonales, callejones y callejones con
                                        escalera) y plazas, en coordenadas de Blender (x este, y norte)
  debug/out/markers_meta.json           marcadores importados (tools/import_report.gd), en coordenadas de Godot:
                                        escalinatas, puentes, arcos, escaleras, puertas de la muralla, moradas

Salida: lista de rutas {nombre, tipo, puntos [[x, z] Godot]}; la altura la pone walk_test.gd ajustando cada punto a
la malla de navegacion. Las calles se cortan en tramos de ~12 m; las estructuras se cruzan de un lado al otro.

python3 godot_concordia/tools/walk_routes.py
"""

import json
import math
import os

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.path.abspath(os.path.join(HERE, ".."))
REPO = os.path.abspath(os.path.join(PROJECT, ".."))
STEP = 12.0


def g(p):
    """Blender (x, y) -> Godot (x, z)"""
    return [round(p[0], 2), round(-p[1], 2)]


def resample(pts, step):
    out = [pts[0]]
    acc = 0.0
    for a, b in zip(pts, pts[1:]):
        seg = math.dist(a, b)
        t = step - acc
        while t <= seg:
            out.append([a[0] + (b[0] - a[0]) * t / seg, a[1] + (b[1] - a[1]) * t / seg])
            t += step
        acc = (acc + seg) % step
    if math.dist(out[-1], pts[-1]) > 2.0:
        out.append(pts[-1])
    return out


def cross(pos, fwd, half):
    return [[round(pos[0] - fwd[0] * half, 2), round(pos[2] - fwd[2] * half, 2)],
            [round(pos[0] + fwd[0] * half, 2), round(pos[2] + fwd[2] * half, 2)]]


def clamp_r(q, rmax):
    r = math.hypot(q[0], q[1])
    return q if r <= rmax else [round(q[0] * rmax / r, 2), round(q[1] * rmax / r, 2)]


def main():
    lay = json.load(open(os.path.join(REPO, "docs", "reports", "stage05_layout.json")))
    mk = json.load(open(os.path.join(PROJECT, "debug", "out", "markers_meta.json")))["marcadores"]
    routes = []
    # calles
    kinds = {"avenue": "avenida", "ring": "ronda", "diagonal": "diagonal", "alley": "callejon"}
    for r in lay["roads"]:
        k = kinds.get(r["type"], r["type"])
        if "CallejonEscalera" in r["name"]:
            k = "callejon_escalera"
        routes.append({"nombre": r["name"], "tipo": k, "puntos": [g(p) for p in resample(r["pts"], STEP)]})
    # plazas: dos cruces (O-E y S-N) entre puntos del contorno al 85 %
    for p in lay["plazas"]:
        if p["type"] == "stair_link":
            continue
        poly = p["poly"]
        cx = sum(q[0] for q in poly) / len(poly)
        cy = sum(q[1] for q in poly) / len(poly)
        for ang in (0.0, 90.0):
            a = math.radians(ang)
            d = (math.cos(a), math.sin(a))
            ends = []
            for sgn in (-1, 1):
                best = max(poly, key=lambda q: sgn * ((q[0] - cx) * d[0] + (q[1] - cy) * d[1]))
                ends.append([cx + (best[0] - cx) * 0.85, cy + (best[1] - cy) * 0.85])
            pts = [ends[0], ends[1]]          # de borde a borde: el camino rodea fuentes, pozos y puestos
            routes.append({"nombre": "%s_%s" % (p["name"], "OE" if ang == 0 else "SN"), "tipo": "plaza",
                           "puntos": [g(q) for q in pts]})
    # estructuras (marcadores en coordenadas de Godot: pos [x, y, z], frente = sentido de paso)
    for name, m in sorted(mk.items()):
        meta = m.get("meta", {})
        pos, fwd = m["pos"], m["frente"]
        kit = str(meta.get("kit_piece", ""))
        if name.startswith("MARKER_Escalinata_"):
            routes.append({"nombre": name, "tipo": "escalinata", "puntos": cross(pos, fwd, 3.5 + 2.5)})
        elif name.startswith("MARKER_Bridge_") and kit.startswith("BRIDGE"):
            routes.append({"nombre": name, "tipo": "puente", "puntos": cross(pos, fwd, float(meta["length_m"]) / 2 + 3)})
        elif name.startswith("MARKER_Bridge_") and kit.startswith("ARCH"):
            # el paso alto une dos casas; por la calle se pasa por debajo, en perpendicular
            right = [-fwd[2], 0.0, fwd[0]]
            routes.append({"nombre": name, "tipo": "arco", "puntos": cross(pos, right, 9.0)})
        elif name.startswith("MARKER_Stairs_Monumental"):
            routes.append({"nombre": name, "tipo": "escalera_monumental", "puntos": cross(pos, fwd, 13.0)})
        elif name.startswith("MARKER_Stairs_Lateral"):
            n = float(meta.get("risers", 7))
            # la cara interior de la muralla esta a r 196,6: el extremo de fuera se recorta a r 194
            routes.append({"nombre": name, "tipo": "escalera_lateral", "puntos": [clamp_r(q, 194.0) for q in cross(pos, fwd, n * 0.30 + 2.5)]})
        elif name.startswith("MARKER_Stairs_Terrace"):
            routes.append({"nombre": name, "tipo": "escalera_terraza", "puntos": cross(pos, fwd, 4.5)})
        elif name.startswith("MARKER_Gate_"):
            # puertas selladas (decision del usuario): solo la aproximacion por dentro, de r 180 a r 192
            inner = [[round(pos[0] - fwd[0] * 20.0, 2), round(pos[2] - fwd[2] * 20.0, 2)],
                     [round(pos[0] - fwd[0] * 8.0, 2), round(pos[2] - fwd[2] * 8.0, 2)]]
            routes.append({"nombre": name, "tipo": "puerta_muralla", "puntos": inner})
    # moradas: delante de cada casa (parcela 10 m de fondo -> calle a ~7 m del centro), tramos de 4 en 4 casas
    for conj in ("NE", "NO", "SE", "SO"):
        houses = sorted(k for k in mk if k.startswith("MARKER_Morada_%s_" % conj))
        fronts = []
        for k in houses:
            p, f = mk[k]["pos"], mk[k]["frente"]
            fronts.append([round(p[0] + f[0] * 7.0, 2), round(p[2] + f[2] * 7.0, 2)])
        for i in range(0, len(fronts) - 4, 4):
            routes.append({"nombre": "Moradas_%s_%03d_%03d" % (conj, i + 1, i + 5), "tipo": "morada",
                           "puntos": [fronts[i], fronts[i + 4]]})
    out = os.path.join(HERE, "walk_routes.json")
    json.dump({"fuente": ["docs/reports/stage05_layout.json", "debug/out/markers_meta.json"], "paso_m": STEP,
               "rutas": routes}, open(out, "w"), indent=1)
    from collections import Counter
    c = Counter(r["tipo"] for r in routes)
    tramos = sum(len(r["puntos"]) - 1 for r in routes)
    print(json.dumps({"rutas": len(routes), "tramos": tramos, "por_tipo": c}))


if __name__ == "__main__":
    main()
