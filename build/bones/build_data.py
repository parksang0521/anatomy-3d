import json, numpy as np, re
from vb import run
from rules import R, hand, foot
from compute import compute
from pos_skull import SK, MAND
cat=json.load(open('catalog_raw.json')); IDS=[c['id'] for c in cat]
def ids_where(f): return [i for i in IDS if f(i)]
skull=[c['id'] for c in cat if c['grp'] in ('머리뼈','치아') and c['id']!='hyoid_bone']
nm=[i for i in skull if i!='mandible' and 'lower' not in i]
items=[]
def P(lst): return [[x['k'],*[round(v,1) for v in x['p']],x['m'],x.get('side',''),x.get('fl','')] for x in lst]
def add(iid,ko,en,grp,var,kind=None,views=None):
    items.append(dict(id=iid,ko=ko,en=en,grp=grp,var=var,kind=kind or iid,views=views))
# --- skull
sk=compute(SK,skull,nm); md=compute(MAND,['mandible'])
from auto import B as _B
for sd in ('R','L'):
    b=_B('mandible',sd); i=b.ext('P1I1',m=(0,0.12)); p,_=b.pt(i); md.append(dict(k='angle_mandible',side=sd,p=p.round(2).tolist(),m='mandible',alt=0))
for mid,k,d,reg in [('right_nasal_bone','nasal_bone_body','A',{}),('left_nasal_bone','nasal_bone_body','A',{}),('vomer','vomer_body','L',{}),('right_lacrimal_bone','lacrimal_groove','A1L1',{}),('left_lacrimal_bone','lacrimal_groove','A1L1',{})]:
    sd='L' if mid.startswith('left') else ('R' if mid.startswith('right') else '')
    b=_B(mid,sd or 'R'); i=b.centroid(d,**reg); p,_=b.pt(i); sk.append(dict(k=k,side=sd,p=p.round(2).tolist(),m=mid,alt=0))
for x in sk+md: x['m']=str(x['m'])
from pick import mesh as _mesh
def near_bones(p,cands,tol=1.6):
    out=[]
    for c in cands:
        d=_mesh(c).nearest.on_surface([p])[1][0]
        if d<tol: out.append(c)
    return out
skb=[i for i in skull if 'tooth' not in i]
for x in sk: x['near']=near_bones(x['p'],skb)
for x in md: x['near']=['mandible']
add('skull','머리뼈 전체','Skull','머리뼈',{'':dict(meshes=skull,pts=P(sk+md))},views='skull')
def skull_bone(iid,ko,en,mesh_by_side,extra=None):
    var={}
    for sd,mid in mesh_by_side.items():
        pts=[x for x in sk+md if mid in x['near']]
        var[sd]=dict(meshes=[mid],pts=P(pts))
    add(iid,ko,en,'머리뼈',var)
skull_bone('frontal','이마뼈 (전두골)','Frontal bone',{'':'frontal_bone'})
skull_bone('parietal','마루뼈 (두정골)','Parietal bone',{'R':'right_parietal_bone','L':'left_parietal_bone'})
skull_bone('occipital','뒤통수뼈 (후두골)','Occipital bone',{'':'occipital_bone'})
skull_bone('temporal','관자뼈 (측두골)','Temporal bone',{'R':'right_temporal_bone','L':'left_temporal_bone'})
skull_bone('sphenoid','나비뼈 (접형골)','Sphenoid bone',{'':'sphenoid_bone'})
skull_bone('ethmoid','벌집뼈 (사골)','Ethmoid bone',{'':'ethmoid'})
skull_bone('maxilla','위턱뼈 (상악골)','Maxilla',{'R':'right_maxilla','L':'left_maxilla'})
skull_bone('zygomatic','광대뼈 (관골)','Zygomatic bone',{'R':'right_zygomatic_bone','L':'left_zygomatic_bone'})
skull_bone('palatine','입천장뼈 (구개골)','Palatine bone',{'R':'right_palatine_bone','L':'left_palatine_bone'})
skull_bone('nasal','코뼈 (비골)','Nasal bone',{'R':'right_nasal_bone','L':'left_nasal_bone'})
skull_bone('lacrimal','눈물뼈 (누골)','Lacrimal bone',{'R':'right_lacrimal_bone','L':'left_lacrimal_bone'})
skull_bone('vomer','보습뼈 (서골)','Vomer',{'':'vomer'})
mand_teeth=['mandible']+[i for i in skull if 'lower' in i]
add('mandible','아래턱뼈 (하악골)','Mandible','머리뼈',{'':dict(meshes=['mandible'],pts=P(md))})
add('hyoid','목뿔뼈 (설골)','Hyoid bone','머리뼈',{'':dict(meshes=['hyoid_bone'],pts=P(run(R['hyoid'],'hyoid_bone')))})
# --- spine
names=[('atlas','C1','고리뼈 (환추)','Atlas','atlas'),('axis','C2','중쇠뼈 (축추)','Axis','axis')]
ordn=['first','second','third','fourth','fifth','sixth','seventh','eighth','ninth','tenth','eleventh','twelfth']
for i in range(3,8): names.append(('%s_cervical_vertebra'%ordn[i-1],'C%d'%i,'제%d목뼈'%i+(' (솟을뼈)' if i==7 else ''),'C%d vertebra'%i,'c7' if i==7 else 'cervical'))
for i in range(1,13): names.append(('%s_thoracic_vertebra'%ordn[i-1],'T%d'%i,'제%d등뼈'%i,'T%d vertebra'%i,'thoracic'))
for i in range(1,6): names.append(('%s_lumbar_vertebra'%ordn[i-1],'L%d'%i,'제%d허리뼈'%i,'L%d vertebra'%i,'lumbar'))
spine_m=[]; spine_pts=[]
from auto import B
for mid,code,ko,en,rule in names:
    pts=run(R[rule],mid); spine_m.append(mid)
    add(code,ko+'  ·  '+code,en,'척주',{'':dict(meshes=[mid],pts=P(pts))},kind=rule)
    b=B(mid,'R'); i=b.ext('P'); p,_=b.pt(i); spine_pts.append(['vname_'+code,*[round(v,1) for v in p],mid,'',''])
sp=run(R['sacrum'],'sacrum')
add('sacrum','엉치뼈 (천골)','Sacrum','척주',{'':dict(meshes=['sacrum'],pts=P(sp))})
add('spine','척주 전체','Vertebral column','척주',{'':dict(meshes=spine_m+['sacrum'],pts=spine_pts)},views='spine')
# --- thorax
st=['manubrium','body_of_sternum','xiphoid_process']
add('sternum','복장뼈 (흉골)','Sternum','가슴우리',{'':dict(meshes=st,pts=P(run(R['sternum'],st,'R')))})
for n in range(1,13):
    var={}
    for sd,S in (('R','right'),('L','left')):
        mid='%s_%s_rib'%(S,ordn[n-1]); var[sd]=dict(meshes=[mid],pts=P(run(R['rib1' if n==1 else 'rib'],mid,sd)))
    add('rib%d'%n,'제%d갈비뼈'%n+(' (뜬갈비뼈)' if n>=11 else ''),'Rib %d'%n,'가슴우리',var,kind='rib1' if n==1 else 'rib')
# --- limbs
def pair(iid,ko,en,grp,rule,base,kind=None):
    var={}
    for sd,S in (('R','right'),('L','left')):
        mid='%s_%s'%(S,base); var[sd]=dict(meshes=[mid],pts=P(run(R[rule],mid,sd)))
    add(iid,ko,en,grp,var,kind=kind or rule)
pair('clavicle','빗장뼈 (쇄골)','Clavicle','팔','clavicle','clavicle')
pair('scapula','어깨뼈 (견갑골)','Scapula','팔','scapula','scapula')
pair('humerus','위팔뼈 (상완골)','Humerus','팔','humerus','humerus')
pair('radius','노뼈 (요골)','Radius','팔','radius','radius')
pair('ulna','자뼈 (척골)','Ulna','팔','ulna','ulna')
var={}
for sd,S in (('R','right'),('L','left')):
    ms=ids_where(lambda i: (S in i) and any(k in i for k in ['scaphoid','lunate','triquetral','pisiform','trapezium','trapezoid','capitate','hamate','metacarpal','finger','thumb']))
    var[sd]=dict(meshes=ms,pts=P(run(hand(sd),ms,sd)))
add('hand','손뼈 (손목·손허리·손가락)','Bones of the hand','팔',var,kind='hand')
pair('hip','볼기뼈 (관골)','Hip bone','다리','hip','hip_bone')
var={}
for sd,S in (('R','right'),('L','left')):
    pass
pv=P(run(R['hip'],'right_hip_bone','R'))+P(run(R['hip'],'left_hip_bone','L'))+P(sp)
add('pelvis','골반 전체','Pelvis','다리',{'':dict(meshes=['right_hip_bone','left_hip_bone','sacrum'],pts=pv)},kind='pelvis')
pair('femur','넙다리뼈 (대퇴골)','Femur','다리','femur','femur')
pair('patella','무릎뼈 (슬개골)','Patella','다리','patella','patella')
pair('tibia','정강뼈 (경골)','Tibia','다리','tibia','tibia')
pair('fibula','종아리뼈 (비골)','Fibula','다리','fibula','fibula')
var={};tal={};cal={}
for sd,S in (('R','right'),('L','left')):
    ms=ids_where(lambda i: (S in i) and any(k in i for k in ['talus','calcaneus','navicular','cuboid','cuneiform','metatarsal','toe','sesamoid_bone_of']))
    pts=P(run(foot(sd),ms,sd)); var[sd]=dict(meshes=ms,pts=pts)
    tal[sd]=dict(meshes=['%s_talus'%S],pts=[p for p in pts if p[4]=='%s_talus'%S])
    cal[sd]=dict(meshes=['%s_calcaneus'%S],pts=[p for p in pts if p[4]=='%s_calcaneus'%S])
add('foot','발뼈 (발목·발허리·발가락)','Bones of the foot','다리',var,kind='foot')
add('talus','목말뼈 (거골)','Talus','다리',tal)
add('calcaneus','발꿈치뼈 (종골)','Calcaneus','다리',cal)
json.dump(dict(items=items),open('items.json','w'),ensure_ascii=False)
keys=sorted(set(p[0] for it in items for v in it['var'].values() for p in v['pts']))
json.dump(keys,open('keys.json','w'))
print(len(items),len(keys))
