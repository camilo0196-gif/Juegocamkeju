# CONCORDIA — documento de traspaso (Opus → nueva conversación con acceso local)

Fecha: 2026-11-12. Repositorio: `https://github.com/camilo0196-gif/Juegocamkeju`, rama de trabajo
`claude/loving-wozniak-yac27d` (último commit de modelo: `9fddcf7`, etapa 29). Este documento no cambia ningún
modelo: solo describe el estado. Todo lo que cito está en la rama salvo lo que se marca como "solo en `respaldo/`".

**Cómo leer este documento**
- Secciones 1–4 y 6–9: escritas para el traspaso, con las cifras medidas.
- Sección 5: todos tus prompts, literales y en orden cronológico (76 mensajes), anexo A.
- Anexos B–K: copia literal de los documentos del repositorio (README, TODO, informes de Godot, licencias), para que
  este archivo sea autosuficiente aunque la nueva conversación aún no haya leído la carpeta.

**Entorno con el que se hizo todo**
- Blender **4.5 LTS sin interfaz** (módulo `bpy` de Python 3.11 en un venv; los scripts se lanzan con
  `python tools/blender/<script>.py`). En tu PC con Blender instalado: `blender -b --python tools/blender/<script>.py`
  (los scripts abren y guardan los .blend ellos mismos; algunos aceptan argumentos tras `--`).
- Render de capturas: Cycles por CPU (`capture_stage02.setup_render`), 1920×1080, 48 muestras.
- Godot **4.7.2 estable** (Forward+); pruebas aquí sin GPU (rasterizador vacío) o con lavapipe/llvmpipe por software.
- No hubo Blender MCP ni generadores de IA en ninguna sesión (`get_addon_status` / `generate_3d` no existían): todo
  se generó por script.
- Red: Poly Haven (api/dl) permitido; github.com, kenney.nl, quaternius.com e itch.io bloqueados en el contenedor.

---

## 0. Numeraciones usadas (para no perderse)

Tú usaste cuatro numeraciones; yo numeré mis entregas como "etapa NN" (archivos `stageNN_*`). Equivalencias:

| Tu código | Mi etapa | Contenido | Archivo principal |
|---|---|---|---|
| (prompt maestro "ROL") | — | reglas generales del proyecto | — |
| Prompt 1 | 01 | escena base, colecciones, CAM_Iso, puertas | concordia_v01.blend |
| Prompt 2 | 02 | terreno de la colina TRN_City | v02 |
| Prompt 3 | 03 | Plaza del Portal | v03 |
| Prompt 4 | 04 | muralla como kit modular | v04 |
| Prompt 5 | 05 | calles y parcelas de los 4 distritos | v05 |
| Prompt 6 | 06 | terreno de las 4 Moradas | v06 |
| Prompt 7 | 07 | Cauce, puentes, arcos, escalinatas | v07 |
| Prompt 8 | 08 | terreno exterior de ceniza | v08 |
| Prompt 9 | 09 | materiales glTF (procedurales) | v09 |
| Prompt 9 (Poly Haven) | 10 | texturas reales Poly Haven, máscaras | v10 |
| Prompt 10/11 (Godot 4) | 11 | limpieza, chunks, LOD, colisión, navmesh, export | concordia_master_v11.blend |
| E0 | 12 | kit modular de edificios + `build_building` | v12 |
| E1 | 13 | Portal y Atrio | v13 |
| E2 | 14 | Obelisco de los Pisos | v14 |
| E3 | 15 (+17) | Torre del Faro (y decisiones sobre el Faro) | v15 / v17 |
| E4 | 16 | Santuario del Retorno y Salón de las Hazañas | v16 |
| (decisiones E3 y pendientes A–E) | 17 | Faro, regla de alturas, LOD2 de lejos, Puente 01 | v17 |
| E5 | 18 | Mercado | v18 |
| E6 | 19 | Oficios | v19 |
| E7 | 20 | Clases | v20 |
| E8 | 21 | Razas | v21 |
| E9 | 22 | conexiones (puentes, arcos, escalinatas, escaleras) | v22 |
| E10 | 23 | viviendas de las Moradas | v23 |
| E11 | 24 | exportación de edificios a Godot y verificación | v24 |
| E12 | 25 | decisiones sobre las pendientes (brasas, Cazadores, Razas, Faro) | v25 |
| E13 | 26 | decisiones sobre el balance (Moradas, tubos, Faro, repositorio) | v26 |
| (fuentes de assets) | — | aprobación de fuentes CC0 (sin construir) | — |
| E14 | 27 | interiores: kit BLD_INT_KIT, `build_interior`, piloto del Banco | concordia_interiors_v01.blend |
| (balance + decisiones) | 28 | props a mano e importados, vitrinas, interiores tipo de Moradas, ciudad v28 | v28, props_v01, moradas_int_v01 |
| PJ0–PJ5, PJ4b | — | personaje: elfo Sanador | elfo_v01..v04, concordia_personajes_master.blend |
| G0–G5 (+ parada 1 ampliada) | — | proyecto de Godot | godot_concordia/ |
| (arreglo PC, A–F) | — | errores de tu PC: mundo horneado, streaming, calidad F2 | godot_concordia/ |
| (interiores, resto) | 29 | Tesorería y Santuario | concordia_interiors_unicos_v01.blend |

Tu "E0–E28" lo interpreto como todo el proyecto hasta la etapa 28 (y añado la 29).

---

## 1. Estado por etapa

Leyenda: **HECHO** = cumple lo pedido; **PARCIAL** = hecho con desvíos aceptados o pendientes; **PENDIENTE** = no empezado.

### 1.1 Ciudad: terreno, muralla y materiales (etapas 01–11)

| Etapa | Estado | Cifras clave | Desvíos / notas |
|---|---|---|---|
| 01 Escena base | HECHO | 9 colecciones (TERRAIN, PLAZA, WALL_KIT, WALL_LAYOUT, STREETS, MARKERS_DISTRICTS, MORADAS, CAUCE, EXTERIOR); `CAM_Iso` ortográfica escala 120, rotación (54.736°, 0, 45°); 4 puertas a r = 200 (Alba E, Norte, Ocaso O, Sur) a Z = +6; sectores 4 × 50° cardinales + 4 × 40° Moradas | `concordia_const.py` = única fuente de datos fijos |
| 02 Terreno de la colina | HECHO | TRN_City malla maestra de 1 m: 154,985 vért. / 308,280 tris tras v2; pendiente máx. en zonas caminables ≤ 4.88°; saltos de terraza 80° (muros de contención 9,528 caras); 6 terrazas por Morada; chunks de 50 m con LOD1/LOD2 | decisiones del Prompt 2: bordes laterales de Moradas opción (a), terraplén al pie de la muralla, plazoletas, escalinatas r 95–105 |
| 03 Plaza del Portal | HECHO | plaza r 60 a +8.0; anillos de losas cada 6 m + 8 bandas de travertino de 0.4 m (máscaras, no geometría); Atrio r 15 a +8.6 con 21 pedestales (pisos 1, 5 … 100) en r 13.5; pedestal del Portal r 6 a +8.9; 7 piedras rúnicas en r 9; 4 canales de luz de 58.95 m; 8 parcelas de 22 × 16 | pendiente máx. de la plaza 4.96° |
| 04 Muralla (kit) | HECHO | 11 piezas en WALL_KIT, 48 posiciones (`MARKER_WallSlot_00..47`), 4 puertas selladas GATE_Sealed_Twin (5,348 tris), 8 torres de guardia; altura 15 m (+21 abs.), ronda a 12.4 m; Mod_A 1,020 / Mod_B 1,192 / Mod_C 2,004 tris | las puertas no tienen camino exterior; runas a +4.5 poco legibles desde el mirador (opciones dadas, no aplicadas en su momento) |
| 05 Calles y parcelas | HECHO | 4 avenidas de 10 m; anillos r 100 (8 m, 10 m en el Mercado) y r 150 (6 m); 48 callejones de 4–5 m (7 ciegos); plazoletas de 30 m; todas las calles ≤ 4.5° | faltaban parcelas en Razas (resuelto en 25–26) |
| 06 Terreno de las Moradas | PARCIAL (aceptado) | 72 parcelas por Morada (no ~100), calle de servicio 3.3–3.4 m (no 4), 14 escaleras de servicio por Morada, `MARKER_Morada_*` (288 al principio; 283 tras la etapa 07) | 19 puertas tapadas en SE en la etapa 06 (se resolvió en la etapa 23 con techos escalonados) |
| 07 Cauce | PARCIAL (aceptado) | canal de 252.6 m × 4 m × 1.2 m, 4 azudes, 10 escaleras de acceso, muelle de Pescadores 8 × 3, hueco de rueda de la Carpintería | el agua no llega a la reja exterior; 5 puentes en vez de 4; 4 arcos entre barrios en vez de 6–8; Cazadores no cabía (resuelto en 25); Morada SE pierde 5 parcelas |
| 08 Exterior de ceniza | HECHO | r 212–400, 98,302 tris, foso seco hasta r 222 (fondo −1.5), 17 rocas, 6 cráteres, acantilados r 380–400 (27,360 tris), 204 chunks exteriores (presupuesto 8,000, máx. 1,319) | desde los miradores el relieve se ve casi plano (anotado) |
| 09 Materiales | HECHO | 18 materiales glTF de 2048 (procedurales al principio, porque Poly Haven estaba bloqueado); Shard_Blue emisión 2.5; Wall_Runes 0.8 | sustituidos en la 10 |
| 10 Texturas Poly Haven | HECHO | 14 texturas CC0 de Poly Haven (registradas en ASSETS_LICENSES.md), ORM, máscaras de taludes y foso, transiciones dentadas; memoria de texturas de terreno 52 imágenes | roca `rock_boulder_dry`; muralla `castle_wall_varriation` en vez de `castle_wall_slates` (piedra blanca repetida) |
| 11 Preparación para Godot | HECHO | 69 chunks de ciudad (presupuesto 35,000, ninguno lo supera), 204 exteriores; LOD1 225,990 / LOD2 80,476 tris; 84 estructuras con colisión (37,068 tris); navmesh de Blender 45,299 m² (30 componentes); export `concordia_terrain_<distrito>.glb`, `concordia_wall_*.glb`, `concordia_markers.glb` | navmesh de Blender sustituida después por la horneada en Godot |

### 1.2 Edificios (E0–E13, etapas 12–26) — balance a la v28

| Código | Estado | Hecho / esperado | Problemas abiertos |
|---|---|---|---|
| E0 Kit y assembler | HECHO | 45/45 piezas del kit + `concordia_buildings.build_building`; casa de prueba TEST_Casa_12x9 (4,606 tris, LOD1 0.49, LOD2 0.09); codo de 45° añadido en la 26 | TEST_Casa_12x9 exportada sin colisión (FIXES F3) |
| E1 Portal y Atrio | HECHO | trilito, velo 7.8 × 11 m (emisión 3.0), 7/7 piedras, 21/21 pedestales | — |
| E2 Obelisco | HECHO | columna + 100/100 marcas de piso (OBELISK_Mark_001..100), 2,118 tris sin marcas | — |
| E3 Faro | HECHO (objetivo de visibilidad no alcanzado, aceptado) | torre de 40 m, cristal (MAT_Shard_Blue_E40, 4.0), haz FARO_Beam 80 m, rampa decorativa, 4 canales; tubos de luz Tesorería → Faro por la ruta oeste (etapa 28): 130.3 m, 7,418 tris, 13 pilares de piedra (10 en techos, 3 en terreno verde), 4 arcos | visibilidad (criterio de 11 rayos): avenidas 91.7 %, anillos 71.1 %, callejones 76.4 %, diagonales 79.6 % (objetivo 100 / ≥ 90): aceptado porque Godot dibuja cristal y haz encima y hay brújula |
| E4 Santuario y Salón | HECHO | 2/2; Salón con `occludes_iso = true` | el pozo SANTUARIO_Well del master sigue con `provisional = true` (la copia del interior ya no) |
| E5 Mercado | HECHO | 20/20 (Tesorería, Banco, Gran Subasta abierta, Posada con TablonGrupos, 14 puestos, fuente, Registro); MER_Casa_01 bajada de 3 a 2 plantas (14.0 → 10.8 m) por el Faro | — |
| E6 Oficios | HECHO | 13/13 (4 gremios, 7 talleres, Crisol, Casa de Reparaciones); Cazadores dentro de la muralla (casa 12 × 8 + campo 14 × 8 a 84 m, con camino y navmesh) | — |
| E7 Clases | HECHO | 8 salones (plantilla, N_CLASES = 8), Plaza de las Armas (12 maniquíes, 10 blancos, 8 postes), Casa de Reposición (10/10) | presets CLASE_01..08 con nombres genéricos (placeholders) |
| E8 Razas | PARCIAL (aceptado como provisional) | 6 Casas de Raza, 6 plazuelas; casas por barrio B01 6, B02 6, B03 6, B04 6, B05 5, B06 2 = 31/36 | B06 con 2 casas: aceptado como provisional hasta la lista real de razas (plantilla N_RAZAS = 6) |
| E9 Conexiones | HECHO | 9/9 pasos (5 puentes, 4 arcos), 4 escalinatas monumentales, 76 escaleras de terraza, 32 laterales, 10 escalinatas de paso | F6 (escalinatas metidas en rampa) y F10 (escalones > 0.25 m) anotados en FIXES_BLENDER.md |
| E10 Moradas | HECHO con 13 puertas aceptadas | 283 casas (142 habitaciones, 98 casas pequeñas, 43 grandes); **1,398 viviendas** (NE 360, NO 354, SE 330, SO 354); 13 puertas tapadas aceptadas (0.93 % < 1 %; lista en README_buildings §19) | Godot aclara techos y aleros al acercarse (G6) |
| E11 Godot y verificación | HECHO (v28) | 369 edificios; LOD0 de edificios 606,054 tris, LOD2 50,149; 364 huellas dentro de ±0.2 m; 217 materiales, todos de Concordia y dentro de la paleta; puertas visibles 1,407 (13 tapadas) | — |
| E12 (etapa 25) | HECHO | brasas (MAT_Embers) solo en Gran Forja y Hornos; Crisol → MAT_Crisol_Molten; Cazadores dentro; 3 casas de raza nuevas; escalera de alturas por el Faro | — |
| E13 (etapa 26) | HECHO | balcón por puerta en Moradas NE/SO; RAZ_B02_Casa_04 a 1 planta; acceso al campo de tiro; Gran Subasta interior = false; criterio nuevo del Faro | — |

**Cifras globales de la ciudad**
- Ciudad completa (v26, última medición completa): **LOD0 1,226,282 tris** (edificios 615,074; conexiones 44,056;
  terreno 452,076; muralla 107,132; tubos 7,944). **LOD2 178,021** (edificios 50,961; conexiones 25,686; terreno
  80,476; muralla 20,898, suma de instancias del kit). En la v28 los edificios bajan a 606,054 / 50,149 (369 edificios,
  por las Moradas a 2 plantas y MER_Casa_01).
- **Memoria de texturas** (Godot, VRAM Compressed, criterio de README_buildings §1c): 154.7 MB (etapa 17) → 160.7 (26)
  → 161.4 (27, atlas de cajas) → ~165.7 (28, lote Mercado) → **~173.7 MB** (28, con Oficios y Clases; 18 normal maps
  de props = 12.0 MB) → **~174.4 MB** (29, MAT_Vault_Stars 1K, +0.67). Límite 220 MB; aviso a partir de 200.

### 1.3 Interiores (E14 y siguientes)

34 edificios tienen interior (32 con `interior = true` + Santuario y Salón). Además, las Moradas usan 3 plantillas.

| Interior | Estado | Archivo | Volumen (m) | Tris | Notas |
|---|---|---|---|---|---|
| Kit BLD_INT_KIT + `build_interior` | HECHO | concordia_interiors_v01.blend | — | 28 módulos ≤ 300 tris | 3 estilos: piedra, entramado, revoco |
| Sala de prueba 8 × 6 | HECHO | (en interiors_v01) | 8 × 6 × 3.2 | 2,004 | — |
| Banco (piloto) | HECHO | int_banco.glb (1.69 MB) | 23.1 × 19.1 × 6.4 | 25,936 | Banquero 75 %, mostrador 100 %, bóveda 88.9 %; 200 cajas numeradas (1–40 abiertas); tiene los 3 defectos del kit corregidos en la 29 hasta que se reexporte |
| Morada: Habitación | HECHO | int_morada_habitacion.glb | 4 × 5 × 2.7 | 3,366 | plantilla |
| Morada: Casa pequeña | HECHO | int_morada_casa_pequena.glb | 6 × 8 × 2.7 | 7,332 (último informe; README dice 6,623) | plantilla, con patio |
| Morada: Casa grande | HECHO | int_morada_casa_grande.glb | 8 × 10 × 6.4 | 10,857 (README: 10,148) | plantilla, dos plantas |
| Tesorería de la Muralla | HECHO (etapa 29) | int_tesoreria.glb (1.39 MB) | 26.4 × 13.6 × 8.8 | 21,310 | Tesorero y Cambista 75 %, mostradores, tubos y vitrinas 100 % |
| Santuario del Retorno | HECHO (etapa 29) | int_santuario.glb (0.73 MB) | 13.8 × 9.6 × 9.0 + bóveda a 12.7 | 10,537 | bóveda bajada de 14 a 12.7 m (chocaba con la cubierta); todo 100 % |
| Casa de Reposición "El Remiendo" | PENDIENTE (siguiente) | — | 23.1 × 11.1 × 6.4 | — | ficha completa en tu prompt (anexo A, mensaje 71) |
| Crisol de las Piedras | PENDIENTE | — | 19.0 × 19.0 × 8.0 | — | a mano (regla: sin assets descargados) |
| Posada | PENDIENTE | — | 19.1 × 15.1 × 9.6 | — | — |
| Casa del Registro | PENDIENTE | — | 13.1 × 11.1 × 6.4 | — | — |
| Casa de Reparaciones | PENDIENTE | — | 15.0 × 9.0 × 3.4 | — | taller abierto, vigas, yunque, TOOL_Rack, banco largo, un farol |
| Salón de las Hazañas | PENDIENTE | — | 38.6 × 12.4 × 8.0 (vigas hasta 15) | — | a mano |
| Gran Forja | PENDIENTE (bloqueado por medición) | — | 15.1 × 15.1 × 3.2 | — | antes de construir: medir muros y alero del exterior y decirte el caso (a o b) |
| Gremios (4) | PENDIENTE | — | Mineros/Pescadores 17.1 × 13.1 × 6.4; Cazadores 11.1 × 7.1 × 6.4; Herbolarios 15.4 × 6.6 × 3.2 | — | cada uno con su volumen, sin estirar |
| Talleres (6) | PENDIENTE | — | Carpintería, Sastrería, Hornos ≈ 15 × 11 (3.2–6.4 alto); Curtiduría 15.1 × 6.1; Joyería 9.1 × 9.1; Alquimia 5.5 × 5.5 × 12.8 (torre) | — | Alquimia: plantas apiladas con escalera de caracol; Curtiduría: sala larga |
| Salones de clase (8) | PENDIENTE | — | 16.6 × 9.0 × 7.0 (todos) | — | plantilla |
| Casas de Raza (6) | PENDIENTE | — | 01–04 y 06: 19.1 × 15.1 × 9.6; 05: 9.52 × 9.52 × 3.6 | — | plantilla + variante pequeña para la 05 |

**Hechos 3 de 34 edificios con interior** (Banco, Tesorería, Santuario) **+ las 3 plantillas de Moradas**.
**Faltan 31.**

### 1.4 Props

| Lote | Estado | Cifras |
|---|---|---|
| Props del Banco (a mano) | HECHO | 16 props (BANK_*), 2–460 tris |
| 4 objetos "de IA" hechos a mano | HECHO | telar 746, fuelle 386, maniquí 350, casco 310 (no hubo generador de IA) |
| 14 triviales a mano | HECHO | Ingots_Coal 288, Cloth_Rolls 246, Bar_Counter 150, Trestle 68, Bench_Vise 120, Auction_Gavel 188, Ink_Seal 220, Baker_Peel 40, Tanning_Frame 208, Herb_Rack 436, Fish_Crates 364, Longbow 276, Spinning_Wheel 364, Jeweler_Case 286 (total 5,046 con los 4 anteriores) |
| Importados CC0 Mercado | HECHO (aprobados con criterios) | 36 props (Quaternius 25 + Avramania 11), 20,205 tris tras decimar |
| Importados CC0 Oficios | HECHO | 26 props, 17,097 tris |
| Importados CC0 Clases | HECHO | 13 props, 10,934 tris |
| Vitrina de trofeos | HECHO | pared 128 / mesa 132 / nichos 230 tris (LOD0), un material MAT_TrophyCase (atlas 512), props_trophy_cases.glb |
| Props de la Tesorería y del Santuario (a mano) | HECHO (etapa 29) | balanza grande 169, caja fuerte 504, saco 108, vitrinas A/B/C 148/122/120, esquirla 24, corona 440; mesa 56, ración 61, antorcha 36, candelero 150 |

### 1.5 Personaje: elfo masculino Sanador (PJ0–PJ5, PJ4b)

| Fase | Estado | Cifras / archivos |
|---|---|---|
| PJ1 cuerpo base | HECHO | MakeHuman vía MPFB 2.0.18 (malla CC0); elfo_v01.blend; pj_elfo_cuerpo.glb |
| PJ2 cabello y ropa inicial | HECHO | CLASE_SANADOR provisional; atlas 1K compartido (MAT_Sanador_Atlas); elfo_v02.blend; pj_sanador_ropa.glb |
| PJ3 esqueleto y pesos | HECHO | 70 huesos (perfil SkeletonProfileHumanoid de Godot, 56 + extras: Weapon_R, trenza, falda…); 10 poses de prueba; elfo_v03.blend; pj_elfo_rig.glb |
| PJ4 animaciones | HECHO | 4 propias a mano: Heal_Cast_Single 0.9 s, Heal_Channel-loop 1.5 s, Heal_Cast_Area 1.2 s, Revive 2.0 s (30 fps, sin root motion); UAL 1 y 2 Standard (Quaternius, CC0) sin retarget en Blender |
| PJ4b decisiones | HECHO | lista final de 29 animaciones (tabla en sección 2.9); Death_B espejo; GetUp/GetUp_B con 7 fotogramas de transición |
| PJ5 LODs y exportación | HECHO | LOD0 7,250 / LOD1 4,848 / LOD2 1,757 tris; 9 .glb en export/godot/personajes/; concordia_personajes_master.blend v1.0 |
| Prueba en Godot (G8) | PENDIENTE | checklist de 10 puntos en TODO_GODOT_personaje.txt (PJ5) |

### 1.6 Godot (G0–G9 + arreglo para tu PC)

| Fase | Estado | Notas |
|---|---|---|
| G0 inventario y proyecto | HECHO | `godot_concordia/` (Godot 4.7.2, Forward+) |
| G1 importación | HECHO | `tools/import_settings.py` + `post_import.gd` |
| G2 ensamble | HECHO | `tools/build_city.gd` → `scenes/concordia_glb.tscn` (ciudad fuente) |
| G3 cámara, jugador, HUD | HECHO | prueba de caminata 480/481 tramos, 8.6 km |
| Parada 1 ampliada | HECHO | navegación horneada en Godot (radio 0.35, escalón 0.25, 36°, celda 0.25), shader de terreno, haces, Obelisco |
| G4 luz, cielo, día/noche | HECHO | `day_night.gd` |
| G5 efectos y shaders | HECHO | `effects.gd`, `shaders/*.gdshader` |
| Arreglo PC (A–F) | HECHO, esperando tu prueba | `tools/build_world.gd` (mundo horneado en 214 chunks de 50 m), `world_streamer.gd`, calidad F2, benchmark nuevo; zip de 88 KB enviado; **falta que ejecutes `tools/preparar_pc.bat` y el benchmark** |
| G6 interacciones e interiores (→ parada 2) | PENDIENTE | espera el benchmark de tu PC |
| G7 NPC, navegación y carga | PENDIENTE | — |
| G8 personaje | PENDIENTE | el personaje ya existe |
| G9 informe de pruebas | PENDIENTE | — |

Cifras de Godot: mundo horneado LOD0 de toda la ciudad 1,006 nodos de malla (854 en chunks + 152 sueltos) frente a
8,114 antes; ~15,500 buffers estimados con radio de carga de 120 m frente a ~50,000; en Bajo (software) 189–839 draw
calls frente a 1,010–5,710 antes (en Alto). VRAM medida por software en Bajo: 355 MB (Forward+), 221 MB (Compatibility).

---

## 2. Decisiones tomadas y su motivo

(Cada decisión con el mensaje tuyo donde se tomó; los textos completos están en el anexo A.)

### 2.1 Generales y de método
- **Rol y reglas del proyecto** (mensaje 0): artista técnico senior; un paso cada vez; números reales y capturas;
  avisar si una cifra parece mal; referencias reales (Siena, Carcassonne, Ávila, Rothenburg, Český Krumlov, Bruselas,
  Brujas, Malá Strana, Torre de Hércules, Bardenas Reales).
- **Paleta:** un solo color mágico fuerte, el azul pálido **#8FD0FF**; nada saturado fuera de él (HSV saturación
  ≤ 0.35 salvo tonos 185–215°). Fuego y ventanas = luz natural cálida con emisión ≤ 1.0. **Única excepción cálida:
  MAT_Embers** (#E09A62, s 0.57, emisión ≤ 1.5), solo en fundición/hornos/interior de chimeneas (Gran Forja,
  Hornos; Posada y chimenea de la Forja podrían usarla), < 2 % de la superficie visible, nunca azul ni junto a
  MAT_Shard_Blue (etapa 25, mensaje 36).
- **Memoria de texturas ≤ 220 MB** en Godot (avisar a partir de 200).
- **Cámara isométrica**: todo se comprueba desde CAM_Iso con rayos (puertas, NPC, mostradores, Faro).
- **Aspecto remendado** en toda la ciudad (parches MAT_Stone_Repair, vigas de reemplazo, tejas de otro tono; ningún
  edificio idéntico: semilla por edificio, `rng_for(nombre, semilla)`).
- **Versiones del .blend:** guardar versión nueva antes de cada etapa (v01…v28). No se modifica la anterior.
- **Repositorio:** push normal, nunca forzado; `--force-with-lease` solo si tú lo pides; si el remoto tiene commits
  desconocidos, parar y preguntar. No migrar a LFS (cuota). Desde G0 (mensaje 59) los binarios **sí** van en git
  (.blend, .glb, .png, .jpg); `respaldo/` fuera salvo su MANIFEST.

### 2.2 Terreno y muralla
- Prompt 2 (mensaje 3): bordes laterales de las Moradas opción (a); terraplén y rampas ≤ 5°; escalinatas en las
  diagonales r 95–105; plazoletas.
- Prompt 4 (mensaje 8): muralla de **15 m hasta lo alto de las almenas**, ronda a 12.4 m, puertas selladas (no se
  sale de la ciudad), 48 posiciones; runas a +4.5.
- Exterior (mensaje 13): ceniza gris, **sin salidas** (sin senderos, puentes ni rampas).
- Poly Haven (mensajes 18–20): Hue/Saturation horneado en el albedo (opción A); texturas CC0 2K Normal GL.

### 2.3 Edificios (E0–E11)
- **Techo siempre aparte** (`_Roof`) para que Godot lo oculte al entrar; `_Body` unido por material; `_Props`
  instanciables; interior = `MARKER_<Nombre>_Door` (+Y fuera) + `<Nombre>_InteriorVolume`.
- **Regla de alturas** (etapa 17, sustituye "2 plantas del lado de la cámara"): hasta 3 plantas (≤ 10.5 m); manda la
  prueba de visibilidad desde CAM_Iso: si tapa una puerta o un carril de NPC, se quita una planta (mínimo 2). Hitos
  fuera de la regla. Solo cuentan las puertas que se ven desde CAM_Iso.
- **LOD2 de lejos** (decisión D, etapas 17–18): kit, Obelisco y Portal con LOD2 simplificado; Santuario, Salón y Faro
  (y Tesorería, Gran Subasta) con LOD2 = volumetría cerrada de un material plano MAT_LOD2_<NOMBRE>.
- **Marcador de la Tesorería** (mensaje 27): si el nombre del marcador difiere del prompt, se usa el del archivo
  (`MARKER_Bld_TesoreriaMuralla`).
- **Gran Subasta**: pabellón abierto, `interior = false` (etapa 26).
- **Cazadores** (etapa 25): dentro de la muralla, casa 12 × 8 + campo de tiro 14 × 8 a 84 m; acceso por camino de
  adoquín al norte (etapa 26).
- **Razas** (25–26): solo 4 huecos libres de 8 × 8 en el sector Sur; parcelas de 4 × 8; desnivel hasta 2.5 m
  aceptado **solo con muro de contención o escalón ≤ 15 cm** (mensaje 45); B05 con escalón de piedra a lo largo de la
  fachada (Casa_04/05, 0.193 m → peldaño); **B06 con 2 casas aceptado como provisional** (los barrios son plantilla
  N_RAZAS = 6, se rehacen con la lista real de razas).
- **Moradas** (26–28): galerías corridas → **un balcón por puerta** en NE/SO; escalera con el pie en el extremo
  alejado de CAM_Iso y el tramo alto hacia la cámara (al revés tapaba 39–48 puertas); **SO_036 y SO_037 a 2 plantas**
  (−6 viviendas); **13 puertas tapadas aceptadas** (0.93 % < 1 %, Godot aclara techos/aleros); no aplicar la regla
  literal de la escalera (subiría a 48). 1,398 viviendas.
- **Faro** (25–28): criterio nuevo de 11 rayos (10 al eje del haz entre 60 y 120 m + 1 al cristal; vale 1 libre);
  escalera de alturas aplicada solo donde deja de tapar; **MER_Casa_01 bajada** (decoración); el fallo restante se
  acepta porque Godot dibuja cristal y haz sin depth test y hay brújula; los hitos y la muralla no se tocan.
- **Tubos de luz Tesorería → Faro** (mensajes 27, 45, 50): ruta oeste por tejados (Tesorería → MER_Casa_01 → Posada →
  arco sobre la avenida → Registro → 2 pilares junto al canal → Faro); ningún soporte en calle, plaza ni fuente;
  pilares de piedra de 0.6 m sobre techos, tubo ≥ 1.2 m sobre tejados y ≥ 5 m sobre calles; tramos ≤ 10 m (≤ 16 m con
  arco); rechazada la opción B (pilar en la fuente).
- **Pozo del Santuario**: provisional hasta interiores (26); en la etapa 29 colocado en el interior sin
  `provisional`.

### 2.4 Fuentes de assets (mensajes 39 y 45)
- **Permitidas (CC0):** Quaternius (Fantasy Props MegaKit, UAL 1 y 2 Standard) y Avramania (Sketchfab, CC0
  comprobada en la API y en la página). Poly Haven para texturas. Kenney y KayKit descartados (red bloqueada; no
  hacían falta).
- **Prohibidas:** CC BY-NC, "uso personal", sin licencia visible, sacadas de otros juegos o películas.
- **Sin assets descargados ni IA** en: Portal, Faro, Obelisco, Santuario, Salón de las Hazañas, Banco, Tesorería,
  Crisol y casas de barrios y Moradas. El **mobiliario** de Moradas y Casas de Raza **sí** puede usar descargados.
- Todo gratis: sin addons ni servicios de pago. Solo descargar archivos de datos (glb, gltf, fbx, obj, blend, png,
  jpg, exr, zip de assets); no ejecutar scripts, instaladores ni binarios; addons de Blender solo con tu aprobación
  (MPFB 2.0.18 aprobado para el personaje).
- **Sketchfab:** el token lo escribes tú en el formulario seguro; nunca se escribe en ningún archivo.
- **No entrar con el navegador en Gemini, Meshy ni ninguna web de generación** (ni sesiones, ni captchas, ni cuentas).
  Los objetos "de IA" se hicieron a mano porque no había generador.
- Cada asset va a ASSETS_LICENSES.md (nombre, autor, URL, licencia, fecha, dónde se usa).
- Criterios de importación (mensaje 50): pequeños (lado ≤ 0.6 m) ≤ 500 tris, medianos ≤ 1,500; lo que pasa se decima
  con normal map horneado (512 / 1K, UV `UVBake`); escala en metros, origen en la base; materiales reasignados a
  materiales de Concordia (por nombre en Quaternius, por color de paleta en Avramania, listas por categoría).

### 2.5 Interiores (E14, etapas 27–29)
- Un `int_<nombre>.glb` por interior, origen en la puerta, piso en Z = 0, **tamaño = InteriorVolume (±0.2 m en
  planta)** (no la huella exterior de las fichas) (mensaje 73).
- Grupos ocultables: WALL_Near_A/B, CEILING, WALL_Near_<Recinto>, CEILING_<Recinto>, LEVEL_n (aceptado como
  convención general).
- Ventanilla de cajero de 1.2 m sin barrotes en la línea de vista (Banquero del 58 % al 75 %).
- 40 cajas abiertas por defecto en la bóveda del Banco.
- **Tesorería:** dos plantas de ~4.4 m (26.4 × 13.6 × 8.8).
- **Santuario:** muros de 9 m; bóveda hasta 14 m solo si va en CEILING y no atraviesa la cubierta; si choca, bajarla
  y avisar → **se bajó a 12.7 m** (etapa 29; pendiente tu visto bueno).
- **Gran Forja:** no subir a 6 m sin medir; caso (a) exterior alto → corregir el InteriorVolume y avisar; caso (b)
  alero cerca de 3.2 m → mantener 3.2 con vigas bajas, campana de chimenea alta hasta el hueco de 14 m y lucernario;
  patio de fundición fuera. **Antes de construirla, decirte qué caso es con las dos alturas medidas.**
- **Casa de Reparaciones:** interior único después del Registro, taller abierto 15 × 9 × 3.4.
- **Plantillas:** una por tipo ajustada a cada volumen + variante pequeña para la Casa de Raza 05; gremios y talleres
  cada uno con su volumen (sin estirar); Alquimia en plantas apiladas con escalera de caracol; Curtiduría sala larga.
- **Orden:** Tesorería, Santuario, Casa de Reposición, Crisol, Posada, Registro, Casa de Reparaciones, Salón de las
  Hazañas, Gran Forja, gremios y talleres, salones de clase (8), Casas de Raza (6). Tesorería y Santuario seguidos con
  informe (hecho); después de tres en tres salvo problema bloqueante.

### 2.6 Props (etapa 28)
- Las hojas de props del Mercado (props_mercado_q y props_mercado_av) aprobadas si cumplen los criterios; después
  Oficios y Clases con los mismos criterios (hecho).
- Vitrina de trofeos en 3 variantes (pared 9 slots, mesa 6, nichos 9), un solo material.
- Pendientes visuales anotados (no corregidos): ventanas de las casas con reja de hierro en vez de postigos (falta
  INT_Window_Shutter); llama del hogar = cono blanco a 1.7 m (falta material de llama o partículas en Godot); vidrio
  de las vitrinas casi invisible con alfa 0.3.

### 2.7 Godot (mensajes 59, 61, 72)
- Proyecto en `godot_concordia/`, escenas creadas por script (no a mano), APIs verificadas en la documentación oficial
  4.7 (extractos en `docs/reference/godot47/`), 0 errores y 0 avisos nuevos tras cada fase.
- **Permiso ampliado** (mensaje 61): en Godot puedes arreglar sin consultar ajustes de importación, materiales,
  shaders, rangos de visibilidad y mallas de navegación; lo que cambie la forma de un modelo va a FIXES_BLENDER.md.
- Navegación horneada en Godot (no la de Blender): radio 0.35, escalón 0.25, pendiente 36°, celda 0.25; regiones por
  distrito e interior guardadas como .res; NavigationLink3D en escaleras.
- Haces: aditivos, alfa ~0.3, sin profundidad ni sombras, degradado hacia arriba; el del Crisol limitado a 12 m.
- Obelisco gris muy oscuro azulado, legible.
- **Arreglo de tu PC** (mensaje 72): sin tocar los .blend; mundo horneado por chunks y materiales, MultiMesh para lo
  repetido, carga por distancia con hilos, menú F2 (Bajo/Medio/Alto/Auto, integrada → Bajo), benchmark nuevo, zip
  pequeño solo con lo cambiado; ningún `.import` cambiado.
- Recomendación sobre Compatibility: probar primero Forward+ en Bajo; si no llega a 30 FPS o vuelve el error −10,
  repetir el benchmark con `--rendering-method gl_compatibility` y comparar.

### 2.8 Personaje (mensajes 46–48, 52, 58, 63–65)
- Elfo masculino, clase Sanador (provisional), calidad normal (sin brillo ni legendarios).
- Base MakeHuman con MPFB 2.0.18 (aprobado; GPL como herramienta, assets CC0).
- Verificación sin "look": capturas renderizadas en Blender.
- Esqueleto con los nombres de SkeletonProfileHumanoid de Godot (comprobado en la documentación oficial).
- Animaciones: UAL Standard (gratuita) 1 y 2 de Quaternius; **no retarget en Blender** (se hace en Godot con BoneMap);
  Mixamo de reserva (lo descargarías tú; yo no inicio sesión).
- PJ5: LOD0 ≤ 10,000, LOD1 ≤ 5,000, LOD2 ≤ 1,800 (malla única, esqueleto simplificado); conservar orejas y dobladillo;
  3 materiales, texturas 1K, emisión solo en el colgante.

### 2.9 Animaciones (PJ4b, mensaje 65)
- **Andar hacia atrás:** Walk_Loop con AnimationNodeTimeScale a −0.6 (la Standard gratuita no trae 8 direcciones; no
  se compra la Source de pago).
- **De lado:** el personaje gira hacia donde se mueve; BlendSpace2D (Idle, Walk, Jog, Sprint, atrás).
- **Girar en el sitio:** por código durante Idle (~0.3 s por media vuelta).
- **Dos muertes:** Death_A = Death01 (UAL 1); Death_B = espejo con otro giro de cabeza y brazos.
- **Levantarse:** GetUp = LayToIdle (UAL 2) + 7 fotogramas de transición desde Death_A; GetUp_B desde Death_B.
- **Extras UAL 2:** Consume, Chest_Open, Idle_FoldArms-loop, Yes, Idle_No-loop.
- **Lista final (29):** Idle_Loop 2.50, Idle_FoldArms-loop 2.50, Walk_Loop 1.33 (y atrás −0.6), Walk_Formal_Loop
  1.33, Jog_Fwd_Loop 0.93, Sprint_Loop 0.67, Sitting_Enter 1.30 / Sitting_Exit 1.03, Sitting_Idle_Loop 1.67 /
  Sitting_Talking_Loop 2.93, Hit_Chest 0.33 / Hit_Head 0.43, Hit_Knockback 0.83, Death_A 2.40, Death_B 2.40, GetUp /
  GetUp_B 1.77, Spell_Simple_Enter 0.53 / Shoot 0.50 / Exit 0.43, Spell_Simple_Idle_Loop 2.07, Consume 1.33,
  Chest_Open 1.37, Yes 2.50, Idle_No-loop 2.50, Heal_Cast_Single 0.90, Heal_Channel-loop 1.50, Heal_Cast_Area 1.20,
  Revive 2.00.
- Sufijo `-loop` / `_Loop` / `cycle` → bucle automático al importar en Godot.

---

## 3. Convenciones

### 3.1 Unidades, ejes y cámara
- Metros, escala 1.0. Blender Z arriba; Godot Y arriba (export glTF +Y Up): Blender (x, y, z) → Godot (x, z, −y).
- **DATUM**: base de la muralla a Z = +6.0; plaza a +8.0; Atrio +8.6; pedestal del Portal +8.9.
- Sectores (ángulo desde +X): Oficios E 0° ±25; Mercado N 90° ±25; Clases O 180° ±25; Razas S 270° ±25; Moradas en
  las diagonales 45/135/225/315 (±20 = 40°).
- **CAM_Iso** (Blender): ortográfica, escala 120, rotación (54.736°, 0°, 45°): mira de SE a NO; en pantalla el Norte
  queda arriba a la derecha. Dirección hacia la cámara en mundo: `CAM_BACK = (0.577, −0.577, 0.577)`. En Godot:
  cámara (−35.264°, 45°, 0), distancia 120, zoom 15–120 (Bajo 60, Medio 90, Alto 120), giros de 90° con Q/E.
- Lado de la cámara: las caras que miran al SE (+X y −Y del mundo).

### 3.2 Nombres de objetos (edificios)
- `<NOMBRE>` Empty raíz en el marcador (+Y = door_direction); `<NOMBRE>_Body`; `<NOMBRE>_Roof`; `<NOMBRE>_Props`;
  `<NOMBRE>_Body_LOD1` / `_LOD2` (50 % / 15 %); `MARKER_<Nombre>_Door` (+Y hacia fuera); `<Nombre>_InteriorVolume`
  (caja sin render); `<NOMBRE>-colonly`.
- Si el nombre de un marcador del archivo no coincide con el del prompt, manda el del archivo.
- Terreno: `TRN_City` (malla maestra de 1 m, no se exporta), `TRN_CityChunk_xI_yJ_LODk`, `TRN_ExteriorChunk_*`,
  `TRN_NavMesh_<Distrito>`; muralla `WALL_*`, `GATE_*`, `TOWER_*`, `BASTION_*`; conexiones `BRIDGE_*`, `ARCH_Street_*`,
  `STAIRS_*`, `RAIL_Stone_*`; Moradas `Morada_<NE|NO|SE|SO>_NNN`, `DOOR_Morada`, `PLATE_Morada_*`, `LANTERN_Shard_*`.
- Interiores: raíz `INT_<nombre>` > `INT_<nombre>_Frame` > grupos; mallas unidas `INT_<nombre>_<grupo>`; props
  `PROP_<malla>`; luces `LIGHT_*` (Empties); marcadores `MARKER_*`.

### 3.3 Sufijos de importación (Godot)
- `-colonly` → StaticBody3D solo colisión; `-navmesh` → NavigationRegion3D; `-occonly` → OccluderInstance3D
  (se pidió "-occ"; el importador de Godot usa `-occonly`).
- `_LOD0/_LOD1/_LOD2` (propios; el LOD automático del importador está desactivado). `lod_level` en metadata.
- `-loop` / `_Loop` → animación en bucle.

### 3.4 Marcadores (README_markers.txt, anexo C)
- **+Y local = hacia fuera / al frente**, +Z arriba, +X a la derecha mirando al frente desde detrás. En Godot el nodo
  "mira" con −basis.z adonde apuntaba +Y en Blender. Origen = punto de apoyo.
- Propiedades → extras de glTF → metadata en Godot (`interior`, `type`, `footprint`, `door_direction`, `floor`,
  `occludes_iso`, `nav_exclude`, `npc`, `tipo`, …).
- Interiores: `MARKER_Interior_Exit` (en la puerta), `MARKER_Interior_Spawn`, `MARKER_NPC_Slot_xx` (`npc`),
  `MARKER_Interact_xx` (`tipo`), `MARKER_WorkStation_xx`, `MARKER_Respawn` (Santuario), `MARKER_TrophyCase_*`,
  `MARKER_Trophy_Slot_xx`, `MARKER_Decor_Slot_xx`, `MARKER_Garden`.
- Convención de props: "+Y = frente": quien mira el prop de frente tiene la +X local a su izquierda; el texto en una
  cara +Y lleva la u invertida (lección 12).

### 3.5 Grupos ocultables de los interiores (propiedad `hide_when`)
- `WALL_Near_A` / `WALL_Near_B`: muros del recinto principal cuya normal hacia fuera mira a CAM_Iso: siempre ocultos
  dentro.
- `CEILING`: techo (y en el Santuario todo lo que pasa de 9 m): siempre oculto dentro.
- `WALL_Near_<Recinto>` / `CEILING_<Recinto>`: se ocultan cuando el jugador entra en ese recinto (Area3D en el suelo).
- `LEVEL_n`: planta n con su suelo, muros y `Furniture_Ln`: oculto cuando el jugador está por debajo.
- `Shell`, `Furniture`, `Lights`, `Markers`: nunca se ocultan.

### 3.6 Paleta y materiales
- Regla de aprobación de un material nuevo (README_buildings §1): paleta (s ≤ 0.35 salvo 185–215°; #8FD0FF único
  mágico), exportable (Image Texture → Principled; variantes de tono con Mix Multiply = baseColorFactor) y memoria
  ≤ 220 MB.
- Emisivos: MAT_Shard_Blue 2.5, MAT_Shard_Blue_E40 4.0, MAT_Portal_Veil 3.0, MAT_Obelisk_Mark_Lit 3.0,
  MAT_Faro_Beam 1.5 (alfa 0.3), MAT_Pipe_Light_Core 1.5, MAT_Rune_Glow_12 1.2 / _10 1.0, MAT_Crisol_Molten 1.2,
  MAT_Stained_Glass_Blue 0.6 (#8FD0FF desde la etapa 24), MAT_Glass_R04 0.25, MAT_Window_Warm 1.0 (#AD9072, natural),
  MAT_Embers 1.5 (única cálida), MAT_Shard_Madura 1.0 (etapa 29).
- Interiores: emisión ≤ 1.0 salvo lo pedido explícitamente (tubos 1.5, vitral 0.6); **un solo azul #8FD0FF por sala**
  (una luz azul por interior).
- Tabla completa de los 70+ materiales con color medio: README_buildings §14 (anexo B).
- Materiales nuevos de la etapa 29: MAT_Shard_Opaca #7C8288, MAT_Shard_Brillante #B6CFDF, MAT_Shard_Latente #5B8DB8,
  MAT_Shard_Madura #8FD0FF (emisión 1.0), MAT_Vault_Stars (textura 1K: #2E4057 con estrellas #C9B98A, sin emisión).
- Máscaras de terreno en COLOR_0 (README_masks.txt, anexo D).

### 3.7 Presupuestos
- Edificios: pieza pequeña ≤ 1,500 tris, media ≤ 5,000, grande ≤ 12,000; hitos con presupuesto propio; LOD1 50 %,
  LOD2 15 %. Kit: muros ≤ 250, cubiertas ≤ 400 por módulo de 3 m. Kit de interiores ≤ 300 por módulo.
- Chunk de ciudad ≤ 35,000; chunk exterior ≤ 8,000. Moradas: habitación ≤ 1,500, casa pequeña ≤ 2,000, grande
  ≤ 3,500.
- Interiores: ≤ 40,000 tris (shell + props); texturas 1K; Habitación 8,000, Casa pequeña 15,000, Casa grande 28,000.
- Personaje: LOD0 ≤ 10,000, LOD1 ≤ 5,000, LOD2 ≤ 1,800.
- Huella: ±0.2 m a nivel de calle; interiores ±0.2 m en planta respecto al InteriorVolume.
- Navegación de interiores: celda 0.25 m, pasos ≥ 1.2 m, escaleras ≤ 35°, nada coplanar.

---

## 4. Lecciones y reglas anotadas

### 4.1 Las 12 lecciones del Banco (README_buildings §18, literales)
1. Leer el giro del edificio de rotation_euler (al anexar objetos, matrix_world llega sin evaluar): con el giro mal
   salen los muros cercanos equivocados. Comprobar 'cam_local' en el informe.
2. Cada recinto interior (bóveda, despacho cerrado...) necesita sus propios muros cercanos ocultables
   (WALL_Near_<recinto>, propiedad hide_when) y su techo (CEILING_<recinto>); lo que cuelga de esos muros va en el
   mismo grupo (si no, se ve de espaldas).
3. Entreplantas en los muros del fondo; bajo un forjado de 5 m solo se ve 1.4 m desde el borde: la planta alta va en
   LEVEL_1 (ocultable) y nada importante debajo.
4. Un volumen alto (la bóveda) tapa lo que queda detrás de él respecto a la cámara (+x/+y en el marco del Banco):
   ponerlo en la esquina del fondo o dejar detrás solo lo secundario.
5. Los props miran a la cámara (contra muros del fondo o de doble cara); contra muros cercanos se ven de espaldas.
6. Columnas y arcos solo detrás de los objetivos o a más de altura/0.7 m de ellos; comprobar con rayos antes de unir
   los módulos (los nombres dicen qué tapa).
7. Las rejas tapan ~40 % de lo que hay detrás. Ventanilla de 1.2 m sin barrotes en la LÍNEA DE VISTA de CAM_Iso: lo
   que está a d metros detrás de la reja se ve desplazado d en diagonal, así que el NPC va pegado al tablero
   (d = 0.7 m) y la ventanilla se corre d/2 hacia la cámara; el NPC queda dentro de su luz.
8. Navmesh: con celdas de 0.5 m una puerta de 1.2 m no pasa (margen 0.3); usar 0.25 m. La escalera necesita tiras
   planas en ambos extremos para unir las rejillas; los pasos de 1.2 m se comprueban con holgura en rejilla de 0.1 m.
9. Nada coplanario: el entarimado alto empieza en el borde de la arcada; separaciones ≥ 1 cm.
10. Losas remendadas con MAT_Stone_Repair parecen agujeros desde arriba: usar caliza gastada.
11. La luz se hornea en Godot (LightmapGI); los Empties llevan color, energía y radio; un solo azul por sala.
12. Convención de props "+Y = frente": quien mira el prop de frente tiene la +X local a su IZQUIERDA. Texto en una
    cara +Y (números de las cajas, rótulos) lleva la u invertida, y las series se numeran recorriendo −X local para
    leerse de izquierda a derecha. Comprobarlo siempre con una captura de cerca.

### 4.2 Lecciones 13–20 (etapa 28, Moradas)
13. Plantillas privadas: giro fijo respecto a CAM_Iso (−90) para que la puerta y +X sean los muros cercanos; todo el
    mobiliario contra −X / −Y. La orientación de la casa en la ciudad no importa.
14. Escalera de 5 m en una casa de 10: la entreplanta debe retirarse (y = −1) para dejar ≥ 1.2 m al pie; y ningún
    mueble bajo la llegada.
15. Blender exige nombres únicos en todo el archivo: exportar cada plantilla con nombres limpios y renombrarla después;
    numerar seguidos los slots de varias vitrinas en la misma escena.
16. Un tabique entre zonas (patio / casa) tapa desde CAM_Iso: va en su propio grupo WALL_Near_<Recinto>.
17. Bajo una entreplanta, escalar en Z las piezas altas del kit (campana del hogar) y dejar ≥ 4 cm a las vigas.
18. Assets con textura de paleta: el color más cercano necesita listas por categoría (si no, madera → teja).
19. Patas de varilla asoman bajo z = 0: recortarlas al suelo; piezas coplanarias (postes y largueros) dan manchas
    negras: separarlas 1 cm.
20. Remedios que cuestan viviendas (2 plantas = −3 puertas): aplicarlos solo si liberan puertas y deshacerlos si no.

### 4.3 Lecciones 21–30 (etapa 29, Tesorería y Santuario)
21. Ventanas del interior = las del exterior: `custom_module()` en el espacio del módulo (z real / escala de la
    planta). El módulo del kit escalado a 4.4 m ponía la ventana 0.25–0.8 m más alta que la de la fachada.
22. Ventanilla de cajero: con el NPC a 0.7 m, la ventanilla se corre 0.40 m hacia la cámara (no 0.35: los rayos del
    lado de la cámara rozan la jamba de 6 cm).
23. Regiones de navegación de una misma planta: deben solaparse (≥ 2 × margen); si solo se tocan quedan separadas.
24. Las losas remendadas de INT_Floor_Stone_B podían solaparse a la misma altura (coplanarias): corregido en el kit;
    el Banco lo tiene hasta que se rehaga.
25. Bóveda bajo cubierta de 45°: perfil de poca flecha que siga la pendiente; holgura medida contra la malla real con
    rejilla de 0.1 m (cabios); nervios de sección girada bajados 1.45 r.
26. Tubos que atraviesan el techo: repartir las vigas para que ninguna cruce un tubo (≥ 0.5 m).
27. Varios interiores en un .blend: renombrar tras exportar o el segundo sale con ".001" en marcadores y grupos.
28. Muros con huecos más altos que una planta: sin shell por plantas; muros a mano con slab_holes.
29. Huecos que llegan al suelo (arcos, puertas): la cara del umbral queda coplanaria con el suelo; `realize()` la
    quita (Tesorería 127 caras, Santuario 9).
30. Exportación: con export_keep_originals cada imagen iba dos veces (uri y copia); `glb_tools.strip_embedded_images`
    deja solo la uri. Los .glb anteriores (ciudad, Banco, Moradas) tienen el aviso hasta que se reexporten (FIXES F1).

### 4.4 Otras reglas y lecciones anotadas fuera de README_buildings
- **Godot / tu PC** (TEST_REPORT.md, anexo H): no repartir `.godot/imported` sin sus `.md5` (forzó una reimportación
  con la GPU que guardó mallas vacías); reimportar siempre en modo `--headless`; sin GPU, Godot **no guarda** las
  transformaciones de una MultiMesh (van en metadata `mm_xforms`); `custom_aabb` obligatorio en MultiMesh; el
  rasterizador vacío devuelve AABB 0 en las comprobaciones.
- **Navegación en Godot:** la sincronización del mapa es asíncrona (esperar con `nav_ready.gd`); `merge_rasterizer_cell_scale = 0.01`; obstrucciones proyectadas para fuentes y plazuelas.
- **Personaje:** los drivers de las máscaras HIDE_* se silencian al buscar los LOD; `Idle_No` de la UAL 2 se llama
  `Idle_No_Loop`; comparar giros de cadera con vectores de dirección del mundo, no con ángulos.
- **Sesión:** el contenedor era temporal: lo que no está en git solo existe en `respaldo/` (y en lo que descargues).

---

## 5. Prompts maestros y de etapa

Están **todos, literales y en orden**, en el **anexo A** al final de este documento (76 mensajes tuyos, sin las
notificaciones automáticas; incluye los "Inténtalo de nuevo" y los cambios de modelo para no alterar la numeración). Los más reutilizables:
- Mensaje 0: prompt maestro "ROL" (reglas del proyecto).
- Mensaje 22: prompt maestro de EDIFICIOS (kit, reglas para todos los edificios).
- Mensaje 39: fuentes de assets.
- Mensaje 40: prompt maestro de INTERIORES (kit y piloto del Banco).
- Mensaje 46: prompt maestro del PERSONAJE.
- Mensaje 59: prompt maestro de GODOT (G0–G9).
- Mensaje 71: prompt de INTERIORES (reglas comunes + fichas de Tesorería, Santuario y Casa de Reposición).
- Mensaje 73: decisiones del inventario de interiores (orden y reglas vigentes).

---

## 6. Decisiones pendientes que esperan tu respuesta

**De la etapa 29 (Tesorería y Santuario)**
1. **Bóveda del Santuario a 12.7 m** (la de 14 m se salía hasta 1.84 m por los faldones; holgura medida 0.127 m;
   óculo interior de 2.1 m en vez de 3 m). ¿Te vale?
2. **Marcadores propuestos sin pedir:** `MARKER_NPC_Slot_02` (npc = Cambista, mostrador 2 de la Tesorería) y
   `MARKER_Interact_Santuario_Kit` (tipo = santuario_kit, mesa de 3 raciones y 3 antorchas). ¿Se quedan?
3. **SANTUARIO_Well en el master** (concordia_v28.blend): conserva `provisional = true` y está escondido dentro del
   edificio cerrado. Propuesta: quitar esa copia del exterior en la próxima versión del master (no se guardó una v29
   del master de 78 MB solo por una propiedad).
4. **Rehacer `int_banco.glb`** con los arreglos del kit (losas coplanarias, umbrales coplanarios, imágenes duplicadas).
   ¿Lo rehago? (no cambia el diseño).

**De Godot (arreglo de tu PC)**
5. Ejecutar en tu PC `tools\preparar_pc.bat "<ruta a Godot_v4.7.2-stable_win64_console.exe>"`, abrir el proyecto
   (F5, F2 = calidad) y pasarme `benchmark_resultados.txt` (y, si no llega a 30 FPS en Bajo, el de
   `--rendering-method gl_compatibility`). Con eso: elegir renderizador y seguir con G6 (puertas e interiores, parada 2)
   y G7 (NPC y rendimiento). G8 (personaje) puede ir después.

**De interiores (siguiente bloque, no empezado)**
6. **Gran Forja:** cuando llegue su turno, te diré el caso (a o b) con las dos alturas medidas antes de construir.
7. Siguiente tanda (de tres en tres): Casa de Reposición, Crisol, Posada.

**Abiertos desde antes (anotados; no bloquean)**
8. Muralla: runas a +4.5 poco legibles desde el mirador (opciones de la etapa 04, sin decidir).
9. Exterior: relieve casi plano desde los miradores (etapa 08).
10. Cauce: el agua no llega a la reja exterior; 5 puentes; 4 arcos entre barrios (aceptados en su momento).
11. FIXES_BLENDER.md: F3 (TEST_Casa_12x9 sin colisión), F4 (caras con normal opuesta), F6 (escalinatas metidas en
    rampa), F7 (parcelas vacías de la plaza con UV deformado), F10 (escalones > 0.25 m en 5 sitios): pendientes en
    Blender (cambian la forma).
12. Pendientes visuales de las Moradas: ventana con postigos (INT_Window_Shutter), llama del hogar, vidrio de vitrinas.

---

## 7. Inventario de archivos

La tabla completa con ruta, tamaño en bytes y uso de **cada** archivo está en el **anexo L** (generado por script
sobre la carpeta del proyecto el 2026-11-12). Resumen por carpetas (total en git: 975 archivos, 2.84 GB):

| Carpeta | Archivos | Tamaño | Qué es |
|---|---|---|---|
| `blender/` | 36 .blend en git (+ autoguardados .blend1 fuera) | 1.68 GB | versiones de la ciudad v01–v28 (no hay v11 ni v27 sueltas: la 11 es `concordia_master_v11.blend`; la 27 no tocó la ciudad), interiores, props, personaje |
| `export/godot/` | 46 .glb (+ personajes/) | 169 MB | lo que se importa en Godot (versión actual) |
| `export/godot_v28/` | 18 .glb | 104 MB | la exportación de la v28 que usa `sync_assets.py` (gana sobre `export/godot/` para los mismos nombres) |
| `textures/` | 257 archivos | 348 MB | texturas de Concordia (Poly Haven, generadas, estandartes, atlas), props, personaje |
| `docs/captures/` | 224 .png | 516 MB | capturas de todas las etapas (`stageNN_*`, `pjN_*`) |
| `docs/reports/` | 57 informes | 2.2 MB | JSON/CSV/MD de cada etapa (`stageNN_*.json`, `pjN_*.json`) |
| `docs/reference/godot47/` | extractos | <1 MB | documentación oficial de Godot 4.7 consultada |
| `tools/blender/` | 139 .py | — | todos los scripts (sección 8) |
| `tools/` | 2 .py | — | `fetch_sketchfab_cc0.py`, `inventario_glb.py` |
| `animations/ual/` | 9 | 22 MB | UAL 1 y 2 Standard (Quaternius CC0) y las selecciones del Sanador |
| `licenses/` | 3 | — | licencias de Quaternius |
| `godot_concordia/` | 132 en git | (716 MB en disco con assets/cache) | proyecto de Godot (scripts, escenas, shaders, herramientas, documentos); `assets/` y `world/` se regeneran |
| `respaldo/` | solo `MANIFEST.txt` en git | 944 MB en el contenedor | copias fechadas: v26, v28, glb, interiores, props, personaje, UAL original, binarios sacados de git; **no está en GitHub** |
| raíz | README_buildings.txt, README_markers.txt, README_masks.txt, README_personaje.txt, README_personajes.txt, TODO_GODOT.txt, TODO_GODOT_personaje.txt, ASSETS_LICENSES.md, .gitignore, .gitattributes | — | documentación (anexos B–K) |

Archivos clave:
- **Ciudad (última):** `blender/concordia_v28.blend` (77.9 MB, 2026-11-11). Copia: `respaldo/2026-11-11/concordia_master_2026-11-11_v28.blend`.
- **Interiores:** `blender/concordia_interiors_v01.blend` (kit + sala de prueba + Banco), `concordia_moradas_int_v01.blend` (vitrinas + 3 plantillas), `concordia_interiors_unicos_v01.blend` (Tesorería + Santuario).
- **Props:** `blender/concordia_props_v01.blend` (a mano + importados).
- **Personaje:** `blender/concordia_personajes_master.blend` (v1.0); historia `elfo_v01..v04.blend`.
- **Atlas de las cajas del Banco:** `textures/concordia/MAT_Bank_BoxNumbers/bank_box_numbers_1k.png`.
- **MANIFEST:** `respaldo/MANIFEST.txt` (sha256 de todo el respaldo), `godot_concordia/assets/MANIFEST.txt` y
  `godot_concordia/assets/manifest.json` (lo copiado al proyecto de Godot).
- **Informes por etapa:** `docs/reports/stageNN_*.json`; balance y lista de puertas en README_buildings §19.

---

## 8. Cómo se reconstruye cada cosa desde cero

**Requisitos:** Blender 4.5 LTS (o el módulo `bpy` 4.5 en Python 3.11), Pillow y numpy en ese Python; texturas en
`textures/` (están en git); para la etapa 10, red a Poly Haven (o usar las texturas ya descargadas que están en git).
Godot 4.7.2 para el proyecto. Todos los scripts calculan las rutas desde su propia ubicación (`REPO = ../..`).

### 8.1 Ciudad (cada etapa parte de la versión anterior y guarda la siguiente)
```
python tools/blender/stage01_scene_base.py              # -> blender/concordia_v01.blend
python tools/blender/build_stage02.py                   # v01 -> v02 (terreno, estructuras, sombreado, chunks)
python tools/blender/build_stage03.py                   # v02 -> v03 (plaza)
python tools/blender/build_stage04.py                   # v03 -> v04 (muralla)
python tools/blender/build_stage05.py                   # v04 -> v05 (calles y parcelas)
python tools/blender/build_stage06.py                   # v05 -> v06 (Moradas: terreno)
python tools/blender/build_stage07.py                   # v06 -> v07 (Cauce)
python tools/blender/build_stage08.py                   # v07 -> v08 (exterior)
python tools/blender/build_stage09.py                   # v08 -> v09 (materiales)
python tools/blender/stage10_polyhaven.py               # descarga Poly Haven (si hace falta)
python tools/blender/build_stage10.py                   # v09 -> v10 (texturas reales)
python tools/blender/build_stage11.py                   # v10 -> concordia_master_v11.blend + export/godot
python tools/blender/build_stage12.py                   # master_v11 -> v12 (kit de edificios y assembler)
python tools/blender/build_stage13.py ... build_stage23.py   # v12 -> v23 (Portal, Obelisco, Faro, hitos, 17, Mercado, Oficios, Clases, Razas, conexiones, Moradas)
python tools/blender/build_stage24.py                   # v23 -> v24 + export/godot/bld_*.glb (verificación E11)
python tools/blender/build_stage25.py                   # v24 -> v25; luego build_stage24.py con CONCORDIA_SRC=CONCORDIA_OUT=v25
python tools/blender/build_stage26.py                   # v25 -> v26; luego build_stage24.py sobre v26
python tools/blender/build_stage28_city.py              # v26 -> v28 (+ export a export/godot_v28)
```
Notas: algunas etapas se regeneraron hacia atrás para reservar corredores (la 07 regeneró la 05 y la 06; la 04
regeneró v01–v03 con el escalón de las diagonales). Los `build_stageNN.py` llevan su propio uso en la cabecera
(`--in`, `--out`, `-- N` para N_CLASES / N_RAZAS en 20 y 21). Las capturas: `capture_stageNN.py` (no modifican el
.blend). Las mediciones: `measure_stage25_faro.py`, `measure_stage26_faro.py`, `measure_stage28_moradas.py`,
`audit_materials.py`.

### 8.2 Funciones reutilizables
- `concordia_buildings.build_building(nombre, footprint, pisos, tipo_techo, estilo, seed, module_w=None,
  plan_edit=None, opts=None)`: apila módulos de `bld_kit.py`, crea `_Body` (unido por material) y `_Roof`, aplica
  reparaciones por semilla, respeta el marcador; `fit_iso_height(...)` aplica la regla de alturas; `rng_for(nombre,
  semilla)`; `box_uv(obj)` UV métrica de caja.
- `lod_utils.flat_lod2()`: LOD2 de color plano.
- `interior_kit.build_interior(nombre, volumen, estilo="piedra", seed=0, world_rot_deg=0.0, door=None, col=None,
  openings=(), storeys=None, ceiling=True)` → objeto `Interior` con `.root`, `.groups`, `inst()`, `unique()`,
  `light()`, `marker()`, `entry_markers()`, `ceiling()`, `collider()`, `navmesh(cell=0.25)`, `realize(grupo)`.
  Estilos: piedra, entramado, revoco. `interior_kit.build_kit(col)` crea BLD_INT_KIT; `custom_module(nombre, col,
  'window'|'door'|'door_iron', **medidas)` crea huecos a la medida del exterior (etapa 29).
- `concordia_buildings.build_interior(nombre, volumen, estilo, seed, ...)` llama a `interior_kit.build_interior`.
- Comprobaciones de interiores (`build_stage27.py`): `ray_check`, `nav_reach`, `clearance_check`, `tri_count`;
  `build_stage28_int.ray_vis(it, targets, hide)`; `build_stage29_int.finish(...)` (rayos, unión, colisión,
  navegación, pasillos, triángulos, exportación, renombrado).
- Exportación: `stage11_godot.export_glb(objs, path)` (+ `glb_tools.strip_embedded_images`), `glb_info(path)`.
- Personaje: `concordia_rig.py` (esqueleto común de 70 huesos), `pj_mpfb.py`, `pj1_piel.py`, `pj2_geo.py`,
  `pj2_atlas.py`.

### 8.3 Interiores
```
python tools/blender/build_stage27.py                   # kit + sala 8x6 + Banco -> concordia_interiors_v01.blend, int_banco.glb
python tools/blender/build_stage28_props.py             # props a mano -> concordia_props_v01.blend, props_int_mano.glb
python tools/blender/build_stage28_import.py            # props CC0 (lotes Mercado/Oficios/Clases; requiere las descargas en respaldo o red)
python tools/blender/build_stage28_int.py               # vitrinas + plantillas de Moradas -> concordia_moradas_int_v01.blend
python tools/blender/build_stage29_int.py -- tesoreria santuario   # -> concordia_interiors_unicos_v01.blend, int_tesoreria.glb, int_santuario.glb
python tools/blender/capture_stage27.py / capture_stage28_int.py / capture_stage29_int.py [-- vista ...]
```
Para un interior nuevo: crear `tools/blender/stage29_<nombre>.py` (o `stage30_…`) con `build(col, world_rot_deg)`
siguiendo `stage29_tesoreria.py`, añadirlo a `BUILDINGS` y a la función correspondiente en `build_stage29_int.py`
(volumen, giro y puerta se leen del master), definir objetivos de rayos y puntos clave de navegación.
`build_stage29_int.py` crea el .blend nuevo en cada ejecución: hay que pasar todos los interiores del archivo.

### 8.4 Personaje
```
python tools/blender/build_pj1_elfo.py        # MPFB 2.0.18 -> elfo_v01.blend, pj_elfo_cuerpo.glb
python tools/blender/build_pj2_sanador.py     # -> elfo_v02.blend, pj_sanador_ropa.glb, pj_elfo_sanador_equipado.glb
python tools/blender/build_pj3_rig.py         # -> elfo_v03.blend, pj_elfo_rig.glb
python tools/blender/pj4_compare_rest.py      # comparación de reposo con la UAL
python tools/blender/build_pj4_anim.py        # -> elfo_v04.blend, pj_elfo_sanador_anim.glb
python tools/blender/build_pj4b_ual_seleccion.py   # -> animations/ual/sanador_ual1/2_seleccion.glb
python tools/blender/build_pj5_lods_export.py # -> concordia_personajes_master.blend, export/godot/personajes/*.glb
```

### 8.5 Godot (desde `godot_concordia/`)
```
python3 tools/sync_assets.py                       # copia .glb y texturas a assets/ (+ MANIFEST)
python3 tools/import_settings.py                   # ajustes de importación de cada .glb y textura
godot --headless --path . --import                 # importar SIN GPU (nunca con el editor en una GPU integrada)
godot --headless --path . -s res://tools/build_city.gd     # -> scenes/concordia_glb.tscn (ciudad fuente)
godot --headless --path . -s res://tools/bake_navmesh.gd   # -> navigation/*.res + links.json
godot --headless --path . -s res://tools/build_world.gd    # -> world/ (chunks), scenes/concordia.tscn, scenes/main.tscn
godot --headless --path . -s res://tools/verify_assets.gd  # comprobación de .glb e importaciones
godot --path . -s res://tools/benchmark.gd [-- rapido niveles=Bajo]
```
En Windows todo lo anterior (borrar `.godot`, importar, verificar, hornear) lo hace `tools\preparar_pc.bat`.

---

## 9. Tareas a medias y punto exacto

1. **Interiores:** hechos Banco, 3 plantillas de Moradas, Tesorería y Santuario (etapa 29, commit `9fddcf7`). Parado
   esperando tu respuesta al informe de Tesorería + Santuario (decisiones 1–4 de la sección 6). Siguiente: Casa de
   Reposición (ficha en el anexo A, mensaje 71; volumen 23.1 × 11.1 × 6.4; props Quaternius aprobados permitidos aquí
   porque no está en la lista de "solo a mano"), luego Crisol y Posada.
2. **Godot en tu PC:** zip de arreglo entregado (88 KB, 39 archivos). Parado esperando que ejecutes `preparar_pc.bat`
   y el benchmark. Nada a medias en el código: 0 errores y 0 avisos aquí.
3. **Integración de interiores en Godot (G6):** no empezada. Los 6 .glb de interiores ya importan sin errores en el
   proyecto (int_tesoreria/int_santuario con 0 avisos; los anteriores con el aviso F1 hasta reexportarlos). Falta:
   disparador de puerta → escena interior, ocultar grupos por `hide_when`, LightmapGI, `convert_surfaces` (agua del
   pozo), registro de tubos que laten (TODO_GODOT, sección "Interiores únicos").
4. **G7–G9:** no empezados.
5. **Banco:** reexportación opcional con los arreglos del kit (decisión 4).
6. **Master de la ciudad:** v28 es la última; la próxima versión debería quitar la copia exterior de SANTUARIO_Well y
   reexportar `bld_portal.glb` sin imágenes duplicadas (F1).
7. **Nada quedó a medio escribir:** todos los commits están subidos; el árbol de trabajo está limpio.


---

# ANEXOS (copia literal)


## Anexo A — Todos tus prompts, literales y en orden (76 mensajes)

Fecha y hora UTC de cada mensaje. Texto tal cual lo escribiste (sin notificaciones automáticas).


### Mensaje 0 — 2026-11-04 19:00 — ROL

```text
ROL
Eres artista técnico senior de entornos 3D para videojuegos, experto en Blender (Python/bpy) y en pipelines hacia Godot 4. Trabajas a través de Blender MCP (execute_blender_code, get_scene_info, look, import_asset, search_assets, etc.). Tu meta es producir el MEJOR resultado posible, no el más rápido.

EL JUEGO
- MMORPG 3D de estilo magia medieval, con cámara ISOMÉTRICA (ortográfica, rotación X=54.7°, Z=45°). Se hace en Godot 4.
- Mundo en ruina: todas las razas viven en una única ciudad amurallada llamada Concordia, sobre una colina. En el centro está el Portal, que baja a los pisos del mundo. La ciudad es 100% segura, sin enemigos.
- Tono visual: ciudad apretada y REMENDADA, construida con ruinas reutilizadas (parches de piedra distinta, vigas de reemplazo, techos reparados, piezas antiguas reutilizadas).
- Paleta: caliza clara y gastada, madera oscura, teja ocre desgastada, hierro negro, telas remendadas en tonos tierra, muralla gris. El azul pálido de esquirlas #8FD0FF (emisivo) es el ÚNICO color mágico fuerte. Está prohibido usar otros colores mágicos.
- Capacidad: 300 a 500 jugadores a la vez en la ciudad. Calles y plazas anchas, cero cuellos de botella, y rendimiento obligatorio (piezas modulares, instancias, LODs, presupuestos de triángulos).

REGLAS DE TRABAJO
1. Referencias visuales primero. Antes de modelar cualquier pieza, identifica o busca referencias reales (lugares, fotos, arquitectura, naturaleza) y nómbralas. Si el pedido no trae referencias, búscalas tú y dime cuáles usaste y qué copiaste de cada una. Nunca uses material con derechos de autor de otros juegos o películas como referencia; usa solo lugares y objetos reales.
2. Legibilidad isométrica. Cada pieza debe leerse bien desde arriba y de lejos: silueta clara, contraste de valor entre suelo y objetos, nada alto que tape puertas o NPC importantes, sin voladizos que oculten el suelo. El detalle fino va en los materiales (normal maps), no en la geometría.
3. Un paso a la vez. Después de CADA etapa verifica con look (captura isométrica y otra a altura de personaje) y get_scene_info, y compara con las medidas pedidas. Si algo no coincide, corrígelo antes de seguir.
4. Medidas exactas. 1 unidad de Blender = 1 metro. Ejes: +Y = Norte, +X = Este, +Z arriba. Respeta las cifras del pedido. Si crees que una cifra está mal, avísame y propón el cambio, pero no lo apliques sin confirmación.
5. Código limpio y repetible. Scripts bpy parametrizados (semillas fijas, constantes al inicio) para poder regenerar. Transformaciones aplicadas, origen en la base de cada pieza, normales recalculadas, sin caras duplicadas ni n-gons problemáticos.
6. Organización. Una Collection por zona o familia de piezas. Nombres en inglés, sin espacios ni acentos, con prefijo (TRN_, WALL_, TOWER_, GATE_, BASTION_, MARKER_, MAT_). Guarda el .blend con versionado (concordia_v01.blend, v02...) al terminar cada etapa.
7. Pensado para Godot. Materiales simples compatibles con glTF (Principled BSDF, emisión). UVs sin costuras. Sufijos de importación de Godot: -col, -colonly, -convcolonly, -navmesh, -occ. Exporta .glb con +Y Up. Los Empties se exportan como marcadores para Marker3D.
8. Presupuestos de triángulos. Respeta los del pedido. Si no hay, usa: pieza pequeña ≤ 1.500, media ≤ 5.000, grande ≤ 12.000, con LOD1 (50%) y LOD2 (15%).
9. Honestidad. Si una herramienta falla, un resultado se ve mal o no puedes cumplir algo, dímelo con la causa y tus opciones. No digas que algo quedó bien si no lo verificaste.
10. No improvises alcance. No añadas piezas extra, no cambies el estilo y no rehagas lo ya aprobado. Si hay una decisión abierta, propón 2 o 3 opciones con referencias y espera mi elección.

CONTROL DE CALIDAD (antes de dar algo por terminado, revísalo y repórtalo con números reales)
¿Se lee bien desde la cámara isométrica? ¿Las medidas coinciden? ¿Sin costuras, caras invertidas ni geometría flotante? ¿Triángulos dentro del presupuesto? ¿Respeta la paleta? ¿Está nombrado, organizado y guardado?

FORMATO DE TUS RESPUESTAS
Al empezar: una línea con lo que harás y las referencias que usarás. Durante el trabajo: sin narración innecesaria. Al terminar cada etapa: resultado en 2 o 3 frases, capturas, números de verificación y el siguiente paso.

REFERENCIAS BASE DE CONCORDIA
- Silueta de la ciudad: Mont-Saint-Michel (Francia) y Toledo (España).
- Muralla y torres: Cité de Carcassonne (torres redondas con techo cónico) y murallas de Ávila (torres semicirculares de granito). Camino de ronda: Dubrovnik. Puertas: Caernarfon y Conwy.
- Plaza del Portal: Plaza del Campo de Siena (losas en abanico con bandas radiales).
- Calles y casas: Rothenburg ob der Tauber, Český Krumlov. Gremios: Grand-Place de Bruselas. Canal y puentes: Brujas. Arcos y escalinatas entre barrios: Malá Strana (Praga).
- Torre del Faro: Torre de Hércules (A Coruña).
- Exterior de ceniza: Bardenas Reales (España), en gris.
- Texturas CC0 (Poly Haven, mapas Normal GL para Godot): Cobblestone Floor 001, Sandstone Cracks, Rock Boulder Cracked, Rocks Ground 02, Stone Wall 02.

CUANDO ESTÉS LISTO
Responde solo: "Listo. Dime la primera pieza." y espera mi pedido.
```


### Mensaje 1 — 2026-11-04 19:02 — Vamos a construir CONCORDIA, la ciudad principal. Crea la escena base.

```text
Vamos a construir CONCORDIA, la ciudad principal. Crea la escena base.

1. Escena nueva y limpia. Unidades métricas, escala 1.0. Guarda como concordia_v01.blend.
2. Crea estas Collections vacías: TERRAIN, PLAZA, WALL_KIT, WALL_LAYOUT, STREETS, MARKERS_DISTRICTS, MORADAS, CAUCE, EXTERIOR.
3. Crea una cámara isométrica "CAM_Iso": ortográfica, rotación X=54.736°, Z=45°, escala ortográfica 120. Úsala para todas las capturas de verificación.
4. Crea Empties de ejes: MARKER_Gate_E (Alba), MARKER_Gate_N, MARKER_Gate_W (Ocaso), MARKER_Gate_S, a radio 200 m, en los ángulos 0°, 90°, 180° y 270° (ángulo desde +X, antihorario), Z=+6.

DATOS FIJOS (guárdalos como constantes en un script reutilizable, concordia_const.py):
- Muralla circular en radio 200 m, base a Z=+6.0 (llámalo DATUM). Altura de muralla 15 m. Torre del Faro 40 m. Plaza del Portal de 120 m de diámetro (radio 60).
- Calles principales de 8 a 10 m, callejones de 4 a 5 m.
- Sectores (ángulo desde +X): Oficios (Este) 0° ±25°; Mercado (Norte) 90° ±25°; Clases (Oeste) 180° ±25°; Razas (Sur) 270° ±25°. Moradas en las diagonales 45°, 135°, 225°, 315°, cada una ±20°. Cardinales: radio 60 a 185. Moradas: radio 100 a 190. Hitos junto a la plaza (Faro NE, Santuario NO, Salón de las Hazañas SE, Obelisco SO): radio 60 a 95.
- Niveles (Z absoluto): plaza +8.0; DATUM +6.0; fin de distritos cardinales +4.5; moradas de +4.5 a +9.5; yermo exterior 0.
- Paleta: azul pálido #8FD0FF como único color mágico.

Confirma que todo está creado y muéstrame una captura isométrica de la escena con los 4 marcadores de puerta.
```


### Mensaje 2 — 2026-11-04 19:14 — Crea el terreno base de la colina de Concordia dentro de la muralla (radio 0 a 212 m, incl

```text
Crea el terreno base de la colina de Concordia dentro de la muralla (radio 0 a 212 m, incluye talud exterior).

REFERENCIAS: Mont-Saint-Michel (ciudad que se eleva sobre una base de roca, calles que suben) y Toledo (casco antiguo sobre colina, casas escalonadas). Copia la sensación de ciudad en pendiente con terrazas y muros de contención, no los edificios.

1. Malla: Grid de 424x424 m centrado en el origen, celdas de 1 m, nombrado TRN_City. Elimina los vértices con radio > 212 m. Colección TERRAIN.
2. Altura por código (función h(r, ángulo), con smoothstep en las transiciones):
   - r ≤ 60: Z = +8.0 (plaza, plana, con 0.5% de inclinación hacia afuera para drenaje).
   - r 60 a 90: baja de +8.0 a +6.0 (pendiente ~3.8°).
   - Sectores cardinales (Mercado, Oficios, Clases, Razas): r 90 a 165 baja de +6.0 a +4.5; r 165 a 185 plano a +4.5; r 185 a 196 sube de +4.5 a +6.0 (terraplén al pie de la muralla); r 196 a 204 plano a +6.0 (base de la muralla).
   - Sectores diagonales: r 60 a 95 plano a +6.0 (zona de hitos, con baja suave desde la plaza); r 95 a 105 rampa de +6.0 a +4.5; después 6 terrazas de 14 m de profundidad (de r=105 a r=189) que suben 1.0 m cada una, llegando a +9.5; r 189 a 204 plano a +9.5 hasta fundirse con la base de la muralla (la muralla queda parcialmente enterrada ahí, es correcto).
   - Los saltos de terraza deben tener cara casi vertical (80°): inserta anillos de aristas en cada borde de terraza (bmesh) para que el salto de 1.0 m no se estire.
   - Mezcla las transiciones entre sectores en 6 m de ancho para que no haya costuras bruscas en los bordes angulares.
   - Talud exterior: de r=204 a r=212 baja de +6.0 a 0.
3. Ruido: solo 5 cm de irregularidad en la zona urbana (suelo antiguo remendado). Nada de hundimientos grandes ni ondulación mayor.
4. Pendiente máxima caminable en calles y plazas: 5° (con escalinata si pasa de 8°). Calcula las normales y reporta el máximo por sector.
5. Vertex groups: plaza, landmarks, sector_mercado, sector_oficios, sector_clases, sector_razas, sector_moradas, terraza_id, talud, base_muralla.
6. Vertex colors: retaining_mask (caras casi verticales de terrazas), dirt_mask, stone_mask.

Entrega: capturas isométrica y cenital, y una de perfil (corte) mostrando el relieve. Reporta pendientes máximas.
```


### Mensaje 3 — 2026-11-04 19:38 — Decisiones sobre el Prompt 2 (terreno de la colina):

```text
Decisiones sobre el Prompt 2 (terreno de la colina):

1. Bordes laterales de las Moradas: opción (a). Muros de contención verticales en los bordes laterales, como en Toledo. Su altura crece con cada terraza, de 1.0 m en la primera a 5.0 m en la última. Los tramos de más de 3 m llevan contrafuertes cada 8 m y pretil de 0.9 m en lo alto. Escaleras de 2.5 m de ancho cada 25 m en cada borde lateral, empezando por la terraza más baja. Elimina la mezcla de 6 m en esos bordes. Texturizar con retaining_mask.

2. Terraplén de las puertas: opción (a). Rampa de r 175 a 196 (+4.5 a +6.0, 4.1°); el plano de +4.5 queda en r 165 a 175. Excepción: en el eje de cada avenida, la plazoleta frente a la puerta (30 m de ancho x 20 m de fondo) debe quedar plana a +6.0 entre r=176 y r=196. En ese eje, mueve la rampa a r 150 a 176 (3.3°), con ancho igual a la avenida más la plazoleta. Fuera de ese eje, la rampa queda como en (a).

3. Legibilidad isométrica: opción (c), las dos cosas. Pretil bajo de 0.6 m en el borde superior de cada terraza, y máscara de borde más oclusión ambiental en el material (oscurecer bordes y base de los muros). Después verifica las 4 Moradas (NE, NO, SE, SO) con CAM_Iso a escala ortográfica 45 (aproximado a la escala de juego, no a 120) y muéstrame una captura de cada una. Si alguna no se lee, propón un ajuste antes de seguir.

4. Escalinata r 95 a 105 en las diagonales: confirmada. Referencia: Malá Strana (Praga), escalinata monumental de peldaños bajos. Ancho 6 m (igual que la calle diagonal), 10 peldaños de 15 cm de contrahuella con 1.0 m de huella, y un descanso de 2 m en el medio. Pasamanos de piedra baja de 0.9 m a los lados.

Triángulos: apruebo tu propuesta de mantener la malla de 1 m como MAESTRA y exportar una versión optimizada a Godot (ruido de 5 cm pasado a normal map, zonas planas simplificadas con decimate planar, ciudad troceada por chunks con LOD1 y LOD2).
Aclaración sobre el presupuesto: los 12.000 triángulos por "pieza grande" eran para props y edificios, no para el terreno. El presupuesto del terreno es por CHUNK de 50x50 m: 35.000 máx en la ciudad y 8.000 en el exterior. Con unos 57 chunks de ciudad, tus 292.000 dan ~5.100 por chunk, así que ya cumples. Mide y reporta lo siguiente antes de optimizar: triángulos por chunk en LOD0 (promedio y máximo), y cuáles chunks son los más pesados (probablemente las terrazas de las Moradas y los muros de contención). Después optimiza solo los que se pasen, y reporta el antes y el después.

Cuando termines, repite la verificación del Prompt 2 con los cambios (pendiente máxima por sector, capturas isométrica, cenital, corte de perfil y a altura de personaje) y guarda concordia_v02.blend.
```


### Mensaje 4 — 2026-11-04 21:17 — Construye la Plaza del Portal. Solo terreno, pedestales, marcadores y bases. Los edificios

```text
Construye la Plaza del Portal. Solo terreno, pedestales, marcadores y bases. Los edificios se hacen después.

REFERENCIAS: Plaza del Campo de Siena (losas en abanico con bandas radiales claras de travertino, edificios alrededor, escala de plaza abierta) y Torre de Hércules (A Coruña) para la base de la Torre del Faro: faro de piedra sobre colina. Copia el patrón de losas y la proporción plaza-edificios.

1. Plaza: disco de radio 60 a Z=+8.0 (ya está en TRN_City). El patrón NO es geometría: es textura/máscara. Losas en CÍRCULOS CONCÉNTRICOS (anillos cada 6 m) con 8 bandas radiales de travertino de 0.4 m de ancho alineadas con las 4 avenidas y 4 calles diagonales. En geometría solo hay desniveles suaves de ±3 cm por celdas de 2 m en el 20% de las losas, y remiendos. Crea las máscaras como vertex colors: slab_ring_id, travertine_band, repair_mask.
2. Zona despejada: ningún obstáculo entre r=15 y r=48 (zona de reunión de cientos de jugadores).
3. Pedestal del Portal: disco de radio 6, elevado 0.9 m en el centro (0,0). Empty MARKER_Portal_Center. El arco mide 12 m (se modela después).
4. Siete piedras bajas con runas (0.8 m de alto, 0.6 m de diámetro) en un círculo de radio 9, a 51.4° entre sí. Empties MARKER_Runestone_01 a 07.
5. Atrio de Descenso: plataforma circular de 30 m de diámetro (r=15), elevada 0.6 m. Anillo de 21 pedestales (uno por cada piso al que se baja directo: 1, 5, 10, 15 ... 100) en r=13.5, cada 17.14°, de 1.2 m de diámetro y 0.5 m de alto. Empties MARKER_Descent_Pedestal_01 a 21.
6. Anillo de edificios restaurados (restos de la plaza original): banda r=48 a 60, con 8 parcelas de 22x16 m y fachadas hacia la plaza. Empties MARKER_PlazaBuilding_01 a 08.
7. Hitos diagonales, con plataforma nivelada y marcador:
   - NE (45°, r=72): Torre del Faro, base circular de 14 m de diámetro, altura 40 m. Empty MARKER_Faro. Su cima debe verse desde cualquier calle.
   - NO (135°, r=70): Santuario del Retorno, pad de 16x12 m. MARKER_Santuario.
   - SE (315°, r=72): Salón de las Hazañas, pad de 42x16 m. MARKER_SalonHazanas.
   - SO (225°, r=66): Obelisco de los Pisos, base de 5x5 m, altura 25 m. MARKER_Obelisco.
8. Canales de luz: 4 canales finos (20 cm de ancho, 5 cm de profundidad) que van de la Torre del Faro al Portal por el suelo, para emisión azul pálido (#8FD0FF).
9. Vertex color magic_glow_mask: degradado alto cerca del Portal y los canales.

Entrega: cenital, isométrica y una a altura de personaje desde la entrada de la avenida Norte mirando al Portal.
```


### Mensaje 5 — 2026-11-04 21:45 — Construye la muralla de Concordia como KIT MODULAR para instanciar en Godot.

```text
Construye la muralla de Concordia como KIT MODULAR para instanciar en Godot.

REFERENCIAS: Murallas de Ávila (granito gris cálido, torres semicirculares, almenas regulares), Carcassonne (techos cónicos de pizarra oscura, camino de ronda con parapeto y almenas), Dubrovnik (paseo ancho sobre el muro con vistas al exterior), Caernarfon y Conwy (puerta flanqueada por dos torres con bandas de piedra clara y oscura). Copia de cada una silueta, remate y proporción.

DIMENSIONES: muro de 15 m de alto, 6 m de grosor en la base y 4 m en la corona (talud de 2 m en la base). Camino de ronda de 3 m de ancho. Parapeto de 1.2 m con almenas de 1.4 m de alto, 1 m de ancho y 0.6 m de separación. Saeteras (0.2x1.2 m) cada 4 m.

DISPOSICIÓN (círculo de radio 200, base Z=+6.0): 48 posiciones cada 7.5°, k = 0 a 47.
- k múltiplo de 12 (0°, 90°, 180°, 270°): GATE_Sealed_Twin, las 4 puertas.
- k múltiplo de 4 pero no de 12 (30°, 60°, 120°, 150°, 210°, 240°, 300°, 330°): torres de guardia.
- Las 36 restantes: bastiones.
- Entre posiciones consecutivas: módulo de muro de cuerda 26.16 m (2*200*sin(3.75°)).
Crea Empties MARKER_WallSlot_00 a 47 con la rotación tangente al círculo, mirando hacia afuera. Colección WALL_LAYOUT.

PIEZAS (colección WALL_KIT, origen en el centro de la base de cada pieza):
1. WALL_Mod_A (26.16 m): muro original, hiladas visibles. Máx 3.000 triángulos.
2. WALL_Mod_B: igual con 2 o 3 parches de piedra distinta y vigas de madera de reemplazo.
3. WALL_Mod_C: con hourde de madera a medio terminar sobre el parapeto.
4. BASTION_Open: semicircular, 5 m de diámetro, 16.5 m de alto, almenado, sin techo. Máx 1.200.
5. BASTION_Mirador: balcón de piedra de 4x2.5 m con parapeto que sobresale hacia fuera (para las diagonales 45°, 135°, 225°, 315°, k=6, 18, 30, 42). Vista a la ceniza.
6. TOWER_Guard_Roof: 9 m de diámetro, 22 m de alto, techo cónico de pizarra, y una linterna de cristal azul pálido de 1.2 m en lo alto (emisión 2.5, #8FD0FF). Máx 5.000.
7. TOWER_Guard_Patched: igual con parches de teja y madera en el techo.
8. GATE_Sealed_Twin: dos torres de 12 m de diámetro y 24 m de alto flanqueando un arco ojival de 8 m de ancho y 10 m de alto SELLADO con hojas de hierro negro cerradas a ras y una runa central de 1.5 m (emisión 2.5, #8FD0FF). Sin rastrillo levantado. Máx 12.000.
9. STAIR_Gate (L y R): escalera de piedra de 3 m de ancho por el lado interior de cada puerta que sube al camino de ronda.
10. WALL_Drain_Grate: reja de hierro de 1.2 m de alto en la base del muro, en 345° (para que salga el Cauce).

Distribución con seed 21: módulos 70% A, 20% B, 10% C; torres de guardia 70% Roof y 30% Patched.

MAGIA: una línea de runas talladas (3 cm de profundidad, 8 cm de ancho) continua en la hilada inferior de todos los módulos, color #8FD0FF, emisión base 0.8 como parámetro editable (material MAT_Wall_Runes). Las runas se encienden al anochecer en Godot.

ASPECTO REMENDADO: 30% de los módulos con parches de piedra distinta. Bevel de 3 cm en bordes de bloque.

VERIFICA: altura real 15 m, 12 estructuras principales (4 puertas + 8 torres de guardia), 48 posiciones de muro, ningún camino que salga de las puertas. Capturas: puerta Alba por dentro, torre de guardia con linterna, mirador, y cenital.
```


### Mensaje 6 — 2026-11-04 21:54 — REINTENTA LO DE Empiezo por las texturas: las genero por código, ya que no hay acceso a Po

```text
REINTENTA LO DE Empiezo por las texturas: las genero por código, ya que no hay acceso a Poly Haven desde aquí.
```


### Mensaje 7 — 2026-11-04 21:56 — Construye la muralla de Concordia como KIT MODULAR para instanciar en Godot.

```text
Construye la muralla de Concordia como KIT MODULAR para instanciar en Godot.
REFERENCIAS: Murallas de Ávila (granito gris cálido, torres semicirculares, almenas regulares), Carcassonne (techos cónicos de pizarra oscura, camino de ronda con parapeto y almenas), Dubrovnik (paseo ancho sobre el muro con vistas al exterior), Caernarfon y Conwy (puerta flanqueada por dos torres con bandas de piedra clara y oscura). Copia de cada una silueta, remate y proporción.
DIMENSIONES: muro de 15 m de alto, 6 m de grosor en la base y 4 m en la corona (talud de 2 m en la base). Camino de ronda de 3 m de ancho. Parapeto de 1.2 m con almenas de 1.4 m de alto, 1 m de ancho y 0.6 m de separación. Saeteras (0.2x1.2 m) cada 4 m.
DISPOSICIÓN (círculo de radio 200, base Z=+6.0): 48 posiciones cada 7.5°, k = 0 a 47.

* k múltiplo de 12 (0°, 90°, 180°, 270°): GATE_Sealed_Twin, las 4 puertas.
* k múltiplo de 4 pero no de 12 (30°, 60°, 120°, 150°, 210°, 240°, 300°, 330°): torres de guardia.
* Las 36 restantes: bastiones.
* Entre posiciones consecutivas: módulo de muro de cuerda 26.16 m (2200sin(3.75°)).
Crea Empties MARKER_WallSlot_00 a 47 con la rotación tangente al círculo, mirando hacia afuera. Colección WALL_LAYOUT.

PIEZAS (colección WALL_KIT, origen en el centro de la base de cada pieza):

1. WALL_Mod_A (26.16 m): muro original, hiladas visibles. Máx 3.000 triángulos.
2. WALL_Mod_B: igual con 2 o 3 parches de piedra distinta y vigas de madera de reemplazo.
3. WALL_Mod_C: con hourde de madera a medio terminar sobre el parapeto.
4. BASTION_Open: semicircular, 5 m de diámetro, 16.5 m de alto, almenado, sin techo. Máx 1.200.
5. BASTION_Mirador: balcón de piedra de 4x2.5 m con parapeto que sobresale hacia fuera (para las diagonales 45°, 135°, 225°, 315°, k=6, 18, 30, 42). Vista a la ceniza.
6. TOWER_Guard_Roof: 9 m de diámetro, 22 m de alto, techo cónico de pizarra, y una linterna de cristal azul pálido de 1.2 m en lo alto (emisión 2.5, #8FD0FF). Máx 5.000.
7. TOWER_Guard_Patched: igual con parches de teja y madera en el techo.
8. GATE_Sealed_Twin: dos torres de 12 m de diámetro y 24 m de alto flanqueando un arco ojival de 8 m de ancho y 10 m de alto SELLADO con hojas de hierro negro cerradas a ras y una runa central de 1.5 m (emisión 2.5, #8FD0FF). Sin rastrillo levantado. Máx 12.000.
9. STAIR_Gate (L y R): escalera de piedra de 3 m de ancho por el lado interior de cada puerta que sube al camino de ronda.
10. WALL_Drain_Grate: reja de hierro de 1.2 m de alto en la base del muro, en 345° (para que salga el Cauce).

Distribución con seed 21: módulos 70% A, 20% B, 10% C; torres de guardia 70% Roof y 30% Patched.
MAGIA: una línea de runas talladas (3 cm de profundidad, 8 cm de ancho) continua en la hilada inferior de todos los módulos, color #8FD0FF, emisión base 0.8 como parámetro editable (material MAT_Wall_Runes). Las runas se encienden al anochecer en Godot.
ASPECTO REMENDADO: 30% de los módulos con parches de piedra distinta. Bevel de 3 cm en bordes de bloque.
VERIFICA: altura real 15 m, 12 estructuras principales (4 puertas + 8 torres de guardia), 48 posiciones de muro, ningún camino que salga de las puertas. Capturas: puerta Alba por dentro, torre de guardia con linterna, mirador, y cenital.
```


### Mensaje 8 — 2026-11-04 22:23 — Decisiones sobre tus puntos (Prompt 2, 3 y 4):

```text
Decisiones sobre tus puntos (Prompt 2, 3 y 4):

1. Altura 15 m hasta lo alto de las almenas, con camino de ronda a 12.4 m: APROBADO.

2. Escalón exterior de las Moradas: APROBADO. Baja el terreno de las diagonales hasta quedar bajo el muro (r≈200), de modo que por fuera el talud arranque a +6.0 desde el borde exterior del muro. Regenera la v02 y la v03 con ese cambio. Conserva todas las decisiones anteriores (muros laterales de las Moradas, rampa de las puertas, pretiles de terraza, escalinata de r 95 a 105). Cambia solo esa función del script y repite la verificación de pendientes y las capturas.

3. Runas enterradas: CAMBIO a tu propuesta. No hagas una variante solo para las Moradas, porque el anillo mágico se vería con un salto de altura. Sube la línea de runas a +4.5 m sobre la base del muro en LOS 48 módulos, para que el anillo sea continuo a una sola altura y quede 1 m sobre el terreno de las Moradas. Ajusta MAT_Wall_Runes y las bandas de bloque si hace falta. Verifica que se ve desde dentro y desde fuera.

4. Camino de ronda: APROBADO con cuatro tramos entre puertas, una escalera a cada lado de cada puerta y las torres de guardia desplazadas 4 m hacia fuera. Añade una puerta de acceso a cada torre de guardia a nivel del camino (12.4 m) para que los NPC guardias entren. El adarve de la puerta a 15.05 m es solo una terraza decorativa: no lo conectes a la navegación. Dime también si el camino de ronda queda con colisión plana y continua en cada tramo.

5. Reja del Cauce en la base del frente del bastión k=46: APROBADO. El Cauce (Prompt 7) llegará hasta ahí.

6. Oclusión isométrica: ACEPTADO como caso de Godot. En Blender haz esto: añade la propiedad personalizada occludes_iso=true en los 24 módulos que tapan la ciudad desde CAM_Iso, y confirma que el material de la muralla admite un fade por dithering (sin cambiar nada de la geometría). Mantén los 15 m. Reporta la lista de módulos marcados.

7. Texturas: de momento SIGUE con las procedurales, pero antes de aplicarlas al terreno muéstrame cada material sobre esfera y plano 4x4 m y mejora cualquier cosa que se vea plana, repetitiva o de plástico. Construye cada material con la misma convención de nombres y escala UV (1 m = 1 tile) de forma que cambiarlas más adelante por las de Poly Haven sea solo sustituir 3 imágenes (Albedo, Normal GL, Roughness). Antes de empezar, ejecuta get_addon_status y dime si Poly Haven aparece disponible en el addon de Blender.

8. Orientación de marcadores: SÍ, unifícalos todos. Convención: el eje +Y local de cada Empty apunta hacia afuera / hacia el frente (la fachada o la salida). En Godot eso equivale a -Z (adelante). Aplícalo a MARKER_Gate_*, MARKER_WallSlot_*, y a las propiedades door_direction de los MARKER_Bld_*. Documenta la convención en un archivo README_markers.txt.

Después de aplicar todo: guarda concordia_v04.blend y repíteme la verificación de pendientes máximas por sector, el estado de la muralla (12 estructuras, 48 posiciones, runas visibles a +4.5 m) y las capturas isométricas, de la muralla desde un mirador y de una Morada.
```


### Mensaje 9 — 2026-11-04 23:09 — Inténtalo de nuevo

```text
Inténtalo de nuevo
```


### Mensaje 10 — 2026-11-05 00:14 — Define la red de calles y las parcelas de los 4 distritos cardinales. Solo terreno y marca

```text
Define la red de calles y las parcelas de los 4 distritos cardinales. Solo terreno y marcadores; los edificios se modelan después con un kit.

REFERENCIAS: Rothenburg ob der Tauber (calles de adoquín con casas de entramado), Grand-Place de Bruselas (fachadas de gremios alrededor de una plaza), Český Krumlov (calles estrechas que giran, techos de teja), Malá Strana (calles estrechas con arcos y escalinatas entre barrios).

CALLES (como zona aplanada con bordes marcados en TRN_City, pendiente máx 5°, escalinata si pasa de 8°):
- 4 avenidas axiales de 10 m desde la plaza (r=60) hasta cada puerta sellada.
- 4 calles diagonales de 6 m hacia los hitos y las moradas.
- Anillo de r=100 (8 m) y anillo de r=150 (6 m), con curvas suaves de 1 a 2 m para que parezca crecido sin plan.
- Callejones de 4 a 5 m (seed 11), 15% ciegos.
- Adoquín: la textura lleva el detalle (MAT_Cobble_Concordia); en geometría solo desniveles suaves y 8 parches remendados con otra piedra. Surcos de carretas en el distrito de oficios.
- Plazoleta de 30 m de diámetro frente a cada puerta sellada.
- Vertex colors: road_mask, wear_mask, cobble_type.

PARCELAS: aplanadas a la altura del sector, con bordes marcados. Cada una lleva un Empty MARKER_Bld_<Nombre> con propiedades personalizadas: footprint (ancho x fondo), door_direction, interior (true o false). Los edificios con servicios llevan interior=true; los demás son solo decoración (false).

MERCADO (Norte, calles de 10 m con toldos): Fuente del Mercado (plaza central de 22 m de diámetro en r=105); Tesorería de la Muralla 28x18; Gran Subasta 40x16; Banco 24x20; Plaza de Provisiones con 14 puestos de 3x3 m; Posada 20x16 (con Tablón de Grupos en la entrada); Casa del Registro 14x12.

OFICIOS (Este): 4 gremios (Mineros 18x14, Herbolarios 22x12 con terrazas de hierbas, Cazadores 20x14 más campo de tiro de 20x10, Pescadores 18x14 pegado al Cauce); 7 talleres de 16x12 (Gran Forja 26x16 con fundición abierta, Curtiduría, Sastrería, Carpintería, Alquimia, Hornos de Concordia, Joyería y Tallado); Crisol de las Piedras circular de 22 m de diámetro; Casa de Reparaciones 16x10 abierta.

CLASES (Oeste): Plaza de las Armas de 50x40 (tierra apisonada y adoquín) con 6 zonas de maniquíes; Casa de Reposición 24x12; salones de clase de 18x14 en abanico alrededor de la plaza (N_CLASES = 8 como plantilla, déjalo como parámetro para ajustarlo después).

RAZAS (Sur): N_RAZAS = 6 barrios como plantilla (parámetro). Cada barrio de unos 35x35 con una Casa de Raza de 20x16 (la más grande), de 6 a 10 casas de 8x8 a 12x10 y una plazuela de 10 m de diámetro con fuente o árbol.

Entrega: cenital con calles y parcelas coloreadas por distrito, y una vista isométrica de cada distrito.
```


### Mensaje 11 — 2026-11-05 01:44 — Crea el terreno de las 4 Moradas de Concordia (viviendas de los jugadores).

```text
Crea el terreno de las 4 Moradas de Concordia (viviendas de los jugadores).

REFERENCIAS: Český Krumlov y Toledo (casas apretadas con tejados escalonados sobre colina), Mont-Saint-Michel (calles y escalinatas que suben pegadas a un muro), Malá Strana (arcos y escaleras entre niveles).

POR CADA SECTOR DIAGONAL (NE, NO, SE, SO):
- Las 6 terrazas ya existen en TRN_City (14 m de profundidad, salto de 1.0 m, de r=105 a r=189). Añade el detalle:
- Cada terraza con 16 a 17 parcelas de 6x10 m, unas 100 por conjunto. Empties MARKER_Morada_xx con propiedad tipo (habitacion / casa_pequena / casa_grande), repartidos 50% / 35% / 15%.
- Muros de contención de piedra en cada salto de terraza (1.0 m de alto, textura por retaining_mask), con escalera de 2.5 m de ancho cada 25 m.
- Pequeños jardines marcados en las parcelas de casa grande (garden_mask).
- Calle de servicio de 4 m en cada terraza y una calle de 6 m que une el conjunto con la diagonal hacia la plaza.
- Casa del Registro queda en el Mercado, no aquí.
- Vertex colors: terraza_id, garden_mask.

Importante: comprueba en una captura isométrica que los techos futuros de una terraza no tapen las puertas de la de abajo. Si lo hacen, aumenta la separación entre filas de casas a 2 m extra.
```


### Mensaje 12 — 2026-11-05 02:14 — Crea el canal de agua de la ciudad y las conexiones entre barrios.

```text
Crea el canal de agua de la ciudad y las conexiones entre barrios.

REFERENCIAS: Canales de Brujas (canal estrecho con puentes de piedra) y Malá Strana (arcos, escalinatas y pasos entre barrios).

CAUCE: nace en la Fuente del Mercado (la vertiente propia de la colina). Sigue hacia el Este por el distrito de Oficios con un canal de 4 m de ancho y 1.2 m de profundidad, orillas de piedra con escalones de acceso cada 20 m, y termina en la reja bajo la muralla (WALL_Drain_Grate, a 345°). Superficie del agua plana a 0.4 m bajo el borde, material MAT_Water. En el Gremio de Pescadores, un muelle de 8x3 m. En la Carpintería, un hueco de 3 m de ancho para la rueda hidráulica. Colección CAUCE.

PUENTES: Empties MARKER_Bridge_xx con ancho y largo. 4 puentes de piedra de 5 a 6 m de ancho sobre el Cauce y de 6 a 8 puentes y arcos entre los barrios de las razas (arco sobre calle de 4 a 6 m, 5 m de alto libre). Cada puente es un tramo de calle elevado 0.4 m con pretiles de 0.9 m.

ESCALINATAS: unas 10 donde la pendiente pase de 8°, con contrahuella de 15 cm y huella de 35 cm.

Aspecto remendado: reparaciones con piedra distinta en el 20% de los pretiles. El agua es el único elemento fuera de la paleta que puede reflejar el azul pálido del cielo; mantenla oscura y apagada.
```


### Mensaje 13 — 2026-11-05 12:59 — Crea el terreno exterior (radio 204 a 400 m). Es ceniza gris, sin salidas.

```text
Crea el terreno exterior (radio 204 a 400 m). Es ceniza gris, sin salidas.

REFERENCIAS: Bardenas Reales (España): badlands erosionados, cauces secos, mesetas y colinas aisladas de arenisca. Copia la forma del relieve, pero con color gris ceniza.

1. Talud exterior ya existe en TRN_City (de +6 a 0 entre r=204 y 212). Foso seco de r=212 a 222, relleno de ceniza (fondo a -1.5).
2. Base: Grid de celdas de 3 m, plano en Z=0 con ruido grande (escala 80 m, ±3 m) y ruido medio (escala 15 m, ±0.6 m). Mínimo cerca de la muralla, aumenta hacia afuera.
3. SIN senderos, puentes ni rampas: las 4 puertas dan a un talud de ceniza acumulada sin camino. Dunas bajas (0.5 a 2 m) contra la base de la muralla.
4. Cauce seco de 15 a 25 m de ancho y 4 a 6 m de profundidad, curvas naturales y orillas erosionadas.
5. 15 a 20 afloramientos de roca de 6 a 20 m de alto con estratos horizontales; 6 cráteres de 10 a 30 m.
6. Acantilados en el borde del mapa (r=380 a 400): muros de roca de 25 a 40 m, cerrados, sin paso.
7. Color: ceniza gris #6F6F6F con zonas más oscuras en depresiones y más claras en dunas. Cero verde ni ocre.
8. Desde los miradores debe verse un paisaje gris con capas de relieve a distinta distancia. Las tormentas de ceniza se agregan en Godot (VFX), no aquí.
9. Vertex colors: ash_mask, ash_dark_mask, rock_mask. Colección EXTERIOR.
```


### Mensaje 14 — 2026-11-05 13:16 — Crea los materiales de Concordia, compatibles con glTF, con texturas tileables de 2048x204

```text
Crea los materiales de Concordia, compatibles con glTF, con texturas tileables de 2048x2048.

REFERENCIAS (texturas CC0 de Poly Haven, mapas Normal GL): Cobblestone Floor 001 (calles), Sandstone Cracks (suelo agrietado), Rock Boulder Cracked (taludes y roca), Rocks Ground 02 (ceniza y grava), Stone Wall 02 (muros viejos).

MATERIALES:
- MAT_Limestone_Worn: caliza clara y gastada (calles, muros y edificios).
- MAT_Cobble_Concordia: adoquín claro con juntas oscuras.
- MAT_Plaza_Slab: losas de plaza con bandas radiales de travertino (usa las máscaras de la Plaza).
- MAT_Wall_Gray: piedra gris de la muralla.
- MAT_Wood_Dark: madera oscura.
- MAT_Roof_Tile_Ocher: teja ocre desgastada.
- MAT_Iron_Black: hierro negro, metalicidad 0.6 (única superficie con metal).
- MAT_Cloth_Patch: telas remendadas en tonos tierra (3 variantes).
- MAT_Ash_Gray: ceniza gris.
- MAT_Shard_Blue: azul pálido #8FD0FF, emisión 2.5.
- MAT_Wall_Runes: runas de la muralla, emisión 0.8 parametrizable.
- MAT_Water: agua oscura, roughness 0.1.

REGLAS: roughness 0.7 a 0.95 salvo agua y hierro (0.4). Ningún color saturado fuera del azul pálido. UVs por proyección planar en mundo (1 m = 1 tile) para que no haya costuras entre chunks. Hornea Albedo, Normal y Roughness en /textures/concordia/. Asigna materiales por vertex colors y vertex groups (retaining_mask → muro de contención, road_mask → adoquín, slab_ring_id → plaza, ash_mask → ceniza).

Entrega: una esfera de prueba por material y un render isométrico de toda la ciudad con materiales.
```


### Mensaje 15 — 2026-11-05 13:35 — Prueba si puedes usar el poly haven solo respondeme si lo puedes usar

```text
Prueba si puedes usar el poly haven solo respondeme si lo puedes usar
```


### Mensaje 16 — 2026-11-05 13:39 — Ya lo añadí, prueba Poly Haven otra vez

```text
Ya lo añadí, prueba Poly Haven otra vez
```


### Mensaje 17 — 2026-11-05 13:40 — Si

```text
Si
```


### Mensaje 18 — 2026-11-05 13:54 — Ya tengo Poly Haven conectado (confírmalo con get_addon_status). Ahora reemplaza las textu

```text
Ya tengo Poly Haven conectado (confírmalo con get_addon_status). Ahora reemplaza las texturas procedurales por texturas reales de Poly Haven.

PASO 1: AUDITORÍA (no cambies nada todavía).
Lista TODOS los materiales de la escena en una tabla: nombre, tipo actual (procedural / imagen / vacío), dónde se usa (objetos o chunks) y si falta alguno de los 12 del Prompt 9 (MAT_Limestone_Worn, MAT_Cobble_Concordia, MAT_Plaza_Slab, MAT_Wall_Gray, MAT_Wood_Dark, MAT_Roof_Tile_Ocher, MAT_Iron_Black, MAT_Cloth_Patch, MAT_Ash_Gray, MAT_Shard_Blue, MAT_Wall_Runes, MAT_Water), además de los materiales de taludes, muros de contención y suelo exterior. Marca cuáles están pendientes. Detente y muéstrame la tabla.

PASO 2: PROPUESTA.
Con search_assets busca el mejor asset de Poly Haven (CC0, 2K) para cada material, empezando por estos candidatos:
- MAT_Cobble_Concordia: cobblestone_floor_001
- MAT_Limestone_Worn: stone_wall_02 (o una caliza clara si existe)
- MAT_Wall_Gray: stone_wall (o un muro de castillo gris)
- MAT_Plaza_Slab: un asset de losas o flagstone, con las bandas de travertino por máscara
- MAT_Ash_Gray: rocks_ground_02, desaturado a gris
- Muros de contención y taludes: rock_boulder_cracked, desaturado
- Suelo exterior: sandstone_cracks, desaturado a gris
- Para edificios: madera oscura, teja, hierro oxidado y tela (búscalos, aún no los apliques)
Dime el asset elegido por material con una razón corta. Los que no tengan equivalente (MAT_Shard_Blue, MAT_Wall_Runes, MAT_Water) se quedan procedurales, y los hornearás a PNG.

PASO 3: APLICACIÓN (después de que yo apruebe).
- Importa en 2K, mapas Albedo, Normal GL y Roughness.
- Escala UV: 1 m = 1 tile ajustado al ancho real del asset (Poly Haven indica "m wide"), sin costuras entre chunks (proyección planar en mundo).
- Ajusta el color a la paleta de Concordia con un nodo Hue/Saturation: caliza clara y gastada, muralla gris, ceniza gris #6F6F6F. Nada saturado fuera del azul #8FD0FF. Los tonos naranjas y ocres de los assets de roca deben quedar grises.
- Conserva las máscaras de vertex colors (road_mask, retaining_mask, slab_ring_id, ash_mask) para mezclar materiales.
- Dejar el árbol de nodos simple: solo texturas de imagen, mezcla por vertex color y Principled BSDF, para que exporte bien a glTF.
- Muéstrame cada material sobre esfera y plano de 4x4 m, y una captura isométrica de la ciudad con los materiales nuevos.

Guarda concordia_v05.blend y reporta.
```


### Mensaje 19 — 2026-11-05 13:56 — Decisiones sobre tus puntos. Sigue con el PASO 2 (propuesta de assets), sin aplicar nada t

```text
Decisiones sobre tus puntos. Sigue con el PASO 2 (propuesta de assets), sin aplicar nada todavía.

1. Muros de contención y taludes: SEPÁRALOS.
   - Taludes naturales (talud exterior de la muralla, taludes de la colina): crea MAT_Rock_Gray con rock_boulder_cracked desaturado a gris, mezclado con MAT_Ash_Gray según rock_mask y ash_mask.
   - Muros de contención de las Moradas y de las terrazas: se quedan con MAT_Limestone_Worn (stone_wall_02). Son mampostería construida, tienen que verse de la misma familia que los edificios. Para que se distingan de los edificios, añade los parches de MAT_Stone_Repair (ver punto de Stone_Repair abajo).

2. Suelo: APROBADA tu separación.
   - MAT_Ground_Cracked: la ciudad (sandstone_cracks, como está hoy).
   - MAT_Ash_Ground: nuevo, para el exterior. No uses sandstone_cracks desaturado (se vería igual que el suelo de la ciudad pero gris). Busca otro asset de suelo seco agrietado o de arcilla seca en Poly Haven, desaturado a gris ceniza #6F6F6F. Si no encuentras uno bueno, usa sandstone_cracks con otra escala (x2.5), otra rotación UV y la saturación a 0.
   - MAT_Ash_Gray (rocks_ground_02): se queda para dunas y foso.

3. Archivo: APROBADO. Guarda como concordia_v10.blend. No toques ninguna versión anterior.

4. Búsqueda de assets sin search_assets: APROBADO, con esta condición. Las consultas y descargas a Poly Haven (api.polyhaven.com) las haces con execute_blender_code, es decir, desde el Python de MI Blender (que tiene internet), no desde tu entorno. Si usas el addon de Poly Haven de Blender MCP, mejor. Criterios: CC0, 2K, ancho real en metros. Si algo falla, dime el error exacto.

PENDIENTES (confírmalos en tu propuesta): MAT_Plaza_Slab + MAT_Travertino, MAT_Wall_Gray, MAT_Wood_Dark, MAT_Roof_Tile_Ocher, MAT_Iron_Black, MAT_Cloth_Patch A, B y C, MAT_Stone_Repair, y los nuevos MAT_Rock_Gray y MAT_Ash_Ground.
Palabras clave para buscar: losas/flagstone/paving para la plaza; travertine/marble claro para las bandas; castle wall o muro gris para la muralla; dark wood planks; roof tiles terracotta; rusty/black metal; fabric/canvas/burlap; stone repair = una piedra de otro color y textura que la caliza (para parches remendados).
- MAT_Cloth_Patch A/B/C: usa UN solo asset de tela con 3 variantes de color (tonos tierra) con nodo Hue/Saturation, para ahorrar memoria de texturas.
- Memoria: 2K para terreno, plaza y muralla; 1K para madera, teja, hierro y tela (se usan en edificios).

Reporta la propuesta en una tabla: material, asset elegido de Poly Haven (ID y ancho real en metros), ajustes de color, escala UV, y razón corta. Espera mi aprobación antes del PASO 3.
```


### Mensaje 20 — 2026-11-05 14:08 — Decisiones sobre tus puntos antes del PASO 3:

```text
Decisiones sobre tus puntos antes del PASO 3:

1. Hue/Saturation: opción A. Hornea el ajuste de color dentro del albedo y deja el árbol en Image Texture → Principled BSDF. Guarda siempre el original sin tocar y el ajustado como archivo aparte (concordia_<material>_albedo.png), para poder rehacer el ajuste después. Anota en polyhaven.json: asset, ID, URL, licencia CC0, ancho real en metros, resolución y los valores de Hue/Saturation/Value aplicados. Telas: una sola textura desaturada y un color base distinto en A, B y C (tonos tierra), como propones.

2. Mezcla por vertex color: APROBADO. Asignación por cara según umbral de máscara en Blender, y las máscaras siguen exportándose en COLOR_0 para el shader de terreno de Godot. Para que el corte entre materiales no se vea como una línea dura en la vista isométrica, deja una banda de transición de 1 a 2 celdas donde las caras alternen materiales con un patrón de ruido (no una línea recta). Documenta en un archivo README_masks.txt qué significa cada canal de COLOR_0 (R, G, B, A) y qué mascara va en cada uno.

3. Máscaras que faltan: APROBADO.
   - rock_mask en los taludes por pendiente: roca desde ~35° con ruido para que el límite sea irregular, y que no invada calles ni terrazas.
   - ash_mask en el exterior y dune_mask para dunas.
   - Foso: máscara por la geometría real de la depresión (cota Z < 0 pegada al muro, r 204 a 222 aprox.), con MAT_Ash_Gray igual que las dunas.
   - El resto del exterior con MAT_Ash_Ground, y donde haya rock_mask con MAT_Rock_Gray.
   - Verifica con una captura que ninguna máscara tiñe calles, plaza, ni los muros de contención.

4. Sustituir en el kit de muralla: SÍ. Lo que dije de no aplicar a edificios era para edificios aún no modelados. El kit de muralla ya existe, así que aplica madera, teja, hierro y tela ahí: cadalsos, puertas, tejados de torres, rejas y la reja del Cauce. Las telas, solo en la esfera de prueba. No toques geometría.

5. Memoria: ~160 MB está aceptado como tope para texturas de ciudad. Para ahorrar, empaqueta Occlusion, Roughness y Metallic en una sola textura ORM (canales R, G, B), formato que glTF admite, si no lo estás haciendo ya. Si el total sube de 180 MB, avísame y bajamos a 1K los materiales de muros de contención y roca.

6. Rock_Gray: cambia a rock_boulder_dry SOLO si cumple las tres condiciones: se desatura bien a gris, es tileable (pasa un test 3x3 sin costuras visibles) y tiene ancho real razonable para un talud (1.5 a 4 m). Si falla cualquiera, deja rock_boulder_cracked. Dime en una línea cuál elegiste y por qué.

Procede con el PASO 3 y guarda concordia_v10.blend. Al terminar, muéstrame: cada material sobre esfera y plano 4x4 m, una captura isométrica de la ciudad, una del exterior con taludes y foso, y una de la muralla con madera, teja y hierro aplicados. Reporta la memoria total real en MB.
```


### Mensaje 21 — 2026-11-05 14:36 — Prepara Concordia para Godot 4.

```text
Prepara Concordia para Godot 4.

1. Limpieza: elimina duplicados (distancia 0.001), caras ocultas, normales invertidas. Transformaciones aplicadas.
2. Divide TRN_City en chunks de 50x50 m (TRN_City_Chunk_X_Y). Presupuesto: máx 35.000 triángulos por chunk de ciudad y 8.000 en el exterior. Si te pasas, aplica decimate planar solo en zonas planas. Los bordes entre chunks coinciden exactamente (sin costuras).
3. LOD0/LOD1 (50%)/LOD2 (15%) en terreno y piezas de muralla. La ciudad se ve desde lejos en isométrica, así que el LOD2 debe mantener la silueta.
4. Colisión: "-colonly" por chunk (calles y plaza), simple en pretiles, muros de contención y puentes. Sin colisión en juntas ni detalles de adoquín. Muralla: caja ligeramente cónica por módulo, cilindro por torre.
5. Navegación para NPC que pasean: "TRN_NavMesh-navmesh" que cubra calles, plazas, escaleras, puentes y plazoletas; excluye Cauce, taludes y terrazas no transitables.
6. Occluders ("-occ") para la muralla y las manzanas grandes.
7. Marcadores: todos los Empties (Portal, Runestone, Descent_Pedestal, PlazaBuilding, Faro, Santuario, Obelisco, SalonHazanas, Bld, Morada, Bridge, Gate, WallSlot) en concordia_markers.glb, con sus propiedades personalizadas.
8. Exporta glTF 2.0 (.glb), +Y Up, con vertex colors, materiales, UVs y normales: concordia_terrain_[distrito].glb, concordia_wall_kit.glb, concordia_markers.glb. Guarda concordia_master.blend versionado.
9. Entrega: lista de archivos con tamaño, triángulos totales y lista de Empties con coordenadas.
```


### Mensaje 22 — 2026-11-05 20:17 — Vamos a construir los EDIFICIOS de Concordia. Parte de la escena actual (terreno, muralla 

```text
Vamos a construir los EDIFICIOS de Concordia. Parte de la escena actual (terreno, muralla y marcadores MARKER_Bld_* ya existen). Guarda una nueva versión del .blend antes de empezar y crea las Collections: BLD_KIT, BLD_PORTAL, BLD_MERCADO, BLD_OFICIOS, BLD_CLASES, BLD_RAZAS, BLD_MORADAS, BLD_PROPS.

REFERENCIAS DEL KIT: Rothenburg ob der Tauber y Český Krumlov (casas de entramado, techos de teja, balcones y letreros colgantes), Grand-Place de Bruselas (fachadas altas de gremios), Toledo (muros de piedra y arcos). Copia proporciones, tipos de ventana, aleros y la sensación de ciudad remendada.

REGLAS PARA TODOS LOS EDIFICIOS:
- Solo exterior. Cada edificio con interior=true deja un Empty MARKER_<Nombre>_Door (en la puerta, eje +Y hacia afuera) y un cubo simple "<Nombre>_InteriorVolume" (sin render) del tamaño interior.
- Techo SIEMPRE en objeto aparte (sufijo _Roof) para que Godot lo oculte al entrar.
- Cada edificio se entrega como: <Nombre>_Body (unido, por material) + <Nombre>_Roof + <Nombre>_Props (objetos pequeños como cajones, letreros, farolillos, instanciables).
- Respeta el footprint y door_direction del marcador MARKER_Bld_<Nombre> (tolerancia ±0.2 m). Origen del edificio en el centro de su base, a la altura del terreno.
- Cámara ISOMÉTRICA: calcula con CAM_Iso qué lado queda más cerca de la cámara. Los edificios de ese lado no pasan de 2 plantas (≈7 m) salvo los hitos, para no tapar puertas ni NPC. En el resto, máx 3 plantas (≈10.5 m).
- Aspecto remendado: en cada edificio, 2 a 4 parches de piedra distinta (MAT_Stone_Repair), vigas de reemplazo, techo reparado con tejas de otro tono. Ningún edificio idéntico a otro: usa semilla por edificio.
- Materiales: solo los de Concordia (MAT_Limestone_Worn, MAT_Wood_Dark, MAT_Roof_Tile_Ocher, MAT_Iron_Black, MAT_Cloth_Patch A/B/C, MAT_Stone_Repair, MAT_Wall_Gray, MAT_Cobble_Concordia, MAT_Shard_Blue). UVs por proyección de caja en metros para que la textura sea continua entre piezas.
- Color mágico: SOLO azul pálido #8FD0FF (MAT_Shard_Blue, emisión 2.5). Fuego y luz de ventanas son luz natural cálida con emisión baja (1.0), no mágica. Cualquier humo coloreado o vapor lo hará Godot como efecto.
- Presupuestos: pieza pequeña ≤ 1.500 triángulos, media ≤ 5.000, grande ≤ 12.000. Hitos con presupuesto propio (se indica en su prompt). LOD1 (50%) y LOD2 (15%) para cada edificio.
- Un paso a la vez. Verifica con look en vista isométrica y a altura de personaje, y reporta triángulos reales.

KIT MODULAR (colección BLD_KIT, grilla 1 m, módulo de muro 3 m de ancho, piso 3.2 m de alto, zócalo de 0.6 m):
1. WALL_Solid_3m, WALL_Window_3m, WALL_Door_3m, WALL_Arch_3m, WALL_Barred_3m (ventana con rejas), WALL_Shutter_3m. Cada uno en 3 variantes: limpia, remendada con piedra y remendada con vigas. Máx 250 triángulos cada uno.
2. CORNER_Post (poste de esquina), TIMBER_Overlay (entramado de madera para superponer), BUTTRESS_Stone (contrafuerte).
3. FLOOR_Edge (cornisa de piso), ARCH_Span_3m y ARCH_Span_6m, STAIRS_Ext (escalera exterior de 1.2 m), BALCONY_Wood y BALCONY_Stone (1.5 m de saliente).
4. ROOF_Gable_Tile (pendiente 40°), ROOF_Hip, ROOF_Conical (radio parametrizado), ROOF_Flat_Parapet, ROOF_Lean_To. Cada uno con tejas ocres de 2 tonos, aleros de 0.4 m y reparaciones. Máx 400 triángulos por módulo de 3 m.
5. CHIMNEY_A y CHIMNEY_B (con y sin remate), DORMER_Window.
6. AWNING_Patch (toldo de tela remendada, 3 variantes de color A/B/C), SIGN_Hanging (letrero colgante con soporte de hierro), LANTERN_Shard (farolillo con esquirla azul, emisión 2.5, soporte de hierro), CRATE_Small, CRATE_Fruit, BARREL, TOOL_Rack.

BUILDING ASSEMBLER: crea un script reutilizable concordia_buildings.py con una función build_building(nombre, footprint, pisos, tipo_techo, estilo, seed) que apile los módulos del kit, genere body y roof por separado, una el body por material, aplique las reparaciones aleatorias por semilla y respete el marcador. Los edificios siguientes se construyen con ella (y con modelado a mano para los hitos).

Entrega: una captura de cada pieza del kit en una hoja ("kit sheet") y una casa de prueba ensamblada de 12x9 m con 2 pisos, vista isométrica y a altura de personaje.
```


### Mensaje 23 — 2026-11-05 20:59 — Modela el Portal de Concordia y sus elementos. Es el objeto más importante del juego: que 

```text
Modela el Portal de Concordia y sus elementos. Es el objeto más importante del juego: que se lea al instante desde la cámara isométrica.

REFERENCIAS: Stonehenge (trilito: dos postes enormes con un dintel, proporción de bloques y superficie erosionada), Porta Nigra de Tréveris (piedra oscura maciza y erosionada, ventanas y arcos pesados). Copia la masa, la pesadez y el desgaste. Las runas son inventadas, tallas simples.

1. PORTAL_Arch: arco de piedra gris de 12 m de alto sobre el pedestal circular existente (radio 6, +0.9 m, centro MARKER_Portal_Center). Dos pilares de 2.2 x 2.2 m y un dintel curvo; ancho libre interior 8 m. Superficie erosionada con grietas (sin pasarse de 12.000 triángulos). Runas talladas (3 cm de profundidad) en los pilares y el dintel; el relieve debe leerse a distancia, así que las runas grandes y simples. Líneas de runas con emisión azul #8FD0FF a 1.2 que bajan por los pilares hasta el suelo.
2. PORTAL_Veil: plano curvo en el centro del arco, de 8 m de ancho x 11 m de alto, material MAT_Portal_Veil (azul pálido, emisión 3.0, alpha 0.6). Con UVs en 0 a 1 para que Godot lo anime como agua ondulante. Objeto separado, sin colisión.
3. Siete piedras bajas con runas (0.8 m de alto, 0.6 m de diámetro), en los marcadores MARKER_Runestone_01 a 07 (radio 9, cada 51.4°). Bloques de piedra con forma de pequeño menhir, runa central emisiva a 1.0. Como la Piedra del Umbral del Piso 1.
4. Atrio de Descenso: sobre la plataforma de radio 15 (+0.6 m): anillo de 21 pedestales (1.2 m de diámetro, 0.5 m de alto) en los marcadores MARKER_Descent_Pedestal_01 a 21, cada uno con una placa plana de 0.8 m en la cara superior para los números de piso (la etiqueta la pone Godot). Borde de la plataforma con una línea de runas azules.
5. Colisión simple: "-colonly" de cilindro para pedestal y pilares; sin colisión en el hueco del arco.
Presupuestos: arco ≤ 12.000 tris (excepción de hito), piedras ≤ 400 cada una, pedestales ≤ 300 cada uno. LOD1/LOD2.

Entrega: vista isométrica del Portal con el velo, una a altura de personaje desde la avenida Norte, y un primer plano de las runas.
```


### Mensaje 24 — 2026-11-05 21:21 — Modela el Obelisco de los Pisos (base 5x5 m en MARKER_Obelisco, SO de la plaza, 25 m de al

```text
Modela el Obelisco de los Pisos (base 5x5 m en MARKER_Obelisco, SO de la plaza, 25 m de alto).

REFERENCIAS: Obelisco de Luxor en la Plaza de la Concordia (París): fuste de cuatro caras que se estrecha hacia arriba, remate piramidal, grabados en bajorrelieve; y Porta Nigra para el color oscuro y la textura. Copia la proporción y la silueta limpia.

1. Columna de piedra NEGRA (nuevo material MAT_Obelisk_Black, roughness 0.8, sin color saturado) de sección cuadrada: 3.0 m en la base, 1.8 m en la cima, con pyramidion de 2.5 m. Sobre un pedestal escalonado de 5x5 m, 1.5 m de alto. Total 25 m.
2. 100 marcas (una por piso): placas rectangulares hundidas de 0.3 x 0.5 m repartidas en las 4 caras (25 por cara, en 5 columnas x 5 filas, ordenadas del piso 1 abajo al piso 100 arriba, dando la vuelta de cara en cara). Cada marca es un objeto aparte OBELISK_Mark_001 a 100, con material MAT_Obelisk_Mark: apagado por defecto (gris oscuro) y con emisión azul #8FD0FF a 3.0 como variante para que Godot la encienda por instancia. Que el número de piso sea legible como un glifo simple tallado dentro de la marca.
3. Base con 4 escalones y una placa con una runa grande. Un anillo de 4 faroles de esquirla en la base.
4. Colisión: "-colonly" de caja. Presupuesto: ≤ 6.000 triángulos en total (sin contar las 100 marcas, que son ≤ 20 triángulos cada una).

Entrega: vista isométrica, vista de cerca de una cara con las marcas, y confirma que los 100 objetos están numerados.
```


### Mensaje 25 — 2026-11-05 21:36 — Modela la Torre del Faro (MARKER_Faro, NE de la plaza, base circular de 14 m de diámetro, 

```text
Modela la Torre del Faro (MARKER_Faro, NE de la plaza, base circular de 14 m de diámetro, 40 m de alto). Su luz azul es la referencia de toda la ciudad.

REFERENCIAS: Torre de Hércules (A Coruña): faro de piedra alto y sobrio sobre una colina; y Palazzo Pubblico de Siena (la torre esbelta con remate). Copia la sobriedad de la piedra, la verticalidad y el remate con galería.

1. Base: zócalo circular de 14 m de diámetro y 4 m de alto con contrafuertes. Fuste: sección cilíndrica que se estrecha de 11 m a 7 m en tres tramos con cornisas de piedra. Rampa/escalera exterior en espiral pegada al fuste (como la de la torre original), con barandilla, hasta la galería a 34 m. Puerta de entrada a nivel de calle.
2. Remate: galería abierta con parapeto y 8 columnas, y un cristal ENORME de esquirlas azules (racimo de prismas de 4 a 6 m de alto, material MAT_Shard_Blue, emisión 4.0). Objeto separado FARO_Crystal.
3. FARO_Beam: cilindro de 2 m de radio y 80 m de alto, abierto, material aditivo azul pálido con alpha 0.3, sobre el cristal. Objeto separado, sin colisión (Godot lo anima).
4. Canales de luz: 4 canales de 20 cm de ancho y 5 cm de profundidad bajan por el fuste en espiral y se conectan con los canales del suelo creados en la plaza (Prompt 3), con emisión azul 1.2.
5. Tubos de luz: pieza PIPE_Light_Straight, PIPE_Light_Elbow y PIPE_Light_Support (tubo de 0.4 m de diámetro con vidrio y emisión azul 1.5, soportes de hierro). Crea la curva CRV_LightPipe_Tesoreria_Faro desde el techo de la Tesorería (MARKER_Bld_Tesoreria) hasta la base del Faro, pasando por encima de las calles a 9 m de altura con soportes cada 8 m. No coloques los tubos todavía, solo la curva y las piezas.
6. Colisión "-colonly" de cilindro; presupuesto ≤ 20.000 triángulos (excepción de hito).

Verifica con rayo desde cada calle principal que la cima del Faro es visible. Entrega: vista isométrica y primer plano de la galería con el cristal.
```


### Mensaje 26 — 2026-11-05 22:07 — Modela los dos edificios de los hitos NO y SE.

```text
Modela los dos edificios de los hitos NO y SE.

--- SANTUARIO DEL RETORNO (MARKER_Santuario, pad 16x12 m) ---
REFERENCIAS: Sainte-Chapelle de París (capilla pequeña con enormes ventanales verticales de vitral, contrafuertes finos y techo muy inclinado). Copia la proporción esbelta, los ventanales y el remate con flecha.
- Capilla de piedra CLARA (caliza más clara que el resto, MAT_Limestone_Worn con tinte más claro), 16x12 m, nave de 9 m de alto a los hombros y cubierta a dos aguas empinada de teja ocre desgastada (cumbrera a 14 m), con una pequeña flecha en el extremo.
- 5 ventanales altos por lado (1.4 x 6 m), con vitrales azules (vidrio azul pálido con emisión baja 0.6 y tracería de piedra). Contrafuertes entre ventanas. Puerta de doble hoja de madera oscura con herrajes. Interior=true: Empty MARKER_Santuario_Door y InteriorVolume.
- Exterior: pozo pequeño de 2 m de diámetro como en el interior (modelo aparte SANTUARIO_Well, para colocarse luego dentro), farolillos de esquirla en la entrada.
- Presupuesto ≤ 8.000 triángulos.

--- SALÓN DE LAS HAZAÑAS (MARKER_SalonHazanas, pad 42x16 m) ---
REFERENCIAS: Westminster Hall (Londres): nave larga con techo de vigas monumental (hammerbeam), muros altos con contrafuertes y gran ventanal frontal. Copia la longitud, la cubierta de vigas visible desde fuera por los aleros y el aire solemne.
- Nave larga de piedra, 42x16 m, muros de 8 m de alto y cubierta a dos aguas (cumbrera a 15 m). Muros laterales con contrafuertes cada 6 m y 6 ventanas altas por lado. Fachada principal en el extremo corto con gran portal en arco y un ventanal alto sobre él.
- Exterior: 10 nichos con estatuas de piedra sin rostro (siluetas) en la fachada y laterales, y placas de bronce junto a la puerta. Los nichos de los jefes y los nombres grabados van en el interior (después).
- Interior=true: Empty MARKER_SalonHazanas_Door e InteriorVolume.
- Presupuesto ≤ 14.000 triángulos (excepción de hito).

Colisión "-colonly" de caja para ambos. Techo en objeto aparte. Entrega: vista isométrica y a altura de personaje de cada uno.
```


### Mensaje 27 — 2026-11-05 22:50 — Decisiones sobre el Faro (E3) y las pendientes:

```text
Decisiones sobre el Faro (E3) y las pendientes:

1. Marcador de la Tesorería: APROBADO. En todos los prompts de edificios, si el nombre del marcador difiere del que escribí, usa el nombre real del archivo (MARKER_Bld_TesoreriaMuralla). Deja el primer punto de CRV_LightPipe_Tesoreria_Faro con la propiedad provisional=true. Cuando modeles la Tesorería (E5), su salida de tubos en el techo debe quedar a 9.6 m (±0.5 m) y entonces ajustas ese punto a la salida real.

2. Última vuelta de la rampa separada 1.4 m con ménsulas (de +29.5 a +32): APROBADO, con tres condiciones. Las ménsulas deben verse estructurales (cartelas de piedra), la barandilla debe ser continua, y la rampa es DECORATIVA: sin navegación y sin colisión por encima de los 3 m de altura (solo el cilindro de la torre y el arranque de la rampa).

3. Materiales nuevos (MAT_Shard_Blue_E40, MAT_Faro_Beam, MAT_Pipe_Glass, MAT_Pipe_Light_Core): APROBADOS. MAT_Shard_Blue_E40 debe derivar de MAT_Shard_Blue (mismo color #8FD0FF, solo cambia la emisión a 4.0). Registra los valores de emisión y alpha en README_buildings.txt. Aplica esta misma aprobación a los materiales nuevos del kit de edificios y del Portal, siempre que respeten la paleta (nada saturado fuera del azul pálido), exporten con Image Texture → Principled BSDF (o valores planos) y la memoria total de texturas de la ciudad quede ≤ 220 MB. Si lo superas, avísame antes de seguir.

4. Haz aditivo: crea un archivo TODO_GODOT.txt y anota ahí todo lo que haya que hacer en Godot y que el glTF no guarda (FARO_Beam con blend_mode=add, animación de PORTAL_Veil, encendido de OBELISK_Mark_xxx, WATERWHEEL, etc.). Actualízalo en cada etapa.

5. Zócalo de 14 m sobre la plataforma: APROBADO. Comprueba que los 4 canales del suelo (Prompt 3) y los 4 de la torre coinciden en el arranque con una tolerancia de 5 cm. Si no coinciden, ajusta los de la torre, no el terreno.

PENDIENTES DE ETAPAS ANTERIORES:

A. Arco del Portal que sobresale 0.3 m del pedestal: ajusta el ARCO, no el terreno. Cambia a pilares de 2.0 x 2.0 m y un ancho libre de 7.8 m (velo de 7.8 x 11). Comprueba que todas las esquinas de los pilares quedan a radio ≤ 6.0 m del centro. Si ya lo resolviste de otra manera que deje todo dentro del pedestal, dime cómo.

B. Regla de alturas del kit de edificios: sustitúyela por esta, más clara. La regla manda la prueba de visibilidad desde CAM_Iso, no la altura por lado. Un edificio puede tener hasta 3 plantas (10.5 m); la torre de Alquimia puede tener 4. Si un edificio tapa la puerta de otro o un carril de NPC desde la cámara, baja su altura hasta que deje de taparla (2 plantas, 7 m como mínimo). Los hitos (Portal, Faro, Obelisco, Santuario, Salón de las Hazañas) quedan fuera de la regla.

C. Puente 01 sobre la escalinata de la Morada NE: la escalinata tiene prioridad. Si es un ARCO con al menos 5 m libres sobre los peldaños, déjalo (como en Malá Strana). Si es un puente con calzada, mueve el marcador a la posición libre más cercana (máx 15 m) y dime dónde.

D. Manchas de material en el LOD2: pruébalo con CAM_Iso a escala 120 y a 45. Si no se nota en esas escalas, acéptalo. Si se nota, usa para el LOD2 un solo material de color plano por edificio (el color promedio del LOD0), porque solo se ve de lejos.

E. Git LFS: SÍ, para los .glb, .png y .exr. Pero no subas cada versión del .blend: guarda solo el concordia_master.blend más reciente en el repositorio y deja las versiones anteriores (v01...) en una carpeta local de respaldo fuera del repo. Así no se agota el almacenamiento. Dime cuánto pesan hoy el .blend y las exportaciones antes de configurarlo.

Cuando termines, repíteme: la verificación de visibilidad del Faro desde las 8 calles, el estado de los materiales nuevos, y confirma que no hay nada pendiente del E3. Después seguimos con E4 (Santuario y Salón de las Hazañas).
```


### Mensaje 28 — 2026-11-06 20:12 — Inténtalo de nuevo

```text
Inténtalo de nuevo
```


### Mensaje 29 — 2026-11-06 20:24 — Modela los edificios del Mercado en sus parcelas MARKER_Bld_*. Usa build_building del kit 

```text
Modela los edificios del Mercado en sus parcelas MARKER_Bld_*. Usa build_building del kit y modelado a mano en los elementos singulares.

REFERENCIAS GENERALES: Rothenburg ob der Tauber y Český Krumlov (casas de entramado, adoquín, toldos), Grand-Place de Bruselas (fachadas altas y ornamentadas).

1. TESORERÍA DE LA MURALLA (28x18, interior=true). REFERENCIA: Palazzo Pubblico de Siena (edificio macizo con arcadas y torre). Piedra, arcada frontal de 7 arcos con columnas, balanzas de bronce grandes en la fachada (balanzas de 1.2 m de alto, material MAT_Bronze_Worn). 2 plantas con torre pequeña de reloj. En el techo, 4 salidas para los tubos de luz azul (PIPE_Light) hacia el Faro. Dentro, vitrinas (después). ≤ 8.000 triángulos.
2. BANCO DE CONCORDIA (24x20, interior=true). REFERENCIA: Palazzo Pubblico de Siena (volumen macizo) y Porta Nigra (bloques pesados). Edificio macizo de piedra clara de 2 plantas, ventanas con rejas (WALL_Barred), puerta de hierro negro con un candado enorme de 1 m, pocas ventanas. Muy sólido, sin balcones. ≤ 6.000.
3. GRAN SUBASTA (40x16, interior=false: pabellón abierto). REFERENCIA: mercado medieval de madera cubierto (halles de entramado con tejado sostenido por pilares de madera, en la imagen del pueblo francés y el Market Hall de Titchfield). Pabellón largo abierto, 2 galerías laterales a 3.5 m, tarima central de 5x3 m con campana de remate (BELL de 1.2 m en un soporte de madera), 6 tableros de madera para precios. ≤ 7.000.
4. POSADA DE CONCORDIA (20x16, interior=true). REFERENCIA: Český Krumlov y Rothenburg. 3 plantas con entramado de madera, chimenea enorme, letrero con una vela encendida (SIGN_Hanging con una vela de emisión cálida 1.0), aleros que sobresalen, balcones. En la entrada, el Tablón de Grupos (tablero de madera de 3 x 2 m con ganchos, objeto aparte). ≤ 6.500.
5. PLAZA DE PROVISIONES: 14 puestos de 3x3 m (STALL_A a STALL_E, 5 variantes) con toldos de tela remendada (A/B/C), cajones de fruta, herramientas colgadas. Instanciables. Puesto ≤ 500 triángulos.
6. FUENTE DEL MERCADO (plaza de 22 m de diámetro): fuente circular de piedra de 6 m de diámetro, 4 caños, 8 bancos de piedra en círculo, y un rebosadero que arranca el Cauce hacia el Este. ≤ 3.000.
7. CASA DEL REGISTRO (14x12, interior=true): oficina de piedra y madera con tablones de avisos y un letrero de libro. ≤ 3.000.

Edificios de más de 2 plantas: respetan la regla de cámara del E0. Entrega: vista isométrica del distrito completo y primer plano de la Tesorería, la Posada y la Gran Subasta.
```


### Mensaje 30 — 2026-11-06 21:05 — Modela los gremios, talleres y edificios especiales del distrito Este (parcelas MARKER_Bld

```text
Modela los gremios, talleres y edificios especiales del distrito Este (parcelas MARKER_Bld_*). Cada uno debe reconocerse por la silueta desde la cámara isométrica.

REFERENCIAS GENERALES: Grand-Place de Bruselas (fachadas de gremios con emblema), Toledo (forjas de piedra), molino de agua histórico (rueda y obra de piedra).

GREMIOS DE RECOLECCIÓN:
1. Gremio de Mineros (18x14): fachada de piedra que imita una bocamina, vagonetas (2) con rieles en la puerta, pico gigante de 3 m colgado sobre la puerta (emblema dorado MAT_Bronze_Worn). ≤ 5.000.
2. Gremio de Herbolarios (22x12): invernadero de vidrio y madera (vidrio translúcido, alpha 0.35) con jardines de hierbas en terrazas pequeñas alrededor. Vegetación en tonos verdes APAGADOS. ≤ 6.000.
3. Gremio de Cazadores (20x14 + campo de tiro 20x10): casa con cornamentas, pieles secándose en bastidores, 6 blancos de tiro en el campo. ≤ 5.000.
4. Gremio de Pescadores (18x14, junto al Cauce): casa con redes colgadas, barcas (2 de 4 m), muelle de 8x3 m. ≤ 5.000.

TALLERES (16x12 salvo indicación):
5. La Gran Forja (26x16, interior=true). REFERENCIA: forja y yunque (fuego, yunques, chimenea) y herrerías de Toledo. Edificio ancho de piedra con chimenea alta de 14 m, fundición al aire libre con crisol, 3 yunques, luz naranja cálida de las brasas (emisión 1.5 natural) y espacio para vapor (Godot). ≤ 8.000.
6. Curtiduría: 4 tinas de curtido de madera, bastidores con pieles estiradas, casa de 2 plantas. ≤ 5.000.
7. Sastrería: 2 plantas con balcones de los que cuelgan telas (MAT_Cloth_Patch A/B/C), telares visibles en una planta abierta. ≤ 5.000.
8. Carpintería: vigas expuestas y una rueda hidráulica de 3.5 m de diámetro en el costado, junto al Cauce (referencia: molino de agua histórico), con sierra y troncos apilados. Rueda separada (WATERWHEEL) para animarla. ≤ 6.000.
9. Alquimia: torre estrecha de 4 plantas con alambiques de vidrio en los balcones, chimeneas y ventanas redondas. El humo coloreado lo pone Godot. ≤ 5.000.
10. Hornos de Concordia: horno comunal grande con chimenea, mesas largas bajo un cobertizo abierto. ≤ 4.000.
11. Joyería y Tallado (pequeño, 10x10): edificio luminoso con grandes escaparates, lupas de bronce en las ventanas y un farolillo de esquirla. ≤ 3.000.

EDIFICIOS ESPECIALES:
12. Crisol de las Piedras (círculo de 22 m de diámetro, interior=true). REFERENCIA: Mina de sal de Wieliczka (salas abovedadas con cristales y luz cálida). Edificio circular de piedra y cristal con un óculo en el centro del techo (3 m de diámetro) por donde sube la luz azul. Un cuenco de metal fundido (ø 4 m) en el centro visible por las ventanas altas; piedras flotantes sobre el cuenco (objetos aparte CRISOL_FloatStone, esquirlas pequeñas azules). ≤ 9.000.
13. Casa de Reparaciones (16x10): taller abierto con yunque, pared de herramientas (TOOL_Rack) y un banco largo de madera. ≤ 3.500.

Entrega: vista isométrica del distrito, y de cada edificio con su rasgo distintivo.
```


### Mensaje 31 — 2026-11-06 22:14 — Modela el distrito de las Clases con plantillas ajustables (N_CLASES = 8, parámetro).

```text
Modela el distrito de las Clases con plantillas ajustables (N_CLASES = 8, parámetro).

REFERENCIAS: Grand-Place de Bruselas (fachadas sobrias con emblema), Toledo (piedra, pórticos y teja ocre). Copia la sobriedad de los pórticos y la lectura del estandarte.

1. SALÓN DE CLASE (plantilla 18x14, interior=true, uno por clase en abanico alrededor de la Plaza de las Armas): arquitectura sobria común (piedra, pórtico de 4 columnas, techo de teja) con estas partes ajustables por clase:
   - Estandarte grande (banner de 2.5 x 6 m, plano con UVs para el emblema; textura por clase), color tierra apagado por clase (no saturado).
   - Slots de props propios: soporte para 2 a 3 objetos de clase (libros, armas, símbolos) a la entrada. Deja Empties MARKER_ClassProp_Slot_xx.
   - Cada preset de clase cambia el color del estandarte, la forma de un remate sobre el frontón y uno o dos objetos del pórtico (2 a 3 modelos de props por clase). Entrega la plantilla y los 8 presets con nombres genéricos (CLASE_01 a 08) listos para renombrar.
   - ≤ 5.000 triángulos por salón.
2. PLAZA DE LAS ARMAS (50x40): suelo de tierra apisonada y adoquín (ya en el terreno). Props: 12 maniquíes de paja y madera (DUMMY_Straw, 3 variantes, ≤ 600 triángulos), 10 blancos de tiro, 8 postes de prueba, y una valla baja de madera alrededor. Los maniquíes no atacan: son props estáticos con un Empty en el pecho (MARKER_DamageNumber).
3. LA CASA DE REPOSICIÓN "EL REMIENDO" (24x12, interior=true): tienda larga de piedra y madera con perchas de armaduras remendadas en la fachada, espadas viejas pulidas colgadas, cajones de botas y capas. Letrero SIGN_Hanging con un parche cosido. ≤ 5.000.

Entrega: vista isométrica del distrito y primer plano de un salón y de la Casa de Reposición.
```


### Mensaje 32 — 2026-11-06 22:26 — Modela los barrios de las razas con presets ajustables (N_RAZAS = 6, plantilla).

```text
Modela los barrios de las razas con presets ajustables (N_RAZAS = 6, plantilla).

REFERENCIAS: Malá Strana de Praga (calles estrechas con arcos y escalinatas entre barrios), Český Krumlov y Rothenburg (casas apretadas con techos de distintas formas), Toledo (muros y arcos).

Cada barrio (unos 35x35) tiene:
- 1 CASA DE LA RAZA (20x16, interior=true): la más grande del barrio, con la bandera y el símbolo de la raza (banner con UVs para el símbolo) en la fachada. Es donde aparecen los personajes nuevos de esa raza (Empty MARKER_RaceSpawn_xx frente a la puerta).
- 6 a 10 CASAS (8x8 a 12x10), construidas con el assembler, con puertas, materiales, techos y colores propios del barrio.
- 1 PLAZUELA (10 m de diámetro) con una fuente pequeña o un árbol viejo de hojas verdes apagadas, y 4 bancos.

PRESETS (plantillas; cámbialos cuando llegue la lista de razas): diccionario RACE_PRESETS con material dominante, forma de techo, escala de puerta y paleta:
- R01: piedra, techo a dos aguas, puerta 1.0.
- R02: madera clara, techo a cuatro aguas, puerta 1.0.
- R03: madera oscura, techo muy inclinado, puerta 0.9.
- R04: piedra y cristal (vidrio azul pálido translúcido con emisión baja), techo cónico, puerta 1.1.
- R05: pieles y madera (telas y cueros), techo circular tipo yurta, puerta 1.3.
- R06: mixto piedra y madera, techo plano con parapeto, puerta 0.8.
Si una raza es de talla muy distinta, escala también escalones y alturas de umbral con el parámetro DOOR_SCALE. En la vista isométrica los barrios deben distinguirse a simple vista por silueta de techo y color dominante (tonos tierra, nada saturado).
Presupuesto: Casa de Raza ≤ 6.000 triángulos, casa del barrio ≤ 2.500 (4.000 las de 3 plantas).

Entrega: vista isométrica de cada barrio y una comparación de los 6 barrios lado a lado.
```


### Mensaje 33 — 2026-11-07 12:00 — Modela las conexiones entre barrios y sobre el Cauce, en los marcadores MARKER_Bridge_xx y

```text
Modela las conexiones entre barrios y sobre el Cauce, en los marcadores MARKER_Bridge_xx y las escalinatas de los Prompts 2 a 7.

REFERENCIAS: Canales de Brujas (puentes de piedra de arco bajo sobre canal estrecho), Malá Strana de Praga (arcos sobre calles y escalinatas), Toledo (arcos de piedra).

1. BRIDGE_Stone_5m y BRIDGE_Stone_6m: puente de piedra de arco rebajado, calzada elevada 0.4 m sobre las calles, pretiles de 0.9 m, estribos con sillares. Variantes con remiendos de piedra distinta. ≤ 1.800 triángulos.
2. ARCH_Street_4m, ARCH_Street_5m, ARCH_Street_6m: arco de piedra que cruza una calle uniendo edificios de dos barrios, con 5 m de altura libre y una pequeña linterna de esquirla en la clave. ≤ 1.200.
3. STAIRS_Monumental (r 95 a 105 de las diagonales): escalinata de 6 m de ancho con 10 peldaños de 15 cm de contrahuella y 1.0 m de huella, descanso de 2 m y pasamanos de piedra de 0.9 m. Como el Prompt 2.
4. STAIRS_Terrace: escalera de 2.5 m de ancho para las terrazas de las Moradas (acompaña a los muros de contención de los bordes laterales).
5. Barandillas y pretiles de piedra baja instanciables (RAIL_Stone_3m).

Cada pieza lleva marcador de colocación con rotación correcta y colisión simple ("-colonly") plana y continua para que los jugadores crucen. Entrega: un puente y un arco colocados en la escena, con vista isométrica y a altura de personaje.
```


### Mensaje 34 — 2026-11-07 13:57 — Modela las viviendas de las 4 Moradas (parcelas de 6x10 m en los marcadores MARKER_Morada_

```text
Modela las viviendas de las 4 Moradas (parcelas de 6x10 m en los marcadores MARKER_Morada_xx, 6 terrazas por conjunto).

REFERENCIAS: Český Krumlov y Toledo (casas apretadas y escalonadas), Mont-Saint-Michel (casas pegadas a un muro en pendiente), Malá Strana (escaleras y arcos entre niveles).

TIPOS (según la propiedad tipo del marcador):
1. HABITACIÓN (parcela 6x10, 50%): fachada de casa comunal de 3 plantas con varias puertas (3 por planta), balcones corridos de madera y una escalera exterior. Cada módulo de 6 m es una unidad. ≤ 1.500 triángulos por módulo.
2. CASA PEQUEÑA (35%): una planta con patio y muro bajo, techo a una agua o dos aguas, chimenea. ≤ 2.000.
3. CASA GRANDE (15%): dos plantas con jardín y muro, balcón, chimenea y techo a dos aguas. ≤ 3.500.

PERSONALIZACIÓN: la puerta exterior es un objeto separado DOOR_Morada con: color de pintura (material con texture por instancia), un soporte para farol (Empty MARKER_Lantern, farol LANTERN_Shard) y una placa de número (plano de 0.3 x 0.2 m para decal). Dejar los 3 elementos parametrizables en Godot.
Cada casa tiene una vitrina de trofeos: solo marca el Empty MARKER_TrophyCase en el interior (no modelar interior).

REGLAS ESPECIALES:
- Techos escalonados contra el muro de la muralla, sin tapar las puertas de la terraza inferior desde CAM_Iso (comprueba una captura isométrica de cada conjunto).
- 4 variantes por tipo (semilla) y 3 variantes de color de fachada en tonos tierra, para que ninguna terraza se vea repetida.
- Instancias en cada conjunto: unas 100 casas visibles. LOD1 al 50% y LOD2 al 10%, con LOD2 de casi caja con techo. Cada conjunto se exporta aparte (moradas_NE.glb, _NO, _SE, _SO).
- Interior: cada puerta se abre a un interior propio (se carga aparte), así que solo deja MARKER_Morada_Door.

Entrega: una terraza completa con 17 casas variadas en vista isométrica y a altura de personaje, y el conteo de triángulos por conjunto (medido) con LOD0 y LOD2.
```


### Mensaje 35 — 2026-11-07 15:11 — Prepara todos los edificios para Godot 4 y verifica.

```text
Prepara todos los edificios para Godot 4 y verifica.

1. Limpieza: elimina duplicados, caras ocultas y normales invertidas; transformaciones aplicadas; origen en el centro de la base de cada edificio.
2. Cada edificio exporta: <Nombre>_Body, <Nombre>_Roof (objeto separado para ocultarlo al entrar), <Nombre>_Props, y colisión "<Nombre>-colonly" simple (cajas o convexo, sin detalles de ventanas). Edificios con interior=true llevan MARKER_<Nombre>_Door y <Nombre>_InteriorVolume.
3. LOD0 / LOD1 (50%) / LOD2 (15%), con el LOD2 de los edificios de las Moradas como caja con techo.
4. Presupuesto: reporta triángulos reales por edificio y por distrito. Total de la ciudad en LOD0 y en LOD2.
5. Materiales: solo los de Concordia; sin nodos que no exporten a glTF (solo Image Texture → Principled BSDF). Las emisiones se exportan como EMISSIVE. Dejar un archivo README_buildings.txt con: lista de materiales, valores de emisión y objetos animables (PORTAL_Veil, FARO_Beam, WATERWHEEL, OBELISK_Mark_xxx, CRISOL_FloatStone, banners).
6. Exporta glTF 2.0 (.glb), +Y Up: bld_portal.glb, bld_mercado.glb, bld_oficios.glb, bld_clases.glb, bld_razas.glb, bld_moradas_[NE,NO,SE,SO].glb, bld_kit.glb, bld_props.glb.
7. Navegación: confirma que las plazas, puertas y escalinatas siguen transitables y que ningún edificio invade la malla de navegación.

VERIFICACIÓN con CAM_Iso:
- Cada puerta de los edificios con interior=true es visible (sin ser tapada por otro edificio) desde la cámara. Si hay una tapada, reporta y propón un ajuste.
- Todos respetan su footprint (±0.2 m).
- Ningún edificio idéntico a otro (comprueba la semilla).
- Nada con color mágico fuera del azul #8FD0FF.
- 8 capturas: Portal, Mercado, Oficios, Clases, Razas, una Morada, la ciudad completa en isométrica y a altura de personaje.
Reporta cada problema con su corrección y guarda la versión final.
```


### Mensaje 36 — 2026-11-07 15:57 — Decisiones sobre las pendientes:

```text
Decisiones sobre las pendientes:

1. MAT_Embers (excepción de saturación): APROBADA, con límites. El fuego y las brasas son luz natural, no mágica, así que la excepción es válida. Condiciones:
   - Solo para brasas, fundición y hornos: Gran Forja (fundición), Hornos de Concordia, y el interior visible de chimeneas de Posada y Forja.
   - Emisión máxima 1.5. Nunca azul ni mezclado con MAT_Shard_Blue.
   - Ocupa menos del 2% de la superficie visible de cada edificio.
   - Ningún otro material usa naranja saturado. Los toldos, telas y banderas siguen en tonos tierra apagados.
   - Anótalo en README_buildings.txt como ÚNICA excepción cálida a la paleta, y haz que el chequeo de paleta (verificación) la ignore solo para ese material.

2. Parcela de los Cazadores: no puede quedar fuera de la ciudad, porque nada existe más allá de la muralla.
   - Si lo que pasa es que construiste el edificio aparte de su parcela (en un glb suelto o en otra zona de la escena), colócalo en MARKER_Bld_Cazadores y únelo a bld_oficios.glb.
   - Si la parcela real (edificio 20x14 + campo de tiro 20x10) no cabe en el sector Este (±25°, radio 60 a 185 m), este es el orden de ajuste: (a) busca la parcela libre más cercana dentro del sector; (b) si no cabe, reduce el campo de tiro a 14x8 m y alinéalo paralelo al anillo interior de la muralla (r 165 a 185, terraza plana a +4.5), con valla baja de madera de 1.2 m; (c) si aún no cabe, deja el campo de tiro en 12x6 m con 4 blancos. En ningún caso fuera de la muralla. Reporta qué opción usaste.

3. Parcelas que faltan en las Razas: completa los 6 barrios con lo mínimo de cada uno (1 Casa de Raza + mínimo 6 casas + 1 plazuela). Hazlo así, en orden:
   - Primero, reduce la huella de las casas hasta 8x8 m y sube a 3 plantas en vez de ampliar el terreno.
   - Segundo, reduce el barrio de 35x35 a 32x32.
   - Tercero, aprovecha los lados de los anillos de calle (r=100 y r=150) del sector Sur.
   - Nunca coloques parcelas sobre calles, escalinatas, puentes ni fuera del sector Sur (±25°, r 60 a 185). Si con todo esto algún barrio queda por debajo del mínimo, dime exactamente cuántas parcelas faltan y en cuál barrio, no inventes espacio.
   Respeta la regla de visibilidad del Faro (punto 5) al subir a 3 plantas.

4. Push forzado de LFS: NO fuerces el push todavía.
   - Primero diagnostica por qué se rechaza (git fetch, git status, git lfs ls-files, git lfs env) y dime el error exacto, el tamaño del repositorio y el espacio de LFS que usas.
   - Si el remoto solo tiene versiones anteriores de este mismo proyecto (sin trabajo de otras personas), entonces sí: haz un respaldo (git tag respaldo-antes-de-forzar y un clon de seguridad del remoto en una carpeta aparte) y usa git push --force-with-lease, no --force.
   - Si el remoto tiene commits que no reconoces, detente y pregúntame.
   - Avísame si el almacenamiento de LFS se acerca al límite de tu plan, porque el .blend y las texturas pesan mucho.

5. Edificios que tapan el Faro: la visibilidad del Faro manda sobre la altura de los edificios normales. Los hitos (Portal, Faro, Obelisco, Santuario, Salón de las Hazañas) y las puertas de la muralla no se tocan.
   - Criterio: desde puntos de calle a altura de ojos (1.7 m) cada 10 m a lo largo de las 4 avenidas, las 4 calles diagonales y los 2 anillos, debe verse la galería superior del Faro (los últimos 6 m de la torre y el cristal). Las avenidas, diagonales y anillos deben cumplirlo al 100%; en los callejones secundarios acepto hasta un 10% de puntos bloqueados.
   - Para cada edificio que bloquee, aplica en este orden hasta que deje de bloquear: (a) baja a 2 plantas (7 m); (b) cambia el techo a una forma más baja (a una agua o plano con parapeto); (c) baja a 1 planta y media (5.5 m); (d) si aun así bloquea y es un edificio de servicio, avísame, no lo borres.
   - Edificios con servicios (Banco, Tesorería, gremios, salones, Casa de Raza) se bajan solo si no hay otra opción; los de decoración se bajan primero.
   - Entrégame una tabla con edificio, altura antes y después, y qué calles estaba tapando. Verifica de nuevo con rayos y reporta el porcentaje final de puntos con visibilidad, por tipo de calle.

6. Los dos ajustes que no te contesté: reenvíamelos con tu recomendación y espera mi decisión. No los apliques todavía.

Cuando termines, actualiza TODO_GODOT.txt y README_buildings.txt y dime si queda algo abierto del Mercado (E5) o de los Oficios (E6).
```


### Mensaje 37 — 2026-11-07 16:43 — Haz un balance del estado de los EDIFICIOS de Concordia, sin modificar nada. Para cada eta

```text
Haz un balance del estado de los EDIFICIOS de Concordia, sin modificar nada. Para cada etapa responde: HECHA / PARCIAL / NO EMPEZADA, con el número de edificios hechos sobre los esperados y los problemas abiertos.

E0 Kit modular y assembler
E1 Portal y Atrio (arco, velo, 7 piedras, 21 pedestales)
E2 Obelisco (columna y 100 marcas)
E3 Torre del Faro (torre, cristal, haz, tubos)
E4 Santuario del Retorno y Salón de las Hazañas
E5 Mercado (Tesorería, Banco, Gran Subasta, Posada, 14 puestos, Fuente, Casa del Registro)
E6 Oficios (4 gremios, 7 talleres, Crisol, Casa de Reparaciones)
E7 Clases (8 salones plantilla, Plaza de las Armas con props, Casa de Reposición)
E8 Razas (6 barrios: Casa de Raza, 6 a 10 casas, plazuela)
E9 Puentes, arcos y escalinatas (kit y colocación)
E10 Moradas (4 conjuntos, unas 100 casas por conjunto, puertas personalizables)
E11 Exportación a Godot y verificación final

Añade: triángulos totales de la ciudad en LOD0 y LOD2, memoria total de texturas en MB, y la lista de decisiones que sigan abiertas esperando mi respuesta. Termina con cuál es la siguiente etapa que recomiendas y por qué.
```


### Mensaje 38 — 2026-11-08 12:32 — Decisiones sobre el balance (numeración de tu informe):

```text
Decisiones sobre el balance (numeración de tu informe):

1. FARO. Cambio el criterio, no bajo más edificios de servicio.
   - La Posada (3 plantas por diseño), la Gran Subasta, la Sastrería y los demás edificios de servicio NO se bajan. Los edificios de decoración que ya hayas bajado se quedan como están.
   - Nuevo criterio, para una cámara isométrica: desde cada punto de calle (altura de ojos 1.7 m, cada 10 m en avenidas, diagonales, anillos y callejones), lanza rayos a 10 puntos del haz FARO_Beam (entre 60 y 120 m de altura, equiespaciados) y al cristal. El punto de calle cuenta como "con Faro" si al menos 1 de los 11 rayos llega sin obstáculos. Objetivo: 100% en avenidas, diagonales y anillos; ≥ 90% en callejones. Reporta el porcentaje por tipo de calle con este criterio, y también cuántos puntos ven el cristal directamente.
   - Si algún tipo de calle queda por debajo del objetivo, baja SOLO edificios de decoración que bloqueen el haz, empezando por los que bloqueen más puntos (2 plantas mínimo, 7 m). Muéstrame la tabla antes de aplicar.
   - En Godot (anótalo en TODO_GODOT.txt): FARO_Crystal y FARO_Beam se dibujan con depth test desactivado o con un pase de silueta por encima de los edificios, y un indicador en pantalla (brújula) apunta al Faro cuando está fuera de la vista. Los hitos (Obelisco, Salón, Santuario) y las puertas de la muralla no se tocan.

2. MORADAS NE y SO (53 puertas tapadas): APROBADO. Sustituye las galerías corridas por UN balcón por puerta y lleva la escalera al extremo más alejado de la cámara. Condiciones: respeta la regla de que ninguna puerta quede tapada (verifica con CAM_Iso), mantén el presupuesto por vivienda, no cambies footprint ni altura total, y que el aspecto remendado se conserve. Repite la verificación de puertas de las 4 Moradas.

3. RAZ_B02_Casa_04: APROBADO. Déjala en 1 planta (no la retrases).

4. CAMPO DE TIRO DE CAZADORES: APROBADO. Entrada por el extremo norte, camino de 8 x 2 m hasta la calle más cercana (mínimo 2 m de ancho libre, sin cruzar parcelas ni escalinatas, con adoquín o tierra apisonada), una apertura en la valla de 2 m con portillo, y el campo y el camino dentro de la malla de navegación. Comprueba que un punto de navegación del campo se conecta con la red de calles.

5. RAZAS (11 parcelas que faltan): PERMITIDO esto, que antes estaba prohibido, SOLO dentro del sector Sur (±25°, r 60 a 185) y sin tocar otros sectores:
   a) Recolocar los edificios de Razas dentro del sector Sur para compactarlos.
   b) Dividir parcelas de 8x8 m en 2 casas adosadas (4x8 m cada una, con su puerta, hasta 3 plantas, techos y colores distintos).
   c) Usar ambos lados de los anillos de calle de r=100 y r=150.
   Metas: 6 casas mínimo por barrio. Si no se alcanza, acepta 5 como mínimo y dime cuáles. Se mantiene lo prohibido: parcelas sobre calles, escalinatas o puentes; Casa de Raza y plazuela por barrio; respetar visibilidad de puertas. Como el número de razas es provisional (N_RAZAS=6), no inviertas más tiempo que esto; cuando llegue la lista real se rehace.

6. NÚMERO DE MORADAS: ACEPTADO. 283 edificios con 1.404 viviendas con puerta propia cumple "unas 100 moradas por conjunto, ampliables" (la unidad es la vivienda). No añadas más. Sí reporta triángulos por conjunto (NE, NO, SE, SO) en LOD0 y LOD2 y confirma que los 4 están dentro del presupuesto de la etapa 10.

7. SALÓN DE LAS HAZAÑAS (241 m² de plaza tapados): se resuelve en Godot. En Blender: marca el cuerpo y el techo con occludes_iso=true y confirma que sus materiales admiten fade por dithering. No cambies la geometría. Anótalo en TODO_GODOT.txt. El pozo del Santuario se queda provisional hasta la etapa de interiores (déjalo marcado como provisional=true).

8. TUBOS DE LUZ DEL FARO: colócalos AHORA. Primero ajusta el primer punto de CRV_LightPipe_Tesoreria_Faro a la salida real del techo de la Tesorería (quita provisional=true). Luego coloca los tramos (recto, codo y soporte) a lo largo de la curva de 117 m, con un soporte cada 8 m. Condiciones: separación mínima de 1 m sobre techos y chimeneas, que no choquen con edificios ni con el Faro, y que NO bloqueen más puntos del haz (repite la medición del punto 1). Si hay colisiones, sube la curva hasta 14 m. Material emisivo azul (MAT_Pipe_Light_Core), presupuesto ≤ 8.000 triángulos en total.

9. GRAN SUBASTA: CONFIRMADO pabellón abierto, sin interior. Cambia su marcador a interior=false y quita el InteriorVolume si existe. Se opera desde la tarima con el Subastador.

10. REPOSITORIO: acepto tu recomendación, NO migres a LFS.
   - En git: scripts (.py), README_*.txt, TODO_GODOT.txt, ASSETS_LICENSES.md, polyhaven.json, listas de marcadores (JSON) y el proyecto de Godot si es texto.
   - Fuera de git: .blend, .glb, .png, .exr. Mantén concordia_master.blend y los .glb en una carpeta de respaldo con copias fechadas y un archivo MANIFEST.txt con tamaños y sumas de verificación (sha256).
   - Añade un .gitignore que excluya esas extensiones y dime cuánto pesa el repositorio y la carpeta de respaldo. No fuerces ningún push.

CORRECCIONES MENORES:
- README: corrige las marcas del Obelisco (son 100, 001 a 100) en la lista de animables.
- Escalones al pie de escaleras laterales de hasta 14 cm: aceptados (el límite es 15 cm).
- Muralla en LOD2: acepto la suma de instancias, pero anota en el README que la muralla colocada no tiene LOD2 propio.

PROCEDE en este orden: puntos 2, 3, 4, 5, 9, 7, 8, y al final el punto 1 (medición con el nuevo criterio). Después repite la verificación de E11 (puertas visibles, visibilidad del Faro, huellas, paleta, materiales, memoria ≤ 220 MB) y entrégame el balance final de las 12 etapas, con la lista de lo que quede abierto. Guarda concordia_v26.blend.
```


### Mensaje 39 — 2026-11-08 13:46 — Fuentes de assets para Concordia. Tienes acceso a internet y a GitHub.

```text
Fuentes de assets para Concordia. Tienes acceso a internet y a GitHub.

PERMITIDAS (CC0): Kenney, Quaternius (Fantasy Props MegaKit y pack de pueblo medieval), KayKit (releases de GitHub), Poly Haven, ambientCG, Smithsonian Open Access y el filtro CC0 de Sketchfab. Lista de apoyo: github.com/madjin/awesome-cc0.
SOLO CON MI APROBACIÓN: cualquier asset CC BY (Poly Pizza, Icosa, Sketchfab CC BY, Meshy gratis). Si lo apruebo, se anota para los créditos del juego.
PROHIBIDAS: CC BY-NC, "uso personal", sin licencia visible, o sacadas de otros juegos o películas.

REGLAS:
- Descarga solo archivos de datos (glb, gltf, fbx, obj, blend, png, jpg, exr, zip de assets). No ejecutes scripts, instaladores ni binarios. No instales addons de Blender sin mi aprobación (y solo de repos con licencia clara y actividad reciente).
- Cada asset va a ASSETS_LICENSES.md: nombre, autor, URL, licencia, fecha y dónde se usó. Sin ese registro no se usa. Si algún asset requiere atribución, crea también CREDITS.md.
- Adaptación obligatoria: estilo semi-realista oscuro de formas simples; materiales reasignados a los de Concordia; paleta tierra, con el azul #8FD0FF como único color mágico; prop pequeño ≤ 500 triángulos, mediano ≤ 1.500; escala real en metros; origen en la base; texturas a 1K; memoria total ≤ 220 MB.
- Cada familia (madera, hierro, tela) comparte material. No hagas un collage de estilos: si un asset no cuadra tras adaptarlo, descártalo.
- NO usar assets descargados ni IA para el Portal, Faro, Obelisco, Santuario, Salón de las Hazañas, Banco, Tesorería, Crisol ni casas de barrios y moradas.

ASSETS GENERADOS POR IA: yo los genero fuera de Blender (Gemini y TRELLIS.2) y los dejo en la carpeta /ia_assets/. Cuando existan, impórtalos, revisa que la malla sea limpia, rehaz la topología o decimate hasta el presupuesto, hornea el normal map, reasigna a los materiales de Concordia y regístralos en ASSETS_LICENSES.md como "generado con IA (TRELLIS.2, MIT)".

TAREA AHORA: haz una tabla de props pendientes (Mercado, Oficios, Clases, interiores) con: el pack o asset CC0 candidato, su licencia, triángulos, y cuáles no existen en ningún pack (esos son los que yo generaré con IA). Espera mi aprobación antes de importar nada.
```


### Mensaje 40 — 2026-11-08 14:00 — Vamos con los INTERIORES de Concordia. Cada edificio con interior=true se carga como escen

```text
Vamos con los INTERIORES de Concordia. Cada edificio con interior=true se carga como escena aparte al entrar por MARKER_<Nombre>_Door. Hoy solo existen los InteriorVolume, sin mobiliario.

REFERENCIAS (lugares reales, busca imágenes si puedes): Palazzo Pubblico de Siena (salas macizas con arcos y bóvedas), Westminster Hall (vigas de techo a la vista), Mina de sal de Wieliczka (salas con cristales y luz cálida), Rothenburg ob der Tauber y Český Krumlov (interiores de posadas y casas de entramado con vigas bajas y chimenea), Sainte-Chapelle (vitrales). Copia proporción de salas, vigas, arcos y la calidad de la luz.

REGLAS:
- Una escena por interior: int_<nombre>.glb. Origen en la puerta de entrada, piso en Z=0, tamaño igual al InteriorVolume (±0.2 m).
- Cámara isométrica CAM_Iso: calcula qué dos muros quedan cerca de la cámara. Esos (WALL_Near_A, WALL_Near_B) y el techo (CEILING) son objetos aparte ocultables. Los muros del fondo son estáticos.
- Estructura de cada interior: Shell (piso, muros del fondo, columnas, vigas), WALL_Near_*, CEILING, Furniture (props instanciables), Lights (Empties con color, energía y radio) y Markers.
- Marcadores (el eje +Y local es el frente): MARKER_Interior_Exit en la puerta (+Y hacia la calle), MARKER_Interior_Spawn (+Y hacia el interior), MARKER_NPC_Slot_xx (propiedad npc), MARKER_Interact_xx (propiedad tipo), MARKER_WorkStation_xx para oficios, MARKER_TrophyCase donde corresponda.
- Colisión "-colonly" simple, "-navmesh" para el piso transitable. Ningún pasillo de menos de 1.2 m. Escaleras interiores de ≤ 35°.
- Presupuesto ≤ 40.000 triángulos por interior (shell más props), solo materiales de Concordia, texturas 1K.
- Luz horneada: cálida natural (velas, hogares, ventanas, emisión ≤ 1.0). El azul #8FD0FF solo para esquirlas y cristales. Aspecto remendado, igual que el exterior.
- Props: solo los aprobados en ASSETS_LICENSES.md. Lo singular, a mano.

KIT DE INTERIOR (colección BLD_INT_KIT, grilla 1 m, máx 300 triángulos por módulo): INT_Floor_Stone, INT_Floor_Planks (variantes remendadas), INT_Wall_Plaster, INT_Wall_Stone, INT_Wall_Panel, INT_Beam_Straight, INT_Beam_Cross, INT_Arch_3m, INT_Arch_6m, INT_Pillar, INT_Stairs_Int, INT_Door_Int, INT_Window_Int, INT_Fireplace, INT_Counter_Straight, INT_Counter_Corner, INT_Grille (reja de mostrador), INT_Railing, INT_Trim. Crea la función build_interior(nombre, volumen, estilo, seed) en concordia_buildings.py.
Entrega: hoja del kit y una sala de prueba de 8x6 m en vista isométrica, con los muros cercanos ocultos y a altura de personaje.

PILOTO: INTERIOR DEL BANCO DE CONCORDIA (int_banco.glb). Sirve para validar cámara, escala, luz y exportación; lo que aprendas se aplica a los demás.
REFERENCIAS: Palazzo Pubblico de Siena (volumen macizo y arcos), antigua sede del Monte dei Paschi de Siena (uno de los bancos más antiguos del mundo, sala sobria de piedra), Porta Nigra (bloques pesados). Copia la sobriedad, la masa de piedra, las rejas y la luz escasa.
ESPECIFICACIÓN (volumen 24x20 m, 2 plantas, ventanas con rejas, puerta de hierro con candado):
1. Planta baja: vestíbulo con mostrador largo de piedra y madera con reja de 10 m (INT_Counter + INT_Grille). El Banquero (MARKER_NPC_Slot_01, npc=Banquero) va detrás del mostrador, a la vista de la cámara. Sala de espera con 3 bancos, archivo con estantes y libros contables, escritorio.
2. Bóveda: al fondo, tras una puerta de hierro de 3 m con herrajes (hecha a mano), una cámara de piedra con arcos y cajas de depósito numeradas: 200 en total (parámetro BOXES_TOTAL), en 4 paredes. Dos variantes: BANK_Box_Open (placa de bronce clara) y BANK_Box_Locked (candado de hierro y placa oscura). Los números 1 a 200 se leen desde cerca: un solo material con atlas de números y UV por caja. La capacidad se amplía con oro, así que Godot cambiará cada caja entre Open y Locked.
3. Planta alta: galería con balaustrada que da al vestíbulo, despacho con escritorio, escalera de piedra de 2 m de ancho.
4. Marcadores: MARKER_Interact_Bank_Counter (abre el banco), MARKER_Interact_Vault, MARKER_Interior_Exit, MARKER_Interior_Spawn.
5. Luz: lámparas de aceite y velas (cálida), ventanas con reja, y un solo detalle azul pálido (un farol de esquirla sobre la puerta de la bóveda).
Verifica con rayos desde CAM_Iso que el Banquero, el mostrador y la puerta de la bóveda son visibles sin que una columna o arco los tape. Entrega capturas isométrica y a altura de personaje, triángulos reales, y una lista de lecciones para los demás interiores.
```


### Mensaje 41 — 2026-11-10 14:31 — Inténtalo de nuevo

```text
Inténtalo de nuevo
```


### Mensaje 42 — 2026-11-10 15:06 — continua

```text
continua
```


### Mensaje 43 — 2026-11-11 04:01 — Inténtalo de nuevo

```text
Inténtalo de nuevo
```


### Mensaje 44 — 2026-11-11 04:02 — Balance sin modificar nada. Responde HECHO / PARCIAL / NO EMPEZADO, con números y problema

```text
Balance sin modificar nada. Responde HECHO / PARCIAL / NO EMPEZADO, con números y problemas abiertos:
1. ASSETS_LICENSES.md y registro de las texturas de Poly Haven.
2. Props importados (Quaternius y Avramania): cuántos, triángulos y memoria de texturas total en MB.
3. Props a mano (incluida la vitrina de trofeos en 3 variantes) y los 4 objetos de IA en /ia_assets/ (¿llegaron? ¿importados?).
4. Kit de interior: piezas hechas y sala de prueba.
5. Piloto del Banco: ¿hecho? Triángulos, visibilidad del Banquero, mostrador y bóveda desde CAM_Iso, y las lecciones para los demás interiores.
6. Decisiones que esperan mi respuesta.
Termina con la siguiente etapa que recomiendas y por qué.
```


### Mensaje 45 — 2026-11-11 04:09 — Sobre los 4 objetos de IA pendientes (telar, fuelle de forja, maniquí de costura, casco de

```text
Sobre los 4 objetos de IA pendientes (telar, fuelle de forja, maniquí de costura, casco de minero con lámpara) y la generación de modelos en general:

1. Ejecuta get_addon_status y dime qué generadores de generate_3d están activos (tripo, hunyuan3d, hyper3d, meshy), cuáles son Premium y cuáles usan mis propias claves, y qué librerías de assets están activas. No generes nada todavía.
2. Para cada generador activo, comprueba en su página oficial la licencia actual de lo que genera mi plan (uso comercial, atribución, restricciones por territorio) y dímelo en una tabla. Un generador solo se usa si permite uso comercial sin atribución, o con una atribución que yo apruebe. Tripo gratis y cualquier plan "no comercial" o "personal" quedan descartados. Registra todo en ASSETS_LICENSES.md si se usa.
3. NO uses el navegador para entrar a Gemini, Meshy ni a ninguna web de generación (nada de iniciar sesión, captchas ni crear cuentas). Si yo quiero usar la API de Gemini, te daré una clave por el formulario seguro y entonces compruebas su capa gratuita y sus términos.
4. Haz primero los 4 objetos A MANO con el kit y los materiales de Concordia, cada uno ≤ 1.000 triángulos, estilo semi-realista oscuro de formas simples, escala real en metros, origen en la base:
   - Telar de madera de suelo con una tela remendada a medio tejer.
   - Fuelle de forja de cuero y madera con boquilla de hierro.
   - Maniquí de costura (torso de madera sobre pie, sin cabeza ni cara) con tela remendada.
   - Casco de minero de hierro abollado con correa de cuero y una pequeña lámpara de aceite con una esquirla azul pálido (#8FD0FF).
   Muéstrame capturas (isométrica y de cerca) y triángulos reales.
5. Si algún objeto no queda bien, pídeme permiso antes de gastar una generación de generate_3d, y dime cuántas me quedan y qué cuesta cada una. Cada llamada puede costar dinero o una de las generaciones del mes, así que no repitas una generación ni dupliques llamadas: si hay que repetir un objeto, duplícalo en la escena.
6. Si decidimos usar generate_3d, sigue la regla de assets de Concordia: reasigna a los materiales de la ciudad, baja a presupuesto, hornea el normal map, y registra en ASSETS_LICENSES.md el proveedor, la fecha y la licencia del plan.
7. Decisiones sobre tu balance (numeración de tu informe):

INTERIORES (etapa 27)
1. 23.1 x 19.1 m: ACEPTADO (la diferencia es el grosor de muros).
2. Banquero al 58%: abre UNA ventanilla de 1.2 m en la reja, justo delante del Banquero (como una ventanilla de cajero, con marco de piedra y mostrador libre). El resto de la reja se queda igual. Repite la medición de rayos del Banquero y del mostrador y reporta el nuevo porcentaje. Objetivo: ≥ 75%.
3. Grupos ocultables extra: ACEPTADOS como convención. Generalízalos: LEVEL_n, WALL_Near_<Recinto>, CEILING_<Recinto>. Documéntalo en README_buildings.txt para todos los interiores.
4. 40 cajas abiertas por defecto: ACEPTADO como estado de muestra. Godot decidirá por jugador cuáles cambia entre BANK_Box_Open y BANK_Box_Locked. Anótalo en TODO_GODOT.txt.
Cierra la etapa 27 con los 3 pasos que faltan: revisar la captura de las cajas (los números deben leerse en el orden correcto y no en espejo), copiar el .blend, el glb y el atlas a respaldo/2026-11-08/interiors/ con MANIFEST (sha256), y enviarme las capturas y los binarios.

ASSETS
5. Fuentes: APROBADAS. Quaternius Fantasy Props MegaKit y Avramania (serie Low Poly Medieval) como base; Poly Haven para casos sueltos; Kenney, KayKit, Quaternius Medieval Village y Smithsonian descartados. Condición para Avramania: en cada descarga confirma en la página del modelo que la licencia sigue siendo CC0 y registra URL, fecha y texto de la licencia en ASSETS_LICENSES.md. Copia License_Standard.txt de Quaternius a /licenses/.
6. Mobiliario de Moradas y Casas de Raza: SÍ puede usar props descargados. La regla de "no descargados" es solo para los edificios (Portal, Faro, Obelisco, Santuario, Salón, Banco, Tesorería, Crisol y casas de barrios y moradas).
7. Token de Sketchfab: lo escribo yo en el formulario seguro cuando toque importar.
8. Red: no cambies nada. Con las fuentes aprobadas no hace falta github.com ni kenney.nl.
9. Los 4 objetos de IA (telar, fuelle de forja, maniquí de costura, casco de minero): aún no los genero, NO bloquean nada, déjalos pendientes. Los triviales hazlos a mano (lingotes y carbón, rollos de tela, mostrador de barra, caballete, tornillo de banco, martillo de subastador, tintero y sello, pala de panadero, bastidor y raspador de curtir, secadero de hierbas, cajas de pescado y cañas, arco largo, rueca, vitrina de joyero), ≤ 1.000 triángulos cada uno. La rueca, a mano (no decimes el modelo de Poly Haven de 52.000 triángulos).
   Decimado: solo lo que pase de 1.700 triángulos, hasta ≤ 1.500 (Barrel_Holder, Chandelier, Chest_Wood, Chain_Coil, WeaponStand), con normal map horneado.
   Orden: importa primero los props del Mercado (Posada, Casa del Registro, Gran Subasta) en BLD_PROPS_INT, muéstrame la hoja de props con triángulos y materiales, y espera mi aprobación.

PENDIENTES DE LA ETAPA 26
10. Faro: SÍ, baja MER_Casa_01 (decoración) hasta que deje de tapar. Acepto el fallo restante del criterio porque lo resuelve Godot (cristal y haz dibujados por encima de los edificios, y brújula en pantalla). Documéntalo en TODO_GODOT.txt con la lista de puntos que quedan sin vista del Faro.
11. Moradas, 16 puertas bloqueadas: arréglalas así.
   a) Las 7 por balcón o escalera: balcón de 1.2 m de saliente como máximo, y la escalera va en el extremo de la fachada más alejado de la cámara.
   b) Las 9 por cuerpo o alero: reduce el alero a 0.3 m; si sigue tapando, baja esa vivienda a 2 plantas; si aun así tapa, mueve la puerta a otra fachada de la misma casa.
   c) Tolerancia final: acepto hasta 10 puertas residuales (menos del 1%) si me entregas la lista con parcela y causa, porque Godot puede aclarar techos y aleros cuando el jugador se acerca. Mide de nuevo y reporta.
12. Barrio B06 con 2 casas: ACEPTADO como provisional. Los barrios de razas son una plantilla (N_RAZAS=6) y se rehacen cuando llegue la lista real de razas. Anótalo en TODO_GODOT.txt.
13. "Margen de pendiente de 2.5 m en los solares de Razas": no tengo el detalle de tu pregunta original, así que reexplícamela en 3 líneas con 2 opciones y tu recomendación, y espera mi respuesta. Regla general mientras tanto: acepto el margen solo si la diferencia de nivel entre solar y calle se resuelve con muro de contención o escalón de ≤ 15 cm, sin taludes de tierra.
14. Soportes de tubos que pisan calles: los soportes no pueden quedar sobre la zona de paso. Muévelos al borde de la calle (a 0.6 m de la línea de edificios) o a las fachadas y techos. Si en algún tramo no cabe, haz un pórtico (arco de piedra o hierro) con pilares en los bordes de la calle y el tubo pasando por encima a 9 m. Mantén ≥ 5 m de altura libre sobre las calles y ≥ 1.2 m de separación de techos. Repite la medición del punto 1 del Faro (haz visible).
15. Git: .jpg, .gltf y .bin son assets binarios, así que NO van en git, igual que .blend, .glb, .png y .exr. Añádelos al .gitignore. Si ya están trackeados, sácalos del índice sin tocar los archivos (git rm --cached) y no reescribas el historial ni fuerces ningún push. Guárdalos en la carpeta de respaldo con su MANIFEST.

SIGUIENTE
Cierra la etapa 27 y arranca la ETAPA 28: la vitrina de trofeos a mano y el interior tipo de una Morada. Hazlo en este orden: vitrina, interior de Habitación, de Casa pequeña y de Casa grande; luego un resumen con lecciones. Esa etapa se hace con el kit y no espera a los objetos de IA.

ETAPA 28: ESPECIFICACIÓN
REFERENCIAS: interiores de casas medievales de Český Krumlov y Rothenburg ob der Tauber (vigas bajas de madera, chimenea de piedra, muros de revoco, ventanas pequeñas con postigos). Copia proporciones, vigas y la calidez de la luz, con aspecto remendado.
1. Vitrina de trofeos (MARKER_TrophyCase): a mano, 3 variantes (de pared, de mesa, estante con nichos), ≤ 800 triángulos cada una, un solo material (madera con vidrio), LOD1 y LOD2. Cada variante tiene 6 a 9 slots para trofeos (Empties MARKER_Trophy_Slot_xx). Se instancia en 1.404 viviendas, así que debe ser muy ligera.
2. Plantillas de interior (tres, instanciadas por Godot con cada puerta como escena privada):
   - Habitación (cuarto de casa comunal): 4 x 5 m, cama, baúl seguro (MARKER_Interact_Chest, 40 espacios), una vitrina de pared, una ventana. ≤ 8.000 triángulos.
   - Casa pequeña: 6 x 8 m, una planta con patio, baúl (100 espacios), mesa de trabajo básica (MARKER_WorkStation_01), hogar, mesa y sillas, vitrina. ≤ 15.000.
   - Casa grande: 8 x 10 m, dos plantas, baúl (200 espacios), dos mesas de oficio (MARKER_WorkStation_01 y 02), sala para recibir amigos, escalera interior, vitrina, y un espacio de jardín para hierbas en la fachada (MARKER_Garden). ≤ 28.000.
3. Reglas de las lecciones de la etapa 27 aplican: muros cercanos y techo ocultables, entreplantas en los muros del fondo, props mirando a la cámara, nada coplanario, un solo azul por sala, MARKER_Interior_Exit y MARKER_Interior_Spawn, navmesh con celdas de 0.25 m, y los marcadores con +Y al frente.
4. Personalización por Godot: puerta exterior (color, farol, número) ya es parte del exterior; aquí deja MARKER_Interact_TrophyCase y que los 3 interiores se puedan decorar (props instanciables en slots).
5. Reutiliza build_interior (estilo entramado) y reporta lecciones nuevas. Entrega capturas isométrica y a altura de personaje de cada plantilla, triángulos reales, y guarda la versión.
```


### Mensaje 46 — 2026-11-11 04:53 — Vamos a crear el primer PERSONAJE JUGABLE de Concordia: un elfo masculino con la clase San

```text
Vamos a crear el primer PERSONAJE JUGABLE de Concordia: un elfo masculino con la clase Sanador (provisional hasta tener la lista de clases). Es para un MMORPG 3D de cámara isométrica en Godot 4, magia medieval oscura, estilo semi-realista de formas simples. Todo gratis y con licencia comercial clara.

REGLAS:
- Referencias visuales primero. Úsalas y dime qué copias de cada una. Prohibido usar personajes de otros juegos, películas o libros (nada de elfos de WoW, Tolkien, etc.): el diseño debe ser original.
  Proporciones y rostro: esculturas góticas de catedral (figuras esbeltas, alargadas, rostro sereno). Ropa: túnicas y batas medievales de lino y lana. Paleta y ánimo: bosque de abedules con luz suave (plateados, grises, verdes apagados). Accesorios: iconografía de herbarios medievales (hierbas, frascos).
- Paleta tierra y apagada. El azul pálido #8FD0FF (emisivo) es el único color mágico fuerte.
- Un solo esqueleto para TODAS las razas y clases: usa los nombres de huesos del SkeletonProfileHumanoid de Godot (verifica la lista en la documentación oficial), T-pose, el personaje mira hacia -Y en Blender (se exporta como +Z en Godot), unidades en metros, origen en el suelo entre los pies, transformaciones aplicadas.
- Modular: cuerpo, cabello y piezas de ropa son objetos separados que comparten el mismo esqueleto, con máscaras (vertex groups HIDE_*) para ocultar el cuerpo bajo la armadura.
- Presupuesto LOD0 (personaje completo con ropa inicial): ≤ 10.000 triángulos (cuerpo ≤ 4.500, ropa ≤ 4.000, cabello ≤ 1.000, extras ≤ 500). LOD1 ≤ 5.000, LOD2 ≤ 1.800. Hay 100+ jugadores a la vez por piso. Texturas 1K con tres mapas (albedo, normal, ORM). Máximo 3 materiales por personaje.
- Cámara isométrica (CAM_Iso con escala ortográfica ~6 para personajes): la silueta debe leerse a distancia (orejas, cabello, dobladillo de la túnica, capucha).
- Todo gratis: sin addons ni servicios de pago. Antes de instalar cualquier addon de Blender, pídeme aprobación (verifica licencia y actividad del repositorio). No uses generate_3d para el cuerpo del personaje.
- Registra en ASSETS_LICENSES.md cada herramienta o asset (nombre, URL, licencia, fecha, dónde se usó).
- Verifica con look después de cada etapa (T-pose frontal, lateral, trasera, e isométrica) y reporta triángulos reales. Guarda con versión (elfo_v01.blend...). Un paso a la vez.
Confirma que entendiste y espera el siguiente prompt.
```


### Mensaje 47 — 2026-11-11 04:55 — Decisiones sobre tu mensaje:

```text
Decisiones sobre tu mensaje:

1. Verificación sin "look": APROBADO. Renderiza tú las vistas en Blender y revísalas antes de enviarlas. Usa CAM_Iso (ortográfica, escala ~6) para la vista isométrica y una cámara ortográfica frontal, lateral y trasera para las T-pose, con fondo gris neutro e iluminación pareja. Reporta cuáles imágenes revisaste y qué problemas viste antes de enviarlas.

2. Un solo esqueleto para todas las razas: APROBADA tu interpretación. Misma jerarquía y mismos nombres de hueso del SkeletonProfileHumanoid en todas las razas; cada raza puede tener su propia longitud de huesos en la pose de reposo. Godot comparte las animaciones con el retargeting del perfil humanoide (con Normalize Position Tracks para que no patine por la distinta longitud de piernas). Condiciones: todas las razas son bípedas con la misma estructura de huesos (sin brazos o patas extra), y toda raza empieza en T-pose. Si más adelante aparece una raza de forma muy distinta, se decide aparte. Los huesos extra de cada raza (orejas, colas, alas, trenzas) van como huesos no mapeados.

3. Rig por script sin addons de terceros: APROBADO. Deja el script en un archivo (concordia_rig.py) para poder regenerar el rig y reutilizarlo con las demás razas. Rigify queda sin usar.

4. Etapa 28 (renders de interiores de Moradas): NO la pauses. Termina los renders, revísalos y entrégame las capturas, los binarios y el informe. Haz eso primero. No empieces el personaje hasta cerrar la etapa 28, para no mezclar versiones del .blend ni competir por el render.

5. Cuando cierres la 28, usa un archivo nuevo para el personaje (elfo_v01.blend, separado del de la ciudad) y no toques concordia_master.blend. Registra todo en ASSETS_LICENSES.md y avísame cuando estés listo para la etapa 1 (PJ1, cuerpo base).
```


### Mensaje 48 — 2026-11-11 04:59 — Etapa 1: CUERPO BASE del elfo masculino.

```text
Etapa 1: CUERPO BASE del elfo masculino.

1. Base: usa MakeHuman mediante su addon de Blender (MPFB), que exporta en CC0. Pídeme aprobación antes de instalarlo. Si no es posible, busca una malla base humana CC0 (por ejemplo, listadas en github.com/madjin/awesome-cc0) y verifica su licencia. Registra la fuente y la licencia. Como CC0 permite que cualquiera use la misma base, el resultado final debe ser claramente propio: proporciones, rostro, orejas y texturas modificadas.
2. Proporciones élficas: altura 1.85 m (la referencia humana es 1.75 m), unas 8 cabezas de alto, hombros ~8% más estrechos, piernas algo más largas respecto al torso (+6%), extremidades finas pero con musculatura visible, cuello largo. Referencia: esculturas góticas de catedral (figuras esbeltas y alargadas).
3. Rostro: ángulos marcados, pómulos altos, ojos almendrados algo rasgados, nariz pequeña, expresión serena. Detalle simple, sin poros ni arrugas finas (cámara isométrica).
4. Orejas: puntiagudas, de 12 a 14 cm de largo, inclinadas hacia atrás 25 a 30° respecto a la vertical, con un borde de cartílago visible y grosor fino. Deben leerse en la silueta isométrica.
5. Manos de dedos largos y delgados.
6. Topología: cuadros predominantes, sin n-gons, con anillos de aristas en hombros, codos, muñecas, cadera, rodillas y tobillos. Cuerpo desnudo (con cabeza) ≤ 4.500 triángulos.
7. Modularidad: separa en objetos Head, Torso, Arms, Hands, Legs, Feet con vértices coincidentes en las uniones y normales continuas. Crea los vertex groups HIDE_Torso, HIDE_Arms, HIDE_Hands, HIDE_Legs, HIDE_Feet. Ojos como un objeto aparte (Eyes), sin dientes ni lengua.
8. Piel: material con textura PBR horneada a PNG 1K (albedo con variación suave de tono, normal, ORM). Estilo semi-realista simple, sin fotorrealismo. 2 variantes de tono para probar.
Entrega: T-pose frontal, lateral, trasera, primer plano del rostro y orejas, vista isométrica, triángulos reales por objeto.
```


### Mensaje 49 — 2026-11-11 05:06 — continúa y cierra la etapa 28

```text
continúa y cierra la etapa 28
```


### Mensaje 50 — 2026-11-11 05:09 — Decisiones:

```text
Decisiones:

1. PROPS DEL MERCADO (props_mercado_q y props_mercado_av): APROBADAS si cumplen TODO esto. Si algo falla, corrige ese prop y no me preguntes:
   - Cada Avramania con su página mostrando CC0 el día de la descarga (URL, fecha y texto de la licencia en ASSETS_LICENSES.md); los Quaternius con License_Standard.txt copiado en /licenses/.
   - Triángulos: ≤ 500 los pequeños y ≤ 1.500 los medianos (≤ 1.700 antes de decimar).
   - Materiales reasignados a los de Concordia, escala real en metros, origen en la base.
   - Memoria total de texturas ≤ 220 MB (avísame si pasas de 200).
   Cuando pasen, impórtalos a BLD_PROPS_INT y sigue con Oficios y Clases en el mismo orden.

2. PUERTAS DE LAS MORADAS: mantén SO_036 y SO_037 a 2 plantas y acepta 13 puertas residuales. 13 de 1.404 es el 0,93 %, dentro de mi criterio de menos del 1 %. No apliques la regla literal de la escalera (subiría a 48). Quedan 1.398 viviendas: actualiza ese número en README_buildings.txt y en el informe. Entrégame la lista de las 13 puertas con parcela, causa y distancia a la cámara. Anota en TODO_GODOT.txt que Godot debe aclarar techos y aleros de esas casas cuando el jugador se acerca.

3. SOPORTES DE LOS TUBOS: opción A, desviar el tubo por encima del Banco y de la Casa del Registro. Condiciones:
   - Ningún pilar ni soporte dentro de la plaza del Mercado ni en la fuente, ni en calles (se mantienen despejadas para la multitud). Rechazo la opción B.
   - Los soportes de la desviación son pilares de piedra sobre los techos, de 0,6 m de sección, anclados al edificio (sin atravesar la cubierta ni el alero), con la tubería a ≥ 1,2 m sobre el tejado.
   - Separación entre soportes ≤ 10 m. Cuando un tramo tenga que salvar más (plaza), usa un arco de piedra entre dos techos o un pilar en el techo intermedio; nunca pases de 16 m sin apoyo.
   - Altura libre ≥ 5 m sobre calles. No subas la altura de ningún edificio ni bloquees puertas.
   - Repite la medición de visibilidad del Faro con la nueva ruta y confirma que los techos del Banco y del Registro soportan visualmente los pilares (sin flotar).
   Actualiza la curva CRV_LightPipe_Tesoreria_Faro y los marcadores de soporte.

4. MARGEN EN SOLARES DE RAZAS: opción A (mantener RAZ_B05_Casa_04 y Casa_05). Haz ahora la comprobación pendiente: el zócalo del lado de la puerta debe quedar con escalón ≤ 15 cm. Si algún zócalo falla, añade 1 o 2 peldaños de ≤ 15 cm a lo largo de la fachada o una rampa corta, sin tocar el terreno. Reporta el resultado de ambas casas. Recuerda que los barrios de razas son plantilla.

PERSONAJE (etapa 1, cuerpo base): APROBADO instalar
- MPFB 2.0.18 desde extensions.blender.org (GPL-3.0 como herramienta, y su FAQ oficial dice que los modelos y assets base son CC0).
- MakeHuman system assets desde files.makehumancommunity.org (paquete CC0 con ojos y proxies).
Condiciones: instala solo desde esas dos fuentes oficiales. No ejecutes ningún .exe, instalador ni script suelto, y descomprime el paquete de assets solo en la carpeta de datos del addon. Registra en ASSETS_LICENSES.md el URL de la FAQ, la fecha, la versión y el sha256 del paquete. Los demás permisos y reglas de PJ0 siguen igual.

ORDEN: primero cierra los puntos 1 a 4 y la etapa 28 (entrégame capturas, binarios e informe). Después empieza el personaje en elfo_v01.blend sin tocar los .blend de la ciudad. Antes de crear el rig, verifica la lista de huesos del SkeletonProfileHumanoid en la documentación oficial de Godot. Al terminar el PJ1, envíame las 4 vistas, los triángulos por objeto y las proporciones medidas (altura, cabezas, ancho de hombros) para revisarlas.
```


### Mensaje 51 — 2026-11-11 12:29 — Inténtalo de nuevo

```text
Inténtalo de nuevo
```


### Mensaje 52 — 2026-11-11 13:24 — Etapa 2: CABELLO y ROPA INICIAL del Sanador (calidad normal, sin brillo ni legendarios).

```text
Etapa 2: CABELLO y ROPA INICIAL del Sanador (calidad normal, sin brillo ni legendarios).

REFERENCIAS: túnicas y batas medievales de lino y lana (corte, mangas amplias, dobladillo), iconografía de herbarios medievales (hierbas, frascos, bolsitas), bosque de abedules (paleta plateada y apagada).
Diseño: sanador viajero y sobrio. Túnica larga de lino crema-gris con parches remendados, cinturón de cuero con 3 bolsitas de hierbas y 2 frascos, mantón o capucha de lana verde-gris apagada, botas de cuero marrón, brazaletes de tela. Un solo detalle mágico: un pequeño colgante de cristal azul pálido (emisión 1.0, #8FD0FF). Bordados de hojas sencillos en la orilla (en la textura, no en geometría).
Piezas separadas (todas con vertex groups para ocultar el cuerpo): Robe_Top (pecho y mangas), Robe_Skirt (falda dividida en panel delantero y trasero para que las piernas se muevan), Hood (capucha como pieza aparte, ocultable), Belt_Pouches, Boots, Bracers. Cabello: Hair_Elf, largo, color ceniza plateado, recogido atrás con una trenza (cards de ≤ 1.000 triángulos, alpha clip en lugar de blend para evitar problemas de transparencia en Godot).
Presupuesto: ropa ≤ 4.000 triángulos, cabello ≤ 1.000. Un atlas de 1K para ropa y cabello (albedo, normal, ORM). Remendado visible, sin saturar colores. La silueta (capucha, dobladillo, orejas que sobresalen del cabello) debe leerse desde la cámara isométrica.
Registro: nada de assets descargados sin licencia verificada. Marca el conjunto como CLASE_SANADOR (provisional).
Entrega: T-pose con ropa en 3 vistas, vista isométrica, triángulos por pieza, y una captura con cada pieza ocultada para comprobar los HIDE_*.
```


### Mensaje 53 — 2026-11-11 14:25 — quiero cambiar quiero que ahora los archivos tambien se guarden es esta carpeta C:\Users\U

```text
quiero cambiar quiero que ahora los archivos tambien se guarden es esta carpeta C:\Users\USER\Desktop\Juego_1\Juegocamkeju
```


### Mensaje 54 — 2026-11-11 14:27 — ya le di permiso a las carpeta y envia los binarios

```text
ya le di permiso a las carpeta y envia los binarios
```


### Mensaje 55 — 2026-11-11 14:28 — revisa lo de la carpeta

```text
revisa lo de la carpeta
```


### Mensaje 56 — 2026-11-11 14:29 — vuelve y revisa

```text
vuelve y revisa
```


### Mensaje 57 — 2026-11-11 14:31 — necesito conectar la carpeta porque me esta subiendo todo al gif pero no puedo hacer prueb

```text
necesito conectar la carpeta porque me esta subiendo todo al gif pero no puedo hacer pruebas ni mirar desde el git por eso tambien necesit ocrear una copia en mi ordenador para que este en los dos lados
```


### Mensaje 58 — 2026-11-11 14:36 — Etapa 3: ESQUELETO (RIG) del elfo.

```text
Etapa 3: ESQUELETO (RIG) del elfo.

1. Crea un armature limpio con los huesos del SkeletonProfileHumanoid de Godot (incluido Root, Hips, Spine, Chest, UpperChest, Neck, Head, hombros, brazos, antebrazos, manos y dedos, piernas, pies y dedos de pie), usando exactamente esos nombres y la jerarquía del perfil. Verifica la lista contra la documentación oficial de Godot. T-pose, mirando hacia -Y, rotación 0, escala 1 aplicadas.
2. Huesos extra (no mapeados al perfil, para que Godot los ignore en el retargeting): Weapon_R, Weapon_L (ranuras para bastón o arma, en las manos), Back_Slot, Head_Top (efectos), 4 huesos para la trenza del cabello (Hair_01 a 04), 3 huesos para el dobladillo de la falda de cada lado (Skirt_*), pensados para el SpringBoneSimulator3D de Godot. Máximo 65 huesos de deformación en total.
3. Pesos: automáticos y luego limpieza manual en hombros, codos, muñecas, cadera, rodillas y tobillos. Máximo 4 influencias por vértice, normalizados. La ropa se pesa igual que el cuerpo (puede transferir pesos desde el cuerpo) y la falda solo a piernas y huesos Skirt_*.
4. Prueba de deformación en 10 poses: T, A, contacto de caminata, carrera, sentado, brazos levantados (lanzar hechizo), de rodillas, agachado, golpe recibido y caído. Captura de cada una, y corrige los defectos de pesos (codos aplastados, hombros que se rompen, falda atravesando piernas).
5. Verifica que el esqueleto cumple la convención de Godot: +Y del hueso hacia el hijo, T-pose, sin transform en el nodo. Los pasos de importación (BoneMap, SkeletonProfileHumanoid y Rest Fixer) van en TODO_GODOT_personaje.txt.
Herramientas de pago: ninguna (RigPort cuesta dinero). Si propones Rigify o Rigodotify, pídeme aprobación y verifica la licencia antes.
Entrega: capturas de las 10 poses, lista de huesos, triángulos, y guarda la versión.
```


### Mensaje 59 — 2026-11-11 15:05 — Vamos a MONTAR EN GODOT todo lo que hemos modelado de Concordia, para probarlo y arreglar 

```text
Vamos a MONTAR EN GODOT todo lo que hemos modelado de Concordia, para probarlo y arreglar lo que haga falta. Godot instalado: 4.7.2 stable. Todo gratis.

REGLAS
- Verifica cada ajuste de importación, sufijo y función de Godot en la documentación oficial de la versión 4.7 antes de usarlo; no lo des por supuesto. Si hay Godot MCP disponible (get_godot_version, list_projects, create_scene, add_node, save_scene, run_project, get_debug_output), úsalo; si no, escribe los .gd y .tscn directamente y ejecuta Godot desde la terminal (revisa godot --help para las opciones de importación, scripts y ejecución). Después de cada fase, ejecuta el proyecto y lee la salida de depuración: cero errores y cero advertencias nuevas.
- NO modifiques ningún .blend ni .glb de la ciudad. Si un problema viene del modelo (normales, escala, material, hueco, pieza mal colocada), arréglalo en Godot solo si es un ajuste de importación o de material; si no, apúntalo en FIXES_BLENDER.md con: objeto, qué pasa, gravedad (bloqueante, alta, baja), captura, y cómo reproducirlo.
- Proyecto nuevo en una carpeta propia (godot_concordia/), renderer Forward+, unidades en metros. Estructura de res://: assets/{terrain,wall,buildings,interiors,props,markers,textures}/, scenes/, scripts/, shaders/, materials/, ui/, debug/, tools/.
- Git: en el repositorio solo van scripts, escenas (.tscn), shaders, ajustes y documentos de texto. Los .glb, .png, .exr y .import se ignoran (.gitignore) y se copian con un script tools/sync_assets.py desde las exportaciones, con MANIFEST (sha256). Sin push forzado ni LFS.
- Referencias de ambiente para la iluminación (lugares reales): Plaza del Campo de Siena a la hora dorada (luz cálida y sombras largas), Rothenburg ob der Tauber al atardecer, Carcassonne iluminada de noche, Mont-Saint-Michel al crepúsculo. Copia el contraste cálido/frío y la lectura de siluetas. Paleta apagada; el azul pálido #8FD0FF es el único color mágico fuerte.
- Cada fase termina con un resumen corto: qué quedó, números medidos y problemas abiertos. Tareas visuales: tira capturas del juego desde un script (tools/capture_tour.gd: guarda PNG del viewport en puntos de cámara fijos) y revísalas tú antes de enviármelas.

G0 · INVENTARIO Y PROYECTO
1. Localiza las exportaciones más recientes (carpetas respaldo/ y de export, con su MANIFEST) y lista cada .glb con tamaño, fecha y qué contiene: terreno (concordia_terrain_*), muralla (concordia_wall_kit y lo colocado), bld_* (portal, mercado, oficios, clases, razas, moradas NE/NO/SE/SO, kit, props), int_banco, interiores de Moradas (etapa 28), markers_concordia, y los de personaje si existen. Dime cuáles faltan.
2. Crea el proyecto, copia los assets con sync_assets.py, y lee TODO_GODOT.txt, README_buildings.txt, README_masks.txt y README_markers.txt (convenciones de marcadores: el +Y local de Blender es el frente, que en Godot es -Z). Haz una lista de todo lo pendiente de TODO_GODOT.txt; es nuestra lista de tareas.

G1 · IMPORTACIÓN
- Ajustes por tipo (usa archivos .import o un script de postimportación, repetibles): escala 1.0; sufijos de colisión (-colonly, -convcolonly), navegación (-navmesh) y oclusión (-occ) soportados por el importador; materiales como StandardMaterial3D con texturas comprimidas VRAM (normal maps marcados como normales; las ORM con oclusión/rugosidad/metálico correctos); sin generar LODs automáticos (usamos los propios _LOD0/_LOD1/_LOD2, que se muestran con rangos de visibilidad: LOD0 hasta ~40 m, LOD1 hasta ~100 m, LOD2 más allá, con margen de transición); sombra de malla activada; tangentes asegurados.
- Los extras de glTF (propiedades personalizadas de los Empties: footprint, door_direction, interior, tipo, npc, occludes_iso, provisional…) deben quedar legibles como metadatos de los nodos: compruébalo y haz un script que los liste.
- Reporta errores de importación, materiales sin textura, normales invertidas y mallas sin colisión.

G2 · ENSAMBLE DE LA CIUDAD (escena scenes/concordia.tscn, creada por un script repetible, no a mano)
- Terreno por chunks con su colisión y malla de navegación (NavigationRegion3D). Muralla (si la muralla colocada viene exportada, úsala; si no, instancia el kit en los MARKER_WallSlot por su tipo). Portal y Atrio, Obelisco, Faro con cristal y haz, Santuario, Salón de las Hazañas, Mercado, Oficios, Clases, Razas, puentes, arcos y escaleras, las 4 Moradas (1.398 viviendas), tubos de luz con su curva.
- Cada edificio con sus partes: _Body, _Roof (grupo "roofs"), _Props, colisión simple. Marcadores como Marker3D con sus metadatos (grupos: doors, npc_slots, interact, spawns).
- Rendimiento desde el principio: rangos de visibilidad por distrito y por LOD, occlusion culling con los -occ importados, y las Moradas como instancias ligeras.
- Reporta: nodos, triángulos visibles en 3 cámaras (plaza, mercado, moradas), draw calls y VRAM.

G3 · CÁMARA, JUGADOR DE PRUEBA Y HUD DE DEPURACIÓN  → PARADA 1 PARA QUE PRUEBE
- Cámara isométrica ortográfica: en Godot, la CAM_Iso de Blender (X=54.736°, Z=45°) corresponde a una rotación de (-35.264°, 45°, 0°); compruébalo con los marcadores de las puertas (el lado SE está más cerca de la cámara). Zoom con la rueda entre 15 y 120 m de visión, giro opcional en pasos de 90°, seguimiento suave del jugador.
- Jugador de prueba: cápsula (o el maniquí de la Universal Animation Library de Quaternius si ya la descargamos) que camina con WASD y también con clic para moverse (navegación). Colisión con edificios, escaleras, puentes y muralla; no debe atravesar nada ni caerse del mapa.
- HUD (tecla F1): FPS, tiempo de frame, draw calls, triángulos, objetos, VRAM, zona actual (plaza, Mercado, Oficios, Clases, Razas, Moradas, ceniza), posición, zoom y hora del día.
- Entrega la lista de problemas encontrados caminando por todas las avenidas, escaleras, puentes, plazas y callejones (¿algún hueco? ¿alguna escalera intransitable? ¿algún punto donde el jugador se atasca?). Detente aquí, avísame y espera.

G4 · LUZ, CIELO Y DÍA/NOCHE
- DirectionalLight3D con sombras de calidad media (cascadas ajustadas a la vista isométrica), WorldEnvironment con cielo despejado dentro de la muralla, niebla suave, tonemap y brillo (glow) discretos. Ciclo día/noche configurable (tecla T para avanzar la hora): de día luz cálida y sombras largas; de noche faroles de esquirla azules y la Torre del Faro como referencia.
- Luces puntuales suaves sin sombras, con un tope de 16 visibles a la vez; el resto de la iluminación nocturna es emisión más glow. Evita la iluminación en tiempo real costosa; deja preparado el horneado (LightmapGI por distrito con UV2) como opción posterior y mide el costo.
- Exterior: el suelo de ceniza gris, niebla lejana y partículas de ceniza (GPUParticles3D) alrededor de la cámara cuando está cerca de los muros. Desde los miradores debe verse el paisaje gris. Sin tormenta pesada aún.

G5 · EFECTOS Y SHADERS (todo de TODO_GODOT.txt)
- PORTAL_Veil: shader de agua ondulante azul pálido con transparencia y emisión, con ruido animado y borde brillante.
- FARO_Crystal y FARO_Beam: se dibujan por encima de los edificios (aditivo, sin prueba de profundidad, prioridad de render alta) y una brújula en pantalla (flecha en el borde del HUD) que señala el Faro cuando está fuera de la vista. Pulso suave del cristal.
- Obelisco: las 100 marcas (OBELISK_Mark_001 a 100) con material por instancia, apagadas por defecto; un diccionario de pisos vencidos (en la prueba, enciende los pisos 1 y 2) y una tecla de depuración para encender y apagar cualquiera.
- Runas de la muralla (MAT_Wall_Runes): emisión controlada por una variable global faro_energy (0 a 1) y por la hora (encendidas al anochecer, atenuadas con poca energía). Las linternas azules de las torres y las esquirlas de los faroles siguen esa variable.
- Rueda hidráulica de la Carpintería (WATERWHEEL) girando, agua del Cauce con shader oscuro y simple, humo de las chimeneas (partículas simples), brasas de la Forja (MAT_Embers).
- Transparencia por proximidad: los objetos con occludes_iso=true (módulos de muralla, Salón de las Hazañas, etc.) se aclaran por dithering (alpha hash) cuando quedan entre la cámara y el jugador, con material único por instancia; no cambies el material compartido.

G6 · INTERACCIONES E INTERIORES  → PARADA 2 PARA QUE PRUEBE
- Puertas: un Area3D en cada MARKER_*_Door (interior=true) con aviso "E: entrar". Al entrar: fundido corto, se carga el interior (int_banco.glb y los de Moradas), el jugador aparece en MARKER_Interior_Spawn y la salida (MARKER_Interior_Exit) lo devuelve a la puerta exterior sin errores de posición ni de orientación.
- Dentro: ocultar WALL_Near_*, CEILING y los grupos extra (LEVEL_n, WALL_Near_<Recinto>, CEILING_<Recinto>) según la planta del jugador; colisión y navegación del interior; NPC del Banco (Banquero) como cápsula con etiqueta en su MARKER_NPC_Slot; zonas de interacción (mostrador, bóveda); las cajas del Banco entre BANK_Box_Open y BANK_Box_Locked (40 abiertas de muestra).
- Portal: al acercarse, panel con los 21 pedestales (pisos 1, 5, 10, ... 100) y un aviso "Piso X" al hacer clic. Solo debe funcionar como prueba de interfaz, sin cargar pisos.
- Mercado: interactuables simples (Tablón de Grupos, Fuente) con un mensaje. Entrega la lista de problemas (puertas que no responden, interiores con escala o luz mala, techos que no se ocultan, el jugador atravesando muros). Detente y espera.

G7 · NPC, NAVEGACIÓN Y PRUEBA DE CARGA
- 20 NPC de prueba (cápsulas con etiqueta) que pasean por la malla de navegación entre puntos de las calles y plazas; que no se queden atascados ni crucen edificios.
- Prueba de carga con 100, 300 y 500 jugadores falsos (cápsulas instanciadas con movimiento aleatorio) en la plaza y calles principales, y mide FPS y tiempo de frame con la cámara a 3 niveles de zoom. Objetivo: 60 FPS estables. Lee las especificaciones de mi PC (GPU, CPU, RAM) y repórtalas junto a los resultados.
- Si no se llega al objetivo, perfila (monitores de Godot) y aplica mejoras en este orden: rangos de visibilidad más cortos, menos luces, sombras menos costosas, oclusión, instanciado con MultiMesh en repeticiones (barriles, cajones, tejas), texturas más comprimidas. Reporta antes y después.

G8 · PERSONAJE (solo cuando existan personaje_elfo_base.glb y sus animaciones; si no, sáltate esta fase y dímelo)
- Importa el elfo con retargeting: BoneMap y SkeletonProfileHumanoid, Rest Fixer, normalizar pistas de posición, Fix Silhouette si hace falta, sufijo -loop para las animaciones cíclicas. Reutiliza las animaciones de la Universal Animation Library (CC0) por retargeting. Monta las piezas de ropa sobre el mismo Skeleton3D. Sustituye la cápsula del jugador y prueba el ciclo de caminata, carrera, hechizo y muerte, y la falda y las orejas desde la cámara isométrica.

G9 · INFORME DE PRUEBAS
- TEST_REPORT.md con: resultados por fase, números de rendimiento antes y después, y cada problema clasificado (arreglado en Godot, pendiente en Blender, aceptado) con captura.
- FIXES_BLENDER.md (solo lo que hay que arreglar en los modelos), actualizado.
- TODO_GODOT.txt marcando lo ya hecho.
- Un README_godot.md con cómo abrir el proyecto, las teclas de prueba (F1 HUD, T hora del día, y las que añadas), y cómo regenerar la escena (script de ensamble) tras nuevas exportaciones.

G10 · GIT Y RESPALDO
- Commit con scripts, escenas, shaders y documentos; .gitignore con los binarios; copia de respaldo del proyecto y los assets con MANIFEST. Sin forzar ningún push.

ORDEN: G0 y G1 primero, luego G2 y G3 (parada 1). No empieces G4 hasta que yo responda. Avísame con el informe y las capturas.
```


### Mensaje 60 — 2026-11-11 15:29 — NO TODOS LOS ARCHIVOS ESTAN SUBIDOS EN EL REPOSITORIO NO VEO LOS GLB NI VEO LOS DEMAS ARCH

```text
NO TODOS LOS ARCHIVOS ESTAN SUBIDOS EN EL REPOSITORIO NO VEO LOS GLB NI VEO LOS DEMAS ARCHIVOS NECESITO QUE SUBAS TODO LOS ARCHIVOS ANTES DE SEGUIR CON LO QUE TE PEDI
```


### Mensaje 61 — 2026-11-11 18:54 — Decisiones sobre tu informe:

```text
Decisiones sobre tu informe:

PERMISO NUEVO (amplía mi regla anterior): en Godot puedes arreglar, sin consultarme, ajustes de importación, materiales, shaders, rangos de visibilidad, y generar o rehacer mallas de navegación. Lo que cambie la forma de un modelo se apunta en FIXES_BLENDER.md.

1. MALLA DE NAVEGACIÓN (F8 a F10): genérala en Godot a partir de las colisiones.
   - Parámetros: radio de agente 0,35 m, escalón máximo 0,25 m, pendiente máxima 36° (no 46°: en el diseño las calles tienen ≤ 5° y las escaleras interiores ≤ 35°, y 46° dejaría subir a los NPC por taludes). Celdas de 0,25 m.
   - Una NavigationRegion3D por distrito y por interior, horneada una sola vez y guardada como recurso (.res) para que no se recalcule al iniciar. Deja los parámetros en un script (tools/bake_navmesh.gd) para repetir el horneado cuando cambien los modelos.
   - Los puentes, arcos y escaleras deben quedar conectados a las calles; si una escalera no conecta, añade un NavigationLink3D.
   - La malla "-navmesh" que viene de Blender se queda solo como referencia: compara cobertura y dime dónde difieren.
   - F8 y F9 deben quedar arreglados con esto. F10 (escalones): los que superen 0,25 m van a FIXES_BLENDER.md con gravedad ALTA si están en avenidas, escaleras de acceso o puertas, y BAJA si están en un rincón.

2. ZONAS SIN MALLA (F11).
   - Recorribles: el terreno de las escalinatas, escaleras, puentes y arcos; las franjas junto a la muralla mientras la pendiente sea ≤ 36° y el ancho ≥ 1,2 m (que salga del horneado, sin forzarlo a mano). El camino de ronda de la muralla se hornea aparte, si tiene colisión, y se enlaza con NavigationLink3D en las escaleras junto a cada puerta; el adarve de las puertas no.
   - NO recorribles: el exterior de la muralla (las puertas están selladas y nadie sale), el talud exterior, el foso, los taludes de más de 36°, las caras de los muros de contención y las azoteas de los edificios.
   - Para el exterior, que el jugador no pueda salir: la propia muralla y sus colisiones; verifica que no haya huecos y añade una barrera invisible solo si encuentras alguno.
   - Lista cada zona de F11 con su tamaño y pendiente y dime cuál queda en cada categoría.

3. F6: SÍ, apúntalo en FIXES_BLENDER.md como pendiente de Blender (recortar la rampa bajo cada escalinata), con gravedad MEDIA, salvo que bloquee un paso de jugadores o NPC (entonces ALTA). No lo toques ahora. Te enviaré todo el paquete de arreglos de Blender junto cuando cierres la lista.

4. PENDIENTES DE G4 Y G5 (son de Godot, arréglalos tú):
   - Huertos que se ven como tierra: hace falta el shader de máscaras del terreno. Constrúyelo (ShaderMaterial para el terreno) con COLOR_0 y las máscaras de README_masks.txt (road_mask, retaining_mask, rock_mask, ash_mask, dune_mask, garden_mask, etc.), con la transición suave y las texturas de los materiales de Concordia. Los huertos y jardines (garden_mask) deben verse como tierra labrada con verdes apagados.
   - Haz del Faro y del Crisol: material aditivo con transparencia (alpha ~0,3), sin prueba de profundidad, sin sombras, con textura de degradado que se desvanece hacia arriba. No debe tapar la fuente del Mercado ni los edificios: si el haz del Crisol es corto (sube por el óculo), limita su altura y desvanece su base. Reporta el motivo del bloque opaco (el material exportado, el modo de mezcla…).
   - Obelisco negro: sigue siendo piedra negra pero legible en isométrica. Ajusta el material en Godot: albedo gris muy oscuro azulado (no negro puro), normal map visible, rugosidad 0,6, un ligero reflejo en los bordes (rim o fresnel suave) y las marcas con emisión azul cuando estén encendidas. Si la textura base falta o llega vacía desde el .glb, dímelo y va a FIXES_BLENDER.md.

5. RENDIMIENTO (cifras de G2: 1.270 a 3.104 draw calls, máx 758 mil triángulos, VRAM 437 MB):
   - Objetivos: con el zoom de juego (visión de ~45 m) ≤ 1.200 draw calls y ≤ 300 mil triángulos; con el zoom máximo de 120 m ≤ 2.000 draw calls y ≤ 800 mil. VRAM total ≤ 600 MB incluyendo el motor (130 MB) y las texturas (161 MB, tope 220 MB). Cuando se agreguen personajes (elfo ×100 y más), debe quedar margen: reporta el margen restante.
   - Para las Moradas (lo más caro): rangos de visibilidad más cortos para los LOD, fusionar mallas estáticas por terraza y por material, instanciado con MultiMesh para barriles, cajones, tejas y repeticiones, y oclusión. Hazlo en G7, sin cambiar la forma de los modelos.
   - Desglosa los 437 MB de VRAM (texturas, mallas, sombras, buffers del motor) y dime qué se puede reducir.

6. FPS: las cifras de tu servidor no sirven (sin tarjeta gráfica). Crea tools/benchmark.gd: un recorrido automático por la plaza, el Mercado, las Moradas y el zoom máximo, que escribe benchmark_resultados.txt con FPS promedio, el 1% peor, tiempo de frame, draw calls, triángulos y VRAM por escena, y la información de la GPU y la CPU. Yo lo ejecutaré en mi PC y te pasaré el archivo.

7. G8 (personaje): se salta por ahora, y es lo esperado. Cuando termine el PJ3 y el PJ4 (esqueleto y animaciones) te entregaré personaje_elfo_base.glb; entonces haces G8. Las 10 poses fijas no sirven para probar animaciones.

8. ENTREGA DE ARCHIVOS: como mi carpeta no conecta, haz un paquete para ejecutarlo en mi PC:
   - concordia_godot_paquete.zip (en partes de ≤ 100 MB si pesa mucho) con el proyecto y los assets ya importados, el .gitignore, README_godot.md con los pasos para abrirlo (Godot 4.7.2) y las teclas de prueba.
   - Si el tamaño impide adjuntarlo, dímelo y busco cómo conectar la carpeta en esta sesión (voy a abrir el chat en la aplicación de escritorio y agregar la carpeta desde el "+").

ORDEN: 1) navegación (puntos 1 y 2), 2) los pendientes del punto 4, 3) G4 (luz, cielo, día y noche, ceniza) y G5 (efectos y shaders) con estas decisiones, 4) el benchmark y el paquete para mi PC. Detente ahí: yo pruebo en mi PC (parada 1 ampliada) antes de que hagas G6 (puertas e interiores) y G7. Al entregar, incluye TEST_REPORT.md y FIXES_BLENDER.md actualizados, con cada problema clasificado (arreglado en Godot, pendiente en Blender, aceptado).
```


### Mensaje 62 — 2026-11-11 21:03 — No podemos conectar mi carpeta, así que envíame el proyecto de Godot como adjuntos, en paq

```text
No podemos conectar mi carpeta, así que envíame el proyecto de Godot como adjuntos, en paquetes independientes por carpeta, para descomprimirlos todos en el mismo lugar:

- Cada paquete es un .zip aparte, de máximo 30 MB, con nombre numerado (concordia_01_proyecto.zip, concordia_02_terreno.zip, concordia_03_muralla.zip, ...). Si una carpeta pesa más, divídela en varios zips por subcarpeta.
- Dentro de cada zip, las rutas deben empezar en godot_concordia/ para que, al descomprimir todos en la misma carpeta, quede el proyecto completo.
- El primer paquete (concordia_01_proyecto.zip) lleva solo scripts, escenas, shaders, project.godot y un LEEME.txt con el orden de los paquetes y los pasos para abrirlo en Godot 4.7.2.
- Si algún .glb solo ya pasa de 30 MB, dime cuál y cuánto pesa antes de enviarlo.
- Al final, envíame una lista de los paquetes con su tamaño y qué contiene cada uno.
```


### Mensaje 63 — 2026-11-11 21:31 — Etapa 4: ANIMACIONES del elfo sanador.

```text
Etapa 4: ANIMACIONES del elfo sanador.

1. Descarga la Universal Animation Library de Quaternius, versión Standard (CC0), desde quaternius.com o su mirror en OpenGameArt (si itch.io pide inicio de sesión, usa OpenGameArt). Prueba también la UAL 2 Standard. Verifica que la licencia es CC0 y regístrala. Si una descarga está bloqueada, dímelo y yo la bajo a mano a /assets_manual/.
2. NO retargetees en Blender: Godot lo hace con BoneMap y SkeletonProfileHumanoid. En Blender solo compara la pose de reposo de la UAL con la del elfo, y anota en TODO_GODOT_personaje.txt los ajustes necesarios (Fix Silhouette si una está en A-pose, normalizar pistas de posición, etc.).
3. Del paquete usaremos: Idle, Walk, Run, Sit, Hit, Death y cualquier animación de hechizo que traiga. Lista las que existan y cuáles faltan.
4. Animaciones propias del Sanador, hechas a mano sobre el esqueleto (30 fps, sin movimiento de raíz, nombres claros; las cíclicas con el sufijo -loop para que Godot las marque como bucle):
   - Heal_Cast_Single (0.9 s): extiende la mano derecha con el bastón hacia el frente, pulso de energía y vuelve.
   - Heal_Channel-loop (1.5 s): ambos brazos hacia afuera, postura serena, ligero balanceo.
   - Heal_Cast_Area (1.2 s): brazos hacia arriba y luego hacia abajo como una onda.
   - Revive (2.0 s): se arrodilla y coloca la mano sobre el objetivo.
   Mantén las poses legibles desde la cámara isométrica (gestos amplios). Los efectos visuales y sonoros de cada habilidad se hacen aparte.
5. Cada animación es una Action con fake user, y el rango de frames correcto. Entrega capturas de 3 fotogramas clave por animación, la lista completa y la duración de cada una.
Mixamo queda como opción de reserva si la UAL no cubre algo: la cuenta y la descarga las hago yo, tú no inicies sesión.
```


### Mensaje 64 — 2026-11-11 21:50 — Etapa 5: LODs, EXPORTACIÓN y cierre del personaje.

```text
Etapa 5: LODs, EXPORTACIÓN y cierre del personaje.

1. LODs: LOD0 ≤ 10.000, LOD1 ≤ 5.000, LOD2 ≤ 1.800 triángulos (el LOD2 es una sola malla con el esqueleto simplificado). Mantén la silueta de las orejas y el dobladillo en todos los LODs.
2. Exportación glTF 2.0 (.glb), +Y Up, con esqueleto: personaje_elfo_base.glb (esqueleto, cuerpo modular, ojos y cabello) y una pieza por equipo (elfo_sanador_robe_top.glb, elfo_sanador_skirt.glb, elfo_sanador_hood.glb, elfo_sanador_boots.glb, etc.) con el MISMO esqueleto y los mismos nombres de hueso, para que Godot los monte sobre el mismo Skeleton3D. Animaciones propias en elfo_sanador_anims.glb.
3. Materiales: 3 como máximo, texturas 1K (albedo, normal, ORM). Emisión solo en el colgante.
4. Documentos: ASSETS_LICENSES.md actualizado (MakeHuman, UAL, cualquier otra fuente); README_personaje.txt con la lista de huesos, vertex groups HIDE_*, convención de nombres y presupuesto real; TODO_GODOT_personaje.txt con los pasos de importación (BoneMap y SkeletonProfileHumanoid, Rest Fixer, Normalize Position Tracks, Fix Silhouette si hace falta, suffix -loop, retargeting de las animaciones de la UAL).
5. Guarda concordia_personajes_master.blend con versión y copia de respaldo con MANIFEST (sha256).
Entrega: lista de archivos con tamaño, triángulos por LOD, y una checklist de 10 puntos para probar en Godot (el personaje camina, se equipa la ropa, las animaciones de la UAL retargeteadas funcionan, la falda no atraviesa las piernas, las orejas se leen en isométrica, etc.).
```


### Mensaje 65 — 2026-11-11 22:04 — Decisiones sobre las animaciones (PJ4):

```text
Decisiones sobre las animaciones (PJ4):

1. ANDAR HACIA ATRÁS Y DE LADO: no las cubras con Mixamo por ahora.
   - Hacia atrás: usa Walk reproducida al revés (en Godot, velocidad de reproducción negativa, ~-0.6) con el mismo clip, sin duplicarlo. Anótalo en TODO_GODOT_personaje.txt para el AnimationTree.
   - De lado: usa Walk/Run mezcladas en un BlendSpace2D de Godot, con el personaje girando hacia la dirección de movimiento (como en la mayoría de MMO isométricos). No hacen falta clips laterales por ahora. 
   - Antes de dar esto por cerrado, comprueba si la versión Standard (gratuita) de la UAL 1 o la UAL 2 incluye locomoción en 8 direcciones. Si solo viene en las versiones de pago (Pro o Source), NO las compres: todo debe ser gratis.

2. GIRAR EN EL SITIO: no hace falta clip. Godot gira al personaje por código (rotación suave hacia el destino) mientras reproduce Idle. Anótalo en TODO_GODOT_personaje.txt.

3. SEGUNDA MUERTE: hazla tú reflejando la muerte existente (espejo izquierda-derecha de la acción en Blender, con las pistas de huesos intercambiadas) y ajusta la caída para que no sea idéntica (otro giro de cabeza, distinta posición de brazos). Nómbralas Death_A y Death_B. Si queda mal, déjalo con una sola muerte; no hagas animación a mano de cero para esto.

4. LEVANTARSE DEL SUELO: APROBADO usar LayToIdle de la UAL 2 como apaño. Nómbralo GetUp y comprueba que enlaza con Death (termina en la pose del suelo que usa Death) sin salto brusco; si salta, añade 6 a 8 fotogramas de transición.

5. EXTRAS DE LA UAL 2: APROBADAS Consume (comer o beber), Yes, Idle_No, Idle_FoldArms_Loop y Chest_Open. Úsalas así: Consume para raciones y pociones, Chest_Open para cofres y las cajas de la bóveda del Banco, Idle_FoldArms_Loop como variación de espera, Yes e Idle_No como emotes. Todas con el sufijo -loop si son cíclicas.

6. MIXAMO: queda de reserva, no la uses ahora. Si más adelante hace falta algo concreto (girar en el sitio, golpes de otras armas), te lo pido y yo bajo las animaciones con mi cuenta.

7. REGISTRO: añade a ASSETS_LICENSES.md qué animaciones vienen de la UAL 1 y de la UAL 2 (CC0), con URL y fecha, y confirma que todo lo descargado es de la versión Standard gratuita.

8. Entrégame la lista final de animaciones del elfo sanador (nombre, duración, origen: UAL 1, UAL 2 o hecha a mano, y si es cíclica) y sigue con el PJ5 (LODs, exportación y registro).
```


### Mensaje 66 — 2026-11-11 22:26 — <command-name>/model</command-name>

```text
<command-name>/model</command-name>
            <command-message>model</command-message>
            <command-args>claude-fable-5-2</command-args>
```


### Mensaje 67 — 2026-11-11 22:26 — <local-command-stdout>Set model to `claude-fable-5-2`</local-command-stdout>

```text
<local-command-stdout>Set model to `claude-fable-5-2`</local-command-stdout>
```


### Mensaje 68 — 2026-11-11 22:26 — Vamos a hacer el resto de INTERIORES de Concordia. Reutiliza el kit de interior (BLD_INT_K

```text
Vamos a hacer el resto de INTERIORES de Concordia. Reutiliza el kit de interior (BLD_INT_KIT), la función build_interior y las 12 lecciones del piloto del Banco (sección 18 de README_buildings.txt). Un interior a la vez, en este orden de prioridad: 1) Tesorería de la Muralla, 2) Santuario del Retorno, 3) Casa de Reposición, 4) Crisol de las Piedras, 5) Posada, 6) Casa del Registro, 7) Salón de las Hazañas, 8) Gran Forja, 9) gremios y talleres, 10) salón de clase (plantilla), 11) Casa de Raza (plantilla).

ANTES DE EMPEZAR (no modifiques nada todavía):
1. Lista todos los MARKER_*_Door con interior=true, con su InteriorVolume, y los interiores ya hechos (Banco y las 3 plantillas de Morada). Agrúpalos: únicos (Tesorería, Santuario, Crisol, Salón, Gran Forja, Posada, Registro, Casa de Reposición), plantillas (gremios, talleres, salones de clase, Casas de Raza). Dime cuántos son y cuáles de los pendientes no tienen puerta o volumen. Espera mi confirmación.

REGLAS COMUNES:
- Archivo nuevo por interior: int_<nombre>.glb. Origen en la puerta, piso en Z=0, tamaño igual al InteriorVolume (±0.2 m).
- Cámara isométrica: calcula con CAM_Iso los dos muros cercanos (WALL_Near_A, WALL_Near_B), el techo (CEILING) y los grupos extra (LEVEL_n, WALL_Near_<Recinto>, CEILING_<Recinto>) ocultables. Lo importante (NPC, mostrador, objeto de interacción) debe verse desde CAM_Iso, comprobado con rayos, y ninguna columna o arco debe taparlo.
- Marcadores (+Y local al frente): MARKER_Interior_Exit en la puerta, MARKER_Interior_Spawn, MARKER_NPC_Slot_xx (propiedad npc), MARKER_Interact_xx (propiedad tipo), MARKER_WorkStation_xx (oficios).
- Colisión "-colonly", navegación "-navmesh" con celdas de 0,25 m, pasillos ≥ 1,2 m, escaleras ≤ 35°, nada coplanar.
- Presupuesto ≤ 40.000 triángulos por interior (shell más props). Texturas 1K. Materiales de Concordia. Solo un azul pálido (#8FD0FF) por sala; luz cálida natural el resto (emisión ≤ 1,0).
- Props: solo los aprobados en ASSETS_LICENSES.md (Quaternius y Avramania) y los hechos a mano. Lo singular, a mano.
- Aspecto remendado, igual que el exterior. Cada interior que modeles debe encajar con su fachada.
- Entrega por interior: capturas isométrica y a altura de personaje (con muros cercanos ocultos), triángulos reales, resultados de los rayos (NPC e interacciones visibles), y las lecciones nuevas.
Confirma que entendiste y haz el punto 1.
```


### Mensaje 69 — 2026-11-11 22:47 — <command-name>/model</command-name>

```text
<command-name>/model</command-name>
            <command-message>model</command-message>
            <command-args>claude-opus-5-5</command-args>
```


### Mensaje 70 — 2026-11-11 22:47 — <local-command-stdout>Set model to `claude-opus-5-5`</local-command-stdout>

```text
<local-command-stdout>Set model to `claude-opus-5-5`</local-command-stdout>
```


### Mensaje 71 — 2026-11-11 22:50 — Vamos a hacer el resto de INTERIORES de Concordia. Reutiliza el kit de interior (BLD_INT_K

```text
Vamos a hacer el resto de INTERIORES de Concordia. Reutiliza el kit de interior (BLD_INT_KIT), la función build_interior y las 12 lecciones del piloto del Banco (sección 18 de README_buildings.txt). Un interior a la vez, en este orden de prioridad: 1) Tesorería de la Muralla, 2) Santuario del Retorno, 3) Casa de Reposición, 4) Crisol de las Piedras, 5) Posada, 6) Casa del Registro, 7) Salón de las Hazañas, 8) Gran Forja, 9) gremios y talleres, 10) salón de clase (plantilla), 11) Casa de Raza (plantilla).
ANTES DE EMPEZAR (no modifiques nada todavía):

1. Lista todos los MARKER_*_Door con interior=true, con su InteriorVolume, y los interiores ya hechos (Banco y las 3 plantillas de Morada). Agrúpalos: únicos (Tesorería, Santuario, Crisol, Salón, Gran Forja, Posada, Registro, Casa de Reposición), plantillas (gremios, talleres, salones de clase, Casas de Raza). Dime cuántos son y cuáles de los pendientes no tienen puerta o volumen. Espera mi confirmación.

REGLAS COMUNES:

* Archivo nuevo por interior: int_<nombre>.glb. Origen en la puerta, piso en Z=0, tamaño igual al InteriorVolume (±0.2 m).
* Cámara isométrica: calcula con CAM_Iso los dos muros cercanos (WALL_Near_A, WALL_Near_B), el techo (CEILING) y los grupos extra (LEVEL_n, WALL_Near_<Recinto>, CEILING_<Recinto>) ocultables. Lo importante (NPC, mostrador, objeto de interacción) debe verse desde CAM_Iso, comprobado con rayos, y ninguna columna o arco debe taparlo.
* Marcadores (+Y local al frente): MARKER_Interior_Exit en la puerta, MARKER_Interior_Spawn, MARKER_NPC_Slot_xx (propiedad npc), MARKER_Interact_xx (propiedad tipo), MARKER_WorkStation_xx (oficios).
* Colisión "-colonly", navegación "-navmesh" con celdas de 0,25 m, pasillos ≥ 1,2 m, escaleras ≤ 35°, nada coplanar.
* Presupuesto ≤ 40.000 triángulos por interior (shell más props). Texturas 1K. Materiales de Concordia. Solo un azul pálido (#8FD0FF) por sala; luz cálida natural el resto (emisión ≤ 1,0).
* Props: solo los aprobados en ASSETS_LICENSES.md (Quaternius y Avramania) y los hechos a mano. Lo singular, a mano.
* Aspecto remendado, igual que el exterior. Cada interior que modeles debe encajar con su fachada.
* Entrega por interior: capturas isométrica y a altura de personaje (con muros cercanos ocultos), triángulos reales, resultados de los rayos (NPC e interacciones visibles), y las lecciones nuevas.
Confirma que entendiste y haz el punto 1.

INTERIOR 1: TESORERÍA DE LA MURALLA (28x18, 2 plantas).
REFERENCIAS: Palazzo Pubblico de Siena (salas macizas con arcos y bóvedas, luz tamizada) y gran salón medieval de piedra (muros altos, vigas, poca luz).
Función: compra esquirlas a precio fijo y cambia plata por oro (1 de oro = 100 de plata). Los tubos de luz azul del techo hacia el Faro se ven entrar por el techo.

* Planta baja: vestíbulo con 2 mostradores de piedra y madera (taquillas con reja de ventanilla abierta frente al NPC, como en el Banco). Tesorero (MARKER_NPC_Slot_01, npc=Tesorero), balanzas de bronce grandes sobre cada mostrador.
* Vitrinas con esquirlas de todos los tipos (Opaca, Brillante, Latente, Madura): 4 vitrinas (hechas a mano, ≤ 800 triángulos, 3 variantes) con esquirlas instanciadas (cristales pequeños, un material cada tipo: Opaca gris, Brillante azul tenue, Latente azul medio, Madura azul pálido emisivo). Solo el color azul pálido de las más maduras brilla.
* Tubos de luz: 4 tubos de 0,4 m que suben por columnas y atraviesan el techo (PIPE_Light_*), con emisión azul 1,5, de modo que el color mágico es el único acento.
* Planta alta: galería con balaustrada que da al vestíbulo, despacho del tesorero, caja fuerte (a mano, ≤ 1.000 triángulos), escalera de piedra.
* Interacción: MARKER_Interact_Tesoreria_Vender (mostrador 1) y MARKER_Interact_Tesoreria_Cambio (mostrador 2).

INTERIOR 2: SANTUARIO DEL RETORNO (16x12, con porche +Y).
REFERENCIAS: interior de la Sainte-Chapelle (nave alta y estrecha, vitrales azules muy altos, columnas esbeltas, techo azul con estrellas). Copia verticalidad, vitrales y la luz azul filtrada.
Función: punto de reaparición tras morir.

* Nave única de 14 m de alto con 5 ventanales altos por lado (vitral azul pálido con emisión 0,6 y tracería de piedra), contrafuertes interiores, bóveda nervada simple.
* Pozo de agua limpia en el centro (SANTUARIO_Well, ya modelado: colócalo aquí y quita provisional=true): brocal de piedra de 2 m, agua oscura quieta (material MAT_Water), un solo farol de esquirla azul sobre el pozo.
* Cuidador del Santuario (MARKER_NPC_Slot_01, npc=Cuidador) junto al pozo, mesa pequeña con 3 raciones y 3 antorchas (kit mínimo gratis, props aprobados). Bancos de madera (8) a ambos lados.
* MARKER_Interior_Spawn de reaparición (nuevo marcador MARKER_Respawn) frente al pozo, que debe verse sin obstáculos desde CAM_Iso. Es lo primero que ve el jugador que murió: la sala debe sentirse serena y legible.
* Sin color mágico fuera del azul de los vitrales y del pozo.

INTERIOR 3: CASA DE REPOSICIÓN "EL REMIENDO" (24x12).
REFERENCIAS: gran salón medieval de piedra y madera (vigas a la vista) y tiendas de armeros históricos (perchas, estantes).
Función: vende equipo básico de calidad normal por clase a precio bajo y fijo.

* Tienda larga con mostrador en U, perchas de armaduras remendadas en las paredes (8 maniquíes-perchas con piezas de cada clase: tela, cuero, malla), estantes con espadas viejas pulidas, escudos, cajones de botas y capas. Vendedor (MARKER_NPC_Slot_01, npc=Reposicion).
* Letrero con un parche cosido. Aspecto muy remendado (la tienda de las cosas arregladas).
* Interacción: MARKER_Interact_Reposicion. Props aprobados de Quaternius (armero, escudos, espadas) más estantes del kit.
```


### Mensaje 72 — 2026-11-11 22:53 — El proyecto de Godot NO abre bien en mi PC. Lo ejecuté en Godot 4.7.2 (Forward+, Vulkan 1.

```text
El proyecto de Godot NO abre bien en mi PC. Lo ejecuté en Godot 4.7.2 (Forward+, Vulkan 1.3, tarjeta integrada AMD Radeon Graphics, memoria compartida). Estos son los errores reales:

1. Se detiene en el depurador: "Out of bounds get index '0' (on base: 'Array')" en res://scripts/materials_fix.gd:96, función _beams. Hay un arreglo vacío (probablemente la malla o superficie de FARO_Beam o del haz del Crisol, que llega vacía).
2. Cientos de errores "Size of vertex data provided (0) does not match expected (N)" en mesh_add_surface: mallas que llegan vacías a la tarjeta.
3. Miles de "Can't create buffer of size N (VkResult error -10)" (VK_ERROR_TOO_MANY_OBJECTS): hay demasiados buffers de malla (la escena tiene unos 16.000 nodos con mallas sueltas).
4. Aviso menor: parámetro "unit_depth" sin usar en add_scene_root() de lod_manager.gd:25.

HAZ ESTO, EN ORDEN (todo gratis, sin tocar los .blend):
A. Corrige materials_fix.gd:96: valida que el arreglo no esté vacío y que cada nodo y malla existan antes de usarlos (is_instance_valid, size() > 0). Busca el mismo patrón de acceso a [0] en todos los scripts y blíndalos. Si FARO_Beam o el haz del Crisol no tienen malla, averigua por qué (importación del .glb, nombre de nodo, material) y dime la causa.
B. Averigua por qué llegan mallas vacías (errores 2): revisa los ajustes de importación de los .glb, si algún script reconstruye ArrayMesh sin datos, si lod_manager.gd o el ensamblador generan mallas desde superficies vacías, y si hay archivos .glb corruptos o incompletos (compara con MANIFEST sha256 y los tamaños). Reporta cuáles son y por qué.
C. Reduce el número de objetos de GPU, que es la causa del error -10: fusiona las mallas estáticas por distrito y por material (una malla por material y por chunk), usa MultiMesh para repeticiones (barriles, cajones, tejas, farolillos, ventanas, pretiles), mantén separados solo los techos (para ocultarlos), los objetos con occludes_iso y los animables. Objetivo: menos de 3.000 mallas en toda la escena en LOD0 y menos de 1.000 visibles a la vez.
D. Carga por distrito y por distancia: la escena inicial solo instancia la plaza y lo que está a menos de 120 m; el resto se carga y descarga por distrito (con carga en un hilo) y con rangos de visibilidad cortos. No cargues las 4 Moradas completas al iniciar.
E. Añade un menú de calidad (tecla F2): Bajo (para mi gráfica integrada: sin sombras, rangos de visibilidad cortos, resolución al 70%, sin glow), Medio y Alto. Que el juego arranque en Bajo si detecta una gráfica integrada (comprueba el nombre del dispositivo con RenderingServer.get_video_adapter_name()). Compara también el renderizador Compatibility y dime si es mejor para mi PC.
F. Los números de G2 (VRAM, draw calls) se midieron en un servidor SIN tarjeta gráfica y no valen. Rehaz el benchmark (tools/benchmark.gd) para que lo ejecute yo en mi PC y lo dejaré en benchmark_resultados.txt. Un objetivo realista para mi gráfica integrada: 30 FPS estables en Bajo; el objetivo de 60 FPS con 500 jugadores es para tarjetas dedicadas.

ENTREGA: no me mandes el proyecto entero. Mándame SOLO los archivos cambiados (scripts, escenas .tscn, ajustes) en un .zip pequeño, con las rutas relativas a godot_concordia/ para descomprimirlo encima, y una lista de qué cambió en cada archivo. Si cambias ajustes de importación de los .glb (.import), dime exactamente cuáles y qué valor. Yo lo descomprimo en C:\Users\USER\Desktop\Juego_1\Concordia\godot_concordia y lo pruebo.
```


### Mensaje 73 — 2026-11-11 23:54 — Decisiones sobre el inventario de interiores:

```text
Decisiones sobre el inventario de interiores:

INVENTARIO: confirmado. 34 edificios con interior: 4 hechos y 30 pendientes. Las puertas de las torres, la del Faro, las de RAZ_B05 y la de TEST_Casa_12x9 no son interiores.

1. CASA DE REPARACIONES: SÍ, interior único, después del Registro. Es un taller abierto de 15,0 x 9,0 x 3,4 m: bajo, con vigas a la vista, yunque, pared de herramientas (TOOL_Rack) y un banco largo. Un solo azul por sala (un farol de esquirla).

2. MEDIDAS: SÍ, se construye con el volumen interior (±0,2 m en planta), no con la huella exterior de las fichas.

3. TESORERÍA: SÍ, dos plantas de unos 4,4 m (26,4 x 13,6 x 8,8 m).

4. SANTUARIO: SÍ, con una condición. Los muros miden 9 m (el volumen interior) y la bóveda nervada puede subir hasta 14 m dentro del espacio de la cubierta, como en la Sainte-Chapelle, SOLO SI ese tramo por encima de los 9 m va en el grupo CEILING (ocultable) y no se sale por la cubierta exterior (comprueba que no atraviese el techo, con una captura). Si choca con el exterior, baja la bóveda hasta que no choque y dímelo. La huella (13,8 x 9,6 m) sigue dentro de ±0,2 m.

5. GRAN FORJA: NO subas la nave a 6 m sin comprobar. Primero revisa la altura real del exterior (muros y alero de la Gran Forja):
   a) Si el exterior es más alto que el volumen (muros de 6 m o más), el volumen estaba mal calculado: avísame, corrige el InteriorVolume y construye la nave a esa altura.
   b) Si el exterior es bajo (alero cerca de los 3,2 m), mantén 3,2 m con vigas bajas y NO cambies el exterior ni el volumen. Resuelve el aire con una campana de chimenea alta (la campana sube hasta el hueco de la chimenea de 14 m, visible por la parte alta) y un respiradero (lucernario) en el techo. El patio de fundición abierto queda fuera, como dices.
   Dime qué caso es antes de construir esa sala, con las dos alturas medidas.

6. PLANTILLAS: SÍ, una plantilla por tipo que se ajuste al volumen de cada edificio, más una variante pequeña para la Casa de Raza 05 (9,52 x 9,52 x 3,6). Gremios y talleres con medidas distintas: no los estires ni los deformes, construye cada uno con su volumen. La torre de Alquimia (5,5 x 5,5 x 12,8) se resuelve apilando plantas con escalera de caracol, y la Curtiduría (15,1 x 6,1) como sala larga.

ORDEN: Tesorería, Santuario, Casa de Reposición, Crisol, Posada, Registro, Casa de Reparaciones, Salón de las Hazañas, Gran Forja, gremios y talleres, salones de clase (8) y Casas de Raza (6).
Empieza por la Tesorería. Entrega cada interior completo (capturas isométrica y a altura de personaje, triángulos, rayos, lecciones). Haz Tesorería y Santuario seguidos, y me mandas el informe de los dos antes de seguir. Después, de tres en tres, salvo que haya un problema bloqueante, en cuyo caso paras y me avisas. Mantén las reglas comunes, los props aprobados y las lecciones del Banco.
```


### Mensaje 74 — 2026-11-12 12:20 — Inténtalo de nuevo

```text
Inténtalo de nuevo
```


### Mensaje 75 — 2026-11-12 12:39 — Voy a migrar este proyecto a otra conversación con acceso local a mi carpeta. No modifique

```text
Voy a migrar este proyecto a otra conversación con acceso local a mi carpeta. No modifiques nada del modelo.
Genera UN archivo CONCORDIA_OPUS_TRASPASO.md con todo lo que sabes del proyecto, sin resumir de más:

1. Estado por etapa (E0–E28): qué está hecho, qué parcial, qué pendiente, con cifras (edificios, triángulos, memoria de texturas).
2. Todas las decisiones tomadas y su motivo (muralla, Moradas, Faro, Razas, interiores, props, fuentes de assets, personaje elfo, animaciones).
3. Las convenciones: nombres de objetos, sufijos (-colonly, -navmesh, -occ, _LOD0/1/2), marcadores (+Y = frente), grupos ocultables, cámara iso, paleta y materiales (MAT_*).
4. Las 12 lecciones de README_buildings.txt (sección 18) y todas las demás reglas que hayas anotado.
5. Todos los prompts maestros y de etapa que me diste, tal cual (para poder reutilizarlos).
6. Lista de decisiones pendientes que esperan mi respuesta.
7. Inventario de archivos: ruta, tamaño y para qué sirve cada uno (.blend, .glb, atlas, capturas, MANIFEST, README, informes).
8. Cómo se reconstruye cada cosa desde cero: scripts de Blender que usaste, funciones como build_interior(nombre, volumen, estilo, seed), y el orden de ejecución.
9. Qué tareas quedaron a medias y en qué punto exacto.

Además, entrégame para descargar: concordia_v25.blend (o la última versión), todos los .glb exportados, el atlas de las cajas, MANIFEST.txt/manifest.json, README_buildings.txt, ASSETS_LICENSES.md y las capturas más recientes. Si algún archivo es muy grande, dime cómo bajarlo por partes.
Al final, dime qué NO pudiste incluir.
```


## Anexo B — README_buildings.txt (edificios, materiales, lecciones §18–20, balance §19)

```text
CONCORDIA - Edificios y materiales nuevos (kit, Portal y landmarks)
==================================================================
Actualizado en la etapa 27 (concordia_v26.blend; interiores en concordia_interiors_v01.blend). Auditoria automatica: tools/blender/audit_materials.py ->
docs/reports/stage17_materials.json.

1. Regla de aprobacion de materiales nuevos
-------------------------------------------
Un material nuevo del kit de edificios, del Portal o de un landmark queda aprobado si cumple las tres condiciones:
  a) Paleta: nada saturado fuera del azul palido. Prueba: saturacion HSV <= 0.35, salvo tonos 185-215 grados (azul).
     El unico color magico fuerte es #8FD0FF.
     UNICA excepcion calida (decision del usuario, etapa 25): MAT_Embers (brasas y metal fundido, #E09A62, s 0.57).
     Solo en fundicion, hornos e interior visible de chimeneas: Gran Forja, Hornos de Concordia y chimeneas de la
     Posada y de la Forja. Emision <= 1.5, nunca azul ni mezclado con MAT_Shard_Blue, < 2 % de la superficie visible
     de cada edificio. La prueba de saturacion ignora SOLO ese material (build_stage24.embers_check comprueba los
     limites). Ningun otro material usa naranja saturado: toldos, telas y banderas siguen en tierras apagadas.
  b) Export: grafo Image Texture -> Principled BSDF, o valores planos. Las variantes de tono usan Mix (Multiply) con
     un color constante: el exportador glTF lo escribe como baseColorFactor junto a la textura (comprobado en los
     .glb). No hay otros nodos.
  c) Memoria total de texturas de la ciudad <= 220 MB (Godot 4, VRAM Compressed: albedo/ORM/emision BC1 0.5 B/px,
     normal BC5 1 B/px, mipmaps x4/3). Etapa 17: 53 imagenes, 154.7 MB. Si un material nuevo la pasa de 220 MB,
     se avisa antes de seguir.

2. Materiales nuevos (valores de emision y alpha)
-------------------------------------------------
Colores en sRGB. "Fuerza" = Emission Strength de Blender = KHR_materials_emissive_strength del glTF (si es 1.0 o
menos, el glTF lo guarda multiplicado en emissiveFactor).

Material                 Uso                               Base / textura                       Emision         Alpha / mezcla
-----------------------  --------------------------------  -----------------------------------  --------------  ----------------
MAT_Roof_Tile_Ocher_B    tejas de reparacion (otro tono)   textura de MAT_Roof_Tile_Ocher       -               1.0 opaco
                                                           x baseColorFactor (0.80,0.74,0.68)
MAT_Window_Warm          ventanas (luz natural, no magica) #35302C plano                        #AD9072  1.0    1.0 opaco
                                                           (etapa 17: emision #AD865D sat 0.46 -> #AD9072 sat 0.34)
MAT_Portal_Veil          velo del Portal                   #8FD0FF plano                        #8FD0FF  3.0    0.6 BLEND, 2 caras
MAT_Rune_Glow_12         runas y canales de luz            #8FD0FF plano                        #8FD0FF  1.2    1.0 opaco
MAT_Rune_Glow_10         runas del Atrio                   #8FD0FF plano                        #8FD0FF  1.0    1.0 opaco
MAT_Obelisk_Black        piedra del Obelisco               textura x baseColorFactor            -               1.0 opaco
                                                           (0.16,0.16,0.165), roughness 0.8
MAT_Obelisk_Mark         marca de piso apagada             #4A4A4A plano                        -               1.0 opaco
MAT_Obelisk_Mark_Lit     marca de piso encendida           #8FD0FF plano                        #8FD0FF  3.0    1.0 opaco
MAT_Shard_Blue_E40       cristal del Faro                  = MAT_Shard_Blue (mismas texturas)   #8FD0FF  4.0    1.0 opaco
                         (deriva de MAT_Shard_Blue: copia; solo cambia la fuerza de emision 2.5 -> 4.0)
MAT_Faro_Beam            haz del Faro                      #8FD0FF plano                        #8FD0FF  1.5    0.3 BLEND, 2 caras
                                                           (aditivo en Godot: ver TODO_GODOT.txt)
MAT_Pipe_Glass           vidrio de las tuberias de luz     #C9DDE6 plano, roughness 0.08        -               0.35 BLEND, 2 caras
MAT_Pipe_Light_Core      nucleo de las tuberias de luz     #8FD0FF plano                        #8FD0FF  1.5    1.0 opaco
MAT_Limestone_Light      caliza clara del Santuario        albedo horneado propio               -               1.0 opaco
                         textures/concordia/MAT_Limestone_Light/concordia_limestone_light_albedo.png (2K, media
                         sRGB 0.72 -> 0.82); ORM y normal de MAT_Limestone_Worn. +2.7 MB de VRAM.
MAT_Stained_Glass_Blue   vitrales (Santuario y Salon)      #4F80AD plano, roughness 0.18        #7DB5E5  0.6    1.0 opaco
MAT_Bronze_Aged          placas de bronce del Salon        #73644C plano, metallic 0.85,        -               1.0 opaco
                                                           roughness 0.5
                                                           (etapa 17: #735C38 sat 0.51 -> #73644C sat 0.34)

Etapa 21 (Razas; todos pasan la paleta: saturacion <= 0.35 o tono 185-215; ver docs/reports/stage21_razas.json)
MAT_Wood_Light           madera clara (R02, yurtas R05)    albedo horneado propio (#A4947C,     -               1.0 opaco
                                                           s 0.24) de MAT_Wood_Dark; 1K, +0.67 MB de VRAM
MAT_Roof_Slate           pizarra gris (R01)                albedo horneado propio (#6D6F74,     -               1.0 opaco
                                                           s 0.06) de la teja ocre; 1K, +0.67 MB de VRAM
MAT_Roof_Slate_B         pizarra de reparacion             Slate x (0.84,0.84,0.86)             -               1.0 opaco
MAT_Roof_Slate_Blue      pizarra azulada (R04)             Slate x (0.74,0.88,1.0) #5F6974      -               1.0 opaco
MAT_Roof_Shingle_Dark(_B) teja oscura (R03)                teja ocre x (0.50,0.43,0.39) /       -               1.0 opaco
                                                           (0.42,0.37,0.34); #725D4B s 0.34
MAT_Stone_R01            piedra gris (R01)                 caliza x (0.80,0.80,0.82)            -               1.0 opaco
MAT_Stone_Sand           arenisca (R06)                    caliza x (1.0,0.90,0.76) #C3B195     -               1.0 opaco
MAT_Felt_R05             fieltro de yurta                  Cloth_Patch_A x (1.0,0.98,0.92)      -               1.0 opaco
MAT_Hide_R05             pieles y cuero (R05)              Cloth_Patch_A x (0.62,0.48,0.37)     -               1.0 opaco
MAT_Glass_R04            vidrio de R04 (laminas delante    #A9C9DC plano (copia de              #8FD0FF  0.25   0.35 BLEND
                         del cristal calido; linterna)     MAT_Pipe_Glass), roughness 0.08
MAT_Leaf_Old             hojas del arbol viejo             #5F6B4E plano (s 0.27)               -               1.0 opaco
MAT_Banner_R01..R06      estandarte y bandera de la raza   textura generada 512 x 1024 por      -               1.0, 2 caras
                                                           raza (+0.35 MB de VRAM cada una)
Memoria de texturas tras la etapa 21: ~160.8 MB (154.7 + 8 estandartes de clase + 2 albedos + 6 estandartes de raza).

Etapa 23 (Moradas; sin texturas nuevas, todos pasan la paleta)
MAT_Facade_Earth_A/B/C   fachadas de las Moradas           caliza clara x (1.0,0.89,0.72) /     -               1.0 opaco
                                                           (0.98,0.84,0.76) / (0.90,0.90,0.81)
MAT_Door_Paint_01..06    pintura de DOOR_Morada            madera clara x factor (s <= 0.31)    -               1.0 opaco
MAT_Door_NumberPlate     placa de numero (decal encima)    #D9D3C4 plano                        -               1.0 opaco

Etapa 25
MAT_Crisol_Molten        cuenco del Crisol (piedra fundida  #39404A plano, roughness 0.6         #8FD0FF  1.2    1.0 opaco
                         magica; antes MAT_Embers)
MAT_Embers (etapa 19)    brasas: Gran Forja y Hornos        #A67148 plano                        #E09A62  1.5    1.0 opaco
                         (excepcion calida, seccion 1a)

Ya existentes y con emision: MAT_Shard_Blue (#8FD0FF, 2.5; farolillos de esquirla). MAT_Water: sin emision.

3. Convencion de piezas por edificio
------------------------------------
  <NOMBRE>                    Empty raiz en el marcador (+Y = door_direction)
  <NOMBRE>_Body               cuerpo unido, por materiales; UV metrica de caja (1 m = 1 unidad)
  <NOMBRE>_Roof               cubierta, objeto aparte
  <NOMBRE>_Props              Empty con instancias (malla compartida)
  <NOMBRE>_Body_LOD1 / _LOD2  50 % / 15 % (diezmado o kit simplificado)
  MARKER_<Nombre>_Door        Empty en la puerta, +Y hacia fuera (si interior = true)
  <Nombre>_InteriorVolume     caja sin render con el volumen interior
  <NOMBRE>-colonly            colision (caja o cilindros)
Si el nombre de un marcador del archivo no coincide con el del prompt, se usa el del archivo (ej.:
MARKER_Bld_TesoreriaMuralla en lugar de MARKER_Bld_Tesoreria).

4. Regla de alturas (etapa 17; sustituye a la regla "2 plantas en el lado de la camara")
-----------------------------------------------------------------------------------------
  - Hasta 3 plantas (<= 10.5 m; con el kit, alero a 9.6 m). La torre de Alquimia (use="alchemy_tower") hasta 4.
  - Manda la prueba de visibilidad desde CAM_Iso: si el edificio tapa la puerta de otro edificio (MARKER_*_Door, o el
    frente de un MARKER_Bld_* aun sin construir) o un carril de NPC (curvas NPC_Lane_*), se reconstruye con una
    planta menos hasta que deje de taparla, como minimo 2 plantas (7 m; alero a 6.4 m con el kit).
    Prueba: rayo desde el punto (a 1.0 m del suelo) hacia la camara contra el LOD0 del edificio.
  - Los hitos (Portal, Faro, Obelisco, Santuario, Salon de las Hazanas) quedan fuera de la regla.
  - Codigo: concordia_buildings.fit_iso_height(nombre, pisos, ...) -> rep["iso_rule"] = historial de plantas y lo que
    tapaba en cada intento. Si a 2 plantas aun tapa algo, se marca still_blocking = true y se avisa.
  - Comprobado en la etapa 17 con una casa de 12 x 9 m: una puerta 7.5 m detras (en la vista) baja la casa de 3 a 2
    plantas; sin nada detras se queda en 3.

5. Faro (decisiones de la etapa 17)
-----------------------------------
  - Rampa decorativa: sin navegacion; colision solo en el arranque de la escalera por debajo de 3 m
    (FARO_Ramp-colonly: los 16 peldanos de 0.2 a 3.0 m) + el cilindro de la torre (FARO-colonly). Raiz FARO: navigation = false.
  - Ultima vuelta (+29.5 a +32) separada del fuste y apoyada en cartelas de piedra cada 22.5 grados (con zapata);
    barandilla exterior continua (pasamanos a 1.05 m + barra a 0.55 m) y barandilla interior en el tramo separado.
  - Canales: los 4 canales de la torre arrancan sobre los 4 de la plaza (desfase lateral 0 cm). Los de +-1.8 m
    bajan por el zocalo encima del canal. Los de +-0.6 m chocan con el umbral de la puerta (+-1.45 m): bajan junto
    a la portada (x = +-1.55 m) y se unen a su canal con una L sobre el pavimento delante del umbral.
  - CRV_LightPipe_Tesoreria_Faro: el primer punto es provisional (MARKER_PipeOutlet_TesoreriaMuralla,
    provisional = true). En E5, la salida de tubos del tejado de la Tesoreria debe quedar a +9.6 m (+-0.5 m) y ese
    punto se mueve a la salida real.

6. LOD2 de lejos (pendiente D, etapas 17-18)
-------------------------------------------
Prueba con CAM_Iso a ortho 45 y 120 (docs/captures/stage17_lod2_test.png, docs/reports/stage17_lod2_test.json):
  - Kit (LOD2 simplificado por el propio kit), Obelisco y Portal: no se nota -> se acepta.
  - Santuario, Salon y Faro (LOD2 diezmado al 15 %): se nota (las tejas desaparecen y aparece el tablero oscuro de
    debajo; tracerias y contrafuertes se vuelven pinchos). Desde la etapa 18 su LOD2 es UN objeto <NOMBRE>_Body_LOD2
    (cuerpo + cubierta) con UN material plano MAT_LOD2_<NOMBRE> = color medio del LOD0 ponderado por area.
    Malla: volumetria cerrada con las cotas reales (caja + prisma de cubierta + torres/flecha/linterna), porque la
    envolvente por voxeles no cierra las cubiertas de una cara y el diezmado las borraba (cajas sin tapa). El Faro
    (volumenes cerrados) conserva la envolvente por voxeles (Remesh 0.3 m) diezmada al 15 %.
    MAT_LOD2_SANTUARIO #C0BBB4, MAT_LOD2_SALON_HAZANAS #91877E, MAT_LOD2_FARO #B5B0A5 (grises calidos, saturacion
    < 0.1: cumplen la paleta). Lo mismo para los edificios hechos a mano del Mercado (Tesoreria, Gran Subasta).
  - Herramienta: tools/blender/lod_utils.flat_lod2().

7. Opciones del ensamblador (etapa 18)
--------------------------------------
build_building(..., module_w=None, plan_edit=None, opts=None)
  module_w            ancho de modulo de fachada (3.0 por defecto; 4.0 en edificios grandes para el presupuesto)
  plan_edit(plan,rng) edita el plan de modulos (p. ej. el Banco: casi todo macizo y pocas ventanas WALL_Barred)
  opts:
    side_detail       detalle minimo por fachada en LOD0, p. ej. {"back": 1, "left": 1, "right": 1}
    roof_seg          largo del tramo de teja (m)            eave         vuelo del alero (m)
    n_balconies       balcones en la fachada                 wall_mat     material de los muros (p. ej. caliza clara)
    no_buttress       sin contrafuertes laterales (sobresalen 0.9 m de la huella)
Regla de alturas: solo cuentan las puertas que se ven desde CAM_Iso (que miran a la camara o de lado); una puerta de
espaldas a la camara la tapa siempre su propio edificio y no obliga a bajar a los vecinos.
Huella: a nivel de calle (por debajo de 2.2 m) todos los edificios del kit quedan dentro de +-0.2 m; por encima
vuelan cornisas (0.2), balcones (1.5) y sus mensulas, y aleros.

8. Mercado (etapa 18)
---------------------
  - MAT_Bronze_Worn del prompt no existe: las balanzas usan MAT_Bronze_Aged (el bronce envejecido ya aprobado).
  - Tesoreria: 4 salidas de tubos en la azotea con la boca a +9.6 m sobre el pad (MARKER_PipeOutlet_TesoreriaMuralla_01..04);
    la curva CRV_LightPipe_Tesoreria_Faro sale de la 02 y cruza la almenara que tiene delante.
  - Gran Subasta: pabellon abierto (interior = false, aunque el marcador decia true): sin puerta ni InteriorVolume.
  - Posada: letrero colgante con vela (llama MAT_Window_Warm, emision 1.0) y Posada_TablonGrupos (3 x 2 m, objeto aparte,
    interactive = true) en MARKER_Prop_TablonGrupos.

9. Oficios (etapa 19)
---------------------
  - MAT_Embers (nuevo): brasas y metal fundido, naranja calido NATURAL #E09A62, emision 1.5. Excepcion APROBADA en la
    etapa 25 (seccion 1a): Gran Forja y Hornos. El cuenco del Crisol pasa a MAT_Crisol_Molten (#8FD0FF): no es
    fundicion ni horno.
  - MAT_Herb_Green (nuevo): hierbas, verde apagado #6E7B58 (saturacion 0.28, dentro de la paleta).
  - Vidrio del invernadero y alambiques: MAT_Pipe_Glass (alpha 0.35, ya aprobado). Lupas: MAT_Bronze_Aged.
  - Gremio de Cazadores: colocado en la etapa 25 dentro de la muralla (seccion 15); va en bld_oficios.glb.
  - Gremio de Pescadores: el muelle 8 x 3 ya existia (CAU_Muelle_Pescadores, etapa 07); las 2 barcas van en
    MARKER_Mooring_01 y _03.
  - Joyeria y Tallado: 10 x 10 (prompt) dentro de su parcela de 16 x 12, alineada al frente.
  - Gran Forja: edificio 16 x 16 + patio de fundicion 10 x 16 en el extremo exterior de la parcela (26 x 16).
  - Curtiduria: casa 16 x 7 al fondo y patio delante con las 4 tinas (la puerta mira a la camara).
  - Sastreria: 2 plantas = planta baja cerrada + planta alta abierta de telares (balcones y telas en los 4 lados).

10. Clases (etapa 20): plantilla de Salon de clase y presets
------------------------------------------------------------
  - tools/blender/stage20_clases.py: N_CLASES (parametro, <= 8 parcelas) y CLASS_PRESETS (CLASE_01..CLASE_08, nombres
    genericos para renombrar). Cada preset: color tierra apagado del estandarte (saturacion <= 0.35), emblema
    (textura generada, placeholder), remate sobre el fronton y 2 modelos de props de clase.
    Para otro numero de clases: python build_stage20.py -- N.
  - Estandartes: objetos aparte SalonClase_NN_Banner_Front / _Back (2.5 x 6 m, UV 0..1) con MAT_Banner_CLASE_NN y su
    textura textures/concordia/MAT_Banner/concordia_banner_clase_NN_albedo.png (512 x 1024, +0.33 MB de VRAM cada una).
    El trasero se lee desde CAM_Iso cuando la fachada mira al otro lado.
  - Slots: MARKER_ClassProp_Slot_<salon>_<slot> (3 por salon, sobre peanas a la entrada); los slots 01 y 02 llevan los
    2 props del preset y el 03 queda libre.
  - MAT_Straw (nuevo): paja de los maniquies #A69472 (saturacion 0.31).
  - Plaza de las Armas: DUMMY_Straw_A/B/C (156-186 triangulos), 12 maniquies con MARKER_DamageNumber_NN en el pecho,
    10 blancos, 8 postes de prueba, valla baja con huecos en la avenida y delante de los salones 01 y 02.

11. Razas (etapa 21): plantilla de barrio y presets
----------------------------------------------------
  - tools/blender/stage21_razas.py: N_RAZAS (parametro, <= 6 parcelas MARKER_Bld_CasaRaza_*) y RACE_PRESETS R01..R06:
      R01 piedra gris, dos aguas 40 grados, pizarra, puerta x1.0      (Rothenburg / Cesky Krumlov)
      R02 madera clara, cuatro aguas 34 grados, teja ocre, puerta x1.0 (Mala Strana)
      R03 madera oscura, dos aguas muy inclinado 52 grados, puerta x0.9 (Cesky Krumlov / Selva Negra)
      R04 piedra clara y vidrio, chapitel 'spire' 58 grados + torrecillas conicas, puerta x1.1 (chapiteles de Praga)
      R05 pieles y madera, yurtas (ger) con corona, puerta x1.3
      R06 piedra arenisca abajo y entramado arriba, azotea con pretil, puerta x0.8 (Toledo)
    Cada preset: material de muro (con alternativas por casa), remates, hastiales, tejas (tono A/B que se alterna en
    una de cada tres casas), pendiente, escala de puerta, color del estandarte y simbolo (placeholder).
    Para otro numero de razas: python build_stage21.py -- N.
  - DOOR_SCALE (bld_kit.DOOR_SCALE, opts door_scale del ensamblador): escala el ancho y alto del hueco de puerta, el
    dintel y el escalon de umbral (0.12 m x escala; sale 0.18 m de la fachada, dentro de la tolerancia de 0.2).
  - Casa de la Raza (20 x 16, interior = true): la mas grande del barrio. Estandarte CasaRaza_NN_Banner (1.8 m de ancho,
    UV 0..1, MAT_Banner_RNN) colgado sobre la puerta (sin ventana encima), bandera CasaRaza_NN_Flag (UV recortada al
    simbolo) en la cumbrera / vertice / pretil / corona, y MARKER_RaceSpawn_NN 3 m delante de la puerta (+Y fuera).
    R05: yurta grande (r 6.8) + 2 anexos, estandarte en mastil exento junto a la puerta.
  - Casas del barrio: las parcelas MARKER_Bld_RAZ_Bxx_Casa_yy existentes (22): B01 5, B02 5, B03 6, B04 5, B05 0,
    B06 1. El prompt pide 6-10 por barrio: faltan parcelas (no se han inventado; ver informe).
  - Presupuesto por niveles: si una casa pasa de 2,500 (4,000 con 3 plantas) o la Casa de la Raza de 6,000, se
    reconstruye con modulos mas anchos, hiladas de teja mas largas y menos detalle en los lados que no ve CAM_Iso.
  - Faldon bajo rasante en todas las casas (las parcelas tienen hasta 0.86 m de desnivel): llega 20 cm por debajo del
    punto mas bajo del terreno en el perimetro, 8 cm fuera del muro (sin caras coplanarias).
  - Plazuelas (ya pavimentadas en el terreno): fuente pequena de 3.2 m (barrios 1, 2, 5) o arbol viejo de ~10 m con
    alcorque (3, 4, 6) y 4 bancos a 3.7 m del centro.

12. Conexiones (etapa 22): puentes, arcos, escalinatas, escaleras y pretiles
---------------------------------------------------------------------------
  - tools/blender/stage22_conexiones.py (constructores) y build_stage22.py (colocacion). Referencias: canales de Brujas,
    Mala Strana (Praga), Toledo. Solo materiales ya aprobados (calizas, MAT_Stone_Repair, empedrado, losa, hierro,
    MAT_Shard_Blue de la linterna).
  - Convenio de las piezas: cada una es hija de su marcador (MARKER_*), +Y local = sentido de paso (cruzar el puente o
    el arco, bajar las escalinatas, subir las escaleras de terraza); "<pieza>-colonly" es la superficie de paso plana y
    continua (rampa sobre los bordes de los peldanos) mas los muros/pretiles; LOD1 (0.5) y LOD2 (0.15, color plano).
  - BRIDGE_Stone_5m / _6m en MARKER_Bridge_01..05: arco rebajado (flecha 0.35 m; 0.79 en el 05), calzada 0.4 m sobre la
    calle con rampas de 5.5 m que llegan a la cota real de la calle en cada extremo, pretiles de 0.9 m con albardilla
    (20 % de tramos remendados), imposta, 11 dovelas con clave (una de otra piedra), sillares en estribos y arranques.
    820-882 triangulos (limite 1,800). Puente 01: rampa lejana de 2.5 m (9.1 grados) hasta r 95, el rellano superior
    de la escalinata NE (decision C del usuario). El 03 es oblicuo (luz 7.36 m).
  - ARCH_Street_4m/5m/6m: arco rebajado que arranca a 5.0 m (altura libre), paso alto a 6.4 m (planta 2 de las casas),
    pilares con sillares que llegan a las fachadas (0.8-0.91 m), linterna de esquirla en la clave (las dos caras).
    674-678 triangulos (limite 1,200). En MARKER_Bridge_06..09 (Ronda r150, barrios distintos): ARCH_Street_6m;
    los marcadores se han subido a la cota del paso alto (deck_z) y llevan street_z.
  - RAIL_Stone_3m (0.9 m), RAIL_Stone_3m_Patch (remiendo) y RAIL_Stone_3m_Low (0.5 m): 38-40 triangulos, instanciables;
    en los pasos altos de los arcos (6 por arco, escala Y 0.85-0.86 para ajustarse a la longitud, MARKER_Rail_*).
  - STAIRS_Monumental (4, r 95-105 de las diagonales): 6 m, 10 x 0.15 / 1.0, descanso de 2 m, pasamanos de piedra de
    0.9 m con albardilla inclinada y pilares; 530 triangulos, una malla instanciada 4 veces (MARKER_Stairs_Monumental_*).
  - STAIRS_Terrace: 2.5 m (variantes A/B) y 6 m en el eje, 7 x 0.143 / 0.30 con zancas y albardilla, 242 triangulos,
    76 instancias en las Moradas (MARKER_Stairs_Terrace_<Morada>_NN); 32 escaleras de los muros laterales (Prompt 2,
    2.5 m de paso, 7-31 contrahuellas, MARKER_Stairs_Lateral_*). STAIRS_Pass_3m: las 10 escalinatas de paso del Prompt 7
    (3 m, 10 x 0.15 / 0.35, pretiles de 0.9 m) en MARKER_Escalinata_01..10 (rotacion corregida: antes todas a -90).
  - Los provisionales (TRN_Bridge_*, TRN_ArchBridge_*, TRN_Escalinata_Morada_*, TRN_StairPass_*, TRN_TerraceStairs_*,
    TRN_LateralStairs_*, con sus -colonly y _Repair; 80 objetos) pasan a LEGACY_PLACEHOLDERS (excluida de la escena y de
    la exportacion). Los concordia_terrain_<distrito>.glb y concordia_markers.glb se han reexportado sin ellos.



13. Moradas (etapa 23): viviendas de los 4 conjuntos
----------------------------------------------------
  - tools/blender/stage23_moradas.py (tipos) y build_stage23.py (plan, instancias, exportacion). Referencias: Cesky
    Krumlov y Toledo, Mont-Saint-Michel, Mala Strana.
  - 283 casas en los 283 MARKER_Morada_* (NE 72, NO 72, SO 72, SE 67; parcelas 6 x 10, fachada retranqueada 2 m como en la
    etapa 06): 142 habitaciones (casa comunal de 3 plantas, 9 puertas por modulo, galerias corridas y escalera
    exterior en diagonal), 98 casas pequenas (1 planta, patio delantero con muro bajo, a un agua o dos aguas,
    chimenea) y 43 casas grandes (2 plantas, balcon, jardin trasero con muro, dos aguas o faldon trasero largo,
    chimenea). 1,419 viviendas (puertas).
    RECUENTO ACTUAL (etapa 28): 1,398 viviendas (etapa 26: 1,404 con balcones por puerta; etapa 28: Morada_SO_036
    y SO_037 a 2 plantas, -6). Por conjunto: NE 360, NO 354, SE 330, SO 354.
  - Variantes: 4 por tipo (semilla: lado de la escalera, barandilla, cubierta, puerta, chimenea, balcon, jardin) x 3
    fachadas; en cada fila se alternan para que dos casas vecinas no coincidan ni en variante ni en fachada.
  - Techos escalonados y CAM_Iso: el lado de cada casa que da a las puertas de la terraza vecina se mantiene por debajo
    de la linea de vision (sube 0.707 m por metro). Casas comunales de seccion escalonada (trasera a 3.6 m, fachada a
    9.25 m, sin chimenea), casas pequenas a un agua con el lado bajo hacia esas puertas, casas grandes con faldon
    trasero hasta 3.8 m. Resultado medido con las mallas reales: 0 puertas tapadas por casas de otra terraza en los 4
    conjuntos. En NE y SO (la camara mira a lo largo de las filas) 33 y 50 puertas de planta baja quedan detras de la
    galeria o la escalera de la casa vecina de la MISMA fila.
  - Puerta exterior = DOOR_Morada (malla compartida; la ranura de pintura enlazada al objeto con uno de
    MAT_Door_Paint_01..06; props paint_material, house_number, lantern) con hijos PLATE_Morada_* (0.3 x 0.2, UV 0..1),
    MARKER_Lantern_* y LANTERN_Shard_* (solo en las puertas de planta baja). MARKER_Morada_Door_* delante de cada
    puerta (+Y fuera, interior aparte) y MARKER_TrophyCase_* 2 m dentro (uno por vivienda).
  - LOD1 = diezmado 0.5; LOD2 = caja con tejado, galerias / patio / balcon / muro de jardin y chimenea como cajas, un
    material plano (~11 % del LOD0). Exportacion por conjunto: export/godot/moradas_NE.glb, _NO, _SO, _SE.

14. Godot 4: version final (etapa 24)
-------------------------------------
  Archivos (export/godot, glTF 2.0 binario, +Y arriba, texturas externas ../../textures/concordia/...):
    bld_portal.glb         Portal (raiz PORTAL), Obelisco, Faro, Santuario, Salon de las Hazanas, Puente 01, escalinatas monumentales y tubos de luz Tesoreria -> Faro (PIPES_Tesoreria_Faro, instancias de 4 mallas)  [5.64 MB, 82001 tris con LOD y colisiones]
    bld_mercado.glb        Mercado (Norte)  [6.66 MB, 102058 tris con LOD y colisiones]
    bld_oficios.glb        Oficios (Este) y puentes 02-05  [5.06 MB, 74969 tris con LOD y colisiones]
    bld_clases.glb         Clases (Oeste)  [6.69 MB, 97896 tris con LOD y colisiones]
    bld_razas.glb          Razas (Sur) y arcos 06-09  [10.25 MB, 148777 tris con LOD y colisiones]
    bld_moradas_NE.glb     Morada NE (+ sus escaleras)  [4.04 MB, 47478 tris con LOD y colisiones]
    bld_moradas_NO.glb     Morada NO  [4.37 MB, 52299 tris con LOD y colisiones]
    bld_moradas_SE.glb     Morada SE  [3.65 MB, 42661 tris con LOD y colisiones]
    bld_moradas_SO.glb     Morada SO  [3.97 MB, 46267 tris con LOD y colisiones]
    bld_kit.glb            kit modular (muros, cubiertas, conexiones)  [1.56 MB, 21303 tris con LOD y colisiones]
    bld_props.glb          biblioteca de props (una instancia de cada malla)  [0.35 MB, 3688 tris con LOD y colisiones]
    Siguen: concordia_terrain_<distrito>.glb (con la malla de navegacion recortada), concordia_wall_*.glb,
    concordia_markers.glb (concordia_gremio_cazadores_sin_parcela.glb se borra en la etapa 25). Sustituidos y borrados: concordia_clases.glb, concordia_mercado.glb, concordia_oficios.glb, concordia_razas.glb, concordia_portal.glb, concordia_faro.glb, concordia_santuario.glb, concordia_salon_hazanas.glb, concordia_obelisk.glb, concordia_conexiones.glb, moradas_NE.glb, moradas_NO.glb, moradas_SE.glb, moradas_SO.glb.
  Por edificio: <N>_Body, <N>_Roof (oculta al entrar), <N>_Props, <N>-colonly (cajas / prismas convexos),
  <N>_Body_LOD1 / _Roof_LOD1 (0.49-0.57) y LOD2 (caja con tejado en las Moradas; volumetria de color plano en
  los hitos, decision D); con interior: MARKER_<N>_Door (+Y hacia fuera) y <N>_InteriorVolume. Sin cubierta
  separada: FARO, OBELISK, PORTAL (monumentos sin interior que ocultar; el Faro entra por la base).
  Puertas tras porticos o patios (12): NAVLINK_<puerta>_Start/_End = NavigationLink3D de la malla a la puerta.

  Materiales de Concordia usados por los edificios (70 + 114 planos MAT_LOD2_*; todos exportables: Image Texture ->
  Principled, con Mix Multiply = baseColorFactor; sin otros nodos). Color medio sRGB (y alpha si < 1):
    MAT_Ash_Gray #727272; MAT_Banner_CLASE_01 #907764; MAT_Banner_CLASE_02 #777E8A
    MAT_Banner_CLASE_03 #798163; MAT_Banner_CLASE_04 #807987; MAT_Banner_CLASE_05 #89735A
    MAT_Banner_CLASE_06 #758471; MAT_Banner_CLASE_07 #A39372; MAT_Banner_CLASE_08 #65605C
    MAT_Banner_R01 #797570; MAT_Banner_R02 #978666; MAT_Banner_R03 #69584B
    MAT_Banner_R04 #778692; MAT_Banner_R05 #967D6A; MAT_Banner_R06 #A79172
    MAT_Bronze_Aged #73644C; MAT_Cloth_Patch_A #8A7462; MAT_Cloth_Patch_B #6E6B58
    MAT_Cloth_Patch_C #A49884; MAT_Cobble_Concordia #AEA79D; MAT_Door_NumberPlate #D8D3C5
    MAT_Door_Paint_01 #847E62; MAT_Door_Paint_02 #827E70; MAT_Door_Paint_03 #8D755E
    MAT_Door_Paint_04 #7D6C56; MAT_Door_Paint_05 #917F62; MAT_Door_Paint_06 #887769
    MAT_Embers #A67148; MAT_Facade_Earth_A #D8C9AF; MAT_Facade_Earth_B #D6C4B4
    MAT_Facade_Earth_C #CECAB9; MAT_Faro_Beam #8FD0FF a0.3; MAT_Felt_R05 #B8B6B1
    MAT_Glass_R04 #A9C9DC a0.35; MAT_Ground_Cracked #A49A88; MAT_Herb_Green #6E7B58
    MAT_Hide_R05 #948475; MAT_Iron_Black #2E2D2B; MAT_Leaf_Old #5F6B4E
    MAT_Limestone_Light #D8D3CB; MAT_Limestone_Worn #C3B9A8; MAT_Obelisk_Black #2C2C2D
    MAT_Obelisk_Mark #4A4A4A; MAT_Obelisk_Mark_Lit #8FD0FF; MAT_Pipe_Glass #C9DDE6 a0.35
    MAT_Pipe_Light_Core #8FD0FF; MAT_Plaza_Slab #B4ADA2; MAT_Portal_Veil #8FD0FF a0.6
    MAT_Rock_Gray #6F6F6F; MAT_Roof_Shingle_Dark #725D4B; MAT_Roof_Shingle_Dark_B #695646
    MAT_Roof_Slate #6D6F74; MAT_Roof_Slate_B #64676C; MAT_Roof_Slate_Blue #5F6974
    MAT_Roof_Tile_Ocher #9E8A76; MAT_Roof_Tile_Ocher_B #8E7863; MAT_Rune_Glow_10 #8FD0FF
    MAT_Rune_Glow_12 #8FD0FF; MAT_Shard_Blue #88C6F3; MAT_Shard_Blue_E40 #88C6F3
    MAT_Stained_Glass_Blue #75AEDB; MAT_Stone_R01 #B1A89A; MAT_Stone_Repair #8D8579
    MAT_Stone_Sand #C3B195; MAT_Straw #A69472; MAT_Wall_Gray #8F8D89
    MAT_Water #1A201F; MAT_Window_Warm #836E58; MAT_Wood_Dark #4A4037
    MAT_Wood_Light #A4947C

  Emision (glTF: emissiveFactor + KHR_materials_emissive_strength si la fuerza pasa de 1):
    MAT_Crisol_Molten            emision #8FD0FF fuerza 1.2   magico #8FD0FF (etapa 25)
    MAT_Embers                   emision #E09A62 fuerza 1.5   natural: UNICA excepcion calida (seccion 1a)
    MAT_Faro_Beam                emision #8FD0FF fuerza 1.5   magico #8FD0FF
    MAT_Glass_R04                emision #8FD0FF fuerza 0.25  magico #8FD0FF
    MAT_Obelisk_Mark_Lit         emision #8FD0FF fuerza 3.0   magico #8FD0FF
    MAT_Pipe_Light_Core          emision #8FD0FF fuerza 1.5   magico #8FD0FF
    MAT_Portal_Veil              emision #8FD0FF fuerza 3.0   magico #8FD0FF
    MAT_Rune_Glow_10             emision #8FD0FF fuerza 1.0   magico #8FD0FF
    MAT_Rune_Glow_12             emision #8FD0FF fuerza 1.2   magico #8FD0FF
    MAT_Shard_Blue               emision #8FD0FF fuerza 2.5   magico #8FD0FF
    MAT_Shard_Blue_E40           emision #8FD0FF fuerza 4.0   magico #8FD0FF
    MAT_Stained_Glass_Blue       emision #8FD0FF fuerza 0.6   magico #8FD0FF
    MAT_Window_Warm              emision #AD9072 fuerza 1.0   natural
  Etapa 24: MAT_Stained_Glass_Blue pasa de #7DB5E5 a #8FD0FF (unico color magico de la ciudad). MAT_Embers: excepcion
  aprobada en la etapa 25 (seccion 1a).

  Objetos animables (nodos propios en los glb):
    PORTAL_Veil: velo del Portal: desplazamiento de UV / ondulacion, emision 3.0
    FARO_Beam: haz del Faro: giro lento, mezcla aditiva
    Taller_Carpinteria_WATERWHEEL: rueda hidraulica: giro en su eje Y local (~6 rpm); eje Taller_Carpinteria_Axle
    OBELISK_Mark_001..100: las 100 marcas de piso del Obelisco: material MAT_Obelisk_Mark_Lit al subir de piso
    CRISOL_FloatStone_01..07: piedras flotantes del Crisol: flotar y girar
    SalonClase_NN_Banner_Front/_Back, CasaRaza_NN_Banner, CasaRaza_NN_Flag: estandartes y banderas: viento (shader de vertices)

  Presupuesto medido (etapa 26): 376 edificios, LOD0 615,074 tris (cuerpo + cubierta + props y extras), LOD2 50,961.
  Ciudad completa en LOD0 (edificios + conexiones 44,056 + terreno 452,076 + muralla 107,132 + tubos de luz 7,944):
  1,226,282. En LOD2: edificios 50,961 + conexiones 25,686 + terreno 80,476 + muralla 20,898 = 178,021.
  OJO: la muralla colocada (WALL_LAYOUT, 105 piezas) NO tiene LOD2 propio; la cifra de LOD2 es la suma del LOD2 del
  kit (WALL_KIT_LODS) en cada instancia. Los tubos de luz no tienen LOD (se ocultan por visibility_range en Godot).
  (Etapa 25: 370 edificios, 611,051 / 46,911; ciudad 1,214,315. Etapa 24: 366, 607,876 / 46,517; 1,211,140.)
  (Etapa 24: 366 edificios, 607,876 / 46,517; ciudad 1,211,140.)
  Detalle por edificio y distrito: docs/reports/stage24_godot.json.

15. Decisiones de la etapa 25 (E12): concordia_v25.blend
--------------------------------------------------------
  Scripts: tools/blender/build_stage25.py (v24 -> v25), stage25_lots.py (suelo libre), stage25_faro.py (visuales al
  Faro), measure_stage25_faro.py; despues se repite build_stage24.py sobre v25 (CONCORDIA_SRC = CONCORDIA_OUT = v25,
  informe docs/reports/stage25_godot.json). Informes: stage25_decisiones.json, stage25_faro.json.

  a) Brasas: ver seccion 1 (UNICA excepcion calida). Comprobado en v25: MAT_Embers solo en Taller_GranForja (2.12 m2,
     0.08 % de su superficie) y Taller_Hornos (1.08 m2, 0.16 %); emision #E09A62 1.5, tono 27 grados, sin textura
     de esquirla. El cuenco del Crisol (antes MAT_Embers, 0.47 %) pasa a MAT_Crisol_Molten (#8FD0FF 1.2). La Posada
     y la chimenea de la Forja pueden usarlo en el interior de la chimenea; hoy no lo usan.

  b) Gremio de Cazadores dentro de la muralla (opcion elegida: casa 12 x 8 + campo 14 x 8). No hay hueco de 20 x 14
     ni de 14 x 10 libre en el sector Este (sin calles, plazas, escalinatas, puentes ni objetos).
       Casa: MARKER_Bld_Gremio_Cazadores en (117.0, -21.0), giro -10.2 grados, r 118.9; 12 x 8, 2 plantas, gable,
       timber, desnivel 0.29 m (faldon 0.6 m). Props: 2 cornamentas y 1 secadero de pieles. Interior: si.
       Campo de tiro: Gremio_Cazadores_Range en (161.0, 51.0), giro 107.6 grados (tangente: paralelo a la muralla),
       r 168.9 (anillo interior r 165-185); 14 x 8, valla de madera de 1.2 m (postes cada 2 m, 2 travesanos,
       entrada de 2 m del lado de la ciudad), mostrador de tiro y 4 dianas; MARKER_Cazadores_Range; colision de la
       valla (Gremio_Cazadores_Range-colonly). Esta a 84 m de la casa (no hay suelo libre de 14 x 8 mas cerca).
       Exportado en bld_oficios.glb; concordia_gremio_cazadores_sin_parcela.glb borrado.
       ACCESO AL CAMPO (pendiente de decision, no aplicado): el campo no toca la malla de navegacion por ningun
       lado (el invernadero de Herbolarios queda a 1.5 m de la entrada y el lado de la muralla esta ocupado). El
       punto publico mas cercano es (155, 65), a 8 m del extremo norte (+X local) por suelo libre. No hay ningun
       hueco de 14 x 8 con frente a calle en el sector Este (el unico 12 x 6 con frente, (74, -54), cae a -36 grados,
       fuera del sector). Propuesta: abrir la entrada en el extremo norte, camino de tierra de 8 x 2 m hasta (155, 65)
       y anadir campo + camino a la malla de navegacion.

  c) Razas: parcelas nuevas de 8 x 8 (3 plantas si no tapan el Faro). Busqueda en rejilla de 1 m en todo el sector Sur
     (+-25 grados, r 60-185), incluidos los lados de los anillos r 100 y r 150: parcela + 0.3 m de margen sin
     calle, plaza, escalinata, puente ni objeto, desnivel <= 1.2 m y frente a calle a <= 3.5 m. Solo hay 4 huecos:
       (49, -117) -> RAZ_B01_Casa_06; (-59, -157) -> RAZ_B04_Casa_06; (33, -83) -> RAZ_B05_Casa_01 (yurta);
       (23, -167) -> sin usar (junto a B03, que ya tiene sus 6 casas).
     Las 3 casas nuevas tapaban alguna visual del Faro a 3 plantas y bajaron por la escalera hasta el paso c
     (5.27-5.6 m); ninguna es la unica que tapa un punto de calle (0 puntos perdidos por ellas).
     FALTAN 11 parcelas (no se inventa espacio): B02 1, B05 5, B06 5. Reducir el barrio a 32 x 32 no crea suelo
     libre: los 4 huecos del sector ya son todos los que hay.

  d) Faro (criterio: 1.7 m cada 10 m; se ve si >= 2 de 6 visuales a la galeria superior: ultimos 6 m + cristal).
     Escalera aplicada solo donde deja de tapar (simulacion sobre v24):
       Edificio           Antes   Despues  Paso                       Tapaba
       Morada_NO_033      9.36    6.06     a (habitacion 2 plantas)    Diagonal NO
       Morada_NO_002      9.36    6.06     a                           Diagonal NO
       Morada_SE_023      9.36    6.06     a                           Diagonal SE
       Morada_SE_036      9.36    6.06     a                           Diagonal SE
       Morada_SE_004      9.36    6.06     a                           Diagonal SE
       RAZ_B01_Casa_01    11.02   5.38     c (1 planta + cubierta)     STR_RAZ_Ring150
       RAZ_B01_Casa_02    11.42   5.50     c                           STR_RAZ_Ring150
       RAZ_B02_Casa_02    13.12   5.50     c                           STR_RAZ_Ring150
     Visibilidad (v24 -> v25): avenidas 78.3 -> 78.3 %; anillos 56.6 -> 57.8 %; diagonales 36.7 -> 38.8 %;
     callejones 47.8 -> 47.8 %. Edificios que tapan: 96 -> 88 (29 de servicio).
     El 100 % (y el 90 % en callejones) NO se alcanza con la escalera: los hitos y puertas de la muralla, que no se
     tocan, tapan 18 de los 49 puntos de las diagonales (Obelisco 12, Salon 4, Santuario 2) y 4 de las avenidas
     (puertas selladas); los demas edificios necesitarian quedarse por debajo de 0.8-6.6 m (la mayoria < 5.5 m, el
     paso c). Edificios de servicio que siguen tapando: lista en stage25_faro.json (decision pendiente).

  e) Ajustes SIN aplicar (pendientes de decision): galerias de las Moradas NE/SO que tapan 53 puertas;
     RAZ_B02_Casa_04 que tapa la puerta de CasaRaza_02.

  f) Repositorio y LFS (diagnostico, sin forzar push): rama sincronizada con el remoto (0/0), solo commits de este
     proyecto; git-lfs 3.4.1 instalado pero sin configurar (0 archivos en LFS). .git ocupa 3.3 GB; historial con 42
     .blend antes de la v25 (2.19 GiB) y 579 glb/png/jpg (1.56 GiB). El .blend mayor (v25) pesa 77.6 MB: < 100 MB (limite duro de
     GitHub; aviso a partir de 50 MB). Migrar el historial a LFS supondria ~3.7 GiB en LFS: por encima de la cuota
     gratuita (1 GiB de almacenamiento y 1 GiB/mes de descarga). No se migra ni se fuerza nada.

16. Decisiones de la etapa 26 (E13): concordia_v26.blend
--------------------------------------------------------
  Scripts: build_stage26.py (pasos moradas, raza04, cazadores, razas, subasta, salon, pipes), stage26_moradas.py,
  stage26_cazadores.py, stage26_razas.py, stage26_pipes.py, stage26_faro.py + measure_stage26_faro.py; despues
  build_stage24.py sobre v26 (docs/reports/stage26_godot.json). Informes: stage26_decisiones.json, stage26_faro.json,
  stage26_faro_proposal.json, stage26_texture_memory.json.

  Punto 2 - Moradas NE y SO: un balcon por puerta (1.5 x 0.35 m, losa con mensula, tablas de dos tonos, una tabla de
    remiendo por casa) en lugar de las galerias corridas; escalera de dos tramos en la franja y 4.2-4.98 (0.78 m),
    sin pasamanos en los tramos (tapaba puertas vecinas); dos rellanos llevan a los balcones de las puertas x=0
    (planta 2) y del extremo (planta 3). Las demas puertas altas son puertas-balcon (acceso por el interior).
    Lado de la escalera: el PIE en el extremo alejado de CAM_Iso y el tramo alto hacia la camara. Al reves (tramo
    alto en el extremo alejado) se tapaban 39-48 puertas; asi, 16-19. 3 casas con el lado cambiado por prueba
    (NE_013, NE_064, SO_022). Huella, altura total y seccion sin cambios.
    Puertas tapadas desde CAM_Iso: NE 24 -> 5, SO 29 -> 11, NO 0, SE 0 (total 53 -> 16).
      Tapadas por el cuerpo o el alero de casas a 6-12 m en la fila curva (ya lo estaban sin galerias): NE_063_1, SO_035_1, SO_035_2, SO_035_3, SO_035_4, SO_035_5, SO_035_6, SO_048_1, SO_064_1.
      Tapadas por balcones o escaleras de la vecina: NE_013_1, NE_022_1, NE_047_1, NE_070_1, SO_018_3, SO_058_3, SO_059_3.
    Presupuesto por casa (etapa 10): todos dentro. Por conjunto (LOD0 con puertas, placas y faroles / LOD2):
      NE 74,074 / 6,488; NO 71,128 / 4,806; SE 64,398 / 4,410; SO 74,298 / 6,516.
      Maximos: habitacion 1418 (NE), 1460 (NO), 1340 (SE), 1418 (SO) de 1,500;
      casa pequena 672 de 2,000; casa grande 752 de 3,500.
  Punto 3 - RAZ_B02_Casa_04 a 1 planta (10.49 -> 7.29 m, cubierta a cuatro aguas del preset): la puerta de
    CasaRaza_02 queda visible.
  Punto 4 - Campo de tiro de los Cazadores: valla cerrada por el lado de la ciudad; apertura de 2 m en el extremo
    norte con portillo de tablas abierto hacia dentro (fuera del paso libre); camino de adoquin de 2 m x 9.1 m
    (8.5 m hasta la calle + 0.6 m de encuentro) hasta [155.4, 65.5], sin parcelas, objetos, escalinatas ni
    puentes (comprobado celda a celda); campo y camino dentro de TRN_NavMesh_Oficios (145 caras) y soldados a
    una arista de la calle: el campo esta en la misma componente que la red de calles (4428 caras).
  Punto 5 - Razas: B01 6, B02 6, B03 6, B04 6, B05 5, B06 2.
    B02: casa nueva de 4 x 8 (3 plantas) en (-19, -137). B05: la parcela 8 x 8 dividida en 2 adosadas + 3 parcelas de
    4 x 8 (una al otro lado del anillo r 100); yurtas pequenas (r 1.85 m) por el preset de pieles. B06: la parcela de
    8 x 8 dividida en 2 adosadas (3 y 2 plantas). B05 queda en el minimo aceptado (5). B06 NO llega: tiene 2, faltan
    3 para el minimo de 5 (4 para 6). No hay mas suelo libre de 4 x 8 en su lado del sector; compactar (mover la
    Casa de Raza o la plazuela) no se ha hecho. Huecos sin usar (cerca de B03 y B04, ya completos): [[-29.0, -173.0], [21.0, -165.0], [21.0, -171.0], [-21.0, -167.0]].
    Desnivel admitido en estas parcelas: hasta 2.5 m cubiertos por el zocalo (antes 1.2 m).
  Punto 9 - Gran Subasta: marcador interior = false (no habia InteriorVolume ni puerta que quitar).
  Punto 7 - Salon de las Hazanas: SALON_HAZANAS_Body y _Roof con occludes_iso = true (salen como metadatos glTF).
    Sus 8 materiales son Principled + texturas (+ grupo 'glTF Material Output'), alpha 1: en Godot son
    StandardMaterial3D y admiten distance_fade_mode PIXEL/OBJECT_DITHER (o alpha hash en un shader propio). Geometria
    sin cambios. SANTUARIO_Well: provisional = true hasta la etapa de interiores.
  Punto 8 - Tubos de luz Tesoreria -> Faro: el primer punto ya estaba en la salida real (MARKER_PipeOutlet_
    TesoreriaMuralla_02, azotea +9.6 m) desde la etapa 18; provisional = false. La curva original cruzaba la almenara
    de delante a 0.08-0.24 m del eje (el tubo de 0.23 m de radio la atravesaba): colision -> la curva sube 3.5 m
    (tramo vertical en la boca) y va a <= 14.0 m sobre la calle. Piezas: 34 rectos (estirados hasta 4 m), 3 codos de
    90, 4 codos de 45 (PIPE_Light_Elbow45, mitad del de 90), 14 soportes cada 8 m (ninguno en el agua del Cauce).
    7,944 triangulos (limite 8,000). Holguras: >= 8.43 m a otros edificios, 1.17 m al Faro, 2 cm de
    aire en la almenara de la Tesoreria. Longitud 123.1 m. No tapan ningun punto del haz.
  Punto 1 - Faro, criterio nuevo (11 rayos: 10 al eje del haz entre 60 y 120 m y 1 al cristal; vale 1 libre):
      avenidas 91.7 % (55/60), cristal directo 78.3 %
      anillos 69.9 % (58/83), cristal directo 54.2 %
      diagonales 79.6 % (39/49), cristal directo 34.7 %
      callejones 76.4 % (120/157), cristal directo 46.5 %
    Ningun tipo llega al objetivo. Bajar decoracion (minimo 7 m) solo liberaria 1 punto (MER_Casa_01, 14.01 -> 7.89 m,
    anillo): tabla en stage26_faro.json y stage26_faro_proposal.json; NO aplicado (pendiente de tu confirmacion). El
    resto lo tapan la muralla (4 puntos de avenida), los hitos (8 de diagonal), edificios de servicio o decoracion
    que tendria que bajar de 7 m.
  Punto 10 - Repositorio: ver la seccion 17.

17. Repositorio (etapa 26, punto 10: NO se migra a LFS)
--------------------------------------------------------
  En git: scripts (.py), README_*.txt, TODO_GODOT.txt, informes y listas (docs/reports/*.json, stage11_markers.csv),
  textures/concordia/polyhaven.json, .gitignore/.gitattributes. (ASSETS_LICENSES.md no existe todavia; no hay
  proyecto de Godot en el repositorio.)
  Fuera de git (.gitignore): *.blend, *.glb, *.png, *.exr y respaldo/ (salvo respaldo/MANIFEST.txt). En la etapa 26
  se quitaron del indice 306 archivos (git rm --cached): siguen en disco y en el historial anterior; no se ha
  reescrito el historial ni forzado ningun push.
  Respaldo: respaldo/2026-11-08/concordia_master_2026-11-08_v26.blend (= concordia_v26.blend) y respaldo/2026-11-08/
  glb/ (los 21 .glb de export/godot); respaldo/MANIFEST.txt con tamano y sha256 de cada archivo (22 archivos,
  191.8 MiB). Comprobacion: ver la cabecera del MANIFEST.
  Tamanos al cerrar la etapa 26: archivos versionados 259 (183.8 MB, de ellos 180.7 MB son las texturas .jpg y
  export/godot/materials/*.gltf/.bin, que no estaban en la lista: siguen en git hasta que se decida); .git local
  3.4 GiB (historial con todas las versiones anteriores); respaldo/ 192 MB.
  AVISO: el contenedor de esta sesion es temporal. respaldo/ y los .blend/.glb/.png nuevos SOLO existen aqui y en
  lo que se descargue; concordia_v26.blend no esta en GitHub.

18. Interiores (etapa 27): kit BLD_INT_KIT, build_interior y piloto del Banco
---------------------------------------------------------------------------
  Archivo: blender/concordia_interiors_v01.blend (materiales copiados de concordia_v26). Scripts:
  tools/blender/interior_kit.py (kit y escena de interior), stage27_banco.py, build_stage27.py, capture_stage27.py;
  concordia_buildings.build_interior(nombre, volumen, estilo, seed, ...) llama a interior_kit.build_interior.
  Informe: docs/reports/stage27_interiors.json.

  Kit (coleccion BLD_INT_KIT, grilla de 1 m, <= 300 triangulos por modulo; variantes _B remendadas):
    INT_Floor_Stone 10, INT_Floor_Stone_B 30, INT_Floor_Planks 40, INT_Floor_Planks_B 40, INT_Wall_Plaster 16, INT_Wall_Plaster_B 26, INT_Wall_Stone 108, INT_Wall_Stone_B 108, INT_Wall_Panel 66, INT_Wall_Panel_B 66, INT_Beam_Straight 12, INT_Beam_Cross 40, INT_Arch_3m 236, INT_Arch_6m 236, INT_Pillar 30, INT_Stairs_Int 136, INT_Door_Int 98, INT_Door_Int_Iron 130, INT_Window_Int 92, INT_Fireplace 70, INT_Counter_Straight 42, INT_Counter_Straight_B 42, INT_Counter_Corner 22, INT_Grille 142, INT_Grille_Wicket 154, INT_Grille_Teller 104, INT_Railing 78, INT_Trim 20.
  Convencion: muros x en [0, ancho], cara visible en y = 0 hacia +Y, grosor hacia -Y; suelos 2 x 2 con la cara
  en z = 0; la escalera sube hacia +Y (16 peldanos, 5.0 x 3.2 m, 32.6 grados).

  Escena de interior (int_<nombre>.glb): raiz INT_<nombre> (origen en la puerta, piso en z = 0, giro del edificio
  en el mundo) > INT_<nombre>_Frame > grupos Shell, WALL_Near_A, WALL_Near_B, CEILING, Furniture, Lights, Markers,
  -colonly y -navmesh. Los muros cercanos salen de CAM_Iso: la normal hacia fuera del muro apunta a la camara.
  Al exportar, cada grupo de estructura se une en una malla (INT_<nombre>_<grupo>, UV metrica continua); el
  mobiliario queda instanciado. Luces = Empties con light_color, light_energy (Godot), light_range (m).

  Piloto: int_banco.glb (export/godot, 1.61 MB, 29,434 tris con colision y navmesh). Volumen = Banco_InteriorVolume 23.1 x 19.1 x 6.4 m
  (diferencia 0.0 m; los "24 x 20 m" del pedido son la huella exterior). Giro 90 grados: muros cercanos -X y -Y.
    Planta baja: vestibulo de doble altura; mostrador de piedra y madera de 10 m (5 INT_Counter_Straight) con reja
      (5 modulos: 3 INT_Grille, 1 INT_Grille_Wicket y 1 INT_Grille_Teller = ventanilla de cajero de 1.2 m de luz con
      jambas y dintel de piedra, tablero libre, centro y = 1.25); el Banquero (MARKER_NPC_Slot_01, de pie en
      x 5.0, y 1.65) detras, de cara al publico y a la camara;
      sala de espera (3 bancos); archivo (6 estanterias de doble cara con libros contables, escritorio); hogar en
      la fachada; cuarto del personal tras la boveda (puerta de 1.235 m en la arcada).
    Boveda: tabique de 0.4 m con puerta de hierro de 2.2 x 3.0 m hecha a mano (bandas, remaches, pernios, rueda,
      candado; VAULT_Door aparte para animarla), arco de descarga y farol de esquirla encima (el unico azul);
      boveda de canon con 3 arcos fajones; 200 cajas (BOXES_TOTAL) en 4 paredes
      (+X: 86, -Yv: 30, -Xv: 55, -Y: 29), 4 filas de 0.36 x 0.32 m. Cada caja: Empty
      BANK_Box_NNN (box_number, state) con _Body (malla compartida BANK_Box_Open 18 tris o BANK_Box_Locked 36 tris)
      y _Plate (malla propia con UV a su celda del atlas MAT_Bank_BoxNumbers 1K: mitad clara = abierta, mitad oscura
      = cerrada). Por defecto 1-40 abiertas.
    Planta alta (LEVEL_1, a lo largo de la fachada): galeria con balaustrada sobre una arcada de 5 vanos
      (INT_Arch_3m), despacho con escritorio, estanteria y cofre; escalera de piedra de 2 m de ancho (32.6 grados).
    Marcadores: MARKER_Interior_Exit, _Spawn, MARKER_NPC_Slot_01 (npc=Banquero), MARKER_Interact_Bank_Counter
      (tipo=bank_counter), MARKER_Interact_Vault (tipo=vault).
    Luz: 5 lamparas de aceite (pilares de la arcada, boveda, despacho), 4 velas, hogar, 6 ventanas con reja (luz
      calida de dia) y 1 luz azul (farol de la boveda). Emision de llamas MAT_Window_Warm 1.0.
  Verificacion:
    Triangulos: 25,936 de 40,000 (todas las cajas cerradas: 26,656). Por grupo: Shell 7,984, WALL_Near_A 1,444, WALL_Near_B 2,910, CEILING 142, Furniture 7,660, WALL_Near_Vault 2,984, CEILING_Vault 348, LEVEL_1 1,844, Furniture_L1 620.
    Rayos desde CAM_Iso (muros cercanos y techos ocultos), con la ventanilla de cajero: Banquero 75.0 % de 12
      puntos (antes 58.3 %; los 3 tapados son los de 0.6 m, rodillas tras el tablero de 1.1 m; ningun barrote),
      mostrador 100 % (5 puntos en la cara del publico y 5 en la mitad publica del tablero; con la medicion de la
      etapa 27, que ponia los puntos del tablero dentro de la barra baja de la reja, 60 %), puerta de la boveda
      88.9 % (1 punto tras el farol). Ninguna columna ni arco los tapa.
      La ventanilla no esta enfrente fisico exacto del Banquero sino 0.35 m a -Y: en CAM_Iso lo que esta 0.7 m
      detras de la reja se ve desplazado en diagonal, y la ventanilla debe cruzar esa linea de vista.
    Navegacion: 6,258 caras (rejilla de 0.25 m, margen 0.3 m); desde el spawn se llega al mostrador,
      la zona del banquero, la boveda, el archivo, la espera, el cuarto del personal, la galeria y el despacho; con
      holgura de 0.6 m (pasos de 1.2 m) tambien. Escalera 2 m, 32.6 grados.

  Grupos ocultables (convencion para TODOS los interiores; cada grupo lleva la propiedad hide_when):
    WALL_Near_A / WALL_Near_B   muros del recinto principal cuya normal mira a CAM_Iso: siempre ocultos dentro.
    CEILING                     techo del recinto principal: siempre oculto dentro.
    WALL_Near_<Recinto>         muros cercanos de un recinto cerrado (Vault, Despacho, Taller...): se ocultan
                                cuando el jugador entra en ese recinto (Area3D en su suelo).
    CEILING_<Recinto>           techo propio del recinto: igual que WALL_Near_<Recinto>.
    LEVEL_n                     planta n (1 = primera alta) con su suelo, muros y Furniture_Ln: se oculta cuando
                                el jugador esta por debajo de n y tapa lo que hay debajo (corte isometrico).
    Shell, Furniture, Lights, Markers no se ocultan nunca.

  Lecciones para los demas interiores:
    1. Leer el giro del edificio de rotation_euler (al anexar objetos, matrix_world llega sin evaluar): con el giro
       mal salen los muros cercanos equivocados. Comprobar 'cam_local' en el informe.
    2. Cada recinto interior (boveda, despacho cerrado...) necesita sus propios muros cercanos ocultables
       (WALL_Near_<recinto>, propiedad hide_when) y su techo (CEILING_<recinto>); lo que cuelga de esos muros va en
       el mismo grupo (si no, se ve de espaldas).
    3. Entreplantas en los muros del fondo; bajo un forjado de 5 m solo se ve 1.4 m desde el borde: la planta alta
       va en LEVEL_1 (ocultable) y nada importante debajo.
    4. Un volumen alto (la boveda) tapa lo que queda detras de el respecto a la camara (+x/+y en el marco del Banco):
       ponerlo en la esquina del fondo o dejar detras solo lo secundario.
    5. Los props miran a la camara (contra muros del fondo o de doble cara); contra muros cercanos se ven de espaldas.
    6. Columnas y arcos solo detras de los objetivos o a mas de altura/0.7 m de ellos; comprobar con rayos antes de
       unir los modulos (los nombres dicen que tapa).
    7. Las rejas tapan ~40 % de lo que hay detras. Ventanilla de 1.2 m sin barrotes en la LINEA DE VISTA de
       CAM_Iso: lo que esta a d metros detras de la reja se ve desplazado d en diagonal, asi que el NPC va pegado
       al tablero (d = 0.7 m) y la ventanilla se corre d/2 hacia la camara; el NPC queda dentro de su luz.
    8. Navmesh: con celdas de 0.5 m una puerta de 1.2 m no pasa (margen 0.3); usar 0.25 m. La escalera necesita
       tiras planas en ambos extremos para unir las rejillas; los pasos de 1.2 m se comprueban con holgura en
       rejilla de 0.1 m.
    9. Nada coplanario: el entarimado alto empieza en el borde de la arcada; separaciones >= 1 cm.
    10. Losas remendadas con MAT_Stone_Repair parecen agujeros desde arriba: usar caliza gastada.
    11. La luz se hornea en Godot (LightmapGI); los Empties llevan color, energia y radio; un solo azul por sala.
    12. Convencion de props "+Y = frente": quien mira el prop de frente tiene la +X local a su IZQUIERDA. Texto en
        una cara +Y (numeros de las cajas, rotulos) lleva la u invertida, y las series se numeran recorriendo -X local
        para leerse de izquierda a derecha. Comprobarlo siempre con una captura de cerca.

19. Etapa 28: props a mano, importacion CC0 (Mercado), pendientes de la ciudad e interiores de las Moradas
-----------------------------------------------------------------------------------------------------------
  Scripts: tools/blender/props_mano.py + build_stage28_props.py + capture_stage28_props.py (props a mano);
  build_stage28_import.py (Quaternius / Avramania) y tools/fetch_sketchfab_cc0.py (descarga CC0 con comprobacion de
  licencia en la API y en la pagina); build_stage28_city.py (concordia_v26 -> concordia_v28); stage28_moradas_int.py +
  build_stage28_int.py + capture_stage28_int.py (vitrinas e interiores). Informes: docs/reports/stage28_*.json.

  Generadores de IA: en esta sesion no hay herramientas get_addon_status / generate_3d (no hay servidor MCP de
  Blender conectado): no se ha generado ni comprobado ningun modelo de IA. Los 4 objetos de la lista se hicieron a mano.

  Props a mano (concordia_props_v01.blend, BLD_PROPS_INT; props_int_mano.glb), <= 1,000 tris, origen en la base, +Y al
  frente, solo materiales de Concordia (cuero = MAT_Hide_R05, vidrio = MAT_Glass_R04):
    Los 4 de la lista de IA: Loom 746, Forge_Bellows 386, Dress_Form 350, Miner_Helmet 310.
    14 triviales: Ingots_Coal 288, Cloth_Rolls 246, Bar_Counter 150, Trestle 68, Bench_Vise 120, Auction_Gavel 188, Ink_Seal 220, Baker_Peel 40, Tanning_Frame 208, Herb_Rack 436, Fish_Crates 364, Longbow 276, Spinning_Wheel 364, Jeweler_Case 286.
    Total 5,046 tris; cajas -colonly en los de suelo.

  Importacion CC0 (props_int_<lote>.glb; aprobada por el usuario con criterios): Mercado 36 props
    (20,205 tris), Oficios 26 (17,097), Clases 13 (10,934).
    Quaternius Fantasy Props MegaKit (licencia en licenses/) y Avramania Low Poly Medieval (licencia CC0 comprobada el
    dia de la descarga en la API y en la pagina de cada modelo). Materiales reasignados: Quaternius por nombre de
    material (MI_Trim_Furniture -> madera, MI_Trim_Metal -> hierro/bronce, pergamino -> cuero, *_Vertex por color);
    Avramania por color de su paleta (o del material si no tiene paleta) al material de Concordia mas cercano (muebles
    y armas solo entre madera, hierro, bronce, piedra, tela y paja; comida con la lista amplia). Criterios: <= 500 tris
    los pequenos (lado mayor <= 0.6 m) y <= 1,500 los medianos, escala en metros, origen en la base; lo que pasa se
    decima con normal map horneado (512 los pequenos, 1K los medianos; UV 'UVBake'): Q_Barrel_Holder 2,676 -> 1,480; Q_CandleStick 730 -> 479; Q_Chandelier 5,680 -> 1,479; Q_BookStand 1,526 -> 1,479; Q_Scroll_1 512 -> 480; Q_Scroll_2 672 -> 480; Q_Chest_Wood 2,546 -> 1,480; Q_Coin_Pile 960 -> 480; Q_Pouch_Large 730 -> 480; AV_Cheese_Wheel 1,270 -> 480; AV_Grapes 708 -> 480; AV_Grain_Sack 938 -> 480; Q_Potion_4 536 -> 480; AV_Herb_Bundle 666 -> 480; Q_Bucket_Wooden_1 976 -> 480; AV_Handaxe 504 -> 480; Q_Chain_Coil 3,744 -> 1,480; Q_WeaponStand 2,084 -> 1,480.
    Memoria de texturas total ~173.7 MB de 220 (18 normal maps de props = 12.0 MB).

  Ciudad (concordia_v28.blend; informe stage28_ciudad.json):
    Faro: MER_Casa_01 (decoracion) de 3 a 2 plantas (14.0 -> 10.8 m): libera el punto del anillo r 100. Visibilidad:
      avenida 91.7 %, anillo 71.1 %, callejon 76.4 %, diagonal 79.6 %. Lista de puntos sin Faro en TODO_GODOT.
    Moradas: balcones de 0.35 m (<= 1.2). Escalera: se mantiene la de la etapa 26; la prueba literal "tramo alto en el
      extremo alejado" en las 69 casas subio las puertas tapadas de 16 a 48 (stage28_moradas_prueba_far.json). Cuerpo/
      alero: alero 0.3 m y, si no basta, 2 plantas, solo si libera puertas: Morada_SO_036 y SO_037 a 2 plantas
      (-6 viviendas: 1,404 -> 1,398); el resto se deshizo. Puertas tapadas: 16 -> 13 (tolerancia 10).
    Tubos (ruta oeste, decision del usuario: la ruta por el Banco no cabe con tramos <= 16 m): Tesoreria -> 1 pilar en
      terreno sin calle -> MER_Casa_01 -> Posada -> arco sobre la avenida -> Casa del Registro -> 2 pilares junto al
      canal -> Faro. 13 pilares de piedra de 0.6 m (10 en techos, 3 en terreno verde; ninguno en calle, plaza ni
      fuente), 4 arcos de piedra en los tramos de mas de 10 m (maximo 14.42 m), tubo inclinado entre apoyos
      (sin quiebros verticales salvo la salida y la entrada), >= 1.2 m sobre tejados (minimo medido 1.6 m) y >= 5 m
      sobre calles (minimo 9.44 m), 0 choques con edificios. 130.3 m, 7,418 tris (<= 8,000; rectos
      de hasta 6 m). CRV_LightPipe_Tesoreria_Faro y MARKER_PipeSupport_01-13 actualizados. Faro: 0 puntos tapados
      por los tubos; visibilidad sin cambios.
    Razas B05: escalon de la puerta medido en +-0.8 m x 0.1-0.6 m: Casa_04 0.193 m y Casa_05 0.193 m (> 0.15): un
      peldano de piedra a lo largo de toda la fachada (4.2 m, huella 0.35 m), contrahuellas 0.096 m; el terreno no se
      toca (los barrios de razas siguen siendo plantilla).

  Vitrina de trofeos (MARKER_TrophyCase; props_trophy_cases.glb): un solo material MAT_TrophyCase (atlas 512: madera
    oscura de Concordia + vidrio alfa 0.3). Pared 1.0 x 0.4 x 1.9 m, 9 slots: 128 / 82 / 18 tris
    (LOD0 / LOD1 / LOD2); mesa 1.2 x 0.6 x 1.0 m, 6 slots: 132 / 120 / 20; nichos 1.2 x 0.35 x 1.6 m,
    9 slots: 230 / 86 / 18. Slots = Empties MARKER_Trophy_Slot_xx (+Y al frente).

  Interiores tipo (concordia_moradas_int_v01.blend; int_morada_<plantilla>.glb), build_interior estilo entramado,
  referencias Cesky Krumlov / Rothenburg (vigas bajas a 2.7 m, hogar de piedra, revoco sobre zocalo de tablas,
  ventanas pequenas), giro fijo de -90 grados (puerta +Y y lado +X = muros cercanos):
    Habitacion 4 x 5 x 2.7: cama, baul (40), vitrina de pared, ventana, mesa y taburete. Tris 3,366 de 8,000.
    Casa pequena 6 x 8 x 2.7 con patio de 2.5 m (tabique con puerta = WALL_Near_Casa): baul (100), mesa de trabajo
      (MARKER_WorkStation_01), hogar, mesa y sillas, cama, vitrina de nichos. Tris 6,623 de 15,000.
    Casa grande 8 x 10 x 6.4, dos plantas: entreplanta de 4 m sobre el fondo (LEVEL_1), escalera de 1.2 m a 32.6
      grados con rellano de 1.3 m al pie, sala para recibir, dos mesas de oficio (WorkStation_01/02), baul (200),
      vitrina de pared (slots 01-09) y de mesa (10-15), jardinera de hierbas junto a la fachada (MARKER_Garden),
      dormitorio arriba. Tris 10,148 de 28,000.
    Las tres: navmesh (celda 0.25) conectada a todos los puntos clave, pasos de 1.2 m, rayos desde CAM_Iso a la vitrina,
    el baul y las mesas de oficio 100 %, un solo azul (lamparilla de esquirla), MARKER_Decor_Slot_xx para decorar.

  Lecciones nuevas (etapa 28):
    13. Plantillas privadas: giro fijo respecto a CAM_Iso (-90) para que la puerta y +X sean los muros cercanos; todo
        el mobiliario contra -X / -Y. La orientacion de la casa en la ciudad no importa.
    14. Escalera de 5 m en una casa de 10: la entreplanta debe retirarse (y = -1) para dejar >= 1.2 m al pie; y ningun
        mueble bajo la llegada (el baul quedo debajo y la prueba de 1.2 m lo detecto).
    15. Blender exige nombres unicos en todo el archivo: exportar cada plantilla con nombres limpios y renombrarla
        despues; numerar seguidos los slots de varias vitrinas en la misma escena.
    16. Un tabique entre zonas (patio / casa) tapa desde CAM_Iso: va en su propio grupo WALL_Near_<Recinto>.
    17. Bajo una entreplanta, escalar en Z las piezas altas del kit (campana del hogar) y dejar >= 4 cm a las vigas.
    18. Assets con textura de paleta: el color mas cercano necesita listas por categoria (si no, madera -> teja).
    19. Patas de varilla asoman bajo z = 0: recortarlas al suelo; piezas coplanarias (postes y largueros) dan manchas
        negras: separarlas 1 cm.
    20. Remedios que cuestan viviendas (2 plantas = -3 puertas): aplicarlos solo si liberan puertas y deshacerlos si no.


  Puertas de Moradas tapadas aceptadas (etapa 28, decision del usuario: 13 de 1,404 = 0.93 % < 1 %):
    puerta | parcela (n.) | causa | casa que tapa | distancia por el rayo de CAM_Iso hasta lo que tapa
    NE_022_1 | Morada_NE_022 (NE-306) | balcon/escalera | Morada_NE_021 | 7.62 m
    NE_047_1 | Morada_NE_047 (NE-507) | balcon/escalera | Morada_NE_046 | 8.0 m
    NE_063_1 | Morada_NE_063 (NE-609) | cuerpo/alero | Morada_NE_061, Morada_NE_062 | 8.86 m
    NE_070_1 | Morada_NE_070 (NE-616) | balcon/escalera | Morada_NE_069 | 3.97 m
    NE_013_1 | Morada_NE_013 (NE-207) | balcon/escalera | Morada_NE_012 | 4.78 m
    SO_048_1 | Morada_SO_048 (SO-508) | balcon/escalera | Morada_SO_049, Morada_SO_050 | 7.88 m
    SO_064_1 | Morada_SO_064 (SO-610) | cuerpo/alero | Morada_SO_065, Morada_SO_066 | 8.86 m
    SO_018_3 | Morada_SO_018 (SO-302) | balcon/escalera | Morada_SO_019 | 3.99 m
    SO_035_1 | Morada_SO_035 (SO-407) | cuerpo/alero | Morada_SO_036 | 8.83 m
    SO_035_2 | Morada_SO_035 (SO-407) | cuerpo/alero | Morada_SO_036 | 6.54 m
    SO_035_3 | Morada_SO_035 (SO-407) | cuerpo/alero | Morada_SO_036, Morada_SO_037 | 4.78 m
    SO_058_3 | Morada_SO_058 (SO-604) | balcon/escalera | Morada_SO_059 | 3.95 m
    SO_059_3 | Morada_SO_059 (SO-605) | balcon/escalera | Morada_SO_060 | 4.65 m

  Revision de capturas (etapa 28) - pendientes visuales, sin corregir:
    - Las ventanas de las casas usan INT_Window_Int (reja de hierro del Banco); las referencias piden ventanas
      pequenas con postigos: falta una variante del kit (INT_Window_Shutter).
    - La llama del hogar del kit (MAT_Window_Warm) se lee como un cono blanco a 1.7 m: falta un material de llama
      calido o particulas en Godot (ya anotado en TODO_GODOT para el Banco).
    - Vitrinas: con alfa 0.3 el vidrio casi no se ve y las baldas interiores salen oscuras en iluminacion neutra; en
      la escena (luz calida + lamparilla) se leen como armario acristalado.


20. Etapa 29: interiores unicos (1/n): Tesoreria de la Muralla y Santuario del Retorno
-------------------------------------------------------------------------------------
  Archivo: blender/concordia_interiors_unicos_v01.blend (kit y props de las etapas 27-28, materiales de concordia_v28).
  Scripts: tools/blender/stage29_tesoreria.py, stage29_santuario.py, build_stage29_int.py (construye, comprueba y
  exporta; `-- tesoreria santuario`), capture_stage29_int.py. Informes: docs/reports/stage29_<interior>.json.
  Datos de cada edificio (volumen, giro, puerta, ventanas) leidos del master de la ciudad (concordia_v28): el master
  no se modifica. Todo hecho a mano (regla del usuario: ni assets descargados ni IA en la Tesoreria y el Santuario).
  Cambios en el kit (interior_kit.py): custom_module() para ventanas y puertas a la medida del exterior (los tipos de
  hueco de Interior.shell aceptan su nombre); m_window / m_door con medidas; las dos losas remendadas de
  INT_Floor_Stone_B ya no se solapan (ver leccion 24).

  Tesoreria (int_tesoreria.glb, 1.39 MB): volumen 26.4 x 13.6 x 8.8 m (diferencia 0.0), dos plantas de 4.4 m.
    Giro -90: CAM_Iso mira desde +X +Y; muros cercanos +X (WALL_Near_A) y +Y fachada (WALL_Near_B). Todo lo importante
    contra -X y -Y, de cara a la camara. Ventanas en las posiciones y medidas del exterior (planta baja 1.0 x 1.4 m,
    planta alta 1.4 x 2.2 m, fachada 1.2 x 1.6 m; puerta 1.6 x 3.0 m).
    Planta baja: 2 mostradores contra -X (modulo de ventanilla de cajero de 1.2 m + reja de 1.6 m): 1 = Vender
      (Tesorero, MARKER_NPC_Slot_01) y 2 = Cambio (MARKER_NPC_Slot_02, npc = Cambista: propuesta), balanza grande de
      bronce en cada uno (TES_Scale_Large 169 tris); arcada de 6 vanos (INT_Arch_3m) bajo el borde de la galeria;
      4 tubos de luz PIPE_Light_01-04 (0.4 m, MAT_Pipe_Glass + nucleo MAT_Pipe_Light_Core emision 1.5, basa de piedra,
      abrazaderas) por los pilares de la arcada hasta atravesar el techo (en el desvan siguen hasta las salidas
      MARKER_PipeOutlet_TesoreriaMuralla_*); 4 vitrinas delante de la arcada, 3 variantes a mano (A armario 148,
      B mesa 122, C pedestal 120 tris; vidrio MAT_Pipe_Glass sin emision): Brillante (A, 20 esquirlas), Opaca (B, 12),
      Madura (C, 7, la unica emisiva) y Latente (B, 12); esquirla = prisma hexagonal con puntas (24 tris), un material
      por tipo (MAT_Shard_Opaca #7C8288, _Brillante #B6CFDF, _Latente #5B8DB8, _Madura #8FD0FF emision 1.0);
      contaduria bajo la galeria (estantes, mesa, cofres, sacos de monedas), bancos de espera, 2 coronas de velas.
      Escalera de piedra de 1.98 m contra +X: 22 peldanos, 6.6 m de recorrido, 33.7 grados; sube por un hueco del
      forjado y deja libre la ventana de la planta baja que tiene detras.
    Planta alta (LEVEL_1): galeria con balaustrada, archivo, despacho del tesorero (WALL_Near_Despacho, dentro de
      LEVEL_1: tabique con puerta de 1.4 m y frente con ventana interior) con la caja fuerte (TES_Safe, 504 tris:
      hierro con cantos, rueda de 6 radios, bandas remachadas, bocallave y placa con escudo).
    Interaccion: MARKER_Interact_Tesoreria_Vender (mostrador 1), MARKER_Interact_Tesoreria_Cambio (mostrador 2).
    Luz: 24 empties (coronas, lamparas, velas, 10 ventanas) y un solo azul (LIGHT_Pipes_Glow).
    Verificacion: 21,310 tris (Shell 8,078, LEVEL_1 2,428, mobiliario 7,482); rayos desde CAM_Iso: Tesorero y
    Cambista 75 % (los 3 puntos tapados son las rodillas tras el tablero), mostradores, tubos y las 4 vitrinas 100 %;
    con LEVEL_1 visible igual; caja fuerte y mesa del despacho 100 %. Navegacion 5,258 caras, todas conectadas;
    los 14 puntos clave (mostradores, NPC, vitrinas, contaduria, escalera, galeria, despacho, caja fuerte) se
    alcanzan con pasos de 1.2 m.

  Santuario (int_santuario.glb, 0.73 MB): volumen 13.8 x 9.6 x 9.0 m (diferencia 0.0). Giro -135: CAM_Iso mira a lo
    largo de -Y; solo la fachada (+Y) es muro cercano (WALL_Near_A); el muro -Y con sus 5 ventanales queda de frente.
    Muros a mano (los ventanales de 6 m no caben en el shell por plantas) con los huecos del exterior: 5 ventanales
    de 1.4 x 6.0 m en -Y, 4 y una ventana alta sobre la puerta en +Y, 2 ventanas de 1.0 x 4.6 m en cada hastial;
    cabeza apuntada, parteluz, dos luces, circulo, plomos; vitral MAT_Stained_Glass_Blue (emision 0.6).
    Zocalo-banco de piedra, imposta, 6 contrafuertes interiores por muro largo (pilar + 3 columnillas + capitel).
    Boveda (CEILING, todo lo que pasa de 9.0 m): la pedida (clave 14 m, apuntada con arranque vertical) CHOCA con la
      cubierta exterior (a dos aguas de 45 grados desde 9.0 m): se saldria hasta 1.84 m por los faldones. Se baja a
      clave 12.7 m con un perfil de dos arcos apuntados de flecha 0.06 x cuerda que sigue la pendiente; holgura minima
      medida vertice a vertice contra SANTUARIO_Roof (rejilla de 0.1 m, incluidos los cabios de madera): 0.127 m.
      Nervios fajones en los contrafuertes, diagonales por tramo, espinazo y claves de bronce; plementeria
      MAT_Vault_Stars (1K a mano: azul #2E4057 con estrellas #C9B98A, sin emision); timpanos con oculo de 2.1 m (el
      exterior es de 3 m: el interior de 3 m no cabe bajo la boveda baja). Los 218 vertices del grueso de los
      timpanos quedan dentro del hastial exterior.
    Pozo: SANTUARIO_Well del master (290 tris, MAT_Water), sin 'provisional'; un solo farol de esquirla colgado
      encima (unica luz azul). Cuidador (MARKER_NPC_Slot_01) junto al pozo, mesa con 3 raciones y 3 antorchas
      (SAN_Table, SAN_Ration, SAN_Torch a mano), MARKER_Interact_Santuario_Kit (propuesta), 8 bancos (BANK_Bench),
      2 candeleros. MARKER_Respawn (tipo = respawn) delante del pozo, mirando a la salida.
    Verificacion: 10,537 tris; rayos desde CAM_Iso: reaparicion, Cuidador, mesa, pozo, farol y ventanales del fondo
      100 %; navegacion 889 caras conectadas, 10 puntos clave con pasos de 1.2 m.
    El SANTUARIO_Well del master (concordia_v28) conserva provisional = true: no se ha guardado otra version del
    master por una propiedad (78 MB). En la proxima version del master conviene quitar esa copia del exterior
    (queda escondida dentro del edificio cerrado).

  Lecciones nuevas (etapa 29):
    21. Ventanas del interior = las del exterior: custom_module() en el espacio del modulo (z real / escala de la
        planta). El modulo del kit escalado a 4.4 m ponia la ventana 0.25-0.8 m mas alta que la de la fachada en un
        muro de 0.36 m.
    22. Ventanilla de cajero: con el NPC a 0.7 m de la reja, la ventanilla se corre 0.40 m hacia la camara (no
        0.35): con 0.35 los rayos del lado de la camara rozan la jamba de 6 cm (50 % en vez de 75 %).
    23. Regiones de navegacion de una misma planta: deben solaparse (>= 2 x margen); dos rectangulos que solo se
        tocan quedan separados por el margen del agente (la galeria y el rellano de la escalera no se unian).
    24. Las dos losas remendadas de INT_Floor_Stone_B podian solaparse a la misma altura: caras coplanarias (salen
        negras en Cycles, parpadean en Godot). Corregido en el kit; el Banco (int_banco.glb) lo tiene hasta que se
        rehaga.
    25. Boveda bajo una cubierta de 45 grados: una boveda apuntada con arranque vertical atraviesa enseguida el
        faldon; perfil de poca flecha que siga la pendiente, holgura medida contra la malla real de la cubierta con
        rejilla de 0.1 m (los cabios quedan entre muestras de 0.4 m) y nervios de seccion girada bajados 1.45 r.
    26. Tubos que atraviesan el techo: repartir las vigas del techo para que ninguna cruce un tubo (>= 0.5 m).
    27. Varios interiores en un .blend: renombrar tras exportar (leccion 15) o el segundo sale con ".001" en sus
        marcadores y grupos (Godot no los encontraria).
    28. Muros con huecos mas altos que una planta (Santuario): sin shell por plantas (cortaria los ventanales con
        impostas); muros a mano con slab_holes y los huecos del exterior.
    29. Huecos que llegan al suelo (arcos de la arcada, puertas, tabiques): slab_holes deja la cara del umbral a la
        altura del suelo, coplanaria con el (franjas negras en la base de los vanos, tambien en el Banco).
        Interior.realize() quita las caras horizontales de las piezas que no son suelo a la altura de cada nivel de
        suelo (Tesoreria 127, Santuario 9).
    30. Exportacion: con export_keep_originals el .glb llevaba cada imagen dos veces (uri y copia incrustada) y Godot
        avisaba 52 veces al importar; stage11_godot.export_glb deja solo la uri (tools/blender/glb_tools.py). Los
        .glb anteriores (Banco, Moradas) tienen el aviso hasta que se vuelvan a exportar.
```


## Anexo C — README_markers.txt (marcadores)

```text
CONCORDIA - Convencion de marcadores (Empties)
==============================================

Regla unica para TODOS los Empties MARKER_*:

  +Y local  = hacia FUERA / hacia el FRENTE (la fachada, la salida, lo que "mira" el objeto)
  +Z local  = arriba
  +X local  = derecha mirando hacia el frente desde detras (X = Y x Z)

Equivalencia en Godot 4 (export glTF con +Y Up):
  Blender +Y  ->  Godot -Z   (= "adelante", lo que devuelve -basis.z)
  Blender +Z  ->  Godot +Y
  Blender +X  ->  Godot +X
  Es decir: un Node3D importado "mira" (look_at / -basis.z) hacia donde apuntaba +Y en Blender.

Posicion: el origen del Empty es el punto de apoyo (base, a nivel del suelo o de la plataforma).

Aplicacion por familia
- MARKER_Gate_E/N/W/S ............ en r=200, Z=+6.0; +Y radial hacia el exterior (la salida).
                                   (Hasta la v04 inicial usaban +X hacia fuera: CORREGIDO.)
- MARKER_WallSlot_00..47 ......... en r=200, Z=+6.0; +Y radial hacia el exterior.
                                   Rotacion Z = 7.5*k - 90 grados.
- MARKER_TowerDoor_kNN ........... puerta de cada torre de guardia, a nivel del camino de ronda
                                   (+18.4 abs); +Y sale de la torre hacia el camino.
- MARKER_PlazaBuilding_01..08 .... centro de la fachada (r=48); +Y hacia la plaza (fachada).
                                   Propiedad door_direction = "+Y".
- MARKER_Faro / _Santuario / _SalonHazanas / _Obelisco ... centro del basamento; +Y hacia la
                                   plaza (fachada principal). Propiedad door_direction = "+Y".
- MARKER_Bld_* (v05, MARKERS_DISTRICTS/MARKERS_<Distrito>) ... origen = CENTRO de la huella a la
                                   cota de su plataforma (pad_z); +Y = fachada de la puerta principal (mira a
                                   la calle o plaza de 'front_street'). Propiedades:
                                     footprint "AxF" (A = ancho de fachada, eje X local; F = fondo, eje Y local),
                                     footprint_w, footprint_d (m), door_direction = "+Y", interior (bool:
                                     true = edificio con servicio y interior jugable; false = decoracion),
                                     type, label, district, pad_z, front_street, shape (rect | circle) y, segun
                                     el caso, service, barrio, race_slot, class_slot, open_foundry, ...
                                   Los puestos de la Plaza de Provisiones (MARKER_Bld_PuestoProvisiones_NN,
                                   3x3) llevan interior = false y has_service = true (se atienden desde fuera).
- MARKER_Prop_* .................. atrezo con funcion: FuenteMercado, Plazuela_NN (type fountain | tree),
                                   TablonGrupos (entrada de la Posada, interactive = true). +Y = frente.
- MARKER_Awning_NN ............... toldo de la fachada de cada parcela del Mercado a calle de 10 m;
                                   en la puerta, +Y hacia la calle; width_m = ancho de fachada.
- MARKER_TrainingZone_01..06 ..... zonas de maniquies de la Plaza de las Armas (footprint, dummies = 4).
- MARKER_ArcheryRange_Targets .... dianas del campo de tiro del Gremio de Cazadores (+Y hacia el gremio).
- MARKER_CauceReserve_Outlet ..... fin del corredor reservado para el Cauce (desague del bastion k=46).
- MARKER_Portal_Center ........... centro del pedestal (+8.9); +Y = Norte (avenida Mercado).
- MARKER_Runestone_01..07, MARKER_Descent_Pedestal_01..21 ... su frente mira al Portal:
                                   +Y hacia el centro de la plaza.

Propiedades personalizadas habituales (se exportan como "extras" de glTF -> metadata en Godot):
  k, angle_deg, type, piece, floor, door_direction, height_m, occludes_iso, nav_exclude
```


## Anexo D — README_masks.txt (máscaras de terreno)

```text
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
```


## Anexo E — README_personaje.txt

```text
CONCORDIA - README_personaje: elfo base + equipo inicial del Sanador (cierre PJ5, version 1.0 (PJ5, 2026-11-11))
========================================================================================================
Blend maestro: blender/concordia_personajes_master.blend (propiedad de escena concordia_personajes_version).
Historia de cada etapa (PJ1-PJ5) y decisiones: README_personajes.txt. Godot: TODO_GODOT_personaje.txt.
Fuentes y licencias: ASSETS_LICENSES.md (MakeHuman CC0 + MPFB como herramienta, UAL de Quaternius CC0).

1. ARCHIVOS (export/godot/personajes/, glTF 2.0 .glb, +Y arriba, metros, todos con el MISMO esqueleto)
--------------------------------------------------------------------------------------------------------
  personaje_elfo_base.glb        3198.1 KB  esqueleto + cuerpo modular (6 piezas) + ojos + cabello, LOD0 y LOD1
  elfo_sanador_robe_top.glb      1904.9 KB  tunica (con el colgante emisivo), LOD0 y LOD1
  elfo_sanador_skirt.glb         1905.7 KB  falda en dos paneles, LOD0 y LOD1
  elfo_sanador_hood.glb          1902.3 KB  capucha / esclavina, LOD0 y LOD1
  elfo_sanador_belt.glb          1907.8 KB  cinturon con bolsitas, LOD0 y LOD1
  elfo_sanador_boots.glb         1873.7 KB  botas, LOD0 y LOD1
  elfo_sanador_bracers.glb       1856.5 KB  vendas de los antebrazos, LOD0 y LOD1
  elfo_sanador_lod2.glb          3024.8 KB  LOD2: una sola malla del Sanador equipado (esqueleto simplificado)
  elfo_sanador_anims.glb          269.6 KB  esqueleto + 4 animaciones propias, sin mallas
  Los .glb llevan sus texturas dentro (cada prenda incluye el atlas del Sanador): en Godot se comparten extrayendo
  los materiales una vez (TODO_GODOT_personaje.txt PJ5, paso 2).

2. PRESUPUESTO REAL (triangulos)
--------------------------------------------------------------------------------------------------------
  pieza                   LOD0    LOD1
  PJ_Elfo_Head            1196     974
  PJ_Elfo_Torso            516     246
  PJ_Elfo_Arms             128      64
  PJ_Elfo_Hands           1068     400
  PJ_Elfo_Legs             224     104
  PJ_Elfo_Feet             196     100
  PJ_Elfo_Eyes             172     152
  Hair_Elf                 472     320
  Robe_Top                 646     528
  Robe_Skirt               832     706
  Hood                     640     500
  Belt_Pouches             676     414
  Boots                    324     228
  Bracers                  160     112
  TOTAL                   7250    4848   (limites: LOD0 <= 10.000, LOD1 <= 5.000)
  LOD2 (PJ_Elfo_Sanador_LOD2): 1757 tris (limite 1.800), una malla, 3 superficies (piel, ojos, atlas);
       sin la piel que tapa la ropa del Sanador; diezmado desde 6250 tris (ratio 0.282).
  LOD1: Decimate (colapso, simetria X salvo cinturon y pelo) con reparto por pieza (mas en manos y piel tapada,
       menos en cara, ojos y ropa), ratio base 0.681. Protegidos en LOD1 y LOD2: silueta de las orejas,
       dobladillo de la falda y de la tunica, costuras entre piezas del cuerpo; la cara con proteccion suave.
  Materiales: 3 (MAT_Elfo_Piel, MAT_Elfo_Ojos, MAT_Sanador_Atlas). Texturas 1K: piel albedo + normal + ORM
    (textures/personajes/elfo/elfo_m_*_1k.png; ojos albedo 256), atlas del Sanador albedo + normal + ORM +
    emision (textures/personajes/sanador/sanador_atlas_*_1k.png). ORM: AO en R, rugosidad en G, metal en B.
    Emision: solo el colgante (82 pixeles del atlas, 7 caras de Robe_Top), #8FD0FF.
    Nota: MAT_Elfo_Piel tiene en Blender dos albedos de piel (abedul y corteza); el glb exporta el primero (abedul)
    y el exportador avisa de ello. El tono corteza se aplica en Godot cambiando la textura del material.

3. CONVENCION DE NOMBRES
--------------------------------------------------------------------------------------------------------
  Piezas del cuerpo: PJ_Elfo_<Head|Torso|Arms|Hands|Legs|Feet>, ojos PJ_Elfo_Eyes, pelo Hair_Elf.
  Prendas: nombre de la pieza en ingles (Robe_Top, Robe_Skirt, Hood, Belt_Pouches, Boots, Bracers); archivo
    elfo_<clase>_<pieza>.glb. Cada prenda guarda en sus extras: clase, oculta (que grupos HIDE_* tapa), oculta_motivo.
  LOD: <pieza>_LOD1 en el mismo .glb; LOD2 = PJ_Elfo_<Clase>_LOD2 en su propio .glb.
  Materiales: MAT_<Raza|Clase>_<Uso>. Texturas: <raza>_<sexo>_<mapa>_<res>.png / <clase>_atlas_<mapa>_<res>.png.
  Animaciones: nombre claro en ingles, las ciclicas con -loop (Heal_Channel-loop); UAL: sus nombres (_Loop).
  Huesos: los del SkeletonProfileHumanoid de Godot 4.7 (LeftUpperArm...) + extra con nombre propio.

4. HUESOS (70; deforman 65; perfil de Godot 56 + 14 extra; LOD2: pesos solo en los marcados con *)
--------------------------------------------------------------------------------------------------------
  Root                     padre -                NO deforma perfil  *
  Hips                     padre Root             deforma    perfil  *
  Spine                    padre Hips             deforma    perfil  *
  Chest                    padre Spine            deforma    perfil  *
  UpperChest               padre Chest            deforma    perfil  *
  Neck                     padre UpperChest       deforma    perfil  *
  Head                     padre Neck             deforma    perfil  *
  LeftEye                  padre Head             deforma    perfil
  RightEye                 padre Head             deforma    perfil
  Jaw                      padre Head             deforma    perfil
  Head_Top                 padre Head             NO deforma extra
  Hair_01                  padre Head             deforma    extra
  Hair_02                  padre Hair_01          deforma    extra
  Hair_03                  padre Hair_02          deforma    extra
  Hair_04                  padre Hair_03          deforma    extra
  LeftShoulder             padre UpperChest       deforma    perfil  *
  LeftUpperArm             padre LeftShoulder     deforma    perfil  *
  LeftLowerArm             padre LeftUpperArm     deforma    perfil  *
  LeftHand                 padre LeftLowerArm     deforma    perfil  *
  LeftThumbMetacarpal      padre LeftHand         deforma    perfil
  LeftThumbProximal        padre LeftThumbMetacarpal deforma    perfil
  LeftThumbDistal          padre LeftThumbProximal deforma    perfil
  LeftIndexProximal        padre LeftHand         deforma    perfil
  LeftIndexIntermediate    padre LeftIndexProximal deforma    perfil
  LeftIndexDistal          padre LeftIndexIntermediate deforma    perfil
  LeftMiddleProximal       padre LeftHand         deforma    perfil
  LeftMiddleIntermediate   padre LeftMiddleProximal deforma    perfil
  LeftMiddleDistal         padre LeftMiddleIntermediate deforma    perfil
  LeftRingProximal         padre LeftHand         deforma    perfil
  LeftRingIntermediate     padre LeftRingProximal deforma    perfil
  LeftRingDistal           padre LeftRingIntermediate deforma    perfil
  LeftLittleProximal       padre LeftHand         deforma    perfil
  LeftLittleIntermediate   padre LeftLittleProximal deforma    perfil
  LeftLittleDistal         padre LeftLittleIntermediate deforma    perfil
  Weapon_L                 padre LeftHand         NO deforma extra
  RightShoulder            padre UpperChest       deforma    perfil  *
  RightUpperArm            padre RightShoulder    deforma    perfil  *
  RightLowerArm            padre RightUpperArm    deforma    perfil  *
  RightHand                padre RightLowerArm    deforma    perfil  *
  RightThumbMetacarpal     padre RightHand        deforma    perfil
  RightThumbProximal       padre RightThumbMetacarpal deforma    perfil
  RightThumbDistal         padre RightThumbProximal deforma    perfil
  RightIndexProximal       padre RightHand        deforma    perfil
  RightIndexIntermediate   padre RightIndexProximal deforma    perfil
  RightIndexDistal         padre RightIndexIntermediate deforma    perfil
  RightMiddleProximal      padre RightHand        deforma    perfil
  RightMiddleIntermediate  padre RightMiddleProximal deforma    perfil
  RightMiddleDistal        padre RightMiddleIntermediate deforma    perfil
  RightRingProximal        padre RightHand        deforma    perfil
  RightRingIntermediate    padre RightRingProximal deforma    perfil
  RightRingDistal          padre RightRingIntermediate deforma    perfil
  RightLittleProximal      padre RightHand        deforma    perfil
  RightLittleIntermediate  padre RightLittleProximal deforma    perfil
  RightLittleDistal        padre RightLittleIntermediate deforma    perfil
  Weapon_R                 padre RightHand        NO deforma extra
  Back_Slot                padre UpperChest       NO deforma extra
  LeftUpperLeg             padre Hips             deforma    perfil  *
  LeftLowerLeg             padre LeftUpperLeg     deforma    perfil  *
  LeftFoot                 padre LeftLowerLeg     deforma    perfil  *
  LeftToes                 padre LeftFoot         deforma    perfil  *
  RightUpperLeg            padre Hips             deforma    perfil  *
  RightLowerLeg            padre RightUpperLeg    deforma    perfil  *
  RightFoot                padre RightLowerLeg    deforma    perfil  *
  RightToes                padre RightFoot        deforma    perfil  *
  Skirt_Front_01           padre Hips             deforma    extra  *
  Skirt_Front_02           padre Skirt_Front_01   deforma    extra
  Skirt_Front_03           padre Skirt_Front_02   deforma    extra
  Skirt_Back_01            padre Hips             deforma    extra  *
  Skirt_Back_02            padre Skirt_Back_01    deforma    extra
  Skirt_Back_03            padre Skirt_Back_02    deforma    extra
  Ranuras sin deformacion: Weapon_R (baston, +Y = eje del asta), Weapon_L, Back_Slot, Head_Top. Jaw sin pesos.

5. GRUPOS HIDE_* (ocultar la piel bajo la ropa) y que prenda los usa
--------------------------------------------------------------------------------------------------------
  PJ_Elfo_Torso  HIDE_Torso (280 de 280 vertices: toda la pieza), HIDE_Torso_Sup (222), HIDE_Torso_Inf (58)
  PJ_Elfo_Arms   HIDE_Arms (80 de 80), HIDE_Arms_Sup (48), HIDE_Arms_Inf (16)
  PJ_Elfo_Hands  HIDE_Hands (544 de 544)
  PJ_Elfo_Legs   HIDE_Legs (128 de 128), HIDE_Legs_Sup (48), HIDE_Legs_Inf (32)
  PJ_Elfo_Feet   HIDE_Feet (108 de 108)
  PJ_Elfo_Head   ninguno (la cabeza nunca se oculta)
  Robe_Top -> Torso:HIDE_Torso_Sup, Arms:HIDE_Arms_Sup | Robe_Skirt -> Torso:HIDE_Torso_Inf, Legs:HIDE_Legs_Sup
  Boots -> Legs:HIDE_Legs_Inf, Feet:HIDE_Feet | Bracers -> Arms:HIDE_Arms_Inf | Hood, Belt_Pouches, Hair_Elf -> nada
  En Blender son modificadores Mask con driver; glTF no lleva ni vertex groups ni mascaras, asi que en
  Godot se oculta la pieza entera cuando queda tapada del todo (Feet con botas; Torso con tunica + falda) o se usa
  la mascara en el shader de piel (TODO_GODOT_personaje.txt PJ3 punto 5).

6. ANIMACIONES DEL ELFO SANADOR (lista final; duraciones leidas con el lector glTF de Godot 4.7)
--------------------------------------------------------------------------------------------------------
  nombre                    duracion  ciclica  origen                                  archivo
  Idle_Loop                  2,50 s    si      UAL 1                                   animations/ual/sanador_ual1_seleccion.glb
  Idle_FoldArms-loop         2,50 s    si      UAL 2 (Idle_FoldArms_Loop)              animations/ual/sanador_ual2_seleccion.glb
  Walk_Loop                  1,33 s    si      UAL 1  (al reves a -0,6 = andar atras)  ual1
  Walk_Formal_Loop           1,33 s    si      UAL 1                                   ual1
  Jog_Fwd_Loop               0,93 s    si      UAL 1                                   ual1
  Sprint_Loop                0,67 s    si      UAL 1                                   ual1
  Sitting_Enter              1,30 s    no      UAL 1                                   ual1
  Sitting_Idle_Loop          1,67 s    si      UAL 1                                   ual1
  Sitting_Talking_Loop       2,93 s    si      UAL 1                                   ual1
  Sitting_Exit               1,03 s    no      UAL 1                                   ual1
  Hit_Chest                  0,33 s    no      UAL 1                                   ual1
  Hit_Head                   0,43 s    no      UAL 1                                   ual1
  Hit_Knockback              0,83 s    no      UAL 2                                   ual2
  Death_A                    2,40 s    no      UAL 1 (Death01)                         ual1
  Death_B                    2,40 s    no      UAL 1 Death01 en espejo + ajustes (Concordia)  ual1
  GetUp                      1,77 s    no      UAL 2 LayToIdle + 7 fotogramas desde Death_A   ual2
  GetUp_B                    1,77 s    no      UAL 2 LayToIdle + 7 fotogramas desde Death_B   ual2
  Spell_Simple_Enter         0,53 s    no      UAL 1                                   ual1
  Spell_Simple_Idle_Loop     2,07 s    si      UAL 1                                   ual1
  Spell_Simple_Shoot         0,50 s    no      UAL 1                                   ual1
  Spell_Simple_Exit          0,43 s    no      UAL 1                                   ual1
  Consume                    1,33 s    no      UAL 2 (raciones y pociones)             ual2
  Chest_Open                 1,37 s    no      UAL 2 (cofres, cajas de la boveda)      ual2
  Yes                        2,50 s    no      UAL 2 (emote)                           ual2
  Idle_No-loop               2,50 s    si      UAL 2 (Idle_No_Loop, emote)             ual2
  Heal_Cast_Single           0,90 s    no      hecha a mano (PJ4)                      export/godot/personajes/elfo_sanador_anims.glb
  Heal_Channel-loop          1,50 s    si      hecha a mano (PJ4)                      elfo_sanador_anims.glb
  Heal_Cast_Area             1,20 s    no      hecha a mano (PJ4)                      elfo_sanador_anims.glb
  Revive                     2,00 s    no      hecha a mano (PJ4)                      elfo_sanador_anims.glb
  Sin clip (en Godot): andar hacia atras (Walk_Loop a -0,6), de lado (BlendSpace2D + giro hacia el movimiento),
  girar en el sitio (giro por codigo sobre Idle_Loop). TODO_GODOT_personaje.txt, seccion PJ4b.
  UAL 1 y UAL 2: version Standard gratuita (CC0), ASSETS_LICENSES.md.
```


## Anexo F — README_personajes.txt

```text
README_personajes - Concordia
==============================

Normas comunes (PJ0)
--------------------
  - Pose T, de cara a -Y en Blender (+Z en Godot), metros, origen en el suelo entre los pies, transformaciones
    aplicadas. Un esqueleto para todas las razas con los nombres de SkeletonProfileHumanoid de Godot (lista
    verificada en docs/reference/godot_SkeletonProfileHumanoid.txt); el rig se hara en tools/blender/concordia_rig.py.
  - Modular: cuerpo en 6 piezas (Head, Torso, Arms, Hands, Legs, Feet) + Eyes; ropa y pelo en objetos aparte.
    Cada pieza (menos Head) lleva el grupo HIDE_<pieza> con todos sus vertices: la ropa que la cubre la oculta.
  - Presupuesto LOD0 <= 10.000 tris (cuerpo con cabeza <= 4.500, ropa <= 4.000, pelo <= 1.000, extras <= 500);
    LOD1 <= 5.000, LOD2 <= 1.800; texturas 1K (albedo, normal, ORM); <= 3 materiales.
  - Paleta: tierra apagada, saturacion <= 0,35 (salvo tono 185-215); #8FD0FF solo emisivo.

PJ1 - cuerpo base del elfo masculino (blender/elfo_v01.blend)
-------------------------------------------------------------
  Scripts: tools/blender/pj_mpfb.py (MPFB sin interfaz), build_pj1_elfo.py (-- medir cuerpo piel exportar),
  pj1_piel.py (horneado), capture_pj1.py (capturas). Informe: docs/reports/pj1_elfo_cuerpo.json y
  pj1_elfo_referencia.json. Export: export/godot/pj_elfo_cuerpo.glb (1177.4 KB).
  Base: MakeHuman (MPFB 2.0.18, assets CC0): malla base + proxy male1591 + ojos low-poly (ASSETS_LICENSES.md).

  Medidas (1,85 m):  cabeza 0.2252 m -> 8.21 cabezas; hombros (biacromial) 0.399 m;
    pierna (suelo-cadera) 1.0299 m, torso (cadera-base del cuello) 0.5533 m, pierna/torso 1.8615;
    cuello 0.1171 m.
  Frente a un humano de referencia (mismos macros, sin rasgos elficos, tambien a 1,85 m: 8.02 cabezas,
    hombros 0.4354 m): hombros -8.4 %, pierna/torso +6.0 %, cuello +16.8 %.
  Orejas: 13.5 cm de lobulo a punta, 28.0 grados hacia atras, 14.5 grados hacia fuera;
    el proxy traia 23 vertices por oreja: un nivel de subdivision (16 triangulos en la union), perfil de hoja
    afilado, concha hundida 3 mm con borde (helix) y la piel de alrededor acompana en dos anillos (sin pliegues).
  Triangulos: Head 1196, Torso 516, Arms 128, Hands 1068, Legs 224, Feet 196 = 3328 (<= 4.500);
    Eyes 172; total 3500. Caras: {'4': 1656, '3': 16} (sin n-gonos).
  Costuras sobre bucles reales de aristas (munecas, hombros, tobillos, muslos, base del cuello): todos los vertices
    de borde tienen pareja coincidente en la otra pieza; normales personalizadas del cuerpo entero (diferencia 0
    grados en las costuras). Los 42 bordes sin pareja son aberturas del propio proxy (ojos y boca).
  Materiales: MAT_Elfo_Piel (tono A 'abedul', asignado), MAT_Elfo_Piel_B (tono B 'corteza', usuario falso, mismo
    normal y ORM), MAT_Elfo_Ojos. Texturas en textures/personajes/elfo/ (fuera de git, copia en respaldo/).
  Piel: albedo = color por vertice en la malla de alta (zonas de rubor, labios, cejas pintadas, unas) x ruido
    suave; normal y AO de la malla de alta. En orejas y dedos de los pies el normal es plano (la malla de alta no
    coincide con el proxy en esas zonas; la forma la da la geometria). Saturacion maxima: A 0.255, B 0.348.

  Lecciones (MPFB sin interfaz)
    1. El rig 'default' solo se ajusta a la malla si se crea con detailed_helpers=True (grupos joint-*); sin ellos
       usa posiciones fijas y la pose T deforma los hombros.
    2. Fundir los targets (shape_key_remove apply_mix) ANTES del rig y aplicar el modificador Armature despues;
       modifier_apply_as_shapekey solo deforma la Basis.
    3. create_human(feet_on_ground=False): con True sube la malla pero no el rig.
    4. MPFB deja un hilo vivo: los scripts terminan con os._exit(0).

  Pendiente / limites conocidos
    - Rig (concordia_rig.py) y LOD1/LOD2: siguiente etapa.
    - Boca: el proxy trae la abertura de los labios (linea oscura); no hay dientes ni lengua (pedido).
    - Cejas solo pintadas; pelo en su etapa.

PJ2 - cabello y ropa inicial del Sanador (CLASE_SANADOR, provisional) (blender/elfo_v02.blend)
--------------------------------------------------------------------------------------------
  Scripts: tools/blender/pj2_geo.py (geometria), pj2_atlas.py (UV, atlas y material), build_pj2_sanador.py
  (orquesta; parte de elfo_v01.blend sin modificarlo), capture_pj2.py. Informe: docs/reports/pj2_sanador.json.
  Export: export/godot/pj_sanador_ropa.glb (ropa + pelo) y pj_elfo_sanador_equipado.glb (cuerpo con mascaras).
  Calidad normal: sin brillo ni piezas legendarias; todo modelado y pintado por script (ningun asset descargado).

  Piezas (coleccion CLASE_SANADOR; el pelo en PJ_CABELLO, comun al elfo) y triangulos:
    Robe_Top 646 (tunica: cuerpo desplazado 1,6 cm, cortado en la cintura y a media manga por bucles reales;
      mangas acampanadas con dobladillo vuelto; cordon y colgante de cristal #8FD0FF con emision 1,0)
    Robe_Skirt 832 (anillos sobre la seccion del cuerpo + holgura + vuelo; paneles delantero y trasero separados por
      aberturas laterales desde el dobladillo hasta z 0,66; dobladillo vuelto de 3,5 cm)
    Hood 640 (esclavina de lana que marcha sobre la tunica desde el cuello + capucha bajada como cuello vuelto que en
      la espalda se hace bolsa)
    Belt_Pouches 676 (cinturon de seccion rectangular, hebilla de hierro y punta; 3 bolsitas con solapa; 2 frascos
      de vidrio con tintura y tapon)
    Boots 324 (pie y pierna baja desplazados y suavizados, suela en z = 0, vuelta en la cana a z 0,40)
    Bracers 160 (vendas del antebrazo de 0,525 a 0,728)
    Ropa: 3.278 (<= 4.000). Hair_Elf 472 (<= 1.000): casquete sobre el cuero cabelludo sin tocar las orejas,
      20 mechones (cards) peinados hacia atras y trenza de 0,51 m con atadura y punta.
  Atlas 1K (textures/personajes/sanador/, fuera de git): albedo RGBA (alfa recortada, solo en el pelo), normal
    (OpenGL), ORM (R AO por vertice, G rugosidad, B metal) y emision (solo los 82 texeles del cristal). Un material:
    MAT_Sanador_Atlas (doble cara, alphaMode MASK en el glb). Densidad 360 texeles/m (pelo 648); ocupacion 47 %.
    Patrones por atributos de la malla (pu, pv: metros desde la orilla), no por el UV: 12 remiendos cosidos, bordado
    de hojas en el dobladillo, las mangas y el borde de la esclavina. Saturacion maxima 0,30 (sin el cristal).
  Ocultar el cuerpo: grupos finos en las piezas del cuerpo (HIDE_Torso_Sup / _Inf, HIDE_Arms_Sup / _Inf,
    HIDE_Legs_Sup / _Inf, HIDE_Feet). Cada prenda lleva la propiedad 'oculta' con los grupos que tapa; en el cuerpo
    hay un modificador Mask (invertido) por grupo con driver '1 - oculta' de la prenda: al ocultar la prenda vuelve
    la piel. Los limites van entre anillos del proxy (el Mask quita toda cara que toque un vertice oculto).
    Hood, Belt_Pouches y Hair_Elf no ocultan nada (van sobre otras prendas; el casquete flota sobre el cuero
    cabelludo).
  Pendiente / limites conocidos
    - Pelo de cerca: el casquete tiene ruido de textura y el flequillo recortado se ve dentado; a la distancia de la
      camara iso se lee bien. Se puede mejorar con mas mechones (quedan ~500 tris de presupuesto).
    - El bordado de la esclavina se ve pixelado de cerca (360 texeles/m).
    - La capucha bajada se lee como cuello vuelto alto en la espalda, no como bolsa grande.
    - En Godot hace falta un mecanismo para los HIDE_* (ver TODO_GODOT.txt).

PJ3 - esqueleto (rig) del elfo (blender/elfo_v03.blend)
-----------------------------------------------------
  Scripts: tools/blender/concordia_rig.py (esqueleto comun de todas las razas y pesos), build_pj3_rig.py (elfo,
  poses de prueba, export), capture_pj3.py. Informe: docs/reports/pj3_rig.json (lista de huesos con padre y si
  deforma). Articulaciones: docs/reports/pj1_elfo_articulaciones.json (rig 'default' de MPFB ajustado al elfo).
  Godot: TODO_GODOT_personaje.txt. Export: export/godot/pj_elfo_rig.glb.
  Huesos: 70 (56 del SkeletonProfileHumanoid de Godot 4.7, verificado en la documentacion oficial y
    en scene/resources/skeleton_profile.cpp; 14 extra sin mapear). Deformacion: 65 (<= 65): no
    deforman Root, Weapon_R, Weapon_L, Back_Slot y Head_Top. Jaw deforma pero no tiene pesos (boca sin rig).
    Extra: Head_Top, Hair_01, Hair_02, Hair_03, Hair_04, Weapon_L, Weapon_R, Back_Slot, Skirt_Front_01, Skirt_Front_02, Skirt_Front_03, Skirt_Back_01, Skirt_Back_02, Skirt_Back_03.
  Convencion: cola de cada hueso = cabeza del hijo (+Y hacia el hijo; desviacion max 0.7806 grados en
    47 pares), pose T, de cara a -Y, objeto del armature sin transformacion; roll con Z hacia delante.
  Pesos: cuerpo con pesos automaticos de Blender (calor de huesos) sobre el cuerpo unido (las costuras reciben
    los mismos pesos en las dos piezas), limpieza por script: transicion suave a lo largo del eje en codos,
    munecas, rodillas y tobillos; suavizado por vecinos en hombros (r 15 cm) y cadera (r 17 cm); max. 4
    influencias, normalizado. 4130 vertices, 0 sin peso, max 4 influencias.
    Ropa: transferencia desde el cuerpo (tunica, esclavina, botas, vendas); cinturon a Hips (+ muslo en las
    bolsitas); falda solo a muslos (tercio superior) y cadenas Skirt_*; pelo a Head y trenza a Hair_01..04; ojos
    rigidos a LeftEye / RightEye.
  Poses de prueba (acciones POSE_*): T, A, caminar (contacto), correr, sentado, hechizo (brazos arriba, con
    clavicula), de rodillas, agachado, golpe recibido, caido. Falda dentro de piernas o botas (medido):
      01_T: 0 vertices, max 0.0 cm
      02_A: 0 vertices, max 0.0 cm
      03_Caminar: 2 vertices, max 2.5 cm
      04_Correr: 15 vertices, max 2.7 cm
      05_Sentado: 12 vertices, max 2.8 cm
      06_Hechizo: 0 vertices, max 0.0 cm
      07_Rodillas: 13 vertices, max 2.9 cm
      08_Agachado: 7 vertices, max 2.5 cm
      09_Golpe: 2 vertices, max 2.6 cm
      10_Caido: 1 vertices, max 1.9 cm
  Correcciones hechas tras revisar las capturas: falda que se hinchaba en reposo (las cadenas ya no se tocan si
    las piernas no salen del vuelo), rodillas que atravesaban la falda al sentarse / arrodillarse / agacharse
    (cadena tendida por delante de rodilla y tobillo), pliegue duro en el hombro al levantar los brazos (clavicula
    en la pose + suavizado mas amplio), cadera (suavizado mas amplio).
  Limites conocidos: perdida de volumen en rodillas y codos por encima de ~120 grados (piel lineal en malla
    low-poly; correctivos o mas aristas en otra etapa); la falda de "caido" se abre (en Godot la gravedad del
    SpringBoneSimulator3D la dejara caer); la pierna asoma por la abertura lateral en zancadas largas (diseno).


PJ4 - animaciones (blender/elfo_v04.blend)
------------------------------------------
  Scripts: tools/blender/pj4_compare_rest.py (reposo UAL frente al elfo), build_pj4_anim.py (animaciones propias,
  export), capture_pj4.py (capturas). Informe: docs/reports/pj4_anim.json y pj4_reposo_ual.json.
  Godot: TODO_GODOT_personaje.txt (seccion PJ4) y godot_concordia/tools/make_bonemaps.gd (BoneMap .tres).
  UAL 1 y UAL 2 Standard de Quaternius (CC0, ASSETS_LICENSES.md): no se retargetean en Blender; las dos ya estan en
  pose T y miran a -Y como el elfo; Godot las retargetea con BoneMap + SkeletonProfileHumanoid.
  Propias del Sanador (30 fps, sin movimiento de raiz, Action con fake user y rango manual desde el fotograma 1):
    Heal_Cast_Single   1-28  0,90 s  baston al frente con el brazo derecho, pulso (f14-19) y vuelta
    Heal_Channel-loop  1-46  1,50 s  brazos abiertos, palmas arriba, balanceo lateral; f46 = f1 (bucle)
    Heal_Cast_Area     1-37  1,20 s  brazos y baston arriba (f11-16), onda hacia abajo con rodillas flexionadas (f24)
    Revive             1-61  2,00 s  se arrodilla (f28) y apoya la mano izquierda en el objetivo (f42-61)
  Capturas: docs/captures/pj4_animaciones.png (3 fotogramas clave por animacion, camara isometrica de lado-frente,
  baston temporal solo para la captura) y pj4_<animacion>.png. Export: export/godot/pj_elfo_sanador_anim.glb.

PJ5 - LODs, exportacion y cierre (blender/concordia_personajes_master.blend, version 1.0)
-----------------------------------------------------------------------------------------
  Scripts: tools/blender/build_pj5_lods_export.py (LOD1, LOD2, export), capture_pj5.py (capturas). Informe:
  docs/reports/pj5_lods.json. Documento de cierre: README_personaje.txt (huesos, HIDE_*, nombres, presupuesto).
  LOD0 7250 / LOD1 4848 / LOD2 1757 tris. Export: export/godot/personajes/ (9 .glb, mismo esqueleto).
  Respaldo: respaldo/2026-11-11/personajes_pj5/ con MANIFEST (sha256). Captura: docs/captures/pj5_lods.png.

PJ4b - decisiones de animacion (tras PJ4)
-----------------------------------------
  tools/blender/build_pj4b_ual_seleccion.py -> animations/ual/sanador_ual1_seleccion.glb y sanador_ual2_seleccion.glb
  (seleccion con nombres finales sobre los esqueletos originales de la UAL), docs/reports/pj4b_ual_seleccion.json,
  docs/captures/pj4b_muertes_getup.png. Death_B = espejo de Death01 (matriz del hueso simetrico reflejada en X y
  corregida por el reposo) con otro giro de cabeza y otros brazos a partir del 30 %; GetUp / GetUp_B = LayToIdle con
  7 fotogramas de transicion desde el final de Death_A / Death_B (sin ella: cadera 0,31 m atras, media 46 cm).
  Andar atras, de lado y girar en el sitio: en Godot (TODO_GODOT_personaje.txt PJ4b). Lista final: README_personaje.txt.
```


## Anexo G — TODO_GODOT.txt

```text
CONCORDIA - TODO en Godot 4 (lo que el glTF no guarda)
======================================================
Se actualiza en cada etapa. Ultima: etapa 27. [ ] = pendiente en Godot; (E#) = etapa en que aparece.

Importacion general
[ ] (E11) Los .glb usan texturas EXTERNAS con ruta relativa "../../textures/concordia/...": copiar la carpeta textures/
    con la misma estructura junto a export/ en el proyecto de Godot, o reimportar con las texturas embebidas.
[ ] (E11) Importar las texturas como "VRAM Compressed" (albedo/ORM/emision BC1, normales BC5) para quedarse en
    ~155 MB (limite acordado 220 MB).
[ ] (E11) Sufijos de importacion: "-colonly" -> StaticBody3D solo colision; "-navmesh" -> malla de navegacion;
    "-occonly" -> OccluderInstance3D. Comprobar que el importador los aplica (Advanced Import Settings).
[ ] (E11) COLOR_0 = mask_pack (mascaras del terreno, ver README_masks.txt): shader del terreno que lo lea.
[ ] (E11/E13-16) LODs manuales (_LOD1 / _LOD2): asignar visibility_range_begin/end en cada MeshInstance3D (o un HLOD)
    y desactivar el LOD automatico del importador en esas mallas para no duplicar.
[ ] (E17) Todos los materiales salen con doubleSided = true (en Blender esta desactivado el backface culling). Para
    los opacos poner cull_mode = BACK (ahorra relleno); dejar dos caras solo en velo, haz, vidrios y telas. Hacerlo en
    Godot o pedir que se active el culling en Blender antes del export.
[ ] (E13-17) Emision: activar Glow en el WorldEnvironment (HDR threshold ~1.0) para que #8FD0FF brille. Comprobar que
    el importador lee KHR_materials_emissive_strength (fuerza > 1.0: cristal 4.0, velo 3.0, marcas 3.0...).
[ ] (E25) MAT_Embers (#E09A62, 1.5) es la UNICA emision calida: no subir su fuerza en Godot por encima de 1.5 ni
    mezclarla con luces azules; su OmniLight3D (si se pone) naranja tenue y solo en Gran Forja y Hornos.
[ ] (E13-17) Materiales con alpha (BLEND): MAT_Portal_Veil 0.6, MAT_Faro_Beam 0.3, MAT_Pipe_Glass 0.35 -> revisar
    render_priority / orden de transparencias y desactivar sombras en el velo y el haz.

Portal (E13, E17)
[ ] PORTAL_Veil: animar el velo como agua (desplazamiento de UV: u = 0..1 a lo ancho, v = z / 11 m) + brillo;
    sin colision (propiedad no_collision). Tamano en la etapa 17: 7.8 x 11 m.
[ ] Runas del Atrio y lineas de los pilares (MAT_Rune_Glow_10/12): pulso opcional.

Obelisco (E14)
[ ] OBELISK_Mark_001..100: al alcanzar un piso, cambiar la superficie 0 de la marca a MAT_Obelisk_Mark_Lit
    (material_override o set_surface_override_material). El .blend y el .glb las dejan todas apagadas.
[ ] OBELISK_Mark_LitMaterialRef: pieza oculta dentro del pedestal solo para que el .glb incluya MAT_Obelisk_Mark_Lit;
    ocultarla o borrarla al importar (guardar antes el material).

Faro (E15, E17)
[ ] FARO_Beam: material con blend_mode = ADD, unshaded, sin sombras, cull desactivado; animar el desplazamiento de
    UV en v (0..1 a lo largo de los 80 m) y/o un giro lento. Sin colision.
[ ] FARO_Crystal: emision 4.0 (Glow). Opcional: OmniLight3D azul palido en el cristal.
[ ] Rampa decorativa: no incluir FARO_Body en la NavigationRegion3D (raiz FARO: navigation = false). La colision de
    la rampa es solo el arranque por debajo de 3 m (FARO_Ramp-colonly).
[ ] Canales de luz (torre -> plaza): opcional, un pulso que baje del cristal por los 4 canales y siga por los canales
    de la plaza (TRN_LightCanals) hacia el Portal.
[x] (E26) Tubos de luz colocados en Blender: PIPES_Tesoreria_Faro (bld_portal.glb), instancias de 4 mallas
    (recto estirado, codo 90, codo 45, soporte). Primer punto en la salida real de la Tesoreria.
[ ] (E26) MAT_Pipe_Light_Core 1.5: pulso opcional que baje de la Tesoreria al Faro (desplazamiento de UV en el
    nucleo). Los tubos no tienen LOD: visibility_range_end ~250 m en sus MeshInstance3D.
[ ] (E26) Los 14 soportes (PIPE_TF_Support_NN, 0.6 x 0.4 m) estan sobre calle y plaza: NavigationObstacle3D o
    recortar la malla de navegacion alrededor de cada pie.

Santuario y Salon de las Hazanas (E16)
[ ] MARKER_Santuario_Door / MARKER_SalonHazanas_Door + *_InteriorVolume: disparador de puerta -> escena interior.
[x] SANTUARIO_Well: colocado en el interior (int_santuario.glb, etapa 29, sin provisional). La copia del exterior
    (concordia_v28) sigue dentro del edificio cerrado: quitarla en la proxima version del master.
[ ] Salon: desde CAM_Iso tapa ~241 m2 de plaza delante de su fachada (hasta 20.9 m): fundido/dither o corte del
    tejado cuando el jugador quede detras (decision pendiente).
[ ] Farolillos de esquirla (LANTERN_Shard): OmniLight3D pequena azul palido opcional.
[ ] Vitrales (MAT_Stained_Glass_Blue, emision 0.6) y MAT_Window_Warm (1.0): subir o bajar con el ciclo dia/noche.

Cauce y molino (E07)
[ ] MARKER_Cauce_WaterWheel: rueda hidraulica (aun sin modelo) con animacion de giro.
[ ] MAT_Water del cauce: desplazamiento de UV en el sentido de la corriente (MARKER_Cauce_Source -> _Outlet).

Kit de edificios (E12, E17)
[ ] Regla de alturas aplicada en Blender (fit_iso_height). En Godot, carriles de NPC: si se crean, exportarlos
    tambien como curvas NPC_Lane_* para poder repetir la prueba en Blender.

Mercado (E18)
[ ] Posada_TablonGrupos: interactive = true -> Area3D + UI del tablon de grupos.
[ ] Letrero de la Posada: la llama de la vela (MAT_Window_Warm, 1.0) con parpadeo suave y OmniLight3D calida pequena.
[ ] Chimenea de la Posada: particulas de humo.
[ ] Gran Subasta: la campana (GranSubasta_Body, malla de la tarima) -> si debe sonar/moverse, separarla como nodo
    propio; los 6 tableros de precios admiten texto dinamico (Label3D delante de cada tablero).
[ ] Tesoreria: manecillas del reloj (parte de TesoreriaMuralla_Body; si se quieren animar, separarlas); bocas de los
    tubos (MAT_Pipe_Light_Core 1.5) y Path3D de la curva hacia el Faro.
[ ] Fuente del Mercado: agua de la pila y chorros (MAT_Water) con desplazamiento de UV o shader; el rebosadero corre
    hacia CAU_SpringHead (sentido: de la fuente al manantial).
[ ] Puestos (PuestoProvisiones_01..14): comparten 5 mallas (STALL_A..E) -> se pueden pasar a MultiMeshInstance3D.
    Toldos: balanceo leve opcional.
[ ] LOD2 de Santuario, Salon, Faro, Tesoreria y Gran Subasta: un solo objeto *_Body_LOD2 que sustituye a cuerpo + cubierta.

Oficios (E19)
[ ] Taller_Carpinteria_WATERWHEEL: giro continuo sobre su eje Y local (eje hacia la Carpinteria), ~6 rpm; el agua
    del Cauce en la rueda puede llevar salpicaduras (particulas). Sustituye a MARKER_Cauce_WaterWheel.
[ ] Gran Forja: vapor en MARKER_GranForja_Steam (abrevadero de temple); brasas (MAT_Embers 1.5) con parpadeo y
    OmniLight3D naranja; chispas opcionales sobre los yunques.
[ ] Alquimia: humo de color en MARKER_Alquimia_Smoke_01/02 (bocas de las chimeneas).
[ ] Crisol de las Piedras: CRISOL_FloatStone_01..07 flotan y giran sobre el cuenco; el haz del oculo
    (MAT_Faro_Beam dentro de CrisolPiedras_Body) en blend_mode ADD como el del Faro; el cuenco (MAT_Embers) con
    ondulacion. Etapa 25: el cuenco usa MAT_Crisol_Molten (#8FD0FF 1.2), ya no MAT_Embers.
[ ] Hornos: humo en la chimenea y brasas en la boca del horno.
[ ] Pescadores: las barcas (Gremio_Pescadores_Prop_Boat_01/02) con balanceo leve en el agua.
[ ] (E25) Gremio de Cazadores: ya en bld_oficios.glb (casa en MARKER_Bld_Gremio_Cazadores). El campo de tiro
    (Gremio_Cazadores_Range, MARKER_Cazadores_Range) esta a 84 m, junto a la muralla: si hace falta, un indicador
    de camino o una NPC que lleve de la casa al campo. Dianas Gremio_Cazadores_Prop_Target_01..04: Area3D de
    impacto opcional. Borrar concordia_gremio_cazadores_sin_parcela.glb del proyecto si ya se importo.
    (E26) Resuelto: entrada norte con portillo, camino de adoquin de 2 m hasta la calle y campo + camino dentro de
    TRN_NavMesh_Oficios (concordia_terrain_oficios.glb), conectados a la red de calles.

Clases (E20)
[ ] Estandartes (SalonClase_NN_Banner_*): cambiar la textura por clase (material_override con el emblema definitivo,
    UV 0..1); ondulacion leve con un shader de vertices (viento).
[ ] MARKER_ClassProp_Slot_<salon>_<slot>: instanciar ahi los objetos de clase (el slot 03 esta libre).
[ ] DUMMY_Straw_NN: estaticos; MARKER_DamageNumber_NN es el punto de los numeros de dano (Label3D / particulas).

Razas (E21)
[ ] Estandartes y banderas (CasaRaza_NN_Banner / _Flag): textura por raza (MAT_Banner_RNN, UV 0..1; la bandera usa un
    recorte del simbolo); ondulacion por viento con shader de vertices; la bandera mira hacia CAM_Iso.
[ ] MARKER_RaceSpawn_NN: punto de aparicion de cada raza (delante de la puerta de su Casa, +Y hacia fuera).
[ ] MAT_Glass_R04: alpha 0.35 BLEND con emision 0.25; en Godot, transparencia con depth draw "opaque only" para que
    las laminas delante de las ventanas no parpadeen con el cristal calido de detras.
[ ] Yurtas (CasaRaza_05): humo suave en la chimenea de la corona.
[ ] Plazuelas: agua de las fuentes (MAT_Water) con desplazamiento de UV; arboles viejos con balanceo leve de las copas.

Conexiones (E22)
[ ] Reimportar concordia_terrain_<distrito>.glb y concordia_markers.glb (ya sin puentes, arcos ni escaleras
    provisionales) y anadir concordia_conexiones.glb: cada pieza cuelga de su MARKER_* (+Y = sentido de paso).
[ ] Colisiones: las "-colonly" de puentes y escaleras son rampas continuas (no peldanos): StaticBody3D con la forma
    concava; el CharacterBody3D sube sin "step offset". Pie de algunas escaleras laterales: hasta 14 cm de escalon.
[ ] Navmesh: el horneado de la etapa 11 se hizo con los provisionales (mismos perfiles); rehornear con las piezas
    nuevas cuando se reimporten (los pasos altos de los arcos no tienen acceso: no son transitables).
[ ] Linternas de esquirla de los arcos (MAT_Shard_Blue, 2.5): OmniLight3D azul palido pequena opcional.
[ ] RAIL_Stone_3m de los arcos: instancias escaladas en Y (0.85-0.86); se pueden pasar a MultiMeshInstance3D.

Moradas (E23)
[ ] Importar moradas_NE / _NO / _SO / _SE.glb (una escena por conjunto; 63 mallas compartidas entre las 283 casas):
    pasar Body/Roof/LOD a MultiMeshInstance3D o dejar las instancias (mismas mallas).
[ ] DOOR_Morada: material_override de la ranura de pintura por instancia (prop paint_material); Decal o Label3D con el
    house_number sobre PLATE_Morada_*; MARKER_Lantern_*: farol LANTERN_Shard opcional (solo planta baja trae el
    modelo) y OmniLight3D pequena si se quiere de noche.
[ ] MARKER_Morada_Door_*: zona de interaccion que carga el interior propio de cada vivienda; MARKER_TrophyCase_*: punto
    de la vitrina dentro del interior.
[ ] Escaleras exteriores y galerias de las casas comunales: la -colonly incluye rampa y pasarelas (las puertas de
    las plantas 2 y 3 son accesibles desde la calle).

Version final (E24)
[ ] Importar bld_portal / bld_mercado / bld_oficios / bld_clases / bld_razas / bld_moradas_NE,NO,SE,SO / bld_kit /
    bld_props.glb (sustituyen a concordia_<distrito>.glb, moradas_*.glb y concordia_conexiones.glb, ya borrados).
[ ] Reimportar concordia_terrain_<distrito>.glb: la malla de navegacion ya no pasa por debajo del Obelisco, el Faro,
    el Santuario, el Salon de las Hazanas ni el Crisol (1,047 m2 recortados).
[ ] NAVLINK_<puerta>_Start / _End (12 puertas tras porticos o patios: Salones de clase, Tesoreria, Herbolarios,
    Curtiduria, Alquimia): crear un NavigationLink3D por pareja.
[ ] <N>_Roof: ocultar al entrar en <N>_InteriorVolume; LOD con visibility_range (LOD0 / LOD1 / LOD2).
[ ] Animables: ver README_buildings.txt seccion 14.

Decisiones de la etapa 25 (E12)
[ ] Reimportar bld_oficios.glb (Cazadores, cuenco del Crisol), bld_razas.glb (casas nuevas RAZ_B01_Casa_06,
    RAZ_B04_Casa_06, RAZ_B05_Casa_01 y casas rebajadas por el Faro), bld_moradas_NO / _SE.glb (5 habitaciones a 2
    plantas) y concordia_markers.glb.
[ ] NAVLINK_RAZ_B05_Casa_01_Door_Start/_End: la puerta de la yurta nueva queda fuera de la malla (2.87 m):
    NavigationLink3D como las otras 12.
[ ] Faro: la visibilidad desde las calles sigue por debajo del criterio (avenidas 78.3 %, anillos 57.8 %,
    diagonales 38.8 %, callejones 47.8 %). Si no se decide bajar edificios de servicio, alternativa en Godot: el
    cristal y el haz del Faro sin depth test o un icono de brujula/HUD que apunte al Faro (decision pendiente).

Decisiones de la etapa 26 (E13)
[ ] Faro (criterio nuevo): FARO_Crystal y FARO_Beam se dibujan SIN depth test (no_depth_test = true y
    render_priority alto) o con un pase de silueta por encima de los edificios; indicador en pantalla (brujula) que
    apunta al Faro cuando queda fuera de la vista. Los hitos (Obelisco, Salon, Santuario) y las puertas de la muralla
    no se tocan en Blender.
[ ] Salon de las Hazanas: SALON_HAZANAS_Body y _Roof traen occludes_iso = true (metadatos glTF): cuando el jugador
    quede detras desde CAM_Iso, fundido por dithering (StandardMaterial3D distance_fade_mode = PIXEL_DITHER u
    OBJECT_DITHER, o shader con alpha hash). Sus materiales son opacos y compatibles.
[x] SANTUARIO_Well: definitivo en el interior (etapa 29); ver arriba la copia del exterior.
[ ] Moradas NE y SO: balcon por puerta. Desde la escalera exterior se llega a 2 balcones por casa comunal (puerta
    central de la planta 2 y la del extremo de la planta 3); las demas puertas altas son puertas-balcon: su
    MARKER_Morada_Door es zona de interaccion (Area3D) que se activa desde la calle o el interior.
[ ] NAVLINK_RAZ_B05_Casa_01/02/03/05_Door_Start/_End (yurtas pequenas): NavigationLink3D como los otros 12.
[ ] Reimportar: bld_portal (tubos), bld_oficios (campo de tiro), bld_razas (casas nuevas y adosadas, B02_Casa_04 a
    1 planta), bld_moradas_NE / _SO (balcones), concordia_terrain_oficios (malla de navegacion) y concordia_markers.

Interiores (E27; piloto int_banco.glb)
[ ] Cargar int_<nombre>.glb como escena aparte al usar MARKER_<Nombre>_Door: el jugador aparece en
    MARKER_Interior_Spawn (+Y hacia dentro); MARKER_Interior_Exit (+Y hacia la calle) devuelve a la ciudad.
    La raiz INT_<nombre> ya trae el giro del edificio: CAM_Iso es la misma que fuera.
[ ] Ocultar siempre WALL_Near_A, WALL_Near_B y CEILING con el jugador dentro (o fundido por dithering).
    Convencion general (README seccion 18): LEVEL_n, WALL_Near_<Recinto>, CEILING_<Recinto>; cada grupo trae
    la propiedad hide_when con la regla.
    WALL_Near_Vault y CEILING_Vault: ocultarlos con un Area3D en el suelo de la boveda. LEVEL_1 (planta alta):
    ocultarla con el jugador en la planta baja si tapa (corte isometrico); mostrarla al subir.
[ ] Luces: OmniLight3D por cada Empty de Lights (light_color, light_energy, light_range); hornear LightmapGI
    (importar con 'Light Baking: Static Lightmaps' para generar UV2). Llamas: particulas sobre las caras de
    MAT_Window_Warm; el farol de la boveda es la unica luz azul.
[ ] Cajas de deposito: BANK_Box_NNN (box_number, state). Cambiar la malla de _Body entre BANK_Box_Open y
    BANK_Box_Locked; la placa (_Plate) usa MAT_Bank_BoxNumbers: sustituir por un ShaderMaterial con
    'instance uniform float locked' que suma 0.5 a v (mitad oscura del atlas). Opcional: MultiMeshInstance3D.
    El .glb trae 1-40 abiertas solo como ESTADO DE MUESTRA: Godot decide por jugador (datos del servidor) que cajas
    pasan de BANK_Box_Locked a BANK_Box_Open y viceversa; no hay que respetar el reparto exportado.
[ ] VAULT_Door: AnimatableBody3D con giro sobre el pernio (hinge_local) y su propia colision (la -colonly deja
    el hueco libre); se abre con MARKER_Interact_Vault.
[ ] MARKER_NPC_Slot_01 (npc=Banquero, de pie tras el tablero) y MARKER_Interact_Bank_Counter (abre la interfaz
    del banco, delante de la ventanilla de cajero INT_Grille_Teller de 1.2 m): Area3D.
[ ] INT_Banco-navmesh -> NavigationRegion3D (rejilla de 0.25 m, ya conectada por la escalera).

Faro (E28, punto 10): puntos de calle SIN vista del Faro (ojo a 1.7 m, criterio de la etapa 26: 11 rayos, >= 1 libre)
[ ] Aceptado por el usuario: lo resuelve Godot dibujando el cristal y el haz por encima de los edificios (depth test
    off o pase de silueta) y con la brujula en pantalla. MER_Casa_01 ya bajo de 3 a 2 plantas (14.0 -> 10.8 m).
    Visibilidad tras la etapa 28: avenida 55/60 (91.7 %), anillo 59/83 (71.1 %), callejon 120/157 (76.4 %), diagonal 39/49 (79.6 %).
    Lista (calle | x, y, z del ojo | lo que tapa):
    avenida   STR_OFI_Avenue                  89.4     0.0   6.4  MARKER_Bridge_02, Taller_Carpinteria
    avenida   STR_OFI_GateApproach           196.0     0.0   7.7  GATE_Slot00_Sealed_Twin
    avenida   STR_MER_GateApproach             0.0   196.0   7.7  GATE_Slot12_Sealed_Twin
    avenida   STR_CLA_GateApproach          -196.0     0.0   7.7  GATE_Slot24_Sealed_Twin
    avenida   STR_RAZ_GateApproach            -0.0  -196.0   7.7  GATE_Slot36_Sealed_Twin
    anillo    STR_OFI_Ring150                145.4   -40.1   5.5  Gremio_Mineros, MARKER_Bridge_04
    anillo    STR_OFI_Ring150                147.6   -30.3   6.5  Gremio_Mineros
    anillo    STR_OFI_Ring150                149.0   -20.4   6.5  Gremio_Mineros
    anillo    STR_MER_Ring150                -41.3   144.4   6.5  TesoreriaMuralla
    anillo    STR_CLA_Ring100                -97.3    27.6   7.5  SalonClase_08
    anillo    STR_CLA_Ring100                -99.1    17.8   7.5  SalonClase_08
    anillo    STR_CLA_Ring100                -96.8   -22.0   7.6  CLA_Casa_01, SalonClase_07
    anillo    STR_CLA_Ring100                -93.9   -31.6   7.6  SalonClase_07
    anillo    STR_CLA_Ring150               -141.6    49.3   6.5  CasaReposicion
    anillo    STR_CLA_Ring150               -144.9    39.8   6.5  CasaReposicion
    anillo    STR_CLA_Ring150               -147.7    30.2   6.5  CasaReposicion, SalonClase_02
    anillo    STR_CLA_Ring150               -144.2   -38.9   6.5  CLA_Casa_03, SalonClase_01
    anillo    STR_CLA_Ring150               -141.5   -48.5   6.5  CLA_Casa_04, SalonClase_01
    anillo    STR_RAZ_Ring100                -36.3   -92.1   7.6  CasaRaza_06, RAZ_B06_Casa_01, RAZ_B06_Casa_02
    anillo    STR_RAZ_Ring100                -27.0   -95.9   7.6  CasaRaza_06, Plazuela_06
    anillo    STR_RAZ_Ring150                -58.5  -137.7   6.5  RAZ_B02_Casa_01, RAZ_B02_Casa_03
    anillo    STR_RAZ_Ring150                -49.1  -141.3   6.5  CasaRaza_02, RAZ_B02_Casa_01
    anillo    STR_RAZ_Ring150                -39.6  -144.4   6.5  CasaRaza_02
    anillo    STR_RAZ_Ring150                -29.9  -146.7   6.5  MARKER_Bridge_07, RAZ_B02_Casa_04, RAZ_B02_Casa_05
    anillo    STR_RAZ_Ring150                -20.0  -148.1   6.5  RAZ_B02_Casa_06
    anillo    STR_RAZ_Ring150                 19.9  -148.7   6.5  CasaRaza_01, RAZ_B01_Casa_03, RAZ_B01_Casa_05
    anillo    STR_RAZ_Ring150                 29.8  -147.6   6.5  CasaRaza_01, SALON_HAZANAS
    anillo    STR_RAZ_Ring150                 39.6  -145.7   6.5  CasaRaza_01
    anillo    STR_RAZ_Ring150                 49.2  -142.8   6.5  RAZ_B01_Casa_04, SALON_HAZANAS
    callejon  STR_OFI_CallejonRonda_L        181.1    41.5   7.0  OFI_Casa_01
    callejon  STR_OFI_CallejonRonda_L        178.9    51.2   7.0  OFI_Casa_02
    callejon  STR_OFI_CallejonRonda_L        176.0    60.8   7.0  OFI_Casa_02
    callejon  STR_OFI_CallejonRonda_R        171.9   -70.0   7.0  Taller_Curtiduria, Taller_Sastreria
    callejon  STR_MER_CallejonRonda_L        -31.7   183.3   7.0  MER_Casa_02
    callejon  STR_MER_CallejonRonda_L        -41.5   181.5   7.0  MER_Casa_02, MER_Casa_03
    callejon  STR_MER_CallejonRonda_L        -51.2   179.1   7.0  MER_Casa_03
    callejon  STR_MER_CallejonRonda_L        -70.2   172.9   7.1  MER_Casa_08, TesoreriaMuralla
    callejon  STR_MER_CallejonRonda_R         21.8   184.6   7.1  GranSubasta, MER_Casa_04
    callejon  STR_MER_CallejonRonda_R         31.6   183.0   7.0  GranSubasta, MER_Casa_05
    callejon  STR_MER_CallejonRonda_R         41.4   180.7   7.0  GranSubasta, MER_Casa_06
    callejon  STR_MER_CallejonRonda_R         51.0   178.0   7.0  GranSubasta, MER_Casa_07
    callejon  STR_MER_CallejonRonda_R         60.6   175.1   7.0  GranSubasta, MER_Casa_07
    callejon  STR_CLA_CallejonRonda_L       -183.9   -31.7   7.1  CLA_Casa_05
    callejon  STR_CLA_CallejonRonda_L       -181.8   -41.5   7.0  CLA_Casa_06, SalonClase_03
    callejon  STR_CLA_CallejonRonda_L       -179.1   -51.1   7.0  CLA_Casa_07, SalonClase_03
    callejon  STR_CLA_CallejonRonda_L       -172.7   -70.1   7.0  CLA_Casa_04, CLA_Casa_12, SalonClase_05
    callejon  STR_CLA_CallejonRonda_R       -183.9    31.7   7.1  CLA_Casa_08, CasaReposicion, SalonClase_04
    callejon  STR_CLA_CallejonRonda_R       -182.0    41.5   7.1  CLA_Casa_09, CasaReposicion, SalonClase_04
    callejon  STR_CLA_CallejonRonda_R       -179.3    51.2   7.0  CLA_Casa_10, CasaReposicion, SalonClase_06
    callejon  STR_RAZ_CallejonRonda_L         21.8  -185.3   7.1  CasaRaza_01, RAZ_B01_Casa_03, RAZ_B03_Casa_01, RAZ_B03_Casa_04
    callejon  STR_RAZ_CallejonRonda_L         31.7  -184.0   7.1  CasaRaza_01, RAZ_B03_Casa_02, RAZ_B03_Casa_05
    callejon  STR_RAZ_CallejonRonda_L         41.5  -181.9   7.1  CasaRaza_01, CasaRaza_03, Plazuela_03, RAZ_B01_Casa_04
    callejon  STR_RAZ_CallejonRonda_L         51.1  -179.2   7.0  CasaRaza_03, RAZ_B01_Casa_04, RAZ_B03_Casa_03
    callejon  STR_RAZ_CallejonRonda_L         60.6  -176.0   7.0  RAZ_B03_Casa_03, RAZ_B03_Casa_06
    callejon  STR_RAZ_CallejonRonda_L         70.0  -172.5   7.0  Morada_SE_028, RAZ_B03_Casa_06
    callejon  STR_RAZ_CallejonRonda_R        -21.7  -183.6   7.0  RAZ_B04_Casa_03
    callejon  STR_RAZ_CallejonRonda_R        -41.4  -180.7   7.0  CasaRaza_04, MARKER_Bridge_07, RAZ_B04_Casa_02
    callejon  STR_RAZ_CallejonRonda_R        -51.2  -178.7   7.0  CasaRaza_02, CasaRaza_04, Plazuela_04
    callejon  STR_RAZ_CallejonRonda_R        -60.8  -175.9   7.0  CasaRaza_02, RAZ_B04_Casa_04
    callejon  STR_MER_CallejonEscalera_10    -39.7   136.5   6.7  TesoreriaMuralla
    callejon  STR_MER_CallejonEscalera_12    -66.9   170.4   6.9  MER_Casa_08, TesoreriaMuralla
    callejon  STR_CLA_CallejonEscalera_15   -170.4    66.9   6.9  CLA_Casa_11, Morada_NO_028
    callejon  STR_CLA_CallejonEscalera_19   -169.0   -65.4   6.7  CLA_Casa_04, CLA_Casa_12, SalonClase_01, SalonClase_05
    callejon  STR_MER_Callejon_02            -39.3   118.9   7.0  TesoreriaMuralla
    callejon  STR_CLA_Callejon_05           -103.1    24.5   7.4  SalonClase_08
    callejon  STR_RAZ_Callejon_01            -45.7  -139.9   6.5  CasaRaza_02, RAZ_B02_Casa_01
    diagonal  Diagonal NO                    -50.9    50.9   8.7  SANTUARIO
    diagonal  Diagonal NO                    -58.0    58.0   8.1  SANTUARIO
    diagonal  Diagonal NO                   -114.6   114.6  10.2  Morada_NO_034
    diagonal  Diagonal SO                    -50.9   -50.9   8.7  OBELISK
    diagonal  Diagonal SO                    -58.0   -58.0   8.1  OBELISK
    diagonal  Diagonal SO                    -65.1   -65.1   7.7  OBELISK
    diagonal  Diagonal SO                    -72.1   -72.1   6.4  OBELISK
    diagonal  Diagonal SE                     50.9   -50.9   8.7  SALON_HAZANAS
    diagonal  Diagonal SE                     58.0   -58.0   8.0  SALON_HAZANAS
    diagonal  Diagonal SE                     93.3   -93.3   7.2  Morada_SE_011

Barrios de razas (E28, punto 12)
[ ] B06 con 2 casas: PROVISIONAL. Los barrios de razas son una plantilla (N_RAZAS = 6) y se rehacen cuando llegue
    la lista real de razas; no fijar logica de juego al numero de casas por barrio.

Interiores de las Moradas (E28)
[ ] Tres plantillas: int_morada_habitacion.glb (4 x 5), int_morada_casa_pequena.glb (6 x 8 con patio),
    int_morada_casa_grande.glb (8 x 10, dos plantas). Cada MARKER_Morada_Door_* carga la plantilla de su tipo como
    escena PRIVADA del dueno (una instancia por jugador que entra). La plantilla lleva un giro fijo de -90 grados
    respecto a CAM_Iso (la puerta +Y y el lado +X son los muros cercanos), sea cual sea la orientacion de la casa.
[ ] Ocultar WALL_Near_A / WALL_Near_B / CEILING siempre; WALL_Near_Casa (tabique del patio) al entrar en la casa
    pequena; LEVEL_1 + Furniture_L1 con el jugador en la planta baja de la casa grande (regla hide_when).
[ ] MARKER_Interact_Chest (slots = 40 / 100 / 200), MARKER_WorkStation_01/02, MARKER_Garden (jardinera de 7 matas),
    MARKER_Reception, MARKER_Interact_TrophyCase: Area3D. MARKER_Decor_Slot_xx (tipo pared / mesa / suelo / patio,
    level 0/1): Godot instancia ahi el prop que elija el jugador.
[ ] Vitrina: TROPHY_<Variante>_<plantilla> con hijos MARKER_Trophy_Slot_xx (+Y al frente; en la casa grande 01-09
    vitrina de pared y 10-15 vitrina de mesa). props_trophy_cases.glb trae TROPHY_Case_<v> con _LOD1 y _LOD2:
    visibility_range si se usan fuera de la escena privada. MAT_TrophyCase es transparente (alpha 0.3 en el vidrio).
[ ] Luces: Empties de Lights (como el Banco); hornear LightmapGI por plantilla. Un solo azul: la lamparilla de
    esquirla junto a la vitrina.
[ ] Props importados (Quaternius / Avramania): props_int_mercado.glb; los decimados traen material <MAT>__N_<prop>
    con su normal map (UV 'UVBake' = UV2 en Godot): normal_texture en UV2.

Moradas: puertas tapadas residuales (E28, punto 11)
[ ] ACEPTADAS por el usuario (13 de 1,404 = 0.93 %). Godot debe aclarar (dithering) techos, aleros, balcones y escaleras de
    la casa que tapa cuando el jugador se acerca a una de estas puertas (Area3D de ~6 m alrededor de MARKER_Morada_Door_*):
      NE_022_1: aclarar Morada_NE_021 (balcon/escalera, 7.62 m por el rayo)
      NE_047_1: aclarar Morada_NE_046 (balcon/escalera, 8.0 m por el rayo)
      NE_063_1: aclarar Morada_NE_061, Morada_NE_062 (cuerpo/alero, 8.86 m por el rayo)
      NE_070_1: aclarar Morada_NE_069 (balcon/escalera, 3.97 m por el rayo)
      NE_013_1: aclarar Morada_NE_012 (balcon/escalera, 4.78 m por el rayo)
      SO_048_1: aclarar Morada_SO_049, Morada_SO_050 (balcon/escalera, 7.88 m por el rayo)
      SO_064_1: aclarar Morada_SO_065, Morada_SO_066 (cuerpo/alero, 8.86 m por el rayo)
      SO_018_3: aclarar Morada_SO_019 (balcon/escalera, 3.99 m por el rayo)
      SO_035_1: aclarar Morada_SO_036 (cuerpo/alero, 8.83 m por el rayo)
      SO_035_2: aclarar Morada_SO_036 (cuerpo/alero, 6.54 m por el rayo)
      SO_035_3: aclarar Morada_SO_036, Morada_SO_037 (cuerpo/alero, 4.78 m por el rayo)
      SO_058_3: aclarar Morada_SO_059 (balcon/escalera, 3.95 m por el rayo)
      SO_059_3: aclarar Morada_SO_060 (balcon/escalera, 4.65 m por el rayo)
    Lista con parcela y distancias: docs/reports/stage28_moradas_residual.json. Viviendas totales: 1,398.

Personajes: cuerpo del elfo (PJ1)
---------------------------------
  - export/godot/pj_elfo_cuerpo.glb: 6 piezas + ojos en pose T, sin rig todavia (llega con concordia_rig.py).
    De cara a +Z en Godot, origen en el suelo entre los pies.
  - MAT_Elfo_Piel: ORM con R = AO; en Godot usar ao_texture_channel = R, roughness_texture_channel = G,
    metallic 0. Normal en convencion OpenGL (la de Godot).
  - Tono B ('corteza'): mismo material con albedo textures/personajes/elfo/elfo_m_albedo_corteza_1k.png (no va en
    el glb); conviene un StandardMaterial3D duplicado o cambiar la textura en tiempo de ejecucion.
  - Los grupos HIDE_* no viajan en el glb sin skin; cuando haya rig se exportaran como piezas separadas y la ropa
    ocultara la pieza entera (visible = false) o por mascara. Decidir al montar la ropa (PJ2).

Personajes: conjunto del Sanador (PJ2)
--------------------------------------
  - export/godot/pj_sanador_ropa.glb: Robe_Top, Robe_Skirt, Hood, Belt_Pouches, Boots, Bracers, Hair_Elf con un
    material (MAT_Sanador_Atlas): alpha scissor 0,5 (MASK), cull_disabled (doble cara), emision 1,0 con textura
    (solo el cristal, #8FD0FF). ORM: ao R, roughness G, metallic B.
  - pj_elfo_sanador_equipado.glb lleva el cuerpo ya recortado (vista previa). Para el juego: decidir en el rig
    (concordia_rig.py) como se ocultan los grupos HIDE_* (propiedad 'oculta' de cada prenda): borrar caras al
    equipar o mascara en el shader de piel (COLOR_0 con un bit por grupo).


Interiores unicos (etapa 29: int_tesoreria.glb, int_santuario.glb)
[ ] Al cargar un interior: effects.gd convert_surfaces() sobre su raiz (MAT_Water del pozo del Santuario -> shader de
    agua) y register_material() de sus materiales (MAT_Pipe_Light_Core de los 4 tubos de la Tesoreria laten).
[ ] Grupos ocultables por la propiedad hide_when (WALL_Near_A/B, CEILING siempre; LEVEL_1 con el jugador en la planta
    baja; WALL_Near_Despacho con el jugador dentro del despacho; Area3D en su suelo).
[ ] Luces: Empties de Lights (light_color, light_energy, light_range, light_kind) -> LightmapGI; un solo azul por sala
    (LIGHT_Pipes_Glow en la Tesoreria, LIGHT_Shard_Well en el Santuario).
[ ] Santuario: MARKER_Respawn (tipo = respawn) es el punto de reaparicion; MARKER_Interact_Santuario_Kit (propuesta).
[ ] Tesoreria: MARKER_NPC_Slot_02 (npc = Cambista) es una propuesta (el pedido solo nombraba al Tesorero).
[ ] Vitrinas: MAT_Pipe_Glass (alfa 0.35) con render_priority 0 como en la ciudad; esquirlas MAT_Shard_* (solo la Madura
    emite, 1.0).
```


## Anexo G2 — TODO_GODOT_personaje.txt

```text
TODO_GODOT_personaje - importar el elfo con esqueleto (PJ3) en Godot 4.7
======================================================================
Archivo: export/godot/pj_elfo_rig.glb (cuerpo completo + ojos + ropa del Sanador + pelo + esqueleto PJ_Elfo_Rig
de 70 huesos + 10 poses de prueba como animaciones POSE_01_T ... POSE_10_Caido). De cara a +Z, metros, pose T,
nodo del esqueleto sin transformacion.

1. Importar el .glb y abrir "Advanced Import Settings" (doble clic en el archivo).
2. Seleccionar el nodo Skeleton3D (PJ_Elfo_Rig):
   - Retarget > Bone Map: New BoneMap; Profile: New SkeletonProfileHumanoid.
     Los 56 huesos del perfil tienen exactamente los nombres de Godot, asi que el mapeo automatico los asigna todos
     (comprobar que no queda ningun hueso del perfil en rojo).
   - Los 14 huesos extra (Weapon_R, Weapon_L, Back_Slot, Head_Top, Hair_01..04, Skirt_Front_01..03,
     Skirt_Back_01..03) quedan SIN mapear a proposito: el retargeting los ignora.
   - Retarget > Rest Fixer: Apply Node Transforms = on; Normalize Position Tracks = on; Overwrite Axis = on;
     Fix Silhouette = on (el esqueleto ya esta en pose T; deberia no mover nada).
   - Retarget > Remove Tracks: Unmapped Bones = off si se quiere animar la trenza o la falda a mano; si solo las
     mueve SpringBoneSimulator3D, puede ir en on.
   - Skeleton3D > Unique Node: Make Unique on, Skeleton Name "GeneralSkeleton" (permite compartir animaciones entre
     razas: todas usan este mismo perfil).
3. Ranuras (sin deformacion): BoneAttachment3D en Weapon_R (baston en la mano derecha; el +Y del hueso es el eje
   del asa), Weapon_L, Back_Slot (arma o mochila a la espalda), Head_Top (efectos sobre la cabeza).
4. Trenza y falda: SpringBoneSimulator3D sobre el Skeleton3D, dos o tres juegos de cadenas:
   - Hair_01 -> Hair_04 (raiz Hair_01; Head queda fijo): stiffness ~0,6, drag ~0,4, gravity 1,0 (-Y).
   - Skirt_Front_01 -> Skirt_Front_03 y Skirt_Back_01 -> Skirt_Back_03: stiffness ~0,8, drag ~0,5, radio ~0,06.
   - Colisionadores: SpringBoneCollisionCapsule3D en LeftUpperLeg, RightUpperLeg, LeftLowerLeg, RightLowerLeg
     (radio 0,07-0,08) y una esfera en Hips. En las capturas de Blender las cadenas de la falda se colocaron por
     script delante/detras de rodillas y tobillos para imitar ese resultado.
5. Ocultar el cuerpo bajo la ropa: los grupos HIDE_* (ver README_personajes.txt y la propiedad 'oculta' de cada
   prenda en los extras del glb) no viajan como mascaras. Opciones al equipar: (a) ocultar la pieza del cuerpo
   entera cuando la tapa del todo (Torso, Arms, Feet con el conjunto completo); (b) mascara en el shader de piel.
6. Materiales: MAT_Elfo_Piel / MAT_Elfo_Ojos (opacos) y MAT_Sanador_Atlas (alpha scissor 0,5, cull disabled,
   emision solo en el cristal). ORM: AO en R, roughness en G, metallic en B.
7. Comprobacion rapida: AnimationPlayer > POSE_05_Sentado y POSE_10_Caido deben verse como en
   docs/captures/pj3_poses_ropa.png.

======================================================================
PJ4 - ANIMACIONES (Universal Animation Library de Quaternius + 4 propias del Sanador)
======================================================================
Archivos:
  animations/ual/ual1/AnimationLibrary_Godot_Standard.glb  UAL 1 Standard (CC0), 46 animaciones, rig DEF-* (53 huesos)
  animations/ual/ual2/UAL2_Standard.glb                    UAL 2 Standard (CC0), 43 animaciones, rig estilo Unreal (65)
  export/godot/pj_elfo_sanador_anim.glb                    elfo + ropa + esqueleto + 4 animaciones propias del Sanador
  godot_concordia/animations/bonemap_ual1.tres / bonemap_ual2.tres / bonemap_elfo.tres  (tools/make_bonemaps.gd)
NO se retargetea en Blender: lo hace Godot al importar.

Pose de reposo (tools/blender/pj4_compare_rest.py, docs/reports/pj4_reposo_ual.json, captura
docs/captures/pj4_reposo_ual_vs_elfo.png):
  - Las dos UAL estan en POSE T (brazo a 0 grados de la horizontal, codo 2 grados), igual que el elfo: no hay A-pose.
  - Las dos miran a -Y en Blender (+Z en Godot), igual que el elfo. Escala del armature 1.
  - Maniqui de la UAL: 1,65 m de esqueleto y cadera a 0,917 m; elfo: 1,94 m (con Head_Top) y cadera a 1,00 m.
  - Piernas: UAL casi juntas (0,4 grados); elfo algo abiertas (6,4 grados).

Ajustes del importador para CADA .glb de la UAL (Advanced Import Settings, nodo Skeleton3D):
  1. Retarget > Bone Map: cargar res://animations/bonemap_ual1.tres (o _ual2). Los 53 huesos de cuerpo y manos
     quedan asignados; LeftEye, RightEye y Jaw no existen en la UAL (normal: no los anima). Perfil:
     SkeletonProfileHumanoid. UAL1: spine.001/.002/.003 -> Spine/Chest/UpperChest; thumb.01 -> ThumbMetacarpal.
     UAL2: spine_01/02/03 -> Spine/Chest/UpperChest; los huesos *_leaf y ball_leaf quedan sin mapear.
  2. Rest Fixer:
     - Apply Node Transforms: on.
     - Normalize Position Tracks: ON (imprescindible: la cadera de la UAL esta a 0,917 m y la del elfo a 1,00 m;
       sin esto el elfo andaria hundido o flotando).
     - Overwrite Axis: on (los ejes de los huesos de Rigify / Unreal no son los del perfil).
     - Fix Silhouette: on. Las dos UAL ya estan en pose T, asi que casi no deberia mover nada; sirve para igualar
       las piernas algo abiertas del elfo (6,4 grados) con las de la UAL (0,4) y los dedos.
     - Reset All Bone Poses After Import: on.
  3. Remove Tracks: Except Bone Transform = on (quita pistas de malla o propiedades); Unimportant Positions = on
     (solo se conserva la posicion de Hips); Unmapped Bones = on (los leaf de la UAL2).
  4. Skeleton3D > Unique Node: Make Unique on, nombre "GeneralSkeleton" (el mismo que el elfo, PJ3 punto 2): asi las
     animaciones de la UAL se pueden guardar como AnimationLibrary y usar en el AnimationPlayer del elfo.
  5. Guardar las animaciones (Actions > Save to File: .res) en res://animations/ual/ y crear una AnimationLibrary
     "ual" con las que se usan (lista abajo). Las que acaban en _Loop ya entran en bucle (sufijo loop, documentacion
     4.7 "Animation loop (-loop, -cycle)").
  6. Movimiento de raiz: las variantes *_RM (Roll_RM, Sword_Attack_RM, Hit_Knockback_RM...) llevan desplazamiento en
     el hueso root; las demas son en el sitio. Si se usan las _RM: AnimationTree.root_motion_track = "%GeneralSkeleton:Root".

Ajustes del importador para export/godot/pj_elfo_sanador_anim.glb (las 4 propias):
  - Bone Map: res://animations/bonemap_elfo.tres (identidad: el elfo ya usa los nombres del perfil); Rest Fixer igual
    que en PJ3 (punto 2); Make Unique "GeneralSkeleton".
  - Heal_Channel-loop entra en bucle por el sufijo -loop; las otras tres no.
  - No llevan movimiento de raiz (Root sin desplazamiento; la cadera solo baja en vertical en Heal_Cast_Area y Revive).
  - Revive acaba de rodillas con la mano en el objetivo: salir con un blend de 0,3-0,4 s a Idle (o LayToIdle de la
    UAL2 al reves no hace falta).
  - El baston va en el BoneAttachment3D de Weapon_R (+Y del hueso = eje del asta, agarre a media altura); en las 4
    animaciones el asta queda: vertical en reposo, al frente y arriba en Heal_Cast_Single, vertical en
    Heal_Channel-loop, arriba y luego barriendo hacia abajo en Heal_Cast_Area, vertical apoyado en Revive.
  - Trenza y falda: en Blender son rigidas (la trenza se levanta en Revive al inclinarse); en Godot las mueve
    SpringBoneSimulator3D (PJ3 punto 4), que tambien las deja colgar en las poses inclinadas.
  - Efectos visuales y sonido de cada habilidad: aparte (G5 / audio), anclados a Weapon_R (punta del baston),
    LeftHand / RightHand y Head_Top. Momentos utiles: Heal_Cast_Single pulso en 0,43-0,60 s; Heal_Cast_Area arriba
    0,33-0,50 s y onda en 0,77 s; Revive mano en el objetivo desde 1,37 s.

Animaciones que se usan (ver docs/reports/pj4_anim.json):
  Idle            UAL1 Idle_Loop (2,50 s)                      [tambien Idle_Talking_Loop, UAL2 Idle_FoldArms_Loop]
  Walk            UAL1 Walk_Loop (1,33 s)                      [Walk_Formal_Loop 1,33 s: paso sereno, buena para el Sanador]
  Run             UAL1 Jog_Fwd_Loop (0,93 s) y Sprint_Loop (0,67 s)
  Sit             UAL1 Sitting_Enter (1,30 s), Sitting_Idle_Loop (1,67 s), Sitting_Exit (1,03 s), Sitting_Talking_Loop
  Hit             UAL1 Hit_Chest (0,33 s), Hit_Head (0,43 s); UAL2 Hit_Knockback (0,83 s, en el sitio)
  Death           UAL1 Death01 (2,40 s)                        [UAL2 LayToIdle 1,53 s sirve para levantarse al revivir]
  Hechizos UAL    UAL1 Spell_Simple_Enter (0,53 s), Spell_Simple_Idle_Loop (2,10 s), Spell_Simple_Shoot (0,50 s),
                  Spell_Simple_Exit (0,43 s)
  Propias         Heal_Cast_Single (0,90 s), Heal_Channel-loop (1,50 s), Heal_Cast_Area (1,20 s), Revive (2,00 s)
Faltan en la UAL Standard (Mixamo de reserva, lo descarga el usuario): andar hacia atras y de lado (strafe), girar
en el sitio, una segunda muerte, correr hacia atras, "lanzar con baston" (lo cubren las propias), levantarse del
suelo propio del Sanador (se puede usar LayToIdle de la UAL2).

======================================================================
PJ5 - IMPORTAR EL PERSONAJE FINAL (export/godot/personajes/) EN GODOT 4.7
======================================================================
Archivos: personaje_elfo_base.glb (esqueleto + cuerpo + ojos + pelo), elfo_sanador_<prenda>.glb (robe_top, skirt,
hood, belt, boots, bracers), elfo_sanador_lod2.glb, elfo_sanador_anims.glb. TODOS tienen el mismo esqueleto
(70 huesos, mismos nombres y orden; comprobado con debug/probe_pj5_glb.gd).

1. Copiar la carpeta a res://characters/elfo/ (o con tools/sync_assets.py cuando se anada la ruta).
2. Materiales (una sola vez): en personaje_elfo_base.glb, Advanced Import Settings > Materials: "Use External" para
   MAT_Elfo_Piel, MAT_Elfo_Ojos y MAT_Sanador_Atlas -> res://characters/elfo/materials/*.tres. En cada prenda y en el
   LOD2, apuntar MAT_Sanador_Atlas (y piel / ojos) a esos mismos .tres: las texturas del atlas se cargan una vez.
   MAT_Sanador_Atlas: alpha scissor 0,5, cull disabled; emision solo en el colgante (textura de emision).
3. Esqueleto en CADA .glb (base, prendas, LOD2, anims): Skeleton3D > Retarget:
   - Bone Map: res://animations/bonemap_elfo.tres (perfil SkeletonProfileHumanoid; identidad: el elfo ya usa los
     nombres del perfil; los 14 huesos extra quedan sin mapear).
   - Rest Fixer: Apply Node Transforms on, Normalize Position Tracks on, Overwrite Axis on. Fix Silhouette: on
     (el elfo esta en pose T; solo endereza las piernas, abiertas 6,4 grados).
   - Unique Node: Make Unique, nombre "GeneralSkeleton" (el mismo en todos los .glb).
4. Montar el personaje: instanciar personaje_elfo_base.glb; para cada prenda, instanciar su .glb y mover sus
   MeshInstance3D bajo el Skeleton3D del base (o poner su skeleton = ruta al GeneralSkeleton del base) y borrar el
   esqueleto de la prenda. Los nombres de hueso coinciden: el skin se resuelve solo. Al equipar, ocultar las piezas del
   cuerpo tapadas (Feet con botas; Torso con tunica + falda; ver README_personaje.txt seccion 5).
5. LODs: en cada pieza, visibility_range_end del LOD0 = 15 m y visibility_range_begin del <pieza>_LOD1 = 15 m,
   end = 40 m; el LOD2 (elfo_sanador_lod2.glb, una sola malla) desde 40 m (con el Sanador equipado; al desnudar o
   cambiar de clase se usa el LOD1 hasta tener su LOD2). Con camara isometrica ortografica la distancia es la del
   jugador (como scripts/lod_manager.gd de la ciudad).
6. Animaciones propias: elfo_sanador_anims.glb (sin mallas) -> Animation > Save to file / AnimationLibrary "sanador".
   Heal_Channel-loop entra en bucle por el sufijo -loop (verificado: el lector glTF de Godot 4.7 la marca en bucle).
7. UAL (seccion PJ4): importar AnimationLibrary_Godot_Standard.glb y UAL2_Standard.glb con bonemap_ual1/2.tres,
   Normalize Position Tracks ON (cadera 0,917 frente a 1,00 m), Overwrite Axis ON, Fix Silhouette ON (ya estan en pose
   T), Make Unique "GeneralSkeleton", guardar las animaciones en una AnimationLibrary "ual". Las _Loop entran en
   bucle; las _RM llevan movimiento de raiz.
8. AnimationPlayer del personaje con las librerias "ual" y "sanador"; AnimationTree con estados Idle / Walk / Run /
   Cast / Channel / Revive / Hit / Death. Baston: BoneAttachment3D en Weapon_R. Falda y trenza: SpringBoneSimulator3D
   (PJ3 punto 4).

======================================================================
PJ4b - DECISIONES DE ANIMACION (usuario, tras PJ4) y AnimationTree
======================================================================
Archivos nuevos (sobre los esqueletos ORIGINALES de la UAL; se retargetean al importar igual que la UAL completa):
  animations/ual/sanador_ual1_seleccion.glb  (bonemap_ual1.tres) Death_A, Death_B, Idle_Loop, Walk_Loop,
      Walk_Formal_Loop, Jog_Fwd_Loop, Sprint_Loop, Sitting_Enter/Idle_Loop/Exit/Talking_Loop, Hit_Chest, Hit_Head,
      Spell_Simple_Enter/Idle_Loop/Shoot/Exit
  animations/ual/sanador_ual2_seleccion.glb  (bonemap_ual2.tres) GetUp, GetUp_B, Consume, Yes, Idle_No-loop,
      Idle_FoldArms-loop, Chest_Open, Hit_Knockback
  (tools/blender/build_pj4b_ual_seleccion.py; informe docs/reports/pj4b_ual_seleccion.json; captura
   docs/captures/pj4b_muertes_getup.png). Comprobado con el lector glTF de Godot 4.7 (debug/probe_ual_sel.gd):
   las _Loop y -loop entran en bucle.

1. Andar hacia atras: SIN clip nuevo. En el AnimationTree, la misma Walk_Loop a traves de un AnimationNodeTimeScale
   con scale = -0.6 (documentacion 4.7: "scale the speed of the animation (or reverse it)"). Alternativa equivalente:
   AnimationNodeAnimation de Walk_Loop con play_mode = PLAY_MODE_BACKWARD y un TimeScale de 0.6.
2. Andar de lado: SIN clips laterales. El personaje gira hacia la direccion de movimiento (como en los MMO
   isometricos) y la locomocion es un AnimationNodeBlendSpace2D con blend_position = velocidad en ejes locales
   (x lateral, y adelante, en m/s normalizados): (0,0) Idle_Loop, (0,1) Walk_Formal_Loop o Walk_Loop, (0,2)
   Jog_Fwd_Loop, (0,3) Sprint_Loop, (0,-1) el nodo de andar hacia atras del punto 1; (+-1,0) y (+-2,0) con Walk/Jog
   (en la practica casi no se usan, porque el cuerpo ya gira). blend_mode = BLEND_MODE_INTERPOLATED, sync on.
   La UAL Standard (gratis) NO trae locomocion en 8 direcciones: segun su pagina de OpenGameArt, "all the
   locomotion movements in different directions" estan en la version completa de 120+ animaciones (Source, de
   pago); la Standard trae 45. No se compra nada.
3. Girar en el sitio: SIN clip. Por codigo, mientras suena Idle_Loop: rotation.y = lerp_angle(rotation.y, objetivo,
   1.0 - exp(-giro * delta)) con giro ~ 10 1/s (unos 0,3 s para media vuelta); al moverse, el mismo giro hacia la
   velocidad (la direccion de movimiento).
4. Muertes: Death_A (= Death01 de la UAL1, cae de espaldas) y Death_B (espejo izquierda-derecha de Death01 con otro
   giro de cabeza y otros brazos: se nota distinta y sigue siendo creible). Al morir se elige una al azar.
5. Levantarse: GetUp (LayToIdle de la UAL2, aprobado como apano) con 7 fotogramas de transicion al principio
   desde la pose final de Death_A: sin ellos, el LayToIdle original empezaba con el cuerpo en el mismo eje (boca arriba)
   pero con la cadera 0,31 m mas atras y los brazos en otro sitio (media 46 cm, maximo 1,36 m en una mano).
   Con la transicion, el primer fotograma coincide con el ultimo de Death_A (0 cm). GetUp_B: lo mismo desde Death_B.
   Tras Death_A -> GetUp; tras Death_B -> GetUp_B (sin fundido, o con 0,1 s). Revive (el Sanador) dispara GetUp
   (o GetUp_B) en el objetivo.
6. Extras de la UAL2 (aprobados): Consume para raciones y pociones; Chest_Open para cofres y las cajas de la boveda del
   Banco (G6); Idle_FoldArms-loop como variacion de espera (cada 8-15 s en Idle); Yes e Idle_No-loop como emotes.
7. Mixamo: de reserva, no se usa (lo descarga el usuario si un dia hace falta).
```


## Anexo H — godot_concordia/TEST_REPORT.md

```text
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
```


## Anexo H2 — godot_concordia/README_godot.md

````text
# CONCORDIA en Godot 4.7.2 — como abrirlo y probarlo en tu PC

## 1. Lo que necesitas
- **Godot 4.7.2 estable** (version normal, no la .NET): https://godotengine.org/download/archive/4.7.2-stable/
  (Windows: `Godot_v4.7.2-stable_win64.exe.zip`). Es la misma version con la que se ha montado el proyecto.
- Una tarjeta grafica con Vulkan (el proyecto usa Forward+). Con GPU integrada arranca en calidad Bajo.

## 2. Descomprimir el paquete
1. Descarga todas las partes `concordia_godot_paquete_parteNN.zip`.
2. Extrae **todas** en la **misma carpeta**, por ejemplo `C:\Users\USER\Desktop\Juego_1\Juegocamkeju\godot_concordia`
   (cada parte es un zip normal; si Windows pregunta por reemplazar archivos, di que si).
3. Debe quedar una carpeta con `project.godot`, `assets/`, `scenes/`, `scripts/`, `shaders/`, `navigation/`,
   `tools/`, `ui/`. La carpeta oculta `.godot/` es cache: `tools\preparar_pc.bat` la borra y la rehace sin GPU.

## 3. Prepararlo (una vez, y cada vez que cambien los .glb) y abrirlo
Desde 2026-11-11 el juego no carga los .glb: carga un **mundo horneado** (`world/`, chunks de 50 m con las mallas
fusionadas por material) que se genera en tu PC a partir de los .glb importados. Asi pasa de ~50.000 buffers de GPU
a ~15.000 con la ciudad cargada alrededor del jugador (arreglo de `VK_ERROR_TOO_MANY_OBJECTS`, error -10).
1. **Cierra el editor.** Desde la carpeta `godot_concordia`, en `cmd`:
   ```
   tools\preparar_pc.bat "C:\ruta\a\Godot_v4.7.2-stable_win64_console.exe"
   ```
   Borra la cache `.godot`, reimporta **sin GPU** (`--headless --import`), comprueba los .glb contra
   `assets/MANIFEST.txt` (`verificacion_assets.txt`) y hornea el mundo (`tools/build_world.gd`, `world/build_report.json`).
   A mano son tres ordenes: `--headless --path . --import`, `--headless --path . -s res://tools/verify_assets.gd` y
   `--headless --path . -s res://tools/build_world.gd`.
2. Abre Godot 4.7.2 -> **Importar** -> `project.godot` -> Importar y editar. No abras `scenes/concordia_glb.tscn` en el
   editor (es la ciudad fuente con todos los .glb: es justo lo que agota la GPU integrada).
3. Pulsa **F5**. Arranca en la plaza con la calidad automatica (GPU integrada -> **Bajo**); **F2** la cambia.

## 4. Teclas de prueba
| tecla | que hace |
|---|---|
| W A S D / flechas | andar (relativo a la camara) |
| Shift | correr |
| clic izquierdo | ir andando a ese punto por la navegacion |
| rueda del raton | zoom de 15 m al maximo del nivel de calidad (Bajo 60, Medio 90, Alto 120 m) |
| Q / E | girar la camara 90 grados |
| T | adelantar una hora (dia y noche) |
| F1 | mostrar u ocultar el HUD de depuracion (FPS, draw calls, triangulos, VRAM, zona, posicion, hora) |
| F2 | menu de calidad: Auto / Bajo / Medio / Alto, GPU detectada, FPS, draw calls y chunks cargados |
| R | volver al punto de inicio |

La flecha azul en el borde de la pantalla apunta al Faro cuando no se ve.

## 5. Benchmark (lo que necesito que me pases)
Cierra el editor y, en `cmd` dentro de la carpeta del proyecto:
```
"C:\ruta\a\Godot_v4.7.2-stable_win64_console.exe" --path . -s res://tools/benchmark.gd
```
Tarda unos 6-8 minutos: por cada nivel (Bajo, Medio, Alto) 8 escenas (plaza, Mercado, Oficios, Moradas de dia y de
noche, Razas y dos con el zoom maximo del nivel) y un paseo de 30 s cruzando distritos que mide los tirones de la
carga por hilos. Deja **`benchmark_resultados.txt`** en la carpeta del proyecto: pasamelo. Objetivo: **30 FPS
estables en Bajo** (FPS medio >= 30 y 1 % peor >= 25). Solo Bajo y mas corto: anade ` -- rapido niveles=Bajo`.
Para comparar con el renderizador **Compatibility** (OpenGL), repite con `--rendering-method gl_compatibility` antes de
`-s` y renombra antes el primer `benchmark_resultados.txt` (si no, se sobrescribe).

## 6. Que mirar en la prueba (parada 1 ampliada)
- Andar por avenidas, escaleras de las Moradas, puentes y la plaza; probar el clic para andar.
- La luz a distintas horas (T): 6:12 amanecer, 12:00, 17:30 hora dorada, 19:30 atardecer, 20:36 hora azul, noche.
- Los haces del Faro y del Crisol, el velo del Portal, el Obelisco, los huertos detras de las casas, la transparencia
  del Salon de las Hazanas cuando el jugador pasa por detras.
- Si algo falla, el HUD (F1) da la posicion en coordenadas de Blender: apuntala con una captura.

## 7. Notas
- Escena principal: `scenes/main.tscn` con `scenes/concordia.tscn` (las genera `tools/build_world.gd` a partir de la
  ciudad fuente `scenes/concordia_glb.tscn` de `tools/build_city.gd`; la navegacion se hornea con
  `tools/bake_navmesh.gd`). `world/` no va en git: se hornea en cada PC. Problemas de los modelos: `FIXES_BLENDER.md`; pruebas y cifras: `TEST_REPORT.md`.
- Los assets no estan en git (son copias de `export/` y `textures/` hechas por `tools/sync_assets.py`).
````


## Anexo H3 — godot_concordia/LEEME_CAMBIOS.txt (arreglo PC)

```text
CONCORDIA - arreglo para tu PC (GPU AMD integrada, Vulkan 1.3) - 2026-11-11
Descomprime este zip DENTRO de C:\Users\USER\Desktop\Juego_1\Concordia\godot_concordia (las rutas ya empiezan en
godot_concordia\). Reemplaza los archivos que pregunte. No toca ningun .blend, ningun .glb ni ningun .import.

PASOS EN TU PC (una vez)
1. Cierra el editor de Godot.
2. En cmd, dentro de godot_concordia:
     tools\preparar_pc.bat "C:\ruta\a\Godot_v4.7.2-stable_win64_console.exe"
   - borra la cache .godot (la reimportacion del editor dejo mallas vacias: errores 1 y 2)
   - reimporta SIN GPU (--headless --import)
   - comprueba los .glb contra assets\MANIFEST.txt -> verificacion_assets.txt
   - hornea el mundo del juego -> world\ (unos 41 MB, chunks de 50 m con las mallas fusionadas) y
     scenes\concordia.tscn + scenes\main.tscn
3. Abre el proyecto y pulsa F5. Con GPU integrada arranca en calidad Bajo. F2 = menu de calidad.
4. Benchmark (cierra el editor):
     "C:\ruta\a\Godot_v4.7.2-stable_win64_console.exe" --path . -s res://tools/benchmark.gd
   Mandame benchmark_resultados.txt. Si no llega a 30 FPS en Bajo, renombralo y repite con
   --rendering-method gl_compatibility delante de -s, y mandame los dos.
No abras scenes\concordia_glb.tscn en el editor: es la ciudad fuente con todos los .glb (lo que agota la GPU).

ARCHIVOS .import: ninguno cambia.  project.godot: no cambia.

QUE CAMBIA EN CADA ARCHIVO
scripts/materials_fix.gd   A: _beams blindado; beam_span() saca la altura del haz de la metadata del horneado, de los
                           vertices si existen o de la caja; comprueba nulos, is_instance_valid y arreglos vacios.
scripts/lod_manager.gd     quitado el parametro unit_depth (aviso); LOD por chunk (metadata lod_mask), distancias
                           ajustables por calidad (lod0_end / lod1_end), add_chunk / remove_chunk / force_refresh.
scripts/world_streamer.gd  NUEVO. Carga los chunks con hilos (ResourceLoader.load_threaded_request) a menos del radio
                           de carga (Bajo 120 m) y los libera a +25 m; carga inmediata alrededor del jugador al
                           arrancar y al teletransportar; monta las MultiMesh de cada chunk.
scripts/city.gd            modo mundo horneado (nodo Chunks): streaming + Special + Logic; materials_in_use(),
                           ensure_loaded(), apply_quality(); zone_name() estatico; links.json validado. Sin nodo Chunks
                           funciona como antes con los .glb.
scripts/quality.gd         NUEVO. Niveles Bajo / Medio / Alto y Auto (GPU integrada -> Bajo), guardado en
                           user://calidad.cfg.
ui/quality_menu.gd         NUEVO. Menu F2: Auto/Bajo/Medio/Alto, GPU y renderizador, FPS, draw calls, chunks, VRAM.
scripts/game.gd            tecla F2, crea Quality y el menu; prepare_area() antes de colocar al jugador; R recarga
                           la zona de inicio.
scripts/effects.gd         convert_surfaces() (velo, agua, estandartes; la usa tambien el horneado) y
                           register_material(); con el mundo horneado solo registra pulsos desde la biblioteca.
scripts/day_night.gd       ventanas y vitrales desde la lista de materiales; max_lanterns por calidad.
scripts/iso_camera.gd      zoom_max por calidad (Bajo 60, Medio 90, Alto 120 m).
scripts/nav_ready.gd       connected(): sin acceso a [0] con menos de 2 regiones.
scenes/concordia.tscn      AHORA es la ciudad del juego (mundo horneado). La genera tools/build_world.gd.
scenes/concordia_glb.tscn  NUEVO NOMBRE de la antigua concordia.tscn: ciudad fuente con los .glb (para hornear).
scenes/main.tscn           regenerada por tools/build_world.gd (misma luz y entorno).
tools/build_world.gd       NUEVO. Hornea world\: chunks de 50 m, una superficie por material, MultiMesh para lo
                           repetido, tejados por edificio, colisiones y oclusores por chunk, piezas especiales,
                           marcadores y biblioteca de materiales. Se para si alguna malla importada esta vacia.
tools/verify_assets.gd     NUEVO. sha256 y tamano contra assets\MANIFEST.txt + superficies vacias por .glb.
tools/preparar_pc.bat      NUEVO. Los pasos 1-2 de arriba.
tools/benchmark.gd         rehecho: Bajo / Medio / Alto, 8 escenas, paseo de 30 s con tirones de carga, veredicto
                           contra 30 FPS en Bajo, renderizador y GPU en la cabecera.
tools/build_city.gd        ahora genera scenes/concordia_glb.tscn (la ciudad fuente).
tools/bake_navmesh.gd      lee scenes/concordia_glb.tscn; caras vacias comprobadas.
tools/capture_tour.gd      q=<nivel>, escena=<ruta>; carga la zona antes de capturar.
tools/pick.gd, tools/make_bonemaps.gd   accesos a [0] blindados; pick carga la zona.
tools/sync_assets.py       --check leia mal el MANIFEST (decia que todo cambiaba).
debug/probe_gpu_objects.gd cuenta nodos, superficies, buffers estimados, visibles y chunks cargados.
debug/capture_top.gd, debug/make_main_glb.gd   herramientas de captura y comparacion.
README_godot.md, TEST_REPORT.md, .gitignore   documentacion y world/ fuera de git.
*.gd.uid                   identificadores de los scripts nuevos (los crea Godot).
```


## Anexo H4 — godot_concordia/TAREAS_GODOT.md

```text
# Tareas de Godot (lista de trabajo sacada de TODO_GODOT.txt)

Cada linea es un `[ ]` pendiente de `TODO_GODOT.txt` con la fase en que se hace. Se marca `[x]` cuando queda hecho y
probado (con la fecha y la prueba en `TEST_REPORT.md`).

## G1 - Importacion
- [x] Texturas externas `../../textures/...`: cada .glb en `assets/<tipo>/glb/` y las texturas en `assets/textures/` (sync_assets.py).
- [x] Texturas VRAM Compressed (normales RGTC por deteccion en los materiales, 35 de 255) — tools/import_settings.py.
- [x] Sufijos `-colonly` / `-navmesh` / `-occonly` aplicados por el importador (comprobado en el informe: StaticBody3D, NavigationRegion3D, OccluderInstance3D).
- [x] LOD automatico del importador desactivado (`meshes/generate_lods=false`); `_LOD1/_LOD2` marcados con metadata `lod_level`.
- [x] Opacos a una cara (CULL_BACK) salvo telas, hojas, velos, vidrios, pelo (post_import.gd).
- [x] Extras de glTF legibles como metadatos (metadata `extras` + claves sueltas) — tools/list_metadata.gd.
- [x] COLOR_0 = mask_pack del terreno: shaders/terrain.gdshader (huertos con CUSTOM0).

## G2 - Ensamble de la ciudad
- [x] LOD0/LOD1/LOD2 por distancia en planta al jugador (scripts/lod_manager.gd; los rangos de visibilidad usan la distancia de la camara, que en ortografica no sirve).
- [x] bld_* (portal, mercado, oficios, clases, razas, moradas NE/NO/SE/SO), terrenos por distrito, muralla colocada, marcadores.
- [x] NavigationRegion3D por distrito con las -navmesh (6); NAVLINK_*_Start/_End -> NavigationLink3D (16 parejas en la v28). Malla con fallos: FIXES F8-F11.
- [x] ~~13 soportes de tubos sobre calle/plaza~~: obsoleto, la ruta oeste de la v28 apoya los tubos en tejados.
- [x] `<N>_Roof` en grupo "roofs"; marcadores como Marker3D con grupos doors / npc_slots / interact / spawns.
- [ ] FARO_Body fuera de la navegacion (raiz FARO navigation=false); OBELISK_Mark_LitMaterialRef oculto.
- [ ] Tubos sin LOD: visibility_range_end ~250 m.
- [ ] Puestos (STALL_A..E), RAIL_Stone_3m, mallas de las Moradas: instancias ligeras / MultiMesh si hace falta (G7).

## G3 - Camara, jugador, HUD
- [x] Camara iso (-35.264, 45, 0), zoom 15-120 m, giro 90 grados, seguimiento.
- [x] Jugador capsula WASD + clic (navegacion); escaleras como rampas, subida de escalones hasta 0,25 m. Prueba de caminata: TEST_REPORT G3.
- [x] HUD F1.

## G4 - Luz y ambiente
- [x] Glow (umbral ~1.0) para los emisivos #8FD0FF; MAT_Embers (unica calida) no pasar de 1.5.
- [x] Vitrales y MAT_Window_Warm con el ciclo dia/noche; farolillos LANTERN_Shard (OmniLight3D pequena, tope 16).
- [ ] LightmapGI por distrito / interiores (UV2 con `--lightmaps` en import_settings.py) — medir coste (pasa a G6/G7: interiores).

## G5 - Efectos y shaders
- [x] PORTAL_Veil (agua, UV u 0..1, v = z/11 m), sin colision; runas del Atrio y pilares (pulso).
- [x] FARO_Beam (ADD, unshaded, sin sombras, sin profundidad) y FARO_Crystal (emision 4.0, pulso); brujula HUD.
- [x] OBELISK_Mark_001..100: material por instancia (MAT_Obelisk_Mark_Lit), diccionario de pisos.
- [x] MAT_Pipe_Light_Core: pulso Tesoreria -> Faro; MAT_Wall_Runes con faro_energy.
- [x] Taller_Carpinteria_WATERWHEEL girando ~6 rpm; agua del Cauce (MARKER_Cauce_Source -> _Outlet); fuente del Mercado.
- [x] Humo (Alquimia y Gran Forja; Posada, Hornos y Yurtas sin marcador: pendiente): Posada, Alquimia (MARKER_Alquimia_Smoke_01/02), Hornos, Yurtas; vapor MARKER_GranForja_Steam; brasas MAT_Embers.
- [x] Crisol: CRISOL_FloatStone_01..07 flotando; haz del oculo ADD.
- [x] Estandartes y banderas (clases y razas): textura por instancia y viento.
- [x] Transparencia por proximidad (occludes_iso: Salon de las Hazanas, muralla) con material por instancia.
- [x] MAT_Glass_R04: depth draw opaque only; MAT_Portal_Veil 0.6 / MAT_Faro_Beam 0.3 / MAT_Pipe_Glass 0.35: orden de transparencias.
- [ ] 13 puertas residuales de las Moradas: dither de la casa que tapa (Area3D ~6 m).

## G6 - Interacciones e interiores
- [ ] Puertas `MARKER_*_Door` (interior=true) -> int_banco.glb e interiores de Moradas (escena privada por jugador).
- [ ] Ocultar WALL_Near_*, CEILING, LEVEL_n segun hide_when; Area3D de la boveda.
- [ ] Banco: Banquero (MARKER_NPC_Slot_01), mostrador, boveda (VAULT_Door AnimatableBody3D), cajas Open/Locked.
- [ ] Moradas: cofre, estaciones, jardinera, vitrina (TROPHY_* y MARKER_Trophy_Slot_*), Decor_Slot.
- [ ] Portal: panel de 21 pedestales (MARKER_Descent_Pedestal_01..21). Mercado: Tablon de Grupos, Fuente.
- [ ] Santuario / Salon: disparador de puerta (interiores aun no modelados: solo aviso).
- [ ] Props decimados con normal en UV2 ('UVBake'): ver FIXES_BLENDER.md (Godot no lo admite en StandardMaterial3D).

## G7 - NPC y carga
- [ ] 20 NPC por la navegacion; prueba de 100 / 300 / 500 jugadores falsos; medidas en el PC del usuario.

## G8 - Personaje
- [ ] Solo con `personaje_elfo_base.glb` y animaciones (hoy: `pj_elfo_rig.glb` con 10 poses fijas, sin ciclos) — se salta.

## Fuera de alcance de Godot (decisiones / Blender)
- Faro: visibilidad desde calles aceptada; lo resuelve G5 (sin depth test + brujula).
- B06 provisional (plantilla de razas), SANTUARIO_Well provisional.
```


## Anexo H5 — godot_concordia/benchmark_resultados.txt (medido aquí, sin GPU)

```text
CONCORDIA - benchmark_resultados.txt (tools/benchmark.gd)
Fecha: 2026-11-11 23:26:27
Godot: 4.7.2-stable (official)
Sistema: Linux 24.04
CPU: Intel(R) Xeon(R) Processor @ 2.10GHz (4 hilos)
Memoria fisica: 15.7 GB
GPU: Unknown / llvmpipe (LLVM 20.1.2, 256 bits)  (tipo: software (CPU); nivel automatico: Bajo)
API grafica: 1.4.318  Driver: 
Renderizador: forward_plus (vulkan)
Ventana: (1280, 720)  Pantalla: (1280, 720)  Vsync: desactivado
Mundo horneado: 214 chunks; mallas fusionadas por material (tools/build_world.gd)
Escenas: 3 s de calentamiento + 5 s de medida; el jugador da vueltas de 6 m alrededor del punto.

== Nivel Bajo ==
escena                  FPS  1% peor ms medio   ms max   draw triangulos objetos  VRAM MB  chunks
plaza                   5.5      1.5   182.78   681.33    189     171458     406    354.8      42
mercado                 4.9      1.4   204.20   737.98    294     205145     503    345.5      41
oficios                 5.3      4.5   189.17   219.88    353     204494     562    340.5      38
moradas_ne              5.2      4.5   190.55   221.02    477     214510     684    343.0      41
moradas_ne_noche        5.1      4.1   195.29   246.75    477     217991     683    343.0      41
razas                   3.9      1.0   258.61   981.38    432     206781     644    343.6      41
plaza_zoom_max          5.0      4.4   201.71   227.76    315     195200     529    358.3      44
moradas_so_zoom_max     0.9      0.2  1157.36  5192.36    839     242748    1055    349.4      42
paseo_streaming         5.4      3.2   185.38   354.69  tirones > 50 ms: 161   chunks cargados/descargados: 10 / 11

Criterio: FPS medio >= 30 y 1 % peor >= 25 en todas las escenas y en el paseo.
Bajo: NO llega a 30 FPS estables en alguna escena
JSON: {"Bajo":[{"buffers_mb":54.868278503418,"chunks":42,"draw_calls":189,"escena":"plaza","fotogramas":28,"fps":5.47102390070026,"hora":17.5,"low1":1.46771541191661,"ms":182.78114264352,"ms_max":681.330993652344,"objetos":406,"texturas_mb":247.067138671875,"triangulos":171458,"vram_mb":354.804565429688,"zoom_m":45.0},{"buffers_mb":45.5323085784912,"chunks":41,"draw_calls":294,"escena":"mercado","fotogramas":26,"fps":4.89718730691273,"hora":17.5,"low1":1.35505210135631,"ms":204.198846670297,"ms_max":737.97900390625,"objetos":503,"texturas_mb":247.067138671875,"triangulos":205145,"vram_mb":345.45491027832,"zoom_m":45.0},{"buffers_mb":40.5810890197754,"chunks":38,"draw_calls":353,"escena":"oficios","fotogramas":28,"fps":5.28616663639209,"hora":17.5,"low1":4.54793513640752,"ms":189.172999790737,"ms_max":219.880004882812,"objetos":562,"texturas_mb":247.067138671875,"triangulos":204494,"vram_mb":340.498046875,"zoom_m":45.0},{"buffers_mb":43.1079158782959,"chunks":41,"draw_calls":477,"escena":"moradas_ne","fotogramas":27,"fps":5.24790625023958,"hora":17.5,"low1":4.52455917547752,"ms":190.552184493453,"ms_max":221.016006469727,"objetos":684,"texturas_mb":247.067138671875,"triangulos":214510,"vram_mb":343.026458740234,"zoom_m":45.0},{"buffers_mb":43.1079158782959,"chunks":41,"draw_calls":477,"escena":"moradas_ne_noche","fotogramas":26,"fps":5.1205252846551,"hora":23.0,"low1":4.05265207354906,"ms":195.292464036208,"ms_max":246.751998901367,"objetos":683,"texturas_mb":247.067138671875,"triangulos":217991,"vram_mb":343.026458740234,"zoom_m":45.0},{"buffers_mb":43.6914939880371,"chunks":41,"draw_calls":432,"escena":"razas","fotogramas":21,"fps":3.86687422561528,"hora":12.0,"low1":1.01897118613931,"ms":258.606807890392,"ms_max":981.382019042969,"objetos":644,"texturas_mb":247.067138671875,"triangulos":206781,"vram_mb":343.611236572266,"zoom_m":45.0},{"buffers_mb":58.3238201141357,"chunks":44,"draw_calls":315,"escena":"plaza_zoom_max","fotogramas":26,"fps":4.95770033902313,"hora":17.5,"low1":4.39068287660477,"ms":201.706422659067,"ms_max":227.755004882812,"objetos":529,"texturas_mb":247.067138671875,"triangulos":195200,"vram_mb":358.262359619141,"zoom_m":60.0},{"buffers_mb":49.5012226104736,"chunks":42,"draw_calls":839,"escena":"moradas_so_zoom_max","fotogramas":7,"fps":0.864038936477822,"hora":17.5,"low1":0.192590548825701,"ms":1157.3552507673,"ms_max":5192.36279296875,"objetos":1055,"texturas_mb":247.067138671875,"triangulos":242748,"vram_mb":349.428573608398,"zoom_m":60.0},{"cargas":10,"descargas":11,"escena":"paseo_streaming","fallos_carga":0,"fotogramas":162,"fps":5.39433199100835,"low1":3.19760554303672,"ms":185.37976558856,"ms_max":354.68798828125,"tirones_50ms":161}]}
```


## Anexo I — godot_concordia/FIXES_BLENDER.md (F1–F11)

```text
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
```


## Anexo J — ASSETS_LICENSES.md

```text
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
```


## Anexo K — respaldo/MANIFEST.txt (copias de seguridad con sha256)

```text
CONCORDIA - carpeta de respaldo (fuera de git, decision del usuario en la etapa 26)
concordia_master_<fecha>_v<NN>.blend = copia del .blend maestro de esa fecha; glb/ = export/godot de esa fecha;
interiors/ = blend de interiores y texturas generadas que no estan en git.
2026-11-12/interiores_e29/ = interiores unicos de la etapa 29 (Tesoreria, Santuario): blend, .glb, textura de la boveda e informes.
personajes/ = blend, texturas y capturas de los personajes; personajes_pj5/ = cierre del personaje (master v1.0,
              .glb finales, texturas, con su propio MANIFEST); ual_original/ = zips de la UAL 1 y 2 de Quaternius; fuentes_assets/mpfb = paquetes oficiales de MPFB y MakeHuman.
binarios_git/ = .jpg, .gltf y .bin que estaban en git hasta la etapa 27 (sacados con git rm --cached; la
               historia de git los conserva hasta el commit 6861619), con su ruta original.
Comprobar (desde respaldo/): grep -E '^ +[0-9]+  [0-9a-f]{64}' MANIFEST.txt | awk '{print $2"  "$3}' | sha256sum -c

       bytes  sha256                                                            archivo
    77872912  e4759847416e765b08b470d7c0c23fe79528efd910e638d7ceb1d0818ae6d735  2026-11-08/concordia_master_2026-11-08_v26.blend
     7011912  538db23e76f71ed190cbac8319046984cbce9263ce49e66fd046ea90df165119  2026-11-08/glb/bld_clases.glb
     1636816  af2efef8e8f4e6f9170b76911167c568f4700a91699250a12626ac8e3c18a524  2026-11-08/glb/bld_kit.glb
     6988376  333330c14025e816c9990d99ce9ac93dae0a0d25e7784c10a3f05f18fcc0d851  2026-11-08/glb/bld_mercado.glb
     4240536  2fc578694bf99924a2174cd4e8d3dfb728caa1a8acefbf81f33b8e1aa177c9a2  2026-11-08/glb/bld_moradas_NE.glb
     4580368  44b49259cd2a48f9c9bee4bf034bea7934e2ad259262fb9982c2739e8d711ed9  2026-11-08/glb/bld_moradas_NO.glb
     3824712  490a181c64a3505f6b54bf2343bc85efb4c6de3c15b38e2b477eeebe5e592232  2026-11-08/glb/bld_moradas_SE.glb
     4158680  989c8508b89a4ac693ed929596de6c952abcd97e4f5d7d17dcec83897e0d9e89  2026-11-08/glb/bld_moradas_SO.glb
     5304908  a2cd6266216519a151f5f2d2600936d76f88679d5a1a8ce11889e72e20f15e53  2026-11-08/glb/bld_oficios.glb
     5918276  57577bcc4175384992adf5733f7111c59584bd71e29f8876baa8b114c88827d4  2026-11-08/glb/bld_portal.glb
      367556  517e7220387dac37d441fb3779dc9a3d890f14654d2f15099c1be98ffca8a950  2026-11-08/glb/bld_props.glb
    10750344  1ed1b567a81967ae4eb741e16801d26955ef239b34c349718caf74638196d845  2026-11-08/glb/bld_razas.glb
      250304  ea6498d1cb929114bb39c3f770f9dcc6cfefdf043bd8477b94d0df11ec66ec7c  2026-11-08/glb/concordia_markers.glb
     4833968  9107c1c52418aa6d6ea40dc34ecc767b6fa688bb83eb0819a999c3846b3af1ef  2026-11-08/glb/concordia_terrain_clases.glb
    16391716  3f96c6bc501175fac754304534fc5b236cb68982adcc75256556af8dff473606  2026-11-08/glb/concordia_terrain_exterior.glb
     4716248  397e4143134d6b66bc9932b1904599b946f10d0e2977a4ef55eeb64a23c2d842  2026-11-08/glb/concordia_terrain_mercado.glb
    18902852  8b7ad94acce65ec3bc1d2f5a7b31a76d359d3ef30993d04266def8985f18eb8d  2026-11-08/glb/concordia_terrain_moradas.glb
     8306616  e28ce828da176af0e70fb3bcb90d20d3c4c1d0b588d0f48a4244706586e86052  2026-11-08/glb/concordia_terrain_oficios.glb
     7723296  cbfbc08065edff90ee7596a3837262327be0b18664b4681d54b5e5b87de70142  2026-11-08/glb/concordia_terrain_plaza.glb
     4681556  acff056c96ddd642cf9a4463e0c2605226c5d5489af610a5818bb5d6bf0e0e3e  2026-11-08/glb/concordia_terrain_razas.glb
     1690444  d4e0a80342588ad23bae871086253e8daeff5b8b77a55da250408e1e11480228  2026-11-08/glb/concordia_wall_kit.glb
     1004568  b7542d05044a6fbe18e9717e664e376f3f4415876e014884f0989c12e95e961b  2026-11-08/glb/concordia_wall_layout.glb
      102761  1651aeee3450dcbc7f529ed589d60b3ed689c51cf5465a0dbd241471d2cb67d7  2026-11-08/interiors/bank_box_numbers_1k.png
      709346  5eb21e12a2d54f257be00cef1f3f3801dea70ee932b208bb1d401a0590f9b93d  2026-11-08/interiors/concordia_interiors_v01.blend
     1689852  6153a48869c87789ec2c91117f18463368c1729234415e4db17c371a7ee50d32  2026-11-08/interiors/int_banco.glb
     1021452  c8e787e4c0b97e515d97b38317d8b54cc022c6be76f47558e4ff67d42db0e220  2026-11-11/binarios_git/export/godot/materials/concordia_materials.bin
       84250  fde16298c6b1d1ab688b85f497a5f10a44ef4d7765a19fb11d7bb229dacb6801  2026-11-11/binarios_git/export/godot/materials/concordia_materials.gltf
     2341084  781ff604ccb3986092c29e7cfa0dab7bd59378a2d789cd530dd4d31e1513bd89  2026-11-11/binarios_git/textures/concordia/MAT_Ash_Gray/T_Ash_Gray_Albedo.jpg
     3272397  9719a346368fb16d3a8cf261d78a84333d2e1eba6409f84e3ce2bcdab7785565  2026-11-11/binarios_git/textures/concordia/MAT_Ash_Gray/T_Ash_Gray_Normal.jpg
      774903  54529f81a6dfde3f59ace18d42dfd83789bd12eac9f1087124a54e8b82ccc37a  2026-11-11/binarios_git/textures/concordia/MAT_Ash_Gray/T_Ash_Gray_Roughness.jpg
      828620  8c13e4db9b6f1b273922182b61d3e862f4530c661ca26d822a5f0dfb4fab8f88  2026-11-11/binarios_git/textures/concordia/MAT_Cloth_Patch_A/T_Cloth_Patch_A_Albedo.jpg
     2285051  c993a42205bca3bc7e5df33bc57b692a39401ece453375c83b0f257edc315e2f  2026-11-11/binarios_git/textures/concordia/MAT_Cloth_Patch_A/T_Cloth_Patch_A_Normal.jpg
      197292  2ee92062a8b9ed40af1a15b37e211c3c1cfdccabbb754d61dc0feeef91aa318f  2026-11-11/binarios_git/textures/concordia/MAT_Cloth_Patch_A/T_Cloth_Patch_A_Roughness.jpg
      909145  5ff7b31065605a1cc9220d79b2504421743b9eaa35540fb92956344134af0eff  2026-11-11/binarios_git/textures/concordia/MAT_Cloth_Patch_B/T_Cloth_Patch_B_Albedo.jpg
     2285024  357b148703f187c2b70a688b8ab3a2e425b649f23d532ae90bda4b81622a31cf  2026-11-11/binarios_git/textures/concordia/MAT_Cloth_Patch_B/T_Cloth_Patch_B_Normal.jpg
      191826  d2cf9471ca7b4a37c713143b584b828a147cc0c6b92432d9dfc8a3a894a369df  2026-11-11/binarios_git/textures/concordia/MAT_Cloth_Patch_B/T_Cloth_Patch_B_Roughness.jpg
      906921  0326bcdc817f44b64b91ab9b87452613023c587de09b039c60b77deae139d55e  2026-11-11/binarios_git/textures/concordia/MAT_Cloth_Patch_C/T_Cloth_Patch_C_Albedo.jpg
     2285288  b99f3c2d7f35c13588126107ee0f371a69ca9c3f93f4a0893a1fe18fd6b8dc97  2026-11-11/binarios_git/textures/concordia/MAT_Cloth_Patch_C/T_Cloth_Patch_C_Normal.jpg
      194780  8b3ac6bd5397427a4cc4cdb8abd2de996a44d58b28c2ce5aeb66eda3dfc5f070  2026-11-11/binarios_git/textures/concordia/MAT_Cloth_Patch_C/T_Cloth_Patch_C_Roughness.jpg
     1954783  2ca2447fccffa37d6e37c0c3146c9bdbf935980d763241303fb7878c4179eba6  2026-11-11/binarios_git/textures/concordia/MAT_Cobble_Concordia/T_Cobble_Concordia_Albedo.jpg
     2303270  3c4a0499c5d5d65640e05ab0f8b79d2ecb0631ec157a136593cc6f5cca9edae2  2026-11-11/binarios_git/textures/concordia/MAT_Cobble_Concordia/T_Cobble_Concordia_Normal.jpg
      918187  db378b392df3e60de36dba95687a90fb842dc4ce2c04eb3a97305125dc4485ba  2026-11-11/binarios_git/textures/concordia/MAT_Cobble_Concordia/T_Cobble_Concordia_Roughness.jpg
     2044506  eafd5dde7ba6ef9ac36075cd17bf7437ade0ce2c899e87a7382b5812810d80cf  2026-11-11/binarios_git/textures/concordia/MAT_Ground_Cracked/T_Ground_Cracked_Albedo.jpg
     2860067  9811549da08621691b09e5bd33f0607cf8200ff1f1670a5a9691f4d628c6ad76  2026-11-11/binarios_git/textures/concordia/MAT_Ground_Cracked/T_Ground_Cracked_Normal.jpg
     1361968  8c37eaa0617df79b908a8a295e0d0581f485e158890f0757781081d080745fda  2026-11-11/binarios_git/textures/concordia/MAT_Ground_Cracked/T_Ground_Cracked_Roughness.jpg
      213437  5597773d5ecc0e3faf43a2d0725b1c67e8d0f8e0f04b7f7ef02d5ff8490749ea  2026-11-11/binarios_git/textures/concordia/MAT_Iron_Black/T_Iron_Black_Albedo.jpg
      378561  445ae1e39aaaed41f711bfb47988082af436dc9c2605f9013244e3097a4f0afa  2026-11-11/binarios_git/textures/concordia/MAT_Iron_Black/T_Iron_Black_Normal.jpg
      206091  0c91fc917919e161843421f306a75e2c088e854d8ea0204e65f8018857e516b1  2026-11-11/binarios_git/textures/concordia/MAT_Iron_Black/T_Iron_Black_Roughness.jpg
     1829927  096ec29fa39f8a1148d51fd5b7263a6f44ea31fc424d24a9a976b0f848b8eea0  2026-11-11/binarios_git/textures/concordia/MAT_Limestone_Worn/T_Limestone_Worn_Albedo.jpg
     1891945  d9171fc1bef5b1e0c116ecff491fb70286971bde2e36e747bff3c0af4fca4d9a  2026-11-11/binarios_git/textures/concordia/MAT_Limestone_Worn/T_Limestone_Worn_Normal.jpg
     1446708  469b0d89d1de432c18f581ef46f5ccfc310db4a11308585f9efc6cd2b0fd40ee  2026-11-11/binarios_git/textures/concordia/MAT_Limestone_Worn/T_Limestone_Worn_Roughness.jpg
      213172  d6a2abb3d1352ae44f0cf2940e11049316d58511062d869f395dcf9dc09501bd  2026-11-11/binarios_git/textures/concordia/MAT_Plaza_Slab/T_Plaza_Slab_Albedo.jpg
      195350  fa3bc71cbf6d5a2562f7bb4cc530c041b88c77bc2b84bf4eea9113d891dc6471  2026-11-11/binarios_git/textures/concordia/MAT_Plaza_Slab/T_Plaza_Slab_Normal.jpg
      177611  c9c84116248f617aad74bfcc1ece0a922056a5de47428e1b770894b681ace1e1  2026-11-11/binarios_git/textures/concordia/MAT_Plaza_Slab/T_Plaza_Slab_Roughness.jpg
      262599  4d46a15339627690ce40a99a35e88cfa32fc4190a83abac2cee5fd541cc6923d  2026-11-11/binarios_git/textures/concordia/MAT_Plaza_Slab_Travertino/T_Plaza_Slab_Travertino_Albedo.jpg
      223212  68f6d499ce870cf915efe6d4ca3be9e2de35453e6fb688a80baef4099bee0f97  2026-11-11/binarios_git/textures/concordia/MAT_Plaza_Slab_Travertino/T_Plaza_Slab_Travertino_Normal.jpg
      180281  a76f43226a6f8800e4f1c19fa9c1fbb318d1de57b2bb79e81e21338bf9a310da  2026-11-11/binarios_git/textures/concordia/MAT_Plaza_Slab_Travertino/T_Plaza_Slab_Travertino_Roughness.jpg
     1402587  d520adafcd28db14dc1ebdd88f85c6daf568ca3523bd4df8ac04cd55758f368e  2026-11-11/binarios_git/textures/concordia/MAT_Rock_Gray/T_Rock_Gray_Albedo.jpg
     2293668  7c93a2facdd3717b9216e35fc50c398ff43145c70b00fe7e69f05e18db7a1aed  2026-11-11/binarios_git/textures/concordia/MAT_Rock_Gray/T_Rock_Gray_Normal.jpg
     1163555  94852af484a7add5bc616e9a15c96e090601565d61d582dbf2d10070eee837b8  2026-11-11/binarios_git/textures/concordia/MAT_Rock_Gray/T_Rock_Gray_Roughness.jpg
      249550  00714a429b96fa97e5f7a169fdcefdb2015d9531e9bf6f014c7b0c3c485a092d  2026-11-11/binarios_git/textures/concordia/MAT_Roof_Tile_Ocher/T_Roof_Tile_Ocher_Albedo.jpg
      220520  f5e0730a0c43f6c89f19887cf9f93aa909d19488b6600e66c73ae20e2acb21b1  2026-11-11/binarios_git/textures/concordia/MAT_Roof_Tile_Ocher/T_Roof_Tile_Ocher_Normal.jpg
      179207  f184723a80ffe86e007c4ad783bb4abe282eda734b5432d3f3cc5b2b4bbc669d  2026-11-11/binarios_git/textures/concordia/MAT_Roof_Tile_Ocher/T_Roof_Tile_Ocher_Roughness.jpg
       93356  3a50e9ec0b412bb3529b2d584e69a6b89bb2fe4a37ef6b81d41ebb4afd147665  2026-11-11/binarios_git/textures/concordia/MAT_Shard_Blue/T_Shard_Blue_Albedo.jpg
      143418  d2f434b814126f540314b26675f15ceef22b1fd8d53bd7726d5dea2be9828497  2026-11-11/binarios_git/textures/concordia/MAT_Shard_Blue/T_Shard_Blue_Normal.jpg
       68718  0aeb95527d95df77dbb9625e7a68f14f5ba52c2f9d5320456151c4d3dd1f760d  2026-11-11/binarios_git/textures/concordia/MAT_Shard_Blue/T_Shard_Blue_Roughness.jpg
      261028  9c9670f3ae16a1aabf4fbb2b17a0fcbfb8cfa7d4df62be360a878bb6bfe342b6  2026-11-11/binarios_git/textures/concordia/MAT_Stone_Repair/T_Stone_Repair_Albedo.jpg
      289772  9e38a79536c1c1b3c9328a017fafba5ed98c8e881ff767ba3c1dfa50f87235b7  2026-11-11/binarios_git/textures/concordia/MAT_Stone_Repair/T_Stone_Repair_Normal.jpg
      156978  8db80cda932da23e0cb7de411b7e117c915ef3cff73bcac42c94582e4dc80f55  2026-11-11/binarios_git/textures/concordia/MAT_Stone_Repair/T_Stone_Repair_Roughness.jpg
     2124186  7d3254fd5ed73b104ee0b80e03743d295861de9300a4f98bedfe54c3cb370d53  2026-11-11/binarios_git/textures/concordia/MAT_Wall_Gray/T_Wall_Gray_Albedo.jpg
      411830  bfa479e63dd50bbdc9f89c3981063cacb01e6e737b3f7894e881a054835a2291  2026-11-11/binarios_git/textures/concordia/MAT_Wall_Gray/T_Wall_Gray_Normal.jpg
      157416  fe87889c4431d0f8e3a44749359ed745a8f66ee3277622d45398b68bcb9d56f9  2026-11-11/binarios_git/textures/concordia/MAT_Wall_Gray/T_Wall_Gray_Roughness.jpg
      271684  411619ae3ec10b9251a6b2df69b912b3a63cc6578028f66a02cd78ed9b0665c3  2026-11-11/binarios_git/textures/concordia/MAT_Wall_Runes/T_Wall_Runes_Albedo.jpg
      420411  0ba61fd59df6dcd67f218e305fb7f03b4535c9aec2b1ddb9c2731486bc8b10ce  2026-11-11/binarios_git/textures/concordia/MAT_Wall_Runes/T_Wall_Runes_Emission.jpg
      522259  517c4de614ad45c4492d057d3614d1995718015e34fac254e3395a2238b0bf9c  2026-11-11/binarios_git/textures/concordia/MAT_Wall_Runes/T_Wall_Runes_Normal.jpg
      190016  143c6e25d494a314a97c389263b420fd8d294aaba3c718882dd334656ccb56c2  2026-11-11/binarios_git/textures/concordia/MAT_Wall_Runes/T_Wall_Runes_Roughness.jpg
       66164  fb73740406e7d7f80bd220b522d06ed75f7b332fdf71d6cc32af44e6c9a62375  2026-11-11/binarios_git/textures/concordia/MAT_Water/T_Water_Albedo.jpg
      212795  4d801bdcbe5792c2bc1f6c9137229e87d7646a2c55817512056e7320bd101bb4  2026-11-11/binarios_git/textures/concordia/MAT_Water/T_Water_Normal.jpg
       49484  ccbf1ab467bf8219217a0217c568e41c0e6b199627e671aa5281763c8ccc5888  2026-11-11/binarios_git/textures/concordia/MAT_Water/T_Water_Roughness.jpg
      781282  4b814f538f167a7a355dcd3eeead94294cf195dba6f98773c043e019bed64229  2026-11-11/binarios_git/textures/concordia/MAT_Wood_Dark/T_Wood_Dark_Albedo.jpg
      909112  af31081f3975a282480a753b76585681df02fab69af092046c68455483485bd9  2026-11-11/binarios_git/textures/concordia/MAT_Wood_Dark/T_Wood_Dark_Normal.jpg
      469521  666bb10f2a05bb9dec54721fbdf813ad8c9d7c2611b2b315cab49abc22127df9  2026-11-11/binarios_git/textures/concordia/MAT_Wood_Dark/T_Wood_Dark_Roughness.jpg
     1483267  56e50f8868646a6dbb453391bfa9a4606fe91658293ce78cc616b075f45393aa  2026-11-11/binarios_git/textures/concordia/polyhaven_src/broken_wall/broken_wall_AO_2k.jpg
     2382913  35615ed619b14ab8991205e887a24cadcf8edffdf15b36b153421604b9ba29ce  2026-11-11/binarios_git/textures/concordia/polyhaven_src/broken_wall/broken_wall_Diffuse_2k.jpg
     1215009  3a729439f9ad59bbf702ddcef2dafd47d8ce51dbf05dd960f0a916755a8ebb35  2026-11-11/binarios_git/textures/concordia/polyhaven_src/broken_wall/broken_wall_Rough_2k.jpg
     3578159  ce7935ef7b418a7e20ade08311443deb0b30a0f77559879780bba2e2e07f5a44  2026-11-11/binarios_git/textures/concordia/polyhaven_src/broken_wall/broken_wall_nor_gl_2k.jpg
     1653941  dee95cf4b7f88c7a214e3a55163553c7552d804cdb3d11ec3ebc1079a71c6106  2026-11-11/binarios_git/textures/concordia/polyhaven_src/castle_wall_slates/castle_wall_slates_AO_2k.jpg
     2381426  89e1dce61cf53decf586bd123b9280365e447019ebedaf3b8e48663ab37eab30  2026-11-11/binarios_git/textures/concordia/polyhaven_src/castle_wall_slates/castle_wall_slates_Diffuse_2k.jpg
     2005253  84fe81f77d25e4dc37be41174b0a1fa85e8aece244eabe54ed48c542cb5bed08  2026-11-11/binarios_git/textures/concordia/polyhaven_src/castle_wall_slates/castle_wall_slates_Rough_2k.jpg
     4054865  ea6042cdb95576d9c2d67c7fa26e3648cca09d8d2fcaf4dfe7d6052a970d7b28  2026-11-11/binarios_git/textures/concordia/polyhaven_src/castle_wall_slates/castle_wall_slates_nor_gl_2k.jpg
     1600880  2923714c9866f29792379ef0ebe4f4dec3c399030141462baa695d7a92937a9b  2026-11-11/binarios_git/textures/concordia/polyhaven_src/castle_wall_varriation/castle_wall_varriation_AO_2k.jpg
     2386019  47d50ed57e111e3abfbd367872b5d23e3ab128c45b7172886752ce985f5b9f2b  2026-11-11/binarios_git/textures/concordia/polyhaven_src/castle_wall_varriation/castle_wall_varriation_Diffuse_2k.jpg
     1643779  1f407860d6e9ce2ab074fddf6a0cbbfd3cd751e842bd115ab0ce6b6500e9eb24  2026-11-11/binarios_git/textures/concordia/polyhaven_src/castle_wall_varriation/castle_wall_varriation_Rough_2k.jpg
     3537669  b78d76a84e3b37a936f8bd3fb870f8740f3e0c5dd56179cef4b35bd1341a4ee5  2026-11-11/binarios_git/textures/concordia/polyhaven_src/castle_wall_varriation/castle_wall_varriation_nor_gl_2k.jpg
     2394580  cb290db525b86cb9ce398fc42b5547ee79943b68fa2e35c9cf2c4ad3abd3f3bc  2026-11-11/binarios_git/textures/concordia/polyhaven_src/cobblestone_floor_001/cobblestone_floor_001_Diffuse_2k.jpg
     1581274  8fb9fe5f128f9878dd0858c18ae83864acad2492562175b9d62ba6df9f93693d  2026-11-11/binarios_git/textures/concordia/polyhaven_src/cobblestone_floor_001/cobblestone_floor_001_Rough_2k.jpg
     3683849  f4a33714608a5ebf0895084a3821d64619f3e565f8840716177cd5be9655f50b  2026-11-11/binarios_git/textures/concordia/polyhaven_src/cobblestone_floor_001/cobblestone_floor_001_nor_gl_2k.jpg
     2014209  26a099a07e81a1d806fc3b49db5984d27cfc9f7b6abffd483c765ee687d1fa02  2026-11-11/binarios_git/textures/concordia/polyhaven_src/dry_ground_01/dry_ground_01_AO_2k.jpg
     2541635  b6b601e75ba68d91ea1b09af87e95f186d15d8210e4f14692f9b20d2e21d437b  2026-11-11/binarios_git/textures/concordia/polyhaven_src/dry_ground_01/dry_ground_01_Diffuse_2k.jpg
     1456821  a63000ba9e78a8ad5ddd1ea128ed20d91e68dba841c486af7292b8e7724c685a  2026-11-11/binarios_git/textures/concordia/polyhaven_src/dry_ground_01/dry_ground_01_Rough_2k.jpg
     1080854  ffb7d63a0d93ff7fa352a2b9340ce5d3e29156435634dfe75e7647a99fee9fa8  2026-11-11/binarios_git/textures/concordia/polyhaven_src/dry_ground_01/dry_ground_01_nor_gl_2k.jpg
     1748232  b5579dd40e6182a8d077db04e9d008d1f240c5a4fa8e4a11c54cb409c444328b  2026-11-11/binarios_git/textures/concordia/polyhaven_src/floor_tiles_02/floor_tiles_02_AO_2k.jpg
     1381118  9a4e5acbb6c71e03979cc75fe1121ae0dc66583153cab9f32116c79e33707634  2026-11-11/binarios_git/textures/concordia/polyhaven_src/floor_tiles_02/floor_tiles_02_Diffuse_2k.jpg
     1214592  95007052c6cc7a92284a5cea92ebdaecbfae6fcdd6dfd6ac443e2af43ddcd9a6  2026-11-11/binarios_git/textures/concordia/polyhaven_src/floor_tiles_02/floor_tiles_02_Rough_2k.jpg
      540151  0c0d11a6ee43f523131db810720e4232ff35f05c126a7959d499a715294a1ad6  2026-11-11/binarios_git/textures/concordia/polyhaven_src/floor_tiles_02/floor_tiles_02_nor_gl_2k.jpg
      537495  3e665f5cbe8f0c0760e54b49c15ee6a6236c59d103c2ea5834548c1748ed0dc9  2026-11-11/binarios_git/textures/concordia/polyhaven_src/hessian_380/hessian_380_AO_1k.jpg
      944914  5727302df3a9c845e6320ff186ac13fc7d0f1ffcd6fda71667e808e09379fe6f  2026-11-11/binarios_git/textures/concordia/polyhaven_src/hessian_380/hessian_380_Diffuse_1k.jpg
      849875  9aee9570e37bbe7effd229774c53099c06f67cc2b690587bb491210448488527  2026-11-11/binarios_git/textures/concordia/polyhaven_src/hessian_380/hessian_380_Metal_1k.jpg
      956823  a828755c5ddc9af0697eeed46427c5145df1dea5f1e2839f643156a285282fed  2026-11-11/binarios_git/textures/concordia/polyhaven_src/hessian_380/hessian_380_Rough_1k.jpg
     1076074  3994fd74148cb413892edd08155976497b3e7e15a403a182f07325a6b1e7be1a  2026-11-11/binarios_git/textures/concordia/polyhaven_src/hessian_380/hessian_380_nor_gl_1k.jpg
      999921  e0d535b591430f1ebfd8ffa38086949bb074ae470f6fec7f3dcd55f594f52d4e  2026-11-11/binarios_git/textures/concordia/polyhaven_src/marble_01/marble_01_AO_2k.jpg
     1269188  d403786171716f86718bdd67eba923d4fb6125c0636bacef0e6a21dd5d623a48  2026-11-11/binarios_git/textures/concordia/polyhaven_src/marble_01/marble_01_Diffuse_2k.jpg
      281388  1b970e033856c93ee7390d947da5340e101b489fc8c1463354ea9e6655ce039a  2026-11-11/binarios_git/textures/concordia/polyhaven_src/marble_01/marble_01_Rough_2k.jpg
      409581  d5e17ccb2913adbf28fcb781fddf0aa711259ddea6c1c918442f9a3589aa4660  2026-11-11/binarios_git/textures/concordia/polyhaven_src/marble_01/marble_01_nor_gl_2k.jpg
      208277  031142984b8deb259203d1998e737de37ee571833ae80e5c05e0add3c5b2b86e  2026-11-11/binarios_git/textures/concordia/polyhaven_src/metal_plate_02/metal_plate_02_AO_1k.jpg
      625917  6e80877d0e9d5973d96298c6091df7ace906b0a6760afc4f3592e4855f3f1d4c  2026-11-11/binarios_git/textures/concordia/polyhaven_src/metal_plate_02/metal_plate_02_Diffuse_1k.jpg
      551170  fb1b120a2be5887dfeebed7a198a8151b292e963713d914b74ed7669434afb41  2026-11-11/binarios_git/textures/concordia/polyhaven_src/metal_plate_02/metal_plate_02_Metal_1k.jpg
      911772  73a6bd6393f6de7be42058584c2d382f2a3e9148ceabc2d02e748e2c860e74d1  2026-11-11/binarios_git/textures/concordia/polyhaven_src/metal_plate_02/metal_plate_02_Rough_1k.jpg
      183264  58736fbb8aa4fc6690cf8152b174db65caf22a766375b625fb0087e1bc955bc7  2026-11-11/binarios_git/textures/concordia/polyhaven_src/metal_plate_02/metal_plate_02_nor_gl_1k.jpg
     1929334  b54912b313b8798d14b31bbbe5aa95f69458eee2e529333faf44aef18f979754  2026-11-11/binarios_git/textures/concordia/polyhaven_src/rock_boulder_cracked/rock_boulder_cracked_AO_2k.jpg
     3962095  d7010ebf5157dc707f4bb555c74f589e1b794a308c186f6de2271f3ad0ff0da4  2026-11-11/binarios_git/textures/concordia/polyhaven_src/rock_boulder_cracked/rock_boulder_cracked_Diffuse_2k.jpg
     1680734  511e9df71b8285149303278e1eed2bc70fdc6d7171ed7b3cbf4eefc171673b12  2026-11-11/binarios_git/textures/concordia/polyhaven_src/rock_boulder_cracked/rock_boulder_cracked_Rough_2k.jpg
     4144084  03a9815ebb58cc9ab5a59ab333f1bc50fa2539571aa6868bfb30d76b21601b30  2026-11-11/binarios_git/textures/concordia/polyhaven_src/rock_boulder_cracked/rock_boulder_cracked_nor_gl_2k.jpg
     2182922  cc27725b9bd4b3482823ced876ea5a4ff4cef8485a8193f6f071b56a3a2bb14d  2026-11-11/binarios_git/textures/concordia/polyhaven_src/rock_boulder_dry/rock_boulder_dry_AO_2k.jpg
     3437626  c66de7f7b48ef1ba542c17af780787ca6d43da2160a46ff3544dd9fcdf65ca30  2026-11-11/binarios_git/textures/concordia/polyhaven_src/rock_boulder_dry/rock_boulder_dry_Diffuse_2k.jpg
     2706723  63bb4105e6f60b5968da785afc292b94026a5afa6f18388e98b00232e9e2c433  2026-11-11/binarios_git/textures/concordia/polyhaven_src/rock_boulder_dry/rock_boulder_dry_Rough_2k.jpg
     3307320  72a3c96d563fc17ac36c568802e106222e6480512d98e07318e1f431cea33dd6  2026-11-11/binarios_git/textures/concordia/polyhaven_src/rock_boulder_dry/rock_boulder_dry_nor_gl_2k.jpg
     2168833  1c371f4fd1a2538fd8a686384fcbc669736c6f556fb60858aa80be0344abf79c  2026-11-11/binarios_git/textures/concordia/polyhaven_src/rocks_ground_02/rocks_ground_02_AO_2k.jpg
     3224700  a2a4fc4e10a307ca6e345e0df50d6115ba1058174de915bfcfdd5ff3f49dc2fa  2026-11-11/binarios_git/textures/concordia/polyhaven_src/rocks_ground_02/rocks_ground_02_Diffuse_2k.jpg
     1810785  c5b54993717852963382876bd0558c831af389b00a2dbd40317c51ff8b9c0817  2026-11-11/binarios_git/textures/concordia/polyhaven_src/rocks_ground_02/rocks_ground_02_Rough_2k.jpg
     5387529  bde35636a0c548e57006917287e067d11abf3bfac2d70373162deb171ca9a4ef  2026-11-11/binarios_git/textures/concordia/polyhaven_src/rocks_ground_02/rocks_ground_02_nor_gl_2k.jpg
      137405  081bab7e0a772cecc9dba0ab71ebf98a9e0f72465e150ccc7ce885980a61bc38  2026-11-11/binarios_git/textures/concordia/polyhaven_src/roof_09/roof_09_AO_1k.jpg
      553309  6baaf5dca30d14566791ad6603e3b3dbd69b76990fd8d1314efc35dd2655e818  2026-11-11/binarios_git/textures/concordia/polyhaven_src/roof_09/roof_09_Diffuse_1k.jpg
      503295  82ebb728f9e128202b9f03f2be4589331c02517a86b6921002af203b20fef124  2026-11-11/binarios_git/textures/concordia/polyhaven_src/roof_09/roof_09_Rough_1k.jpg
      325412  60fc61343316bbe73399cdddfb3da8b47d41c2d147e2b3384f244f8be9ed1668  2026-11-11/binarios_git/textures/concordia/polyhaven_src/roof_09/roof_09_nor_gl_1k.jpg
     2254805  e02ec83fd03719903a7660d5d30d01794997390d01c95c4da685ecf6607b5770  2026-11-11/binarios_git/textures/concordia/polyhaven_src/rustic_stone_wall/rustic_stone_wall_AO_2k.jpg
     3525377  7f562fdf6b685e15a736f18b34b8f435f04a1065d2734a85ea1b9d9847f860dc  2026-11-11/binarios_git/textures/concordia/polyhaven_src/rustic_stone_wall/rustic_stone_wall_Diffuse_2k.jpg
     2649266  517a3d1bc589313b849e8ddf46c0256f17edde11f81d553bbd46f8bbd345b3c7  2026-11-11/binarios_git/textures/concordia/polyhaven_src/rustic_stone_wall/rustic_stone_wall_Rough_2k.jpg
     4739942  9367541088efd9e60752f9de400a719fa811bb7bb6334e6be2df3e9af7534847  2026-11-11/binarios_git/textures/concordia/polyhaven_src/rustic_stone_wall/rustic_stone_wall_nor_gl_2k.jpg
     2043727  a58ec86af4beb8c0e6ae1572a02fda97e3f23b768c8da47b0ae6a368de22ddd9  2026-11-11/binarios_git/textures/concordia/polyhaven_src/sandstone_cracks/sandstone_cracks_AO_2k.jpg
     2870078  6d3f99604c85a818277150db784ac66e67a4d91ddc255dabf61b3e956564090d  2026-11-11/binarios_git/textures/concordia/polyhaven_src/sandstone_cracks/sandstone_cracks_Diffuse_2k.jpg
     1569280  45347870225f1f1b223968e8fc0ac2125374c0b1e0907cda7ad93b1c5dda39f4  2026-11-11/binarios_git/textures/concordia/polyhaven_src/sandstone_cracks/sandstone_cracks_Rough_2k.jpg
     4545235  904e852268e1fb1bd5c0d035382f6a0e64c98dceea784fe957b1983d98b0231a  2026-11-11/binarios_git/textures/concordia/polyhaven_src/sandstone_cracks/sandstone_cracks_nor_gl_2k.jpg
     2730634  f1d516dbb9e55ebe33f5a1bac3a202dd7ac500e92e14cde8151a2cc79d8179de  2026-11-11/binarios_git/textures/concordia/polyhaven_src/stone_wall_02/stone_wall_02_AO_2k.jpg
     2554296  0b84bf19acc263bbb52071317de12a7fafcc0ffa95dd585fb4dfa33dcbed0e1d  2026-11-11/binarios_git/textures/concordia/polyhaven_src/stone_wall_02/stone_wall_02_Diffuse_2k.jpg
     1215515  83e849a0a2fb11c77b682014b228a18d0392801fba951e58db8dddaedd1ff31b  2026-11-11/binarios_git/textures/concordia/polyhaven_src/stone_wall_02/stone_wall_02_Rough_2k.jpg
     3715793  f7b684c229f2e80100b700dcf41df312c345b13e4345f1db24a8dcfe5bb81f72  2026-11-11/binarios_git/textures/concordia/polyhaven_src/stone_wall_02/stone_wall_02_nor_gl_2k.jpg
      594177  a4ff0df66640229e315f75637a135622504094cf4d6d57c6cca4dacf619b1a5b  2026-11-11/binarios_git/textures/concordia/polyhaven_src/weathered_planks/weathered_planks_AO_1k.jpg
      599581  01c9a372cfd7a7bf471b59c2458ed3ccecc93448aebf7ba0cc5b3b5b6ed24349  2026-11-11/binarios_git/textures/concordia/polyhaven_src/weathered_planks/weathered_planks_Diffuse_1k.jpg
      218802  a017728183597417a350d1846a5a46db9702ee6d472a21c5da2f23015d606aa3  2026-11-11/binarios_git/textures/concordia/polyhaven_src/weathered_planks/weathered_planks_Rough_1k.jpg
      681552  381d298f3194ec4961b04b4912b9b6efea4b2ff7b914dac57e24c8b6b0be6a25  2026-11-11/binarios_git/textures/concordia/polyhaven_src/weathered_planks/weathered_planks_nor_gl_1k.jpg
    77936948  e1caf844e57a837c3d5bebcca72be3e792d29e22cca1c041e42fa0e88eaf4958  2026-11-11/concordia_master_2026-11-11_v28.blend
      673465  7acd32323950dd444ce20fdf75870dbfd6f414f9adf2d5e00180e844022bd58a  2026-11-11/concordia_moradas_int_v01.blend
     2756763  3bc2eebda91cc56576b3e66d031b1681a0abfce274efa61632d4f77e305a0a83  2026-11-11/concordia_props_v01.blend
       46060  5e62a5d472c80ca07847c1cbb80c0a2466e992b9d38ab5b5cc9fd8f097d79269  2026-11-11/fuentes_assets/avramania/0be8094364f4482f9ddad92236514b96/model.glb
       76512  9235d8ff9d967c3172cdbd92b85fc2451daca34ee4e6c5be421e1c6ccb5ddffd  2026-11-11/fuentes_assets/avramania/0daff83382444c95b022de235cea1ceb/model.glb
       49944  8c6ec6fdd3de5a048a256378bbb41c3411da6ed50a3e880329440ae21c9e5fc9  2026-11-11/fuentes_assets/avramania/1b9b17a3cb0f44dd9141e70fba061c71/model.glb
       88564  c69f07a765d99aa27664d592abc1ce4cf23d02ba5755305ab3b11885a1ee092b  2026-11-11/fuentes_assets/avramania/24704040010a42ceaeffb1631ed1ae9b/model.glb
      111024  9e7de119210da89c2646b71bd8a41e5dcc7b3ec17ac62dbfd9f682c78c9c4080  2026-11-11/fuentes_assets/avramania/2ba720b8921543b69edad075b9d7c5c5/model.glb
       24488  6c481869ef57133383a3e21f39cc99ecdea80360e6e8f9bc5ffc97fe6ad01bf5  2026-11-11/fuentes_assets/avramania/34e64ec1bab74f3b921d3078cecd06dc/model.glb
       43232  89e9058f1a6c3deaaaaa10653944ac1394a7844b113ca98297a0df3440057493  2026-11-11/fuentes_assets/avramania/3899142ec92c46059d35fc0fa1a0bd41/model.glb
       58704  287e58f40655fdd5b532e189f37b8cc0559ddfc4104eb54e12f8724722b2c16b  2026-11-11/fuentes_assets/avramania/3b71fc881aaf4602ad53605474baf0ff/model.glb
       37600  ff7259bc1ef0ba2b0d5499e31c3ab6514c6fcf4984670b0c0b8c334f5604b85e  2026-11-11/fuentes_assets/avramania/3ced62581eb84f9a914cb1d120d2d519/model.glb
       33320  0d465cb01a0ef97677f20418f2ae02bc4f0a69c683abb46eb24c318921ea38b1  2026-11-11/fuentes_assets/avramania/3f3b24dd3bf24ce49b518bfbd5ec93df/model.glb
       55764  e9b63ac77edcc89140cde8766229eccb87cb1caf686f3f98a9b06b51b3b451b2  2026-11-11/fuentes_assets/avramania/41ec7f9ddd8c4e999449b5e746790fe4/model.glb
       37672  9344ad50776d0bc203ee9a92a962d4c71b114b44fc5bd38386a068fc185a5e02  2026-11-11/fuentes_assets/avramania/64e25ccc90c84e3b8c2ad02dd39150ba/model.glb
       40920  7b1c091f285eb020b35475b5605d5e29f026403016e1c6db14532b10e1d3f12e  2026-11-11/fuentes_assets/avramania/78265b91861e406ea62acaa67b78d60b/model.glb
       18168  96905d3d3f626aec9784577d3c892e7a258591013e962ab1d1c776e2ed9beb48  2026-11-11/fuentes_assets/avramania/7aa298b830fc4d6eafa1980adfe0f5cf/model.glb
       76520  021ef05dbbbc02d92414163872ecda4bc2fae3baf605d93e69fae056cd6aec7c  2026-11-11/fuentes_assets/avramania/7db2a14529fd4e1f9391c68337f71eac/model.glb
       29088  5b2a19423da072f57e08a098cee57e339908886c71cf953a8335d7ef81b4eae0  2026-11-11/fuentes_assets/avramania/7decd7f6750644fab34f3f54cd9a6a89/model.glb
       72320  08e4a248f1c967e10699403cfbe0a26daaccb08854dec1b5eb30c737f516e7f3  2026-11-11/fuentes_assets/avramania/82f2cac9741c467c844c9c5b62ab6050/model.glb
       41272  3dde865315b3513f21c5ea216c061040055c77a820dcc472c2290f1a7385145c  2026-11-11/fuentes_assets/avramania/8a3dc887ea9d48c19ad48469ba11e753/model.glb
       55996  c4bf7aee605e8257516fc405109f1a285eb6642f748f8d6e97d9041588169854  2026-11-11/fuentes_assets/avramania/94a5f575c311487b8fbd6091b09abd94/model.glb
       19360  6cf3ccb3ec10e7898fd3601b7f656a5f15736cde20c3a6ddd3751b9227b411bc  2026-11-11/fuentes_assets/avramania/9cd0c6d36336456e86c2a79e968e47b6/model.glb
       35432  4ea2245978da1030bcbec184e8c2b52429eab390cd87c955eb665f1712a1e1b9  2026-11-11/fuentes_assets/avramania/a8a9568469524a548ca730b1058de3ef/model.glb
       88788  db9a357a03ebecd5c3bc6ed7357a836e79267ec8239a3313e287dcea7a9cacf8  2026-11-11/fuentes_assets/avramania/b0f1cb5493bd4af8a829c49816a1cf79/model.glb
       24436  4ddb20f511f895dd816aea172e92357ea5dfbb12e07feede8e0f0e16a19e6623  2026-11-11/fuentes_assets/avramania/b5ee3e7fbb0049059bf23a6724eebc1b/model.glb
       29800  de6c833cfffce40738ab4c3adf93b14893c21eaafa4da602df8ad26704a05972  2026-11-11/fuentes_assets/avramania/b8142e327147499a83add0dfcb1a32d9/model.glb
       57548  2b50e3f48a32719825c568ea13396b58fceff83f5b4acd197f081c4ad2408113  2026-11-11/fuentes_assets/avramania/b935b180c92c4fe79c067113d8929cb4/model.glb
       86968  f7c9b0642bfd1850630a0daf861365c91102cada81a49df2f7050d508ed53110  2026-11-11/fuentes_assets/avramania/ba2de923a54547beaddc1f49e000b3d3/model.glb
       42040  f74129287ad6a6313bbdb06da51a1cad95408657a29e3b3a9246f5b52f1d1fed  2026-11-11/fuentes_assets/avramania/bd0ad320c35249b9b1a37e2adc061bb9/model.glb
       78340  31c3386a28be3257d31d244866c2c0fd61de13c026a7f4beb98094780b2fc405  2026-11-11/fuentes_assets/avramania/c66175e51d044dfda9e6edff21d4d38a/model.glb
       15572  8613d8eecf8c44501749d701fce5506713aa5839bb7ce408c0afb223a5b0f193  2026-11-11/fuentes_assets/avramania/cc820300ee694dd5aae898a87ccc6c67/model.glb
       78016  e51dc10cee8108d8ea06d7d2524e6029cd2f0b1651441f024da486b1f1d26cc4  2026-11-11/fuentes_assets/avramania/cc950686a4dc4ac89edda92b21afca11/model.glb
       75448  af42cf3243f3e801346f0246755d9eca1c1f93315bab0619d03bcee1a2849b0c  2026-11-11/fuentes_assets/avramania/d041cc0462ab4da6be30fff811765685/model.glb
       62224  a68d0874061a5a7d7c424e7e131799a77dae1c1f79aa373d9e3668d589930b9b  2026-11-11/fuentes_assets/avramania/e06f39a8521d4a728f6de1a399e2097a/model.glb
      153328  77cd275807f153ae4c3c2057797627bf0a474f9652cb3d2e462c0d2e8f60dee4  2026-11-11/fuentes_assets/avramania/eb4311e2df0549d5a5a26edc313c38c4/model.glb
       40560  16f5444d9fdc9d84762fd6e317b8d3f4a5758a472f28a40139c3dd64f406e7cc  2026-11-11/fuentes_assets/avramania/f12b9a6915a34c59bf4ea3d5634a03f5/model.glb
       41424  a30b94ed11e381abe58daf5bce4ab1f25ab84c05c566be92b10b84f8cd99d854  2026-11-11/fuentes_assets/avramania/fa90afdde3e541458de26d42e1323d7d/model.glb
       31524  80b7ba7e06d779c8a679a6fbbba3105563f1fd815414a507e8d6bcbfe028d06e  2026-11-11/fuentes_assets/avramania/fe8f28bcadaf44a7836e12fe30f9a3dd/model.glb
       22263  275ad13cf3f67421a6ffcafe4cbd356f42e082dd48842af224c9cca1ab4c03bc  2026-11-11/fuentes_assets/avramania/licenses.json
    45956992  c075b3e9b94b8e5556a5f03f4653602d02ea306de08126e8f55ed6dee28a2dad  2026-11-11/fuentes_assets/mpfb/add-on-mpfb-v2.0.18.zip
   280737770  b542127a8e25547c7c29c19f2d1d2adb9a664c80396ecd694095dbc8028a0107  2026-11-11/fuentes_assets/mpfb/makehuman_system_assets_cc0.zip
    73727082  0bc1e5843c9f245c44bda82f97f738b09f88fe51bb34d2a69a7847a969f868e3  2026-11-11/fuentes_assets/quaternius_fantasy_props_megakitstandard.zip
      946072  199cb545ca497f7c7755066bc9933b5d3544412497f560e2da3239f71e42f935  2026-11-11/glb/int_morada_casa_grande.glb
      728004  3b9c1a87b92a6026fa153457a0eeab911c7c94b1052ff1b74325e90b6c7264d0  2026-11-11/glb/int_morada_casa_pequena.glb
      424468  ca8b1c1f2c0f7130a6616ddf10b41c4600751d34055fc55e19222cd4c03b6a94  2026-11-11/glb/int_morada_habitacion.glb
     1205616  fbb3477afa6128e6304f61e2a1e9627f12643f216d3f01ffe331ac6120e3c03d  2026-11-11/glb/pj_elfo_cuerpo.glb
     3734100  431e466ebc24a5dc46afb214ca5fd1bb7c638aeac21f8cf0203d7f3afef2b54a  2026-11-11/glb/pj_elfo_rig.glb
     3169772  8294234e006d52383d35856cc62652805d492234aa7505f68dae97fea4d3202d  2026-11-11/glb/pj_elfo_sanador_equipado.glb
     2001628  fac899ebd67059cc2e149b50432088700e597f565b027c9dea4d410a06ccf830  2026-11-11/glb/pj_sanador_ropa.glb
     1204760  bda2062b4738d185dfc46f1adb5ad1418b72d44c98e47a610391465eb715a952  2026-11-11/glb/props_int_clases.glb
      442880  b85f07a83712df13834d7243a57d7e9627df5444bf15ebaae306b0782d1e68ff  2026-11-11/glb/props_int_mano.glb
     2441900  36fd587dfbecc8ad06d1200ed1bf98c674383a5652fbb711f1ac590ecbf472c3  2026-11-11/glb/props_int_mercado.glb
     2006716  45674efc69e58624f8b490561dc1364d889266b040c59a77aeada5cac681888a  2026-11-11/glb/props_int_oficios.glb
       70708  ded9ce2d6f997c4d4c4aeea5bde72047e274816ff14283a732762356429fc243  2026-11-11/glb/props_trophy_cases.glb
     1472936  9f62e00250091b97743a90d1ba999fff96564d74a028e0cf00e18343ed338b03  2026-11-11/personajes/capturas/pj1_cara.png
      825967  5716901d8c866f9aa822fd295facdf6f456a5eec04bc06f4712eb36d9bd2d9ba  2026-11-11/personajes/capturas/pj1_iso.png
      848379  c5eac7b6a714a1240644bc92fa356c44b91acad7ceb5c83916ca2443851d78c5  2026-11-11/personajes/capturas/pj1_piezas.png
      467902  43a881d15f2d4c501f600efaffbd14c7090b59e523a01e4923a45b3530aace0e  2026-11-11/personajes/capturas/pj1_texturas.png
     1067969  b0f81d8ab063b3bcdb70143333764bde9fd39d1b0a7dadde5a54e05b9de8d484  2026-11-11/personajes/capturas/pj1_tpose.png
      770203  0cef817c373f682b5bb1e563d05fbbf947b64ca49b57fa82c9aa5bd6d0c56e68  2026-11-11/personajes/capturas/pj2_atlas.png
     2151875  6f40219bbcce5b339f690dfd254a55a6694faa37913b5bb5f7c478dc005f58b4  2026-11-11/personajes/capturas/pj2_detalle.png
      893213  b0be40a60315f18d9e8602af85a9c60bdea03ff1f1e09c93ef092e71c73657d7  2026-11-11/personajes/capturas/pj2_iso.png
     1359054  398aa866fe7c4dabf6ae748b9fdd7840a53f6a1ee133959378eca8c4d0592b4d  2026-11-11/personajes/capturas/pj2_ocultar.png
     1451550  89056ed16094a136f774cbf107137e42c6ac91d0f4e481a348da1214bef2d2f8  2026-11-11/personajes/capturas/pj2_tpose.png
     1430751  170ee5a9a491802e9cb7e7c9c79f5a7b8701fc9f59833cd9df52503761555182  2026-11-11/personajes/capturas/pj3_articulaciones.png
      816136  25f5d23627a1f40fdb1923e14ddf4bb6c3a53142e8ce1ce81e043b5350fb93ee  2026-11-11/personajes/capturas/pj3_esqueleto.png
     1624383  e47f2f9fd6eb5d5e15c747d22795ebec722d4957acf69d87f7d17abc28ac863f  2026-11-11/personajes/capturas/pj3_poses_cuerpo.png
     2107296  255e803619f56842d696fcb5d3721c1a842d80bce67748baf4a7cee32a18a69b  2026-11-11/personajes/capturas/pj3_poses_ropa.png
     3422225  90987ee9f4585fcfdf42750841ee1e7667ed5d07299f845ead7ed75c84bac991  2026-11-11/personajes/elfo_v01.blend
     3895747  a23ce648c7f6586b6b463b141ffa787b0c51b8eda4e31092ba659753c01ea580  2026-11-11/personajes/elfo_v02.blend
     5725070  68b6bdba48718d7139e95feb66812c6a8c0e44bbcfe4c810097887d5442943a2  2026-11-11/personajes/elfo_v03.blend
      246339  8a8541c43fc9d89a3890fcde34857a06383bfa8d4aba5f62b14759bdbb312c0e  2026-11-11/personajes/textures/elfo_m_albedo_abedul_1k.png
      192224  340691269799321022f4d561f713e7553329c59f36083271b2fbca11a0fa9380  2026-11-11/personajes/textures/elfo_m_albedo_corteza_1k.png
      572828  a874f4d548118aa9f9486541e220f4578d5c08576c9d76fd0a3ca9fbe5d44289  2026-11-11/personajes/textures/elfo_m_normal_1k.png
        9635  12bdc8ba1e79f7b6d556976bd4f66d3ecdf65bac4765ee1cf470a802a3a1026f  2026-11-11/personajes/textures/elfo_m_ojos_albedo_256.png
      271424  1e77fb87f2395dea48ca9d7a80104bcd917584dcd0cfd57ea3c8c1eaffc97392  2026-11-11/personajes/textures/elfo_m_orm_1k.png
      714898  4fda9dc2b34e079059cb89c0f2e4b0f824ff0cbd268305bb978adddb9df64c40  2026-11-11/personajes/textures_sanador/sanador_atlas_albedo_1k.png
        3317  f599d4ccc7d76bad7937862890474bcebb199e889ffc2bce1573052290d353a8  2026-11-11/personajes/textures_sanador/sanador_atlas_emision_1k.png
      732703  10c83a69bd191ff5c044ff110bc48048080f66e4c4a46b8b765b55b028415181  2026-11-11/personajes/textures_sanador/sanador_atlas_normal_1k.png
      400653  8b41ebcb4b6b3917fef9bfe7c7ed2144504d7707c6adf980d66aa6def64aced8  2026-11-11/personajes/textures_sanador/sanador_atlas_orm_1k.png
        3229  320e5247d2cfe136d96ac80dae24f217c60fba7b498d36c8f2749a63976961e0  2026-11-11/personajes_pj5/MANIFEST.txt
       14256  b0d6bd4554d17831ad43f04c9222193df3fef4f0eebc84635ab07e077de6dc4f  2026-11-11/personajes_pj5/README_personaje.txt
       15866  8d0babc2e7ff37607bac18d6a7516a1ffba6e88729b1bb3955d6d875c9d438aa  2026-11-11/personajes_pj5/TODO_GODOT_personaje.txt
     8212958  d13fb953267f9fecca323522186abd6014881cf7852b502dafd52cbc2734fbc6  2026-11-11/personajes_pj5/concordia_personajes_master_2026-11-11_v1.0.blend
      276116  e9cb42a2b8a2184940981d764d6cff9e2a0b8c0d8b0b7f5cf3181e3344906ab6  2026-11-11/personajes_pj5/glb/elfo_sanador_anims.glb
     1953636  8b511f71bae9be9af06a01922438094c5ecfa5434401e97683dd59bab4117f3f  2026-11-11/personajes_pj5/glb/elfo_sanador_belt.glb
     1918624  d299c33901794970ed91616c1e8b95d318b6cf2642d70ded5d06b10a9fb5a661  2026-11-11/personajes_pj5/glb/elfo_sanador_boots.glb
     1901020  eade452c017123022a19038d0f9c379176537caafbc967b6b852e498ef19b8b4  2026-11-11/personajes_pj5/glb/elfo_sanador_bracers.glb
     1947912  e5ecef35a5d42b6a84d1482b720a5f36f11debb4859b1d95c5647fc8f3adb6cb  2026-11-11/personajes_pj5/glb/elfo_sanador_hood.glb
     3097444  d805c86fa9d963e3b4e013a1b265197b14b2b0e1a18790f220624ff069e262c1  2026-11-11/personajes_pj5/glb/elfo_sanador_lod2.glb
     1950640  2ddf94dfabac999af562efbe43f1b060f8660bc26f7dcb5834cf06d0a79da963  2026-11-11/personajes_pj5/glb/elfo_sanador_robe_top.glb
     1951464  3a004e5655e09be01fd19a2eec0aed4aa1cc3529ebc0517244f7acb4f91b98f8  2026-11-11/personajes_pj5/glb/elfo_sanador_skirt.glb
     3274816  d71ab8025c7c9d14d57a0dc17b4ab1efcc2eb23669e137cf314a19ea207eaa61  2026-11-11/personajes_pj5/glb/personaje_elfo_base.glb
        3790  c5219de481c7d90e53576adc387b79975d6b8ec37ae9aed8a5c2e2e70955a80f  2026-11-11/personajes_pj5/pj5_lods.json
      246339  8a8541c43fc9d89a3890fcde34857a06383bfa8d4aba5f62b14759bdbb312c0e  2026-11-11/personajes_pj5/texturas/elfo_m_albedo_abedul_1k.png
      192224  340691269799321022f4d561f713e7553329c59f36083271b2fbca11a0fa9380  2026-11-11/personajes_pj5/texturas/elfo_m_albedo_corteza_1k.png
      572828  a874f4d548118aa9f9486541e220f4578d5c08576c9d76fd0a3ca9fbe5d44289  2026-11-11/personajes_pj5/texturas/elfo_m_normal_1k.png
        9635  12bdc8ba1e79f7b6d556976bd4f66d3ecdf65bac4765ee1cf470a802a3a1026f  2026-11-11/personajes_pj5/texturas/elfo_m_ojos_albedo_256.png
      271424  1e77fb87f2395dea48ca9d7a80104bcd917584dcd0cfd57ea3c8c1eaffc97392  2026-11-11/personajes_pj5/texturas/elfo_m_orm_1k.png
      714898  4fda9dc2b34e079059cb89c0f2e4b0f824ff0cbd268305bb978adddb9df64c40  2026-11-11/personajes_pj5/texturas/sanador_atlas_albedo_1k.png
        3317  f599d4ccc7d76bad7937862890474bcebb199e889ffc2bce1573052290d353a8  2026-11-11/personajes_pj5/texturas/sanador_atlas_emision_1k.png
      732703  10c83a69bd191ff5c044ff110bc48048080f66e4c4a46b8b765b55b028415181  2026-11-11/personajes_pj5/texturas/sanador_atlas_normal_1k.png
      400653  8b41ebcb4b6b3917fef9bfe7c7ed2144504d7707c6adf980d66aa6def64aced8  2026-11-11/personajes_pj5/texturas/sanador_atlas_orm_1k.png
     1625276  d893d848c59d28f7352014eda985958911b0fa56844c8eddc80e39c1c6e87a3a  2026-11-11/personajes_pj5/ual/sanador_ual1_seleccion.glb
     1169564  740a0f5f6f129172631938c1630bb725d940f096ba331ee56fb82cefa829728a  2026-11-11/personajes_pj5/ual/sanador_ual2_seleccion.glb
      225986  8bfd8ec5347f15ad083bdd9de9d5d79e63439e2f77739a9d0a59e15d2287d4c1  2026-11-11/textures/PROP_AV_Cheese_Wheel_normal_512.png
      208829  5556477cc00b35a7cce65dafcf35d692931d1c10fd078408a176cef3aa1b19db  2026-11-11/textures/PROP_AV_Grain_Sack_normal_512.png
      329735  d9739ffd1cd0e298bd844698a41b595ad696faaf36f96ed499b34cc8c03b8fbf  2026-11-11/textures/PROP_AV_Grapes_normal_512.png
      198801  f863f21822e77602219a6e33f38283b34d695cb0822e70b8c2b4a1fdd3e69463  2026-11-11/textures/PROP_AV_Handaxe_normal_512.png
      134607  39e13b802ba8e5d7e2dd13eda733ca9c64031e0fc293109e8a48f8332bb64a7e  2026-11-11/textures/PROP_AV_Herb_Bundle_normal_512.png
      535399  8934f9eb784ed0ec2fc5f0fbb109ce8a9fb92101abe24790d9d3bc23c26de3ad  2026-11-11/textures/PROP_Q_Barrel_Holder_normal_1k.png
      771881  db991bb570ed949e3059234ee397b64563ef2e39b1ec0e0bfac7ac7d68ce1627  2026-11-11/textures/PROP_Q_BookStand_normal_1k.png
      270021  6eebf5b2e02d4efc1001d2288fe19f3fa0e0f38207094a62098e32fed8063988  2026-11-11/textures/PROP_Q_Bucket_Wooden_1_normal_512.png
      124185  fd8ddc548809f5abcf407ec88c3c159b394297aee1ebde81c9e1596821e3f589  2026-11-11/textures/PROP_Q_CandleStick_normal_512.png
      668103  e0458e602d766724537cce246110421639712d99a97b94c90817b59ce4ef18c6  2026-11-11/textures/PROP_Q_Chain_Coil_normal_1k.png
      645973  3a8179427079963943fd9a491ba65b334cdbdff259cf477dbbf976959655a094  2026-11-11/textures/PROP_Q_Chandelier_normal_1k.png
      399570  39b52fb632c8a9a65242bf4a5ec649f4e9fa2aa9d60013fecff8c28356a00239  2026-11-11/textures/PROP_Q_Chest_Wood_normal_1k.png
      214385  bb566a7e0225867c8ec3c89e1eeb8a27cb73d3deab4de0770c521a549a2df50d  2026-11-11/textures/PROP_Q_Coin_Pile_normal_512.png
      363280  4c0c05a97c2220fda0be7b4c4d09e426d4efff1f5d48ef64ef6b45f3777eb123  2026-11-11/textures/PROP_Q_Potion_4_normal_512.png
      421577  a115fcd19d32ad1d634a5e8c3a829a338a9a1b0fa8ab520d3bb385e15e4eecbb  2026-11-11/textures/PROP_Q_Pouch_Large_normal_512.png
      425540  3403b94e2856d43fc514c276cf3690c25ca2904b933cefb3dc97fb90452663c9  2026-11-11/textures/PROP_Q_Scroll_1_normal_512.png
      435197  a7909ce95b126bf6c39428f8ff8fde82606d6b7b3e2265664c48a162ad549076  2026-11-11/textures/PROP_Q_Scroll_2_normal_512.png
      772159  cd1a5382da65cca5b693dd09972c47b6e2385871cf5c8413e755a8f0310906b4  2026-11-11/textures/PROP_Q_WeaponStand_normal_1k.png
      290103  b43e85d44132548af1e19c707b769b1e6d8e864448444d2f66da7ce84329fe60  2026-11-11/textures/trophy_case_atlas_512.png
    10257419  ec0e40d6d78fe9aaad59e322f40865a8675c22f0745e291622e54520391a9217  2026-11-11/ual_original/universal_animation_library_2standard.zip
    14541205  18ff1a7215f4852b320203e8aaf02a1578b5c8eef9027fbaedfcedc7b85a3ac2  2026-11-11/ual_original/universal_animation_librarystandard.zip

Total: 278 archivos, 984,658,615 bytes (939.0 MiB)
      986756  8d75305ec88bb270082279c6c983ff111b1392c577fd2ff873fd5b91c4757cb7  2026-11-12/interiores_e29/concordia_interiors_unicos_v01.blend
      768224  28173c9c1c49b49d7c53f120d45c7c9c8c5058761da7760e5377fd757ca0b981  2026-11-12/interiores_e29/int_santuario.glb
     1455876  6f554ecdf886404b7f94e7b35f5a44fdc7f96df33840385202efc70bebe2b964  2026-11-12/interiores_e29/int_tesoreria.glb
        5731  33f25017506536ba7330f4fab1c94611e8e311e57f6193e7806ee92b866e4420  2026-11-12/interiores_e29/stage29_santuario.json
       11128  8f06cbf4d885e09813215580afd82b80cfbe0ec759c7afe341aa4af6a2d2e8e4  2026-11-12/interiores_e29/stage29_tesoreria.json
       56190  2450488d2748d58563f651dde229b9634c27a982407052a8981cac84e924a8a3  2026-11-12/interiores_e29/vault_stars_1k.png
```


## Anexo L — Inventario completo de archivos en git (975 archivos, 2.84 GB)

Tamaño en bytes. Fuera de git (solo en el contenedor o regenerables): `respaldo/` (944 MB salvo MANIFEST), `*.blend1`, `godot_concordia/assets/` (copias), `godot_concordia/world/` y `.godot/` (se regeneran).

| Ruta | Bytes | Para qué sirve |
|---|---:|---|
| `.gitattributes` | 41 | documentación / configuración |
| `.gitignore` | 320 | documentación / configuración |
| `ASSETS_LICENSES.md` | 42,301 | documentación / configuración |
| `README_buildings.txt` | 71,968 | documentación / configuración |
| `README_markers.txt` | 3,793 | documentación / configuración |
| `README_masks.txt` | 4,325 | documentación / configuración |
| `README_personaje.txt` | 14,256 | documentación / configuración |
| `README_personajes.txt` | 13,395 | documentación / configuración |
| `TODO_GODOT.txt` | 29,214 | documentación / configuración |
| `TODO_GODOT_personaje.txt` | 15,866 | documentación / configuración |
| `animations/ual/sanador_ual1_seleccion.glb` | 1,625,276 | animaciones UAL (Quaternius CC0) / selección del Sanador |
| `animations/ual/sanador_ual2_seleccion.glb` | 1,169,564 | animaciones UAL (Quaternius CC0) / selección del Sanador |
| `animations/ual/ual1/AnimationLibrary_Godot_Standard.glb` | 6,671,104 | animaciones UAL (Quaternius CC0) / selección del Sanador |
| `animations/ual/ual1/License.txt` | 446 | animaciones UAL (Quaternius CC0) / selección del Sanador |
| `animations/ual/ual1/Preview.png` | 2,424,027 | animaciones UAL (Quaternius CC0) / selección del Sanador |
| `animations/ual/ual2/Godot_Setup.png` | 499,312 | animaciones UAL (Quaternius CC0) / selección del Sanador |
| `animations/ual/ual2/License.txt` | 541 | animaciones UAL (Quaternius CC0) / selección del Sanador |
| `animations/ual/ual2/Mannequin_F.glb` | 1,442,824 | animaciones UAL (Quaternius CC0) / selección del Sanador |
| `animations/ual/ual2/UAL2_Standard.glb` | 8,061,600 | animaciones UAL (Quaternius CC0) / selección del Sanador |
| `blender/concordia_interiors_unicos_v01.blend` | 986,756 | interiores únicos: Tesorería y Santuario (etapa 29) |
| `blender/concordia_interiors_v01.blend` | 709,346 | kit BLD_INT_KIT + sala de prueba + Banco |
| `blender/concordia_master_v11.blend` | 66,208,574 | etapa 11: master preparado para Godot (chunks, LOD, colisión) |
| `blender/concordia_moradas_int_v01.blend` | 673,465 | vitrinas de trofeos + 3 plantillas de Moradas |
| `blender/concordia_personajes_master.blend` | 8,212,958 | personaje final (elfo Sanador, LOD0–2, animaciones) v1.0 |
| `blender/concordia_props_v01.blend` | 2,756,763 | props hechos a mano + importados CC0 |
| `blender/concordia_v01.blend` | 389,943 | ciudad etapa 01: escena base |
| `blender/concordia_v02.blend` | 27,881,813 | etapa 02: terreno de la colina |
| `blender/concordia_v03.blend` | 30,575,301 | etapa 03: Plaza del Portal |
| `blender/concordia_v04.blend` | 31,114,961 | etapa 04: muralla (kit) |
| `blender/concordia_v05.blend` | 44,069,345 | etapa 05: calles y parcelas |
| `blender/concordia_v06.blend` | 50,233,168 | etapa 06: Moradas (terreno) |
| `blender/concordia_v07.blend` | 51,913,680 | etapa 07: Cauce |
| `blender/concordia_v08.blend` | 60,223,692 | etapa 08: exterior de ceniza |
| `blender/concordia_v09.blend` | 62,264,610 | etapa 09: materiales |
| `blender/concordia_v10.blend` | 58,996,659 | etapa 10: texturas Poly Haven |
| `blender/concordia_v12.blend` | 66,468,461 | E0: kit de edificios |
| `blender/concordia_v13.blend` | 67,024,767 | E1: Portal |
| `blender/concordia_v14.blend` | 67,130,512 | E2: Obelisco |
| `blender/concordia_v15.blend` | 67,435,850 | E3: Faro |
| `blender/concordia_v16.blend` | 68,117,420 | E4: Santuario y Salón |
| `blender/concordia_v17.blend` | 68,219,103 | decisiones del Faro y pendientes A–E |
| `blender/concordia_v18.blend` | 69,997,881 | E5: Mercado |
| `blender/concordia_v19.blend` | 71,273,078 | E6: Oficios |
| `blender/concordia_v20.blend` | 72,991,385 | E7: Clases |
| `blender/concordia_v21.blend` | 75,440,096 | E8: Razas |
| `blender/concordia_v22.blend` | 75,938,104 | E9: conexiones |
| `blender/concordia_v23.blend` | 77,540,228 | E10: Moradas (viviendas) |
| `blender/concordia_v24.blend` | 77,559,506 | E11: verificación y export |
| `blender/concordia_v25.blend` | 77,596,872 | E12: decisiones (brasas, Cazadores, Razas, Faro) |
| `blender/concordia_v26.blend` | 77,872,912 | E13: decisiones (Moradas, tubos, Faro) |
| `blender/concordia_v28.blend` | 77,936,948 | ÚLTIMA ciudad (etapa 28: Moradas a 2 plantas, tubos, props colocados) |
| `blender/elfo_v01.blend` | 3,422,225 | PJ1 cuerpo base |
| `blender/elfo_v02.blend` | 3,895,747 | PJ2 cabello y ropa |
| `blender/elfo_v03.blend` | 5,725,070 | PJ3 esqueleto y pesos |
| `blender/elfo_v04.blend` | 7,012,964 | PJ4 animaciones |
| `docs/captures/pj1_cara.png` | 1,472,936 | captura (pj1): pj1_cara |
| `docs/captures/pj1_iso.png` | 825,967 | captura (pj1): pj1_iso |
| `docs/captures/pj1_piezas.png` | 848,379 | captura (pj1): pj1_piezas |
| `docs/captures/pj1_texturas.png` | 467,902 | captura (pj1): pj1_texturas |
| `docs/captures/pj1_tpose.png` | 1,067,969 | captura (pj1): pj1_tpose |
| `docs/captures/pj2_atlas.png` | 770,203 | captura (pj2): pj2_atlas |
| `docs/captures/pj2_detalle.png` | 2,151,875 | captura (pj2): pj2_detalle |
| `docs/captures/pj2_iso.png` | 893,213 | captura (pj2): pj2_iso |
| `docs/captures/pj2_ocultar.png` | 1,359,054 | captura (pj2): pj2_ocultar |
| `docs/captures/pj2_tpose.png` | 1,451,550 | captura (pj2): pj2_tpose |
| `docs/captures/pj3_articulaciones.png` | 1,430,751 | captura (pj3): pj3_articulaciones |
| `docs/captures/pj3_esqueleto.png` | 816,136 | captura (pj3): pj3_esqueleto |
| `docs/captures/pj3_poses_cuerpo.png` | 1,624,383 | captura (pj3): pj3_poses_cuerpo |
| `docs/captures/pj3_poses_ropa.png` | 2,107,296 | captura (pj3): pj3_poses_ropa |
| `docs/captures/pj4_Heal_Cast_Area.png` | 1,133,089 | captura (pj4): pj4_Heal_Cast_Area |
| `docs/captures/pj4_Heal_Cast_Single.png` | 1,033,524 | captura (pj4): pj4_Heal_Cast_Single |
| `docs/captures/pj4_Heal_Channel_loop.png` | 977,508 | captura (pj4): pj4_Heal_Channel_loop |
| `docs/captures/pj4_Revive.png` | 1,101,533 | captura (pj4): pj4_Revive |
| `docs/captures/pj4_animaciones.png` | 4,248,151 | captura (pj4): pj4_animaciones |
| `docs/captures/pj4_reposo_ual_vs_elfo.png` | 1,526,082 | captura (pj4): pj4_reposo_ual_vs_elfo |
| `docs/captures/pj4b_muertes_getup.png` | 860,664 | captura (pj4b): pj4b_muertes_getup |
| `docs/captures/pj5_lods.png` | 3,083,058 | captura (pj5): pj5_lods |
| `docs/captures/stage01_eye_gate_E.png` | 1,160,212 | captura (stage01): stage01_eye_gate_E |
| `docs/captures/stage01_iso_cam120.png` | 1,146,708 | captura (stage01): stage01_iso_cam120 |
| `docs/captures/stage01_iso_overview.png` | 1,217,368 | captura (stage01): stage01_iso_overview |
| `docs/captures/stage02_eye_escalinata_NE.png` | 1,239,276 | captura (stage02): stage02_eye_escalinata_NE |
| `docs/captures/stage02_eye_muro_lateral_NE.png` | 1,267,386 | captura (stage02): stage02_eye_muro_lateral_NE |
| `docs/captures/stage02_eye_plazoleta_N.png` | 1,176,431 | captura (stage02): stage02_eye_plazoleta_N |
| `docs/captures/stage02_iso45_Morada_NE.png` | 1,371,405 | captura (stage02): stage02_iso45_Morada_NE |
| `docs/captures/stage02_iso45_Morada_NW.png` | 1,409,253 | captura (stage02): stage02_iso45_Morada_NW |
| `docs/captures/stage02_iso45_Morada_SE.png` | 1,309,798 | captura (stage02): stage02_iso45_Morada_SE |
| `docs/captures/stage02_iso45_Morada_SW.png` | 1,369,823 | captura (stage02): stage02_iso45_Morada_SW |
| `docs/captures/stage02_iso_overview.png` | 1,478,779 | captura (stage02): stage02_iso_overview |
| `docs/captures/stage02_profile.png` | 169,513 | captura (stage02): stage02_profile |
| `docs/captures/stage02_top.png` | 1,540,694 | captura (stage02): stage02_top |
| `docs/captures/stage02_top_masks.png` | 1,374,086 | captura (stage02): stage02_top_masks |
| `docs/captures/stage03_eye_avenida_N.png` | 1,233,723 | captura (stage03): stage03_eye_avenida_N |
| `docs/captures/stage03_iso120.png` | 1,322,642 | captura (stage03): stage03_iso120 |
| `docs/captures/stage03_iso220_proxies.png` | 1,386,211 | captura (stage03): stage03_iso220_proxies |
| `docs/captures/stage03_masks.png` | 1,063,255 | captura (stage03): stage03_masks |
| `docs/captures/stage03_top.png` | 1,457,505 | captura (stage03): stage03_top |
| `docs/captures/stage04_cenital.png` | 2,217,341 | captura (stage04): stage04_cenital |
| `docs/captures/stage04_eye_desde_mirador_k18.png` | 2,163,441 | captura (stage04): stage04_eye_desde_mirador_k18 |
| `docs/captures/stage04_eye_desde_mirador_k18_anochecer.png` | 1,755,242 | captura (stage04): stage04_eye_desde_mirador_k18_anochecer |
| `docs/captures/stage04_eye_puerta_Alba_dentro.png` | 2,056,829 | captura (stage04): stage04_eye_puerta_Alba_dentro |
| `docs/captures/stage04_iso30_torre_puerta_camino.png` | 1,923,462 | captura (stage04): stage04_iso30_torre_puerta_camino |
| `docs/captures/stage04_iso45_mirador.png` | 1,797,301 | captura (stage04): stage04_iso45_mirador |
| `docs/captures/stage04_iso45_morada_NW_muralla.png` | 1,810,695 | captura (stage04): stage04_iso45_morada_NW_muralla |
| `docs/captures/stage04_iso50_torre_linterna_anochecer.png` | 1,592,683 | captura (stage04): stage04_iso50_torre_linterna_anochecer |
| `docs/captures/stage04_iso_overview.png` | 1,843,047 | captura (stage04): stage04_iso_overview |
| `docs/captures/stage04_iso_overview_anochecer.png` | 1,623,060 | captura (stage04): stage04_iso_overview_anochecer |
| `docs/captures/stage04_kit.png` | 2,148,588 | captura (stage04): stage04_kit |
| `docs/captures/stage04_materials_sheet.png` | 3,558,365 | captura (stage04): stage04_materials_sheet |
| `docs/captures/stage04_textures_preview.png` | 1,038,443 | captura (stage04): stage04_textures_preview |
| `docs/captures/stage05_cenital.png` | 3,606,831 | captura (stage05): stage05_cenital |
| `docs/captures/stage05_iso_Clases.png` | 2,075,193 | captura (stage05): stage05_iso_Clases |
| `docs/captures/stage05_iso_Mercado.png` | 2,163,658 | captura (stage05): stage05_iso_Mercado |
| `docs/captures/stage05_iso_Oficios.png` | 2,267,850 | captura (stage05): stage05_iso_Oficios |
| `docs/captures/stage05_iso_Razas.png` | 2,295,966 | captura (stage05): stage05_iso_Razas |
| `docs/captures/stage05_plan.png` | 66,363 | captura (stage05): stage05_plan |
| `docs/captures/stage06_cenital_moradas.png` | 3,357,921 | captura (stage06): stage06_cenital_moradas |
| `docs/captures/stage06_iso_NE.png` | 2,159,224 | captura (stage06): stage06_iso_NE |
| `docs/captures/stage06_iso_NO.png` | 1,891,060 | captura (stage06): stage06_iso_NO |
| `docs/captures/stage06_iso_SE.png` | 2,063,779 | captura (stage06): stage06_iso_SE |
| `docs/captures/stage06_iso_SE_puertas.png` | 1,614,915 | captura (stage06): stage06_iso_SE_puertas |
| `docs/captures/stage06_iso_SO.png` | 2,174,181 | captura (stage06): stage06_iso_SO |
| `docs/captures/stage07_cenital_cauce.png` | 3,315,748 | captura (stage07): stage07_cenital_cauce |
| `docs/captures/stage07_eye_cauce.png` | 1,769,389 | captura (stage07): stage07_eye_cauce |
| `docs/captures/stage07_iso_arco_razas.png` | 1,985,250 | captura (stage07): stage07_iso_arco_razas |
| `docs/captures/stage07_iso_arcos_razas.png` | 2,371,652 | captura (stage07): stage07_iso_arcos_razas |
| `docs/captures/stage07_iso_cauce_arco.png` | 1,834,335 | captura (stage07): stage07_iso_cauce_arco |
| `docs/captures/stage07_iso_cauce_detalle.png` | 1,612,447 | captura (stage07): stage07_iso_cauce_detalle |
| `docs/captures/stage07_iso_cauce_oficios.png` | 2,293,246 | captura (stage07): stage07_iso_cauce_oficios |
| `docs/captures/stage07_iso_cauce_rueda.png` | 1,876,798 | captura (stage07): stage07_iso_cauce_rueda |
| `docs/captures/stage07_iso_escalinata.png` | 1,621,954 | captura (stage07): stage07_iso_escalinata |
| `docs/captures/stage08_cenital_exterior.png` | 2,797,990 | captura (stage08): stage08_cenital_exterior |
| `docs/captures/stage08_eye_mirador_exterior.png` | 1,282,897 | captura (stage08): stage08_eye_mirador_exterior |
| `docs/captures/stage08_eye_mirador_k42.png` | 1,223,294 | captura (stage08): stage08_eye_mirador_k42 |
| `docs/captures/stage08_iso_overview_exterior.png` | 1,838,636 | captura (stage08): stage08_iso_overview_exterior |
| `docs/captures/stage08_iso_puerta_sin_salida.png` | 1,742,580 | captura (stage08): stage08_iso_puerta_sin_salida |
| `docs/captures/stage09_iso_ciudad.png` | 2,760,525 | captura (stage09): stage09_iso_ciudad |
| `docs/captures/stage09_iso_mercado.png` | 2,870,855 | captura (stage09): stage09_iso_mercado |
| `docs/captures/stage09_materiales_esferas.png` | 1,524,020 | captura (stage09): stage09_materiales_esferas |
| `docs/captures/stage10_iso_ciudad.png` | 2,085,117 | captura (stage10): stage10_iso_ciudad |
| `docs/captures/stage10_iso_exterior_sector.png` | 2,061,190 | captura (stage10): stage10_iso_exterior_sector |
| `docs/captures/stage10_iso_exterior_taludes.png` | 3,246,006 | captura (stage10): stage10_iso_exterior_taludes |
| `docs/captures/stage10_iso_talud_interior.png` | 2,577,095 | captura (stage10): stage10_iso_talud_interior |
| `docs/captures/stage10_mascaras_cenital.png` | 173,046 | captura (stage10): stage10_mascaras_cenital |
| `docs/captures/stage10_materiales.png` | 2,946,525 | captura (stage10): stage10_materiales |
| `docs/captures/stage10_muralla_puerta_sur.png` | 3,615,188 | captura (stage10): stage10_muralla_puerta_sur |
| `docs/captures/stage10_muralla_torre.png` | 3,532,269 | captura (stage10): stage10_muralla_torre |
| `docs/captures/stage10_rock_test_3x3.png` | 2,726,024 | captura (stage10): stage10_rock_test_3x3 |
| `docs/captures/stage11_lod0_vs_lod2.png` | 4,296,684 | captura (stage11): stage11_lod0_vs_lod2 |
| `docs/captures/stage12_casa_prueba_iso.png` | 2,911,157 | captura (stage12): stage12_casa_prueba_iso |
| `docs/captures/stage12_casa_prueba_partes.png` | 2,704,683 | captura (stage12): stage12_casa_prueba_partes |
| `docs/captures/stage12_casa_prueba_personaje.png` | 2,088,628 | captura (stage12): stage12_casa_prueba_personaje |
| `docs/captures/stage12_kit_sheet_estructura.png` | 3,667,904 | captura (stage12): stage12_kit_sheet_estructura |
| `docs/captures/stage12_kit_sheet_muros.png` | 3,668,165 | captura (stage12): stage12_kit_sheet_muros |
| `docs/captures/stage12_kit_sheet_props.png` | 3,502,790 | captura (stage12): stage12_kit_sheet_props |
| `docs/captures/stage13_portal_avenida_n.png` | 1,519,388 | captura (stage13): stage13_portal_avenida_n |
| `docs/captures/stage13_portal_iso.png` | 2,391,466 | captura (stage13): stage13_portal_iso |
| `docs/captures/stage13_portal_runas.png` | 2,169,326 | captura (stage13): stage13_portal_runas |
| `docs/captures/stage14_obelisco_cara.png` | 1,533,614 | captura (stage14): stage14_obelisco_cara |
| `docs/captures/stage14_obelisco_iso.png` | 2,346,370 | captura (stage14): stage14_obelisco_iso |
| `docs/captures/stage14_obelisco_numeros.png` | 1,843,103 | captura (stage14): stage14_obelisco_numeros |
| `docs/captures/stage15_faro_calle.png` | 1,921,389 | captura (stage15): stage15_faro_calle |
| `docs/captures/stage15_faro_galeria.png` | 2,292,597 | captura (stage15): stage15_faro_galeria |
| `docs/captures/stage15_faro_iso.png` | 2,704,835 | captura (stage15): stage15_faro_iso |
| `docs/captures/stage15_faro_tuberia.png` | 15,172 | captura (stage15): stage15_faro_tuberia |
| `docs/captures/stage16_salon_calle.png` | 2,487,206 | captura (stage16): stage16_salon_calle |
| `docs/captures/stage16_salon_iso.png` | 2,841,613 | captura (stage16): stage16_salon_iso |
| `docs/captures/stage16_salon_iso_frente.png` | 2,869,712 | captura (stage16): stage16_salon_iso_frente |
| `docs/captures/stage16_santuario_calle.png` | 1,989,812 | captura (stage16): stage16_santuario_calle |
| `docs/captures/stage16_santuario_iso.png` | 2,460,732 | captura (stage16): stage16_santuario_iso |
| `docs/captures/stage16_santuario_pozo.png` | 2,468,262 | captura (stage16): stage16_santuario_pozo |
| `docs/captures/stage17_faro_canales.png` | 2,975,221 | captura (stage17): stage17_faro_canales |
| `docs/captures/stage17_faro_cartelas.png` | 2,251,611 | captura (stage17): stage17_faro_cartelas |
| `docs/captures/stage17_lod2_test.png` | 3,385,342 | captura (stage17): stage17_lod2_test |
| `docs/captures/stage17_portal.png` | 2,549,201 | captura (stage17): stage17_portal |
| `docs/captures/stage18_fuente.png` | 2,832,884 | captura (stage18): stage18_fuente |
| `docs/captures/stage18_lod2_test.png` | 4,066,047 | captura (stage18): stage18_lod2_test |
| `docs/captures/stage18_mercado_iso.png` | 3,050,684 | captura (stage18): stage18_mercado_iso |
| `docs/captures/stage18_posada.png` | 2,666,086 | captura (stage18): stage18_posada |
| `docs/captures/stage18_puestos.png` | 2,381,780 | captura (stage18): stage18_puestos |
| `docs/captures/stage18_subasta.png` | 2,208,953 | captura (stage18): stage18_subasta |
| `docs/captures/stage18_tesoreria.png` | 2,494,022 | captura (stage18): stage18_tesoreria |
| `docs/captures/stage19_casareparaciones.png` | 3,044,995 | captura (stage19): stage19_casareparaciones |
| `docs/captures/stage19_crisolpiedras.png` | 3,223,593 | captura (stage19): stage19_crisolpiedras |
| `docs/captures/stage19_gremio_cazadores.png` | 2,085,771 | captura (stage19): stage19_gremio_cazadores |
| `docs/captures/stage19_gremio_herbolarios.png` | 2,817,800 | captura (stage19): stage19_gremio_herbolarios |
| `docs/captures/stage19_gremio_mineros.png` | 3,358,559 | captura (stage19): stage19_gremio_mineros |
| `docs/captures/stage19_gremio_pescadores.png` | 2,937,154 | captura (stage19): stage19_gremio_pescadores |
| `docs/captures/stage19_oficios_iso.png` | 3,017,920 | captura (stage19): stage19_oficios_iso |
| `docs/captures/stage19_taller_alquimia.png` | 2,642,581 | captura (stage19): stage19_taller_alquimia |
| `docs/captures/stage19_taller_carpinteria.png` | 3,169,545 | captura (stage19): stage19_taller_carpinteria |
| `docs/captures/stage19_taller_curtiduria.png` | 3,027,579 | captura (stage19): stage19_taller_curtiduria |
| `docs/captures/stage19_taller_granforja.png` | 3,227,135 | captura (stage19): stage19_taller_granforja |
| `docs/captures/stage19_taller_hornos.png` | 3,180,290 | captura (stage19): stage19_taller_hornos |
| `docs/captures/stage19_taller_joyeriatallado.png` | 3,160,674 | captura (stage19): stage19_taller_joyeriatallado |
| `docs/captures/stage19_taller_sastreria.png` | 3,060,616 | captura (stage19): stage19_taller_sastreria |
| `docs/captures/stage20_clases_iso.png` | 3,061,684 | captura (stage20): stage20_clases_iso |
| `docs/captures/stage20_plaza_armas.png` | 3,722,509 | captura (stage20): stage20_plaza_armas |
| `docs/captures/stage20_presets.png` | 61,314 | captura (stage20): stage20_presets |
| `docs/captures/stage20_reposicion.png` | 2,860,250 | captura (stage20): stage20_reposicion |
| `docs/captures/stage20_salon_calle.png` | 2,526,489 | captura (stage20): stage20_salon_calle |
| `docs/captures/stage20_salon_iso.png` | 3,277,755 | captura (stage20): stage20_salon_iso |
| `docs/captures/stage21_barrio_01.png` | 3,382,476 | captura (stage21): stage21_barrio_01 |
| `docs/captures/stage21_barrio_02.png` | 3,481,924 | captura (stage21): stage21_barrio_02 |
| `docs/captures/stage21_barrio_03.png` | 3,461,119 | captura (stage21): stage21_barrio_03 |
| `docs/captures/stage21_barrio_04.png` | 3,363,341 | captura (stage21): stage21_barrio_04 |
| `docs/captures/stage21_barrio_05.png` | 2,929,337 | captura (stage21): stage21_barrio_05 |
| `docs/captures/stage21_barrio_06.png` | 3,143,248 | captura (stage21): stage21_barrio_06 |
| `docs/captures/stage21_comparacion.png` | 4,875,770 | captura (stage21): stage21_comparacion |
| `docs/captures/stage21_razas_iso.png` | 3,191,101 | captura (stage21): stage21_razas_iso |
| `docs/captures/stage22_arco_calle.png` | 2,723,746 | captura (stage22): stage22_arco_calle |
| `docs/captures/stage22_arco_iso.png` | 3,124,530 | captura (stage22): stage22_arco_iso |
| `docs/captures/stage22_kit.png` | 1,456,333 | captura (stage22): stage22_kit |
| `docs/captures/stage22_puente_calle.png` | 2,396,044 | captura (stage22): stage22_puente_calle |
| `docs/captures/stage22_puente_iso.png` | 2,688,522 | captura (stage22): stage22_puente_iso |
| `docs/captures/stage22_terraza_calle.png` | 3,040,643 | captura (stage22): stage22_terraza_calle |
| `docs/captures/stage23_conjunto_NE.png` | 3,126,776 | captura (stage23): stage23_conjunto_NE |
| `docs/captures/stage23_conjunto_NO.png` | 3,242,015 | captura (stage23): stage23_conjunto_NO |
| `docs/captures/stage23_conjunto_SE.png` | 3,162,439 | captura (stage23): stage23_conjunto_SE |
| `docs/captures/stage23_conjunto_SO.png` | 3,252,265 | captura (stage23): stage23_conjunto_SO |
| `docs/captures/stage23_puerta.png` | 2,427,264 | captura (stage23): stage23_puerta |
| `docs/captures/stage23_terraza_calle.png` | 2,473,665 | captura (stage23): stage23_terraza_calle |
| `docs/captures/stage23_terraza_iso.png` | 3,184,028 | captura (stage23): stage23_terraza_iso |
| `docs/captures/stage24_ciudad_calle.png` | 1,702,691 | captura (stage24): stage24_ciudad_calle |
| `docs/captures/stage24_ciudad_iso.png` | 2,662,561 | captura (stage24): stage24_ciudad_iso |
| `docs/captures/stage24_clases.png` | 3,369,451 | captura (stage24): stage24_clases |
| `docs/captures/stage24_mercado.png` | 3,319,199 | captura (stage24): stage24_mercado |
| `docs/captures/stage24_morada_NO.png` | 3,247,386 | captura (stage24): stage24_morada_NO |
| `docs/captures/stage24_oficios.png` | 3,286,371 | captura (stage24): stage24_oficios |
| `docs/captures/stage24_portal.png` | 2,828,526 | captura (stage24): stage24_portal |
| `docs/captures/stage24_razas.png` | 3,401,287 | captura (stage24): stage24_razas |
| `docs/captures/stage25_cazadores.png` | 3,491,990 | captura (stage25): stage25_cazadores |
| `docs/captures/stage25_cazadores_campo.png` | 3,419,311 | captura (stage25): stage25_cazadores_campo |
| `docs/captures/stage25_cazadores_campo_calle.png` | 2,611,971 | captura (stage25): stage25_cazadores_campo_calle |
| `docs/captures/stage25_faro_calle.png` | 2,403,137 | captura (stage25): stage25_faro_calle |
| `docs/captures/stage25_razas_nuevas.png` | 3,461,386 | captura (stage25): stage25_razas_nuevas |
| `docs/captures/stage26_cazadores_acceso.png` | 3,438,155 | captura (stage26): stage26_cazadores_acceso |
| `docs/captures/stage26_faro_haz.png` | 1,396,031 | captura (stage26): stage26_faro_haz |
| `docs/captures/stage26_moradas_ne.png` | 3,129,930 | captura (stage26): stage26_moradas_ne |
| `docs/captures/stage26_moradas_so_calle.png` | 2,597,877 | captura (stage26): stage26_moradas_so_calle |
| `docs/captures/stage26_razas_b05_b06.png` | 3,136,208 | captura (stage26): stage26_razas_b05_b06 |
| `docs/captures/stage26_tubos.png` | 3,046,098 | captura (stage26): stage26_tubos |
| `docs/captures/stage27_banco_boveda.png` | 2,253,603 | captura (stage27): stage27_banco_boveda |
| `docs/captures/stage27_banco_cajas.png` | 1,160,088 | captura (stage27): stage27_banco_cajas |
| `docs/captures/stage27_banco_calle.png` | 2,298,278 | captura (stage27): stage27_banco_calle |
| `docs/captures/stage27_banco_iso.png` | 2,164,218 | captura (stage27): stage27_banco_iso |
| `docs/captures/stage27_kit.png` | 1,248,761 | captura (stage27): stage27_kit |
| `docs/captures/stage27_sala_calle.png` | 2,317,882 | captura (stage27): stage27_sala_calle |
| `docs/captures/stage27_sala_iso.png` | 1,991,294 | captura (stage27): stage27_sala_iso |
| `docs/captures/stage28_casa_grande_alta.png` | 2,385,931 | captura (stage28): stage28_casa_grande_alta |
| `docs/captures/stage28_casa_grande_calle.png` | 2,147,651 | captura (stage28): stage28_casa_grande_calle |
| `docs/captures/stage28_casa_grande_iso.png` | 2,257,551 | captura (stage28): stage28_casa_grande_iso |
| `docs/captures/stage28_casa_pequena_calle.png` | 2,329,823 | captura (stage28): stage28_casa_pequena_calle |
| `docs/captures/stage28_casa_pequena_iso.png` | 2,227,681 | captura (stage28): stage28_casa_pequena_iso |
| `docs/captures/stage28_habitacion_calle.png` | 2,301,437 | captura (stage28): stage28_habitacion_calle |
| `docs/captures/stage28_habitacion_iso.png` | 2,100,632 | captura (stage28): stage28_habitacion_iso |
| `docs/captures/stage28_props_clases_av.png` | 2,453,671 | captura (stage28): stage28_props_clases_av |
| `docs/captures/stage28_props_clases_q.png` | 2,774,831 | captura (stage28): stage28_props_clases_q |
| `docs/captures/stage28_props_ia_cerca.png` | 2,512,220 | captura (stage28): stage28_props_ia_cerca |
| `docs/captures/stage28_props_ia_iso.png` | 2,858,012 | captura (stage28): stage28_props_ia_iso |
| `docs/captures/stage28_props_mercado_av.png` | 2,654,699 | captura (stage28): stage28_props_mercado_av |
| `docs/captures/stage28_props_mercado_q.png` | 2,616,363 | captura (stage28): stage28_props_mercado_q |
| `docs/captures/stage28_props_oficios_av.png` | 2,614,648 | captura (stage28): stage28_props_oficios_av |
| `docs/captures/stage28_props_oficios_q.png` | 2,646,447 | captura (stage28): stage28_props_oficios_q |
| `docs/captures/stage28_props_triviales.png` | 2,751,926 | captura (stage28): stage28_props_triviales |
| `docs/captures/stage28_razas_peldanos.png` | 2,327,904 | captura (stage28): stage28_razas_peldanos |
| `docs/captures/stage28_tubos.png` | 3,096,183 | captura (stage28): stage28_tubos |
| `docs/captures/stage28_tubos_posada.png` | 3,424,592 | captura (stage28): stage28_tubos_posada |
| `docs/captures/stage28_tubos_propuesta.png` | 42,083 | captura (stage28): stage28_tubos_propuesta |
| `docs/captures/stage28_tubos_registro.png` | 2,864,703 | captura (stage28): stage28_tubos_registro |
| `docs/captures/stage28_vitrinas.png` | 1,430,259 | captura (stage28): stage28_vitrinas |
| `docs/captures/stage29_santuario_boveda.png` | 2,392,673 | captura (stage29): stage29_santuario_boveda |
| `docs/captures/stage29_santuario_calle.png` | 2,343,374 | captura (stage29): stage29_santuario_calle |
| `docs/captures/stage29_santuario_iso.png` | 2,035,271 | captura (stage29): stage29_santuario_iso |
| `docs/captures/stage29_santuario_seccion.png` | 2,001,907 | captura (stage29): stage29_santuario_seccion |
| `docs/captures/stage29_tesoreria_alta.png` | 2,429,138 | captura (stage29): stage29_tesoreria_alta |
| `docs/captures/stage29_tesoreria_calle.png` | 2,485,325 | captura (stage29): stage29_tesoreria_calle |
| `docs/captures/stage29_tesoreria_iso.png` | 2,383,503 | captura (stage29): stage29_tesoreria_iso |
| `docs/captures/stage29_tesoreria_mostrador.png` | 2,783,998 | captura (stage29): stage29_tesoreria_mostrador |
| `docs/captures/stage29_tesoreria_vitrinas.png` | 2,254,669 | captura (stage29): stage29_tesoreria_vitrinas |
| `docs/reference/godot47/class_animationnodeanimation.txt` | 115,372 | extracto de la documentación oficial (Godot 4.7 u otra referencia) |
| `docs/reference/godot47/class_animationnodeblendspace2d.txt` | 120,492 | extracto de la documentación oficial (Godot 4.7 u otra referencia) |
| `docs/reference/godot47/class_animationnodetimescale.txt` | 112,704 | extracto de la documentación oficial (Godot 4.7 u otra referencia) |
| `docs/reference/godot47/class_arraymesh.txt` | 10,407 | extracto de la documentación oficial (Godot 4.7 u otra referencia) |
| `docs/reference/godot47/class_basematerial3d.txt` | 70,948 | extracto de la documentación oficial (Godot 4.7 u otra referencia) |
| `docs/reference/godot47/class_bonemap.txt` | 114,397 | extracto de la documentación oficial (Godot 4.7 u otra referencia) |
| `docs/reference/godot47/class_boxoccluder3d.txt` | 819 | extracto de la documentación oficial (Godot 4.7 u otra referencia) |
| `docs/reference/godot47/class_camera3d.txt` | 13,662 | extracto de la documentación oficial (Godot 4.7 u otra referencia) |
| `docs/reference/godot47/class_characterbody3d.txt` | 14,666 | extracto de la documentación oficial (Godot 4.7 u otra referencia) |
| `docs/reference/godot47/class_editorscenepostimport.txt` | 2,260 | extracto de la documentación oficial (Godot 4.7 u otra referencia) |
| `docs/reference/godot47/class_engine.txt` | 131,928 | extracto de la documentación oficial (Godot 4.7 u otra referencia) |
| `docs/reference/godot47/class_geometryinstance3d.txt` | 14,055 | extracto de la documentación oficial (Godot 4.7 u otra referencia) |
| `docs/reference/godot47/class_gltfdocument.txt` | 14,620 | extracto de la documentación oficial (Godot 4.7 u otra referencia) |
| `docs/reference/godot47/class_marker3d.txt` | 696 | extracto de la documentación oficial (Godot 4.7 u otra referencia) |
| `docs/reference/godot47/class_mesh.txt` | 16,338 | extracto de la documentación oficial (Godot 4.7 u otra referencia) |
| `docs/reference/godot47/class_multimesh.txt` | 11,013 | extracto de la documentación oficial (Godot 4.7 u otra referencia) |
| `docs/reference/godot47/class_multimeshinstance3d.txt` | 1,025 | extracto de la documentación oficial (Godot 4.7 u otra referencia) |
| `docs/reference/godot47/class_navigationagent3d.txt` | 23,751 | extracto de la documentación oficial (Godot 4.7 u otra referencia) |
| `docs/reference/godot47/class_navigationlink3d.txt` | 4,692 | extracto de la documentación oficial (Godot 4.7 u otra referencia) |
| `docs/reference/godot47/class_navigationmesh.txt` | 11,715 | extracto de la documentación oficial (Godot 4.7 u otra referencia) |
| `docs/reference/godot47/class_navigationmeshsourcegeometrydata3d.txt` | 117,444 | extracto de la documentación oficial (Godot 4.7 u otra referencia) |
| `docs/reference/godot47/class_navigationserver3d.txt` | 154,964 | extracto de la documentación oficial (Godot 4.7 u otra referencia) |
| `docs/reference/godot47/class_performance.txt` | 15,489 | extracto de la documentación oficial (Godot 4.7 u otra referencia) |
| `docs/reference/godot47/class_projectsettings.txt` | 342,355 | extracto de la documentación oficial (Godot 4.7 u otra referencia) |
| `docs/reference/godot47/class_renderingserver.txt` | 282,947 | extracto de la documentación oficial (Godot 4.7 u otra referencia) |
| `docs/reference/godot47/class_resourceimporterscene.txt` | 11,449 | extracto de la documentación oficial (Godot 4.7 u otra referencia) |
| `docs/reference/godot47/class_resourceimportertexture.txt` | 15,868 | extracto de la documentación oficial (Godot 4.7 u otra referencia) |
| `docs/reference/godot47/class_resourceloader.txt` | 9,933 | extracto de la documentación oficial (Godot 4.7 u otra referencia) |
| `docs/reference/godot47/class_resourcesaver.txt` | 3,622 | extracto de la documentación oficial (Godot 4.7 u otra referencia) |
| `docs/reference/godot47/class_skeletonprofilehumanoid.txt` | 115,645 | extracto de la documentación oficial (Godot 4.7 u otra referencia) |
| `docs/reference/godot47/class_viewport.txt` | 60,095 | extracto de la documentación oficial (Godot 4.7 u otra referencia) |
| `docs/reference/godot47/class_visualinstance3d.txt` | 4,670 | extracto de la documentación oficial (Godot 4.7 u otra referencia) |
| `docs/reference/godot47/import_configuration.txt` | 18,166 | extracto de la documentación oficial (Godot 4.7 u otra referencia) |
| `docs/reference/godot47/node_type_customization.txt` | 6,238 | extracto de la documentación oficial (Godot 4.7 u otra referencia) |
| `docs/reference/godot47/occlusion_culling.txt` | 12,505 | extracto de la documentación oficial (Godot 4.7 u otra referencia) |
| `docs/reference/godot47/retargeting_3d_skeletons.txt` | 6,994 | extracto de la documentación oficial (Godot 4.7 u otra referencia) |
| `docs/reference/godot47/spatial_shader.txt` | 187,361 | extracto de la documentación oficial (Godot 4.7 u otra referencia) |
| `docs/reference/godot47/visibility_ranges.txt` | 11,102 | extracto de la documentación oficial (Godot 4.7 u otra referencia) |
| `docs/reference/godot_SkeletonProfileHumanoid.txt` | 2,823 | extracto de la documentación oficial (Godot 4.7 u otra referencia) |
| `docs/reports/inventario_glb.md` | 20,458 | informe de medición: inventario_glb |
| `docs/reports/pj1_elfo_articulaciones.json` | 24,667 | informe de medición: pj1_elfo_articulaciones |
| `docs/reports/pj1_elfo_cuerpo.json` | 6,256 | informe de medición: pj1_elfo_cuerpo |
| `docs/reports/pj1_elfo_referencia.json` | 742 | informe de medición: pj1_elfo_referencia |
| `docs/reports/pj2_sanador.json` | 4,383 | informe de medición: pj2_sanador |
| `docs/reports/pj3_rig.json` | 11,344 | informe de medición: pj3_rig |
| `docs/reports/pj4_anim.json` | 3,501 | informe de medición: pj4_anim |
| `docs/reports/pj4_reposo_ual.json` | 1,434 | informe de medición: pj4_reposo_ual |
| `docs/reports/pj4b_ual_seleccion.json` | 4,743 | informe de medición: pj4b_ual_seleccion |
| `docs/reports/pj5_lods.json` | 3,790 | informe de medición: pj5_lods |
| `docs/reports/stage02_terrain.json` | 50,712 | informe de medición: stage02_terrain |
| `docs/reports/stage03_plaza.json` | 12,988 | informe de medición: stage03_plaza |
| `docs/reports/stage04_wall.json` | 17,387 | informe de medición: stage04_wall |
| `docs/reports/stage05_layout.json` | 351,617 | informe de medición: stage05_layout |
| `docs/reports/stage05_streets.json` | 27,957 | informe de medición: stage05_streets |
| `docs/reports/stage06_layout.json` | 125,212 | informe de medición: stage06_layout |
| `docs/reports/stage06_moradas.json` | 16,801 | informe de medición: stage06_moradas |
| `docs/reports/stage07_cauce.json` | 17,770 | informe de medición: stage07_cauce |
| `docs/reports/stage08_exterior.json` | 4,169 | informe de medición: stage08_exterior |
| `docs/reports/stage09_materials.json` | 12,691 | informe de medición: stage09_materials |
| `docs/reports/stage10_textures.json` | 41,535 | informe de medición: stage10_textures |
| `docs/reports/stage11_godot.json` | 78,505 | informe de medición: stage11_godot |
| `docs/reports/stage11_markers.csv` | 191,568 | informe de medición: stage11_markers |
| `docs/reports/stage12_kit.json` | 8,778 | informe de medición: stage12_kit |
| `docs/reports/stage13_portal.json` | 8,103 | informe de medición: stage13_portal |
| `docs/reports/stage14_obelisk.json` | 1,178 | informe de medición: stage14_obelisk |
| `docs/reports/stage15_faro.json` | 2,573 | informe de medición: stage15_faro |
| `docs/reports/stage16_landmarks.json` | 6,719 | informe de medición: stage16_landmarks |
| `docs/reports/stage17_decisions.json` | 8,722 | informe de medición: stage17_decisions |
| `docs/reports/stage17_lod2_test.json` | 1,702 | informe de medición: stage17_lod2_test |
| `docs/reports/stage17_materials.json` | 26,235 | informe de medición: stage17_materials |
| `docs/reports/stage18_lod2_test.json` | 1,154 | informe de medición: stage18_lod2_test |
| `docs/reports/stage18_mercado.json` | 20,293 | informe de medición: stage18_mercado |
| `docs/reports/stage19_oficios.json` | 17,960 | informe de medición: stage19_oficios |
| `docs/reports/stage20_clases.json` | 27,088 | informe de medición: stage20_clases |
| `docs/reports/stage21_razas.json` | 61,787 | informe de medición: stage21_razas |
| `docs/reports/stage22_conexiones.json` | 21,366 | informe de medición: stage22_conexiones |
| `docs/reports/stage23_moradas.json` | 14,174 | informe de medición: stage23_moradas |
| `docs/reports/stage24_godot.json` | 190,567 | informe de medición: stage24_godot |
| `docs/reports/stage25_decisiones.json` | 4,562 | informe de medición: stage25_decisiones |
| `docs/reports/stage25_faro.json` | 20,062 | informe de medición: stage25_faro |
| `docs/reports/stage25_godot.json` | 173,275 | informe de medición: stage25_godot |
| `docs/reports/stage26_decisiones.json` | 23,167 | informe de medición: stage26_decisiones |
| `docs/reports/stage26_faro.json` | 26,455 | informe de medición: stage26_faro |
| `docs/reports/stage26_faro_proposal.json` | 1,098 | informe de medición: stage26_faro_proposal |
| `docs/reports/stage26_godot.json` | 169,293 | informe de medición: stage26_godot |
| `docs/reports/stage26_texture_memory.json` | 13,387 | informe de medición: stage26_texture_memory |
| `docs/reports/stage27_interiors.json` | 9,236 | informe de medición: stage27_interiors |
| `docs/reports/stage28_ciudad.json` | 35,034 | informe de medición: stage28_ciudad |
| `docs/reports/stage28_godot_v28.json` | 162,995 | informe de medición: stage28_godot_v28 |
| `docs/reports/stage28_moradas_int.json` | 11,090 | informe de medición: stage28_moradas_int |
| `docs/reports/stage28_moradas_prueba_far.json` | 1,324 | informe de medición: stage28_moradas_prueba_far |
| `docs/reports/stage28_moradas_residual.json` | 4,650 | informe de medición: stage28_moradas_residual |
| `docs/reports/stage28_props_import.json` | 79,441 | informe de medición: stage28_props_import |
| `docs/reports/stage28_props_mano.json` | 5,468 | informe de medición: stage28_props_mano |
| `docs/reports/stage29_santuario.json` | 5,731 | informe de medición: stage29_santuario |
| `docs/reports/stage29_tesoreria.json` | 11,128 | informe de medición: stage29_tesoreria |
| `export/godot/bld_clases.glb` | 7,011,912 | edificios para Godot |
| `export/godot/bld_kit.glb` | 1,636,816 | edificios para Godot |
| `export/godot/bld_mercado.glb` | 6,988,376 | edificios para Godot |
| `export/godot/bld_moradas_NE.glb` | 4,240,536 | edificios para Godot |
| `export/godot/bld_moradas_NO.glb` | 4,580,368 | edificios para Godot |
| `export/godot/bld_moradas_SE.glb` | 3,824,712 | edificios para Godot |
| `export/godot/bld_moradas_SO.glb` | 4,158,680 | edificios para Godot |
| `export/godot/bld_oficios.glb` | 5,304,908 | edificios para Godot |
| `export/godot/bld_portal.glb` | 5,918,276 | edificios para Godot |
| `export/godot/bld_props.glb` | 367,556 | edificios para Godot |
| `export/godot/bld_razas.glb` | 10,750,344 | edificios para Godot |
| `export/godot/concordia_markers.glb` | 250,304 | export para Godot |
| `export/godot/concordia_terrain_clases.glb` | 4,833,968 | export para Godot |
| `export/godot/concordia_terrain_exterior.glb` | 16,391,716 | export para Godot |
| `export/godot/concordia_terrain_mercado.glb` | 4,716,248 | export para Godot |
| `export/godot/concordia_terrain_moradas.glb` | 18,902,852 | export para Godot |
| `export/godot/concordia_terrain_oficios.glb` | 8,306,616 | export para Godot |
| `export/godot/concordia_terrain_plaza.glb` | 7,723,296 | export para Godot |
| `export/godot/concordia_terrain_razas.glb` | 4,681,556 | export para Godot |
| `export/godot/concordia_wall_kit.glb` | 1,690,444 | export para Godot |
| `export/godot/concordia_wall_layout.glb` | 1,004,568 | export para Godot |
| `export/godot/int_banco.glb` | 1,689,852 | interior para Godot |
| `export/godot/int_morada_casa_grande.glb` | 946,072 | interior para Godot |
| `export/godot/int_morada_casa_pequena.glb` | 728,004 | interior para Godot |
| `export/godot/int_morada_habitacion.glb` | 424,468 | interior para Godot |
| `export/godot/int_santuario.glb` | 768,224 | interior para Godot |
| `export/godot/int_tesoreria.glb` | 1,455,876 | interior para Godot |
| `export/godot/materials/concordia_materials.bin` | 1,021,452 | export para Godot |
| `export/godot/materials/concordia_materials.gltf` | 84,250 | export para Godot |
| `export/godot/personajes/elfo_sanador_anims.glb` | 276,116 | personaje para Godot (PJ5) |
| `export/godot/personajes/elfo_sanador_belt.glb` | 1,953,636 | personaje para Godot (PJ5) |
| `export/godot/personajes/elfo_sanador_boots.glb` | 1,918,624 | personaje para Godot (PJ5) |
| `export/godot/personajes/elfo_sanador_bracers.glb` | 1,901,020 | personaje para Godot (PJ5) |
| `export/godot/personajes/elfo_sanador_hood.glb` | 1,947,912 | personaje para Godot (PJ5) |
| `export/godot/personajes/elfo_sanador_lod2.glb` | 3,097,444 | personaje para Godot (PJ5) |
| `export/godot/personajes/elfo_sanador_robe_top.glb` | 1,950,640 | personaje para Godot (PJ5) |
| `export/godot/personajes/elfo_sanador_skirt.glb` | 1,951,464 | personaje para Godot (PJ5) |
| `export/godot/personajes/personaje_elfo_base.glb` | 3,274,816 | personaje para Godot (PJ5) |
| `export/godot/pj_elfo_cuerpo.glb` | 1,205,616 | personaje (fases PJ1–PJ4) |
| `export/godot/pj_elfo_rig.glb` | 3,734,100 | personaje (fases PJ1–PJ4) |
| `export/godot/pj_elfo_sanador_anim.glb` | 3,585,536 | personaje (fases PJ1–PJ4) |
| `export/godot/pj_elfo_sanador_equipado.glb` | 3,169,772 | personaje (fases PJ1–PJ4) |
| `export/godot/pj_sanador_ropa.glb` | 2,001,628 | personaje (fases PJ1–PJ4) |
| `export/godot/props_int_clases.glb` | 1,204,760 | props para Godot |
| `export/godot/props_int_mano.glb` | 442,880 | props para Godot |
| `export/godot/props_int_mercado.glb` | 2,441,900 | props para Godot |
| `export/godot/props_int_oficios.glb` | 2,006,716 | props para Godot |
| `export/godot/props_trophy_cases.glb` | 70,708 | props para Godot |
| `export/godot_v28/bld_clases.glb` | 7,011,912 | export de la ciudad v28 para Godot (gana sobre export/godot en sync_assets) |
| `export/godot_v28/bld_kit.glb` | 1,636,712 | export de la ciudad v28 para Godot (gana sobre export/godot en sync_assets) |
| `export/godot_v28/bld_mercado.glb` | 6,876,140 | export de la ciudad v28 para Godot (gana sobre export/godot en sync_assets) |
| `export/godot_v28/bld_moradas_NE.glb` | 4,230,096 | export de la ciudad v28 para Godot (gana sobre export/godot en sync_assets) |
| `export/godot_v28/bld_moradas_NO.glb` | 4,465,732 | export de la ciudad v28 para Godot (gana sobre export/godot en sync_assets) |
| `export/godot_v28/bld_moradas_SE.glb` | 3,824,712 | export de la ciudad v28 para Godot (gana sobre export/godot en sync_assets) |
| `export/godot_v28/bld_moradas_SO.glb` | 4,352,548 | export de la ciudad v28 para Godot (gana sobre export/godot en sync_assets) |
| `export/godot_v28/bld_oficios.glb` | 5,304,908 | export de la ciudad v28 para Godot (gana sobre export/godot en sync_assets) |
| `export/godot_v28/bld_portal.glb` | 5,957,152 | export de la ciudad v28 para Godot (gana sobre export/godot en sync_assets) |
| `export/godot_v28/bld_props.glb` | 367,556 | export de la ciudad v28 para Godot (gana sobre export/godot en sync_assets) |
| `export/godot_v28/bld_razas.glb` | 10,755,728 | export de la ciudad v28 para Godot (gana sobre export/godot en sync_assets) |
| `export/godot_v28/concordia_markers.glb` | 250,048 | export de la ciudad v28 para Godot (gana sobre export/godot en sync_assets) |
| `export/godot_v28/concordia_terrain_clases.glb` | 4,833,968 | export de la ciudad v28 para Godot (gana sobre export/godot en sync_assets) |
| `export/godot_v28/concordia_terrain_mercado.glb` | 4,716,248 | export de la ciudad v28 para Godot (gana sobre export/godot en sync_assets) |
| `export/godot_v28/concordia_terrain_moradas.glb` | 18,902,852 | export de la ciudad v28 para Godot (gana sobre export/godot en sync_assets) |
| `export/godot_v28/concordia_terrain_oficios.glb` | 8,306,616 | export de la ciudad v28 para Godot (gana sobre export/godot en sync_assets) |
| `export/godot_v28/concordia_terrain_plaza.glb` | 7,723,296 | export de la ciudad v28 para Godot (gana sobre export/godot en sync_assets) |
| `export/godot_v28/concordia_terrain_razas.glb` | 4,681,556 | export de la ciudad v28 para Godot (gana sobre export/godot en sync_assets) |
| `godot_concordia/.gitignore` | 523 | proyecto de Godot |
| `godot_concordia/FIXES_BLENDER.md` | 14,347 | proyecto de Godot |
| `godot_concordia/LEEME_CAMBIOS.txt` | 5,186 | proyecto de Godot |
| `godot_concordia/README_godot.md` | 4,794 | proyecto de Godot |
| `godot_concordia/TAREAS_GODOT.md` | 5,154 | proyecto de Godot |
| `godot_concordia/TEST_REPORT.md` | 27,016 | proyecto de Godot |
| `godot_concordia/animations/bonemap_elfo.tres` | 2,637 | proyecto de Godot |
| `godot_concordia/animations/bonemap_ual1.tres` | 2,579 | proyecto de Godot |
| `godot_concordia/animations/bonemap_ual2.tres` | 2,327 | proyecto de Godot |
| `godot_concordia/assets/MANIFEST.txt` | 60,359 | proyecto de Godot |
| `godot_concordia/debug/capture_top.gd` | 1,399 | script de Godot |
| `godot_concordia/debug/capture_top.gd.uid` | 19 | proyecto de Godot |
| `godot_concordia/debug/make_main_glb.gd` | 713 | script de Godot |
| `godot_concordia/debug/make_main_glb.gd.uid` | 19 | proyecto de Godot |
| `godot_concordia/debug/out/.gdignore` | 0 | proyecto de Godot |
| `godot_concordia/debug/probe_custom.gd` | 1,207 | script de Godot |
| `godot_concordia/debug/probe_custom.gd.uid` | 20 | proyecto de Godot |
| `godot_concordia/debug/probe_gpu_objects.gd` | 2,423 | script de Godot |
| `godot_concordia/debug/probe_gpu_objects.gd.uid` | 20 | proyecto de Godot |
| `godot_concordia/debug/probe_meta.gd` | 439 | script de Godot |
| `godot_concordia/debug/probe_meta.gd.uid` | 19 | proyecto de Godot |
| `godot_concordia/debug/probe_navcover.gd` | 5,250 | script de Godot |
| `godot_concordia/debug/probe_navcover.gd.uid` | 20 | proyecto de Godot |
| `godot_concordia/debug/probe_navmesh.gd` | 1,220 | script de Godot |
| `godot_concordia/debug/probe_navmesh.gd.uid` | 20 | proyecto de Godot |
| `godot_concordia/debug/probe_navres.gd` | 1,225 | script de Godot |
| `godot_concordia/debug/probe_navres.gd.uid` | 20 | proyecto de Godot |
| `godot_concordia/debug/probe_normals.gd` | 917 | script de Godot |
| `godot_concordia/debug/probe_normals.gd.uid` | 20 | proyecto de Godot |
| `godot_concordia/debug/probe_pj5_glb.gd` | 1,583 | script de Godot |
| `godot_concordia/debug/probe_pj5_glb.gd.uid` | 20 | proyecto de Godot |
| `godot_concordia/debug/probe_stair_profile.gd` | 1,575 | script de Godot |
| `godot_concordia/debug/probe_stair_profile.gd.uid` | 20 | proyecto de Godot |
| `godot_concordia/debug/probe_stairs.gd` | 1,914 | script de Godot |
| `godot_concordia/debug/probe_stairs.gd.uid` | 19 | proyecto de Godot |
| `godot_concordia/debug/probe_tree.gd` | 586 | script de Godot |
| `godot_concordia/debug/probe_tree.gd.uid` | 20 | proyecto de Godot |
| `godot_concordia/debug/probe_ual_sel.gd` | 847 | script de Godot |
| `godot_concordia/debug/probe_ual_sel.gd.uid` | 20 | proyecto de Godot |
| `godot_concordia/debug/probe_vram.gd` | 2,276 | script de Godot |
| `godot_concordia/debug/probe_vram.gd.uid` | 19 | proyecto de Godot |
| `godot_concordia/debug/probe_wall_gaps.gd` | 1,779 | script de Godot |
| `godot_concordia/debug/probe_wall_gaps.gd.uid` | 19 | proyecto de Godot |
| `godot_concordia/debug/probe_winding.gd` | 582 | script de Godot |
| `godot_concordia/debug/probe_winding.gd.uid` | 20 | proyecto de Godot |
| `godot_concordia/navigation/links.json` | 1,729 | navegación horneada en Godot |
| `godot_concordia/navigation/nav_clases.res` | 18,654 | navegación horneada en Godot |
| `godot_concordia/navigation/nav_int_banco.res` | 1,791 | navegación horneada en Godot |
| `godot_concordia/navigation/nav_int_morada_casa_grande.res` | 709 | navegación horneada en Godot |
| `godot_concordia/navigation/nav_int_morada_casa_pequena.res` | 671 | navegación horneada en Godot |
| `godot_concordia/navigation/nav_int_morada_habitacion.res` | 588 | navegación horneada en Godot |
| `godot_concordia/navigation/nav_mercado.res` | 24,431 | navegación horneada en Godot |
| `godot_concordia/navigation/nav_moradas_ne.res` | 10,743 | navegación horneada en Godot |
| `godot_concordia/navigation/nav_moradas_no.res` | 10,607 | navegación horneada en Godot |
| `godot_concordia/navigation/nav_moradas_se.res` | 10,525 | navegación horneada en Godot |
| `godot_concordia/navigation/nav_moradas_so.res` | 10,461 | navegación horneada en Godot |
| `godot_concordia/navigation/nav_muralla_ronda.res` | 1,768 | navegación horneada en Godot |
| `godot_concordia/navigation/nav_oficios.res` | 21,926 | navegación horneada en Godot |
| `godot_concordia/navigation/nav_plaza.res` | 5,356 | navegación horneada en Godot |
| `godot_concordia/navigation/nav_razas.res` | 18,410 | navegación horneada en Godot |
| `godot_concordia/project.godot` | 774 | proyecto de Godot |
| `godot_concordia/scenes/concordia.tscn` | 3,178 | escena de Godot (generada por script) |
| `godot_concordia/scenes/concordia_glb.tscn` | 6,882 | escena de Godot (generada por script) |
| `godot_concordia/scenes/main.tscn` | 1,658 | escena de Godot (generada por script) |
| `godot_concordia/scripts/city.gd` | 7,251 | script de Godot |
| `godot_concordia/scripts/city.gd.uid` | 20 | proyecto de Godot |
| `godot_concordia/scripts/day_night.gd` | 7,394 | script de Godot |
| `godot_concordia/scripts/day_night.gd.uid` | 20 | proyecto de Godot |
| `godot_concordia/scripts/effects.gd` | 12,420 | script de Godot |
| `godot_concordia/scripts/effects.gd.uid` | 20 | proyecto de Godot |
| `godot_concordia/scripts/game.gd` | 4,385 | script de Godot |
| `godot_concordia/scripts/game.gd.uid` | 20 | proyecto de Godot |
| `godot_concordia/scripts/iso_camera.gd` | 2,516 | script de Godot |
| `godot_concordia/scripts/iso_camera.gd.uid` | 20 | proyecto de Godot |
| `godot_concordia/scripts/lod_manager.gd` | 5,437 | script de Godot |
| `godot_concordia/scripts/lod_manager.gd.uid` | 20 | proyecto de Godot |
| `godot_concordia/scripts/materials_fix.gd` | 8,279 | script de Godot |
| `godot_concordia/scripts/materials_fix.gd.uid` | 20 | proyecto de Godot |
| `godot_concordia/scripts/nav_ready.gd` | 3,139 | script de Godot |
| `godot_concordia/scripts/nav_ready.gd.uid` | 19 | proyecto de Godot |
| `godot_concordia/scripts/player.gd` | 3,592 | script de Godot |
| `godot_concordia/scripts/player.gd.uid` | 19 | proyecto de Godot |
| `godot_concordia/scripts/quality.gd` | 5,160 | script de Godot |
| `godot_concordia/scripts/quality.gd.uid` | 20 | proyecto de Godot |
| `godot_concordia/scripts/world_streamer.gd` | 6,384 | script de Godot |
| `godot_concordia/scripts/world_streamer.gd.uid` | 20 | proyecto de Godot |
| `godot_concordia/shaders/banner.gdshader` | 1,183 | shader de Godot |
| `godot_concordia/shaders/banner.gdshader.uid` | 20 | proyecto de Godot |
| `godot_concordia/shaders/beam.gdshader` | 1,404 | shader de Godot |
| `godot_concordia/shaders/beam.gdshader.uid` | 19 | proyecto de Godot |
| `godot_concordia/shaders/terrain.gdshader` | 5,835 | shader de Godot |
| `godot_concordia/shaders/terrain.gdshader.uid` | 19 | proyecto de Godot |
| `godot_concordia/shaders/veil.gdshader` | 1,270 | shader de Godot |
| `godot_concordia/shaders/veil.gdshader.uid` | 20 | proyecto de Godot |
| `godot_concordia/shaders/water.gdshader` | 1,382 | shader de Godot |
| `godot_concordia/shaders/water.gdshader.uid` | 19 | proyecto de Godot |
| `godot_concordia/tools/bake_navmesh.gd` | 19,034 | script de Godot |
| `godot_concordia/tools/bake_navmesh.gd.uid` | 19 | proyecto de Godot |
| `godot_concordia/tools/benchmark.gd` | 10,686 | script de Godot |
| `godot_concordia/tools/benchmark.gd.uid` | 20 | proyecto de Godot |
| `godot_concordia/tools/build_city.gd` | 3,217 | script de Godot |
| `godot_concordia/tools/build_city.gd.uid` | 19 | proyecto de Godot |
| `godot_concordia/tools/build_world.gd` | 32,684 | script de Godot |
| `godot_concordia/tools/build_world.gd.uid` | 20 | proyecto de Godot |
| `godot_concordia/tools/capture_tour.gd` | 5,048 | script de Godot |
| `godot_concordia/tools/capture_tour.gd.uid` | 20 | proyecto de Godot |
| `godot_concordia/tools/g3_problem_points.json` | 786 | proyecto de Godot |
| `godot_concordia/tools/import_report.gd` | 5,537 | script de Godot |
| `godot_concordia/tools/import_report.gd.uid` | 20 | proyecto de Godot |
| `godot_concordia/tools/import_settings.py` | 5,527 | ajustes de importacion repetibles: reescribe la seccion [params] de los .import (Godot 4.7.2). Valores verificados en la documentacion oficial 4.7 (docs/reference/godot47/class_resourceimporterscene.txt y class_resourcei… |
| `godot_concordia/tools/list_metadata.gd` | 1,242 | script de Godot |
| `godot_concordia/tools/list_metadata.gd.uid` | 19 | proyecto de Godot |
| `godot_concordia/tools/make_bonemaps.gd` | 4,969 | script de Godot |
| `godot_concordia/tools/make_bonemaps.gd.uid` | 20 | proyecto de Godot |
| `godot_concordia/tools/pick.gd` | 2,149 | script de Godot |
| `godot_concordia/tools/pick.gd.uid` | 20 | proyecto de Godot |
| `godot_concordia/tools/post_import.gd` | 7,582 | script de Godot |
| `godot_concordia/tools/post_import.gd.uid` | 20 | proyecto de Godot |
| `godot_concordia/tools/preparar_pc.bat` | 1,941 | script de Windows |
| `godot_concordia/tools/sync_assets.py` | 4,852 | copia las exportaciones de Blender al proyecto de Godot (godot_concordia/assets/) con MANIFEST (sha256). Origen (del repositorio): export/godot_v28/*.glb (ciudad v28: prioridad) export/godot/*.glb (lo que no esta en godo… |
| `godot_concordia/tools/verify_assets.gd` | 4,336 | script de Godot |
| `godot_concordia/tools/verify_assets.gd.uid` | 20 | proyecto de Godot |
| `godot_concordia/tools/walk_routes.json` | 59,941 | proyecto de Godot |
| `godot_concordia/tools/walk_routes.py` | 6,461 | rutas de la prueba de caminata (G3). Genera tools/walk_routes.json, que lee tools/walk_test.gd. Fuentes: ../docs/reports/stage05_layout.json calles (avenidas, rondas r100/r150, diagonales, callejones y callejones con esc… |
| `godot_concordia/tools/walk_test.gd` | 10,125 | script de Godot |
| `godot_concordia/tools/walk_test.gd.uid` | 20 | proyecto de Godot |
| `godot_concordia/ui/compass.gd` | 1,527 | script de Godot |
| `godot_concordia/ui/compass.gd.uid` | 19 | proyecto de Godot |
| `godot_concordia/ui/debug_hud.gd` | 2,444 | script de Godot |
| `godot_concordia/ui/debug_hud.gd.uid` | 20 | proyecto de Godot |
| `godot_concordia/ui/quality_menu.gd` | 2,595 | script de Godot |
| `godot_concordia/ui/quality_menu.gd.uid` | 20 | proyecto de Godot |
| `licenses/Quaternius_FantasyPropsMegaKit_License_Standard.txt` | 837 | texto de licencia del asset |
| `licenses/Quaternius_UAL1_Standard_License.txt` | 446 | texto de licencia del asset |
| `licenses/Quaternius_UAL2_Standard_License.txt` | 541 | texto de licencia del asset |
| `respaldo/MANIFEST.txt` | 44,509 | documentación / configuración |
| `textures/concordia/MAT_Ash_Gray/T_Ash_Gray_Albedo.jpg` | 2,341,084 | textura (concordia/MAT_Ash_Gray) |
| `textures/concordia/MAT_Ash_Gray/T_Ash_Gray_Normal.jpg` | 3,272,397 | textura (concordia/MAT_Ash_Gray) |
| `textures/concordia/MAT_Ash_Gray/T_Ash_Gray_Roughness.jpg` | 774,903 | textura (concordia/MAT_Ash_Gray) |
| `textures/concordia/MAT_Ash_Gray/concordia_ash_gray_albedo.png` | 5,051,251 | textura (concordia/MAT_Ash_Gray) |
| `textures/concordia/MAT_Ash_Gray/concordia_ash_gray_orm.png` | 6,111,014 | textura (concordia/MAT_Ash_Gray) |
| `textures/concordia/MAT_Ash_Ground/concordia_ash_ground_albedo.png` | 4,339,052 | textura (concordia/MAT_Ash_Ground) |
| `textures/concordia/MAT_Ash_Ground/concordia_ash_ground_orm.png` | 6,077,202 | textura (concordia/MAT_Ash_Ground) |
| `textures/concordia/MAT_Bank_BoxNumbers/bank_box_numbers_1k.png` | 102,761 | textura (concordia/MAT_Bank_BoxNumbers) |
| `textures/concordia/MAT_Banner/concordia_banner_clase_01_albedo.png` | 4,541 | textura (concordia/MAT_Banner) |
| `textures/concordia/MAT_Banner/concordia_banner_clase_02_albedo.png` | 4,527 | textura (concordia/MAT_Banner) |
| `textures/concordia/MAT_Banner/concordia_banner_clase_03_albedo.png` | 3,563 | textura (concordia/MAT_Banner) |
| `textures/concordia/MAT_Banner/concordia_banner_clase_04_albedo.png` | 3,933 | textura (concordia/MAT_Banner) |
| `textures/concordia/MAT_Banner/concordia_banner_clase_05_albedo.png` | 3,073 | textura (concordia/MAT_Banner) |
| `textures/concordia/MAT_Banner/concordia_banner_clase_06_albedo.png` | 3,745 | textura (concordia/MAT_Banner) |
| `textures/concordia/MAT_Banner/concordia_banner_clase_07_albedo.png` | 3,844 | textura (concordia/MAT_Banner) |
| `textures/concordia/MAT_Banner/concordia_banner_clase_08_albedo.png` | 3,257 | textura (concordia/MAT_Banner) |
| `textures/concordia/MAT_Banner/concordia_banner_raza_r01_albedo.png` | 3,069 | textura (concordia/MAT_Banner) |
| `textures/concordia/MAT_Banner/concordia_banner_raza_r02_albedo.png` | 4,327 | textura (concordia/MAT_Banner) |
| `textures/concordia/MAT_Banner/concordia_banner_raza_r03_albedo.png` | 3,827 | textura (concordia/MAT_Banner) |
| `textures/concordia/MAT_Banner/concordia_banner_raza_r04_albedo.png` | 3,435 | textura (concordia/MAT_Banner) |
| `textures/concordia/MAT_Banner/concordia_banner_raza_r05_albedo.png` | 4,754 | textura (concordia/MAT_Banner) |
| `textures/concordia/MAT_Banner/concordia_banner_raza_r06_albedo.png` | 3,353 | textura (concordia/MAT_Banner) |
| `textures/concordia/MAT_Cloth/concordia_cloth_albedo.png` | 1,048,151 | textura (concordia/MAT_Cloth) |
| `textures/concordia/MAT_Cloth/concordia_cloth_orm.png` | 1,931,435 | textura (concordia/MAT_Cloth) |
| `textures/concordia/MAT_Cloth_Patch_A/T_Cloth_Patch_A_Albedo.jpg` | 828,620 | textura (concordia/MAT_Cloth_Patch_A) |
| `textures/concordia/MAT_Cloth_Patch_A/T_Cloth_Patch_A_Normal.jpg` | 2,285,051 | textura (concordia/MAT_Cloth_Patch_A) |
| `textures/concordia/MAT_Cloth_Patch_A/T_Cloth_Patch_A_Roughness.jpg` | 197,292 | textura (concordia/MAT_Cloth_Patch_A) |
| `textures/concordia/MAT_Cloth_Patch_B/T_Cloth_Patch_B_Albedo.jpg` | 909,145 | textura (concordia/MAT_Cloth_Patch_B) |
| `textures/concordia/MAT_Cloth_Patch_B/T_Cloth_Patch_B_Normal.jpg` | 2,285,024 | textura (concordia/MAT_Cloth_Patch_B) |
| `textures/concordia/MAT_Cloth_Patch_B/T_Cloth_Patch_B_Roughness.jpg` | 191,826 | textura (concordia/MAT_Cloth_Patch_B) |
| `textures/concordia/MAT_Cloth_Patch_C/T_Cloth_Patch_C_Albedo.jpg` | 906,921 | textura (concordia/MAT_Cloth_Patch_C) |
| `textures/concordia/MAT_Cloth_Patch_C/T_Cloth_Patch_C_Normal.jpg` | 2,285,288 | textura (concordia/MAT_Cloth_Patch_C) |
| `textures/concordia/MAT_Cloth_Patch_C/T_Cloth_Patch_C_Roughness.jpg` | 194,780 | textura (concordia/MAT_Cloth_Patch_C) |
| `textures/concordia/MAT_Cobble_Concordia/T_Cobble_Concordia_Albedo.jpg` | 1,954,783 | textura (concordia/MAT_Cobble_Concordia) |
| `textures/concordia/MAT_Cobble_Concordia/T_Cobble_Concordia_Normal.jpg` | 2,303,270 | textura (concordia/MAT_Cobble_Concordia) |
| `textures/concordia/MAT_Cobble_Concordia/T_Cobble_Concordia_Roughness.jpg` | 918,187 | textura (concordia/MAT_Cobble_Concordia) |
| `textures/concordia/MAT_Cobble_Concordia/concordia_cobble_concordia_albedo.png` | 8,849,016 | textura (concordia/MAT_Cobble_Concordia) |
| `textures/concordia/MAT_Cobble_Concordia/concordia_cobble_concordia_orm.png` | 2,743,161 | textura (concordia/MAT_Cobble_Concordia) |
| `textures/concordia/MAT_Ground_Cracked/T_Ground_Cracked_Albedo.jpg` | 2,044,506 | textura (concordia/MAT_Ground_Cracked) |
| `textures/concordia/MAT_Ground_Cracked/T_Ground_Cracked_Normal.jpg` | 2,860,067 | textura (concordia/MAT_Ground_Cracked) |
| `textures/concordia/MAT_Ground_Cracked/T_Ground_Cracked_Roughness.jpg` | 1,361,968 | textura (concordia/MAT_Ground_Cracked) |
| `textures/concordia/MAT_Ground_Cracked/concordia_ground_cracked_albedo.png` | 7,719,132 | textura (concordia/MAT_Ground_Cracked) |
| `textures/concordia/MAT_Ground_Cracked/concordia_ground_cracked_orm.png` | 6,501,105 | textura (concordia/MAT_Ground_Cracked) |
| `textures/concordia/MAT_Iron_Black/T_Iron_Black_Albedo.jpg` | 213,437 | textura (concordia/MAT_Iron_Black) |
| `textures/concordia/MAT_Iron_Black/T_Iron_Black_Normal.jpg` | 378,561 | textura (concordia/MAT_Iron_Black) |
| `textures/concordia/MAT_Iron_Black/T_Iron_Black_ORM.png` | 709,820 | textura (concordia/MAT_Iron_Black) |
| `textures/concordia/MAT_Iron_Black/T_Iron_Black_Roughness.jpg` | 206,091 | textura (concordia/MAT_Iron_Black) |
| `textures/concordia/MAT_Iron_Black/concordia_iron_black_albedo.png` | 1,030,705 | textura (concordia/MAT_Iron_Black) |
| `textures/concordia/MAT_Iron_Black/concordia_iron_black_orm.png` | 1,428,446 | textura (concordia/MAT_Iron_Black) |
| `textures/concordia/MAT_Limestone_Light/concordia_limestone_light_albedo.png` | 6,111,865 | textura (concordia/MAT_Limestone_Light) |
| `textures/concordia/MAT_Limestone_Worn/T_Limestone_Worn_Albedo.jpg` | 1,829,927 | textura (concordia/MAT_Limestone_Worn) |
| `textures/concordia/MAT_Limestone_Worn/T_Limestone_Worn_Normal.jpg` | 1,891,945 | textura (concordia/MAT_Limestone_Worn) |
| `textures/concordia/MAT_Limestone_Worn/T_Limestone_Worn_Roughness.jpg` | 1,446,708 | textura (concordia/MAT_Limestone_Worn) |
| `textures/concordia/MAT_Limestone_Worn/concordia_limestone_worn_albedo.png` | 7,615,477 | textura (concordia/MAT_Limestone_Worn) |
| `textures/concordia/MAT_Limestone_Worn/concordia_limestone_worn_orm.png` | 5,814,128 | textura (concordia/MAT_Limestone_Worn) |
| `textures/concordia/MAT_Plaza_Slab/T_Plaza_Slab_Albedo.jpg` | 213,172 | textura (concordia/MAT_Plaza_Slab) |
| `textures/concordia/MAT_Plaza_Slab/T_Plaza_Slab_Normal.jpg` | 195,350 | textura (concordia/MAT_Plaza_Slab) |
| `textures/concordia/MAT_Plaza_Slab/T_Plaza_Slab_Roughness.jpg` | 177,611 | textura (concordia/MAT_Plaza_Slab) |
| `textures/concordia/MAT_Plaza_Slab/concordia_plaza_slab_albedo.png` | 5,337,746 | textura (concordia/MAT_Plaza_Slab) |
| `textures/concordia/MAT_Plaza_Slab/concordia_plaza_slab_orm.png` | 5,400,594 | textura (concordia/MAT_Plaza_Slab) |
| `textures/concordia/MAT_Plaza_Slab_Travertino/T_Plaza_Slab_Travertino_Albedo.jpg` | 262,599 | textura (concordia/MAT_Plaza_Slab_Travertino) |
| `textures/concordia/MAT_Plaza_Slab_Travertino/T_Plaza_Slab_Travertino_Normal.jpg` | 223,212 | textura (concordia/MAT_Plaza_Slab_Travertino) |
| `textures/concordia/MAT_Plaza_Slab_Travertino/T_Plaza_Slab_Travertino_Roughness.jpg` | 180,281 | textura (concordia/MAT_Plaza_Slab_Travertino) |
| `textures/concordia/MAT_Plaza_Slab_Travertino/concordia_plaza_slab_travertino_albedo.png` | 5,308,496 | textura (concordia/MAT_Plaza_Slab_Travertino) |
| `textures/concordia/MAT_Plaza_Slab_Travertino/concordia_plaza_slab_travertino_orm.png` | 3,355,938 | textura (concordia/MAT_Plaza_Slab_Travertino) |
| `textures/concordia/MAT_Rock_Gray/T_Rock_Gray_Albedo.jpg` | 1,402,587 | textura (concordia/MAT_Rock_Gray) |
| `textures/concordia/MAT_Rock_Gray/T_Rock_Gray_Normal.jpg` | 2,293,668 | textura (concordia/MAT_Rock_Gray) |
| `textures/concordia/MAT_Rock_Gray/T_Rock_Gray_Roughness.jpg` | 1,163,555 | textura (concordia/MAT_Rock_Gray) |
| `textures/concordia/MAT_Rock_Gray/concordia_rock_gray_albedo.png` | 3,370,584 | textura (concordia/MAT_Rock_Gray) |
| `textures/concordia/MAT_Rock_Gray/concordia_rock_gray_orm.png` | 5,157,492 | textura (concordia/MAT_Rock_Gray) |
| `textures/concordia/MAT_Roof_Slate/concordia_roof_slate_albedo.png` | 1,505,216 | textura (concordia/MAT_Roof_Slate) |
| `textures/concordia/MAT_Roof_Tile_Ocher/T_Roof_Tile_Ocher_Albedo.jpg` | 249,550 | textura (concordia/MAT_Roof_Tile_Ocher) |
| `textures/concordia/MAT_Roof_Tile_Ocher/T_Roof_Tile_Ocher_Normal.jpg` | 220,520 | textura (concordia/MAT_Roof_Tile_Ocher) |
| `textures/concordia/MAT_Roof_Tile_Ocher/T_Roof_Tile_Ocher_Roughness.jpg` | 179,207 | textura (concordia/MAT_Roof_Tile_Ocher) |
| `textures/concordia/MAT_Roof_Tile_Ocher/concordia_roof_tile_ocher_albedo.png` | 1,892,397 | textura (concordia/MAT_Roof_Tile_Ocher) |
| `textures/concordia/MAT_Roof_Tile_Ocher/concordia_roof_tile_ocher_orm.png` | 889,317 | textura (concordia/MAT_Roof_Tile_Ocher) |
| `textures/concordia/MAT_Shard_Blue/T_Shard_Blue_Albedo.jpg` | 93,356 | textura (concordia/MAT_Shard_Blue) |
| `textures/concordia/MAT_Shard_Blue/T_Shard_Blue_Normal.jpg` | 143,418 | textura (concordia/MAT_Shard_Blue) |
| `textures/concordia/MAT_Shard_Blue/T_Shard_Blue_Roughness.jpg` | 68,718 | textura (concordia/MAT_Shard_Blue) |
| `textures/concordia/MAT_Shard_Blue/concordia_shard_blue_albedo.png` | 49,585 | textura (concordia/MAT_Shard_Blue) |
| `textures/concordia/MAT_Shard_Blue/concordia_shard_blue_normal.png` | 93,119 | textura (concordia/MAT_Shard_Blue) |
| `textures/concordia/MAT_Shard_Blue/concordia_shard_blue_orm.png` | 42,474 | textura (concordia/MAT_Shard_Blue) |
| `textures/concordia/MAT_Stone_Repair/T_Stone_Repair_Albedo.jpg` | 261,028 | textura (concordia/MAT_Stone_Repair) |
| `textures/concordia/MAT_Stone_Repair/T_Stone_Repair_Normal.jpg` | 289,772 | textura (concordia/MAT_Stone_Repair) |
| `textures/concordia/MAT_Stone_Repair/T_Stone_Repair_Roughness.jpg` | 156,978 | textura (concordia/MAT_Stone_Repair) |
| `textures/concordia/MAT_Stone_Repair/concordia_stone_repair_albedo.png` | 7,712,827 | textura (concordia/MAT_Stone_Repair) |
| `textures/concordia/MAT_Stone_Repair/concordia_stone_repair_orm.png` | 5,593,999 | textura (concordia/MAT_Stone_Repair) |
| `textures/concordia/MAT_TrophyCase/trophy_case_atlas_512.png` | 290,103 | textura (concordia/MAT_TrophyCase) |
| `textures/concordia/MAT_Vault_Stars/vault_stars_1k.png` | 56,190 | textura (concordia/MAT_Vault_Stars) |
| `textures/concordia/MAT_Wall_Gray/T_Wall_Gray_Albedo.jpg` | 2,124,186 | textura (concordia/MAT_Wall_Gray) |
| `textures/concordia/MAT_Wall_Gray/T_Wall_Gray_Normal.jpg` | 411,830 | textura (concordia/MAT_Wall_Gray) |
| `textures/concordia/MAT_Wall_Gray/T_Wall_Gray_Roughness.jpg` | 157,416 | textura (concordia/MAT_Wall_Gray) |
| `textures/concordia/MAT_Wall_Gray/concordia_wall_gray_albedo.png` | 6,953,076 | textura (concordia/MAT_Wall_Gray) |
| `textures/concordia/MAT_Wall_Gray/concordia_wall_gray_orm.png` | 5,389,964 | textura (concordia/MAT_Wall_Gray) |
| `textures/concordia/MAT_Wall_Runes/T_Wall_Runes_Albedo.jpg` | 271,684 | textura (concordia/MAT_Wall_Runes) |
| `textures/concordia/MAT_Wall_Runes/T_Wall_Runes_Emission.jpg` | 420,411 | textura (concordia/MAT_Wall_Runes) |
| `textures/concordia/MAT_Wall_Runes/T_Wall_Runes_Normal.jpg` | 522,259 | textura (concordia/MAT_Wall_Runes) |
| `textures/concordia/MAT_Wall_Runes/T_Wall_Runes_Roughness.jpg` | 190,016 | textura (concordia/MAT_Wall_Runes) |
| `textures/concordia/MAT_Wall_Runes/concordia_wall_runes_albedo.png` | 942,422 | textura (concordia/MAT_Wall_Runes) |
| `textures/concordia/MAT_Wall_Runes/concordia_wall_runes_emission.png` | 45,909 | textura (concordia/MAT_Wall_Runes) |
| `textures/concordia/MAT_Wall_Runes/concordia_wall_runes_normal.png` | 1,022,692 | textura (concordia/MAT_Wall_Runes) |
| `textures/concordia/MAT_Wall_Runes/concordia_wall_runes_orm.png` | 78,952 | textura (concordia/MAT_Wall_Runes) |
| `textures/concordia/MAT_Water/T_Water_Albedo.jpg` | 66,164 | textura (concordia/MAT_Water) |
| `textures/concordia/MAT_Water/T_Water_Normal.jpg` | 212,795 | textura (concordia/MAT_Water) |
| `textures/concordia/MAT_Water/T_Water_Roughness.jpg` | 49,484 | textura (concordia/MAT_Water) |
| `textures/concordia/MAT_Water/concordia_water_albedo.png` | 16,912 | textura (concordia/MAT_Water) |
| `textures/concordia/MAT_Water/concordia_water_normal.png` | 553,463 | textura (concordia/MAT_Water) |
| `textures/concordia/MAT_Water/concordia_water_orm.png` | 16,910 | textura (concordia/MAT_Water) |
| `textures/concordia/MAT_Wood_Dark/T_Wood_Dark_Albedo.jpg` | 781,282 | textura (concordia/MAT_Wood_Dark) |
| `textures/concordia/MAT_Wood_Dark/T_Wood_Dark_Normal.jpg` | 909,112 | textura (concordia/MAT_Wood_Dark) |
| `textures/concordia/MAT_Wood_Dark/T_Wood_Dark_Roughness.jpg` | 469,521 | textura (concordia/MAT_Wood_Dark) |
| `textures/concordia/MAT_Wood_Dark/concordia_wood_dark_albedo.png` | 1,377,642 | textura (concordia/MAT_Wood_Dark) |
| `textures/concordia/MAT_Wood_Dark/concordia_wood_dark_orm.png` | 1,091,875 | textura (concordia/MAT_Wood_Dark) |
| `textures/concordia/MAT_Wood_Light/concordia_wood_light_albedo.png` | 1,005,875 | textura (concordia/MAT_Wood_Light) |
| `textures/concordia/polyhaven.json` | 36,943 | textura (concordia) |
| `textures/concordia/polyhaven_src/broken_wall/broken_wall_AO_2k.jpg` | 1,483,267 | textura (concordia/polyhaven_src/broken_wall) |
| `textures/concordia/polyhaven_src/broken_wall/broken_wall_Diffuse_2k.jpg` | 2,382,913 | textura (concordia/polyhaven_src/broken_wall) |
| `textures/concordia/polyhaven_src/broken_wall/broken_wall_Rough_2k.jpg` | 1,215,009 | textura (concordia/polyhaven_src/broken_wall) |
| `textures/concordia/polyhaven_src/broken_wall/broken_wall_nor_gl_2k.jpg` | 3,578,159 | textura (concordia/polyhaven_src/broken_wall) |
| `textures/concordia/polyhaven_src/castle_wall_slates/castle_wall_slates_AO_2k.jpg` | 1,653,941 | textura (concordia/polyhaven_src/castle_wall_slates) |
| `textures/concordia/polyhaven_src/castle_wall_slates/castle_wall_slates_Diffuse_2k.jpg` | 2,381,426 | textura (concordia/polyhaven_src/castle_wall_slates) |
| `textures/concordia/polyhaven_src/castle_wall_slates/castle_wall_slates_Rough_2k.jpg` | 2,005,253 | textura (concordia/polyhaven_src/castle_wall_slates) |
| `textures/concordia/polyhaven_src/castle_wall_slates/castle_wall_slates_nor_gl_2k.jpg` | 4,054,865 | textura (concordia/polyhaven_src/castle_wall_slates) |
| `textures/concordia/polyhaven_src/castle_wall_varriation/castle_wall_varriation_AO_2k.jpg` | 1,600,880 | textura (concordia/polyhaven_src/castle_wall_varriation) |
| `textures/concordia/polyhaven_src/castle_wall_varriation/castle_wall_varriation_Diffuse_2k.jpg` | 2,386,019 | textura (concordia/polyhaven_src/castle_wall_varriation) |
| `textures/concordia/polyhaven_src/castle_wall_varriation/castle_wall_varriation_Rough_2k.jpg` | 1,643,779 | textura (concordia/polyhaven_src/castle_wall_varriation) |
| `textures/concordia/polyhaven_src/castle_wall_varriation/castle_wall_varriation_nor_gl_2k.jpg` | 3,537,669 | textura (concordia/polyhaven_src/castle_wall_varriation) |
| `textures/concordia/polyhaven_src/cobblestone_floor_001/cobblestone_floor_001_Diffuse_2k.jpg` | 2,394,580 | textura (concordia/polyhaven_src/cobblestone_floor_001) |
| `textures/concordia/polyhaven_src/cobblestone_floor_001/cobblestone_floor_001_Rough_2k.jpg` | 1,581,274 | textura (concordia/polyhaven_src/cobblestone_floor_001) |
| `textures/concordia/polyhaven_src/cobblestone_floor_001/cobblestone_floor_001_nor_gl_2k.jpg` | 3,683,849 | textura (concordia/polyhaven_src/cobblestone_floor_001) |
| `textures/concordia/polyhaven_src/dry_ground_01/dry_ground_01_AO_2k.jpg` | 2,014,209 | textura (concordia/polyhaven_src/dry_ground_01) |
| `textures/concordia/polyhaven_src/dry_ground_01/dry_ground_01_Diffuse_2k.jpg` | 2,541,635 | textura (concordia/polyhaven_src/dry_ground_01) |
| `textures/concordia/polyhaven_src/dry_ground_01/dry_ground_01_Rough_2k.jpg` | 1,456,821 | textura (concordia/polyhaven_src/dry_ground_01) |
| `textures/concordia/polyhaven_src/dry_ground_01/dry_ground_01_nor_gl_2k.jpg` | 1,080,854 | textura (concordia/polyhaven_src/dry_ground_01) |
| `textures/concordia/polyhaven_src/floor_tiles_02/floor_tiles_02_AO_2k.jpg` | 1,748,232 | textura (concordia/polyhaven_src/floor_tiles_02) |
| `textures/concordia/polyhaven_src/floor_tiles_02/floor_tiles_02_Diffuse_2k.jpg` | 1,381,118 | textura (concordia/polyhaven_src/floor_tiles_02) |
| `textures/concordia/polyhaven_src/floor_tiles_02/floor_tiles_02_Rough_2k.jpg` | 1,214,592 | textura (concordia/polyhaven_src/floor_tiles_02) |
| `textures/concordia/polyhaven_src/floor_tiles_02/floor_tiles_02_nor_gl_2k.jpg` | 540,151 | textura (concordia/polyhaven_src/floor_tiles_02) |
| `textures/concordia/polyhaven_src/hessian_380/hessian_380_AO_1k.jpg` | 537,495 | textura (concordia/polyhaven_src/hessian_380) |
| `textures/concordia/polyhaven_src/hessian_380/hessian_380_Diffuse_1k.jpg` | 944,914 | textura (concordia/polyhaven_src/hessian_380) |
| `textures/concordia/polyhaven_src/hessian_380/hessian_380_Metal_1k.jpg` | 849,875 | textura (concordia/polyhaven_src/hessian_380) |
| `textures/concordia/polyhaven_src/hessian_380/hessian_380_Rough_1k.jpg` | 956,823 | textura (concordia/polyhaven_src/hessian_380) |
| `textures/concordia/polyhaven_src/hessian_380/hessian_380_nor_gl_1k.jpg` | 1,076,074 | textura (concordia/polyhaven_src/hessian_380) |
| `textures/concordia/polyhaven_src/marble_01/marble_01_AO_2k.jpg` | 999,921 | textura (concordia/polyhaven_src/marble_01) |
| `textures/concordia/polyhaven_src/marble_01/marble_01_Diffuse_2k.jpg` | 1,269,188 | textura (concordia/polyhaven_src/marble_01) |
| `textures/concordia/polyhaven_src/marble_01/marble_01_Rough_2k.jpg` | 281,388 | textura (concordia/polyhaven_src/marble_01) |
| `textures/concordia/polyhaven_src/marble_01/marble_01_nor_gl_2k.jpg` | 409,581 | textura (concordia/polyhaven_src/marble_01) |
| `textures/concordia/polyhaven_src/metal_plate_02/metal_plate_02_AO_1k.jpg` | 208,277 | textura (concordia/polyhaven_src/metal_plate_02) |
| `textures/concordia/polyhaven_src/metal_plate_02/metal_plate_02_Diffuse_1k.jpg` | 625,917 | textura (concordia/polyhaven_src/metal_plate_02) |
| `textures/concordia/polyhaven_src/metal_plate_02/metal_plate_02_Metal_1k.jpg` | 551,170 | textura (concordia/polyhaven_src/metal_plate_02) |
| `textures/concordia/polyhaven_src/metal_plate_02/metal_plate_02_Rough_1k.jpg` | 911,772 | textura (concordia/polyhaven_src/metal_plate_02) |
| `textures/concordia/polyhaven_src/metal_plate_02/metal_plate_02_nor_gl_1k.jpg` | 183,264 | textura (concordia/polyhaven_src/metal_plate_02) |
| `textures/concordia/polyhaven_src/rock_boulder_cracked/rock_boulder_cracked_AO_2k.jpg` | 1,929,334 | textura (concordia/polyhaven_src/rock_boulder_cracked) |
| `textures/concordia/polyhaven_src/rock_boulder_cracked/rock_boulder_cracked_Diffuse_2k.jpg` | 3,962,095 | textura (concordia/polyhaven_src/rock_boulder_cracked) |
| `textures/concordia/polyhaven_src/rock_boulder_cracked/rock_boulder_cracked_Rough_2k.jpg` | 1,680,734 | textura (concordia/polyhaven_src/rock_boulder_cracked) |
| `textures/concordia/polyhaven_src/rock_boulder_cracked/rock_boulder_cracked_nor_gl_2k.jpg` | 4,144,084 | textura (concordia/polyhaven_src/rock_boulder_cracked) |
| `textures/concordia/polyhaven_src/rock_boulder_dry/rock_boulder_dry_AO_2k.jpg` | 2,182,922 | textura (concordia/polyhaven_src/rock_boulder_dry) |
| `textures/concordia/polyhaven_src/rock_boulder_dry/rock_boulder_dry_Diffuse_2k.jpg` | 3,437,626 | textura (concordia/polyhaven_src/rock_boulder_dry) |
| `textures/concordia/polyhaven_src/rock_boulder_dry/rock_boulder_dry_Rough_2k.jpg` | 2,706,723 | textura (concordia/polyhaven_src/rock_boulder_dry) |
| `textures/concordia/polyhaven_src/rock_boulder_dry/rock_boulder_dry_nor_gl_2k.jpg` | 3,307,320 | textura (concordia/polyhaven_src/rock_boulder_dry) |
| `textures/concordia/polyhaven_src/rocks_ground_02/rocks_ground_02_AO_2k.jpg` | 2,168,833 | textura (concordia/polyhaven_src/rocks_ground_02) |
| `textures/concordia/polyhaven_src/rocks_ground_02/rocks_ground_02_Diffuse_2k.jpg` | 3,224,700 | textura (concordia/polyhaven_src/rocks_ground_02) |
| `textures/concordia/polyhaven_src/rocks_ground_02/rocks_ground_02_Rough_2k.jpg` | 1,810,785 | textura (concordia/polyhaven_src/rocks_ground_02) |
| `textures/concordia/polyhaven_src/rocks_ground_02/rocks_ground_02_nor_gl_2k.jpg` | 5,387,529 | textura (concordia/polyhaven_src/rocks_ground_02) |
| `textures/concordia/polyhaven_src/roof_09/roof_09_AO_1k.jpg` | 137,405 | textura (concordia/polyhaven_src/roof_09) |
| `textures/concordia/polyhaven_src/roof_09/roof_09_Diffuse_1k.jpg` | 553,309 | textura (concordia/polyhaven_src/roof_09) |
| `textures/concordia/polyhaven_src/roof_09/roof_09_Rough_1k.jpg` | 503,295 | textura (concordia/polyhaven_src/roof_09) |
| `textures/concordia/polyhaven_src/roof_09/roof_09_nor_gl_1k.jpg` | 325,412 | textura (concordia/polyhaven_src/roof_09) |
| `textures/concordia/polyhaven_src/rustic_stone_wall/rustic_stone_wall_AO_2k.jpg` | 2,254,805 | textura (concordia/polyhaven_src/rustic_stone_wall) |
| `textures/concordia/polyhaven_src/rustic_stone_wall/rustic_stone_wall_Diffuse_2k.jpg` | 3,525,377 | textura (concordia/polyhaven_src/rustic_stone_wall) |
| `textures/concordia/polyhaven_src/rustic_stone_wall/rustic_stone_wall_Rough_2k.jpg` | 2,649,266 | textura (concordia/polyhaven_src/rustic_stone_wall) |
| `textures/concordia/polyhaven_src/rustic_stone_wall/rustic_stone_wall_nor_gl_2k.jpg` | 4,739,942 | textura (concordia/polyhaven_src/rustic_stone_wall) |
| `textures/concordia/polyhaven_src/sandstone_cracks/sandstone_cracks_AO_2k.jpg` | 2,043,727 | textura (concordia/polyhaven_src/sandstone_cracks) |
| `textures/concordia/polyhaven_src/sandstone_cracks/sandstone_cracks_Diffuse_2k.jpg` | 2,870,078 | textura (concordia/polyhaven_src/sandstone_cracks) |
| `textures/concordia/polyhaven_src/sandstone_cracks/sandstone_cracks_Rough_2k.jpg` | 1,569,280 | textura (concordia/polyhaven_src/sandstone_cracks) |
| `textures/concordia/polyhaven_src/sandstone_cracks/sandstone_cracks_nor_gl_2k.jpg` | 4,545,235 | textura (concordia/polyhaven_src/sandstone_cracks) |
| `textures/concordia/polyhaven_src/stone_wall_02/stone_wall_02_AO_2k.jpg` | 2,730,634 | textura (concordia/polyhaven_src/stone_wall_02) |
| `textures/concordia/polyhaven_src/stone_wall_02/stone_wall_02_Diffuse_2k.jpg` | 2,554,296 | textura (concordia/polyhaven_src/stone_wall_02) |
| `textures/concordia/polyhaven_src/stone_wall_02/stone_wall_02_Rough_2k.jpg` | 1,215,515 | textura (concordia/polyhaven_src/stone_wall_02) |
| `textures/concordia/polyhaven_src/stone_wall_02/stone_wall_02_nor_gl_2k.jpg` | 3,715,793 | textura (concordia/polyhaven_src/stone_wall_02) |
| `textures/concordia/polyhaven_src/weathered_planks/weathered_planks_AO_1k.jpg` | 594,177 | textura (concordia/polyhaven_src/weathered_planks) |
| `textures/concordia/polyhaven_src/weathered_planks/weathered_planks_Diffuse_1k.jpg` | 599,581 | textura (concordia/polyhaven_src/weathered_planks) |
| `textures/concordia/polyhaven_src/weathered_planks/weathered_planks_Rough_1k.jpg` | 218,802 | textura (concordia/polyhaven_src/weathered_planks) |
| `textures/concordia/polyhaven_src/weathered_planks/weathered_planks_nor_gl_1k.jpg` | 681,552 | textura (concordia/polyhaven_src/weathered_planks) |
| `textures/lib/CobblestoneFloor001/T_CobblestoneFloor001_Albedo.png` | 320,965 | textura (lib/CobblestoneFloor001) |
| `textures/lib/CobblestoneFloor001/T_CobblestoneFloor001_NormalGL.png` | 650,058 | textura (lib/CobblestoneFloor001) |
| `textures/lib/CobblestoneFloor001/T_CobblestoneFloor001_Roughness.png` | 110,160 | textura (lib/CobblestoneFloor001) |
| `textures/lib/IronBlack/T_IronBlack_Albedo.png` | 372,422 | textura (lib/IronBlack) |
| `textures/lib/IronBlack/T_IronBlack_NormalGL.png` | 691,735 | textura (lib/IronBlack) |
| `textures/lib/IronBlack/T_IronBlack_Roughness.png` | 300,576 | textura (lib/IronBlack) |
| `textures/lib/RockBoulderCracked/T_RockBoulderCracked_Albedo.png` | 637,430 | textura (lib/RockBoulderCracked) |
| `textures/lib/RockBoulderCracked/T_RockBoulderCracked_NormalGL.png` | 1,231,565 | textura (lib/RockBoulderCracked) |
| `textures/lib/RockBoulderCracked/T_RockBoulderCracked_Roughness.png` | 148,430 | textura (lib/RockBoulderCracked) |
| `textures/lib/RocksGround02/T_RocksGround02_Albedo.png` | 603,116 | textura (lib/RocksGround02) |
| `textures/lib/RocksGround02/T_RocksGround02_NormalGL.png` | 574,017 | textura (lib/RocksGround02) |
| `textures/lib/RocksGround02/T_RocksGround02_Roughness.png` | 9,412 | textura (lib/RocksGround02) |
| `textures/lib/RoofSlate/T_RoofSlate_Albedo.png` | 427,596 | textura (lib/RoofSlate) |
| `textures/lib/RoofSlate/T_RoofSlate_NormalGL.png` | 267,507 | textura (lib/RoofSlate) |
| `textures/lib/RoofSlate/T_RoofSlate_Roughness.png` | 192,120 | textura (lib/RoofSlate) |
| `textures/lib/RoofTileOchre/T_RoofTileOchre_Albedo.png` | 379,710 | textura (lib/RoofTileOchre) |
| `textures/lib/RoofTileOchre/T_RoofTileOchre_NormalGL.png` | 325,812 | textura (lib/RoofTileOchre) |
| `textures/lib/RoofTileOchre/T_RoofTileOchre_Roughness.png` | 170,735 | textura (lib/RoofTileOchre) |
| `textures/lib/SandstoneCracks/T_SandstoneCracks_Albedo.png` | 583,261 | textura (lib/SandstoneCracks) |
| `textures/lib/SandstoneCracks/T_SandstoneCracks_NormalGL.png` | 553,439 | textura (lib/SandstoneCracks) |
| `textures/lib/SandstoneCracks/T_SandstoneCracks_Roughness.png` | 143,032 | textura (lib/SandstoneCracks) |
| `textures/lib/StoneBand/T_StoneBand_Albedo.png` | 1,409,421 | textura (lib/StoneBand) |
| `textures/lib/StoneBand/T_StoneBand_NormalGL.png` | 594,435 | textura (lib/StoneBand) |
| `textures/lib/StoneBand/T_StoneBand_Roughness.png` | 121,008 | textura (lib/StoneBand) |
| `textures/lib/StoneWall02/T_StoneWall02_Albedo.png` | 431,991 | textura (lib/StoneWall02) |
| `textures/lib/StoneWall02/T_StoneWall02_NormalGL.png` | 397,333 | textura (lib/StoneWall02) |
| `textures/lib/StoneWall02/T_StoneWall02_Roughness.png` | 14,258 | textura (lib/StoneWall02) |
| `textures/lib/WallGranite/T_WallGranite_Albedo.png` | 1,641,877 | textura (lib/WallGranite) |
| `textures/lib/WallGranite/T_WallGranite_NormalGL.png` | 900,461 | textura (lib/WallGranite) |
| `textures/lib/WallGranite/T_WallGranite_Roughness.png` | 116,073 | textura (lib/WallGranite) |
| `textures/lib/WallPatch/T_WallPatch_Albedo.png` | 477,939 | textura (lib/WallPatch) |
| `textures/lib/WallPatch/T_WallPatch_NormalGL.png` | 451,950 | textura (lib/WallPatch) |
| `textures/lib/WallPatch/T_WallPatch_Roughness.png` | 17,926 | textura (lib/WallPatch) |
| `textures/lib/WoodDark/T_WoodDark_Albedo.png` | 981,128 | textura (lib/WoodDark) |
| `textures/lib/WoodDark/T_WoodDark_NormalGL.png` | 1,179,204 | textura (lib/WoodDark) |
| `textures/lib/WoodDark/T_WoodDark_Roughness.png` | 245,824 | textura (lib/WoodDark) |
| `textures/personajes/elfo/elfo_m_albedo_abedul_1k.png` | 246,339 | textura (personajes/elfo) |
| `textures/personajes/elfo/elfo_m_albedo_corteza_1k.png` | 192,224 | textura (personajes/elfo) |
| `textures/personajes/elfo/elfo_m_normal_1k.png` | 572,828 | textura (personajes/elfo) |
| `textures/personajes/elfo/elfo_m_ojos_albedo_256.png` | 9,635 | textura (personajes/elfo) |
| `textures/personajes/elfo/elfo_m_orm_1k.png` | 271,424 | textura (personajes/elfo) |
| `textures/personajes/sanador/sanador_atlas_albedo_1k.png` | 714,898 | textura (personajes/sanador) |
| `textures/personajes/sanador/sanador_atlas_emision_1k.png` | 3,317 | textura (personajes/sanador) |
| `textures/personajes/sanador/sanador_atlas_normal_1k.png` | 732,703 | textura (personajes/sanador) |
| `textures/personajes/sanador/sanador_atlas_orm_1k.png` | 400,653 | textura (personajes/sanador) |
| `textures/props/PROP_AV_Cheese_Wheel_normal_512.png` | 225,986 | textura (props) |
| `textures/props/PROP_AV_Grain_Sack_normal_512.png` | 208,829 | textura (props) |
| `textures/props/PROP_AV_Grapes_normal_512.png` | 329,735 | textura (props) |
| `textures/props/PROP_AV_Handaxe_normal_512.png` | 198,801 | textura (props) |
| `textures/props/PROP_AV_Herb_Bundle_normal_512.png` | 134,607 | textura (props) |
| `textures/props/PROP_Q_Barrel_Holder_normal_1k.png` | 535,399 | textura (props) |
| `textures/props/PROP_Q_BookStand_normal_1k.png` | 771,881 | textura (props) |
| `textures/props/PROP_Q_Bucket_Wooden_1_normal_512.png` | 270,021 | textura (props) |
| `textures/props/PROP_Q_CandleStick_normal_512.png` | 124,185 | textura (props) |
| `textures/props/PROP_Q_Chain_Coil_normal_1k.png` | 668,103 | textura (props) |
| `textures/props/PROP_Q_Chandelier_normal_1k.png` | 645,973 | textura (props) |
| `textures/props/PROP_Q_Chest_Wood_normal_1k.png` | 399,570 | textura (props) |
| `textures/props/PROP_Q_Coin_Pile_normal_512.png` | 214,385 | textura (props) |
| `textures/props/PROP_Q_Potion_4_normal_512.png` | 363,280 | textura (props) |
| `textures/props/PROP_Q_Pouch_Large_normal_512.png` | 421,577 | textura (props) |
| `textures/props/PROP_Q_Scroll_1_normal_512.png` | 425,540 | textura (props) |
| `textures/props/PROP_Q_Scroll_2_normal_512.png` | 435,197 | textura (props) |
| `textures/props/PROP_Q_WeaponStand_normal_1k.png` | 772,159 | textura (props) |
| `textures/streets/T_StreetMasks.png` | 51,210 | textura (streets) |
| `textures/wall/T_Granite_Courses_albedo.png` | 1,389,903 | textura (wall) |
| `textures/wall/T_Granite_Courses_normal.png` | 242,476 | textura (wall) |
| `textures/wall/T_Patch_Stone_albedo.png` | 339,286 | textura (wall) |
| `textures/wall/T_Patch_Stone_normal.png` | 56,357 | textura (wall) |
| `textures/wall/T_Runes_emission.png` | 2,267 | textura (wall) |
| `textures/wall/T_Slate_albedo.png` | 202,454 | textura (wall) |
| `textures/wall/T_Slate_normal.png` | 38,271 | textura (wall) |
| `textures/wall/T_TileOchre_albedo.png` | 281,703 | textura (wall) |
| `textures/wall/T_Wood_Dark_albedo.png` | 169,950 | textura (wall) |
| `tools/blender/audit_materials.py` | 9,066 | auditoria de materiales y memoria de texturas (etapa 17). Lee blender/concordia_v17.blend y los .glb de export/godot. Escribe docs/reports/stage17_materials.json. - por material: grafo (tipos de nodo), color base / textu… |
| `tools/blender/bld_kit.py` | 39,636 | etapa 12: kit modular de edificios (generadores parametricos en bmesh). Convencion de modulo de muro: plano X-Z, x en [-w/2, w/2], z en [0, h], grosor en Y centrado en 0 con la cara EXTERIOR en +Y (+t/2). Grilla 1 m, mod… |
| `tools/blender/build_pj1_elfo.py` | 33,269 | PJ1: cuerpo base del elfo masculino (blender/elfo_v01.blend). Base MakeHuman via MPFB 2.0.18 (assets CC0); proporciones, cara, orejas y texturas propias de Concordia. Pasos (python build_pj1_elfo.py -- <paso> ...): medir… |
| `tools/blender/build_pj2_sanador.py` | 11,782 | PJ2: cabello del elfo y conjunto inicial del Sanador (CLASE_SANADOR, provisional), calidad normal. Parte de blender/elfo_v01.blend (no se modifica) y guarda blender/elfo_v02.blend. piezas Robe_Top, Robe_Skirt, Hood, Belt… |
| `tools/blender/build_pj3_rig.py` | 19,814 | PJ3: esqueleto del elfo (concordia_rig.py) y pesos de cuerpo, ropa del Sanador y pelo. Parte de blender/elfo_v02.blend (no se modifica) y guarda blender/elfo_v03.blend. rig 70 huesos (56 del SkeletonProfileHumanoid + 14 … |
| `tools/blender/build_pj4_anim.py` | 13,375 | PJ4: animaciones propias del Sanador hechas a mano sobre el esqueleto del elfo (PJ3). Parte de blender/elfo_v03.blend (no se modifica) y guarda blender/elfo_v04.blend. 30 fps, sin movimiento de raiz (Root fijo; la cadera… |
| `tools/blender/build_pj4b_ual_seleccion.py` | 15,929 | PJ4b: seleccion de animaciones de la Universal Animation Library (Quaternius, Standard, CC0) para el elfo Sanador, con los nombres finales, sobre los esqueletos ORIGINALES de la UAL (no se retargetea en Blender: lo hace … |
| `tools/blender/build_pj5_lods_export.py` | 17,132 | PJ5: LODs, exportacion y cierre del personaje (elfo + equipo inicial del Sanador). Parte de blender/elfo_v04.blend (no se modifica) y guarda blender/concordia_personajes_master.blend (version en la propiedad de escena "c… |
| `tools/blender/build_stage02.py` | 3,016 | Etapa 02 completa (orquestador). Genera concordia_v02.blend desde v01. Pasos (en orden): terrain stage02_terrain.py malla MAESTRA TRN_City (1 m) + mascaras + QA de pendientes structures stage02_structures.py pretiles, co… |
| `tools/blender/build_stage03.py` | 2,309 | Etapa 03 (Plaza del Portal). Genera concordia_v03.blend desde v02. Pasos: plaza (terreno + piezas + marcadores) -> shading (AO y mascaras de nuevo) -> chunks + export (.glb del terreno, estructuras y plaza) -> comprobaci… |
| `tools/blender/build_stage04.py` | 12,054 | Etapa 04 (kit modular de muralla). Genera concordia_v04.blend desde v03. Pasos: texturas (si faltan) -> kit + montaje (stage04_wall) -> comprobaciones -> export: export/godot/concordia_wall_kit.glb piezas del kit (+ hijo… |
| `tools/blender/build_stage05.py` | 3,207 | Etapa 05 (red de calles y parcelas de los 4 distritos cardinales). v04 -> v05. Pasos: raster de obstaculos (escena) -> plan (stage05_layout, seed 11) -> cortes, alturas, mascaras y marcadores (stage05_streets) -> AO + ma… |
| `tools/blender/build_stage06.py` | 3,263 | Etapa 06 (Moradas: parcelas, calles de servicio, escaleras, mascaras). v05 -> v06. Pasos: raster de obstaculos -> stage06_moradas (trazado, terreno, mascaras, escaleras, pretiles, oclusion, marcadores) -> AO + mask_pack … |
| `tools/blender/build_stage07.py` | 2,896 | Etapa 07 (Cauce, puentes, arcos entre barrios, escalinatas). v06 -> v07. Pasos: stage07_cauce (canal, puentes, arcos, escalinatas, remiendos, marcadores) -> AO + mask_pack + material -> chunks + export (concordia_cauce.g… |
| `tools/blender/build_stage08.py` | 1,629 | Etapa 08 (terreno exterior de ceniza, r 212-400). v07 -> v08. Uso: python tools/blender/build_stage08.py [--in v07.blend] [--out v08.blend] [--no-export] |
| `tools/blender/build_stage09.py` | 3,855 | Etapa 09 (materiales glTF 2048, UV de mundo, asignacion por mascaras). v08 -> v09. Uso: python tools/blender/build_stage09.py [--no-bake] [--no-export] |
| `tools/blender/build_stage10.py` | 4,974 | Etapa 10 (texturas reales de Poly Haven, ORM, mascaras de taludes y foso, transiciones). v09 -> v10. Antes: python tools/blender/stage10_polyhaven.py (descarga originales + albedo ajustado + ORM + polyhaven.json) Uso: py… |
| `tools/blender/build_stage11.py` | 5,281 | Etapa 11: preparacion para Godot 4. concordia_v10.blend -> concordia_master_v11.blend + export/godot/*.glb Salidas: export/godot/concordia_terrain_<distrito>.glb plaza, mercado, oficios, clases, razas, moradas, exterior … |
| `tools/blender/build_stage12.py` | 9,648 | Etapa 12 (paso 1): kit modular de edificios + assembler + casa de prueba 12 x 9 m, 2 plantas. concordia_master_v11.blend -> concordia_v12.blend (se guarda ANTES de empezar y otra vez al final). Uso: python tools/blender/… |
| `tools/blender/build_stage13.py` | 4,993 | Etapa 13: el Portal y sus elementos. concordia_v12.blend -> concordia_v13.blend (guardada antes de empezar) + export/godot/concordia_portal.glb + docs/reports/stage13_portal.json. Los marcadores de prueba de la etapa 03 … |
| `tools/blender/build_stage14.py` | 4,784 | Etapa 14: Obelisco de los Pisos. concordia_v13.blend -> concordia_v14.blend (guardada antes de empezar) + export/godot/concordia_obelisk.glb + docs/reports/stage14_obelisk.json |
| `tools/blender/build_stage15.py` | 19,837 | Etapa 15: Torre del Faro. concordia_v14.blend -> concordia_v15.blend (guardada antes de empezar) + export/godot/concordia_faro.glb + docs/reports/stage15_faro.json Ademas: piezas PIPE_Light_* en BLD_KIT y la curva CRV_Li… |
| `tools/blender/build_stage16.py` | 17,774 | Etapa 16: Santuario del Retorno (NO) y Salon de las Hazanas (SE). concordia_v15.blend -> concordia_v16.blend (guardada antes de empezar) + export/godot/concordia_santuario.glb + export/godot/concordia_salon_hazanas.glb +… |
| `tools/blender/build_stage17.py` | 12,532 | Etapa 17: decisiones sobre el Faro (E3) y pendientes A-E. concordia_v16.blend -> concordia_v17.blend (guardada antes de empezar) 1. CRV_LightPipe_Tesoreria_Faro: primer punto provisional (MARKER_PipeOutlet_TesoreriaMural… |
| `tools/blender/build_stage18.py` | 27,037 | Etapa 18 (E5): el Mercado. concordia_v17.blend -> concordia_v18.blend (guardada antes de empezar) + export/godot/concordia_mercado.glb + docs/reports/stage18_mercado.json Kit (concordia_buildings.build_building / fit_iso… |
| `tools/blender/build_stage19.py` | 27,247 | Etapa 19 (E6): distrito Este (Oficios). concordia_v18.blend -> concordia_v19.blend (guardada antes) + export/godot/concordia_oficios.glb (+ concordia_gremio_cazadores_sin_parcela.glb) + docs/reports/stage19_oficios.json … |
| `tools/blender/build_stage20.py` | 16,952 | Etapa 20 (E7): distrito de las Clases. concordia_v19.blend -> concordia_v20.blend (guardada antes) + export/godot/concordia_clases.glb + docs/reports/stage20_clases.json + docs/captures/stage20_presets.png Uso: python bu… |
| `tools/blender/build_stage21.py` | 27,221 | Etapa 21 (E8): barrios de las razas. concordia_v20.blend -> concordia_v21.blend (guardada antes) + export/godot/concordia_razas.glb + docs/reports/stage21_razas.json Uso: python build_stage21.py [N_RAZAS] (por defecto st… |
| `tools/blender/build_stage22.py` | 25,077 | Etapa 22 (E9): conexiones. concordia_v21.blend -> concordia_v22.blend (guardada antes) + export/godot/concordia_conexiones.glb + terrenos por distrito y marcadores reexportados (sin los provisionales) + docs/reports/stag… |
| `tools/blender/build_stage23.py` | 20,656 | Etapa 23 (E10): viviendas de las Moradas. concordia_v22.blend -> concordia_v23.blend (guardada antes) + export/godot/moradas_NE.glb, _NO, _SE, _SO + docs/reports/stage23_moradas.json 1. Plan de secciones: cada casa parte… |
| `tools/blender/build_stage24.py` | 46,037 | Etapa 24 (E11): preparacion de todos los edificios para Godot 4 y verificacion final. concordia_v23.blend -> concordia_v24.blend (version final) + export/godot/bld_*.glb + docs/reports/stage24_godot.json 1. Limpieza de m… |
| `tools/blender/build_stage25.py` | 23,258 | Etapa 25 (E12): decisiones del usuario sobre las pendientes. concordia_v24.blend -> concordia_v25.blend (version final) + docs/reports/stage25_decisiones.json + pipeline de Godot de la etapa 24 sobre el resultado (docs/r… |
| `tools/blender/build_stage26.py` | 13,716 | Etapa 26 (E13): decisiones del usuario sobre el balance de la etapa 25. concordia_v25.blend -> concordia_v26.blend + docs/reports/stage26_decisiones.json Pasos (en el orden pedido; cada uno abre v26 si ya existe, o v25 l… |
| `tools/blender/build_stage27.py` | 14,317 | Etapa 27 (E14): kit de interiores, sala de prueba 8 x 6 y piloto del Banco. -> blender/concordia_interiors_v01.blend (materiales copiados de concordia_v26.blend), export/godot/int_banco.glb, docs/reports/stage27_interior… |
| `tools/blender/build_stage28_city.py` | 32,577 | Etapa 28 (ciudad): pendientes de la etapa 26 decididos por el usuario. concordia_v26.blend -> concordia_v28.blend + docs/reports/stage28_ciudad.json faro punto 10: MER_Casa_01 (decoracion) baja de 3 a 2 plantas hasta que… |
| `tools/blender/build_stage28_import.py` | 28,879 | Etapa 28: importacion de props CC0 aprobados (Quaternius Fantasy Props MegaKit, Avramania "Low Poly Medieval" en Sketchfab) a la coleccion BLD_PROPS_INT de blender/concordia_props_v01.blend (despues de build_stage28_prop… |
| `tools/blender/build_stage28_int.py` | 9,035 | Etapa 28: vitrina de trofeos (3 variantes, LOD1/LOD2) e interiores tipo de las Moradas. -> blender/concordia_moradas_int_v01.blend, export/godot/int_morada_<plantilla>.glb, export/godot/props_trophy_cases.glb, docs/repor… |
| `tools/blender/build_stage28_props.py` | 5,252 | Etapa 28: props hechos a mano (props_mano.py) en la coleccion BLD_PROPS_INT. -> blender/concordia_props_v01.blend, export/godot/props_int_mano.glb, docs/reports/stage28_props_mano.json Comprueba por prop: <= 1,000 triang… |
| `tools/blender/build_stage29_int.py` | 12,789 | Etapa 29: interiores unicos (Tesoreria de la Muralla, Santuario del Retorno, ...). -> blender/concordia_interiors_unicos_v01.blend, export/godot/int_<nombre>.glb, docs/reports/stage29_<nombre>.json Kit, convenciones y co… |
| `tools/blender/capture_pj1.py` | 6,952 | capturas del PJ1 (cuerpo base del elfo). Fondo gris neutro, luz uniforme (cielo gris + luz de relleno suave), camaras ortograficas. pj1_tpose frente, lado y espalda en una hoja (ortograficas) pj1_cara cara y orejas de ce… |
| `tools/blender/capture_pj2.py` | 4,367 | capturas del PJ2 (cabello y ropa inicial del Sanador) sobre blender/elfo_v02.blend. tpose frente, lado y espalda (ortograficas, fondo gris, luz uniforme) iso CAM_Iso (direccion de la ciudad) a ortho 6 (escala de juego) y… |
| `tools/blender/capture_pj3.py` | 7,424 | capturas del PJ3 (esqueleto y pesos) sobre blender/elfo_v03.blend. poses_cuerpo las 10 poses de prueba solo con el cuerpo (para juzgar los pesos de las articulaciones) poses_ropa las 10 poses con la ropa del Sanador y el… |
| `tools/blender/capture_pj4.py` | 4,749 | capturas del PJ4 (animaciones del Sanador) sobre blender/elfo_v04.blend (no se guarda). Tres fotogramas clave por animacion con la camara isometrica del juego (elevacion 35,26 grados, 45 grados de azimut, ortografica), m… |
| `tools/blender/capture_pj5.py` | 2,598 | capturas del PJ5 (LODs) sobre blender/concordia_personajes_master.blend (no se guarda). Por LOD (0, 1, 2): de frente (cuerpo entero), isometrica (35,26 grados, como el juego) y dos de cerca para la silueta: orejas (cabez… |
| `tools/blender/capture_stage01.py` | 8,258 | capturas de verificacion de la etapa 01. Abre concordia_v01.blend, anade PROXIES TEMPORALES (no se guardan) para hacer visibles los Empties y las cotas de referencia, renderiza con Cycles (CPU) y rotula los marcadores pr… |
| `tools/blender/capture_stage02.py` | 16,342 | capturas de verificacion de la etapa 02 (v2: muros laterales, plazoletas, escalinatas, pretiles, material con borde + AO). Renderiza con Cycles CPU usando los MATERIALES REALES (MAT_Terrain_City, MAT_Stone_Limestone); so… |
| `tools/blender/capture_stage03.py` | 9,313 | capturas de verificacion de la etapa 03 (Plaza del Portal). Materiales reales; luz y cielo temporales. Los volumenes del Faro (40 m) y del Obelisco (25 m) se muestran como PROXIES TEMPORALES semitransparentes (no se guar… |
| `tools/blender/capture_stage04.py` | 9,843 | capturas de la etapa 04 (muralla). eye_puerta_Alba_dentro altura de personaje en la plazoleta de Oficios mirando la puerta Alba (k=0) iso_torre_linterna CAM_Iso (ortho 50) sobre la torre de guardia k=44 (330 grados), al … |
| `tools/blender/capture_stage05.py` | 8,543 | capturas de la etapa 05 (calles y parcelas). cenital render cenital del terreno (Norte arriba) + parcelas y calles coloreadas por distrito plan plano 2D del trazado (sin render) con leyenda iso_<distrito> CAM_Iso (ortho … |
| `tools/blender/capture_stage06.py` | 5,260 | capturas de la etapa 06 (Moradas). iso_<Morada> CAM_Iso (ortho 100) sobre cada Morada con volumenes provisionales de casa por tipo (habitacion / casa_pequena / casa_grande) y la puerta marcada en blanco. iso_SE_puertas d… |
| `tools/blender/capture_stage07.py` | 6,122 | capturas de la etapa 07 (Cauce, puentes, arcos, escalinatas). iso_cauce_oficios CAM_Iso (ortho 110) sobre el tramo radial del Cauce en Oficios iso_cauce_detalle CAM_Iso (ortho 35) puente + muelle de Pescadores + hueco de… |
| `tools/blender/capture_stage08.py` | 3,801 | capturas de la etapa 08 (exterior de ceniza). iso_overview_exterior CAM_Iso con ortho temporal 840 (ciudad + exterior + acantilados) eye_mirador_exterior desde el balcon del mirador k=18 (NO) mirando hacia fuera: capas d… |
| `tools/blender/capture_stage09.py` | 2,360 | capturas de la etapa 09 (materiales). materiales_esferas esfera de 1 m por material (UV de mundo, como en el juego), con etiqueta iso_ciudad CAM_Iso, ortho temporal 460, ciudad entera con materiales iso_mercado CAM_Iso o… |
| `tools/blender/capture_stage10.py` | 8,820 | capturas de la etapa 10 (texturas Poly Haven). materiales esfera de 1.6 m + plano de 4 x 4 m por material (UV de mundo), CAM_Iso iso_ciudad CAM_Iso ortho 460 iso_exterior_taludes CAM_Iso ortho 90 en el SE: talud (roca + … |
| `tools/blender/capture_stage11.py` | 2,152 | captura de la etapa 11: silueta de la ciudad con los chunks LOD0 frente a LOD2 (CAM_Iso, ortho 460). Salida: docs/captures/stage11_lod0_vs_lod2.png (izquierda LOD0, derecha LOD2). |
| `tools/blender/capture_stage12.py` | 5,660 | capturas de la etapa 12 (kit de edificios). kit_sheet_muros 18 modulos de muro (6 tipos x 3 variantes), CAM_Iso kit_sheet_estructura esquinas, entramado, contrafuerte, cornisa, arcos, escalera, balcones, tejados, chimene… |
| `tools/blender/capture_stage13.py` | 2,891 | capturas de la etapa 13 (Portal). portal_iso CAM_Iso ortho 46 sobre el Portal (velo, piedras, atrio de descenso) portal_avenida_n a 1.7 m de altura en la avenida Norte (y = 46), mirando al Portal portal_runas primer plan… |
| `tools/blender/capture_stage14.py` | 3,352 | capturas de la etapa 14 (Obelisco de los Pisos). Solo para la captura se encienden los pisos 1..37 (MAT_Obelisk_Mark_Lit por objeto), como haria Godot; el .blend guardado los deja todos apagados. obelisco_iso CAM_Iso ort… |
| `tools/blender/capture_stage15.py` | 4,800 | capturas de la etapa 15 (Torre del Faro). faro_iso CAM_Iso ortho 62 (torre completa + arranque del haz) faro_galeria primer plano de la galeria con el cristal (desde fuera, a la altura de la galeria) faro_calle desde la … |
| `tools/blender/capture_stage16.py` | 5,539 | capturas de la etapa 16 (Santuario del Retorno y Salon de las Hazanas). santuario_iso CAM_Iso ortho 30 santuario_calle desde la plaza (+Y), ojo a 1.7 m santuario_pozo SANTUARIO_Well (modelo aparte para el interior) con e… |
| `tools/blender/capture_stage17.py` | 2,534 | capturas de la etapa 17. faro_canales base del Faro desde la plaza: canales de la torre unidos a los 4 canales del suelo faro_cartelas ultima vuelta de la rampa: cartelas de piedra y barandillas continuas portal Portal c… |
| `tools/blender/capture_stage17_lod.py` | 5,635 | etapa 17, pendiente D: manchas de material en LOD2. CAM_Iso a ortho 45 y 120 (1920 px de ancho), LOD0 frente a LOD2 de cada edificio, recortado al edificio. Escribe docs/captures/stage17_lod2_test.png y docs/reports/stag… |
| `tools/blender/capture_stage18.py` | 5,203 | capturas de la etapa 18 (E5, Mercado). mercado_iso distrito completo, CAM_Iso ortho 150 tesoreria primer plano 3/4 desde la avenida: porticada, balanzas, torre del reloj y salidas de tubos posada desde la calle (ojo 1.7 … |
| `tools/blender/capture_stage19.py` | 4,662 | capturas de la etapa 19 (E6, Oficios): isometrica del distrito y una isometrica (direccion de CAM_Iso) de cada edificio encuadrada en su rasgo distintivo. `-- nombre ...` para repetir solo algunas. |
| `tools/blender/capture_stage20.py` | 4,206 | capturas de la etapa 20 (E7, Clases). clases_iso distrito, CAM_Iso ortho 150 (haz del Faro oculto) plaza_armas Plaza de las Armas, CAM_Iso ortho 64: maniquies, blancos, postes, valla salon_iso Salon de clase 02 (fachada … |
| `tools/blender/capture_stage21.py` | 6,368 | capturas de la etapa 21 (E8, Razas). barrio_01..06 isometrica de cada barrio (direccion de CAM_Iso, misma escala ortho para los 6, haz del Faro oculto) comparacion los 6 barrios lado a lado (3 x 2) con su preset: materia… |
| `tools/blender/capture_stage22.py` | 6,228 | capturas de la etapa 22 (E9, Conexiones). puente_iso Puente 01 (diagonal NE) con la escalinata monumental NE, CAM_Iso ortho 34 puente_calle Puente 01 desde la orilla del Cauce, ojo a 1.7 m (arco rebajado, dovelas, sillar… |
| `tools/blender/capture_stage23.py` | 4,504 | capturas de la etapa 23 (E10, Moradas). conjunto_NE/NO/SO/SE isometrica de cada conjunto (CAM_Iso ortho 140): comprobacion de techos escalonados terraza_iso una terraza completa (Morada NO, terraza 6: 18 casas) en isomet… |
| `tools/blender/capture_stage24.py` | 3,239 | capturas de la etapa 24 (E11, version final para Godot): 8 vistas. portal, mercado, oficios, clases, razas, morada_NO CAM_Iso por distrito ciudad_iso la ciudad completa en CAM_Iso ciudad_calle a altura de personaje (1.7 … |
| `tools/blender/capture_stage25.py` | 4,892 | capturas de la etapa 25 (E12): Cazadores dentro de la muralla, casas nuevas de las Razas y el Faro. cazadores CAM_Iso sobre la casa 12 x 8 (117, -21) cazadores_campo CAM_Iso sobre el campo de tiro 14 x 8 junto a la mural… |
| `tools/blender/capture_stage26.py` | 4,340 | capturas de la etapa 26 (E13). moradas_ne CAM_Iso sobre una terraza de NE con un balcon por puerta (Morada_NE_013) moradas_so_calle a 1.7 m en una terraza de SO mirando a los balcones y la escalera cazadores_acceso CAM_I… |
| `tools/blender/capture_stage27.py` | 7,987 | capturas de la etapa 27 (interiores) sobre blender/concordia_interiors_v01.blend. kit hoja del kit BLD_INT_KIT (iso) sala_iso sala de prueba 8 x 6 en CAM_Iso con WALL_Near_A/B y CEILING ocultos sala_calle sala de prueba … |
| `tools/blender/capture_stage28_city.py` | 3,195 | capturas de la ciudad en la etapa 28 (concordia_v28.blend). tubos CAM_Iso sobre la ruta oeste completa de los tubos de luz tubos_posada de cerca: pilares sobre el tejado de la Posada y el arco sobre la avenida tubos_regi… |
| `tools/blender/capture_stage28_int.py` | 5,152 | capturas de la etapa 28 (vitrinas e interiores de las Moradas) sobre blender/concordia_moradas_int_v01.blend. vitrinas las 3 vitrinas (LOD0) con sus slots, en CAM_Iso <plantilla>_iso CAM_Iso con muros cercanos, techo y t… |
| `tools/blender/capture_stage28_props.py` | 5,622 | capturas de los props hechos a mano (etapa 28) sobre blender/concordia_props_v01.blend. props_ia_iso los 4 objetos de la lista de IA en CAM_Iso, con triangulos props_ia_cerca los 4 de cerca (2 x 2 en una imagen, a la alt… |
| `tools/blender/capture_stage29_int.py` | 5,771 | capturas de la etapa 29 (interiores unicos) sobre blender/concordia_interiors_unicos_v01.blend. Por interior: <nombre>_iso (CAM_Iso con muros cercanos, techo y plantas altas ocultos), vistas a 1.7 m y las particulares (p… |
| `tools/blender/cauce_route.py` | 5,152 | trazado del Cauce (Python puro). Lo usan stage05_layout (reserva del corredor) y stage07_cauce. Recorrido (ref. Brujas): Fuente del Mercado (vertiente, r=105 en el eje Norte) -> sale por su lado Este hacia dentro -> arco… |
| `tools/blender/concordia_buildings.py` | 30,558 | Building assembler (etapa 12). build_building(nombre, footprint, pisos, tipo_techo, estilo, seed, ...) apila los modulos de bld_kit y crea: <Nombre> Empty raiz (origen = centro de la base, a la cota del terreno; +Y = pue… |
| `tools/blender/concordia_const.py` | 11,774 | datos fijos de la ciudad. Fuente unica de verdad para todos los scripts bpy (y para herramientas de Godot). No depende de bpy: se puede importar desde cualquier Python. Convenciones - 1 unidad = 1 metro. - Ejes Blender: … |
| `tools/blender/concordia_rig.py` | 15,278 | esqueleto comun de todas las razas (SkeletonProfileHumanoid de Godot 4.7, 56 huesos, verificado en https://docs.godotengine.org/en/stable/classes/class_skeletonprofilehumanoid.html y scene/resources/ skeleton_profile.cpp… |
| `tools/blender/glb_tools.py` | 2,926 | utilidades para los .glb exportados (sin bpy). strip_embedded_images(path): con export_keep_originals el exportador de Blender escribe en cada imagen la ruta original (uri) Y una copia incrustada (bufferView); Godot avis… |
| `tools/blender/interior_kit.py` | 34,278 | Etapa 27: kit de interiores (BLD_INT_KIT) y build_interior(). Referencias: Palazzo Pubblico de Siena (salas macizas, arcos), Westminster Hall (vigas a la vista), Rothenburg ob der Tauber y Cesky Krumlov (entramado, vigas… |
| `tools/blender/lod_utils.py` | 11,928 | LOD2 de lejos (decision D, etapa 17/18): un solo material de color plano por edificio (el color medio del LOD0, ponderado por area) y una malla que no se rompe al diezmar: envolvente por voxeles (Remesh) del LOD0 y luego… |
| `tools/blender/material_library.py` | 17,453 | biblioteca de materiales PBR procedurales (sin red: Poly Haven bloqueado). Convencion (para sustituirlas por Poly Haven cambiando SOLO 3 imagenes): textures/lib/<Nombre>/T_<Nombre>_Albedo.png color (sRGB) textures/lib/<N… |
| `tools/blender/measure_stage25_faro.py` | 2,765 | Etapa 25: medicion final de la visibilidad del Faro sobre concordia_v25.blend (tras el pipeline de Godot). Escribe docs/reports/stage25_faro.json: % por tipo de calle y cada edificio que aun tapa (calles, altura actual, … |
| `tools/blender/measure_stage26_faro.py` | 2,161 | Etapa 26: medicion del Faro con el criterio nuevo (stage26_faro.py) sobre concordia_v26.blend. Escribe docs/reports/stage26_faro.json. No modifica el .blend. |
| `tools/blender/measure_stage28_moradas.py` | 3,275 | Etapa 28: lista de las puertas de Moradas que siguen tapadas desde CAM_Iso en concordia_v28.blend, con parcela (casa, conjunto, terraza, numero), causa, casa que tapa y distancia a lo largo del rayo de CAM_Iso desde la p… |
| `tools/blender/pj1_piel.py` | 22,465 | PJ1: piel del elfo horneada a 1K (PNG) sobre el UV del proxy, compartida por las 6 piezas del cuerpo. albedo color por vertice en la malla base de alta (tono base + zonas: orejas, nariz, mejillas, labios, cejas pintadas,… |
| `tools/blender/pj2_atlas.py` | 19,134 | PJ2: atlas 1K compartido por la ropa del Sanador y el cabello (MAT_Sanador_Atlas). uv_pack(objs) UV por objeto (smart project) reescalado a metros (pelo x1,5) y empaquetado conjunto: densidad de texel uniforme; los patro… |
| `tools/blender/pj2_geo.py` | 39,132 | PJ2: geometria del conjunto inicial del Sanador (CLASE_SANADOR, provisional) y del cabello del elfo. Todo se construye por script sobre el cuerpo de elfo_v01.blend (pose T, metros, de cara a -Y): Robe_Top tunica (pecho y… |
| `tools/blender/pj4_compare_rest.py` | 5,769 | PJ4: compara la pose de reposo de la Universal Animation Library (UAL 1 y UAL 2 Standard, Quaternius, CC0) con la del esqueleto del elfo (blender/elfo_v03.blend). NO retargetea (lo hace Godot con BoneMap + SkeletonProfil… |
| `tools/blender/pj_mpfb.py` | 6,494 | utilidades para usar MPFB 2.0.18 (extension de Blender, GPL-3.0; assets base CC0) desde scripts sin interfaz. MPFB deja un hilo vivo al salir: los scripts que lo usan terminan con os._exit(0). enable() refresca el indice… |
| `tools/blender/props_mano.py` | 27,956 | props hechos a mano (etapa 28): los 4 objetos que iban a IA (telar, fuelle, maniqui, casco de minero) y los 14 triviales de la tabla de props. Estilo semirrealista oscuro de formas simples, escala real en metros, origen … |
| `tools/blender/render_material_previews.py` | 3,533 | vista previa de la biblioteca de materiales: cada material sobre una esfera de 1 m de diametro y un plano de 4 x 4 m (UV en metros: 1 m = 1 tile). Cycles CPU. Salida: docs/captures/stage04_materials_sheet.png (+ una imag… |
| `tools/blender/stage01_scene_base.py` | 4,566 | Etapa 01: escena base. Crea una escena limpia (metrica, escala 1.0), las Collections vacias, la camara isometrica CAM_Iso y los Empties de las 4 puertas. Guarda concordia_v01.blend. Uso (Blender como modulo o binario): p… |
| `tools/blender/stage02_chunks.py` | 11,072 | Etapa 02d: version para Godot del terreno (chunks de 50 m + LODs) y export .glb. - La malla MAESTRA TRN_City (1 m) NO se toca ni se exporta. - Rejilla de chunks de 50 x 50 m centrada en el origen (el Portal cae en el cen… |
| `tools/blender/stage02_shading.py` | 9,648 | Etapa 02c: material del terreno + mascara de borde + oclusion ambiental. - edge_mask : 1 junto a la arista superior de cada muro (bordes que se oscurecen). - AO : horneada con Cycles en un atributo de color por esquina (… |
| `tools/blender/stage02_structures.py` | 18,083 | Etapa 02b: estructuras de contencion y escaleras sobre TRN_City. Referencias: muros de contencion con contrafuertes y escaleras adosadas de Toledo; escalinata monumental de peldanos bajos de Mala Strana (Praga). Piezas (… |
| `tools/blender/stage02_terrain.py` | 32,571 | Etapa 02: terreno base de la colina (TRN_City). v2 Genera TRN_City (malla MAESTRA de 1 m) en la coleccion TERRAIN. Pasos 1. Grid 424 x 424 m, celdas de 1 m, centrado; se eliminan vertices con r > 212. 2. Cortes (bmesh) d… |
| `tools/blender/stage03_analysis.py` | 8,372 | Etapa 03: comprobaciones de la Plaza del Portal. - zona despejada r 15..48: ningun vertice de pieza por encima del suelo. - canales: a que profundidad queda la tira emisiva respecto al suelo. - pendientes de la plaza tra… |
| `tools/blender/stage03_plaza.py` | 27,217 | Etapa 03: Plaza del Portal (solo terreno, pedestales, bases y marcadores). Referencias - Piazza del Campo (Siena): suelo de losas con bandas radiales claras de travertino que convergen en el centro; plaza abierta rodeada… |
| `tools/blender/stage04_wall.py` | 47,602 | Etapa 04: muralla como KIT MODULAR (WALL_KIT) + montaje (WALL_LAYOUT). Referencias (silueta, remate y proporcion) - Avila: granito gris calido en sillares por hiladas, cubos semicirculares (BASTION), almenas regulares. -… |
| `tools/blender/stage05_layout.py` | 70,526 | etapa 05: planificador 2D de calles y parcelas de los 4 distritos cardinales. Python puro + numpy (sin bpy). Determinista (semilla 11). Entrada : raster de obstaculos de la escena (stage05_obstacles.py; 1 = estructura, 2… |
| `tools/blender/stage05_obstacles.py` | 3,815 | etapa 05: raster de obstaculos (vista cenital) de lo que ya existe en la escena. Lanza rayos verticales en una rejilla de CELL m sobre todo el terreno contra: 1 = estructuras (PLAZA, STREETS, MORADAS, WALL_LAYOUT; sin -c… |
| `tools/blender/stage05_plan_preview.py` | 4,102 | etapa 05: dibujo 2D del plan (calles + parcelas por distrito) sin Blender. Uso: python stage05_plan_preview.py --obst obst.npz --out plan.png [--json layout.json] |
| `tools/blender/stage05_streets.py` | 45,598 | etapa 05: aplica el plan de calles y parcelas (stage05_layout.py) a TRN_City. 1. Cortes (cuchillo con indice espacial): bordes de calle + linea de hombro a SHOULDER m (borde marcado), contornos de parcelas, plazas, zonas… |
| `tools/blender/stage06_moradas.py` | 30,583 | etapa 06: Moradas (viviendas de jugadores) en los 4 sectores diagonales. v05 -> v06. Trazado por terraza (las 6 terrazas de la etapa 02: 14 m, salto de 1.0 m, r 105..189): [pretil 0.6 m del borde] -> calle de servicio (f… |
| `tools/blender/stage07_cauce.py` | 39,894 | etapa 07: Cauce, puentes, arcos entre barrios y escalinatas. v06 -> v07. Cauce (cauce_route.py): canal de 4 m x 1.2 m, orillas de piedra de 1 m, agua plana 0.4 m bajo el borde de cada tramo (4 azudes de 0.3 m), escalones… |
| `tools/blender/stage08_exterior.py` | 27,460 | etapa 08: terreno exterior de ceniza (r = 212 .. 400). v07 -> v08. Coleccion EXTERIOR. Ref. Bardenas Reales (forma del relieve: badlands, cauces secos, mesetas y cabezos de arenisca) con color gris ceniza. Sin senderos, … |
| `tools/blender/stage09_apply.py` | 11,017 | etapa 09 (Blender): crea los materiales glTF con las texturas de textures/concordia, UV de mundo y asignacion por mascaras; reexporta chunks, muralla y una biblioteca de materiales. v08 -> v09. |
| `tools/blender/stage09_materials.py` | 13,541 | etapa 09: materiales glTF (Principled + Albedo / Normal GL / Roughness) con texturas tileables 2048 x 2048 (1 m = 1 tile) horneadas por codigo en textures/concordia/<MAT>/T_<MAT>_{Albedo,Normal,Roughness}.jpg. Referencia… |
| `tools/blender/stage09_polyhaven.py` | 4,206 | etapa 09: texturas CC0 de Poly Haven (2K, Normal GL) en lugar de las procedurales. Descarga Diffuse / nor_gl / Rough y las deja en textures/concordia/<MAT>/T_<..>_{Albedo,Normal,Roughness}.jpg (misma convencion: el mater… |
| `tools/blender/stage10_apply.py` | 28,994 | etapa 10 (Blender): materiales con texturas reales de Poly Haven, mascaras nuevas y asignacion por cara. Materiales (todos glTF): UV Map 'UVWorld' -> Mapping (escala real, KHR_texture_transform) -> Image Texture albedo (… |
| `tools/blender/stage10_polyhaven.py` | 15,897 | etapa 10: texturas CC0 de Poly Haven para todos los materiales (salvo Shard_Blue, Wall_Runes, Water, que siguen procedurales y se hornean a PNG). Por material: textures/concordia/polyhaven_src/<asset>/<asset>_<mapa>_<res… |
| `tools/blender/stage11_godot.py` | 40,632 | etapa 11: preparacion para Godot 4 (a partir de concordia_v10.blend). 1. Limpieza: vertices duplicados (0.001 m), caras degeneradas, geometria suelta, caras interiores, caras de apoyo ocultas (base de piezas apoyadas), n… |
| `tools/blender/stage13_portal.py` | 31,288 | etapa 13: el Portal y sus elementos (coleccion BLD_PORTAL). Referencias: Stonehenge (trilito: dos postes enormes y un dintel, bloques erosionados) y Porta Nigra de Treveris (masa oscura y pesada, desgaste). Runas inventa… |
| `tools/blender/stage14_obelisk.py` | 14,110 | etapa 14: el Obelisco de los Pisos (coleccion BLD_PORTAL), sobre MARKER_Obelisco (SO de la plaza). Referencias: obelisco de Luxor en la Place de la Concorde (fuste de 4 caras que se estrecha, pyramidion, grabados en bajo… |
| `tools/blender/stage15_faro.py` | 36,731 | etapa 15: Torre del Faro (MARKER_Faro, NE de la plaza). Coleccion BLD_PORTAL. Referencias: Torre de Hercules (A Coruna: faro de piedra sobrio, rampa exterior en espiral de la torre romana) y Torre del Mangia del Palazzo … |
| `tools/blender/stage16_landmarks.py` | 42,693 | Etapa 16: hitos NO y SE de la plaza. SANTUARIO DEL RETORNO (MARKER_Santuario, pad 16 x 12): capilla esbelta tipo Sainte-Chapelle en caliza clara (MAT_Limestone_Light), nave de 9 m a los hombros, cubierta a dos aguas de t… |
| `tools/blender/stage18_mercado.py` | 34,332 | Etapa 18 (E5): distrito del Mercado. Piezas singulares hechas a mano (los edificios corrientes salen del kit con concordia_buildings.build_building / fit_iso_height, ver build_stage18.py). tesoreria_meshes Tesoreria de l… |
| `tools/blender/stage19_oficios.py` | 37,340 | Etapa 19 (E6): distrito Este (Oficios). Piezas singulares y extras de los edificios del kit. Cada edificio se reconoce por la SILUETA desde CAM_Iso (que mira al NO): por eso los rasgos van tambien en el tejado o en los l… |
| `tools/blender/stage20_clases.py` | 24,538 | Etapa 20 (E7): distrito de las Clases. Plantilla SALON DE CLASE (18 x 14): piedra sobria (Toledo), portico de 4 columnas con fronton, teja ocre, y partes ajustables por clase (CLASS_PRESETS, CLASE_01..CLASE_08, nombres g… |
| `tools/blender/stage21_razas.py` | 30,612 | Etapa 21 (E8): barrios de las razas. Plantilla con presets ajustables (N_RAZAS = 6). Referencias reales: Mala Strana (Praga) para la mezcla de alturas y calles en cuesta, Cesky Krumlov y Rothenburg ob der Tauber para las… |
| `tools/blender/stage22_conexiones.py` | 21,577 | Etapa 22 (E9): conexiones entre barrios y sobre el Cauce. Referencias: canales de Brujas (puentes de piedra de arco muy rebajado sobre un canal estrecho), Mala Strana de Praga (arcos sobre calles y escalinatas), Toledo (… |
| `tools/blender/stage23_moradas.py` | 31,128 | Etapa 23 (E10): viviendas de las 4 Moradas (parcelas 6 x 10 m en MARKER_Morada_<conjunto>_NNN). Referencias: Cesky Krumlov y Toledo (casas apretadas y escalonadas), Mont-Saint-Michel (casas pegadas a un muro en pendiente… |
| `tools/blender/stage25_faro.py` | 9,325 | Etapa 25: visibilidad del Faro desde las calles (criterio del usuario, E12). Puntos de calle cada 10 m a 1.7 m sobre el suelo en: 4 avenidas (+ accesos de puerta), 4 diagonales (r 62-190, eje), 2 anillos (r 100 y r 150, … |
| `tools/blender/stage25_lots.py` | 7,019 | Etapa 25: busqueda de suelo libre para parcelas nuevas (Cazadores, casas de las Razas). Rejilla de 1 m sobre un sector (angulo central, semiapertura, r min-max): publico = sobre la malla de navegacion (calles, plazas, es… |
| `tools/blender/stage26_cazadores.py` | 12,164 | Etapa 26 (E6, punto 4 aprobado): acceso al campo de tiro del Gremio de Cazadores. - Valla de 1.2 m cerrada por el lado de la ciudad (+Y local, daba al invernadero) y apertura de 2 m en el extremo norte (+X local, y 0..2)… |
| `tools/blender/stage26_faro.py` | 6,728 | Etapa 26 (punto 1): visibilidad del Faro con el criterio nuevo para camara isometrica. Desde cada punto de calle (ojo a 1.7 m, cada 10 m en avenidas, diagonales, anillos y callejones; los mismos puntos que stage25_faro) … |
| `tools/blender/stage26_faro_proposal.py` | 3,135 | Etapa 26 (punto 1): tabla de bajadas propuestas (solo decoracion, minimo 7 m) con el criterio nuevo del Faro. Lee concordia_v26.blend (no lo modifica) y escribe docs/reports/stage26_faro_proposal.json. |
| `tools/blender/stage26_moradas.py` | 6,469 | Etapa 26 (E10, punto 2 aprobado): Moradas NE y SO sin galerias corridas. Cada habitacion (casa comunal) de NE y SO pasa a UN balcon por puerta en las plantas 2 y 3 (1.5 x 0.6 m) y la escalera exterior se orienta segun CA… |
| `tools/blender/stage26_pipes.py` | 15,785 | Etapa 26 (E3, punto 8 aprobado): tubos de luz Tesoreria -> Faro sobre CRV_LightPipe_Tesoreria_Faro. - Primer punto de la curva = MARKER_PipeOutlet_TesoreriaMuralla_02 (salida real de la azotea, +9.6 m sobre el pad): se c… |
| `tools/blender/stage26_razas.py` | 11,778 | Etapa 26 (E8, punto 5 autorizado): casas que faltan en los barrios de las Razas. Solo dentro del sector Sur (+-25 grados, r 60-185). Permitido por el usuario en esta etapa: a) recolocar/compactar edificios de Razas dentr… |
| `tools/blender/stage27_banco.py` | 31,203 | Etapa 27: interior piloto del Banco de Concordia (int_banco.glb). Todo hecho a mano (regla del usuario: el Banco no usa assets descargados ni IA). Referencias: Palazzo Pubblico de Siena (volumen macizo, arcadas), antigua… |
| `tools/blender/stage28_moradas_int.py` | 29,454 | Etapa 28: vitrina de trofeos (3 variantes) e interiores tipo de las Moradas (Habitacion, Casa pequena, Casa grande) con build_interior (estilo entramado). Referencias: casas de Cesky Krumlov y Rothenburg ob der Tauber: v… |
| `tools/blender/stage29_santuario.py` | 32,375 | Etapa 29: interior del Santuario del Retorno (int_santuario.glb). Todo hecho a mano (regla del usuario: el Santuario no usa assets descargados ni IA). Funcion: punto de reaparicion tras morir; sereno y legible. Referenci… |
| `tools/blender/stage29_tesoreria.py` | 35,817 | Etapa 29: interior de la Tesoreria de la Muralla (int_tesoreria.glb). Todo hecho a mano (regla del usuario: la Tesoreria no usa assets descargados ni IA). Referencias: Palazzo Pubblico de Siena (salas macizas, arcos, luz… |
| `tools/blender/terrain_profile.py` | 13,632 | modelo de alturas de la colina h(x, y). Python puro (sin bpy). v2 Piezas del modelo - Perfiles radiales: comun (plaza + bajada 60..90), cardinal fuera del eje, eje de avenida (banda recta de 30 m), diagonal (hitos, rampa… |
| `tools/blender/wall_textures.py` | 6,293 | texturas procedurales tileables para el kit de muralla (sin red: Poly Haven esta bloqueado en este entorno). Se pueden sustituir por las CC0 de Poly Haven (Stone Wall 02, Rock Boulder Cracked...) sin tocar la geometria: … |
| `tools/fetch_sketchfab_cc0.py` | 4,662 | descarga de modelos CC0 de Sketchfab (solo ficheros de datos: glb/gltf). Por cada uid: (1) ficha de la API (/v3/models/<uid>): la licencia debe ser CC0; (2) pagina publica del modelo: debe mostrar la licencia CC0 (texto … |
| `tools/inventario_glb.py` | 4,158 | inventario de las exportaciones .glb (sin Blender ni Godot: lee el JSON del glTF). Por archivo: tamano, fecha, nodos, mallas, triangulos, materiales, imagenes, sufijos de importacion de Godot (-colonly, -convcolonly, -na… |
