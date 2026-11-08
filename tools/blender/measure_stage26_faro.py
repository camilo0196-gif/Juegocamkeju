"""
CONCORDIA - Etapa 26: medicion del Faro con el criterio nuevo (stage26_faro.py) sobre concordia_v26.blend.
Escribe docs/reports/stage26_faro.json. No modifica el .blend.
"""

import json
import os
import sys

import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import concordia_const as C  # noqa: E402
import stage26_faro as F  # noqa: E402

REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
BLEND = os.path.join(REPO, "blender", f"{C.BLEND_BASENAME}_v26.blend")
OUT = os.path.join(REPO, "docs", "reports", "stage26_faro.json")
GOAL = {"avenida": 100.0, "diagonal": 100.0, "anillo": 100.0, "callejon": 90.0}


def main():
    bpy.ops.wm.open_mainfile(filepath=BLEND)
    for o in bpy.data.objects:
        if o.name.endswith(("_LOD1", "_LOD2")):
            o.hide_render = True
    res, sole, pipe_pts = F.measure()
    rows = F.proposal(sole, res, GOAL)
    below = {k: {"pct": v["pct"], "goal": GOAL[k]} for k, v in res.items() if v["pct"] < GOAL[k]}
    out = {"criterion": "ojo a 1.7 m cada 10 m; 11 rayos: 10 al eje del haz (z 60-120 m) y 1 al centro del cristal; "
                        "con Faro si >= 1 rayo libre",
           "beam_targets_z": [round(z, 2) for z in F.BEAM_Z], "goal": GOAL,
           "visibility": {k: {kk: vv for kk, vv in v.items() if kk != "blocked_points"} for k, v in res.items()},
           "blocked_points": {k: v["blocked_points"] for k, v in res.items()},
           "below_goal": below, "points_lost_to_pipes": pipe_pts,
           "proposal_decor_lowering": [r for r in rows if r["kind"] == "decorativo"],
           "service_sole_blockers_not_touched": [r for r in rows if r["kind"] == "servicio"]}
    with open(OUT, "w") as fh:
        json.dump(out, fh, indent=1, ensure_ascii=False, default=str)
    for k, v in res.items():
        print("FARO26", k, v["points"], v["with_faro"], v["pct"], "cristal", v["crystal_direct"], v["crystal_direct_pct"],
              "sin tubos", v["pct_without_pipes"], flush=True)
    print("FARO26 below", below, "pipes", len(pipe_pts), "proposal", len(out["proposal_decor_lowering"]), flush=True)


if __name__ == "__main__":
    main()
