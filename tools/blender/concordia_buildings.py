"""
CONCORDIA - Building assembler (etapa 12).

build_building(nombre, footprint, pisos, tipo_techo, estilo, seed, ...) apila los modulos de bld_kit y crea:
  <Nombre>              Empty raiz (origen = centro de la base, a la cota del terreno; +Y = puerta)
  <Nombre>_Body         muros, zocalo, cornisas, esquinas, balcones, hastiales (un objeto, caras por material)
  <Nombre>_Roof         cubierta + chimeneas + buhardillas (aparte: Godot lo oculta al entrar)
  <Nombre>_Props        Empty con instancias (malla enlazada) de letreros, farolillos, toldos, cajas...
  <Nombre>_Body_LOD1/2, <Nombre>_Roof_LOD1/2
  MARKER_<Nombre>_Door  en la puerta, +Y hacia fuera          (si interior=True)
  <Nombre>_InteriorVolume  caja sin render del tamano interior (si interior=True)
Reglas: footprint y door_direction del MARKER_Bld_<Nombre> (+-0.2 m); remiendos por semilla (2-4 parches de
piedra, 1-3 vigas de reemplazo, tejas de otro tono); altura limitada por la camara isometrica (lado camara: 2
plantas salvo hitos; resto: 3).
"""

import hashlib
import math
import os
import random
import sys

import bpy
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bld_kit as K  # noqa: E402

STYLES = ("timber", "stone", "guild")
ROOFS = ("gable", "gable_front", "hip", "conical", "flat", "lean_to")
ISO_AWAY_DOT = 0.35          # (informativo) puerta mirando "hacia dentro" de la vista
# Regla de alturas (etapa 17): manda la prueba de visibilidad desde CAM_Iso, no el lado de la calle.
#   - hasta 3 plantas (<= 10.5 m); la torre de Alquimia hasta 4
#   - si el edificio tapa desde la camara la puerta de otro edificio o un carril de NPC, se baja planta a planta hasta que
#     deje de taparla, como minimo 2 plantas (7 m)
#   - los hitos (Portal, Faro, Obelisco, Santuario, Salon de las Hazanas) quedan fuera de la regla
MAX_FLOORS, MAX_FLOORS_ALCHEMY, MIN_FLOORS_OCCLUDING = 3, 4, 2
MAX_HEIGHT_M, MIN_HEIGHT_M = 10.5, 7.0
LANDMARKS = ("PORTAL", "FARO", "OBELISK", "SANTUARIO", "SALON_HAZANAS")
NPC_LANE_PREFIX = "NPC_Lane_"


def rng_for(name, seed):
    h = hashlib.sha1(f"{name}:{seed}".encode()).hexdigest()
    return int(h[:12], 16)


def stable(*parts):
    """Entero estable entre ejecuciones (hash() de Python cambia con PYTHONHASHSEED)."""
    return int(hashlib.sha1(":".join(map(str, parts)).encode()).hexdigest()[:8], 16)


# ---------------------------------------------------------------------------
# materiales extra (sin texturas nuevas)
# ---------------------------------------------------------------------------
def ensure_materials():
    """MAT_Roof_Tile_Ocher_B: el mismo albedo con otro tono (Mix Multiply = baseColorFactor en glTF).
    MAT_Window_Warm: luz calida natural de ventana, emision 1.0 (no magica)."""
    import stage10_apply as AP
    out = {}
    if "MAT_Roof_Tile_Ocher_B" not in bpy.data.materials:
        src = bpy.data.materials["MAT_Roof_Tile_Ocher"]
        m = src.copy()
        m.name = "MAT_Roof_Tile_Ocher_B"
        N, L = m.node_tree.nodes, m.node_tree.links
        alb = N["Albedo"]
        b = next(n for n in N if n.type == "BSDF_PRINCIPLED")
        mix = N.new("ShaderNodeMix")
        mix.data_type = "RGBA"
        mix.blend_type = "MULTIPLY"
        mix.inputs["Factor"].default_value = 1.0
        L.new(alb.outputs["Color"], mix.inputs["A"])
        mix.inputs["B"].default_value = (0.80, 0.74, 0.68, 1.0)     # teja mas vieja: algo mas oscura y fria
        L.new(mix.outputs["Result"], b.inputs["Base Color"])
        m["base_color_factor"] = "0.80, 0.74, 0.68 (teja de reparacion, otro tono)"
        out["MAT_Roof_Tile_Ocher_B"] = "creado"
    if "MAT_Window_Warm" not in bpy.data.materials:
        m = bpy.data.materials.new("MAT_Window_Warm")
        m.use_nodes = True
        b = m.node_tree.nodes["Principled BSDF"]
        b.inputs["Base Color"].default_value = (0.035, 0.03, 0.025, 1)
        b.inputs["Roughness"].default_value = 0.35
        b.inputs["Emission Color"].default_value = (0.4173, 0.2803, 0.1682, 1)   # sRGB #AD9072 (sat 0.34): interior calido
        b.inputs["Emission Strength"].default_value = 1.0
        m["note"] = "luz natural calida de ventana, emision 1.0; NO es color magico"
        out["MAT_Window_Warm"] = "creado"
    for n in K.M_CLOTH:                                              # toldos: dos caras visibles
        if n in bpy.data.materials:
            bpy.data.materials[n].use_backface_culling = False
    _ = AP
    return out


# ---------------------------------------------------------------------------
# geometria
# ---------------------------------------------------------------------------
def iso_view_dir():
    cam = bpy.data.objects.get("CAM_Iso")
    if cam is None:
        return Vector((-0.7071, 0.7071, 0.0))
    d = cam.matrix_world.to_3x3() @ Vector((0, 0, -1))
    d.z = 0
    return d.normalized()


def iso_max_floors(rot_z, landmark=False, use="house"):
    """Tope de plantas antes de la prueba de visibilidad: 3 (torre de Alquimia 4); hitos sin tope. Devuelve
    (tope, puerta mirando hacia dentro de la vista) - lo segundo solo es informativo."""
    door = Vector((-math.sin(rot_z), math.cos(rot_z), 0))
    away = door.dot(iso_view_dir()) > ISO_AWAY_DOT
    if landmark:
        return 99, away
    return (MAX_FLOORS_ALCHEMY if use == "alchemy_tower" else MAX_FLOORS), away


def iso_cam_back():
    """Direccion 3D desde la escena hacia CAM_Iso."""
    cam = bpy.data.objects.get("CAM_Iso")
    d = cam.matrix_world.to_3x3() @ Vector((0, 0, -1)) if cam else Vector((-0.5774, 0.5774, -0.5774))
    return -d.normalized()


def iso_targets(exclude_root=None, lane_step=2.0, h=1.0):
    """Puntos que ningun edificio debe tapar desde CAM_Iso: puertas (MARKER_*_Door y el frente de cada
    MARKER_Bld_* aun sin construir) y carriles de NPC (curvas NPC_Lane_*, una muestra cada lane_step m), a h m."""
    pts = []
    own = set()
    if exclude_root is not None:
        own = {o.name for o in exclude_root.children_recursive} | {exclude_root.name}
        own.add(exclude_root.get("marker", ""))
    for o in bpy.data.objects:
        if o.name in own:
            continue
        if o.type == "EMPTY" and o.name.startswith("MARKER_") and o.name.endswith("_Door"):
            pts.append((o.name, o.matrix_world.translation + Vector((0, 0, h))))
        elif o.type == "EMPTY" and o.name.startswith("MARKER_Bld_") and "footprint_d" in o:
            if any(c.name.startswith("MARKER_") and c.name.endswith("_Door") for c in o.children_recursive):
                continue
            mw = o.matrix_world
            p = mw @ Vector((0, float(o["footprint_d"]) / 2 + 0.5, 0))
            pts.append((o.name + ":door", p + Vector((0, 0, h))))
        elif o.type == "CURVE" and o.name.startswith(NPC_LANE_PREFIX):
            for sp in o.data.splines:
                cs = [o.matrix_world @ Vector(p.co[:3]) for p in sp.points] or \
                     [o.matrix_world @ p.co for p in sp.bezier_points]
                for a, b in zip(cs[:-1], cs[1:]):
                    n = max(1, int((b - a).length / lane_step))
                    for k in range(n):
                        pts.append((o.name, a.lerp(b, k / n) + Vector((0, 0, h))))
    return pts


def iso_blocked(objs, targets, max_dist=60.0):
    """Puntos de targets que las mallas objs tapan desde CAM_Iso (rayo desde el punto hacia la camara)."""
    import bmesh
    from mathutils.bvhtree import BVHTree
    bm = bmesh.new()
    for o in objs:
        if o.type != "MESH":
            continue
        t = bmesh.new()
        t.from_mesh(o.data)
        t.transform(o.matrix_world)
        me = bpy.data.meshes.new("TMP_iso")
        t.to_mesh(me)
        t.free()
        bm.from_mesh(me)
        bpy.data.meshes.remove(me)
    if not bm.faces:
        bm.free()
        return []
    bvh = BVHTree.FromBMesh(bm)
    bm.free()
    back = iso_cam_back()
    return [(n, p) for n, p in targets if bvh.ray_cast(p, back, max_dist)[0] is not None]


def fit_iso_height(nombre, pisos, targets=None, **kw):
    """Construye el edificio y aplica la regla de alturas: si tapa una puerta o un carril de NPC desde CAM_Iso, lo
    reconstruye con una planta menos hasta que no tape nada o llegue a 2 plantas. Los hitos no se prueban."""
    history = []
    p = pisos
    while True:
        root, objs, rep = build_building(nombre, pisos=p, **kw)
        if kw.get("landmark"):
            rep["iso_rule"] = "hito: fuera de la regla"
            return root, objs, rep
        bpy.context.view_layer.update()                      # matrices del mundo de las piezas recien creadas
        tg = targets if targets is not None else iso_targets(exclude_root=root)
        lod0 = [o for k, o in objs.items() if k in ("Body", "Roof")]
        blocked = iso_blocked(lod0, tg)
        history.append({"floors": rep["floors"], "blocked": sorted({n for n, _ in blocked})})
        if not blocked or rep["floors"] <= MIN_FLOORS_OCCLUDING:
            rep["iso_rule"] = {"history": history, "final_floors": rep["floors"], "still_blocking": bool(blocked)}
            return root, objs, rep
        for o in list(root.children_recursive) + [root]:
            bpy.data.objects.remove(o)
        p = rep["floors"] - 1


def facades(W, D, t):
    """(lado, longitud, centro, rotZ) con la cara exterior del modulo en el borde del footprint."""
    return [("front", W, (0.0, D / 2 - t / 2), 0.0), ("back", W, (0.0, -D / 2 + t / 2), math.pi),
            ("right", D - 2 * t, (W / 2 - t / 2, 0.0), -math.pi / 2), ("left", D - 2 * t, (-W / 2 + t / 2, 0.0), math.pi / 2)]


def plan_modules(W, D, floors, style, rng, door_index=None, use="house"):
    """Decide tipo y variante de cada modulo (mismo plan para LOD0/1/2)."""
    plan = []
    for side, length, c, rz in facades(W, D, K.WALL_T):
        n = max(1, int(round(length / K.MODULE_W)))
        for f in range(floors):
            for i in range(n):
                if side == "front" and f == 0:
                    di = n // 2 if door_index is None else max(0, min(n - 1, door_index))
                    if i == di:
                        kind = "Door"
                    elif use == "shop":
                        kind = rng.choice(("Arch", "Window", "Shutter", "Arch"))
                    elif style == "stone":
                        kind = rng.choice(("Barred", "Window", "Solid"))
                    else:
                        kind = rng.choice(("Window", "Shutter", "Solid"))
                elif side == "front":
                    kind = rng.choice(("Window", "Shutter", "Window", "Solid") if style != "stone" else
                                      ("Window", "Barred", "Solid"))
                else:
                    kind = rng.choice(("Solid", "Solid", "Window", "Shutter", "Barred") if f > 0 else
                                      ("Solid", "Solid", "Barred", "Window"))
                plan.append({"side": side, "floor": f, "i": i, "n": n, "kind": kind, "variant": "Clean"})
    idx = [k for k, m in enumerate(plan) if m["kind"] != "Door"]
    rng.shuffle(idx)
    ns = rng.randint(2, 4)
    nt = rng.randint(1, 3)
    for k in idx[:ns]:
        plan[k]["variant"] = "StonePatch"
    for k in idx[ns:ns + nt]:
        plan[k]["variant"] = "TimberPatch"
    return plan


def build_meshes(W, D, floors, roof_type, style, seed_int, plan, detail, use="house", balcony_ok=True):
    rng = random.Random(seed_int * 7 + 1)            # mismas decisiones en todos los LODs
    body, roof = K.MB(), K.MB()
    t = K.WALL_T
    door_local = None
    for side, length, (cx, cy), rz in facades(W, D, t):
        mods = [m for m in plan if m["side"] == side]
        for m in mods:
            n = m["n"]
            mw = length / n
            x = -length / 2 + mw * (m["i"] + 0.5)
            z0 = m["floor"] * K.FLOOR_H
            mrng = random.Random(stable(seed_int, side, m["floor"], m["i"]))
            body.push(Matrix.Translation((cx, cy, z0)) @ Matrix.Rotation(rz, 4, "Z") @ Matrix.Translation((x, 0, 0)))
            timber_floor = style == "timber" and m["floor"] >= 1 or style == "guild" and m["floor"] == floors - 1 >= 1
            K.wall(body, m["kind"], w=mw, variant=m["variant"], rng=mrng, ground=m["floor"] == 0, detail=detail)
            if timber_floor and detail < 2:
                K.timber_overlay(body, mw, K.FLOOR_H, t / 2, K.opening_of(m["kind"], mw), mrng, detail)
            body.pop()
            if m["kind"] == "Door" and side == "front":
                door_local = (x, D / 2, 0.0)
    top = floors * K.FLOOR_H
    # cornisas de piso
    if detail < 2:
        for f in range(1, floors + 1):
            for side, length, (cx, cy), rz in facades(W, D, t):
                L = W + 0.44 if side in ("front", "back") else D
                body.push(Matrix.Translation((cx, cy, f * K.FLOOR_H)) @ Matrix.Rotation(rz, 4, "Z"))
                K.floor_edge(body, L, t / 2, "timber" if style == "timber" and f > 1 else "stone")
                body.pop()
    # esquinas
    for sx in ((-1, 1) if detail < 2 else ()):
        for sy in (-1, 1):
            body.push(Matrix.Translation((sx * (W / 2 - 0.1), sy * (D / 2 - 0.1), 0)))
            K.corner_post(body, top, "timber" if style == "timber" else "stone", random.Random(seed_int + sx * 3 + sy))
            body.pop()
    # balcon y contrafuertes
    if detail < 2 and balcony_ok and floors >= 2 and style in ("timber", "guild") and rng.random() < 0.65:
        cands = [m for m in plan if m["side"] == "front" and m["floor"] == 1 and m["kind"] in ("Window", "Shutter")]
        if cands:
            m = rng.choice(cands)
            mw = W / m["n"]
            x = -W / 2 + mw * (m["i"] + 0.5)
            body.push(Matrix.Translation((x, D / 2, K.FLOOR_H)))
            K.balcony(body, min(mw, 3.0) - 0.2, 1.5 if detail == 0 else 1.2, "wood" if style == "timber" else "stone")
            body.pop()
    if style == "stone" and W >= 10 and detail < 2:
        for sx in (-1, 1):
            body.push(Matrix.Translation((sx * W / 2, 0.0, 0)) @ Matrix.Rotation(-sx * math.pi / 2, 4, "Z"))
            K.buttress(body, top - 0.6)
            body.pop()
    # cubierta y hastiales
    body.push(Matrix.Translation((0, 0, top)))
    roof.push(Matrix.Translation((0, 0, top)))
    rrng = random.Random(seed_int * 13 + 5)
    reps = rrng.randint(2, 4)
    ridge = 0.0
    if roof_type == "gable":
        ridge = K.roof_gable(roof, W, D, rng=rrng, detail=detail, repairs=reps)
        K.gable_walls(body, W, D, ridge)
    elif roof_type == "gable_front":
        roof.push(Matrix.Rotation(math.pi / 2, 4, "Z"))
        ridge = K.roof_gable(roof, D, W, rng=rrng, detail=detail, repairs=reps)
        roof.pop()
        body.push(Matrix.Rotation(math.pi / 2, 4, "Z"))
        if style == "guild":
            stepped_gables(body, D, W, ridge)
        else:
            K.gable_walls(body, D, W, ridge)
        body.pop()
    elif roof_type == "hip":
        ridge = K.roof_hip(roof, W, D, rng=rrng, detail=detail)
    elif roof_type == "conical":
        ridge = K.roof_conical(roof, min(W, D) / 2, rng=rrng, detail=detail)
    elif roof_type == "flat":
        ridge = K.roof_flat_parapet(roof, W, D)
    elif roof_type == "lean_to":
        ridge = K.roof_lean_to(roof, W, D, rng=rrng, detail=detail)
        for sx in (-1, 1):
            body.push(Matrix.Translation((sx * (W / 2 - t / 2), 0, 0)) @ Matrix.Rotation(math.pi / 2, 4, "Z"))
            body.prism([(-D / 2, 0), (D / 2, 0), (-D / 2, ridge)], -t / 2, t / 2, K.M_STONE)
            body.pop()
    # chimeneas y buhardillas (parte del techo)
    if roof_type in ("gable", "gable_front", "hip", "lean_to") and detail < 2:
        for _ in range(rrng.randint(1, 2)):
            if roof_type == "gable_front":
                y, x = rrng.uniform(-D / 2 + 1.2, D / 2 - 1.2), rrng.uniform(-0.6, 0.6) + rrng.choice((-1, 1)) * W / 5
                zr = ridge * (1 - abs(x) / (W / 2))
            else:
                x, y = rrng.uniform(-W / 2 + 1.2, W / 2 - 1.2), rrng.choice((-1, 1)) * D / 5
                zr = ridge * (1 - abs(y) / (D / 2)) if roof_type != "lean_to" else ridge * (0.5 - y / D)
            roof.push(Matrix.Translation((x, y, zr - 0.6)))
            K.chimney(roof, h=max(1.6, ridge - zr + 1.3), capped=rrng.random() < 0.6, rng=rrng)
            roof.pop()
        if roof_type == "gable" and D >= 8 and detail == 0:
            for _ in range(rrng.randint(1, 2)):
                x = rrng.uniform(-W / 2 + 1.5, W / 2 - 1.5)
                yf = D / 4
                zf = ridge * (1 - yf / (D / 2))
                roof.push(Matrix.Translation((x, yf - 0.9, zf - 0.45)))
                K.dormer(roof, rng=rrng)
                roof.pop()
    body.pop()
    roof.pop()
    body.finish()
    roof.finish()
    return body, roof, door_local, top, ridge


def stepped_gables(mb, W, D, rise, t=K.WALL_T, steps=5):
    """Hastial escalonado de gremio (Grand-Place): escalones a cada lado + remate."""
    for sx in (-1, 1):
        x = sx * (W / 2 - t / 2)
        pts = [(-D / 2, 0), (D / 2, 0)]
        for k in range(steps):
            y_out = D / 2 * (1 - k / steps)
            y_in = D / 2 * (1 - (k + 1) / steps)
            z = rise * (k + 1) / steps + 0.3
            pts += [(y_out, z), (y_in, z)]
        pts = pts[:-1]
        top = rise + 0.6
        pts += [(0.35, top), (-0.35, top)]
        for k in range(steps - 1, -1, -1):
            y_in = -D / 2 * (1 - (k + 1) / steps)
            y_out = -D / 2 * (1 - k / steps)
            z = rise * (k + 1) / steps + 0.3
            pts += [(y_in, z), (y_out, z)]
        mb.push(Matrix.Translation((x, 0, 0)) @ Matrix.Rotation(math.pi / 2, 4, "Z"))
        mb.prism(_dedupe(pts), -t / 2, t / 2, K.M_STONE)
        mb.pop()


def _dedupe(pts):
    out = []
    for p in pts:
        if not out or (abs(out[-1][0] - p[0]) > 1e-4 or abs(out[-1][1] - p[1]) > 1e-4):
            out.append(p)
    return out


def to_object(mb, name, col):
    me = bpy.data.meshes.new(name)
    mb.bm.to_mesh(me)
    for n in mb.mats:
        me.materials.append(bpy.data.materials[n])
    o = bpy.data.objects.new(name, me)
    col.objects.link(o)
    return o


def box_uv(o, name="UVWorld"):
    """UV metrica alineada a cada cara, en el espacio LOCAL del objeto (el del edificio): 1 m = 1 unidad.
    Caras horizontales: (x, y). Resto: u = horizontal sobre el plano, v = a lo largo de la maxima pendiente
    (las tejas siguen la vertiente con su tamano real). Continua entre piezas coplanarias del mismo edificio y
    no depende del giro del edificio en el mundo."""
    me = o.data
    uv = me.uv_layers.get(name) or me.uv_layers.new(name=name)
    me.uv_layers.active = uv
    co = [v.co for v in me.vertices]
    Z = Vector((0, 0, 1))
    flat = [0.0] * (len(me.loops) * 2)
    for p in me.polygons:
        n = p.normal
        if abs(n.z) > 0.95:
            ax_u, ax_v = Vector((1, 0, 0)), Vector((0, 1, 0)) * (1 if n.z > 0 else -1)
        else:
            ax_v = (Z - n * n.z).normalized()
            ax_u = ax_v.cross(n).normalized()
        for li in range(p.loop_start, p.loop_start + p.loop_total):
            c = co[me.loops[li].vertex_index]
            flat[li * 2], flat[li * 2 + 1] = c.dot(ax_u), c.dot(ax_v)
    uv.data.foreach_set("uv", flat)


# ---------------------------------------------------------------------------
# props
# ---------------------------------------------------------------------------
PROP_BUILDERS = {
    "SIGN_Hanging": lambda mb, r: K.sign_hanging(mb, r),
    "LANTERN_Shard": lambda mb, r: K.lantern_shard(mb),
    "AWNING_Patch_A": lambda mb, r: K.awning(mb, variant=0, rng=r),
    "AWNING_Patch_B": lambda mb, r: K.awning(mb, variant=1, rng=r),
    "AWNING_Patch_C": lambda mb, r: K.awning(mb, variant=2, rng=r),
    "CRATE_Small": lambda mb, r: K.crate(mb, rng=r),
    "CRATE_Fruit": lambda mb, r: K.crate(mb, fruit=True, rng=r),
    "BARREL": lambda mb, r: K.barrel(mb),
    "TOOL_Rack": lambda mb, r: K.tool_rack(mb, r),
}


def prop_mesh(kind):
    """Malla compartida del kit para instanciar (se crea una vez)."""
    me = bpy.data.meshes.get(f"KITMESH_{kind}")
    if me is None:
        mb = K.MB()
        PROP_BUILDERS[kind](mb, random.Random(stable(kind)))
        mb.finish()
        me = bpy.data.meshes.new(f"KITMESH_{kind}")
        mb.bm.to_mesh(me)
        for n in mb.mats:
            me.materials.append(bpy.data.materials[n])
        tmp = bpy.data.objects.new("TMP_uv", me)
        bpy.context.scene.collection.objects.link(tmp)
        box_uv(tmp)
        bpy.data.objects.remove(tmp)
    return me


def place_props(name, root, col, W, D, door_local, plan, use, rng):
    """Props instanciados alrededor de la puerta y la fachada (frente +Y)."""
    pe = bpy.data.objects.new(f"{name}_Props", None)
    pe.empty_display_size = 0.5
    col.objects.link(pe)
    pe.parent = root
    items = []
    dx = door_local[0] if door_local else 0.0
    yF = D / 2
    items.append(("LANTERN_Shard", (dx - 1.05, yF, 2.55), 0.0))
    items.append(("SIGN_Hanging", (dx + 1.05, yF, 3.0), 0.0))
    if use == "shop":
        fronts = [m for m in plan if m["side"] == "front" and m["floor"] == 0 and m["kind"] != "Door"]
        for m in fronts[:2]:
            mw = W / m["n"]
            x = -W / 2 + mw * (m["i"] + 0.5)
            items.append((rng.choice(("AWNING_Patch_A", "AWNING_Patch_B", "AWNING_Patch_C")), (x, yF, 2.9), 0.0))
            items.append(("CRATE_Fruit", (x + rng.uniform(-0.6, 0.6), yF + 0.7, 0.0), rng.uniform(-0.2, 0.2)))
    for _ in range(rng.randint(2, 4)):
        kind = rng.choice(("CRATE_Small", "BARREL", "CRATE_Small", "TOOL_Rack"))
        side = rng.choice((-1, 1))
        x = side * rng.uniform(W / 2 - 1.6, W / 2 - 0.6)
        items.append((kind, (x, yF + 0.45 if kind != "TOOL_Rack" else yF + 0.1, 0.0), rng.uniform(-0.4, 0.4)))
    objs = []
    for k, (kind, pos, rz) in enumerate(items):
        o = bpy.data.objects.new(f"{name}_Prop_{kind}_{k:02d}", prop_mesh(kind))
        col.objects.link(o)
        o.parent = pe
        o.location = pos
        o.rotation_euler = (0, 0, rz)
        objs.append(o)
    return pe, objs


# ---------------------------------------------------------------------------
# API
# ---------------------------------------------------------------------------
def build_building(nombre, footprint=None, pisos=2, tipo_techo="gable", estilo="timber", seed=0, marker=None,
                   location=(0.0, 0.0, 0.0), rot_z=0.0, collection=None, props_collection=None, interior=True,
                   use="house", landmark=False, door_index=None):
    """Crea un edificio a partir del kit. Si se da 'marker' (MARKER_Bld_*), se usan su footprint, su posicion
    (centro de la base a pad_z) y su +Y (door_direction) y se ignoran footprint/location/rot_z."""
    assert estilo in STYLES and tipo_techo in ROOFS
    report = {"name": nombre}
    if marker is not None:
        W, D = float(marker["footprint_w"]), float(marker["footprint_d"])
        location = tuple(marker.matrix_world.translation)
        rot_z = marker.matrix_world.to_euler().z
        report["marker"] = marker.name
        if marker.get("door_direction", "+Y") != "+Y":
            report["warning_door_direction"] = marker.get("door_direction")
        interior = bool(marker.get("interior", interior))
    else:
        W, D = footprint
    mx, away = iso_max_floors(rot_z, landmark, use)
    if pisos > mx:
        report["floors_clamped"] = f"{pisos} -> {mx} (tope de la regla de alturas)"
        pisos = mx
    report.update({"footprint": [W, D], "floors": pisos, "roof": tipo_techo, "style": estilo,
                   "camera_side": away, "max_floors_rule": mx})
    seed_int = rng_for(nombre, seed)
    rng = random.Random(seed_int)
    plan = plan_modules(W, D, pisos, estilo, rng, door_index, use)
    col = collection or bpy.context.scene.collection
    root = bpy.data.objects.new(nombre, None)
    root.empty_display_size = 1.0
    col.objects.link(root)
    root.location = location
    root.rotation_euler = (0, 0, rot_z)
    root["building"] = True
    if marker is not None:
        root["marker"] = marker.name
    root["footprint_w"], root["footprint_d"] = W, D
    root["floors"], root["roof"], root["style"], root["seed"] = pisos, tipo_techo, estilo, seed
    objs = {}
    tris = {}
    door_local, top, ridge = None, 0.0, 0.0
    for detail, suf in ((0, ""), (1, "_LOD1"), (2, "_LOD2")):
        body, roof, dl, top, ridge = build_meshes(W, D, pisos, tipo_techo, estilo, seed_int, plan, detail, use)
        if detail == 0:
            door_local = dl
        for part, mb in (("Body", body), ("Roof", roof)):
            o = to_object(mb, f"{nombre}_{part}{suf}", col)
            o.parent = root
            box_uv(o)
            objs[f"{part}{suf}"] = o
            tris[f"{part}{suf}"] = sum(len(p.vertices) - 2 for p in o.data.polygons)
            mb.bm.free()
            if suf:
                o.hide_render = True
                o.hide_set(True)
    pe, props = place_props(nombre, root, props_collection or col, W, D, door_local, plan, use, random.Random(seed_int + 99))
    tris["Props"] = sum(sum(len(p.vertices) - 2 for p in o.data.polygons) for o in props)
    if interior and door_local is not None:
        dm = bpy.data.objects.new(f"MARKER_{nombre}_Door", None)
        dm.empty_display_type = "SINGLE_ARROW"
        dm.empty_display_size = 1.0
        col.objects.link(dm)
        dm.parent = root
        dm.location = door_local
        dm.rotation_euler = (0, 0, 0)                      # +Y local = hacia fuera (hereda el giro del edificio)
        dm["door_of"] = nombre
        dm["axis"] = "+Y hacia fuera"
        me = bpy.data.meshes.new(f"{nombre}_InteriorVolume")
        iw, idp, ih = W - 2 * K.WALL_T, D - 2 * K.WALL_T, pisos * K.FLOOR_H
        import bmesh
        bm = bmesh.new()
        bmesh.ops.create_cube(bm, size=1.0)
        for v in bm.verts:
            v.co = Vector((v.co.x * iw, v.co.y * idp, (v.co.z + 0.5) * ih))
        bm.to_mesh(me)
        bm.free()
        iv = bpy.data.objects.new(f"{nombre}_InteriorVolume", me)
        col.objects.link(iv)
        iv.parent = root
        iv.display_type = "WIRE"
        iv.hide_render = True
        iv["interior_size_m"] = [round(iw, 2), round(idp, 2), round(ih, 2)]
        objs["Door"], objs["InteriorVolume"] = dm, iv
    t0 = tris["Body"] + tris["Roof"]
    t1 = tris["Body_LOD1"] + tris["Roof_LOD1"]
    t2 = tris["Body_LOD2"] + tris["Roof_LOD2"]
    report.update({"tris": tris, "tris_body_roof": t0, "lod1_ratio": round(t1 / max(1, t0), 3),
                   "lod2_ratio": round(t2 / max(1, t0), 3), "eave_height_m": round(top, 2),
                   "ridge_height_m": round(top + ridge, 2),
                   "modules": {k: sum(1 for m in plan if m["kind"] == k) for k in K.WALL_KINDS},
                   "variants": {k: sum(1 for m in plan if m["variant"] == k) for k in K.VARIANTS},
                   "door_local": [round(c, 3) for c in door_local] if door_local else None})
    size = "pequena" if t0 <= 1500 else "media" if t0 <= 5000 else "grande" if t0 <= 12000 else "FUERA DE PRESUPUESTO"
    report["budget_class"] = size
    return root, objs, report
