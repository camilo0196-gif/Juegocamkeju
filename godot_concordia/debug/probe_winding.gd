extends SceneTree
func _init():
	var b := BoxMesh.new()
	var arr := b.surface_get_arrays(0)
	var v: PackedVector3Array = arr[Mesh.ARRAY_VERTEX]
	var idx: PackedInt32Array = arr[Mesh.ARRAY_INDEX]
	var vol := 0.0
	var nd := 0.0
	var nrm: PackedVector3Array = arr[Mesh.ARRAY_NORMAL]
	for t in range(0, idx.size(), 3):
		var a := v[idx[t]]; var bb := v[idx[t+1]]; var c := v[idx[t+2]]
		vol += a.dot(bb.cross(c)) / 6.0
		nd += (bb - a).cross(c - a).normalized().dot(nrm[idx[t]])
	print("BoxMesh volumen=", vol, " dot(normal geom, normal vertice) medio=", nd / (idx.size() / 3))
	quit()
