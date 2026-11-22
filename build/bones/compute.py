import json,sys,numpy as np
from pick import *
def compute(specs, ids, ids_nm=None):
    out=[]
    for s in specs:
        for side in ([0,1] if s.get('bi') else [0]):
            ss=mirror_spec(s) if side else dict(s)
            use=ids_nm if (s.get('nm') and ids_nm) else ids
            p,m=place(ss,use)
            pts=[(p,m)]
            if 's2' in s:
                s2=mirror_spec(s['s2']) if side else dict(s['s2'])
                pts.append(place(s2,use))
            for j,(p,m) in enumerate(pts):
                if p is None: print('MISS',s['k'],side,j,file=sys.stderr); continue
                vv=(s['s2'].get('v','') if j else s.get('v',''))
                out.append(dict(k=s['k'],side='L' if side else ('R' if s.get('bi') else ''),p=[round(float(x),2) for x in p],m=m,alt=j,fl=('i' if vv=='sup' else 'e' if vv=='inf' else '')))
    return out
