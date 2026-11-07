"""
CONCORDIA - Etapa 25: medicion final de la visibilidad del Faro sobre concordia_v25.blend (tras el pipeline de Godot).
Escribe docs/reports/stage25_faro.json: % por tipo de calle y cada edificio que aun tapa (calles, altura actual,
altura que dejaria libres sus visuales y si es de servicio o decorativo).
"""

import json
import os
import sys

import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import concordia_const as C  # noqa: E402
import stage25_faro as F  # noqa: E402

REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
BLEND = os.path.join(REPO, "blender", f"{C.BLEND_BASENAME}_v25.blend")
OUT = os.path.join(REPO, "docs", "reports", "stage25_faro.json")
# edificios de servicio (criterio del usuario): Banco, Tesoreria, gremios, salones, Casas de Raza; mas los que dan
# servicio de juego (Posada, Subasta, talleres, casas de oficios con interior)
SERVICE = ("Banco", "Tesoreria", "Gremio_", "SalonClase", "CasaRaza", "Posada", "GranSubasta", "Taller_", "Casa",
           "CrisolPiedras", "Joyeria", "Alquimia", "Herbolarios", "Curtiduria", "Sastreria")
DECOR = ("RAZ_B", "Morada_", "OFI_Casa", "CLA_Casa", "MER_Casa", "PuestoProvisiones")


def kind_of(name):
    if name.startswith(DECOR):
        return "decorativo"
    return "servicio" if name.startswith(SERVICE) else "decorativo"


def height(r):
    from mathutils import Vector
    inv = r.matrix_world.inverted()
    hs = [(inv @ (o.matrix_world @ Vector(c))).z for o in [r] + list(r.children_recursive)
          if o.type == "MESH" and not o.name.endswith(F.SKIP_SUFFIX) for c in o.bound_box]
    return round(max(hs), 2) if hs else None


def main():
    bpy.ops.wm.open_mainfile(filepath=BLEND)
    for o in bpy.data.objects:
        if o.name.endswith(("_LOD1", "_LOD2")):
            o.hide_render = True
    res, bl = F.measure()
    rows = []
    for n, b in sorted(bl.items(), key=lambda kv: -kv[1]["points"]):
        r = bpy.data.objects.get(n)
        if r is None:
            continue
        rows.append({"name": n, "kind": kind_of(n), "points": b["points"], "streets": dict(b["streets"]),
                     "h_now": height(r), "h_req": F.required_height(r, b["rays"]), "floors": r.get("floors")})
    out = {"visibility": res, "blockers": rows,
           "criterion": "1.7 m cada 10 m; >= 2 de 6 visuales a la galeria superior del Faro (ultimos 6 m + cristal)"}
    with open(OUT, "w") as fh:
        json.dump(out, fh, indent=1, ensure_ascii=False, default=str)
    for k, v in res.items():
        print("FARO", k, v["points"], v["visible"], v["pct"], v["blocked_by_category"], flush=True)
    print("BLOCKERS", len(rows), sum(1 for r_ in rows if r_["kind"] == "servicio"), flush=True)


if __name__ == "__main__":
    main()
