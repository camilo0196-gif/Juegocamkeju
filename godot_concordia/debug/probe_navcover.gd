extends SceneTree
## CONCORDIA - cobertura de la navegacion: malla horneada en Godot (la del mapa) frente a las -navmesh de Blender
## (desactivadas, consultadas region a region), en una rejilla de 1 m sobre la ciudad (r < 215 m).
## Por celda: primer suelo bajo un rayo vertical, su pendiente, si hay malla de Godot / de Blender a < 0,6 m en planta
## y < 0,8 m en altura, y si la malla de Godot pasa bajo un obstaculo de 0,35-2,2 m.
## Salidas: debug/out/walk/navcover.png (norte arriba) y navcover.json (por distrito y zonas de F11).
##   verde: las dos mallas  ·  cian: solo Godot  ·  magenta: solo Blender  ·  rojo: suelo sin malla
##   azul: malla de Godot bajo un obstaculo  ·  gris: edificios y muralla  ·  negro: sin colision (exterior)
## godot --headless --fixed-fps 60 --path godot_concordia -s res://debug/probe_navcover.gd

const NavReady = preload("res://scripts/nav_ready.gd")
const R := 215
const CELL := 1.0


func _initialize() -> void:
	change_scene_to_file("res://scenes/main.tscn")
	_run.call_deferred()


func _run() -> void:
	for i in 10:
		await physics_frame
	var game = current_scene.get_node("Game")
	var map: RID = game.player.get_world_3d().navigation_map
	var space: PhysicsDirectSpaceState3D = game.player.get_world_3d().direct_space_state
	await NavReady.wait(self, map)
	var blender: Array[RID] = []
	for r in current_scene.find_children("*", "NavigationRegion3D", true, false):
		if not r.is_in_group("nav_godot"):
			blender.append((r as NavigationRegion3D).get_rid())
	var n := int(2 * R / CELL)
	var img := Image.create(n, n, false, Image.FORMAT_RGB8)
	var stats := {}
	var f11 := {}
	var obst := {}
	for iy in n:
		for ix in n:
			var x := -R + (ix + 0.5) * CELL
			var by := R - (iy + 0.5) * CELL
			var z := -by
			var rr := Vector2(x, z).length()
			if rr > R:
				continue
			var hit := space.intersect_ray(PhysicsRayQueryParameters3D.create(Vector3(x, 80, z), Vector3(x, -50, z)))
			if hit.is_empty():
				img.set_pixel(ix, iy, Color(0.05, 0.05, 0.05))
				_add(f11, _f11_zone(rr, x, z, game), "sin_colision", 1, 0.0)
				continue
			var path := String(hit.collider.get_path())
			var hp: Vector3 = hit.position
			var slope := rad_to_deg(acos(clampf((hit.normal as Vector3).y, -1.0, 1.0)))
			var c := NavigationServer3D.map_get_closest_point(map, hp)
			var dh := Vector2(c.x - x, c.z - z).length()
			var over := hp.y - c.y
			var g_nav := dh < 0.6 and (absf(over) < 0.8 or over >= 2.2)
			var g_obst := dh < 0.25 and over > 0.35 and over < 2.2
			var b_nav := false
			for rid in blender:
				var bc := NavigationServer3D.region_get_closest_point(rid, hp)
				if Vector2(bc.x - x, bc.z - z).length() < 0.6 and absf(bc.y - hp.y) < 0.8:
					b_nav = true
					break
			var zone: String = game.city.zone_at(hp)
			var building := path.contains("/Buildings/") or path.contains("/Wall/")
			var col: Color
			var key: String
			if g_obst:
				col = Color(0.2, 0.35, 0.95)
				key = "obstaculo"
				var on := String(hit.collider.name)
				obst[on] = obst.get(on, 0) + 1
			elif g_nav and b_nav:
				col = Color(0.35, 0.75, 0.4)
				key = "ambas"
			elif g_nav:
				col = Color(0.3, 0.85, 0.85)
				key = "solo_godot"
			elif b_nav:
				col = Color(0.85, 0.3, 0.8)
				key = "solo_blender"
			elif building:
				col = Color(0.55, 0.55, 0.55)
				key = "edificio"
			else:
				col = Color(0.85, 0.25, 0.2)
				key = "suelo_sin_malla"
			var s: Dictionary = stats.get(zone, {})
			s[key] = s.get(key, 0) + 1
			stats[zone] = s
			_add(f11, _f11_zone(rr, x, z, game), key, 1, slope if not building else -1.0)
			img.set_pixel(ix, iy, col)
	DirAccess.make_dir_recursive_absolute("res://debug/out/walk")
	img.save_png("res://debug/out/walk/navcover.png")
	for k in f11:
		var d: Dictionary = f11[k]
		if d.has("_pend_n"):
			d["pendiente_media"] = snappedf(d._pend_sum / d._pend_n, 0.1)
			d["pendiente_p90"] = snappedf(_p90(d._pend), 0.1)
			d["m2_pendiente_mayor_36"] = d._pend.filter(func(v): return v > 36.0).size()
			d.erase("_pend_sum")
			d.erase("_pend_n")
			d.erase("_pend")
	var out := {"por_zona": stats, "zonas_f11": f11, "obstaculos_bajo_malla_godot_m2": obst}
	var f := FileAccess.open("res://debug/out/walk/navcover.json", FileAccess.WRITE)
	f.store_string(JSON.stringify(out, " "))
	f = null
	print("NAVCOVER ", JSON.stringify(out))
	quit()


func _f11_zone(rr: float, x: float, z: float, game) -> String:
	## zonas de F11: terreno de las escalinatas (anillo r 60-100 fuera de los ejes de distrito), franja junto a la
	## muralla (r 185-199), muralla (199-206), exterior (> 206)
	if rr > 206.0:
		return "exterior"
	if rr > 199.0:
		return "muralla"
	if rr > 185.0:
		return "franja_muralla"
	if rr > 60.0 and rr < 100.0 and String(game.city.zone_at(Vector3(x, 0, z))).begins_with("Moradas"):
		return "anillo_escalinatas"
	return "resto"


func _add(f11: Dictionary, zone: String, key: String, n: int, slope: float) -> void:
	var d: Dictionary = f11.get(zone, {})
	d[key] = d.get(key, 0) + n
	if slope >= 0.0:
		d["_pend_sum"] = d.get("_pend_sum", 0.0) + slope
		d["_pend_n"] = d.get("_pend_n", 0) + 1
		if not d.has("_pend"):
			d["_pend"] = []
		d._pend.append(slope)
	f11[zone] = d


func _p90(a: Array) -> float:
	if a.is_empty():
		return 0.0
	a.sort()
	return a[int(a.size() * 0.9)]
