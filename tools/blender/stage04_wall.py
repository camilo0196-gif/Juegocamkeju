"""
CONCORDIA - Etapa 04: muralla como KIT MODULAR (WALL_KIT) + montaje (WALL_LAYOUT).

Referencias (silueta, remate y proporcion)
- Avila: granito gris calido en sillares por hiladas, cubos semicirculares (BASTION), almenas regulares.
- Carcassonne: torres de guardia redondas con cono de pizarra oscura; camino de ronda tras parapeto almenado.
- Dubrovnik: paseo de 3 m sobre el muro, con vistas al exterior (BASTION_Mirador).
- Caernarfon / Conwy: puerta entre dos torres poligonales con bandas de piedra clara y oscura.

Convenciones
- Unidades en metros. Origen de cada pieza en el centro de su base (Z = 0 = DATUM +6.0).
- Ejes locales: +X tangente (sentido horario visto desde arriba), +Y hacia FUERA de la ciudad,
  +Z arriba. Rotacion de un slot k: Z = 7.5*k - 90 grados (en Godot -Z local mira al exterior).
- Altura del muro 15 m HASTA LO ALTO DE LAS ALMENAS: camino de ronda a 12.4, parapeto 12.4-13.6,
  almenas 13.6-15.0 (decision por defecto, ver informe).
- Perfil del muro (cara interior en Y=-3): base de 6 m (Y -3..+3), talud exterior de 2 m hasta Z=4,
  corona de 4 m (Y -3..+1) = camino de 3 m + parapeto de 1 m.
"""

import os
import random
import sys
from math import atan2, ceil, cos, degrees, pi, radians, sin, sqrt, tan

import bpy  # noqa: I001
import bmesh
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import concordia_const as C  # noqa: E402
import terrain_profile as T  # noqa: E402

REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
TEX = os.path.join(REPO, "textures", "wall")

# --- Datos del pedido --------------------------------------------------------
N_SLOTS = 48
STEP_DEG = 360.0 / N_SLOTS                     # 7.5
HALF = radians(STEP_DEG / 2)
CHORD = 2 * C.WALL_RADIUS * sin(HALF)          # 26.159
WALL_H = 15.0
WALK_Z = 12.4
PARAPET_H = 1.2
MERLON_H = 1.4
MERLON_W = 1.0
CRENEL_W = 0.6
PARAPET_T = 1.0
WALK_W = 3.0
BASE_T = 6.0
TALUD = 2.0
TALUD_H = 4.0                                   # altura del talud (no fijada en el pedido)
SLIT_W, SLIT_H = 0.2, 1.2
SLIT_EVERY = 4.0
RUNE_W, RUNE_D = 0.08, 0.03
RUNE_Z = 4.50                                   # v4: anillo continuo a +4.5 m (1 m sobre las Moradas), ambas caras
TILE_M = 1.0                                    # 1 m = 1 tile
RUNE_EMISSION = 0.8
BEVEL = 0.03
SEED = 21

Y_IN = -BASE_T / 2                              # -3 cara interior
Y_OUT_BASE = BASE_T / 2                         # +3 pie del talud
Y_OUT = Y_IN + WALK_W + PARAPET_T               # +1 cara exterior sobre el talud
END_CLEAR = 2.6                                 # sin almenas a < 2.6 m de cada junta (las cubren las piezas de slot)

BASTION_D, BASTION_H = 5.0, 16.5
BASTION_PLAT = BASTION_H - PARAPET_H - MERLON_H   # 13.9
MIRADOR = (4.0, 2.5)
TOWER_D, TOWER_H = 9.0, 22.0
TOWER_CY = 4.0                                  # centro de la torre: 4 m hacia fuera (el camino pasa detras)
ROOF_PITCH = 55.0
LANTERN_H, LANTERN_E = 1.2, 2.5
GATE_TOWER_D, GATE_TOWER_H = 12.0, 24.0
GATE_ARCH_W, GATE_ARCH_H = 8.0, 10.0
GATE_RUNE_D, GATE_RUNE_E = 1.5, 2.5
GATE_BLOCK_Y = 4.0                              # cuerpo central entre torres: Y -4..+4
GATE_WALK = WALL_H + 0.05                       # el adarve de la puerta tapa las almenas de los modulos
STAIR_W = 3.0
DOOR_W, DOOR_H = 1.2, 2.2                       # puerta de la torre de guardia al camino de ronda
STAIR_RISER, STAIR_TREAD, STAIR_N = WALK_Z / 62, 0.26, 31
STAIR_LANDING_END = (STAIR_N - 1) * STAIR_TREAD / 2 - 1.6 + 3.4     # extremo del rellano en X local (5.7)
DRAIN_W, DRAIN_H = 1.8, 1.2
DRAIN_SLOT = 46                                 # 345 grados (es un bastion)

MATS = {
    "MAT_Wall_Granite": ("T_Granite_Courses", "#FFFFFF", 0.85),
    "MAT_Wall_Patch": ("T_Patch_Stone", "#FFFFFF", 0.9),
    "MAT_Roof_Slate": ("T_Slate", "#FFFFFF", 0.6),
    "MAT_Roof_TileOchre": ("T_TileOchre", "#FFFFFF", 0.8),
    "MAT_Wood_Dark": ("T_Wood_Dark", "#FFFFFF", 0.8),
    "MAT_Iron_Black": (None, "#1D1D1F", 0.5),
    "MAT_Stone_Band": (None, "#C9BFA8", 0.85),      # banda clara (Caernarfon) / arquivolta
    "MAT_Void": (None, "#060607", 1.0),
}


# ---------------------------------------------------------------------------
# Materiales
# ---------------------------------------------------------------------------
def load_img(name, non_color=False):
    p = os.path.join(TEX, name + ".png")
    img = bpy.data.images.get(name + ".png") or bpy.data.images.load(p, check_existing=True)
    img.filepath = bpy.path.relpath(p) if bpy.data.filepath else p
    if non_color:
        img.colorspace_settings.name = "Non-Color"
    return img


def textured_material(name, tex, tint, rough):
    if name in bpy.data.materials:
        bpy.data.materials.remove(bpy.data.materials[name])
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    N, L = m.node_tree.nodes, m.node_tree.links
    b = N["Principled BSDF"]
    b.inputs["Roughness"].default_value = rough
    if tex:
        t = N.new("ShaderNodeTexImage")
        t.image = load_img(tex + "_albedo")
        L.new(t.outputs["Color"], b.inputs["Base Color"])
        if os.path.exists(os.path.join(TEX, tex + "_normal.png")):
            tn = N.new("ShaderNodeTexImage")
            tn.image = load_img(tex + "_normal", non_color=True)
            nm = N.new("ShaderNodeNormalMap")
            L.new(tn.outputs["Color"], nm.inputs["Color"])
            L.new(nm.outputs["Normal"], b.inputs["Normal"])
    else:
        b.inputs["Base Color"].default_value = C.hex_to_linear_rgba(tint)
    if name == "MAT_Iron_Black":
        b.inputs["Metallic"].default_value = 0.8
    return m


def emissive_material(name, strength, tex=None, base="#8FD0FF"):
    if name in bpy.data.materials:
        bpy.data.materials.remove(bpy.data.materials[name])
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    N, L = m.node_tree.nodes, m.node_tree.links
    b = N["Principled BSDF"]
    b.inputs["Base Color"].default_value = C.hex_to_linear_rgba(base)
    b.inputs["Emission Color"].default_value = C.hex_to_linear_rgba(C.MAGIC_BLUE_HEX)
    b.inputs["Emission Strength"].default_value = strength
    if tex:
        t = N.new("ShaderNodeTexImage")
        t.image = load_img(tex)
        mix = N.new("ShaderNodeMix")
        mix.data_type = "RGBA"
        mix.blend_type = "MULTIPLY"
        mix.inputs["Factor"].default_value = 1.0
        mix.inputs["A"].default_value = C.hex_to_linear_rgba(C.MAGIC_BLUE_HEX)
        L.new(t.outputs["Color"], mix.inputs["B"])
        L.new(mix.outputs["Result"], b.inputs["Emission Color"])
    m["emission_base"] = strength          # parametro editable (Godot: emission_energy)
    return m


LIB_MAP = {"MAT_Wall_Granite": "WallGranite", "MAT_Wall_Patch": "WallPatch", "MAT_Stone_Band": "StoneBand",
           "MAT_Roof_Slate": "RoofSlate", "MAT_Roof_TileOchre": "RoofTileOchre", "MAT_Wood_Dark": "WoodDark",
           "MAT_Iron_Black": "IronBlack"}
TERRAIN_LIB = ("CobblestoneFloor001", "SandstoneCracks", "RockBoulderCracked", "RocksGround02", "StoneWall02")


def build_materials():
    import material_library as ML
    out = {k: ML.make_material(k, v) for k, v in LIB_MAP.items()}
    out["MAT_Void"] = textured_material("MAT_Void", *MATS["MAT_Void"])
    out["MAT_Wall_Runes"] = emissive_material("MAT_Wall_Runes", RUNE_EMISSION, tex="T_Runes_emission",
                                              base="#4F4B45")
    out["MAT_Wall_Runes"]["note"] = "Emission Strength = emission_base (0.8). En Godot: emission_energy; animar al anochecer"
    out["MAT_Magic_Glow25"] = emissive_material("MAT_Magic_Glow25", LANTERN_E)
    for name in TERRAIN_LIB:                      # preparados para el terreno, aun SIN aplicar
        m = ML.make_material(f"MAT_{name}", name)
        m.use_fake_user = True
    return out


# ---------------------------------------------------------------------------
# Constructor de piezas
# ---------------------------------------------------------------------------
class Kit:
    """bmesh con materiales por cara, bisel de 3 cm en aristas vivas y UV por partes."""

    def __init__(self, mats):
        self.bm = bmesh.new()
        self.mats = mats
        self.uvp = self.bm.faces.layers.int.new("uvp")
        self.parts = [None]                       # 0 = proyeccion plana por cara

    def mi(self, name):
        if name not in self.mats:
            self.mats.append(name)
        return self.mats.index(name)

    def add(self, verts, faces, mat, bevel=True, part=0, recalc=True, face_mats=None, no_bevel_faces=()):
        vs = [self.bm.verts.new(v) for v in verts]
        new = []
        for i, f in enumerate(faces):
            try:
                face = self.bm.faces.new([vs[j] for j in f])
            except ValueError:
                continue
            face.material_index = self.mi(face_mats[i] if face_mats else mat)
            face[self.uvp] = part
            new.append((i, face))
        fs = [f for _i, f in new]
        if recalc:
            bmesh.ops.recalc_face_normals(self.bm, faces=fs)
        if bevel and BEVEL > 0:
            skip = {f for i, f in new if i in no_bevel_faces}
            edges = set()
            for f in fs:
                for e in f.edges:
                    if len(e.link_faces) == 2 and not any(lf in skip for lf in e.link_faces):
                        if e.calc_face_angle(0.0) > radians(40):
                            edges.add(e)
            if edges:
                bmesh.ops.bevel(self.bm, geom=list(edges), offset=BEVEL, offset_type="OFFSET", segments=1,
                                profile=0.5, affect="EDGES", clamp_overlap=True)
        return fs

    def part(self, kind, *data):
        self.parts.append((kind,) + data)
        return len(self.parts) - 1

    # --- primitivas
    def prism(self, prof, origin, pdir, wdir, w0, w1, mat, **kw):
        O, Pd, Wd = Vector(origin), Vector(pdir), Vector(wdir)
        n = len(prof)
        pts = []
        for w in (w0, w1):
            for p, z in prof:
                v = O + Pd * p + Wd * w
                pts.append((v.x, v.y, v.z + z))
        faces = [tuple(range(n)), tuple(range(2 * n - 1, n - 1, -1))]
        faces += [(i, (i + 1) % n, n + (i + 1) % n, n + i) for i in range(n)]
        return self.add(pts, faces, mat, **kw)

    def box(self, x0, x1, y0, y1, z0, z1, mat, **kw):
        return self.prism([(y0, z0), (y1, z0), (y1, z1), (y0, z1)], (0, 0, 0), (0, 1, 0), (1, 0, 0), x0, x1, mat, **kw)

    def obox(self, c, ax, ay, h, mat, z0=None, **kw):
        """Caja orientada: centro c (x,y), semiejes horizontales ax, ay (vectores), alto h desde z0."""
        c = Vector(c)
        ax, ay = Vector(ax), Vector(ay)
        z0 = c.z if z0 is None else z0
        corners = [c - ax - ay, c + ax - ay, c + ax + ay, c - ax + ay]
        pts = [(p.x, p.y, z0) for p in corners] + [(p.x, p.y, z0 + h) for p in corners]
        faces = [(3, 2, 1, 0), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
        return self.add(pts, faces, mat, **kw)

    def lathe(self, prof, cx, cy, seg, mat, closed=True, part_kind="cyl", face_mat_fn=None, rot=0.0, **kw):
        rings, verts = [], []
        for r, z in prof:
            if r < 1e-9:
                rings.append([len(verts)])
                verts.append((cx, cy, z))
            else:
                idx = []
                for i in range(seg):
                    a = 2 * pi * i / seg + rot
                    idx.append(len(verts))
                    verts.append((cx + r * cos(a), cy + r * sin(a), z))
                rings.append(idx)
        faces, fz = [], []
        n = len(rings)
        for k in range(n if closed else n - 1):
            A, B = rings[k], rings[(k + 1) % n]
            if len(A) == 1 and len(B) == 1:
                continue
            zc = (prof[k][1] + prof[(k + 1) % n][1]) / 2
            for i in range(seg):
                j = (i + 1) % seg
                if len(A) == 1:
                    faces.append((A[0], B[i], B[j]))
                elif len(B) == 1:
                    faces.append((A[i], A[j], B[0]))
                else:
                    faces.append((A[i], A[j], B[j], B[i]))
                fz.append(zc)
        part = self.part(part_kind, cx, cy, prof) if part_kind else 0
        fm = [face_mat_fn(z) for z in fz] if face_mat_fn else None
        return self.add(verts, faces, mat, part=part, face_mats=fm, **kw)

    def _plate(self, poly, y0, y1, mat, **kw):
        """Poligono (x,z) extruido en Y entre y0 e y1 (puertas, runas, arquivoltas)."""
        n = len(poly)
        pts = [(x, y0, z) for x, z in poly] + [(x, y1, z) for x, z in poly]
        faces = [tuple(range(n)), tuple(range(2 * n - 1, n - 1, -1))]
        faces += [(i, (i + 1) % n, n + (i + 1) % n, n + i) for i in range(n)]
        return self.add(pts, faces, mat, **kw)

    # --- salida
    def to_object(self, name, collection, materials, smooth_angle=35.0):
        bm = self.bm
        bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=1e-5)
        bmesh.ops.triangulate(bm, faces=bm.faces[:], quad_method="BEAUTY", ngon_method="EAR_CLIP")
        uvl = bm.loops.layers.uv.new("UVMap")
        rune_i = self.mats.index("MAT_Wall_Runes") if "MAT_Wall_Runes" in self.mats else -1
        for f in bm.faces:
            n = f.normal
            part = self.parts[f[self.uvp]] if f[self.uvp] < len(self.parts) else None
            for lp in f.loops:
                c = lp.vert.co
                if f.material_index == rune_i:
                    uv = (c.x / 0.64, (c.z - (RUNE_Z - RUNE_W / 2)) / RUNE_W)
                elif part and part[0] in ("cyl", "cone") and abs(n.z) < 0.95:
                    cx, cy = part[1], part[2]
                    ang = atan2(c.y - cy, c.x - cx)
                    rr = max(sqrt((c.x - cx) ** 2 + (c.y - cy) ** 2), 1e-6)
                    r_ref = max(p[0] for p in part[3])
                    if part[0] == "cone":
                        uv = (ang * r_ref / TILE_M, -rr / cos(radians(ROOF_PITCH)) / TILE_M)
                    else:
                        uv = (ang * r_ref / TILE_M, c.z / TILE_M)
                elif abs(n.z) > 0.7:
                    uv = (c.x / TILE_M, c.y / TILE_M)
                else:
                    t = Vector((-n.y, n.x, 0.0)).normalized()
                    uv = ((c.x * t.x + c.y * t.y) / TILE_M, c.z / TILE_M)
                lp[uvl].uv = uv
        if name in bpy.data.objects:
            bpy.data.objects.remove(bpy.data.objects[name])
        if name in bpy.data.meshes:
            bpy.data.meshes.remove(bpy.data.meshes[name])
        me = bpy.data.meshes.new(name)
        bm.to_mesh(me)
        bm.free()
        for mname in self.mats:
            me.materials.append(materials[mname])
        me.shade_smooth()
        me.set_sharp_from_angle(angle=radians(smooth_angle))
        obj = bpy.data.objects.new(name, me)
        collection.objects.link(obj)
        return obj


# ---------------------------------------------------------------------------
# Piezas
# ---------------------------------------------------------------------------
def merlon_positions(L):
    avail = L - 2 * END_CLEAR
    n = int((avail + CRENEL_W) // (MERLON_W + CRENEL_W))
    span = n * MERLON_W + (n - 1) * CRENEL_W
    x0 = -span / 2 + MERLON_W / 2
    return [x0 + i * (MERLON_W + CRENEL_W) for i in range(n)]


def merlon(kit, x, y0, y1, z0, mat, slit=False):
    if not slit:
        kit.box(x - MERLON_W / 2, x + MERLON_W / 2, y0, y1, z0, z0 + MERLON_H, mat)
        return
    sw, m = SLIT_W / 2, (MERLON_H - SLIT_H) / 2
    kit.box(x - MERLON_W / 2, x - sw, y0, y1, z0, z0 + MERLON_H, mat)
    kit.box(x + sw, x + MERLON_W / 2, y0, y1, z0, z0 + MERLON_H, mat)
    kit.box(x - sw, x + sw, y0, y1, z0, z0 + m, mat, bevel=False)
    kit.box(x - sw, x + sw, y0, y1, z0 + MERLON_H - m, z0 + MERLON_H, mat, bevel=False)


def wall_module(variant, materials, col, rng):
    kit = Kit([])
    L = CHORD
    ta = tan(HALF)
    g0, g1 = RUNE_Z - RUNE_W / 2, RUNE_Z + RUNE_W / 2
    yr = Y_IN + RUNE_D
    yo = Y_OUT - RUNE_D
    prof = [(Y_IN, -0.5), (Y_OUT_BASE, -0.5), (Y_OUT_BASE, 0.0), (Y_OUT, TALUD_H),
            (Y_OUT, g0), (yo, g0), (yo, g1), (Y_OUT, g1),                       # surco exterior (4..6)
            (Y_OUT, WALK_Z + PARAPET_H),
            (Y_OUT - PARAPET_T, WALK_Z + PARAPET_H), (Y_OUT - PARAPET_T, WALK_Z), (Y_IN, WALK_Z),
            (Y_IN, g1), (yr, g1), (yr, g0), (Y_IN, g0)]                         # surco interior (12..14)
    n = len(prof)
    pts = []
    for sgn in (-1, 1):
        for y, z in prof:
            pts.append((sgn * (L / 2 + y * ta), y, z))
    faces = [tuple(range(n - 1, -1, -1)), tuple(range(n, 2 * n))]
    side = [(i, (i + 1) % n, n + (i + 1) % n, n + i) for i in range(n)]
    faces += side
    fm = ["MAT_Wall_Granite"] * len(faces)
    for rune_face in (2 + 5, 2 + 13):                  # fondo de los dos surcos
        fm[rune_face] = "MAT_Wall_Runes"
    groove = {2 + 4, 2 + 5, 2 + 6, 2 + 12, 2 + 13, 2 + 14}
    kit.add(pts, faces, None, face_mats=fm, no_bevel_faces=groove)
    xs = merlon_positions(L)
    slit_idx = set()
    for target in range(-int(L // SLIT_EVERY) * 2, int(L // SLIT_EVERY) * 2 + 1):
        t = target * SLIT_EVERY
        if abs(t) <= xs[-1] + 0.5:
            slit_idx.add(min(range(len(xs)), key=lambda i: abs(xs[i] - t)))
    for i, x in enumerate(xs):
        merlon(kit, x, Y_OUT - PARAPET_T, Y_OUT, WALK_Z + PARAPET_H, "MAT_Wall_Granite", slit=i in slit_idx)
    info = {"merlons": len(xs), "slits": len(slit_idx)}
    if variant in ("B", "C"):
        npatch = rng.choice([2, 3])
        used = []
        for _ in range(npatch):
            for _try in range(20):
                w, h = rng.uniform(2.0, 4.0), rng.uniform(1.8, 3.2)
                x = rng.uniform(-L / 2 + END_CLEAR + w / 2, L / 2 - END_CLEAR - w / 2)
                z = rng.uniform(RUNE_Z + 0.35, WALK_Z - h - 0.6)        # por encima del anillo de runas
                if all(abs(x - ux) > (w + uw) / 2 + 0.5 for ux, uw in used):
                    break
            used.append((x, w))
            kit.box(x - w / 2, x + w / 2, Y_OUT, Y_OUT + 0.04, z, z + h, "MAT_Wall_Patch")
            if variant == "B" and len(used) <= 3:
                kit.box(x - w / 2 - 0.4, x + w / 2 + 0.4, Y_OUT - 0.15, Y_OUT + 0.18, z + h, z + h + 0.3,
                        "MAT_Wood_Dark")
        inner = rng.uniform(-L / 2 + 5, L / 2 - 5)
        kit.box(inner - 1.5, inner + 1.5, Y_IN - 0.04, Y_IN, RUNE_Z + 0.7, RUNE_Z + 3.3, "MAT_Wall_Patch")
        info["patches"] = npatch + 1
    if variant == "C":
        z0 = WALK_Z - 0.25
        built = 0.6                                   # hourde a medio terminar: 60 % de vigas con suelo
        xs_all = [x - (MERLON_W + CRENEL_W) / 2 for x in xs] + [xs[-1] + (MERLON_W + CRENEL_W) / 2]
        lim = -L / 2 + END_CLEAR + built * (L - 2 * END_CLEAR)
        for i, xj in enumerate(xs_all):
            kit.box(xj - 0.1, xj + 0.1, Y_OUT - PARAPET_T, Y_OUT + 1.6, z0, z0 + 0.25, "MAT_Wood_Dark")
            if xj <= lim and i % 2 == 0:
                kit.box(xj - 0.1, xj + 0.1, Y_OUT + 1.35, Y_OUT + 1.55, z0 + 0.25, z0 + 2.9, "MAT_Wood_Dark")
        xa, xb = xs_all[0] - 0.1, lim
        kit.box(xa, xb, Y_OUT, Y_OUT + 1.6, z0 + 0.25, z0 + 0.31, "MAT_Wood_Dark")
        kit.box(xa, lim - 4.0, Y_OUT + 1.3, Y_OUT + 1.6, z0 + 2.9, z0 + 3.1, "MAT_Wood_Dark")
        for i, xj in enumerate(xs_all):
            if xj <= lim - 4.0 and i % 2 == 0:
                c = Vector((xj, (Y_OUT + 1.45 + Y_OUT - 0.2) / 2, 0))
                kit.obox((c.x, c.y, z0 + 3.1), (0.08, 0, 0), (0, 0.9, 0), 0.12, "MAT_Wood_Dark", bevel=False)
        info["hourde_built_fraction"] = built
    obj = kit.to_object(f"WALL_Mod_{variant}", col, materials)
    return obj, info


def bastion(materials, col, mirador=False):
    kit = Kit([])
    R = BASTION_D / 2
    cy = Y_OUT
    seg = 12
    arc = [(R * cos(pi * i / seg), cy + R * sin(pi * i / seg)) for i in range(seg + 1)]
    foot = [(-R, Y_OUT - PARAPET_T), (R, Y_OUT - PARAPET_T)] + arc
    pts = [(x, y, -1.0) for x, y in foot] + [(x, y, BASTION_PLAT) for x, y in foot]
    n = len(foot)
    faces = [tuple(range(n - 1, -1, -1)), tuple(range(n, 2 * n))]
    faces += [(i, (i + 1) % n, n + (i + 1) % n, n + i) for i in range(n)]
    kit.add(pts, faces, "MAT_Wall_Granite")
    ri = R - 0.5
    gap_mid = mirador
    ring = []
    for i in range(seg + 1):
        t = pi * i / seg
        ring.append(((R * cos(t), cy + R * sin(t)), (ri * cos(t), cy + ri * sin(t))))
    for i in range(seg):
        tm = pi * (i + 0.5) / seg
        if gap_mid and abs(tm - pi / 2) < 0.35:
            continue
        (o0, i0), (o1, i1) = ring[i], ring[i + 1]
        p = [(o0[0], o0[1]), (o1[0], o1[1]), (i1[0], i1[1]), (i0[0], i0[1])]
        pts = [(x, y, BASTION_PLAT) for x, y in p] + [(x, y, BASTION_PLAT + PARAPET_H) for x, y in p]
        kit.add(pts, [(3, 2, 1, 0), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)],
                "MAT_Wall_Granite", bevel=False)
    n_m = 5
    for k in range(n_m):
        t = pi / 2 + (k - (n_m - 1) / 2) * (MERLON_W + CRENEL_W) / (R - 0.25)
        if mirador and abs(t - pi / 2) < 0.35:
            continue
        c = Vector((cos(t) * (R - 0.25), cy + sin(t) * (R - 0.25), 0))
        rad = Vector((cos(t), sin(t), 0))
        tan_ = Vector((-sin(t), cos(t), 0))
        kit.obox((c.x, c.y, BASTION_PLAT + PARAPET_H), tan_ * (MERLON_W / 2), rad * 0.25, MERLON_H,
                 "MAT_Wall_Granite")
    info = {"merlons": n_m - (1 if mirador else 0)}
    if mirador:
        w, d = MIRADOR
        y0, y1 = cy + R - 0.2, cy + R - 0.2 + d
        zt = BASTION_PLAT
        kit.box(-w / 2, w / 2, y0, y1, zt - 0.35, zt, "MAT_Wall_Granite")
        for x in (-w / 2 + 0.3, 0.0, w / 2 - 0.3):
            kit.prism([(y0, zt - 0.35), (y1 - 0.3, zt - 0.35), (y0, zt - 2.2)], (x, 0, 0), (0, 1, 0), (1, 0, 0),
                      -0.25, 0.25, "MAT_Wall_Granite")
        pt = 0.3
        kit.box(-w / 2, w / 2, y1 - pt, y1, zt, zt + PARAPET_H, "MAT_Wall_Granite")
        kit.box(-w / 2, -w / 2 + pt, y0, y1 - pt, zt, zt + PARAPET_H, "MAT_Wall_Granite")
        kit.box(w / 2 - pt, w / 2, y0, y1 - pt, zt, zt + PARAPET_H, "MAT_Wall_Granite")
        info["balcony_m"] = [w, d]
    name = "BASTION_Mirador" if mirador else "BASTION_Open"
    return kit.to_object(name, col, materials), info


def guard_tower(materials, col, patched=False):
    kit = Kit([])
    R = TOWER_D / 2
    seg = 24
    cy = TOWER_CY
    prof = [(0.0, -3.0), (R + 0.3, -3.0), (R, 1.5), (R, TOWER_H - 0.6), (R + 0.4, TOWER_H - 0.3),
            (R + 0.4, TOWER_H), (0.0, TOWER_H)]
    kit.lathe(prof, 0.0, cy, seg, "MAT_Wall_Granite")
    re = R + 0.5
    apex = TOWER_H + re * tan(radians(ROOF_PITCH))
    r_top = 0.5
    z_top = apex - r_top * tan(radians(ROOF_PITCH))
    kit.lathe([(0.0, TOWER_H - 0.05), (re, TOWER_H - 0.05), (re, TOWER_H + 0.15), (r_top, z_top + 0.15),
               (0.0, z_top + 0.15)], 0.0, cy, seg, "MAT_Roof_Slate", part_kind="cone")
    lz0, lz1 = z_top + 0.15, z_top + 0.15 + LANTERN_H
    kit.lathe([(0.0, lz0), (0.42, lz0), (0.42, lz1), (0.0, lz1)], 0.0, cy, 8, "MAT_Magic_Glow25", part_kind=None,
              bevel=False)
    for a in range(4):
        t = pi / 4 + a * pi / 2
        kit.box(0.42 * cos(t) - 0.05, 0.42 * cos(t) + 0.05, cy + 0.42 * sin(t) - 0.05, cy + 0.42 * sin(t) + 0.05,
                lz0, lz1, "MAT_Iron_Black", bevel=False)
    kit.lathe([(0.0, lz1), (0.6, lz1), (0.0, lz1 + 0.7)], 0.0, cy, 8, "MAT_Roof_Slate", part_kind=None, bevel=False)
    kit.box(-0.04, 0.04, cy - 0.04, cy + 0.04, lz1 + 0.6, lz1 + 1.3, "MAT_Iron_Black", bevel=False)
    # saeteras en el cuerpo (huecos oscuros a ras)
    for tier, z in enumerate((8.0, 13.0, 18.0)):
        for k in range(4):
            t = radians(45 + 90 * k + 22.5 * tier)
            c = Vector((R * cos(t), cy + R * sin(t), 0)) * 1.0
            c = Vector((c.x, c.y, 0)) + Vector((cos(t), sin(t), 0)) * 0.01
            kit.obox((c.x, c.y, z), Vector((-sin(t), cos(t), 0)) * (SLIT_W / 2), Vector((cos(t), sin(t), 0)) * 0.01,
                     SLIT_H, "MAT_Void", bevel=False)
    # puerta de acceso a nivel del camino de ronda (cara que mira al camino, -Y local)
    yd = cy - R
    kit.box(-DOOR_W / 2, DOOR_W / 2, yd - 0.05, yd + 0.35, WALK_Z, WALK_Z + DOOR_H, "MAT_Wood_Dark", bevel=False)
    for sx in (-1, 1):
        x0, x1 = sorted((sx * DOOR_W / 2, sx * (DOOR_W / 2 + 0.25)))
        kit.box(x0, x1, yd - 0.12, yd + 0.45, WALK_Z, WALK_Z + DOOR_H, "MAT_Stone_Band")
    kit.box(-DOOR_W / 2 - 0.25, DOOR_W / 2 + 0.25, yd - 0.12, yd + 0.45, WALK_Z + DOOR_H, WALK_Z + DOOR_H + 0.3,
            "MAT_Stone_Band")
    kit.box(-DOOR_W / 2 - 0.25, DOOR_W / 2 + 0.25, yd - 0.35, yd + 0.3, WALK_Z - 0.1, WALK_Z + 0.02,
            "MAT_Stone_Band", bevel=False)
    info = {"apex_z": round(apex, 2), "lantern_z": [round(lz0, 2), round(lz1, 2)], "top_z": round(lz1 + 1.3, 2),
            "door": {"w": DOOR_W, "h": DOOR_H, "sill_z": WALK_Z, "local_pos": [0.0, round(yd - 0.05, 3), WALK_Z]}}
    if patched:
        rng = random.Random(SEED + 7)
        for k, mat in enumerate(["MAT_Roof_TileOchre"] * 3 + ["MAT_Wood_Dark"] * 2):
            a0 = rng.uniform(0, 2 * pi)
            da = rng.uniform(0.35, 0.6)
            s0, s1 = rng.uniform(0.25, 0.55), rng.uniform(0.6, 0.85)
            pts = []
            for s in (s0, s1):
                r = re - (re - r_top) * s + 0.04
                z = TOWER_H + 0.15 + (z_top - TOWER_H) * s
                for a in (a0, a0 + da / 2, a0 + da):
                    pts.append((r * cos(a), cy + r * sin(a), z))
            kit.add(pts, [(0, 1, 4, 3), (1, 2, 5, 4)], mat, bevel=False, recalc=False,
                    part=kit.part("cone", 0.0, cy, [(re, 0.0)]))
        info["roof_patches"] = 5
    name = "TOWER_Guard_Patched" if patched else "TOWER_Guard_Roof"
    return kit.to_object(name, col, materials), info


def arch_curve(n=12):
    half = GATE_ARCH_W / 2
    R = GATE_ARCH_W
    spring = GATE_ARCH_H - sqrt(R * R - half * half)
    left = []
    for i in range(n + 1):
        t = radians(180 - 60 * i / n)
        left.append((half + R * cos(t), spring + R * sin(t)))
    return left, spring


def gate(materials, col):
    kit = Kit([])
    R = GATE_TOWER_D / 2
    seg = 12
    band = lambda z: "MAT_Stone_Band" if (z % 3.0) < 0.6 and 0.0 < z < GATE_TOWER_H - 3 else "MAT_Wall_Granite"
    zp = GATE_TOWER_H - PARAPET_H - MERLON_H
    prof = [(0.0, -3.0), (R + 0.6, -3.0), (R, 2.0)]
    z = 3.0
    while z < zp:
        prof += [(R, z), (R, min(z + 0.6, zp))]
        z += 3.0
    prof += [(R, zp), (0.0, zp)]
    info = {"tower_top": GATE_TOWER_H}
    for sx in (-1, 1):
        cx = sx * (GATE_ARCH_W / 2 + R)
        kit.lathe(prof, cx, Y_OUT, seg, "MAT_Wall_Granite", face_mat_fn=band, rot=pi / seg)
        ap = R * cos(pi / seg)
        for k in range(seg):
            t = 2 * pi * k / seg + pi / seg + pi / seg
            mid = Vector((cx + ap * cos(t), Y_OUT + ap * sin(t), 0))
            inward = Vector((-cos(t), -sin(t), 0))
            tang = Vector((-sin(t), cos(t), 0))
            c = mid + inward * 0.3
            pts = [c - tang * (R * sin(pi / seg)) - inward * 0.3, c + tang * (R * sin(pi / seg)) - inward * 0.3,
                   c + tang * (R * sin(pi / seg) - 0.35) + inward * 0.3, c - tang * (R * sin(pi / seg) - 0.35) + inward * 0.3]
            pp = [(p.x, p.y, zp) for p in pts] + [(p.x, p.y, zp + PARAPET_H) for p in pts]
            kit.add(pp, [(3, 2, 1, 0), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)],
                    "MAT_Wall_Granite", bevel=False)
            for off in (-0.8, 0.8):
                mc = c + tang * off
                kit.obox((mc.x, mc.y, zp + PARAPET_H), tang * (MERLON_W / 2), inward * 0.3, MERLON_H,
                         "MAT_Wall_Granite")
    # cuerpo central sobre el arco
    bx = GATE_ARCH_W / 2 + 2.0
    by = GATE_BLOCK_Y
    left, spring = arch_curve()
    half = GATE_ARCH_W / 2
    for sy in (1, -1):
        y = sy * by
        # pano de piedra (dos mitades con el hueco del arco)
        lp = [(-bx, -1.0), (-half, -1.0)] + left + [(0.0, GATE_WALK), (-bx, GATE_WALK)]
        rp = [(-x, z) for x, z in reversed(lp)]
        for poly in (lp, rp):
            kit._plate(poly, y - sy * 0.6, y, "MAT_Wall_Granite", bevel=False)
        kit._plate([(-half, -1.0), (half, -1.0), (half, 0.0), (-half, 0.0)], y - sy * 0.6, y, "MAT_Wall_Granite",
                   bevel=False)
        # hojas de hierro a ras
        leaf_l = [(-half, 0.0), (0.0, 0.0), (0.0, GATE_ARCH_H)] + list(reversed(left))
        for poly in (leaf_l, [(-x, z) for x, z in reversed(leaf_l)]):
            kit._plate(poly, y - sy * 0.6, y - sy * 0.0, "MAT_Iron_Black", bevel=False)
        # flejes y cubrejuntas
        for zf in (1.4, 3.8, 6.2, 8.4):
            zt_ = zf + 0.15
            xa = (half - sqrt(GATE_ARCH_W ** 2 - (zt_ - spring) ** 2)) if zt_ > spring else -half
            kit.box(xa + 0.15, -xa - 0.15, min(y, y + sy * 0.03), max(y, y + sy * 0.03), zf, zf + 0.15,
                    "MAT_Iron_Black", bevel=False)
        kit.box(-0.08, 0.08, min(y, y + sy * 0.04), max(y, y + sy * 0.04), 0.0, GATE_ARCH_H - 0.3, "MAT_Iron_Black",
                bevel=False)
        # arquivolta clara
        outer = []
        for x, z in left:
            cxa, cza = half, spring
            v = Vector((x - cxa, z - cza))
            v = v.normalized() * (v.length + 0.6)
            outer.append((cxa + v.x, cza + v.y))
        band_l = [(-half - 0.6, 0.0), (-half, 0.0)] + left + [(0.0, GATE_ARCH_H + 0.6)] + list(reversed(outer))
        for poly in (band_l, [(-x, z) for x, z in reversed(band_l)]):
            kit._plate(poly, y, y + sy * 0.15, "MAT_Stone_Band", bevel=False)
        # runa central de 1.5 m
        rz = 5.0
        rr = GATE_RUNE_D / 2
        yr0, yr1 = y + sy * 0.04, y + sy * 0.07
        ring_o = [(rr * cos(2 * pi * i / 32), rz + rr * sin(2 * pi * i / 32)) for i in range(32)]
        for i in range(32):
            a, b = ring_o[i], ring_o[(i + 1) % 32]
            ai = (a[0] * 0.88, rz + (a[1] - rz) * 0.88)
            bi = (b[0] * 0.88, rz + (b[1] - rz) * 0.88)
            kit._plate([a, b, bi, ai], yr0, yr1, "MAT_Magic_Glow25", bevel=False)
        kit._plate([(-0.05, rz - 0.62), (0.05, rz - 0.62), (0.05, rz + 0.62), (-0.05, rz + 0.62)], yr0, yr1,
                   "MAT_Magic_Glow25", bevel=False)
        for sxx in (-1, 1):
            kit._plate([(0.0, rz + 0.15), (sxx * 0.45, rz + 0.45), (sxx * 0.45, rz + 0.33), (0.0, rz + 0.03)][::sxx],
                       yr0, yr1, "MAT_Magic_Glow25", bevel=False)
    # techo del cuerpo central (adarve de la puerta) + parapetos almenados a ambos lados
    kit.box(-bx, bx, -by + 0.61, by - 0.61, GATE_WALK - 0.4, GATE_WALK, "MAT_Wall_Granite")   # dentro de los panos
    for sy in (1, -1):
        y0, y1 = sorted((sy * by, sy * (by - PARAPET_T)))
        kit.box(-bx, bx, y0, y1, GATE_WALK, GATE_WALK + PARAPET_H, "MAT_Wall_Granite", bevel=False)
        for x in (-3.2, -1.6, 0.0, 1.6, 3.2):
            merlon(kit, x, y0, y1, GATE_WALK + PARAPET_H, "MAT_Wall_Granite")
    left_, spring = arch_curve()
    info.update({"arch_w": GATE_ARCH_W, "arch_h": GATE_ARCH_H, "arch_spring_z": round(spring, 2),
                 "gate_walk_z": GATE_WALK, "rune_d": GATE_RUNE_D})
    return kit.to_object("GATE_Sealed_Twin", col, materials), info


def stair(materials, col, mirror=False):
    """Escalera en dos tramos (ida y vuelta) adosada a la cara interior junto a la puerta.
    Local: X a lo largo del muro (la puerta queda hacia +X en L), Y=+3 contra el muro."""
    kit = Kit([])
    n, r, t = STAIR_N, STAIR_RISER, STAIR_TREAD
    run = (n - 1) * t
    x0 = -run / 2 - 1.6
    xl = x0 + run                                       # ultima contrahuella del tramo A
    x_end = xl + 3.4                                    # rellano intermedio
    zf = -0.6
    zl = n * r
    # tramo A (Y -3..0): sube hacia la puerta
    pa = [(x0, zf), (x_end, zf), (x_end, zl)]
    for i in range(n - 1, -1, -1):
        pa += [(x0 + i * t, (i + 1) * r), (x0 + i * t, i * r)]
    # tramo B (Y 0..3): sube alejandose de la puerta
    pb = [(x_end, zf), (x_end, zl)]
    for i in range(n):
        xb = xl - i * t
        pb += [(xb, zl + i * r), (xb, zl + (i + 1) * r)]
    xb_top = xl - (n - 1) * t - 0.6
    pb += [(xb_top, 2 * zl), (xb_top, zf)]
    sgn = -1 if mirror else 1

    def mir(poly):
        return [(sgn * x, z) for x, z in (poly if not mirror else list(reversed(poly)))]
    kit.prism(mir(pa), (0, 0, 0), (1, 0, 0), (0, 1, 0), -STAIR_W, 0.0, "MAT_Wall_Granite", bevel=False)
    kit.prism(mir(pb), (0, 0, 0), (1, 0, 0), (0, 1, 0), 0.0, STAIR_W, "MAT_Wall_Granite", bevel=False)
    obj = kit.to_object("STAIR_Gate_R" if mirror else "STAIR_Gate_L", col, materials)
    return obj, {"risers": 2 * n, "riser_m": round(r, 3), "tread_m": t, "width_m": STAIR_W,
                 "footprint_x": [round(min(xb_top, x0), 2), round(x_end, 2)], "top_z": round(2 * zl, 2)}


def drain(materials, col):
    kit = Kit([])
    w, h = DRAIN_W, DRAIN_H
    kit.box(-w / 2 - 0.1, w / 2 + 0.1, -0.30, -0.25, 0.0, h, "MAT_Void", bevel=False)
    for sx in (-1, 1):
        kit.box(sx * w / 2 - (0.1 if sx < 0 else 0), sx * w / 2 + (0.1 if sx > 0 else 0), -0.25, 0.05, 0.0, h,
                "MAT_Void", bevel=False)
    kit.box(-w / 2, w / 2, -0.25, 0.05, h, h + 0.1, "MAT_Void", bevel=False)
    kit.box(-w / 2 - 0.08, w / 2 + 0.08, 0.0, 0.08, h - 0.08, h + 0.02, "MAT_Iron_Black", bevel=False)
    kit.box(-w / 2 - 0.08, w / 2 + 0.08, 0.0, 0.08, 0.0, 0.08, "MAT_Iron_Black", bevel=False)
    for sx in (-1, 1):
        kit.box(sx * (w / 2) - 0.04, sx * (w / 2) + 0.04, 0.0, 0.08, 0.0, h, "MAT_Iron_Black", bevel=False)
    for i in range(1, 9):
        x = -w / 2 + i * w / 9
        kit.box(x - 0.025, x + 0.025, 0.01, 0.06, 0.05, h - 0.05, "MAT_Iron_Black", bevel=False)
    kit.box(-w / 2, w / 2, 0.01, 0.06, h / 2 - 0.03, h / 2 + 0.03, "MAT_Iron_Black", bevel=False)
    return kit.to_object("WALL_Drain_Grate", col, materials), {"w": w, "h": h}


# ---------------------------------------------------------------------------
# Colisiones simples (Godot: sufijo -colonly)
# ---------------------------------------------------------------------------
def collision_mesh(name, kind):
    bm = bmesh.new()

    def prism(poly, z0, z1):
        vs = [bm.verts.new((x, y, z0)) for x, y in poly] + [bm.verts.new((x, y, z1)) for x, y in poly]
        n = len(poly)
        bm.faces.new(vs[:n][::-1])
        bm.faces.new(vs[n:])
        for i in range(n):
            j = (i + 1) % n
            bm.faces.new((vs[i], vs[j], vs[n + j], vs[n + i]))

    def circle(cx, cy, r, n=16):
        return [(cx + r * cos(2 * pi * i / n), cy + r * sin(2 * pi * i / n)) for i in range(n)]

    if kind == "module":
        L, ta = CHORD, tan(HALF)
        def xe(y):
            return L / 2 + y * ta
        prism([(-xe(Y_IN), Y_IN), (xe(Y_IN), Y_IN), (xe(Y_OUT), Y_OUT), (-xe(Y_OUT), Y_OUT)], 0.0, WALK_Z)
        prism([(-xe(0), 0.0), (xe(0), 0.0), (xe(Y_OUT), Y_OUT), (-xe(Y_OUT), Y_OUT)], WALK_Z, WALL_H)
    elif kind == "bastion":
        R = BASTION_D / 2
        prism([(-R, 0.0), (R, 0.0)] + [(R * cos(pi * i / 8), Y_OUT + R * sin(pi * i / 8)) for i in range(9)],
              -1.0, BASTION_H)
    elif kind == "tower":
        prism(circle(0.0, TOWER_CY, TOWER_D / 2), -3.0, TOWER_H)
    elif kind == "gate":
        for sx in (-1, 1):
            prism(circle(sx * (GATE_ARCH_W / 2 + GATE_TOWER_D / 2), Y_OUT, GATE_TOWER_D / 2, 12), -3.0, GATE_TOWER_H)
        bx = GATE_ARCH_W / 2 + 2.0
        prism([(-bx, -GATE_BLOCK_Y), (bx, -GATE_BLOCK_Y), (bx, GATE_BLOCK_Y), (-bx, GATE_BLOCK_Y)], -1.0,
              GATE_WALK + PARAPET_H)
    elif kind in ("stair_L", "stair_R"):
        s = -1 if kind == "stair_R" else 1
        n, r, t = STAIR_N, STAIR_RISER, STAIR_TREAD
        run = (n - 1) * t
        x0 = -run / 2 - 1.6
        xl, x_end = x0 + run, x0 + run + 3.4
        zl = n * r
        for (xa, za, xb, zb, y0, y1) in ((x0, 0.0, xl, zl, -STAIR_W, 0.0), (xl, zl, xl - run - 0.6, 2 * zl, 0.0, STAIR_W)):
            vs = [bm.verts.new((s * x, y, z)) for x, y, z in
                  ((xa, y0, -0.6), (xb, y0, -0.6), (xb, y0, zb), (xa, y0, za),
                   (xa, y1, -0.6), (xb, y1, -0.6), (xb, y1, zb), (xa, y1, za))]
            for f in ((0, 1, 2, 3), (7, 6, 5, 4), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)):
                bm.faces.new([vs[i] for i in f])
        prism([(s * xl, -STAIR_W), (s * x_end, -STAIR_W), (s * x_end, STAIR_W), (s * xl, STAIR_W)], -0.6, zl)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    return me


# ---------------------------------------------------------------------------
# Montaje
# ---------------------------------------------------------------------------
def slot_type(k):
    if k % 12 == 0:
        return "gate"
    if k % 4 == 0:
        return "tower"
    return "mirador" if k in (6, 18, 30, 42) else "bastion"


def slot_matrix(angle_deg, r, z=C.DATUM):
    a = radians(angle_deg)
    return Matrix.Translation((r * cos(a), r * sin(a), z)) @ Matrix.Rotation(radians(angle_deg - 90.0), 4, "Z")


def quotas(n, fracs):
    raw = [n * f for f in fracs]
    base = [int(x) for x in raw]
    order = sorted(range(len(fracs)), key=lambda i: -(raw[i] - base[i]))
    for i in order[:n - sum(base)]:
        base[i] += 1
    return base


def instance(name, mesh_obj, matrix, col, col_mesh=None):
    if name in bpy.data.objects:
        bpy.data.objects.remove(bpy.data.objects[name])
    o = bpy.data.objects.new(name, mesh_obj.data)
    o.matrix_world = matrix
    col.objects.link(o)
    if col_mesh is not None:
        cn = f"{name}-colonly"
        if cn in bpy.data.objects:
            bpy.data.objects.remove(bpy.data.objects[cn])
        c = bpy.data.objects.new(cn, col_mesh)
        col.objects.link(c)
        c.parent = o
        c.display_type = "WIRE"
        c.hide_render = True
    return o


def build(scene, stats):
    mats = build_materials()
    kit_col = bpy.data.collections["WALL_KIT"]
    lay_col = bpy.data.collections["WALL_LAYOUT"]
    for col in (kit_col, lay_col):
        for o in list(col.objects):
            if not o.name.startswith("MARKER_Gate_"):
                bpy.data.objects.remove(o)
    rng = random.Random(SEED)
    pieces, info = {}, {}
    for v in ("A", "B", "C"):
        pieces[f"WALL_Mod_{v}"], info[f"WALL_Mod_{v}"] = wall_module(v, mats, kit_col, rng)
    pieces["BASTION_Open"], info["BASTION_Open"] = bastion(mats, kit_col)
    pieces["BASTION_Mirador"], info["BASTION_Mirador"] = bastion(mats, kit_col, mirador=True)
    pieces["TOWER_Guard_Roof"], info["TOWER_Guard_Roof"] = guard_tower(mats, kit_col)
    pieces["TOWER_Guard_Patched"], info["TOWER_Guard_Patched"] = guard_tower(mats, kit_col, patched=True)
    pieces["GATE_Sealed_Twin"], info["GATE_Sealed_Twin"] = gate(mats, kit_col)
    pieces["GATE_Sealed_Twin"]["nav_exclude"] = "adarve (+15.05) decorativo: no conectar a la navegacion"
    pieces["STAIR_Gate_L"], info["STAIR_Gate_L"] = stair(mats, kit_col)
    pieces["STAIR_Gate_R"], info["STAIR_Gate_R"] = stair(mats, kit_col, mirror=True)
    pieces["WALL_Drain_Grate"], info["WALL_Drain_Grate"] = drain(mats, kit_col)
    budgets = {"WALL_Mod_A": 3000, "WALL_Mod_B": 3000, "WALL_Mod_C": 3000, "BASTION_Open": 1200,
               "BASTION_Mirador": 1200, "TOWER_Guard_Roof": 5000, "TOWER_Guard_Patched": 5000,
               "GATE_Sealed_Twin": 12000, "STAIR_Gate_L": 1500, "STAIR_Gate_R": 1500, "WALL_Drain_Grate": 1500}
    colk = {"WALL_Mod_A": "module", "WALL_Mod_B": "module", "WALL_Mod_C": "module", "BASTION_Open": "bastion",
            "BASTION_Mirador": "bastion", "TOWER_Guard_Roof": "tower", "TOWER_Guard_Patched": "tower",
            "GATE_Sealed_Twin": "gate", "STAIR_Gate_L": "stair_L", "STAIR_Gate_R": "stair_R"}
    col_meshes = {k: collision_mesh(f"{k}-colonly", v) for k, v in colk.items()}
    # exposicion del kit fuera de la ciudad (fila en Y = -330) + colisiones hijas + LODs
    lod_col = bpy.data.collections.get("WALL_KIT_LODS")
    if lod_col is None:
        lod_col = bpy.data.collections.new("WALL_KIT_LODS")
        kit_col.children.link(lod_col)
    for o in list(lod_col.objects):
        bpy.data.objects.remove(o)
    report = {}
    for i, (name, obj) in enumerate(pieces.items()):
        obj.location = (-250.0 + i * 50.0, -330.0, 0.0)
        obj["budget_tris"] = budgets[name]
        tris = len(obj.data.polygons)
        if name in col_meshes:
            c = bpy.data.objects.new(f"{name}-colonly", col_meshes[name])
            kit_col.objects.link(c)
            c.parent = obj
            c.display_type = "WIRE"
            c.hide_render = True
        if name.startswith("TOWER_Guard"):
            dn = f"{name}_MARKER_Door"
            if dn in bpy.data.objects:
                bpy.data.objects.remove(bpy.data.objects[dn])
            de = bpy.data.objects.new(dn, None)
            de.empty_display_type = "ARROWS"
            kit_col.objects.link(de)
            de.parent = obj
            de.matrix_parent_inverse = Matrix.Identity(4)
            de.location = (0.0, TOWER_CY - TOWER_D / 2 - 0.05, WALK_Z)
            de.rotation_euler = (0.0, 0.0, pi)
            de["door_direction"] = "+Y"
        lods = {}
        for lod, ratio in (("LOD1", 0.5), ("LOD2", 0.15)):
            lo = bpy.data.objects.new(f"{name}_{lod}", obj.data.copy())
            lo.data.name = lo.name
            lo.location = obj.location + Vector((0, 40 if lod == "LOD1" else 80, 0))
            lod_col.objects.link(lo)
            m = lo.modifiers.new("dec", "DECIMATE")
            m.ratio = ratio
            dg = bpy.context.evaluated_depsgraph_get()
            new = bpy.data.meshes.new_from_object(lo.evaluated_get(dg))
            old = lo.data
            lo.modifiers.clear()
            lo.data = new
            new.name = lo.name
            bpy.data.meshes.remove(old)
            lods[lod] = len(new.polygons)
        zs = [v.co.z for v in obj.data.vertices]
        report[name] = {"tris": tris, "budget": budgets[name], "ok": tris <= budgets[name], "lods": lods,
                        "z_max": round(max(zs), 3), "z_min": round(min(zs), 3), **info[name]}
    lod_col.hide_render = True

    # --- montaje: 48 slots, 48 modulos, escaleras y reja
    mod_q = quotas(N_SLOTS, (0.7, 0.2, 0.1))
    mods = ["A"] * mod_q[0] + ["B"] * mod_q[1] + ["C"] * mod_q[2]
    random.Random(SEED).shuffle(mods)
    tow_q = quotas(8, (0.7, 0.3))
    tows = ["Roof"] * tow_q[0] + ["Patched"] * tow_q[1]
    random.Random(SEED).shuffle(tows)
    layout = {"slots": [], "modules": [], "counts": {}}
    ti = 0
    cam = bpy.data.objects[C.CAM_ISO_NAME]
    dview = cam.rotation_euler.to_matrix() @ Vector((0, 0, -1))
    to_cam = Vector((-dview.x, -dview.y, 0.0)).normalized()
    for k in range(N_SLOTS):
        ang = k * STEP_DEG
        typ = slot_type(k)
        mname = f"MARKER_WallSlot_{k:02d}"
        if mname in bpy.data.objects:
            bpy.data.objects.remove(bpy.data.objects[mname])
        e = bpy.data.objects.new(mname, None)
        e.empty_display_type = "ARROWS"
        e.empty_display_size = 3.0
        e.matrix_world = slot_matrix(ang, C.WALL_RADIUS)
        lay_col.objects.link(e)
        if typ == "gate":
            piece = "GATE_Sealed_Twin"
        elif typ == "tower":
            piece = f"TOWER_Guard_{tows[ti]}"
            ti += 1
        elif typ == "mirador":
            piece = "BASTION_Mirador"
        else:
            piece = "BASTION_Open"
        e["k"], e["angle_deg"], e["type"], e["piece"] = k, ang, typ, piece
        inst = instance(f"{piece.split('_')[0]}_Slot{k:02d}_{piece.split('_', 1)[1]}", pieces[piece],
                        e.matrix_world.copy(), lay_col, col_meshes.get(piece))
        if typ == "gate":
            inst["nav_exclude"] = "adarve de la puerta (+15.05): terraza decorativa, fuera de la navegacion"
        if typ == "tower":
            dn = f"MARKER_TowerDoor_{k:02d}"
            if dn in bpy.data.objects:
                bpy.data.objects.remove(bpy.data.objects[dn])
            de = bpy.data.objects.new(dn, None)
            de.empty_display_type = "ARROWS"
            de.empty_display_size = 1.0
            de.matrix_world = e.matrix_world @ Matrix.Translation((0.0, TOWER_CY - TOWER_D / 2 - 0.05, WALK_Z)) \
                @ Matrix.Rotation(pi, 4, "Z")
            de["door_direction"] = "+Y"
            de["use"] = "acceso de NPC guardias desde el camino de ronda"
            de["tower_slot"] = k
            lay_col.objects.link(de)
        layout["slots"].append({"k": k, "angle": ang, "type": typ, "piece": piece})
        # modulo entre k y k+1
        v = mods[k]
        mm = slot_matrix(ang + STEP_DEG / 2, C.WALL_RADIUS * cos(HALF))
        mo = instance(f"WALL_Seg{k:02d}_{v}", pieces[f"WALL_Mod_{v}"], mm, lay_col, col_meshes[f"WALL_Mod_{v}"])
        am = radians(ang + STEP_DEG / 2)
        occl = (cos(am) * to_cam.x + sin(am) * to_cam.y) > 0.0
        mo["occludes_iso"] = bool(occl)
        layout["modules"].append({"from_k": k, "to_k": (k + 1) % N_SLOTS, "variant": v, "occludes_iso": bool(occl),
                                  "name": mo.name})
        if typ == "gate":
            # la torre de la puerta (r=6, centro a 10 m) llega en la cara interior (Y=-3) hasta:
            R6 = GATE_TOWER_D / 2
            x_clear = CHORD / 2 - (GATE_ARCH_W / 2 + R6) - sqrt(R6 ** 2 - (Y_IN - Y_OUT) ** 2) - 0.3
            sx_l = x_clear - STAIR_LANDING_END
            # modulo k -> k+1: la puerta esta en su extremo +X  -> escalera L
            m_after = slot_matrix(ang + STEP_DEG / 2, C.WALL_RADIUS * cos(HALF))
            instance(f"STAIR_Gate{k:02d}_L", pieces["STAIR_Gate_L"],
                     m_after @ Matrix.Translation((sx_l, Y_IN - STAIR_W, 0.0)), lay_col, col_meshes["STAIR_Gate_L"])
            m_before = slot_matrix(ang - STEP_DEG / 2, C.WALL_RADIUS * cos(HALF))
            instance(f"STAIR_Gate{k:02d}_R", pieces["STAIR_Gate_R"],
                     m_before @ Matrix.Translation((-sx_l, Y_IN - STAIR_W, 0.0)), lay_col, col_meshes["STAIR_Gate_R"])
    dm = slot_matrix(DRAIN_SLOT * STEP_DEG, C.WALL_RADIUS) @ Matrix.Translation((0.0, Y_OUT + BASTION_D / 2 - 0.02, 0.0))
    instance("WALL_Drain_Slot46", pieces["WALL_Drain_Grate"], dm, lay_col)
    from collections import Counter
    layout["counts"] = {"slots": N_SLOTS, "by_type": dict(Counter(s["type"] for s in layout["slots"])),
                        "by_piece": dict(Counter(s["piece"] for s in layout["slots"])),
                        "modules": dict(Counter(m["variant"] for m in layout["modules"])),
                        "module_quota_70_20_10": mod_q, "tower_quota_70_30": tow_q}
    layout["occludes_iso_modules"] = [m["name"] for m in layout["modules"] if m["occludes_iso"]]
    stats["wall_kit"] = report
    stats["wall_layout"] = layout
    stats["wall_dims"] = {"chord_m": round(CHORD, 4), "wall_top_z": WALL_H, "walkway_z": WALK_Z,
                          "parapet_z": [WALK_Z, WALK_Z + PARAPET_H], "merlon_z": [WALK_Z + PARAPET_H, WALL_H],
                          "base_t": BASE_T, "crown_t": WALK_W + PARAPET_T, "talud": [TALUD, TALUD_H],
                          "rune_line": {"z_center": RUNE_Z, "w": RUNE_W, "d": RUNE_D, "emission": RUNE_EMISSION}}
    return stats
