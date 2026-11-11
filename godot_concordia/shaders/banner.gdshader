// CONCORDIA - estandartes y banderas al viento (MAT_Banner_*): la textura y el color son los del material importado;
// el vertice se mueve en Z local en proporcion a su distancia al lado sujeto (v = 0 arriba en los estandartes que
// cuelgan; u = 0 junto al mastil en las banderas), con dos ondas y una fase por posicion en el mundo.
shader_type spatial;
render_mode cull_disabled;

uniform sampler2D banner_alb : source_color, filter_linear_mipmap, repeat_enable;
uniform vec4 albedo_color : source_color = vec4(1.0);
uniform vec4 uv_xform = vec4(1.0, 1.0, 0.0, 0.0);
uniform bool flag_mode = false;     // false: cuelga de arriba (estandarte); true: sujeto al mastil por u = 0
uniform float amplitude = 0.12;
uniform float speed = 1.3;

void vertex() {
	vec3 wp = (MODEL_MATRIX * vec4(0.0, 0.0, 0.0, 1.0)).xyz;
	float phase = wp.x * 0.37 + wp.z * 0.23;
	float k = flag_mode ? UV.x : UV.y;
	float a = amplitude * k * (sin(TIME * speed * 6.2832 + k * 5.0 + phase) * 0.7 + sin(TIME * speed * 3.7 + k * 9.0 + phase) * 0.3);
	VERTEX += NORMAL * a;
}

void fragment() {
	vec4 c = texture(banner_alb, UV * uv_xform.xy + uv_xform.zw) * albedo_color;
	ALBEDO = c.rgb;
	ROUGHNESS = 0.9;
}
