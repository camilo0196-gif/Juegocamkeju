extends SceneTree
## CONCORDIA - aristas compartidas por mas de 2 poligonos (clave a 1 cm) y poligonos degenerados en navigation/*.res
func _init() -> void:
	for f in DirAccess.get_files_at("res://navigation"):
		if not f.ends_with(".res"):
			continue
		var nm: NavigationMesh = load("res://navigation/" + f)
		var v := nm.get_vertices()
		var edges := {}
		var degen := 0
		for i in nm.get_polygon_count():
			var p := nm.get_polygon(i)
			var a := 0.0
			for k in range(1, p.size() - 1):
				a += (v[p[k]] - v[p[0]]).cross(v[p[k + 1]] - v[p[0]]).length() * 0.5
			if a < 0.0005:
				degen += 1
			for j in p.size():
				var x := v[p[j]].snapped(Vector3.ONE * 0.01)
				var y := v[p[(j + 1) % p.size()]].snapped(Vector3.ONE * 0.01)
				var key := [x, y] if str(x) < str(y) else [y, x]
				edges[str(key)] = edges.get(str(key), 0) + 1
		var bad := 0
		var ex := []
		for k in edges:
			if edges[k] > 2:
				bad += 1
				if ex.size() < 2: ex.append(k)
		var dupv := {}
		var nd := 0
		for p in v:
			var k := str(p.snapped(Vector3.ONE * 0.01))
			if dupv.has(k): nd += 1
			dupv[k] = true
		print(f, " polig ", nm.get_polygon_count(), " aristas>2 ", bad, " degenerados ", degen, " vertices duplicados ", nd, " ", ex)
	quit()
