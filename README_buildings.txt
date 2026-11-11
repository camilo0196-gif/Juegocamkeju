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
    (20,205 tris), Oficios 26 (16,589), Clases 13 (10,934).
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
