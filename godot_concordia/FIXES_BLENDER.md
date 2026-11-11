# FIXES_BLENDER — lo que hay que arreglar en los modelos (no se toca ningun .blend ni .glb de la ciudad)

Formato: objeto · que pasa · gravedad (bloqueante / alta / media / baja) · captura · como reproducirlo · **estado**.
Estados: **ARREGLADO EN GODOT** (ajuste de importacion, material, shader, navegacion: permiso del usuario, PARADA 1),
**PENDIENTE EN BLENDER** (cambia la forma del modelo: va al paquete de arreglos de Blender), **ACEPTADO**.

## Resumen de estados (PARADA 1 ampliada)
| | problema | gravedad | estado |
|---|---|---|---|
| F1 | imagenes con uri + bufferView | baja | PENDIENTE EN BLENDER (exportador) |
| F2 | normal map en UV 'UVBake' (49 materiales de props) | alta | PENDIENTE EN BLENDER |
| F3 | TEST_Casa_12x9 en bld_kit.glb | baja | PENDIENTE EN BLENDER (no exportarla) |
| F4 | caras sueltas con normal invertida (~0,03 %) | baja | ACEPTADO (no se ven huecos) |
| F5 | astillas en TRN_NavMesh_Plaza | baja | ARREGLADO EN GODOT (la navegacion ahora se hornea en Godot) |
| F6 | escalinatas de paso metidas en una rampa | media | PENDIENTE EN BLENDER (no bloquea el paso) |
| F7 | UV deformado en las parcelas de la plaza | baja | PENDIENTE EN BLENDER |
| F8 | malla de navegacion bajo obstaculos | alta | ARREGLADO EN GODOT (horneado desde colisiones) |
| F9 | escaleras sin unir en la malla | alta | ARREGLADO EN GODOT (horneado + 8 NavigationLink3D de la ronda) |
| F10 | escalones de mas de 0,25 m (5 sitios) | alta (3) / baja (2) | PENDIENTE EN BLENDER; la navegacion los evita |
| F11 | zonas sin malla | - | ARREGLADO EN GODOT segun la decision del usuario (tabla en F11) |

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
- **Estado:** ACEPTADO.
- **Gravedad:** baja. En G2/G3 no se ven huecos; si se ven triangulos oscuros sueltos en el terreno junto a las
  escalinatas de paso (ver F6), que pueden ser estas caras o sombras del corte del terreno.
- **Reproducir:** `debug/probe_normals.gd`.

## F5 · Astillas en la malla de navegacion de la Plaza (TRN_NavMesh_Plaza)
- **Que pasa:** vertices a ~1 cm unos de otros; Godot avisaba de 40 "edge errors" (4 con celda de 5 cm).
- **Estado:** ARREGLADO EN GODOT. Ademas, la -navmesh de Blender ya no se usa (solo referencia, desactivada).
- **Gravedad:** baja (resuelto en Godot: `post_import.gd::_weld_navmesh` funde a 2 cm: 9 vertices, 13 poligonos de
  astilla quitados; 0 avisos). Solo se tocan los datos de navegacion.
- **Reproducir:** quitar `_weld_navmesh` y reimportar (`import_settings.py --force`, `--import`).
- **Arreglo en Blender:** `Merge by Distance` 0,02 m en TRN_NavMesh_Plaza antes de exportar.

## F6 · Escalinatas de paso STAIRS_Pass_3m_01..10 metidas en una rampa de terreno
- **Objeto:** STAIRS_Pass_3m_01..10 (bld_portal.glb, MARKER_Escalinata_01..10, r ~100 entre la plaza y las Moradas).
- **Que pasa:** los extremos casan con el terreno (abajo 4,50, arriba 6,00 m, medido en Godot), pero debajo el
  terreno es una rampa continua (10 grados, `terrain_slope_deg`): peldanos, muretes y pretiles asoman y se hunden a
  trozos y alrededor salen triangulos oscuros. Se ve como una escalera rota tirada en el suelo. Ademas, el terreno que
  las rodea no tiene malla de navegacion (F10).
- **Gravedad:** MEDIA (decision del usuario: no bloquea el paso de jugadores ni NPC: las 10 escalinatas se cruzan
  bien andando y con la navegacion horneada en Godot).
- **Estado:** PENDIENTE EN BLENDER (no se toca ahora).
- **Captura:** `debug/out/tour/g3_p13_escalinata_01.png`, `g2_escalinata_ne.png`, `g2_faro.png` (borde derecho).
- **Reproducir:** `capture_tour.gd -- g3 @res://tools/g3_problem_points.json` (p13); perfil:
  `debug/probe_stairs.gd`.
- **Arreglo en Blender:** recortar la rampa del terreno bajo cada escalinata (caja de corte con la huella de la
  escalera + 0,3 m) o asentar la escalinata en un tramo plano con rellanos.

## F7 · Parcelas vacias de la plaza (TRN_PlazaParcel_01..16) con UV deformado
- **Que pasa:** el UV de cada parcela abarca ~118 x 27 repeticiones en ~23 x 26 m (MAT_Limestone_Worn con
  KHR_texture_transform 0,5): la textura se repite cada 20 cm en un sentido y cada metro en el otro y, con mipmaps,
  sale un color liso.
- **Gravedad:** baja (visual).
- **Estado:** PENDIENTE EN BLENDER.
- **Captura:** `debug/out/tour/g3_p14_parcela_plaza.png`, `g2_plaza_120.png`.
- **Reproducir:** mirar cualquier TRN_PlazaParcel desde zoom 30.
- **Arreglo en Blender:** proyectar el UV de las parcelas a escala del mundo (1 repeticion = 2-4 m, igual en u y v).

## F8 · La malla de navegacion pasa por debajo de obstaculos (0,35 - 2,2 m)
- **Que pasa:** la malla (-navmesh) no se recorto con los obstaculos ni con el radio del agente (0,35 m): el camino
  de la navegacion atraviesa cosas en las que el jugador (y los NPC de G7) chocan. Medido con
  `debug/probe_navcover.gd` (rejilla de 1 m): ~1.070 m2 de malla bajo obstaculos.
  - Pretiles de las terrazas de las Moradas (TRN_Parapets_Morada_NE/NW/SW/SE): ~460 m2. La malla llega hasta el borde
    de la terraza por debajo del pretil.
  - Laterales de las escaleras STAIRS_Terrace_6m / 2_5m de las Moradas (zancas y albardillas a 0,45-0,97 m sobre el
    paso): 19 atascos en las calles de las Moradas y 14 en las propias escaleras.
  - Fuente del Mercado (0,6 m), fuentes / pozos de las 6 plazuelas de Razas (0,5-0,65 m), 12 puestos de la Plaza de
    Provisiones (1,0 m), STAIRS_Pass_3m (pretiles), BRIDGE_Stone (pretiles), OBELISK, bancos del Portal (0,8 m).
- **Gravedad:** alta (bloqueante para los NPC de G7 y para el clic-para-andar: el jugador se queda atascado).
- **Estado:** ARREGLADO EN GODOT. `tools/bake_navmesh.gd` hornea la navegacion desde las colisiones (radio 0,35,
  escalon 0,25, pendiente 36, celda 0,25) y anade la huella del mobiliario bajo (fuentes, pozos, puestos) como
  obstruccion. Prueba de caminata: 480 de 481 tramos (antes 475 de 553 con muchos atascos); 0 m2 de malla sobre
  obstaculos (las celdas que marca la sonda en el borde de la fuente y los pozos son el anillo de 0,5 m alrededor).
- **Captura:** `debug/out/walk/navcover.png` (azul = malla bajo obstaculo), `g3_p01`, `g3_p03`, `g3_p04`, `g3_p05`.
- **Reproducir:** `walk_test.gd -- plaza morada escalera_terraza`; `debug/probe_navcover.gd`.
- **Arreglo en Blender:** regenerar las -navmesh restando la huella de pretiles, escaleras (salvo su paso), fuentes,
  puestos y mobiliario, encogida 0,35 m (radio del agente).
- **Alternativa en Godot (no aplicada, decision del usuario):** hornear la malla en Godot (NavigationRegion3D con
  NavigationMesh desde las colisiones, agent_radius 0,35, agent_max_climb 0,25, agent_max_slope 46) en lugar de usar
  las -navmesh de Blender.

## F9 · Escaleras que la malla de navegacion no une (islas y rodeos)
- **Que pasa:** en varias escaleras la malla de abajo y la de arriba no comparten arista (huecos de 0,3-0,5 m entre
  el rellano y la terraza): el camino no las usa y da un rodeo de 60-190 m, o no hay camino.
  - Sin camino (14 escaleras laterales): Stairs_Lateral_Morada NE_01/02/03/05/06/07, NW_14/15, SE_26/27/30/31,
    SW_19/23 (Blender p. ej. NE_02 en 121.8, 57.3).
  - Sin malla en un extremo (10): Stairs_Lateral NE_04/08, NW_12/16, SE_28/32, SW_20/24 (el pie de fuera, r ~200,
    a 6-7 m de la malla) y SE_28/32 arriba.
  - Rodeo (19): Stairs_Terrace SE_01/04/05/07/10/11/12/13/15/16/17, SW_01/02, NE_05, NW_12; Stairs_Lateral NW_10/11,
    SW_18/22.
  - Con estas islas Godot escribe 2 veces `ERROR: It's not expect to not find the most reachable polygons` al pedir
    un camino hacia una isla (solo en la prueba; puede salir en el juego al hacer clic en una isla).
  - Arco del Puente_06 (Razas): la calle bajo el arco no esta unida (sin camino de -64.9, -135.1 a -48.3, -141.9).
- **Gravedad:** alta (zonas de las Moradas a las que los NPC no llegan y el clic no lleva).
- **Estado:** ARREGLADO EN GODOT (navegacion horneada: las 76 escaleras de terraza, 32 laterales y 4 monumentales
  quedan unidas; quedan 2 rodeos de 57 m en las laterales SE_27 / SE_31 por como cruza la prueba, no por la malla).
  Error `It's not expect to not find the most reachable polygons`: ya no sale (se quitan las islas al hornear).
- **Captura:** `g3_p11_escalera_lateral_ne02.png`, `g3_p12_arco_puente06.png`.
- **Reproducir:** `walk_test.gd -- escalera_lateral escalera_terraza arco`.
- **Arreglo en Blender:** que la malla de cada escalera comparta los vertices de su rellano con la de la terraza y la
  de la calle (o un `NAVLINK_` por escalera).

## F10 · Escalones de mas de 0,25 m en pasos de la ciudad
| sitio (Blender x, y) | que | altura | gravedad |
|---|---|---|---|
| 67.0, 63.7 | fin del BRIDGE_Stone_6m_01 (diagonal del Faro) contra el rellano de STAIRS_Monumental_Morada_NE | 0,94 m | ALTA (avenida diagonal / escalera de acceso) |
| 60.1, -73.2 | STAIRS_Monumental_Morada_SE contra STAIRS_Pass_3m_10 (union de dos escaleras de acceso) | 1,06 m | ALTA (escalera de acceso) |
| 99.3, -33.4 | STR_OFI_CallejonEscalera_25 contra el pretil de BRIDGE_Stone_6m_03 | 1,16 m | ALTA (escalera de acceso del callejon) |
| -71.8, 77.2 | pie lateral de STAIRS_Monumental_Morada_NW (el frente si es practicable) | 1,00 m | BAJA (rincon) |
| 12.8, -10.2 y -1.2, 16.5 | borde del pedestal del Portal sin peldano (se sube y baja por su escalera) | 0,61-0,63 m | BAJA (borde) |
- **Estado:** PENDIENTE EN BLENDER. Con la navegacion horneada (escalon maximo 0,25) la malla no cruza esos bordes:
  NPC y clic-para-andar dan la vuelta; el jugador con WASD sigue chocando ahi.
- **Captura:** `g3_p06_puente01_monumental_ne.png`, `g3_p07_monumental_no.png`, `g3_p08_monumental_se_escalinata10.png`,
  `g3_p09_callejon25_puente03.png`, `g3_p10_pedestal_portal.png`.
- **Reproducir:** andar con WASD hacia esos puntos; `debug/probe_stair_profile.gd -- <MARKER_...>`.
- **Arreglo en Blender:** casar las cotas (rampa o peldanos de 0,15 m).

## F11 · Zonas sin malla de navegacion (decision del usuario aplicada)
Medido con `debug/probe_navcover.gd` (rejilla de 1 m; pendiente = normal de la colision).
| zona | suelo m2 | pendiente media / p90 | m2 > 36 grados | malla Godot | categoria |
|---|---|---|---|---|---|
| terreno de las escalinatas (anillo r 60-100 en los cuadrantes de las Moradas) | 5.680 | 3,7 / 10,0 | 27 | 5.457 m2 (96 %) | RECORRIBLE |
| franja junto a la muralla (r 185-199) | 14.750 | 2,1 / 4,3 | 53 | 14.149 m2 (96 %) | RECORRIBLE (sale del horneado, ancho >= 1,2 m) |
| camino de ronda (sobre WALL_Seg y BASTION, 4 tramos entre puertas) | 1.892 | plano | 0 | 1.892 m2 | RECORRIBLE, region aparte, 8 NavigationLink3D en las escaleras STAIR_Gate*_L/_R |
| adarve de las puertas y torres (GATE_*, TOWER_*) | - | - | - | 0 | NO RECORRIBLE |
| exterior (r > 206: talud, foso, ceniza) | 13.290 (4.040 sin colision) | 25 / 41,4 | 5.402 | 0 | NO RECORRIBLE (puertas selladas) |
| azoteas y tejados de los edificios | - | - | - | 0 (36.000 poligonos quitados) | NO RECORRIBLE |
| muros de contencion y taludes > 36 grados | - | > 36 | - | 0 (los quita el horneado) | NO RECORRIBLE |
- Huecos en la muralla (`debug/probe_wall_gaps.gd`, 21.567 rayos cada 0,1 grados a 0,3 / 0,9 / 1,6 m): desde el
  suelo de dentro (r 186) y desde el camino de ronda, **ningun hueco**. Solo quedan abiertos rayos que salen de lo
  alto de puertas y torres (22,25 y 30 m) y de tejados (19,5 m), adonde no se llega andando. No hace falta barrera
  invisible.
- **Estado:** ARREGLADO EN GODOT.
