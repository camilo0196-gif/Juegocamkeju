extends SceneTree
## CONCORDIA - comprobacion de los .glb y de sus importaciones (paso B del arreglo del PC, 2026-11-11).
##  1. cada archivo de assets/MANIFEST.txt existe y tiene el mismo tamano y sha256 (FileAccess.get_sha256)
##  2. cada .glb importado (la escena de .godot/imported) tiene datos en todas sus superficies: una superficie con
##     vertices declarados pero sin datos es lo que deja una importacion hecha con la GPU sin buffers (VK -10) y lo
##     que da "Size of vertex data provided (0) does not match expected (N)" al cargar
## Escribe verificacion_assets.txt en la carpeta del proyecto (o en user://). No cambia nada.
## Uso, desde la carpeta godot_concordia (sin abrir el editor):
##   Godot_v4.7.2-stable_win64.exe --headless --path . -s res://tools/verify_assets.gd

var lines: PackedStringArray = []


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	var ok_files := 0
	var bad_files: Array = []
	var glbs: Array = []
	lines.append("CONCORDIA - verificacion_assets.txt (tools/verify_assets.gd)  %s" % Time.get_datetime_string_from_system(false, true))
	lines.append("")
	lines.append("1. Archivos contra assets/MANIFEST.txt (tamano y sha256)")
	var re := RegEx.create_from_string("^\\s*(\\d+)\\s+([0-9a-f]{64})\\s+(\\S+)")
	var f := FileAccess.open("res://assets/MANIFEST.txt", FileAccess.READ)
	if f == null:
		lines.append("   falta assets/MANIFEST.txt")
	else:
		while not f.eof_reached():
			var m := re.search(f.get_line())
			if m == null:
				continue
			var path := "res://assets/" + m.get_string(3)
			if path.ends_with(".glb"):
				glbs.append(path)
			if not FileAccess.file_exists(path):
				bad_files.append("%s: FALTA" % m.get_string(3))
				continue
			var size := FileAccess.get_file_as_bytes(path).size() if path.ends_with(".glb") else int(m.get_string(1))
			var sha := FileAccess.get_sha256(path)
			if sha != m.get_string(2) or size != int(m.get_string(1)):
				bad_files.append("%s: DISTINTO (bytes %d, esperado %s)" % [m.get_string(3), size, m.get_string(1)])
			else:
				ok_files += 1
	lines.append("   iguales: %d   con problemas: %d" % [ok_files, bad_files.size()])
	for b in bad_files:
		lines.append("   - " + b)
	lines.append("")
	lines.append("2. Importaciones de los .glb (superficies sin datos)")
	var total_bad := 0
	for path in glbs:
		var ps := load(path) as PackedScene
		if ps == null:
			lines.append("   %s: NO SE PUEDE CARGAR (falta la importacion o esta rota)" % path)
			total_bad += 1
			continue
		var scene := ps.instantiate()
		var surfaces := 0
		var empty := 0
		var examples: Array = []
		var seen := {}
		for node in scene.find_children("*", "MeshInstance3D", true, false):
			var mi := node as MeshInstance3D
			if mi.mesh == null or seen.has(mi.mesh):
				continue
			seen[mi.mesh] = true
			for i in mi.mesh.get_surface_count():
				surfaces += 1
				var a := mi.mesh.surface_get_arrays(i)
				var good := a.size() > Mesh.ARRAY_VERTEX and a[Mesh.ARRAY_VERTEX] is PackedVector3Array \
						and (a[Mesh.ARRAY_VERTEX] as PackedVector3Array).size() > 0
				if not good:
					empty += 1
					if examples.size() < 4:
						examples.append(String(mi.name))
		scene.free()
		if empty > 0:
			total_bad += 1
			lines.append("   %s: %d de %d superficies VACIAS (p. ej. %s)" % [path.get_file(), empty, surfaces, ", ".join(examples)])
		else:
			lines.append("   %s: %d superficies, todas con datos" % [path.get_file(), surfaces])
	lines.append("")
	if total_bad > 0 or not bad_files.is_empty():
		lines.append("RESULTADO: HAY PROBLEMAS. Si solo fallan las importaciones (punto 2): cierra el editor, borra la")
		lines.append("carpeta .godot y ejecuta:  Godot_v4.7.2-stable_win64.exe --headless --path . --import")
		lines.append("(sin GPU no se agotan los buffers) y despues tools/build_world.gd. Si fallan los archivos (punto 1),")
		lines.append("vuelve a copiar esos .glb del paquete.")
	else:
		lines.append("RESULTADO: todo correcto.")
	var out := "res://verificacion_assets.txt"
	var fo := FileAccess.open(out, FileAccess.WRITE)
	if fo == null:
		out = "user://verificacion_assets.txt"
		fo = FileAccess.open(out, FileAccess.WRITE)
	if fo:
		fo.store_string("\n".join(lines) + "\n")
	print("\n".join(lines))
	print("VERIFY escrito en ", ProjectSettings.globalize_path(out))
	quit(1 if total_bad > 0 or not bad_files.is_empty() else 0)
