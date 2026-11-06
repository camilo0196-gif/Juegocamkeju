"""
CONCORDIA - etapa 12: kit modular de edificios (generadores parametricos en bmesh).

Convencion de modulo de muro: plano X-Z, x en [-w/2, w/2], z en [0, h], grosor en Y centrado en 0 con la cara
EXTERIOR en +Y (+t/2). Grilla 1 m, modulo 3 m, piso 3.2 m, zocalo 0.6 m.
Referencias: Rothenburg ob der Tauber / Cesky Krumlov (entramado, teja, balcones, letreros), Grand-Place de Bruselas
(gremios altos, hastial a la calle), Toledo (muros de piedra y arcos).

Todo generador escribe en un MeshBuilder (bmesh + lista de materiales por nombre); 'detail' (0, 1, 2) quita piezas
pequenas para LOD1 / LOD2.
"""

import math
import random

import bmesh
from mathutils import Matrix, Vector

FLOOR_H = 3.2
PLINTH_H = 0.6
MODULE_W = 3.0
WALL_T = 0.45
EAVE = 0.4
ROOF_PITCH = 40.0
TILE_COURSE = 0.42           # paso de las hiladas de teja sobre la pendiente
TILE_SEG = 3.0               # largo de cada tramo de hilada (se puede subir en edificios grandes para el presupuesto)

M_STONE = "MAT_Limestone_Worn"
M_WOOD = "MAT_Wood_Dark"
M_ROOF = "MAT_Roof_Tile_Ocher"
M_ROOF_B = "MAT_Roof_Tile_Ocher_B"      # mismo albedo, otro tono (baseColorFactor)
M_IRON = "MAT_Iron_Black"
M_REPAIR = "MAT_Stone_Repair"
M_GRAY = "MAT_Wall_Gray"
M_COBBLE = "MAT_Cobble_Concordia"
M_SHARD = "MAT_Shard_Blue"
M_WARM = "MAT_Window_Warm"              # luz natural calida, emision 1.0 (no magica)
M_CLOTH = ("MAT_Cloth_Patch_A", "MAT_Cloth_Patch_B", "MAT_Cloth_Patch_C")


class MB:
    """Constructor de malla: bmesh + materiales por nombre + matriz de transformacion actual."""

    def __init__(self):
        self.bm = bmesh.new()
        self.mats = []
        self.M = Matrix.Identity(4)
        self.stack = []

    def mi(self, name):
        if name not in self.mats:
            self.mats.append(name)
        return self.mats.index(name)

    def push(self, m):
        self.stack.append(self.M.copy())
        self.M = self.M @ m

    def pop(self):
        self.M = self.stack.pop()

    def v(self, co):
        return self.bm.verts.new(self.M @ Vector(co))

    def face(self, cos, mat, nrm=None):
        """Cara; con nrm (vector local) se orienta para que su normal apunte hacia nrm."""
        vs = [self.v(c) for c in cos]
        try:
            f = self.bm.faces.new(vs)
        except ValueError:
            return None
        f.material_index = self.mi(mat)
        if nrm is not None:
            f.normal_update()
            if f.normal.dot(self.M.to_3x3() @ Vector(nrm)) < 0:
                f.normal_flip()
        return f

    def rod(self, p0, p1, r, mat, caps=False):
        """Varilla de seccion cuadrada entre dos puntos (tirantes, brazos, barandillas)."""
        a, b = Vector(p0), Vector(p1)
        d = b - a
        L = d.length
        q = d.normalized().to_track_quat("Z", "Y")
        self.push(Matrix.Translation(a) @ q.to_matrix().to_4x4())
        self.box((-r, -r, 0), (r, r, L), mat, skip=() if caps else ("z-", "z+"))
        self.pop()

    def box(self, lo, hi, mat, skip=()):
        """Caja alineada (en el espacio actual). skip: caras omitidas ('x-','x+','y-','y+','z-','z+')."""
        x0, y0, z0 = lo
        x1, y1, z1 = hi
        P = {k: (x, y, z) for k, (x, y, z) in {
            0: (x0, y0, z0), 1: (x1, y0, z0), 2: (x1, y1, z0), 3: (x0, y1, z0),
            4: (x0, y0, z1), 5: (x1, y0, z1), 6: (x1, y1, z1), 7: (x0, y1, z1)}.items()}
        faces = {"z-": (0, 3, 2, 1), "z+": (4, 5, 6, 7), "y-": (0, 1, 5, 4), "y+": (2, 3, 7, 6),
                 "x-": (3, 0, 4, 7), "x+": (1, 2, 6, 5)}
        for k, idx in faces.items():
            if k not in skip:
                self.face([P[i] for i in idx], mat)

    def obox(self, center, size, rot_y=0.0, rot_z=0.0, mat=M_WOOD, skip=()):
        """Caja orientada: centro, tamano, giro en Y (diagonales en fachada) y Z."""
        m = Matrix.Translation(center) @ Matrix.Rotation(rot_z, 4, "Z") @ Matrix.Rotation(rot_y, 4, "Y")
        self.push(m)
        sx, sy, sz = size
        self.box((-sx / 2, -sy / 2, -sz / 2), (sx / 2, sy / 2, sz / 2), mat, skip)
        self.pop()

    def prism(self, poly2d, y0, y1, mat, cap_mat=None):
        """Extruye un poligono del plano X-Z entre y0 e y1 (perfil de escalera, hastial...)."""
        n = len(poly2d)
        a = [(x, y0, z) for x, z in poly2d]
        b = [(x, y1, z) for x, z in poly2d]
        self.ngon_fill(a, cap_mat or mat, flip=True)
        self.ngon_fill(b, cap_mat or mat)
        for i in range(n):
            j = (i + 1) % n
            self.face([a[i], a[j], b[j], b[i]], mat)

    def ngon_fill(self, cos, mat, flip=False):
        if flip:
            cos = cos[::-1]
        vs = [self.v(c) for c in cos]
        try:
            f = self.bm.faces.new(vs)
        except ValueError:
            return
        f.material_index = self.mi(mat)
        if len(vs) > 4:
            bmesh.ops.triangulate(self.bm, faces=[f])

    def cylinder(self, r, z0, z1, n, mat, r1=None, caps=True, center=(0, 0)):
        r1 = r if r1 is None else r1
        cx, cy = center
        lo = [(cx + r * math.cos(2 * math.pi * i / n), cy + r * math.sin(2 * math.pi * i / n), z0) for i in range(n)]
        hi = [(cx + r1 * math.cos(2 * math.pi * i / n), cy + r1 * math.sin(2 * math.pi * i / n), z1) for i in range(n)]
        for i in range(n):
            j = (i + 1) % n
            self.face([lo[i], lo[j], hi[j], hi[i]], mat)
        if caps:
            self.ngon_fill(hi, mat)
            self.ngon_fill(lo, mat, flip=True)

    def slab_holes(self, outer, holes, y0, y1, mat, reveal_mat=None):
        """Placa del plano X-Z con contorno 'outer' y huecos 'holes' (poligonos 2D), entre y0 (dentro) e y1 (fuera)."""
        for yy, flip in ((y1, False), (y0, True)):
            vs_all, es = [], []
            for poly in [outer] + holes:
                vs = [self.bm.verts.new(self.M @ Vector((x, yy, z))) for x, z in poly]
                es += [self.bm.edges.new((vs[i], vs[(i + 1) % len(vs)])) for i in range(len(vs))]
                vs_all += vs
            r = bmesh.ops.triangle_fill(self.bm, use_beauty=True, use_dissolve=False, edges=es)
            fs = [g for g in r["geom"] if isinstance(g, bmesh.types.BMFace)]
            for f in fs:
                f.material_index = self.mi(mat)
            # orientar: cara exterior hacia +Y local
            nrm_target = (self.M.to_3x3() @ Vector((0, 1 if not flip else -1, 0))).normalized()
            for f in fs:
                f.normal_update()
                if f.normal.dot(nrm_target) < 0:
                    f.normal_flip()
        for poly in [outer]:
            n = len(poly)
            for i in range(n):
                j = (i + 1) % n
                (xa, za), (xb, zb) = poly[i], poly[j]
                self.face([(xa, y1, za), (xa, y0, za), (xb, y0, zb), (xb, y1, zb)], mat)
        for poly in holes:
            n = len(poly)
            for i in range(n):
                j = (i + 1) % n
                (xa, za), (xb, zb) = poly[i], poly[j]
                self.face([(xa, y0, za), (xa, y1, za), (xb, y1, zb), (xb, y0, zb)], reveal_mat or mat)

    def finish(self):
        bmesh.ops.remove_doubles(self.bm, verts=self.bm.verts[:], dist=1e-5)
        # normales: solo se recalculan las partes cerradas; las caras sueltas ya se orientaron al crearlas
        seen = set()
        closed = []
        for f in self.bm.faces:
            if f in seen:
                continue
            comp, st = [], [f]
            seen.add(f)
            while st:
                g = st.pop()
                comp.append(g)
                for e in g.edges:
                    for h in e.link_faces:
                        if h not in seen:
                            seen.add(h)
                            st.append(h)
            if all(len(e.link_faces) == 2 for g in comp for e in g.edges):
                closed.extend(comp)
        if closed:
            bmesh.ops.recalc_face_normals(self.bm, faces=closed)

    def tris(self):
        return sum(len(f.verts) - 2 for f in self.bm.faces)


# ---------------------------------------------------------------------------
# muros
# ---------------------------------------------------------------------------
WALL_KINDS = ("Solid", "Window", "Door", "Arch", "Barred", "Shutter")
VARIANTS = ("Clean", "StonePatch", "TimberPatch")


def _rect(x0, z0, x1, z1):
    return [(x0, z0), (x1, z0), (x1, z1), (x0, z1)]


def opening_of(kind, w):
    """Hueco en coordenadas del modulo: (tipo, x0, z0, x1, z1) o None."""
    if kind in ("Window", "Barred", "Shutter"):
        ow = min(0.95, w * 0.34)
        return ("win", -ow / 2, 0.95, ow / 2, 2.25)
    if kind == "Door":
        ow = min(1.3, w * 0.45)
        return ("door", -ow / 2, 0.0, ow / 2, 2.35)
    if kind == "Arch":
        ow = min(2.2, w * 0.74)
        return ("arch", -ow / 2, 0.0, ow / 2, 1.9 + ow / 2)
    return None


def arch_points(x0, x1, z_spring, n=8):
    r = (x1 - x0) / 2
    cx = (x0 + x1) / 2
    return [(cx + r * math.cos(math.pi * (1 - i / n)), z_spring + r * math.sin(math.pi * (1 - i / n)))
            for i in range(n + 1)]


def wall(mb, kind="Solid", w=MODULE_W, h=FLOOR_H, t=WALL_T, variant="Clean", rng=None, ground=False,
         mat=M_STONE, detail=0, warm=True):
    """Modulo de muro con hueco, marcos, alfeizar, dintel, zocalo y variante de remiendo. Cara exterior en +Y."""
    rng = rng or random.Random(0)
    y0, y1 = -t / 2, t / 2
    op = opening_of(kind, w)
    hw = w / 2
    if detail >= 2:
        # LOD2: caja maciza; el hueco se pinta como un plano 1 cm por delante
        mb.box((-hw, y0, 0), (hw, y1, h), mat, skip=("y-",))
        if op is not None:
            _, ox0, oz0, ox1, oz1 = op
            m2 = M_WARM if op[0] == "win" else M_WOOD
            mb.face([(ox0, y1 + 0.01, oz0), (ox1, y1 + 0.01, oz0), (ox1, y1 + 0.01, oz1), (ox0, y1 + 0.01, oz1)], m2,
                    nrm=(0, 1, 0))
        return
    if op is None:
        mb.box((-hw, y0, 0), (hw, y1, h), mat)
    elif op[0] == "win":
        _, ox0, oz0, ox1, oz1 = op
        mb.slab_holes(_rect(-hw, 0, hw, h), [_rect(ox0, oz0, ox1, oz1)], y0, y1, mat)
    elif op[0] == "door":
        _, ox0, oz0, ox1, oz1 = op
        outer = [(-hw, 0), (ox0, 0), (ox0, oz1), (ox1, oz1), (ox1, 0), (hw, 0), (hw, h), (-hw, h)]
        mb.slab_holes(outer, [], y0, y1, mat)
    else:
        _, ox0, oz0, ox1, oz1 = op
        pts = arch_points(ox0, ox1, oz1 - (ox1 - ox0) / 2, 8)
        outer = [(-hw, 0), (ox0, 0)] + pts + [(ox1, 0), (hw, 0), (hw, h), (-hw, h)]
        mb.slab_holes(outer, [], y0, y1, mat)
    # detalles del hueco
    if op is not None and detail < 2:
        _, ox0, oz0, ox1, oz1 = op
        if op[0] == "win":
            fr = 0.07
            inset = y1 - 0.12
            # marco de madera (anillo) + cristal calido + cruz
            if detail == 0:
                mb.slab_holes(_rect(ox0, oz0, ox1, oz1), [_rect(ox0 + fr, oz0 + fr, ox1 - fr, oz1 - fr)],
                              inset - 0.06, inset, M_WOOD)
            mb.face([(ox0 + fr, inset - 0.04, oz0 + fr), (ox1 - fr, inset - 0.04, oz0 + fr),
                     (ox1 - fr, inset - 0.04, oz1 - fr), (ox0 + fr, inset - 0.04, oz1 - fr)],
                    M_WARM if warm else M_IRON, nrm=(0, 1, 0))
            if detail == 0:
                mx = (ox0 + ox1) / 2
                mb.box((mx - 0.025, inset - 0.05, oz0 + fr), (mx + 0.025, inset, oz1 - fr), M_WOOD, skip=("y-",))
                mz = oz0 + (oz1 - oz0) * 0.62
                mb.box((ox0 + fr, inset - 0.05, mz - 0.025), (ox1 - fr, inset, mz + 0.025), M_WOOD, skip=("y-",))
            # alfeizar y dintel de piedra
            if detail == 0:
                mb.box((ox0 - 0.08, y1 - 0.05, oz0 - 0.09), (ox1 + 0.08, y1 + 0.07, oz0), M_STONE, skip=("y-",))
                mb.box((ox0 - 0.12, y1 - 0.02, oz1), (ox1 + 0.12, y1 + 0.04, oz1 + 0.18), M_STONE, skip=("y-",))
            if kind == "Barred" and detail == 0:
                nb = 4
                for i in range(nb):
                    bx = ox0 + (ox1 - ox0) * (i + 1) / (nb + 1)
                    mb.box((bx - 0.018, y1 - 0.06, oz0), (bx + 0.018, y1 - 0.024, oz1), M_IRON, skip=("z-", "z+"))
                mb.box((ox0, y1 - 0.065, (oz0 + oz1) / 2 - 0.02), (ox1, y1 - 0.02, (oz0 + oz1) / 2 + 0.02), M_IRON,
                       skip=("x-", "x+"))
            if kind == "Shutter":
                sw = (ox1 - ox0) / 2 + 0.02
                for side in (-1, 1):
                    xa = ox0 - sw if side < 0 else ox1
                    mb.box((xa, y1, oz0 - 0.02), (xa + sw, y1 + 0.04, oz1 + 0.02), M_WOOD, skip=("y-",))
        elif op[0] == "door":
            # hoja de madera rehundida, herrajes y dintel
            mb.box((ox0, y0 + 0.12, 0), (ox1, y0 + 0.18, oz1), M_WOOD, skip=("y-",))
            if detail == 0:
                for zz in (0.5, 1.7):
                    mb.box((ox0 + 0.08, y0 + 0.18, zz), (ox1 - 0.08, y0 + 0.2, zz + 0.06), M_IRON, skip=("y-",))
            mb.box((ox0 - 0.15, y1 - 0.02, oz1), (ox1 + 0.15, y1 + 0.05, oz1 + 0.24), M_STONE, skip=("y-",))
        else:
            # dovelas del arco: anillo de 6 piezas sobre el intrados
            pts = arch_points(ox0 - 0.18, ox1 + 0.18, oz1 - (ox1 - ox0) / 2, 6)
            ptsi = arch_points(ox0, ox1, oz1 - (ox1 - ox0) / 2, 6)
            for i in range(6):
                quad = [ptsi[i], pts[i], pts[i + 1], ptsi[i + 1]]
                mb.prism([(x, z) for x, z in quad], y1, y1 + 0.04, M_STONE)
    # zocalo
    if ground and detail < 2:
        if op is not None and op[0] in ("door", "arch"):
            _, ox0, _, ox1, _ = op
            for xa, xb in ((-hw, ox0), (ox1, hw)):
                if xb - xa > 0.05:
                    mb.box((xa, y1, 0), (xb, y1 + 0.05, PLINTH_H), M_GRAY, skip=("y-", "z-"))
        else:
            mb.box((-hw, y1, 0), (hw, y1 + 0.05, PLINTH_H), M_GRAY, skip=("y-", "z-"))
    # variantes remendadas
    if variant == "StonePatch" and detail < 2:  # el parche se conserva en LOD1 (se lee de lejos)
        stone_patch(mb, w, h, y1, op, rng)
    if variant == "TimberPatch" and detail == 0:
        timber_patch(mb, w, h, y1, op, rng)


def _free_spot(w, h, op, rng, pw, ph):
    """Busca hueco libre para un parche; si no cabe, prueba tamanos menores. Devuelve (cx, cz, pw, ph) o None."""
    hw = w / 2
    for scale in (1.0, 0.75, 0.55, 0.4):
        qw, qh = pw * scale, ph * scale
        for _ in range(25):
            cx = rng.uniform(-hw + qw / 2 + 0.08, hw - qw / 2 - 0.08)
            cz = rng.uniform(PLINTH_H + qh / 2 + 0.05, h - qh / 2 - 0.12)
            if op is None:
                return cx, cz, qw, qh
            _, ox0, oz0, ox1, oz1 = op
            if (cx + qw / 2 < ox0 - 0.1 or cx - qw / 2 > ox1 + 0.1 or cz - qh / 2 > oz1 + 0.2
                    or cz + qh / 2 < oz0 - 0.12):
                return cx, cz, qw, qh
    return None


def stone_patch(mb, w, h, y1, op, rng):
    """Parche irregular de otra piedra (MAT_Stone_Repair), 1.5 cm por delante de la fachada."""
    s = _free_spot(w, h, op, rng, rng.uniform(0.6, 1.1), rng.uniform(0.5, 0.9))
    if s is None:
        return
    cx, cz, pw, ph = s
    n = 6
    poly = []
    for i in range(n):
        a = 2 * math.pi * i / n + rng.uniform(-0.25, 0.25)
        poly.append((cx + math.cos(a) * pw / 2 * rng.uniform(0.8, 1.0), cz + math.sin(a) * ph / 2 * rng.uniform(0.8, 1.0)))
    mb.prism(poly, y1, y1 + 0.015, M_REPAIR)


def timber_patch(mb, w, h, y1, op, rng):
    """Vigas de reemplazo: una horizontal bajo la cornisa y un tornapuntas / riostra clavados encima."""
    hw = w / 2
    zz = h - 0.35
    mb.box((-hw + 0.05, y1, zz), (hw - 0.05, y1 + 0.08, zz + 0.2), M_WOOD, skip=("y-",))
    s = _free_spot(w, h, op, rng, 0.25, 1.2)
    if s:
        cx, cz, _pw, _ph = s
        ang = rng.choice((-1, 1)) * math.radians(rng.uniform(25, 40))
        mb.obox((cx, y1 + 0.04, cz), (0.16, 0.07, 1.3), rot_y=ang, mat=M_WOOD, skip=("y-",))


def timber_overlay(mb, w, h, y1, op, rng, detail=0):
    """Entramado de madera superpuesto (Rothenburg): soleras, pies derechos y riostras en las zonas macizas."""
    if detail >= 2:
        return
    hw = w / 2
    d = 0.06
    mb.box((-hw, y1, 0), (hw, y1 + d, 0.16), M_WOOD, skip=("y-",))
    mb.box((-hw, y1, h - 0.16), (hw, y1 + d, h), M_WOOD, skip=("y-",))
    xs = [-hw + 0.08, hw - 0.08]
    if op is None:
        xs.append(0.0)
    for x in xs:
        mb.box((x - 0.08, y1, 0.16), (x + 0.08, y1 + d, h - 0.16), M_WOOD, skip=("y-", "z-", "z+"))
    if detail == 0:
        if op is None:
            for sgn in (-1, 1):
                L = math.hypot(hw - 0.2, h - 0.4)
                ang = math.atan2(hw - 0.2, h - 0.4) * sgn
                mb.obox((sgn * hw / 2, y1 + d / 2, h / 2), (0.14, d, L), rot_y=ang, mat=M_WOOD, skip=("y-",))
        else:
            _, ox0, oz0, ox1, oz1 = op
            if op[0] == "win":
                mb.box((-hw + 0.16, y1, oz0 - 0.16), (hw - 0.16, y1 + d, oz0), M_WOOD, skip=("y-",))
                mb.box((-hw + 0.16, y1, oz1), (hw - 0.16, y1 + d, oz1 + 0.16), M_WOOD, skip=("y-",))
            for sgn, xa in ((-1, -hw + 0.16), (1, hw - 0.16)):
                xb = ox0 - 0.1 if sgn < 0 else ox1 + 0.1
                span = abs(xb - xa)
                if span > 0.35:
                    L = math.hypot(span, 1.0)
                    mb.obox(((xa + xb) / 2, y1 + d / 2, 0.66), (0.12, d, L), rot_y=math.atan2(span, 1.0) * -sgn,
                            mat=M_WOOD, skip=("y-",))


# ---------------------------------------------------------------------------
# piezas
# ---------------------------------------------------------------------------
def corner_post(mb, h, style="timber", rng=None):
    rng = rng or random.Random(0)
    if style == "timber":
        mb.box((-0.14, -0.14, 0), (0.14, 0.14, h), M_WOOD)
    else:
        z = 0.0
        k = 0
        while z < h - 0.05:
            hh = min(0.4, h - z)
            ext = 0.32 if k % 2 == 0 else 0.22
            mb.box((-ext / 2 - 0.04, -ext / 2 - 0.04, z), (ext / 2 + 0.04, ext / 2 + 0.04, z + hh),
                   M_STONE if rng.random() > 0.15 else M_REPAIR)
            z += hh
            k += 1


def buttress(mb, h, w=0.6, d0=0.9, d1=0.25):
    poly = [(0, 0), (d0, 0), (d0, 0.8), (d1, h - 0.3), (d1, h), (0, h)]
    # perfil en el plano Y-Z extruido en X: se reutiliza prism (plano X-Z) girando 90 grados
    mb.push(Matrix.Rotation(math.radians(90), 4, "Z"))
    mb.prism([(y, z) for y, z in poly], -w / 2, w / 2, M_STONE)
    mb.pop()


def floor_edge(mb, w, y1=WALL_T / 2, style="stone"):
    """Cornisa de piso: dos escalones de 12 y 22 cm de vuelo."""
    mat = M_STONE if style != "timber" else M_WOOD
    hw = w / 2
    mb.box((-hw, y1 - 0.02, -0.1), (hw, y1 + 0.12, 0.05), mat, skip=("y-",))
    mb.box((-hw, y1 - 0.02, 0.05), (hw, y1 + 0.22, 0.17), mat, skip=("y-",))


def arch_span(mb, w=3.0, h=4.2, t=0.7, pier=0.6):
    """Arco exento sobre calle: dos pilares + rosca semicircular + enjutas."""
    hw = w / 2 + pier
    ox0, ox1 = -w / 2, w / 2
    pts = arch_points(ox0, ox1, h - w / 2 - 0.5, 10)
    outer = [(-hw, 0), (ox0, 0)] + pts + [(ox1, 0), (hw, 0), (hw, h), (-hw, h)]
    mb.slab_holes(outer, [], -t / 2, t / 2, M_STONE)
    po = arch_points(ox0 - 0.25, ox1 + 0.25, h - w / 2 - 0.5, 8)
    pi_ = arch_points(ox0, ox1, h - w / 2 - 0.5, 8)
    for i in range(8):
        mb.prism([pi_[i], po[i], po[i + 1], pi_[i + 1]], t / 2, t / 2 + 0.05,
                 M_STONE if i % 3 else M_REPAIR)
    mb.box((-hw - 0.05, -t / 2 - 0.05, h - 0.2), (hw + 0.05, t / 2 + 0.05, h), M_STONE)


def stairs_ext(mb, rise=FLOOR_H, width=1.2, step_h=0.2, tread=0.28):
    """Escalera exterior adosada (sube hacia +X), con zanca de piedra y barandilla de hierro."""
    n = int(round(rise / step_h))
    prof = [(0.0, 0.0)]
    for i in range(n):
        prof += [(i * tread, (i + 1) * step_h), ((i + 1) * tread, (i + 1) * step_h)]
    prof += [(n * tread, 0.0)]
    mb.push(Matrix.Rotation(math.radians(0), 4, "Z"))
    mb.prism(prof, 0.0, width, M_STONE)
    mb.pop()
    for i in range(0, n + 1, 3):
        x = min(i, n) * tread
        z = min(i, n) * step_h
        mb.box((x - 0.02, width - 0.04, z), (x + 0.02, width, z + 0.95), M_IRON, skip=("z-",))
    L = math.hypot(n * tread, n * step_h)
    mb.obox((n * tread / 2, width - 0.02, n * step_h / 2 + 0.95), (L, 0.04, 0.04),
            rot_y=-math.atan2(n * step_h, n * tread), mat=M_IRON)


def balcony(mb, w=3.0, depth=1.5, kind="wood"):
    """Balcon de 1.5 m de vuelo: plataforma, ménsulas y antepecho. Origen en el pie de la fachada (y=0)."""
    hw = w / 2
    if kind == "wood":
        mb.box((-hw, 0, -0.12), (hw, depth, 0.0), M_WOOD)
        for x in (-hw + 0.2, 0, hw - 0.2):
            mb.obox((x, depth * 0.35, -0.45), (0.12, 0.12, 0.95), rot_y=0, rot_z=0, mat=M_WOOD)
            mb.obox((x, depth * 0.42, -0.4), (0.1, depth * 0.95, 0.1), rot_y=0, mat=M_WOOD)
        n = int(w / 0.3)
        for i in range(n + 1):
            x = -hw + w * i / n
            mb.box((x - 0.025, depth - 0.06, 0), (x + 0.025, depth - 0.01, 0.95), M_WOOD, skip=("z-",))
        for side in (-1, 1):
            mb.box((side * hw - 0.03, 0.05, 0), (side * hw + 0.03, depth, 0.95), M_WOOD, skip=("z-",))
        mb.box((-hw, depth - 0.08, 0.95), (hw, depth + 0.02, 1.02), M_WOOD)
    else:
        mb.box((-hw, 0, -0.2), (hw, depth, 0.0), M_STONE)
        for x in (-hw + 0.25, hw - 0.25):
            mb.prism([(0, -0.2), (depth * 0.8, -0.2), (0, -0.9)], x - 0.15, x + 0.15, M_STONE)
        mb.box((-hw, depth - 0.18, 0), (hw, depth, 0.95), M_STONE, skip=("z-",))
        for side in (-1, 1):
            mb.box((side * hw - 0.18 * (side > 0), 0.02, 0), (side * hw + 0.18 * (side < 0) - 0.0, depth - 0.18, 0.95),
                   M_STONE, skip=("z-",))


# ---------------------------------------------------------------------------
# tejados (W a lo largo de X, D a lo largo de Y; base de la cubierta en z=0)
# ---------------------------------------------------------------------------
def _course_slope(mb, x0, x1, y_eave, y_ridge, z_eave, z_ridge, rng, toneB=0.18, detail=0, th=0.06):
    """Una vertiente de tejas por hiladas (tablas solapadas) entre el alero y la cumbrera, con 2 tonos."""
    L = math.hypot(y_ridge - y_eave, z_ridge - z_eave)
    n = max(1, int(L / TILE_COURSE)) if detail == 0 else max(1, int(L / (TILE_COURSE * 3)))
    seg = TILE_SEG if detail == 0 else (x1 - x0)
    nx = max(1, int(round((x1 - x0) / seg)))
    for i in range(n):
        t0, t1 = i / n, min(1.0, (i + 1) / n + 0.06)
        ya, za = y_eave + (y_ridge - y_eave) * t0, z_eave + (z_ridge - z_eave) * t0
        yb, zb = y_eave + (y_ridge - y_eave) * t1, z_eave + (z_ridge - z_eave) * t1
        for k in range(nx):
            xa = x0 + (x1 - x0) * k / nx
            xb = x0 + (x1 - x0) * (k + 1) / nx
            mat = M_ROOF_B if rng.random() < toneB else M_ROOF
            lift = th * (1 if i % 2 else 0.6)
            # tabla inclinada: cara superior + canto inferior (la hilada se lee desde la camara)
            down = 1.0 if y_eave > y_ridge else -1.0
            mb.face([(xa, ya, za + lift), (xb, ya, za + lift), (xb, yb, zb + th * 0.3), (xa, yb, zb + th * 0.3)],
                    mat, nrm=(0, down * 0.3, 1))
            mb.face([(xa, ya, za), (xb, ya, za), (xb, ya, za + lift), (xa, ya, za + lift)], mat, nrm=(0, down, 0))


def roof_gable(mb, W, D, pitch=ROOF_PITCH, eave=EAVE, rng=None, detail=0, repairs=2):
    """Cubierta a dos aguas, cumbrera paralela a X. Devuelve (altura de cumbrera, triangulos de hastial)."""
    rng = rng or random.Random(0)
    hx = W / 2 + eave
    hy = D / 2 + eave
    rise = (D / 2) * math.tan(math.radians(pitch))
    z_e = -eave * math.tan(math.radians(pitch))
    for sgn in (-1, 1):
        y_e = sgn * hy
        _course_slope(mb, -hx, hx, y_e, 0.0, z_e, rise, rng, detail=detail)
        # tablero de base (cierra la vista por debajo del alero) y tabica de alero
        mb.face([(-hx, y_e, z_e), (-hx, 0, rise), (hx, 0, rise), (hx, y_e, z_e)], M_WOOD, nrm=(0, 0, -1))
        mb.box((-hx, y_e - 0.03, z_e - 0.18), (hx, y_e + 0.03, z_e), M_WOOD)
    # cumbrera
    mb.box((-hx, -0.12, rise - 0.02), (hx, 0.12, rise + 0.14), M_ROOF_B if rng.random() < 0.5 else M_ROOF)
    # tabicas de hastial (bargeboards)
    for sx in (-1, 1):
        x = sx * hx
        for sgn in (-1, 1):
            mb.rod((x, sgn * hy, z_e + 0.05), (x, 0.0, rise + 0.08), 0.06, M_WOOD, caps=True)
    if detail == 0:
        roof_repairs(mb, W, D, rise, z_e, hy, rng, repairs)
    return rise


def roof_repairs(mb, W, D, rise, z_e, hy, rng, n):
    """Remiendos: rectangulos de teja de otro tono 2 cm por encima de la vertiente."""
    for _ in range(n):
        sgn = rng.choice((-1, 1))
        t0 = rng.uniform(0.15, 0.6)
        t1 = t0 + rng.uniform(0.15, 0.3)
        xa = rng.uniform(-W / 2 + 0.3, W / 2 - 1.5)
        xb = xa + rng.uniform(0.8, 1.6)
        ya, yb = sgn * hy * (1 - t0), sgn * hy * (1 - t1)
        za, zb = z_e + (rise - z_e) * t0 + 0.11, z_e + (rise - z_e) * t1 + 0.11
        mb.face([(xa, ya, za), (xb, ya, za), (xb, yb, zb), (xa, yb, zb)], M_ROOF_B, nrm=(0, 0.3 * sgn, 1))


def gable_walls(mb, W, D, rise, t=WALL_T, mat=M_STONE, axis="x"):
    """Triangulos de hastial (parte del cuerpo). axis='x': cumbrera paralela a X -> hastiales en x=+-W/2."""
    for sx in (-1, 1):
        x = sx * (W / 2 - t / 2)
        poly = [(-D / 2, 0), (D / 2, 0), (0, rise)]
        mb.push(Matrix.Translation((x, 0, 0)) @ Matrix.Rotation(math.radians(90), 4, "Z"))
        mb.prism([(y, z) for y, z in poly], -t / 2, t / 2, mat)
        mb.pop()


def roof_hip(mb, W, D, pitch=ROOF_PITCH, eave=EAVE, rng=None, detail=0):
    rng = rng or random.Random(0)
    hx, hy = W / 2 + eave, D / 2 + eave
    rise = (min(W, D) / 2) * math.tan(math.radians(pitch))
    z_e = -eave * math.tan(math.radians(pitch))
    rx = max(0.0, hx - hy)
    ry = max(0.0, hy - hx)
    top = [(-rx, -ry, rise), (rx, -ry, rise), (rx, ry, rise), (-rx, ry, rise)]
    base = [(-hx, -hy, z_e), (hx, -hy, z_e), (hx, hy, z_e), (-hx, hy, z_e)]
    for i in range(4):
        j = (i + 1) % 4
        mat = M_ROOF if rng.random() > 0.25 else M_ROOF_B
        quad = [base[i], base[j], top[j], top[i]]
        out = ((base[i][0] + base[j][0]) / 2, (base[i][1] + base[j][1]) / 2, 0)
        if top[i] == top[j]:
            mb.face(quad[:3], mat, nrm=(out[0], out[1], 1))
        else:
            mb.face(quad, mat, nrm=(out[0], out[1], 1))
        mb.face([base[j], base[i], (base[i][0], base[i][1], base[i][2] - 0.18), (base[j][0], base[j][1], base[j][2] - 0.18)],
                M_WOOD, nrm=out)
    mb.face([(b[0], b[1], b[2] - 0.18) for b in base], M_WOOD, nrm=(0, 0, -1))
    if rx > 0 or ry > 0:
        mb.box((-rx - 0.1, -ry - 0.1, rise - 0.02), (rx + 0.1, ry + 0.1, rise + 0.12), M_ROOF_B)
    if detail == 0:
        # hiladas marcadas: listones horizontales por vertiente (relieve de teja) y remiendos
        L = rise - z_e
        n = max(2, int(L / (TILE_COURSE * 1.6)))
        for k in range(1, n):
            f = k / n
            z = z_e + L * f
            bx = hx - (hx - rx) * f
            by = hy - (hy - ry) * f
            for (a, b) in (((-bx, -by), (bx, -by)), ((bx, -by), (bx, by)), ((bx, by), (-bx, by)), ((-bx, by), (-bx, -by))):
                mb.face([(a[0], a[1], z), (b[0], b[1], z), (b[0] * 0.995, b[1] * 0.995, z + 0.05),
                         (a[0] * 0.995, a[1] * 0.995, z + 0.05)], M_ROOF if rng.random() > 0.2 else M_ROOF_B,
                        nrm=((a[0] + b[0]) / 2, (a[1] + b[1]) / 2, 0))
    return rise


def roof_conical(mb, r, pitch=55.0, eave=EAVE, n=16, rng=None, detail=0):
    rng = rng or random.Random(0)
    R = r + eave
    h = R * math.tan(math.radians(pitch))
    bands = 4 if detail == 0 else 1
    z_e = 0.0
    for b in range(bands):
        r0 = R * (1 - b / bands)
        r1 = R * (1 - (b + 1) / bands)
        z0 = z_e + h * b / bands
        z1 = z_e + h * (b + 1) / bands
        mat = M_ROOF_B if (b % 2 == 1 and rng.random() < 0.7) else M_ROOF
        if r1 < 1e-3:
            for i in range(n):
                a0, a1 = 2 * math.pi * i / n, 2 * math.pi * (i + 1) / n
                mb.face([(r0 * math.cos(a0), r0 * math.sin(a0), z0), (r0 * math.cos(a1), r0 * math.sin(a1), z0),
                         (0, 0, z1)], mat)
        else:
            mb.cylinder(r0, z0, z1, n, mat, r1=r1 + 0.03, caps=False)
    mb.cylinder(R, -0.2, 0.0, n, M_WOOD, caps=False)
    mb.ngon_fill([(R * math.cos(2 * math.pi * i / n), R * math.sin(2 * math.pi * i / n), -0.2) for i in range(n)],
                 M_WOOD, flip=True)
    mb.cylinder(0.05, h, h + 1.0, 6, M_IRON, caps=True)
    return h


def roof_flat_parapet(mb, W, D, ph=0.9, t=0.3):
    """Azotea con pretil (Toledo): losa, pretil perimetral y gargolas de piedra."""
    hw, hd = W / 2, D / 2
    mb.box((-hw + t, -hd + t, 0), (hw - t, hd - t, 0.12), M_GRAY, skip=("z-",))
    for (x0, y0, x1, y1) in ((-hw, -hd, hw, -hd + t), (-hw, hd - t, hw, hd), (-hw, -hd + t, -hw + t, hd - t),
                             (hw - t, -hd + t, hw, hd - t)):
        mb.box((x0, y0, 0), (x1, y1, ph), M_STONE, skip=("z-",))
    for x in (-hw / 2, hw / 2):
        mb.box((x - 0.1, hd, 0.15), (x + 0.1, hd + 0.5, 0.32), M_STONE, skip=("y-",))
    return ph


def roof_lean_to(mb, W, D, pitch=25.0, eave=EAVE, rng=None, detail=0):
    """Cubierta de un agua (cobertizo): cae hacia +Y desde el muro trasero."""
    rng = rng or random.Random(0)
    hx = W / 2 + eave
    rise = D * math.tan(math.radians(pitch))
    z_e = -eave * math.tan(math.radians(pitch))
    _course_slope(mb, -hx, hx, D / 2 + eave, -D / 2, z_e, rise, rng, detail=detail)
    mb.face([(hx, D / 2 + eave, z_e), (hx, -D / 2, rise), (-hx, -D / 2, rise), (-hx, D / 2 + eave, z_e)], M_WOOD,
            nrm=(0, 0, -1))
    mb.box((-hx, D / 2 + eave - 0.03, z_e - 0.18), (hx, D / 2 + eave + 0.03, z_e), M_WOOD)
    return rise


def chimney(mb, h=1.8, capped=True, rng=None):
    rng = rng or random.Random(0)
    mb.box((-0.35, -0.3, 0), (0.35, 0.3, h), M_STONE if rng.random() > 0.3 else M_REPAIR)
    mb.box((-0.42, -0.37, h - 0.25), (0.42, 0.37, h - 0.1), M_STONE)
    if capped:
        mb.box((-0.45, -0.4, h + 0.25), (0.45, 0.4, h + 0.33), M_STONE)
        for x in (-0.28, 0.28):
            mb.box((x - 0.05, -0.05, h), (x + 0.05, 0.05, h + 0.25), M_STONE, skip=("z-",))
        mb.cylinder(0.08, h, h + 0.35, 6, M_GRAY, caps=False, center=(0.0, 0.0))
    else:
        mb.box((-0.3, -0.25, h), (0.3, 0.25, h + 0.12), M_REPAIR, skip=("z-",))


def dormer(mb, w=1.4, h=1.3, d=1.2, rng=None):
    """Buhardilla: frente con ventana calida, laterales y tejadito a dos aguas. Frente hacia +Y."""
    rng = rng or random.Random(0)
    mb.slab_holes(_rect(-w / 2, 0, w / 2, h), [_rect(-0.3, 0.25, 0.3, 1.0)], d - 0.1, d, M_STONE)
    mb.face([(-0.3, d - 0.08, 0.25), (0.3, d - 0.08, 0.25), (0.3, d - 0.08, 1.0), (-0.3, d - 0.08, 1.0)], M_WARM,
            nrm=(0, 1, 0))
    for sx in (-1, 1):
        mb.face([(sx * w / 2, 0, 0), (sx * w / 2, d, 0), (sx * w / 2, d, h), (sx * w / 2, 0, h)], M_STONE,
                nrm=(sx, 0, 0))
    rise = (w / 2) * math.tan(math.radians(45))
    for sx in (-1, 1):
        mb.face([(0, -0.1, h + rise), (0, d + 0.25, h + rise), (sx * (w / 2 + 0.15), d + 0.25, h - 0.1),
                 (sx * (w / 2 + 0.15), -0.1, h - 0.1)], M_ROOF if rng.random() > 0.3 else M_ROOF_B, nrm=(sx, 0, 1))
    mb.prism([(-w / 2, h), (w / 2, h), (0, h + rise)], d - 0.1, d, M_STONE)


# ---------------------------------------------------------------------------
# props
# ---------------------------------------------------------------------------
def awning(mb, w=3.0, depth=1.5, variant=0, rng=None):
    """Toldo de tela remendada (A/B/C) con dos tirantes de hierro. Origen en la fachada, cae hacia +Y."""
    rng = rng or random.Random(variant)
    base = M_CLOTH[variant % 3]
    patch = M_CLOTH[(variant + 1) % 3]
    hw = w / 2
    drop = 0.6
    top = [(-hw, 0, 0), (hw, 0, 0), (hw, depth, -drop), (-hw, depth, -drop)]
    mb.face(top, base, nrm=(0, 0.5, 1))
    mb.face(top, base, nrm=(0, -0.5, -1))
    val = [(-hw, depth, -drop), (hw, depth, -drop), (hw, depth, -drop - 0.25), (-hw, depth, -drop - 0.25)]
    mb.face(val, base, nrm=(0, 1, 0))
    mb.face(val, base, nrm=(0, -1, 0))
    for _ in range(2):
        a = rng.uniform(0.1, 0.5)
        x0 = rng.uniform(-hw + 0.2, hw - 0.9)
        x1 = x0 + rng.uniform(0.4, 0.7)
        t0, t1 = a, a + rng.uniform(0.2, 0.35)
        cos = [(x0, depth * t0, -drop * t0 + 0.012), (x1, depth * t0, -drop * t0 + 0.012),
               (x1, depth * t1, -drop * t1 + 0.012), (x0, depth * t1, -drop * t1 + 0.012)]
        mb.face(cos, patch, nrm=(0, 0.5, 1))
    for x in (-hw + 0.1, hw - 0.1):
        mb.rod((x, 0.0, 0.7), (x, depth, -drop), 0.015, M_IRON)


def sign_hanging(mb, rng=None):
    """Letrero colgante: brazo de hierro con voluta + tablero de madera colgado de dos cadenas. Sale hacia +Y."""
    mb.box((-0.03, 0, 0), (0.03, 0.95, 0.06), M_IRON)
    mb.rod((0, 0.0, -0.45), (0, 0.55, 0.0), 0.02, M_IRON)
    mb.box((-0.04, -0.04, -0.06), (0.04, 0.04, 0.12), M_IRON)
    for y in (0.3, 0.85):
        mb.box((-0.01, y - 0.01, -0.25), (0.01, y + 0.01, 0.0), M_IRON, skip=("z-", "z+"))
    mb.box((-0.03, 0.2, -0.85), (0.03, 0.95, -0.25), M_WOOD)
    mb.box((-0.035, 0.27, -0.78), (0.035, 0.88, -0.32), M_CLOTH[0], skip=("z-", "z+"))


def lantern_shard(mb):
    """Farolillo de esquirla: brazo de hierro, jaula, esquirla azul #8FD0FF (emision 2.5). Sale hacia +Y."""
    mb.box((-0.025, 0, 0), (0.025, 0.55, 0.05), M_IRON)
    mb.box((-0.06, -0.02, -0.2), (0.06, 0.02, 0.15), M_IRON)
    cy = 0.5
    mb.box((-0.11, cy - 0.11, -0.05), (0.11, cy + 0.11, 0.0), M_IRON)
    mb.box((-0.13, cy - 0.13, -0.42), (0.13, cy + 0.13, -0.37), M_IRON)
    for sx in (-1, 1):
        for sy in (-1, 1):
            mb.box((sx * 0.11 - 0.012, cy + sy * 0.11 - 0.012, -0.37), (sx * 0.11 + 0.012, cy + sy * 0.11 + 0.012, -0.05),
                   M_IRON, skip=("z-", "z+"))
    top, bot = (0, cy, -0.08), (0, cy, -0.34)
    ring = [(0.07 * math.cos(a), cy + 0.07 * math.sin(a), -0.21) for a in [i * math.pi / 2 for i in range(4)]]
    for i in range(4):
        j = (i + 1) % 4
        mb.face([ring[i], ring[j], top], M_SHARD)
        mb.face([ring[j], ring[i], bot], M_SHARD)


def crate(mb, s=0.6, fruit=False, rng=None):
    rng = rng or random.Random(0)
    if not fruit:
        mb.box((-s / 2, -s / 2, 0), (s / 2, s / 2, s), M_WOOD, skip=("z-",))
        for z in (0.08, s - 0.08):
            mb.box((-s / 2 - 0.015, -s / 2 - 0.015, z - 0.04), (s / 2 + 0.015, s / 2 + 0.015, z + 0.04), M_WOOD,
                   skip=("z-", "z+"))
    else:
        w, d, h = 0.8, 0.5, 0.3
        mb.box((-w / 2, -d / 2, 0), (w / 2, d / 2, 0.04), M_WOOD)
        for (x0, y0, x1, y1) in ((-w / 2, -d / 2, w / 2, -d / 2 + 0.03), (-w / 2, d / 2 - 0.03, w / 2, d / 2),
                                 (-w / 2, -d / 2, -w / 2 + 0.03, d / 2), (w / 2 - 0.03, -d / 2, w / 2, d / 2)):
            mb.box((x0, y0, 0.04), (x1, y1, h), M_WOOD, skip=("z-",))
        for i in range(10):
            x = rng.uniform(-w / 2 + 0.1, w / 2 - 0.1)
            y = rng.uniform(-d / 2 + 0.1, d / 2 - 0.1)
            r = rng.uniform(0.05, 0.07)
            m = M_CLOTH[rng.randrange(3)]
            z = h - 0.03
            pts = [(x + r * math.cos(a), y + r * math.sin(a), z) for a in [k * 2 * math.pi / 5 for k in range(5)]]
            for k in range(5):
                mb.face([pts[k], pts[(k + 1) % 5], (x, y, z + r)], m, nrm=(0, 0, 1))


def barrel(mb, r=0.32, h=0.9, n=12):
    mid = r * 1.12
    mb.cylinder(r, 0, h * 0.5, n, M_WOOD, r1=mid, caps=False)
    mb.cylinder(mid, h * 0.5, h, n, M_WOOD, r1=r, caps=False)
    mb.ngon_fill([(r * math.cos(2 * math.pi * i / n), r * math.sin(2 * math.pi * i / n), h) for i in range(n)], M_WOOD)
    for z, rr in ((0.12, r * 1.04), (h - 0.12, r * 1.04)):
        mb.cylinder(rr + 0.01, z - 0.03, z + 0.03, n, M_IRON, caps=False)


def tool_rack(mb, rng=None):
    rng = rng or random.Random(0)
    w, h = 1.4, 1.6
    for x in (-w / 2, w / 2):
        mb.box((x - 0.04, -0.04, 0), (x + 0.04, 0.04, h), M_WOOD)
    for z in (0.35, 1.35):
        mb.box((-w / 2, -0.03, z - 0.04), (w / 2, 0.03, z + 0.04), M_WOOD, skip=("x-", "x+"))
    for i in range(4):
        x = -w / 2 + 0.25 + i * 0.3
        mb.box((x - 0.02, 0.04, 0.2), (x + 0.02, 0.08, 1.45), M_WOOD)
        if i % 2 == 0:
            mb.box((x - 0.09, 0.03, 1.45), (x + 0.09, 0.09, 1.6), M_IRON)
        else:
            mb.box((x - 0.03, 0.03, 0.05), (x + 0.03, 0.12, 0.25), M_IRON)
