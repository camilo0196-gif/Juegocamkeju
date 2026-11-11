extends SceneTree
## CONCORDIA - banco de pruebas de rendimiento para ejecutar en el PC del usuario (las cifras del servidor de pruebas no
## valen: no tiene tarjeta grafica). Recorre escenas fijas con la camara de juego y escribe benchmark_resultados.txt
## (en la carpeta del proyecto) con, por escena: FPS medio, 1 % peor (FPS del percentil 99 del tiempo de fotograma),
## tiempo de fotograma medio y maximo, draw calls, triangulos, objetos y memoria de video; y la GPU, CPU, sistema,
## memoria, resolucion y version de Godot.
##
## Uso (sin abrir el editor), desde la carpeta godot_concordia:
##   Windows:  Godot_v4.7.2-stable_win64.exe --path . -s res://tools/benchmark.gd
##   Linux:    ./Godot_v4.7.2-stable_linux.x86_64 --path . -s res://tools/benchmark.gd
## Opcional: -- rapido  (5 s por escena en vez de 12)
## Durante la prueba la sincronizacion vertical se desactiva para medir el maximo real.
## API verificada en docs/reference/godot47 (RenderingServer.get_rendering_info, Performance, OS, DisplayServer).

const NavReady = preload("res://scripts/nav_ready.gd")

# nombre, x / y de Blender, zoom (metros visibles), hora
const SCENES := [
	["plaza_juego", 0.0, 30.0, 45.0, 17.5],
	["mercado_juego", 0.0, 100.0, 45.0, 17.5],
	["oficios_juego", 125.0, 10.0, 45.0, 17.5],
	["moradas_ne_juego", 95.0, 62.0, 45.0, 17.5],
	["moradas_so_juego", -95.0, -62.0, 45.0, 17.5],
	["moradas_ne_noche", 95.0, 62.0, 45.0, 23.0],
	["plaza_zoom_max", 0.0, 0.0, 120.0, 17.5],
	["moradas_zoom_max", 95.0, 62.0, 120.0, 17.5],
	["razas_zoom_max", 20.0, -118.0, 120.0, 12.0],
]
const WARMUP_S := 3.0

var measure_s := 12.0
var lines: PackedStringArray = []


func _initialize() -> void:
	if OS.get_cmdline_user_args().has("rapido"):
		measure_s = 5.0
	DisplayServer.window_set_vsync_mode(DisplayServer.VSYNC_DISABLED)
	Engine.max_fps = 0
	change_scene_to_file("res://scenes/main.tscn")
	_run.call_deferred()


func _info(k: int) -> float:
	return float(RenderingServer.get_rendering_info(k))


func _run() -> void:
	while current_scene == null or current_scene.get_node_or_null("Game") == null or current_scene.get_node("Game").day_night == null:
		await process_frame
	var game = current_scene.get_node("Game")
	await NavReady.wait(self, game.player.get_world_3d().navigation_map)
	_header()
	lines.append("")
	lines.append("%-20s %7s %8s %9s %9s %8s %10s %8s %9s %9s" % ["escena", "FPS", "1% peor", "ms medio", "ms max",
		"draw", "triangulos", "objetos", "VRAM MB", "texturas"])
	var summary := []
	for s in SCENES:
		var r: Dictionary = await _scene(game, s)
		summary.append(r)
		lines.append("%-20s %7.1f %8.1f %9.2f %9.2f %8d %10d %8d %9.1f %9.1f" % [r.escena, r.fps, r.low1, r.ms, r.ms_max,
			r.draw_calls, r.triangulos, r.objetos, r.vram_mb, r.texturas_mb])
		print("BENCH ", JSON.stringify(r))
	lines.append("")
	lines.append("Objetivos (PARADA 1): zoom de juego (45 m) <= 1.200 draw calls y <= 300.000 triangulos;")
	lines.append("zoom maximo (120 m) <= 2.000 draw calls y <= 800.000 triangulos; VRAM total <= 600 MB.")
	lines.append("JSON: " + JSON.stringify(summary))
	var path := ProjectSettings.globalize_path("res://benchmark_resultados.txt")
	var f := FileAccess.open("res://benchmark_resultados.txt", FileAccess.WRITE)
	if f == null:
		path = ProjectSettings.globalize_path("user://benchmark_resultados.txt")
		f = FileAccess.open("user://benchmark_resultados.txt", FileAccess.WRITE)
	f.store_string("\n".join(lines) + "\n")
	f = null
	print("BENCH resultados en ", path)
	quit()


func _header() -> void:
	var v := Engine.get_version_info()
	var mem := OS.get_memory_info()
	lines.append("CONCORDIA - benchmark_resultados.txt (tools/benchmark.gd)")
	lines.append("Fecha: %s" % Time.get_datetime_string_from_system(false, true))
	lines.append("Godot: %s" % v.string)
	lines.append("Sistema: %s %s" % [OS.get_name(), OS.get_version()])
	lines.append("CPU: %s (%d hilos)" % [OS.get_processor_name(), OS.get_processor_count()])
	lines.append("Memoria fisica: %.1f GB" % (float(mem.get("physical", 0)) / 1073741824.0))
	lines.append("GPU: %s / %s" % [RenderingServer.get_video_adapter_vendor(), RenderingServer.get_video_adapter_name()])
	lines.append("API grafica: %s  Driver: %s" % [RenderingServer.get_video_adapter_api_version(), ", ".join(OS.get_video_adapter_driver_info())])
	lines.append("Renderizador: %s" % ProjectSettings.get_setting("rendering/renderer/rendering_method"))
	lines.append("Ventana: %s  Pantalla: %s  Vsync: desactivado" % [DisplayServer.window_get_size(), DisplayServer.screen_get_size()])
	lines.append("Escenas: %d s de calentamiento + %d s de medida cada una; la camara gira despacio alrededor del punto." % [WARMUP_S, measure_s])


func _scene(game, s: Array) -> Dictionary:
	game.day_night.hour = s[4]
	game.day_night.apply()
	var center: Vector3 = game.ground_at(s[1], -s[2])
	game.cam_rig.zoom = s[3]
	var t := 0.0
	var frames: PackedFloat32Array = []
	var dc := 0.0
	var tris := 0.0
	var objs := 0.0
	var n := 0
	var last := Time.get_ticks_usec()
	while t < WARMUP_S + measure_s:
		await process_frame
		var now := Time.get_ticks_usec()
		var dt := (now - last) / 1000000.0
		last = now
		t += dt
		# recorrido lento: el jugador da vueltas de 6 m de radio alrededor del punto (la camara le sigue)
		var a := t * 0.35
		game.player.global_position = game.ground_at(center.x + cos(a) * 6.0, center.z + sin(a) * 6.0) + Vector3(0, 0.05, 0)
		game.player.velocity = Vector3.ZERO
		if t >= WARMUP_S:
			frames.append(dt * 1000.0)
			dc += _info(RenderingServer.RENDERING_INFO_TOTAL_DRAW_CALLS_IN_FRAME)
			tris += _info(RenderingServer.RENDERING_INFO_TOTAL_PRIMITIVES_IN_FRAME)
			objs += _info(RenderingServer.RENDERING_INFO_TOTAL_OBJECTS_IN_FRAME)
			n += 1
	var sorted := frames.duplicate()
	sorted.sort()
	var total := 0.0
	for x in frames:
		total += x
	var ms := total / maxf(frames.size(), 1)
	var p99: float = sorted[int(sorted.size() * 0.99)] if sorted.size() > 0 else 0.0
	return {"escena": s[0], "zoom_m": s[3], "hora": s[4], "fotogramas": frames.size(),
		"fps": 1000.0 / maxf(ms, 0.001), "low1": 1000.0 / maxf(p99, 0.001), "ms": ms,
		"ms_max": sorted[sorted.size() - 1] if sorted.size() > 0 else 0.0,
		"draw_calls": int(dc / maxf(n, 1)), "triangulos": int(tris / maxf(n, 1)), "objetos": int(objs / maxf(n, 1)),
		"vram_mb": _info(RenderingServer.RENDERING_INFO_VIDEO_MEM_USED) / 1048576.0,
		"texturas_mb": _info(RenderingServer.RENDERING_INFO_TEXTURE_MEM_USED) / 1048576.0,
		"buffers_mb": _info(RenderingServer.RENDERING_INFO_BUFFER_MEM_USED) / 1048576.0}
