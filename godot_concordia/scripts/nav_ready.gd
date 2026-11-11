extends RefCounted
## CONCORDIA - espera a que el mapa de navegacion tenga TODAS las regiones de la ciudad.
## Las regiones (NavigationRegion3D de los .glb, -navmesh) se sincronizan en hilos aparte (iteraciones asincronas,
## Godot 4.7): las primeras iteraciones del mapa pueden salir sin las regiones grandes (Plaza 8.131 poligonos,
## Moradas 14.925). Se da por listo cuando, para cada region, el punto de malla mas cercano del MAPA a un punto de esa
## region coincide con el de la propia region (NavigationServer3D.region_get_closest_point / map_get_closest_point).


static func is_ready(tree: SceneTree, map: RID) -> bool:
	if NavigationServer3D.map_get_iteration_id(map) < 1:
		return false
	for r in tree.current_scene.find_children("*", "NavigationRegion3D", true, false):
		var rid: RID = (r as NavigationRegion3D).get_rid()
		if NavigationServer3D.region_get_iteration_id(rid) < 1:
			return false
		var nm: NavigationMesh = (r as NavigationRegion3D).navigation_mesh
		if nm == null or nm.get_polygon_count() == 0:
			continue
		var v := nm.get_vertices()
		var p := (r as NavigationRegion3D).global_transform * v[nm.get_polygon(nm.get_polygon_count() / 2)[0]]
		var rp := NavigationServer3D.region_get_closest_point(rid, p)
		var mp := NavigationServer3D.map_get_closest_point(map, p)
		if rp.distance_to(mp) > 0.05:
			return false
	return true


static func wait(tree: SceneTree, map: RID, max_frames: int = 6000) -> int:
	for i in max_frames:
		if is_ready(tree, map):
			return i
		await tree.physics_frame
	return -1
