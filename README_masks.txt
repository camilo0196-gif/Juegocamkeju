CONCORDIA - mascaras de vertex color (COLOR_0) en los .glb para el shader de terreno de Godot
==========================================================================================
Etapa 10 (concordia_v10.blend). Generado por tools/blender/stage10_apply.py.

En Blender cada mascara es un atributo de color propio (CORNER, BYTE_COLOR). Al exportar, solo
'mask_pack' sale como COLOR_0 (export_vertex_color="NAME"). Los valores llegan a Godot tal cual
(verificado: 0.333 / 0.502 / 0.667 en Blender = mismos valores en el accessor COLOR_0 del .glb),
asi que en el shader se leen directamente desde COLOR (0..1, sin conversion de gamma).

El material de cada cara YA esta asignado en Blender por umbral (> 0.5) mas una banda de transicion
dentada de 1-2 celdas entre materiales naturales. COLOR_0 sirve para que el shader de Godot suavice
esa transicion (mezcla) y para efectos (polvo, humedad, brillo).

1) Terreno de la ciudad  -  concordia_terrain.glb  (TRN_CityChunk_xI_yJ_LODk)
------------------------------------------------------------------------------
  R = retaining_mask   muros de contencion (caras >= 70 grados en Moradas, terrazas y plaza)
                       -> MAT_Limestone_Worn (18 % de esas caras con parches MAT_Stone_Repair)
  G = road_mask        calles, callejones, plazoletas y escalinatas de calle
                       -> MAT_Cobble_Concordia (tipo 2 remiendo -> MAT_Stone_Repair, tipo 4 losa -> MAT_Plaza_Slab)
  B = rock_mask        taludes naturales con pendiente >= ~35 grados (+-7 de ruido, escala 6 m), nunca
                       en calles, plaza, muros, terrazas, jardines ni parcelas (ni en caras que las tocan)
                       -> MAT_Rock_Gray (rock_boulder_dry)
  A = ash_mask         talud exterior de la muralla (vertex group 'talud' o r >= 204 m) donde no hay roca
                       -> MAT_Ash_Gray (rocks_ground_02)
  rock_mask y ash_mask son la media por vertice de las caras (borde suave de 1 celda) y valen 0
  forzado en las caras protegidas.
  Sin mascara (R=G=B=A=0) -> MAT_Ground_Cracked (sandstone_cracks), suelo de la ciudad.

  Otras mascaras de la ciudad (no van en COLOR_0):
  UV2 'UVMasks' (TEXCOORD_1): x = magic_glow_mask ; y = slab_ring_id + 16*travertine_band + 32*repair_mask
                              (slab_ring_id -> MAT_Plaza_Slab, travertine_band -> MAT_Plaza_Slab_Travertino)
  UV3 'UVRoads' (TEXCOORD_2): x = road_mask ; y = cobble_type + 0.99*wear_mask
                              cobble_type: 0 terreno, 1 adoquin, 2 remiendo, 3 tierra apisonada, 4 losa,
                              5 plataforma de parcela, 6 jardin, 7 lecho del cauce (-> MAT_Wall_Gray)
  Nota: el importador glTF de Godot trae TEXCOORD_0 y TEXCOORD_1 como UV / UV2; comprobar en la
  version de Godot del proyecto como llega TEXCOORD_2 (si no llega, usar la mascara road de COLOR_0.G).
  Atributos que siguen en el .blend pero ya no van en COLOR_0: dirt_mask, stone_mask, ao_edge
  (antes R/G/B/A de la etapa 02), wear_mask, terraza_id, garden_mask.

2) Terreno exterior  -  concordia_exterior.glb  (TRN_ExteriorChunk_xI_yJ_LODk)
--------------------------------------------------------------------------------
  R = ash_dark_mask    depresiones y cauce seco (ceniza mas oscura, efecto de tono)
  G = dune | moat      max(dune_mask, moat_mask): dunas de 0.5-2 m y foso seco
                       -> MAT_Ash_Gray (rocks_ground_02, grava de ceniza)
                       moat_mask = depresion real Z < 0 conexa con el pie del talud, r 212-224 m
  B = rock_mask        cabezos, crateres, estratos -> MAT_Rock_Gray (rock_boulder_dry)
  A = ash_mask         ceniza (1 en casi todo el exterior)
  Resto (G < 0.5 y B < 0.5) -> MAT_Ash_Ground (dry_ground_01, suelo seco agrietado en gris #6F6F6F)
  B (roca) y A (ceniza) significan lo mismo en la ciudad y en el exterior.

3) Resto de .glb (plaza, calles, cauce, Moradas, muralla, kit)
--------------------------------------------------------------
  Sin COLOR_0 de mascaras: el material va por cara / por pieza.

Umbral de la asignacion: 0.5. Banda de transicion: celda 1 cambia con probabilidad 0.50 y celda 2 con
0.22, decidida por ruido de valor (2.5 m en la ciudad, 7 m en el exterior); solo entre materiales
naturales (Ground_Cracked / Ash_Gray / Rock_Gray en la ciudad; Ash_Ground / Ash_Gray / Rock_Gray fuera).
