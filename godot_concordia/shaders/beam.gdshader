// CONCORDIA - haz de luz aditivo (Faro y oculo del Crisol). Decision del usuario (PARADA 1): mezcla aditiva con
// alpha ~0,3, sin prueba de profundidad (se ve detras de los edificios, guia de orientacion), sin sombras, y un
// degradado que se desvanece hacia arriba; la base tambien se funde para que no corte en seco.
// Alturas en mundo (base_y, top_y): las pone scripts/materials_fix.gd con la caja de cada haz.
shader_type spatial;
render_mode blend_add, unshaded, cull_disabled, depth_test_disabled, depth_draw_never, shadows_disabled, fog_disabled;

uniform vec4 beam_color : source_color = vec4(0.561, 0.816, 1.0, 1.0);   // #8FD0FF
uniform float alpha = 0.3;
uniform float base_y = 0.0;
uniform float top_y = 80.0;
uniform float base_fade = 0.12;      // fraccion de la altura en la que la base aparece
uniform float top_power = 1.6;       // caida hacia arriba
uniform float pulse = 0.12;
uniform float pulse_speed = 0.8;

varying float h;

void vertex() {
	float y = (MODEL_MATRIX * vec4(VERTEX, 1.0)).y;
	h = clamp((y - base_y) / max(top_y - base_y, 0.01), 0.0, 1.0);
}

void fragment() {
	float fade = smoothstep(0.0, base_fade, h) * pow(1.0 - h, top_power);
	float soft = pow(abs(dot(normalize(NORMAL), VIEW)), 1.5);      // bordes del cilindro mas suaves
	float p = 1.0 - pulse + pulse * sin(TIME * pulse_speed * 6.2832 - h * 12.0);
	ALBEDO = beam_color.rgb * alpha * fade * soft * p;
}
