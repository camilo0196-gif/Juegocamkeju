// CONCORDIA - agua del Cauce y de las fuentes (MAT_Water). Usa el normal map de MAT_Water importado, desplazado en
// dos direcciones (corriente del Cauce de MARKER_Cauce_Source a _Outlet: en el sentido de la u de la malla), color
// gris azulado apagado, poco rugosa. Opaca (el lecho no se ve: el Cauce es oscuro en la paleta).
shader_type spatial;
render_mode cull_back;

uniform sampler2D water_nrm : hint_normal, filter_linear_mipmap, repeat_enable;
uniform sampler2D water_alb : source_color, filter_linear_mipmap, repeat_enable;
uniform bool has_albedo = false;
uniform vec4 uv_xform = vec4(1.0, 1.0, 0.0, 0.0);
uniform vec3 deep : source_color = vec3(0.16, 0.20, 0.24);
uniform vec3 shallow : source_color = vec3(0.33, 0.40, 0.45);
uniform vec2 flow = vec2(0.06, 0.0);
uniform float normal_strength = 0.6;

void fragment() {
	vec2 uv = UV * uv_xform.xy + uv_xform.zw;
	vec3 n1 = texture(water_nrm, uv * 2.0 + flow * TIME).rgb;
	vec3 n2 = texture(water_nrm, uv * 3.1 - flow.yx * TIME * 0.7 + 0.37).rgb;
	vec3 n = normalize((n1 + n2) - 1.0);
	float fres = pow(1.0 - clamp(dot(NORMAL, VIEW), 0.0, 1.0), 3.0);
	vec3 base = mix(deep, shallow, fres);
	if (has_albedo) {
		base = mix(base, texture(water_alb, uv).rgb * shallow * 2.0, 0.25);
	}
	ALBEDO = base;
	NORMAL_MAP = n * 0.5 + 0.5;
	NORMAL_MAP_DEPTH = normal_strength;
	ROUGHNESS = 0.06;
	METALLIC = 0.0;
	SPECULAR = 0.6;
}
