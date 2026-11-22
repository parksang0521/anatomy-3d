import json
from content import L, TYPES
from bone_info import I
items=json.load(open('items.json'))['items']
cat={c['id']:c for c in json.load(open('catalog_raw.json'))}
used=set()
for it in items:
    info=I.get(it['kind']) or I.get(it['id']) or {}
    it['info']=info
    for v in it['var'].values():
        for p in v['pts']: used.add(p[0])
meshes={}
for it in items:
    for v in it['var'].values():
        for m in v['meshes']:
            c=cat[m]; meshes[m]=dict(vc=c['vc'],ic=c['ic'],i32=c['i32'],lo=c['lo'],sc=c['sc'],ko=c['ko'],en=c['en'])
D=dict(items=items,lm={k:L[k] for k in sorted(used)},types=TYPES,meshes=meshes)
s=json.dumps(D,ensure_ascii=False,separators=(',',':'))
open('/home/claude/anatomy-3d/bones/data.json','w').write(s)
print(len(s)//1024,'KB', len(items),'items', len(D['lm']),'lm', len(meshes),'meshes')
