import sys,json; sys.path.insert(0,'/home/claude/rt')
from shot import shoot
from PIL import Image
def vb(ids,pts,views,out,size=500,half=55,extra_ids=None,clip=None):
    pins=[dict(p=x['p'],l=str(i)) for i,x in enumerate(pts)]
    J=[]
    for j,(v,c) in enumerate(views):
        cfg={'ids':ids,'view':v,'center':c,'half':half,'W':size,'H':size,'grid':False,'pins':pins}
        if isinstance(v,dict): cfg.update(v)
        J.append((cfg,'/tmp/_q%d.png'%j))
    shoot(J)
    ims=[Image.open('/tmp/_q%d.png'%j) for j in range(len(views))]
    o=Image.new('RGB',(size*len(ims),size),'white'); [o.paste(im,(size*j,0)) for j,im in enumerate(ims)]; o.save(out)
def run(rules,bone,side='R'):
    from auto import B
    import numpy as np
    bs={side:B(bone,side)}
    pts=[]
    for r in rules:
        k,meth,d,reg=r[:4]; opt=r[4] if len(r)>4 else {}
        sides=[side]+(['L' if side=='R' else 'R'] if opt.get('bi') else [])
        for sd in sides:
            if sd not in bs: bs[sd]=B(bone,sd)
            b=bs[sd]
            try: i=getattr(b,meth)(d,**reg)
            except Exception as e: print('ERR',k,e); continue
            if isinstance(i,np.ndarray): p=i; m=b.ids[0]
            else: p,m=b.pt(i)
            pts.append(dict(k=k,p=np.round(p,2).tolist(),m=str(m),side=(sd if opt.get('bi') else '')))
    return pts
