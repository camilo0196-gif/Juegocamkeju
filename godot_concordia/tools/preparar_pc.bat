@echo off
REM CONCORDIA - preparar el proyecto en Windows sin abrir el editor (arreglo VK -10, 2026-11-11).
REM   1. borra la cache de importacion .godot (la reimportacion hecha en el editor la dejo con mallas vacias)
REM   2. reimporta los .glb SIN GPU (--headless): no se agotan los buffers de Vulkan
REM   3. comprueba los .glb contra assets\MANIFEST.txt y las importaciones (verificacion_assets.txt)
REM   4. hornea el mundo del juego (world\ + scenes\concordia.tscn + scenes\main.tscn)
REM Uso: desde la carpeta godot_concordia
REM   tools\preparar_pc.bat "C:\ruta\a\Godot_v4.7.2-stable_win64_console.exe"
REM (si no se pasa ruta, se usa Godot_v4.7.2-stable_win64_console.exe que este en el PATH o en esta carpeta)

setlocal
set "GODOT=%~1"
if "%GODOT%"=="" set "GODOT=Godot_v4.7.2-stable_win64_console.exe"
cd /d "%~dp0.."
if not exist project.godot (
  echo No encuentro project.godot: ejecuta este archivo desde godot_concordia\tools
  pause
  exit /b 1
)
echo.
echo Se va a BORRAR la carpeta .godot (solo es cache; Godot la vuelve a crear). Cierra el editor antes.
echo Pulsa una tecla para seguir o cierra esta ventana para cancelar.
pause >nul
if exist .godot rmdir /s /q .godot

echo [1/3] Reimportando sin GPU (tarda unos minutos)...
"%GODOT%" --headless --path . --import
if errorlevel 1 goto fallo

echo [2/3] Comprobando assets...
"%GODOT%" --headless --path . -s res://tools/verify_assets.gd
if errorlevel 1 (
  echo HAY PROBLEMAS con los assets: mira verificacion_assets.txt
  goto fallo
)

echo [3/3] Horneando el mundo...
"%GODOT%" --headless --path . -s res://tools/build_world.gd
if errorlevel 1 (
  echo El horneado fallo: mira world\build_report.json
  goto fallo
)
echo.
echo Listo. Abre el proyecto en el editor y ejecuta (F5). F2 abre el menu de calidad.
pause
exit /b 0

:fallo
echo.
echo Algo fallo. Copia el texto de esta ventana y mandamelo.
pause
exit /b 1
