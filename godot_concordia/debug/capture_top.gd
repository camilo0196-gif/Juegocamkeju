extends SceneTree
## CONCORDIA - captura cenital (camara ortografica mirando hacia abajo) de un punto, para revisar el suelo que la
## camara isometrica no ve (huertos detras de las casas). Sin tejados: se ocultan los grupos "roofs".
## xvfb-run godot --path godot_concordia --resolution 1600x900 -s res://debug/capture_top.gd -- <nombre> <x> <y> <ancho_m>
##   (x, y en coordenadas de Blender) -> debug/out/tour/top_<nombre>.png

func _initialize() -> void:
	change_scene_to_file("res://scenes/main.tscn")
	_run.call_deferred()


func _run() -> void:
	for i in 30:
		await process_frame
	var a := OS.get_cmdline_user_args()
	var x := float(a[1])
	var z := -float(a[2])
	for r in get_nodes_in_group("roofs"):
		(r as Node3D).visible = false
	var game = current_scene.get_node("Game")
	game.player.global_position = game.ground_at(x, z) + Vector3(0, 0.05, 0)
	game.city.lod.apply_all()
	var cam := Camera3D.new()
	current_scene.add_child(cam)
	cam.projection = Camera3D.PROJECTION_ORTHOGONAL
	cam.size = float(a[3]) * 900.0 / 1600.0
	cam.global_transform = Transform3D(Basis.from_euler(Vector3(deg_to_rad(-90), 0, 0)), Vector3(x, 120, z))
	cam.far = 300.0
	cam.current = true
	for i in 12:
		await process_frame
	await RenderingServer.frame_post_draw
	root.get_texture().get_image().save_png("res://debug/out/tour/top_%s.png" % a[0])
	quit()
