extends Node
## CONCORDIA - niveles de calidad (Bajo / Medio / Alto) y deteccion de la GPU integrada (menu: ui/quality_menu.gd, F2).
##  - Bajo: sin sombras, sin glow ni SSAO, 70 % de resolucion 3D, LOD0 hasta 25 m y LOD1 hasta 70 m, radio de carga
##    de chunks 120 m, zoom maximo 60 m, 6 farolillos con luz, 300 copos de ceniza
##  - Medio: sombras a 70 m (2 cortes, atlas 2048), glow, FXAA, 85 %, LOD 40 / 100 m, carga 140 m, zoom 90 m
##  - Alto: lo de antes: sombras a 140 m (4 cortes, atlas 4096), glow, SSAO, MSAA 2x, 100 %, carga 170 m, zoom 120 m
##  - Auto (por defecto): GPU integrada (o de software) -> Bajo; dedicada -> Alto; sin datos -> Medio
##    RenderingServer.get_video_adapter_type() (con OpenGL siempre devuelve "otro": entonces se mira el nombre)
## La eleccion se guarda en user://calidad.cfg.
## API verificada en docs/reference/godot47 (class_renderingserver.txt, class_viewport.txt).

signal changed(level: String)

const CFG := "user://calidad.cfg"
const LEVELS := ["Bajo", "Medio", "Alto"]
const PRESETS := {
	"Bajo": {"escala_3d": 0.7, "sombras": false, "sombra_m": 0.0, "cortes": 0, "atlas": 1024, "glow": false,
		"ssao": false, "msaa": false, "fxaa": false, "lod0_m": 25.0, "lod1_m": 70.0, "carga_m": 120.0,
		"zoom_max": 60.0, "farolillos": 6, "ceniza": 300},
	"Medio": {"escala_3d": 0.85, "sombras": true, "sombra_m": 70.0, "cortes": 2, "atlas": 2048, "glow": true,
		"ssao": false, "msaa": false, "fxaa": true, "lod0_m": 40.0, "lod1_m": 100.0, "carga_m": 140.0,
		"zoom_max": 90.0, "farolillos": 10, "ceniza": 600},
	"Alto": {"escala_3d": 1.0, "sombras": true, "sombra_m": 140.0, "cortes": 4, "atlas": 4096, "glow": true,
		"ssao": true, "msaa": true, "fxaa": false, "lod0_m": 40.0, "lod1_m": 100.0, "carga_m": 170.0,
		"zoom_max": 120.0, "farolillos": 16, "ceniza": 900},
}
const INTEGRATED_NAMES := "(?i)(radeon\\s*\\(tm\\)\\s*graphics|radeon graphics|vega|radeon \\d{3}m|intel|uhd|iris|" \
		+ "llvmpipe|lavapipe|swiftshader|basic render)"

var main: Node
var game: Node
var mode := "auto"                  # "auto" o un nivel
var level := "Medio"
var gpu := {}


func setup(main_node: Node, game_node: Node) -> void:
	main = main_node
	game = game_node
	gpu = detect()
	var cf := ConfigFile.new()
	if cf.load(CFG) == OK:
		var m := String(cf.get_value("calidad", "modo", "auto"))
		if m == "auto" or m in LEVELS:
			mode = m
	set_mode(mode, false)


static func detect() -> Dictionary:
	var name := RenderingServer.get_video_adapter_name()
	var t := RenderingServer.get_video_adapter_type()
	var types := {RenderingDevice.DEVICE_TYPE_OTHER: "otro", RenderingDevice.DEVICE_TYPE_INTEGRATED_GPU: "integrada",
		RenderingDevice.DEVICE_TYPE_DISCRETE_GPU: "dedicada", RenderingDevice.DEVICE_TYPE_VIRTUAL_GPU: "virtual",
		RenderingDevice.DEVICE_TYPE_CPU: "software (CPU)"}
	var integrated := t == RenderingDevice.DEVICE_TYPE_INTEGRATED_GPU or t == RenderingDevice.DEVICE_TYPE_CPU
	if t == RenderingDevice.DEVICE_TYPE_OTHER or t == RenderingDevice.DEVICE_TYPE_VIRTUAL_GPU:
		integrated = RegEx.create_from_string(INTEGRATED_NAMES).search(name) != null
	var auto := "Bajo" if integrated else ("Alto" if t == RenderingDevice.DEVICE_TYPE_DISCRETE_GPU else "Medio")
	return {"nombre": name, "tipo": types.get(t, "?"), "integrada": integrated, "auto": auto,
		"metodo": RenderingServer.get_current_rendering_method(),
		"driver": RenderingServer.get_current_rendering_driver_name()}


func set_mode(m: String, save := true) -> void:
	mode = m
	level = String(gpu.get("auto", "Medio")) if m == "auto" else m
	apply(PRESETS[level])
	if save:
		var cf := ConfigFile.new()
		cf.set_value("calidad", "modo", mode)
		cf.save(CFG)
	print("CALIDAD ", mode, " -> ", level, "  GPU ", gpu.get("nombre", "?"), " (", gpu.get("tipo", "?"), ")")
	changed.emit(level)


func apply(q: Dictionary) -> void:
	var compat := String(gpu.get("metodo", "")) == "gl_compatibility"
	var vp := main.get_viewport()
	vp.scaling_3d_mode = Viewport.SCALING_3D_MODE_BILINEAR if compat or q.escala_3d >= 1.0 else Viewport.SCALING_3D_MODE_FSR
	vp.scaling_3d_scale = q.escala_3d
	vp.msaa_3d = Viewport.MSAA_2X if q.msaa else Viewport.MSAA_DISABLED
	vp.screen_space_aa = Viewport.SCREEN_SPACE_AA_FXAA if q.fxaa else Viewport.SCREEN_SPACE_AA_DISABLED
	var sun := main.get_node_or_null("Sun") as DirectionalLight3D
	if sun:
		sun.shadow_enabled = q.sombras
		if q.sombras:
			sun.directional_shadow_max_distance = q.sombra_m
			sun.directional_shadow_mode = DirectionalLight3D.SHADOW_PARALLEL_4_SPLITS if q.cortes >= 4 \
					else DirectionalLight3D.SHADOW_PARALLEL_2_SPLITS
			RenderingServer.directional_shadow_atlas_set_size(int(q.atlas), true)
	var we := main.get_node_or_null("WorldEnvironment") as WorldEnvironment
	if we and we.environment:
		we.environment.glow_enabled = q.glow
		we.environment.ssao_enabled = q.ssao and not compat
	if game:
		if game.city:
			game.city.apply_quality(q)
		if game.cam_rig:
			game.cam_rig.zoom_max = q.zoom_max
			game.cam_rig.zoom = minf(game.cam_rig.zoom, q.zoom_max)
		if game.day_night:
			game.day_night.max_lanterns = int(q.farolillos)
		if game.effects and game.effects.ash:
			game.effects.ash.amount = int(q.ceniza)
