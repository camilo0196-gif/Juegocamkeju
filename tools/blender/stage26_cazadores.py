"""
CONCORDIA - Etapa 26 (E6, punto 4 aprobado): acceso al campo de tiro del Gremio de Cazadores.

- Valla de 1.2 m cerrada por el lado de la ciudad (+Y local, daba al invernadero) y apertura de 2 m en el extremo
  norte (+X local, y 0..2) con portillo de tablas abierto hacia dentro.
- Camino de 2 m de ancho libre desde la apertura hasta la calle mas cercana (adoquin MAT_Cobble_Concordia, 3 cm sobre
  el terreno), comprobado celda a celda: sin parcelas (huella de marcadores), objetos, escalinatas ni puentes.
- Malla de navegacion: el interior del campo (y -2.4..2.0: sin la franja de las dianas, el mostrador ni el portillo) y el camino se anaden a
  TRN_NavMesh_Oficios-navmesh; el final del camino se suelda a una arista de borde de la calle (caras con arista
  comun) y se comprueba la conexion por adyacencia de caras.
"""

import math

import bmesh
import bpy
from mathutils import Matrix, Vector
from mathutils.geometry import intersect_point_line

NAV = "TRN_NavMesh_Oficios-navmesh"
W, D = 14.0, 8.0
OPEN_Y = (0.0, 2.0)
FENCE_H = 1.2


def fence_mesh(mb, K):
    hw, hd = W / 2, D / 2
    edges = [((-hw, -hd), (hw, -hd)), ((-hw, hd), (hw, hd)), ((-hw, -hd), (-hw, hd)),
             ((hw, -hd), (hw, OPEN_Y[0])), ((hw, OPEN_Y[1]), (hw, hd))]
    for (x0, y0), (x1, y1) in edges:
        L = math.hypot(x1 - x0, y1 - y0)
        n = max(1, int(round(L / 2.0)))
        for k in range(n + 1):
            x = x0 + (x1 - x0) * k / n
            y = y0 + (y1 - y0) * k / n
            mb.box((x - 0.07, y - 0.07, -0.3), (x + 0.07, y + 0.07, FENCE_H), K.M_WOOD, skip=("z-",))
        for z in (0.55, 1.08):
            mb.rod((x0, y0, z), (x1, y1, z), 0.04, K.M_WOOD)
    # mostrador de tiro (con dos patas) junto al lado de la ciudad
    mb.box((-hw + 0.5, hd - 1.6, 0.85), (hw - 0.5, hd - 1.45, 0.95), K.M_WOOD)
    for x in (-hw + 0.8, hw - 0.8):
        mb.box((x - 0.05, hd - 1.58, 0.0), (x + 0.05, hd - 1.47, 0.85), K.M_WOOD, skip=("z-", "z+"))
    # portillo: hoja de tablas de 1.9 m abierta hacia dentro, bisagra en el poste (hw, 2.0)
    x0 = hw - 0.08
    mb.box((x0 - 1.9, OPEN_Y[1] + 0.04, 0.15), (x0, OPEN_Y[1] + 0.09, 1.05), K.M_WOOD)
    for z in (0.3, 0.9):
        mb.box((x0 - 1.9, OPEN_Y[1] + 0.09, z), (x0, OPEN_Y[1] + 0.13, z + 0.1), K.M_WOOD, skip=("y-",))


def fence_colliders():
    hw, hd = W / 2, D / 2
    t = 0.07
    return [((-hw - t, -hd - t, 0), (hw + t, -hd + t, FENCE_H)), ((-hw - t, hd - t, 0), (hw + t, hd + t, FENCE_H)),
            ((-hw - t, -hd, 0), (-hw + t, hd, FENCE_H)), ((hw - t, -hd, 0), (hw + t, OPEN_Y[0], FENCE_H)),
            ((hw - t, OPEN_Y[1], 0), (hw + t, hd, FENCE_H))]


def parcel_rects():
    out = []
    for m in bpy.data.objects:
        if m.type == "EMPTY" and m.name.startswith("MARKER_Bld_") and m.get("footprint_w"):
            out.append((m.name, m.matrix_world.inverted(), float(m["footprint_w"]) / 2, float(m["footprint_d"]) / 2))
    return out


def in_parcel(p, rects, skip=()):
    for name, inv, hx, hy in rects:
        if name in skip:
            continue
        q = inv @ Vector((p.x, p.y, 0.0))
        if abs(q.x) <= hx and abs(q.y) <= hy:
            return name
    return None


def plan_path(grid, mw, rects):
    """Avanza por +X local desde la apertura hasta encontrar calle publica en toda la anchura."""
    y_mid = sum(OPEN_Y) / 2
    x = W / 2
    checks = []
    while x < W / 2 + 25.0:
        x += 0.5
        row = []
        for t in (OPEN_Y[0] + 0.1, y_mid, OPEN_Y[1] - 0.1):
            p = mw @ Vector((x, t, 0.0))
            s = grid.state(p.x, p.y)[0]
            par = in_parcel(p, rects, skip=("MARKER_Bld_Gremio_Cazadores",))
            row.append((s, par))
        checks.append((round(x, 2), row))
        if any(s == "occupied" or par for s, par in row):
            return None, checks
        if all(s == "public" for s, _p in row):
            return x, checks
    return None, checks


def boundary_edges(bm):
    return [e for e in bm.edges if len(e.link_faces) == 1]


def nav_offset(nav, g, around):
    mw = nav.matrix_world
    ds = []
    for p in nav.data.polygons:
        c = mw @ p.center
        if (c.xy - around).length < 10:
            ds.append(c.z - g(c.x, c.y))
    ds.sort()
    return ds[len(ds) // 2] if ds else 0.05


def add_navmesh(nav, mw, x_end, g, off, st):
    """Campo + camino en la malla (marco del mundo), soldado a una arista de borde de la calle."""
    inv = nav.matrix_world.inverted()
    bm = bmesh.new()
    bm.from_mesh(nav.data)
    bm.verts.ensure_lookup_table()
    n_faces0 = len(bm.faces)
    big = components(bm)
    main = max(big, key=len)

    def wv(lx, ly):
        p = mw @ Vector((lx, ly, 0.0))
        return inv @ Vector((p.x, p.y, g(p.x, p.y) + off))

    # extremo del camino: arista de borde de la malla de calle mas cercana al centro del final, de >= 2 m
    end_mid = mw @ Vector((x_end, sum(OPEN_Y) / 2, 0.0))
    best = None
    for e in boundary_edges(bm):
        a, b = nav.matrix_world @ e.verts[0].co, nav.matrix_world @ e.verts[1].co
        if (a - b).length < 2.05:
            continue
        q, t = intersect_point_line(end_mid, a, b)
        t = min(max(t, 0.0), 1.0)
        q = a + (b - a) * t
        d = (q.xy - end_mid.xy).length
        if d < 3.0 and (best is None or d < best[0]):
            best = (d, e, a, b, t)
    if best is None:
        st["navmesh_error"] = "no hay arista de borde de >= 2 m a menos de 3 m del final del camino"
        bm.free()
        return None
    d, e, a, b, t = best
    L = (b - a).length
    tm = min(max(t, 1.0 / L + 0.01), 1.0 - 1.0 / L - 0.01)
    p0, p1 = a + (b - a) * (tm - 1.0 / L), a + (b - a) * (tm + 1.0 / L)
    # partir la arista de la calle en p0 y p1 (dos vertices nuevos sobre la misma arista)
    v_a, v_b = e.verts
    ne, nv0 = bmesh.utils.edge_split(e, v_a, (tm - 1.0 / L))
    nv0.co = inv @ p0
    e2 = next(x for x in nv0.link_edges if v_b in x.verts)
    fac = ((tm + 1.0 / L) - (tm - 1.0 / L)) / (1.0 - (tm - 1.0 / L))
    _ne2, nv1 = bmesh.utils.edge_split(e2, nv0, fac)
    nv1.co = inv @ p1
    # orientar: el vertice de p0/p1 que cae del lado y = 0 del camino
    l0 = mw.inverted() @ Vector((p0.x, p0.y, 0.0))
    l1 = mw.inverted() @ Vector((p1.x, p1.y, 0.0))
    end_lo, end_hi = (nv0, nv1) if l0.y < l1.y else (nv1, nv0)
    # rejilla del campo (x -6.5..7.0, y -2.4..2.0) y camino (x 7.0..final, y 0..2; dos vertices de ancho)
    xs = [-6.5 + 0.5 * i for i in range(0, 28)]           # hasta 7.0
    ys_field = [-2.4, -1.4, -0.4, 0.0, 1.0, 2.0]
    grid = {}
    for x in xs:
        for y in ys_field:
            grid[(round(x, 2), y)] = bm.verts.new(wv(x, y))
    for i in range(len(xs) - 1):
        for j in range(len(ys_field) - 1):
            vs = [grid[(round(xs[i], 2), ys_field[j])], grid[(round(xs[i + 1], 2), ys_field[j])],
                  grid[(round(xs[i + 1], 2), ys_field[j + 1])], grid[(round(xs[i], 2), ys_field[j + 1])]]
            bm.faces.new(vs)
    lo, hi, top = grid[(7.0, 0.0)], grid[(7.0, 1.0)], grid[(7.0, 2.0)]
    lx_end = (l0.x + l1.x) / 2
    xs_path = []
    x = 7.0
    while x + 1.0 < lx_end - 0.3:
        x += 1.0
        xs_path.append(x)
    first = True
    prev = (lo, top)
    for x in xs_path:
        cur = (bm.verts.new(wv(x, 0.0)), bm.verts.new(wv(x, 2.0)))
        if first:                                         # pentagono: reutiliza las aristas lo-hi-top del campo
            bm.faces.new([lo, cur[0], cur[1], top, hi])
            first = False
        else:
            bm.faces.new([prev[0], cur[0], cur[1], prev[1]])
        prev = cur
    if first:
        bm.faces.new([lo, end_lo, end_hi, top, hi])
    else:
        bm.faces.new([prev[0], end_lo, end_hi, prev[1]])  # reutiliza la arista partida de la calle
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    for f in bm.faces:
        if f.normal.z < 0:
            f.normal_flip()
    comps = components(bm)
    field_face = min(bm.faces, key=lambda f: (f.calc_center_median() - wv(0.0, 0.0)).length)
    comp = next(c for c in comps if field_face.index in c)
    main_hit = len(comp & main) > 0
    res = {"faces_added": len(bm.faces) - n_faces0, "street_edge_len_m": round(L, 2), "weld_dist_m": round(d, 2),
           "components_before": len(big), "main_component_faces_before": len(main),
           "range_component_faces": len(comp), "range_connected_to_main_street_network": main_hit,
           "nav_offset_m": round(off, 3)}
    bm.to_mesh(nav.data)
    bm.free()
    nav.data.update()
    return res


def components(bm):
    bm.faces.ensure_lookup_table()
    for i, f in enumerate(bm.faces):
        f.index = i
    seen, out = set(), []
    for f in bm.faces:
        if f.index in seen:
            continue
        stack, comp = [f], set()
        seen.add(f.index)
        while stack:
            x = stack.pop()
            comp.add(x.index)
            for e in x.edges:
                for y in e.link_faces:
                    if y.index not in seen:
                        seen.add(y.index)
                        stack.append(y)
        out.append(comp)
    return out


def path_mesh(mb, K, x_end, mw, g, root_inv):
    """Adoquin de 2 m desde la apertura hasta la calle, a 3 cm sobre el terreno (tiras de 1 m)."""
    xs = [7.0]
    while xs[-1] + 1.0 < x_end:
        xs.append(xs[-1] + 1.0)
    xs.append(x_end)

    def pt(lx, ly):
        p = mw @ Vector((lx, ly, 0.0))
        return root_inv @ Vector((p.x, p.y, g(p.x, p.y) + 0.03))
    for a, b in zip(xs, xs[1:]):
        mb.face([pt(a, OPEN_Y[0]), pt(b, OPEN_Y[0]), pt(b, OPEN_Y[1]), pt(a, OPEN_Y[1])], "MAT_Cobble_Concordia",
                nrm=(0, 0, 1))


def step(st):
    import bld_kit as K
    import build_stage18 as B18
    import build_stage19 as B19
    import stage25_lots as LOTS
    g = B18.ground_fn()
    rng_o = bpy.data.objects["Gremio_Cazadores_Range"]
    root = bpy.data.objects["Gremio_Cazadores"]
    mw = rng_o.matrix_world.copy()
    col = rng_o.users_collection[0]
    # valla nueva
    old_me = rng_o.data
    mb = K.MB()
    fence_mesh(mb, K)
    import concordia_buildings as B
    tmp = B.to_object(mb, "TMP_fence", col)
    mb.bm.free()
    rng_o.data = tmp.data
    bpy.data.objects.remove(tmp)
    rng_o.data.name = "Gremio_Cazadores_Range"
    if old_me.users == 0:
        bpy.data.meshes.remove(old_me)
    B.box_uv(rng_o)
    oc = bpy.data.objects.get("Gremio_Cazadores_Range-colonly")
    if oc is not None:
        bpy.data.objects.remove(oc)
    B19.box_collider("Gremio_Cazadores_Range-colonly", col, rng_o, fence_colliders())
    bpy.context.view_layer.update()
    # camino
    grid = LOTS.Grid(0.0, 40.0, 60.0, 195.0)
    rects = parcel_rects()
    x_end, checks = plan_path(grid, mw, rects)
    if x_end is None:
        st["cazadores_access"] = {"ok": False, "reason": "el camino cruza algo ocupado o una parcela", "checks": checks}
        return
    pm = K.MB()
    path_mesh(pm, K, x_end + 0.6, mw, g, root.matrix_world.inverted())
    po = B19.mb_object(pm, "Gremio_Cazadores_Path", col, root)
    po["note"] = "camino de acceso al campo de tiro (2 m de ancho libre), adoquin; etapa 26"
    mk = bpy.data.objects.get("MARKER_Cazadores_Range")
    if mk is not None:
        mk["entrance"] = "extremo norte (+X local), apertura de 2 m con portillo"
    # malla de navegacion
    nav = bpy.data.objects[NAV]
    off = nav_offset(nav, g, (mw @ Vector((x_end, 1.0, 0))).xy)
    res = add_navmesh(nav, mw, x_end + 0.6, g, off, st)
    length = round(x_end + 0.6 - 7.0, 2)
    st["cazadores_access"] = {"ok": bool(res and res["range_connected_to_main_street_network"]),
                              "opening": "extremo norte del campo (+X local), y 0..2 m, portillo abierto hacia dentro",
                              "path_m": [length, 2.0], "path_surface": "MAT_Cobble_Concordia",
                              "street_reached_at": [round(c, 1) for c in (mw @ Vector((x_end, 1.0, 0))).xy],
                              "path_checks": [(x, [s for s, _p in row]) for x, row in checks],
                              "navmesh": res}
    print("cazadores", st["cazadores_access"]["ok"], length, res, flush=True)
    _ = Matrix
