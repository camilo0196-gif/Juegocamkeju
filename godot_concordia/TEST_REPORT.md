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

## PARADA 1 ampliada (decisiones del usuario aplicadas)

### Navegacion horneada en Godot (F8-F11)
- `tools/bake_navmesh.gd`: desde las colisiones (792 formas), radio 0,35 (Recast lo redondea a 2 celdas = 0,50 m y
  avisa al hornear; el juego no), escalon 0,25, pendiente 36 grados, celda 0,25 (altura 0,05 para que el escalon
  y los 1,8 m del agente sean multiplos exactos). Ciudad entera en ~33 s; 19.996 poligonos brutos -> 12.919 tras
  quitar azoteas y tejados, adarve de puertas y torres, exterior, islas < 20 m2, 349 suelos encerrados (dentro de
  edificios, 17.846 m2) y 1 solape. Mobiliario bajo (fuentes, pozos, 14 puestos, barandillas, 7 casas pequenas)
  como obstruccion proyectada. Regiones guardadas en `navigation/*.res` (no se recalcula al iniciar):
  Plaza 11.332 m2, Mercado 13.054, Oficios 12.344, Clases 12.451, Razas 11.249, Moradas NE/NO/SE/SO
  4.151 / 4.402 / 4.076 / 4.475, camino de ronda 1.892; interiores: Banco 344 m2, casa grande 31, casa pequena 12,
  habitacion 4,5 (se revisaran en G6 con los props y las puertas).
- Las -navmesh de Blender quedan desactivadas como referencia. Cobertura (1 m2 por celda): las dos 52.443 m2,
  solo Godot 39.013 (anillo de escalinatas, franja de la muralla, ronda, terreno entre calles), solo Blender 1.302
  (anillo de baldosas del pedestal del Portal, bordes de terrazas que el radio 0,35 erosiona). Mapa:
  `debug/out/walk/navcover.png`.
- Mapa de navegacion listo ~1,3 s despues de cargar la escena (sincronizacion asincrona de Godot 4.7;
  `scripts/nav_ready.gd` lo espera: regiones, conexion entre todas, iteracion estable). 0 avisos al ejecutar
  (`merge_rasterizer_cell_scale` 0,01).
- Prueba de caminata con la malla nueva: **480 de 481 tramos, 8,6 km, 0 atascos, 0 caidas**. Quedan 3 rodeos (arco
  del Puente_06 y escaleras laterales SE_27 / SE_31: los extremos de la prueba caen a los dos lados de un pretil) y
  1 destino a 1,9 m de su punto.
- Zonas de F11 (tamano, pendiente, categoria) y huecos de la muralla: `FIXES_BLENDER.md` F11.

### Pendientes de G4/G5 arreglados en Godot
- **Terreno** (`shaders/terrain.gdshader`, aplicado por `scripts/materials_fix.gd` a 2.013 superficies): mezcla
  suave de las capas de Concordia con COLOR_0 (muro, calle, roca, ceniza; en el exterior dunas, roca y ceniza
  oscura). Huertos: cobble_type 6 de TEXCOORD_2, que Godot importa como CUSTOM0 (RG_FLOAT) con la v invertida:
  `tipo = floor(1 - CUSTOM0.y)`; se ven como tierra labrada con surcos y verdes apagados (captura cenital
  `debug/out/tour/top_huertos_no.png`; en isometrica quedan detras de las casas).
- **Haces del Faro y del Crisol** (`shaders/beam.gdshader`): aditivo, alpha 0,3, sin profundidad, sin sombras,
  degradado hacia arriba y base fundida; el del Crisol (18,5 m por el oculo) se limita a 12 m. Motivo del bloque
  opaco: el material exportado era BLEND con alpha 0,3 pero emision 1,5 x #8FD0FF que se suma entera, a dos caras
  (dos capas) y con el brillo (glow) por encima del umbral: el cilindro de 80 m se veia como una columna cian casi
  solida que tapaba la fuente del Mercado.
- **Obelisco**: la textura base llega bien (roca + ORM + normal); salia negro porque el color base exportado era
  0,16 x la textura. Ahora albedo #8E9AAF sobre la roca (media ~#383E4A, gris muy oscuro azulado), normal 2,0,
  rugosidad 0,6, rim 0,5; marcas de piso encendidas con MAT_Obelisk_Mark_Lit (prueba: 12 pisos).

### G4 · Luz, cielo, dia y noche, ceniza (`scripts/day_night.gd`)
Sol que sale por el este, pasa por el sur y se pone por el oeste; luna fria; cielo procedural, luz ambiente,
niebla baja y glow por horas: amanecer y hora azul de Mont-Saint-Michel (6:12 y 20:36), mediodia templado, hora
dorada de Siena (17:30), atardecer de Rothenburg (19:30) y noche de Carcassonne (22-5): ventanas calidas,
vitrales y 16 luces #8FD0FF repartidas entre los 2.034 farolillos mas cercanos al jugador. Colores de luz con
saturacion <= 0,35. Ceniza: particulas grises alrededor del jugador y niebla baja. T adelanta una hora. Capturas
por hora: `debug/out/tour/g4b_*_hXX.png`, `g4d_*`. Ajustes tras revisarlas: niebla 5 veces menos densa (con la
camara a 120 m lavaba la imagen), mediodia con menos sol y ambiente, sin bloom global y tonemap_white 4.

### G5 · Efectos y shaders (`scripts/effects.gd`, `shaders/`)
Velo del Portal (ondas, Fresnel, #8FD0FF), agua del Cauce y de 5 fuentes, 28 estandartes y banderas al viento,
pulso de runas y tubos de luz y cristal del Faro (mas fuerte de noche), MAT_Embers <= 1,5, orden de transparencias
(vidrios con profundidad solo opaca), rueda de la Carpinteria a 6 rpm, 7 piedras del Crisol flotando, humo de la
Alquimia y vapor de la Gran Forja, transparencia del Salon de las Hazanas y de los 24 tramos SE de la muralla cuando
tapan al jugador (`GeometryInstance3D.transparency`), brujula del Faro en el borde de la pantalla (`ui/compass.gd`).
Pendientes de G5 que dependen de G6: dither de las 13 puertas residuales de las Moradas (va con las puertas).
Ejecucion: 0 errores, 0 avisos.

### Rendimiento (cifras del servidor: draw calls, triangulos y VRAM validos; FPS no)
`tools/benchmark.gd -- rapido` (zoom de juego 45 m y maximo 120 m, 17:30):

| escena | draw calls | triangulos | objetos | objetivo |
|---|---|---|---|---|
| plaza 45 m | 1.010 | 368.215 | 1.375 | <= 1.200 / <= 300.000 |
| mercado 45 m | 1.543 | 434.234 | 2.705 | idem |
| oficios 45 m | 1.119 | 424.311 | 1.375 | idem |
| moradas NE 45 m | 1.845 | 447.255 | 2.855 | idem |
| moradas SO 45 m | 2.414 | 371.150 | 4.740 | idem |
| moradas NE 45 m, 23:00 (sin sombras del sol) | 467 | 131.959 | 915 | idem |
| plaza 120 m | 3.332 | 835.431 | 3.929 | <= 2.000 / <= 800.000 |
| moradas 120 m | 5.276 | 1.033.922 | 9.860 | idem |
| razas 120 m | 5.710 | 961.744 | 10.044 | idem |

- Hoy solo la plaza y Oficios a 45 m quedan cerca del objetivo de draw calls; ninguno cumple el de triangulos. De
  noche (sin sol) bajan a un tercio: **las sombras del sol duplican o triplican el coste** (cada objeto se dibuja
  tambien en las cascadas de sombra). Plan de G7 (sin cambiar la forma de los modelos, despues de tu prueba):
  sombra solo de las mallas grandes (las pequenas de las Moradas sin cast_shadow), distancia de sombra 140 -> 80 m
  y 2 cascadas, rangos LOD mas cortos en las Moradas, fusion de mallas estaticas por terraza y material, MultiMesh
  para barriles, cajones y repeticiones, y oclusion.
- **VRAM: 456 MB** (objetivo <= 600): texturas 306 MB = 161 MB de texturas de materiales (tope 220) + ~145 MB del
  motor (mapa de sombras direccional 4096^2 y atlas de sombras puntuales 4096^2 a 16 bits = ~64 MB, buffers de
  pantalla a 1600x900 con SSAO, glow y profundidad ~60 MB, cielo con radiancia ~20 MB); mallas y otros buffers
  97 MB; resto ~53 MB. Se puede bajar: atlas de sombras puntuales a 1024 (no se usan sombras puntuales: ~30 MB),
  sombra direccional 4096 -> 2048 (~24 MB, peor nitidez a 120 m), texturas 2K de suelo lejano a 1K
  (`process/size_limit`, ~60 MB). **Margen para personajes: ~144 MB.** 100 elfos comparten malla (3.500 tris) y
  atlas 1K (~1,3 MB): menos de 10 MB de VRAM; el coste real seran draw calls y skinning (G7).
- G8 (personaje) se salta hasta tener `personaje_elfo_base.glb` con animaciones (PJ3/PJ4).

## Arreglo para el PC del usuario (AMD Radeon integrada, Vulkan 1.3, Forward+) — 2026-11-11
Errores que dio el proyecto en su PC: (1) `Out of bounds get index '0'` en `materials_fix.gd:96` (`_beams`);
(2) cientos de `Size of vertex data provided (0) does not match expected (N)`; (3) miles de
`Can't create buffer of size N (VkResult error -10)` = `VK_ERROR_TOO_MANY_OBJECTS`; (4) aviso `unused parameter
unit_depth` en `lod_manager.gd:25`.

### A · `[0]` y haces
- `materials_fix.gd`: `_beams` ya no lee los vertices a pelo. `beam_span()` usa, por orden, la metadata
  `beam_y_<n>` que deja el horneado (sin tocar la GPU), los vertices si existen o la caja de la malla; comprueba
  `is_instance_valid`, malla nula, indice de superficie y arreglo vacio. Si no hay datos lo anota y sigue.
- Accesos a `[0]` blindados: `nav_ready.gd` (menos de 2 regiones), `city.gd` (enlaces de `links.json` mal formados),
  `effects.gd` (mallas no validas), `make_bonemaps.gd` (sin Skeleton3D o escena nula), `bake_navmesh.gd` (caras
  vacias), `pick.gd` (sin argumento). El resto de `[0]` son sobre constantes o arreglos ya comprobados.
- `lod_manager.gd`: quitado el parametro `unit_depth` (aviso 4).
- **Causa de los haces sin malla**: los .glb estan bien (FARO_Beam 80 m desde y = 46,35; haz del Crisol en
  CrisolPiedras_Body, 18,5 m, tope 12 m; ver abajo B). En su PC las mallas importadas llegaron vacias (error 2) y
  `surface_get_arrays()` devolvio un arreglo vacio: `[Mesh.ARRAY_VERTEX]` sobre el fallaba.

### B · Por que llegan mallas vacias
- Los 289 archivos de `assets/` coinciden con `assets/MANIFEST.txt` (tamano y sha256) y las 11.763 primitivas de los
  35 .glb tienen vertices e indices (lectura directa del JSON y del binario del glb). No son .glb corruptos.
- Ninguna herramienta reconstruye ArrayMesh desde superficies vacias; `lod_manager.gd` solo cambia visibilidad.
- Causa mas probable: el paquete de la parada 1 llevaba `.godot/imported` **sin los .md5** (los quite al limpiar
  importaciones viejas) y sin `.godot/editor`. Su editor reimporto los 34 .glb con Vulkan; con la GPU sin objetos
  (error 3), los buffers no se crearon y al guardar la escena importada Godot lee las mallas de vuelta de la GPU:
  se guardaron superficies con N vertices y 0 bytes. Al cargarlas: error 2; al leerlas: error 1.
- Arreglo: borrar `.godot` y reimportar **sin GPU** (`--headless --import`, rasterizador vacio: los datos se quedan
  en la CPU) con `tools/preparar_pc.bat`. `tools/verify_assets.gd` lo comprueba en su PC (sha256 contra el MANIFEST y
  superficies vacias por .glb -> `verificacion_assets.txt`); aqui: 289 iguales, 0 superficies vacias.
  `tools/build_world.gd` se niega a hornear si encuentra alguna vacia y dice en que .glb.
- `tools/sync_assets.py --check` leia mal el MANIFEST (siempre decia "todo cambia"): corregido; ahora 289 iguales y 1
  nuevo (`pj_elfo_sanador_anim.glb`, del PJ4, aun sin copiar a `assets/`).
- No he cambiado ningun `.import`.

### C · Menos objetos en la GPU (`tools/build_world.gd`, horneado en 5,8 s)
La ciudad del juego ya no instancia los .glb: `scenes/concordia_glb.tscn` (antes `concordia.tscn`) queda como
ciudad fuente para hornear el mundo y la navegacion.
- 214 chunks de 50 m (`world/chunks/*.scn`, 39 MB): una MeshInstance3D por mascara de LOD y sombra con **una
  superficie por material**; mallas sin malla de sombra aparte (la mitad de buffers).
- 136 MultiMesh (3.019 instancias) para lo que se repite >= 8 veces en un chunk (tubos, baldosas, farolillos,
  ventanas, almenas...). Sin GPU Godot no guarda las transformaciones de la MultiMesh: van en metadata y
  `world_streamer.gd` las pone al cargar (fallo encontrado en las capturas: faltaba el tubo de luz de la plaza).
- Aparte: 808 tejados (uno por edificio y LOD, grupo `roofs`), y en `world/special.scn` (siempre cargado, 152 nodos)
  los occludes_iso, haces, FARO_*, Obelisco (100 marcas por piso), rueda de la Carpinteria y piedras del Crisol.
  `world/logic.scn`: 10.321 nodos sin malla (marcadores, enlaces, volumenes de interior, puntos de farolillos).
- Biblioteca de 237 materiales (`world/materials`) con los cambios de Godot ya puestos (terreno por mascaras,
  velo, agua, estandartes, ascuas, vidrios, Obelisco); colisiones (788) y 360 oclusores de caja dentro de cada chunk.

| | antes (.glb enteros) | despues (mundo horneado) |
|---|---|---|
| nodos de malla en LOD0, ciudad entera | 8.114 | 854 en chunks + 152 sueltos = 1.006 (objetivo < 3.000) |
| nodos de malla cargados (plaza, radio 120 m) | 8.114 | 1.078 (38 de 214 chunks) |
| nodos visibles a la vez (4 puntos) | — | 357-545 (objetivo < 1.000) |
| superficies cargadas / de sombra | 9.995 / 9.994 | 5.142 / 0 |
| buffers estimados en la GPU | ~49.973 | ~15.545 (plaza), 11.000-13.100 (Moradas, Razas) |

Comparado con capturas (lavapipe, 1600x900): misma imagen en la plaza, el Faro, las Moradas NE y las Razas.

### D · Carga por distancia (`scripts/world_streamer.gd`)
- Al arrancar: la plaza y todo lo que este a menos del radio de carga (sin hilos). Despues, cada 0,25 s, los chunks
  a menos del radio se piden con `ResourceLoader.load_threaded_request` (4 a la vez, el mas cercano primero) y se
  instancian como mucho 2 por fotograma; mas alla de radio + 25 m se liberan. Las Moradas no se cargan enteras:
  solo sus chunks cercanos.
- Radio por calidad: Bajo 120 m, Medio 140, Alto 170 (cubre la pantalla con el zoom maximo de cada nivel).
- LOD por chunk (mascara horneada, mismas reglas de unidad que antes); distancias Bajo 25/70 m, Medio y Alto 40/100.
- "Rangos de visibilidad cortos": se hacen por distancia al jugador (LOD y radio de carga), no con
  `visibility_range`, porque con la camara ortografica a 120 m la distancia a la camara no mide la cercania al
  jugador (ver la cabecera de `lod_manager.gd`).

### E · Calidad (F2, `scripts/quality.gd`, `ui/quality_menu.gd`)
Bajo: sin sombras, sin glow ni SSAO, 70 % de resolucion 3D (FSR 1; bilineal en Compatibility), sin MSAA, LOD 25/70,
carga 120 m, zoom maximo 60 m, 6 farolillos con luz, 300 copos de ceniza. Medio: sombras 70 m (2 cortes, atlas 2048),
glow, FXAA, 85 %, LOD 40/100, carga 140 m, zoom 90. Alto: lo anterior (sombras 140 m, 4 cortes, SSAO, MSAA 2x).
Auto: `RenderingServer.get_video_adapter_type()` integrada o CPU -> Bajo, dedicada -> Alto, otra -> Medio; con
OpenGL (siempre "otro") se mira el nombre (Radeon(TM) Graphics, Vega, 680M/780M, Intel, UHD, Iris...). Se guarda en
`user://calidad.cfg`.

Cifras en Bajo (lavapipe; draw calls, triangulos y VRAM validos, FPS no): plaza 189 draw calls / 171.000
triangulos / 355 MB de VRAM; Mercado 294; Oficios 353; Moradas NE 477; Razas 432; zoom maximo (60 m) 315-839.
Antes, en Alto: 1.010-5.710 draw calls y 456 MB. Con la calidad Alto el mundo horneado da los mismos draw calls que
antes (~1.500 en la plaza) y mas triangulos (851.000 frente a 469.000): el LOD cambia por chunk de 50 m y no por
edificio, asi que el LOD0 llega algo mas lejos. Para una tarjeta dedicada no es problema.

### F · Benchmark (`tools/benchmark.gd`)
Bajo, Medio y Alto (o `niveles=`), 8 escenas por nivel y un paseo de 30 s a 6 m/s por 7 puntos (cuenta los tirones de
la carga por hilos: fotogramas > 50 ms y > 2,5x la mediana), chunks cargados, GPU, tipo y nivel automatico, y el
veredicto contra el objetivo (FPS medio >= 30 y 1 % peor >= 25 en Bajo). Probado aqui de principio a fin: 0 errores,
0 avisos (los FPS de lavapipe no valen).

### Compatibility (OpenGL) frente a Forward+ (Vulkan)
Probado aqui con `--rendering-method gl_compatibility` (Mesa llvmpipe, OpenGL 4.5): arranca y captura con 0 errores
(el unico aviso, "Could not set V-Sync mode", es del driver de software del servidor). Mismos draw calls (plaza en Bajo
318 frente a 322) y la imagen se ve bien, incluido el shader del terreno con 15 texturas. VRAM en Bajo 221 MB frente a
365 MB de Forward+ (sin buffers de iluminacion por clusters ni de SSAO). Pierde: SSAO, FSR (escala bilineal) y algo de
calidad en las sombras y el glow.
Recomendacion para su PC: probar primero **Forward+ en Bajo** con el mundo horneado. El error -10 venia de los ~50.000
buffers, que ahora son ~15.000, y el driver Vulkan de AMD suele rendir mas que su OpenGL en Windows. Si el benchmark
no llega a 30 FPS en Bajo o vuelve el error -10, repetirlo con `--rendering-method gl_compatibility`: OpenGL no tiene el
limite de objetos de Vulkan y gasta menos VRAM. Si gana, se cambia en Proyecto > Configuracion > Renderizado >
Renderer > Rendering Method (lo cambio yo cuando tenga las dos tablas).
