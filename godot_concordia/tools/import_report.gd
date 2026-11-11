extends SceneTree
## CONCORDIA - informe de importacion (G1). Carga cada .glb importado y escribe debug/out/import_report.json:
##   nodos, mallas, triangulos, colisiones (StaticBody3D), navegacion, oclusores, LOD, metadatos (extras) por clave,
##   materiales sin textura, mallas cerradas con volumen negativo (normales invertidas probables) y edificios sin
##   colision. Tambien lista los marcadores con sus metadatos (debug/out/markers_meta.json).
## godot --headless --path godot_concordia -s res://tools/import_report.gd

var rep := {}


func _init() -> void:
	var files := []
	_scan("res://assets", files)
	files.sort()
	for f in files:
		rep[f.get_file()] = _report(f)
		print("OK ", f.get_file(), " ", rep[f.get_file()].tris, " tris")
	DirAccess.make_dir_recursive_absolute("res://debug/out")
	var fh := FileAccess.open("res://debug/out/import_report.json", FileAccess.WRITE)
	fh.store_string(JSON.stringify(rep, " "))
	fh = null
	_markers()
	quit()


func _scan(dir: String, out: Array) -> void:
	for d in DirAccess.get_directories_at(dir):
		_scan(dir.path_join(d), out)
	for f in DirAccess.get_files_at(dir):
		if f.ends_with(".glb"):
			out.append(dir.path_join(f))


func _report(path: String) -> Dictionary:
	var root: Node = (load(path) as PackedScene).instantiate()
	var r := {"nodos": 0, "mallas": 0, "tris": 0, "colisiones": 0, "navmesh": 0, "oclusores": 0, "lod": [0, 0, 0],
		"meta_claves": {}, "con_meta": 0, "sin_textura": {}, "invertidas": [], "caras_invertidas_parcial": [], "edificios": 0,
		"edificios_sin_colision": [], "skeletons": 0, "animaciones": []}
	_walk(root, r)
	# edificios: hijos directos de la raiz con metadata "building" o "landmark" (o nombres de edificio)
	for c in root.get_children():
		if c.has_meta("building") or c.has_meta("landmark") or c.has_meta("house"):
			r.edificios += 1
			if c.find_children("*", "StaticBody3D", true, false).is_empty():
				r.edificios_sin_colision.append(String(c.name))
	r.sin_textura = r.sin_textura.keys()
	r.meta_claves = r.meta_claves.keys()
	r.meta_claves.sort()
	if r.caras_invertidas_parcial.size() > 40:
		r.caras_invertidas_parcial = r.caras_invertidas_parcial.slice(0, 40) + ["... (%d)" % r.caras_invertidas_parcial.size()]
	if r.invertidas.size() > 40:
		r.invertidas = r.invertidas.slice(0, 40) + ["... (%d)" % r.invertidas.size()]
	root.free()
	return r


func _walk(n: Node, r: Dictionary) -> void:
	r.nodos += 1
	if n.has_meta("extras"):
		r.con_meta += 1
		for k in (n.get_meta("extras") as Dictionary).keys():
			r.meta_claves[k] = true
	if n is StaticBody3D:
		r.colisiones += 1
	elif n is NavigationRegion3D:
		r.navmesh += 1
	elif n is OccluderInstance3D:
		r.oclusores += 1
	elif n is Skeleton3D:
		r.skeletons += 1
	elif n is AnimationPlayer:
		r.animaciones = (n as AnimationPlayer).get_animation_list()
	if n is MeshInstance3D:
		var mi := n as MeshInstance3D
		r.mallas += 1
		if mi.has_meta("lod_level"):
			r.lod[int(mi.get_meta("lod_level"))] += 1
		if mi.mesh:
			for i in mi.mesh.get_surface_count():
				var arr := mi.mesh.surface_get_arrays(i)
				var idx: PackedInt32Array = arr[Mesh.ARRAY_INDEX]
				var v: PackedVector3Array = arr[Mesh.ARRAY_VERTEX]
				var nt := idx.size() / 3 if idx.size() > 0 else v.size() / 3
				r.tris += nt
				var m := mi.mesh.surface_get_material(i)
				if m is BaseMaterial3D and (m as BaseMaterial3D).albedo_texture == null:
					r.sin_textura[m.resource_name] = true
			var inv := _inverted_ratio(mi.mesh)
			if inv > 0.5:
				r.invertidas.append("%s (%d%%)" % [mi.name, int(inv * 100)])
			elif inv > 0.05:
				r.caras_invertidas_parcial.append("%s (%d%%)" % [mi.name, int(inv * 100)])
	for c in n.get_children():
		_walk(c, r)


func _inverted_ratio(mesh: Mesh) -> float:
	## fraccion de triangulos cuya normal geometrica no coincide con la normal guardada. Godot guarda las caras
	## delanteras en sentido horario (comprobado con BoxMesh: (b-a)x(c-a) es opuesta a la normal en una malla
	## correcta), asi que una cara bien orientada da dot < 0; dot > 0 = cara invertida respecto a su normal.
	var bad := 0
	var tot := 0
	for i in mesh.get_surface_count():
		var arr := mesh.surface_get_arrays(i)
		var v: PackedVector3Array = arr[Mesh.ARRAY_VERTEX]
		var nr: PackedVector3Array = arr[Mesh.ARRAY_NORMAL]
		var idx: PackedInt32Array = arr[Mesh.ARRAY_INDEX]
		if nr.is_empty() or idx.is_empty():
			continue
		for t in range(0, idx.size(), 3):
			var a := v[idx[t]]
			var g := (v[idx[t + 1]] - a).cross(v[idx[t + 2]] - a)
			if g.length_squared() < 1e-12:
				continue
			var nn := nr[idx[t]] + nr[idx[t + 1]] + nr[idx[t + 2]]
			tot += 1
			if g.dot(nn) > 0.0:
				bad += 1
	return float(bad) / tot if tot > 0 else 0.0


func _markers() -> void:
	var root: Node = (load("res://assets/markers/glb/concordia_markers.glb") as PackedScene).instantiate()
	var out := {}
	var fam := {}
	for c in root.get_children():
		var ex = c.get_meta("extras", {})
		var t: Transform3D = c.transform
		out[String(c.name)] = {"pos": [snappedf(t.origin.x, 0.01), snappedf(t.origin.y, 0.01), snappedf(t.origin.z, 0.01)],
			"frente": [snappedf(-t.basis.z.x, 0.001), snappedf(-t.basis.z.y, 0.001), snappedf(-t.basis.z.z, 0.001)],
			"meta": ex}
		var parts := String(c.name).split("_")
		var key := parts[1] if parts.size() > 1 else String(c.name)
		fam[key] = fam.get(key, 0) + 1
	var fh := FileAccess.open("res://debug/out/markers_meta.json", FileAccess.WRITE)
	fh.store_string(JSON.stringify({"familias": fam, "marcadores": out}, " "))
	print("MARCADORES ", out.size(), " familias ", fam.size())
	root.free()
