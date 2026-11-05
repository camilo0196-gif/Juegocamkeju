"""
CONCORDIA - trazado del Cauce (Python puro). Lo usan stage05_layout (reserva del corredor) y stage07_cauce.

Recorrido (ref. Brujas):
  Fuente del Mercado (vertiente, r=105 en el eje Norte) -> sale por su lado Este hacia dentro ->
  arco r = ARC_R (terreno a +6.0 en Mercado, zona de hitos NE y Oficios) -> en Oficios gira hacia
  fuera por el radio de 345 grados (desague del bastion k=46) -> alcantarilla bajo la muralla.
Seccion: canal de WIDTH m y DEPTH m (borde -> fondo); agua plana WATER_BELOW m bajo el borde en cada
tramo; orillas de piedra de BANK m. El borde baja en escalones de STEP m (azudes) siguiendo el terreno
y nunca por debajo de EDGE_MIN; en el terraplen final el canal va en trinchera (el terreno sube, el
agua no puede subir).
"""

from math import atan2, cos, degrees, hypot, pi, radians, sin

import concordia_const as C
import terrain_profile as T

WIDTH = 4.0
DEPTH = 1.2
WATER_BELOW = 0.4
BANK = 1.0
CORRIDOR_HALF = WIDTH / 2 + BANK          # 3.0 m (reserva de 6 m)
ARC_R = 89.5
OUTLET_DEG = 46 * 7.5 - 360.0             # -15 grados (345)
TURN_DEG = -6.0                            # donde el arco empieza a girar hacia fuera
FOUNTAIN_C = (0.0, 105.0)
FOUNTAIN_R = 11.0
START_ANG = -48.0                          # punto de salida sobre el borde de la fuente (desde su centro)
END_R = 196.6                              # boca de la alcantarilla (cara interior de la muralla)
STEP = 0.3
EDGE_TOP = 5.90
EDGE_MIN = 4.50
STEP_SPACING = 20.0                        # escalones de acceso


def _arc(r, a0, a1, step=1.0):
    n = max(2, int(abs(radians(a1 - a0)) * r / step) + 1)
    return [(r * cos(radians(a0 + (a1 - a0) * i / (n - 1))), r * sin(radians(a0 + (a1 - a0) * i / (n - 1))))
            for i in range(n)]


def centerline(step=1.0):
    """Polilinea del eje del canal (x, y), de la fuente a la alcantarilla, puntos cada ~step m."""
    cx, cy = FOUNTAIN_C
    p0 = (cx + FOUNTAIN_R * cos(radians(START_ANG)), cy + FOUNTAIN_R * sin(radians(START_ANG)))
    a_start = degrees(atan2(p0[1], p0[0]))
    pts = [p0]
    # 1) de la fuente al arco: transicion suave del radio (r0 -> ARC_R) en 8 grados
    r0 = hypot(*p0)
    a1 = a_start - 8.0
    n = 12
    for i in range(1, n + 1):
        t = i / n
        s = t * t * (3 - 2 * t)
        r = r0 + (ARC_R - r0) * s
        a = a_start + (a1 - a_start) * t
        pts.append((r * cos(radians(a)), r * sin(radians(a))))
    # 2) arco hasta TURN_DEG
    pts += _arc(ARC_R, a1, TURN_DEG, step)[1:]
    # 3) giro hacia fuera hasta el radio de 345 grados (curva de 9 m)
    n = 14
    for i in range(1, n + 1):
        t = i / n
        s = t * t * (3 - 2 * t)
        a = TURN_DEG + (OUTLET_DEG - TURN_DEG) * s
        r = ARC_R + 14.0 * t
        pts.append((r * cos(radians(a)), r * sin(radians(a))))
    # 4) radial hasta la muralla
    r = hypot(*pts[-1])
    while r < END_R:
        r = min(END_R, r + step)
        pts.append((r * cos(radians(OUTLET_DEG)), r * sin(radians(OUTLET_DEG))))
    return pts


def cumlen(pts):
    out = [0.0]
    for a, b in zip(pts, pts[1:]):
        out.append(out[-1] + hypot(b[0] - a[0], b[1] - a[1]))
    return out


def edge_profile(pts):
    """Cota del borde E(s) (escalonada, no creciente) y del agua W = E - 0.4 por punto del eje."""
    E = []
    cur = EDGE_TOP
    for p in pts:
        ground = T.height(*p)
        # baja un escalon cuando el terreno queda 0.25 m por debajo del borde actual
        while cur - STEP >= EDGE_MIN - 1e-9 and ground < cur - 0.25:
            cur = round(cur - STEP, 3)
        E.append(cur)
    return E, [e - WATER_BELOW for e in E]


def weirs(pts, E):
    out = []
    cum = cumlen(pts)
    for i in range(1, len(E)):
        if E[i] < E[i - 1] - 1e-6:
            out.append({"s": round(cum[i], 2), "pt": pts[i], "drop": round(E[i - 1] - E[i], 3),
                        "edge_before": E[i - 1], "edge_after": E[i]})
    return out


def corridor_poly(pts, half=CORRIDOR_HALF):
    """Poligono cerrado del corredor (eje +- half)."""
    L, R = [], []
    n = len(pts)
    for i in range(n):
        a = pts[max(0, i - 1)]
        b = pts[min(n - 1, i + 1)]
        tx, ty = b[0] - a[0], b[1] - a[1]
        Lt = hypot(tx, ty) or 1.0
        nx, ny = -ty / Lt, tx / Lt
        L.append((pts[i][0] + nx * half, pts[i][1] + ny * half))
        R.append((pts[i][0] - nx * half, pts[i][1] - ny * half))
    return L + list(reversed(R))


def district_of(p):
    th = T.angle_deg(*p)
    r = hypot(*p)
    if T.s_lateral(r, th) > 0:
        return "Diagonal"
    return {"Oficios": "Oficios", "Mercado": "Mercado", "Clases": "Clases", "Razas": "Razas"}[T.nearest_cardinal(th)]


if __name__ == "__main__":
    pts = centerline()
    E, W = edge_profile(pts)
    cum = cumlen(pts)
    print("longitud", round(cum[-1], 1), "puntos", len(pts))
    for w in weirs(pts, E):
        print("azud", w["s"], [round(v, 1) for v in w["pt"]], w["drop"], w["edge_after"])
    for s_, p, e in list(zip(cum, pts, E))[::25]:
        print(round(s_, 1), [round(v, 1) for v in p], "r", round(hypot(*p), 1), "th", round(T.angle_deg(*p), 1),
              "terreno", round(T.height(*p), 2), "borde", e)
