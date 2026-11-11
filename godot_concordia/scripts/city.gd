extends Node3D
## CONCORDIA - raiz de scenes/concordia.tscn (la escena la genera tools/build_world.gd a partir de la ciudad fuente
## scenes/concordia_glb.tscn de tools/build_city.gd; este script prepara en tiempo de ejecucion lo que depende de
## la escena montada):
##  - mundo horneado (world/): chunks de 50 m con las mallas fusionadas por material, cargados y descargados por
##    distancia con hilos (scripts/world_streamer.gd); Special (piezas sueltas siempre cargadas) y Logic (marcadores)
##  - LOD propios (scripts/lod_manager.gd) con foco en el jugador: por chunk (mascara de LOD) y por unidad en Special
##  - NavigationLink3D por cada pareja NAVLINK_<puerta>_Start / _End y por cada escalera de puerta de la muralla
##    (res://navigation/links.json, del horneado); las -navmesh de Blender se desactivan (solo referencia): manda la
##    navegacion horneada en Godot (nodo Navigation, grupo nav_godot)
##  - oclusores: cajas horneadas en cada chunk (modo .glb: BoxOccluder3D en los cuerpos grandes)
##  - ajustes de material de Godot (scripts/materials_fix.gd): haces y Obelisco (el resto ya viene horneado)
##  - zona actual (plaza, Mercado, Oficios, Clases, Razas, Moradas, muralla, ceniza) para el HUD
## Si la escena no tiene nodo Chunks (scenes/concordia_glb.tscn) funciona como antes, con los .glb enteros.

signal ready_city

@export var focus_path: NodePath
## pisos del Obelisco encendidos (valor de prueba hasta que G6/G7 lo lean de la partida)
@export var obelisk_floors := 12

var lod: Node
var stream: Node                 # scripts/world_streamer.gd (null con la ciudad de .glb)
var stats := {}
var materials: RefCounted


func _ready() -> void:
	var t0 := Time.get_ticks_msec()
	materials = preload("res://scripts/materials_fix.gd").new()
	lod = preload("res://scripts/lod_manager.gd").new()
	lod.name = "LodManager"
	add_child(lod)
	var chunks := get_node_or_null("Chunks")
	if chunks:
		stream = preload("res://scripts/world_streamer.gd").new()
		stream.name = "WorldStreamer"
		add_child(stream)
		stats["mundo"] = stream.setup(self, chunks, lod, String(get_meta("world_index", "res://world/world_index.json")))
		stats["materiales"] = materials.apply(self)
		var sp := get_node_or_null("Special")
		if sp:
			lod.add_scene_root(sp)
		# arranque: la plaza y todo lo que este a menos del radio de carga (120 m en Bajo); el resto, con hilos
		stream.sync_around(Vector3.ZERO)
	else:
		stats["materiales"] = materials.apply(self)
		for group in ["Terrain", "Wall", "Buildings"]:
			var g := get_node_or_null(group)
			if g == null:
				continue
			for inst in g.get_children():
				lod.add_scene_root(inst)
		stats["oclusores_caja"] = _box_occluders()
	materials.set_obelisk_floors(obelisk_floors)
	stats["navlinks"] = _navlinks()
	stats["nav_regiones"] = _navigation()
	if not focus_path.is_empty():
		lod.focus = get_node(focus_path)
	lod.apply_all()
	stats["lod_unidades"] = lod.stats.unidades
	stats["preparacion_ms"] = Time.get_ticks_msec() - t0
	print("CITY ", JSON.stringify(stats))
	ready_city.emit()


func is_streamed() -> bool:
	return stream != null


func materials_in_use() -> Array:
	## materiales de la ciudad (biblioteca del mundo horneado, o los de las mallas con la ciudad de .glb)
	if stream:
		return stream.materials
	var out := {}
	for mi in find_children("*", "MeshInstance3D", true, false):
		var m: Mesh = (mi as MeshInstance3D).mesh
		if m == null:
			continue
		for i in m.get_surface_count():
			var mat := (mi as MeshInstance3D).get_active_material(i)
			if mat:
				out[mat] = true
	return out.keys()


func set_focus(n: Node3D) -> void:
	lod.focus = n
	if stream:
		stream.focus = n
		if n:
			stream.sync_around(n.global_position)
	lod.apply_all()


func ensure_loaded(p: Vector3) -> void:
	## carga ya (sin hilos) los chunks alrededor de p; para teletransportes y herramientas (benchmark, capturas)
	if stream:
		stream.sync_around(p)
	lod.apply_all()


func apply_quality(q: Dictionary) -> void:
	lod.lod0_end = q.get("lod0_m", lod.lod0_end)
	lod.lod1_end = q.get("lod1_m", lod.lod1_end)
	if stream:
		stream.load_radius = q.get("carga_m", stream.load_radius)
		stream.update_now()
	lod.force_refresh()


func _navlinks() -> int:
	var starts := {}
	for n in get_tree().get_nodes_in_group("navlinks"):
		var nm := String(n.name)
		if nm.ends_with("_Start"):
			starts[nm.trim_suffix("_Start")] = n
	var k := 0
	for n in get_tree().get_nodes_in_group("navlinks"):
		var nm := String(n.name)
		if not nm.ends_with("_End") or not starts.has(nm.trim_suffix("_End")):
			continue
		var a: Node3D = starts[nm.trim_suffix("_End")]
		var link := NavigationLink3D.new()
		link.name = "NavLink_" + nm.trim_suffix("_End").trim_prefix("NAVLINK_")
		link.bidirectional = true
		add_child(link)
		link.global_position = a.global_position
		link.start_position = Vector3.ZERO
		link.end_position = link.to_local((n as Node3D).global_position)
		k += 1
	return k


func _navigation() -> int:
	var k := 0
	for r in find_children("*", "NavigationRegion3D", true, false):
		if r.is_in_group("nav_godot"):
			k += 1
		else:
			(r as NavigationRegion3D).enabled = false
	if FileAccess.file_exists("res://navigation/links.json"):
		var links = JSON.parse_string(FileAccess.get_file_as_string("res://navigation/links.json"))
		for l in (links if links is Array else []):
			if not (l is Dictionary) or (l.get("inicio", []) as Array).size() < 3 or (l.get("fin", []) as Array).size() < 3:
				push_warning("navigation/links.json: enlace mal formado, se salta")
				continue
			var link := NavigationLink3D.new()
			link.name = "NavLink_" + String(l.nombre)
			link.bidirectional = true
			add_child(link)
			link.global_position = Vector3(l.inicio[0], l.inicio[1], l.inicio[2])
			link.end_position = link.to_local(Vector3(l.fin[0], l.fin[1], l.fin[2]))
			stats["enlaces_muralla"] = stats.get("enlaces_muralla", 0) + 1
	return k


func _box_occluders() -> int:
	## una caja algo menor que el cuerpo (80 %) en los edificios de mas de 5 m de lado y 4 m de alto
	var k := 0
	var holder := Node3D.new()
	holder.name = "BoxOccluders"
	add_child(holder)
	for mi in find_children("*_Body", "MeshInstance3D", true, false):
		var box: AABB = mi.global_transform * mi.get_aabb()
		if box.size.x < 5.0 or box.size.z < 5.0 or box.size.y < 4.0:
			continue
		var oi := OccluderInstance3D.new()
		var bo := BoxOccluder3D.new()
		bo.size = box.size * Vector3(0.8, 0.85, 0.8)
		oi.occluder = bo
		holder.add_child(oi)
		oi.global_position = box.get_center() - Vector3(0, box.size.y * 0.075, 0)
		k += 1
	return k


func zone_at(p: Vector3) -> String:
	return zone_name(p)


static func zone_name(p: Vector3) -> String:
	## Blender (x, y) = Godot (x, -z). Plaza r < 48; muralla r 195-205; fuera r > 205 = ceniza.
	var x := p.x
	var y := -p.z
	var r := sqrt(x * x + y * y)
	if r < 60.0:
		return "Plaza del Portal"
	if r > 207.0:
		return "Ceniza (exterior)"
	if r > 193.0:
		return "Muralla"
	var ang := rad_to_deg(atan2(y, x))
	var district_ang := {"Mercado": 90.0, "Oficios": 0.0, "Razas": -90.0, "Clases": 180.0}
	for d in district_ang:
		var da: float = absf(wrapf(ang - district_ang[d], -180.0, 180.0))
		if da < 30.0:
			return d
	var q := ""
	q += "N" if y > 0 else "S"
	q += "E" if x > 0 else "O"
	return "Moradas " + q
