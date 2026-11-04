"""
CONCORDIA - modelo de alturas de la colina h(x, y). Python puro (sin bpy).  v2

Piezas del modelo
- Perfiles radiales: comun (plaza + bajada 60..90), cardinal fuera del eje,
  eje de avenida (banda recta de 30 m), diagonal (hitos, rampa, 6 terrazas).
- Rampas con "rodillas" suavizadas (smoothstep en la pendiente). Las rampas
  caminables limitan la rodilla para que la pendiente maxima quede 0.7 grados
  por debajo de WALK_SLOPE_MAX (margen para el ruido de 5 cm).
- Muros de contencion: entre dos niveles a cada lado de una linea (borde
  lateral de Morada o borde de la banda del eje) la transicion es una cara de
  80 grados: arista superior sobre la linea, arista inferior desplazada
  max(|dz|, 1 m) / tan(80) hacia el lado bajo. Sin mezclas suaves.
- Saltos de terraza: caras de 80 grados entre dos anillos.
- Escalinata diagonal r 95..105: el terreno se rebaja 0.2 m bajo la huella para
  que la pieza de escalones (TRN_Escalinata_*) quede siempre por encima.
"""

from math import atan2, cos, degrees, radians, sin, sqrt, tan

import concordia_const as C

# ---------------------------------------------------------------------------
# Parametros artisticos (no vienen del pedido; ajustables)
# ---------------------------------------------------------------------------
KNEE_MAX = 4.0        # longitud maxima de rodilla (m)
KNEE_FRAC = 0.15      # rodilla = min(KNEE_MAX, KNEE_FRAC * L)
WALK_MARGIN = 0.7     # grados de margen bajo WALK_SLOPE_MAX en rampas caminables

TAN_FACE = tan(radians(C.TERRACE_FACE_ANGLE))
STEP_RUN = C.TERRACE_RISE / TAN_FACE                                  # 0.1763 m
WALL_STEP_RUN = (C.Z_MORADAS_MAX - C.DATUM) / TAN_FACE               # 0.6171 m
Z_PLAZA_EDGE = C.Z_PLAZA - C.PLAZA_DRAIN * C.PLAZA_RADIUS            # 7.70
HALF_BAND = C.AXIS_BAND_WIDTH / 2.0                                  # 15 m

ESC_U0 = C.DIAG_LANDMARK_END          # 95
ESC_U1 = C.DIAG_RAMP_END              # 105
ESC_HALF_W = C.ESC_WIDTH / 2.0        # 3.0
ESC_HALF_OUT = ESC_HALF_W + C.ESC_BALUSTRADE_THICK   # 3.45
ESC_EDGE = 0.05                       # transicion del rebaje en los extremos (m)
ESC_CARVE = 0.20                      # rebaje bajo la escalinata (m)


def smoothstep(e0, e1, x):
    if x <= e0:
        return 0.0
    if x >= e1:
        return 1.0
    t = (x - e0) / (e1 - e0)
    return t * t * (3.0 - 2.0 * t)


def knee_len(r0, r1, dz=0.0, walkable=False):
    L = r1 - r0
    k = min(KNEE_MAX, KNEE_FRAC * L)
    if walkable and dz:
        smax = tan(radians(C.WALK_SLOPE_MAX - WALK_MARGIN))
        k = min(k, max(0.0, L - abs(dz) / smax))
    return k


def _knee_int(t):
    return t ** 3 - 0.5 * t ** 4      # integral de smoothstep(0,1,t) entre 0 y t


def ramp(r, r0, r1, z0, z1, walkable=False):
    """Rampa z0->z1 entre r0 y r1 con rodillas smoothstep."""
    if r <= r0:
        return z0
    if r >= r1:
        return z1
    L = r1 - r0
    k = min(knee_len(r0, r1, z1 - z0, walkable), L / 2.0)
    u = r - r0
    if k <= 0.0:
        f = u / L
    else:
        total = L - k
        if u < k:
            F = k * _knee_int(u / k)
        elif u <= L - k:
            F = k / 2.0 + (u - k)
        else:
            F = total - k * _knee_int((L - u) / k)
        f = F / total
    return z0 + (z1 - z0) * f


def ramp_max_slope_deg(r0, r1, z0, z1, walkable=False):
    L = r1 - r0
    k = min(knee_len(r0, r1, z1 - z0, walkable), L / 2.0)
    return degrees(atan2(abs(z1 - z0), L - k))


# ---------------------------------------------------------------------------
# Terrazas
# ---------------------------------------------------------------------------
def terrace_jumps():
    """Radios centrales de los saltos entre terrazas (5 saltos: 119..175)."""
    return [C.TERRACE_START_R + C.TERRACE_DEPTH * j for j in range(1, C.TERRACE_COUNT)]


def terrace_level(k):
    return C.Z_MORADAS_MIN + (k - 1) * C.TERRACE_RISE


def wall_step_rings():
    """Salto 9.5 -> 6.0 bajo la cara exterior de la muralla (solo diagonales)."""
    r_out = C.WALL_BASE_R[1]
    return (r_out - WALL_STEP_RUN, r_out)


def ring_pairs():
    """[(r_interior, r_exterior)] de cada cara de 80 grados en las Moradas."""
    pairs = [(R - STEP_RUN / 2.0, R + STEP_RUN / 2.0) for R in terrace_jumps()]
    pairs.append(wall_step_rings())
    return pairs


def terrace_index(r):
    """1..6 si r cae en una terraza (105..189), si no 0."""
    if r < C.TERRACE_START_R or r >= C.TERRACE_END_R:
        return 0
    return int((r - C.TERRACE_START_R) // C.TERRACE_DEPTH) + 1


# ---------------------------------------------------------------------------
# Perfiles
# ---------------------------------------------------------------------------
def prof_common(r):
    if r <= C.PLAZA_RADIUS:
        return C.Z_PLAZA - C.PLAZA_DRAIN * r
    return ramp(r, C.RING_DESCENT[0], C.RING_DESCENT[1], Z_PLAZA_EDGE, C.DATUM, walkable=True)


def prof_talud(r):
    return ramp(r, C.TALUD_R[0], C.TALUD_R[1], C.DATUM, C.Z_EXTERIOR)


def prof_card(r):
    """Sector cardinal fuera de la banda del eje."""
    if r <= C.RING_DESCENT[1]:
        return prof_common(r)
    if r <= C.CARD_SLOPE_END:
        return ramp(r, C.RING_DESCENT[1], C.CARD_SLOPE_END, C.DATUM, C.Z_CARDINAL_END, walkable=True)
    if r <= C.CARD_FLAT_END:
        return C.Z_CARDINAL_END
    if r <= C.CARD_EMBANK_END:
        return ramp(r, C.CARD_FLAT_END, C.CARD_EMBANK_END, C.Z_CARDINAL_END, C.DATUM, walkable=True)
    if r <= C.WALL_BASE_R[1]:
        return C.DATUM
    return prof_talud(r)


def prof_axis(u):
    """Banda del eje (u = distancia a lo largo del eje). None fuera de la banda."""
    if u <= C.AXIS_DESCENT[0]:
        return prof_common(u)
    if u <= C.AXIS_DESCENT[1]:
        return ramp(u, C.AXIS_DESCENT[0], C.AXIS_DESCENT[1], C.DATUM, C.Z_CARDINAL_END, walkable=True)
    if u <= C.AXIS_RAMP[1]:
        return ramp(u, C.AXIS_RAMP[0], C.AXIS_RAMP[1], C.Z_CARDINAL_END, C.DATUM, walkable=True)
    if u < C.AXIS_PLAZOLETA[1]:
        return C.DATUM
    return None


def prof_diag(r):
    if r <= C.RING_DESCENT[1]:
        return prof_common(r)
    if r <= C.DIAG_LANDMARK_END:
        return C.DATUM
    if r <= C.DIAG_RAMP_END:
        return ramp(r, C.DIAG_LANDMARK_END, C.DIAG_RAMP_END, C.DATUM, C.Z_MORADAS_MIN)
    w0, w1 = wall_step_rings()
    if r < w0:
        z = C.Z_MORADAS_MIN
        for R in terrace_jumps():
            a, b = R - STEP_RUN / 2.0, R + STEP_RUN / 2.0
            if r >= b:
                z += C.TERRACE_RISE
            elif r > a:
                z += C.TERRACE_RISE * (r - a) / (b - a)
        return z
    if r <= w1:
        return C.Z_MORADAS_MAX + (C.DATUM - C.Z_MORADAS_MAX) * (r - w0) / (w1 - w0)
    return prof_talud(r)


# ---------------------------------------------------------------------------
# Muros de contencion entre dos niveles
# ---------------------------------------------------------------------------
def face_run(dz):
    """Ancho horizontal de la cara de 80 grados para un desnivel dz."""
    return max(abs(dz), C.TERRACE_RISE) / TAN_FACE


def blend_wall(s, z_neg, z_pos):
    """Altura junto a una linea de borde. s = distancia firmada a la linea
    (s>0 lado 'pos'). La cara de 80 grados cae siempre en el lado bajo."""
    dz = z_pos - z_neg
    d = face_run(dz)
    if dz >= 0.0:                         # lado pos alto: cara en s in [-d, 0]
        if s >= 0.0:
            return z_pos
        if s <= -d:
            return z_neg
        return z_neg + dz * (1.0 + s / d)
    if s <= 0.0:                          # lado neg alto: cara en s in [0, d]
        return z_neg
    if s >= d:
        return z_pos
    return z_neg + dz * (s / d)


# ---------------------------------------------------------------------------
# Sectores
# ---------------------------------------------------------------------------
CARDINAL_KEYS = ("Oficios", "Mercado", "Clases", "Razas")             # 0, 90, 180, 270
DIAGONAL_KEYS = ("Morada_NE", "Morada_NW", "Morada_SW", "Morada_SE")  # 45, 135, 225, 315
CARDINAL_ANGLE = {"Oficios": 0.0, "Mercado": 90.0, "Clases": 180.0, "Razas": 270.0}
DIAGONAL_ANGLE = {"Morada_NE": 45.0, "Morada_NW": 135.0, "Morada_SW": 225.0, "Morada_SE": 315.0}


def angle_deg(x, y):
    return degrees(atan2(y, x)) % 360.0


def diag_angular_distance(theta):
    """Grados desde el eje diagonal mas cercano (0 = eje de Morada, 45 = eje cardinal)."""
    m = (theta - 45.0) % 90.0
    return min(m, 90.0 - m)


def s_lateral(r, theta):
    """Distancia firmada al borde lateral Morada/cardinal mas cercano (>0 dentro de la Morada)."""
    return r * sin(radians(C.MORADA_HALF_ANGLE - diag_angular_distance(theta)))


def nearest_cardinal(theta):
    return CARDINAL_KEYS[int(round(theta / 90.0)) % 4]


def nearest_diagonal(theta):
    return DIAGONAL_KEYS[int(((theta - 45.0) % 360.0 + 45.0) // 90.0) % 4]


def axis_frame(x, y, axis_deg):
    """(u, v): u a lo largo del eje, v perpendicular (CCW positivo)."""
    a = radians(axis_deg)
    return x * cos(a) + y * sin(a), -x * sin(a) + y * cos(a)


def card_z(x, y, r=None, th=None):
    r = sqrt(x * x + y * y) if r is None else r
    th = angle_deg(x, y) if th is None else th
    zo = prof_card(r)
    u, v = axis_frame(x, y, CARDINAL_ANGLE[nearest_cardinal(th)])
    if u < C.AXIS_DESCENT[0] - 1.0:
        return zo
    zb = prof_axis(u)
    if zb is None:
        return zo
    return blend_wall(HALF_BAND - abs(v), zo, zb)


def escalinata_weight(x, y, th=None):
    """0..1 peso del rebaje bajo la escalinata (1 = bajo los peldanos)."""
    th = angle_deg(x, y) if th is None else th
    u, v = axis_frame(x, y, DIAGONAL_ANGLE[nearest_diagonal(th)])
    av = abs(v)
    if av > ESC_HALF_OUT or u < ESC_U0 - ESC_EDGE or u > ESC_U1 + ESC_EDGE:
        return 0.0, u
    wu = min(1.0, (u - (ESC_U0 - ESC_EDGE)) / ESC_EDGE, ((ESC_U1 + ESC_EDGE) - u) / ESC_EDGE)
    wv = 1.0 if av <= ESC_HALF_W else (ESC_HALF_OUT - av) / (ESC_HALF_OUT - ESC_HALF_W)
    return max(0.0, wu) * wv, u


def escalinata_env(u):
    uu = min(max(u, ESC_U0), ESC_U1)
    return C.Z_MORADAS_MIN + (C.DATUM - C.Z_MORADAS_MIN) * (ESC_U1 - uu) / (ESC_U1 - ESC_U0) - ESC_CARVE


def height(x, y):
    r = sqrt(x * x + y * y)
    if r <= C.RING_DESCENT[1]:
        return prof_common(r)
    th = angle_deg(x, y)
    z = blend_wall(s_lateral(r, th), card_z(x, y, r, th), prof_diag(r))
    w, u = escalinata_weight(x, y, th)
    if w > 0.0:
        z_env = escalinata_env(u)
        if z > z_env:
            z = z + (z_env - z) * w
    return z


def lateral_dz(a, theta_b):
    """Desnivel Morada - cardinal sobre la linea de borde (a = distancia al centro)."""
    x, y = a * cos(radians(theta_b)), a * sin(radians(theta_b))
    return prof_diag(a) - card_z(x, y, a, theta_b % 360.0)


def lateral_edges():
    """[(morada, side, theta_b, e, n_card)]: e = direccion del borde, n_card = normal hacia el cardinal."""
    out = []
    for key, phi in DIAGONAL_ANGLE.items():
        for side in (-1, 1):
            tb = phi + side * C.MORADA_HALF_ANGLE
            e = (cos(radians(tb)), sin(radians(tb)))
            n = (-e[1], e[0]) if side > 0 else (e[1], -e[0])
            out.append((key, side, tb % 360.0, e, n))
    return out


if __name__ == "__main__":
    checks = [
        ("plaza centro", prof_common(0), 8.0), ("plaza borde r60", prof_common(60), Z_PLAZA_EDGE),
        ("r90", prof_common(90), 6.0), ("card r165", prof_card(165), 4.5), ("card r175", prof_card(175), 4.5),
        ("card r196", prof_card(196), 6.0), ("card r204", prof_card(204), 6.0), ("talud r212", prof_card(212), 0.0),
        ("eje u150", prof_axis(150), 4.5), ("eje u176", prof_axis(176), 6.0), ("plazoleta u186", prof_axis(186), 6.0),
        ("diag r95", prof_diag(95), 6.0), ("diag r105", prof_diag(105), 4.5), ("diag r182", prof_diag(182), 9.5),
        ("diag r204", prof_diag(204), 6.0), ("height Mercado eje r186", height(0, 186), 6.0),
        ("height Mercado fuera eje r170", height(40, 165.1), None),
    ]
    for name, got, want in checks:
        ok = "   " if want is None else ("OK " if abs(got - want) < 1e-9 else "BAD")
        print(f"{ok} {name:30s} {got:8.4f}  (esperado {want})")
    for seg in [("60-90", 60, 90, Z_PLAZA_EDGE, 6.0, True), ("card 90-165", 90, 165, 6.0, 4.5, True),
                ("terraplen 175-196", 175, 196, 4.5, 6.0, True), ("eje 90-150", 90, 150, 6.0, 4.5, True),
                ("eje 150-176", 150, 176, 4.5, 6.0, True), ("diag 95-105", 95, 105, 6.0, 4.5, False),
                ("talud 204-212", 204, 212, 6.0, 0.0, False)]:
        n, a, b, z0, z1, w = seg
        print(f"pendiente max teorica {n:18s} {ramp_max_slope_deg(a, b, z0, z1, w):6.2f} "
              f"(lineal {degrees(atan2(abs(z1 - z0), b - a)):5.2f})")
    print("desnivel lateral Morada NE borde 25 grados (a: dz):")
    print("  ", [(a, round(lateral_dz(a, 25.0), 2)) for a in (96, 100, 105, 112, 118, 120, 126, 132, 134,
                                                             140, 146, 148, 155, 160, 162, 170, 174, 176,
                                                             182, 188, 190, 196, 203)])
    print("desnivel banda eje Mercado (u: zb - zo en v=15):")
    print("  ", [(u, round(prof_axis(u) - prof_card(sqrt(u * u + 225)), 2)) for u in (100, 120, 140, 150, 155,
                                                                                    160, 165, 170, 176, 180,
                                                                                    185, 190, 195)])
