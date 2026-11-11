// CONCORDIA - terreno por mascaras (README_masks.txt). Sustituye a las superficies naturales de los TRN_City_Chunk_*
// (Ground_Cracked, Cobble_Concordia, Rock_Gray, Ash_Gray, Limestone_Worn) y TRN_ExteriorChunk_* (Ash_Ground,
// Ash_Gray, Rock_Gray). Las texturas y escalas UV son las de los materiales de Concordia importados (las pone
// scripts/materials_fix.gd). Mezcla suave entre capas con las mascaras de COLOR_0:
//   ciudad:   R muro de contencion (Limestone) · G calle (Cobble) · B roca · A ceniza · resto suelo (Ground_Cracked)
//             huertos/jardines: cobble_type 6 de TEXCOORD_2 (llega en CUSTOM0, con v invertida: tipo = floor(1 - y))
//   exterior: R ceniza oscura (tono) · G dunas y foso (Ash_Gray) · B roca · resto suelo de ceniza (Ash_Ground)
// Paleta: huertos en tierra labrada gris parda con verdes apagados (saturacion <= 0,35).
shader_type spatial;
render_mode cull_back, depth_draw_opaque;

uniform bool exterior = false;

uniform sampler2D ground_alb : source_color, filter_linear_mipmap_anisotropic, repeat_enable;
uniform sampler2D ground_nrm : hint_normal, filter_linear_mipmap_anisotropic, repeat_enable;
uniform sampler2D ground_rgh : hint_default_white, filter_linear_mipmap, repeat_enable;
uniform vec4 ground_uv = vec4(1.0, 1.0, 0.0, 0.0);
uniform sampler2D road_alb : source_color, filter_linear_mipmap_anisotropic, repeat_enable;
uniform sampler2D road_nrm : hint_normal, filter_linear_mipmap_anisotropic, repeat_enable;
uniform sampler2D road_rgh : hint_default_white, filter_linear_mipmap, repeat_enable;
uniform vec4 road_uv = vec4(1.0, 1.0, 0.0, 0.0);
uniform sampler2D rock_alb : source_color, filter_linear_mipmap_anisotropic, repeat_enable;
uniform sampler2D rock_nrm : hint_normal, filter_linear_mipmap_anisotropic, repeat_enable;
uniform sampler2D rock_rgh : hint_default_white, filter_linear_mipmap, repeat_enable;
uniform vec4 rock_uv = vec4(1.0, 1.0, 0.0, 0.0);
uniform sampler2D ash_alb : source_color, filter_linear_mipmap_anisotropic, repeat_enable;
uniform sampler2D ash_nrm : hint_normal, filter_linear_mipmap_anisotropic, repeat_enable;
uniform sampler2D ash_rgh : hint_default_white, filter_linear_mipmap, repeat_enable;
uniform vec4 ash_uv = vec4(1.0, 1.0, 0.0, 0.0);
uniform sampler2D wall_alb : source_color, filter_linear_mipmap_anisotropic, repeat_enable;
uniform sampler2D wall_nrm : hint_normal, filter_linear_mipmap_anisotropic, repeat_enable;
uniform sampler2D wall_rgh : hint_default_white, filter_linear_mipmap, repeat_enable;
uniform vec4 wall_uv = vec4(1.0, 1.0, 0.0, 0.0);

uniform vec3 garden_soil : source_color = vec3(0.47, 0.41, 0.35);
uniform vec3 garden_green : source_color = vec3(0.45, 0.50, 0.36);
uniform float furrow_period = 0.7;
uniform float blend_soft = 0.25;

varying vec3 world_pos;
varying float garden;

float hash(vec2 p) { return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
float vnoise(vec2 p) {
	vec2 i = floor(p);
	vec2 f = fract(p);
	vec2 u = f * f * (3.0 - 2.0 * f);
	return mix(mix(hash(i), hash(i + vec2(1.0, 0.0)), u.x), mix(hash(i + vec2(0.0, 1.0)), hash(i + vec2(1.0, 1.0)), u.x), u.y);
}

void vertex() {
	world_pos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
	float t = floor(1.0 - CUSTOM0.y + 0.002);
	garden = (!exterior && abs(t - 6.0) < 0.5) ? 1.0 : 0.0;
}

float w(float m) { return smoothstep(0.5 - blend_soft, 0.5 + blend_soft, m); }

void fragment() {
	vec4 m = COLOR;
	float w_wall = exterior ? 0.0 : w(m.r);
	float w_road = exterior ? 0.0 : w(m.g);
	float w_rock = w(m.b);
	float w_ash = exterior ? w(m.g) : w(m.a);
	float w_gard = garden * (1.0 - w_road) * (1.0 - w_wall);
	float sum = w_wall + w_road + w_rock + w_ash + w_gard;
	float w_ground = max(0.0, 1.0 - sum);
	float norm = 1.0 / max(sum + w_ground, 1e-4);

	vec2 uvg = UV * ground_uv.xy + ground_uv.zw;
	vec3 alb = vec3(0.0);
	vec3 nrm = vec3(0.0);
	float rgh = 0.0;
	vec3 g_alb = texture(ground_alb, uvg).rgb;
	vec3 g_nrm = texture(ground_nrm, uvg).rgb;
	float g_rgh = texture(ground_rgh, uvg).g;
	alb += g_alb * w_ground;
	nrm += g_nrm * w_ground;
	rgh += g_rgh * w_ground;
	if (w_road > 0.001) {
		vec2 uv = UV * road_uv.xy + road_uv.zw;
		alb += texture(road_alb, uv).rgb * w_road;
		nrm += texture(road_nrm, uv).rgb * w_road;
		rgh += texture(road_rgh, uv).g * w_road;
	}
	if (w_rock > 0.001) {
		vec2 uv = UV * rock_uv.xy + rock_uv.zw;
		alb += texture(rock_alb, uv).rgb * w_rock;
		nrm += texture(rock_nrm, uv).rgb * w_rock;
		rgh += texture(rock_rgh, uv).g * w_rock;
	}
	if (w_ash > 0.001) {
		vec2 uv = UV * ash_uv.xy + ash_uv.zw;
		alb += texture(ash_alb, uv).rgb * w_ash;
		nrm += texture(ash_nrm, uv).rgb * w_ash;
		rgh += texture(ash_rgh, uv).g * w_ash;
	}
	if (w_wall > 0.001) {
		vec2 uv = UV * wall_uv.xy + wall_uv.zw;
		alb += texture(wall_alb, uv).rgb * w_wall;
		nrm += texture(wall_nrm, uv).rgb * w_wall;
		rgh += texture(wall_rgh, uv).g * w_wall;
	}
	if (w_gard > 0.001) {
		// tierra labrada: surcos en X de mundo, tierra algo mas oscura y verdes apagados en los lomos
		float f = sin(world_pos.x * 6.2832 / furrow_period + vnoise(world_pos.xz * 0.5) * 2.0);
		float ridge = smoothstep(-0.2, 0.7, f);
		float n = vnoise(world_pos.xz * 1.7) * 0.6 + vnoise(world_pos.xz * 5.0) * 0.4;
		vec3 soil = mix(g_alb, garden_soil * (0.75 + 0.5 * g_alb), 0.65) * mix(0.72, 1.0, ridge);
		vec3 crop = garden_green * (0.75 + 0.45 * n);
		vec3 gard = mix(soil, crop, ridge * smoothstep(0.42, 0.62, n) * 0.85);
		alb += gard * w_gard;
		vec3 fn = normalize(vec3(-cos(world_pos.x * 6.2832 / furrow_period) * 0.35, 0.0, 1.0)) * 0.5 + 0.5;
		nrm += mix(g_nrm, fn, 0.6) * w_gard;
		rgh += 0.9 * w_gard;
	}
	alb *= norm;
	nrm *= norm;
	rgh *= norm;
	if (exterior) {
		alb *= 1.0 - 0.35 * w(m.r);     // ceniza oscura en depresiones y cauce seco
	}
	ALBEDO = alb;
	NORMAL_MAP = nrm;
	ROUGHNESS = clamp(rgh, 0.35, 1.0);
	METALLIC = 0.0;
}
