extends SceneTree
## CONCORDIA - canales del terreno importado: formato de superficie (CUSTOM0 = TEXCOORD_2?) y valores de cobble_type
func _init() -> void:
	var s: Node = (load("res://assets/terrain/glb/concordia_terrain_moradas.glb") as PackedScene).instantiate()
	var mi := s.find_children("TRN_City_Chunk_10_10*", "MeshInstance3D", true, false)[0] as MeshInstance3D
	print("malla ", mi.name)
	var m := mi.mesh
	for i in m.get_surface_count():
		var f: int = m.surface_get_format(i)
		var arr := m.surface_get_arrays(i)
		var types := {}
		var c0 = arr[Mesh.ARRAY_CUSTOM0]
		if c0 != null:
			var stride := 2
			if c0 is PackedFloat32Array:
				var n := 0
				for k in range(1, c0.size(), stride):
					var t := int(floor(c0[k]))
					types[t] = types.get(t, 0) + 1
		var col: PackedColorArray = arr[Mesh.ARRAY_COLOR] if arr[Mesh.ARRAY_COLOR] != null else PackedColorArray()
		var g := 0
		for c in col:
			if c.g > 0.5: g += 1
		print(m.surface_get_material(i).resource_name, " fmt custom0 ", (f & Mesh.ARRAY_FORMAT_CUSTOM0) != 0, " tipo ", (f >> Mesh.ARRAY_FORMAT_CUSTOM0_SHIFT) & Mesh.ARRAY_FORMAT_CUSTOM_MASK, " tipos cobble ", types, " verts ", col.size(), " G>0.5 ", g, " c0 ", typeof(c0))
	quit()
