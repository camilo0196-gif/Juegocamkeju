extends CharacterBody3D
## CONCORDIA - jugador de prueba (capsula). WASD relativo a la camara; clic izquierdo: ir andando por la malla de
## navegacion (NavigationAgent3D). Gravedad, ajuste al suelo, subida de escalones de hasta 0,25 m (los pies de
## algunas escaleras tienen 14 cm; las escaleras -colonly son rampas). Si cae por debajo de -40 m vuelve al inicio.

const SPEED := 5.0
const RUN := 9.0
const GRAVITY := 20.0
const STEP_MAX := 0.25

var cam_rig: Node3D
var agent: NavigationAgent3D
var spawn: Vector3
var stuck_t := 0.0
var last_pos := Vector3.ZERO
var stats := {"respawns": 0, "atascos": 0, "pasos_subidos": 0}


func _ready() -> void:
	floor_max_angle = deg_to_rad(46.0)
	floor_snap_length = 0.35
	var col := CollisionShape3D.new()
	var cap := CapsuleShape3D.new()
	cap.radius = 0.35
	cap.height = 1.8
	col.shape = cap
	col.position.y = 0.9
	add_child(col)
	var mi := MeshInstance3D.new()
	var cm := CapsuleMesh.new()
	cm.radius = 0.35
	cm.height = 1.8
	var mat := StandardMaterial3D.new()
	mat.albedo_color = Color("8FD0FF")
	mat.emission_enabled = true
	mat.emission = Color("8FD0FF")
	mat.emission_energy_multiplier = 0.4
	cm.material = mat
	mi.mesh = cm
	mi.position.y = 0.9
	add_child(mi)
	agent = NavigationAgent3D.new()
	agent.path_desired_distance = 0.6
	agent.target_desired_distance = 0.6
	agent.radius = 0.35
	agent.height = 1.8
	add_child(agent)
	spawn = global_position


func _unhandled_input(e: InputEvent) -> void:
	if e is InputEventMouseButton and e.pressed and e.button_index == MOUSE_BUTTON_LEFT and cam_rig:
		var cam: Camera3D = cam_rig.cam
		var from := cam.project_ray_origin(e.position)
		var to := from + cam.project_ray_normal(e.position) * 1000.0
		var hit := get_world_3d().direct_space_state.intersect_ray(PhysicsRayQueryParameters3D.create(from, to))
		if hit:
			agent.target_position = hit.position


func _physics_process(delta: float) -> void:
	var input := Input.get_vector("move_left", "move_right", "move_back", "move_forward")
	var dir := Vector3.ZERO
	if input.length() > 0.05 and cam_rig:
		var f: Vector3 = cam_rig.forward_flat()
		var r := f.cross(Vector3.UP).normalized()
		dir = (f * input.y + r * input.x).normalized()
		agent.target_position = global_position              # el teclado cancela el clic
	elif not agent.is_navigation_finished():
		var nxt := agent.get_next_path_position()
		var d := nxt - global_position
		d.y = 0.0
		if d.length() > 0.05:
			dir = d.normalized()
	var spd := RUN if Input.is_action_pressed("run") else SPEED
	velocity.x = dir.x * spd
	velocity.z = dir.z * spd
	if not is_on_floor():
		velocity.y -= GRAVITY * delta
	else:
		velocity.y = maxf(velocity.y, -1.0)
	var before := global_position
	move_and_slide()
	if dir != Vector3.ZERO and is_on_wall() and (global_position - before).length() < spd * delta * 0.3:
		_try_step(dir * spd * delta)
	if dir != Vector3.ZERO:
		look_at(global_position + dir, Vector3.UP)
	if global_position.y < -40.0:
		global_position = spawn
		velocity = Vector3.ZERO
		stats.respawns += 1


func _try_step(motion: Vector3) -> void:
	## sube un escalon de hasta STEP_MAX: arriba, adelante, y vuelve a bajar hasta el suelo
	var t := global_transform
	if test_move(t, Vector3(0, STEP_MAX, 0)):
		return
	t.origin.y += STEP_MAX
	var fwd := motion.normalized() * maxf(motion.length(), 0.08)
	if test_move(t, fwd):
		return
	t.origin += fwd
	var col := KinematicCollision3D.new()
	if test_move(t, Vector3(0, -STEP_MAX - 0.05, 0), col):
		var land := t.origin + col.get_travel()
		if land.y > global_position.y + 0.02:
			global_position = land
			stats.pasos_subidos += 1
