extends PanelContainer
## CONCORDIA - menu de calidad (F2): Auto / Bajo / Medio / Alto (scripts/quality.gd), la GPU detectada y, mientras
## esta abierto, FPS, draw calls, objetos dibujados, chunks cargados y memoria de video.

var quality: Node
var game: Node
var _buttons := {}
var _info: Label
var _stats: Label
var _t := 0.0


func _ready() -> void:
	visible = false
	mouse_filter = Control.MOUSE_FILTER_STOP
	set_anchors_and_offsets_preset(Control.PRESET_TOP_RIGHT)
	position = Vector2(get_viewport().get_visible_rect().size.x - 380, 12)
	custom_minimum_size = Vector2(360, 0)
	var box := VBoxContainer.new()
	add_child(box)
	var title := Label.new()
	title.text = "Calidad grafica (F2 cierra)"
	box.add_child(title)
	var row := HBoxContainer.new()
	box.add_child(row)
	var group := ButtonGroup.new()
	for m in ["auto", "Bajo", "Medio", "Alto"]:
		var b := Button.new()
		b.text = "Auto" if m == "auto" else m
		b.toggle_mode = true
		b.button_group = group
		b.focus_mode = Control.FOCUS_NONE
		b.pressed.connect(_on_pick.bind(m))
		row.add_child(b)
		_buttons[m] = b
	_info = Label.new()
	_info.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	box.add_child(_info)
	_stats = Label.new()
	box.add_child(_stats)
	if quality:
		quality.changed.connect(func(_l): _refresh())
	_refresh()


func _on_pick(m: String) -> void:
	if quality:
		quality.set_mode(m)


func _refresh() -> void:
	if quality == null:
		return
	for m in _buttons:
		_buttons[m].button_pressed = (m == quality.mode)
	var g: Dictionary = quality.gpu
	_info.text = "GPU: %s (%s)\nRenderizador: %s / %s\nNivel actual: %s%s" % [g.get("nombre", "?"), g.get("tipo", "?"),
		g.get("metodo", "?"), g.get("driver", "?"), quality.level, "  (auto)" if quality.mode == "auto" else ""]


func _unhandled_input(e: InputEvent) -> void:
	if e.is_action_pressed("quality_menu"):
		visible = not visible
		_refresh()
		get_viewport().set_input_as_handled()


func _process(delta: float) -> void:
	if not visible:
		return
	_t -= delta
	if _t > 0.0:
		return
	_t = 0.5
	var chunks := "-"
	if game and game.city and game.city.stream:
		chunks = "%d / %d" % [game.city.stream.stats.cargados, game.city.stream.chunks.size()]
	_stats.text = "FPS %d   draw calls %d   objetos %d\nchunks cargados %s   VRAM %.0f MB" % [
		Engine.get_frames_per_second(),
		RenderingServer.get_rendering_info(RenderingServer.RENDERING_INFO_TOTAL_DRAW_CALLS_IN_FRAME),
		RenderingServer.get_rendering_info(RenderingServer.RENDERING_INFO_TOTAL_OBJECTS_IN_FRAME), chunks,
		RenderingServer.get_rendering_info(RenderingServer.RENDERING_INFO_VIDEO_MEM_USED) / 1048576.0]
