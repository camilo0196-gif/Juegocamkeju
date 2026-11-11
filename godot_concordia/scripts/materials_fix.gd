extends RefCounted
## CONCORDIA - ajustes de material en Godot sobre la ciudad cargada (permiso del usuario, PARADA 1: materiales y
## shaders se arreglan en Godot; lo que cambie la forma va a FIXES_BLENDER.md). Lo llama scripts/city.gd al arrancar.
##  - terreno: shaders/terrain.gdshader en las superficies naturales de TRN_City_Chunk_* y TRN_ExteriorChunk_*, con
##    las texturas y escalas UV de los materiales de Concordia importados (mascaras de COLOR_0, huertos)
##  - haces (MAT_Faro_Beam: FARO_Beam y oculo del Crisol): shaders/beam.gdshader aditivo, sin profundidad ni sombras
##  - Obelisco (MAT_Obelisk_Black): piedra negra legible: albedo gris muy oscuro azulado, normal visible,
##    rugosidad 0,6 y un borde suave (rim); marcas de piso encendidas con MAT_Obelisk_Mark_Lit (set_obelisk_floors)

const CITY_LAYERS := {"MAT_Ground_Cracked": "ground", "MAT_Cobble_Concordia": "road", "MAT_Rock_Gray": "rock",
		"MAT_Ash_Gray": "ash", "MAT_Limestone_Worn": "wall"}
const EXT_LAYERS := {"MAT_Ash_Ground": "ground", "MAT_Ash_Gray": "ash", "MAT_Rock_Gray": "rock"}

var report := {}
var lit_mark: Material
var marks: Array[MeshInstance3D] = []


func apply(city: Node) -> Dictionary:
	_terrain(city)
	_beams(city)
	_obelisk(city)
	return report


# ------------------------------------------------------------------------------------------------------------ terreno

func _terrain(city: Node) -> void:
	var terrain := city.get_node_or_null("Terrain")
	if terrain == null:
		return
	var src := {}                                              # nombre de material -> BaseMaterial3D importado
	var meshes: Array = terrain.find_children("TRN_*Chunk_*", "MeshInstance3D", true, false)
	for mi in meshes:
		var m: Mesh = (mi as MeshInstance3D).mesh
		if m == null:
			continue
		for i in m.get_surface_count():
			var mat := m.surface_get_material(i) as BaseMaterial3D
			if mat and not src.has(mat.resource_name) and (CITY_LAYERS.has(mat.resource_name) or EXT_LAYERS.has(mat.resource_name)):
				src[mat.resource_name] = mat
	var shader := load("res://shaders/terrain.gdshader") as Shader
	var city_mat := _terrain_material(shader, src, CITY_LAYERS, false)
	var ext_mat := _terrain_material(shader, src, EXT_LAYERS, true)
	var n := 0
	var done := {}
	for mi in meshes:
		var m: Mesh = (mi as MeshInstance3D).mesh
		if m == null or done.has(m):
			continue
		done[m] = true
		var is_ext := String(mi.name).begins_with("TRN_Exterior")
		var layers: Dictionary = EXT_LAYERS if is_ext else CITY_LAYERS
		for i in m.get_surface_count():
			var mat := m.surface_get_material(i)
			if mat and layers.has(mat.resource_name) and (m.surface_get_format(i) & Mesh.ARRAY_FORMAT_COLOR):
				m.surface_set_material(i, ext_mat if is_ext else city_mat)
				n += 1
	report["terreno_superficies"] = n
	report["terreno_capas"] = src.keys()


func _terrain_material(shader: Shader, src: Dictionary, layers: Dictionary, exterior: bool) -> ShaderMaterial:
	var sm := ShaderMaterial.new()
	sm.resource_name = "MAT_Terrain_Exterior_Godot" if exterior else "MAT_Terrain_City_Godot"
	sm.shader = shader
	sm.set_shader_parameter("exterior", exterior)
	for mat_name in layers:
		var layer: String = layers[mat_name]
		var bm := src.get(mat_name) as BaseMaterial3D
		if bm == null:
			report["capa_sin_material_" + layer] = mat_name
			continue
		sm.set_shader_parameter(layer + "_alb", bm.albedo_texture)
		sm.set_shader_parameter(layer + "_nrm", bm.normal_texture)
		sm.set_shader_parameter(layer + "_rgh", bm.roughness_texture)
		sm.set_shader_parameter(layer + "_uv", Vector4(bm.uv1_scale.x, bm.uv1_scale.y, bm.uv1_offset.x, bm.uv1_offset.y))
		if bm.albedo_texture == null:
			report["capa_sin_textura_" + layer] = mat_name
	return sm


# -------------------------------------------------------------------------------------------------------------- haces

func _beams(city: Node) -> void:
	var shader := load("res://shaders/beam.gdshader") as Shader
	var list := []
	if shader == null:
		report["haces_error"] = "falta res://shaders/beam.gdshader"
		return
	for node in city.find_children("*", "MeshInstance3D", true, false):
		var mi := node as MeshInstance3D
		if mi == null or not is_instance_valid(mi) or mi.mesh == null:
			continue
		var m: Mesh = mi.mesh
		for i in m.get_surface_count():
			var mat := m.surface_get_material(i)
			if mat == null or mat.resource_name != "MAT_Faro_Beam":
				continue
			var span := beam_span(mi, i)
			if span.is_empty():
				list.append({"malla": String(mi.name), "error": "superficie sin datos (ver TEST_REPORT.md, PC del usuario)"})
				continue
			var lo: float = span[0]
			var hi: float = span[1]
			var sm := ShaderMaterial.new()
			sm.resource_name = "MAT_Beam_Godot"
			sm.shader = shader
			sm.set_shader_parameter("base_y", lo)
			var is_faro := String(mi.name).begins_with("FARO_Beam")
			# el haz del Crisol sube por el oculo: corto; la base se funde antes y el tope no pasa de 12 m
			var top := hi if is_faro else minf(hi, lo + 12.0)
			sm.set_shader_parameter("top_y", top)
			if not is_faro:
				sm.set_shader_parameter("base_fade", 0.3)
				sm.set_shader_parameter("top_power", 1.2)
			mi.set_surface_override_material(i, sm)
			if m.get_surface_count() == 1:
				mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
			list.append({"malla": String(mi.name), "base_y": snappedf(lo, 0.01), "alto_m": snappedf(hi - lo, 0.01),
				"tope_usado_m": snappedf(top - lo, 0.01), "fuente": span[2]})
	report["haces"] = list


static func beam_span(mi: MeshInstance3D, surface: int) -> Array:
	## [y minima, y maxima, fuente] en el mundo de la superficie del haz. Orden de preferencia:
	##  1. metadata beam_y_<n> que deja tools/build_world.gd al hornear el mundo (sin leer la GPU)
	##  2. vertices de la superficie (surface_get_arrays; puede volver vacio si el buffer de la GPU no se creo)
	##  3. caja de la malla entera (aproximada si la malla tiene mas superficies)
	## [] si no hay ningun dato utilizable.
	if mi == null or not is_instance_valid(mi) or mi.mesh == null or surface < 0 or surface >= mi.mesh.get_surface_count():
		return []
	var key := "beam_y_%d" % surface
	if mi.has_meta(key):
		var v = mi.get_meta(key)
		if v is Vector2:
			return [v.x, v.y, "metadata"]
	var arrays := mi.mesh.surface_get_arrays(surface)
	if arrays.size() > Mesh.ARRAY_VERTEX and arrays[Mesh.ARRAY_VERTEX] is PackedVector3Array:
		var verts: PackedVector3Array = arrays[Mesh.ARRAY_VERTEX]
		if verts.size() > 0:
			var lo := INF
			var hi := -INF
			var xf := mi.global_transform
			for v in verts:
				var g: Vector3 = xf * v
				lo = minf(lo, g.y)
				hi = maxf(hi, g.y)
			return [lo, hi, "vertices"]
	var box: AABB = mi.global_transform * mi.get_aabb()
	if box.size == Vector3.ZERO:
		return []
	return [box.position.y, box.end.y, "caja"]


# ---------------------------------------------------------------------------------------------------------- obelisco

func _obelisk(city: Node) -> void:
	for mi in city.find_children("OBELISK_*", "MeshInstance3D", true, false):
		if not is_instance_valid(mi):
			continue
		var m: Mesh = (mi as MeshInstance3D).mesh
		if m == null:
			continue
		for i in m.get_surface_count():
			var mat := m.surface_get_material(i) as BaseMaterial3D
			if mat == null:
				continue
			if mat.resource_name == "MAT_Obelisk_Black" and not mat.has_meta("concordia_fix"):
				mat.set_meta("concordia_fix", true)
				report["obelisco_textura_base"] = mat.albedo_texture != null
				report["obelisco_normal"] = mat.normal_texture != null
				mat.albedo_color = Color("8E9AAF")       # con la textura de roca: media ~#383E4A (gris muy oscuro azulado)
				mat.roughness = 0.6
				mat.normal_enabled = mat.normal_texture != null
				mat.normal_scale = 2.0
				mat.rim_enabled = true
				mat.rim = 0.5
				mat.rim_tint = 0.5
			elif mat.resource_name == "MAT_Obelisk_Mark_Lit":
				lit_mark = mat
		if String(mi.name).begins_with("OBELISK_Mark_") and mi.has_meta("floor"):
			marks.append(mi)
	report["obelisco_marcas"] = marks.size()


func set_obelisk_floors(n: int) -> void:
	## marcas de piso 1..n encendidas (#8FD0FF, emision 3.0, material del .glb); el resto apagadas
	for mi in marks:
		if not is_instance_valid(mi):
			continue
		mi.material_override = lit_mark if int(mi.get_meta("floor")) <= n and lit_mark else null
