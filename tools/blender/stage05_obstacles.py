"""
CONCORDIA - etapa 05: raster de obstaculos (vista cenital) de lo que ya existe en la escena.

Lanza rayos verticales en una rejilla de CELL m sobre todo el terreno contra:
  1 = estructuras (PLAZA, STREETS, MORADAS, WALL_LAYOUT; sin -colonly ni marcadores)
  2 = caras de muro del terreno (caras de TRN_City con pendiente > STEEP_DEG)
El planificador de calles y parcelas (stage05_layout.py) no puede ocupar esas celdas.

Uso (bpy): grid = build_raster(); np.savez(...)   |   CLI: python stage05_obstacles.py --out X.npz
"""

import argparse
import os
import sys
from math import cos, radians

import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import concordia_const as C  # noqa: E402

REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
CELL = 0.5
EXTENT = C.TERRAIN_GRID_SIZE / 2.0          # 212
STEEP_DEG = 30.0
STRUCT_COLLECTIONS = ("PLAZA", "STREETS", "MORADAS", "WALL_LAYOUT")
SKIP_SUFFIX = ("-colonly", "-col")


def grid_n():
    return int(round(2 * EXTENT / CELL))


def cell_centers():
    n = grid_n()
    c = -EXTENT + CELL * (np.arange(n) + 0.5)
    return c, n


def _collect(collections_):
    verts, polys = [], []
    dg = bpy.context.evaluated_depsgraph_get()
    seen = set()
    for cname in collections_:
        col = bpy.data.collections.get(cname)
        if col is None:
            continue
        for o in col.all_objects:
            if o.name in seen or o.type != "MESH" or o.name.endswith(SKIP_SUFFIX):
                continue
            seen.add(o.name)
            ev = o.evaluated_get(dg)
            me = ev.to_mesh()
            mw = o.matrix_world
            base = len(verts)
            verts.extend([mw @ v.co for v in me.vertices])
            polys.extend([[base + i for i in p.vertices] for p in me.polygons])
            ev.to_mesh_clear()
        # instancias de coleccion (WALL_LAYOUT usa objetos enlazados, no instancias; por si acaso)
    return verts, polys


def _steep_terrain():
    o = bpy.data.objects["TRN_City"]
    me = o.data
    cmin = cos(radians(STEEP_DEG))
    verts = [v.co.copy() for v in me.vertices]
    polys = [list(p.vertices) for p in me.polygons if p.normal.z < cmin]
    return verts, polys


def _cast(bvh, n, c):
    out = np.zeros((n, n), dtype=bool)
    down = Vector((0.0, 0.0, -1.0))
    for j in range(n):
        y = float(c[j])
        for i in range(n):
            x = float(c[i])
            if x * x + y * y > (EXTENT + 1) ** 2:
                continue
            if bvh.ray_cast(Vector((x, y, 200.0)), down)[0] is not None:
                out[j, i] = True
    return out


def build_raster():
    """Devuelve (codes[n,n] uint8, info). Indices [j, i] = (y, x)."""
    c, n = cell_centers()
    v, p = _collect(STRUCT_COLLECTIONS)
    s = _cast(BVHTree.FromPolygons(v, p), n, c) if p else np.zeros((n, n), bool)
    v2, p2 = _steep_terrain()
    f = _cast(BVHTree.FromPolygons(v2, p2), n, c) if p2 else np.zeros((n, n), bool)
    codes = np.zeros((n, n), dtype=np.uint8)
    codes[f] = 2
    codes[s] = 1
    info = {"cell_m": CELL, "extent_m": EXTENT, "n": n, "struct_cells": int(s.sum()), "steep_cells": int(f.sum()),
            "struct_polys": len(p), "steep_polys": len(p2)}
    return codes, info


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    ap = argparse.ArgumentParser()
    ap.add_argument("--blend", default=os.path.join(REPO, "blender", f"{C.BLEND_BASENAME}_v04.blend"))
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    bpy.ops.wm.open_mainfile(filepath=a.blend)
    codes, info = build_raster()
    np.savez_compressed(a.out, codes=codes)
    print(info)


if __name__ == "__main__":
    main()
