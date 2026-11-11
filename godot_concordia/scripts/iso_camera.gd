extends Node3D
## CONCORDIA - camara isometrica ortografica (G3).
## CAM_Iso de Blender: rotacion X = 54.736, Z = 45 grados (mira de SE a NO, el lado SE mas cerca). En Godot
## (Blender (x, y, z) -> Godot (x, z, -y)) la direccion de vision (-0.577, -0.577, -0.577) es la de una camara con
## rotacion (-35.264, 45, 0): comprobado en el calculo y con los marcadores de puertas (ver TEST_REPORT.md, G3).
## Rueda: zoom (tamano ortografico 15 - 120 m). Q / E: giro de 90 grados. Seguimiento suave del objetivo.

const PITCH := -35.264
const YAW := 45.0
const DIST := 120.0                 # distancia de la camara al objetivo a lo largo del eje de vision
const ZOOM_MIN := 15.0
const ZOOM_MAX := 120.0

@export var target_path: NodePath
var target: Node3D
var zoom := 40.0
## zoom maximo del nivel de calidad (scripts/quality.gd: Bajo 60, Medio 90, Alto 120)
var zoom_max := ZOOM_MAX
var yaw_steps := 0
var _yaw := YAW
var cam: Camera3D


func _ready() -> void:
	cam = Camera3D.new()
	cam.name = "Camera"
	cam.projection = Camera3D.PROJECTION_ORTHOGONAL
	cam.size = zoom
	cam.near = 1.0
	cam.far = 600.0
	cam.current = true
	add_child(cam)
	if not target_path.is_empty():
		target = get_node(target_path)
	_apply(true)


func _unhandled_input(e: InputEvent) -> void:
	if e is InputEventMouseButton and e.pressed:
		if e.button_index == MOUSE_BUTTON_WHEEL_UP:
			zoom = clampf(zoom / 1.12, ZOOM_MIN, zoom_max)
		elif e.button_index == MOUSE_BUTTON_WHEEL_DOWN:
			zoom = clampf(zoom * 1.12, ZOOM_MIN, zoom_max)
	elif e.is_action_pressed("cam_rot_left"):
		yaw_steps -= 1
	elif e.is_action_pressed("cam_rot_right"):
		yaw_steps += 1


func _process(delta: float) -> void:
	_apply(false, delta)


func _apply(snap: bool, delta: float = 0.0) -> void:
	var want_yaw := YAW + 90.0 * yaw_steps
	_yaw = want_yaw if snap else lerpf(_yaw, want_yaw, clampf(delta * 8.0, 0.0, 1.0))
	cam.size = zoom if snap else lerpf(cam.size, zoom, clampf(delta * 10.0, 0.0, 1.0))
	if target:
		var p := target.global_position
		global_position = p if snap else global_position.lerp(p, clampf(delta * 6.0, 0.0, 1.0))
	var basis := Basis.from_euler(Vector3(deg_to_rad(PITCH), deg_to_rad(_yaw), 0.0), EULER_ORDER_YXZ)
	cam.global_transform = Transform3D(basis, global_position + basis.z * DIST)


func forward_flat() -> Vector3:
	## "arriba" en pantalla proyectado al suelo (para mover el jugador con WASD)
	var f := -cam.global_transform.basis.z
	f.y = 0.0
	return f.normalized()


func view_dir() -> Vector3:
	return -cam.global_transform.basis.z
