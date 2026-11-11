extends Control
## CONCORDIA - brujula del Faro (G5): cuando el cristal del Faro (FARO_Crystal) queda fuera de la pantalla, una flecha
## #8FD0FF en el borde apunta hacia el, con la distancia en metros. Dentro de la pantalla no se dibuja nada (el haz
## ya se ve). Se coloca en la capa del HUD (ui/debug_hud.gd la crea).

const COLOR := Color("8FD0FF")
var cam_rig: Node
var target: Node3D
var focus: Node3D


func _ready() -> void:
	set_anchors_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_IGNORE


func _process(_d: float) -> void:
	queue_redraw()


func _draw() -> void:
	if cam_rig == null or target == null:
		return
	var cam: Camera3D = cam_rig.cam
	var vp := get_viewport_rect().size
	var p := cam.unproject_position(target.global_position)
	var margin := 40.0
	if p.x > margin and p.y > margin and p.x < vp.x - margin and p.y < vp.y - margin:
		return
	var c := vp * 0.5
	var d := (p - c).normalized()
	var half := vp * 0.5 - Vector2(margin, margin)
	var s := minf(absf(half.x / maxf(absf(d.x), 0.001)), absf(half.y / maxf(absf(d.y), 0.001)))
	var at := c + d * s
	var n := Vector2(-d.y, d.x)
	draw_colored_polygon(PackedVector2Array([at + d * 16.0, at - d * 10.0 + n * 10.0, at - d * 10.0 - n * 10.0]), COLOR)
	if focus:
		var dist := Vector2(target.global_position.x - focus.global_position.x, target.global_position.z - focus.global_position.z).length()
		draw_string(ThemeDB.fallback_font, at - d * 34.0 - Vector2(22, -5), "Faro %d m" % int(dist), HORIZONTAL_ALIGNMENT_LEFT, -1, 14, COLOR)
