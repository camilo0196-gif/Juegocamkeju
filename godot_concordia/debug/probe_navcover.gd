extends SceneTree
## CONCORDIA - mapa de cobertura de la malla de navegacion: rejilla de 1 m sobre la ciudad (r < 200 m).
## Azul: la malla pasa bajo un obstaculo de 0,35 a 2,2 m (lo que bloquea a jugador y NPC).
## Cada celda: primer suelo que toca un rayo vertical (se saltan tejados y cuerpos de edificios) y distancia en planta
## al punto de malla mas cercano. Imagen debug/out/walk/navcover.png (norte arriba) y resumen por distrito.
## godot --headless --fixed-fps 60 --path godot_concordia -s res://debug/probe_navcover.gd

const NavReady = preload("res://scripts/nav_ready.gd")

const R := 200
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
	var nav_frames: int = await NavReady.wait(self, map)
	print("NAV lista en %d fotogramas de fisica (iteracion %d)" % [nav_frames, NavigationServer3D.map_get_iteration_id(map)])
	var n := int(2 * R / CELL)
	var img := Image.create(n, n, false, Image.FORMAT_RGB8)
	var stats := {}
	var obst := {}
	for iy in n:
		for ix in n:
			var x := -R + (ix + 0.5) * CELL
			var by := R - (iy + 0.5) * CELL              # Blender y (norte arriba)
			var z := -by
			if Vector2(x, z).length() > R:
				img.set_pixel(ix, iy, Color(0, 0, 0))
				continue
			var hit := space.intersect_ray(PhysicsRayQueryParameters3D.create(Vector3(x, 80, z), Vector3(x, -50, z)))
			if hit.is_empty():
				img.set_pixel(ix, iy, Color(0.2, 0, 0.3))
				continue
			var path := String(hit.collider.get_path())
			var hp: Vector3 = hit.position
			var c := NavigationServer3D.map_get_closest_point(map, hp)
			var dh := Vector2(c.x - x, c.z - z).length()
			var dv := absf(c.y - hp.y)
			var zone: String = game.city.zone_at(hp)
			var s: Dictionary = stats.get(zone, {"celdas": 0, "malla": 0, "edificio": 0, "sin_malla": 0})
			s.celdas += 1
			var col: Color
			var over := hp.y - c.y
			if dh < 0.6 and over > 0.35 and over < 2.2:
				# la malla pasa por debajo de algo de 0,35 a 2,2 m: muro, pretil, fuente, puesto... (obstaculo en la malla)
				col = Color(0.2, 0.35, 0.95)
				s.obstaculo = s.get("obstaculo", 0) + 1
				var key := String(hit.collider.name)
				obst[key] = obst.get(key, 0) + 1
			elif dh < 0.6 and dv < 0.8 or dh < 0.6 and over >= 2.2:
				col = Color(0.35, 0.75, 0.4)
				s.malla += 1
			elif path.contains("/Buildings/") or path.contains("/Wall/"):
				col = Color(0.55, 0.55, 0.55)
				s.edificio += 1
			else:
				col = Color(0.85, 0.25, 0.2) if dh > 3.0 else Color(0.95, 0.7, 0.2)
				s.sin_malla += 1
			stats[zone] = s
			img.set_pixel(ix, iy, col)
	DirAccess.make_dir_recursive_absolute("res://debug/out/walk")
	img.save_png("res://debug/out/walk/navcover.png")
	print("NAVCOVER ", JSON.stringify(stats))
	var keys := obst.keys()
	keys.sort_custom(func(a, b): return obst[a] > obst[b])
	var top := {}
	for k in keys.slice(0, 60):
		top[k] = obst[k]
	var f := FileAccess.open("res://debug/out/walk/navcover.json", FileAccess.WRITE)
	f.store_string(JSON.stringify({"por_zona": stats, "obstaculos_sobre_malla_m2": top, "colisionadores_con_obstaculo": keys.size()}, " "))
	f = null
	quit()
