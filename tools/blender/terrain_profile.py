"""
CONCORDIA - perfil de alturas de la colina h(r, angulo). Python puro (sin bpy).

Transiciones: rampas con "rodillas" suavizadas. La pendiente sube y baja con
smoothstep en los extremos de cada rampa (longitud KNEE), de modo que:
  - las cotas en los radios del pedido son exactas,
  - la altura es continua y la pendiente tambien (sin aristas en los cambios),
  - la pendiente maxima es dz / (L - K), solo algo mayor que la lineal dz / L.
Los saltos de terraza NO se suavizan: son caras de 80 grados entre dos anillos.
"""

from math import atan2, degrees, radians, sqrt, tan

import concordia_const as C

# ---------------------------------------------------------------------------
# Parametros artisticos (no vienen del pedido; ajustables)
# ---------------------------------------------------------------------------
KNEE_MAX = 4.0        # longitud maxima de rodilla (m)
KNEE_FRAC = 0.15      # rodilla = min(KNEE_MAX, KNEE_FRAC * L) en rampas cortas

STEP_RUN = C.TERRACE_RISE / tan(radians(C.TERRACE_FACE_ANGLE))     # 0.1763 m
WALL_STEP_DROP = (C.Z_MORADAS_MAX - C.DATUM)                         # 3.5 m
WALL_STEP_RUN = WALL_STEP_DROP / tan(radians(C.TERRACE_FACE_ANGLE))  # 0.6171 m
Z_PLAZA_EDGE = C.Z_PLAZA - C.PLAZA_DRAIN * C.PLAZA_RADIUS            # 7.70


def smoothstep(e0, e1, x):
    if x <= e0:
        return 0.0
    if x >= e1:
        return 1.0
    t = (x - e0) / (e1 - e0)
    return t * t * (3.0 - 2.0 * t)


def knee_len(r0, r1):
    return min(KNEE_MAX, KNEE_FRAC * (r1 - r0))


def _knee_int(t):
    # integral de smoothstep(0,1,t) entre 0 y t
    return t ** 3 - 0.5 * t ** 4


def ramp(r, r0, r1, z0, z1, k=None):
    """Rampa z0->z1 entre r0 y r1 con rodillas smoothstep de longitud k."""
    if r <= r0:
        return z0
    if r >= r1:
        return z1
    L = r1 - r0
    k = knee_len(r0, r1) if k is None else k
    k = min(k, L / 2.0)
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


def ramp_max_slope_deg(r0, r1, z0, z1):
    L = r1 - r0
    k = min(knee_len(r0, r1), L / 2.0)
    return degrees(atan2(abs(z1 - z0), L - k))


# ---------------------------------------------------------------------------
# Saltos de terraza (radios) y anillos de aristas
# ---------------------------------------------------------------------------
def terrace_jumps():
    """Radios centrales de los saltos entre terrazas (5 saltos: 119..175)."""
    return [C.TERRACE_START_R + C.TERRACE_DEPTH * j for j in range(1, C.TERRACE_COUNT)]


def wall_step_rings():
    """Salto 9.5 -> 6.0 bajo la cara exterior de la muralla (solo diagonales)."""
    r_out = C.WALL_BASE_R[1]
    return (r_out - WALL_STEP_RUN, r_out)


def ring_pairs():
    """[(r_bajo_interior, r_alto_exterior)] de cada cara casi vertical."""
    pairs = [(R - STEP_RUN / 2.0, R + STEP_RUN / 2.0) for R in terrace_jumps()]
    w0, w1 = wall_step_rings()
    pairs.append((w0, w1))   # aqui el lado interior es el ALTO (9.5) y el exterior 6.0
    return pairs


def terrace_index(r):
    """1..6 si r cae en una terraza (105..189), si no 0."""
    if r < C.TERRACE_START_R or r >= C.TERRACE_END_R:
        return 0
    return int((r - C.TERRACE_START_R) // C.TERRACE_DEPTH) + 1


# ---------------------------------------------------------------------------
# Perfiles radiales
# ---------------------------------------------------------------------------
def prof_common(r):
    if r <= C.PLAZA_RADIUS:
        return C.Z_PLAZA - C.PLAZA_DRAIN * r
    return ramp(r, C.RING_DESCENT[0], C.RING_DESCENT[1], Z_PLAZA_EDGE, C.DATUM)


def prof_talud(r):
    return ramp(r, C.TALUD_R[0], C.TALUD_R[1], C.DATUM, C.Z_EXTERIOR)


def prof_card(r):
    if r <= C.RING_DESCENT[1]:
        return prof_common(r)
    if r <= C.CARD_SLOPE_END:
        return ramp(r, C.RING_DESCENT[1], C.CARD_SLOPE_END, C.DATUM, C.Z_CARDINAL_END)
    if r <= C.CARD_FLAT_END:
        return C.Z_CARDINAL_END
    if r <= C.CARD_EMBANK_END:
        return ramp(r, C.CARD_FLAT_END, C.CARD_EMBANK_END, C.Z_CARDINAL_END, C.DATUM)
    if r <= C.WALL_BASE_R[1]:
        return C.DATUM
    return prof_talud(r)


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
# Sectores
# ---------------------------------------------------------------------------
CARDINAL_KEYS = ("Oficios", "Mercado", "Clases", "Razas")          # 0, 90, 180, 270
DIAGONAL_KEYS = ("Morada_NE", "Morada_NW", "Morada_SW", "Morada_SE")  # 45, 135, 225, 315


def angle_deg(x, y):
    return degrees(atan2(y, x)) % 360.0


def diag_angular_distance(theta):
    """Grados desde el eje diagonal mas cercano (0 = eje de Morada, 45 = eje cardinal)."""
    m = (theta - 45.0) % 90.0
    return min(m, 90.0 - m)


def diag_weight(r, theta):
    """0 = sector cardinal, 1 = sector diagonal; mezcla en SECTOR_BLEND_WIDTH m de arco."""
    s = r * radians(C.MORADA_HALF_ANGLE - diag_angular_distance(theta))
    hw = C.SECTOR_BLEND_WIDTH / 2.0
    return smoothstep(-hw, hw, s)


def nearest_cardinal(theta):
    return CARDINAL_KEYS[int(round(theta / 90.0)) % 4]


def nearest_diagonal(theta):
    return DIAGONAL_KEYS[int(((theta - 45.0) % 360.0 + 45.0) // 90.0) % 4]


def height(x, y):
    r = sqrt(x * x + y * y)
    if r <= C.RING_DESCENT[1]:
        return prof_common(r)
    w = diag_weight(r, angle_deg(x, y))
    if w <= 0.0:
        return prof_card(r)
    if w >= 1.0:
        return prof_diag(r)
    return prof_card(r) * (1.0 - w) + prof_diag(r) * w


def ring_half_angle(R):
    """Semiancho angular (grados, desde el eje diagonal) donde hay que cortar anillos."""
    return C.MORADA_HALF_ANGLE + degrees((C.SECTOR_BLEND_WIDTH / 2.0 + 1.5) / R)


if __name__ == "__main__":
    # Autocomprobacion de cotas del pedido
    checks = [
        ("plaza centro", prof_common(0), 8.0),
        ("plaza borde r60", prof_common(60), Z_PLAZA_EDGE),
        ("r90", prof_common(90), 6.0),
        ("card r165", prof_card(165), 4.5),
        ("card r185", prof_card(185), 4.5),
        ("card r196", prof_card(196), 6.0),
        ("card r204", prof_card(204), 6.0),
        ("talud r212", prof_card(212), 0.0),
        ("diag r95", prof_diag(95), 6.0),
        ("diag r105", prof_diag(105), 4.5),
        ("diag terraza1 r112", prof_diag(112), 4.5),
        ("diag terraza6 r182", prof_diag(182), 9.5),
        ("diag r189", prof_diag(189), 9.5),
        ("diag r203", prof_diag(203), 9.5),
        ("diag r204", prof_diag(204), 6.0),
        ("diag r212", prof_diag(212), 0.0),
    ]
    for name, got, want in checks:
        print(f"{'OK ' if abs(got - want) < 1e-9 else 'BAD'} {name:22s} {got:8.4f}  (esperado {want})")
    print("terrazas:", [(k, C.Z_MORADAS_MIN + (k - 1) * C.TERRACE_RISE) for k in range(1, 7)])
    print("saltos:", terrace_jumps(), "run cara 80deg =", round(STEP_RUN, 4), "m")
    for seg in [("60-90", 60, 90, Z_PLAZA_EDGE, 6.0), ("card 90-165", 90, 165, 6.0, 4.5),
                ("terraplen 185-196", 185, 196, 4.5, 6.0), ("diag 95-105", 95, 105, 6.0, 4.5),
                ("talud 204-212", 204, 212, 6.0, 0.0)]:
        n, a, b, z0, z1 = seg
        print(f"pendiente max teorica {n:18s} {ramp_max_slope_deg(a, b, z0, z1):6.2f} deg "
              f"(lineal {degrees(atan2(abs(z1 - z0), b - a)):5.2f})")
