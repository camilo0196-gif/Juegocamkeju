"""
CONCORDIA - datos fijos de la ciudad.

Fuente unica de verdad para todos los scripts bpy (y para herramientas de Godot).
No depende de bpy: se puede importar desde cualquier Python.

Convenciones
- 1 unidad = 1 metro.
- Ejes Blender: +X = Este, +Y = Norte, +Z = Arriba.
- Angulos en grados, medidos desde +X en sentido antihorario (0 = Este, 90 = Norte).
- Todas las cotas Z son absolutas.
- Exportacion glTF con +Y Up (Godot): el Norte de Blender (+Y) pasa a -Z en Godot.
"""

from math import cos, radians, sin

# ---------------------------------------------------------------------------
# Escena / unidades
# ---------------------------------------------------------------------------
UNIT_SYSTEM = "METRIC"
UNIT_SCALE = 1.0
BLEND_BASENAME = "concordia"          # concordia_v01.blend, concordia_v02.blend ...

# ---------------------------------------------------------------------------
# Niveles (Z absoluto, metros)
# ---------------------------------------------------------------------------
Z_PLAZA = 8.0                         # Plaza del Portal
DATUM = 6.0                           # Base de la muralla
Z_CARDINAL_END = 4.5                  # Fin de los distritos cardinales (radio 185)
Z_MORADAS_MIN = 4.5                   # Moradas: de +4.5 ...
Z_MORADAS_MAX = 9.5                   # ... a +9.5
Z_EXTERIOR = 0.0                      # Yermo exterior (ceniza)

# ---------------------------------------------------------------------------
# Muralla, Faro, Plaza
# ---------------------------------------------------------------------------
WALL_RADIUS = 200.0                   # Muralla circular
WALL_BASE_Z = DATUM
WALL_HEIGHT = 15.0                    # Altura de la muralla sobre DATUM
LIGHTHOUSE_HEIGHT = 40.0              # Torre del Faro
PLAZA_DIAMETER = 120.0
PLAZA_RADIUS = PLAZA_DIAMETER / 2.0   # 60

# ---------------------------------------------------------------------------
# Calles (anchos en metros, min / max)
# ---------------------------------------------------------------------------
STREET_MAIN_WIDTH = (8.0, 10.0)
ALLEY_WIDTH = (4.0, 5.0)

# ---------------------------------------------------------------------------
# Sectores
# Cada sector: angulo central, semiancho angular, radio min/max.
# ---------------------------------------------------------------------------
CARDINAL_HALF_ANGLE = 25.0
CARDINAL_R = (60.0, 185.0)

MORADA_HALF_ANGLE = 20.0
MORADA_R = (100.0, 190.0)

LANDMARK_R = (60.0, 95.0)             # Hitos junto a la plaza

DISTRICTS_CARDINAL = {
    # key: (nombre_es, angulo, semiancho, (r_min, r_max))
    "Oficios": ("Oficios", 0.0, CARDINAL_HALF_ANGLE, CARDINAL_R),     # Este
    "Mercado": ("Mercado", 90.0, CARDINAL_HALF_ANGLE, CARDINAL_R),    # Norte
    "Clases": ("Clases", 180.0, CARDINAL_HALF_ANGLE, CARDINAL_R),     # Oeste
    "Razas": ("Razas", 270.0, CARDINAL_HALF_ANGLE, CARDINAL_R),       # Sur
}

MORADAS = {
    "Morada_NE": ("Morada NE", 45.0, MORADA_HALF_ANGLE, MORADA_R),
    "Morada_NW": ("Morada NO", 135.0, MORADA_HALF_ANGLE, MORADA_R),
    "Morada_SW": ("Morada SO", 225.0, MORADA_HALF_ANGLE, MORADA_R),
    "Morada_SE": ("Morada SE", 315.0, MORADA_HALF_ANGLE, MORADA_R),
}

LANDMARKS = {
    # key: (nombre_es, angulo, (r_min, r_max))
    "Lighthouse": ("Torre del Faro", 45.0, LANDMARK_R),             # NE
    "Sanctuary": ("Santuario", 135.0, LANDMARK_R),                  # NO
    "HallOfDeeds": ("Salon de las Hazanas", 315.0, LANDMARK_R),     # SE
    "Obelisk": ("Obelisco", 225.0, LANDMARK_R),                     # SO
}

# ---------------------------------------------------------------------------
# Puertas (en la muralla, a DATUM)
# ---------------------------------------------------------------------------
GATE_RADIUS = WALL_RADIUS
GATE_Z = DATUM
GATES = {
    # nombre_objeto: (angulo, nombre_es)
    "MARKER_Gate_E": (0.0, "Puerta del Alba"),
    "MARKER_Gate_N": (90.0, "Puerta Norte"),
    "MARKER_Gate_W": (180.0, "Puerta del Ocaso"),
    "MARKER_Gate_S": (270.0, "Puerta Sur"),
}

# ---------------------------------------------------------------------------
# Terreno de la colina (etapa 02) - cifras del pedido
# ---------------------------------------------------------------------------
TERRAIN_RADIUS = 212.0                # incluye talud exterior
TERRAIN_CELL = 1.0                    # celdas de 1 m
TERRAIN_GRID_SIZE = 424.0             # grid 424 x 424 m centrado en el origen

PLAZA_DRAIN = 0.005                   # 0.5 % hacia fuera desde el centro
RING_DESCENT = (60.0, 90.0)           # plaza -> +6.0, comun a todos los sectores

# Sectores cardinales (radios de cambio de perfil)
CARD_SLOPE_END = 165.0                # 90..165 baja 6.0 -> 4.5
CARD_FLAT_END = 185.0                 # 165..185 plano 4.5
CARD_EMBANK_END = 196.0               # 185..196 sube 4.5 -> 6.0 (terraplen)
WALL_BASE_R = (196.0, 204.0)          # base de la muralla, plano a DATUM

# Sectores diagonales (Moradas + hitos)
DIAG_LANDMARK_END = 95.0              # 60..95 zona de hitos a +6.0
DIAG_RAMP_END = 105.0                 # 95..105 rampa 6.0 -> 4.5
TERRACE_COUNT = 6
TERRACE_DEPTH = 14.0                  # 105..189
TERRACE_RISE = 1.0                    # 4.5, 5.5 ... 9.5
TERRACE_START_R = DIAG_RAMP_END
TERRACE_END_R = TERRACE_START_R + TERRACE_COUNT * TERRACE_DEPTH   # 189
TERRACE_FACE_ANGLE = 80.0             # cara del muro de contencion (grados)

SECTOR_BLEND_WIDTH = 6.0              # mezcla entre sectores (arco, metros)
TALUD_R = (204.0, TERRAIN_RADIUS)     # 204..212 baja 6.0 -> 0

TERRAIN_NOISE_PP = 0.05               # 5 cm de irregularidad (pico a pico)
WALK_SLOPE_MAX = 5.0                  # grados, calles y plazas
STAIR_SLOPE = 8.0                     # grados, a partir de aqui escalinata

# ---------------------------------------------------------------------------
# Paleta
# El azul de esquirlas es el UNICO color magico permitido (siempre emisivo).
# Resto de la paleta (descriptiva, sin hex fijados aun): caliza clara gastada,
# madera oscura, teja ocre desgastada, hierro negro, telas remendadas en tonos
# tierra, muralla gris.
# ---------------------------------------------------------------------------
MAGIC_BLUE_HEX = "#8FD0FF"


def hex_to_linear_rgba(hex_str, alpha=1.0):
    """sRGB hex -> RGBA lineal (lo que esperan los nodos de Blender)."""
    h = hex_str.lstrip("#")
    out = []
    for i in (0, 2, 4):
        c = int(h[i:i + 2], 16) / 255.0
        out.append(c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4)
    return (*out, alpha)


MAGIC_BLUE_LINEAR = hex_to_linear_rgba(MAGIC_BLUE_HEX)

# ---------------------------------------------------------------------------
# Camara isometrica de verificacion
# ---------------------------------------------------------------------------
CAM_ISO_NAME = "CAM_Iso"
CAM_ISO_ROT_X = 54.736                # grados
CAM_ISO_ROT_Z = 45.0                  # grados
CAM_ISO_ORTHO_SCALE = 120.0
CAM_ISO_TARGET = (0.0, 0.0, Z_PLAZA)  # punto al que mira (centro de la plaza)
CAM_ISO_DISTANCE = 800.0              # distancia al objetivo (solo afecta al clipping)
CAM_ISO_CLIP = (1.0, 2000.0)
RENDER_RES = (1920, 1080)

# ---------------------------------------------------------------------------
# Collections
# ---------------------------------------------------------------------------
COLLECTIONS = (
    "TERRAIN",
    "PLAZA",
    "WALL_KIT",
    "WALL_LAYOUT",
    "STREETS",
    "MARKERS_DISTRICTS",
    "MORADAS",
    "CAUCE",
    "EXTERIOR",
)

# ---------------------------------------------------------------------------
# Presupuestos de triangulos por defecto (si el pedido no fija otros)
# ---------------------------------------------------------------------------
TRI_BUDGET = {"small": 1500, "medium": 5000, "large": 12000}
LOD_RATIOS = {"LOD1": 0.50, "LOD2": 0.15}


# ---------------------------------------------------------------------------
# Utilidades
# ---------------------------------------------------------------------------
def polar(angle_deg, radius, z=0.0):
    """(angulo desde +X antihorario, radio, z) -> (x, y, z)."""
    a = radians(angle_deg)
    # Redondeo a 1e-6 m para evitar residuos de coma flotante (-0.000000123...)
    x = round(radius * cos(a), 6) + 0.0
    y = round(radius * sin(a), 6) + 0.0
    return (x, y, z)
