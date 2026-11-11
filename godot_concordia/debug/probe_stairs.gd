extends SceneTree
## CONCORDIA - escalinatas STAIRS_Pass_3m_*: cota del terreno (sin la escalera) en los dos extremos frente a la escalera.
## godot --headless --path godot_concordia -s res://debug/probe_stairs.gd

func _initialize() -> void:
	change_scene_to_file("res://scenes/main.tscn")
	_run.call_deferred()


func _ground(space: PhysicsDirectSpaceState3D, p: Vector3, ex: Array[RID]) -> float:
	var q := PhysicsRayQueryParameters3D.create(Vector3(p.x, 200, p.z), Vector3(p.x, -100, p.z))
	q.exclude = ex
	var h := space.intersect_ray(q)
	return h.position.y if h else NAN


func _run() -> void:
	for i in 20:
		await process_frame
	var space := (current_scene as Node3D).get_world_3d().direct_space_state
	for n in current_scene.find_children("STAIRS_Pass_3m_*", "MeshInstance3D", true, false):
		if String(n.name).contains("_LOD"):
			continue
		var mi := n as MeshInstance3D
		var ex: Array[RID] = []
		for b in current_scene.find_children("*", "StaticBody3D", true, false):
			if String(b.get_path()).contains(String(mi.name)):
				ex.append((b as StaticBody3D).get_rid())
		# eje largo de la escalera en planta (local Y de Blender = -Z o X en Godot): se toma el mayor de la caja
		var box := mi.get_aabb()
		var xf := mi.global_transform
		var c := box.get_center()
		var ax := Vector3(box.size.x * 0.5, 0, 0) if box.size.x > box.size.z else Vector3(0, 0, box.size.z * 0.5)
		var a := xf * (c - ax)
		var b := xf * (c + ax)
		var lo := xf * Vector3(c.x, box.position.y, c.z)
		var hi := xf * Vector3(c.x, box.end.y, c.z)
		var ga := _ground(space, a + (a - b).normalized() * 1.0, ex)
		var gb := _ground(space, b + (b - a).normalized() * 1.0, ex)
		var gc := _ground(space, xf * c, ex)
		print("STAIRS %s centro Blender (%.1f, %.1f) caja y %.2f..%.2f | suelo extremo A %.2f, B %.2f, bajo el centro %.2f | escalones %d" % [
			mi.name, (xf * c).x, -(xf * c).z, lo.y, hi.y, ga, gb, gc, ex.size()])
	quit()
