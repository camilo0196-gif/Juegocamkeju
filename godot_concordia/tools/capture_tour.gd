extends SceneTree
## CONCORDIA - recorrido de capturas (PNG del viewport) en puntos de camara fijos + medidas de render por punto.
## xvfb-run godot --path godot_concordia --audio-driver Dummy -s res://tools/capture_tour.gd -- [prefijo] [punto ...]
## Sale en debug/out/tour/<prefijo>_<punto>.png y debug/out/tour/<prefijo>_medidas.json.
## Los puntos se dan en coordenadas de Blender (x este, y norte) y se convierten a Godot (x, -y).
## Un argumento @res://ruta.json anade puntos {nombre: [x, y, zoom]} (p. ej. debug/out/walk/puntos_captura.json) y
## solo se capturan esos (mas los que se nombren).

const POINTS := {
	"plaza": [0.0, 30.0, 60.0],
	"plaza_120": [0.0, 0.0, 120.0],
	"faro": [40.0, 40.0, 50.0],
	"salon_hazanas": [42.0, -38.0, 45.0],
	"mercado": [0.0, 100.0, 60.0],
	"banco": [20.0, 118.0, 35.0],
	"oficios": [125.0, 10.0, 60.0],
	"clases": [-110.0, -15.0, 60.0],
	"razas": [20.0, -118.0, 60.0],
	"moradas_ne": [95.0, 62.0, 60.0],
	"moradas_so": [-95.0, -62.0, 60.0],
	"puerta_este": [180.0, 0.0, 60.0],
	"escalinata_mercado": [50.0, 82.0, 35.0],
	"puente_oficios": [89.5, 4.0, 35.0],
	"escalinata_ne": [84.4, 50.0, 18.0],
	"obelisco": [-40.0, -40.0, 30.0],
	"salon_detras": [33.0, -27.0, 40.0],
	"huertos_no": [-124.0, 140.0, 22.0],
	"huertos_ne": [124.0, 100.0, 22.0],
	"exterior_sur": [0.0, -185.0, 60.0],
}

var prefix := "g2"
var only: Array = []
var hours: Array = []           # h=6.2,12,17.5 -> una captura por hora (scripts/day_night.gd)
var points: Dictionary = POINTS.duplicate()
var scene_path := "res://scenes/main.tscn"   # escena=res://... (p. ej. la ciudad de .glb para comparar)
var quality := "Alto"           # q=Bajo|Medio|Alto|auto (por defecto Alto: las capturas de referencia)
var out := {}


func _initialize() -> void:
	var a := OS.get_cmdline_user_args()
	if a.size() > 0:
		prefix = a[0]
	for arg in a.slice(1):
		if String(arg).begins_with("h="):
			for h in String(arg).substr(2).split(","):
				hours.append(float(h))
		elif String(arg).begins_with("escena="):
			scene_path = String(arg).substr(7)
		elif String(arg).begins_with("q="):
			quality = String(arg).substr(2)
		elif String(arg).begins_with("@"):
			var extra: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(String(arg).substr(1)))
			for k in extra:
				points[k] = extra[k]
				only.append(k)
		else:
			only.append(arg)
	change_scene_to_file(scene_path)
	_run.call_deferred()


func _run() -> void:
	for i in 30:
		await process_frame
	var main := current_scene
	var game = main.get_node("Game")
	while game.quality == null:
		await process_frame
	game.quality.set_mode(quality, false)
	out["calidad"] = {"modo": quality, "nivel": game.quality.level, "gpu": game.quality.gpu}
	DirAccess.make_dir_recursive_absolute("res://debug/out/tour")
	out["iso_check"] = _iso_check(main, game)
	if hours.is_empty():
		hours = [-1.0]
	for hr in hours:
		await _tour(game, hr)
	var fh := FileAccess.open("res://debug/out/tour/%s_medidas.json" % prefix, FileAccess.WRITE)
	fh.store_string(JSON.stringify(out, " "))
	fh = null
	quit()


func _tour(game, hr: float) -> void:
	if hr >= 0.0 and game.day_night:
		game.day_night.hour = hr
		game.day_night.apply()
	var suffix := "" if hr < 0.0 else "_h%04.1f" % hr
	for name in points:
		if not only.is_empty() and not only.has(name):
			continue
		var p: Array = points[name]
		await game.prepare_area(p[0], -p[1])
		var g: Vector3 = game.ground_at(p[0], -p[1])
		game.player.global_position = g + Vector3(0, 0.05, 0)
		game.player.velocity = Vector3.ZERO
		game.cam_rig.zoom = minf(p[2], game.cam_rig.zoom_max)
		game.cam_rig._apply(true)
		game.city.ensure_loaded(game.player.global_position)
		for i in 12:
			await process_frame
		await RenderingServer.frame_post_draw
		var img := root.get_texture().get_image()
		img.save_png("res://debug/out/tour/%s_%s%s.png" % [prefix, name, suffix])
		var m: Dictionary = game.hud.snapshot()
		m["zona"] = game.city.zone_at(game.player.global_position)
		m["lod_niveles"] = game.city.lod.stats.nivel.duplicate()
		m["suelo_y"] = snappedf(g.y, 0.01)
		out[name + suffix] = m
		print("TOUR ", name, suffix, " ", JSON.stringify(m))


func _iso_check(main: Node, game) -> Dictionary:
	## distancia de la camara a los hitos de la plaza: el lado SE (Salon de las Hazanas) debe quedar mas cerca
	## que el NO (Santuario); NE (Faro) y SO (Obelisco) a la misma distancia (la camara mira de SE a NO)
	game.player.global_position = Vector3(0, 9, 0)
	game.cam_rig._apply(true)
	var cam: Camera3D = game.cam_rig.cam
	var d := {}
	for n in ["MARKER_SalonHazanas", "MARKER_Santuario", "MARKER_Faro", "MARKER_Obelisco"]:
		var m := main.find_child(n, true, false) as Node3D
		if m:
			d[n] = snappedf(cam.global_position.distance_to(m.global_position), 0.01)
	d["camara_rotacion_grados"] = cam.global_rotation_degrees.snapped(Vector3.ONE * 0.001)
	d["direccion_vista"] = (-cam.global_transform.basis.z).snapped(Vector3.ONE * 0.001)
	d["se_mas_cerca"] = d.get("MARKER_SalonHazanas", 0.0) < d.get("MARKER_Santuario", 0.0)
	print("ISO ", JSON.stringify(d))
	return d
