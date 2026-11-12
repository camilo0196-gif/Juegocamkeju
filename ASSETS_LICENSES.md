# ASSETS_LICENSES - Concordia

Registro de todos los assets de terceros que usa Concordia. Regla del proyecto: sin entrada aqui, el asset no se usa.
Licencias permitidas: CC0 (Kenney, Quaternius, KayKit, Poly Haven, ambientCG, Smithsonian Open Access, Sketchfab con
filtro CC0). CC BY solo con aprobacion del usuario (y entonces tambien va a CREDITS.md). Prohibidas: CC BY-NC, "uso
personal", sin licencia visible, o sacadas de otros juegos o peliculas. Los assets generados con IA se registran como
"generado con IA (TRELLIS.2, MIT)".

## Texturas (Poly Haven, CC0)

Descargadas en las etapas 09-10 (commit 063636a, 2026-11-05) con tools/blender/stage09_polyhaven.py y
stage10_polyhaven.py; datos completos en textures/concordia/polyhaven.json. Se usan a 1K-2K, desaturadas a la paleta.

| Asset | Autor(es) | URL | Licencia | Fecha | Donde se usa |
|---|---|---|---|---|---|
| Castle Wall Variation | Rob Tuytel | https://polyhaven.com/a/castle_wall_varriation | CC0 (https://polyhaven.com/license) | 2026-11-05 | MAT_Wall_Gray (edificios, terreno e interiores) |
| Cobblestone Floor 001 | Rob Tuytel | https://polyhaven.com/a/cobblestone_floor_001 | CC0 (https://polyhaven.com/license) | 2026-11-05 | MAT_Cobble_Concordia (edificios, terreno e interiores) |
| Dry Ground 01 | Rob Tuytel | https://polyhaven.com/a/dry_ground_01 | CC0 (https://polyhaven.com/license) | 2026-11-05 | MAT_Ash_Ground (edificios, terreno e interiores) |
| Floor Tiles 02 | Rob Tuytel | https://polyhaven.com/a/floor_tiles_02 | CC0 (https://polyhaven.com/license) | 2026-11-05 | MAT_Plaza_Slab (edificios, terreno e interiores) |
| Hessian 380 | colormass, Rico Cilliers | https://polyhaven.com/a/hessian_380 | CC0 (https://polyhaven.com/license) | 2026-11-05 | MAT_Cloth, MAT_Cloth_Patch_A, MAT_Cloth_Patch_B, MAT_Cloth_Patch_C (edificios, terreno e interiores) |
| Marble 01 | Rob Tuytel | https://polyhaven.com/a/marble_01 | CC0 (https://polyhaven.com/license) | 2026-11-05 | MAT_Plaza_Slab_Travertino (edificios, terreno e interiores) |
| Metal Plate 02 | Rob Tuytel | https://polyhaven.com/a/metal_plate_02 | CC0 (https://polyhaven.com/license) | 2026-11-05 | MAT_Iron_Black (edificios, terreno e interiores) |
| Rock Boulder Dry | Dimitrios Savva, Rico Cilliers | https://polyhaven.com/a/rock_boulder_dry | CC0 (https://polyhaven.com/license) | 2026-11-05 | MAT_Rock_Gray (edificios, terreno e interiores) |
| Rocks Ground 02 | Rob Tuytel | https://polyhaven.com/a/rocks_ground_02 | CC0 (https://polyhaven.com/license) | 2026-11-05 | MAT_Ash_Gray (edificios, terreno e interiores) |
| Roof 09 | Rob Tuytel | https://polyhaven.com/a/roof_09 | CC0 (https://polyhaven.com/license) | 2026-11-05 | MAT_Roof_Tile_Ocher (edificios, terreno e interiores) |
| Rustic Stone Wall | Dimitrios Savva | https://polyhaven.com/a/rustic_stone_wall | CC0 (https://polyhaven.com/license) | 2026-11-05 | MAT_Stone_Repair (edificios, terreno e interiores) |
| Sandstone Cracks | Rob Tuytel | https://polyhaven.com/a/sandstone_cracks | CC0 (https://polyhaven.com/license) | 2026-11-05 | MAT_Ground_Cracked (edificios, terreno e interiores) |
| Stone Wall 02 | Dario Barresi, Charlotte Baglioni | https://polyhaven.com/a/stone_wall_02 | CC0 (https://polyhaven.com/license) | 2026-11-05 | MAT_Limestone_Worn (edificios, terreno e interiores) |
| Weathered Planks | Dario Barresi, Dimitrios Savva | https://polyhaven.com/a/weathered_planks | CC0 (https://polyhaven.com/license) | 2026-11-05 | MAT_Wood_Dark (edificios, terreno e interiores) |

Descargadas como candidatas en las etapas 09-10 y NO usadas en ningun material (se conservan en
textures/concordia/polyhaven_src/ y en respaldo/2026-11-11/binarios_git/):

| Asset | Autor(es) | URL | Licencia | Fecha | Donde se usa |
|---|---|---|---|---|---|
| Broken Wall | Rob Tuytel | https://polyhaven.com/a/broken_wall | CC0 (https://polyhaven.com/license) | 2026-11-05 | no se usa (candidata) |
| Castle Wall Slates | Rob Tuytel | https://polyhaven.com/a/castle_wall_slates | CC0 (https://polyhaven.com/license) | 2026-11-05 | no se usa (candidata) |
| Rock Boulder Cracked | Dario Barresi, Dimitrios Savva | https://polyhaven.com/a/rock_boulder_cracked | CC0 (https://polyhaven.com/license) | 2026-11-05 | no se usa (candidata de MAT_Rock_Gray, se eligio Rock Boulder Dry) |

## Modelos 3D (props)

Fuentes aprobadas por el usuario (etapa 28): Quaternius Fantasy Props MegaKit y Avramania (serie Low Poly Medieval)
como base, Poly Haven para casos sueltos. Todos se reasignan a materiales de Concordia, escala en metros y origen en
la base; limite 500 triangulos los pequenos (lado mayor <= 0.6 m) y 1,500 los medianos: lo que pasa se decima con
normal map horneado (textures/props/, 512 o 1K). Informe: docs/reports/stage28_props_import.json.
Ningun asset descargado se usa en Portal, Faro, Obelisco, Santuario, Salon de las Hazanas, Banco, Tesoreria, Crisol
ni en los edificios de barrios y moradas (solo mobiliario, decision del usuario en la etapa 28).

### Lote Mercado (Posada, Casa del Registro, Gran Subasta)

Quaternius - Fantasy Props MegaKit (Standard): descargado de OpenGameArt (fantasy_props_megakitstandard.zip,
sha256 0bc1e5843c9f245c44bda82f97f738b09f88fe51bb34d2a69a7847a969f868e3) el 2026-11-11; licencia copiada en
licenses/Quaternius_FantasyPropsMegaKit_License_Standard.txt.

| Asset | Autor(es) | URL | Licencia | Fecha | Donde se usa |
|---|---|---|---|---|---|
| Table_Large (PROP_Q_Table_Large) | Quaternius | https://quaternius.com/packs/fantasypropsmegakit.html (copia en https://opengameart.org/content/fantasy-props-megakit) | CC0 1.0 | 2026-11-11 | Posada: mesa larga (props_int_mercado.glb) |
| Chair_1 (PROP_Q_Chair_1) | Quaternius | https://quaternius.com/packs/fantasypropsmegakit.html (copia en https://opengameart.org/content/fantasy-props-megakit) | CC0 1.0 | 2026-11-11 | Posada / Registro: silla (props_int_mercado.glb); interiores de Moradas (int_morada_*.glb) |
| Bench (PROP_Q_Bench) | Quaternius | https://quaternius.com/packs/fantasypropsmegakit.html (copia en https://opengameart.org/content/fantasy-props-megakit) | CC0 1.0 | 2026-11-11 | Posada: banco (props_int_mercado.glb) |
| Stool (PROP_Q_Stool) | Quaternius | https://quaternius.com/packs/fantasypropsmegakit.html (copia en https://opengameart.org/content/fantasy-props-megakit) | CC0 1.0 | 2026-11-11 | Posada: taburete (props_int_mercado.glb); interiores de Moradas (int_morada_*.glb) |
| Barrel_Holder (PROP_Q_Barrel_Holder) | Quaternius | https://quaternius.com/packs/fantasypropsmegakit.html (copia en https://opengameart.org/content/fantasy-props-megakit) | CC0 1.0 | 2026-11-11 | Posada: barril en soporte (props_int_mercado.glb); decimado 2676 -> 1480 con normal map textures/props/PROP_Q_Barrel_Holder_normal_1k.png |
| Mug (PROP_Q_Mug) | Quaternius | https://quaternius.com/packs/fantasypropsmegakit.html (copia en https://opengameart.org/content/fantasy-props-megakit) | CC0 1.0 | 2026-11-11 | Posada: jarra (props_int_mercado.glb); interiores de Moradas (int_morada_*.glb) |
| Table_Plate (PROP_Q_Table_Plate) | Quaternius | https://quaternius.com/packs/fantasypropsmegakit.html (copia en https://opengameart.org/content/fantasy-props-megakit) | CC0 1.0 | 2026-11-11 | Posada: plato (props_int_mercado.glb) |
| Table_Knife (PROP_Q_Table_Knife) | Quaternius | https://quaternius.com/packs/fantasypropsmegakit.html (copia en https://opengameart.org/content/fantasy-props-megakit) | CC0 1.0 | 2026-11-11 | Posada: cuchillo (props_int_mercado.glb) |
| Table_Fork (PROP_Q_Table_Fork) | Quaternius | https://quaternius.com/packs/fantasypropsmegakit.html (copia en https://opengameart.org/content/fantasy-props-megakit) | CC0 1.0 | 2026-11-11 | Posada: tenedor (props_int_mercado.glb) |
| Table_Spoon (PROP_Q_Table_Spoon) | Quaternius | https://quaternius.com/packs/fantasypropsmegakit.html (copia en https://opengameart.org/content/fantasy-props-megakit) | CC0 1.0 | 2026-11-11 | Posada: cuchara (props_int_mercado.glb) |
| Candle_1 (PROP_Q_Candle_1) | Quaternius | https://quaternius.com/packs/fantasypropsmegakit.html (copia en https://opengameart.org/content/fantasy-props-megakit) | CC0 1.0 | 2026-11-11 | Posada / Registro: vela (props_int_mercado.glb); interiores de Moradas (int_morada_*.glb) |
| CandleStick (PROP_Q_CandleStick) | Quaternius | https://quaternius.com/packs/fantasypropsmegakit.html (copia en https://opengameart.org/content/fantasy-props-megakit) | CC0 1.0 | 2026-11-11 | Posada / Registro: candelero (props_int_mercado.glb); interiores de Moradas (int_morada_*.glb); decimado 730 -> 479 con normal map textures/props/PROP_Q_CandleStick_normal_512.png |
| Chandelier (PROP_Q_Chandelier) | Quaternius | https://quaternius.com/packs/fantasypropsmegakit.html (copia en https://opengameart.org/content/fantasy-props-megakit) | CC0 1.0 | 2026-11-11 | Posada: lampara de techo (props_int_mercado.glb); decimado 5680 -> 1479 con normal map textures/props/PROP_Q_Chandelier_normal_1k.png |
| Workbench_Drawers (PROP_Q_Workbench_Drawers) | Quaternius | https://quaternius.com/packs/fantasypropsmegakit.html (copia en https://opengameart.org/content/fantasy-props-megakit) | CC0 1.0 | 2026-11-11 | Registro: cajonera del escritorio (props_int_mercado.glb) |
| Shelf_Simple (PROP_Q_Shelf_Simple) | Quaternius | https://quaternius.com/packs/fantasypropsmegakit.html (copia en https://opengameart.org/content/fantasy-props-megakit) | CC0 1.0 | 2026-11-11 | Registro: estante (props_int_mercado.glb) |
| BookGroup_Medium_1 (PROP_Q_BookGroup_Medium_1) | Quaternius | https://quaternius.com/packs/fantasypropsmegakit.html (copia en https://opengameart.org/content/fantasy-props-megakit) | CC0 1.0 | 2026-11-11 | Registro: libros en estante (props_int_mercado.glb) |
| BookStand (PROP_Q_BookStand) | Quaternius | https://quaternius.com/packs/fantasypropsmegakit.html (copia en https://opengameart.org/content/fantasy-props-megakit) | CC0 1.0 | 2026-11-11 | Registro: atril (props_int_mercado.glb); decimado 1526 -> 1479 con normal map textures/props/PROP_Q_BookStand_normal_1k.png |
| Scroll_1 (PROP_Q_Scroll_1) | Quaternius | https://quaternius.com/packs/fantasypropsmegakit.html (copia en https://opengameart.org/content/fantasy-props-megakit) | CC0 1.0 | 2026-11-11 | Registro: pergamino (props_int_mercado.glb); decimado 512 -> 480 con normal map textures/props/PROP_Q_Scroll_1_normal_512.png |
| Scroll_2 (PROP_Q_Scroll_2) | Quaternius | https://quaternius.com/packs/fantasypropsmegakit.html (copia en https://opengameart.org/content/fantasy-props-megakit) | CC0 1.0 | 2026-11-11 | Registro: pergamino abierto (props_int_mercado.glb); decimado 672 -> 480 con normal map textures/props/PROP_Q_Scroll_2_normal_512.png |
| Book_Stack_1 (PROP_Q_Book_Stack_1) | Quaternius | https://quaternius.com/packs/fantasypropsmegakit.html (copia en https://opengameart.org/content/fantasy-props-megakit) | CC0 1.0 | 2026-11-11 | Registro: pila de libros (props_int_mercado.glb) |
| Book_Stack_2 (PROP_Q_Book_Stack_2) | Quaternius | https://quaternius.com/packs/fantasypropsmegakit.html (copia en https://opengameart.org/content/fantasy-props-megakit) | CC0 1.0 | 2026-11-11 | Registro: pila de libros con cierre (props_int_mercado.glb) |
| Chest_Wood (PROP_Q_Chest_Wood) | Quaternius | https://quaternius.com/packs/fantasypropsmegakit.html (copia en https://opengameart.org/content/fantasy-props-megakit) | CC0 1.0 | 2026-11-11 | Gran Subasta: arcon de lotes (props_int_mercado.glb); interiores de Moradas (int_morada_*.glb); decimado 2546 -> 1480 con normal map textures/props/PROP_Q_Chest_Wood_normal_1k.png |
| Coin_Pile (PROP_Q_Coin_Pile) | Quaternius | https://quaternius.com/packs/fantasypropsmegakit.html (copia en https://opengameart.org/content/fantasy-props-megakit) | CC0 1.0 | 2026-11-11 | Gran Subasta: monedas (props_int_mercado.glb); decimado 960 -> 480 con normal map textures/props/PROP_Q_Coin_Pile_normal_512.png |
| Pouch_Large (PROP_Q_Pouch_Large) | Quaternius | https://quaternius.com/packs/fantasypropsmegakit.html (copia en https://opengameart.org/content/fantasy-props-megakit) | CC0 1.0 | 2026-11-11 | Gran Subasta: bolsa de monedas (props_int_mercado.glb); decimado 730 -> 480 con normal map textures/props/PROP_Q_Pouch_Large_normal_512.png |
| Bag (PROP_Q_Bag) | Quaternius | https://quaternius.com/packs/fantasypropsmegakit.html (copia en https://opengameart.org/content/fantasy-props-megakit) | CC0 1.0 | 2026-11-11 | Gran Subasta / puestos: saco (props_int_mercado.glb) |

Avramania - Low Poly Medieval (Sketchfab): licencia comprobada el dia de la descarga en la API (/v3/models/<uid>)
y en la pagina publica del modelo (texto de la licencia citado).

| Asset | Autor(es) | URL | Licencia | Fecha | Donde se usa |
|---|---|---|---|---|---|
| Village Hearth - Low Poly Medieval, CC0 (PROP_AV_Village_Hearth) | Avramania | https://sketchfab.com/3d-models/village-hearth-low-poly-medieval-cc0-1b9b17a3cb0f44dd9141e70fba061c71 | CC0 Public Domain (http://creativecommons.org/publicdomain/zero/1.0/; "Credit is not mandatory. Commercial use is allowed."; pagina: "CC0 - Download Free 3D model by Avramania [1b9b17a] - Sketchfab") | 2026-11-11 | Posada: hogar (props_int_mercado.glb) |
| Potcrane - Low Poly Medieval, CC0 (PROP_AV_Potcrane) | Avramania | https://sketchfab.com/3d-models/potcrane-low-poly-medieval-cc0-d041cc0462ab4da6be30fff811765685 | CC0 Public Domain (http://creativecommons.org/publicdomain/zero/1.0/; "Credit is not mandatory. Commercial use is allowed."; pagina: "CC0 - Download Free 3D model by Avramania [d041cc0] - Sketchfab") | 2026-11-11 | Posada: pescante del hogar (props_int_mercado.glb) |
| Bed - Low Poly Medieval, CC0 (PROP_AV_Bed) | Avramania | https://sketchfab.com/3d-models/bed-low-poly-medieval-cc0-24704040010a42ceaeffb1631ed1ae9b | CC0 Public Domain (http://creativecommons.org/publicdomain/zero/1.0/; "Credit is not mandatory. Commercial use is allowed."; pagina: "CC0 - Download Free 3D model by Avramania [2470404] - Sketchfab") | 2026-11-11 | Posada: cama (props_int_mercado.glb) |
| Table - Low Poly Medieval, CC0 (PROP_AV_Table) | Avramania | https://sketchfab.com/3d-models/table-low-poly-medieval-cc0-bd0ad320c35249b9b1a37e2adc061bb9 | CC0 Public Domain (http://creativecommons.org/publicdomain/zero/1.0/; "Credit is not mandatory. Commercial use is allowed."; pagina: "CC0 - Download Free 3D model by Avramania [bd0ad32] - Sketchfab") | 2026-11-11 | Registro: mesa del escritorio (props_int_mercado.glb); interiores de Moradas (int_morada_*.glb) |
| Apple - Low Poly Medieval, CC0 (PROP_AV_Apple) | Avramania | https://sketchfab.com/3d-models/apple-low-poly-medieval-cc0-64e25ccc90c84e3b8c2ad02dd39150ba | CC0 Public Domain (http://creativecommons.org/publicdomain/zero/1.0/; "Credit is not mandatory. Commercial use is allowed."; pagina: "CC0 - Download Free 3D model by Avramania [64e25cc] - Sketchfab") | 2026-11-11 | puestos: manzanas (props_int_mercado.glb) |
| Carrot - Low Poly Medieval, CC0 (PROP_AV_Carrot) | Avramania | https://sketchfab.com/3d-models/carrot-low-poly-medieval-cc0-3f3b24dd3bf24ce49b518bfbd5ec93df | CC0 Public Domain (http://creativecommons.org/publicdomain/zero/1.0/; "Credit is not mandatory. Commercial use is allowed."; pagina: "CC0 - Download Free 3D model by Avramania [3f3b24d] - Sketchfab") | 2026-11-11 | puestos: zanahorias (props_int_mercado.glb) |
| Onion - Low Poly Medieval, CC0 (PROP_AV_Onion) | Avramania | https://sketchfab.com/3d-models/onion-low-poly-medieval-cc0-a8a9568469524a548ca730b1058de3ef | CC0 Public Domain (http://creativecommons.org/publicdomain/zero/1.0/; "Credit is not mandatory. Commercial use is allowed."; pagina: "CC0 - Download Free 3D model by Avramania [a8a9568] - Sketchfab") | 2026-11-11 | puestos: cebollas (props_int_mercado.glb) |
| Loaf - Low Poly Medieval, CC0 (PROP_AV_Loaf) | Avramania | https://sketchfab.com/3d-models/loaf-low-poly-medieval-cc0-fe8f28bcadaf44a7836e12fe30f9a3dd | CC0 Public Domain (http://creativecommons.org/publicdomain/zero/1.0/; "Credit is not mandatory. Commercial use is allowed."; pagina: "CC0 - Download Free 3D model by Avramania [fe8f28b] - Sketchfab") | 2026-11-11 | puestos: pan (props_int_mercado.glb) |
| Cheese Wheel - Low Poly Medieval, CC0 (PROP_AV_Cheese_Wheel) | Avramania | https://sketchfab.com/3d-models/cheese-wheel-low-poly-medieval-cc0-c66175e51d044dfda9e6edff21d4d38a | CC0 Public Domain (http://creativecommons.org/publicdomain/zero/1.0/; "Credit is not mandatory. Commercial use is allowed."; pagina: "CC0 - Download Free 3D model by Avramania [c66175e] - Sketchfab") | 2026-11-11 | puestos: queso (props_int_mercado.glb); decimado 1270 -> 480 con normal map textures/props/PROP_AV_Cheese_Wheel_normal_512.png |
| Grapes - Low Poly Medieval, CC0 (PROP_AV_Grapes) | Avramania | https://sketchfab.com/3d-models/grapes-low-poly-medieval-cc0-cc950686a4dc4ac89edda92b21afca11 | CC0 Public Domain (http://creativecommons.org/publicdomain/zero/1.0/; "Credit is not mandatory. Commercial use is allowed."; pagina: "CC0 - Download Free 3D model by Avramania [cc95068] - Sketchfab") | 2026-11-11 | puestos: uvas (props_int_mercado.glb); decimado 708 -> 480 con normal map textures/props/PROP_AV_Grapes_normal_512.png |
| Grain Sack - Low Poly Medieval, CC0 (PROP_AV_Grain_Sack) | Avramania | https://sketchfab.com/3d-models/grain-sack-low-poly-medieval-cc0-7db2a14529fd4e1f9391c68337f71eac | CC0 Public Domain (http://creativecommons.org/publicdomain/zero/1.0/; "Credit is not mandatory. Commercial use is allowed."; pagina: "CC0 - Download Free 3D model by Avramania [7db2a14] - Sketchfab") | 2026-11-11 | puestos: saco de grano (props_int_mercado.glb); interiores de Moradas (int_morada_*.glb); decimado 938 -> 480 con normal map textures/props/PROP_AV_Grain_Sack_normal_512.png |

### Lote Oficios (talleres y gremios)

Quaternius - Fantasy Props MegaKit (Standard): descargado de OpenGameArt (fantasy_props_megakitstandard.zip,
sha256 0bc1e5843c9f245c44bda82f97f738b09f88fe51bb34d2a69a7847a969f868e3) el 2026-11-11; licencia copiada en
licenses/Quaternius_FantasyPropsMegaKit_License_Standard.txt.

| Asset | Autor(es) | URL | Licencia | Fecha | Donde se usa |
|---|---|---|---|---|---|
| Whetstone (PROP_Q_Whetstone) | Quaternius | https://quaternius.com/packs/fantasypropsmegakit.html (copia en https://opengameart.org/content/fantasy-props-megakit) | CC0 1.0 | 2026-11-11 | Forja: piedra de afilar (props_int_oficios.glb) |
| Peg_Rack (PROP_Q_Peg_Rack) | Quaternius | https://quaternius.com/packs/fantasypropsmegakit.html (copia en https://opengameart.org/content/fantasy-props-megakit) | CC0 1.0 | 2026-11-11 | Forja / Reparaciones: colgador de herramientas (props_int_oficios.glb) |
| Workbench (PROP_Q_Workbench) | Quaternius | https://quaternius.com/packs/fantasypropsmegakit.html (copia en https://opengameart.org/content/fantasy-props-megakit) | CC0 1.0 | 2026-11-11 | Carpinteria: banco de carpintero (props_int_oficios.glb) |
| Potion_1 (PROP_Q_Potion_1) | Quaternius | https://quaternius.com/packs/fantasypropsmegakit.html (copia en https://opengameart.org/content/fantasy-props-megakit) | CC0 1.0 | 2026-11-11 | Alquimia: pocion (props_int_oficios.glb) |
| Potion_2 (PROP_Q_Potion_2) | Quaternius | https://quaternius.com/packs/fantasypropsmegakit.html (copia en https://opengameart.org/content/fantasy-props-megakit) | CC0 1.0 | 2026-11-11 | Alquimia: pocion (props_int_oficios.glb) |
| Potion_4 (PROP_Q_Potion_4) | Quaternius | https://quaternius.com/packs/fantasypropsmegakit.html (copia en https://opengameart.org/content/fantasy-props-megakit) | CC0 1.0 | 2026-11-11 | Alquimia: pocion (props_int_oficios.glb); decimado 536 -> 480 con normal map textures/props/PROP_Q_Potion_4_normal_512.png |
| Pickaxe_Bronze (PROP_Q_Pickaxe_Bronze) | Quaternius | https://quaternius.com/packs/fantasypropsmegakit.html (copia en https://opengameart.org/content/fantasy-props-megakit) | CC0 1.0 | 2026-11-11 | Mineros: pico (props_int_oficios.glb) |
| Bucket_Wooden_1 (PROP_Q_Bucket_Wooden_1) | Quaternius | https://quaternius.com/packs/fantasypropsmegakit.html (copia en https://opengameart.org/content/fantasy-props-megakit) | CC0 1.0 | 2026-11-11 | Pescadores: cubo (props_int_oficios.glb); decimado 976 -> 480 con normal map textures/props/PROP_Q_Bucket_Wooden_1_normal_512.png |
| Rope_2 (PROP_Q_Rope_2) | Quaternius | https://quaternius.com/packs/fantasypropsmegakit.html (copia en https://opengameart.org/content/fantasy-props-megakit) | CC0 1.0 | 2026-11-11 | Pescadores: cuerda (props_int_oficios.glb) |
| Chain_Coil (PROP_Q_Chain_Coil) | Quaternius | https://quaternius.com/packs/fantasypropsmegakit.html (copia en https://opengameart.org/content/fantasy-props-megakit) | CC0 1.0 | 2026-11-11 | Reparaciones: rollo de cadena (props_int_oficios.glb); decimado 3744 -> 1480 con normal map textures/props/PROP_Q_Chain_Coil_normal_1k.png |

Avramania - Low Poly Medieval (Sketchfab): licencia comprobada el dia de la descarga en la API (/v3/models/<uid>)
y en la pagina publica del modelo (texto de la licencia citado).

| Asset | Autor(es) | URL | Licencia | Fecha | Donde se usa |
|---|---|---|---|---|---|
| Water Trough - Low Poly Medieval, CC0 (PROP_AV_Water_Trough) | Avramania | https://sketchfab.com/3d-models/water-trough-low-poly-medieval-cc0-2ba720b8921543b69edad075b9d7c5c5 | CC0 Public Domain (http://creativecommons.org/publicdomain/zero/1.0/; "Credit is not mandatory. Commercial use is allowed."; pagina: "CC0 - Download Free 3D model by Avramania [2ba720b] - Sketchfab") | 2026-11-11 | Forja: pilon de temple (props_int_oficios.glb) |
| Hammer - Low Poly Medieval, CC0 (PROP_AV_Hammer) | Avramania | https://sketchfab.com/3d-models/hammer-low-poly-medieval-cc0-34e64ec1bab74f3b921d3078cecd06dc | CC0 Public Domain (http://creativecommons.org/publicdomain/zero/1.0/; "Credit is not mandatory. Commercial use is allowed."; pagina: "CC0 - Download Free 3D model by Avramania [34e64ec] - Sketchfab") | 2026-11-11 | Forja / Reparaciones: martillo (props_int_oficios.glb) |
| Woodpile - Low Poly Medieval, CC0 (PROP_AV_Woodpile) | Avramania | https://sketchfab.com/3d-models/woodpile-low-poly-medieval-cc0-e06f39a8521d4a728f6de1a399e2097a | CC0 Public Domain (http://creativecommons.org/publicdomain/zero/1.0/; "Credit is not mandatory. Commercial use is allowed."; pagina: "CC0 - Download Free 3D model by Avramania [e06f39a] - Sketchfab") | 2026-11-11 | Carpinteria: lena (props_int_oficios.glb) |
| Village Ladder - Low Poly Medieval, CC0 (PROP_AV_Village_Ladder) | Avramania | https://sketchfab.com/3d-models/village-ladder-low-poly-medieval-cc0-b5ee3e7fbb0049059bf23a6724eebc1b | CC0 Public Domain (http://creativecommons.org/publicdomain/zero/1.0/; "Credit is not mandatory. Commercial use is allowed."; pagina: "CC0 - Download Free 3D model by Avramania [b5ee3e7] - Sketchfab") | 2026-11-11 | Carpinteria: escalera de mano (props_int_oficios.glb) |
| Cauldron - Low Poly Medieval, CC0 (PROP_AV_Cauldron) | Avramania | https://sketchfab.com/3d-models/cauldron-low-poly-medieval-cc0-eb4311e2df0549d5a5a26edc313c38c4 | CC0 Public Domain (http://creativecommons.org/publicdomain/zero/1.0/; "Credit is not mandatory. Commercial use is allowed."; pagina: "CC0 - Download Free 3D model by Avramania [eb4311e] - Sketchfab") | 2026-11-11 | Alquimia: caldero (props_int_oficios.glb) |
| Roll - Low Poly Medieval, CC0 (PROP_AV_Roll) | Avramania | https://sketchfab.com/3d-models/roll-low-poly-medieval-cc0-9cd0c6d36336456e86c2a79e968e47b6 | CC0 Public Domain (http://creativecommons.org/publicdomain/zero/1.0/; "Credit is not mandatory. Commercial use is allowed."; pagina: "CC0 - Download Free 3D model by Avramania [9cd0c6d] - Sketchfab") | 2026-11-11 | Hornos: panecillo (props_int_oficios.glb) |
| Herb Bundle - Low Poly Medieval, CC0 (PROP_AV_Herb_Bundle) | Avramania | https://sketchfab.com/3d-models/herb-bundle-low-poly-medieval-cc0-41ec7f9ddd8c4e999449b5e746790fe4 | CC0 Public Domain (http://creativecommons.org/publicdomain/zero/1.0/; "Credit is not mandatory. Commercial use is allowed."; pagina: "CC0 - Download Free 3D model by Avramania [41ec7f9] - Sketchfab") | 2026-11-11 | Herbolarios: manojo de hierbas (props_int_oficios.glb); decimado 666 -> 480 con normal map textures/props/PROP_AV_Herb_Bundle_normal_512.png |
| Pottedplant - Low Poly Medieval, CC0 (PROP_AV_Pottedplant) | Avramania | https://sketchfab.com/3d-models/pottedplant-low-poly-medieval-cc0-82f2cac9741c467c844c9c5b62ab6050 | CC0 Public Domain (http://creativecommons.org/publicdomain/zero/1.0/; "Credit is not mandatory. Commercial use is allowed."; pagina: "CC0 - Download Free 3D model by Avramania [82f2cac] - Sketchfab") | 2026-11-11 | Herbolarios: maceta (props_int_oficios.glb) |
| Pot - Low Poly Medieval, CC0 (PROP_AV_Pot) | Avramania | https://sketchfab.com/3d-models/pot-low-poly-medieval-cc0-fa90afdde3e541458de26d42e1323d7d | CC0 Public Domain (http://creativecommons.org/publicdomain/zero/1.0/; "Credit is not mandatory. Commercial use is allowed."; pagina: "CC0 - Download Free 3D model by Avramania [fa90afd] - Sketchfab") | 2026-11-11 | Herbolarios: tiesto (props_int_oficios.glb) |
| Shovel - Low Poly Medieval, CC0 (PROP_AV_Shovel) | Avramania | https://sketchfab.com/3d-models/shovel-low-poly-medieval-cc0-7decd7f6750644fab34f3f54cd9a6a89 | CC0 Public Domain (http://creativecommons.org/publicdomain/zero/1.0/; "Credit is not mandatory. Commercial use is allowed."; pagina: "CC0 - Download Free 3D model by Avramania [7decd7f] - Sketchfab") | 2026-11-11 | Mineros: pala (props_int_oficios.glb) |
| Rocks - Low Poly Medieval, CC0 (PROP_AV_Rocks) | Avramania | https://sketchfab.com/3d-models/rocks-low-poly-medieval-cc0-7aa298b830fc4d6eafa1980adfe0f5cf | CC0 Public Domain (http://creativecommons.org/publicdomain/zero/1.0/; "Credit is not mandatory. Commercial use is allowed."; pagina: "CC0 - Download Free 3D model by Avramania [7aa298b] - Sketchfab") | 2026-11-11 | Mineros: mineral (props_int_oficios.glb) |
| Lantern - Low Poly Medieval, CC0 (PROP_AV_Lantern) | Avramania | https://sketchfab.com/3d-models/lantern-low-poly-medieval-cc0-8a3dc887ea9d48c19ad48469ba11e753 | CC0 Public Domain (http://creativecommons.org/publicdomain/zero/1.0/; "Credit is not mandatory. Commercial use is allowed."; pagina: "CC0 - Download Free 3D model by Avramania [8a3dc88] - Sketchfab") | 2026-11-11 | Mineros: farol (props_int_oficios.glb) |
| Crossbow - Low Poly Medieval, CC0 (PROP_AV_Crossbow) | Avramania | https://sketchfab.com/3d-models/crossbow-low-poly-medieval-cc0-0daff83382444c95b022de235cea1ceb | CC0 Public Domain (http://creativecommons.org/publicdomain/zero/1.0/; "Credit is not mandatory. Commercial use is allowed."; pagina: "CC0 - Download Free 3D model by Avramania [0daff83] - Sketchfab") | 2026-11-11 | Cazadores: ballesta (props_int_oficios.glb) |
| Arrow - Low Poly Medieval, CC0 (PROP_AV_Arrow) | Avramania | https://sketchfab.com/3d-models/arrow-low-poly-medieval-cc0-cc820300ee694dd5aae898a87ccc6c67 | CC0 Public Domain (http://creativecommons.org/publicdomain/zero/1.0/; "Credit is not mandatory. Commercial use is allowed."; pagina: "CC0 - Download Free 3D model by Avramania [cc82030] - Sketchfab") | 2026-11-11 | Cazadores: flecha (props_int_oficios.glb) |
| Axe - Low Poly Medieval, CC0 (PROP_AV_Axe) | Avramania | https://sketchfab.com/3d-models/axe-low-poly-medieval-cc0-b8142e327147499a83add0dfcb1a32d9 | CC0 Public Domain (http://creativecommons.org/publicdomain/zero/1.0/; "Credit is not mandatory. Commercial use is allowed."; pagina: "CC0 - Download Free 3D model by Avramania [b8142e3] - Sketchfab") | 2026-11-11 | Reparaciones: hacha (props_int_oficios.glb) |
| Handaxe - Low Poly Medieval, CC0 (PROP_AV_Handaxe) | Avramania | https://sketchfab.com/3d-models/handaxe-low-poly-medieval-cc0-f12b9a6915a34c59bf4ea3d5634a03f5 | CC0 Public Domain (http://creativecommons.org/publicdomain/zero/1.0/; "Credit is not mandatory. Commercial use is allowed."; pagina: "CC0 - Download Free 3D model by Avramania [f12b9a6] - Sketchfab") | 2026-11-11 | Reparaciones: hachuela (props_int_oficios.glb); decimado 504 -> 480 con normal map textures/props/PROP_AV_Handaxe_normal_512.png |

### Lote Clases (8 salones y Casa de Reposicion)

Quaternius - Fantasy Props MegaKit (Standard): descargado de OpenGameArt (fantasy_props_megakitstandard.zip,
sha256 0bc1e5843c9f245c44bda82f97f738b09f88fe51bb34d2a69a7847a969f868e3) el 2026-11-11; licencia copiada en
licenses/Quaternius_FantasyPropsMegaKit_License_Standard.txt.

| Asset | Autor(es) | URL | Licencia | Fecha | Donde se usa |
|---|---|---|---|---|---|
| WeaponStand (PROP_Q_WeaponStand) | Quaternius | https://quaternius.com/packs/fantasypropsmegakit.html (copia en https://opengameart.org/content/fantasy-props-megakit) | CC0 1.0 | 2026-11-11 | Clases: armero grande (props_int_clases.glb); decimado 2084 -> 1480 con normal map textures/props/PROP_Q_WeaponStand_normal_1k.png |
| Shield_Wooden (PROP_Q_Shield_Wooden) | Quaternius | https://quaternius.com/packs/fantasypropsmegakit.html (copia en https://opengameart.org/content/fantasy-props-megakit) | CC0 1.0 | 2026-11-11 | Clases: escudo de madera (props_int_clases.glb) |
| Shelf_Arch (PROP_Q_Shelf_Arch) | Quaternius | https://quaternius.com/packs/fantasypropsmegakit.html (copia en https://opengameart.org/content/fantasy-props-megakit) | CC0 1.0 | 2026-11-11 | Casa de Reposicion: estante de arco (props_int_clases.glb) |
| SmallBottles_1 (PROP_Q_SmallBottles_1) | Quaternius | https://quaternius.com/packs/fantasypropsmegakit.html (copia en https://opengameart.org/content/fantasy-props-megakit) | CC0 1.0 | 2026-11-11 | Casa de Reposicion: frascos (props_int_clases.glb) |

Avramania - Low Poly Medieval (Sketchfab): licencia comprobada el dia de la descarga en la API (/v3/models/<uid>)
y en la pagina publica del modelo (texto de la licencia citado).

| Asset | Autor(es) | URL | Licencia | Fecha | Donde se usa |
|---|---|---|---|---|---|
| Pew - Low Poly Medieval, CC0 (PROP_AV_Pew) | Avramania | https://sketchfab.com/3d-models/pew-low-poly-medieval-cc0-ba2de923a54547beaddc1f49e000b3d3 | CC0 Public Domain (http://creativecommons.org/publicdomain/zero/1.0/; "Credit is not mandatory. Commercial use is allowed."; pagina: "CC0 - Download Free 3D model by Avramania [ba2de92] - Sketchfab") | 2026-11-11 | Clases: banco con respaldo (props_int_clases.glb) |
| Rack - Low Poly Medieval, CC0 (PROP_AV_Rack) | Avramania | https://sketchfab.com/3d-models/rack-low-poly-medieval-cc0-3ced62581eb84f9a914cb1d120d2d519 | CC0 Public Domain (http://creativecommons.org/publicdomain/zero/1.0/; "Credit is not mandatory. Commercial use is allowed."; pagina: "CC0 - Download Free 3D model by Avramania [3ced625] - Sketchfab") | 2026-11-11 | Clases: armero (props_int_clases.glb) |
| Chest - Low Poly Medieval, CC0 (PROP_AV_Chest) | Avramania | https://sketchfab.com/3d-models/chest-low-poly-medieval-cc0-94a5f575c311487b8fbd6091b09abd94 | CC0 Public Domain (http://creativecommons.org/publicdomain/zero/1.0/; "Credit is not mandatory. Commercial use is allowed."; pagina: "CC0 - Download Free 3D model by Avramania [94a5f57] - Sketchfab") | 2026-11-11 | Clases: arcon (props_int_clases.glb) |
| Shield Round - Low Poly Medieval, CC0 (PROP_AV_Shield_Round) | Avramania | https://sketchfab.com/3d-models/shield-round-low-poly-medieval-cc0-b0f1cb5493bd4af8a829c49816a1cf79 | CC0 Public Domain (http://creativecommons.org/publicdomain/zero/1.0/; "Credit is not mandatory. Commercial use is allowed."; pagina: "CC0 - Download Free 3D model by Avramania [b0f1cb5] - Sketchfab") | 2026-11-11 | Clases: escudo redondo (props_int_clases.glb) |
| Armingsword - Low Poly Medieval, CC0 (PROP_AV_Armingsword) | Avramania | https://sketchfab.com/3d-models/armingsword-low-poly-medieval-cc0-b935b180c92c4fe79c067113d8929cb4 | CC0 Public Domain (http://creativecommons.org/publicdomain/zero/1.0/; "Credit is not mandatory. Commercial use is allowed."; pagina: "CC0 - Download Free 3D model by Avramania [b935b18] - Sketchfab") | 2026-11-11 | Clases: espada (props_int_clases.glb) |
| Shortsword - Low Poly Medieval, CC0 (PROP_AV_Shortsword) | Avramania | https://sketchfab.com/3d-models/shortsword-low-poly-medieval-cc0-0be8094364f4482f9ddad92236514b96 | CC0 Public Domain (http://creativecommons.org/publicdomain/zero/1.0/; "Credit is not mandatory. Commercial use is allowed."; pagina: "CC0 - Download Free 3D model by Avramania [0be8094] - Sketchfab") | 2026-11-11 | Clases: espada corta (props_int_clases.glb) |
| Dagger - Low Poly Medieval, CC0 (PROP_AV_Dagger) | Avramania | https://sketchfab.com/3d-models/dagger-low-poly-medieval-cc0-78265b91861e406ea62acaa67b78d60b | CC0 Public Domain (http://creativecommons.org/publicdomain/zero/1.0/; "Credit is not mandatory. Commercial use is allowed."; pagina: "CC0 - Download Free 3D model by Avramania [78265b9] - Sketchfab") | 2026-11-11 | Clases: daga (props_int_clases.glb) |
| Staff - Low Poly Medieval, CC0 (PROP_AV_Staff) | Avramania | https://sketchfab.com/3d-models/staff-low-poly-medieval-cc0-3b71fc881aaf4602ad53605474baf0ff | CC0 Public Domain (http://creativecommons.org/publicdomain/zero/1.0/; "Credit is not mandatory. Commercial use is allowed."; pagina: "CC0 - Download Free 3D model by Avramania [3b71fc8] - Sketchfab") | 2026-11-11 | Clases: baston (props_int_clases.glb) |
| Rug - Low Poly Medieval, CC0 (PROP_AV_Rug) | Avramania | https://sketchfab.com/3d-models/rug-low-poly-medieval-cc0-3899142ec92c46059d35fc0fa1a0bd41 | CC0 Public Domain (http://creativecommons.org/publicdomain/zero/1.0/; "Credit is not mandatory. Commercial use is allowed."; pagina: "CC0 - Download Free 3D model by Avramania [3899142] - Sketchfab") | 2026-11-11 | Clases: esterilla (props_int_clases.glb) |

## Personajes (PJ1 en adelante)

Herramienta y base usadas para el cuerpo del elfo (blender/elfo_v01.blend, export/godot/pj_elfo_cuerpo.glb). Se
instalaron solo desde las dos fuentes oficiales; no se ejecuto ningun .exe, instalador ni script suelto; el paquete
de assets se descomprimio solo en la carpeta de datos del addon. Copias de los dos paquetes en
respaldo/2026-11-11/fuentes_assets/.

| Asset | Autor | URL | Licencia | Fecha | Version y sha256 | Donde se usa |
|---|---|---|---|---|---|---|
| MPFB (extension de Blender) | MakeHuman Community | https://extensions.blender.org/add-ons/mpfb/ (FAQ de uso en proyectos cerrados: https://static.makehumancommunity.org/mpfb/faq/use_in_closed_source.html; licencia: https://static.makehumancommunity.org/about/license.html) | GPL-3.0-or-later para el codigo del addon; segun la FAQ oficial, los modelos generados y exportados no quedan sujetos a la GPL. No se redistribuye el addon | 2026-11-11 | 2.0.18; add-on-mpfb-v2.0.18.zip sha256 c075b3e9b94b8e5556a5f03f4653602d02ea306de08126e8f55ed6dee28a2dad | solo herramienta de construccion (tools/blender/pj_mpfb.py, build_pj1_elfo.py) |
| MakeHuman system assets (malla base, targets, rig 'default' para la pose T, proxy male1591, ojos low-poly) | MakeHuman Community | https://files.makehumancommunity.org/asset_packs/makehuman_system_assets/makehuman_system_assets_cc0.zip | CC0 1.0 | 2026-11-11 | makehuman_system_assets_cc0.zip sha256 b542127a8e25547c7c29c19f2d1d2adb9a664c80396ecd694095dbc8028a0107 | base del cuerpo del elfo (PJ_Elfo_Head/Torso/Arms/Hands/Legs/Feet, PJ_Elfo_Eyes); ver lo propio de Concordia abajo |
| Blender | Blender Foundation | https://www.blender.org/ | GPL (herramienta; los ficheros producidos no quedan sujetos a ella) | - | bpy 4.5 | herramienta |

Propio de Concordia sobre esa base: proporciones (hombros -8 %, pierna/torso +6 %, cuello +17 % frente a un humano
de referencia con los mismos macros), cara (pomulos, ojos rasgados, nariz y boca), orejas rehechas (subdivision,
largo 13,5 cm, 28 grados atras, perfil de hoja, concha y borde), division en 6 piezas, grupos HIDE_* y todas las
texturas (ver la tabla siguiente). Informe: docs/reports/pj1_elfo_cuerpo.json.

## Animaciones (PJ4)

Descargadas el 2026-11-11 desde el mirror de OpenGameArt (no hizo falta itch.io ni iniciar sesion). Solo se
extrajeron los archivos de datos (.glb, License.txt, imagenes de muestra); los .fbx y el .blend del maniqui no se
abrieron. Zips originales en respaldo/ual_original/ (fuera de git); textos de licencia en licenses/.
No se retargetean en Blender: Godot lo hace al importar (BoneMap + SkeletonProfileHumanoid, ver
TODO_GODOT_personaje.txt).

| Asset | Autor | URL | Licencia | Fecha | Archivo y sha256 del zip | Donde se usa |
|---|---|---|---|---|---|---|
| Universal Animation Library [Standard] (46 animaciones, rig de 53 huesos DEF-* estilo Rigify, version para Godot) | Quaternius | https://opengameart.org/content/universal-animation-library (pagina del autor: https://quaternius.com/packs/universalanimationlibrary.html) | CC0 1.0 (licenses/Quaternius_UAL1_Standard_License.txt) | 2026-11-11 | universal_animation_librarystandard.zip sha256 18ff1a7215f4852b320203e8aaf02a1578b5c8eef9027fbaedfcedc7b85a3ac2 -> animations/ual/ual1/AnimationLibrary_Godot_Standard.glb | animaciones base del elfo en Godot (Idle, Walk, Run, Sit, Hit, Death, Spell_Simple); G8 |
| Universal Animation Library 2 [Standard] (43 animaciones, rig de 65 huesos estilo Unreal + maniqui femenino sin animaciones) | Quaternius | https://opengameart.org/content/universal-animation-library-2 (pagina del autor: https://quaternius.itch.io/universal-animation-library-2) | CC0 1.0 (licenses/Quaternius_UAL2_Standard_License.txt) | 2026-11-11 | universal_animation_library_2standard.zip sha256 ec0e40d6d78fe9aaad59e322f40865a8675c22f0745e291622e54520391a9217 -> animations/ual/ual2/UAL2_Standard.glb, Mannequin_F.glb | complemento (Hit_Knockback, Consume, LayToIdle, Yes, Idle_No, Chest_Open...); G8 |

Animaciones propias del Sanador (Heal_Cast_Single, Heal_Channel-loop, Heal_Cast_Area, Revive): hechas a mano en
el proyecto (tools/blender/build_pj4_anim.py), sin licencia de terceros.

Version descargada: SOLO la Standard gratuita de las dos librerias (zips universal_animation_librarystandard.zip y
universal_animation_library_2standard.zip de OpenGameArt, 2026-11-11; nada de Pro ni Source, no se ha comprado nada).
Animaciones que usa el elfo Sanador (seleccion en animations/ual/sanador_ual1_seleccion.glb y
sanador_ual2_seleccion.glb, sobre los esqueletos originales; tools/blender/build_pj4b_ual_seleccion.py):

| Animacion en Concordia | Fuente | Clip original | URL | Licencia | Fecha |
|---|---|---|---|---|---|
| Idle_Loop, Walk_Loop, Walk_Formal_Loop, Jog_Fwd_Loop, Sprint_Loop | UAL 1 Standard | mismos nombres | https://opengameart.org/content/universal-animation-library | CC0 1.0 | 2026-11-11 |
| Sitting_Enter, Sitting_Idle_Loop, Sitting_Exit, Sitting_Talking_Loop | UAL 1 Standard | mismos nombres | idem | CC0 1.0 | 2026-11-11 |
| Hit_Chest, Hit_Head | UAL 1 Standard | mismos nombres | idem | CC0 1.0 | 2026-11-11 |
| Spell_Simple_Enter, Spell_Simple_Idle_Loop, Spell_Simple_Shoot, Spell_Simple_Exit | UAL 1 Standard | mismos nombres | idem | CC0 1.0 | 2026-11-11 |
| Death_A | UAL 1 Standard | Death01 | idem | CC0 1.0 | 2026-11-11 |
| Death_B | derivada de UAL 1 Standard (espejo + ajustes de cabeza y brazos, en Concordia) | Death01 | idem | CC0 1.0 (la obra derivada es propia) | 2026-11-11 |
| GetUp, GetUp_B | UAL 2 Standard (+ 7 fotogramas de transicion hechos en Concordia) | LayToIdle | https://opengameart.org/content/universal-animation-library-2 | CC0 1.0 | 2026-11-11 |
| Consume, Yes, Chest_Open, Hit_Knockback | UAL 2 Standard | mismos nombres | idem | CC0 1.0 | 2026-11-11 |
| Idle_No-loop, Idle_FoldArms-loop | UAL 2 Standard | Idle_No_Loop, Idle_FoldArms_Loop | idem | CC0 1.0 | 2026-11-11 |

### Cierre del personaje (PJ5): de donde sale cada parte de los .glb finales (export/godot/personajes/)

| Parte | Fuente | Licencia |
|---|---|---|
| Malla base del cuerpo, rig de referencia para la pose T, ojos low-poly, proxy | MakeHuman system assets (via MPFB 2.0.18 como herramienta) | CC0 1.0 (ver tabla de arriba); MPFB no se redistribuye |
| Proporciones, cara, orejas, division en piezas, grupos HIDE_*, LODs (LOD1 y LOD2) | Concordia (tools/blender/build_pj1_elfo.py ... build_pj5_lods_export.py) | propio |
| Texturas de piel y del atlas del Sanador (albedo, normal, ORM, emision) | Concordia (generadas por script, pj1_piel.py y pj2_atlas.py) | propio |
| Ropa del Sanador, cabello y trenza | Concordia (pj2_geo.py) | propio |
| Esqueleto de 70 huesos (nombres del SkeletonProfileHumanoid de Godot + 14 extra) | Concordia (concordia_rig.py; nombres segun la documentacion de Godot 4.7) | propio |
| Animaciones propias Heal_Cast_Single, Heal_Channel-loop, Heal_Cast_Area, Revive | Concordia (build_pj4_anim.py) | propio |
| Animaciones base (Idle, Walk, Run, Sit, Hit, Death, Spell) | Universal Animation Library 1 y 2 Standard, Quaternius (seccion Animaciones) | CC0 1.0 |
| Herramientas | Blender 4.5 (bpy), Godot 4.7.2 | GPL / MIT (no afectan a los archivos producidos) |

## Generados en el proyecto (sin licencia de terceros)

| Asset | Origen | Donde se usa |
|---|---|---|
| Estandartes de clase y de raza (MAT_Banner_*) | generados por script (etapas 20-21) | Clases, Razas |
| Atlas de numeros de las cajas (MAT_Bank_BoxNumbers, 1K) | tools/blender/stage27_banco.py (fuente DejaVu Serif, licencia libre de Bitstream Vera/DejaVu) | interior del Banco |
| Plementeria con estrellas (MAT_Vault_Stars, 1K) | tools/blender/stage29_santuario.py (generada con PIL, propia) | boveda del Santuario (etapa 29) |
| Texturas de MAT_Shard_Blue, MAT_Wall_Runes y MAT_Water (T_*.jpg) | horneadas de nodos procedurales (tools/blender/stage09_materials.py) | esquirlas, runas, cauce |
| Props a mano de la etapa 28 (telar, fuelle, maniqui, casco de minero y 14 triviales) | tools/blender/props_mano.py | props_int_mano.glb |
| Kit de interiores BLD_INT_KIT y todo el interior del Banco | modelado por script (etapa 27) | int_banco.glb |
| Piel del elfo (albedo 1K tonos abedul y corteza, normal 1K, ORM 1K) y ojos (albedo 256) | horneadas por tools/blender/pj1_piel.py (color por vertice + ruido; normal y AO de la malla base de MakeHuman, CC0) | textures/personajes/elfo/, pj_elfo_cuerpo.glb |
| Conjunto del Sanador (Robe_Top, Robe_Skirt, Hood, Belt_Pouches, Boots, Bracers) y Hair_Elf, con su atlas 1K (textures/personajes/sanador/) | modelado y pintado por script (tools/blender/pj2_geo.py, pj2_atlas.py); sin assets descargados | pj_sanador_ropa.glb, elfo_v02.blend |
