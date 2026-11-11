extends SceneTree
## CONCORDIA - lista los metadatos (extras de glTF) de los nodos de una escena importada.
## godot --headless --path godot_concordia -s res://tools/list_metadata.gd -- <res://ruta.glb|.tscn> [prefijo] [clave]
##   prefijo: solo nodos cuyo nombre empieza asi (p. ej. MARKER_Bld_);  clave: solo nodos con esa clave (p. ej. interior)
## Ejemplo: ... -- res://assets/markers/glb/concordia_markers.glb MARKER_ occludes_iso


func _init() -> void:
	var args := OS.get_cmdline_user_args()
	if args.is_empty():
		print("uso: -- <res://escena> [prefijo] [clave]")
		quit(1)
		return
	var path: String = args[0]
	var prefix: String = args[1] if args.size() > 1 else ""
	var key: String = args[2] if args.size() > 2 else ""
	var root: Node = (load(path) as PackedScene).instantiate()
	var n := 0
	for node in [root] + root.find_children("*", "", true, false):
		if not node.has_meta("extras"):
			continue
		if prefix != "" and not String(node.name).begins_with(prefix):
			continue
		var ex: Dictionary = node.get_meta("extras")
		if key != "" and not ex.has(key):
			continue
		print("%s [%s] %s" % [root.get_path_to(node), node.get_class(), JSON.stringify(ex)])
		n += 1
	print("-- %d nodos con metadatos" % n)
	root.free()
	quit()
