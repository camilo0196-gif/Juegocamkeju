"""
CONCORDIA - Etapa 26 (punto 1): tabla de bajadas propuestas (solo decoracion, minimo 7 m) con el criterio nuevo del
Faro. Lee concordia_v26.blend (no lo modifica) y escribe docs/reports/stage26_faro_proposal.json.
"""
import bpy, sys, math, json
from collections import Counter, defaultdict
sys.path.insert(0,"/home/user/Juegocamkeju/tools/blender")
from mathutils import Vector
bpy.ops.wm.open_mainfile(filepath="/home/user/Juegocamkeju/blender/concordia_v26.blend")
for o in bpy.data.objects:
    if o.name.endswith(("_LOD1","_LOD2")): o.hide_render=True
import stage26_faro as F, stage25_faro as F25
bvh,owner=F25.occluders(); g=F25.ground_fn(); tg=F.targets()
def zcross(root, eye, t):
    inv=root.matrix_world.inverted(); pts=[]
    for o in [root]+list(root.children_recursive):
        if o.type=="MESH" and not o.name.endswith(F25.SKIP_SUFFIX):
            m2=inv@o.matrix_world; pts+=[m2@Vector(c) for c in o.bound_box]
    x0,x1=min(p.x for p in pts)-0.3,max(p.x for p in pts)+0.3; y0,y1=min(p.y for p in pts)-0.3,max(p.y for p in pts)+0.3
    e,tt=inv@eye,inv@t; zmin=None
    for k in range(401):
        q=e+(tt-e)*(k/400)
        if x0<=q.x<=x1 and y0<=q.y<=y1: zmin=q.z if zmin is None else min(zmin,q.z)
    return zmin
res={}; cats=defaultdict(Counter); lower=defaultdict(dict)
for kind,lst in F25.streets().items():
    n=ok=fix=0
    for sname,pts in lst:
        for p in pts:
            if math.hypot(p.x-F25.FARO_XY[0],p.y-F25.FARO_XY[1])<12: continue
            eye=Vector((p.x,p.y,g(p.x,p.y)+F25.EYE)); n+=1
            rays=[F.ray_roots(bvh,owner,eye,t) for t in tg]
            if any(not r for r in rays): ok+=1; continue
            # can a single decorative lowering (>=7 m) free some ray?
            freed=None
            for r,t in zip(rays,tg):
                if len(r)==1 and F.kind_of(r[0])=="decorativo" and F25.category(r[0])=="edificio":
                    z=zcross(bpy.data.objects[r[0]],eye,t)
                    if z is not None and z-0.3>=F.MIN_DECOR_H:
                        if freed is None or z>freed[1]: freed=(r[0],z)
            if freed:
                fix+=1; nm,z=freed; lower[nm][(kind,sname,tuple(round(c,1) for c in eye))]=round(z-0.3,2)
            else:
                allr={x for r in rays for x in r}
                c={("servicio" if F.kind_of(x)=="servicio" and F25.category(x)=="edificio" else (F25.category(x) if F25.category(x)!="edificio" else "decorativo")) for x in allr}
                cats[kind][" + ".join(sorted(c))]+=1
    res[kind]={"points":n,"now":ok,"pct_now":round(100*ok/n,1),"fixable_by_decor":fix,"pct_if_decor_lowered":round(100*(ok+fix)/n,1)}
print("SIM", json.dumps(res))
for k,v in cats.items(): print("CAT",k,dict(v))
rows=[]
for nm,d in lower.items():
    r=bpy.data.objects[nm]
    rows.append((nm, len(d), dict(Counter(k for k,_s,_e in d)), F.height(r), min(d.values()), r.get("floors")))
rows.sort(key=lambda x:-x[1])
for row in rows: print("ROW", row)
json.dump({"sim":res,"cats":{k:dict(v) for k,v in cats.items()},"rows":rows}, open("/home/user/Juegocamkeju/docs/reports/stage26_faro_proposal.json","w"), indent=1, default=str)
