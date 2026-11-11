extends SceneTree
func _init():
	for d in ["plaza", "mercado", "oficios", "clases", "razas", "moradas"]:
		var root = (load("res://assets/terrain/glb/concordia_terrain_%s.glb" % d) as PackedScene).instantiate()
		for r in root.find_children("*", "NavigationRegion3D", true, false):
			var nm: NavigationMesh = r.navigation_mesh
			var v := nm.get_vertices()
			var edges := {}
			var dup_poly := 0
			var polys := {}
			for i in nm.get_polygon_count():
				var p := nm.get_polygon(i)
				var key := []
				for j in p.size():
					var a := v[p[j]].snapped(Vector3.ONE * 0.01)
					var b := v[p[(j + 1) % p.size()]].snapped(Vector3.ONE * 0.01)
					var k := str(a) + str(b) if str(a) < str(b) else str(b) + str(a)
					edges[k] = edges.get(k, 0) + 1
					key.append(str(a))
				key.sort()
				var pk := "".join(key)
				if polys.has(pk): dup_poly += 1
				polys[pk] = true
			var tri := 0
			var where := []
			for k in edges:
				if edges[k] > 2:
					tri += 1
					if where.size() < 4: where.append(k)
			print(d, " ", r.name, " polig ", nm.get_polygon_count(), " vert ", v.size(), " cell ", nm.cell_size, "/", nm.cell_height, " aristas>2 ", tri, " poligonos duplicados ", dup_poly, " ej ", where)
		root.free()
	quit()
