"""
CONCORDIA - Etapa 22 (E9): conexiones entre barrios y sobre el Cauce.

Referencias: canales de Brujas (puentes de piedra de arco muy rebajado sobre un canal estrecho), Mala Strana de Praga
(arcos sobre calles y escalinatas), Toledo (arcos de piedra entre casas).

Piezas (constructores parametricos sobre bld_kit.MB; materiales ya aprobados):
  BRIDGE_Stone_5m / _6m   puente de arco rebajado: calzada 0.4 m sobre las calles con rampas, pretiles de 0.9 m con
                          albardilla, imposta, dovelas con clave, estribos con sillares, remiendos de otra piedra.
  ARCH_Street_4m/5m/6m    arco sobre una calle entre dos edificios: 5 m de altura libre (arranque a 5 m), paso alto
                          a 6.4 m (planta 2 de las casas), linterna de esquirla en la clave (las dos caras).
  STAIRS_Monumental       escalinata de las diagonales (r 95-105): 6 m, 10 x 0.15 / 1.0, descanso de 2 m,
                          pasamanos de piedra de 0.9 m con pilares (perfil del Prompt 2).
  STAIRS_Terrace          escaleras de las terrazas de las Moradas (2.5 m; 6 m en el eje) y de los muros laterales
                          (2.5 m de paso, altura variable); STAIRS_Pass_3m: escalinatas de paso del Prompt 7.
  RAIL_Stone_3m(_Low)     pretil de piedra instanciable de 3 m (0.9 m y 0.5 m), variante con remiendo.

Convenio: +Y local = sentido de paso (cruzar el puente o el arco, bajar las escalinatas, subir las escaleras de
terraza); +Z arriba. Colision ("-colonly"): superficie de paso plana y continua (rampas en lugar de peldanos) + muros.
"""

import math
import random

from mathutils import Matrix

import bld_kit as K

ST, LIGHT, REPAIR = "MAT_Limestone_Worn", "MAT_Limestone_Light", K.M_REPAIR
COBBLE, IRON, SLAB, COL = K.M_COBBLE, K.M_IRON, "MAT_Plaza_Slab", "MAT_Wall_Gray"
PARAPET_H, PARAPET_T = 0.9, 0.3


# --------------------------------------------------------------------------- utilidades
def along_prism(mb, prof, x0, x1, mat):
    """Perfil (y, z) extruido a lo ancho entre x0 y x1. Tapas teseladas con mathutils.geometry.tessellate_polygon
    (los perfiles con el hueco del arco son muy concavos: la triangulacion de n-gonos de bmesh cruzaba el hueco)."""
    from mathutils import Vector
    from mathutils.geometry import tessellate_polygon
    pts = _clean(prof)
    mi = mb.mi(mat)
    tri = tessellate_polygon([[Vector((y, z, 0.0)) for y, z in pts]])
    caps = []
    for x in (x0, x1):
        caps.append([mb.v((x, y, z)) for y, z in pts])
    for k, vs in enumerate(caps):
        for t in tri:
            ids = t if k == 1 else t[::-1]
            try:
                f = mb.bm.faces.new([vs[i] for i in ids])
                f.material_index = mi
            except ValueError:
                pass
    a, b = caps
    n = len(pts)
    for i in range(n):
        j = (i + 1) % n
        try:
            f = mb.bm.faces.new([a[i], a[j], b[j], b[i]])
            f.material_index = mi
        except ValueError:
            pass


def _clean(pts):
    out = []
    for p in pts:
        if not out or abs(out[-1][0] - p[0]) > 1e-6 or abs(out[-1][1] - p[1]) > 1e-6:
            out.append(p)
    if len(out) > 2 and abs(out[0][0] - out[-1][0]) < 1e-6 and abs(out[0][1] - out[-1][1]) < 1e-6:
        out.pop()
    return out


def seg_arc(c, f, z_s, n, y_c=0.0):
    """Arco rebajado de luz 2c y flecha f desde z_s: puntos de +c a -c. Devuelve (puntos, R, z_centro)."""
    R = (c * c + f * f) / (2 * f)
    zc = z_s + f - R
    th = math.asin(min(1.0, c / R))
    pts = []
    for i in range(n + 1):
        t = th - 2 * th * i / n
        pts.append((y_c + R * math.sin(t), zc + R * math.cos(t)))
    return pts, R, zc, th


def interp(prof, y):
    """z de una polilinea (y creciente) en y."""
    for (y0, z0), (y1, z1) in zip(prof, prof[1:]):
        if y0 - 1e-9 <= y <= y1 + 1e-9:
            return z0 + (z1 - z0) * (y - y0) / max(1e-9, y1 - y0)
    return prof[0][1] if y < prof[0][0] else prof[-1][1]


def band(mb, line, x0, x1, dz0, dz1, mat, seg=None, rng=None, repair=0.0, stats=None):
    """Banda que sigue la polilinea 'line' (y, z): de z+dz0 a z+dz1, entre x0 y x1; troceada en tramos de 'seg' m
    (un 'repair' de ellos con piedra de remiendo)."""
    for (ya, za), (yb, zb) in zip(line, line[1:]):
        n = 1 if not seg else max(1, int(math.ceil((yb - ya) / seg - 1e-6)))
        for k in range(n):
            y0 = ya + (yb - ya) * k / n
            y1 = ya + (yb - ya) * (k + 1) / n
            z0 = za + (zb - za) * k / n
            z1 = za + (zb - za) * (k + 1) / n
            m = mat
            if rng is not None and rng.random() < repair:
                m = REPAIR
                if stats is not None:
                    stats["repaired_segments"] = stats.get("repaired_segments", 0) + 1
            if stats is not None:
                stats["segments"] = stats.get("segments", 0) + 1
            along_prism(mb, [(y0, z0 + dz0), (y1, z1 + dz0), (y1, z1 + dz1), (y0, z0 + dz1)], x0, x1, m)


def face_quad(mb, x, y0, y1, z0, z1, mat, side):
    """Cara plana en el plano x (remiendos de sillar), mirando a +X (side=1) o -X."""
    mb.face([(x, y0, z0), (x, y1, z0), (x, y1, z1), (x, y0, z1)], mat, nrm=(side, 0, 0))


def quoins(mb, x_face, side, y_edge, inward, z0, z1, rng, mat=LIGHT, h=0.42):
    """Sillares de esquina en la arista vertical (x_face, y_edge): largos y cortos alternos, 2 cm fuera del plano,
    cara frontal + canto."""
    z = z0
    k = 0
    while z < z1 - 0.05:
        zt = min(z1, z + h)
        L = 0.75 if k % 2 == 0 else 0.45
        ya, yb = sorted((y_edge, y_edge + inward * L))
        xo = x_face + side * 0.02
        face_quad(mb, xo, ya, yb, z + 0.01, zt - 0.01, mat, side)
        mb.face([(x_face, ya, zt - 0.01), (xo, ya, zt - 0.01), (xo, yb, zt - 0.01), (x_face, yb, zt - 0.01)], mat,
                nrm=(0, 0, 1))
        z = zt
        k += 1
    return k


# --------------------------------------------------------------------------- puente
def bridge(mb, cm, W, hs, span, z_road, e, w, ramp_a, ramp_b, rng, stats, n_vous=11, z_ends=None):
    """Puente de arco rebajado. Origen en el centro del tablero a la cota de la calzada (z = 0 = deck); +Y = eje del
    puente (sentido de paso), X a lo ancho. z_road, e (borde del cauce), w (agua) relativos al tablero.
    hs: semilongitud del tramo sobre el cauce (corredor), span: semiluz del arco. ramp_a / ramp_b: rampas en -Y / +Y."""
    yA, y1, y2, yB = -(hs + ramp_a), -hs, hs, hs + ramp_b
    za, zb_ = z_ends or (z_road, z_road)          # cota real de la calle en cada extremo de rampa
    top = [(yA, za), (y1, 0.0), (y2, 0.0), (yB, zb_)]
    bed = e - 1.2
    spring = w - 0.1
    crown = -0.65
    arc, R, zc, th = seg_arc(span, crown - spring, spring, 12)
    T = 0.5
    prof = [(yA, za), (y1, 0.0), (y2, 0.0), (yB, zb_), (yB, min(zb_, z_road) - T), (y2, z_road - T), (y2, bed - 0.2),
            (span, bed - 0.2)] + arc + [(-span, bed - 0.2), (y1, bed - 0.2), (y1, z_road - T), (yA, min(za, z_road) - T)]
    along_prism(mb, prof, -W / 2, W / 2, ST)
    # calzada empedrada (1 cm por encima, entre pretiles)
    hw = W / 2 - PARAPET_T
    for (ya, z_a), (yb, z_b) in zip(top, top[1:]):
        mb.face([(-hw, ya, z_a + 0.01), (hw, ya, z_a + 0.01), (hw, yb, z_b + 0.01), (-hw, yb, z_b + 0.01)], COBBLE,
                nrm=(0, 0, 1))
    # dovelas y clave (las dos caras), una de repuesto en otra piedra
    ring = 0.4
    rep_i = rng.randrange(n_vous)
    while rep_i == n_vous // 2:
        rep_i = rng.randrange(n_vous)
    for side in (1, -1):
        x0 = side * W / 2
        for i in range(n_vous):
            t0 = th - 2 * th * i / n_vous
            t1 = th - 2 * th * (i + 1) / n_vous
            key = i == n_vous // 2
            rr = ring + (0.12 if key else 0.0)
            q = [(R * math.sin(t0), zc + R * math.cos(t0)), ((R + rr) * math.sin(t0), zc + (R + rr) * math.cos(t0)),
                 ((R + rr) * math.sin(t1), zc + (R + rr) * math.cos(t1)), (R * math.sin(t1), zc + R * math.cos(t1))]
            out = 0.05 if key else 0.025
            m = REPAIR if (i == rep_i and side == 1) else LIGHT
            along_prism(mb, q, *sorted((x0, x0 + side * out)), m)
    stats["voussoirs"] = 2 * n_vous
    # imposta siguiendo el tablero y pretiles de 0.9 m con albardilla (tramos de 2 m, 20 % remendados)
    for side in (1, -1):
        xo = side * W / 2
        band(mb, top, *sorted((xo - side * 0.01, xo + side * 0.07)), -0.22, -0.06, LIGHT)
        band(mb, top, *sorted((xo, xo - side * PARAPET_T)), 0.0, PARAPET_H - 0.08, ST, seg=2.0, rng=rng, repair=0.2,
             stats=stats)
        band(mb, top, *sorted((xo + side * 0.04, xo - side * (PARAPET_T + 0.04))), PARAPET_H - 0.08, PARAPET_H, LIGHT)
        # pilares de arranque en los cuatro extremos
        # 5 cm por fuera de la testa y del costado: sin caras coplanarias con el tablero ni con el pretil
        for yy, zz in ((yA + 0.2, za + 0.2 / max(0.1, ramp_a) * (0 - za)),
                       (yB - 0.2, zb_ + 0.2 / max(0.1, ramp_b) * (0 - zb_))):
            cx = side * (W / 2 - 0.2)
            mb.box((cx - 0.25, yy - 0.25, zz - 0.1), (cx + 0.25, yy + 0.25, zz + 1.05), ST, skip=("z-",))
            mb.box((cx - 0.3, yy - 0.3, zz + 1.05), (cx + 0.3, yy + 0.3, zz + 1.15), LIGHT)
        # sillares de los estribos (aristas del tramo y de los arranques del arco)
        n = 0
        for y_edge, inward in ((y1, 1), (y2, -1)):
            n += quoins(mb, xo, side, y_edge, inward, bed + 0.2, z_road - 0.1, rng)
        for y_edge, inward in ((span, 1), (-span, -1)):
            n += quoins(mb, xo, side, y_edge, inward, bed + 0.2, spring, rng, h=0.36)
        stats["quoins"] = stats.get("quoins", 0) + n
        # remiendos de piedra distinta en los timpanos y estribos
        cands = [(span + 0.15, y2 - 0.2), (-y2 + 0.2, -span - 0.15)]
        for k in range(rng.randint(1, 2)):
            ya, yb = cands[k % 2]
            if yb - ya < 0.4:
                continue
            u0 = rng.uniform(ya, yb - 0.35)
            u1 = min(yb, u0 + rng.uniform(0.35, 0.7))
            z0 = rng.uniform(spring + 0.05, max(spring + 0.1, -0.75))
            z1 = min(-0.3, z0 + rng.uniform(0.25, 0.45))
            if z1 - z0 > 0.12:
                face_quad(mb, xo + side * 0.012, u0, u1, z0, z1, REPAIR, side)
                stats["patches"] = stats.get("patches", 0) + 1
    # colision: superficie de paso continua (de calle a calle) + pretiles
    walk = [(yA - 0.3, za - 0.04)] + top + [(yB + 0.3, zb_ - 0.04)]
    along_prism(cm, walk + [(yB + 0.3, min(za, zb_, z_road) - 0.6), (yA - 0.3, min(za, zb_, z_road) - 0.6)], -hw, hw, COL)
    for side in (1, -1):
        band(cm, top, *sorted((side * W / 2, side * hw)), -0.3, PARAPET_H + 0.05, COL)
    stats.update({"length_m": round(yB - yA, 2), "width_m": W, "ramps_m": [round(ramp_a, 2), round(ramp_b, 2)],
                  "ramp_deg": [round(math.degrees(math.atan2(-z, r)), 2) for z, r in ((za, ramp_a), (zb_, ramp_b))],
                  "street_at_ends_rel_deck_m": [round(za, 3), round(zb_, 3)],
                  "arch_span_m": round(2 * span, 2), "arch_rise_m": round(crown - spring, 2),
                  "clear_over_water_m": round(crown - w, 2), "deck_over_street_m": round(-z_road, 2)})
    return top


# --------------------------------------------------------------------------- arco sobre calle
class ARCH:
    SPRING = 5.0            # altura libre: el arco arranca a 5 m sobre la calle
    DECK = 6.4              # paso alto a la cota de la planta 2 (2 x 3.2)
    DEPTH = 2.6             # grosor a lo largo de la calle (marcador)
    PIER = 0.8


def arch_street(mb, cm, S, rng, stats, pier_l=ARCH.PIER, pier_r=ARCH.PIER, z_base=-0.4):
    """Arco sobre calle de luz libre S. Origen en el eje de la calle a la cota de la calle (z = 0), +Y = cruza la
    calle (de un edificio al otro), X a lo largo de la calle (grosor 2.6 m)."""
    D = ARCH.DEPTH
    f = S * 0.15
    arc, R, zc, th = seg_arc(S / 2, f, ARCH.SPRING, 14)
    yl, yr = -S / 2 - pier_l, S / 2 + pier_r
    prof = [(yl, z_base), (-S / 2, z_base), (-S / 2, ARCH.SPRING)] + arc[::-1] + [(S / 2, ARCH.SPRING), (S / 2, z_base),
                                                                                 (yr, z_base), (yr, ARCH.DECK), (yl, ARCH.DECK)]
    along_prism(mb, prof, -D / 2, D / 2, ST)
    mb.face([(-D / 2 + 0.05, yl, ARCH.DECK + 0.01), (D / 2 - 0.05, yl, ARCH.DECK + 0.01),
             (D / 2 - 0.05, yr, ARCH.DECK + 0.01), (-D / 2 + 0.05, yr, ARCH.DECK + 0.01)], SLAB, nrm=(0, 0, 1))
    n_v = 9
    rep_i = rng.choice([i for i in range(n_v) if i != n_v // 2])
    for side in (1, -1):
        x0 = side * D / 2
        # sillares de los pilares (aristas hacia la calle) e impostas
        n = 0
        for y_edge, inward in ((-S / 2, -1), (S / 2, 1)):
            n += quoins(mb, x0, side, y_edge, inward, 0.0, ARCH.SPRING - 0.25, rng, h=0.5)
            ya, yb = sorted((y_edge, y_edge + inward * 0.9))
            xa, xb = sorted((x0, x0 + side * 0.08))
            mb.box((xa, ya, ARCH.SPRING - 0.25), (xb, yb, ARCH.SPRING), LIGHT, skip=("z-",))
        stats["quoins"] = stats.get("quoins", 0) + n
        # dovelas y clave
        for i in range(n_v):
            t0 = th - 2 * th * i / n_v
            t1 = th - 2 * th * (i + 1) / n_v
            key = i == n_v // 2
            rr = 0.55 + (0.2 if key else 0.0)
            q = [(R * math.sin(t0), zc + R * math.cos(t0)), ((R + rr) * math.sin(t0), zc + (R + rr) * math.cos(t0)),
                 ((R + rr) * math.sin(t1), zc + (R + rr) * math.cos(t1)), (R * math.sin(t1), zc + R * math.cos(t1))]
            out = 0.07 if key else 0.03
            m = REPAIR if (i == rep_i and side == 1) else LIGHT
            along_prism(mb, q, *sorted((x0, x0 + side * out)), m)
        # imposta del paso alto
        xa, xb = sorted((x0 - side * 0.01, x0 + side * 0.08))
        mb.box((xa, yl, ARCH.DECK - 0.2), (xb, yr, ARCH.DECK - 0.05), LIGHT)
        # linterna de esquirla colgada de la clave
        crown = ARCH.SPRING + f
        mb.push(Matrix.Translation((x0 + side * 0.07, 0.0, crown + 0.05)) @ Matrix.Rotation(-side * math.pi / 2, 4, "Z"))
        K.lantern_shard(mb)
        mb.pop()
        # remiendo en un pilar
        if rng.random() < 0.8:
            yy = rng.choice((-1, 1)) * (S / 2 + 0.05)
            ya, yb = sorted((yy, yy + math.copysign(min(0.6, (pier_l if yy < 0 else pier_r) - 0.1), yy)))
            z0 = rng.uniform(0.8, 3.2)
            face_quad(mb, x0 + side * 0.012, ya, yb, z0, z0 + rng.uniform(0.3, 0.5), REPAIR, side)
            stats["patches"] = stats.get("patches", 0) + 1
    # colision: pilares, arco macizo por encima del arranque y paso alto plano
    for ya, yb in ((yl, -S / 2), (S / 2, yr)):
        cm.box((-D / 2, ya, z_base), (D / 2, yb, ARCH.DECK), COL)
    cm.box((-D / 2, -S / 2, ARCH.SPRING), (D / 2, S / 2, ARCH.DECK), COL)
    stats.update({"clear_span_m": S, "clear_height_m": ARCH.SPRING, "crown_m": round(ARCH.SPRING + f, 2),
                  "walkway_m": ARCH.DECK, "piers_m": [round(pier_l, 2), round(pier_r, 2)], "depth_m": D,
                  "walkway_length_m": round(yr - yl, 2), "lanterns": 2})
    return yl, yr


# --------------------------------------------------------------------------- pretil instanciable
def rail(mb, cm, L=3.0, h=0.9, patch=False):
    """Pretil de piedra de L m a lo largo de +Y (origen en el centro de la base): zocalo, muro, albardilla."""
    t = 0.3
    mb.box((-t / 2 - 0.03, -L / 2, -0.1), (t / 2 + 0.03, L / 2, 0.1), ST, skip=("z-",))
    mb.box((-t / 2, -L / 2, 0.1), (t / 2, L / 2, h - 0.09), REPAIR if patch else ST, skip=("z-", "z+"))
    mb.box((-t / 2 - 0.04, -L / 2, h - 0.09), (t / 2 + 0.04, L / 2, h), LIGHT)
    # junta de sillares marcada: dos llagas verticales por cara (resalte de 1 cm)
    for y in (-L / 6, L / 6):
        for s in (1, -1):
            mb.face([(s * (t / 2 + 0.01), y - 0.02, 0.12), (s * (t / 2 + 0.01), y + 0.02, 0.12),
                     (s * (t / 2 + 0.01), y + 0.02, h - 0.1), (s * (t / 2 + 0.01), y - 0.02, h - 0.1)], LIGHT, nrm=(s, 0, 0))
    if patch:
        mb.face([(t / 2 + 0.012, -0.5, 0.25), (t / 2 + 0.012, 0.3, 0.25), (t / 2 + 0.012, 0.3, h - 0.25),
                 (t / 2 + 0.012, -0.5, h - 0.25)], LIGHT, nrm=(1, 0, 0))
    if cm is not None:
        cm.box((-t / 2, -L / 2, -0.1), (t / 2, L / 2, h + 0.05), COL)


# --------------------------------------------------------------------------- escalinata monumental
MONO_RISERS = (0.0, 1.0, 2.0, 3.0, 4.0, 6.0, 7.0, 8.0, 9.0, 10.0)      # r 95..105 (Prompt 2)
MONO_R, MONO_W, MONO_BAL = 0.15, 6.0, 0.45


def mono_treads():
    """[(y0, y1, z)] de huellas y descanso (z relativo a DATUM, y = r - 95)."""
    out = []
    for k in range(1, len(MONO_RISERS)):
        out.append((MONO_RISERS[k - 1], MONO_RISERS[k], -k * MONO_R))
    return out


def stairs_monumental(mb, cm, rng, stats):
    """Escalinata de 6 m: origen en el eje a r 95 (cota DATUM), +Y hacia fuera (bajando)."""
    tr = mono_treads()
    zb = -1.5
    zf = zb - 0.5
    end = MONO_RISERS[-1]
    prof = [(-0.1, 0.01), (0.0, 0.01)]
    for y0, y1, z in tr:
        prof += [(y0, z), (y1, z)]
    prof += [(end, zb), (end, zf), (-0.1, zf)]
    hw = MONO_W / 2
    along_prism(mb, prof, -hw, hw, ST)
    # bocel de cada peldano (3 cm de vuelo), uno sustituido por otra piedra
    rep = rng.randrange(len(MONO_RISERS))
    for k, y in enumerate(MONO_RISERS):
        zt = 0.01 if k == 0 else -k * MONO_R
        mb.box((-hw, y, zt - 0.06), (hw, y + 0.035, zt), REPAIR if k == rep else LIGHT, skip=("y-",))
    stats["treads_replaced"] = 1
    # pasamanos de piedra 0.9 m (muro de balaustrada con albardilla inclinada) y pilares
    rail_line = [(-0.5, 0.9), (0.0, 0.9), (4.0, -0.75 + 0.9), (6.0, -0.75 + 0.9), (10.0, zb + 0.9), (10.5, zb + 0.9)]
    for side in (1, -1):
        x0, x1 = sorted((side * hw, side * (hw + MONO_BAL)))
        body = [(y, z - 0.08) for y, z in rail_line] + [(10.5, zf), (-0.5, zf)]
        along_prism(mb, body, x0, x1, ST)
        cx0, cx1 = sorted((side * (hw - 0.05), side * (hw + MONO_BAL + 0.05)))
        band(mb, rail_line, cx0, cx1, -0.08, 0.02, LIGHT)
        for y, z in ((-0.25, 0.9), (4.0, 0.15), (6.0, 0.15), (10.25, zb + 0.9)):
            cx = side * (hw + MONO_BAL / 2)
            mb.box((cx - 0.33, y - 0.33, zf + 0.3), (cx + 0.33, y + 0.33, z + 0.25), ST, skip=("z-",))
            mb.box((cx - 0.38, y - 0.38, z + 0.25), (cx + 0.38, y + 0.38, z + 0.35), LIGHT)
        for _ in range(rng.randint(1, 2)):
            y0 = rng.uniform(0.5, 8.5)
            zr = interp(rail_line, y0) - 0.08
            face_quad(mb, side * (hw + MONO_BAL) + side * 0.012, *sorted((y0, y0 + 0.8)), zr - 0.75, zr - 0.25, REPAIR, side)
            stats["patches"] = stats.get("patches", 0) + 1
    # colision: rampa por los bordes de los peldanos + descanso + muros
    walk = [(-0.6, 0.0), (0.0, 0.0), (4.0, -0.75), (6.0, -0.75), (10.0, zb), (10.6, zb), (10.6, zf), (-0.6, zf)]
    along_prism(cm, walk, -hw, hw, COL)
    for side in (1, -1):
        along_prism(cm, [(y, z + 0.1) for y, z in rail_line] + [(10.5, zf), (-0.5, zf)],
                    *sorted((side * hw, side * (hw + MONO_BAL))), COL)
    stats.update({"width_m": MONO_W, "risers": len(MONO_RISERS), "riser_m": MONO_R, "tread_m": 1.0, "landing_m": 2.0,
                  "handrail_m": 0.9, "rise_m": 1.5})


# --------------------------------------------------------------------------- tramo de escalera generico
def stairs_flight(mb, cm, W, n_r, riser, tread, top_len, bot_len, rng, stats, cheek_h=0.5, cheeks=(1, -1),
                  floor=-0.4, top_ext=0.0, x_range=None, repair_tread=True):
    """Tramo recto que BAJA hacia +Y: rellano superior de top_len (y < 0, z = 0), n_r contrahuellas (la primera en
    y = 0), pie a z = -n_r * riser y prolongacion inferior de bot_len. x_range: (x0, x1) del paso (por defecto +-W/2).
    Zancas (muretes de 'cheek_h' sobre los bordes de los peldanos) en los lados de 'cheeks'."""
    x0, x1 = x_range or (-W / 2, W / 2)
    zb = -n_r * riser
    run = (n_r - 1) * tread
    prof = [(-top_len, 0.0)]
    for k in range(n_r):
        y = k * tread
        prof += [(y, -k * riser), (y, -(k + 1) * riser)]
    prof += [(run + bot_len, zb), (run + bot_len, zb + floor), (-top_len, zb + floor)]
    along_prism(mb, prof, x0, x1, ST)
    rep = rng.randrange(n_r) if repair_tread else -1
    for k in range(n_r):
        y = k * tread
        z = -k * riser
        mb.box((x0, y, z - 0.05), (x1, y + 0.03, z), REPAIR if k == rep else LIGHT, skip=("y-",))
    line = [(-top_len, cheek_h), (0.0, cheek_h), (run, zb + riser + cheek_h), (run + bot_len, zb + cheek_h)]
    t = 0.25
    for side in cheeks:
        xa, xb = (x1, x1 + t) if side > 0 else (x0 - t, x0)
        along_prism(mb, [(y, z - 0.07) for y, z in line] + [(run + bot_len, zb + floor), (-top_len, zb + floor)], xa, xb, ST)
        band(mb, line, xa - 0.03, xb + 0.03, -0.07, 0.0, LIGHT)
        along_prism(cm, [(y, z + 0.1) for y, z in line] + [(run + bot_len, zb + floor), (-top_len, zb + floor)], xa, xb, COL)
    walk = [(-top_len - 0.3, 0.0), (0.0, 0.0), (run, zb + riser * 0.5), (run + tread * 0.5, zb), (run + bot_len + 0.3, zb),
            (run + bot_len + 0.3, zb + floor), (-top_len - 0.3, zb + floor)]
    along_prism(cm, walk, x0, x1, COL)
    stats.update({"width_m": round(x1 - x0, 2), "risers": n_r, "riser_m": round(riser, 3), "tread_m": tread,
                  "rise_m": round(n_r * riser, 2), "run_m": round(run, 2), "slope_deg": round(math.degrees(math.atan2(riser, tread)), 1)})


_ = random
