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
