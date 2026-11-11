extends SceneTree
func _init():
	var ps: PackedScene = load("res://assets/markers/glb/concordia_markers.glb")
	var root = ps.instantiate()
	var n = 0
	for c in root.get_children():
		if n < 3 or c.name.begins_with("MARKER_Bld_Posada") or c.name == "MARKER_Faro":
			print(c.name, " ", c.get_class(), " meta=", c.get_meta_list())
			for k in c.get_meta_list():
				print("   ", k, " = ", c.get_meta(k))
		n += 1
	print("hijos ", n)
	quit()
