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
