extends SceneTree
## CONCORDIA - ensamble repetible de la ciudad (G2). Genera:
##   res://scenes/concordia_glb.tscn  ciudad FUENTE (instancias de los .glb importados), raiz Concordia (scripts/city.gd) con
##       Terrain   : concordia_terrain_{plaza,mercado,oficios,clases,razas,moradas,exterior}.glb
##       Wall      : concordia_wall_layout.glb (muralla ya colocada en Blender)
##       Buildings : bld_{portal,mercado,oficios,clases,razas,moradas_NE,_NO,_SE,_SO}.glb
##       Markers   : concordia_markers.glb (Marker3D con metadatos y grupos, ver tools/post_import.gd)
##       Navigation: NavigationRegion3D por distrito con res://navigation/nav_*.res (tools/bake_navmesh.gd)
## La usan tools/build_world.gd (que hornea el mundo del juego: res://world/ + scenes/concordia.tscn + scenes/main.tscn)
## y tools/bake_navmesh.gd. El juego ya no instancia los .glb (ver tools/build_world.gd, arreglo VK -10).
## Cada .glb entra como instancia de su escena importada (no se copia nada): tras una nueva exportacion basta con
## sync_assets.py + import_settings.py + --import, volver a ejecutar este script y despues tools/build_world.gd.
## godot --headless --path godot_concordia -s res://tools/build_city.gd

const TERRAIN := ["plaza", "mercado", "oficios", "clases", "razas", "moradas", "exterior"]
const BUILDINGS := ["portal", "mercado", "oficios", "clases", "razas", "moradas_NE", "moradas_NO", "moradas_SE",
		"moradas_SO"]


func _init() -> void:
	var root := Node3D.new()
	root.name = "Concordia"
	root.set_script(load("res://scripts/city.gd"))
	var groups := {}
	for g in ["Terrain", "Wall", "Buildings", "Markers"]:
		var n := Node3D.new()
		n.name = g
		root.add_child(n)
		n.owner = root
		groups[g] = n
	for t in TERRAIN:
		_inst(root, groups.Terrain, "res://assets/terrain/glb/concordia_terrain_%s.glb" % t, "Terrain_" + t)
	_inst(root, groups.Wall, "res://assets/wall/glb/concordia_wall_layout.glb", "WallLayout")
	for b in BUILDINGS:
		_inst(root, groups.Buildings, "res://assets/buildings/glb/bld_%s.glb" % b, "Bld_" + b)
	_inst(root, groups.Markers, "res://assets/markers/glb/concordia_markers.glb", "Markers")
	# navegacion horneada en Godot (tools/bake_navmesh.gd): una region por distrito + camino de ronda
	var nav := Node3D.new()
	nav.name = "Navigation"
	root.add_child(nav)
	nav.owner = root
	for f in DirAccess.get_files_at("res://navigation"):
		if not f.ends_with(".res") or f.begins_with("nav_int_"):
			continue
		var r := NavigationRegion3D.new()
		r.name = f.get_basename().trim_prefix("nav_").capitalize().replace(" ", "_")
		r.navigation_mesh = load("res://navigation/" + f)
		r.add_to_group("nav_godot", true)
		nav.add_child(r)
		r.owner = root
	root.set("focus_path", NodePath(""))
	DirAccess.make_dir_recursive_absolute("res://scenes")
	var ps := PackedScene.new()
	ps.pack(root)
	var err := ResourceSaver.save(ps, "res://scenes/concordia_glb.tscn")
	print("concordia_glb.tscn ", error_string(err))
	root.free()
	quit()


func _inst(root: Node, parent: Node, path: String, name: String) -> void:
	var ps := load(path) as PackedScene
	if ps == null:
		push_error("no se pudo cargar " + path)
		return
	var n := ps.instantiate()
	n.name = name
	parent.add_child(n)
	n.owner = root
