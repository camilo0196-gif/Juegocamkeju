"""
CONCORDIA - Etapa 28: lista de las puertas de Moradas que siguen tapadas desde CAM_Iso en concordia_v28.blend, con
parcela (casa, conjunto, terraza, numero), causa, casa que tapa y distancia a lo largo del rayo de CAM_Iso desde la
puerta (1.1 m) hasta la superficie que tapa (la camara es ortografica: esa distancia es la que sirve para el aclarado).
Escribe docs/reports/stage28_moradas_residual.json; no modifica el .blend.
"""
import json
import os
import sys

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
CAM_BACK = Vector((0.577, -0.577, 0.577)).normalized()


def main():
    bpy.ops.wm.open_mainfile(filepath=os.path.join(REPO, "blender", "concordia_v28.blend"))
    st = json.load(open(os.path.join(REPO, "docs", "reports", "stage28_ciudad.json")))
    res = st["moradas"]["residual"]
    occ = {}
    for r in res:
        for b in r["blockers"]:
            for part in ("Body", "Roof"):
                o = bpy.data.objects.get(f"{b}_{part}")
                if o is not None:
                    occ[o.name] = o
    rows = []
    for r in res:
        dm = bpy.data.objects[r["door"]]
        house = dm.parent
        mw = dm.matrix_world
        n = (mw.to_3x3() @ Vector((0, 1, 0))).normalized()
        best = None
        for hgt in (0.3, 1.1, 2.0):                      # las 3 alturas de la prueba de puertas
            o = mw.translation + n * 0.35 + Vector((0, 0, hgt))
            for name in [f"{b}_{p}" for b in r["blockers"] for p in ("Body", "Roof")]:
                ob = occ.get(name)
                if ob is None:
                    continue
                inv = ob.matrix_world.inverted()
                hit, loc, _n, _i = ob.ray_cast(inv @ o, (inv.to_3x3() @ CAM_BACK).normalized())
                if hit:
                    d = ((ob.matrix_world @ loc) - o).length
                    if best is None or d < best[0]:
                        best = (d, name)
        rows.append({"door": r["door"], "parcela": house.name, "set": r["set"], "terraza": house.get("terraza"),
                     "house_number": house.get("house_number"), "tipo": house.get("tipo"),
                     "floor": int(r["door"].split("_")[-1]) - 1 if house.get("tipo") == "habitacion" else 0,
                     "cause": r["cause"], "blocked_by": r["blockers"],
                     "ray_distance_to_blocker_m": round(best[0], 2) if best else None,
                     "first_hit": best[1] if best else None})
    out = {"criterion": "rayos desde 0.35 m delante de la puerta a 0.3 / 1.1 / 2.0 m en la direccion de CAM_Iso; "
                        "distancia minima hasta la casa que tapa",
           "dwellings_total": st["moradas"]["dwellings_total"], "residual": len(rows),
           "pct": round(100.0 * len(rows) / 1404, 2), "rows": rows}
    with open(os.path.join(REPO, "docs", "reports", "stage28_moradas_residual.json"), "w") as fh:
        json.dump(out, fh, indent=1, ensure_ascii=False)
    for x in rows:
        print("ROW", x["door"], x["parcela"], x["house_number"], x["cause"], x["blocked_by"], x["ray_distance_to_blocker_m"])


if __name__ == "__main__":
    main()
