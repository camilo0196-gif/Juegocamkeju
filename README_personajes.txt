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
