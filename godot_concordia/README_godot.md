# CONCORDIA en Godot 4.7.2 — como abrirlo y probarlo en tu PC

## 1. Lo que necesitas
- **Godot 4.7.2 estable** (version normal, no la .NET): https://godotengine.org/download/archive/4.7.2-stable/
  (Windows: `Godot_v4.7.2-stable_win64.exe.zip`). Es la misma version con la que se ha montado el proyecto.
- Una tarjeta grafica con Vulkan (el proyecto usa Forward+).

## 2. Descomprimir el paquete
1. Descarga todas las partes `concordia_godot_paquete_parteNN.zip`.
2. Extrae **todas** en la **misma carpeta**, por ejemplo `C:\Users\USER\Desktop\Juego_1\Juegocamkeju\godot_concordia`
   (cada parte es un zip normal; si Windows pregunta por reemplazar archivos, di que si).
3. Debe quedar una carpeta con `project.godot`, `assets/`, `scenes/`, `scripts/`, `shaders/`, `navigation/`,
   `tools/`, `ui/`, `.godot/` (oculta: ya trae los assets importados, asi que no tiene que reimportar).

## 3. Abrirlo
1. Abre Godot 4.7.2 -> **Importar** -> elige `project.godot` -> Importar y editar.
   - La primera vez puede tardar 1-2 minutos en cargar (468 MB de modelos y texturas). Si empieza a reimportar, deja
     que termine (5-10 minutos como mucho) y no lo cierres.
2. Pulsa **F5** (Ejecutar proyecto). Arranca en la plaza, a las 17:30 (hora dorada).

## 4. Teclas de prueba
| tecla | que hace |
|---|---|
| W A S D / flechas | andar (relativo a la camara) |
| Shift | correr |
| clic izquierdo | ir andando a ese punto por la navegacion |
| rueda del raton | zoom de 15 a 120 m |
| Q / E | girar la camara 90 grados |
| T | adelantar una hora (dia y noche) |
| F1 | mostrar u ocultar el HUD de depuracion (FPS, draw calls, triangulos, VRAM, zona, posicion, hora) |
| R | volver al punto de inicio |

La flecha azul en el borde de la pantalla apunta al Faro cuando no se ve.

## 5. Benchmark (lo que necesito que me pases)
Cierra el editor y, en una ventana de comandos (`cmd`) dentro de la carpeta del proyecto:
```
"C:\ruta\a\Godot_v4.7.2-stable_win64.exe" --path . -s res://tools/benchmark.gd
```
Tarda unos 2-3 minutos (9 escenas: plaza, Mercado, Oficios, Moradas de dia y de noche, y zoom maximo). Al terminar
se cierra solo y deja **`benchmark_resultados.txt`** en la carpeta del proyecto: pasamelo. Lleva el FPS medio, el
1 % peor, el tiempo de fotograma, los draw calls, los triangulos y la VRAM por escena, y los datos de tu GPU y CPU.
Version corta (5 s por escena): anade ` -- rapido` al final.

## 6. Que mirar en la prueba (parada 1 ampliada)
- Andar por avenidas, escaleras de las Moradas, puentes y la plaza; probar el clic para andar.
- La luz a distintas horas (T): 6:12 amanecer, 12:00, 17:30 hora dorada, 19:30 atardecer, 20:36 hora azul, noche.
- Los haces del Faro y del Crisol, el velo del Portal, el Obelisco, los huertos detras de las casas, la transparencia
  del Salon de las Hazanas cuando el jugador pasa por detras.
- Si algo falla, el HUD (F1) da la posicion en coordenadas de Blender: apuntala con una captura.

## 7. Notas
- Escena principal: `scenes/main.tscn` (la generan `tools/build_city.gd`; la navegacion se hornea con
  `tools/bake_navmesh.gd`). Problemas de los modelos: `FIXES_BLENDER.md`; pruebas y cifras: `TEST_REPORT.md`.
- Los assets no estan en git (son copias de `export/` y `textures/` hechas por `tools/sync_assets.py`).
