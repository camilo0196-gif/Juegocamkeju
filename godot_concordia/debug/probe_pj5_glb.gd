extends SceneTree
## CONCORDIA - lee los .glb del personaje (export/godot/personajes) con GLTFDocument de Godot 4.7 y comprueba: un
## Skeleton3D de 70 huesos con los mismos nombres, mallas con skin, materiales y animaciones (bucle de las -loop).
func _init() -> void:
	var dir := ProjectSettings.globalize_path("res://../export/godot/personajes/")
	var ref := PackedStringArray()
	for f in DirAccess.get_files_at(dir):
		if not f.ends_with(".glb"):
			continue
		var doc := GLTFDocument.new()
		var st := GLTFState.new()
		var err := doc.append_from_file(dir + f, st)
		var scene := doc.generate_scene(st)
		var sk := scene.find_children("*", "Skeleton3D", true, false)
		var names := PackedStringArray()
		if sk.size() > 0:
			for i in (sk[0] as Skeleton3D).get_bone_count():
				names.append((sk[0] as Skeleton3D).get_bone_name(i))
		if ref.is_empty():
			ref = names
		var meshes := []
		for mi in scene.find_children("*", "MeshInstance3D", true, false):
			meshes.append("%s(skin %s, %d sup)" % [mi.name, (mi as MeshInstance3D).skin != null, (mi as MeshInstance3D).mesh.get_surface_count()])
		var anims := []
		for ap in scene.find_children("*", "AnimationPlayer", true, false):
			for a in (ap as AnimationPlayer).get_animation_list():
				var an := (ap as AnimationPlayer).get_animation(a)
				anims.append("%s %.2fs %s" % [a, an.length, "bucle" if an.loop_mode != Animation.LOOP_NONE else ""])
		print("GLB %s err=%s esqueletos=%d huesos=%d mismos=%s mallas=%s anims=%s" % [f, error_string(err), sk.size(), names.size(), names == ref, meshes, anims])
		scene.free()
	quit()
