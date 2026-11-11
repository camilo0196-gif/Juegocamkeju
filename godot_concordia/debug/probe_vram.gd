extends SceneTree
## CONCORDIA - de donde sale la memoria de texturas: base (cielo, sombras, buffers) frente a texturas de los materiales.
## xvfb-run godot --path godot_concordia --resolution 1600x900 -s res://debug/probe_vram.gd

func _initialize() -> void:
	_run.call_deferred()


func _mem() -> Dictionary:
	return {"texturas_mb": snappedf(RenderingServer.get_rendering_info(RenderingServer.RENDERING_INFO_TEXTURE_MEM_USED) / 1048576.0, 0.1),
		"video_mb": snappedf(RenderingServer.get_rendering_info(RenderingServer.RENDERING_INFO_VIDEO_MEM_USED) / 1048576.0, 0.1),
		"buffers_mb": snappedf(RenderingServer.get_rendering_info(RenderingServer.RENDERING_INFO_BUFFER_MEM_USED) / 1048576.0, 0.1)}


func _frames(n: int) -> void:
	for i in n:
		await process_frame


func _run() -> void:
	await _frames(10)
	var out := {"vacio": _mem()}
	# escena base: el mismo sol y entorno de main.tscn, sin ciudad
	var main: Node = load("res://scenes/main.tscn").instantiate()
	main.get_node("Concordia").free()
	main.get_node("Game").free()
	var cam := Camera3D.new()
	main.add_child(cam)
	root.add_child(main)
	cam.current = true
	await _frames(10)
	out["sol_cielo_sombras"] = _mem()
	main.free()
	await _frames(5)
	change_scene_to_file("res://scenes/main.tscn")
	await _frames(40)
	out["ciudad"] = _mem()
	# texturas unicas de los materiales de la ciudad
	var tex := {}
	for mi in current_scene.find_children("*", "MeshInstance3D", true, false):
		var m: Mesh = (mi as MeshInstance3D).mesh
		if m == null:
			continue
		for s in m.get_surface_count():
			var bm := m.surface_get_material(s) as BaseMaterial3D
			if bm == null:
				continue
			for p in ["albedo_texture", "normal_texture", "roughness_texture", "metallic_texture", "emission_texture", "ao_texture", "orm_texture"]:
				var t = bm.get(p)
				if t is Texture2D:
					tex[t.resource_path] = t
	var fmt := {}
	var est := 0.0
	for k in tex:
		var t: Texture2D = tex[k]
		var img := t.get_image()
		var f := img.get_format()
		var key := "fmt%d %dx%d" % [f, img.get_width(), img.get_height()]
		fmt[key] = fmt.get(key, 0) + 1
		est += img.get_data_size() / 1048576.0
	out["texturas_unicas"] = tex.size()
	out["texturas_estimado_mb"] = snappedf(est, 0.1)
	out["formatos"] = fmt
	print("VRAM ", JSON.stringify(out, " "))
	quit()
