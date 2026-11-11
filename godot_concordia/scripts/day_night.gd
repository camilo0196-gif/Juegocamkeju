extends Node
## CONCORDIA - ciclo de dia y noche (G4). Referencias del usuario: amanecer y hora azul de Mont-Saint-Michel, mediodia
## templado, hora dorada de Siena (17:30), atardecer de Rothenburg (19:30) y noche de Carcassonne (ventanas calidas,
## luna fria, farolillos de esquirla #8FD0FF). Paleta apagada: colores de luz y cielo con saturacion <= 0,35 (los
## azules de 185-215 grados pueden subir); #8FD0FF es el unico color magico fuerte.
## Controla: sol (direccion por la hora: sale por el este, mediodia al sur, se pone por el oeste), luna, cielo
## procedural, luz ambiente, niebla con ceniza, brillo (glow), emision de ventanas y vitrales y un grupo de 16
## OmniLight3D que se reparten entre los farolillos mas cercanos al jugador por la noche.
## Teclas (scripts/game.gd): T adelanta una hora. `minutes_per_second` > 0 hace correr el reloj solo.

const KEYS := [
	# hora, cielo arriba, horizonte, suelo, sol (color, energia), luna, ambiente, niebla (color, densidad), noche (0-1)
	[0.0, "0E1624", "1D2738", "121519", "C9D3E0", 0.0, 0.16, 0.22, "1A2230", 0.00044, 1.0],
	[5.0, "1E2A42", "4A5068", "1C1F26", "D9C7BD", 0.0, 0.12, 0.25, "3A4256", 0.00044, 0.9],
	[6.2, "3C4B69", "B09C98", "3A3836", "E8C9B6", 0.35, 0.05, 0.35, "8D8A90", 0.00040, 0.5],   # Mont-Saint-Michel
	[8.0, "7790AE", "D6CDBE", "6E6A64", "F2DFC9", 0.85, 0.0, 0.45, "B9B4AA", 0.00028, 0.0],
	[12.0, "86A0BD", "DCD6CA", "7A766F", "FFF2E0", 1.0, 0.0, 0.45, "C8C3B8", 0.00024, 0.0],
	[16.0, "8296AE", "E0D2BC", "7A7266", "FFE6C8", 1.0, 0.0, 0.45, "CDBFA8", 0.00026, 0.0],
	[17.5, "7C8BA0", "E3C9A6", "776B5D", "FFD3A6", 1.05, 0.0, 0.45, "D2BC9C", 0.00030, 0.0],   # Siena, hora dorada
	[19.5, "586180", "D9A68C", "4E4540", "FFC9A6", 0.55, 0.03, 0.4, "A88E84", 0.00036, 0.35], # Rothenburg
	[20.6, "2B3552", "6A7088", "26262B", "E0B9A8", 0.08, 0.08, 0.3, "4C5268", 0.00040, 0.75],  # hora azul
	[22.0, "121B2E", "26314A", "15171C", "C9D3E0", 0.0, 0.16, 0.22, "1E2638", 0.00044, 1.0],  # Carcassonne
	[24.0, "0E1624", "1D2738", "121519", "C9D3E0", 0.0, 0.16, 0.22, "1A2230", 0.00044, 1.0],
]
const MOON_COLOR := Color("A9B9D6")
const LANTERN_COLOR := Color("8FD0FF")
const LANTERN_POOL := 16

@export var hour := 17.5
@export var minutes_per_second := 0.0

var sun: DirectionalLight3D
var moon: DirectionalLight3D
var env: Environment
var sky_mat: ProceduralSkyMaterial
var window_mats: Array[BaseMaterial3D] = []
var stained_mats: Array[BaseMaterial3D] = []
var lantern_pos := PackedVector3Array()
var lanterns: Array[OmniLight3D] = []
var focus: Node3D
var night := 0.0
var _t_lanterns := 0.0


func setup(main: Node, city: Node, focus_node: Node3D) -> void:
	focus = focus_node
	sun = main.get_node("Sun") as DirectionalLight3D
	var we := main.get_node("WorldEnvironment") as WorldEnvironment
	env = we.environment
	sky_mat = env.sky.sky_material as ProceduralSkyMaterial
	env.glow_enabled = true
	env.glow_hdr_threshold = 1.0
	env.glow_intensity = 0.7
	env.glow_bloom = 0.0
	env.tonemap_mode = Environment.TONE_MAPPER_FILMIC
	env.tonemap_white = 4.0          # mas margen en las luces altas (la plaza de travertino se quemaba a mediodia)
	env.ssao_enabled = true
	env.ssao_radius = 1.4
	env.ssao_intensity = 1.6
	env.fog_enabled = true
	env.fog_sky_affect = 0.1
	env.fog_height = 7.0
	env.fog_height_density = 0.008     # niebla baja de ceniza; la camara iso esta a 120 m: densidad pequena
	env.ambient_light_source = Environment.AMBIENT_SOURCE_SKY
	moon = DirectionalLight3D.new()
	moon.name = "Moon"
	moon.light_color = MOON_COLOR
	moon.shadow_enabled = false
	main.add_child(moon)
	# ventanas y vitrales
	var seen := {}
	for mi in city.find_children("*", "MeshInstance3D", true, false):
		var m: Mesh = (mi as MeshInstance3D).mesh
		if m == null:
			continue
		for i in m.get_surface_count():
			var mat := m.surface_get_material(i) as BaseMaterial3D
			if mat == null or seen.has(mat):
				continue
			seen[mat] = true
			if mat.resource_name.begins_with("MAT_Window_Warm"):
				window_mats.append(mat)
			elif mat.resource_name.begins_with("MAT_Stained_Glass"):
				stained_mats.append(mat)
	# farolillos: marcadores MARKER_Lantern_* (Moradas) y mallas LANTERN_Shard del resto de la ciudad
	for n in city.find_children("MARKER_Lantern_*", "Node3D", true, false):
		lantern_pos.append((n as Node3D).global_position)
	for n in city.find_children("*LANTERN_Shard*", "Node3D", true, false):
		if not String(n.name).contains("_LOD"):
			lantern_pos.append((n as Node3D).global_position)
	for i in LANTERN_POOL:
		var l := OmniLight3D.new()
		l.light_color = LANTERN_COLOR
		l.omni_range = 7.0
		l.omni_attenuation = 1.4
		l.shadow_enabled = false
		l.visible = false
		main.add_child(l)
		lanterns.append(l)
	apply()


func stats() -> Dictionary:
	return {"ventanas": window_mats.size(), "vitrales": stained_mats.size(), "farolillos": lantern_pos.size()}


func advance(hours: float) -> void:
	hour = fposmod(hour + hours, 24.0)
	apply()


func _process(delta: float) -> void:
	if minutes_per_second > 0.0:
		hour = fposmod(hour + delta * minutes_per_second / 60.0, 24.0)
		apply()
	_t_lanterns -= delta
	if _t_lanterns <= 0.0:
		_t_lanterns = 0.5
		_place_lanterns()


func _key(h: float) -> Array:
	for i in range(1, KEYS.size()):
		if h <= KEYS[i][0]:
			var a: Array = KEYS[i - 1]
			var b: Array = KEYS[i]
			var t: float = (h - float(a[0])) / maxf(float(b[0]) - float(a[0]), 0.001)
			var out := [h]
			for k in range(1, a.size()):
				if a[k] is String:
					out.append(Color(a[k]).lerp(Color(b[k]), t))
				else:
					out.append(lerpf(a[k], b[k], t))
			return out
	return KEYS[0]


func apply() -> void:
	if sun == null:
		return
	var k := _key(hour)
	sky_mat.sky_top_color = k[1]
	sky_mat.sky_horizon_color = k[2]
	sky_mat.ground_horizon_color = (k[2] as Color).darkened(0.25)
	sky_mat.ground_bottom_color = k[3]
	# sol: este (+X) a las 6, sur (+Z de Godot = -Y de Blender) a mediodia, oeste a las 18
	var a := PI * (hour - 6.0) / 12.0
	var elev := deg_to_rad(maxf(sin(a), -0.15) * 58.0 + 4.0)
	var dir_to_sun := Vector3(cos(a) * cos(elev), sin(elev), sin(a) * cos(elev)).normalized()
	sun.look_at_from_position(dir_to_sun * 100.0, Vector3.ZERO, Vector3.UP if absf(dir_to_sun.y) < 0.99 else Vector3.FORWARD)
	sun.light_color = k[4]
	sun.light_energy = k[5]
	sun.visible = k[5] > 0.01
	var md := Vector3(-cos(a) * 0.5, 0.75, -sin(a) * 0.5).normalized()
	moon.look_at_from_position(md * 100.0, Vector3.ZERO)
	moon.light_energy = k[6]
	moon.visible = k[6] > 0.01
	env.ambient_light_sky_contribution = 0.85
	env.ambient_light_energy = k[7]
	env.fog_light_color = k[8]
	env.fog_density = k[9]
	night = k[10]
	for m in window_mats:
		m.emission_energy_multiplier = lerpf(0.0, 1.3, night)
	for m in stained_mats:
		m.emission_energy_multiplier = lerpf(0.35, 1.0, night)
	_place_lanterns()


func _place_lanterns() -> void:
	if lanterns.is_empty():
		return
	var on := night > 0.15 and focus != null
	if not on:
		for l in lanterns:
			l.visible = false
		return
	var p := focus.global_position
	var best: Array = []
	for i in lantern_pos.size():
		var d := lantern_pos[i].distance_squared_to(p)
		if d > 3600.0:
			continue
		best.append([d, i])
	best.sort_custom(func(x, y): return x[0] < y[0])
	for j in lanterns.size():
		var l := lanterns[j]
		if j < best.size():
			l.global_position = lantern_pos[best[j][1]] + Vector3(0, -0.2, 0)
			l.light_energy = 0.9 * night
			l.visible = true
		else:
			l.visible = false
