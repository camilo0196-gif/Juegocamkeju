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

## Modelos 3D (props)

Ninguno importado todavia. Candidatos propuestos en la etapa 26 (pendientes de aprobacion): Quaternius Fantasy Props
MegaKit (CC0), serie "Low Poly Medieval" de Avramania en Sketchfab (CC0), modelos de Poly Haven (CC0).

## Generados en el proyecto (sin licencia de terceros)

| Asset | Origen | Donde se usa |
|---|---|---|
| Estandartes de clase y de raza (MAT_Banner_*) | generados por script (etapas 20-21) | Clases, Razas |
| Atlas de numeros de las cajas (MAT_Bank_BoxNumbers, 1K) | tools/blender/stage27_banco.py (fuente DejaVu Serif, licencia libre de Bitstream Vera/DejaVu) | interior del Banco |
| Kit de interiores BLD_INT_KIT y todo el interior del Banco | modelado por script (etapa 27) | int_banco.glb |
