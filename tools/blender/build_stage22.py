"""
CONCORDIA - Etapa 22 (E9): conexiones. concordia_v21.blend -> concordia_v22.blend (guardada antes)
+ export/godot/concordia_conexiones.glb + terrenos por distrito y marcadores reexportados (sin los provisionales)
+ docs/reports/stage22_conexiones.json

Coloca en sus marcadores (con rotacion: +Y = sentido de paso) las piezas de stage22_conexiones.py y sustituye a los
provisionales de las etapas 02 (escalinatas y escaleras laterales), 06 (escaleras de terraza) y 07 (puentes, arcos y
escalinatas de paso), que pasan a LEGACY_PLACEHOLDERS (fuera de la exportacion).
"""

import json
import math
import os
import random
import sys

import bpy  # noqa: I001
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import concordia_const as C  # noqa: E402
import bld_kit as K  # noqa: E402
import concordia_buildings as B  # noqa: E402
import stage13_portal as P13  # noqa: E402
import stage22_conexiones as X  # noqa: E402
import lod_utils as LU  # noqa: E402
import terrain_profile as T  # noqa: E402

REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
SRC = os.path.join(REPO, "blender", f"{C.BLEND_BASENAME}_v21.blend")
OUT = os.path.join(REPO, "blender", f"{C.BLEND_BASENAME}_v22.blend")
REPORT = os.path.join(REPO, "docs", "reports", "stage22_conexiones.json")
EXP = os.path.join(REPO, "export", "godot")
SEED = 2201
BUDGET = {"bridge": 1800, "arch": 1200}
LEGACY_PREFIX = ("TRN_Bridge_", "TRN_ArchBridge_", "TRN_Escalinata_Morada_", "TRN_StairPass_", "TRN_TerraceStairs_",
                 "TRN_LateralStairs_")
KIT_ORIGIN = Vector((3000.0, 1060.0, 0.0))


def tris_me(me):
    return sum(len(p.vertices) - 2 for p in me.polygons)


def save():
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)


def ensure_col(name, parent=None):
    c = bpy.data.collections.get(name)
    if c is None:
        c = bpy.data.collections.new(name)
        (parent or bpy.context.scene.collection).children.link(c)
    return c


# --------------------------------------------------------------------------- mallas compartidas y LOD
def make_mesh(name, fn, uv=True):
    """Construye (vis, col) con fn(mb, cm) -> mallas '<name>' y '<name>-colonly'. Devuelve (me, cme, info)."""
    for n in (name, f"{name}-colonly", f"{name}_LOD1", f"{name}_LOD2"):
        old = bpy.data.meshes.get(n)
        if old is not None:
            bpy.data.meshes.remove(old)
    mb, cm = K.MB(), K.MB()
    info = fn(mb, cm) or {}
    mb.finish()
    cm.finish()
    me = bpy.data.meshes.new(name)
    mb.bm.to_mesh(me)
    for n in mb.mats:
        me.materials.append(bpy.data.materials[n])
    cme = bpy.data.meshes.new(f"{name}-colonly")
    cm.bm.to_mesh(cme)
    for n in cm.mats:
        cme.materials.append(bpy.data.materials[n])
    mb.bm.free()
    cm.bm.free()
    if uv:
        tmp = bpy.data.objects.new("TMP_uv", me)
        bpy.context.scene.collection.objects.link(tmp)
        B.box_uv(tmp)
        bpy.data.objects.remove(tmp)
    return me, cme, info


_LODS = {}


def lod_meshes(me, col):
    """LOD1 (diezmado 0.5) y LOD2 (0.15 con un material plano = color medio del LOD0), una vez por malla."""
    if me.name in _LODS:
        return _LODS[me.name]
    tmp = bpy.data.objects.new(f"TMPLOD_{me.name}", me)
    col.objects.link(tmp)
    flat = LU.flat_material(f"MAT_LOD2_{me.name}", LU.average_color([tmp]))
    P13.lods(tmp, col)
    out = {}
    for tag in ("LOD1", "LOD2"):
        o = bpy.data.objects[f"{tmp.name}_{tag}"]
        m = o.data
        m.name = f"{me.name}_{tag}"
        if tag == "LOD2":
            m.materials.clear()
            m.materials.append(flat)
            for p in m.polygons:
                p.material_index = 0
        out[tag] = m
        bpy.data.objects.remove(o)
    bpy.data.objects.remove(tmp)
    _LODS[me.name] = out
    return out


def place(name, me, cme, parent, col, lods=True, local=Matrix.Identity(4)):
    o = bpy.data.objects.new(name, me)
    col.objects.link(o)
    o.parent = parent
    o.matrix_parent_inverse = Matrix.Identity(4)
    o.matrix_basis = local
    c = bpy.data.objects.new(f"{name}-colonly", cme)
    col.objects.link(c)
    c.parent = o
    c.hide_render = True
    c.display_type = "WIRE"
    if lods:
        for tag, m in lod_meshes(me, col).items():
            lo = bpy.data.objects.new(f"{name}_{tag}", m)
            col.objects.link(lo)
            lo.parent = parent
            lo.matrix_parent_inverse = Matrix.Identity(4)
            lo.matrix_basis = local
            lo.hide_render = True
            lo.hide_set(True)
    return o


def marker(name, mcol, loc, rot_z, **props):
    m = bpy.data.objects.get(name)
    if m is None:
        m = bpy.data.objects.new(name, None)
        mcol.objects.link(m)
    m.empty_display_type = "SINGLE_ARROW"
    m.empty_display_size = 1.5
    m.parent = None
    m.location = loc
    m.rotation_euler = (0.0, 0.0, rot_z)
    for k, v in props.items():
        m[k] = v
    m["axis"] = "+Y local = sentido de paso"
    return m


# --------------------------------------------------------------------------- provisionales
def retire_placeholders(st):
    legacy = ensure_col("LEGACY_PLACEHOLDERS")
    moved = []
    for o in list(bpy.data.objects):
        if o.name.startswith(LEGACY_PREFIX):
            for c in list(o.users_collection):
                c.objects.unlink(o)
            legacy.objects.link(o)
            o.hide_render = True
            o["replaced_by_stage22"] = True
            moved.append(o.name)
    def find(lc):
        if lc.name == "LEGACY_PLACEHOLDERS":
            return lc
        for ch in lc.children:
            r = find(ch)
            if r:
                return r
    lc = find(bpy.context.view_layer.layer_collection)
    if lc is not None:
        lc.exclude = True
    st["placeholders_retired"] = sorted(moved)
    return moved


# --------------------------------------------------------------------------- puentes
def bridges(col, mcol, st):
    import stage07_cauce as S7
    import cauce_route as CR
    import build_stage18 as B18
    canal = S7.Canal()
    g = B18.ground_fn()
    with open(os.path.join(REPO, "docs", "reports", "stage05_layout.json")) as fh:
        lay = json.load(fh)
    cross = S7.crossings(canal, lay["roads"])
    out = {}
    for k, cx in enumerate(cross, 1):
        m = bpy.data.objects[f"MARKER_Bridge_{k:02d}"]
        ax = Vector((cx["dir"][0], cx["dir"][1], 0)).normalized()
        p, t, n, e, w = canal.at(cx["s"])
        sin_a = max(0.35, abs(ax.x * t[1] - ax.y * t[0]))
        z_road = max(e + 0.1, T.height(*cx["pt"]))
        deck = z_road + 0.4
        W = max(5.0, min(6.0, cx["road_w"]))
        hs, span = CR.CORRIDOR_HALF / sin_a, (CR.WIDTH / 2) / sin_a
        ramp_a = ramp_b = 5.5
        note = None
        r_mark = math.hypot(*cx["pt"])
        if k == 1:
            # decision C (usuario, etapa 22): la rampa lejana termina en r 95, en el rellano de la escalinata NE
            ramp_b = round(T.ESC_U0 - (r_mark + hs), 3)
            note = f"rampa lejana acortada a {ramp_b} m: termina en r {T.ESC_U0:.0f} (rellano superior de la escalinata NE)"
        za = g(cx["pt"][0] - ax.x * (hs + ramp_a), cx["pt"][1] - ax.y * (hs + ramp_a)) - deck
        zb = g(cx["pt"][0] + ax.x * (hs + ramp_b), cx["pt"][1] + ax.y * (hs + ramp_b)) - deck
        name = f"BRIDGE_Stone_{int(W)}m_{k:02d}"
        rng = random.Random(f"{SEED}-{name}")
        stats = {}
        me, cme, _ = make_mesh(name, lambda mb, cm: X.bridge(mb, cm, W, hs, span, z_road - deck, e - deck, w - deck,
                                                             ramp_a, ramp_b, rng, stats, z_ends=(za, zb)))
        marker(m.name, mcol, (cx["pt"][0], cx["pt"][1], deck), math.atan2(ax.y, ax.x) - math.pi / 2,
               kit_piece=f"BRIDGE_Stone_{int(W)}m", deck_z=round(deck, 3), length_m=stats["length_m"], width_m=W)
        o = place(name, me, cme, m, col)
        t0 = tris_me(me)
        out[name] = {"marker": m.name, "road": cx["road"], "tris": t0, "budget": BUDGET["bridge"],
                     "ok": t0 <= BUDGET["bridge"], "deck_z": round(deck, 3), "street_z": round(z_road, 3),
                     "water_z": round(w, 3), "skew_sin": round(sin_a, 3), "note": note, **stats,
                     "collision": f"{o.name}-colonly", "lod_tris": [tris_me(x) for x in lod_meshes(me, col).values()]}
    st["bridges"] = out


# --------------------------------------------------------------------------- arcos
def wall_dist(o, d, z, sc, dg, maxd=6.0):
    best = None
    for off in (-0.9, 0.0, 0.9):
        side = Vector((-d.y, d.x, 0)) * off
        hit, loc, _n, _i, ob, _m = sc.ray_cast(dg, Vector((o.x, o.y, z)) + side, d, distance=maxd)
        if hit and ob.name.endswith(("_Body", "_Roof")):
            dd = (loc - (Vector((o.x, o.y, z)) + side)).length
            best = dd if best is None else min(best, dd)
    return best


def arches(col, mcol, rails, st):
    sc = bpy.context.scene
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    out = {}
    for i in range(6, 10):
        m = bpy.data.objects[f"MARKER_Bridge_{i:02d}"]
        if m.get("type") != "arco":
            continue
        o = m.matrix_world.translation.copy()
        z0 = float(T.height(o.x, o.y))
        S = float(m.get("street_w_m", 6.0))
        kit = f"ARCH_Street_{int(round(S))}m"
        ang = math.radians(float(m["angle"]))
        d = Vector((math.cos(ang), math.sin(ang), 0))
        piers = []
        dists = []
        for sg in (-1, 1):
            dd = wall_dist(o, d * sg, z0 + X.ARCH.DECK - 0.8, sc, dg)
            dists.append(round(dd, 2) if dd else None)
            piers.append(X.ARCH.PIER if dd is None else min(2.5, max(X.ARCH.PIER, dd - S / 2 + 0.3)))
        name = f"{kit}_{i:02d}"
        rng = random.Random(f"{SEED}-{name}")
        stats = {}

        def fn(mb, cm):
            mb.push(Matrix.Translation((0, 0, -X.ARCH.DECK)))
            cm.push(Matrix.Translation((0, 0, -X.ARCH.DECK)))
            yl, yr = X.arch_street(mb, cm, S, rng, stats, pier_l=piers[0], pier_r=piers[1])
            mb.pop()
            cm.pop()
            stats["walk"] = (yl, yr)
        me, cme, _ = make_mesh(name, fn)
        mk = marker(m.name, mcol, (o.x, o.y, z0 + X.ARCH.DECK), ang - math.pi / 2, kit_piece=kit,
                    deck_z=round(z0 + X.ARCH.DECK, 3), clear_height_m=X.ARCH.SPRING, street_z=round(z0, 3))
        a = place(name, me, cme, mk, col)
        # pretiles instanciables sobre el paso alto (escalados a la longitud)
        yl, yr = stats.pop("walk")
        L = yr - yl
        nr = int(math.ceil(L / 3.0 - 1e-6))
        sy = L / (3.0 * nr)
        placed = []
        for sx in (-1, 1):
            for k in range(nr):
                yc = yl + 3.0 * sy * (k + 0.5)
                rn = f"MARKER_Rail_{i:02d}_{'L' if sx < 0 else 'R'}_{k + 1:02d}"
                rm = marker(rn, mcol, (0, 0, 0), 0.0, kit_piece="RAIL_Stone_3m", host=a.name, scale_y=round(sy, 3))
                rm.parent = mk
                rm.matrix_parent_inverse = Matrix.Identity(4)
                rm.location = (sx * (X.ARCH.DEPTH / 2 - 0.15), yc, 0.0)
                me_r, cme_r = rails[(k + i) % 3 == 0]
                ro = place(f"RAIL_Stone_3m_{i:02d}_{'L' if sx < 0 else 'R'}_{k + 1:02d}", me_r, cme_r, rm, col,
                           local=Matrix.Diagonal((1.0, sy, 1.0, 1.0)))
                placed.append(ro.name)
        import build_stage18 as B18
        t0 = tris_me(me)
        out[name] = {"marker": m.name, "kit_piece": kit, "street": m.get("street"), "between": m.get("between"),
                     "tris": t0, "budget": BUDGET["arch"], "ok": t0 <= BUDGET["arch"], "street_z": round(z0, 3),
                     "wall_distances_m": dists, "rails": {"count": len(placed), "scale_y": round(sy, 3),
                                                          "tris_each": tris_me(rails[False][0])},
                     **stats, "collision": f"{a.name}-colonly", "iso_blocks": B18.iso_check(mk, [a]),
                     "lod_tris": [tris_me(x) for x in lod_meshes(me, col).values()]}
    st["arches"] = out


# --------------------------------------------------------------------------- escalinatas y escaleras
def monumental(col, mcol, st):
    stats = {}
    rng = random.Random(f"{SEED}-mono")
    me, cme, _ = make_mesh("STAIRS_Monumental", lambda mb, cm: X.stairs_monumental(mb, cm, rng, stats))
    out = []
    for key, phi in T.DIAGONAL_ANGLE.items():
        a = math.radians(phi)
        e = Vector((math.cos(a), math.sin(a), 0))
        m = marker(f"MARKER_Stairs_Monumental_{key}", mcol, tuple(e * T.ESC_U0 + Vector((0, 0, C.DATUM))), a - math.pi / 2,
                   kit_piece="STAIRS_Monumental", morada=key, r_from=T.ESC_U0, r_to=T.ESC_U1)
        out.append(place(f"STAIRS_Monumental_{key}", me, cme, m, col).name)
    st["stairs_monumental"] = {"instances": out, "tris": tris_me(me), **stats}


def stair_pass(col, mcol, st):
    import stage07_cauce as S7
    stats = {}
    rng = random.Random(f"{SEED}-pass")
    run = 9 * S7.TREAD
    u_s0 = (T.ESC_U0 + T.ESC_U1) / 2 - run / 2
    top_len = u_s0 - (T.ESC_U0 - 0.6)
    bot_len = (T.ESC_U1 + 0.4) - (u_s0 + run)
    me, cme, _ = make_mesh("STAIRS_Pass_3m", lambda mb, cm: X.stairs_flight(
        mb, cm, S7.ESC_W, 10, S7.RISER, S7.TREAD, top_len, bot_len, rng, stats, cheek_h=0.9, floor=-0.6,
        x_range=(-S7.ESC_W / 2, S7.ESC_W / 2)))
    out = []
    for k, (key, ang) in enumerate(S7.esc_sites(None), 1):
        a = math.radians(ang)
        e = Vector((math.cos(a), math.sin(a), 0))
        m = marker(f"MARKER_Escalinata_{k:02d}", mcol, tuple(e * u_s0 + Vector((0, 0, C.DATUM))), a - math.pi / 2,
                   kit_piece="STAIRS_Pass_3m", morada=key)
        out.append(place(f"STAIRS_Pass_3m_{k:02d}", me, cme, m, col).name)
    st["stairs_pass"] = {"instances": out, "tris": tris_me(me), "top_len_m": round(top_len, 3),
                         "bottom_len_m": round(bot_len, 3), **stats}


def terrace(col, mcol, st):
    import stage06_moradas as SM
    J = T.terrace_jumps()
    meshes = {}
    for tag, W in (("A", SM.SERVICE_STAIR_W), ("B", SM.SERVICE_STAIR_W), ("Axis", SM.AXIS_STREET_W)):
        stats = {}
        rng = random.Random(f"{SEED}-terr-{tag}")
        nm = f"STAIRS_Terrace_{W:g}m" + ("" if tag == "Axis" else f"_{tag}")
        me, cme, _ = make_mesh(nm, lambda mb, cm, W=W, rng=rng, stats=stats: X.stairs_flight(
            mb, cm, W, SM.STAIR_RISERS, C.TERRACE_RISE / SM.STAIR_RISERS, SM.STAIR_TREAD, T.STEP_RUN + 0.3, 0.3, rng,
            stats, cheek_h=0.45, floor=-0.25, x_range=(-W / 2 + 0.25, W / 2 - 0.25)))
        meshes[tag] = (me, cme, stats)
    out = {}
    n = 0
    for key, phi in T.DIAGONAL_ANGLE.items():
        items = []
        for k in range(1, C.TERRACE_COUNT):
            R = J[k - 1]
            for typ, a_deg in [("servicio", a) for a in SM.stair_slots(R, phi)] + [("eje", phi)]:
                n += 1
                a = math.radians(a_deg)
                e = Vector((math.cos(a), math.sin(a), 0))
                foot = R - T.STEP_RUN / 2
                z_top = T.terrace_level(k) + C.TERRACE_RISE
                tag = "Axis" if typ == "eje" else ("A" if n % 2 else "B")
                me, cme, _ = meshes[tag]
                idx = len(items) + 1
                m = marker(f"MARKER_Stairs_Terrace_{key}_{idx:02d}", mcol, tuple(e * foot + Vector((0, 0, z_top))),
                           a + math.pi / 2, kit_piece=me.name, morada=key, terrace_jump=k, type=typ)
                items.append(place(f"{me.name}_{key}_{idx:02d}", me, cme, m, col).name)
        out[key] = items
    st["stairs_terrace"] = {"per_morada": {k: len(v) for k, v in out.items()},
                            "meshes": {meshes[t][0].name: {"tris": tris_me(meshes[t][0]), **meshes[t][2]} for t in meshes}}


def lateral(col, mcol, st):
    """Escaleras de los muros laterales (Prompt 2): mismas posiciones y alturas que stage02_structures."""
    import stage02_structures as ST2
    W = C.LATERAL_STAIR_WIDTH
    cache, out = {}, []
    idx = 0
    for key, phi in T.DIAGONAL_ANGLE.items():
        for k2, side, tb, e, n_card in T.lateral_edges():
            if k2 != key:
                continue
            a_s = C.TERRACE_START_R + ST2.STAIR_FIRST_OFFSET
            while a_s + W / 2 <= ST2.LAT_END:
                dz, z_hi, _zl, hi_side = ST2.edge_levels(a_s, tb)
                if abs(dz) < C.LATERAL_MIN_WALL:
                    a_s += C.LATERAL_STAIR_SPACING
                    continue
                n_low = n_card if hi_side == "diag" else (-n_card[0], -n_card[1])
                a_top = a_s - W / 2

                def ground(a, t):
                    p = ST2.P(a, e, t, n_low)
                    return T.height(p.x, p.y)
                n = max(2, round(abs(dz) / ST2.STAIR_RISER_TARGET))
                for _ in range(6):
                    a_bot = a_top - (n - 1) * ST2.STAIR_TREAD
                    d_mid = T.face_run(ST2.edge_levels(a_bot, tb)[0])
                    z_bot = ground(a_bot - 0.05, d_mid + W / 2)
                    n = max(2, round((z_hi - z_bot) / ST2.STAIR_RISER_TARGET))
                a_bot = a_top - (n - 1) * ST2.STAIR_TREAD
                riser = (z_hi - z_bot) / n
                d_max = max(T.face_run(ST2.edge_levels(a, tb)[0]) for a in ST2.frange(a_bot, a_s + W / 2, 0.25))
                t_out = d_max + W
                z_floor = min(ground(a, t) for a in ST2.frange(a_bot - 0.3, a_s + W / 2, 0.5)
                              for t in (0.0, d_max, t_out)) - ST2.EMBED
                idx += 1
                dvec = Vector((-e[0], -e[1], 0))
                rot = math.atan2(dvec.y, dvec.x) - math.pi / 2
                xax = Vector((math.cos(rot), math.sin(rot), 0))
                sgn = 1 if xax.dot(Vector((n_low[0], n_low[1], 0))) > 0 else -1
                ck = (n, round(riser, 3), round(t_out, 2), round(z_floor - z_bot, 1), sgn)
                if ck not in cache:
                    stats = {}
                    rng = random.Random(f"{SEED}-lat-{len(cache)}")
                    nm = f"STAIRS_Terrace_Lateral_{len(cache) + 1:02d}"
                    xr = (0.0, t_out) if sgn > 0 else (-t_out, 0.0)
                    me, cme, _ = make_mesh(nm, lambda mb, cm: X.stairs_flight(
                        mb, cm, W, n, riser, ST2.STAIR_TREAD, W, 0.3, rng, stats, cheek_h=0.5,
                        cheeks=(sgn,), floor=min(-0.25, z_floor - z_bot), x_range=xr))
                    cache[ck] = (me, cme, stats)
                me, cme, stats = cache[ck]
                p = ST2.P(a_top, e, 0.0, n_low)
                m = marker(f"MARKER_Stairs_Lateral_{key}_{idx:02d}", mcol, (p.x, p.y, z_hi), rot,
                           kit_piece="STAIRS_Terrace", morada=key, edge=f"{key}{side:+d}", risers=n,
                           riser_m=round(riser, 3), width_m=W)
                out.append(place(f"STAIRS_Terrace_Lateral_{key}_{idx:02d}", me, cme, m, col).name)
                a_s += C.LATERAL_STAIR_SPACING
    st["stairs_lateral"] = {"instances": len(out), "meshes": {v[0].name: {"tris": tris_me(v[0]), **v[2]}
                                                              for v in cache.values()}}


# --------------------------------------------------------------------------- biblioteca (fila del kit)
def library(col, rails, st):
    root = bpy.data.objects.get("KIT_Conexiones") or bpy.data.objects.new("KIT_Conexiones", None)
    if root.name not in col.objects:
        col.objects.link(root)
    root.location = KIT_ORIGIN
    lib = {}
    x = 0.0
    for W in (5.0, 6.0):
        nm = f"BRIDGE_Stone_{int(W)}m"
        stats = {}
        rng = random.Random(f"{SEED}-{nm}")
        me, cme, _ = make_mesh(nm, lambda mb, cm: X.bridge(mb, cm, W, 3.0, 2.0, -0.4, -0.5, -0.9, 5.5, 5.5, rng, stats))
        place(nm, me, cme, root, col, local=Matrix.Translation((x, 0, 1.6)))
        lib[nm] = {"tris": tris_me(me), **stats}
        x += 12.0
    for S in (4.0, 5.0, 6.0):
        nm = f"ARCH_Street_{int(S)}m"
        stats = {}
        rng = random.Random(f"{SEED}-{nm}")
        def fn(mb, cm, S=S, rng=rng, stats=stats):
            mb.push(Matrix.Translation((0, 0, -X.ARCH.DECK)))
            cm.push(Matrix.Translation((0, 0, -X.ARCH.DECK)))
            X.arch_street(mb, cm, S, rng, stats)
            mb.pop()
            cm.pop()
        me, cme, _ = make_mesh(nm, fn)
        place(nm, me, cme, root, col, local=Matrix.Translation((x, 0, X.ARCH.DECK)))
        lib[nm] = {"tris": tris_me(me), **stats}
        x += S + 6.0
    for patch in (False, True):
        me, cme = rails[patch]
        place(me.name, me, cme, root, col, local=Matrix.Translation((x, 0, 0)))
        lib[me.name] = {"tris": tris_me(me)}
        x += 1.5
    me, cme = rails["low"]
    place(me.name, me, cme, root, col, local=Matrix.Translation((x, 0, 0)))
    lib[me.name] = {"tris": tris_me(me)}
    st["library"] = lib
    return root


def main():
    st = {"budgets": BUDGET}
    bpy.ops.wm.open_mainfile(filepath=SRC)
    save()
    st["saved_before"] = os.path.relpath(OUT, REPO)
    B.ensure_materials()
    col = ensure_col("BLD_CONEXIONES")
    mcol = ensure_col("MARKERS_Conexiones")
    for o in list(col.all_objects):
        bpy.data.objects.remove(o)
    retire_placeholders(st)
    rails = {}
    for key, nm, h, patch in ((False, "RAIL_Stone_3m", 0.9, False), (True, "RAIL_Stone_3m_Patch", 0.9, True),
                              ("low", "RAIL_Stone_3m_Low", 0.5, False)):
        me, cme, _ = make_mesh(nm, lambda mb, cm, h=h, patch=patch: X.rail(mb, cm, 3.0, h, patch))
        rails[key] = (me, cme)
    bridges(col, mcol, st)
    arches(col, mcol, rails, st)
    monumental(col, mcol, st)
    stair_pass(col, mcol, st)
    terrace(col, mcol, st)
    lateral(col, mcol, st)
    lib = library(bpy.data.collections["BLD_KIT"], rails, st)
    for o in bpy.data.objects:
        if o.name.endswith(("_LOD1", "_LOD2")):
            o.hide_render = True
            o.hide_set(True)
    bpy.context.view_layer.update()
    import build_stage17 as B17
    with open(os.path.join(REPO, "docs", "reports", "stage15_faro.json")) as fh:
        tgt = Vector(json.load(fh)["visibility"]["target"])
    B17.faro_visibility(st, tgt)
    import stage11_godot as G
    objs = [o for o in col.all_objects] + [o for o in mcol.objects]
    objs += [lib] + list(lib.children_recursive)
    path = os.path.join(EXP, "concordia_conexiones.glb")
    size = G.export_glb(list(dict.fromkeys(objs)), path)
    st["export"] = {"file": os.path.relpath(path, REPO), "mb": round(size / 2 ** 20, 2), **G.glb_info(path)}
    # terrenos por distrito y marcadores, sin los provisionales retirados (misma agrupacion que build_stage11)
    def col_objs(prefix):
        return [o for c in bpy.data.collections if c.name.startswith(prefix) for o in c.objects]
    city = col_objs("GODOT_CITY_")
    sobjs = [o for cn in G.STRUCT_COLS for o in bpy.data.collections[cn].objects
             if o.type == "MESH" and not o.name.endswith("-colonly")]
    scol = col_objs("GODOT_STRUCT_COL")
    nav = col_objs("GODOT_NAVMESH")
    re = {}
    for d in G.DISTRICTS:
        objs = [o for o in city + sobjs + scol + nav if o.get("district") == d]
        p = os.path.join(EXP, f"concordia_terrain_{d}.glb")
        re[os.path.basename(p)] = {"mb": round(G.export_glb(objs, p) / 2 ** 20, 2), **G.glb_info(p)}
    p = os.path.join(EXP, "concordia_markers.glb")
    mk = [o for o in bpy.data.objects if o.type == "EMPTY" and o.name.startswith("MARKER_")]
    re["concordia_markers.glb"] = {"mb": round(G.export_glb(mk, p) / 2 ** 20, 2), "markers": len(mk), **G.glb_info(p)}
    st["reexported"] = re
    for o in bpy.data.objects:
        if o.name.endswith(("_LOD1", "_LOD2")):
            o.hide_set(True)
    save()
    with open(REPORT, "w") as fh:
        json.dump(st, fh, indent=1, ensure_ascii=False, default=str)
    print("saved:", OUT)
    for k, v in st["bridges"].items():
        print(k, v["tris"], v["ok"], v["length_m"], v["ramps_m"], v["ramp_deg"], v["arch_span_m"], v["arch_rise_m"],
              v["clear_over_water_m"], v["note"])
    for k, v in st["arches"].items():
        print(k, v["tris"], v["ok"], v["piers_m"], v["wall_distances_m"], v["rails"], v["iso_blocks"])
    for k in ("stairs_monumental", "stairs_pass"):
        print(k, {a: b for a, b in st[k].items() if a != "instances"}, len(st[k]["instances"]))
    print("terrace", json.dumps(st["stairs_terrace"])[:600])
    print("lateral", json.dumps(st["stairs_lateral"])[:900])
    print("library", {k: v["tris"] for k, v in st["library"].items()})
    print("retired", len(st["placeholders_retired"]))
    print(json.dumps({k: (v["axis_pct"], v.get("best_lane_pct")) for k, v in st["faro_visibility"].items()}, ensure_ascii=False))
    print(json.dumps(st["export"], default=str)[:300])
    print(json.dumps({k: (v["mb"], v.get("tris")) for k, v in re.items()}))


if __name__ == "__main__":
    main()
