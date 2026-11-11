extends SceneTree
func _init():
	var tot := 0
	var bad := 0
	for p in ["res://assets/props/glb/bld_props.glb", "res://assets/buildings/glb/bld_portal.glb", "res://assets/terrain/glb/concordia_terrain_plaza.glb"]:
		var root = (load(p) as PackedScene).instantiate()
		for mi in root.find_children("*", "MeshInstance3D", true, false):
			for s in mi.mesh.get_surface_count():
				var arr = mi.mesh.surface_get_arrays(s)
				var v: PackedVector3Array = arr[Mesh.ARRAY_VERTEX]
				var nr: PackedVector3Array = arr[Mesh.ARRAY_NORMAL]
				var idx: PackedInt32Array = arr[Mesh.ARRAY_INDEX]
				for t in range(0, idx.size(), 3):
					var a := v[idx[t]]
					var g := (v[idx[t+1]] - a).cross(v[idx[t+2]] - a)
					if g.length_squared() < 1e-12: continue
					tot += 1
					if g.dot(nr[idx[t]] + nr[idx[t+1]] + nr[idx[t+2]]) > 0.0: bad += 1
		root.free()
		print(p.get_file(), " triangulos ", tot, " invertidos ", bad)
	quit()
