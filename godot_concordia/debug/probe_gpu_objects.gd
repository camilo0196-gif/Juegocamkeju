extends SceneTree
## CONCORDIA - cuenta lo que va a la GPU con la ciudad cargada: nodos de malla (MeshInstance3D + MultiMeshInstance3D),
## recursos Mesh distintos, superficies, superficies de sombra aparte y una estimacion de buffers (vertices + atributos
## + indices por superficie, +2 por superficie de sombra, +1 por MultiMesh); cuantos nodos estan visibles (LOD) y,
## con el mundo horneado, cuantos chunks hay cargados. Uso: -s res://debug/probe_gpu_objects.gd [-- x z]  (Blender x, y)
func _initialize() -> void:
	change_scene_to_file("res://scenes/main.tscn")
	_run.call_deferred()


func _run() -> void:
	while current_scene == null or current_scene.get_node_or_null("Game") == null or current_scene.get_node("Game").effects == null:
		await process_frame
	var game = current_scene.get_node("Game")
	var a := OS.get_cmdline_user_args()
	if a.size() >= 2:
		var p := Vector3(float(a[0]), 0, -float(a[1]))
		game.city.ensure_loaded(p)
		for i in 3:
			await physics_frame
		game.player.global_position = game.ground_at(p.x, p.z) + Vector3(0, 0.05, 0)
		game.city.ensure_loaded(game.player.global_position)
	for i in 30:
		await process_frame
	var nodes := current_scene.find_children("*", "GeometryInstance3D", true, false)
	var meshes := {}
	var n_mesh := 0
	var visible := 0
	var vis_surf := 0
	var surf := 0
	var shadow := 0
	var mm := 0
	for gi in nodes:
		var m: Mesh = null
		if gi is MeshInstance3D:
			m = (gi as MeshInstance3D).mesh
		elif gi is MultiMeshInstance3D and (gi as MultiMeshInstance3D).multimesh:
			m = (gi as MultiMeshInstance3D).multimesh.mesh
			mm += 1
		if m == null:
			continue
		n_mesh += 1
		if (gi as Node3D).is_visible_in_tree():
			visible += 1
			vis_surf += m.get_surface_count()
		if meshes.has(m):
			continue
		meshes[m] = true
		surf += m.get_surface_count()
		if m is ArrayMesh and (m as ArrayMesh).shadow_mesh:
			shadow += (m as ArrayMesh).shadow_mesh.get_surface_count()
	var info := {"nodos_malla": n_mesh, "multimesh": mm, "mallas_distintas": meshes.size(), "superficies": surf,
		"superficies_sombra": shadow, "buffers_estimados": surf * 3 + shadow * 2 + mm,
		"nodos_visibles_lod": visible, "superficies_visibles_lod": vis_surf}
	if game.city.stream:
		info["chunks_cargados"] = game.city.stream.stats.cargados
		info["chunks_total"] = game.city.stream.chunks.size()
		info["radio_carga_m"] = game.city.stream.load_radius
	print("GPU ", JSON.stringify(info))
	quit()
