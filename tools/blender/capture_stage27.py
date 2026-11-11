"""
CONCORDIA - capturas de la etapa 27 (interiores) sobre blender/concordia_interiors_v01.blend.
  kit             hoja del kit BLD_INT_KIT (iso)
  sala_iso        sala de prueba 8 x 6 en CAM_Iso con WALL_Near_A/B y CEILING ocultos
  sala_calle      sala de prueba a 1.7 m
  banco_iso       Banco: vestibulo en CAM_Iso (muros cercanos y techos ocultos)
  banco_boveda    Banco: boveda en CAM_Iso (tambien WALL_Near_Vault oculto)
  banco_cajas     cajas de deposito de cerca (numeros legibles)
  banco_calle     Banco a 1.7 m desde la sala de espera hacia el mostrador y la boveda
Las luces son los Empties de 'Lights' convertidos en puntos de luz solo para la captura (Godot hornea las suyas).
`-- nombre ...` para repetir solo algunas.
"""

import math
import os
import sys

import bpy
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import capture_stage02 as K  # noqa: E402
import interior_kit as IK  # noqa: E402

REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
BLEND = os.path.join(REPO, "blender", "concordia_interiors_v01.blend")
OUT = os.path.join(REPO, "docs", "captures")
ONLY = set(sys.argv[sys.argv.index("--") + 1:]) if "--" in sys.argv else set()
W_PER_ENERGY = 110.0


def P(n):
    return os.path.join(OUT, f"stage27_{n}.png")


def want(n):
    return not ONLY or n in ONLY


def srgb_lin(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def hexcol(h):
    h = h.lstrip("#")
    return tuple(srgb_lin(int(h[i:i + 2], 16) / 255) for i in (0, 2, 4))


def lights_from_empties(root):
    made = []
    for e in root.children_recursive:
        if e.type == "EMPTY" and e.get("light_kind"):
            ld = bpy.data.lights.new(f"TMPL_{e.name}", "POINT")
            ld.color = hexcol(e["light_color"])
            ld.energy = e["light_energy"] * W_PER_ENERGY * (0.8 if e["light_kind"] == "omni_window" else 1.0)
            ld.shadow_soft_size = 0.08
            ld.use_custom_distance = True
            ld.cutoff_distance = e["light_range"] * 1.6
            o = bpy.data.objects.new(f"TMPL_{e.name}", ld)
            bpy.context.scene.collection.objects.link(o)
            o.matrix_world = e.matrix_world.copy()
            made.append(o)
    return made


def set_hidden(root, groups, hide=True):
    for e in root.children_recursive:
        if e.get("interior_group") in groups:
            for o in [e] + list(e.children_recursive):
                o.hide_render = hide


def iso_cam(target, ortho):
    cam = K.new_cam("TMP_iso", ortho=ortho)
    cam.data.clip_end = 3000
    K.look_at(cam, Vector(target) + IK.CAM_BACK * 300.0, Vector(target))
    return cam


def only_collections(keep):
    for c in bpy.data.collections:
        c.hide_render = c.name not in keep
    for o in bpy.data.objects:
        if o.name.endswith(("-colonly", "-navmesh")):
            o.hide_render = True


def interior_world(scene, strength=0.18):
    w = scene.world
    bg = w.node_tree.nodes["Background"]
    bg.inputs["Color"].default_value = (0.32, 0.30, 0.28, 1)
    bg.inputs["Strength"].default_value = strength
    for o in scene.collection.objects:
        if o.name.startswith("TMP_sun"):
            o.hide_render = True


def main():
    bpy.ops.wm.open_mainfile(filepath=BLEND)
    scene = bpy.context.scene
    K.setup_render(scene)
    scene.cycles.samples = 48
    bank = bpy.data.objects["INT_Banco"]
    room = bpy.data.objects["INT_Sala_Prueba_8x6"]
    bf = bpy.data.objects["INT_Banco_Frame"].matrix_world
    rf = bpy.data.objects["INT_Sala_Prueba_8x6_Frame"].matrix_world
    if want("kit"):
        only_collections({"BLD_INT_KIT"})
        labels = [(n, (4000.0 + (i % 7) * 8.0 + 1.0, -(i // 7) * 8.0, 3.6)) for i, n in enumerate(IK.KIT)]
        cam = iso_cam((4024.0, -12.0, 1.0), 62.0)
        K.render(scene, cam, P("kit"))
        K.annotate(scene, cam, P("kit"), "BLD_INT_KIT: 27 modulos (grilla 1 m, <= 300 triangulos cada uno)", labels)
        bpy.data.objects.remove(cam)
    interior_world(scene)
    if want("sala_iso") or want("sala_calle"):
        only_collections({"INT_TEST"})
        tmp = lights_from_empties(room)
        set_hidden(room, ("WALL_Near_A", "WALL_Near_B", "CEILING"))
        if want("sala_iso"):
            cam = iso_cam(rf @ Vector((0.0, 0.0, 1.0)), 13.0)
            K.render(scene, cam, P("sala_iso"))
            K.annotate(scene, cam, P("sala_iso"), "Sala de prueba 8 x 6 m (entramado) en CAM_Iso: WALL_Near_A/B y CEILING "
                       "ocultos", [("Salida", rf @ Vector((0.0, 3.0, 0.3))), ("Hogar", rf @ Vector((-2.0, 2.6, 1.6)))])
            bpy.data.objects.remove(cam)
        set_hidden(room, ("WALL_Near_A", "WALL_Near_B", "CEILING"), False)
        if want("sala_calle"):
            cam = K.new_cam("TMP_eye", lens=20)
            K.look_at(cam, rf @ Vector((2.6, -2.2, 1.7)), rf @ Vector((-2.0, 2.0, 1.2)))
            K.render(scene, cam, P("sala_calle"))
            K.annotate(scene, cam, P("sala_calle"), "Sala de prueba a 1.7 m", [])
            bpy.data.objects.remove(cam)
        for o in tmp:
            bpy.data.objects.remove(o)
    if any(want(n) for n in ("banco_iso", "banco_boveda", "banco_cajas", "banco_calle")):
        only_collections({"INT_BANCO"})
        tmp = lights_from_empties(bank)
        hid = ("WALL_Near_A", "WALL_Near_B", "CEILING", "CEILING_Vault")
        set_hidden(bank, hid)
        labels = [("Banquero", bf @ Vector((5.5, 1.25, 1.9))), ("Mostrador y reja", bf @ Vector((4.3, -2.5, 2.7))),
                  ("Puerta de la boveda", bf @ Vector((7.45, -4.4, 3.1))), ("Galeria", bf @ Vector((-2.0, 6.0, 4.4))),
                  ("Escalera", bf @ Vector((-10.4, 2.0, 2.2))), ("Archivo", bf @ Vector((-7.2, -6.0, 2.4))),
                  ("Espera", bf @ Vector((-2.5, 2.2, 1.0))), ("Despacho", bf @ Vector((8.5, 7.2, 4.3)))]
        if want("banco_iso"):
            cam = iso_cam(bf @ Vector((0.0, -0.5, 1.5)), 31.0)
            K.render(scene, cam, P("banco_iso"))
            K.annotate(scene, cam, P("banco_iso"), "Banco de Concordia (interior 23.1 x 19.1 x 6.4 m) en CAM_Iso: muros "
                       "cercanos y techos ocultos", labels)
            bpy.data.objects.remove(cam)
        if want("banco_boveda"):
            set_hidden(bank, ("WALL_Near_Vault",))
            cam = iso_cam(bf @ Vector((9.7, -5.0, 1.0)), 13.0)
            K.render(scene, cam, P("banco_boveda"))
            K.annotate(scene, cam, P("banco_boveda"), "Boveda: 200 cajas de deposito numeradas (1-40 abiertas, 41-200 "
                       "cerradas) en 4 paredes; WALL_Near_Vault oculto", [])
            bpy.data.objects.remove(cam)
            set_hidden(bank, ("WALL_Near_Vault",), False)
        set_hidden(bank, hid, False)
        if want("banco_cajas"):
            cam = K.new_cam("TMP_box", lens=35)
            K.look_at(cam, bf @ Vector((9.5, -6.6, 1.35)), bf @ Vector((11.55, -6.9, 1.1)))
            ev = scene.view_settings.exposure
            scene.view_settings.exposure = 1.5  # solo para leer los numeros; Godot hornea su propia luz
            K.render(scene, cam, P("banco_cajas"))
            scene.view_settings.exposure = ev
            K.annotate(scene, cam, P("banco_cajas"), "Cajas de deposito a 2 m (exposicion +1.5 solo en la captura): "
                       "placa clara = abierta, oscura con candado = cerrada", [])
            bpy.data.objects.remove(cam)
        if want("banco_calle"):
            cam = K.new_cam("TMP_eye", lens=18)
            K.look_at(cam, bf @ Vector((1.4, 3.6, 1.7)), bf @ Vector((7.0, -4.2, 1.6)))
            K.render(scene, cam, P("banco_calle"))
            K.annotate(scene, cam, P("banco_calle"), "Banco a 1.7 m: mostrador con reja, el sitio del Banquero y la puerta "
                       "de la boveda con su farol de esquirla", [])
            bpy.data.objects.remove(cam)
        for o in tmp:
            bpy.data.objects.remove(o)
    _ = math


if __name__ == "__main__":
    main()
