extends SceneTree
## CONCORDIA - BoneMap de las librerias de animacion (PJ4) hacia SkeletonProfileHumanoid (56 huesos), para el
## retargeting de Godot al importar (Advanced Import Settings > Skeleton3D > Retarget > Bone Map: cargar el .tres).
##   res://animations/bonemap_ual1.tres  UAL 1 Standard (Quaternius, rig DEF-* estilo Rigify, 53 huesos)
##   res://animations/bonemap_ual2.tres  UAL 2 Standard (Quaternius, rig estilo Unreal, 65 huesos)
##   res://animations/bonemap_elfo.tres  esqueleto del elfo (PJ3: ya usa los nombres del perfil)
## Comprueba cada mapa contra el esqueleto real del .glb (GLTFDocument) e imprime los huesos del perfil sin asignar.
## godot --headless --path godot_concordia -s res://tools/make_bonemaps.gd
## API: docs/reference/godot47/class_bonemap.txt, class_skeletonprofilehumanoid.txt.

const SIDES := {"Left": ["L", "l"], "Right": ["R", "r"]}
const FINGERS_UAL1 := {"Index": "f_index", "Middle": "f_middle", "Ring": "f_ring", "Little": "f_pinky"}
const FINGERS_UAL2 := {"Index": "index", "Middle": "middle", "Ring": "ring", "Little": "pinky"}
const GLB := {
	"ual1": "../animations/ual/ual1/AnimationLibrary_Godot_Standard.glb",
	"ual2": "../animations/ual/ual2/UAL2_Standard.glb",
	"elfo": "../export/godot/pj_elfo_sanador_anim.glb",
}


func ual1() -> Dictionary:
	var m := {"Root": "root", "Hips": "DEF-hips", "Spine": "DEF-spine.001", "Chest": "DEF-spine.002",
		"UpperChest": "DEF-spine.003", "Neck": "DEF-neck", "Head": "DEF-head"}
	for side in SIDES:
		var s: String = SIDES[side][0]
		m[side + "Shoulder"] = "DEF-shoulder." + s
		m[side + "UpperArm"] = "DEF-upper_arm." + s
		m[side + "LowerArm"] = "DEF-forearm." + s
		m[side + "Hand"] = "DEF-hand." + s
		m[side + "ThumbMetacarpal"] = "DEF-thumb.01." + s
		m[side + "ThumbProximal"] = "DEF-thumb.02." + s
		m[side + "ThumbDistal"] = "DEF-thumb.03." + s
		for f in FINGERS_UAL1:
			m[side + f + "Proximal"] = "DEF-%s.01.%s" % [FINGERS_UAL1[f], s]
			m[side + f + "Intermediate"] = "DEF-%s.02.%s" % [FINGERS_UAL1[f], s]
			m[side + f + "Distal"] = "DEF-%s.03.%s" % [FINGERS_UAL1[f], s]
		m[side + "UpperLeg"] = "DEF-thigh." + s
		m[side + "LowerLeg"] = "DEF-shin." + s
		m[side + "Foot"] = "DEF-foot." + s
		m[side + "Toes"] = "DEF-toe." + s
	return m


func ual2() -> Dictionary:
	var m := {"Root": "root", "Hips": "pelvis", "Spine": "spine_01", "Chest": "spine_02", "UpperChest": "spine_03",
		"Neck": "neck_01", "Head": "Head"}
	for side in SIDES:
		var s: String = SIDES[side][1]
		m[side + "Shoulder"] = "clavicle_" + s
		m[side + "UpperArm"] = "upperarm_" + s
		m[side + "LowerArm"] = "lowerarm_" + s
		m[side + "Hand"] = "hand_" + s
		m[side + "ThumbMetacarpal"] = "thumb_01_" + s
		m[side + "ThumbProximal"] = "thumb_02_" + s
		m[side + "ThumbDistal"] = "thumb_03_" + s
		for f in FINGERS_UAL2:
			m[side + f + "Proximal"] = "%s_01_%s" % [FINGERS_UAL2[f], s]
			m[side + f + "Intermediate"] = "%s_02_%s" % [FINGERS_UAL2[f], s]
			m[side + f + "Distal"] = "%s_03_%s" % [FINGERS_UAL2[f], s]
		m[side + "UpperLeg"] = "thigh_" + s
		m[side + "LowerLeg"] = "calf_" + s
		m[side + "Foot"] = "foot_" + s
		m[side + "Toes"] = "ball_" + s
	return m


func skeleton_names(path: String) -> PackedStringArray:
	var doc := GLTFDocument.new()
	var state := GLTFState.new()
	var err := doc.append_from_file(ProjectSettings.globalize_path("res://" + path), state)
	if err != OK:
		push_error("no se pudo leer " + path)
		return PackedStringArray()
	var scene := doc.generate_scene(state)
	var sk := scene.find_children("*", "Skeleton3D", true, false)[0] as Skeleton3D
	var out := PackedStringArray()
	for i in sk.get_bone_count():
		out.append(sk.get_bone_name(i))
	scene.free()
	return out


func _init() -> void:
	var profile := SkeletonProfileHumanoid.new()
	var maps := {"ual1": ual1(), "ual2": ual2(), "elfo": {}}
	for i in profile.bone_size:
		var b := profile.get_bone_name(i)
		maps.elfo[b] = b
	var report := {}
	for key in maps:
		var bm := BoneMap.new()
		bm.profile = profile
		var names := skeleton_names(GLB[key])
		var missing := []
		var unmapped := []
		for i in profile.bone_size:
			var pb := profile.get_bone_name(i)
			if not maps[key].has(pb):
				unmapped.append(String(pb))
				continue
			var sb: String = maps[key][pb]
			if not names.has(sb):
				missing.append("%s -> %s" % [pb, sb])
				continue
			bm.set_skeleton_bone_name(pb, sb)
		var path := "res://animations/bonemap_%s.tres" % key
		var err := ResourceSaver.save(bm, path)
		report[key] = {"huesos_esqueleto": names.size(), "asignados": profile.bone_size - unmapped.size() - missing.size(),
			"sin_asignar_en_el_perfil": unmapped, "nombre_que_no_existe": missing, "archivo": path, "guardado": error_string(err)}
	print("BONEMAP ", JSON.stringify(report, " "))
	quit()
