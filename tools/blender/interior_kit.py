"""
CONCORDIA - Etapa 27: kit de interiores (BLD_INT_KIT) y build_interior().

Referencias: Palazzo Pubblico de Siena (salas macizas, arcos), Westminster Hall (vigas a la vista), Rothenburg ob
der Tauber y Cesky Krumlov (entramado, vigas bajas, chimenea), Sainte-Chapelle (vitrales), Wieliczka (luz calida).

Convencion de los modulos del kit (grilla de 1 m, <= 300 triangulos cada uno):
  muros y piezas de muro: x en [0, ancho], cara visible en y = 0 mirando a +Y (hacia la sala), grosor hacia -Y,
  z en [0, alto]; suelos: x, y en [0, 2], cara superior en z = 0; vigas a lo largo de +X; escalera sube hacia +Y.

Escena de interior (una por edificio, int_<nombre>.glb):
  <ROOT> (origen en la puerta de entrada, piso en Z = 0, giro del edificio en el mundo)
    <ROOT>_Frame (desplazamiento: el marco centrado de la sala queda con la puerta en el origen)
      Shell            piso, muros del fondo, columnas, vigas (una malla por grupo al exportar)
      WALL_Near_A / B  los dos muros que quedan del lado de CAM_Iso (ocultables)
      CEILING          techo (ocultable)
      Furniture        props instanciados
      Lights           Empties: light_color, light_energy (Godot), light_range (m), light_kind
      Markers          MARKER_Interior_Exit / _Spawn, MARKER_NPC_Slot_xx, MARKER_Interact_xx, ...
      <ROOT>-colonly   colision simple (cajas y rampas)
      <ROOT>-navmesh   piso transitable (rejilla de 0.5 m, margen del agente 0.3 m)
"""

import math
import random

import bmesh
import bpy
from mathutils import Matrix, Vector
from mathutils.geometry import tessellate_polygon

import bld_kit as K

FH = 3.2
T = 0.4
CAM_BACK = Vector((0.577, -0.577, 0.577)).normalized()
KIT_MAX_TRIS = 300

STONE = "MAT_Limestone_Worn"
STONE_L = "MAT_Limestone_Light"
BLOCK = "MAT_Wall_Gray"
REPAIR = "MAT_Stone_Repair"
SLAB = "MAT_Plaza_Slab"
WOOD = "MAT_Wood_Dark"
WOOD_L = "MAT_Wood_Light"
IRON = "MAT_Iron_Black"
BRONZE = "MAT_Bronze_Aged"
WARM = "MAT_Window_Warm"
SHARD = "MAT_Shard_Blue"
ASH = "MAT_Ash_Gray"
CLOTH = ("MAT_Cloth_Patch_A", "MAT_Cloth_Patch_B", "MAT_Cloth_Patch_C")


# --------------------------------------------------------------------------- utilidades de malla
def prism(mb, prof, s0, s1, mat, axis="x"):
    """Perfil 2D extruido (tapas teseladas: perfiles concavos). axis='x': perfil (y, z) entre x=s0..s1;
    axis='y': perfil (x, z) entre y=s0..s1."""
    co = (lambda a, b, s: (s, a, b)) if axis == "x" else (lambda a, b, s: (a, s, b))
    pts = []
    for p in prof:
        if not pts or abs(pts[-1][0] - p[0]) > 1e-6 or abs(pts[-1][1] - p[1]) > 1e-6:
            pts.append(p)
    if len(pts) > 2 and abs(pts[0][0] - pts[-1][0]) < 1e-6 and abs(pts[0][1] - pts[-1][1]) < 1e-6:
        pts.pop()
    mi = mb.mi(mat)
    tri = tessellate_polygon([[Vector((a, b, 0.0)) for a, b in pts]])
    caps = [[mb.v(co(a, b, s)) for a, b in pts] for s in (s0, s1)]
    for k, vs in enumerate(caps):
        for t in tri:
            try:
                f = mb.bm.faces.new([vs[i] for i in (t if k else t[::-1])])
                f.material_index = mi
            except ValueError:
                pass
    a, b = caps
    for i in range(len(pts)):
        j = (i + 1) % len(pts)
        try:
            f = mb.bm.faces.new([a[i], a[j], b[j], b[i]])
            f.material_index = mi
        except ValueError:
            pass


def arc(cx, z_spring, r, a0=math.pi, a1=0.0, n=8):
    return [(cx + r * math.cos(a0 + (a1 - a0) * i / n), z_spring + r * math.sin(a0 + (a1 - a0) * i / n))
            for i in range(n + 1)]


def to_obj(mb, name, col, uv=True):
    import concordia_buildings as B
    mb.finish()
    o = B.to_object(mb, name, col)
    mb.bm.free()
    if uv:
        B.box_uv(o)
    return o


def tris(o):
    return sum(len(p.vertices) - 2 for p in o.data.polygons)


# --------------------------------------------------------------------------- modulos del kit
def m_floor_stone(mb, v, rng):
    """Losa de 2 x 2 m; la variante B lleva dos losas repuestas de caliza gastada (2 cm por encima)."""
    mb.box((0, 0, -0.12), (2, 2, 0), SLAB, skip=("z-",))
    if v:
        for _ in range(2):
            x, y = rng.uniform(0.1, 1.2), rng.uniform(0.1, 1.2)
            mb.box((x, y, 0), (x + rng.uniform(0.4, 0.7), y + rng.uniform(0.35, 0.6), 0.02), STONE, skip=("z-",))


def m_floor_planks(mb, v, rng):
    mb.box((0, 0, -0.14), (2, 2, -0.02), WOOD, skip=("z-", "z+"))
    n = 8
    for i in range(n):
        y0, y1 = 2.0 * i / n + 0.004, 2.0 * (i + 1) / n - 0.004
        mat = WOOD_L if (v and i == 2) else WOOD
        dz = 0.008 if (v and i == 5) else 0.0
        mb.face([(0, y0, dz), (2, y0, dz), (2, y1, dz), (0, y1, dz)], mat, nrm=(0, 0, 1))
        mb.face([(0, y0, -0.02), (2, y0, -0.02), (2, y0, dz), (0, y0, dz)], WOOD, nrm=(0, -1, 0))


def m_wall_stone(mb, v, rng, h=FH):
    """Sillares grandes (Porta Nigra): cara base + hiladas de bloques salientes 3 cm, juntas escalonadas."""
    mb.box((0, -T, 0), (2, 0, h), BLOCK, skip=("y-", "z-"))
    z = 0.0
    k = 0
    while z < h - 0.05:
        ch = min(0.8, h - z)
        xs = [0.0, 1.0, 2.0] if k % 2 == 0 else [0.0, 0.5, 1.5, 2.0]
        for i in range(len(xs) - 1):
            mat = REPAIR if (v and (k + i) % 4 == 1) else BLOCK
            out = 0.01 if (v and (k + i) % 5 == 3) else 0.03
            mb.box((xs[i] + 0.015, 0, z + 0.015), (xs[i + 1] - 0.015, out, z + ch - 0.015), mat, skip=("y-",))
        z += ch
        k += 1


def m_wall_plaster(mb, v, rng, h=FH):
    mb.box((0, -T, 0), (2, 0, h), STONE_L, skip=("y-", "z-"))
    mb.box((0, 0, 0), (2, 0.04, 0.28), STONE, skip=("y-", "z-"))
    if v:
        x, z = rng.uniform(0.2, 1.0), rng.uniform(0.9, 1.8)
        mb.box((x, 0, z), (x + 0.7, 0.02, z + 0.5), REPAIR, skip=("y-",))


def m_wall_panel(mb, v, rng, h=FH):
    """Revoco arriba y friso de tablas abajo (1.2 m) con 4 cuarterones; tabla de remiendo en la variante B."""
    mb.box((0, -T, 0), (2, 0, h), STONE_L, skip=("y-", "z-"))
    mb.box((0, 0, 0), (2, 0.03, 1.2), WOOD, skip=("y-", "z-"))
    mb.box((0, 0, 1.2), (2, 0.06, 1.28), WOOD, skip=("y-",))
    for i in range(4):
        x0 = 0.08 + i * 0.48
        mat = WOOD_L if (v and i == 2) else WOOD
        mb.box((x0, 0.03, 0.15), (x0 + 0.4, 0.05, 1.05), mat, skip=("y-",))


def m_trim(mb, v, rng):
    prism(mb, [(0, 0), (0.07, 0), (0.07, 0.05), (0.035, 0.09), (0.035, 0.16), (0, 0.16)], 0.0, 2.0, STONE, axis="x")


def m_beam_straight(mb, v, rng):
    mb.box((0, -0.125, -0.3), (2, 0.125, 0), WOOD)


def m_beam_cross(mb, v, rng):
    mb.box((0, -0.125, -0.3), (2, 0.125, 0), WOOD)
    mb.box((0.875, -1.0, -0.55), (1.125, 1.0, -0.3), WOOD)
    for s in (-1, 1):
        mb.rod((1.0, s * 0.95, -0.55), (1.0, s * 0.35, -1.05), 0.06, WOOD)


def m_pillar(mb, v, rng, h=FH):
    mb.box((-0.38, -0.38, 0), (0.38, 0.38, 0.28), STONE, skip=("z-",))
    mb.box((-0.3, -0.3, 0.28), (0.3, 0.3, h - 0.3), BLOCK, skip=("z-", "z+"))
    mb.box((-0.4, -0.4, h - 0.3), (0.4, 0.4, h), STONE)


def _arch_piece(mb, W, H, ow, spring, t, ring, mat=BLOCK):
    x0, x1 = (W - ow) / 2, (W + ow) / 2
    r = ow / 2
    outer = [(0, 0), (W, 0), (W, H), (0, H)]
    hole = [(x0, 0.0)] + arc(W / 2, spring, r, a0=math.pi, a1=0.0, n=10) + [(x1, 0.0)]
    mb.slab_holes(outer, [hole], -t / 2, t / 2, mat, reveal_mat=STONE)
    # dovelas: anillo saliente 2 cm por ambas caras (media luna, teselada)
    for y0, y1 in ((t / 2, t / 2 + 0.02), (-t / 2 - 0.02, -t / 2)):
        inner = arc(W / 2, spring, r, a0=0.0, a1=math.pi, n=10)
        outer_r = arc(W / 2, spring, r + ring, a0=math.pi, a1=0.0, n=10)
        prism(mb, inner + outer_r, y0, y1, STONE, axis="y")


def m_arch_3m(mb, v, rng):
    _arch_piece(mb, 4.0, FH, 3.0, 1.4, 0.5, 0.22)


def m_arch_6m(mb, v, rng):
    _arch_piece(mb, 7.0, 2 * FH, 6.0, 2.9, 0.7, 0.35)


def m_stairs(mb, v, rng, run=5.0, rise=FH, n=16):
    prof = [(0.0, 0.0)]
    for i in range(n):
        prof += [(run * i / n, rise * (i + 1) / n), (run * (i + 1) / n, rise * (i + 1) / n)]
    prof += [(run, rise - 0.3), (0.45, 0.0)]
    prism(mb, prof, 0.0, 1.0, STONE, axis="x")


def m_door(mb, v, rng, kind="wood"):
    """Muro de 2 m con puerta de 1.3 x 2.5: jambas y dintel de piedra, hoja de madera con herrajes o de hierro."""
    ow, oh = 1.3, 2.5
    x0, x1 = 1.0 - ow / 2, 1.0 + ow / 2
    mb.slab_holes([(0, 0), (2, 0), (2, FH), (0, FH)], [[(x0, 0), (x0, oh), (x1, oh), (x1, 0)]], -T, 0, BLOCK,
                  reveal_mat=STONE)
    mb.box((x0 - 0.18, 0, 0), (x0, 0.05, oh), STONE, skip=("y-", "z-"))
    mb.box((x1, 0, 0), (x1 + 0.18, 0.05, oh), STONE, skip=("y-", "z-"))
    mb.box((x0 - 0.22, 0, oh), (x1 + 0.22, 0.07, oh + 0.3), STONE, skip=("y-",))
    leaf = IRON if kind == "iron" else WOOD
    mb.box((x0 + 0.02, -T + 0.12, 0.0), (x1 - 0.02, -T + 0.18, oh - 0.02), leaf, skip=("z-",))
    for z in (0.35, 1.25, 2.15):
        mb.box((x0 + 0.05, -T + 0.18, z), (x1 - 0.05, -T + 0.2, z + 0.1), IRON, skip=("y-",))
    if kind == "iron":
        mb.box((x1 - 0.32, -T + 0.2, 1.0), (x1 - 0.18, -T + 0.26, 1.18), IRON)           # cerradero
        mb.rod((x1 - 0.25, -T + 0.24, 1.18), (x1 - 0.25, -T + 0.24, 1.32), 0.012, IRON)   # candado
        mb.box((x1 - 0.31, -T + 0.21, 0.93), (x1 - 0.19, -T + 0.28, 1.04), BRONZE)


def m_window(mb, v, rng):
    """Muro de 2 m con ventana de 1.0 x 1.4 (antepecho 1.2 m), reja de hierro y vidrio de luz calida."""
    x0, x1, z0, z1 = 0.5, 1.5, 1.2, 2.6
    mb.slab_holes([(0, 0), (2, 0), (2, FH), (0, FH)], [[(x0, z0), (x0, z1), (x1, z1), (x1, z0)]], -T, 0, BLOCK,
                  reveal_mat=STONE)
    mb.face([(x0, -T + 0.1, z0), (x1, -T + 0.1, z0), (x1, -T + 0.1, z1), (x0, -T + 0.1, z1)], WARM, nrm=(0, 1, 0))
    mb.box((x0 - 0.06, 0, z0 - 0.1), (x1 + 0.06, 0.08, z0), STONE, skip=("y-",))
    for i in range(1, 5):
        x = x0 + (x1 - x0) * i / 5
        mb.rod((x, -0.08, z0), (x, -0.08, z1), 0.014, IRON)
    for z in (z0 + 0.45, z0 + 0.95):
        mb.rod((x0, -0.08, z), (x1, -0.08, z), 0.014, IRON)


def m_fireplace(mb, v, rng):
    """Hogar de 2 m: solera, jambas, repisa de madera, campana hasta 3.2 m, fondo de ceniza, lenos y llama."""
    mb.box((0.1, 0, 0), (1.9, 0.7, 0.12), STONE, skip=("z-",))
    for x0 in (0.1, 1.6):
        mb.box((x0, 0, 0.12), (x0 + 0.3, 0.65, 1.3), BLOCK, skip=("z-", "y-"))
    mb.box((0.0, 0, 1.3), (2.0, 0.75, 1.45), WOOD, skip=("y-",))
    prism(mb, [(0.0, 1.45), (0.7, 1.45), (0.35, 3.2), (0.0, 3.2)], 0.15, 1.85, STONE_L, axis="x")
    mb.face([(0.4, 0.02, 0.12), (1.6, 0.02, 0.12), (1.6, 0.02, 1.3), (0.4, 0.02, 1.3)], ASH, nrm=(0, 1, 0))
    for dx in (-0.12, 0.12):
        mb.rod((0.6, 0.35 + dx, 0.2), (1.4, 0.3 + dx, 0.2), 0.06, WOOD)
    for a in (0.0, math.pi / 2):
        c, s = math.cos(a) * 0.22, math.sin(a) * 0.22
        mb.face([(1.0 - c, 0.32 - s, 0.22), (1.0 + c, 0.32 + s, 0.22), (1.0 + c * 0.3, 0.32 + s * 0.3, 0.75),
                 (1.0 - c * 0.3, 0.32 - s * 0.3, 0.75)], WARM, nrm=(-s, c, 0))


def m_counter(mb, v, rng):
    """Mostrador de 2 m: base de piedra (0.8 de fondo, 1.0 m) con dos entrepanos y tablero de madera de 10 cm."""
    mb.box((0, -0.4, 0), (2, 0.4, 1.0), STONE, skip=("z-",))
    for x0 in (0.12, 1.06):
        mat = REPAIR if (v and x0 > 1) else BLOCK
        mb.box((x0, -0.42, 0.15), (x0 + 0.82, -0.4, 0.85), mat, skip=("y+",))
    mb.box((-0.02, -0.46, 1.0), (2.02, 0.46, 1.1), WOOD)


def m_counter_corner(mb, v, rng):
    mb.box((-0.4, -0.4, 0), (0.4, 0.4, 1.0), STONE, skip=("z-",))
    mb.box((-0.46, -0.46, 1.0), (0.46, 0.46, 1.1), WOOD)


def m_grille(mb, v, rng, wicket=False, teller=False):
    """Reja de mostrador de 2 m x 1.5 m (va sobre el tablero, z 0 = 1.1 m): marco y barrotes cada 0.14 m;
    variante ventanilla: hueco central de 0.6 x 0.4 m abajo con dintel;
    variante cajero (teller): ventanilla de 1.2 m de luz (x 0.4-1.6) a toda la altura de la reja, con jambas y dintel
    de piedra de 12 cm de fondo que asoman 15 cm por encima; el tablero queda libre (sin barra baja en el hueco)."""
    a, b = (0.4, 1.6) if teller else (None, None)
    if teller:
        for x0, x1 in ((0.0, a), (b, 2.0)):
            mb.box((x0, -0.04, 1.42), (x1, 0.04, 1.5), IRON)
            mb.box((x0, -0.04, 0), (x1, 0.04, 0.05), IRON, skip=("z-",))
        for x0, x1 in ((a - 0.15, a), (b, b + 0.15)):  # jambas
            mb.box((x0, -0.06, 0.0), (x1, 0.06, 1.5), STONE, skip=("z-", "z+"))
        mb.box((a - 0.2, -0.07, 1.5), (b + 0.2, 0.07, 1.65), STONE)  # dintel
    else:
        mb.box((0, -0.04, 1.42), (2, 0.04, 1.5), IRON)
        mb.box((0, -0.04, 0), (2, 0.04, 0.05), IRON, skip=("z-",))
    for x in (0.0, 1.96):
        mb.box((x, -0.04, 0.05), (x + 0.04, 0.04, 1.42), IRON, skip=("z-", "z+"))
    n = 13
    for i in range(1, n + 1):
        x = 2.0 * i / (n + 1)
        z0 = 0.05
        if teller and a - 0.17 <= x <= b + 0.17:
            continue
        if wicket and 0.7 <= x <= 1.3:
            z0 = 0.45
        mb.rod((x, 0, z0), (x, 0, 1.42), 0.011, IRON)
    if wicket:
        mb.box((0.68, -0.035, 0.42), (1.32, 0.035, 0.47), IRON)


def m_railing(mb, v, rng):
    mb.box((0, -0.12, 0), (2, 0.12, 0.12), STONE, skip=("z-",))
    mb.box((0, -0.14, 0.92), (2, 0.14, 1.02), STONE)
    for i in range(7):
        x = 0.14 + i * 0.287
        mb.box((x - 0.05, -0.06, 0.12), (x + 0.05, 0.06, 0.92), STONE_L, skip=("z-", "z+"))


KIT = {
    "INT_Floor_Stone": (m_floor_stone, 0), "INT_Floor_Stone_B": (m_floor_stone, 1),
    "INT_Floor_Planks": (m_floor_planks, 0), "INT_Floor_Planks_B": (m_floor_planks, 1),
    "INT_Wall_Plaster": (m_wall_plaster, 0), "INT_Wall_Plaster_B": (m_wall_plaster, 1),
    "INT_Wall_Stone": (m_wall_stone, 0), "INT_Wall_Stone_B": (m_wall_stone, 1),
    "INT_Wall_Panel": (m_wall_panel, 0), "INT_Wall_Panel_B": (m_wall_panel, 1),
    "INT_Beam_Straight": (m_beam_straight, 0), "INT_Beam_Cross": (m_beam_cross, 0),
    "INT_Arch_3m": (m_arch_3m, 0), "INT_Arch_6m": (m_arch_6m, 0), "INT_Pillar": (m_pillar, 0),
    "INT_Stairs_Int": (m_stairs, 0), "INT_Door_Int": (m_door, 0), "INT_Door_Int_Iron": (m_door, 1),
    "INT_Window_Int": (m_window, 0), "INT_Fireplace": (m_fireplace, 0),
    "INT_Counter_Straight": (m_counter, 0), "INT_Counter_Straight_B": (m_counter, 1),
    "INT_Counter_Corner": (m_counter_corner, 0), "INT_Grille": (m_grille, 0), "INT_Grille_Wicket": (m_grille, 1),
    "INT_Grille_Teller": (m_grille, 2),
    "INT_Railing": (m_railing, 0), "INT_Trim": (m_trim, 0),
}


def build_kit(col, seed=2701):
    """Crea las mallas del kit (nombre de malla = nombre del modulo) y un objeto de muestra de cada una en la
    coleccion; devuelve {nombre: triangulos}."""
    rng = random.Random(seed)
    out = {}
    for name, (fn, v) in KIT.items():
        if bpy.data.meshes.get(name) is not None:
            continue
        mb = K.MB()
        if fn is m_door:
            fn(mb, v, rng, kind="iron" if v else "wood")
        elif fn is m_grille:
            fn(mb, 0, rng, wicket=(v == 1), teller=(v == 2))
        else:
            fn(mb, v, rng)
        o = to_obj(mb, name, col)
        o.data.name = name
        o["kit_piece"] = True
        out[name] = tris(o)
        if out[name] > KIT_MAX_TRIS:
            raise RuntimeError(f"{name}: {out[name]} triangulos > {KIT_MAX_TRIS}")
    return out


def kit_sheet(col, origin=(4000.0, 0.0, 0.0), cols=7, step=8.0):
    """Ordena las muestras del kit en una hoja (filas de 'cols')."""
    ox, oy, oz = origin
    names = list(KIT)
    for i, n in enumerate(names):
        o = bpy.data.objects[n]
        o.location = (ox + (i % cols) * step, oy - (i // cols) * step, oz)
    return [(n, (ox + (i % cols) * step + 1.0, oy - (i // cols) * step, oz + 3.6)) for i, n in enumerate(names)]


# --------------------------------------------------------------------------- escena de interior
STYLES = {
    "piedra": {"floor": ("INT_Floor_Stone", "INT_Floor_Stone_B"), "walls": [("INT_Wall_Stone", "INT_Wall_Stone_B"),
                                                                              ("INT_Wall_Plaster", "INT_Wall_Plaster_B")]},
    "entramado": {"floor": ("INT_Floor_Planks", "INT_Floor_Planks_B"), "walls": [("INT_Wall_Panel", "INT_Wall_Panel_B"),
                                                                                 ("INT_Wall_Plaster", "INT_Wall_Plaster_B")]},
    "revoco": {"floor": ("INT_Floor_Stone", "INT_Floor_Stone_B"), "walls": [("INT_Wall_Plaster", "INT_Wall_Plaster_B"),
                                                                            ("INT_Wall_Plaster", "INT_Wall_Plaster_B")]},
}
GROUPS = ("Shell", "WALL_Near_A", "WALL_Near_B", "CEILING", "Furniture", "Lights", "Markers")


def sides(W, D):
    """(nombre, normal hacia dentro, inicio sobre la cara interior, longitud); el modulo corre por t = (n.y, -n.x)."""
    return [("-Y", Vector((0, 1)), Vector((-W / 2, -D / 2)), W), ("+Y", Vector((0, -1)), Vector((W / 2, D / 2)), W),
            ("-X", Vector((1, 0)), Vector((-W / 2, D / 2)), D), ("+X", Vector((-1, 0)), Vector((W / 2, -D / 2)), D)]


def frame_mat(start, n, s, z=0.0, sx=1.0, sz=1.0):
    t = Vector((n.y, -n.x))
    p = start + t * s
    rot = Matrix(((t.x, n.x, 0, 0), (t.y, n.y, 0, 0), (0, 0, 1, 0), (0, 0, 0, 1)))
    return Matrix.Translation((p.x, p.y, z)) @ rot @ Matrix.Diagonal((sx, 1.0, sz, 1.0))


class Interior:
    def __init__(self, nombre, volumen, estilo, seed, world_rot_deg, door, col):
        self.name = nombre
        self.W, self.D, self.H = volumen
        self.estilo = estilo
        self.rng = random.Random(f"{nombre}-{seed}")
        self.col = col
        self.world_rot = math.radians(world_rot_deg)
        self.door = Vector(door)                       # (x, y) de la puerta en el marco centrado
        root = bpy.data.objects.new(f"INT_{nombre}", None)
        col.objects.link(root)
        root.rotation_euler = (0, 0, self.world_rot)
        root["interior_of"] = nombre
        root["interior_size_m"] = [self.W, self.D, self.H]
        root["world_rot_deg"] = world_rot_deg
        frame = bpy.data.objects.new(f"INT_{nombre}_Frame", None)
        col.objects.link(frame)
        frame.parent = root
        frame.location = (-self.door.x, -self.door.y, 0.0)
        self.root, self.frame = root, frame
        self.groups = {}
        for g in GROUPS:
            self.group(g)
        self.cam_local = Matrix.Rotation(-self.world_rot, 3, "Z") @ CAM_BACK
        self.colboxes = []          # (lo, hi) en el marco centrado
        self.colprisms = []         # (perfil yz o xz, s0, s1, eje)
        self.obstacles = []         # (nivel, x0, y0, x1, y1)
        self.nav_regions = []       # (nivel, z, x0, y0, x1, y1)
        self.ramps = []             # (x0, x1, y0, y1, z0, z1)  rampa a lo largo de +Y
        self.near = {}
        self.log = {}

    def group(self, name):
        if name not in self.groups:
            e = bpy.data.objects.new(name if name in GROUPS else name, None)
            self.col.objects.link(e)
            e.parent = self.frame
            e.name = name
            e["interior_group"] = name
            self.groups[name] = e
        return self.groups[name]

    def inst(self, mesh_name, mw, group, name=None):
        me = bpy.data.meshes[mesh_name]
        o = bpy.data.objects.new(name or f"KITI_{mesh_name}", me)
        self.col.objects.link(o)
        o.parent = self.group(group)
        o.matrix_parent_inverse = Matrix.Identity(4)
        o.matrix_basis = mw
        o["merge"] = group not in ("Furniture", "Furniture_L1")
        return o

    def unique(self, mb, name, group, mw=Matrix.Identity(4), merge=True):
        o = to_obj(mb, name, self.col)
        o.parent = self.group(group)
        o.matrix_parent_inverse = Matrix.Identity(4)
        o.matrix_basis = mw
        o["merge"] = merge
        return o

    def light(self, name, loc, color="#FFB46B", energy=1.0, rng=5.0, kind="omni"):
        e = bpy.data.objects.new(name, None)
        self.col.objects.link(e)
        e.parent = self.group("Lights")
        e.matrix_parent_inverse = Matrix.Identity(4)
        e.location = loc
        e.empty_display_type = "SPHERE"
        e.empty_display_size = 0.2
        e["light_kind"] = kind
        e["light_color"] = color
        e["light_energy"] = energy
        e["light_range"] = rng
        e["baked"] = True
        return e

    def marker(self, name, loc, yaw_deg=0.0, **props):
        e = bpy.data.objects.new(name, None)
        self.col.objects.link(e)
        e.parent = self.group("Markers")
        e.matrix_parent_inverse = Matrix.Identity(4)
        e.location = loc
        e.rotation_euler = (0, 0, math.radians(yaw_deg))
        e.empty_display_type = "SINGLE_ARROW"
        e.empty_display_size = 0.8
        e["axis"] = "+Y local = frente"
        for k, v in props.items():
            e[k] = v
        return e

    def is_near(self, n):
        c = Vector((self.cam_local.x, self.cam_local.y)).normalized()
        return (-n).dot(c) > 0.05

    def shell(self, openings=(), storeys=None, floor=True, ceiling=True, skip_sides=()):
        """Suelo, muros (los cercanos a CAM_Iso en WALL_Near_A/B), cornisas y techo. openings: (lado, s, tipo,
        planta) con tipo en {'door', 'door_iron', 'window'}; s = distancia al centro del hueco a lo largo del lado."""
        W, D, H = self.W, self.D, self.H
        st = STYLES[self.estilo]
        storeys = storeys or max(1, round(H / FH))
        sh = H / storeys
        rng = self.rng
        if floor:
            nx, ny = max(1, round(W / 2)), max(1, round(D / 2))
            for i in range(nx):
                for j in range(ny):
                    mesh = st["floor"][1] if rng.random() < 0.18 else st["floor"][0]
                    mw = Matrix.Translation((-W / 2 + i * W / nx, -D / 2 + j * D / ny, 0)) @ \
                        Matrix.Diagonal((W / nx / 2, D / ny / 2, 1, 1))
                    self.inst(mesh, mw, "Shell")
        near = [s for s in sides(W, D) if self.is_near(s[1])]
        near.sort(key=lambda s: s[0])
        labels = {s[0]: lab for s, lab in zip(near, ("WALL_Near_A", "WALL_Near_B"))}
        self.near = {v: k for k, v in labels.items()}
        for name, n, start, L in sides(W, D):
            if name in skip_sides:
                continue
            group = labels.get(name, "Shell")
            for k in range(storeys):
                ops = sorted((s, kind) for (sd, s, kind, f) in openings if sd == name and f == k)
                cuts = [(s - 1.0, s + 1.0, kind) for s, kind in ops]
                pos = 0.0
                segs = []
                for a, b, kind in cuts:
                    if a > pos + 1e-3:
                        segs.append((pos, a, None))
                    segs.append((a, b, kind))
                    pos = b
                if pos < L - 1e-3:
                    segs.append((pos, L, None))
                walls = st["walls"][min(k, len(st["walls"]) - 1)]
                for a, b, kind in segs:
                    if kind is None:
                        m = max(1, round((b - a) / 2))
                        w = (b - a) / m
                        for i in range(m):
                            mesh = walls[1] if rng.random() < 0.22 else walls[0]
                            self.inst(mesh, frame_mat(start, n, a + i * w, k * sh, w / 2, sh / FH), group)
                    else:
                        mesh = {"door": "INT_Door_Int", "door_iron": "INT_Door_Int_Iron", "window": "INT_Window_Int"}[kind]
                        self.inst(mesh, frame_mat(start, n, a, k * sh, (b - a) / 2, sh / FH), group)
                if k > 0:
                    m = max(1, round(L / 2))
                    for i in range(m):
                        self.inst("INT_Trim", frame_mat(start, n, i * L / m, k * sh - 0.16, L / m / 2, 1.0), group)
            # colision del muro
            t = Vector((n.y, -n.x))
            p0, p1 = start - n * T, start + t * L
            lo = (min(p0.x, p1.x), min(p0.y, p1.y), 0.0)
            hi = (max(p0.x, p1.x), max(p0.y, p1.y), H)
            self.colboxes.append((lo, hi))
        if floor:
            self.colboxes.append(((-W / 2, -D / 2, -0.3), (W / 2, D / 2, 0.0)))
        if ceiling:
            self.ceiling()
        self.log["near_walls"] = {v: k for k, v in labels.items()}
        self.log["cam_local"] = [round(c, 3) for c in self.cam_local]

    def ceiling(self, z=None, span_axis=None, every=2.3, group="CEILING"):
        W, D = self.W, self.D
        z = self.H if z is None else z
        mb = K.MB()
        mb.box((-W / 2, -D / 2, z), (W / 2, D / 2, z + 0.12), WOOD, skip=("z+",))
        self.unique(mb, f"{self.name}_CeilingBoards", group)
        axis = span_axis or ("y" if D <= W else "x")
        L = D if axis == "y" else W
        across = W if axis == "y" else D
        m = max(1, round(across / every))
        for i in range(m + 1):
            c = -across / 2 + across * i / m
            c = max(-across / 2 + 0.15, min(across / 2 - 0.15, c))
            if axis == "y":
                mw = Matrix.Translation((c, -L / 2, z)) @ Matrix.Rotation(math.pi / 2, 4, "Z") @ \
                    Matrix.Diagonal((L / 2, 1, 1, 1))
            else:
                mw = Matrix.Translation((-L / 2, c, z)) @ Matrix.Diagonal((L / 2, 1, 1, 1))
            self.inst("INT_Beam_Straight", mw, group)

    def entry_markers(self, inward_yaw_deg, exit_yaw_deg, spawn_dist=1.6):
        d = Vector((math.cos(math.radians(inward_yaw_deg + 90)), math.sin(math.radians(inward_yaw_deg + 90))))
        self.marker("MARKER_Interior_Exit", (self.door.x, self.door.y, 0.0), exit_yaw_deg, to="calle",
                    note="+Y hacia la calle")
        sp = self.door + d * spawn_dist
        self.marker("MARKER_Interior_Spawn", (sp.x, sp.y, 0.0), inward_yaw_deg, note="+Y hacia el interior")

    # ----------------------------------------------------------------- colision y navegacion
    def collider(self):
        mb = K.MB()
        for lo, hi in self.colboxes:
            mb.box(lo, hi, BLOCK)
        for prof, s0, s1, axis in self.colprisms:
            prism(mb, prof, s0, s1, BLOCK, axis=axis)
        o = to_obj(mb, f"INT_{self.name}-colonly", self.col, uv=False)
        o.parent = self.frame
        o.display_type = "WIRE"
        o.hide_render = True
        return o

    def navmesh(self, margin=0.3, cell=0.5, name_suffix="-navmesh"):
        """Rejilla comun (origen en la esquina -X -Y de la sala): celdas libres de cada nivel (region menos
        obstaculos ampliados con el margen) y rampas; los vertices coincidentes se sueldan."""
        W, D = self.W, self.D
        ox, oy = -W / 2, -D / 2
        bm = bmesh.new()
        faces = 0
        cells = {}

        def free(level, x0, y0, x1, y1):
            for (lv, zz, rx0, ry0, rx1, ry1) in self.nav_regions:
                if lv == level and x0 >= rx0 + margin - 1e-6 and y0 >= ry0 + margin - 1e-6 and \
                        x1 <= rx1 - margin + 1e-6 and y1 <= ry1 - margin + 1e-6:
                    break
            else:
                return False
            for (lv, ax0, ay0, ax1, ay1) in self.obstacles:
                if lv == level and x1 > ax0 - margin and x0 < ax1 + margin and y1 > ay0 - margin and y0 < ay1 + margin:
                    return False
            return True
        nx, ny = int(math.ceil(W / cell)), int(math.ceil(D / cell))
        levels = sorted({(lv, zz) for (lv, zz, *_r) in self.nav_regions})
        for lv, zz in levels:
            for i in range(nx):
                for j in range(ny):
                    x0, y0 = ox + i * cell, oy + j * cell
                    x1, y1 = x0 + cell, y0 + cell
                    if free(lv, x0, y0, x1, y1):
                        vs = [bm.verts.new((x, y, zz + 0.05)) for x, y in ((x0, y0), (x1, y0), (x1, y1), (x0, y1))]
                        bm.faces.new(vs)
                        cells[(lv, i, j)] = True
                        faces += 1
        for (x0, x1, y0, y1, z0, z1) in self.ramps:
            i0, i1 = int(math.ceil((x0 + margin - ox) / cell - 1e-6)), int(math.floor((x1 - margin - ox) / cell + 1e-6))
            j0, j1 = int(round((y0 - oy) / cell)), int(round((y1 - oy) / cell))
            ya, yb = oy + j0 * cell, oy + j1 * cell
            for i in range(i0, i1):
                for j in range(j0, j1):
                    xa, xb = ox + i * cell, ox + (i + 1) * cell
                    ya_, yb_ = oy + j * cell, oy + (j + 1) * cell
                    za = z0 + (z1 - z0) * (ya_ - ya) / (yb - ya)
                    zb = z0 + (z1 - z0) * (yb_ - ya) / (yb - ya)
                    vs = [bm.verts.new(c) for c in ((xa, ya_, za + 0.05), (xb, ya_, za + 0.05), (xb, yb_, zb + 0.05),
                                                     (xa, yb_, zb + 0.05))]
                    bm.faces.new(vs)
                    faces += 1
        for (x0, x1, y0, y1, zz) in getattr(self, "patches", []):
            i0, i1 = int(math.ceil((x0 + margin - ox) / cell - 1e-6)), int(math.floor((x1 - margin - ox) / cell + 1e-6))
            j0, j1 = int(round((y0 - oy) / cell)), int(round((y1 - oy) / cell))
            for i in range(i0, i1):
                for j in range(j0, j1):
                    xa, xb, ya_, yb_ = ox + i * cell, ox + (i + 1) * cell, oy + j * cell, oy + (j + 1) * cell
                    bm.faces.new([bm.verts.new((x, y, zz + 0.05)) for x, y in ((xa, ya_), (xb, ya_), (xb, yb_), (xa, yb_))])
                    faces += 1
        bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=0.06)
        me = bpy.data.meshes.new(f"INT_{self.name}{name_suffix}")
        bm.to_mesh(me)
        bm.free()
        o = bpy.data.objects.new(f"INT_{self.name}{name_suffix}", me)
        self.col.objects.link(o)
        o.parent = self.frame
        o.hide_render = True
        o.display_type = "WIRE"
        return o

    # ----------------------------------------------------------------- exportacion
    def realize(self, gname):
        """Une los modulos instanciados (KITI_*) y las piezas unicas de un grupo en una sola malla <grupo>_Mesh."""
        g = self.groups[gname]
        objs = [o for o in g.children if o.type == "MESH" and o.get("merge")]
        if not objs:
            return None
        bm_all = bmesh.new()
        mats = []
        tmpme = bpy.data.meshes.new("TMP_realize")
        for o in objs:
            m = o.matrix_basis
            bm = bmesh.new()
            bm.from_mesh(o.data)
            bm.transform(m)
            if m.determinant() < 0:
                bmesh.ops.reverse_faces(bm, faces=bm.faces[:])
            remap = []
            for s in o.data.materials:
                if s.name not in mats:
                    mats.append(s.name)
                remap.append(mats.index(s.name))
            for f in bm.faces:
                f.material_index = remap[f.material_index] if remap else 0
            bm.to_mesh(tmpme)
            bm.free()
            bm_all.from_mesh(tmpme)
        bpy.data.meshes.remove(tmpme)
        me = bpy.data.meshes.new(f"INT_{self.name}_{gname}")
        bm_all.to_mesh(me)
        bm_all.free()
        for mn in mats:
            me.materials.append(bpy.data.materials[mn])
        for o in objs:
            bpy.data.objects.remove(o)
        out = bpy.data.objects.new(f"INT_{self.name}_{gname}", me)
        self.col.objects.link(out)
        out.parent = g
        out.matrix_parent_inverse = Matrix.Identity(4)
        import concordia_buildings as B
        B.box_uv(out)
        return out

    def all_objects(self):
        return [self.root] + list(self.root.children_recursive)


def build_interior(nombre, volumen, estilo="piedra", seed=0, world_rot_deg=0.0, door=None, col=None, openings=(),
                   storeys=None, ceiling=True):
    """Crea la escena de interior <nombre> con el kit: volumen (W, D, H) en m; estilo en STYLES; door = (x, y) de
    la puerta en el marco centrado (por defecto el centro del lado +Y). Devuelve el objeto Interior (raiz en .root,
    grupos en .groups) para anadir mobiliario, luces y marcadores."""
    col = col or bpy.context.scene.collection
    W, D, H = volumen
    door = door or (0.0, D / 2)
    it = Interior(nombre, volumen, estilo, seed, world_rot_deg, door, col)
    it.shell(openings=openings, storeys=storeys, ceiling=ceiling)
    return it
