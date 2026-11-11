extends SceneTree
## CONCORDIA - que objeto hay en un pixel de una captura del recorrido (misma camara que capture_tour.gd).
## godot --path godot_concordia -s res://tools/pick.gd -- <punto del recorrido> <px> <py> [<px> <py> ...]
## Imprime el colisionador que toca el rayo y las mallas visibles cuya caja corta el rayo (las 6 mas cercanas).

func _initialize() -> void:
	change_scene_to_file("res://scenes/main.tscn")
	_run.call_deferred()


func _run() -> void:
	for i in 20:
		await process_frame
	var a := OS.get_cmdline_user_args()
	var tour = load("res://tools/capture_tour.gd")
	if a.is_empty() or not tour.POINTS.has(a[0]):
		print("uso: -- <punto de tools/capture_tour.gd POINTS> ...")
		quit(1)
		return
	var p: Array = tour.POINTS[a[0]]
	var game = current_scene.get_node("Game")
	await game.prepare_area(p[0], -p[1])
	var g: Vector3 = game.ground_at(p[0], -p[1])
	game.player.global_position = g + Vector3(0, 0.05, 0)
	game.cam_rig.zoom = p[2]
	game.cam_rig._apply(true)
	game.city.ensure_loaded(game.player.global_position)
	for i in 4:
		await process_frame
	var cam: Camera3D = game.cam_rig.cam
	var meshes: Array = current_scene.find_children("*", "MeshInstance3D", true, false)
	for k in range(1, a.size(), 2):
		var px := Vector2(float(a[k]), float(a[k + 1]))
		var o := cam.project_ray_origin(px)
		var d := cam.project_ray_normal(px)
		var hit: Dictionary = game.player.get_world_3d().direct_space_state.intersect_ray(
				PhysicsRayQueryParameters3D.create(o, o + d * 1000.0))
		var col := "nada"
		if hit:
			col = "%s @ %s (Blender %.1f, %.1f, %.1f)" % [hit.collider.get_path(), hit.position.snapped(Vector3.ONE * 0.01),
					hit.position.x, -hit.position.z, hit.position.y]
		var found := []
		for mi in meshes:
			if not mi.is_visible_in_tree():
				continue
			var box: AABB = mi.global_transform * mi.get_aabb()
			var t = box.intersects_ray(o, d)
			if t != null:
				found.append([o.distance_to(t), String(mi.get_path()).get_slice("/", 4) + "/" + String(mi.name)])
		found.sort()
		print("PICK ", px, " colision: ", col)
		for f in found.slice(0, 6):
			print("      malla ", snappedf(f[0], 0.1), " m  ", f[1])
	quit()
