"""
CONCORDIA - etapa 14: el Obelisco de los Pisos (coleccion BLD_PORTAL), sobre MARKER_Obelisco (SO de la plaza).

Referencias: obelisco de Luxor en la Place de la Concorde (fuste de 4 caras que se estrecha, pyramidion, grabados
en bajorrelieve; silueta limpia) y Porta Nigra (piedra oscura). Medidas (m, origen = centro de la base a la cota
del basamento, +Y local = frente hacia la plaza):
  pedestal escalonado 5 x 5, 4 escalones de 0.375 (5.0 / 4.5 / 4.0 / 3.5)      z 0 .. 1.5
  fuste de seccion cuadrada 3.0 -> 1.8                                          z 1.5 .. 22.5
  pyramidion de 2.5                                                              z 22.5 .. 25.0
100 marcas OBELISK_Mark_001..100: hueco rectangular de 0.3 x 0.5 x 0.04 tallado en el fuste (5 columnas x 5 filas
por cara) y, dentro, el numero del piso como numeral cisterciense (un solo glifo: palo + trazos en los cuadrantes;
unidades arriba-dcha, decenas arriba-izda, centenas abajo-dcha) en MAT_Obelisk_Mark (apagado) con la variante
MAT_Obelisk_Mark_Lit (#8FD0FF, emision 3.0) para encenderla por instancia en Godot. Orden: el piso 1 abajo y el 100
arriba, dando la vuelta: fila 0 = pisos 1-5 cara frontal, 6-10 cara izquierda, 11-15 trasera, 16-20 derecha; fila 1
= 21-40 ... fila 4 = 81-100.
"""

import math

import bmesh
import bpy
from mathutils import Vector

Z_PED = 1.5
Z_SHAFT_TOP = 22.5
H_TOTAL = 25.0
HALF0, HALF1 = 1.5, 0.9
STEPS = (5.0, 4.5, 4.0, 3.5)
MARK_W, MARK_H, MARK_D = 0.3, 0.5, 0.04
ROWS_Z = (3.6, 7.6, 11.6, 15.6, 19.6)
GLOW = "#8FD0FF"
# caras en orden de vuelta (vistas desde arriba, sentido antihorario): frente +Y, izquierda -X, trasera -Y, dcha +X
FACES = ((0, 1), (-1, 0), (0, -1), (1, 0))


def _lin(hexs):
    h = hexs.lstrip("#")
    c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return [x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c]


def half(z):
    """Semiancho del fuste a la cota z."""
    return HALF0 + (HALF1 - HALF0) * (z - Z_PED) / (Z_SHAFT_TOP - Z_PED)


# ---------------------------------------------------------------------------
# materiales
# ---------------------------------------------------------------------------
def ensure_materials():
    out = {}
    if "MAT_Obelisk_Black" not in bpy.data.materials:
        src = bpy.data.materials["MAT_Rock_Gray"]
        m = src.copy()
        m.name = "MAT_Obelisk_Black"
        N, L = m.node_tree.nodes, m.node_tree.links
        b = next(n for n in N if n.type == "BSDF_PRINCIPLED")
        alb = N["Albedo"]
        mix = N.new("ShaderNodeMix")
        mix.data_type = "RGBA"
        mix.blend_type = "MULTIPLY"
        mix.inputs["Factor"].default_value = 1.0
        L.new(alb.outputs["Color"], mix.inputs["A"])
        mix.inputs["B"].default_value = (0.16, 0.16, 0.165, 1.0)       # gris de roca -> casi negro, sin saturar
        L.new(mix.outputs["Result"], b.inputs["Base Color"])
        for lk in list(b.inputs["Roughness"].links):
            L.remove(lk)
        b.inputs["Roughness"].default_value = 0.8
        m["note"] = "piedra negra (textura de roca, baseColorFactor 0.16), roughness 0.8 constante"
        out["MAT_Obelisk_Black"] = "creado"
    if "MAT_Obelisk_Mark" not in bpy.data.materials:
        m = bpy.data.materials.new("MAT_Obelisk_Mark")
        m.use_nodes = True
        b = m.node_tree.nodes["Principled BSDF"]
        b.inputs["Base Color"].default_value = (*_lin("#4A4A4A"), 1)
        b.inputs["Roughness"].default_value = 0.6
        b.inputs["Emission Strength"].default_value = 0.0
        m["note"] = "marca de piso APAGADA (gris oscuro). Variante encendida: MAT_Obelisk_Mark_Lit"
        out["MAT_Obelisk_Mark"] = "creado"
    if "MAT_Obelisk_Mark_Lit" not in bpy.data.materials:
        m = bpy.data.materials.new("MAT_Obelisk_Mark_Lit")
        m.use_nodes = True
        b = m.node_tree.nodes["Principled BSDF"]
        c = _lin(GLOW)
        b.inputs["Base Color"].default_value = (*c, 1)
        b.inputs["Roughness"].default_value = 0.4
        b.inputs["Emission Color"].default_value = (*c, 1)
        b.inputs["Emission Strength"].default_value = 3.0
        m["note"] = "marca de piso ENCENDIDA: #8FD0FF, emision 3.0 (Godot la asigna por instancia)"
        out["MAT_Obelisk_Mark_Lit"] = "creado"
    return out


class Mesh:
    def __init__(self):
        self.bm = bmesh.new()
        self.mats = []

    def mi(self, n):
        if n not in self.mats:
            self.mats.append(n)
        return self.mats.index(n)

    def face(self, cos, mat, nrm=None):
        vs = [self.bm.verts.new(Vector(c)) for c in cos]
        f = self.bm.faces.new(vs)
        f.material_index = self.mi(mat)
        if nrm is not None:
            f.normal_update()
            if f.normal.dot(Vector(nrm)) < 0:
                f.normal_flip()
        return f

    def box(self, lo, hi, mat, skip=()):
        x0, y0, z0 = lo
        x1, y1, z1 = hi
        P = [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0), (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
        F = {"z-": ((0, 3, 2, 1), (0, 0, -1)), "z+": ((4, 5, 6, 7), (0, 0, 1)), "y-": ((0, 1, 5, 4), (0, -1, 0)),
             "y+": ((2, 3, 7, 6), (0, 1, 0)), "x-": ((3, 0, 4, 7), (-1, 0, 0)), "x+": ((1, 2, 6, 5), (1, 0, 0))}
        for k, (idx, n) in F.items():
            if k not in skip:
                self.face([P[i] for i in idx], mat, n)

    def to_object(self, name, col, weld=True):
        if weld:
            bmesh.ops.remove_doubles(self.bm, verts=self.bm.verts[:], dist=1e-4)
        me = bpy.data.meshes.new(name)
        self.bm.to_mesh(me)
        self.bm.free()
        for n in self.mats:
            me.materials.append(bpy.data.materials[n])
        o = bpy.data.objects.new(name, me)
        col.objects.link(o)
        return o


# ---------------------------------------------------------------------------
# marcas
# ---------------------------------------------------------------------------
def mark_slot(floor):
    """(cara, fila, columna) del piso 1..100."""
    i = floor - 1
    return (i % 20) // 5, i // 20, i % 5


def face_frame(k):
    nx, ny = FACES[k]
    n = Vector((nx, ny, 0))
    right = Vector((0, 0, 1)).cross(n)          # derecha de quien mira la cara desde fuera
    return n, right


def mark_center(floor):
    k, row, col = mark_slot(floor)
    z = ROWS_Z[row]
    h = half(z)
    spacing = min(0.5, (2 * h - 0.45) / 5)
    u = (col - 2) * spacing
    return k, u, z


def P(k, u, z, inset=0.0):
    """Punto de la cara k con coordenada horizontal u (derecha +) a la cota z; inset hacia dentro."""
    n, right = face_frame(k)
    return n * (half(z) - inset) + right * u + Vector((0, 0, z))


def cistercian_strokes(num):
    """Trazos (x, y) en un glifo de 1 x 1 centrado (x: derecha, y: arriba) del numeral cisterciense de num."""
    S = [((0.0, -0.45), (0.0, 0.45))]                    # palo
    q = {1: [((0, 1), (1, 1))], 2: [((0, 0), (1, 0))], 3: [((0, 1), (1, 0))], 4: [((0, 0), (1, 1))],
         6: [((1, 1), (1, 0))]}
    q[5] = q[1] + q[4]
    q[7] = q[1] + q[6]
    q[8] = q[2] + q[6]
    q[9] = q[1] + q[2] + q[6]
    units, tens, hundreds = num % 10, (num // 10) % 10, (num // 100) % 10

    def place(d, sx, sy):
        out = []
        for (a, b) in q.get(d, []):
            def m(p):
                x = p[0] * 0.36 * sx
                y = sy * (0.45 - (1 - p[1]) * 0.3)          # cuadrante de arriba (sy=1) o abajo (sy=-1)
                return (x, y)
            out.append((m(a), m(b)))
        return out
    S += place(units, 1, 1) + place(tens, -1, 1) + place(hundreds, 1, -1)
    return S


def build_mark(floor, col_obj, root_mw):
    k, u, z = mark_center(floor)
    n, right = face_frame(k)
    m = Mesh()
    w = 0.045                                            # grosor del trazo (m)
    for (a, b) in cistercian_strokes(floor):
        pa = (a[0] * MARK_W * 0.9, a[1] * MARK_H * 0.9)
        pb = (b[0] * MARK_W * 0.9, b[1] * MARK_H * 0.9)
        da = Vector((pb[0] - pa[0], pb[1] - pa[1]))
        if da.length < 1e-5:
            continue
        t = da.normalized()
        s = Vector((-t.y, t.x)) * (w / 2)
        e = t * (w / 2)
        quad2 = [Vector(pa) - e - s, Vector(pb) + e - s, Vector(pb) + e + s, Vector(pa) - e + s]
        cos = [P(k, u + q.x, z + q.y, inset=MARK_D - 0.004) for q in quad2]
        m.face([tuple(c) for c in cos], "MAT_Obelisk_Mark", nrm=tuple(n))
    o = m.to_object(f"OBELISK_Mark_{floor:03d}", col_obj, weld=False)
    o.matrix_world = root_mw.copy()
    _, row, colm = mark_slot(floor)
    o["floor"] = floor
    o["face"] = ("front", "left", "back", "right")[k]
    o["row"], o["column"] = row, colm
    o["glyph"] = "numeral cisterciense"
    o["material_off"], o["material_on"] = "MAT_Obelisk_Mark", "MAT_Obelisk_Mark_Lit"
    return o


# ---------------------------------------------------------------------------
# cuerpo
# ---------------------------------------------------------------------------
def build_shaft_faces(m, with_recess=True):
    """Las 4 caras del fuste: trapecio con 25 huecos (paredes + fondo) cada una."""
    mat = "MAT_Obelisk_Black"
    for k in range(4):
        n, right = face_frame(k)
        holes = []
        if with_recess:
            for floor in range(1, 101):
                kk, u, z = mark_center(floor)
                if kk != k:
                    continue
                holes.append((u - MARK_W / 2, z - MARK_H / 2, u + MARK_W / 2, z + MARK_H / 2))
        loops = [[(-half(Z_PED), Z_PED), (half(Z_PED), Z_PED), (half(Z_SHAFT_TOP), Z_SHAFT_TOP),
                  (-half(Z_SHAFT_TOP), Z_SHAFT_TOP)]]
        loops += [[(a, b), (c, b), (c, d), (a, d)] for (a, b, c, d) in holes]
        edges = []
        for lp in loops:
            vs = [m.bm.verts.new(P(k, u, z)) for (u, z) in lp]
            edges += [m.bm.edges.new((vs[i], vs[(i + 1) % len(vs)])) for i in range(len(vs))]
        r = bmesh.ops.triangle_fill(m.bm, use_beauty=True, use_dissolve=False, edges=edges)
        idx = m.mi(mat)
        for f in [g for g in r["geom"] if isinstance(g, bmesh.types.BMFace)]:
            f.material_index = idx
            f.normal_update()
            if f.normal.dot(n) < 0:
                f.normal_flip()
        for (a, b, c, d) in holes:
            rim = [(a, b), (c, b), (c, d), (a, d)]
            for i in range(4):
                (u0, z0), (u1, z1) = rim[i], rim[(i + 1) % 4]
                q = [P(k, u0, z0), P(k, u1, z1), P(k, u1, z1, MARK_D), P(k, u0, z0, MARK_D)]
                cen = P(k, (a + c) / 2, (b + d) / 2, MARK_D / 2)
                mid = (q[0] + q[1]) / 2
                m.face([tuple(p) for p in q], mat, nrm=tuple((cen - mid).normalized()))
            m.face([tuple(P(k, uu, zz, MARK_D)) for (uu, zz) in rim], mat, nrm=tuple(n))


def build_body(col, lod=0):
    m = Mesh()
    blk = "MAT_Obelisk_Black"
    z = 0.0
    hs = Z_PED / len(STEPS)
    for i, s in enumerate(STEPS):
        h2 = s / 2
        m.box((-h2, -h2, z), (h2, h2, z + hs), blk, skip=("z-",) if i == 0 else ("z-",))
        z += hs
    build_shaft_faces(m, with_recess=(lod == 0))
    # pyramidion
    top = [Vector((sx * HALF1, sy * HALF1, Z_SHAFT_TOP)) for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    apex = Vector((0, 0, H_TOTAL))
    for i in range(4):
        a, b = top[i], top[(i + 1) % 4]
        out = ((a + b) / 2).normalized()
        m.face([tuple(a), tuple(b), tuple(apex)], blk, nrm=(out.x, out.y, 0.4))
    if lod < 2:
        # placa con runa grande al pie del fuste (cara frontal)
        k = 0
        n, right = face_frame(k)
        pw, ph, pz = 1.3, 1.1, 2.15
        lo_ = [P(k, -pw / 2, pz - ph / 2, -0.07), P(k, pw / 2, pz - ph / 2, -0.07), P(k, pw / 2, pz + ph / 2, -0.07),
               P(k, -pw / 2, pz + ph / 2, -0.07)]
        base = [P(k, -pw / 2, pz - ph / 2, 0.0), P(k, pw / 2, pz - ph / 2, 0.0), P(k, pw / 2, pz + ph / 2, 0.0),
                P(k, -pw / 2, pz + ph / 2, 0.0)]
        m.face([tuple(p) for p in lo_], "MAT_Wall_Gray", nrm=tuple(n))
        for i in range(4):
            q = [base[i], base[(i + 1) % 4], lo_[(i + 1) % 4], lo_[i]]
            mid = (q[0] + q[1] + q[2] + q[3]) / 4
            m.face([tuple(p) for p in q], "MAT_Wall_Gray", nrm=tuple((mid - P(k, 0, pz, -0.035)).normalized()))
        rune = [((0, -.5), (0, .5)), ((-.32, .18), (0, .5)), ((.32, .18), (0, .5)), ((-.3, -.15), (.3, -.15))]
        for (a, b) in rune:
            pa, pb = Vector(a) * 0.8, Vector(b) * 0.8
            d = pb - pa
            t = d.normalized()
            s = Vector((-t.y, t.x)) * 0.05
            e = t * 0.05
            q2 = [pa - e - s, pb + e - s, pb + e + s, pa - e + s]
            m.face([tuple(P(k, q.x, pz + q.y, -0.074)) for q in q2], "MAT_Rune_Glow_12", nrm=tuple(n))
    return m


def build_lanterns(col, root_mw):
    import bld_kit as BK
    out = []
    for i, (sx, sy) in enumerate(((1, 1), (-1, 1), (-1, -1), (1, -1))):
        mb = BK.MB()
        mb.box((-0.06, -0.06, 0), (0.06, 0.06, 2.4), BK.M_IRON)
        mb.box((-0.12, -0.12, 0), (0.12, 0.12, 0.15), BK.M_IRON)
        mb.push(__import__("mathutils").Matrix.Translation((0, 0.05, 2.35)))
        BK.lantern_shard(mb)
        mb.pop()
        mb.finish()
        me = bpy.data.meshes.new(f"OBELISK_Lantern_{i + 1}")
        mb.bm.to_mesh(me)
        mb.bm.free()
        for n in mb.mats:
            me.materials.append(bpy.data.materials[n])
        o = bpy.data.objects.new(f"OBELISK_Lantern_{i + 1}", me)
        col.objects.link(o)
        local = __import__("mathutils").Matrix.Translation((sx * 2.95, sy * 2.95, 0)) @ \
            __import__("mathutils").Matrix.Rotation(math.atan2(-sx, sy), 4, "Z")
        o.matrix_world = root_mw @ local
        out.append(o)
    return out


def box_collider(name, col, root_mw):
    m = Mesh()
    m.box((-2.5, -2.5, 0), (2.5, 2.5, Z_PED), "MAT_Obelisk_Black")
    m.box((-HALF0, -HALF0, Z_PED), (HALF0, HALF0, H_TOTAL), "MAT_Obelisk_Black")
    o = m.to_object(name, col, weld=False)
    o.data.materials.clear()
    o.matrix_world = root_mw.copy()
    o.display_type = "WIRE"
    o.hide_render = True
    return o
