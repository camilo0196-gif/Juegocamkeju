extends SceneTree
## CONCORDIA - escena de comparacion: main.tscn con la ciudad de .glb (scenes/concordia_glb.tscn) en lugar del mundo
## horneado -> res://debug/out/main_glb.tscn (para capture_tour.gd escena=res://debug/out/main_glb.tscn)
func _initialize() -> void:
	var main := (load("res://scenes/main.tscn") as PackedScene).instantiate()
	var old := main.get_node("Concordia")
	var c := (load("res://scenes/concordia_glb.tscn") as PackedScene).instantiate()
	main.remove_child(old)
	old.free()
	main.add_child(c)
	main.move_child(c, 0)
	c.owner = main
	var ps := PackedScene.new()
	ps.pack(main)
	print("main_glb ", error_string(ResourceSaver.save(ps, "res://debug/out/main_glb.tscn")))
	main.free()
	quit()
