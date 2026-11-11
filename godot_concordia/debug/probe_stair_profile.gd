extends SceneTree
## CONCORDIA - perfil de colision de una escalera a lo largo de su eje (marcador MARKER_<nombre>): altura del primer
## colisionador cada 0,25 m de -L a +L, con el nombre del cuerpo, y la de la malla de navegacion.
## godot --headless --path godot_concordia -s res://debug/probe_stair_profile.gd -- <MARKER_...> [L]

const NavReady = preload("res://scripts/nav_ready.gd")


func _initialize() -> void:
	change_scene_to_file("res://scenes/main.tscn")
	_run.call_deferred()


func _run() -> void:
	for i in 10:
		await physics_frame
	var a := OS.get_cmdline_user_args()
	var game = current_scene.get_node("Game")
	var map: RID = game.player.get_world_3d().navigation_map
	await NavReady.wait(self, map)
	var space: PhysicsDirectSpaceState3D = game.player.get_world_3d().direct_space_state
	var m := current_scene.find_child(a[0], true, false) as Node3D
	var L := float(a[1]) if a.size() > 1 else 6.0
	var f := -m.global_transform.basis.z
	f.y = 0
	f = f.normalized()
	print("PERFIL ", a[0], " pos ", m.global_position, " frente ", f)
	var s := -L
	while s <= L + 0.001:
		var p := m.global_position + f * s
		var hit := space.intersect_ray(PhysicsRayQueryParameters3D.create(Vector3(p.x, p.y + 6, p.z), Vector3(p.x, p.y - 6, p.z)))
		var c := NavigationServer3D.map_get_closest_point(map, Vector3(p.x, hit.position.y if hit else p.y, p.z))
		print("  s %5.2f  col %6.2f  %-48s  nav %6.2f (a %.2f m)" % [s, hit.position.y if hit else NAN,
			String(hit.collider.name).left(48) if hit else "-", c.y, Vector2(c.x - p.x, c.z - p.z).length()])
		s += 0.25
	quit()
