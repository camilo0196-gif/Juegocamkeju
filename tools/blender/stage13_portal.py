"""
CONCORDIA - etapa 13: el Portal y sus elementos (coleccion BLD_PORTAL).

Referencias: Stonehenge (trilito: dos postes enormes y un dintel, bloques erosionados) y Porta Nigra de Treveris
(masa oscura y pesada, desgaste). Runas inventadas: trazos simples y grandes.

  PORTAL_Arch          2 pilares 2.2 x 2.2 m de 3 bloques + dintel curvo (trasdos recto a +12 m, intrados de +10.0
                       en los pilares a +11.1 en la clave); hueco libre 8 m. Erosion por desplazamiento (aristas
                       desconchadas), grietas y runas talladas 3 cm (Boolean). Lineas de runas emisivas #8FD0FF a 1.2
                       por las caras N y S de los pilares hasta el suelo (y bajando por el pedestal hasta el atrio).
  PORTAL_Veil          plano curvo 8 x 11 m, MAT_Portal_Veil (emision 3.0, alpha 0.6), UV 0..1, sin colision.
  PORTAL_Runestone_NN  7 menhires de 0.8 m x 0.6 m en MARKER_Runestone_NN, runa central emisiva 1.0.
  PORTAL_DescentPedestal_NN  21 pedestales de 1.2 x 0.5 m con placa de 0.8 m (numero de piso en Godot).
  PORTAL_AtrioRunes    linea de runas azules en el borde de la plataforma (r 14.85).
  *-colonly            cilindros: pedestal del Portal, pilares, piedras y pedestales. Nada en el hueco del arco.
Origen de cada pieza: centro de su base, a la cota del suelo; +Y = frente (hacia la plaza o el Norte).
"""

import math
import random

import bmesh
import bpy
from mathutils import Matrix, Vector
from mathutils.noise import fractal, noise

SEED = 1313
GLOW = "#8FD0FF"
STONE = "MAT_Rock_Gray"
PLATE = "MAT_Iron_Black"
Z_TOP = 8.9                       # cara superior del pedestal existente (MARKER_Portal_Center)
Z_STEP = 8.75                     # escalon del pedestal (r 6.35): apoyo de los pilares
Z_ATRIO = 8.6
CLEAR = 8.0
PIER = 2.2
PIER_X = CLEAR / 2 + PIER / 2     # 5.1
H_ARCH = 12.0
Z_SPRING = 10.0                   # cara superior de los pilares (sobre Z_TOP)
Z_KEY = 11.1                      # intrados en la clave
DEPTH = 2.2

# runas inventadas: trazos en un cuadrado unidad (x, z) en [-0.5, 0.5]
GLYPHS = [
    [((0, -.5), (0, .5)), ((0, .5), (.32, .2)), ((0, .12), (.32, -.18))],
    [((0, .5), (.32, 0)), ((.32, 0), (0, -.5)), ((0, -.5), (-.32, 0)), ((-.32, 0), (0, .5))],
    [((0, -.5), (0, .5)), ((-.32, .18), (0, .5)), ((.32, .18), (0, .5))],
    [((-.3, -.5), (.3, .5)), ((.3, -.5), (-.3, .5)), ((0, -.5), (0, .5))],
    [((-.25, -.5), (-.25, .5)), ((.25, -.5), (.25, .5)), ((-.25, .5), (.25, -.5))],
    [((0, -.5), (0, .5)), ((-.3, -.1), (.3, -.1)), ((-.3, .25), (.3, .25))],
    [((-.3, .5), (-.3, -.1)), ((.3, .5), (.3, -.1)), ((-.3, -.1), (.3, -.1)), ((0, -.5), (0, .5))],
    [((-.3, .5), (.3, .5)), ((.3, .5), (-.3, -.5)), ((-.3, -.5), (.3, -.5))],
    [((-.3, .5), (0, .1)), ((.3, .5), (0, .1)), ((0, .1), (0, -.5)), ((-.25, -.25), (.25, -.25))],
    [((-.3, .45), (.3, .2)), ((.3, .2), (-.3, -.05)), ((-.3, -.05), (.3, -.3)), ((0, .5), (0, -.5))],
]


# ---------------------------------------------------------------------------
# materiales
# ---------------------------------------------------------------------------
def _lin(hexs):
    h = hexs.lstrip("#")
    c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return [x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c]


def glow_material(name, strength):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    c = _lin(GLOW)
    b.inputs["Base Color"].default_value = (*c, 1)
    b.inputs["Roughness"].default_value = 0.4
    b.inputs["Emission Color"].default_value = (*c, 1)
    b.inputs["Emission Strength"].default_value = strength
    m["emission_strength"] = strength
    m["note"] = f"runa {GLOW}, emision {strength}"
    return m


def veil_material():
    m = bpy.data.materials.get("MAT_Portal_Veil") or bpy.data.materials.new("MAT_Portal_Veil")
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    c = _lin(GLOW)
    b.inputs["Base Color"].default_value = (*c, 1)
    b.inputs["Roughness"].default_value = 0.15
    b.inputs["Emission Color"].default_value = (*c, 1)
    b.inputs["Emission Strength"].default_value = 3.0
    b.inputs["Alpha"].default_value = 0.6
    m.use_backface_culling = False
    try:
        m.surface_render_method = "BLENDED"
    except AttributeError:
        m.blend_method = "BLEND"
    m["note"] = "velo del Portal: azul palido #8FD0FF, emision 3.0, alpha 0.6; UV 0..1 para animar en Godot"
    return m


def ensure_materials():
    return {"MAT_Portal_Veil": veil_material().name, "MAT_Rune_Glow_12": glow_material("MAT_Rune_Glow_12", 1.2).name,
            "MAT_Rune_Glow_10": glow_material("MAT_Rune_Glow_10", 1.0).name}


# ---------------------------------------------------------------------------
# utilidades
# ---------------------------------------------------------------------------
class Mesh:
    def __init__(self):
        self.bm = bmesh.new()
        self.mats = []

    def mi(self, n):
        if n not in self.mats:
            self.mats.append(n)
        return self.mats.index(n)

    def quad_grid(self, origin, du, dv, nu, nv, mat, zfun=None):
        """Rejilla de nu x nv quads: P(u,v) = origin + u*du + v*dv (u, v en [0,1]); zfun(p, u, v) la deforma."""
        o, du, dv = Vector(origin), Vector(du), Vector(dv)
        vs = []
        for j in range(nv + 1):
            row = []
            for i in range(nu + 1):
                p = o + du * (i / nu) + dv * (j / nv)
                if zfun:
                    p = zfun(p, i / nu, j / nv)
                row.append(self.bm.verts.new(p))
            vs.append(row)
        k = self.mi(mat)
        for j in range(nv):
            for i in range(nu):
                f = self.bm.faces.new((vs[j][i], vs[j][i + 1], vs[j + 1][i + 1], vs[j + 1][i]))
                f.material_index = k
        return vs

    def to_object(self, name, col):
        bmesh.ops.remove_doubles(self.bm, verts=self.bm.verts[:], dist=1e-4)
        bmesh.ops.recalc_face_normals(self.bm, faces=self.bm.faces[:])
        me = bpy.data.meshes.new(name)
        self.bm.to_mesh(me)
        self.bm.free()
        for n in self.mats:
            me.materials.append(bpy.data.materials[n])
        o = bpy.data.objects.new(name, me)
        col.objects.link(o)
        return o


def box_grid(m, x0, x1, y0, y1, z0, z1, nx, ny, nz, mat, faces="xyz"):
    """Caja subdividida (para erosionar). faces: que pares se crean ('x', 'y', 'z')."""
    if "y" in faces:
        m.quad_grid((x0, y0, z0), (x1 - x0, 0, 0), (0, 0, z1 - z0), nx, nz, mat)
        m.quad_grid((x1, y1, z0), (x0 - x1, 0, 0), (0, 0, z1 - z0), nx, nz, mat)
    if "x" in faces:
        m.quad_grid((x1, y0, z0), (0, y1 - y0, 0), (0, 0, z1 - z0), ny, nz, mat)
        m.quad_grid((x0, y1, z0), (0, y0 - y1, 0), (0, 0, z1 - z0), ny, nz, mat)
    if "z" in faces:
        m.quad_grid((x0, y0, z1), (x1 - x0, 0, 0), (0, y1 - y0, 0), nx, ny, mat)
        m.quad_grid((x0, y1, z0), (x1 - x0, 0, 0), (0, y0 - y1, 0), nx, ny, mat)


def erode(obj, box_dist, amp_face=0.012, amp_edge=0.085, edge_w=0.3, seed=0):
    """Erosion: ruido suave en las caras + desconchado de aristas (hacia dentro por la normal del vertice).
    box_dist(p) -> distancia del punto a la arista mas cercana de su bloque."""
    me = obj.data
    me.update()
    off = Vector((seed * 13.1, seed * 7.7, seed * 3.3))
    bm = bmesh.new()
    bm.from_mesh(me)
    bm.normal_update()
    for v in bm.verts:
        p = v.co
        n = v.normal
        f = fractal(p * 0.9 + off, 0.5, 2.0, 3)
        d = amp_face * f
        e = box_dist(p)
        if e < edge_w:
            k = (1 - e / edge_w) ** 1.6
            chip = 0.5 + 0.5 * noise(p * 2.3 + off)
            d -= amp_edge * k * (0.35 + 0.65 * chip)
        big = noise(p * 0.35 + off * 2)
        if big > 0.55:
            d -= (big - 0.55) * 0.35
        v.co = p + n * d
    bm.to_mesh(me)
    bm.free()


PROBES = {}


def strokes_mesh(name, segs, center, axis_u, axis_v, normal, size, width, depth, out=0.15, jitter=0.0, bvh=None):
    """Prismas de trazo (cortadores) para tallar: un glyph en el plano (u, v) de una cara con normal saliente.
    Devuelve UNA malla por trazo (lista) y guarda en PROBES[malla] su sonda de verificacion."""
    meshes = []
    c = Vector(center)
    u, v, n = Vector(axis_u), Vector(axis_v), Vector(normal)
    for (a, b) in segs:
        pa = c + u * a[0] * size + v * a[1] * size
        pb = c + u * b[0] * size + v * b[1] * size
        d = (pb - pa)
        L = d.length
        if L < 1e-4:
            continue
        t = d.normalized()
        s = n.cross(t).normalized() * (width / 2)
        ext = t * (width / 2)
        corners = [pa - ext - s, pb + ext - s, pb + ext + s, pa - ext + s]
        bm = bmesh.new()
        probes = []
        if jitter:
            corners = [q + Vector((jitter, -jitter * 0.7, jitter * 0.5)) for q in corners]
        if bvh is not None:
            # proyeccion sobre la piedra erosionada: el corte mide 'depth' desde la superficie REAL
            hits = []
            for q in corners + [(pa + pb) / 2]:
                h = bvh.ray_cast(q + n * 0.5, -n, 1.5)
                hits.append(h[0] if h[0] is not None else q)
            base_d = min((h - c).dot(n) for h, c in zip(hits, corners + [(pa + pb) / 2]))
            top_d = max((h - c).dot(n) for h, c in zip(hits, corners + [(pa + pb) / 2]))
            lo = [bm.verts.new(q + n * (base_d - depth)) for q in corners]
            hi = [bm.verts.new(q + n * (top_d + out)) for q in corners]
            probes.append((hits[-1], n.copy(), depth))
        else:
            probes.append(((pa + pb) / 2, n.copy(), depth))
            lo = [bm.verts.new(q - n * depth) for q in corners]
            hi = [bm.verts.new(q + n * out) for q in corners]
        bm.faces.new(lo[::-1])
        bm.faces.new(hi)
        for i in range(4):
            j = (i + 1) % 4
            bm.faces.new((lo[i], lo[j], hi[j], hi[i]))
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
        me = bpy.data.meshes.new(name)
        bm.to_mesh(me)
        bm.free()
        PROBES[me.name] = probes
        meshes.append(me)
    return meshes


def glyph_inlay(m, segs, center, axis_u, axis_v, normal, size, width, mat, lift=0.003, bvh=None):
    """Runa emisiva plana (incrustada) sobre una superficie; con bvh se proyecta cada vertice sobre la piedra."""
    c = Vector(center) + Vector(normal) * lift
    u, v, n = Vector(axis_u), Vector(axis_v), Vector(normal)

    def proj(q):
        if bvh is None:
            return q
        h = bvh.ray_cast(q + n * 0.4, -n, 1.0)
        return (h[0] + n * lift) if h[0] is not None else q
    k = m.mi(mat)
    for (a, b) in segs:
        pa = c + u * a[0] * size + v * a[1] * size
        pb = c + u * b[0] * size + v * b[1] * size
        d = pb - pa
        if d.length < 1e-4:
            continue
        t = d.normalized()
        s = n.cross(t).normalized() * (width / 2)
        ext = t * (width / 2)
        vs = [m.bm.verts.new(proj(q)) for q in (pa - ext - s, pb + ext - s, pb + ext + s, pa - ext + s)]
        f = m.bm.faces.new(vs)
        f.material_index = k
        f.normal_update()
        if f.normal.dot(n) < 0:
            f.normal_flip()


def _bool_once(obj, cutters):
    me = bpy.data.meshes.new(obj.name + "_cutters")
    bm = bmesh.new()
    for cme in cutters:
        bm.from_mesh(cme)
    bm.to_mesh(me)
    bm.free()
    co = bpy.data.objects.new(obj.name + "_cutters", me)
    bpy.context.scene.collection.objects.link(co)
    co.matrix_world = obj.matrix_world
    mod = obj.modifiers.new("runes", "BOOLEAN")
    mod.operation = "DIFFERENCE"
    mod.solver = "FAST"                      # EXACT devuelve malla vacia en bpy sin interfaz (verificado)
    mod.object = co
    dg = bpy.context.evaluated_depsgraph_get()
    new = bpy.data.meshes.new_from_object(obj.evaluated_get(dg))
    obj.modifiers.clear()
    bpy.data.objects.remove(co)
    bpy.data.meshes.remove(me)
    return new


def _probe_ok(me, probes):
    """Cada trazo: desde fuera, el rayo debe entrar al menos 2/3 de la profundidad del corte."""
    from mathutils.bvhtree import BVHTree
    bm = bmesh.new()
    bm.from_mesh(me)
    bvh = BVHTree.FromBMesh(bm)
    bad = 0
    for c, n, depth in probes:
        h = bvh.ray_cast(c + n * 0.3, -n, 1.0)
        if h[0] is None or (c + n * 0.3 - h[0]).length < 0.3 + depth * 0.66:
            bad += 1
    bm.free()
    return bad


BOOL_LOG = []


def _bvh_of(o):
    from mathutils.bvhtree import BVHTree
    bm = bmesh.new()
    bm.from_mesh(o.data)
    t = BVHTree.FromBMesh(bm)
    bm.free()
    return t


def boolean_cut(obj, cutters, regen=None):
    """Boolean DIFFERENCE trazo a trazo (FAST falla con cortadores que se cruzan). Cada trazo se baja 0.7 mm mas
    que el anterior (sin caras coplanarias) y se verifica con su sonda; si no corto, se reintenta desplazado."""
    if not cutters:
        return
    from mathutils import Matrix as _M
    ok = bad = 0
    for k, cme in enumerate(cutters):
        probes = PROBES.get(cme.name, [])
        n = probes[0][1] if probes else Vector((0, 0, 1))
        cme.transform(_M.Translation(-n * 0.0007 * (k % 9)))
        done = False
        for attempt in range(4):
            if attempt:
                cme.transform(_M.Translation(Vector((0.0011, -0.0007, 0.0013)) * attempt))
            new = _bool_once(obj, [cme])
            if probes and _probe_ok(new, probes) > 0 and attempt < 3:
                bpy.data.meshes.remove(new)
                continue
            old = obj.data
            obj.data = new
            new.name = old.name
            bpy.data.meshes.remove(old)
            done = not probes or _probe_ok(new, probes) == 0
            break
        ok += int(done)
        bad += int(not done)
        bpy.data.meshes.remove(cme)
    BOOL_LOG.append({"object": obj.name, "strokes": len(cutters), "cut_ok": ok, "failed": bad})


def tris(o):
    return sum(len(p.vertices) - 2 for p in o.data.polygons)


def cylinder_col(name, r, z0, z1, n, col, loc=(0, 0, 0)):
    bm = bmesh.new()
    lo = [bm.verts.new((r * math.cos(2 * math.pi * i / n), r * math.sin(2 * math.pi * i / n), z0)) for i in range(n)]
    hi = [bm.verts.new((r * math.cos(2 * math.pi * i / n), r * math.sin(2 * math.pi * i / n), z1)) for i in range(n)]
    bm.faces.new(lo[::-1])
    bm.faces.new(hi)
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((lo[i], lo[j], hi[j], hi[i]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new(name, me)
    col.objects.link(o)
    o.location = loc
    o.display_type = "WIRE"
    o.hide_render = True
    return o


def lods(o, col, ratios=(("LOD1", 0.5), ("LOD2", 0.15))):
    out = {}
    for tag, r in ratios:
        lo = bpy.data.objects.new(f"{o.name}_{tag}", o.data.copy())
        lo.data.name = lo.name
        col.objects.link(lo)
        lo.matrix_world = o.matrix_world.copy()
        lo.parent = o.parent
        lo.matrix_parent_inverse = o.matrix_parent_inverse.copy()
        lo.location = o.location.copy()
        lo.rotation_euler = o.rotation_euler.copy()
        m = lo.modifiers.new("lod", "DECIMATE")
        m.decimate_type = "COLLAPSE"
        m.ratio = r
        dg = bpy.context.evaluated_depsgraph_get()
        new = bpy.data.meshes.new_from_object(lo.evaluated_get(dg))
        old = lo.data
        lo.modifiers.clear()
        lo.data = new
        new.name = lo.name
        bpy.data.meshes.remove(old)
        lo.hide_render = True
        out[tag] = tris(lo)
    return out


def uv_metric(o):
    import concordia_buildings as B
    B.box_uv(o)


# ---------------------------------------------------------------------------
# arco
# ---------------------------------------------------------------------------
def z_intrados(x):
    """Intrados del dintel: +10.0 sobre los pilares (|x| >= 4) y arco rebajado hasta +11.1 en la clave."""
    hw = CLEAR / 2
    if abs(x) >= hw:
        return Z_SPRING
    s = Z_KEY - Z_SPRING
    R = (hw * hw + s * s) / (2 * s)
    return Z_SPRING + (math.sqrt(max(0.0, R * R - x * x)) - (R - s))


def block_cutters(j, sx, k, x0, x1, y0, y1, z0, z1, crack, gstart, bvh=None):
    """Cortadores de un bloque de pilar: 2 runas grandes (caras laterales), 2 surcos de linea emisiva (caras N y
    S) y una grieta opcional. j = desplazamiento (m) para reintentar el Boolean."""
    cutters = []
    gi = gstart
    for xf, nxs in ((x0, -1), (x1, 1)):
        zc = (max(z0, 0.0) + z1) / 2
        g = GLYPHS[gi % len(GLYPHS)]
        gi += 1
        cutters.extend(strokes_mesh("c", g, (xf, (y0 + y1) / 2, zc), (0, -nxs, 0), (0, 0, 1), (nxs, 0, 0),
                                    0.95, 0.12, 0.03, jitter=j, bvh=bvh))
    if crack:
        xf, zz, segs = crack
        nxs = -1 if xf == x0 else 1
        cutters.extend(strokes_mesh("k", segs, (xf, (y0 + y1) / 2, zz), (0, -nxs, 0), (0, 0, 1), (nxs, 0, 0),
                                    1.0, 0.025, 0.06, jitter=j, bvh=bvh))
    return cutters


def build_arch(col, rng):
    """Devuelve el objeto PORTAL_Arch (origen en MARKER_Portal_Center, z relativo a Z_TOP)."""
    parts = []
    report = {}
    # bloques de los pilares (3 por pilar, con ligeros descuadres)
    cuts = [0.0, 3.6, 6.9, Z_SPRING]
    blocks = []
    for sx in (-1, 1):
        for k in range(3):
            w = PIER + rng.uniform(-0.05, 0.04)
            dx, dy = rng.uniform(-0.04, 0.04), rng.uniform(-0.04, 0.04)
            z0 = cuts[k] - (Z_TOP - Z_STEP if k == 0 else 0.0)
            z1 = cuts[k + 1]
            cx = sx * PIER_X + dx
            blocks.append((sx, k, cx - w / 2, cx + w / 2, dy - DEPTH / 2, dy + DEPTH / 2, z0, z1))
    objs = []
    for (sx, k, x0, x1, y0, y1, z0, z1) in blocks:
        m = Mesh()
        nz = max(6, int((z1 - z0) / 0.42))
        box_grid(m, x0, x1, y0, y1, z0, z1, 6, 6, nz, STONE)
        o = m.to_object(f"TMP_block_{sx}_{k}", col)

        def bd(p, x0=x0, x1=x1, y0=y0, y1=y1, z0=z0, z1=z1):
            d = sorted((abs(p.x - x0), abs(p.x - x1), abs(p.y - y0), abs(p.y - y1), abs(p.z - z0), abs(p.z - z1)))
            return d[1]
        erode(o, bd, seed=sx * 10 + k)
        objs.append((o, (sx, k, x0, x1, y0, y1, z0, z1)))
    # dintel curvo
    m = Mesh()
    xL, xR = -PIER_X - PIER / 2 - 0.15, PIER_X + PIER / 2 + 0.15
    yF, yB = DEPTH / 2 + 0.1, -DEPTH / 2 - 0.1
    nx = 34

    def front_z(p, u, v):
        zb = z_intrados(p.x)
        return Vector((p.x, p.y, zb + v * (H_ARCH - zb)))
    m.quad_grid((xL, yF, 0), (xR - xL, 0, 0), (0, 0, 1), nx, 5, STONE, front_z)
    m.quad_grid((xR, yB, 0), (xL - xR, 0, 0), (0, 0, 1), nx, 5, STONE, front_z)
    m.quad_grid((xL, yB, H_ARCH), (xR - xL, 0, 0), (0, yF - yB, 0), nx, 5, STONE)
    m.quad_grid((xL, yF, 0), (xR - xL, 0, 0), (0, yB - yF, 0), nx, 5, STONE,
                lambda p, u, v: Vector((p.x, p.y, z_intrados(p.x))))
    for x in (xL, xR):
        m.quad_grid((x, yB if x == xL else yF, Z_SPRING), (0, (yF - yB) * (1 if x == xL else -1), 0),
                    (0, 0, H_ARCH - Z_SPRING), 5, 5, STONE)
    lint = m.to_object("TMP_lintel", col)

    def bdl(p):
        d = sorted((abs(p.x - xL), abs(p.x - xR), abs(p.y - yF), abs(p.y - yB), abs(p.z - H_ARCH),
                    abs(p.z - z_intrados(p.x))))
        return d[1]
    erode(lint, bdl, amp_edge=0.11, seed=77)
    # ---- tallado: runas grandes (caras laterales de los pilares y frentes del dintel), surcos de las lineas
    # emisivas (caras N y S de los pilares) y grietas
    gi = 0
    carved = 0
    for (o, (sx, k, x0, x1, y0, y1, z0, z1)) in objs:
        crack = None
        if rng.random() < 0.7:
            xf = x0 if rng.random() < 0.5 else x1
            zz = rng.uniform(max(z0, 0.3) + 0.4, z1 - 0.6)
            pts = [(rng.uniform(-0.8, 0.8), 0.0)]
            for _ in range(4):
                pts.append((pts[-1][0] + rng.uniform(-0.25, 0.25), pts[-1][1] - rng.uniform(0.18, 0.35)))
            crack = (xf, zz, list(zip(pts[:-1], pts[1:])))
        gstart = gi
        gi += 2

        bvh_o = _bvh_of(o)

        def make(j, sx=sx, k=k, x0=x0, x1=x1, y0=y0, y1=y1, z0=z0, z1=z1, crack=crack, gstart=gstart, bvh_o=bvh_o):
            return block_cutters(j, sx, k, x0, x1, y0, y1, z0, z1, crack, gstart, bvh_o)
        carved += 2
        boolean_cut(o, make(0.0))
    bvh_l = _bvh_of(lint)

    def lint_cutters(j):
        lc = []
        for side, yf, nys in (("N", yF, 1), ("S", yB, -1)):
            for i in range(7):
                x = -3.3 + 6.6 * i / 6
                zb = z_intrados(x)
                zc = (zb + H_ARCH) / 2
                size = min(0.62, (H_ARCH - zb) * 0.62)
                g = GLYPHS[(i * 3 + (side == "S")) % len(GLYPHS)]
                lc.extend(strokes_mesh("l", g, (x, yf, zc), (nys, 0, 0), (0, 0, 1), (0, nys, 0), size, 0.1, 0.03,
                                       jitter=j, bvh=bvh_l))
        lc.extend(strokes_mesh("k", [((-0.2, 0.0), (0.1, -0.3)), ((0.1, -0.3), (-0.05, -0.55)),
                                     ((-0.05, -0.55), (0.15, -0.8))], (2.4, yF, H_ARCH - 0.05), (1, 0, 0), (0, 0, 1),
                               (0, 1, 0), 1.0, 0.03, 0.06, jitter=j, bvh=bvh_l))
        return lc
    carved += 14
    boolean_cut(lint, lint_cutters(0.0))
    # unir bloques + dintel
    allo = [o for o, _ in objs] + [lint]
    bm = bmesh.new()
    mats = []
    for o in allo:
        me = o.data
        offset = len(mats)
        for mm in me.materials:
            mats.append(mm.name)
        tmp = me.copy()
        for p in tmp.polygons:
            p.material_index += offset
        bm.from_mesh(tmp)
        bpy.data.meshes.remove(tmp)
    for o in allo:
        me = o.data
        bpy.data.objects.remove(o)
        bpy.data.meshes.remove(me)
    # materiales repetidos -> uno
    uniq = []
    remap = {}
    for i, n in enumerate(mats):
        if n not in uniq:
            uniq.append(n)
        remap[i] = uniq.index(n)
    for f in bm.faces:
        f.material_index = remap.get(f.material_index, 0)
    # lineas de runas emisivas en el fondo de los surcos (caras N y S de cada pilar) + bajada por el pedestal
    gm = Mesh()
    gm.bm = bm
    gm.mats = list(uniq)
    from mathutils.bvhtree import BVHTree
    bvh_stone = BVHTree.FromBMesh(bm)
    for sx in (-1, 1):
        cx = sx * PIER_X
        for yf, nys in ((DEPTH / 2, 1), (-DEPTH / 2, -1)):
            z = 0.35
            j = 0
            while z < Z_SPRING - 0.4:
                g = GLYPHS[(j + (sx > 0) * 4 + (nys > 0) * 2) % len(GLYPHS)]
                glyph_inlay(gm, g, (cx, yf, z), (nys, 0, 0), (0, 0, 1), (0, nys, 0), 0.24, 0.045,
                            "MAT_Rune_Glow_12", lift=0.004, bvh=bvh_stone)
                z += 0.42
                j += 1
            # hilo continuo que baja hasta el suelo: frente del pilar -> cara superior del pedestal -> canto
            y_edge = math.sqrt(max(0.0, 6.0 ** 2 - cx * cx)) * nys
            k = gm.mi("MAT_Rune_Glow_12")
            hw = 0.06
            quads = [((cx - hw, yf + nys * 0.005, 0.0), (cx + hw, yf + nys * 0.005, 0.0),
                      (cx + hw, yf + nys * 0.005, 0.32), (cx - hw, yf + nys * 0.005, 0.32)),
                     ((cx - hw, yf, 0.004), (cx + hw, yf, 0.004), (cx + hw, y_edge, 0.004), (cx - hw, y_edge, 0.004))]
            for qd in quads:
                vs = [bm.verts.new(q) for q in qd]
                f = bm.faces.new(vs)
                f.material_index = k
                f.normal_update()
                if f.normal.dot(Vector((0, nys, 0)) if qd is quads[0] else Vector((0, 0, 1))) < 0:
                    f.normal_flip()
            # por el canto del pedestal (z 0 -> -0.3) hasta el atrio
            vs = [bm.verts.new(q) for q in ((cx - hw, y_edge + nys * 0.01, 0.004), (cx + hw, y_edge + nys * 0.01, 0.004),
                                            (cx + hw, y_edge + nys * 0.36, Z_ATRIO - Z_TOP + 0.004),
                                            (cx - hw, y_edge + nys * 0.36, Z_ATRIO - Z_TOP + 0.004))]
            f = bm.faces.new(vs)
            f.material_index = k
            f.normal_update()
            if f.normal.dot(Vector((0, nys, 1))) < 0:
                f.normal_flip()
    me = bpy.data.meshes.new("PORTAL_Arch")
    bm.to_mesh(me)
    bm.free()
    for n in gm.mats:
        me.materials.append(bpy.data.materials[n])
    arch = bpy.data.objects.new("PORTAL_Arch", me)
    col.objects.link(arch)
    arch.location = (0, 0, Z_TOP)
    uv_metric(arch)
    report.update({"boolean_checks": BOOL_LOG, "tris": tris(arch), "carved_runes": carved, "blocks": 6, "clear_width_m": CLEAR,
                   "pier_m": PIER, "height_m": H_ARCH, "intrados_spring_key_m": [Z_SPRING, Z_KEY],
                   "pier_outer_corner_radius_m": round(math.hypot(PIER_X + PIER / 2, PIER / 2), 2)})
    return arch, report


def build_veil(col):
    bm = bmesh.new()
    nu, nv = 16, 22
    sag = 0.45
    verts = []
    hw = CLEAR / 2 - 0.03
    for j in range(nv + 1):
        row = []
        for i in range(nu + 1):
            u = i / nu
            x = -hw + 2 * hw * u
            top = z_intrados(x) - 0.06
            v = j / nv
            z = v * top
            y = sag * (1 - (x / hw) ** 2) * 0.5
            row.append(bm.verts.new((x, y, z)))
        verts.append(row)
    uvl = bm.loops.layers.uv.new("UVWorld")
    for j in range(nv):
        for i in range(nu):
            f = bm.faces.new((verts[j][i], verts[j][i + 1], verts[j + 1][i + 1], verts[j + 1][i]))
            for lp in f.loops:
                co = lp.vert.co
                lp[uvl].uv = ((co.x + hw) / (2 * hw), co.z / 11.0)
    me = bpy.data.meshes.new("PORTAL_Veil")
    bm.to_mesh(me)
    bm.free()
    me.materials.append(bpy.data.materials["MAT_Portal_Veil"])
    o = bpy.data.objects.new("PORTAL_Veil", me)
    col.objects.link(o)
    o.location = (0, 0, Z_TOP)
    o["no_collision"] = True
    o["uv"] = "u = 0..1 a lo ancho, v = z / 11 m (0..1 hasta la clave) para animar como agua"
    return o


def build_runestone(name, marker, idx, col):
    rng = random.Random(SEED + idx * 31)
    bm = bmesh.new()
    n = 8
    rings = [(0.0, 0.30), (0.3, 0.29), (0.58, 0.25), (0.74, 0.17)]
    vs = []
    for z, r in rings:
        row = []
        for i in range(n):
            a = 2 * math.pi * (i + 0.5) / n + math.pi / 2       # una cara mira a +Y
            rr = r * rng.uniform(0.9, 1.06)
            row.append(bm.verts.new((rr * math.cos(a), rr * math.sin(a) * 0.82, z + rng.uniform(-0.02, 0.02))))
        vs.append(row)
    top = bm.verts.new((rng.uniform(-0.03, 0.03), rng.uniform(-0.03, 0.03), 0.8))
    for k in range(len(rings) - 1):
        for i in range(n):
            j = (i + 1) % n
            bm.faces.new((vs[k][i], vs[k][j], vs[k + 1][j], vs[k + 1][i]))
    for i in range(n):
        bm.faces.new((vs[-1][i], vs[-1][(i + 1) % n], top))
    bm.faces.new(vs[0][::-1])
    bmesh.ops.subdivide_edges(bm, edges=[e for e in bm.edges if abs(e.verts[0].co.z - e.verts[1].co.z) > 0.2],
                              cuts=1, use_grid_fill=True)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    for v in bm.verts:
        if v.co.z > 0.02:
            v.co += v.normal * (0.02 * noise(v.co * 6 + Vector((idx, idx, idx))))
    m = Mesh()
    m.bm = bm
    m.mats = [STONE]
    # runa central emisiva en la cara +Y (hacia el Portal)
    r_at = 0.29 + (0.25 - 0.29) * (0.38 - 0.3) / (0.58 - 0.3)
    yface = r_at * 0.82 * math.cos(math.pi / n)
    up = Vector((0, 0.14, 1)).normalized()
    glyph_inlay(m, GLYPHS[idx % len(GLYPHS)], (0, yface, 0.38), (1, 0, 0), tuple(up), (0, 1, 0), 0.3, 0.05,
                "MAT_Rune_Glow_10", lift=0.028)
    o = m.to_object(name, col)
    o.matrix_world = marker.matrix_world.copy()
    uv_metric(o)
    return o


def build_pedestal(name, marker, idx, col):
    rng = random.Random(SEED + 500 + idx)
    bm = bmesh.new()
    n = 16
    prof = [(0.0, 0.62), (0.08, 0.6), (0.42, 0.58), (0.47, 0.6), (0.5, 0.56)]
    rings = []
    for z, r in prof:
        rings.append([bm.verts.new(((r + rng.uniform(-0.01, 0.01)) * math.cos(2 * math.pi * i / n),
                                    (r + rng.uniform(-0.01, 0.01)) * math.sin(2 * math.pi * i / n), z))
                      for i in range(n)])
    for k in range(len(rings) - 1):
        for i in range(n):
            j = (i + 1) % n
            bm.faces.new((rings[k][i], rings[k][j], rings[k + 1][j], rings[k + 1][i]))
    bm.faces.new(rings[-1])
    bm.faces.new(rings[0][::-1])
    m = Mesh()
    m.bm = bm
    m.mats = [STONE]
    k = m.mi(PLATE)
    s = 0.4
    lo = [bm.verts.new((x, y, 0.5)) for x, y in ((-s, -s), (s, -s), (s, s), (-s, s))]
    hi = [bm.verts.new((x, y, 0.535)) for x, y in ((-s, -s), (s, -s), (s, s), (-s, s))]
    for f in [bm.faces.new(hi)] + [bm.faces.new((lo[i], lo[(i + 1) % 4], hi[(i + 1) % 4], hi[i])) for i in range(4)]:
        f.material_index = k
    o = m.to_object(name, col)
    mw = marker.matrix_world.copy()
    o.matrix_world = Matrix.Translation(mw.translation - Vector((0, 0, 0.5))) @ mw.to_3x3().to_4x4()
    o["floor"] = marker.get("floor")
    o["plate_m"] = 0.8
    uv_metric(o)
    return o


def build_atrio_runes(col, r=14.85, z=Z_ATRIO):
    m = Mesh()
    k = m.mi("MAT_Rune_Glow_12")
    n_ring = 120
    for rr in (r - 0.32, r + 0.32):
        for i in range(n_ring):
            a0, a1 = 2 * math.pi * i / n_ring, 2 * math.pi * (i + 1) / n_ring
            w = 0.03
            vs = [m.bm.verts.new(((rr - w) * math.cos(a), (rr - w) * math.sin(a), z + 0.004)) for a in (a0, a1)] + \
                 [m.bm.verts.new(((rr + w) * math.cos(a), (rr + w) * math.sin(a), z + 0.004)) for a in (a1, a0)]
            f = m.bm.faces.new(vs)
            f.material_index = k
    ng = 96
    for i in range(ng):
        a = 2 * math.pi * (i + 0.5) / ng
        c = (r * math.cos(a), r * math.sin(a), z)
        t = (-math.sin(a), math.cos(a), 0)
        radial = (math.cos(a), math.sin(a), 0)
        glyph_inlay(m, GLYPHS[(i * 7) % len(GLYPHS)], c, t, radial, (0, 0, 1), 0.42, 0.05, "MAT_Rune_Glow_12",
                    lift=0.004)
    for f in m.bm.faces:
        f.normal_update()
        if f.normal.z < 0:
            f.normal_flip()
    me = bpy.data.meshes.new("PORTAL_AtrioRunes")
    m.bm.to_mesh(me)
    m.bm.free()
    me.materials.append(bpy.data.materials["MAT_Rune_Glow_12"])
    o = bpy.data.objects.new("PORTAL_AtrioRunes", me)
    col.objects.link(o)
    uv_metric(o)
    return o
