"""
CONCORDIA - PJ2: geometria del conjunto inicial del Sanador (CLASE_SANADOR, provisional) y del cabello del elfo.
Todo se construye por script sobre el cuerpo de elfo_v01.blend (pose T, metros, de cara a -Y):
  Robe_Top      tunica (pecho y mangas): superficie del cuerpo desplazada 1,6 cm, cortada en la cintura y a media
                manga por bucles reales; mangas acampanadas con dobladillo vuelto; colgante de cristal y cordon
  Robe_Skirt    falda en anillos (seccion del cuerpo + holgura + vuelo), paneles delantero y trasero separados por
                aberturas laterales desde el dobladillo hasta encima de la rodilla; dobladillo vuelto
  Hood          esclavina de lana sobre los hombros (marcha sobre la tunica desde el cuello) con la capucha bajada
                (bolsa sobre la espalda y cuello vuelto)
  Belt_Pouches  cinturon (tubo de seccion rectangular), hebilla y punta, 3 bolsitas y 2 frascos con tapon
  Boots         pies + pierna baja desplazados, suavizados (sin dedos), suela en z = 0 y vuelta en la cana
  Bracers       vendas de tela del antebrazo (anillos sobre la seccion del brazo)
  Hair_Elf      casquete sobre el cuero cabelludo (sin tapar las orejas), mechones (cards) peinados hacia atras y
                trenza que baja por la espalda con atadura y punta
Cada vertice lleva atributos de patron por esquina (pu, pv en metros; pa, pb normalizados) y cada cara su clase de
material (cls) para pintar el atlas (pj2_atlas.py).
"""

import math

import bmesh
import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree

# clases de material del atlas
LINEN, WOOL, LEATHER, BOOT, WRAP, GLASS, METAL, CRYSTAL, HAIR, CORD, BRAID, HAIRCAP, CORK, LIQUID = range(1, 15)
CLS_NAMES = {LINEN: "lino", WOOL: "lana", LEATHER: "cuero", BOOT: "cuero_bota", WRAP: "venda", GLASS: "vidrio",
             METAL: "hierro", CRYSTAL: "cristal", HAIR: "pelo", CORD: "cordon", BRAID: "trenza", HAIRCAP: "casquete",
             CORK: "tapon", LIQUID: "tintura"}
FAR = 9.0           # pv "lejos de cualquier orilla"


# ----------------------------------------------------------------------------------------------------------------
# utilidades
# ----------------------------------------------------------------------------------------------------------------
def body_bvh(objs):
    bm = bmesh.new()
    for o in objs:
        me = o.data.copy()
        me.transform(o.matrix_world)
        bm.from_mesh(me)
        bpy.data.meshes.remove(me)
    bm.normal_update()
    t = BVHTree.FromBMesh(bm)
    vs = [v.co.copy() for v in bm.verts]
    bm.free()
    return t, vs


class Piece:
    """Acumula geometria (varias partes) con atributos por esquina y clase por cara; se vuelca a un objeto."""

    def __init__(self, name):
        self.name = name
        self.verts = []
        self.faces = []          # lista de (indices, cls, [(pu, pv, pa, pb) por esquina])

    def add_vert(self, co):
        self.verts.append(Vector(co))
        return len(self.verts) - 1

    def add_face(self, idx, cls, attrs=None):
        attrs = attrs or [(0.0, FAR, 0.0, 0.0)] * len(idx)
        self.faces.append((list(idx), cls, [tuple(a) for a in attrs]))

    def add_bmesh(self, bm, cls_of_face, attr_of_loop):
        base = len(self.verts)
        bm.verts.index_update()
        for v in bm.verts:
            self.verts.append(v.co.copy())
        for f in bm.faces:
            self.add_face([base + v.index for v in f.verts], cls_of_face(f), [attr_of_loop(l) for l in f.loops])

    def tris(self):
        return sum(len(f[0]) - 2 for f in self.faces)

    def to_object(self, col):
        me = bpy.data.meshes.new(self.name)
        me.from_pydata([tuple(v) for v in self.verts], [], [f[0] for f in self.faces])
        me.validate(clean_customdata=False)
        cls = me.attributes.new("cls", "INT", "FACE")
        cls.data.foreach_set("value", [f[1] for f in self.faces])
        flat = [a for f in self.faces for a in f[2]]
        for k, nm in enumerate(("pu", "pv", "pa", "pb")):
            at = me.attributes.new(nm, "FLOAT", "CORNER")
            at.data.foreach_set("value", [a[k] for a in flat])
        for p in me.polygons:
            p.use_smooth = True
        me.update()
        o = bpy.data.objects.new(self.name, me)
        col.objects.link(o)
        return o


def lathe(piece, cls_fn, axis_pts, radii, n, frame, start=0.0, close_bottom=True, close_top=False, squash=1.0):
    """Solido de revolucion: axis_pts (centros), radii (radio por anillo), frame=(u, w) ejes del plano del anillo."""
    u, w = frame
    rings = []
    for c, r in zip(axis_pts, radii):
        ring = []
        for j in range(n):
            a = start + 2 * math.pi * j / n
            ring.append(piece.add_vert(c + u * (r * math.cos(a)) + w * (r * squash * math.sin(a))))
        rings.append(ring)
    lens = [0.0]
    for k in range(1, len(axis_pts)):
        lens.append(lens[-1] + (axis_pts[k] - axis_pts[k - 1]).length)
    for k in range(len(rings) - 1):
        for j in range(n):
            j2 = (j + 1) % n
            cu = [(2 * math.pi * jj / n) * max(radii[k], 1e-3) for jj in (j, j + 1, j + 1, j)]
            pv = [lens[k], lens[k], lens[k + 1], lens[k + 1]]
            piece.add_face([rings[k][j], rings[k][j2], rings[k + 1][j2], rings[k + 1][j]], cls_fn(k),
                           [(cu[i], pv[i], j / n, k / max(len(rings) - 1, 1)) for i in range(4)])
    for cap, flag, k in ((rings[0], close_bottom, 0), (rings[-1], close_top, len(rings) - 1)):
        if flag:
            ci = piece.add_vert(axis_pts[k])
            for j in range(n):
                j2 = (j + 1) % n
                idx = [cap[j], ci, cap[j2]] if k == 0 else [cap[j], cap[j2], ci]
                piece.add_face(idx, cls_fn(k))
    return rings


def section_radius(pts, center, n, axis="z", sm=2):
    """Radio maximo por sector angular de una nube de puntos (seccion). axis 'z': plano XY; 'x': plano YZ."""
    r = [0.0] * n
    for p in pts:
        d = p - center
        if axis == "z":
            a, rr = math.atan2(d.y, d.x), math.hypot(d.x, d.y)
        else:
            a, rr = math.atan2(d.z, d.y), math.hypot(d.y, d.z)
        j = int(round((a % (2 * math.pi)) / (2 * math.pi) * n)) % n
        for dj in (-1, 0, 1):
            r[(j + dj) % n] = max(r[(j + dj) % n], rr)
    for _ in range(sm):
        r = [(r[j - 1] + 2 * r[j] + r[(j + 1) % n]) / 4 for j in range(n)]
    return r


def push_out(bm, tree, min_d, skip=()):
    """Ningun vertice a menos de min_d por fuera de la superficie de 'tree'."""
    n = 0
    for v in bm.verts:
        if v.index in skip:
            continue
        loc, nrm, _i, _d = tree.find_nearest(v.co)
        if loc is None:
            continue
        s = (v.co - loc).dot(nrm)
        if s < min_d:
            v.co = v.co + nrm * (min_d - s)
            n += 1
    return n


def body_region_bmesh(objs, face_filter=None):
    bm = bmesh.new()
    for o in objs:
        me = o.data.copy()
        me.transform(o.matrix_world)
        bm.from_mesh(me)
        bpy.data.meshes.remove(me)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    if face_filter:
        bmesh.ops.delete(bm, geom=[f for f in bm.faces if not face_filter(f)], context="FACES")
        bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context="VERTS")
    bm.normal_update()
    return bm


def cut_by_seam(bm, seam_fn, keep_point):
    """Corta la malla por el ciclo de aristas de seam_fn(bm) (find_seam) y deja la componente que contiene el
    punto mas cercano a keep_point."""
    for seq in (bm.verts, bm.edges, bm.faces):
        seq.index_update()
        seq.ensure_lookup_table()
    b = seam_fn(bm)
    if b is None:
        raise RuntimeError("no se encontro el bucle de corte")
    edges = set(b[1])
    bm.faces.ensure_lookup_table()
    bm.edges.ensure_lookup_table()
    comp = {}
    n = 0
    for f0 in bm.faces:
        if f0.index in comp:
            continue
        stack = [f0]
        comp[f0.index] = n
        while stack:
            f = stack.pop()
            for e in f.edges:
                if e.index in edges:
                    continue
                for g in e.link_faces:
                    if g.index not in comp:
                        comp[g.index] = n
                        stack.append(g)
        n += 1
    kp = Vector(keep_point)
    fk = min(bm.faces, key=lambda f: (f.calc_center_median() - kp).length)
    keep = comp[fk.index]
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if comp[f.index] != keep], context="FACES")
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context="VERTS")
    bm.verts.index_update()
    bm.edges.index_update()
    bm.faces.index_update()
    return b


def boundary_loops(bm):
    """Bordes abiertos como listas ordenadas de vertices."""
    bnd = [e for e in bm.edges if e.is_boundary]
    adj = {}
    for e in bnd:
        a, b = e.verts
        adj.setdefault(a, []).append(b)
        adj.setdefault(b, []).append(a)
    seen, loops = set(), []
    for v0 in adj:
        if v0 in seen:
            continue
        loop, prev, v = [v0], None, v0
        seen.add(v0)
        while True:
            nx = [x for x in adj[v] if x is not prev and x not in seen]
            if not nx:
                break
            prev, v = v, nx[0]
            loop.append(v)
            seen.add(v)
        loops.append(loop)
    return loops


def extrude_rings(bm, loop, ring_fn, steps):
    """Extruye un borde (lista de BMVert ordenada y cerrada) en anillos nuevos: ring_fn(k, v_original) -> pos."""
    prev = loop
    allr = [loop]
    orig = [v.co.copy() for v in loop]
    for k in range(1, steps + 1):
        ring = [bm.verts.new(ring_fn(k, orig[i], i)) for i in range(len(loop))]
        n = len(loop)
        for i in range(n):
            i2 = (i + 1) % n
            bm.faces.new((prev[i], prev[i2], ring[i2], ring[i]))
        prev = ring
        allr.append(ring)
    bm.normal_update()
    return allr


def hem_coords(bm, sources):
    """Distancia por la malla (Dijkstra por aristas) a los vertices fuente y posicion a lo largo del borde de la
    fuente mas cercana: (pu, pv) por vertice. sources = lista de bucles ordenados (BMVert)."""
    import heapq
    pu, pv = {}, {}
    pq = []
    for loop in sources:
        s = 0.0
        for i, v in enumerate(loop):
            if i:
                s += (v.co - loop[i - 1].co).length
            pu[v.index], pv[v.index] = s, 0.0
            heapq.heappush(pq, (0.0, v.index))
    vmap = {v.index: v for v in bm.verts}
    while pq:
        d, i = heapq.heappop(pq)
        if d > pv.get(i, 1e9):
            continue
        v = vmap[i]
        for e in v.link_edges:
            o = e.other_vert(v)
            nd = d + e.calc_length()
            if nd < pv.get(o.index, 1e9):
                pv[o.index], pu[o.index] = nd, pu[i]
                heapq.heappush(pq, (nd, o.index))
    return pu, pv


def wrap_fix(vals, period):
    """Valores de pu de una cara que cruzan la costura del bucle: se desenrollan."""
    if period <= 0 or max(vals) - min(vals) < period / 2:
        return vals
    return [x + period if x < period / 2 else x for x in vals]


def add_bm_with_hem(piece, bm, cls, hem_loops, extra_cls=None):
    """Vuelca un bmesh con pu/pv de orilla (dobladillo) a la pieza."""
    bm.verts.index_update()
    pu, pv = hem_coords(bm, hem_loops) if hem_loops else ({}, {})
    per = max((sum((lp[i].co - lp[i - 1].co).length for i in range(len(lp))) for lp in hem_loops), default=0.0)

    def cf(f):
        return extra_cls(f) if extra_cls else cls

    base = len(piece.verts)
    for v in bm.verts:
        piece.verts.append(v.co.copy())
    for f in bm.faces:
        us = wrap_fix([pu.get(v.index, 0.0) for v in f.verts], per)
        piece.add_face([base + v.index for v in f.verts], cf(f),
                       [(us[i], pv.get(v.index, FAR), 0.0, 0.0) for i, v in enumerate(f.verts)])


# ----------------------------------------------------------------------------------------------------------------
# piezas
# ----------------------------------------------------------------------------------------------------------------
def build_robe_top(parts, J, find_seam, P):
    """Tunica: torso (sin cuello) + brazos desplazados, cortados en la cintura y a media manga; campana."""
    bm = body_region_bmesh([parts["Torso"], parts["Arms"]])
    zc = P["robe_top_bottom"]
    cut_by_seam(bm, lambda b: find_seam(b, (0, 0, 1), (0, 0, zc), zc,
                                        lambda c: abs(c.x) < 0.3 and zc - 0.12 < c.z < zc + 0.15), (0, 0, 1.45))
    for sx in (1, -1):
        xc = P["sleeve_cut_x"]
        cut_by_seam(bm, lambda b, sx=sx: find_seam(b, (sx, 0, 0), (sx * xc, -0.01, J["wrist.L"][0][2]), xc,
                                                   lambda c, sx=sx: c.x * sx > xc - 0.08),
                    (0, 0, 1.45))
    bm.normal_update()
    off = P["robe_off"]
    for v in bm.verts:
        v.co = v.co + v.normal * off
    bnd = {v.index for v in bm.verts if v.is_boundary}
    for _ in range(2):
        bmesh.ops.smooth_vert(bm, verts=[v for v in bm.verts if v.index not in bnd], factor=0.5,
                              use_axis_x=True, use_axis_y=True, use_axis_z=True)
    bm.normal_update()
    tree, _ = body_bvh([parts["Torso"], parts["Arms"], parts["Head"]])
    push_out(bm, tree, off * 0.8)
    # mangas acampanadas: 3 anillos + dobladillo vuelto
    loops = [lp for lp in boundary_loops(bm) if abs(sum(v.co.x for v in lp) / len(lp)) > 0.3]
    hems = []
    for lp in loops:
        sx = 1.0 if lp[0].co.x > 0 else -1.0
        c = sum((v.co for v in lp), Vector()) / len(lp)
        sc = (1.0, 1.28, 1.6, 1.82, 1.76)
        dx = (0.0, 0.03, 0.06, 0.085, 0.07)

        def rf(k, p, i, c=c, sx=sx):
            d = p - c
            s = sc[k]
            drop = (0.012 * k + (0.02 * k if d.z < 0 else 0.0)) if k < 4 else 0.02 * 3 + 0.03
            return Vector((c.x + sx * dx[k] + d.x * 0.3, c.y + d.y * s, c.z + d.z * s - drop))
        rings = extrude_rings(bm, lp, rf, 4)
        hems.append(rings[3])
    piece = Piece("Robe_Top")
    add_bm_with_hem(piece, bm, LINEN, hems)
    # colgante: cordon desde debajo de la esclavina y cristal azul palido
    tree2 = BVHTree.FromBMesh(bm)
    hit = tree2.ray_cast(Vector((0, -0.5, P["pendant_z"])), Vector((0, 1, 0)))
    y_front = hit[0].y - 0.006 if hit[0] else -0.14
    tip = Vector((0, y_front - 0.004, P["pendant_z"]))
    for sx in (1, -1):
        a = Vector((sx * 0.05, 0, P["pendant_z"] + 0.085))
        h2 = tree2.ray_cast(Vector((a.x, -0.5, a.z)), Vector((0, 1, 0)))
        a.y = (h2[0].y if h2[0] else y_front) - 0.004
        pts = [a.lerp(tip + Vector((0, 0, 0.02)), t) for t in (0.0, 0.5, 1.0)]
        prev = None
        for k, p in enumerate(pts):
            w = Vector((0, 0, 0.0016)).cross(Vector((0, 1, 0))).normalized() * 0.0015
            i1, i2 = piece.add_vert(p - w), piece.add_vert(p + w)
            if prev:
                piece.add_face([prev[0], prev[1], i2, i1], CORD)
            prev = (i1, i2)
    cap_c = tip + Vector((0, 0, 0.018))
    lathe(piece, lambda k: METAL, [cap_c + Vector((0, 0, 0.006)), cap_c], [0.004, 0.0065], 6,
          (Vector((1, 0, 0)), Vector((0, 1, 0))), close_bottom=False, close_top=True)
    # cristal: bipiramide hexagonal (3,2 cm) apuntando hacia abajo
    ring = []
    for j in range(6):
        a = 2 * math.pi * j / 6
        ring.append(piece.add_vert(tip + Vector((0.0075 * math.cos(a), 0.0075 * math.sin(a) * 0.8, 0.002))))
    up_i = piece.add_vert(tip + Vector((0, 0, 0.016)))
    dn_i = piece.add_vert(tip + Vector((0, 0, -0.016)))
    for j in range(6):
        j2 = (j + 1) % 6
        piece.add_face([ring[j], ring[j2], up_i], CRYSTAL)
        piece.add_face([ring[j2], ring[j], dn_i], CRYSTAL)
    bm.free()
    return piece


def build_skirt(parts, J, P):
    """Falda en anillos desde la cintura al dobladillo; abertura lateral (x = 0) por debajo de P['slit_z']."""
    N, K = 32, 13
    z_top, z_hem, z_slit = P["skirt_top"], P["hem_z"], P["slit_z"]
    cen = Vector((0, P["body_cy"], 0))
    pts = [o.matrix_world @ v.co for k in ("Torso", "Legs") for o in [parts[k]] for v in o.data.vertices]
    zs = [z_top + (z_hem - z_top) * (k / (K - 1)) for k in range(K)]
    radii = []
    prev = None
    for k, z in enumerate(zs):
        band = [p for p in pts if abs(p.z - z) < 0.035]
        r = section_radius(band, Vector((cen.x, cen.y, z)), N) if band else [0.12] * N
        t = k / (K - 1)
        r = [x + P["skirt_margin"] + P["skirt_flare"] * (t ** 1.4) * (0.55 + 0.45 * abs(math.cos(2 * math.pi * j / N)))
             for j, x in enumerate(r)]
        if prev:
            r = [max(a, b * 0.995) for a, b in zip(r, prev)]
        radii.append(r)
        prev = r
    for _ in range(2):         # suavizado vertical
        radii = [radii[0]] + [[(radii[k - 1][j] + 2 * radii[k][j] + radii[k + 1][j]) / 4 for j in range(N)]
                              for k in range(1, K - 1)] + [radii[-1]]
    # anillo del dobladillo vuelto (por dentro, 3,5 cm)
    rings_z = [z_hem + 0.035] + zs[::-1]                       # de abajo arriba: interior, dobladillo, ..., cintura
    rings_r = [[x * 0.975 for x in radii[-1]]] + radii[::-1]
    piece = Piece("Robe_Skirt")
    vid = {}
    split = {0, N // 2}

    def vert(k, j, side):
        z = rings_z[k]
        is_split = z < z_slit - 1e-6 and j in split
        key = (k, j, side if is_split else 0)
        if key not in vid:
            a = 2 * math.pi * j / N
            r = rings_r[k][j]
            p = Vector((cen.x + r * math.cos(a), cen.y + r * math.sin(a), z))
            if is_split:          # la abertura se abre en V hacia el dobladillo
                gap = 0.012 * min(1.0, (z_slit - z) / 0.25)
                p.y += -gap if side == 1 else gap
            vid[key] = piece.add_vert(p)
        return vid[key]
    circ = [sum(math.hypot(rings_r[k][j] * math.cos(2 * math.pi * j / N) - rings_r[k][(j + 1) % N] *
                           math.cos(2 * math.pi * (j + 1) / N),
                           rings_r[k][j] * math.sin(2 * math.pi * j / N) - rings_r[k][(j + 1) % N] *
                           math.sin(2 * math.pi * (j + 1) / N)) for j in range(N)) for k in range(len(rings_z))]
    pvs = [abs(z - z_hem) for z in rings_z]
    pvs[0] = 0.035
    for k in range(len(rings_z) - 1):
        for j in range(N):
            side = 1 if j >= N // 2 else 2              # 1 delantero (y < 0), 2 trasero
            j2 = (j + 1) % N
            idx = [vert(k, j, side), vert(k, j2, side), vert(k + 1, j2, side), vert(k + 1, j, side)]
            u = [circ[kk] * jj / N for kk, jj in ((k, j), (k, j + 1), (k + 1, j + 1), (k + 1, j))]
            v = [pvs[k], pvs[k], pvs[k + 1], pvs[k + 1]]
            piece.add_face(idx, LINEN, [(u[i], v[i], 0.0, 0.0) for i in range(4)])
    return piece, {"anillos": len(rings_z), "lados": N, "radios_cintura": [round(x, 3) for x in radii[0][::8]],
                   "radios_dobladillo": [round(x, 3) for x in radii[-1][::8]]}, (cen, zs, radii)


def build_hood(parts, robe_obj, J, P):
    """Esclavina (marcha sobre la tunica desde el cuello) + capucha bajada sobre la espalda."""
    tree, _ = body_bvh([robe_obj, parts["Torso"], parts["Arms"]])
    N, M = 32, 6
    head_pts = [parts["Head"].matrix_world @ v.co for v in parts["Head"].data.vertices]
    zc = P["collar_z"]
    neck = [p for p in head_pts + [parts["Torso"].matrix_world @ v.co for v in parts["Torso"].data.vertices]
            if abs(p.z - zc) < 0.02]
    cen = Vector((0, sum(p.y for p in neck) / len(neck), zc))
    rn = section_radius(neck, cen, N)
    collar = []
    for j in range(N):
        a = 2 * math.pi * j / N
        collar.append(Vector((cen.x + (rn[j] + 0.022) * math.cos(a), cen.y + (rn[j] + 0.022) * math.sin(a), zc)))
    rows = [collar]
    cur = [p.copy() for p in collar]
    for m in range(M):
        nxt = []
        for j in range(N):
            a = 2 * math.pi * j / N
            Lj = P["cape_len_side"] * abs(math.cos(a)) + P["cape_len_front"] * abs(math.sin(a))
            step = Lj / M
            radial = Vector((math.cos(a), math.sin(a), 0))
            loc, nrm, _i, _d = tree.find_nearest(cur[j])
            d = (radial * 0.7 + Vector((0, 0, -1)) * 0.3)
            d = (d - nrm * d.dot(nrm)).normalized()
            p = cur[j] + d * step
            loc, nrm, _i, _d = tree.find_nearest(p)
            p = loc + nrm * P["cape_off"]
            nxt.append(p)
        rows.append(nxt)
        cur = nxt
    piece = Piece("Hood")
    ids = [[piece.add_vert(p) for p in row] for row in rows]
    lens = []   # pv: distancia al borde exterior (ultima fila) por columna
    for j in range(N):
        acc, col_l = 0.0, [0.0]
        for r in range(len(rows) - 1, 0, -1):
            acc += (rows[r][j] - rows[r - 1][j]).length
            col_l.append(acc)
        lens.append(col_l[::-1])
    circ = [sum((row[(j + 1) % N] - row[j]).length for j in range(N)) for row in rows]
    for r in range(len(rows) - 1):
        for j in range(N):
            j2 = (j + 1) % N
            idx = [ids[r][j], ids[r][j2], ids[r + 1][j2], ids[r + 1][j]]
            u = [circ[rr] * jj / N for rr, jj in ((r, j), (r, j + 1), (r + 1, j + 1), (r + 1, j))]
            v = [lens[j][r], lens[j2][r], lens[j2][r + 1], lens[j][r + 1]]
            piece.add_face(idx, WOOL, [(u[i], v[i], 0.0, 0.0) for i in range(4)])
    # capucha bajada: cuello vuelto alrededor del cuello que en la espalda se hace bolsa (sube, se dobla hacia fuera
    # y cae sobre la esclavina); delante queda como un rollo bajo
    cape_me = bpy.data.meshes.new("TMP_cape")
    cape_me.from_pydata([tuple(v) for v in piece.verts], [], [f[0] for f in piece.faces])
    cbm = bmesh.new()
    cbm.from_mesh(cape_me)
    bpy.data.meshes.remove(cape_me)
    ctree = BVHTree.FromBMesh(cbm)
    cbm.free()
    hb = P["hood_bulge"]
    hrows = []
    for k in range(5):
        row = []
        for j in range(N):
            a = 2 * math.pi * j / N
            w = max(0.0, math.sin(a)) ** 1.3                     # 1 en la espalda (+Y), 0 delante
            radial = Vector((math.cos(a), math.sin(a), 0))
            base = collar[j]
            if k == 0:
                p = base + radial * 0.004 + Vector((0, 0, 0.004))
            elif k == 1:
                p = base + radial * (0.016 + 0.012 * w) + Vector((0, 0, 0.018 + 0.03 * w))
            elif k == 2:
                p = base + radial * (0.036 + 0.05 * w) + Vector((0, 0, 0.01 + 0.035 * w))
            elif k == 3:
                p = base + radial * (0.05 + hb * 1.5 * w) + Vector((0, 0, -0.025 - 0.06 * w))
            else:
                p = base + radial * (0.045 + hb * 1.3 * w) + Vector((0, 0, -0.05 - 0.17 * w))
            if k >= 3:
                loc, nrm, _i, _d = ctree.find_nearest(p)
                if loc is not None and (p - loc).dot(nrm) < 0.012 + 0.03 * w * (k == 3):
                    p = loc + nrm * (0.012 + 0.03 * w * (k == 3))
            row.append(p)
        hrows.append(row)
    hid = [[piece.add_vert(p) for p in row] for row in hrows]
    hlen = [0.0]
    for k in range(1, 5):
        hlen.append(hlen[-1] + sum((hrows[k][j] - hrows[k - 1][j]).length for j in range(N)) / N)
    hc = [sum((row[(j + 1) % N] - row[j]).length for j in range(N)) for row in hrows]
    for k in range(4):
        for j in range(N):
            j2 = (j + 1) % N
            idx = [hid[k][j], hid[k][j2], hid[k + 1][j2], hid[k + 1][j]]
            u = [hc[kk] * jj / N for kk, jj in ((k, j), (k, j + 1), (k + 1, j + 1), (k + 1, j))]
            v = [hlen[4] - hlen[kk] for kk in (k, k, k + 1, k + 1)]
            piece.add_face(idx, WOOL, [(u[i], v[i] + 0.2, 0.0, 0.0) for i in range(4)])
    return piece, {"filas": len(rows), "lados": N}


def build_belt(parts, skirt_data, P):
    cen, zs, radii = skirt_data
    N = 24
    zb, hb, th = P["belt_z"], P["belt_h"], 0.006

    def r_at(z, j):
        for k in range(len(zs) - 1):
            if zs[k] >= z >= zs[k + 1]:
                t = (zs[k] - z) / (zs[k] - zs[k + 1])
                return radii[k][j * 32 // N] * (1 - t) + radii[k + 1][j * 32 // N] * t
        return radii[0][j * 32 // N]
    piece = Piece("Belt_Pouches")
    prof = [(zb + hb / 2, th), (zb - hb / 2, th), (zb - hb / 2, 0.0), (zb + hb / 2, 0.0)]
    rings = []
    for z, dr in prof:
        ring = []
        for j in range(N):
            a = 2 * math.pi * j / N
            r = max(r_at(zb + hb / 2, j), r_at(zb - hb / 2, j)) + 0.004 + dr
            ring.append(piece.add_vert(Vector((cen.x + r * math.cos(a), cen.y + r * math.sin(a), z))))
        rings.append(ring)
    for k in range(4):
        k2 = (k + 1) % 4
        for j in range(N):
            j2 = (j + 1) % N
            piece.add_face([rings[k][j], rings[k][j2], rings[k2][j2], rings[k2][j]], LEATHER,
                           [(0.16 * jj, 0.01 * kk, 0.0, 0.0) for jj, kk in ((j, k), (j + 1, k), (j + 1, k2), (j, k2))])

    def belt_point(ang, z, out=0.0):
        j = int(round(ang / (2 * math.pi) * N)) % N
        r = max(r_at(zb + hb / 2, j), r_at(zb - hb / 2, j)) + 0.004 + th + out
        return Vector((cen.x + r * math.cos(ang), cen.y + r * math.sin(ang), z))

    def skirt_out(ang, z):
        j = int(round(ang / (2 * math.pi) * 32)) % 32
        k = min(range(len(zs)), key=lambda kk: abs(zs[kk] - z))
        return radii[k][j]

    def box(c, ux, uy, uz, cls):
        vs = [piece.add_vert(c + ux * sx + uy * sy + uz * sz) for sz in (-1, 1) for sy in (-1, 1) for sx in (-1, 1)]
        for f in ((0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)):
            piece.add_face([vs[i] for i in f], cls)
    # hebilla (delante, -Y) y punta del cinturon
    a_b = 1.5 * math.pi
    bc = belt_point(a_b, zb, 0.003)
    box(bc, Vector((0.026, 0, 0)), Vector((0, 0.0035, 0)), Vector((0, 0, hb / 2 + 0.006)), METAL)
    tip0 = belt_point(a_b + 0.18, zb - hb / 2, 0.004)
    t1 = Vector((tip0.x, tip0.y - 0.004, tip0.z - 0.075))
    w = Vector((0.016, 0, 0))
    i0, i1 = piece.add_vert(tip0 - w), piece.add_vert(tip0 + w)
    i2, i3 = piece.add_vert(t1 + w * 0.8), piece.add_vert(t1 - w * 0.8)
    piece.add_face([i0, i1, i2, i3], LEATHER)
    # bolsitas de hierbas: 3 (delante a la izquierda, cadera izquierda, delante a la derecha)
    up = Vector((0, 0, 1))
    pouches = []
    for ang, s in ((math.radians(305), 1.0), (math.radians(355), 0.9), (math.radians(222), 0.85)):
        zc = zb - hb / 2 - 0.055 * s
        rad = Vector((math.cos(ang), math.sin(ang), 0))
        tang = up.cross(rad).normalized()
        rr = skirt_out(ang, zc) + 0.028 * s
        c = Vector((cen.x + rr * math.cos(ang), cen.y + rr * math.sin(ang), zc))
        hs = [0.05, 0.035, 0.0, -0.035, -0.05]
        rs = [0.022, 0.04, 0.046, 0.04, 0.02]
        lathe(piece, lambda k: LEATHER, [c + up * (h * s) for h in hs], [x * s for x in rs], 8, (tang, rad),
              squash=0.55, close_top=True)
        # solapa
        f0 = c + up * (0.05 * s) + rad * 0.012 * s
        a0, a1 = piece.add_vert(f0 - tang * 0.03 * s), piece.add_vert(f0 + tang * 0.03 * s)
        b1 = piece.add_vert(f0 + tang * 0.026 * s + rad * 0.014 * s - up * 0.04 * s)
        b0 = piece.add_vert(f0 - tang * 0.026 * s + rad * 0.014 * s - up * 0.04 * s)
        piece.add_face([a0, a1, b1, b0], BOOT)
        pouches.append([round(x, 3) for x in c])
    # frascos (cadera derecha): vidrio con tintura y tapon de corcho
    vials = []
    for ang, tilt in ((math.radians(192), 0.06), (math.radians(176), -0.05)):
        zc = zb - hb / 2 - 0.05
        rad = Vector((math.cos(ang), math.sin(ang), 0))
        tang = up.cross(rad).normalized()
        rr = skirt_out(ang, zc) + 0.02
        base = Vector((cen.x + rr * math.cos(ang), cen.y + rr * math.sin(ang), zc - 0.045))
        ax = (up + tang * tilt).normalized()
        hs = [0.0, 0.012, 0.045, 0.058, 0.066, 0.068, 0.082]
        rs = [0.012, 0.016, 0.016, 0.008, 0.006, 0.0068, 0.0062]
        cls = [LIQUID, LIQUID, GLASS, GLASS, GLASS, CORK, CORK]
        lathe(piece, lambda k, cls=cls: cls[k], [base + ax * h for h in hs], rs, 8, (tang, rad), close_top=True)
        vials.append([round(x, 3) for x in base])
    return piece, {"bolsitas": pouches, "frascos": vials}


def boots_piece(parts, J, find_seam, P):
    piece = Piece("Boots")
    tree, _ = body_bvh([parts["Feet"], parts["Legs"]])
    for sx in (1, -1):
        bm = body_region_bmesh([parts["Feet"], parts["Legs"]],
                               lambda f, sx=sx: f.calc_center_median().x * sx > 0)
        zt = P["boot_top"]
        cut_by_seam(bm, lambda b, sx=sx: find_seam(b, (0, 0, 1), (sx * 0.17, 0.0, zt), zt,
                                                   lambda c, sx=sx: c.x * sx > 0.01 and zt - 0.12 < c.z < zt + 0.12),
                    (sx * 0.2, 0.0, 0.03))
        bm.normal_update()
        for v in bm.verts:
            v.co = v.co + v.normal * P["boot_off"]
        bnd = {v.index for v in bm.verts if v.is_boundary}
        for _ in range(6):
            bmesh.ops.smooth_vert(bm, verts=[v for v in bm.verts if v.index not in bnd], factor=0.6,
                                  use_axis_x=True, use_axis_y=True, use_axis_z=True)
        bm.normal_update()
        push_out(bm, tree, P["boot_off"] * 0.7)
        for v in bm.verts:
            if v.co.z < 0.012:
                v.co.z = max(0.0, v.co.z * 0.3)
        loop = boundary_loops(bm)[0]
        c = sum((v.co for v in loop), Vector()) / len(loop)

        def rf(k, p, i, c=c):
            d = p - c
            if k == 1:
                return c + d * 1.12 + Vector((0, 0, 0.012))
            return c + d * 1.22 + Vector((0, 0, -0.045))
        rings = extrude_rings(bm, loop, rf, 2)
        add_bm_with_hem(piece, bm, BOOT, [rings[2]])
        bm.free()
    return piece


def build_bracers(parts, J, P):
    piece = Piece("Bracers")
    tree, _ = body_bvh([parts["Arms"], parts["Hands"]])
    N, K = 8, 6
    for sx in (1, -1):
        xs = [P["bracer_x0"] + (P["bracer_x1"] - P["bracer_x0"]) * k / (K - 1) for k in range(K)]
        rings = []
        for k, x in enumerate(xs):
            c = Vector((sx * x, J["wrist.L"][0][1], J["wrist.L"][0][2]))
            r = []
            for j in range(N):
                a = 2 * math.pi * j / N
                d = Vector((0, math.cos(a), math.sin(a)))
                hit = tree.ray_cast(c + d * 0.2, -d, 0.2)
                r.append((0.2 - hit[3]) if hit[0] is not None else 0.03)
            r = [(r[j - 1] + 2 * r[j] + r[(j + 1) % N]) / 4 for j in range(N)]
            pad = P["bracer_off"] + (0.003 if k in (0, K - 1) else 0.0)
            ring = []
            for j in range(N):
                a = 2 * math.pi * j / N
                ring.append(piece.add_vert(Vector((sx * x, c.y + (r[j] + pad) * math.cos(a),
                                                   c.z + (r[j] + pad) * math.sin(a)))))
            rings.append(ring)
        for k in range(K - 1):
            for j in range(N):
                j2 = (j + 1) % N
                idx = [rings[k][j], rings[k][j2], rings[k + 1][j2], rings[k + 1][j]]
                if sx < 0:
                    idx = idx[::-1]
                piece.add_face(idx, WRAP, [(0.02 * jj, 0.04 * kk, 0.0, 0.0)
                                           for jj, kk in ((j, k), (j + 1, k), (j + 1, k + 1), (j, k + 1))])
    return piece


def build_hair(parts, eyes, J, P, others):
    """Casquete sobre el cuero cabelludo (sin tocar las orejas) + mechones hacia atras + trenza."""
    head = parts["Head"]
    me = head.data
    eg = head.vertex_groups.get("ears")
    ear = [v.co for v in me.vertices if eg and any(e.group == eg.index and e.weight > 0.3 for e in v.groups)]
    from mathutils.kdtree import KDTree
    kd = KDTree(len(ear))
    for i, c in enumerate(ear):
        kd.insert(c, i)
    kd.balance()
    cy = J["head"][0][1] + 0.02
    brow = P["eye_z"] + 0.012

    def hairline(phi):
        keys = [(0, brow + 0.062), (35, brow + 0.052), (70, 1.778), (100, 1.772), (130, 1.712), (160, 1.672),
                (180, 1.665)]
        a = abs(math.degrees(phi))
        for (a0, z0), (a1, z1) in zip(keys, keys[1:]):
            if a0 <= a <= a1:
                t = (a - a0) / (a1 - a0)
                return z0 + (z1 - z0) * t
        return keys[-1][1]

    def inside(co):
        phi = math.atan2(co.x, -(co.y - cy))
        return co.z > hairline(phi) and kd.find(co)[2] > 0.018 and co.z > J["neck03"][0][2] - 0.02

    bm = bmesh.new()
    bm.from_mesh(me)
    keep = [f for f in bm.faces if all(inside(v.co) for v in f.verts)]
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if f not in set(keep)], context="FACES")
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context="VERTS")
    # componente mayor
    bm.faces.ensure_lookup_table()
    comp, n = {}, 0
    for f0 in bm.faces:
        if f0.index in comp:
            continue
        st = [f0]
        comp[f0.index] = n
        while st:
            f = st.pop()
            for e in f.edges:
                for g in e.link_faces:
                    if g.index not in comp:
                        comp[g.index] = n
                        st.append(g)
        n += 1
    from collections import Counter
    big = Counter(comp.values()).most_common(1)[0][0]
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if comp[f.index] != big], context="FACES")
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context="VERTS")
    bm.normal_update()
    top = max(v.co.z for v in bm.verts)
    for v in bm.verts:
        t = max(0.0, min(1.0, (v.co.z - 1.70) / (top - 1.70)))
        v.co = v.co + v.normal * (P["cap_off"] + 0.006 * t)
    bm.verts.index_update()
    loops = boundary_loops(bm)
    pu_b, pv_b = hem_coords(bm, loops)
    piece = Piece("Hair_Elf")
    base = len(piece.verts)
    for v in bm.verts:
        piece.verts.append(v.co.copy())
    for f in bm.faces:
        at = []
        for v in f.verts:
            phi = math.atan2(v.co.x, -(v.co.y - cy))
            at.append((phi * 0.09, pv_b.get(v.index, FAR), 0.0, 0.0))
        us = wrap_fix([a[0] for a in at], 2 * math.pi * 0.09)
        piece.add_face([base + v.index for v in f.verts], HAIRCAP,
                       [(us[i], at[i][1], at[i][2], at[i][3]) for i in range(len(at))])
    cap_tree = BVHTree.FromBMesh(bm)
    back_y = max(v.co.y for v in bm.verts if abs(v.co.x) < 0.02 and abs(v.co.z - P["gather_z"]) < 0.03)
    G = Vector((0, back_y + 0.006, P["gather_z"]))
    # mechones (cards) desde la linea del pelo hasta el punto de recogida
    bl = max(loops, key=len)
    cards = 0
    starts = []
    for v in bl:
        phi = math.atan2(v.co.x, -(v.co.y - cy))
        if abs(math.degrees(phi)) < 112:
            starts.append((phi, v.co.copy()))
    starts.sort(key=lambda t: t[0])
    picks = [starts[int(i * (len(starts) - 1) / (P["n_cards"] - 1))] for i in range(P["n_cards"])]
    for li, (phi, s0) in enumerate(picks):
        layer = 1 + (li % 2) * 0.6
        segs = 6
        prev = None
        L = 0.0
        pts = []
        for k in range(segs + 1):
            t = 0.06 + 0.94 * k / segs                           # la raiz un poco por detras de la linea del pelo
            p = s0.lerp(G, t)
            loc, nrm, _i, _d = cap_tree.find_nearest(p)
            lift = (0.005 + 0.004 * math.sin(math.pi * t)) * layer
            p = loc + nrm * lift if t < 0.97 else G + Vector((0, 0.004 * layer, 0))
            pts.append((p, nrm))
        for k, (p, nrm) in enumerate(pts):
            if k:
                L += (p - pts[k - 1][0]).length
            d = (pts[min(k + 1, segs)][0] - pts[max(k - 1, 0)][0]).normalized()
            side = nrm.cross(d).normalized()
            wdt = (0.04 - 0.022 * (k / segs)) * (0.9 if li % 2 else 1.0)
            i0, i1 = piece.add_vert(p - side * wdt / 2), piece.add_vert(p + side * wdt / 2)
            if prev:
                piece.add_face([prev[0], prev[1], i1, i0], HAIR,
                               [(li * 0.05, prev[2], 0.0, prev[3]), (li * 0.05 + 0.03, prev[2], 1.0, prev[3]),
                                (li * 0.05 + 0.03, L, 1.0, k / segs), (li * 0.05, L, 0.0, k / segs)])
            prev = (i0, i1, L, k / segs)
        cards += 1
    # trenza: tubo de 6 lados desde el punto de recogida por la espalda
    otree, _ = body_bvh(others)
    path = [G]
    for z in P["braid_z"]:
        ys = []
        for x in (-0.03, 0.0, 0.03):
            hit = otree.ray_cast(Vector((x, 0.8, z)), Vector((0, -1, 0)))
            if hit[0] is not None:
                ys.append(hit[0].y)
        path.append(Vector((0, (max(ys) if ys else 0.15) + 0.02, z)))
    # suavizado del camino
    for _ in range(2):
        path = [path[0]] + [(path[i - 1] + 2 * path[i] + path[i + 1]) / 4 for i in range(1, len(path) - 1)] + [path[-1]]
    n6 = 6
    rads = [0.024 - 0.011 * (i / (len(path) - 1)) for i in range(len(path))]
    rings = []
    L = 0.0
    Ls = [0.0]
    for i in range(1, len(path)):
        Ls.append(Ls[-1] + (path[i] - path[i - 1]).length)
    for i, (c, r) in enumerate(zip(path, rads)):
        d = (path[min(i + 1, len(path) - 1)] - path[max(i - 1, 0)]).normalized()
        u = Vector((1, 0, 0))
        w = d.cross(u).normalized()
        u = w.cross(d).normalized()
        ring = [piece.add_vert(c + u * (r * math.cos(2 * math.pi * j / n6)) + w * (r * 0.8 * math.sin(2 * math.pi * j / n6)))
                for j in range(n6)]
        rings.append(ring)
    for i in range(len(rings) - 1):
        for j in range(n6):
            j2 = (j + 1) % n6
            piece.add_face([rings[i][j], rings[i + 1][j], rings[i + 1][j2], rings[i][j2]], BRAID,
                           [(0.012 * jj, Ls[ii], jj / n6, 0.0) for ii, jj in ((i, j), (i + 1, j), (i + 1, j + 1),
                                                                                  (i, j + 1))])
    # atadura (cuero) y punta suelta (dos cards cruzadas)
    end, dend = path[-1], (path[-1] - path[-2]).normalized()
    lathe(piece, lambda k: CORD, [end - dend * 0.004, end + dend * 0.012], [rads[-1] + 0.003, rads[-1] + 0.003], 6,
          (Vector((1, 0, 0)), dend.cross(Vector((1, 0, 0))).normalized()), close_bottom=False)
    for side in (Vector((1, 0, 0)), Vector((0, 1, 0)).cross(dend).normalized().cross(dend).normalized()):
        a = end + dend * 0.01
        pts = [a + dend * (0.035 * k) for k in range(3)]
        prev = None
        for k, p in enumerate(pts):
            wd = 0.026 - 0.008 * k
            i0, i1 = piece.add_vert(p - side * wd / 2), piece.add_vert(p + side * wd / 2)
            if prev:
                piece.add_face([prev[0], prev[1], i1, i0], HAIR,
                               [(0.7, 0.035 * (k - 1), 0.0, (k - 1) / 2), (0.73, 0.035 * (k - 1), 1.0, (k - 1) / 2),
                                (0.73, 0.035 * k, 1.0, k / 2), (0.7, 0.035 * k, 0.0, k / 2)])
            prev = (i0, i1)
    bm.free()
    return piece, {"mechones": cards, "punto_recogida": [round(x, 3) for x in G], "largo_trenza_m": round(Ls[-1], 3)}
