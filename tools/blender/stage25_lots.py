"""
CONCORDIA - Etapa 25: busqueda de suelo libre para parcelas nuevas (Cazadores, casas de las Razas).

Rejilla de 1 m sobre un sector (angulo central, semiapertura, r min-max):
  publico   = sobre la malla de navegacion (calles, plazas, escalinatas transitables)
  ocupado   = bajo cualquier objeto (edificios, props, puentes, escaleras, cauce, muros, pretiles)
  libre     = ni publico ni ocupado
Una parcela (rectangulo w x d con margen) vale si todas sus celdas son libres, la diferencia de cota del suelo es
<= max_slope_m y el frente (+Y local, donde va la puerta) da a celdas publicas (calle) a <= 3 m.
"""

import math

import bpy
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

SKIP_SUFFIX = ("-colonly", "_LOD1", "_LOD2", "-navmesh", "-occonly", "_InteriorVolume")
SKIP_COLS = ("WALL_KIT", "WALL_KIT_LODS", "BLD_KIT", "BLD_KIT_SHEET", "BLD_KIT_TEST", "BLD_PROPS_LIBRARY",
             "MATERIAL_LIBRARY", "LEGACY_PLACEHOLDERS", "GODOT_CITY_LOD0", "GODOT_CITY_LOD1", "GODOT_CITY_LOD2",
             "GODOT_CITY_COL", "GODOT_EXT_LOD0", "GODOT_EXT_LOD1", "GODOT_EXT_LOD2", "GODOT_EXT_CLIFF",
             "GODOT_NAVMESH", "GODOT_OCCLUDERS", "GODOT_STRUCT_COL", "TERRAIN", "EXTERIOR", "STREETS_AXES")


def _bvh(objs):
    verts, faces = [], []
    for o in objs:
        me = o.data
        mw = o.matrix_world
        b = len(verts)
        verts += [mw @ v.co for v in me.vertices]
        faces += [[b + i for i in p.vertices] for p in me.polygons]
    return BVHTree.FromPolygons(verts, faces, epsilon=1e-6)


class Grid:
    def __init__(self, phi_deg, half_deg, r0, r1, cell=1.0, extra_occupied=()):
        self.phi, self.half, self.r0, self.r1, self.cell = math.radians(phi_deg), math.radians(half_deg), r0, r1, cell
        skip = set()
        for cn in SKIP_COLS:
            c = bpy.data.collections.get(cn)
            if c:
                skip |= {o.name for o in c.all_objects}
        objs = [o for o in bpy.data.objects if o.type == "MESH" and o.name not in skip and not o.name.endswith(SKIP_SUFFIX)
                and not o.hide_render and not o.name.startswith("TRN_City")]
        self.obj_bvh = _bvh(objs + list(extra_occupied))
        self.nav_bvh = _bvh([o for o in bpy.data.objects if o.name.endswith("-navmesh")])
        self.ground_bvh = BVHTree.FromObject(bpy.data.objects["TRN_City"], bpy.context.evaluated_depsgraph_get())
        self.cache = {}

    def in_sector(self, x, y):
        r = math.hypot(x, y)
        if not (self.r0 <= r <= self.r1):
            return False
        d = (math.atan2(y, x) - self.phi + math.pi) % (2 * math.pi) - math.pi
        return abs(d) <= self.half

    def ground(self, x, y):
        h = self.ground_bvh.ray_cast(Vector((x, y, 200.0)), Vector((0, 0, -1)))
        return h[0].z if h[0] else None

    def state(self, x, y):
        """'out' | 'public' | 'occupied' | 'free', cota."""
        k = (round(x / self.cell), round(y / self.cell))
        if k in self.cache:
            return self.cache[k]
        x, y = k[0] * self.cell, k[1] * self.cell
        z = self.ground(x, y)
        if z is None or not self.in_sector(x, y):
            res = ("out", z)
        else:
            loc, _n, _i, dist = self.nav_bvh.find_nearest(Vector((x, y, z)), 1.6)
            if loc is not None and (loc.xy - Vector((x, y))).length <= 0.6 and abs(loc.z - z) <= 1.5:
                res = ("public", z)
            else:
                hit = self.obj_bvh.ray_cast(Vector((x, y, z + 40.0)), Vector((0, 0, -1)), 60.0)
                res = ("occupied", z) if hit[0] is not None and hit[0].z > z - 0.6 else ("free", z)
        self.cache[k] = res
        return res

    def rect_ok(self, c, theta, w, d, margin=0.5, max_slope=0.6, front_need=0.5):
        rm = Matrix.Rotation(theta, 2)
        zs = []
        hw, hd = w / 2 + margin, d / 2 + margin
        nx, ny = int(math.ceil(2 * hw)), int(math.ceil(2 * hd))
        for i in range(nx + 1):
            for j in range(ny + 1):
                lp = Vector((-hw + 2 * hw * i / nx, -hd + 2 * hd * j / ny))
                p = c + rm @ lp
                s, z = self.state(p.x, p.y)
                if s != "free":
                    return None
                zs.append(z)
        if max(zs) - min(zs) > max_slope:
            return None
        # frente a la calle
        pub = tot = 0
        for i in range(nx + 1):
            for off in (1.5, 2.5, 3.5):
                lp = Vector((-w / 2 + w * i / nx, d / 2 + margin + off))
                p = c + rm @ lp
                tot += 1
                if self.state(p.x, p.y)[0] == "public":
                    pub += 1
                    break
        if pub < front_need * (nx + 1):
            return None
        return {"center": (c.x, c.y), "theta": theta, "z": min(zs), "slope": round(max(zs) - min(zs), 2)}

    def search(self, w, d, ref, step=2.0, thetas=None, max_n=1, taken=(), min_gap=0.8, **kw):
        """Parcelas validas ordenadas por distancia a ref; evita solapar 'taken' (lista de (centro, theta, w, d))."""
        out = []
        cands = []
        R = self.r1
        y0 = -R
        while y0 <= R:
            x0 = -R
            while x0 <= R:
                if self.in_sector(x0, y0):
                    cands.append(Vector((x0, y0)))
                x0 += step
            y0 += step
        cands.sort(key=lambda p: (p - Vector(ref)).length)
        for c in cands:
            if any(_overlap(c, t, w, d, min_gap) for t in list(taken) + [(Vector(o["center"]), o["theta"], o["w"], o["d"])
                                                                        for o in out]):
                continue
            radial = math.atan2(c.y, c.x)
            for th in (thetas if thetas is not None else (radial + math.pi / 2, radial - math.pi / 2, radial, radial + math.pi)):
                r = self.rect_ok(c, th, w, d, **kw)
                if r:
                    r.update(w=w, d=d)
                    out.append(r)
                    break
            if len(out) >= max_n:
                break
        return out


def _overlap(c, t, w, d, gap):
    (c2, th2, w2, d2) = t
    return (Vector(c) - Vector(c2)).length < (math.hypot(w, d) + math.hypot(w2, d2)) / 2 + gap - 0.0 and \
        _sat(Vector(c), 0.0, w + gap, d + gap, Vector(c2), th2, w2, d2)


def _sat(c1, th1, w1, d1, c2, th2, w2, d2):
    """Solape de rectangulos orientados (teorema del eje separador); th1 se ignora (circulo envolvente ya filtra)."""
    def corners(c, th, w, d):
        rm = Matrix.Rotation(th, 2)
        return [c + rm @ Vector((sx * w / 2, sy * d / 2)) for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    a = corners(c1, th2, w1, d1)
    b = corners(c2, th2, w2, d2)
    for poly in (a, b):
        for i in range(4):
            e = poly[(i + 1) % 4] - poly[i]
            n = Vector((-e.y, e.x))
            pa = [n.dot(p) for p in a]
            pb = [n.dot(p) for p in b]
            if max(pa) < min(pb) or max(pb) < min(pa):
                return False
    return True
