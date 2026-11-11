extends SceneTree
func _init():
	for p in OS.get_cmdline_user_args():
		var root = (load(p) as PackedScene).instantiate()
		print("== ", p.get_file(), " hijos=", root.get_child_count())
		var k := 0
		for c in root.get_children():
			if k < 4:
				_dump(c, 1, 2)
			k += 1
		root.free()
	quit()
func _dump(n, d, maxd):
	var t: Transform3D = n.transform
	print("  ".repeat(d), n.name, " [", n.get_class(), "] pos=", t.origin.snapped(Vector3.ONE*0.01), " meta=", n.get_meta_list().size())
	if d < maxd:
		var k := 0
		for c in n.get_children():
			if k < 8: _dump(c, d+1, maxd)
			k += 1
