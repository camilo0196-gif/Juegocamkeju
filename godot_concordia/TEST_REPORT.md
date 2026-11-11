# TEST_REPORT — Concordia en Godot 4.7.2

Entorno de pruebas de esta sesion: contenedor en la nube, CPU de 4 nucleos, 15 GB de RAM, **sin GPU**: Godot 4.7.2
oficial (SHA512 comprobado) con Vulkan por software (Mesa llvmpipe / lavapipe). Las capturas son fieles a Forward+;
**los FPS medidos aqui no valen** (render por CPU): las cifras de rendimiento finales se toman en el PC del usuario.

## G0 · Inventario y proyecto

Exportaciones usadas (`tools/sync_assets.py`, MANIFEST con sha256 en `assets/MANIFEST.txt`):
- `export/godot_v28/` (exportada en esta fase desde `concordia_v28.blend` sin tocar el .blend: 18 .glb, 369 edificios,
  606.054 tris LOD0, 1.407 puertas, 13 tapadas = las 13 residuales aceptadas, 217 materiales todos MAT_* de Concordia).
- `export/godot/` para lo que la etapa 28 no cambio: terreno exterior y muralla (2026-11-05), interiores
  (int_banco, 3 plantillas de Moradas), props de interior, personaje.
- Inventario completo con tamano, fecha, nodos, tris, sufijos, LOD y claves de extras: `docs/reports/inventario_glb.md`.

Que hay: terreno por distrito (6) + exterior; muralla (kit + colocada `concordia_wall_layout`); bld_portal (Portal,
Atrio, Obelisco, Faro con cristal y haz, Santuario, Salon de las Hazanas, puentes y escaleras de la plaza, tubos de luz
ruta oeste), bld_mercado, bld_oficios, bld_clases, bld_razas, bld_moradas NE/NO/SE/SO (283 casas, 1.398 viviendas),
bld_kit, bld_props, concordia_markers (667 marcadores, 24 familias), int_banco, 3 interiores de Moradas, props de
interior (mano, mercado, oficios, clases, vitrinas), personaje (cuerpo, ropa, rig con 10 poses).

**Faltan:** `personaje_elfo_base.glb` con animaciones (solo hay 10 poses fijas en pj_elfo_rig.glb) -> G8 se salta;
la Universal Animation Library de Quaternius no esta descargada; interiores de Santuario, Salon y del resto de
edificios con interior=true (solo existen el Banco y las 3 plantillas de Moradas); modelo propio del farol de calle
(solo LANTERN_Shard en las Moradas y arcos).

Lista de tareas: `TAREAS_GODOT.md` (todos los `[ ]` de TODO_GODOT.txt repartidos por fase).

## G1 · Importacion

Ajustes repetibles: `tools/import_settings.py` (reescribe los .import) + `tools/post_import.gd` (EditorScenePostImport),
todo verificado en la documentacion oficial 4.7 (`docs/reference/godot47/`). Escalas 1.0, sufijos activos, tangentes,
sin LOD automatico, sombra de malla, texturas VRAM Compressed con mipmaps (35 normales RGTC detectadas por los
materiales), opacos a una cara, extras como metadatos.

Resultado (34 .glb, 2,346,722 triangulos en total sumando todos los LOD):

| archivo | nodos | mallas | tris | colisiones | navmesh | oclusores | LOD1/LOD2 | nodos con extras |
|---|---|---|---|---|---|---|---|---|
| bld_clases.glb | 433 | 286 | 106,156 | 21 | 0 | 0 | 42/34 | 144 |
| bld_kit.glb | 120 | 99 | 21,102 | 8 | 0 | 0 | 10/10 | 56 |
| bld_mercado.glb | 296 | 193 | 106,930 | 31 | 0 | 0 | 31/28 | 46 |
| bld_moradas_NE.glb | 2884 | 1368 | 118,916 | 96 | 0 | 0 | 171/96 | 2043 |
| bld_moradas_NO.glb | 2859 | 1359 | 113,859 | 97 | 0 | 0 | 171/97 | 2013 |
| bld_moradas_SE.glb | 2685 | 1278 | 105,644 | 94 | 0 | 0 | 161/94 | 1878 |
| bld_moradas_SO.glb | 2859 | 1359 | 118,998 | 97 | 0 | 0 | 171/97 | 2013 |
| bld_oficios.glb | 294 | 197 | 79,157 | 20 | 0 | 0 | 33/27 | 69 |
| bld_portal.glb | 463 | 314 | 96,674 | 52 | 0 | 0 | 51/49 | 172 |
| bld_props.glb | 53 | 51 | 3,688 | 0 | 0 | 0 | 0/0 | 0 |
| bld_razas.glb | 801 | 509 | 159,821 | 76 | 0 | 0 | 102/95 | 122 |
| concordia_markers.glb | 668 | 0 | 0 | 0 | 0 | 0 | 0/0 | 667 |
| concordia_terrain_clases.glb | 47 | 27 | 80,725 | 9 | 1 | 0 | 9/9 | 37 |
| concordia_terrain_exterior.glb | 906 | 905 | 283,562 | 0 | 0 | 0 | 296/296 | 888 |
| concordia_terrain_mercado.glb | 51 | 29 | 77,400 | 10 | 1 | 0 | 9/9 | 40 |
| concordia_terrain_moradas.glb | 136 | 74 | 291,653 | 30 | 1 | 0 | 22/22 | 105 |
| concordia_terrain_oficios.glb | 77 | 41 | 132,145 | 17 | 1 | 0 | 11/11 | 59 |
| concordia_terrain_plaza.glb | 94 | 42 | 118,849 | 25 | 1 | 0 | 9/9 | 68 |
| concordia_terrain_razas.glb | 47 | 27 | 79,186 | 9 | 1 | 0 | 9/9 | 37 |
| concordia_wall_kit.glb | 57 | 33 | 24,186 | 10 | 0 | 1 | 11/11 | 13 |
| concordia_wall_layout.glb | 314 | 105 | 107,132 | 104 | 0 | 0 | 0/0 | 52 |
| int_banco.glb | 685 | 445 | 25,936 | 1 | 1 | 0 | 0/0 | 273 |
| int_morada_casa_grande.glb | 78 | 25 | 10,148 | 1 | 1 | 0 | 0/0 | 68 |
| int_morada_casa_pequena.glb | 58 | 18 | 6,623 | 1 | 1 | 0 | 0/0 | 48 |
| int_morada_habitacion.glb | 45 | 11 | 3,366 | 1 | 1 | 0 | 0/0 | 36 |
| pj_elfo_cuerpo.glb | 8 | 7 | 3,500 | 0 | 0 | 0 | 0/0 | 7 |
| pj_elfo_rig.glb | 18 | 14 | 7,250 | 0 | 0 | 0 | 0/0 | 14 |
| pj_elfo_sanador_equipado.glb | 15 | 11 | 6,250 | 0 | 0 | 0 | 0/0 | 14 |
| pj_sanador_ropa.glb | 8 | 7 | 3,750 | 0 | 0 | 0 | 0/0 | 7 |
| props_int_clases.glb | 36 | 13 | 10,934 | 11 | 0 | 0 | 0/0 | 13 |
| props_int_mano.glb | 48 | 18 | 5,046 | 14 | 0 | 0 | 0/0 | 19 |
| props_int_mercado.glb | 64 | 36 | 20,205 | 13 | 0 | 0 | 0/0 | 37 |
| props_int_oficios.glb | 55 | 26 | 17,097 | 14 | 0 | 0 | 0/0 | 26 |
| props_trophy_cases.glb | 34 | 9 | 834 | 0 | 0 | 0 | 3/3 | 27 |

- Importacion: **0 errores**. Avisos: 761 `uri + bufferView` (F1) y 49 `normal map en otro UV` (F2) -> FIXES_BLENDER.md.
- Extras: legibles como metadata `extras` (y claves sueltas); `tools/list_metadata.gd` los lista con filtro por
  prefijo y clave. Ej.: `occludes_iso` en SALON_HAZANAS_Body/_Roof; `interior` en 102 marcadores MARKER_Bld_*.
- Materiales sin textura de albedo: los LOD2 (`MAT_LOD2_*`, color plano a proposito), emisivos (Window_Warm,
  Pipe_Light_Core, Rune_Glow, Obelisk_Mark...), MAT_Void, Bronze_Aged, Straw, Herb_Green: colores planos de Blender,
  no texturas perdidas (ninguna textura referenciada falta: 0 errores de carga).
- Normales: ninguna malla invertida (>50 % de caras); caras sueltas ~0,03 % (F4).
- Mallas sin colision: solo TEST_Casa_12x9 (casa de prueba del kit, F3). Exterior sin colision (no transitable).

Problemas abiertos de G0-G1: F1-F4 (FIXES_BLENDER.md); la ciudad v28 se exporto a una carpeta nueva por decision del
usuario; G8 sin animaciones.

## G2 · Ensamble de la ciudad

`tools/build_city.gd` genera `scenes/concordia.tscn` (7 terrenos, muralla colocada, 9 bld_*, marcadores) y
`scenes/main.tscn` (ciudad + sol + entorno + Game). `scripts/city.gd` al arrancar: 883 unidades de LOD
(`scripts/lod_manager.gd`, por distancia en planta al jugador: LOD0 < 40 m, LOD1 < 100 m, LOD2 resto, margen 5 m;
la distancia de una camara ortografica no sirve para elegir LOD), 16 NavigationLink3D (parejas NAVLINK_*_Start/_End),
360 BoxOccluder3D al 80 % dentro de los cuerpos grandes (> 5 x 5 x 4 m). Preparacion: ~40 ms.

Escena en marcha: **16.310 nodos** (8.114 MeshInstance3D, 5.403 Marker3D, 824 Node3D, 788 StaticBody3D,
360 OccluderInstance3D, 6 NavigationRegion3D, 16 NavigationLink3D).

Medidas de render (Forward+, 1600 x 900, sombras del sol a 140 m; `capture_tour.gd`, `debug/out/tour/g2_medidas.json`):

| punto (zoom) | draw calls | triangulos visibles | objetos | LOD0/1/2 (unidades) |
|---|---|---|---|---|
| plaza (60 m) | 1.270 | 446.227 | 1.869 | 11 / 78 / 794 |
| plaza (120 m, el mas abierto) | 2.793 | 757.641 | 3.374 | 10 / 60 / 813 |
| mercado (60 m) | 1.630 | 444.686 | 2.522 | 13 / 108 / 762 |
| moradas NE (60 m) | 2.771 | 537.711 | 5.126 | 40 / 109 / 734 |
| moradas SO (60 m) | 3.104 | 483.318 | 5.521 | 39 / 118 / 726 |
| razas / oficios / clases (60 m) | 2.916 / 2.193 / 1.940 | 528.330 / 490.608 / 391.446 | 3.834 / 3.217 / 3.074 | |

- Las Moradas son lo mas caro en draw calls (~3.100): miles de mallas pequenas (puertas, balcones, faroles). Se
  ataca en G7 (MultiMesh / fusion por casa) — medir antes en el PC del usuario.
- **VRAM:** 436,6 MB en total; "texturas" 291 MB = **161 MB de texturas de materiales** (69 texturas unicas de la
  ciudad: 55 BC1 + 17 RGTC normales; limite acordado 220 MB: cumple) + 130 MB del motor (sombras, cielo, buffers;
  medido con la escena sin ciudad, `debug/probe_vram.gd`).
- Orientacion iso comprobada: camara (-35,264, 45, 0), mira (-0,577, -0,577, -0,577); Salon de las Hazanas (SE) a
  75,3 m, Santuario (NO) a 182,3 m.
- Revisadas las 15 capturas del recorrido. Bien: Faro, velo del Portal, Salon, Mercado, Oficios, Clases, Razas,
  Moradas, Puerta del Alba, puentes del Cauce. Mal: escalinatas de paso (F6), parcelas de la plaza (F7); pendientes de
  G4/G5 (no son fallos del modelo): huertos como tierra (shader de mascaras), haz del Crisol/Faro como bloque cian
  opaco que tapa la fuente del Mercado (material ADD), Obelisco negro (material encendido por pisos).

## G3 · Camara, jugador, HUD y prueba de caminata

- Camara iso ortografica (`scripts/iso_camera.gd`): zoom 15-120 m con la rueda, Q / E giran 90 grados.
- Jugador de prueba (`scripts/player.gd`): capsula 0,35 x 1,8, WASD relativo a la camara, Shift corre, clic izquierdo
  anda por la malla de navegacion, pendiente maxima 46 grados, sube escalones de hasta 0,25 m, R vuelve al inicio.
- HUD F1 (`ui/debug_hud.gd`): FPS, ms, draw calls, triangulos, objetos, VRAM, zona, posicion (Godot y Blender), zoom,
  hora.
- **Malla de navegacion asincrona:** Godot 4.7 sincroniza las regiones en hilos aparte; la Plaza (8.131 poligonos)
  y las Moradas (14.925) tardan ~2,3 s en entrar en el mapa. Antes de eso los caminos salen vacios o cortos.
  `scripts/nav_ready.gd` espera a que esten todas (lo usan la prueba y lo usaran los NPC).
- Ejecucion del proyecto: `--quit-after 900` sin ventana y `--quit-after 300` con Vulkan: **0 errores, 0 avisos.**

### Prueba de caminata (`tools/walk_test.gd`, rutas de `tools/walk_routes.py`)

El jugador recorre con fisica real (60 Hz, `--fixed-fps 60`) 314 rutas: 8 avenidas, 8 rondas (r100 y r150),
8 diagonales, 26 callejones, 26 callejones con escalera, 36 cruces de plazas, 5 puentes, 4 arcos, 10 escalinatas,
76 escaleras de terraza, 32 escaleras laterales, 4 monumentales, 4 puertas de la muralla y 67 tramos por las calles de
las Moradas. Resultado: **553 tramos, 475 bien (86 %), 6,7 km andados**, 0 caidas al vacio, 0 respawns.

| problema | cuantos | donde |
|---|---|---|
| atasco | 63 | escaleras de las Moradas (laterales de zancas/pretiles, 33), plazas con fuente o puestos (21), monumentales (3), puentes y callejon (3), avenida del Mercado contra la fuente (2), pedestal del Portal (1) |
| rodeo (la malla no usa la escalera) | 19 | escaleras de terraza y laterales de las Moradas |
| sin camino (islas) | 15 | 14 escaleras laterales de las Moradas, calle bajo el arco del Puente_06 |
| sin malla en un extremo | 16 | 4 puertas de la muralla (fuera), 10 escaleras laterales (pie exterior), centro del pedestal (2) |
| caida > 0,6 m | 2 | borde del pedestal del Portal (0,63 m) |

Sin problemas: avenidas (salvo la fuente), rondas, diagonales, callejones, 10 escalinatas, 4 de 5 puentes.

Detalle y causas -> `FIXES_BLENDER.md` F8 (malla bajo obstaculos), F9 (escaleras sin unir), F10 (escalones de
0,6-1,2 m), F11 (zonas sin malla). Cobertura: `debug/out/walk/navcover.png` (verde malla, azul malla bajo obstaculo,
rojo suelo sin malla, gris edificios). Capturas de los puntos: `debug/out/tour/g3_p01..p14_*.png`
(`tools/g3_problem_points.json`).
