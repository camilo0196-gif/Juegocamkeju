"""
CONCORDIA - utilidades para usar MPFB 2.0.18 (extension de Blender, GPL-3.0; assets base CC0) desde scripts sin
interfaz. MPFB deja un hilo vivo al salir: los scripts que lo usan terminan con os._exit(0).

  enable()                      refresca el indice de extensiones y activa bl_ext.user_default.mpfb
  create_base(macro, targets)   humano base de MakeHuman con macros y targets (pares l-/r- incluidos)
  tpose_base(basemesh)          brazos en T con el rig de MPFB (aplicado); devuelve articulaciones; add_proxy
  evaluated_copy(obj, name)     malla evaluada (targets + pose) como objeto nuevo, sin modificadores
"""

import json
import os

import bpy

MOD = "bl_ext.user_default.mpfb"


def enable():
    import addon_utils
    if MOD in bpy.context.preferences.addons:
        return True
    addon_utils.extensions_refresh(ensure_wheels=False)
    return bool(addon_utils.enable(MOD, default_set=True, persistent=True))


def services():
    from bl_ext.user_default.mpfb.services.humanservice import HumanService
    from bl_ext.user_default.mpfb.services.targetservice import TargetService
    from bl_ext.user_default.mpfb.services.rigservice import RigService
    from bl_ext.user_default.mpfb.services.locationservice import LocationService
    from bl_ext.user_default.mpfb.services.assetservice import AssetService
    return HumanService, TargetService, RigService, LocationService, AssetService


def create_base(macro, targets):
    HumanService, TargetService, _R, _L, _A = services()
    md = TargetService.get_default_macro_info_dict()
    md.update({k: v for k, v in macro.items() if k != "race"})
    if "race" in macro:
        md["race"] = dict(macro["race"])
    bm = HumanService.create_human(mask_helpers=True, detailed_helpers=True, extra_vertex_groups=True,
                                   feet_on_ground=False, scale=0.1, macro_detail_dict=md)   # el rig se ajusta sin el desplazamiento
    loaded = {}
    for name, w in targets.items():
        sides = [name.replace("*", s) for s in ("l", "r")] if "*" in name else [name]
        for n in sides:
            p = TargetService.target_full_path(n)
            if p is None:
                raise IOError(f"target no encontrado: {n}")
            TargetService.load_target(bm, p, weight=w, name=n)
            loaded[n] = w
    return bm, loaded


def _align(arm, bone, a_name, b_name, target):
    """Gira el hueso (pose) para que el vector cabeza(a_name) -> cabeza(b_name) apunte a 'target' (espacio armature)."""
    from mathutils import Matrix
    pb = arm.pose.bones[bone]
    pa, pbn = arm.pose.bones[a_name], arm.pose.bones[b_name]
    v = (pbn.head - pa.head)
    q = v.rotation_difference(target)
    h = pb.head.copy()
    pb.rotation_mode = "QUATERNION"
    pb.matrix = Matrix.Translation(h) @ q.to_matrix().to_4x4() @ Matrix.Translation(-h) @ pb.matrix
    bpy.context.view_layer.update()


JOINTS = ("root", "spine05", "spine01", "neck01", "neck03", "head", "clavicle.L", "clavicle.R", "upperarm01.L",
          "upperarm01.R", "lowerarm01.L", "lowerarm01.R", "wrist.L", "wrist.R", "finger3-1.L", "finger3-1.R",
          "upperleg01.L", "upperleg01.R", "lowerleg01.L", "lowerleg01.R", "foot.L", "foot.R")


def tpose_base(bm, rig="default", joints_wanted=JOINTS):
    """Rig 'default' de MPFB con sus pesos completos; brazos rectos y horizontales (hombro -> codo -> muneca sobre
    +-X); la pose se aplica a la malla base (antes se funden los targets) y el rig se borra. Devuelve las articulaciones
    (cabeza y cola de cada hueso de JOINTS en espacio mundo, ya en T). El proxy que se anada despues se ajusta en T."""
    from mathutils import Vector
    HumanService, _T, _R, _L, _A = services()
    for o in bpy.context.view_layer.objects:
        o.select_set(False)
    bm.select_set(True)
    bpy.context.view_layer.objects.active = bm
    # 1) la mezcla de targets pasa a la malla ANTES del rig: el rig se ajusta a la Basis, no a la mezcla
    if bm.data.shape_keys:
        bpy.ops.object.shape_key_remove(all=True, apply_mix=True)
    arm = HumanService.add_builtin_rig(bm, rig)
    bpy.context.view_layer.update()
    for side in ("L", "R"):
        sx = 1.0 if arm.pose.bones[f"upperarm01.{side}"].head.x > 0 else -1.0     # cada brazo hacia su lado
        t = Vector((sx, 0.0, 0.0))
        _align(arm, f"upperarm01.{side}", f"upperarm01.{side}", f"lowerarm01.{side}", t)
        _align(arm, f"lowerarm01.{side}", f"lowerarm01.{side}", f"wrist.{side}", t)
        _align(arm, f"wrist.{side}", f"wrist.{side}", f"finger3-1.{side}", t)
    joints = {}
    for n in (joints_wanted if joints_wanted is not None else [b.name for b in arm.pose.bones]):
        pb = arm.pose.bones.get(n)
        if pb is not None:
            joints[n] = (tuple(arm.matrix_world @ pb.head), tuple(arm.matrix_world @ pb.tail))
    for o in bpy.context.view_layer.objects:
        o.select_set(False)
    bm.select_set(True)
    bpy.context.view_layer.objects.active = bm
    # 2) la pose T se aplica como modificador (malla ya sin shape keys)
    mod = next(m for m in bm.modifiers if m.type == "ARMATURE")
    bpy.ops.object.modifier_apply(modifier=mod.name)
    mw = bm.matrix_world.copy()
    bm.parent = None
    bm.matrix_world = mw
    bpy.data.objects.remove(arm)
    bpy.context.view_layer.update()
    return joints


def add_proxy(bm, proxy="male1591"):
    HumanService, _T, _R, LocationService, AssetService = services()
    path = AssetService.find_asset_absolute_path(proxy, asset_subdir="proxymeshes")
    if path is None:
        path = os.path.join(LocationService.get_user_data("proxymeshes"), proxy, proxy + ".proxy")
    return HumanService.add_mhclo_asset(path, bm, asset_type="Proxymeshes", subdiv_levels=0, material_type="NONE")


def evaluated_copy(obj, name, col):
    dg = bpy.context.evaluated_depsgraph_get()
    ev = obj.evaluated_get(dg)
    me = bpy.data.meshes.new_from_object(ev, preserve_all_data_layers=True, depsgraph=dg)
    me.name = name
    o = bpy.data.objects.new(name, me)
    col.objects.link(o)
    o.matrix_world = obj.matrix_world.copy()
    return o


def add_eyes(bm, name="low-poly"):
    HumanService, _T, _R, LocationService, AssetService = services()
    path = AssetService.find_asset_absolute_path(name, asset_subdir="eyes")
    if path is None:
        path = os.path.join(LocationService.get_user_data("eyes"), name, name + ".mhclo")
    return HumanService.add_mhclo_asset(path, bm, asset_type="Eyes", subdiv_levels=0, material_type="NONE")
