CONCORDIA - Edificios y materiales nuevos (kit, Portal y landmarks)
==================================================================
Actualizado en la etapa 18 (concordia_v18.blend). Auditoria automatica: tools/blender/audit_materials.py ->
docs/reports/stage17_materials.json.

1. Regla de aprobacion de materiales nuevos
-------------------------------------------
Un material nuevo del kit de edificios, del Portal o de un landmark queda aprobado si cumple las tres condiciones:
  a) Paleta: nada saturado fuera del azul palido. Prueba: saturacion HSV <= 0.35, salvo tonos 185-215 grados (azul).
     El unico color magico fuerte es #8FD0FF.
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
    (cuerpo + cubierta) con UN material plano MAT_LOD2_<NOMBRE> = color medio del LOD0 ponderado por area, y la malla
    sale de una envolvente por voxeles (Remesh 0.3-0.4 m) diezmada al 15 %, para que no se rompa.
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
