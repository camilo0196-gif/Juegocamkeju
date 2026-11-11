extends Node
## CONCORDIA - LOD propios (_LOD0 / _LOD1 / _LOD2) por unidad (edificio, pieza de muralla o chunk de terreno).
##
## Por que no GeometryInstance3D.visibility_range: la documentacion 4.7 (docs/reference/godot47/visibility_ranges.txt)
## mide la distancia a la CAMARA. Con la camara isometrica ortografica, puesta a distancia fija detras del jugador,
## esa distancia no dice lo cerca que esta un edificio del jugador (depende de si queda delante o detras en el eje de
## vision). Aqui se usan los umbrales pedidos (LOD0 hasta 40 m, LOD1 hasta 100 m, LOD2 mas alla, margen 5 m de
## histeresis) medidos en horizontal desde el foco (jugador), hasta el borde de la caja de cada unidad.
##
## Mundo horneado (tools/build_world.gd): cada chunk cargado es una unidad; sus mallas fusionadas llevan la metadata
## lod_mask (bit 0 = visible en LOD0, bit 1 = LOD1, bit 2 = LOD2), calculada al hornear con las reglas de abajo.
##
## Reglas por unidad: se muestran las mallas con lod_level = nivel; si la unidad no tiene ese nivel, el mas alto que
## tenga. Mallas sin lod_level (props, puertas, tejados sin LOD): visibles en niveles 0 y 1, ocultas en 2 si la
## unidad tiene LOD2 (el LOD2 sustituye a cuerpo + cubierta) o si son pequenas (< 3 m).

const LOD0_END := 40.0
const LOD1_END := 100.0
const MARGIN := 5.0
const UPDATE_S := 0.2

## distancias de cambio (scripts/quality.gd las ajusta: Bajo 25 / 70 m)
var lod0_end := LOD0_END
var lod1_end := LOD1_END
var focus: Node3D
var units: Array = []          # [{aabb: AABB (mundo), lods: {0: [], 1: [], 2: []}, free: [], small: [], level: -1}]
var _t := 0.0
var stats := {"unidades": 0, "nivel": [0, 0, 0], "cambios": 0}


func add_scene_root(root: Node) -> void:
	## unidades = hijos directos de root (los hijos directos del .glb importado).
	## En los terrenos (chunks sueltos con sufijo _LODn) se agrupan por nombre base.
	var by_base := {}
	for c in root.get_children():
		if c is MeshInstance3D and String(c.name).contains("_LOD"):
			var base := String(c.name).get_slice("_LOD", 0)
			if not by_base.has(base):
				by_base[base] = []
			by_base[base].append(c)
		else:
			_add_unit([c])
	for base in by_base:
		_add_unit(by_base[base])


func _add_unit(nodes: Array) -> void:
	var u := {"aabb": AABB(), "lods": {0: [], 1: [], 2: []}, "free": [], "small": [], "level": -1, "has2": false}
	var first := true
	for n in nodes:
		var meshes: Array = [n] if n is MeshInstance3D else []
		meshes += n.find_children("*", "MeshInstance3D", true, false)
		for mi in meshes:
			if not (mi as MeshInstance3D).visible and mi.is_in_group("interior_volumes"):
				continue
			var box: AABB = mi.global_transform * mi.get_aabb()
			u.aabb = box if first else u.aabb.merge(box)
			first = false
			if mi.has_meta("lod_level"):
				var lv: int = int(mi.get_meta("lod_level"))
				u.lods[lv].append(mi)
				if lv == 2:
					u.has2 = true
			elif box.size.length() < 3.0:
				u.small.append(mi)
			else:
				u.free.append(mi)
	if first:
		return
	if u.lods[1].is_empty() and u.lods[2].is_empty() and u.small.is_empty():
		return                                  # sin LOD ni detalles: siempre visible, no hace falta gestionarla
	units.append(u)
	stats.unidades = units.size()


func _dist(u: Dictionary, p: Vector3) -> float:
	var a: AABB = u.aabb
	var dx := maxf(maxf(a.position.x - p.x, 0.0), p.x - (a.position.x + a.size.x))
	var dz := maxf(maxf(a.position.z - p.z, 0.0), p.z - (a.position.z + a.size.z))
	return sqrt(dx * dx + dz * dz)


func _level_for(d: float, cur: int) -> int:
	var l0 := lod0_end + (MARGIN if cur == 0 else -MARGIN if cur > 0 else 0.0)
	var l1 := lod1_end + (MARGIN if cur <= 1 and cur >= 0 else -MARGIN if cur == 2 else 0.0)
	if d < l0:
		return 0
	if d < l1:
		return 1
	return 2


func add_chunk(root: Node3D, box: AABB) -> void:
	var u := {"aabb": box, "chunk": root, "masked": [], "level": -1}
	for c in root.get_children():
		if c is GeometryInstance3D and c.has_meta("lod_mask"):
			u.masked.append(c)
	units.append(u)
	stats.unidades = units.size()
	_set_level(u, _level_for(_dist(u, _focus_pos()), -1))


func _focus_pos() -> Vector3:
	## sin foco (antes de que Game cree al jugador) se mide desde el centro de la plaza
	return focus.global_position if is_instance_valid(focus) else Vector3.ZERO


func remove_chunk(root: Node3D) -> void:
	for i in range(units.size() - 1, -1, -1):
		if units[i].get("chunk") == root:
			units.remove_at(i)
	stats.unidades = units.size()


func force_refresh() -> void:
	for u in units:
		u.level = -1
	apply_all()


func apply_all() -> void:
	_t = UPDATE_S
	_process(0.0)


func _process(delta: float) -> void:
	_t += delta
	if _t < UPDATE_S:
		return
	_t = 0.0
	var p := _focus_pos()
	stats.nivel = [0, 0, 0]
	for u in units:
		var lv := _level_for(_dist(u, p), u.level)
		stats.nivel[lv] += 1
		if lv != u.level:
			_set_level(u, lv)


func _set_level(u: Dictionary, lv: int) -> void:
	u.level = lv
	stats.cambios += 1
	if u.has("masked"):
		for gi in u.masked:
			if is_instance_valid(gi):
				gi.visible = (int(gi.get_meta("lod_mask")) >> lv) & 1 == 1
		return
	var show := lv
	while show > 0 and u.lods[show].is_empty():
		show -= 1
	for k in [0, 1, 2]:
		for mi in u.lods[k]:
			if is_instance_valid(mi):
				mi.visible = (k == show)
	var hide_free: bool = lv == 2 and u.has2
	for mi in u.free:
		if is_instance_valid(mi):
			mi.visible = not hide_free
	for mi in u.small:
		if is_instance_valid(mi):
			mi.visible = lv < 2
