extends Node
## CONCORDIA - pegamento de la escena de prueba: acciones de entrada, jugador, camara, HUD y ciudad.
## Teclas: WASD mover, Shift correr, clic izquierdo ir andando, rueda zoom, Q / E girar la camara 90 grados,
## F1 HUD, F2 calidad grafica (scripts/quality.gd), T adelantar una hora (G4, scripts/day_night.gd), R volver al inicio.

const ACTIONS := {
	"move_forward": [KEY_W, KEY_UP], "move_back": [KEY_S, KEY_DOWN], "move_left": [KEY_A, KEY_LEFT],
	"move_right": [KEY_D, KEY_RIGHT], "run": [KEY_SHIFT], "cam_rot_left": [KEY_Q], "cam_rot_right": [KEY_E],
	"toggle_hud": [KEY_F1], "quality_menu": [KEY_F2], "time_advance": [KEY_T], "respawn": [KEY_R],
}
const SPAWN_BLENDER := Vector2(0.0, 30.0)        # plaza, al norte del Portal (Blender x, y)

@onready var city: Node3D = $"../Concordia"
var player: CharacterBody3D
var cam_rig: Node3D
var hud: CanvasLayer
var day_night: Node
var effects: Node
var quality: Node
var hour := 17.5:
	get:
		return day_night.hour if day_night else 17.5


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
	await prepare_area(SPAWN_BLENDER.x, -SPAWN_BLENDER.y)
	player.global_position = ground_at(SPAWN_BLENDER.x, -SPAWN_BLENDER.y) + Vector3(0, 0.1, 0)
	player.spawn = player.global_position
	player.cam_rig = cam_rig
	cam_rig.target = player
	cam_rig._apply(true)
	hud.game = self
	city.set_focus(player)
	# G4: dia y noche; G5: efectos y brujula del Faro
	day_night = Node.new()
	day_night.name = "DayNight"
	day_night.set_script(preload("res://scripts/day_night.gd"))
	get_parent().add_child(day_night)
	day_night.setup(get_parent(), city, player)
	effects = Node.new()
	effects.name = "Effects"
	effects.set_script(preload("res://scripts/effects.gd"))
	get_parent().add_child(effects)
	var fx: Dictionary = effects.setup(city, player, cam_rig, day_night)
	var compass := Control.new()
	compass.set_script(preload("res://ui/compass.gd"))
	compass.cam_rig = cam_rig
	compass.focus = player
	compass.target = city.find_child("FARO_Crystal", true, false)
	hud.add_child(compass)
	# calidad: Auto (GPU integrada -> Bajo), menu en F2
	quality = Node.new()
	quality.name = "Quality"
	quality.set_script(preload("res://scripts/quality.gd"))
	get_parent().add_child(quality)
	quality.setup(get_parent(), self)
	var layer := CanvasLayer.new()
	layer.name = "QualityLayer"
	layer.layer = 10
	get_parent().add_child(layer)
	var menu := PanelContainer.new()
	menu.set_script(preload("res://ui/quality_menu.gd"))
	menu.quality = quality
	menu.game = self
	layer.add_child(menu)
	print("FX ", JSON.stringify({"dia_noche": day_night.stats(), "efectos": fx}))


func prepare_area(x: float, z: float) -> void:
	## carga ya los chunks alrededor de (x, z) y espera dos pasos de fisica para que sus colisiones respondan
	## (teletransportes, herramientas). Con la ciudad de .glb no hace nada.
	if city.has_method("ensure_loaded"):
		city.ensure_loaded(Vector3(x, 0.0, z))
	for i in 2:
		await get_tree().physics_frame


func ground_at(x: float, z: float) -> Vector3:
	var space: PhysicsDirectSpaceState3D = (get_parent() as Node3D).get_world_3d().direct_space_state
	var q := PhysicsRayQueryParameters3D.create(Vector3(x, 200, z), Vector3(x, -100, z))
	var hit: Dictionary = space.intersect_ray(q)
	return hit.position if hit else Vector3(x, 10, z)


func time_of_day_text() -> String:
	return "%02d:%02d" % [int(hour), int(fmod(hour, 1.0) * 60.0)]


func _unhandled_input(e: InputEvent) -> void:
	if e.is_action_pressed("time_advance") and day_night:
		day_night.advance(1.0)
	if e.is_action_pressed("respawn"):
		if city.has_method("ensure_loaded"):
			city.ensure_loaded(player.spawn)
		player.global_position = player.spawn
		player.velocity = Vector3.ZERO
