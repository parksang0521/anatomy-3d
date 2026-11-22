import numpy as np
from pick import mesh
class B:
    """bone-local helper. side 'R' or 'L' or '' (midline). axes: L=lateral, M=medial, A=anterior, P=posterior, S=sup, I=inf"""
    def __init__(s, ids, side='R'):
        s.ids=ids if isinstance(ids,list) else [ids]
        ms=[mesh(i) for i in s.ids]
        s.V=np.concatenate([m.vertices for m in ms]); s.N=np.concatenate([m.vertex_normals for m in ms])
        s.owner=np.concatenate([[i]*len(m.vertices) for i,m in zip(s.ids,ms)])
        s.side=side; mx = 1.0 if side!='L' else -1.0   # medial = +x for right
        s.D={'M':np.array([mx,0,0]),'L':np.array([-mx,0,0]),'A':np.array([0,-1.,0]),'P':np.array([0,1.,0]),'S':np.array([0,0,1.]),'I':np.array([0,0,-1.])}
        s.lo=s.V.min(0); s.hi=s.V.max(0)
        # local normalized coords: m (0 lateral ->1 medial), a (0 post->1 ant), h (0 inf->1 sup)
        n=(s.V-s.lo)/(s.hi-s.lo)
        s.m = n[:,0] if mx>0 else 1-n[:,0]; s.a=1-n[:,1]; s.h=n[:,2]
    def d(s,spec):
        v=np.zeros(3)
        for ch,w in _parse(spec): v+=w*s.D[ch]
        return v/np.linalg.norm(v)
    def mask(s,h=None,m=None,a=None,hm=None,own=None):
        """h: global height fraction. m,a: normalized within the h-slab (hm overrides slab used for m/a)"""
        k=np.ones(len(s.V),bool) if own is None else (s.owner==own)
        if h is not None: k&=(s.h>=h[0])&(s.h<=h[1])
        slab=k.copy() if hm is None else (s.h>=hm[0])&(s.h<=hm[1])
        for arr,r in ((s.m,m),(s.a,a)):
            if r is not None:
                lo,hi=arr[slab].min(),arr[slab].max(); nn=(arr-lo)/(hi-lo+1e-9)
                k&=(nn>=r[0])&(nn<=r[1])
        return k
    def ext(s,dspec,**r):
        k=s.mask(**r); d=s.d(dspec); idx=np.where(k)[0]; i=idx[np.argmax(s.V[idx]@d)]; return i
    def deep(s,dspec,**r):
        """fossa: among verts facing dspec, the least protruding along dspec"""
        k=s.mask(**r); d=s.d(dspec); k&=(s.N@d)>0.3; idx=np.where(k)[0]; i=idx[np.argmin(s.V[idx]@d)]; return i
    def surf(s,dspec,**r):
        """centroid of region projected to the surface facing dspec (ext of region centre)"""
        k=s.mask(**r); d=s.d(dspec); k&=(s.N@d)>0.2; idx=np.where(k)[0]
        c=s.V[idx].mean(0); j=idx[np.argmin(np.linalg.norm(s.V[idx]-c,axis=1)-0.3*(s.V[idx]@d-(s.V[idx]@d).max()))]; return j
    def pt(s,i): return s.V[i], s.owner[i]
    def canal(s,dspec,**r):
        """float point: middle of the vertebral foramen at given height (rays along A at x centre)"""
        from pick import mesh
        import numpy as np
        h=r.get('h',(0.4,0.6)); z=s.lo[2]+(s.hi[2]-s.lo[2])*np.mean(h)
        x=(s.lo[0]+s.hi[0])/2
        hits=[]
        for i in s.ids:
            loc,_,_=mesh(i).ray.intersects_location([[x,s.hi[1]+50,z]],[[0,-1,0]],multiple_hits=True)
            hits+=list(loc)
        ys=sorted(p[1] for p in hits)[::-1]  # from posterior
        if len(ys)>=4: y=(ys[1]+ys[2])/2
        else: y=(s.lo[1]+s.hi[1])/2
        return np.array([x,y,z])
    def centroid(s,dspec,**r):
        k=s.mask(**r); c=s.V[k].mean(0); d=s.d(dspec); idx=np.where(k)[0]
        # surface vertex near centroid facing d
        sc=np.linalg.norm(s.V[idx]-c,axis=1)-0.5*(s.V[idx]@d-(s.V[idx]@d).max())
        return idx[np.argmin(sc)]

    def hole(s,dspec,**r):
        """through-hole centre: rays along axis dspec (S/A/L) over region bbox; returns centre of missed rays"""
        from pick import mesh
        k=s.mask(**{kk:v for kk,v in r.items() if kk in ('h','m','a','own','hm')}); Q=s.V[k]
        d=s.d(dspec); ax=int(np.argmax(np.abs(d)))
        o=[i for i in range(3) if i!=ax]
        lo=Q.min(0); hi=Q.max(0); g=r.get('n',24)
        A,Bv=np.meshgrid(np.linspace(lo[o[0]],hi[o[0]],g),np.linspace(lo[o[1]],hi[o[1]],g))
        org=np.zeros((g*g,3)); org[:,o[0]]=A.ravel(); org[:,o[1]]=Bv.ravel(); org[:,ax]=s.hi[ax]+50
        dirs=np.zeros_like(org); dirs[:,ax]=-1
        hit=np.zeros(len(org),bool)
        for i in s.ids:
            _,ri,_=mesh(i).ray.intersects_location(org,dirs,multiple_hits=False); hit[ri]=True
        miss=org[~hit]
        # keep misses enclosed: drop those on the grid border
        inner=[]
        bord=lambda p:(abs(p[o[0]]-lo[o[0]])<1e-6 or abs(p[o[0]]-hi[o[0]])<1e-6 or abs(p[o[1]]-lo[o[1]])<1e-6 or abs(p[o[1]]-hi[o[1]])<1e-6)
        if len(miss)==0: raise ValueError('no hole')
        # connected components on grid, pick largest not touching border
        mm=(~hit).reshape(g,g); lab=-np.ones((g,g),int); comps=[]
        for i0 in range(g):
            for j0 in range(g):
                if mm[i0,j0] and lab[i0,j0]<0:
                    st=[(i0,j0)]; lab[i0,j0]=len(comps); cells=[]; touch=False
                    while st:
                        i,j=st.pop(); cells.append((i,j))
                        if i in (0,g-1) or j in (0,g-1): touch=True
                        for a2,b2 in ((i+1,j),(i-1,j),(i,j+1),(i,j-1)):
                            if 0<=a2<g and 0<=b2<g and mm[a2,b2] and lab[a2,b2]<0: lab[a2,b2]=len(comps); st.append((a2,b2))
                    comps.append((touch,cells))
        good=[c for t,c in comps if not t] or [c for t,c in comps]
        cells=max(good,key=len)
        P=np.array([org[i*g+j] for i,j in cells]); c=P.mean(0); c[ax]=Q[:,ax].mean()
        return c

def _parse(spec):
    out=[];w=1.0;num=''
    for ch in spec:
        if ch in '0123456789.': num+=ch
        else: out.append((ch,float(num) if num else 1.0)); num=''
    return out

