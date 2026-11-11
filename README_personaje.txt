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

6. ANIMACIONES (elfo_sanador_anims.glb, 30 fps, sin movimiento de raiz)
--------------------------------------------------------------------------------------------------------
  Heal_Cast_Single     fotogramas 1-28  0.90 s
  Heal_Channel-loop    fotogramas 1-46  1.50 s  (bucle)
  Heal_Cast_Area       fotogramas 1-37  1.20 s
  Revive               fotogramas 1-61  2.00 s
  Base (Idle, Walk, Run, Sit, Hit, Death, Spell): UAL 1 / UAL 2 de Quaternius, retargeteadas en Godot.
