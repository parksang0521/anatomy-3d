import numpy as np, struct, json, trimesh
STL='/home/claude/src/bp3/assets/BodyParts3D_data/stl/'
FMA=json.load(open('/tmp/sk_fma.json'))
MAN=json.load(open('/home/claude/anatomy-3d/models/manifest.json'))
P={p['id']:p for p in MAN['parts']}
EN2FMA={P[k]['en']:v for k,v in FMA.items()}
def load(en):
    m=trimesh.load(STL+EN2FMA[en]+'.stl',process=True)
    return m
