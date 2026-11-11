extends SceneTree
## CONCORDIA - mundo horneado para el juego (arreglo del PC del usuario: VK_ERROR_TOO_MANY_OBJECTS, 2026-11-11).
##
## Lee la ciudad montada con los .glb importados (res://scenes/concordia_glb.tscn, de tools/build_city.gd) y genera:
##   res://world/chunks/c_<x>_<z>.scn  un chunk por celda de 50 m (la rejilla de los chunks de terreno) con:
##       - una MeshInstance3D por mascara de LOD y sombra, con UNA superficie por material (todo lo estatico fusionado)
##       - MultiMeshInstance3D para las mallas repetidas (>= MM_MIN copias iguales en el chunk: barriles, cajas,
##         baldosas, farolillos, ventanas, almenas...)
##       - tejados aparte, fusionados por edificio (grupo "roofs", metadata "building"), para poder ocultarlos
##       - las colisiones (StaticBody3D) y los oclusores de caja de los cuerpos grandes
##   res://world/special.scn   piezas que siguen sueltas y siempre cargadas: occludes_iso (Salon de las Hazanas,
##       muralla SE), haces (FARO_Beam, Crisol), todo FARO_*, Obelisco (marcas fusionadas por piso), rueda de la
##       Carpinteria y piedras flotantes del Crisol (se mueven)
##   res://world/logic.scn     marcadores, enlaces, volumenes de interior y nodos con metadata (sin mallas)
##   res://world/materials/    biblioteca de materiales compartida (con los cambios de Godot ya aplicados: terreno
##       por mascaras, velo, agua, estandartes, ascuas, vidrios, Obelisco)
##   res://world/meshes/       mallas de las MultiMesh
##   res://world/world_index.json  indice de chunks (caja, zona, triangulos por LOD) y lista de materiales
##   res://scenes/concordia.tscn y res://scenes/main.tscn  la ciudad del juego (scripts/city.gd la carga por
##       distancia con scripts/world_streamer.gd)
##
## Mascara de LOD (bit 0 = LOD0, bit 1 = LOD1, bit 2 = LOD2): misma regla que scripts/lod_manager.gd por unidad
## (edificio o chunk de terreno) pero cambiando de nivel por chunk.
##
## No toca los .glb ni los .blend: solo lee las escenas importadas. Si alguna malla importada llega vacia (vease
## TEST_REPORT.md, "mallas vacias") se detiene y escribe la lista en world/build_report.json.
##
## Uso, desde la carpeta godot_concordia (sin abrir el editor; usa el rasterizador vacio, sin GPU):
##   Godot_v4.7.2-stable_win64.exe --headless --path . -s res://tools/build_world.gd
## API verificada en docs/reference/godot47 (class_mesh, class_arraymesh, class_multimesh, class_resourcesaver).

const SRC_SCENE := "res://scenes/concordia_glb.tscn"
const OUT := "res://world"
const CHUNK := 50.0
const MM_MIN := 8                 # copias de la misma malla (misma mascara y sombra) en un chunk para usar MultiMesh
const SMALL := 3.0                # diagonal de caja < 3 m = detalle (oculto en LOD2), igual que lod_manager.gd
const SPECIAL_PREFIX := ["OBELISK_", "FARO_", "CRISOL_FloatStone", "Taller_Carpinteria_WATERWHEEL"]
const BEAM_MATS := ["MAT_Faro_Beam", "MAT_Beam_Godot"]
const FMT_KEEP := (1 << 25) - 1   # bits de formato y de formato de canales propios

var city: Node3D
var lib := {}                     # huella -> material de la biblioteca
var lib_of := {}                  # id de instancia original -> material de la biblioteca
var lib_paths: Array = []
var mm_lib := {}                  # malla original -> ruta guardada
var chunks := {}                  # Vector2i -> {items, bodies, boxes}
var special: Array = []
var trace := ""                   # -- trazar=<texto>: escribe como se clasifica cada malla cuyo nombre lo contenga
var rep := {"ocultas_sin_fundir": 0, "no_triangulos": 0, "unidades": 0, "unidades_grandes": 0}
var _t0 := 0


func _initialize() -> void:
	_t0 = Time.get_ticks_msec()
	var ps := load(SRC_SCENE) as PackedScene
	if ps == null:
		printerr("BUILD_WORLD no se pudo cargar ", SRC_SCENE, " (ejecuta antes tools/build_city.gd)")
		quit(1)
		return
	city = ps.instantiate() as Node3D
	city.set_script(null)
	root.add_child(city)
	_run.call_deferred()


func _run() -> void:
	for a in OS.get_cmdline_user_args():
		if String(a).begins_with("trazar="):
			trace = String(a).substr(7)
	DirAccess.make_dir_recursive_absolute(OUT + "/chunks")
	DirAccess.make_dir_recursive_absolute(OUT + "/materials")
	DirAccess.make_dir_recursive_absolute(OUT + "/meshes")
	var bad := _check_empty()
	if not bad.is_empty():
		rep["error"] = "mallas importadas vacias: borra .godot/imported y reimporta en modo --headless (LEEME)"
		rep["mallas_vacias_por_glb"] = bad
		_write_report()
		printerr("BUILD_WORLD ERROR mallas vacias: ", JSON.stringify(bad))
		quit(2)
		return
	# cambios de material de Godot (los mismos que hacian materials_fix.gd y effects.gd en tiempo de ejecucion)
	var mf = load("res://scripts/materials_fix.gd").new()
	var mf_rep: Dictionary = mf.apply(city)
	rep["materiales_godot"] = {"terreno_superficies": mf_rep.get("terreno_superficies", 0), "haces": mf_rep.get("haces", [])}
	var fx_script = load("res://scripts/effects.gd")
	rep["efectos_superficies"] = fx_script.convert_surfaces(city)
	var fx: Node = fx_script.new()
	_remap_materials(fx)
	fx.free()
	print("BUILD_WORLD materiales en biblioteca: ", lib_paths.size(), "  (", Time.get_ticks_msec() - _t0, " ms)")
	_collect()
	_bodies()
	var index := {"version": 1, "fecha": Time.get_datetime_string_from_system(false, true), "chunk_m": CHUNK,
		"mm_min": MM_MIN, "materiales": lib_paths, "chunks": []}
	var tot := {"nodos": [0, 0, 0], "superficies": [0, 0, 0], "tris": [0, 0, 0], "multimesh": 0, "instancias_mm": 0,
		"tejados": 0, "cuerpos": 0, "oclusores": 0, "bytes": 0}
	var keys := chunks.keys()
	keys.sort()
	var city_script = load("res://scripts/city.gd")
	for k in keys:
		var info := _build_chunk(k)
		if info.is_empty():
			continue
		info["zona"] = city_script.zone_name(Vector3(info.centro[0], 0, info.centro[1]))
		index.chunks.append(info)
		for l in 3:
			tot.nodos[l] += info.nodos[l]
			tot.superficies[l] += info.superficies[l]
			tot.tris[l] += info.tris[l]
		for f in ["multimesh", "instancias_mm", "tejados", "cuerpos", "oclusores", "bytes"]:
			tot[f] += info[f]
	var sp := _build_special()
	_build_logic()
	_build_scenes()
	rep["chunks"] = index.chunks.size()
	rep["totales_chunks"] = tot
	rep["especiales"] = sp
	rep["ms"] = Time.get_ticks_msec() - _t0
	index["totales"] = tot
	index["especiales"] = sp
	var f := FileAccess.open(OUT + "/world_index.json", FileAccess.WRITE)
	f.store_string(JSON.stringify(index, " "))
	f = null
	_write_report()
	print("BUILD_WORLD ", JSON.stringify(rep))
	quit()


func _write_report() -> void:
	var f := FileAccess.open(OUT + "/build_report.json", FileAccess.WRITE)
	if f:
		f.store_string(JSON.stringify(rep, " "))


# ------------------------------------------------------------------------------------------------ comprobacion

func _check_empty() -> Dictionary:
	## superficies con numero de vertices > 0 pero sin datos (lo que deja una reimportacion con la GPU agotada)
	var bad := {}
	for node in city.find_children("*", "MeshInstance3D", true, false):
		var mi := node as MeshInstance3D
		if mi.mesh == null:
			continue
		for i in mi.mesh.get_surface_count():
			var a := mi.mesh.surface_get_arrays(i)
			var ok := a.size() > Mesh.ARRAY_VERTEX and a[Mesh.ARRAY_VERTEX] is PackedVector3Array \
					and (a[Mesh.ARRAY_VERTEX] as PackedVector3Array).size() > 0
			if not ok:
				var src := _source_of(mi)
				if not bad.has(src):
					bad[src] = {"superficies": 0, "ejemplos": []}
				bad[src].superficies += 1
				if bad[src].ejemplos.size() < 5:
					bad[src].ejemplos.append(String(mi.name))
	return bad


func _source_of(n: Node) -> String:
	var p := n
	while p and p.get_parent() and p.get_parent().get_parent() != city:
		p = p.get_parent()
	return p.scene_file_path if p and p.scene_file_path != "" else String(p.name) if p else "?"


# ------------------------------------------------------------------------------------------------ materiales

func _fingerprint(m: Material) -> String:
	var parts := [m.get_class(), m.resource_name]
	for p in m.get_property_list():
		if not (int(p.usage) & PROPERTY_USAGE_STORAGE):
			continue
		var nm: String = p.name
		if nm in ["resource_path", "resource_name", "resource_local_to_scene", "script", "resource_scene_unique_id"]:
			continue
		var v = m.get(nm)
		if v is Resource:
			var rp: String = (v as Resource).resource_path
			v = rp if rp != "" and not rp.contains("::") else "obj%d" % (v as Resource).get_instance_id()
		parts.append(nm + "=" + str(v))
	return "|".join(parts).md5_text()


func _lib(m: Material, fx: Node) -> Material:
	if m == null:
		return null
	if lib_of.has(m.get_instance_id()):
		return lib_of[m.get_instance_id()]
	if m.resource_name == "MAT_Beam_Godot":           # lo rehace materials_fix.gd en cada partida
		return m
	if m.next_pass:
		m.next_pass = _lib(m.next_pass, fx)
	fx.register_material(m)
	var fp := _fingerprint(m)
	if not lib.has(fp):
		var safe := m.resource_name if m.resource_name != "" else m.get_class()
		safe = RegEx.create_from_string("[^A-Za-z0-9_]").sub(safe, "_", true)
		var path := "%s/materials/%03d_%s.tres" % [OUT, lib_paths.size(), safe]
		var err := ResourceSaver.save(m, path)
		if err != OK:
			push_error("no se pudo guardar " + path + ": " + error_string(err))
		m.take_over_path(path)
		lib[fp] = m
		lib_paths.append(path)
	lib_of[m.get_instance_id()] = lib[fp]
	return lib[fp]


func _remap_materials(fx: Node) -> void:
	## todas las superficies pasan a usar la biblioteca; sin mallas de sombra aparte (mitad de buffers en la GPU)
	var done := {}
	for node in city.find_children("*", "MeshInstance3D", true, false):
		var mi := node as MeshInstance3D
		var m := mi.mesh
		if m == null:
			continue
		if not done.has(m):
			done[m] = true
			if m is ArrayMesh:
				(m as ArrayMesh).shadow_mesh = null
			for i in m.get_surface_count():
				m.surface_set_material(i, _lib(m.surface_get_material(i), fx))
		for i in m.get_surface_count():
			var o := mi.get_surface_override_material(i)
			if o:
				mi.set_surface_override_material(i, _lib(o, fx))
		if mi.material_override:
			mi.material_override = _lib(mi.material_override, fx)


# ------------------------------------------------------------------------------------------------ clasificacion

func _in_group_up(n: Node, g: String) -> bool:
	var p := n
	while p and p != city:
		if p.is_in_group(g):
			return true
		p = p.get_parent()
	return false


func _is_special(mi: MeshInstance3D) -> bool:
	var nm := String(mi.name)
	for pre in SPECIAL_PREFIX:
		if nm.begins_with(pre):
			return true
	if _in_group_up(mi, "occludes_iso"):
		return true
	if nm.contains("_LOD"):
		var sib := mi.get_parent().get_node_or_null(NodePath(nm.get_slice("_LOD", 0)))
		if sib and sib.is_in_group("occludes_iso"):
			return true
	if mi.mesh:
		for i in mi.mesh.get_surface_count():
			var mat := mi.get_active_material(i)
			if mat and mat.resource_name in BEAM_MATS:
				return true
	return false


func _box(mi: MeshInstance3D) -> AABB:
	return mi.global_transform * mi.get_aabb()


func _key(p: Vector3) -> Vector2i:
	return Vector2i(floori(p.x / CHUNK), floori(p.z / CHUNK))


func _chunk(k: Vector2i) -> Dictionary:
	if not chunks.has(k):
		chunks[k] = {"items": [], "bodies": [], "boxes": []}
	return chunks[k]


func _collect() -> void:
	for group_name in ["Terrain", "Wall", "Buildings"]:
		var g := city.get_node_or_null(group_name)
		if g == null:
			continue
		for inst in g.get_children():
			var by_base := {}
			var units: Array = []
			for c in inst.get_children():
				if c is MeshInstance3D and String(c.name).contains("_LOD"):
					var base := String(c.name).get_slice("_LOD", 0)
					if not by_base.has(base):
						by_base[base] = []
					by_base[base].append(c)
				else:
					units.append([c])
			for base in by_base:
				units.append(by_base[base])
			for u in units:
				_unit(u, String(inst.name))
	# oclusores de caja (antes en city.gd): cuerpos de mas de 5 m de lado y 4 m de alto
	for node in city.find_children("*_Body", "MeshInstance3D", true, false):
		var mi := node as MeshInstance3D
		if not mi.is_visible_in_tree():
			continue
		var b := _box(mi)
		if b.size.x < 5.0 or b.size.z < 5.0 or b.size.y < 4.0:
			continue
		_chunk(_key(b.get_center())).boxes.append(b)


func _unit(nodes: Array, src: String) -> void:
	var meshes: Array = []
	for n in nodes:
		if n is MeshInstance3D:
			meshes.append(n)
		meshes += n.find_children("*", "MeshInstance3D", true, false)
	var keep: Array = []
	for mi in meshes:
		if _is_special(mi):
			special.append(mi)
		elif not (mi as MeshInstance3D).is_visible_in_tree() or (mi as MeshInstance3D).mesh == null:
			rep.ocultas_sin_fundir += 1
		else:
			keep.append(mi)
	if keep.is_empty():
		return
	rep.unidades += 1
	var ubox := AABB()
	var lods := {0: 0, 1: 0, 2: 0}
	var smalls := 0
	for i in keep.size():
		var b := _box(keep[i])
		ubox = b if i == 0 else ubox.merge(b)
		if keep[i].has_meta("lod_level"):
			lods[int(keep[i].get_meta("lod_level"))] += 1
		elif b.size.length() < SMALL:
			smalls += 1
	var managed: bool = lods[1] > 0 or lods[2] > 0 or smalls > 0
	var has2: bool = lods[2] > 0
	var big := ubox.size.x > CHUNK * 1.5 or ubox.size.z > CHUNK * 1.5
	if big:
		rep.unidades_grandes += 1
	var ukey := _key(ubox.get_center())
	var uname := src + "/" + String(nodes[0].name).get_slice("_LOD", 0)
	for mi in keep:
		var mask := 7
		if managed:
			if mi.has_meta("lod_level"):
				var k := int(mi.get_meta("lod_level"))
				mask = 0
				for lv in 3:
					var show := lv
					while show > 0 and lods[show] == 0:
						show -= 1
					if show == k:
						mask |= 1 << lv
			elif _box(mi).size.length() < SMALL:
				mask = 3
			else:
				mask = 3 if has2 else 7
		if mask == 0:
			continue
		var k2 := _key(_box(mi).get_center()) if big else ukey
		if trace != "" and String(mi.name).contains(trace):
			print("TRAZA ", mi.name, " unidad=", uname, " chunk=", k2, " mascara=", mask, " tejado=", _in_group_up(mi, "roofs"),
				" lod=", mi.get_meta("lod_level", -1), " caja=", _box(mi))
		_chunk(k2).items.append({"mi": mi, "mask": mask, "roof": _in_group_up(mi, "roofs"), "unit": uname})


func _bodies() -> void:
	for group_name in ["Terrain", "Wall", "Buildings"]:
		var g := city.get_node_or_null(group_name)
		if g == null:
			continue
		for node in g.find_children("*", "StaticBody3D", true, false):
			var body := node as StaticBody3D
			var box := AABB(body.global_position, Vector3.ZERO)
			for cs in body.get_children():
				if cs is CollisionShape3D and (cs as CollisionShape3D).shape is ConcavePolygonShape3D:
					var faces: PackedVector3Array = ((cs as CollisionShape3D).shape as ConcavePolygonShape3D).get_faces()
					var xf := (cs as CollisionShape3D).global_transform
					if not faces.is_empty():
						box = AABB(xf * faces[0], Vector3.ZERO)
						for p in faces:
							box = box.expand(xf * p)
			_chunk(_key(box.get_center())).bodies.append(body)


# ------------------------------------------------------------------------------------------------ fusion

func _acc_add(acc: Dictionary, src_mesh: Mesh, s: int, mat: Material, xf: Transform3D) -> int:
	var mesh := src_mesh as ArrayMesh
	if mesh == null:
		rep.no_triangulos += 1
		return 0
	if mesh.surface_get_primitive_type(s) != Mesh.PRIMITIVE_TRIANGLES:
		rep.no_triangulos += 1
		return 0
	var a := mesh.surface_get_arrays(s)
	if a.size() <= Mesh.ARRAY_INDEX or not (a[Mesh.ARRAY_VERTEX] is PackedVector3Array):
		return 0
	var verts: PackedVector3Array = a[Mesh.ARRAY_VERTEX]
	if verts.is_empty():
		return 0
	var fmt: int = mesh.surface_get_format(s)
	var kf: int = (fmt & FMT_KEEP & ~Mesh.ARRAY_FORMAT_INDEX) | (fmt & Mesh.ARRAY_FLAG_COMPRESS_ATTRIBUTES)
	var key := "%d_%d" % [mat.get_instance_id() if mat else 0, kf]
	if not acc.has(key):
		acc[key] = {"mat": mat, "fmt": kf, "nv": 0, "v": [], "n": [], "t": [], "c": [], "uv": [], "uv2": [],
			"cu": [[], [], [], []], "i": []}
	var e: Dictionary = acc[key]
	var base: int = e.nv
	e.nv = base + verts.size()
	e.v.append(xf * verts)
	var det := xf.basis.determinant()
	var ortho := absf(absf(det) - 1.0) < 0.001 and xf.basis.orthonormalized().is_equal_approx(xf.basis)
	if a[Mesh.ARRAY_NORMAL] is PackedVector3Array:
		var nb := Transform3D(xf.basis.inverse().transposed(), Vector3.ZERO)
		var nn: PackedVector3Array = nb * (a[Mesh.ARRAY_NORMAL] as PackedVector3Array)
		if not ortho:
			for j in nn.size():
				nn[j] = nn[j].normalized()
		e.n.append(nn)
	if a[Mesh.ARRAY_TANGENT] is PackedFloat32Array:
		var t: PackedFloat32Array = a[Mesh.ARRAY_TANGENT]
		var sgn := -1.0 if det < 0.0 else 1.0
		for j in range(0, t.size(), 4):
			var v := (xf.basis * Vector3(t[j], t[j + 1], t[j + 2])).normalized()
			t[j] = v.x
			t[j + 1] = v.y
			t[j + 2] = v.z
			t[j + 3] = t[j + 3] * sgn
		e.t.append(t)
	if a[Mesh.ARRAY_COLOR] is PackedColorArray:
		e.c.append(a[Mesh.ARRAY_COLOR])
	if a[Mesh.ARRAY_TEX_UV] is PackedVector2Array:
		e.uv.append(a[Mesh.ARRAY_TEX_UV])
	if a[Mesh.ARRAY_TEX_UV2] is PackedVector2Array:
		e.uv2.append(a[Mesh.ARRAY_TEX_UV2])
	for c in 4:
		var ca = a[Mesh.ARRAY_CUSTOM0 + c]
		if ca != null:
			e.cu[c].append(ca)
	var idx: PackedInt32Array
	if a[Mesh.ARRAY_INDEX] is PackedInt32Array and (a[Mesh.ARRAY_INDEX] as PackedInt32Array).size() > 0:
		idx = a[Mesh.ARRAY_INDEX]
	else:
		idx = PackedInt32Array()
		idx.resize(verts.size())
		for j in verts.size():
			idx[j] = j
	if det < 0.0:
		for j in range(0, idx.size() - 2, 3):
			var tmp := idx[j + 1]
			idx[j + 1] = idx[j + 2]
			idx[j + 2] = tmp
	if base > 0:
		for j in idx.size():
			idx[j] += base
	e.i.append(idx)
	return idx.size() / 3


func _acc_mesh(acc: Dictionary) -> ArrayMesh:
	var am := ArrayMesh.new()
	var keys := acc.keys()
	keys.sort_custom(func(x, y): return String(acc[x].mat.resource_name if acc[x].mat else "") < String(acc[y].mat.resource_name if acc[y].mat else ""))
	for k in keys:
		var e: Dictionary = acc[k]
		var arrays := []
		arrays.resize(Mesh.ARRAY_MAX)
		arrays[Mesh.ARRAY_VERTEX] = _cat(e.v, PackedVector3Array())
		if not e.n.is_empty():
			arrays[Mesh.ARRAY_NORMAL] = _cat(e.n, PackedVector3Array())
		if not e.t.is_empty():
			arrays[Mesh.ARRAY_TANGENT] = _cat(e.t, PackedFloat32Array())
		if not e.c.is_empty():
			arrays[Mesh.ARRAY_COLOR] = _cat(e.c, PackedColorArray())
		if not e.uv.is_empty():
			arrays[Mesh.ARRAY_TEX_UV] = _cat(e.uv, PackedVector2Array())
		if not e.uv2.is_empty():
			arrays[Mesh.ARRAY_TEX_UV2] = _cat(e.uv2, PackedVector2Array())
		for c in 4:
			if not e.cu[c].is_empty():
				var first_part = e.cu[c][0]
				arrays[Mesh.ARRAY_CUSTOM0 + c] = _cat(e.cu[c], PackedByteArray() if first_part is PackedByteArray else PackedFloat32Array())
		arrays[Mesh.ARRAY_INDEX] = _cat(e.i, PackedInt32Array())
		var flags := 0
		for c in 4:
			var sh: int = Mesh.ARRAY_FORMAT_CUSTOM_BASE + c * Mesh.ARRAY_FORMAT_CUSTOM_BITS
			flags |= ((int(e.fmt) >> sh) & Mesh.ARRAY_FORMAT_CUSTOM_MASK) << sh
		flags |= int(e.fmt) & Mesh.ARRAY_FLAG_COMPRESS_ATTRIBUTES
		am.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, arrays, [], {}, flags)
		am.surface_set_material(am.get_surface_count() - 1, e.mat)
	return am


func _cat(parts: Array, out: Variant) -> Variant:
	## concatena los trozos una sola vez (los arreglos empaquetados se copian al asignarlos: no se acumulan en el
	## diccionario uno a uno)
	for p in parts:
		out.append_array(p)
	return out


func _add_items(acc: Dictionary, items: Array, inv: Transform3D) -> int:
	var tris := 0
	for it in items:
		var mi: MeshInstance3D = it.mi
		var xf := inv * mi.global_transform
		for s in mi.mesh.get_surface_count():
			tris += _acc_add(acc, mi.mesh, s, mi.get_active_material(s), xf)
	return tris


func _plain_materials(mi: MeshInstance3D) -> bool:
	if mi.material_override:
		return false
	for s in mi.mesh.get_surface_count():
		if mi.get_surface_override_material(s):
			return false
	return true


func _own(n: Node, owner_node: Node) -> void:
	for c in n.get_children():
		c.owner = owner_node
		_own(c, owner_node)


func _build_chunk(k: Vector2i) -> Dictionary:
	var ch: Dictionary = chunks[k]
	var origin := Vector3((k.x + 0.5) * CHUNK, 0.0, (k.y + 0.5) * CHUNK)
	var inv := Transform3D(Basis(), -origin)
	var r := Node3D.new()
	r.name = "Chunk_%d_%d" % [k.x, k.y]
	r.position = origin
	var info := {"archivo": "", "clave": [k.x, k.y], "centro": [origin.x, origin.z], "nodos": [0, 0, 0],
		"superficies": [0, 0, 0], "tris": [0, 0, 0], "multimesh": 0, "instancias_mm": 0, "tejados": 0,
		"cuerpos": 0, "oclusores": 0, "bytes": 0}
	var gbox := AABB()
	var first := true
	# 1. tejados por edificio
	var roofs := {}
	var rest: Array = []
	for it in ch.items:
		var b := _box(it.mi)
		gbox = b if first else gbox.merge(b)
		first = false
		if it.roof:
			var rk := "%s|%d|%d" % [it.unit, it.mask, it.mi.cast_shadow]
			if not roofs.has(rk):
				roofs[rk] = []
			roofs[rk].append(it)
		else:
			rest.append(it)
	for rk in roofs:
		var its: Array = roofs[rk]
		var acc := {}
		var tris := _add_items(acc, its, inv)
		if acc.is_empty():
			continue
		var mi := MeshInstance3D.new()
		var unit: String = its[0].unit
		mi.name = "ROOF_" + unit.get_file().validate_node_name() + "_M%d" % its[0].mask
		mi.mesh = _acc_mesh(acc)
		mi.cast_shadow = its[0].mi.cast_shadow
		mi.set_meta("lod_mask", its[0].mask)
		mi.set_meta("building", unit)
		mi.add_to_group("roofs", true)
		r.add_child(mi, true)
		_count(info, its[0].mask, mi.mesh.get_surface_count(), tris)
		info.tejados += 1
	# 2. repetidas -> MultiMesh
	var by_mesh := {}
	for it in rest:
		if not _plain_materials(it.mi):
			continue
		var mk := "%d|%d|%d" % [it.mi.mesh.get_instance_id(), it.mask, it.mi.cast_shadow]
		if not by_mesh.has(mk):
			by_mesh[mk] = []
		by_mesh[mk].append(it)
	var in_mm := {}
	for mk in by_mesh:
		var its: Array = by_mesh[mk]
		if its.size() < MM_MIN:
			continue
		var src: Mesh = its[0].mi.mesh
		var mm := MultiMesh.new()
		mm.transform_format = MultiMesh.TRANSFORM_3D
		mm.mesh = _mm_mesh(src)
		var tris := 0
		var mbox := AABB()
		# sin GPU (--headless) el servidor de render no guarda las transformaciones de las instancias: se guardan
		# en la metadata mm_xforms (12 floats por instancia: ejes x, y, z y origen) y world_streamer.gd las pone al
		# cargar el chunk (setup_multimeshes)
		var xforms := PackedFloat32Array()
		for i in its.size():
			var ixf := inv * (its[i].mi as MeshInstance3D).global_transform
			xforms.append_array([ixf.basis.x.x, ixf.basis.x.y, ixf.basis.x.z, ixf.basis.y.x, ixf.basis.y.y, ixf.basis.y.z,
				ixf.basis.z.x, ixf.basis.z.y, ixf.basis.z.z, ixf.origin.x, ixf.origin.y, ixf.origin.z])
			mbox = ixf * src.get_aabb() if i == 0 else mbox.merge(ixf * src.get_aabb())
			in_mm[its[i]] = true
		# la caja de recorte de una MultiMesh no se calcula sola: sin custom_aabb queda vacia y se recorta entera
		mm.custom_aabb = mbox
		for s in src.get_surface_count():
			tris += _surface_tris(src, s)
		var mmi := MultiMeshInstance3D.new()
		mmi.name = "MM_" + String(its[0].mi.name).get_slice("_LOD", 0).validate_node_name() + "_M%d" % its[0].mask
		mmi.multimesh = mm
		mmi.set_meta("mm_xforms", xforms)
		mmi.cast_shadow = its[0].mi.cast_shadow
		mmi.set_meta("lod_mask", its[0].mask)
		r.add_child(mmi, true)
		_count(info, its[0].mask, src.get_surface_count(), tris * its.size())
		info.multimesh += 1
		info.instancias_mm += its.size()
	# 3. el resto: una malla por mascara y sombra, una superficie por material
	var groups := {}
	for it in rest:
		if in_mm.has(it):
			continue
		var gk := "%d|%d" % [it.mask, it.mi.cast_shadow]
		if not groups.has(gk):
			groups[gk] = []
		groups[gk].append(it)
	for gk in groups:
		var its: Array = groups[gk]
		var acc := {}
		var tris := _add_items(acc, its, inv)
		if acc.is_empty():
			continue
		var mi := MeshInstance3D.new()
		mi.name = "Merged_M%d_S%d" % [its[0].mask, its[0].mi.cast_shadow]
		mi.mesh = _acc_mesh(acc)
		mi.cast_shadow = its[0].mi.cast_shadow
		mi.set_meta("lod_mask", its[0].mask)
		r.add_child(mi, true)
		_count(info, its[0].mask, mi.mesh.get_surface_count(), tris)
	# 4. colisiones y oclusores
	if not ch.bodies.is_empty():
		var bh := Node3D.new()
		bh.name = "Colisiones"
		r.add_child(bh)
		for body in ch.bodies:
			var b2 := (body as StaticBody3D).duplicate() as StaticBody3D
			bh.add_child(b2, true)
			b2.transform = inv * (body as StaticBody3D).global_transform
			info.cuerpos += 1
	if not ch.boxes.is_empty():
		var oh := Node3D.new()
		oh.name = "Oclusores"
		r.add_child(oh)
		for b in ch.boxes:
			var oi := OccluderInstance3D.new()
			var bo := BoxOccluder3D.new()
			bo.size = (b as AABB).size * Vector3(0.8, 0.85, 0.8)
			oi.occluder = bo
			oh.add_child(oi, true)
			oi.position = (b as AABB).get_center() - Vector3(0, (b as AABB).size.y * 0.075, 0) - origin
			info.oclusores += 1
	if r.get_child_count() == 0:
		r.free()
		return {}
	if first:
		gbox = AABB(origin - Vector3(CHUNK, 0, CHUNK) * 0.5, Vector3(CHUNK, 1, CHUNK))
	r.set_meta("aabb", gbox)
	r.set_meta("chunk_key", k)
	_own(r, r)
	var ps := PackedScene.new()
	ps.pack(r)
	var path := "%s/chunks/c_%d_%d.scn" % [OUT, k.x, k.y]
	var err := ResourceSaver.save(ps, path, ResourceSaver.FLAG_COMPRESS)
	if err != OK:
		push_error("no se pudo guardar " + path + ": " + error_string(err))
	r.free()
	info.archivo = path
	info.aabb = [gbox.position.x, gbox.position.y, gbox.position.z, gbox.size.x, gbox.size.y, gbox.size.z]
	info.bytes = FileAccess.get_file_as_bytes(path).size()
	return info


func _count(info: Dictionary, mask: int, surfaces: int, tris: int) -> void:
	for l in 3:
		if mask & (1 << l):
			info.nodos[l] += 1
			info.superficies[l] += surfaces
			info.tris[l] += tris


func _surface_tris(mesh: Mesh, s: int) -> int:
	var m := mesh as ArrayMesh
	if m == null:
		return 0
	var n: int = m.surface_get_array_index_len(s)
	return (n if n > 0 else m.surface_get_array_len(s)) / 3


func _mm_mesh(src: Mesh) -> Mesh:
	if mm_lib.has(src):
		return mm_lib[src]
	var path := "%s/meshes/mm_%03d.res" % [OUT, mm_lib.size()]
	var err := ResourceSaver.save(src, path, ResourceSaver.FLAG_COMPRESS)
	if err != OK:
		push_error("no se pudo guardar " + path + ": " + error_string(err))
	src.take_over_path(path)
	mm_lib[src] = src
	return src


# ------------------------------------------------------------------------------------------------ especiales

func _copy_meta_groups(src: Node, dst: Node) -> void:
	for k in src.get_meta_list():
		dst.set_meta(k, src.get_meta(k))
	for g in src.get_groups():
		if not String(g).begins_with("_"):
			dst.add_to_group(g, true)


func _build_special() -> Dictionary:
	var r := Node3D.new()
	r.name = "Special"
	var used := {}
	var marks := {}
	var n := 0
	var mf_script = load("res://scripts/materials_fix.gd")
	for mi in special:
		var m := mi as MeshInstance3D
		if used.has(m):
			continue
		used[m] = true
		var nm := String(m.name)
		if nm.begins_with("OBELISK_Mark_") and m.has_meta("floor") and not m.has_meta("lod_level") and m.is_visible_in_tree():
			var fl := int(m.get_meta("floor"))
			if not marks.has(fl):
				marks[fl] = []
			marks[fl].append({"mi": m})
			continue
		var c := MeshInstance3D.new()
		c.name = m.name
		_copy_meta_groups(m, c)
		c.mesh = m.mesh
		c.cast_shadow = m.cast_shadow
		c.transparency = m.transparency
		c.visible = m.is_visible_in_tree()
		if m.material_override:
			c.material_override = m.material_override
		for s in m.mesh.get_surface_count():
			var o := m.get_surface_override_material(s)
			var mat := m.get_active_material(s)
			if mat and mat.resource_name in BEAM_MATS:
				var span: Array = mf_script.beam_span(m, s)
				if not span.is_empty():
					c.set_meta("beam_y_%d" % s, Vector2(span[0], span[1]))
				continue                       # materials_fix.gd pone el material del haz al arrancar
			if o:
				c.set_surface_override_material(s, o)
		r.add_child(c, true)
		c.global_transform = m.global_transform
		n += 1
	for fl in marks:
		var acc := {}
		_add_items(acc, marks[fl], Transform3D())
		var c := MeshInstance3D.new()
		c.name = "OBELISK_Mark_Floor_%02d" % fl
		c.mesh = _acc_mesh(acc)
		c.set_meta("floor", fl)
		r.add_child(c, true)
		n += 1
	_own(r, r)
	var ps := PackedScene.new()
	ps.pack(r)
	var err := ResourceSaver.save(ps, OUT + "/special.scn", ResourceSaver.FLAG_COMPRESS)
	r.free()
	return {"nodos": n, "marcas_obelisco_pisos": marks.size(), "guardado": error_string(err)}


# ------------------------------------------------------------------------------------------------ logica

var _keep_cache := {}


func _keep(n: Node) -> bool:
	if _keep_cache.has(n):
		return _keep_cache[n]
	var k := false
	if n is StaticBody3D or n is CollisionShape3D or n is NavigationRegion3D:
		k = false
	elif n is Marker3D or n.is_in_group("interior_volumes") or n.is_in_group("navlinks"):
		k = true
	elif String(n.name).contains("LANTERN_Shard") and not String(n.name).contains("_LOD"):
		k = true
	else:
		for m in n.get_meta_list():
			if m != "extras" and m != "lod_level":
				k = not (n is MeshInstance3D and n.has_meta("lod_level") and int(n.get_meta("lod_level")) > 0)
				break
	if not k:
		for c in n.get_children():
			if _keep(c):
				k = true
				break
	_keep_cache[n] = k
	return k


func _logic_copy(src: Node, dst_parent: Node) -> int:
	var d: Node3D = Marker3D.new() if src is Marker3D else Node3D.new()
	d.name = src.name
	if src is Node3D:
		d.transform = (src as Node3D).transform
	_copy_meta_groups(src, d)
	if src is MeshInstance3D:
		d.set_meta("aabb_local", (src as MeshInstance3D).get_aabb())
		if src.is_in_group("interior_volumes"):
			d.visible = false
	dst_parent.add_child(d, true)
	var n := 1
	for c in src.get_children():
		if _keep(c):
			n += _logic_copy(c, d)
	return n


func _build_logic() -> void:
	var r := Node3D.new()
	r.name = "Logic"
	var n := 0
	for group_name in ["Terrain", "Wall", "Buildings", "Markers"]:
		var g := city.get_node_or_null(group_name)
		if g == null:
			continue
		var gd := Node3D.new()
		gd.name = group_name
		r.add_child(gd)
		for inst in g.get_children():
			if _keep(inst):
				n += _logic_copy(inst, gd)
	_own(r, r)
	var ps := PackedScene.new()
	ps.pack(r)
	var err := ResourceSaver.save(ps, OUT + "/logic.scn", ResourceSaver.FLAG_COMPRESS)
	r.free()
	rep["logica"] = {"nodos": n, "guardado": error_string(err)}


# ------------------------------------------------------------------------------------------------ escenas

func _build_scenes() -> void:
	var r := Node3D.new()
	r.name = "Concordia"
	r.set_script(load("res://scripts/city.gd"))
	for part in ["logic", "special"]:
		var inst := (load("%s/%s.scn" % [OUT, part]) as PackedScene).instantiate()
		inst.name = part.capitalize()
		r.add_child(inst)
		inst.owner = r
	var chunks_node := Node3D.new()
	chunks_node.name = "Chunks"
	r.add_child(chunks_node)
	chunks_node.owner = r
	var nav := Node3D.new()
	nav.name = "Navigation"
	r.add_child(nav)
	nav.owner = r
	for f in DirAccess.get_files_at("res://navigation"):
		if not f.ends_with(".res") or f.begins_with("nav_int_"):
			continue
		var reg := NavigationRegion3D.new()
		reg.name = f.get_basename().trim_prefix("nav_").capitalize().replace(" ", "_")
		reg.navigation_mesh = load("res://navigation/" + f)
		reg.add_to_group("nav_godot", true)
		nav.add_child(reg)
		reg.owner = r
	r.set_meta("world_index", OUT + "/world_index.json")
	var ps := PackedScene.new()
	ps.pack(r)
	print("concordia.tscn ", error_string(ResourceSaver.save(ps, "res://scenes/concordia.tscn")))
	r.free()
	# main.tscn: la ciudad + luz y entorno basicos + Game (scripts/game.gd)
	var main := Node3D.new()
	main.name = "Main"
	var c := (load("res://scenes/concordia.tscn") as PackedScene).instantiate()
	main.add_child(c)
	c.owner = main
	var sun := DirectionalLight3D.new()
	sun.name = "Sun"
	sun.rotation_degrees = Vector3(-38.0, -150.0, 0.0)
	sun.light_color = Color("ffe2b8")
	sun.light_energy = 1.2
	sun.shadow_enabled = true
	sun.directional_shadow_max_distance = 140.0
	main.add_child(sun)
	sun.owner = main
	var we := WorldEnvironment.new()
	we.name = "WorldEnvironment"
	var env := Environment.new()
	var sky := Sky.new()
	var mat := ProceduralSkyMaterial.new()
	mat.sky_top_color = Color("6b7f96")
	mat.sky_horizon_color = Color("c9c3b6")
	mat.ground_horizon_color = Color("8e8a84")
	mat.ground_bottom_color = Color("4a4846")
	sky.sky_material = mat
	env.background_mode = Environment.BG_SKY
	env.sky = sky
	env.ambient_light_source = Environment.AMBIENT_SOURCE_SKY
	env.tonemap_mode = Environment.TONE_MAPPER_FILMIC
	env.glow_enabled = true
	env.glow_hdr_threshold = 1.0
	we.environment = env
	main.add_child(we)
	we.owner = main
	var game := Node.new()
	game.name = "Game"
	game.set_script(load("res://scripts/game.gd"))
	main.add_child(game)
	game.owner = main
	var ps2 := PackedScene.new()
	ps2.pack(main)
	print("main.tscn ", error_string(ResourceSaver.save(ps2, "res://scenes/main.tscn")))
	main.free()
