import numpy as np, trimesh, json
_M={}
def mesh(i):
    if i not in _M:
        d=np.load('cache/%s.npz'%i); _M[i]=trimesh.Trimesh(d['V'],d['F'],process=False)
    return _M[i]
VIEWS={'ant':((0,-1,0),(0,0,1)),'post':((0,1,0),(0,0,1)),'R':((-1,0,0),(0,0,1)),'L':((1,0,0),(0,0,1)),
       'sup':((0,0,1),(0,-1,0)),'inf':((0,0,-1),(0,-1,0))}
def frame(view):
    D,U=map(np.array,VIEWS[view]); D=D.astype(float);U=U.astype(float)
    R=np.cross(-D,U); return D,U,R
def ray(view,a,b,ids,depth_from=None,nth=0,zmax=None,xr=None):
    """screen coords a (screen-right world value), b (screen-up world value). returns (point, mesh id)"""
    D,U,R=frame(view)
    # world value along axis: a is value of the axis R points along (signed axis value, not projection)
    ra=np.argmax(np.abs(R)); ua=np.argmax(np.abs(U)); da=np.argmax(np.abs(D))
    o=np.zeros(3); o[ra]=a; o[ua]=b; o[da]=D[da]*3000 if depth_from is None else depth_from
    d=-D
    hits=[]
    for i in ids:
        m=mesh(i)
        loc,ri,ti=m.ray.intersects_location([o],[d],multiple_hits=True)
        for p in loc:
            if zmax is not None and p[2]>zmax: continue
            if xr is not None and not (xr[0]<=p[0]<=xr[1]): continue
            hits.append((np.dot(p-o,d),p,i))
    if not hits: return None,None
    hits.sort(key=lambda h:h[0])
    h=hits[min(nth,len(hits)-1)]
    return h[1],h[2]
MIR={'R':'L','L':'R'}
def mirror_spec(s):
    s=dict(s); v=s.get('v','')
    if v in MIR: s['v']=MIR[v]
    elif v in ('ant','post'): s['a']=-s['a']
    elif v in ('sup','inf'): s['a']=-s['a']
    if 'xr' in s: s['xr']=[-s['xr'][1],-s['xr'][0]]
    if 'xyz' in s: s['xyz']=[-s['xyz'][0]]+list(s['xyz'][1:])
    return s

def place(s, ids):
    """s: spec dict. returns point,mesh"""
    if 'xyz' in s: 
        p=np.array(s['xyz'],float); best=None
        for i in ids:
            q=mesh(i).nearest.on_surface([p]); d=q[1][0]
            if best is None or d<best[0]: best=(d,q[0][0],i)
        return (p if s.get('free') else best[1]), best[2]
    zmax=s.get('zmax'); nth=s.get('nth',0); xr=s.get('xr')
    if s.get('rim'):
        r=s.get('r',2.5); pts=[];mids=[]
        for t in np.linspace(0,2*np.pi,12,endpoint=False):
            p,i=ray(s['v'],s['a']+r*np.cos(t),s['b']+r*np.sin(t),ids,zmax=zmax,nth=nth,xr=xr)
            if p is not None: pts.append(p);mids.append(i)
        pts=np.array(pts); D,U,R=frame(s['v']); da=np.argmax(np.abs(D))
        dep=np.array([p[da] for p in pts]); 
        # nearest-to-camera cluster
        key=dep*np.sign(D[da]); key0=key.max(); sel=key>key0-6
        c,_=ray(s['v'],s['a'],s['b'],ids,zmax=zmax,nth=nth,xr=xr)
        o=np.zeros(3); ra=np.argmax(np.abs(R)); ua=np.argmax(np.abs(U))
        o[ra]=s['a']; o[ua]=s['b']; o[da]=np.median(dep[sel])
        from collections import Counter
        return o, Counter(np.array(mids)[sel]).most_common(1)[0][0]
    return ray(s['v'],s['a'],s['b'],ids,zmax=zmax,nth=nth,xr=xr)
