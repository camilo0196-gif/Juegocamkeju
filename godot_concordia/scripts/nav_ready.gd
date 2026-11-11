extends RefCounted
## CONCORDIA - espera a que el mapa de navegacion tenga TODAS las regiones de la ciudad y conectadas entre si.
## Las regiones (NavigationRegion3D, navegacion horneada en res://navigation/) se sincronizan en hilos aparte
## (iteraciones asincronas, Godot 4.7): las primeras iteraciones del mapa pueden salir sin las regiones grandes o
## sin las conexiones entre ellas. Se da por listo cuando:
##  1. el mapa y cada region activa tienen al menos una iteracion,
##  2. para cada region, el punto de malla mas cercano del MAPA a un punto suyo coincide con el de la region,
##  3. hay camino desde la primera region hasta un punto de cada una de las demas (red conectada),
##  4. y la iteracion del mapa no cambia durante 30 fotogramas de fisica.
## Funciones verificadas en docs/reference/godot47/class_navigationserver3d.txt.


static func _sample(r: NavigationRegion3D) -> Vector3:
	var nm := r.navigation_mesh
	var v := nm.get_vertices()
	var p := nm.get_polygon(nm.get_polygon_count() / 2)
	var c := Vector3.ZERO
	for i in p:
		c += v[i]
	return r.global_transform * (c / p.size())


static func is_ready(tree: SceneTree, map: RID) -> bool:
	if NavigationServer3D.map_get_iteration_id(map) < 1:
		return false
	var samples: Array[Vector3] = []
	for r in tree.current_scene.find_children("*", "NavigationRegion3D", true, false):
		var reg := r as NavigationRegion3D
		if not reg.enabled or reg.navigation_mesh == null or reg.navigation_mesh.get_polygon_count() == 0:
			continue
		var rid := reg.get_rid()
		if NavigationServer3D.region_get_iteration_id(rid) < 1:
			return false
		var p := _sample(reg)
		var rp := NavigationServer3D.region_get_closest_point(rid, p)
		var mp := NavigationServer3D.map_get_closest_point(map, p)
		if rp.distance_to(mp) > 0.05:
			return false
		samples.append(rp)
	return true


static func connected(tree: SceneTree, map: RID) -> bool:
	## camino desde la primera region a cada una de las demas (se llama una vez, cuando is_ready ya es cierto)
	var samples: Array[Vector3] = []
	for r in tree.current_scene.find_children("*", "NavigationRegion3D", true, false):
		var reg := r as NavigationRegion3D
		if reg.enabled and reg.navigation_mesh and reg.navigation_mesh.get_polygon_count() > 0:
			samples.append(NavigationServer3D.region_get_closest_point(reg.get_rid(), _sample(reg)))
	for i in range(1, samples.size()):
		var path := NavigationServer3D.map_get_path(map, samples[0], samples[i], true)
		if path.is_empty() or path[path.size() - 1].distance_to(samples[i]) > 0.5:
			return false
	return true


static func wait(tree: SceneTree, map: RID, max_frames: int = 6000) -> int:
	var stable := 0
	var last := -1
	for i in max_frames:
		var it := NavigationServer3D.map_get_iteration_id(map)
		if it != last:
			stable = 0
			last = it
		else:
			stable += 1
		if stable >= 30 and is_ready(tree, map) and connected(tree, map):
			return i
		await tree.physics_frame
	push_warning("NavReady: el mapa de navegacion no quedo listo en %d fotogramas" % max_frames)
	return -1
