import numpy as np, json, gzip, re, trimesh, fast_simplification
from lib import *
cat=json.load(open('catalog_raw.json'))
ids=[c['id'] for c in cat]
meshes=[]
for i in ids:
    d=np.load('cache/%s.npz'%i); meshes.append((i,d['V'],d['F']))
# 갈비연골 추가
for sid,fma in FMA.items():
    en=P[sid]['en']
    if 'costal cartilage' in en:
        m=trimesh.load(STL+fma+'.stl',process=True); m.merge_vertices()
        slug=re.sub(r'[^a-z0-9]+','_',en.lower()).strip('_')
        meshes.append((slug,m.vertices,m.faces))
buf=bytearray(); man=[]
tot=0
for i,V,F in meshes:
    n=len(F); tgt=max(160,int(n*0.13))
    if 'tooth' in i: tgt=max(80,int(n*0.06))
    if n>tgt:
        v,f=fast_simplification.simplify(V.astype(np.float32),F.astype(np.int32),target_reduction=1-tgt/n)
    else: v,f=V,F
    lo=v.min(0); hi=v.max(0); sc=(hi-lo)/65535
    q=np.round((v-lo)/np.where(sc>0,sc,1)).astype('<u2')
    vo=len(buf); buf+=q.tobytes()
    if len(buf)%4: buf+=b'\0'*(4-len(buf)%4)
    io=len(buf); buf+=f.astype('<u2').tobytes()
    if len(buf)%4: buf+=b'\0'*(4-len(buf)%4)
    man.append(dict(id=i,vo=vo,vc=len(v),io=io,ic=int(f.size),lo=np.round(lo,3).tolist(),sc=sc.tolist()))
    tot+=len(f)
open('/home/claude/anatomy-3d/bones/m/_skeleton.bin.gz','wb').write(gzip.compress(bytes(buf),9))
json.dump(man,open('ov.json','w'))
print(len(man),'meshes',tot,'tris')
