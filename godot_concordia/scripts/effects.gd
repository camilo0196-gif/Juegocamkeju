extends Node
## CONCORDIA - efectos de G5 sobre la ciudad cargada (sin cambiar la forma de ningun modelo):
##  - velo del Portal (shaders/veil.gdshader), agua del Cauce y de las fuentes (shaders/water.gdshader),
##    estandartes y banderas al viento (shaders/banner.gdshader)
##  - pulso de emision: runas (MAT_Rune_Glow_*, MAT_Wall_Runes con la "energia del Faro"), tubos de luz
##    (MAT_Pipe_Light_Core: pulso que va de la Tesoreria al Faro), cristal del Faro (MAT_Shard_Blue_E40, ~4,0)
##  - MAT_Embers (unica emision calida) limitada a 1,5; vidrios: MAT_Glass_R04 con profundidad solo opaca y orden
##    de transparencias (velo 1, vidrios de tubo 0, haces 2)
##  - rueda de la Carpinteria girando a ~6 rpm; piedras flotantes del Crisol (subir/bajar y girar)
##  - humo (MARKER_Alquimia_Smoke_*) y vapor (MARKER_GranForja_Steam) con GPUParticles3D
##  - ceniza: particulas grises que caen alrededor del jugador
##  - transparencia por proximidad: mallas con metadata occludes_iso (Salon de las Hazanas, tramos SE de la muralla)
##    se aclaran (GeometryInstance3D.transparency) cuando tapan al jugador desde la camara

const PULSE := {"MAT_Rune_Glow": [0.25, 0.35], "MAT_Wall_Runes": [0.3, 0.25], "MAT_Pipe_Light_Core": [0.35, 0.6],
		"MAT_Shard_Blue_E40": [0.12, 0.5]}

var city: Node
var focus: Node3D
var cam_rig: Node
var day_night: Node
var pulsing: Array = []                 # [material, energia base, amplitud, velocidad]
var wheel: Node3D
var wheel_axis := Vector3.RIGHT
var stones: Array = []                  # [nodo, posicion base, fase]
var occluders: Array = []               # [mallas, caja global, transparencia actual]
var ash: GPUParticles3D
var report := {}
var _t_occ := 0.0


func setup(city_node: Node, focus_node: Node3D, cam: Node, dn: Node) -> Dictionary:
	city = city_node
	focus = focus_node
	cam_rig = cam
	day_night = dn
	_materials()
	_moving_parts()
	_smoke()
	_ash()
	_occluders()
	return report


func _materials() -> void:
	var veil_sh := load("res://shaders/veil.gdshader") as Shader
	var water_sh := load("res://shaders/water.gdshader") as Shader
	var banner_sh := load("res://shaders/banner.gdshader") as Shader
	var replaced := {}
	var counts := {"velo": 0, "agua": 0, "estandartes": 0, "pulso": 0}
	for mi in city.find_children("*", "MeshInstance3D", true, false):
		var m: Mesh = (mi as MeshInstance3D).mesh
		if m == null:
			continue
		for i in m.get_surface_count():
			var mat := m.surface_get_material(i) as BaseMaterial3D
			if mat == null:
				continue
			var n := mat.resource_name
			if n == "MAT_Portal_Veil":
				if not replaced.has(mat):
					var sm := ShaderMaterial.new()
					sm.shader = veil_sh
					sm.render_priority = 1
					replaced[mat] = sm
				m.surface_set_material(i, replaced[mat])
				counts.velo += 1
			elif n == "MAT_Water":
				if not replaced.has(mat):
					var sm := ShaderMaterial.new()
					sm.shader = water_sh
					sm.set_shader_parameter("water_nrm", mat.normal_texture)
					sm.set_shader_parameter("water_alb", mat.albedo_texture)
					sm.set_shader_parameter("has_albedo", mat.albedo_texture != null)
					sm.set_shader_parameter("uv_xform", Vector4(mat.uv1_scale.x, mat.uv1_scale.y, mat.uv1_offset.x, mat.uv1_offset.y))
					replaced[mat] = sm
				m.surface_set_material(i, replaced[mat])
				counts.agua += 1
			elif n.begins_with("MAT_Banner_"):
				var key := [mat, String(mi.name).contains("Flag")]
				if not replaced.has(str(key)):
					var sm := ShaderMaterial.new()
					sm.shader = banner_sh
					sm.set_shader_parameter("banner_alb", mat.albedo_texture)
					sm.set_shader_parameter("albedo_color", mat.albedo_color)
					sm.set_shader_parameter("uv_xform", Vector4(mat.uv1_scale.x, mat.uv1_scale.y, mat.uv1_offset.x, mat.uv1_offset.y))
					sm.set_shader_parameter("flag_mode", key[1])
					replaced[str(key)] = sm
				(mi as MeshInstance3D).set_surface_override_material(i, replaced[str(key)])
				counts.estandartes += 1
			elif n == "MAT_Embers":
				mat.emission_energy_multiplier = minf(mat.emission_energy_multiplier, 1.5)
			elif n == "MAT_Glass_R04":
				mat.depth_draw_mode = BaseMaterial3D.DEPTH_DRAW_OPAQUE_ONLY
				mat.render_priority = 0
			elif n == "MAT_Pipe_Glass":
				mat.render_priority = 0
			for k in PULSE:
				if n.begins_with(k) and not replaced.has("p" + str(mat.get_instance_id())):
					replaced["p" + str(mat.get_instance_id())] = true
					pulsing.append([mat, mat.emission_energy_multiplier, PULSE[k][0], PULSE[k][1], n])
					counts.pulso += 1
	report["materiales_efectos"] = counts


func _moving_parts() -> void:
	wheel = city.find_child("Taller_Carpinteria_WATERWHEEL", true, false) as Node3D
	if wheel and wheel is MeshInstance3D:
		var box := (wheel as MeshInstance3D).get_aabb()
		# el eje de la rueda es el lado mas corto de su caja (en local)
		var s := box.size
		wheel_axis = Vector3.RIGHT if s.x <= s.y and s.x <= s.z else (Vector3.UP if s.y <= s.z else Vector3.BACK)
		report["rueda_eje_local"] = wheel_axis
	for n in city.find_children("CRISOL_FloatStone_*", "Node3D", true, false):
		if String(n.name).contains("_LOD"):
			continue
		stones.append([n, (n as Node3D).position, randf() * TAU])
	report["piedras_crisol"] = stones.size()


func _smoke_particles(color: Color, amount: int, lifetime: float, rise: float, size: float) -> GPUParticles3D:
	var p := GPUParticles3D.new()
	p.amount = amount
	p.lifetime = lifetime
	p.local_coords = false
	var pm := ParticleProcessMaterial.new()
	pm.direction = Vector3(0, 1, 0)
	pm.spread = 12.0
	pm.initial_velocity_min = rise * 0.7
	pm.initial_velocity_max = rise
	pm.gravity = Vector3(0.25, 0.05, 0.1)          # deriva con el viento del oeste
	pm.scale_min = 0.6
	pm.scale_max = 1.4
	var curve := Curve.new()
	curve.add_point(Vector2(0, 0.4))
	curve.add_point(Vector2(1, 1.6))
	var ct := CurveTexture.new()
	ct.curve = curve
	pm.scale_curve = ct
	var grad := Gradient.new()
	grad.set_color(0, Color(color, 0.0))
	grad.add_point(0.15, Color(color, 0.45))
	grad.set_color(grad.get_point_count() - 1, Color(color, 0.0))
	var gt := GradientTexture1D.new()
	gt.gradient = grad
	pm.color_ramp = gt
	p.process_material = pm
	var q := QuadMesh.new()
	q.size = Vector2(size, size)
	var mat := StandardMaterial3D.new()
	mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	mat.billboard_mode = BaseMaterial3D.BILLBOARD_PARTICLES
	mat.vertex_color_use_as_albedo = true
	mat.albedo_texture = _soft_dot()
	q.material = mat
	p.draw_pass_1 = q
	p.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	return p


func _soft_dot() -> Texture2D:
	var g := Gradient.new()
	g.set_color(0, Color(1, 1, 1, 1))
	g.set_color(1, Color(1, 1, 1, 0))
	var t := GradientTexture2D.new()
	t.gradient = g
	t.fill = GradientTexture2D.FILL_RADIAL
	t.fill_from = Vector2(0.5, 0.5)
	t.fill_to = Vector2(1.0, 0.5)
	t.width = 64
	t.height = 64
	return t


func _smoke() -> void:
	var n := 0
	for m in city.find_children("MARKER_Alquimia_Smoke_*", "Node3D", true, false):
		var p := _smoke_particles(Color("8E8C88"), 40, 7.0, 0.8, 1.6)
		city.add_child(p)
		p.global_position = (m as Node3D).global_position
		n += 1
	for m in city.find_children("MARKER_GranForja_Steam", "Node3D", true, false):
		var p := _smoke_particles(Color("C9CCD0"), 50, 4.0, 1.6, 1.4)
		city.add_child(p)
		p.global_position = (m as Node3D).global_position
		n += 1
	report["emisores_humo_vapor"] = n


func _ash() -> void:
	## ceniza: copos grises que caen despacio en una caja de 70 x 30 x 70 m que sigue al jugador
	ash = GPUParticles3D.new()
	ash.name = "Ash"
	ash.amount = 900
	ash.lifetime = 24.0
	ash.preprocess = 24.0
	ash.local_coords = false
	ash.visibility_aabb = AABB(Vector3(-40, -30, -40), Vector3(80, 60, 80))
	var pm := ParticleProcessMaterial.new()
	pm.emission_shape = ParticleProcessMaterial.EMISSION_SHAPE_BOX
	pm.emission_box_extents = Vector3(35, 2, 35)
	pm.direction = Vector3(0.3, -1, 0.1)
	pm.spread = 25.0
	pm.initial_velocity_min = 0.3
	pm.initial_velocity_max = 0.6
	pm.gravity = Vector3(0.08, -0.25, 0.03)
	pm.turbulence_enabled = true
	pm.turbulence_noise_strength = 0.4
	pm.turbulence_noise_scale = 6.0
	pm.scale_min = 0.5
	pm.scale_max = 1.2
	ash.process_material = pm
	var q := QuadMesh.new()
	q.size = Vector2(0.07, 0.07)
	var mat := StandardMaterial3D.new()
	mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	mat.billboard_mode = BaseMaterial3D.BILLBOARD_PARTICLES
	mat.albedo_color = Color(0.62, 0.61, 0.59, 0.75)
	mat.albedo_texture = _soft_dot()
	mat.roughness = 1.0
	q.material = mat
	ash.draw_pass_1 = q
	ash.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	city.add_child(ash)


func _occluders() -> void:
	for n in city.get_tree().get_nodes_in_group("occludes_iso"):
		var meshes: Array = []
		if n is MeshInstance3D:
			meshes.append(n)
		for c in n.find_children("*", "MeshInstance3D", true, false):
			meshes.append(c)
		var p := n.get_parent()
		if p:
			for c in p.get_children():
				if c is MeshInstance3D and String(c.name).begins_with(String(n.name) + "_LOD"):
					meshes.append(c)
		if meshes.is_empty():
			continue
		var box: AABB = (meshes[0] as MeshInstance3D).global_transform * (meshes[0] as MeshInstance3D).get_aabb()
		for mi in meshes:
			box = box.merge((mi as MeshInstance3D).global_transform * (mi as MeshInstance3D).get_aabb())
		occluders.append([meshes, box, 0.0])
	report["oclusores_transparentes"] = occluders.size()


func _process(delta: float) -> void:
	var t := Time.get_ticks_msec() / 1000.0
	var night: float = day_night.night if day_night else 0.0
	var faro_energy := 0.85 + 0.35 * night
	for e in pulsing:
		var mat: BaseMaterial3D = e[0]
		var k: float = faro_energy if String(e[4]).begins_with("MAT_Wall_Runes") or String(e[4]).begins_with("MAT_Rune") else 1.0
		var ph: float = t * float(e[3]) * TAU
		mat.emission_energy_multiplier = e[1] * k * (1.0 + e[2] * sin(ph))
	if wheel:
		wheel.rotate_object_local(wheel_axis, delta * TAU * 6.0 / 60.0)
	for s in stones:
		var n: Node3D = s[0]
		n.position = s[1] + Vector3(0, 0.18 * sin(t * 0.7 + s[2]), 0)
		n.rotate_y(delta * 0.25)
	if ash and focus:
		ash.global_position = focus.global_position + Vector3(0, 22, 0)
	_t_occ -= delta
	if _t_occ <= 0.0:
		_t_occ = 0.1
		_update_occluders()


func _update_occluders() -> void:
	if focus == null or cam_rig == null or occluders.is_empty():
		return
	var cam: Camera3D = cam_rig.cam
	var target := focus.global_position + Vector3(0, 1.0, 0)
	# segmento de la camara al jugador en la direccion de vista (camara ortografica: rayo paralelo)
	var from := target + cam.global_transform.basis.z * 150.0
	for o in occluders:
		var box: AABB = o[1]
		var hit := box.intersects_segment(from, target) != null and not box.has_point(target)
		var want := 0.7 if hit else 0.0
		var cur: float = o[2]
		if absf(cur - want) < 0.01:
			continue
		cur = move_toward(cur, want, 0.2)
		o[2] = cur
		for mi in o[0]:
			(mi as MeshInstance3D).transparency = cur
