extends CanvasLayer
## CONCORDIA - HUD de depuracion (F1): FPS, tiempo de frame, draw calls, triangulos, objetos, VRAM, zona, posicion,
## zoom y hora del dia. Monitores verificados en la doc 4.7 (RenderingServer.get_rendering_info, Performance).

var label: Label
var game: Node
var _acc := 0.0


func _ready() -> void:
	layer = 50
	var panel := PanelContainer.new()
	panel.position = Vector2(10, 10)
	var sb := StyleBoxFlat.new()
	sb.bg_color = Color(0.05, 0.06, 0.07, 0.72)
	sb.set_content_margin_all(8)
	panel.add_theme_stylebox_override("panel", sb)
	label = Label.new()
	label.add_theme_font_size_override("font_size", 14)
	label.add_theme_color_override("font_color", Color("e8e4dc"))
	panel.add_child(label)
	add_child(panel)
	visible = true


func _unhandled_input(e: InputEvent) -> void:
	if e.is_action_pressed("toggle_hud"):
		visible = not visible


func snapshot() -> Dictionary:
	var rs := RenderingServer
	return {
		"fps": Engine.get_frames_per_second(),
		"frame_ms": snappedf(Performance.get_monitor(Performance.TIME_PROCESS) * 1000.0, 0.01),
		"draw_calls": rs.get_rendering_info(RenderingServer.RENDERING_INFO_TOTAL_DRAW_CALLS_IN_FRAME),
		"triangulos": rs.get_rendering_info(RenderingServer.RENDERING_INFO_TOTAL_PRIMITIVES_IN_FRAME),
		"objetos": rs.get_rendering_info(RenderingServer.RENDERING_INFO_TOTAL_OBJECTS_IN_FRAME),
		"vram_mb": snappedf(rs.get_rendering_info(RenderingServer.RENDERING_INFO_VIDEO_MEM_USED) / 1048576.0, 0.1),
		"texturas_mb": snappedf(rs.get_rendering_info(RenderingServer.RENDERING_INFO_TEXTURE_MEM_USED) / 1048576.0, 0.1),
	}


func _process(delta: float) -> void:
	_acc += delta
	if _acc < 0.25 or not visible or game == null:
		return
	_acc = 0.0
	var s := snapshot()
	var p: Vector3 = game.player.global_position
	label.text = "FPS %d   frame %.1f ms\ndraw calls %d   triangulos %s   objetos %d\nVRAM %.0f MB (texturas %.0f MB)\nzona: %s\nposicion (Godot) %.1f, %.1f, %.1f   [Blender %.1f, %.1f, %.1f]\nzoom %.0f m   hora %s\nF1 HUD  WASD/clic mover  Shift correr  Q/E girar  rueda zoom" % [
		s.fps, 1000.0 / maxf(s.fps, 1.0), s.draw_calls, _thousands(s.triangulos), s.objetos, s.vram_mb, s.texturas_mb,
		game.city.zone_at(p), p.x, p.y, p.z, p.x, -p.z, p.y, game.cam_rig.zoom, game.time_of_day_text()]


func _thousands(n: int) -> String:
	var s := str(n)
	var out := ""
	while s.length() > 3:
		out = "." + s.substr(s.length() - 3) + out
		s = s.substr(0, s.length() - 3)
	return s + out
