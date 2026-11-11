extends SceneTree
## CONCORDIA - prueba de caminata (G3): el jugador de prueba recorre con fisica real las rutas de tools/walk_routes.json
## (avenidas, rondas, diagonales, callejones, callejones con escalera, plazas, puentes, arcos, escalinatas, escaleras,
## puertas de la muralla y calles de las moradas), siguiendo la malla de navegacion con su NavigationAgent3D.
## godot --headless --fixed-fps 60 --path godot_concordia --audio-driver Dummy -s res://tools/walk_test.gd -- [filtro ...]
##   filtro: tipo de ruta (p. ej. escalinata) o prefijo de nombre (p. ej. STR_MER_); sin filtro, todas.
## Sale en debug/out/walk/walk_report.json (resumen y lista de problemas, posiciones en coordenadas de Blender)
## y debug/out/walk/puntos_captura.json (para tools/capture_tour.gd -- <prefijo> @res://debug/out/walk/puntos_captura.json).
## API (documentacion 4.7, docs/reference/godot47): NavigationServer3D.map_get_path / map_get_closest_point,
## NavigationAgent3D.target_position / is_navigation_finished, CharacterBody3D.is_on_floor / get_last_slide_collision.
##
## Problemas que detecta, por tramo:
##   sin_navmesh  el punto de la calle no tiene malla de navegacion a menos de 2,5 m (en planta)
##   sin_camino   la malla no une los dos extremos (islas)
##   rodeo        el camino de la malla mide mas del doble que la recta (+8 m): la pieza no esta en la malla
##   atasco       el jugador avanza menos de 0,4 m en 2 s; se anota la altura del obstaculo de delante
##   caida        mas de 0,2 s en el aire y baja mas de 0,6 m
##   fuera_malla  el jugador queda a mas de 1,2 m (en planta) o 1,5 m por debajo de la malla (agujero en el suelo)
##   no_llega     el agente termina a mas de 1,5 m del destino

const NavReady = preload("res://scripts/nav_ready.gd")

const DT := 1.0 / 60.0
const SNAP_MAX := 2.5

var game
var player: CharacterBody3D
var map: RID
var space: PhysicsDirectSpaceState3D
var problems: Array = []
var legs := {"total": 0, "ok": 0, "metros_andados": 0.0, "segundos_simulados": 0.0, "escalones_subidos": 0}
var by_type := {}


func _initialize() -> void:
	change_scene_to_file("res://scenes/main.tscn")
	_run.call_deferred()


func _blender(p: Vector3) -> Array:
	return [snappedf(p.x, 0.1), snappedf(-p.z, 0.1), snappedf(p.y, 0.01)]


func _problem(kind: String, route: String, rtype: String, p: Vector3, detail: Dictionary = {}) -> void:
	var d := {"tipo": kind, "ruta": route, "clase_ruta": rtype, "blender": _blender(p)}
	d.merge(detail)
	problems.append(d)


func _snap(x: float, z: float) -> Dictionary:
	## punto de la malla de navegacion bajo (x, z): se baja por las capas que toca el rayo (tejados, puentes, suelo)
	## y se toma la primera cuya malla quede justo debajo; si ninguna, el punto de malla mas cercano en planta
	var y := 80.0
	var best := {}
	for i in 8:
		var q := PhysicsRayQueryParameters3D.create(Vector3(x, y, z), Vector3(x, -50.0, z))
		var hit := space.intersect_ray(q)
		if hit.is_empty():
			break
		var hp: Vector3 = hit.position
		var c := NavigationServer3D.map_get_closest_point(map, hp)
		var dh := Vector2(c.x - x, c.z - z).length()
		if dh < 0.8 and absf(c.y - hp.y) < 0.6:
			return {"p": c, "dh": dh}
		if best.is_empty() or dh < best.dh:
			best = {"p": c, "dh": dh}
		y = hp.y - 0.05
	if best.is_empty():
		var c := NavigationServer3D.map_get_closest_point(map, Vector3(x, 6.0, z))
		best = {"p": c, "dh": Vector2(c.x - x, c.z - z).length()}
	return best


func _path_len(path: PackedVector3Array) -> float:
	var l := 0.0
	for i in range(1, path.size()):
		l += path[i - 1].distance_to(path[i])
	return l


func _obstacle_height(dir: Vector3) -> float:
	## altura (sobre los pies) de lo que hay 0,6 m por delante del jugador
	var f := player.global_position + dir.normalized() * 0.6
	var hit := space.intersect_ray(PhysicsRayQueryParameters3D.create(f + Vector3(0, 3.0, 0), f - Vector3(0, 2.0, 0),
			0xFFFFFFFF, [player.get_rid()]))
	return snappedf(hit.position.y - player.global_position.y, 0.01) if hit else NAN


func _place(p: Vector3) -> void:
	player.global_position = p + Vector3(0, 0.05, 0)
	player.velocity = Vector3.ZERO
	player.agent.target_position = player.global_position


func _leg(a: Vector3, b: Vector3, route: String, rtype: String) -> void:
	legs.total += 1
	var path := NavigationServer3D.map_get_path(map, a, b, true)
	if path.is_empty() or path[path.size() - 1].distance_to(b) > 1.0:
		var end := a if path.is_empty() else path[path.size() - 1]
		_problem("sin_camino", route, rtype, b, {"desde": _blender(a), "llega_a": _blender(end)})
		_place(b)
		return
	var plen := _path_len(path)
	var straight := a.distance_to(b)
	if plen > straight * 2.0 + 8.0:
		_problem("rodeo", route, rtype, a.lerp(b, 0.5), {"recta_m": snappedf(straight, 0.1), "camino_m": snappedf(plen, 0.1)})
	player.agent.target_position = b
	var timeout := plen / 5.0 * 1.6 + 4.0
	var t := 0.0
	var win_t := 0.0
	var win_pos := player.global_position
	var air_t := 0.0
	var air_y := 0.0
	var nav_t := 0.0
	var steps0: int = player.stats.pasos_subidos
	var failed := false
	var off_reported := false
	while t < timeout:
		await physics_frame
		t += DT
		var p := player.global_position
		# caidas
		if not player.is_on_floor():
			if air_t == 0.0:
				air_y = p.y
			air_t += DT
		else:
			if air_t > 0.2 and air_y - p.y > 0.6:
				_problem("caida", route, rtype, p, {"altura_m": snappedf(air_y - p.y, 0.01)})
			air_t = 0.0
		# fuera de la malla / agujeros
		nav_t += DT
		if nav_t >= 0.5:
			nav_t = 0.0
			var c := NavigationServer3D.map_get_closest_point(map, p)
			var dh := Vector2(c.x - p.x, c.z - p.z).length()
			if (dh > 1.2 or p.y < c.y - 1.5) and not off_reported:
				off_reported = true
				_problem("fuera_malla", route, rtype, p, {"malla": _blender(c), "en_planta_m": snappedf(dh, 0.01),
					"bajo_malla_m": snappedf(c.y - p.y, 0.01)})
		if player.agent.is_navigation_finished():
			break
		# atascos
		win_t += DT
		if win_t >= 2.0:
			var moved := Vector2(p.x - win_pos.x, p.z - win_pos.z).length()
			if moved < 0.4:
				var nxt: Vector3 = player.agent.get_next_path_position()
				var dir := nxt - p
				dir.y = 0.0
				var col := player.get_last_slide_collision()
				_problem("atasco", route, rtype, p, {"obstaculo_altura_m": _obstacle_height(dir),
					"contra": String(col.get_collider().get_path()).get_slice("/", 4) + "/" + String(col.get_collider().name) if col and col.get_collider() else ""})
				failed = true
				break
			win_t = 0.0
			win_pos = p
	legs.segundos_simulados += t
	legs.escalones_subidos += player.stats.pasos_subidos - steps0
	var fin := player.global_position
	var dist := Vector2(fin.x - b.x, fin.z - b.z).length()
	if not failed and (dist > 1.5 or absf(fin.y - b.y) > 1.2):
		_problem("no_llega", route, rtype, fin, {"destino": _blender(b), "a_m": snappedf(dist, 0.01),
			"tiempo_s": snappedf(t, 0.1), "agotado": t >= timeout})
		failed = true
	if not failed:
		legs.ok += 1
		legs.metros_andados += plen
	else:
		_place(b)
		for i in 3:
			await physics_frame


func _run() -> void:
	for i in 30:
		await physics_frame
	game = current_scene.get_node("Game")
	player = game.player
	map = player.get_world_3d().navigation_map
	space = player.get_world_3d().direct_space_state
	# las regiones se sincronizan en un hilo aparte (iteraciones asincronas): la primera iteracion del mapa sale
	# vacia; se espera a la siguiente antes de pedir caminos
	var nav_frames: int = await NavReady.wait(self, map)
	print("NAV lista en %d fotogramas de fisica (iteracion %d)" % [nav_frames, NavigationServer3D.map_get_iteration_id(map)])
	var filt := OS.get_cmdline_user_args()
	var data: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://tools/walk_routes.json"))
	var t0 := Time.get_ticks_msec()
	var n := 0
	for r in data.rutas:
		var rname: String = r.nombre
		var rtype: String = r.tipo
		if not filt.is_empty():
			var keep := false
			for f in filt:
				if rtype == f or rname.begins_with(f):
					keep = true
			if not keep:
				continue
		n += 1
		var pts: Array[Vector3] = []
		for q in r.puntos:
			var s := _snap(q[0], q[1])
			if s.dh > SNAP_MAX:
				_problem("sin_navmesh", rname, rtype, Vector3(q[0], s.p.y, q[1]), {"malla_mas_cercana_m": snappedf(s.dh, 0.1)})
				continue
			pts.append(s.p)
		var bt: Dictionary = by_type.get(rtype, {"rutas": 0, "tramos": 0, "problemas": 0})
		bt.rutas += 1
		var p0 := problems.size()
		if pts.size() >= 2:
			_place(pts[0])
			for i in 3:
				await physics_frame
			for i in range(1, pts.size()):
				await _leg(pts[i - 1], pts[i], rname, rtype)
				bt.tramos += 1
		bt.problemas += problems.size() - p0
		by_type[rtype] = bt
		if n % 20 == 0:
			print("WALK %d rutas, %d tramos, %d problemas, %.0f s" % [n, legs.total, problems.size(), (Time.get_ticks_msec() - t0) / 1000.0])
	_write(n, (Time.get_ticks_msec() - t0) / 1000.0)
	quit()


func _write(n: int, wall: float) -> void:
	var counts := {}
	for p in problems:
		counts[p.tipo] = counts.get(p.tipo, 0) + 1
	legs.metros_andados = snappedf(legs.metros_andados, 1.0)
	legs.segundos_simulados = snappedf(legs.segundos_simulados, 1.0)
	var rep := {"rutas": n, "tramos": legs, "por_clase_de_ruta": by_type, "problemas_por_tipo": counts,
		"respawns": player.stats.respawns, "segundos_reales": snappedf(wall, 1.0), "problemas": problems}
	DirAccess.make_dir_recursive_absolute("res://debug/out/walk")
	var f := FileAccess.open("res://debug/out/walk/walk_report.json", FileAccess.WRITE)
	f.store_string(JSON.stringify(rep, " "))
	f = null
	# puntos para capturas: uno por problema (sin repetir a menos de 6 m), los 40 primeros
	var cap := {}
	var seen: Array = []
	for p in problems:
		var v := Vector2(p.blender[0], p.blender[1])
		var dup := false
		for s in seen:
			if v.distance_to(s) < 6.0:
				dup = true
				break
		if dup or cap.size() >= 40:
			continue
		seen.append(v)
		cap["%02d_%s" % [cap.size() + 1, p.tipo]] = [v.x, v.y, 22.0]
	f = FileAccess.open("res://debug/out/walk/puntos_captura.json", FileAccess.WRITE)
	f.store_string(JSON.stringify(cap, " "))
	f = null
	print("WALK_FIN ", JSON.stringify({"rutas": n, "tramos": legs, "problemas_por_tipo": counts, "segundos_reales": snappedf(wall, 1.0)}))
