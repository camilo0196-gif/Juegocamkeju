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
- [ ] COLOR_0 = mask_pack del terreno: shader del terreno que lo lea (G4).

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
- [ ] Glow (umbral ~1.0) para los emisivos #8FD0FF; MAT_Embers (unica calida) no pasar de 1.5.
- [ ] Vitrales y MAT_Window_Warm con el ciclo dia/noche; farolillos LANTERN_Shard (OmniLight3D pequena, tope 16).
- [ ] LightmapGI por distrito / interiores (UV2 con `--lightmaps` en import_settings.py) — medir coste.

## G5 - Efectos y shaders
- [ ] PORTAL_Veil (agua, UV u 0..1, v = z/11 m), sin colision; runas del Atrio y pilares (pulso).
- [ ] FARO_Beam (ADD, unshaded, sin sombras, sin profundidad) y FARO_Crystal (emision 4.0, pulso); brujula HUD.
- [ ] OBELISK_Mark_001..100: material por instancia (MAT_Obelisk_Mark_Lit), diccionario de pisos.
- [ ] MAT_Pipe_Light_Core: pulso Tesoreria -> Faro; MAT_Wall_Runes con faro_energy.
- [ ] Taller_Carpinteria_WATERWHEEL girando ~6 rpm; agua del Cauce (MARKER_Cauce_Source -> _Outlet); fuente del Mercado.
- [ ] Humo: Posada, Alquimia (MARKER_Alquimia_Smoke_01/02), Hornos, Yurtas; vapor MARKER_GranForja_Steam; brasas MAT_Embers.
- [ ] Crisol: CRISOL_FloatStone_01..07 flotando; haz del oculo ADD.
- [ ] Estandartes y banderas (clases y razas): textura por instancia y viento.
- [ ] Transparencia por proximidad (occludes_iso: Salon de las Hazanas, muralla) con material por instancia.
- [ ] MAT_Glass_R04: depth draw opaque only; MAT_Portal_Veil 0.6 / MAT_Faro_Beam 0.3 / MAT_Pipe_Glass 0.35: orden de transparencias.
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
