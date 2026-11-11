extends SceneTree
## CONCORDIA - ensamble repetible de la ciudad (G2). Genera:
##   res://scenes/concordia.tscn  raiz Concordia (scripts/city.gd) con
##       Terrain   : concordia_terrain_{plaza,mercado,oficios,clases,razas,moradas,exterior}.glb
##       Wall      : concordia_wall_layout.glb (muralla ya colocada en Blender)
##       Buildings : bld_{portal,mercado,oficios,clases,razas,moradas_NE,_NO,_SE,_SO}.glb
##       Markers   : concordia_markers.glb (Marker3D con metadatos y grupos, ver tools/post_import.gd)
##   res://scenes/main.tscn  Main: Concordia + luz y entorno basicos (G4 los sustituye) + Game (scripts/game.gd)
## Cada .glb entra como instancia de su escena importada (no se copia nada): tras una nueva exportacion basta con
## sync_assets.py + import_settings.py + --import y volver a ejecutar este script.
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
	root.set("focus_path", NodePath(""))
	DirAccess.make_dir_recursive_absolute("res://scenes")
	var ps := PackedScene.new()
	ps.pack(root)
	var err := ResourceSaver.save(ps, "res://scenes/concordia.tscn")
	print("concordia.tscn ", error_string(err))
	root.free()
	_main()
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


func _main() -> void:
	var main := Node3D.new()
	main.name = "Main"
	var city := (load("res://scenes/concordia.tscn") as PackedScene).instantiate()
	main.add_child(city)
	city.owner = main
	var sun := DirectionalLight3D.new()
	sun.name = "Sun"
	sun.rotation_degrees = Vector3(-38.0, -150.0, 0.0)          # sol de tarde desde el oeste (provisional, G4)
	sun.light_color = Color("ffe2b8")
	sun.light_energy = 1.2
	sun.shadow_enabled = true
	sun.directional_shadow_max_distance = 140.0
	main.add_child(sun)
	sun.owner = main
	var we := WorldEnvironment.new()
	we.name = "WorldEnvironment"
	var env := Environment.new()
	var sky := Sky.new()
	var mat := ProceduralSkyMaterial.new()
	mat.sky_top_color = Color("6b7f96")
	mat.sky_horizon_color = Color("c9c3b6")
	mat.ground_horizon_color = Color("8e8a84")
	mat.ground_bottom_color = Color("4a4846")
	sky.sky_material = mat
	env.background_mode = Environment.BG_SKY
	env.sky = sky
	env.ambient_light_source = Environment.AMBIENT_SOURCE_SKY
	env.tonemap_mode = Environment.TONE_MAPPER_FILMIC
	env.glow_enabled = true
	env.glow_hdr_threshold = 1.0
	we.environment = env
	main.add_child(we)
	we.owner = main
	var game := Node.new()
	game.name = "Game"
	game.set_script(load("res://scripts/game.gd"))
	main.add_child(game)
	game.owner = main
	var ps := PackedScene.new()
	ps.pack(main)
	print("main.tscn ", error_string(ResourceSaver.save(ps, "res://scenes/main.tscn")))
	main.free()
