// CONCORDIA - velo del Portal (PORTAL_Veil): lamina de agua magica #8FD0FF. UV: u 0..1 de lado a lado, v = altura
// (z / 11 m, TODO_GODOT). Ondas que suben despacio, borde de Fresnel mas brillante, alpha ~0,6, sin colision (la
// malla no tiene -colonly). Transparente: no escribe profundidad, se ordena con render_priority (materials).
shader_type spatial;
render_mode blend_mix, cull_disabled, depth_draw_never, specular_schlick_ggx;

uniform vec4 tint : source_color = vec4(0.561, 0.816, 1.0, 1.0);
uniform float alpha_base = 0.55;
uniform float emission_energy = 1.6;
uniform float speed = 0.25;

float wave(vec2 uv, float t) {
	return sin(uv.y * 18.0 - t * 2.2 + sin(uv.x * 7.0 + t) * 1.5) * 0.5 + 0.5;
}

void fragment() {
	float t = TIME * speed * 6.2832;
	float w = wave(UV, t) * 0.6 + wave(UV * vec2(1.7, 0.6) + 0.3, t * 0.7) * 0.4;
	float fres = pow(1.0 - abs(dot(normalize(NORMAL), VIEW)), 2.0);
	float edge = smoothstep(0.0, 0.06, UV.x) * smoothstep(1.0, 0.94, UV.x);
	ALBEDO = tint.rgb * 0.35;
	EMISSION = tint.rgb * emission_energy * (0.45 + 0.4 * w + 0.6 * fres);
	ROUGHNESS = 0.08;
	METALLIC = 0.0;
	ALPHA = clamp(alpha_base + 0.25 * fres + 0.1 * w, 0.0, 0.9) * edge;
	NORMAL_MAP = normalize(vec3(0.5 + 0.08 * cos(UV.y * 18.0 - t * 2.2), 0.5, 1.0));
}
