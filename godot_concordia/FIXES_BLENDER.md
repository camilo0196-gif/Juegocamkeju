# FIXES_BLENDER — lo que hay que arreglar en los modelos (no se toca ningun .blend ni .glb de la ciudad)

Formato: objeto · que pasa · gravedad (bloqueante / alta / baja) · captura · como reproducirlo.
Origen de los datos: `debug/out/import_report.json` (tools/import_report.gd) y el registro de importacion de Godot 4.7.2.

## F1 · Imagenes con `uri` y `bufferView` a la vez (29 de 34 .glb, 761 imagenes)
- **Que pasa:** cada imagen externa (`../../textures/...`) tambien declara un `bufferView`. Godot avisa
  `Invalid image definition in glTF file using both 'uri' and 'bufferView'. 'uri' will take precedence.` en cada
  importacion (761 avisos). Funciona (usa la textura externa), pero el glTF no es valido y el .glb pesa de mas si
  el bufferView lleva la imagen.
- **Gravedad:** baja (no rompe nada; ensucia el registro y puede duplicar peso).
- **Captura:** no visual (aviso del importador; ver `debug/out/import1.log` al reimportar).
- **Reproducir:** abrir el proyecto o `godot --headless --path godot_concordia --import` con `.godot/` borrado.
- **Arreglo en Blender:** exportar con las imagenes solo externas (o solo embebidas), revisar `export_image_format`
  / `export_keep_originals` en `tools/blender/stage11_godot.py::export_glb`.

## F2 · Normal map en otro mapa UV ('UVBake') en 49 materiales de props importados
- **Objeto:** materiales `<MAT>__N_<prop>` de los props decimados (Quaternius / Avramania): props_int_mercado (21),
  props_int_oficios (14), int_morada_casa_grande (5), int_morada_casa_pequena (5), int_morada_habitacion (2),
  props_int_clases (2). Ejemplos: MAT_Iron_Black__N_Q_Chest_Wood, MAT_Wood_Dark__N_Q_WeaponStand,
  MAT_Straw__N_AV_Grain_Sack.
- **Que pasa:** el normal map usa `texCoord 1` y el albedo `texCoord 0`. StandardMaterial3D no admite un UV por
  textura: Godot avisa `File uses different UV maps for normal and base color textures` y aplica el normal map con
  el UV del albedo -> el relieve horneado sale en el sitio equivocado (manchas de relieve sin sentido).
- **Gravedad:** alta (visual en todos esos props; en G6 se ven de cerca en los interiores).
- **Captura:** pendiente (G6, interiores).
- **Reproducir:** importar props_int_mercado.glb; abrir el material MAT_Wood_Dark__N_Q_Chest_Wood.
- **Arreglo en Blender:** hornear el normal map sobre el UV0 del prop (o un atlas comun con UV0), no sobre
  'UVBake'. Alternativa en Godot (no aplicada): ShaderMaterial propio que lea el normal en UV2.

## F3 · TEST_Casa_12x9 exportada en bld_kit.glb sin colision
- **Que pasa:** la casa de prueba del kit (etapa 12) va en `bld_kit.glb` como edificio (metadata `building`) sin
  `-colonly`. No se instancia en la ciudad.
- **Gravedad:** baja (no se usa; sobra en el archivo).
- **Reproducir:** `-s res://tools/list_metadata.gd -- res://assets/buildings/glb/bld_kit.glb TEST_`.
- **Arreglo en Blender:** no exportar TEST_Casa_12x9 en bld_kit.glb.

## F4 · Caras sueltas con la normal opuesta al orden de vertices (~0,03 %)
- **Que pasa:** p. ej. 30 de 100.079 triangulos en bld_portal y 71 de 218.910 en concordia_terrain_plaza tienen la
  normal guardada contraria a su orden de vertices. Con CULL_BACK pueden verse como pequenos huecos.
- **Gravedad:** baja (pendiente de confirmar en capturas de G2/G3).
- **Reproducir:** `debug/probe_normals.gd`.
