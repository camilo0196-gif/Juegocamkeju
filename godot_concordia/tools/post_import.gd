@tool
extends EditorScenePostImport
## CONCORDIA - post-importacion de todos los .glb (ver tools/import_settings.py, que lo asigna en import_script/path).
## API verificada en la documentacion oficial 4.7 (docs/reference/godot47/class_editorscenepostimport.txt,
## class_basematerial3d.txt, class_geometryinstance3d.txt).
##  - extras de glTF: el importador 4.7.2 los deja en la metadata "extras" (diccionario); aqui se copian ademas como
##    metadata suelta (get_meta("interior"), get_meta("occludes_iso"), ...) sin borrar "extras".
##  - LOD propios: metadata "lod_level" (0, 1, 2) en las mallas _LOD0/_LOD1/_LOD2 y en la malla base que tiene
##    hermanas _LOD1/_LOD2; los rangos de visibilidad se asignan al montar la escena (scripts/lod_ranges.gd), porque
##    dependen de la distancia de la camara isometrica.
##  - sombra de malla activada (cast_shadow = ON) en todas las mallas visibles.
##  - materiales: el glb los trae todos con doubleSided = true; los opacos pasan a una cara (CULL_BACK) salvo telas,
##    hojas, velos, vidrios y pelo (lista OPEN), que siguen a dos caras.
##  - resumen por archivo en debug/out/import/<archivo>.json (lo lee tools/import_report.gd).

const OPEN := ["Veil", "Beam", "Glass", "Banner", "Flag", "Cloth", "Awning", "Leaf", "Leaves", "Hair", "Stained",
		"Water", "TrophyCase", "Sanador_Atlas", "Rope", "Canvas", "Curtain", "Tapestry", "Rug", "Vine", "Ivy",
		"Grass", "Hay", "Thatch", "Net", "Web", "Smoke", "Fire", "Flame", "Embers", "Shard"]

var _stats := {}


func _post_import(scene: Node) -> Object:
	_stats = {"archivo": get_source_file(), "nodos": 0, "mallas": 0, "metas": 0, "lod1": 0, "lod2": 0,
		"cull_back": {}, "dos_caras": {}, "sin_textura": {}, "colisiones": 0, "navmesh": 0, "oclusores": 0}
	_walk(scene)
	var mats_done := {}
	for k in _stats.cull_back.keys():
		mats_done[k] = true
	_stats.cull_back = _stats.cull_back.keys()
	_stats.dos_caras = _stats.dos_caras.keys()
	_stats.sin_textura = _stats.sin_textura.keys()
	DirAccess.make_dir_recursive_absolute("res://debug/out/import")
	var f := FileAccess.open("res://debug/out/import/%s.json" % get_source_file().get_file(), FileAccess.WRITE)
	if f:
		f.store_string(JSON.stringify(_stats, " "))
	return scene


func _walk(n: Node) -> void:
	_stats.nodos += 1
	if n.has_meta("extras"):
		var ex = n.get_meta("extras")
		if ex is Dictionary:
			for k in ex.keys():
				n.set_meta(StringName(str(k)), ex[k])
				_stats.metas += 1
	if n is StaticBody3D:
		_stats.colisiones += 1
	elif n is NavigationRegion3D:
		_stats.navmesh += 1
	elif n is OccluderInstance3D:
		_stats.oclusores += 1
	if n is MeshInstance3D:
		_mesh(n as MeshInstance3D)
	for c in n.get_children():
		_walk(c)


func _lod_of(name: String) -> int:
	var m := RegEx.create_from_string("_LOD(\\d)$").search(name)
	return int(m.get_string(1)) if m else -1


func _mesh(mi: MeshInstance3D) -> void:
	_stats.mallas += 1
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_ON
	var lod := _lod_of(String(mi.name))
	if lod < 0:
		var p := mi.get_parent()
		if p and (p.has_node(NodePath(String(mi.name) + "_LOD1")) or p.has_node(NodePath(String(mi.name) + "_LOD2"))):
			lod = 0
	if lod >= 0:
		mi.set_meta("lod_level", lod)
		if lod == 1:
			_stats.lod1 += 1
		elif lod == 2:
			_stats.lod2 += 1
	if mi.mesh == null:
		return
	for i in mi.mesh.get_surface_count():
		var m := mi.mesh.surface_get_material(i)
		if not (m is BaseMaterial3D):
			continue
		var bm := m as BaseMaterial3D
		var open := false
		for k in OPEN:
			if bm.resource_name.contains(k):
				open = true
				break
		if bm.transparency == BaseMaterial3D.TRANSPARENCY_DISABLED and not open:
			bm.cull_mode = BaseMaterial3D.CULL_BACK
			_stats.cull_back[bm.resource_name] = true
		else:
			_stats.dos_caras[bm.resource_name] = true
		if bm.albedo_texture == null and bm.emission_texture == null:
			_stats.sin_textura[bm.resource_name] = true
