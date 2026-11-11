extends SceneTree
## CONCORDIA - horneado de la navegacion en Godot a partir de las COLISIONES (sustituye a las -navmesh de Blender,
## que quedan desactivadas como referencia). Se hornea una vez y se guarda en res://navigation/*.res; al iniciar el
## juego solo se cargan (no se recalcula nada). Repetir cuando cambien los modelos:
##   godot --headless --path godot_concordia -s res://tools/bake_navmesh.gd [-- ciudad | interiores]
## API verificada en la documentacion 4.7 (docs/reference/godot47/class_navigationmesh.txt,
## class_navigationmeshsourcegeometrydata3d.txt, class_navigationserver3d.txt).
##
## Parametros (decision del usuario, PARADA 1): radio 0,35 m, escalon 0,25 m, pendiente 36 grados, celda 0,25 m.
## cell_height 0,05 m para que el escalon (0,25) sea un multiplo exacto (Godot lo redondea hacia abajo) y la altura
## del agente (1,8) tambien; navigation/3d/default_cell_size / _height del mapa = 0,25 / 0,05 (project.godot).
## Nota: Recast erosiona en celdas enteras: radio 0,35 -> 2 celdas = 0,50 m efectivos.
##
## Ciudad: se hornea entera de una vez (las aristas de las regiones casan exactamente) y despues:
##  1. se quitan los poligonos sobre tejados y azoteas (cielo abierto encima, sobre un cuerpo de edificio y a mas de
##     2,5 m del terreno), sobre el adarve de las puertas (GATE_*) y las torres (TOWER_*), y fuera de la muralla;
##  2. el camino de ronda (sobre WALL_Seg_* y BASTION_*) va en su propia region y se une con NavigationLink3D en las
##     escaleras STAIR_Gate*_L / _R junto a cada puerta (enlaces en navigation/links.json, los crea scripts/city.gd);
##  3. se quitan las islas (componentes sin conexion) de menos de MIN_ISLAND_M2 (techos de fuentes, puestos, muros)
##     y los suelos encerrados que no tocan la red principal (dentro de los edificios); la ronda se queda;
##  4. se reparte por distrito (Plaza, Mercado, Oficios, Clases, Razas, Moradas NE/NO/SE/SO) con el centro de cada
##     poligono; la franja junto a la muralla va al distrito de su angulo.
## Interiores: cada int_*.glb por separado (navigation/nav_int_<nombre>.res), para G6.
## Informe: debug/out/nav/bake_report.json.

const CELL := 0.25
const CELL_H := 0.05
const RADIUS := 0.35
const HEIGHT := 1.8
const CLIMB := 0.25
const SLOPE := 36.0
const MIN_ISLAND_M2 := 20.0
const WALL_INNER_R := 199.0          # cara interior de la muralla ~200 m: fuera solo queda la ronda
const GATE_CLEAR := 14.0             # sin ronda a menos de 14 m del eje de cada puerta (adarve de las puertas)
const DISTRICT_ANG := {"Mercado": 90.0, "Oficios": 0.0, "Razas": -90.0, "Clases": 180.0}

var report := {}


func _initialize() -> void:
	_run.call_deferred()


func _params(nm: NavigationMesh) -> void:
	nm.cell_size = CELL
	nm.cell_height = CELL_H
	nm.agent_radius = RADIUS
	nm.agent_height = HEIGHT
	nm.agent_max_climb = CLIMB
	nm.agent_max_slope = SLOPE
	nm.filter_ledge_spans = true
	nm.filter_low_hanging_obstacles = true
	nm.filter_walkable_low_height_spans = true
	# detalle por defecto de Recast (6 m / 1 m): con 2 m / 0,1 m salian ~120.000 poligonos y el mapa tardaba
	# demasiado en sincronizarse al arrancar; la altura exacta la pone la fisica (el jugador se pega al suelo)
	nm.detail_sample_distance = 6.0
	nm.detail_sample_max_error = 1.0
	nm.edge_max_error = 1.3
	nm.region_min_size = 2.0


func _source_from_colliders(root: Node) -> NavigationMeshSourceGeometryData3D:
	var src := NavigationMeshSourceGeometryData3D.new()
	var n := 0
	for b in root.find_children("*", "StaticBody3D", true, false):
		for cs in b.get_children():
			if not (cs is CollisionShape3D) or (cs as CollisionShape3D).disabled or cs.shape == null:
				continue
			var faces: PackedVector3Array
			if cs.shape is ConcavePolygonShape3D:
				faces = (cs.shape as ConcavePolygonShape3D).get_faces()
			else:
				faces = cs.shape.get_debug_mesh().get_faces()
			src.add_faces(faces, (cs as CollisionShape3D).global_transform)
			n += 1
			_maybe_obstruction(src, b, faces, (cs as CollisionShape3D).global_transform)
	report["formas_de_colision"] = report.get("formas_de_colision", 0) + n
	return src


func _maybe_obstruction(src: NavigationMeshSourceGeometryData3D, b: Node, faces: PackedVector3Array, xf: Transform3D) -> void:
	## mobiliario bajo (fuentes, pozos, puestos, bancos: < 3,5 m de alto y < 80 m2 de planta) bajo /Buildings/:
	## ademas de sus caras se anade su huella como obstruccion proyectada (con el radio del agente), para que la malla
	## no suba encima aunque el suelo de alrededor quede a menos de 0,25 m de su borde
	if not String(b.get_path()).contains("/Buildings/") or _walkable_structure(_body_name(b)):
		return
	if faces.is_empty():
		return
	var box := AABB(xf * faces[0], Vector3.ZERO)
	for p in faces:
		box = box.expand(xf * p)
	if box.size.y > 3.5 or box.size.x * box.size.z > 80.0:
		return
	var pts := PackedVector2Array()
	for p in faces:
		var g := xf * p
		pts.append(Vector2(g.x, g.z))
	var hull := Geometry2D.convex_hull(pts)
	var v := PackedVector3Array()
	for q in hull:
		v.append(Vector3(q.x, 0, q.y))
	src.add_projected_obstruction(v, box.position.y - 0.5, box.size.y + 0.5, false)
	report["obstrucciones_mobiliario"] = report.get("obstrucciones_mobiliario", 0) + 1
	var nm := _body_name(b).get_slice("_0", 0)
	var fam: Dictionary = report.get("obstrucciones_por_familia", {})
	fam[nm] = fam.get(nm, 0) + 1
	report["obstrucciones_por_familia"] = fam


func _run() -> void:
	var what := OS.get_cmdline_user_args()
	DirAccess.make_dir_recursive_absolute("res://navigation")
	DirAccess.make_dir_recursive_absolute("res://debug/out/nav")
	if what.is_empty() or what.has("ciudad"):
		await _bake_city()
	if what.is_empty() or what.has("interiores"):
		for f in DirAccess.get_files_at("res://assets/interiors/glb"):
			if f.ends_with(".glb"):
				await _bake_interior("res://assets/interiors/glb/" + f)
	var fh := FileAccess.open("res://debug/out/nav/bake_report.json", FileAccess.WRITE)
	fh.store_string(JSON.stringify(report, " "))
	fh = null
	print("BAKE ", JSON.stringify(report))
	quit()


# ---------------------------------------------------------------------------------------------------------- ciudad

func _bake_city() -> void:
	var t0 := Time.get_ticks_msec()
	var city: Node3D = (load("res://scenes/concordia_glb.tscn") as PackedScene).instantiate()
	city.set_script(null)                                  # sin LOD ni enlaces: solo la geometria
	root.add_child(city)
	for i in 3:
		await physics_frame
	var src := _source_from_colliders(city)
	var nm := NavigationMesh.new()
	_params(nm)
	nm.filter_baking_aabb = AABB(Vector3(-215, -20, -215), Vector3(430, 90, 430))
	NavigationServer3D.bake_from_source_geometry_data(nm, src)
	report["ciudad_horneado_ms"] = Time.get_ticks_msec() - t0
	report["ciudad_poligonos_brutos"] = nm.get_polygon_count()
	var space := city.get_world_3d().direct_space_state
	var gates: Array[Vector3] = []
	for m in city.find_children("MARKER_Gate_*", "", true, false):
		gates.append((m as Node3D).global_position)
	var verts := nm.get_vertices()
	var polys: Array = []
	for i in nm.get_polygon_count():
		polys.append(nm.get_polygon(i))
	# 1-2. clasificar cada poligono
	var cls: Array = []                                    # "" = quitar, "suelo", "ronda"
	var why := {}
	for i in polys.size():
		var c := _centroid(verts, polys[i])
		var k := _classify(space, c, gates)
		cls.append(k.c)
		why[k.motivo] = why.get(k.motivo, 0) + 1
	report["clasificacion"] = why
	# 3. islas
	var comp := _components(polys, cls)
	var area_of := {}
	for i in polys.size():
		if cls[i] != "":
			area_of[comp[i]] = area_of.get(comp[i], 0.0) + _area(verts, polys[i])
	var islands := []
	for i in polys.size():
		if cls[i] != "" and area_of[comp[i]] < MIN_ISLAND_M2:
			cls[i] = ""
	for cid in area_of:
		if area_of[cid] < MIN_ISLAND_M2:
			islands.append(snappedf(area_of[cid], 0.1))
	report["islas_quitadas"] = islands.size()
	report["islas_quitadas_m2"] = snappedf(islands.reduce(func(a, b): return a + b, 0.0), 1.0)
	var big := []
	for cid in area_of:
		if area_of[cid] >= MIN_ISLAND_M2:
			big.append(snappedf(area_of[cid], 1.0))
	big.sort()
	big.reverse()
	report["componentes_que_quedan_m2"] = big
	# componentes separados de la red principal (para revisar: terrazas sin escalera, galerias, ...)
	var main_cid = null
	var main_a := 0.0
	for cid in area_of:
		if area_of[cid] > main_a:
			main_a = area_of[cid]
			main_cid = cid
	var sep := {}
	for i in polys.size():
		if cls[i] == "" or comp[i] == main_cid:
			continue
		var c := _centroid(verts, polys[i])
		var s: Dictionary = sep.get(comp[i], {"m2": area_of[comp[i]], "suma": Vector3.ZERO, "n": 0, "clase": cls[i], "y_min": 1e9, "y_max": -1e9})
		s.suma += c
		s.n += 1
		s.y_min = minf(s.y_min, c.y)
		s.y_max = maxf(s.y_max, c.y)
		sep[comp[i]] = s
	var sep_list := []
	for cid in sep:
		var s: Dictionary = sep[cid]
		var c: Vector3 = s.suma / s.n
		var hit := space.intersect_ray(PhysicsRayQueryParameters3D.create(c + Vector3(0, 0.4, 0), c - Vector3(0, 2, 0)))
		sep_list.append({"m2": snappedf(s.m2, 1.0), "clase": s.clase, "blender": [snappedf(c.x, 0.1), snappedf(-c.z, 0.1)],
			"y": [snappedf(s.y_min, 0.1), snappedf(s.y_max, 0.1)], "distrito": _district(c),
			"sobre": _body_name(hit.collider) if hit else "-"})
	sep_list.sort_custom(func(a, b): return a.m2 > b.m2)
	# se quedan la red principal y los tramos de ronda (se enlazan por las escaleras de las puertas); el resto de
	# componentes separados son suelos encerrados (dentro de los edificios: el interior va aparte, G6)
	var dropped := []
	for x in sep_list:
		if x.clase != "ronda":
			dropped.append(x)
	for i in polys.size():
		if cls[i] == "suelo" and comp[i] != main_cid:
			cls[i] = ""
	report["red_principal_m2"] = snappedf(main_a, 1.0)
	report["suelos_encerrados_quitados"] = dropped.size()
	report["suelos_encerrados_quitados_m2"] = snappedf(dropped.reduce(func(a, b): return a + b.m2, 0.0), 1.0)
	report["suelos_encerrados_mayores"] = dropped.slice(0, 40)
	report["tramos_de_ronda"] = sep_list.filter(func(x): return x.clase == "ronda").size()
	# 3b. aristas con mas de 2 poligonos (solapes del detalle de Recast) y poligonos degenerados: Godot avisa
	#     "edge errors" al sincronizar; se quita el poligono mas pequeno de cada arista sobrante
	report["poligonos_solapados_quitados"] = _fix_overlaps(verts, polys, cls)
	# 4. regiones
	var groups := {}
	for i in polys.size():
		if cls[i] == "":
			continue
		var reg := "Muralla_Ronda" if cls[i] == "ronda" else _district(_centroid(verts, polys[i]))
		if not groups.has(reg):
			groups[reg] = []
		groups[reg].append(i)
	var regions := {}
	for reg in groups:
		var out := NavigationMesh.new()
		_params(out)
		var remap := {}
		var nv := PackedVector3Array()
		var area := 0.0
		for i in groups[reg]:
			var q := PackedInt32Array()
			for idx in polys[i]:
				if not remap.has(idx):
					remap[idx] = nv.size()
					nv.append(verts[idx])
				q.append(remap[idx])
			area += _area(verts, polys[i])
		out.vertices = nv
		for i in groups[reg]:
			var q := PackedInt32Array()
			for idx in polys[i]:
				q.append(remap[idx])
			out.add_polygon(q)
		var path := "res://navigation/nav_%s.res" % reg.to_lower()
		var err := ResourceSaver.save(out, path, ResourceSaver.FLAG_COMPRESS)
		regions[reg] = {"poligonos": out.get_polygon_count(), "m2": snappedf(area, 1.0), "archivo": path,
			"error": error_string(err)}
	report["regiones"] = regions
	_links(city, space, nm, verts, polys, cls)
	report["ciudad_total_ms"] = Time.get_ticks_msec() - t0
	city.queue_free()
	await process_frame


func _classify(space: PhysicsDirectSpaceState3D, c: Vector3, gates: Array[Vector3]) -> Dictionary:
	var hit := space.intersect_ray(PhysicsRayQueryParameters3D.create(c + Vector3(0, 0.4, 0), c - Vector3(0, 1.0, 0)))
	var r := Vector2(c.x, c.z).length()
	if hit.is_empty():
		return {"c": "suelo" if r < WALL_INNER_R else "", "motivo": "sin_colision_debajo"}
	var col: Node = hit.collider
	var path := String(col.get_path())
	var nm := _body_name(col)
	if path.contains("/Wall/"):
		if nm.begins_with("STAIR_Gate"):
			return {"c": "suelo", "motivo": "escalera_puerta"}
		if nm.begins_with("GATE_") or nm.begins_with("TOWER_"):
			return {"c": "", "motivo": "adarve_puerta_o_torre"}
		for g in gates:
			if Vector2(c.x - g.x, c.z - g.z).length() < GATE_CLEAR:
				return {"c": "", "motivo": "adarve_puerta_o_torre"}
		return {"c": "ronda", "motivo": "ronda"}
	if r > WALL_INNER_R:
		return {"c": "", "motivo": "fuera_de_la_muralla"}
	if path.contains("/Buildings/") and not _walkable_structure(nm):
		# sobre un edificio: azotea si hay cielo abierto encima y esta alta sobre el terreno
		var up := space.intersect_ray(PhysicsRayQueryParameters3D.create(c + Vector3(0, 0.3, 0), c + Vector3(0, 60, 0)))
		var ground := _terrain_y(space, c)
		if up.is_empty() and c.y - ground > 2.5:
			return {"c": "", "motivo": "azotea_o_tejado"}
		return {"c": "suelo", "motivo": "sobre_edificio_cubierto_o_bajo"}
	return {"c": "suelo", "motivo": "suelo"}


func _terrain_y(space: PhysicsDirectSpaceState3D, c: Vector3) -> float:
	## primer terreno (Terrain/) bajo c, saltando lo demas
	var ex: Array[RID] = []
	var from := c + Vector3(0, 0.4, 0)
	for i in 8:
		var q := PhysicsRayQueryParameters3D.create(from, Vector3(c.x, -50, c.z))
		q.exclude = ex
		var h := space.intersect_ray(q)
		if h.is_empty():
			return -50.0
		if String(h.collider.get_path()).contains("/Terrain/"):
			return h.position.y
		ex.append(h.rid)
	return -50.0


func _body_name(col: Node) -> String:
	## el StaticBody de un "-colonly" puede quedar sin nombre (@StaticBody3D@...): se usa el de su malla hermana
	var nm := String(col.name)
	if nm.begins_with("@"):
		var p := col.get_parent()
		if p:
			nm = String(p.name)
	return nm


func _walkable_structure(nm: String) -> bool:
	for k in ["STAIRS_", "BRIDGE_", "ARCH_", "TRN_", "PORTAL", "ATRIO", "Descent", "Plaza_", "PLAZA", "Ramp", "RAMP"]:
		if nm.begins_with(k) or nm.contains(k):
			return true
	return false


func _district(c: Vector3) -> String:
	var x := c.x
	var y := -c.z
	var r := sqrt(x * x + y * y)
	if r < 60.0:
		return "Plaza"
	var ang := rad_to_deg(atan2(y, x))
	for d in DISTRICT_ANG:
		if absf(wrapf(ang - DISTRICT_ANG[d], -180.0, 180.0)) < 30.0:
			return d
	return "Moradas_" + ("N" if y > 0 else "S") + ("E" if x > 0 else "O")


func _fix_overlaps(verts: PackedVector3Array, polys: Array, cls: Array) -> int:
	var removed := 0
	for it in 4:
		var edges := {}
		for i in polys.size():
			if cls[i] == "":
				continue
			var p: PackedInt32Array = polys[i]
			if _area(verts, p) < 0.0005:
				cls[i] = ""
				removed += 1
				continue
			for j in p.size():
				var a := verts[p[j]].snapped(Vector3.ONE * 0.01)
				var b := verts[p[(j + 1) % p.size()]].snapped(Vector3.ONE * 0.01)
				var key := str(a) + str(b) if str(a) < str(b) else str(b) + str(a)
				if not edges.has(key):
					edges[key] = []
				edges[key].append(i)
		var changed := false
		for key in edges:
			var owners: Array = edges[key].filter(func(i): return cls[i] != "")
			if owners.size() <= 2:
				continue
			owners.sort_custom(func(x, y): return _area(verts, polys[x]) > _area(verts, polys[y]))
			for i in owners.slice(2):
				cls[i] = ""
				removed += 1
				changed = true
		if not changed:
			break
	return removed


func _centroid(v: PackedVector3Array, p: PackedInt32Array) -> Vector3:
	var c := Vector3.ZERO
	for i in p:
		c += v[i]
	return c / p.size()


func _area(v: PackedVector3Array, p: PackedInt32Array) -> float:
	var a := 0.0
	for k in range(1, p.size() - 1):
		a += (v[p[k]] - v[p[0]]).cross(v[p[k + 1]] - v[p[0]]).length() * 0.5
	return a


func _components(polys: Array, cls: Array) -> PackedInt32Array:
	## componentes conexos por aristas compartidas (solo poligonos que se quedan); la ronda cuenta aparte
	var edge_owner := {}
	var parent := PackedInt32Array()
	parent.resize(polys.size())
	for i in polys.size():
		parent[i] = i
	var find := func(x: int) -> int:
		while parent[x] != x:
			parent[x] = parent[parent[x]]
			x = parent[x]
		return x
	for i in polys.size():
		if cls[i] == "":
			continue
		var p: PackedInt32Array = polys[i]
		for j in p.size():
			var a := p[j]
			var b := p[(j + 1) % p.size()]
			var key := Vector2i(mini(a, b), maxi(a, b))
			if edge_owner.has(key):
				var o: int = edge_owner[key]
				if cls[o] == cls[i]:
					var ra: int = find.call(i)
					var rb: int = find.call(o)
					if ra != rb:
						parent[ra] = rb
			else:
				edge_owner[key] = i
	var out := PackedInt32Array()
	out.resize(polys.size())
	for i in polys.size():
		out[i] = find.call(i)
	return out


func _links(city: Node, space: PhysicsDirectSpaceState3D, nm: NavigationMesh, verts: PackedVector3Array,
		polys: Array, cls: Array) -> void:
	## un NavigationLink3D por escalera STAIR_Gate*_L / _R: del pie (malla de suelo mas cercana) a lo alto (ronda)
	var links := []
	for b in city.find_children("*", "StaticBody3D", true, false):
		var bn := _body_name(b)
		if not bn.begins_with("STAIR_Gate"):
			continue
		var cs := b.get_child(0) as CollisionShape3D
		var f: PackedVector3Array = (cs.shape as ConcavePolygonShape3D).get_faces() if cs.shape is ConcavePolygonShape3D \
				else cs.shape.get_debug_mesh().get_faces()
		var lo := Vector3(0, 1e9, 0)
		var hi := Vector3(0, -1e9, 0)
		for p in f:
			var g := cs.global_transform * p
			if g.y < lo.y:
				lo = g
			if g.y > hi.y:
				hi = g
		var a := _nearest(verts, polys, cls, "suelo", lo)
		var z := _nearest(verts, polys, cls, "ronda", hi)
		links.append({"nombre": bn, "inicio": [a.x, a.y, a.z], "fin": [z.x, z.y, z.z],
			"inicio_a_m": snappedf(a.distance_to(lo), 0.01), "fin_a_m": snappedf(z.distance_to(hi), 0.01)})
	var fh := FileAccess.open("res://navigation/links.json", FileAccess.WRITE)
	fh.store_string(JSON.stringify(links, " "))
	fh = null
	report["enlaces_escaleras_puertas"] = links.size()


func _nearest(verts: PackedVector3Array, polys: Array, cls: Array, want: String, p: Vector3) -> Vector3:
	var best := Vector3.ZERO
	var bd := 1e9
	for i in polys.size():
		if cls[i] != want:
			continue
		var c := _centroid(verts, polys[i])
		var d := c.distance_to(p)
		if d < bd:
			bd = d
			best = c
	return best


# ------------------------------------------------------------------------------------------------------ interiores

func _bake_interior(path: String) -> void:
	var t0 := Time.get_ticks_msec()
	var n: Node3D = (load(path) as PackedScene).instantiate()
	root.add_child(n)
	await physics_frame
	var src := _source_from_colliders(n)
	var nm := NavigationMesh.new()
	_params(nm)
	NavigationServer3D.bake_from_source_geometry_data(nm, src)
	var name := path.get_file().get_basename()
	var out := "res://navigation/nav_%s.res" % name
	var err := ResourceSaver.save(nm, out, ResourceSaver.FLAG_COMPRESS)
	var area := 0.0
	for i in nm.get_polygon_count():
		area += _area(nm.get_vertices(), nm.get_polygon(i))
	report[name] = {"poligonos": nm.get_polygon_count(), "m2": snappedf(area, 0.1), "ms": Time.get_ticks_msec() - t0,
		"archivo": out, "error": error_string(err)}
	n.queue_free()
	await process_frame
