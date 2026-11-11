extends Node
## CONCORDIA - carga y descarga de los chunks del mundo horneado (tools/build_world.gd) por distancia al jugador.
##  - indice: res://world/world_index.json (caja de cada chunk, zona, triangulos por LOD)
##  - biblioteca de materiales: se carga entera al principio y se guarda la referencia, para que los ajustes de
##    efectos y de dia/noche (pulso de runas, ventanas, vitrales) no se pierdan cuando un chunk se descarga
##  - cerca (< load_radius, distancia horizontal a la caja del chunk): ResourceLoader.load_threaded_request; cuando
##    el hilo termina, se instancia como mucho MAX_ATTACH chunks por fotograma; lejos (> load_radius + UNLOAD_MARGIN):
##    se libera (sus mallas salen de la GPU)
##  - sync_around(p): carga inmediata (sin hilos) alrededor de p: arranque y teletransportes
## API verificada en docs/reference/godot47/class_resourceloader.txt (load_threaded_request / _get_status / _get).

signal chunk_loaded(node: Node3D)
signal chunk_unloaded(node: Node3D)

const UNLOAD_MARGIN := 25.0
const MAX_ATTACH := 2
const MAX_PENDING := 4
const UPDATE_S := 0.25

var city: Node
var holder: Node3D
var lod: Node
var focus: Node3D
var load_radius := 120.0
var chunks: Array = []              # [{archivo, aabb, zona, estado (0 nada, 1 en hilo, 2 cargado), nodo}]
var materials: Array = []
var stats := {"cargados": 0, "en_hilo": 0, "cargas": 0, "descargas": 0, "fallos": 0, "ms_carga_sincrona": 0}
var _t := 0.0


func setup(city_node: Node, holder_node: Node3D, lod_node: Node, index_path: String) -> Dictionary:
	city = city_node
	holder = holder_node
	lod = lod_node
	if not FileAccess.file_exists(index_path):
		push_error("Falta %s: ejecuta tools/build_world.gd (ver LEEME)" % index_path)
		return {"error": "sin indice " + index_path}
	var idx = JSON.parse_string(FileAccess.get_file_as_string(index_path))
	if not (idx is Dictionary):
		push_error("Indice del mundo ilegible: " + index_path)
		return {"error": "indice ilegible"}
	for p in idx.get("materiales", []):
		var m := load(String(p)) as Material
		if m:
			materials.append(m)
		else:
			stats.fallos += 1
	for c in idx.get("chunks", []):
		var a: Array = c.get("aabb", [])
		if a.size() < 6 or not ResourceLoader.exists(String(c.get("archivo", ""))):
			stats.fallos += 1
			continue
		chunks.append({"archivo": String(c.archivo), "aabb": AABB(Vector3(a[0], a[1], a[2]), Vector3(a[3], a[4], a[5])),
			"zona": String(c.get("zona", "")), "estado": 0, "nodo": null})
	return {"chunks": chunks.size(), "materiales": materials.size(), "fallos": stats.fallos}


func _dist(c: Dictionary, p: Vector3) -> float:
	var a: AABB = c.aabb
	var dx := maxf(maxf(a.position.x - p.x, 0.0), p.x - a.end.x)
	var dz := maxf(maxf(a.position.z - p.z, 0.0), p.z - a.end.z)
	return sqrt(dx * dx + dz * dz)


func sync_around(p: Vector3) -> void:
	var t0 := Time.get_ticks_msec()
	for c in chunks:
		if _dist(c, p) > load_radius:
			continue
		if c.estado == 2:
			continue
		var ps: PackedScene
		if c.estado == 1:
			ps = ResourceLoader.load_threaded_get(c.archivo) as PackedScene
		else:
			ps = load(c.archivo) as PackedScene
		_attach(c, ps)
	_unload_far(p)
	stats.ms_carga_sincrona = Time.get_ticks_msec() - t0


func update_now() -> void:
	if focus:
		_update(focus.global_position)


func _process(delta: float) -> void:
	var attached := 0
	for c in chunks:
		if c.estado != 1:
			continue
		var st := ResourceLoader.load_threaded_get_status(c.archivo)
		if st == ResourceLoader.THREAD_LOAD_LOADED:
			if attached >= MAX_ATTACH:
				continue
			var ps := ResourceLoader.load_threaded_get(c.archivo) as PackedScene
			if focus and _dist(c, focus.global_position) > load_radius + UNLOAD_MARGIN:
				c.estado = 0                      # ya no hace falta: se suelta sin instanciar
				continue
			_attach(c, ps)
			attached += 1
		elif st == ResourceLoader.THREAD_LOAD_FAILED or st == ResourceLoader.THREAD_LOAD_INVALID_RESOURCE:
			push_error("No se pudo cargar " + c.archivo)
			c.estado = -1                         # no se reintenta en esta partida
			stats.fallos += 1
	_t += delta
	if _t >= UPDATE_S and focus:
		_t = 0.0
		_update(focus.global_position)


func _update(p: Vector3) -> void:
	var want: Array = []
	var pending := 0
	for c in chunks:
		if c.estado == 1:
			pending += 1
		elif c.estado == 0:
			var d := _dist(c, p)
			if d <= load_radius:
				want.append([d, c])
	want.sort_custom(func(x, y): return x[0] < y[0])
	for w in want:
		if pending >= MAX_PENDING:
			break
		var c: Dictionary = w[1]
		if ResourceLoader.load_threaded_request(c.archivo, "PackedScene", true) == OK:
			c.estado = 1
			pending += 1
		else:
			c.estado = -1
			stats.fallos += 1
	_unload_far(p)
	stats.en_hilo = pending


func _unload_far(p: Vector3) -> void:
	for c in chunks:
		if c.estado == 2 and _dist(c, p) > load_radius + UNLOAD_MARGIN:
			var n: Node3D = c.nodo
			c.nodo = null
			c.estado = 0
			if is_instance_valid(n):
				lod.remove_chunk(n)
				chunk_unloaded.emit(n)
				n.queue_free()
			stats.descargas += 1
			stats.cargados -= 1


func _attach(c: Dictionary, ps: PackedScene) -> void:
	if ps == null:
		push_error("Chunk vacio o ilegible: " + c.archivo)
		c.estado = -1
		stats.fallos += 1
		return
	var n := ps.instantiate() as Node3D
	if n == null:
		c.estado = -1
		stats.fallos += 1
		return
	setup_multimeshes(n)
	holder.add_child(n)
	c.nodo = n
	c.estado = 2
	stats.cargas += 1
	stats.cargados += 1
	lod.add_chunk(n, c.aabb)
	chunk_loaded.emit(n)


static func setup_multimeshes(chunk: Node) -> int:
	## instancias de las MultiMesh del chunk desde la metadata mm_xforms (ver tools/build_world.gd)
	var n := 0
	for c in chunk.get_children():
		var mmi := c as MultiMeshInstance3D
		if mmi == null or mmi.multimesh == null or not mmi.has_meta("mm_xforms"):
			continue
		var x: PackedFloat32Array = mmi.get_meta("mm_xforms")
		var count := x.size() / 12
		if count <= 0:
			continue
		var mm := mmi.multimesh
		if mm.instance_count != count:
			mm.instance_count = count
		for i in count:
			var k := i * 12
			mm.set_instance_transform(i, Transform3D(Vector3(x[k], x[k + 1], x[k + 2]), Vector3(x[k + 3], x[k + 4], x[k + 5]),
				Vector3(x[k + 6], x[k + 7], x[k + 8]), Vector3(x[k + 9], x[k + 10], x[k + 11])))
		n += count
	return n


func loaded_nodes() -> Array:
	var out: Array = []
	for c in chunks:
		if c.estado == 2 and is_instance_valid(c.nodo):
			out.append(c.nodo)
	return out
