"""
CONCORDIA - PJ1: piel del elfo horneada a 1K (PNG) sobre el UV del proxy, compartida por las 6 piezas del cuerpo.
  albedo  color por vertice en la malla base de alta (tono base + zonas: orejas, nariz, mejillas, labios, cejas
          pintadas, parpados, codos, rodillas, nudillos, unas) x ruido suave de baja y media frecuencia -> emision
          horneada de alta a baja. Dos tonos: A 'abedul' (claro frio) y B 'corteza' (oliva calido).
  normal  espacio tangente (OpenGL, como Godot) de la malla base de alta (subdividida 1 nivel) sobre el proxy.
  orm     R = AO horneado del cuerpo, G = rugosidad (0,55 base; labios 0,42; nariz y frente 0,5; unas 0,35), B = 0.
  ojos    albedo 256 px procedural (esclerotica, iris gris verdoso apagado, anillo limbal, pupila).
Paleta: saturacion <= 0,35 (comprobada sobre los PNG), sin el azul magico (#8FD0FF es solo emisivo).
"""

import colorsys
import math
import os

import bpy
import numpy as np
from mathutils import Vector

RES = 1024
TONES = {   # sRGB
    "A": {"nombre": "abedul", "base": "#D6C2AE", "rubor": "#C9998A", "ceja": "#6E6253", "labio": "#B98C80",
          "una": "#E2CFC2"},
    "B": {"nombre": "corteza", "base": "#8F755F", "rubor": "#8A6D5F", "ceja": "#3E352C", "labio": "#7A5E52",
          "una": "#A68E7A"},
}
IRIS = "#6F7A63"      # gris verdoso de abedul (s 0,19)


def lin(hexs):
    c = [int(hexs[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    return Vector([x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c])


def gw(o, name):
    g = o.vertex_groups.get(name)
    if g is None:
        return np.zeros(len(o.data.vertices))
    out = np.zeros(len(o.data.vertices))
    for v in o.data.vertices:
        for e in v.groups:
            if e.group == g.index:
                out[v.index] = e.weight
    return out


def gauss(co, c, r):
    d = np.linalg.norm(co - np.array(c), axis=1)
    return np.exp(-(d / r) ** 2)


def masks(hi, J, eyes):
    """Mascaras 0..1 por vertice de la malla de alta."""
    co = np.array([v.co[:] for v in hi.data.vertices])
    M = {}
    ears = gw(hi, "ears")
    top = co[ears > 0.5][:, 2].max() if (ears > 0.5).any() else 0
    bot = co[ears > 0.5][:, 2].min() if (ears > 0.5).any() else 0
    M["oreja"] = ears * (0.35 + 0.65 * np.clip((co[:, 2] - bot) / max(top - bot, 1e-3), 0, 1))
    M["labio"] = gw(hi, "lips")
    M["una"] = np.maximum(gw(hi, "fingernails"), gw(hi, "toenails"))
    M["ceja"] = np.maximum(gw(hi, "oculi01.L"), gw(hi, "oculi01.R"))
    M["parpado"] = np.maximum.reduce([gw(hi, n) for n in ("orbicularis03.L", "orbicularis03.R",
                                                           "orbicularis04.L", "orbicularis04.R")])
    head = (co[:, 2] > J["neck01"][0][2] + 0.05) & (np.abs(co[:, 0]) < 0.07)
    nose = co[head][np.argmin(co[head][:, 1])]                # punto mas adelantado de la cabeza
    M["nariz"] = gauss(co, nose, 0.018)
    ev = np.array([v.co[:] for v in eyes.data.vertices])
    eL, eR = ev[ev[:, 0] > 0].mean(axis=0), ev[ev[:, 0] < 0].mean(axis=0)
    lips = co[M["labio"] > 0.5].mean(axis=0) if (M["labio"] > 0.5).any() else nose - np.array([0, 0, 0.04])
    ch = []
    for e in (eL, eR):
        c = np.array([e[0] * 1.15, e[1] - 0.005, (e[2] + lips[2]) / 2 + 0.005])
        ch.append(gauss(co, c, 0.026))
    M["mejilla"] = np.maximum(*ch)
    M["frente"] = gauss(co, np.array([0, nose[1] + 0.02, eL[2] + 0.055]), 0.035)
    jo = []
    for n in ("lowerarm01.L", "lowerarm01.R"):
        jo.append(gauss(co, J[n][0], 0.035))
    for n in ("lowerleg01.L", "lowerleg01.R"):
        p = np.array(J[n][0]) + np.array([0, -0.045, 0])        # rotula, por delante
        jo.append(gauss(co, p, 0.04))
    M["articulacion"] = np.maximum.reduce(jo)
    fing = sum(gw(hi, f"finger{a}-{b}.{s}") for a in range(1, 6) for b in (1, 2, 3) for s in "LR")
    M["dedos"] = np.clip(fing, 0, 1)
    toes = sum(gw(hi, f"toe{a}-{b}.{s}") for a in range(1, 6) for b in (1, 2, 3) for s in "LR")
    M["dedos_pie"] = np.clip(toes, 0, 1)
    return {k: np.clip(v, 0, 1) for k, v in M.items()}


def vertex_albedo(M, tone):
    t = TONES[tone]
    base, rub, ceja, lab, una = (np.array(lin(t[k])[:]) for k in ("base", "rubor", "ceja", "labio", "una"))
    n = len(M["oreja"])
    col = np.tile(base, (n, 1))

    red = np.clip(0.40 * M["oreja"] + 0.45 * M["nariz"] + 0.40 * M["mejilla"] + 0.30 * M["articulacion"]
                  + 0.30 * M["dedos"] + 0.25 * M["dedos_pie"] + 0.25 * M["parpado"], 0, 0.7)
    col = col * (1 - red[:, None]) + rub[None, :] * red[:, None]
    lb = np.clip(M["labio"], 0, 1) * 0.6
    col = col * (1 - lb[:, None]) + lab[None, :] * lb[:, None]
    cj = np.clip(M["ceja"] - 0.15, 0, 1) * 0.55
    col = col * (1 - cj[:, None]) + ceja[None, :] * cj[:, None]
    un = M["una"] * 0.8
    col = col * (1 - un[:, None]) + una[None, :] * un[:, None]
    col = col * (1 + 0.05 * M["frente"])[:, None]
    return np.clip(col, 0, 1)


def vertex_rough(M):
    r = np.full(len(M["oreja"]), 0.55)
    r = r - 0.13 * M["labio"] - 0.05 * M["nariz"] - 0.05 * M["frente"] - 0.2 * M["una"]
    return np.clip(r, 0.3, 0.7)


def vertex_ao(hi, extra, rays=24, dist=0.25, seed=7):
    """Oclusion ambiental por vertice de la malla de alta (rayos en hemisferio coseno, hasta 'dist' m) contra la
    propia malla y los ojos. 1 = libre, 0 = tapado."""
    from mathutils.bvhtree import BVHTree
    import bmesh
    bm = bmesh.new()
    bm.from_mesh(hi.data)
    for o in extra:
        me = o.data.copy()
        me.transform(o.matrix_world)
        bm.from_mesh(me)
        bpy.data.meshes.remove(me)
    tree = BVHTree.FromBMesh(bm)
    bm.free()
    hi.data.update()
    rng = np.random.default_rng(seed)
    u1, u2 = rng.random(rays), rng.random(rays)
    r, phi = np.sqrt(u1), 2 * np.pi * u2
    local = np.stack([r * np.cos(phi), r * np.sin(phi), np.sqrt(1 - u1)], axis=1)
    out = np.ones(len(hi.data.vertices))
    for v in hi.data.vertices:
        n = v.normal
        t = n.orthogonal().normalized()
        b = n.cross(t)
        o = v.co + n * 0.0015
        hit = 0
        for lx, ly, lz in local:
            d = t * lx + b * ly + n * lz
            if tree.ray_cast(o, d, dist)[0] is not None:
                hit += 1
        out[v.index] = 1 - hit / rays
    return out


def ear_uv_mask(parts, res, feather=6, prefixes=("ears", "toe")):
    """Mascara (0..1) en el UV de las zonas donde la malla de alta no coincide con el proxy: orejas (rehechas) y
    dedos de los pies (el proxy no los separa). Caras con algun vertice de peso > 0,3, difuminada."""
    from PIL import Image, ImageDraw, ImageFilter
    im = Image.new("L", (res, res), 0)
    d = ImageDraw.Draw(im)
    for o in parts:
        gids = {g.index for g in o.vertex_groups if g.name.startswith(prefixes)}
        if not gids:
            continue
        w = {v.index: sum(e.weight for e in v.groups if e.group in gids) for v in o.data.vertices}
        # tambien la piel de alrededor de la oreja (se movio con ella): vertices a menos de 2,5 cm de la oreja
        from mathutils.kdtree import KDTree
        eg = o.vertex_groups.get("ears")
        ear_v = [v.co for v in o.data.vertices if eg and any(e.group == eg.index and e.weight > 0.3 for e in v.groups)]
        near = set()
        if ear_v:
            kd = KDTree(len(ear_v))
            for i, c in enumerate(ear_v):
                kd.insert(c, i)
            kd.balance()
            near = {v.index for v in o.data.vertices if kd.find(v.co)[2] < 0.025}
        uv = o.data.uv_layers.active.data
        for p in o.data.polygons:
            if max(w[i] for i in p.vertices) > 0.3 or any(i in near for i in p.vertices):
                d.polygon([(uv[li].uv.x * res, (1 - uv[li].uv.y) * res) for li in p.loop_indices], fill=255)
    im = im.filter(ImageFilter.MaxFilter(9)).filter(ImageFilter.GaussianBlur(feather))
    return np.asarray(im, dtype=np.float32)[::-1] / 255.0          # filas de abajo arriba, como img.pixels


def uv_mask(parts, res):
    """Mascara de todas las caras del proxy en el UV (filas de abajo arriba, como img.pixels)."""
    from PIL import Image, ImageDraw
    im = Image.new("L", (res, res), 0)
    d = ImageDraw.Draw(im)
    for o in parts:
        uv = o.data.uv_layers.active.data
        for p in o.data.polygons:
            d.polygon([(uv[li].uv.x * res, (1 - uv[li].uv.y) * res) for li in p.loop_indices], fill=255)
    return np.asarray(im, dtype=np.float32)[::-1] > 127


def fill_misses(px, inside, valid, iters=40):
    """Texeles dentro del UV donde el rayo no encontro la malla de alta (negro): se rellenan desde los vecinos
    validos por dilatacion iterativa. Devuelve el numero de texeles rellenados."""
    bad = inside & ~valid
    n = int(bad.sum())
    ok = valid.copy()
    c = px[..., :3].copy()
    for _ in range(iters):
        if not (bad & ~ok).any():
            break
        acc = np.zeros_like(c)
        cnt = np.zeros(ok.shape, dtype=np.float32)
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (-1, -1), (1, -1), (-1, 1)):
            sh_ok = np.roll(np.roll(ok, dy, 0), dx, 1)
            sh_c = np.roll(np.roll(c, dy, 0), dx, 1)
            acc += sh_c * sh_ok[..., None]
            cnt += sh_ok
        grow = bad & ~ok & (cnt > 0)
        c[grow] = acc[grow] / cnt[grow][:, None]
        ok = ok | grow
    px[..., :3] = c
    return n


def set_color_attr(o, name, cols):
    a = o.data.color_attributes.get(name) or o.data.color_attributes.new(name, "FLOAT_COLOR", "POINT")
    rgba = np.hstack([cols, np.ones((len(cols), 1))]).astype(np.float32)
    a.data.foreach_set("color", rgba.ravel())


def bake_mat_emit(hi, attr, gray=False):
    """Material de horneado en la malla de alta: atributo de color x ruido suave (solo albedo) -> emision."""
    m = bpy.data.materials.new(f"BAKE_{attr}")
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    em = nt.nodes.new("ShaderNodeEmission")
    at = nt.nodes.new("ShaderNodeAttribute")
    at.attribute_name = attr
    src = at.outputs["Color"]
    if not gray:
        tc = nt.nodes.new("ShaderNodeTexCoord")
        mul = None
        for k, (sc, amp) in enumerate(((7.0, 0.07), (38.0, 0.035))):    # manchas suaves de ~14 cm y ~2,6 cm
            nz = nt.nodes.new("ShaderNodeTexNoise")
            nz.inputs["Scale"].default_value = sc
            nz.inputs["Detail"].default_value = 2.0
            nz.inputs["Roughness"].default_value = 0.45
            nt.links.new(tc.outputs["Object"], nz.inputs["Vector"])
            mr = nt.nodes.new("ShaderNodeMapRange")
            mr.inputs["To Min"].default_value = 1 - amp
            mr.inputs["To Max"].default_value = 1 + amp
            nt.links.new(nz.outputs["Fac"], mr.inputs["Value"])
            if mul is None:
                mul = mr.outputs["Result"]
            else:
                mm = nt.nodes.new("ShaderNodeMath")
                mm.operation = "MULTIPLY"
                nt.links.new(mul, mm.inputs[0])
                nt.links.new(mr.outputs["Result"], mm.inputs[1])
                mul = mm.outputs["Value"]
        vm = nt.nodes.new("ShaderNodeVectorMath")
        vm.operation = "SCALE"
        nt.links.new(src, vm.inputs[0])
        nt.links.new(mul, vm.inputs["Scale"])
        src = vm.outputs["Vector"]
    nt.links.new(src, em.inputs["Color"])
    nt.links.new(em.outputs["Emission"], out.inputs["Surface"])
    hi.data.materials.clear()
    hi.data.materials.append(m)
    return m


def target_mat(lo, img):
    m = bpy.data.materials.new("BAKE_target")
    m.use_nodes = True
    tex = m.node_tree.nodes.new("ShaderNodeTexImage")
    tex.image = img
    m.node_tree.nodes.active = tex
    lo.data.materials.clear()
    lo.data.materials.append(m)
    return m


def new_img(name, res, data=True):
    img = bpy.data.images.new(name, res, res, alpha=False, float_buffer=False)
    img.colorspace_settings.name = "Non-Color" if data else "sRGB"
    return img


def select_only(objs, active):
    for o in bpy.context.view_layer.objects:
        o.select_set(False)
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = active


def bake(scene, kind, hi, lo, img, ext=0.03, ray=0.08, **kw):
    """Alta -> baja. Para el normal map distancias cortas (los dedos no se ven entre si); para color, rugosidad y AO
    largas (un fallo deja negro). El proxy no hace sombra ni tapa los rayos de AO de la malla de alta."""
    target_mat(lo, img)
    for a in ("visible_shadow", "visible_diffuse", "visible_glossy", "visible_transmission", "visible_volume_scatter"):
        setattr(lo, a, False)
    if hi is not None:
        select_only([hi, lo], lo)
        bpy.ops.object.bake(type=kind, use_selected_to_active=True, cage_extrusion=ext, max_ray_distance=ray,
                            margin=8, use_clear=True, **kw)
    else:
        select_only([lo], lo)
        bpy.ops.object.bake(type=kind, margin=8, use_clear=True, **kw)


def save(img, path):
    img.filepath_raw = path
    img.file_format = "PNG"
    img.save()


def img_np(img):
    a = np.array(img.pixels[:], dtype=np.float32).reshape(img.size[1], img.size[0], 4)
    return a


def clamp_saturation(path, smax=0.345):
    """Regla de paleta: ningun texel por encima de s 0,35 (HSV); se baja la saturacion conservando tono y valor."""
    from PIL import Image
    a = np.asarray(Image.open(path).convert("RGB"), dtype=np.float32) / 255.0
    mx, mn = a.max(axis=2, keepdims=True), a.min(axis=2, keepdims=True)
    s = (mx - mn) / np.maximum(mx, 1e-6)
    k = np.where(s > smax, smax / np.maximum(s, 1e-6), 1.0)
    b = mx - (mx - a) * k
    n = int((s > smax).sum())
    Image.fromarray((np.clip(b, 0, 1) * 255 + 0.5).astype(np.uint8)).save(path)
    return n


def max_saturation(path):
    from PIL import Image
    a = np.asarray(Image.open(path).convert("RGB"), dtype=np.float32) / 255.0
    mx, mn = a.max(axis=2), a.min(axis=2)
    s = np.where(mx > 0.02, (mx - mn) / np.maximum(mx, 1e-6), 0)
    used = mx > 0.15                       # fuera quedan los texeles casi negros del margen (cuantizacion de 8 bits)
    return float(np.percentile(s[used], 99.5)), float(s[used].max()), int((s[used] > 0.35).sum())


def bake_all(lo_parts, hi, eyes, J, tex_dir, prefix):
    """Hornea todo sobre una copia unida de las piezas; devuelve rutas e informe."""
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = 16
    os.makedirs(tex_dir, exist_ok=True)
    rep = {}
    # copia unida de las piezas (mismo UV) como destino de horneado
    copies = []
    for o in lo_parts:
        c = o.copy()
        c.data = o.data.copy()
        bpy.context.scene.collection.objects.link(c)
        copies.append(c)
    select_only(copies, copies[0])
    bpy.ops.object.join()
    lo = copies[0]
    lo.name = "TMP_BakeTarget"
    # malla de alta: subdividida un nivel para el normal map
    M = masks(hi, J, eyes)
    hi_s = hi.copy()
    hi_s.data = hi.data.copy()
    bpy.context.scene.collection.objects.link(hi_s)
    hi_s.hide_render = False
    for p in hi_s.data.polygons:
        p.use_smooth = True
    sub = hi_s.modifiers.new("SUB", "SUBSURF")
    sub.levels = sub.render_levels = 1
    paths = {}
    inside = uv_mask(lo_parts, RES)
    # albedo A y B
    for tone in TONES:
        set_color_attr(hi_s, f"ALB_{tone}", vertex_albedo(M, tone))
    set_color_attr(hi_s, "ROUGH", np.repeat(vertex_rough(M)[:, None], 3, axis=1))
    for tone in TONES:
        bake_mat_emit(hi_s, f"ALB_{tone}")
        img = new_img(f"{prefix}_albedo_{tone}", RES, data=False)
        bake(scene, "EMIT", hi_s, lo, img)
        px = img_np(img)
        rep[f"albedo_{tone}_texeles_rellenados"] = fill_misses(px, inside, px[..., :3].max(axis=2) > 0.02)
        img.pixels[:] = px.ravel()
        paths[f"albedo_{tone}"] = os.path.join(tex_dir, f"{prefix}_albedo_{TONES[tone]['nombre']}_1k.png")
        save(img, paths[f"albedo_{tone}"])
        rep[f"texeles_saturacion_recortada_{tone}"] = clamp_saturation(paths[f"albedo_{tone}"])
        rep[f"saturacion_albedo_{tone}"] = [round(x, 3) for x in max_saturation(paths[f"albedo_{tone}"])]
    # rugosidad
    bake_mat_emit(hi_s, "ROUGH", gray=True)
    rimg = new_img(f"{prefix}_rough", RES)
    bake(scene, "EMIT", hi_s, lo, rimg)
    px = img_np(rimg)
    rep["rugosidad_texeles_rellenados"] = fill_misses(px, inside, px[..., 0] > 0.05)
    rimg.pixels[:] = px.ravel()
    # normal
    m_any = bpy.data.materials.new("BAKE_hi_plain")
    m_any.use_nodes = True
    hi_s.data.materials.clear()
    hi_s.data.materials.append(m_any)
    nimg = new_img(f"{prefix}_normal", RES)
    bake(scene, "NORMAL", hi_s, lo, nimg, ext=0.01, ray=0.03, normal_space="TANGENT")
    # en las orejas la malla de alta no coincide con la del proxy (subdividida, concha y perfil propios): normal
    # plano; la forma (borde y concha) la da la geometria
    em = ear_uv_mask(lo_parts, RES)
    nn = img_np(nimg)
    rep["normal_texeles_rellenados"] = fill_misses(nn, inside, nn[..., 2] > 0.3)
    flat = np.array([0.5, 0.5, 1.0], dtype=np.float32)
    nn[..., :3] = nn[..., :3] * (1 - em[..., None]) + flat * em[..., None]
    nimg.pixels[:] = nn.ravel()
    rep["orejas_dedos_pie_normal_plano_texeles"] = int((em > 0.5).sum())
    paths["normal"] = os.path.join(tex_dir, f"{prefix}_normal_1k.png")
    save(nimg, paths["normal"])
    # AO por vertice de la malla de alta (rayos contra ella misma y los ojos) -> emision horneada al proxy
    ao = vertex_ao(hi, [eyes])
    rep["ao_vertices_min_media"] = [round(float(ao.min()), 3), round(float(ao.mean()), 3)]
    set_color_attr(hi_s, "AO", np.repeat(ao[:, None], 3, axis=1))
    bake_mat_emit(hi_s, "AO", gray=True)
    aimg = new_img(f"{prefix}_ao", RES)
    bake(scene, "EMIT", hi_s, lo, aimg)
    px = img_np(aimg)
    # el AO de un vertice nunca es exactamente 0 dentro (se horneo con 24 rayos); negro puro = rayo perdido
    rep["ao_texeles_rellenados"] = fill_misses(px, inside, px[..., 0] > 0.004)
    aimg.pixels[:] = px.ravel()
    a, r = img_np(aimg), img_np(rimg)
    orm = np.zeros_like(a)
    orm[..., 0] = np.clip(0.2 + 0.8 * a[..., 0], 0, 1)       # AO suavizado (el motor anade su propia oclusion)
    orm[..., 1] = r[..., 0]
    orm[..., 2] = 0.0
    orm[..., 3] = 1.0
    oimg = new_img(f"{prefix}_orm", RES)
    oimg.pixels[:] = orm.ravel()
    paths["orm"] = os.path.join(tex_dir, f"{prefix}_orm_1k.png")
    save(oimg, paths["orm"])
    rep["ao_media"] = round(float(a[..., 0][inside].mean()), 3)
    # ojos
    paths["ojos"] = os.path.join(tex_dir, f"{prefix}_ojos_albedo_256.png")
    eye_png(eyes, paths["ojos"])
    # limpieza
    for o in (lo, hi_s):
        me = o.data
        bpy.data.objects.remove(o, do_unlink=True)
        bpy.data.meshes.remove(me)
    for m in [m for m in bpy.data.materials if m.name.startswith("BAKE_")]:
        bpy.data.materials.remove(m)
    for im in [im for im in bpy.data.images if im.name.startswith(prefix)]:
        bpy.data.images.remove(im)
    return paths, rep


def eye_png(eyes, path, res=256):
    """Albedo de los ojos: por cada isla UV (disco) radio relativo r -> pupila, iris, anillo limbal, esclerotica."""
    from PIL import Image
    me = eyes.data
    uv = me.uv_layers.active.data
    discs = []
    for sx in (1, -1):
        pts = [uv[li].uv.copy() for p in me.polygons for li in p.loop_indices
               if me.vertices[me.loops[li].vertex_index].co.x * sx > 0]
        us, vs = [p.x for p in pts], [p.y for p in pts]
        c = ((max(us) + min(us)) / 2, (max(vs) + min(vs)) / 2)
        discs.append((c, max(max(us) - min(us), max(vs) - min(vs)) / 2))
    yy, xx = np.mgrid[0:res, 0:res]
    u, v = (xx + 0.5) / res, 1 - (yy + 0.5) / res
    srgb = lambda h: np.array([int(h[i:i + 2], 16) / 255 for i in (1, 3, 5)])  # noqa: E731
    scl, iris, limb, pup = srgb("#D8D2C8"), srgb(IRIS), srgb("#3F4639"), srgb("#141513")
    out = np.tile(scl, (res, res, 1))
    for (cu, cv), R in discs:
        r = np.sqrt((u - cu) ** 2 + (v - cv) ** 2) / R
        ang = np.arctan2(v - cv, u - cu)
        fib = 1 + 0.08 * np.sin(ang * 23) * np.clip((r - 0.12) / 0.2, 0, 1)
        ir = np.clip(1 - (r - 0.36) / 0.04, 0, 1)[..., None]                   # iris hasta r 0,36-0,40
        lm = np.exp(-((r - 0.37) / 0.035) ** 2)[..., None]
        pu = np.clip(1 - (r - 0.13) / 0.02, 0, 1)[..., None]
        icol = iris * fib[..., None] * (0.85 + 0.25 * np.clip(r / 0.36, 0, 1))[..., None]
        icol = icol * (1 - lm * 0.6) + limb * (lm * 0.6)
        out = out * (1 - ir) + icol * ir
        out = out * (1 - pu) + pup * pu
    Image.fromarray((np.clip(out, 0, 1) * 255).astype(np.uint8)).save(path)


def skin_material(name, alb, nrm, orm):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    bs = nt.nodes.new("ShaderNodeBsdfPrincipled")
    nt.links.new(bs.outputs["BSDF"], out.inputs["Surface"])

    def tex(path, data):
        t = nt.nodes.new("ShaderNodeTexImage")
        t.image = bpy.data.images.load(path, check_existing=True)
        t.image.colorspace_settings.name = "Non-Color" if data else "sRGB"
        return t
    ta = tex(alb, False)
    nt.links.new(ta.outputs["Color"], bs.inputs["Base Color"])
    if nrm:
        tn = tex(nrm, True)
        nm = nt.nodes.new("ShaderNodeNormalMap")
        nt.links.new(tn.outputs["Color"], nm.inputs["Color"])
        nt.links.new(nm.outputs["Normal"], bs.inputs["Normal"])
    if orm:
        to = tex(orm, True)
        sp = nt.nodes.new("ShaderNodeSeparateColor")
        nt.links.new(to.outputs["Color"], sp.inputs["Color"])
        nt.links.new(sp.outputs["Green"], bs.inputs["Roughness"])
        nt.links.new(sp.outputs["Blue"], bs.inputs["Metallic"])
        ng = bpy.data.node_groups.get("glTF Material Output")
        if ng is None:
            ng = bpy.data.node_groups.new("glTF Material Output", "ShaderNodeTree")
            ng.interface.new_socket("Occlusion", in_out="INPUT", socket_type="NodeSocketFloat")
        g = nt.nodes.new("ShaderNodeGroup")
        g.node_tree = ng
        nt.links.new(sp.outputs["Red"], g.inputs["Occlusion"])
    else:
        bs.inputs["Roughness"].default_value = 0.25
    bs.inputs["Specular IOR Level"].default_value = 0.45
    return m
