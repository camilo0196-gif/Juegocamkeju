extends SceneTree
## CONCORDIA - lee las selecciones de la UAL (animations/ual/sanador_ual*_seleccion.glb) con el lector glTF de Godot 4.7:
## nombres, duraciones y bucle.
func _init() -> void:
	for f in ["sanador_ual1_seleccion.glb", "sanador_ual2_seleccion.glb"]:
		var doc := GLTFDocument.new()
		var st := GLTFState.new()
		var err := doc.append_from_file(ProjectSettings.globalize_path("res://../animations/ual/" + f), st)
		var scene := doc.generate_scene(st)
		var out := []
		for ap in scene.find_children("*", "AnimationPlayer", true, false):
			for a in (ap as AnimationPlayer).get_animation_list():
				var an := (ap as AnimationPlayer).get_animation(a)
				out.append("%s %.2fs%s" % [a, an.length, " BUCLE" if an.loop_mode != Animation.LOOP_NONE else ""])
		print("UALSEL ", f, " ", error_string(err), " ", out)
		scene.free()
	quit()
