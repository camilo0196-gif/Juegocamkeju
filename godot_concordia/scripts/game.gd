extends Node
## CONCORDIA - pegamento de la escena de prueba: acciones de entrada, jugador, camara, HUD y ciudad.
## Teclas: WASD mover, Shift correr, clic izquierdo ir andando, rueda zoom, Q / E girar la camara 90 grados,
## F1 HUD, T avanzar la hora (G4), R volver al inicio.

const ACTIONS := {
	"move_forward": [KEY_W, KEY_UP], "move_back": [KEY_S, KEY_DOWN], "move_left": [KEY_A, KEY_LEFT],
	"move_right": [KEY_D, KEY_RIGHT], "run": [KEY_SHIFT], "cam_rot_left": [KEY_Q], "cam_rot_right": [KEY_E],
	"toggle_hud": [KEY_F1], "time_advance": [KEY_T], "respawn": [KEY_R],
}
const SPAWN_BLENDER := Vector2(0.0, 30.0)        # plaza, al norte del Portal (Blender x, y)

@onready var city: Node3D = $"../Concordia"
var player: CharacterBody3D
var cam_rig: Node3D
var hud: CanvasLayer
var hour := 17.5


static func setup_input() -> void:
	for a in ACTIONS:
		if InputMap.has_action(a):
			continue
		InputMap.add_action(a)
		for k in ACTIONS[a]:
			var ev := InputEventKey.new()
			ev.physical_keycode = k
			InputMap.action_add_event(a, ev)


func _ready() -> void:
	setup_input()
	player = CharacterBody3D.new()
	player.name = "Player"
	player.set_script(preload("res://scripts/player.gd"))
	get_parent().add_child.call_deferred(player)
	cam_rig = Node3D.new()
	cam_rig.name = "IsoCamera"
	cam_rig.set_script(preload("res://scripts/iso_camera.gd"))
	get_parent().add_child.call_deferred(cam_rig)
	hud = CanvasLayer.new()
	hud.set_script(preload("res://ui/debug_hud.gd"))
	get_parent().add_child.call_deferred(hud)
	await get_tree().process_frame
	player.global_position = ground_at(SPAWN_BLENDER.x, -SPAWN_BLENDER.y) + Vector3(0, 0.1, 0)
	player.spawn = player.global_position
	player.cam_rig = cam_rig
	cam_rig.target = player
	cam_rig._apply(true)
	hud.game = self
	city.set_focus(player)


func ground_at(x: float, z: float) -> Vector3:
	var space: PhysicsDirectSpaceState3D = (get_parent() as Node3D).get_world_3d().direct_space_state
	var q := PhysicsRayQueryParameters3D.create(Vector3(x, 200, z), Vector3(x, -100, z))
	var hit: Dictionary = space.intersect_ray(q)
	return hit.position if hit else Vector3(x, 10, z)


func time_of_day_text() -> String:
	return "%02d:%02d" % [int(hour), int(fmod(hour, 1.0) * 60.0)]


func _unhandled_input(e: InputEvent) -> void:
	if e.is_action_pressed("respawn"):
		player.global_position = player.spawn
		player.velocity = Vector3.ZERO
