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
