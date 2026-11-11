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
como base, Poly Haven para casos sueltos. Todos se reasignan a materiales de Concordia; los de mas de 1,700
triangulos se decimaron a <= 1,500 con normal map horneado (textures/props/). Informe: docs/reports/stage28_props_import.json.
Ningun asset descargado se usa en Portal, Faro, Obelisco, Santuario, Salon de las Hazanas, Banco, Tesoreria, Crisol
ni en los edificios de barrios y moradas (solo mobiliario, decision del usuario en la etapa 28).

### Quaternius - Fantasy Props MegaKit (Standard), lote Mercado

Descargado de OpenGameArt (fantasy_props_megakitstandard.zip, sha256 0bc1e5843c9f245c44bda82f97f738b09f88fe51bb34d2a69a7847a969f868e3) el 2026-11-11; licencia copiada
en licenses/. Uso: blender/concordia_props_v01.blend (BLD_PROPS_INT) y export/godot/props_int_mercado.glb.

| Asset | Autor(es) | URL | Licencia | Fecha | Donde se usa |
|---|---|---|---|---|---|
| Table_Large (PROP_Q_Table_Large) | Quaternius | https://quaternius.com/packs/fantasypropsmegakit.html (copia en https://opengameart.org/content/fantasy-props-megakit) | CC0 1.0 (licenses/Quaternius_FantasyPropsMegaKit_License_Standard.txt) | 2026-11-11 | Posada: mesa larga |
| Chair_1 (PROP_Q_Chair_1) | Quaternius | https://quaternius.com/packs/fantasypropsmegakit.html (copia en https://opengameart.org/content/fantasy-props-megakit) | CC0 1.0 (licenses/Quaternius_FantasyPropsMegaKit_License_Standard.txt) | 2026-11-11 | Posada / Registro: silla; interiores de Moradas (int_morada_*.glb) |
| Bench (PROP_Q_Bench) | Quaternius | https://quaternius.com/packs/fantasypropsmegakit.html (copia en https://opengameart.org/content/fantasy-props-megakit) | CC0 1.0 (licenses/Quaternius_FantasyPropsMegaKit_License_Standard.txt) | 2026-11-11 | Posada: banco |
| Stool (PROP_Q_Stool) | Quaternius | https://quaternius.com/packs/fantasypropsmegakit.html (copia en https://opengameart.org/content/fantasy-props-megakit) | CC0 1.0 (licenses/Quaternius_FantasyPropsMegaKit_License_Standard.txt) | 2026-11-11 | Posada: taburete; interiores de Moradas (int_morada_*.glb) |
| Barrel_Holder (PROP_Q_Barrel_Holder) | Quaternius | https://quaternius.com/packs/fantasypropsmegakit.html (copia en https://opengameart.org/content/fantasy-props-megakit) | CC0 1.0 (licenses/Quaternius_FantasyPropsMegaKit_License_Standard.txt) | 2026-11-11 | Posada: barril en soporte |
| Mug (PROP_Q_Mug) | Quaternius | https://quaternius.com/packs/fantasypropsmegakit.html (copia en https://opengameart.org/content/fantasy-props-megakit) | CC0 1.0 (licenses/Quaternius_FantasyPropsMegaKit_License_Standard.txt) | 2026-11-11 | Posada: jarra; interiores de Moradas (int_morada_*.glb) |
| Table_Plate (PROP_Q_Table_Plate) | Quaternius | https://quaternius.com/packs/fantasypropsmegakit.html (copia en https://opengameart.org/content/fantasy-props-megakit) | CC0 1.0 (licenses/Quaternius_FantasyPropsMegaKit_License_Standard.txt) | 2026-11-11 | Posada: plato |
| Table_Knife (PROP_Q_Table_Knife) | Quaternius | https://quaternius.com/packs/fantasypropsmegakit.html (copia en https://opengameart.org/content/fantasy-props-megakit) | CC0 1.0 (licenses/Quaternius_FantasyPropsMegaKit_License_Standard.txt) | 2026-11-11 | Posada: cuchillo |
| Table_Fork (PROP_Q_Table_Fork) | Quaternius | https://quaternius.com/packs/fantasypropsmegakit.html (copia en https://opengameart.org/content/fantasy-props-megakit) | CC0 1.0 (licenses/Quaternius_FantasyPropsMegaKit_License_Standard.txt) | 2026-11-11 | Posada: tenedor |
| Table_Spoon (PROP_Q_Table_Spoon) | Quaternius | https://quaternius.com/packs/fantasypropsmegakit.html (copia en https://opengameart.org/content/fantasy-props-megakit) | CC0 1.0 (licenses/Quaternius_FantasyPropsMegaKit_License_Standard.txt) | 2026-11-11 | Posada: cuchara |
| Candle_1 (PROP_Q_Candle_1) | Quaternius | https://quaternius.com/packs/fantasypropsmegakit.html (copia en https://opengameart.org/content/fantasy-props-megakit) | CC0 1.0 (licenses/Quaternius_FantasyPropsMegaKit_License_Standard.txt) | 2026-11-11 | Posada / Registro: vela; interiores de Moradas (int_morada_*.glb) |
| CandleStick (PROP_Q_CandleStick) | Quaternius | https://quaternius.com/packs/fantasypropsmegakit.html (copia en https://opengameart.org/content/fantasy-props-megakit) | CC0 1.0 (licenses/Quaternius_FantasyPropsMegaKit_License_Standard.txt) | 2026-11-11 | Posada / Registro: candelero; interiores de Moradas (int_morada_*.glb) |
| Chandelier (PROP_Q_Chandelier) | Quaternius | https://quaternius.com/packs/fantasypropsmegakit.html (copia en https://opengameart.org/content/fantasy-props-megakit) | CC0 1.0 (licenses/Quaternius_FantasyPropsMegaKit_License_Standard.txt) | 2026-11-11 | Posada: lampara de techo |
| Workbench_Drawers (PROP_Q_Workbench_Drawers) | Quaternius | https://quaternius.com/packs/fantasypropsmegakit.html (copia en https://opengameart.org/content/fantasy-props-megakit) | CC0 1.0 (licenses/Quaternius_FantasyPropsMegaKit_License_Standard.txt) | 2026-11-11 | Registro: cajonera del escritorio |
| Shelf_Simple (PROP_Q_Shelf_Simple) | Quaternius | https://quaternius.com/packs/fantasypropsmegakit.html (copia en https://opengameart.org/content/fantasy-props-megakit) | CC0 1.0 (licenses/Quaternius_FantasyPropsMegaKit_License_Standard.txt) | 2026-11-11 | Registro: estante |
| BookGroup_Medium_1 (PROP_Q_BookGroup_Medium_1) | Quaternius | https://quaternius.com/packs/fantasypropsmegakit.html (copia en https://opengameart.org/content/fantasy-props-megakit) | CC0 1.0 (licenses/Quaternius_FantasyPropsMegaKit_License_Standard.txt) | 2026-11-11 | Registro: libros en estante |
| BookStand (PROP_Q_BookStand) | Quaternius | https://quaternius.com/packs/fantasypropsmegakit.html (copia en https://opengameart.org/content/fantasy-props-megakit) | CC0 1.0 (licenses/Quaternius_FantasyPropsMegaKit_License_Standard.txt) | 2026-11-11 | Registro: atril |
| Scroll_1 (PROP_Q_Scroll_1) | Quaternius | https://quaternius.com/packs/fantasypropsmegakit.html (copia en https://opengameart.org/content/fantasy-props-megakit) | CC0 1.0 (licenses/Quaternius_FantasyPropsMegaKit_License_Standard.txt) | 2026-11-11 | Registro: pergamino |
| Scroll_2 (PROP_Q_Scroll_2) | Quaternius | https://quaternius.com/packs/fantasypropsmegakit.html (copia en https://opengameart.org/content/fantasy-props-megakit) | CC0 1.0 (licenses/Quaternius_FantasyPropsMegaKit_License_Standard.txt) | 2026-11-11 | Registro: pergamino abierto |
| Book_Stack_1 (PROP_Q_Book_Stack_1) | Quaternius | https://quaternius.com/packs/fantasypropsmegakit.html (copia en https://opengameart.org/content/fantasy-props-megakit) | CC0 1.0 (licenses/Quaternius_FantasyPropsMegaKit_License_Standard.txt) | 2026-11-11 | Registro: pila de libros |
| Book_Stack_2 (PROP_Q_Book_Stack_2) | Quaternius | https://quaternius.com/packs/fantasypropsmegakit.html (copia en https://opengameart.org/content/fantasy-props-megakit) | CC0 1.0 (licenses/Quaternius_FantasyPropsMegaKit_License_Standard.txt) | 2026-11-11 | Registro: pila de libros con cierre |
| Chest_Wood (PROP_Q_Chest_Wood) | Quaternius | https://quaternius.com/packs/fantasypropsmegakit.html (copia en https://opengameart.org/content/fantasy-props-megakit) | CC0 1.0 (licenses/Quaternius_FantasyPropsMegaKit_License_Standard.txt) | 2026-11-11 | Gran Subasta: arcon de lotes; interiores de Moradas (int_morada_*.glb) |
| Coin_Pile (PROP_Q_Coin_Pile) | Quaternius | https://quaternius.com/packs/fantasypropsmegakit.html (copia en https://opengameart.org/content/fantasy-props-megakit) | CC0 1.0 (licenses/Quaternius_FantasyPropsMegaKit_License_Standard.txt) | 2026-11-11 | Gran Subasta: monedas |
| Pouch_Large (PROP_Q_Pouch_Large) | Quaternius | https://quaternius.com/packs/fantasypropsmegakit.html (copia en https://opengameart.org/content/fantasy-props-megakit) | CC0 1.0 (licenses/Quaternius_FantasyPropsMegaKit_License_Standard.txt) | 2026-11-11 | Gran Subasta: bolsa de monedas |
| Bag (PROP_Q_Bag) | Quaternius | https://quaternius.com/packs/fantasypropsmegakit.html (copia en https://opengameart.org/content/fantasy-props-megakit) | CC0 1.0 (licenses/Quaternius_FantasyPropsMegaKit_License_Standard.txt) | 2026-11-11 | Gran Subasta / puestos: saco |

### Avramania - Low Poly Medieval (Sketchfab), lote Mercado

Licencia comprobada en cada descarga en la API (/v3/models/<uid>) y en la pagina publica del modelo.

| Asset | Autor(es) | URL | Licencia | Fecha | Donde se usa |
|---|---|---|---|---|---|
| Village Hearth - Low Poly Medieval, CC0 (PROP_AV_Village_Hearth) | Avramania | https://sketchfab.com/3d-models/village-hearth-low-poly-medieval-cc0-1b9b17a3cb0f44dd9141e70fba061c71 | CC0 Public Domain (API: "CC0 Public Domain"; pagina: "CC0 - Download Free 3D model by Avramania [1b9b17a] - Sketchfab") | 2026-11-11 | Posada: hogar |
| Potcrane - Low Poly Medieval, CC0 (PROP_AV_Potcrane) | Avramania | https://sketchfab.com/3d-models/potcrane-low-poly-medieval-cc0-d041cc0462ab4da6be30fff811765685 | CC0 Public Domain (API: "CC0 Public Domain"; pagina: "CC0 - Download Free 3D model by Avramania [d041cc0] - Sketchfab") | 2026-11-11 | Posada: pescante del hogar |
| Bed - Low Poly Medieval, CC0 (PROP_AV_Bed) | Avramania | https://sketchfab.com/3d-models/bed-low-poly-medieval-cc0-24704040010a42ceaeffb1631ed1ae9b | CC0 Public Domain (API: "CC0 Public Domain"; pagina: "CC0 - Download Free 3D model by Avramania [2470404] - Sketchfab") | 2026-11-11 | Posada: cama |
| Table - Low Poly Medieval, CC0 (PROP_AV_Table) | Avramania | https://sketchfab.com/3d-models/table-low-poly-medieval-cc0-bd0ad320c35249b9b1a37e2adc061bb9 | CC0 Public Domain (API: "CC0 Public Domain"; pagina: "CC0 - Download Free 3D model by Avramania [bd0ad32] - Sketchfab") | 2026-11-11 | Registro: mesa del escritorio; interiores de Moradas (int_morada_*.glb) |
| Apple - Low Poly Medieval, CC0 (PROP_AV_Apple) | Avramania | https://sketchfab.com/3d-models/apple-low-poly-medieval-cc0-64e25ccc90c84e3b8c2ad02dd39150ba | CC0 Public Domain (API: "CC0 Public Domain"; pagina: "CC0 - Download Free 3D model by Avramania [64e25cc] - Sketchfab") | 2026-11-11 | puestos: manzanas |
| Carrot - Low Poly Medieval, CC0 (PROP_AV_Carrot) | Avramania | https://sketchfab.com/3d-models/carrot-low-poly-medieval-cc0-3f3b24dd3bf24ce49b518bfbd5ec93df | CC0 Public Domain (API: "CC0 Public Domain"; pagina: "CC0 - Download Free 3D model by Avramania [3f3b24d] - Sketchfab") | 2026-11-11 | puestos: zanahorias |
| Onion - Low Poly Medieval, CC0 (PROP_AV_Onion) | Avramania | https://sketchfab.com/3d-models/onion-low-poly-medieval-cc0-a8a9568469524a548ca730b1058de3ef | CC0 Public Domain (API: "CC0 Public Domain"; pagina: "CC0 - Download Free 3D model by Avramania [a8a9568] - Sketchfab") | 2026-11-11 | puestos: cebollas |
| Loaf - Low Poly Medieval, CC0 (PROP_AV_Loaf) | Avramania | https://sketchfab.com/3d-models/loaf-low-poly-medieval-cc0-fe8f28bcadaf44a7836e12fe30f9a3dd | CC0 Public Domain (API: "CC0 Public Domain"; pagina: "CC0 - Download Free 3D model by Avramania [fe8f28b] - Sketchfab") | 2026-11-11 | puestos: pan |
| Cheese Wheel - Low Poly Medieval, CC0 (PROP_AV_Cheese_Wheel) | Avramania | https://sketchfab.com/3d-models/cheese-wheel-low-poly-medieval-cc0-c66175e51d044dfda9e6edff21d4d38a | CC0 Public Domain (API: "CC0 Public Domain"; pagina: "CC0 - Download Free 3D model by Avramania [c66175e] - Sketchfab") | 2026-11-11 | puestos: queso |
| Grapes - Low Poly Medieval, CC0 (PROP_AV_Grapes) | Avramania | https://sketchfab.com/3d-models/grapes-low-poly-medieval-cc0-cc950686a4dc4ac89edda92b21afca11 | CC0 Public Domain (API: "CC0 Public Domain"; pagina: "CC0 - Download Free 3D model by Avramania [cc95068] - Sketchfab") | 2026-11-11 | puestos: uvas |
| Grain Sack - Low Poly Medieval, CC0 (PROP_AV_Grain_Sack) | Avramania | https://sketchfab.com/3d-models/grain-sack-low-poly-medieval-cc0-7db2a14529fd4e1f9391c68337f71eac | CC0 Public Domain (API: "CC0 Public Domain"; pagina: "CC0 - Download Free 3D model by Avramania [7db2a14] - Sketchfab") | 2026-11-11 | puestos: saco de grano; interiores de Moradas (int_morada_*.glb) |

## Generados en el proyecto (sin licencia de terceros)

| Asset | Origen | Donde se usa |
|---|---|---|
| Estandartes de clase y de raza (MAT_Banner_*) | generados por script (etapas 20-21) | Clases, Razas |
| Atlas de numeros de las cajas (MAT_Bank_BoxNumbers, 1K) | tools/blender/stage27_banco.py (fuente DejaVu Serif, licencia libre de Bitstream Vera/DejaVu) | interior del Banco |
| Texturas de MAT_Shard_Blue, MAT_Wall_Runes y MAT_Water (T_*.jpg) | horneadas de nodos procedurales (tools/blender/stage09_materials.py) | esquirlas, runas, cauce |
| Props a mano de la etapa 28 (telar, fuelle, maniqui, casco de minero y 14 triviales) | tools/blender/props_mano.py | props_int_mano.glb |
| Kit de interiores BLD_INT_KIT y todo el interior del Banco | modelado por script (etapa 27) | int_banco.glb |
