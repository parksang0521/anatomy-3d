import json
from content import L, TYPES
from bone_info import I
import os
MSET=set(f[:-4] for f in os.listdir('cache'))
items=json.load(open('items.json'))['items']
cat={c['id']:c for c in json.load(open('catalog_raw.json'))}
used=set()
for it in items:
    info=I.get(it['kind']) or I.get(it['id']) or {}
    it['info']=info
    for v in it['var'].values():
        for p in v['pts']: used.add(p[0])
# 핀을 표면 바깥으로 살짝 띄워 가장자리 핀이 가려지지 않게
from pick import mesh as _mesh
import numpy as _np
_cache={}
for it in items:
    for v in it['var'].values():
        for p in v['pts']:
            mid=p[4]
            if mid not in MSET: continue
            m=_mesh(mid); q,d,tri=m.nearest.on_surface([p[1:4]])
            if d[0]<0.6:
                n=m.face_normals[tri[0]]; np_=_np.array(q[0])+n*1.0
                p[1],p[2],p[3]=[round(float(x),1) for x in np_]
meshes={}
for it in items:
    for v in it['var'].values():
        for m in v['meshes']:
            c=cat[m]; meshes[m]=dict(vc=c['vc'],ic=c['ic'],i32=c['i32'],lo=c['lo'],sc=c['sc'],ko=c['ko'],en=c['en'])
D=dict(items=items,lm={k:L[k] for k in sorted(used)},types=TYPES,meshes=meshes)
s=json.dumps(D,ensure_ascii=False,separators=(',',':'))
open('/home/claude/anatomy-3d/bones/data.json','w').write(s)
print(len(s)//1024,'KB', len(items),'items', len(D['lm']),'lm', len(meshes),'meshes')

# ---------- 전신 뼈대 · 탐색 구조 ----------
ov=json.load(open('ov.json'))
src={c['id']:c for c in json.load(open('catalog_raw.json'))}
import re as _re
def nm(i):
    if i in src: return src[i]['en'], src[i]['ko']
    n=i.replace('_',' '); n=n[0].upper()+n[1:]
    m=_re.match(r'(left|right) (\w+) costal cartilage',i.replace('_',' '))
    ko=('왼쪽 ' if i.startswith('left') else '오른쪽 ')+'갈비연골'
    od=['first','second','third','fourth','fifth','sixth','seventh']
    if m: ko=('왼쪽' if m.group(1)=='left' else '오른쪽')+' 제%d갈비연골'%(od.index(m.group(2))+1)
    return n, ko
for o in ov: o['en'],o['ko']=nm(o['id'])
m2i={}
for it in items:
    for sd,v in it['var'].items():
        if len(v['meshes'])==1: m2i.setdefault(v['meshes'][0],[it['id'],sd])
for it in items:
    if it['id'] in ('hand','foot'):
        for sd,v in it['var'].items():
            for m in v['meshes']: m2i.setdefault(m,[it['id'],sd])
for o in ov:
    i=o['id']
    if i in m2i: continue
    if 'tooth' in i: m2i[i]=['mandible',''] if 'lower' in i else (['maxilla','L' if i.startswith('left') else 'R'])
    elif 'costal_cartilage' in i: m2i[i]=['sternum','']
    elif i in ('manubrium','body_of_sternum','xiphoid_process'): m2i[i]=['sternum','']
for o in ov: o['it']=m2i.get(o['id'])
miss=[o['id'] for o in ov if not o['it']]; print('unmapped',miss)
NAV=[
 dict(en='Skull',ko='머리뼈 (두개골)',subs=[
   dict(en='Whole skull',ko='머리뼈 전체',items=['skull']),
   dict(en='Neurocranium',ko='뇌머리뼈',items=['frontal','parietal','occipital','temporal','sphenoid','ethmoid']),
   dict(en='Viscerocranium',ko='얼굴머리뼈',items=['maxilla','zygomatic','palatine','nasal','lacrimal','vomer','mandible']),
   dict(en='Hyoid',ko='목뿔뼈',items=['hyoid'])]),
 dict(en='Vertebral column',ko='척주',subs=[
   dict(en='Whole column',ko='척주 전체',items=['spine']),
   dict(en='Cervical',ko='목뼈',items=['C1','C2','C3','C4','C5','C6','C7']),
   dict(en='Thoracic',ko='등뼈',items=['T%d'%i for i in range(1,13)]),
   dict(en='Lumbar',ko='허리뼈',items=['L%d'%i for i in range(1,6)]),
   dict(en='Sacrum',ko='엉치뼈',items=['sacrum'])]),
 dict(en='Thorax',ko='가슴우리 (상체)',subs=[
   dict(en='Sternum',ko='복장뼈',items=['sternum']),
   dict(en='True ribs',ko='참갈비뼈 (1–7)',items=['rib%d'%i for i in range(1,8)]),
   dict(en='False ribs',ko='거짓갈비뼈 (8–12)',items=['rib%d'%i for i in range(8,13)])]),
 dict(en='Upper limb',ko='팔',subs=[
   dict(en='Shoulder girdle',ko='팔이음뼈',items=['clavicle','scapula']),
   dict(en='Arm',ko='위팔',items=['humerus']),
   dict(en='Forearm',ko='아래팔',items=['radius','ulna']),
   dict(en='Hand',ko='손',items=['hand'])]),
 dict(en='Pelvis',ko='골반',subs=[
   dict(en='Pelvis',ko='골반 전체',items=['pelvis']),
   dict(en='Hip bone',ko='볼기뼈',items=['hip']),
   dict(en='Sacrum',ko='엉치뼈',items=['sacrum'])]),
 dict(en='Lower limb',ko='다리',subs=[
   dict(en='Thigh',ko='넙다리',items=['femur','patella']),
   dict(en='Leg',ko='종아리',items=['tibia','fibula']),
   dict(en='Foot',ko='발',items=['foot','talus','calcaneus'])]),
]
allnav=set(i for c in NAV for s in c['subs'] for i in s['items']); print('not in nav',[it['id'] for it in items if it['id'] not in allnav])
D['ov']=ov; D['nav']=NAV
s=json.dumps(D,ensure_ascii=False,separators=(',',':'))
open('/home/claude/anatomy-3d/bones/data.json','w').write(s)
print('final',len(s)//1024,'KB')
