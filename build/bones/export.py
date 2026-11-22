import numpy as np, json, gzip, re, os, trimesh, fast_simplification
from lib import *
OUT='/home/claude/anatomy-3d/bones/m/'; os.makedirs(OUT,exist_ok=True)
os.makedirs('cache',exist_ok=True)
cat=[]
for sid,fma in sorted(FMA.items(), key=lambda kv:P[kv[0]]['en']):
    p=P[sid]; en=p['en']
    if 'disk' in en.lower() or 'cartilage' in en.lower(): continue
    m=trimesh.load(STL+fma+'.stl',process=True)
    m.merge_vertices()
    n=len(m.faces)
    tgt=10000 if re.search(r'\brib\b',en) else 26000
    if n>tgt:
        v,f=fast_simplification.simplify(m.vertices.astype(np.float32),m.faces.astype(np.int32),target_reduction=1-tgt/n)
        m=trimesh.Trimesh(v,f,process=True)
    V=m.vertices; F=m.faces
    slug=re.sub(r'[^a-z0-9]+','_',en.lower()).strip('_')
    np.savez('cache/'+slug+'.npz',V=V,F=F)
    lo=V.min(0); hi=V.max(0); sc=(hi-lo)/65535
    q=np.round((V-lo)/sc).astype('<u2')
    i32=len(V)>65535
    idx=F.astype('<u4' if i32 else '<u2')
    buf=q.tobytes()+idx.tobytes()
    open(OUT+slug+'.bin.gz','wb').write(gzip.compress(buf,9))
    side='R' if en.startswith('Right') else 'L' if en.startswith('Left') else ''
    cat.append(dict(id=slug,en=en,ko=p['ko'],grp=p['grp'],side=side,vc=len(V),ic=int(F.size),i32=bool(i32),lo=lo.round(3).tolist(),sc=sc.tolist()))
    print(slug,n,'->',len(F))
json.dump(cat,open('catalog_raw.json','w'),ensure_ascii=False)
