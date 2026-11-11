extends SceneTree
## CONCORDIA - huecos en la muralla: rayos horizontales hacia fuera cada 0,1 grados desde el suelo de dentro (r 186) y
## desde el camino de ronda (r 197) hasta r 245, a 0,3 / 0,9 / 1,6 m sobre el suelo. Un rayo que no toca nada es un
## hueco por el que podria salir el jugador (capsula 0,7 m de ancho). Salida: debug/out/walk/wall_gaps.json.

func _initialize() -> void:
	change_scene_to_file("res://scenes/main.tscn")
	_run.call_deferred()


func _run() -> void:
	for i in 10:
		await physics_frame
	var space: PhysicsDirectSpaceState3D = (current_scene as Node3D).get_world_3d().direct_space_state
	var gaps := []
	var rays := 0
	for start_r: float in [186.0, 197.0]:
		var a := 0.0
		while a < 360.0:
			var d := Vector3(cos(deg_to_rad(a)), 0, -sin(deg_to_rad(a)))
			var p := d * start_r
			var g := space.intersect_ray(PhysicsRayQueryParameters3D.create(p + Vector3(0, 40, 0), p - Vector3(0, 20, 0)))
			if g.is_empty():
				a += 0.1
				continue
			var gy: float = g.position.y
			if start_r > 190.0 and gy < 15.0:
				a += 0.1                                     # aqui no hay camino de ronda (torre, puerta, escalera)
				continue
			for h: float in [0.3, 0.9, 1.6]:
				rays += 1
				var o := Vector3(p.x, gy + h, p.z)
				var hit := space.intersect_ray(PhysicsRayQueryParameters3D.create(o, o + d * (245.0 - start_r)))
				if hit.is_empty():
					gaps.append({"angulo": snappedf(a, 0.1), "desde_r": start_r, "altura": h, "suelo_y": snappedf(gy, 0.01),
						"blender": [snappedf(p.x, 0.1), snappedf(-p.z, 0.1)]})
			a += 0.1
	var f := FileAccess.open("res://debug/out/walk/wall_gaps.json", FileAccess.WRITE)
	f.store_string(JSON.stringify({"rayos": rays, "huecos": gaps}, " "))
	f = null
	print("GAPS rayos ", rays, " huecos ", gaps.size())
	quit()
