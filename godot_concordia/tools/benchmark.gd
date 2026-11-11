extends SceneTree
## CONCORDIA - banco de pruebas de rendimiento para ejecutar en el PC del usuario (las cifras del servidor de pruebas no
## valen: no tiene tarjeta grafica). Escribe benchmark_resultados.txt en la carpeta del proyecto (o en user:// si no
## se puede escribir alli).
##
## Por nivel de calidad (scripts/quality.gd; por defecto Bajo, Medio y Alto) recorre escenas fijas con la camara de
## juego y mide FPS medio, 1 % peor (percentil 99 del tiempo de fotograma), tiempo de fotograma medio y maximo,
## draw calls, triangulos, objetos, memoria de video y chunks cargados. Al final de cada nivel, un paseo de 30 s a
## 6 m/s cruzando distritos mide los tirones de la carga por hilos (fotogramas > 50 ms y > 2,5 veces la mediana).
## Objetivo (2026-11-11): 30 FPS estables en Bajo con la GPU integrada (FPS medio >= 30 y 1 % peor >= 25 en todas
## las escenas). 60 FPS con 500 jugadores es objetivo de tarjeta dedicada (G8, servidor), no de esta prueba.
##
## Uso (sin abrir el editor), desde la carpeta godot_concordia:
##   Windows:  Godot_v4.7.2-stable_win64.exe --path . -s res://tools/benchmark.gd
##   Opciones: -- rapido            (5 s por escena en vez de 10)
##             -- niveles=Bajo      (solo esos niveles, separados por comas)
##   Renderizador Compatibility (OpenGL) para comparar: anade --rendering-method gl_compatibility antes de -s
## Durante la prueba la sincronizacion vertical se desactiva para medir el maximo real.
## API verificada en docs/reference/godot47 (RenderingServer.get_rendering_info, Performance, OS, DisplayServer).

const NavReady = preload("res://scripts/nav_ready.gd")

# nombre, x / y de Blender, zoom (metros visibles; se recorta al zoom maximo del nivel), hora
const SCENES := [
	["plaza", 0.0, 30.0, 45.0, 17.5],
	["mercado", 0.0, 100.0, 45.0, 17.5],
	["oficios", 125.0, 10.0, 45.0, 17.5],
	["moradas_ne", 95.0, 62.0, 45.0, 17.5],
	["moradas_ne_noche", 95.0, 62.0, 45.0, 23.0],
	["razas", 20.0, -118.0, 45.0, 12.0],
	["plaza_zoom_max", 0.0, 0.0, 120.0, 17.5],
	["moradas_so_zoom_max", -95.0, -62.0, 120.0, 17.5],
]
# paseo: puntos de Blender (x, y) a 6 m/s
const WALK := [[0.0, 30.0], [0.0, 100.0], [60.0, 95.0], [95.0, 62.0], [125.0, 10.0], [60.0, -40.0], [20.0, -118.0]]
const WALK_S := 30.0
const WARMUP_S := 3.0

var measure_s := 10.0
var levels: Array = ["Bajo", "Medio", "Alto"]
var lines: PackedStringArray = []


func _initialize() -> void:
	for a in OS.get_cmdline_user_args():
		if a == "rapido":
			measure_s = 5.0
		elif String(a).begins_with("niveles="):
			levels = Array(String(a).substr(8).split(",", false))
	DisplayServer.window_set_vsync_mode(DisplayServer.VSYNC_DISABLED)
	Engine.max_fps = 0
	change_scene_to_file("res://scenes/main.tscn")
	_run.call_deferred()


func _info(k: int) -> float:
	return float(RenderingServer.get_rendering_info(k))


func _run() -> void:
	while current_scene == null or current_scene.get_node_or_null("Game") == null or current_scene.get_node("Game").quality == null:
		await process_frame
	var game = current_scene.get_node("Game")
	await NavReady.wait(self, game.player.get_world_3d().navigation_map)
	_header(game)
	var all := {}
	var verdict: PackedStringArray = []
	for lv in levels:
		if not (lv in game.quality.LEVELS):
			continue
		game.quality.set_mode(lv, false)
		lines.append("")
		lines.append("== Nivel %s ==" % lv)
		lines.append("%-20s %6s %8s %8s %8s %6s %10s %7s %8s %7s" % ["escena", "FPS", "1% peor", "ms medio", "ms max",
			"draw", "triangulos", "objetos", "VRAM MB", "chunks"])
		var rows := []
		var ok := true
		for s in SCENES:
			var r: Dictionary = await _scene(game, s)
			rows.append(r)
			lines.append("%-20s %6.1f %8.1f %8.2f %8.2f %6d %10d %7d %8.1f %7d" % [r.escena, r.fps, r.low1, r.ms,
				r.ms_max, r.draw_calls, r.triangulos, r.objetos, r.vram_mb, r.chunks])
			print("BENCH ", lv, " ", JSON.stringify(r))
			if r.fps < 30.0 or r.low1 < 25.0:
				ok = false
		var w: Dictionary = await _walk(game)
		rows.append(w)
		lines.append("%-20s %6.1f %8.1f %8.2f %8.2f  tirones: %d   chunks cargados/descargados: %d / %d" % [
			"paseo_streaming", w.fps, w.low1, w.ms, w.ms_max, w.tirones, w.cargas, w.descargas])
		print("BENCH ", lv, " ", JSON.stringify(w))
		if w.fps < 30.0 or w.low1 < 25.0:
			ok = false
		all[lv] = rows
		verdict.append("%s: %s" % [lv, "CUMPLE 30 FPS estables" if ok else "NO llega a 30 FPS estables en alguna escena"])
	lines.append("")
	lines.append("Criterio: FPS medio >= 30 y 1 % peor >= 25 en todas las escenas y en el paseo.")
	for v in verdict:
		lines.append(v)
	lines.append("JSON: " + JSON.stringify(all))
	var path := ProjectSettings.globalize_path("res://benchmark_resultados.txt")
	var f := FileAccess.open("res://benchmark_resultados.txt", FileAccess.WRITE)
	if f == null:
		path = ProjectSettings.globalize_path("user://benchmark_resultados.txt")
		f = FileAccess.open("user://benchmark_resultados.txt", FileAccess.WRITE)
	if f:
		f.store_string("\n".join(lines) + "\n")
		f = null
	print("BENCH resultados en ", path)
	quit()


func _header(game) -> void:
	var v := Engine.get_version_info()
	var mem := OS.get_memory_info()
	var g: Dictionary = game.quality.gpu
	lines.append("CONCORDIA - benchmark_resultados.txt (tools/benchmark.gd)")
	lines.append("Fecha: %s" % Time.get_datetime_string_from_system(false, true))
	lines.append("Godot: %s" % v.string)
	lines.append("Sistema: %s %s" % [OS.get_name(), OS.get_version()])
	lines.append("CPU: %s (%d hilos)" % [OS.get_processor_name(), OS.get_processor_count()])
	lines.append("Memoria fisica: %.1f GB" % (float(mem.get("physical", 0)) / 1073741824.0))
	lines.append("GPU: %s / %s  (tipo: %s; nivel automatico: %s)" % [RenderingServer.get_video_adapter_vendor(),
		RenderingServer.get_video_adapter_name(), g.get("tipo", "?"), g.get("auto", "?")])
	lines.append("API grafica: %s  Driver: %s" % [RenderingServer.get_video_adapter_api_version(), ", ".join(OS.get_video_adapter_driver_info())])
	lines.append("Renderizador: %s (%s)" % [RenderingServer.get_current_rendering_method(), RenderingServer.get_current_rendering_driver_name()])
	lines.append("Ventana: %s  Pantalla: %s  Vsync: desactivado" % [DisplayServer.window_get_size(), DisplayServer.screen_get_size()])
	var city = game.city
	if city.stream:
		lines.append("Mundo horneado: %d chunks; mallas fusionadas por material (tools/build_world.gd)" % city.stream.chunks.size())
	else:
		lines.append("Ciudad de .glb sin hornear (scenes/concordia_glb.tscn)")
	lines.append("Escenas: %d s de calentamiento + %d s de medida; el jugador da vueltas de 6 m alrededor del punto." % [WARMUP_S, measure_s])


func _stats(frames: PackedFloat32Array) -> Dictionary:
	var sorted := frames.duplicate()
	sorted.sort()
	var total := 0.0
	for x in frames:
		total += x
	var ms := total / maxf(frames.size(), 1)
	var p99: float = sorted[int(sorted.size() * 0.99)] if sorted.size() > 0 else 0.0
	return {"fotogramas": frames.size(), "fps": 1000.0 / maxf(ms, 0.001), "low1": 1000.0 / maxf(p99, 0.001), "ms": ms,
		"ms_max": sorted[sorted.size() - 1] if sorted.size() > 0 else 0.0}


func _scene(game, s: Array) -> Dictionary:
	game.day_night.hour = s[4]
	game.day_night.apply()
	await game.prepare_area(s[1], -s[2])
	var center: Vector3 = game.ground_at(s[1], -s[2])
	game.player.global_position = center + Vector3(0, 0.05, 0)
	game.cam_rig.zoom = minf(s[3], game.cam_rig.zoom_max)
	game.city.ensure_loaded(center)
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
	var r := _stats(frames)
	r.merge({"escena": s[0], "zoom_m": game.cam_rig.zoom, "hora": s[4],
		"draw_calls": int(dc / maxf(n, 1)), "triangulos": int(tris / maxf(n, 1)), "objetos": int(objs / maxf(n, 1)),
		"vram_mb": _info(RenderingServer.RENDERING_INFO_VIDEO_MEM_USED) / 1048576.0,
		"texturas_mb": _info(RenderingServer.RENDERING_INFO_TEXTURE_MEM_USED) / 1048576.0,
		"buffers_mb": _info(RenderingServer.RENDERING_INFO_BUFFER_MEM_USED) / 1048576.0,
		"chunks": game.city.stream.stats.cargados if game.city.stream else 0})
	return r


func _walk(game) -> Dictionary:
	## paseo a 6 m/s por los puntos de WALK: la carga de chunks va por hilos; cuenta los tirones
	game.day_night.hour = 17.5
	game.day_night.apply()
	game.cam_rig.zoom = minf(45.0, game.cam_rig.zoom_max)
	var pts: Array = []
	for p in WALK:
		pts.append(Vector3(p[0], 0.0, -p[1]))
	await game.prepare_area(pts[0].x, pts[0].z)
	var st0: Dictionary = game.city.stream.stats.duplicate() if game.city.stream else {}
	var frames: PackedFloat32Array = []
	var hitches := 0
	var seg := 0
	var pos: Vector3 = pts[0]
	var t := 0.0
	var last := Time.get_ticks_usec()
	while t < WALK_S:
		await process_frame
		var now := Time.get_ticks_usec()
		var dt := (now - last) / 1000000.0
		last = now
		t += dt
		frames.append(dt * 1000.0)
		var step := 6.0 * minf(dt, 0.1)
		while step > 0.0 and seg < pts.size() - 1:
			var to: Vector3 = pts[seg + 1]
			var d := Vector2(to.x - pos.x, to.z - pos.z)
			if d.length() <= step:
				step -= d.length()
				pos = to
				seg += 1
			else:
				var dn := d.normalized() * step
				pos += Vector3(dn.x, 0, dn.y)
				step = 0.0
		if seg >= pts.size() - 1:
			seg = 0
			pos = pts[0]
		game.player.global_position = game.ground_at(pos.x, pos.z) + Vector3(0, 0.05, 0)
		game.player.velocity = Vector3.ZERO
	# tiron: fotograma de mas de 50 ms y de mas de 2,5 veces la mediana (con pocos FPS todos pasan de 50 ms)
	var sorted := frames.duplicate()
	sorted.sort()
	var med: float = sorted[sorted.size() / 2] if sorted.size() > 0 else 0.0
	for x in frames:
		if x > maxf(50.0, med * 2.5):
			hitches += 1
	var r := _stats(frames)
	var st1: Dictionary = game.city.stream.stats if game.city.stream else {}
	r.merge({"escena": "paseo_streaming", "tirones": hitches,
		"cargas": int(st1.get("cargas", 0)) - int(st0.get("cargas", 0)),
		"descargas": int(st1.get("descargas", 0)) - int(st0.get("descargas", 0)),
		"fallos_carga": int(st1.get("fallos", 0))})
	return r
