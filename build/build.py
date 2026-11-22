"""BodyParts3D → 웹용 계통별 바이너리 + manifest 생성
geometry: BodyParts3D 4.0 (human-atlas 저장소의 경량화본) + BodyParts3D 3.0 STL(허파·간)
"""
import json, gzip, re, struct, sys, os
import numpy as np
sys.path.insert(0, '/home/claude/data')
from common import load, NAMES, to_ha
import fast_simplification
import regions as RG
from names_ko import muscle_ko, vessel_ko, vessel_key

OUT = '/home/claude/anatomy-3d/models'
os.makedirs(OUT, exist_ok=True)
A = json.load(open('/home/claude/data/ha/public/models/atlas.json'))
chunks = [gzip.open('/home/claude/data/ha/public/models/body-%d.bin.gz' % i).read() for i in range(len(A['chunks']))]

ORD = {w: i + 1 for i, w in enumerate('first second third fourth fifth sixth seventh eighth ninth tenth eleventh twelfth'.split())}
KNUM = ['', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12']

# ---------- 이름 사전 (영문 기본형 → 한글, 구용어, 설명키, 소그룹) ----------
BONES = {
 'atlas': ('제1목뼈 (고리뼈)', '제1경추 (환추)', 'C1', '척주'),
 'axis': ('제2목뼈 (중쇠뼈)', '제2경추 (축추)', 'C2', '척주'),
 'body of sternum': ('복장뼈 몸통', '흉골체', 'sternum', '가슴우리'),
 'manubrium': ('복장뼈자루', '흉골병', 'sternum', '가슴우리'),
 'xiphoid process': ('칼돌기', '검상돌기', 'sternum', '가슴우리'),
 'calcaneus': ('발꿈치뼈', '종골', 'foot', '다리뼈'), 'talus': ('목말뼈', '거골', 'foot', '다리뼈'),
 'cuboid bone': ('입방뼈', '입방골', 'foot', '다리뼈'),
 'navicular bone of foot': ('발배뼈', '주상골', 'foot', '다리뼈'),
 'medial cuneiform bone': ('안쪽쐐기뼈', '내측설상골', 'foot', '다리뼈'),
 'intermediate cuneiform bone': ('중간쐐기뼈', '중간설상골', 'foot', '다리뼈'),
 'lateral cuneiform bone': ('가쪽쐐기뼈', '외측설상골', 'foot', '다리뼈'),
 'sesamoid bone of foot': ('발 종자뼈', '종자골', 'foot', '다리뼈'),
 'capitate': ('알머리뼈', '유두골', 'hand', '팔뼈'), 'hamate': ('갈고리뼈', '유구골', 'hand', '팔뼈'),
 'lunate': ('반달뼈', '월상골', 'hand', '팔뼈'), 'pisiform': ('콩알뼈', '두상골', 'hand', '팔뼈'),
 'scaphoid': ('손배뼈', '주상골', 'hand', '팔뼈'), 'trapezium': ('큰마름뼈', '대능형골', 'hand', '팔뼈'),
 'trapezoid': ('작은마름뼈', '소능형골', 'hand', '팔뼈'), 'triquetral': ('세모뼈', '삼각골', 'hand', '팔뼈'),
 'clavicle': ('빗장뼈', '쇄골', 'clavicle', '팔뼈'), 'scapula': ('어깨뼈', '견갑골', 'scapula', '팔뼈'),
 'humerus': ('위팔뼈', '상완골', 'humerus', '팔뼈'), 'radius': ('노뼈', '요골', 'radius', '팔뼈'),
 'ulna': ('자뼈', '척골', 'ulna', '팔뼈'),
 'hip bone': ('볼기뼈', '관골', 'hipbone', '골반'), 'sacrum': ('엉치뼈', '천골', 'sacrum', '골반'),
 'femur': ('넙다리뼈', '대퇴골', 'femur', '다리뼈'), 'patella': ('무릎뼈', '슬개골', 'patella', '다리뼈'),
 'tibia': ('정강뼈', '경골', 'tibia', '다리뼈'), 'fibula': ('종아리뼈', '비골', 'fibula', '다리뼈'),
 'frontal bone': ('이마뼈', '전두골', 'skull', '머리뼈'), 'parietal bone': ('마루뼈', '두정골', 'skull', '머리뼈'),
 'occipital bone': ('뒤통수뼈', '후두골', 'skull', '머리뼈'), 'temporal bone': ('관자뼈', '측두골', 'skull', '머리뼈'),
 'sphenoid bone': ('나비뼈', '접형골', 'skull', '머리뼈'), 'ethmoid': ('벌집뼈', '사골', 'skull', '머리뼈'),
 'zygomatic bone': ('광대뼈', '관골(협골)', 'skull', '머리뼈'), 'maxilla': ('위턱뼈', '상악골', 'skull', '머리뼈'),
 'nasal bone': ('코뼈', '비골', 'skull', '머리뼈'), 'palatine bone': ('입천장뼈', '구개골', 'skull', '머리뼈'),
 'vomer': ('보습뼈', '서골', 'skull', '머리뼈'), 'lacrimal bone': ('눈물뼈', '누골', 'skull', '머리뼈'),
 'mandible': ('아래턱뼈', '하악골', 'mandible', '머리뼈'), 'hyoid bone': ('목뿔뼈', '설골', 'hyoid', '머리뼈'),
 'thyroid cartilage': ('방패연골', '갑상연골', 'larynx', '연골'), 'cricoid cartilage': ('반지연골', '윤상연골', 'larynx', '연골'),
 'arytenoid cartilage': ('모뿔연골', '피열연골', 'larynx', '연골'), 'corniculate cartilage': ('잔뿔연골', '소각연골', 'larynx', '연골'),
 'cuneiform cartilage': ('쐐기연골', '설상연골', 'larynx', '연골'), 'major alar cartilage': ('큰코날개연골', '대비익연골', None, '연골'),
}
FING = {'thumb': '엄지', 'index finger': '집게손가락', 'middle finger': '가운데손가락', 'ring finger': '반지손가락', 'little finger': '새끼손가락',
        'big toe': '엄지발가락', 'second toe': '둘째발가락', 'third toe': '셋째발가락', 'fourth toe': '넷째발가락', 'little toe': '새끼발가락'}
PHAL = {'proximal': '첫마디뼈', 'middle': '중간마디뼈', 'distal': '끝마디뼈'}
TOOTH = {'central secondary incisor': '가운데앞니', 'lateral secondary incisor': '옆앞니', 'secondary canine': '송곳니',
         'first secondary premolar': '첫째작은어금니', 'second secondary premolar': '둘째작은어금니',
         'first secondary molar': '첫째큰어금니', 'second secondary molar': '둘째큰어금니'}
REG = {'cervical': ('목뼈', '경추', 'C'), 'thoracic': ('등뼈', '흉추', 'T'), 'lumbar': ('허리뼈', '요추', 'L')}

BRAIN = {
 'cerebellum': ('소뇌', 'cerebellum'), 'pons': ('다리뇌', 'brainstem'), 'medulla oblongata': ('숨뇌', 'brainstem'),
 'midbrain': ('중간뇌', 'brainstem'), 'peduncle of midbrain': ('대뇌다리', 'brainstem'),
 'corpus callosum': ('뇌들보', 'corpuscallosum'), 'thalamus': ('시상', 'thalamus'), 'hypothalamus': ('시상하부', 'hypothalamus'),
 'hippocampus': ('해마', 'limbic'), 'amygdala': ('편도체', 'limbic'), 'fornix of forebrain': ('뇌활', 'limbic'),
 'commissure of fornix of forebrain': ('뇌활맞교차', 'limbic'), 'mammillary body': ('유두체', 'limbic'),
 'cingulate gyrus': ('띠이랑', 'limbic'), 'parahippocampal gyrus': ('해마곁이랑', 'limbic'),
 'caudate nucleus': ('꼬리핵', 'basal'), 'putamen': ('조가비핵', 'basal'), 'globus pallidus': ('창백핵', 'basal'),
 'internal capsule': ('속섬유막', 'basal'), 'insula': ('섬엽', 'cerebrum'),
 'superior frontal gyrus': ('위이마이랑', 'cerebrum'), 'middle frontal gyrus': ('중간이마이랑', 'cerebrum'),
 'inferior frontal gyrus': ('아래이마이랑', 'cerebrum'), 'precentral gyrus': ('중심앞이랑', 'cerebrum'),
 'postcentral gyrus': ('중심뒤이랑', 'cerebrum'), 'superior parietal lobule': ('위마루소엽', 'cerebrum'),
 'supramarginal gyrus': ('모서리위이랑', 'cerebrum'), 'angular gyrus': ('모이랑', 'cerebrum'),
 'anterior part of superior temporal gyrus': ('위관자이랑 앞부분', 'cerebrum'),
 'posterior part of superior temporal gyrus': ('위관자이랑 뒷부분', 'cerebrum'),
 'middle temporal gyrus': ('중간관자이랑', 'cerebrum'), 'inferior temporal gyrus': ('아래관자이랑', 'cerebrum'),
 'fusiform gyrus': ('방추이랑', 'cerebrum'), 'occipital lobe': ('뒤통수엽', 'cerebrum'), 'orbital gyrus': ('눈확이랑', 'cerebrum'),
 'white matter of cerebral hemisphere': ('대뇌반구 백질', 'cerebrum'),
 'lateral ventricle': ('가쪽뇌실', 'ventricles'), 'third ventricle': ('셋째뇌실', 'ventricles'),
 'fourth ventricle': ('넷째뇌실', 'ventricles'), 'cerebral aqueduct': ('중간뇌수도관', 'ventricles'),
 'interventricular foramen': ('뇌실사이구멍', 'ventricles'), 'central canal of spinal cord': ('척수 중심관', 'ventricles'),
 'optic chiasm': ('시각교차', 'visual'), 'optic nerve': ('시각신경', 'visual'), 'optic tract': ('시각로', 'visual'),
 'lateral geniculate body': ('가쪽무릎체', 'visual'), 'medial geniculate body': ('안쪽무릎체', None),
 'superior colliculus': ('위둔덕', 'brainstem'), 'inferior colliculus': ('아래둔덕', 'brainstem'),
 'pituitary gland': ('뇌하수체', 'pituitary'), 'pineal body': ('솔방울샘', 'pineal'),
 'anterior commissure': ('앞맞교차', None), 'posterior commissure': ('뒤맞교차', None), 'habenula': ('고삐', None),
 'septum of telencephalon': ('종뇌사이막', None), 'lamina terminalis': ('종말판', None), 'tuber cinereum': ('회색융기', 'hypothalamus'),
 'stria terminalis': ('분계섬유줄', None), 'stria medullaris of thalamus': ('시상속질섬유줄', None),
 'brachium of superior colliculus': ('위둔덕팔', None), 'brachium of inferior colliculus': ('아래둔덕팔', None),
 'interpeduncular fossa': ('다리사이오목', None), 'choroid plexus of cerebral hemisphere': ('맥락얼기', 'ventricles'),
 'tentorium cerebelli': ('소뇌천막', None),
}
EYE = {'sclera': '공막', 'cornea': '각막', 'iris': '홍채', 'lens': '수정체', 'vitreous body': '유리체', 'choroid': '맥락막',
       'optic part of retina': '망막', 'corona ciliaris': '섬모체관', 'anterior chamber of eyeball': '앞방'}
ORGAN = {  # name(lower, 좌우 제거) : (ko, old, key, sys, group)
 'stomach': ('위', '위', 'stomach', 'digestive', None), 'esophagus': ('식도', '식도', 'esophagus', 'digestive', None),
 'duodenum': ('샘창자', '십이지장', 'smallint', 'digestive', '작은창자'),
 'proximal part of jejunum': ('빈창자 몸쪽부', '공장', 'smallint', 'digestive', '작은창자'),
 'middle part of jejunum': ('빈창자 중간부', '공장', 'smallint', 'digestive', '작은창자'),
 'distal part of jejunum': ('빈창자 먼쪽부', '공장', 'smallint', 'digestive', '작은창자'),
 'proximal part of ileum': ('돌창자 몸쪽부', '회장', 'smallint', 'digestive', '작은창자'),
 'middle part of ileum': ('돌창자 중간부', '회장', 'smallint', 'digestive', '작은창자'),
 'distal part of ileum': ('돌창자 먼쪽부', '회장', 'smallint', 'digestive', '작은창자'),
 'ileocecal junction': ('돌막창자이음부', '회맹부', 'largeint', 'digestive', '큰창자'),
 'appendix': ('막창자꼬리', '충수', 'appendix', 'digestive', '큰창자'),
 'ascending colon': ('오름잘록창자', '상행결장', 'largeint', 'digestive', '큰창자'),
 'transverse colon': ('가로잘록창자', '횡행결장', 'largeint', 'digestive', '큰창자'),
 'descending colon': ('내림잘록창자', '하행결장', 'largeint', 'digestive', '큰창자'),
 'rectum': ('곧창자', '직장', 'largeint', 'digestive', '큰창자'),
 'taenia libera': ('자유띠', '결장띠', 'largeint', 'digestive', '큰창자'), 'taenia mesocolica': ('창자간막띠', '결장띠', 'largeint', 'digestive', '큰창자'),
 'taenia omentalis': ('그물막띠', '결장띠', 'largeint', 'digestive', '큰창자'),
 'liver': ('간', '간', 'liver', 'digestive', '간·쓸개·이자'), 'caudate lobe of liver': ('간 꼬리엽', '미상엽', 'liver', 'digestive', '간·쓸개·이자'),
 'gallbladder': ('쓸개', '담낭', 'gallbladder', 'digestive', '간·쓸개·이자'),
 'cystic duct': ('쓸개관', '담낭관', 'biliary', 'digestive', '간·쓸개·이자'), 'common hepatic duct': ('온간관', '총간관', 'biliary', 'digestive', '간·쓸개·이자'),
 'hepatic duct': ('간관', '간관', 'biliary', 'digestive', '간·쓸개·이자'),
 'pancreas': ('이자', '췌장', 'pancreas', 'digestive', '간·쓸개·이자'), 'parenchyma of pancreas': ('이자 실질', '췌장', 'pancreas', 'digestive', '간·쓸개·이자'),
 'pancreatic duct': ('이자관', '췌관', 'pancreas', 'digestive', '간·쓸개·이자'), 'pancreatic duct tree': ('이자관 가지', '췌관', 'pancreas', 'digestive', '간·쓸개·이자'),
 'tongue': ('혀', '설', 'tongue', 'digestive', '입'), 'submandibular gland': ('턱밑샘', '악하선', 'salivary', 'digestive', '입'),
 'sublingual gland': ('혀밑샘', '설하선', 'salivary', 'digestive', '입'),
 'trachea': ('기관', '기관', 'trachea', 'respiratory', None), 'main bronchus': ('주기관지', '주기관지', 'bronchi', 'respiratory', '기관지'),
 'main bronchus proper': ('주기관지', '주기관지', 'bronchi', 'respiratory', '기관지'),
 'epiglottis': ('후두덮개', '후두개', 'larynx', 'respiratory', None),
 'inferior nasal concha': ('아래코선반', '하비갑개', None, 'respiratory', None),
 'lateral nasal cartilage': ('가쪽코연골', '외측비연골', None, 'respiratory', None),
 'septal nasal cartilage': ('코사이막연골', '비중격연골', None, 'respiratory', None),
 'upper lobe of right lung': ('오른허파 위엽', '우폐 상엽', 'lung_r', 'respiratory', '허파'),
 'middle lobe of lung': ('오른허파 중간엽', '우폐 중엽', 'lung_r', 'respiratory', '허파'),
 'lower lobe of right lung': ('오른허파 아래엽', '우폐 하엽', 'lung_r', 'respiratory', '허파'),
 'upper lobe of left lung': ('왼허파 위엽', '좌폐 상엽', 'lung_l', 'respiratory', '허파'),
 'lower lobe of left lung': ('왼허파 아래엽', '좌폐 하엽', 'lung_l', 'respiratory', '허파'),
 'wall of ventricle': ('심실벽', '심실벽', 'heart', 'cardio', '심장'), 'wall of left atrium': ('왼심방벽', '좌심방벽', 'heart', 'cardio', '심장'),
 'wall of right atrium': ('오른심방벽', '우심방벽', 'heart', 'cardio', '심장'),
 'cavity of left atrium': ('왼심방 안', '좌심방강', 'heart', 'cardio', '심장'), 'cavity of right atrium': ('오른심방 안', '우심방강', 'heart', 'cardio', '심장'),
 'cavity of left ventricle': ('왼심실 안', '좌심실강', 'heart', 'cardio', '심장'), 'cavity of right ventricle': ('오른심실 안', '우심실강', 'heart', 'cardio', '심장'),
 'anterior leaflet of mitral valve': ('승모판 앞첨판', '이첨판 전첨', 'valves', 'cardio', '판막'),
 'posterior leaflet of mitral valve': ('승모판 뒤첨판', '이첨판 후첨', 'valves', 'cardio', '판막'),
 'anterior leaflet of tricuspid valve': ('삼첨판 앞첨판', '삼첨판 전첨', 'valves', 'cardio', '판막'),
 'posterior leaflet of tricuspid valve': ('삼첨판 뒤첨판', '삼첨판 후첨', 'valves', 'cardio', '판막'),
 'septal leaflet of tricuspid valve': ('삼첨판 중격첨판', '삼첨판 중격첨', 'valves', 'cardio', '판막'),
 'anterior cusp of aortic valve': ('대동맥판 앞반달판', '대동맥판', 'valves', 'cardio', '판막'),
 'posterior cusp of aortic valve': ('대동맥판 뒤반달판', '대동맥판', 'valves', 'cardio', '판막'),
 'anterior cusp of pulmonary valve': ('폐동맥판 앞반달판', '폐동맥판', 'valves', 'cardio', '판막'),
 'posterior cusp of pulmonary valve': ('폐동맥판 뒤반달판', '폐동맥판', 'valves', 'cardio', '판막'),
 'spleen': ('지라', '비장', 'spleen', 'cardio', '림프기관'), 'lobe of thymus': ('가슴샘엽', '흉선', 'thymus', 'cardio', '림프기관'),
 'kidney': ('콩팥', '신장', 'kidney', 'urinary', None), 'ureter': ('요관', '요관', 'ureter', 'urinary', None),
 'urinary bladder': ('방광', '방광', 'bladder', 'urinary', None), 'urethra': ('요도', '요도', 'urethra', 'urinary', None),
 'adrenal gland': ('부신', '부신', 'adrenal', 'endocrine', None),
}
SEGB = {'apical': '꼭대기', 'posterior': '뒤', 'anterior': '앞', 'superior': '위', 'lateral': '가쪽', 'medial': '안쪽',
        'anterior basal': '앞바닥', 'lateral basal': '가쪽바닥', 'posterior basal': '뒤바닥', 'medial basal': '안쪽바닥',
        'superior lingular': '위혀', 'inferior lingular': '아래혀'}

def side_of(n):
    m = re.match(r'^(left|right) ', n)
    if m: return m.group(1)
    m = re.search(r' of (left|right) ', n) or re.search(r' (left|right) ', n)
    return m.group(1) if m else None
SKO = {'left': '왼', 'right': '오른', None: ''}
def sideko(s): return {'left': '왼쪽 ', 'right': '오른쪽 '}.get(s, '')

def classify(p):
    """returns dict or None"""
    en = p['name']; n = en.lower(); s = side_of(n); b = re.sub(r'^(left|right) ', '', n)
    b2 = re.sub(r' of (left|right) ', ' of ', b); b2 = re.sub(r'\b(left|right) ', '', b2)
    sysn = p['system']
    # ----- skeletal -----
    if sysn == 'skeletal' or b2 == 'lacrimal bone':
        if re.search(r'gingiva', b): return None
        if re.search(r'fibularis|tibialis|subscapularis|levator scapulae|iliotibial', b):
            r = muscle_ko(b2); return dict(sys='muscular', ko=sideko(s) + r[0], old='', key=r[1], grp=None)
        m = re.match(r'(\w+) rib$', b)
        if m: k = ORD[m.group(1)]; return dict(sys='skeletal', ko=f'{sideko(s)}제{k}갈비뼈', old=f'제{k}늑골', key=f'rib{k}', grp='가슴우리')
        m = re.match(r'(\w+) costal cartilage$', b)
        if m: k = ORD[m.group(1)]; return dict(sys='skeletal', ko=f'{sideko(s)}제{k}갈비연골', old=f'제{k}늑연골', key='costal', grp='가슴우리')
        m = re.match(r'(\w+) (cervical|thoracic|lumbar) vertebra$', b)
        if m:
            k = ORD[m.group(1)]; r = REG[m.group(2)]
            ko = f'제{k}{r[0]}' + (' (솟을뼈)' if r[2] == 'C' and k == 7 else '')
            return dict(sys='skeletal', ko=ko, old=f'제{k}{r[1]}', key=f'{r[2]}{k}', grp='척주')
        m = re.match(r'intervertebral disk of (.+)$', b)
        if m:
            t = m.group(1)
            if t == 'axis': lab = 'C2'
            else:
                mm = re.match(r'(\w+) (cervical|thoracic|lumbar) vertebra', t); lab = REG[mm.group(2)][2] + str(ORD[mm.group(1)])
            return dict(sys='skeletal', ko=f'척추사이원판 ({lab} 아래)', old='추간판', key='disk', grp='척주')
        if b == 'intervertebral disk': return dict(sys='skeletal', ko='척추사이원판', old='추간판', key='disk', grp='척주')
        m = re.match(r'(\w+) (metacarpal|metatarsal) bone$', b)
        if m:
            k = ORD[m.group(1)]; hand = m.group(2) == 'metacarpal'
            return dict(sys='skeletal', ko=f'{sideko(s)}제{k}{"손허리뼈" if hand else "발허리뼈"}', old=f'제{k}{"중수골" if hand else "중족골"}', key='hand' if hand else 'foot', grp='팔뼈' if hand else '다리뼈')
        m = re.match(r'(proximal|middle|distal) phalanx of (.+)$', b2)
        if m:
            dg = m.group(2); hand = 'finger' in dg or dg == 'thumb'
            return dict(sys='skeletal', ko=f'{sideko(s)}{FING[dg]} {PHAL[m.group(1)]}', old='수지골' if hand else '족지골', key='hand' if hand else 'foot', grp='팔뼈' if hand else '다리뼈')
        m = re.match(r'(upper|lower) (.+) tooth$', b)
        if m:
            return dict(sys='skeletal', ko=f'{sideko(s)}{"위" if m.group(1)=="upper" else "아래"} {TOOTH[m.group(2)]}', old='영구치', key='tooth', grp='치아')
        if b2 in BONES:
            ko, old, key, grp = BONES[b2]; return dict(sys='skeletal', ko=sideko(s) + ko, old=old, key=key, grp=grp)
        return dict(sys='skeletal', ko=None, old='', key=None, grp='기타')
    # ----- nervous / sensory -----
    if sysn in ('nervous', 'sensory') or b2 in ('lateral ventricle', 'third ventricle', 'fourth ventricle', 'interventricular foramen'):
        if re.search(r'nerve|ganglion|branch', b) and b2 not in ('optic nerve',):
            ON = {'frontal nerve': ('이마신경', 'cn5'), 'lacrimal nerve': ('눈물신경', 'cn5'), 'nasociliary nerve': ('코섬모체신경', 'cn5'),
                  'supra-orbital nerve': ('눈확위신경', 'cn5'), 'supratrochlear nerve': ('도르래위신경', 'cn5'), 'infratrochlear nerve': ('도르래아래신경', 'cn5'),
                  'long ciliary nerve': ('긴섬모체신경', 'cn5'), 'short ciliary nerve': ('짧은섬모체신경', 'cn3'), 'ciliary ganglion': ('섬모체신경절', 'cn3'),
                  'anterior ethmoidal nerve': ('앞벌집신경', 'cn5'), 'posterior ethmoidal nerve': ('뒤벌집신경', 'cn5'), 'ophthalmic nerve': ('눈신경 (V1)', 'cn5'),
                  'trochlear nerve': ('도르래신경 (IV)', 'cn4'), 'superior branch of oculomotor nerve': ('눈돌림신경 위가지', 'cn3'),
                  'inferior branch of oculomotor nerve': ('눈돌림신경 아래가지', 'cn3'), 'communicating branch of nasociliary nerve with ciliary ganglion': ('코섬모체신경 교통가지', 'cn5')}
            if b2 in ON: return dict(sys='nerves', ko=sideko(s) + ON[b2][0], old='', key=ON[b2][1], grp='뇌신경')
            return None
        if b2 in EYE: return dict(sys='nervous', ko=sideko(s) + EYE[b2], old='', key='eye', grp='눈')
        if b2 in BRAIN:
            ko, key = BRAIN[b2]
            if key in ('pituitary', 'pineal'): return dict(sys='endocrine', ko=ko, old='', key=key, grp=None)
            return dict(sys='nervous', ko=sideko(s) + ko, old='', key=key, grp='뇌')
        return None
    if sysn == 'endocrine' and b2 in ('pituitary gland', 'pineal body'):
        ko, key = BRAIN[b2]; return dict(sys='endocrine', ko=ko, old='', key=key, grp=None)
    if sysn in ('digestive', 'respiratory', 'cardiac', 'urinary', 'endocrine', 'lymphatic'):
        if re.search(r'pharyn|palatopharyngeus|salpingo|stylopharyngeus|mesentery|mesocolon|mesoappendix|biliary tree', b): return None
        m = re.match(r'(.+) segmental bronchial tree$', b2) or re.match(r'(superior|inferior) lingular bronchial tree$', b2)
        if m:
            t = m.group(1) if 'segmental' in b2 else m.group(0).replace(' bronchial tree', '')
            nm = SEGB.get(t, t)
            return dict(sys='respiratory', ko=f'{sideko(s)}{nm}구역기관지', old='구역기관지', key='bronchi', grp='기관지')
        if b2 in ORGAN:
            ko, old, key, sy, grp = ORGAN[b2]
            if b2 in ('kidney', 'ureter', 'adrenal gland', 'submandibular gland', 'sublingual gland', 'hepatic duct', 'lobe of thymus') and s:
                ko = SKO[s] + ko
            if b2 in ('main bronchus', 'main bronchus proper'): ko = SKO[s] + '주기관지' if s else ko
            return dict(sys=sy, ko=ko, old=old, key=key, grp=grp)
        return None
    if sysn in ('muscular', 'connective'):
        r = muscle_ko(b2)
        if not r:
            if sysn == 'connective': return None
            return dict(sys='muscular', ko=None, old='', key=None, grp=None)
        if 'ventricle' in n: return dict(sys='muscular', ko=('왼심실 ' if 'left' in n else '오른심실 ') + r[0], old='', key=r[1], grp='심장·대혈관')
        return dict(sys='muscular', ko=sideko(s) + r[0], old='', key=r[1], grp=None)
    if sysn in ('arterial', 'venous'):
        if re.search(r'ventricle|atrium', n): s = None
        r = vessel_ko(b2)
        return dict(sys=sysn, ko=(sideko(s) + r) if r else None, old='', key=vessel_key(b2), grp=None)
    if sysn == 'reproductive':
        RP = {'testis': ('고환', '고환', 'testis'), 'epididymis': ('부고환', '부고환', 'epididymis'), 'deferent duct': ('정관', '정관', 'ductus'),
              'seminal vesicle': ('정낭', '정낭', 'seminalv'), 'prostate': ('전립샘', '전립선', 'prostate'),
              'corpus cavernosum of penis': ('음경해면체', '음경해면체', 'penis'), 'corpus spongiosum of penis': ('요도해면체', '요도해면체', 'penis'),
              'glans penis': ('음경귀두', '귀두', 'penis')}
        if b2 in RP: ko, old, key = RP[b2]; return dict(sys='reproductive', ko=sideko(s) + ko, old=old, key=key, grp=None)
        return None
    if sysn == 'integumentary' and b == 'skin': return dict(sys='skin', ko='피부', old='', key=None, grp=None)
    return None

# ---------- 수집 ----------
structs = {}  # en -> dict(meta, pos list, idx list)
def put(en, meta, pos, idx):
    st = structs.setdefault(en, dict(meta=meta, P=[], I=[], n=0))
    st['I'].append(idx + st['n']); st['P'].append(pos); st['n'] += len(pos)

skipped = 0
for p in A['parts']:
    c = classify(p)
    if not c: skipped += 1; continue
    if p['name'] == 'Caudate lobe of liver': continue  # 3.0 간 전체 모델로 대체
    buf = chunks[p['chunk']]
    pos = np.frombuffer(buf, dtype='<f4', count=p['vertexCount'] * 3, offset=p['positions']).reshape(-1, 3).astype(np.float64)
    idx = np.frombuffer(buf, dtype='<u4', count=p['indexCount'], offset=p['indices']).astype(np.int64)
    if False and c['sys'] in ('muscular', 'arterial', 'venous') and len(idx) > 900:
        p2, f2 = fast_simplification.simplify(pos.astype(np.float32), idx.reshape(-1, 3).astype(np.int32), target_reduction=0.5)
        pos, idx = p2.astype(np.float64), f2.reshape(-1).astype(np.int64)
    put(p['name'], c, pos, idx)

# 3.0 STL (허파·간): 좌표 정렬 + 경량화
OFF = np.array([0.0, 0.0600, -0.0985])
extra = {'FMA7333': 'Upper lobe of right lung', 'FMA7383': 'Middle lobe of right lung', 'FMA7337': 'Lower lobe of right lung',
         'FMA7370': 'Upper lobe of left lung', 'FMA7371': 'Lower lobe of left lung', 'FMA7197': 'Liver'}
for fid, en in extra.items():
    v = to_ha(load(f'/home/claude/data/bp3d/assets/BodyParts3D_data/stl/{fid}.stl')) + OFF
    q = np.round(v * 1e5).astype(np.int64)
    uq, inv = np.unique(q, axis=0, return_inverse=True)
    pts = uq / 1e5; faces = inv.reshape(-1, 3)
    faces = faces[(faces[:, 0] != faces[:, 1]) & (faces[:, 1] != faces[:, 2]) & (faces[:, 0] != faces[:, 2])]
    target = 0.85 if len(faces) > 20000 else 0.6
    p2, f2 = fast_simplification.simplify(pts.astype(np.float32), faces.astype(np.int32), target_reduction=target)
    print(en, len(faces), '->', len(f2))
    key = en.lower().replace('middle lobe of right lung', 'middle lobe of lung')
    ko, old, k, sy, grp = ORGAN[key]
    put(en, dict(sys=sy, ko=ko, old=old, key=k, grp=grp), p2.astype(np.float64), f2.reshape(-1).astype(np.int64))

import nerves as NV
for o in NV.build():
    put(o['en'], dict(sys='nerves', ko=o['ko'], old='', key=o['key'], grp=o['grp']), o['V'], o['F'].reshape(-1).astype(np.int64))

import hires
hires.upgrade(structs)
import writer
# ---------- 출력 ----------
allp = np.concatenate([np.concatenate(s['P']) for s in structs.values()])
lo = allp.min(0) - 0.001; hi = allp.max(0) + 0.001; sc = (hi - lo) / 65535
RS = {}
RECS = []
files = {}; manifest = []
tri = {}
for i, (en, st) in enumerate(sorted(structs.items(), key=lambda kv: (kv[1]['meta']['sys'], kv[0]))):
    m = st['meta']; P = np.concatenate(st['P']); I = np.concatenate(st['I'])
    if m['sys'] in ('muscular', 'arterial', 'venous') and not m['grp']:
        cx, cy, cz = (P.min(0) + P.max(0)) / 2
        KG = {'deltoid':'팔','biceps':'팔','triceps':'팔','brachialis':'팔','brachioradialis':'팔','forearmext':'팔','forearmflex':'팔','handintr':'팔','rotator':'팔',
              'quadriceps':'다리','hamstring':'다리','adductors':'다리','sartorius':'다리','triceps_surae':'다리','tibant':'다리','legant':'다리','legpost':'다리','fibularis':'다리',
              'gmax':'골반·엉덩이','gmed':'골반·엉덩이','hiprot':'골반·엉덩이','piriformis':'골반·엉덩이','pelvicfloor':'골반·엉덩이','iliopsoas':'골반·엉덩이','tfl':'골반·엉덩이'}
        if m['sys'] == 'muscular' and m['key'] in KG: m['grp'] = KG[m['key']]
        elif m['sys'] != 'muscular' and re.search(r'coronary|cardiac|interventricular|sinus|conus|pulmonary|aorta|vena cava|ventricle', en.lower()) and 1.15 < cy < 1.45: m['grp'] = '심장·대혈관'
        elif cy > 1.40: m['grp'] = '머리·목'
        elif abs(cx) > (0.165 if m['sys'] == 'muscular' else 0.19) and cy > 0.72: m['grp'] = '팔'
        elif cy < 0.80: m['grp'] = '다리'
        elif cy < 0.98: m['grp'] = '골반·엉덩이'
        else: m['grp'] = '몸통'
    I, segs, rst = RG.split(m['sys'], m['key'], en, m['grp'], P, I, 'm')
    for g, (sm, n, mn, mx) in rst.items():
        a_ = RS.setdefault(g, [np.zeros(3), 0, np.full(3, 9.0), np.full(3, -9.0)]); a_[0] += sm; a_[1] += n; a_[2] = np.minimum(a_[2], mn); a_[3] = np.maximum(a_[3], mx)
    qp = np.round((P - lo) / sc).astype('<u2')
    c = ((P.min(0) + P.max(0)) / 2).round(4).tolist(); r = float(np.linalg.norm(P.max(0) - P.min(0)) / 2)
    tri[m['sys']] = tri.get(m['sys'], 0) + len(I) // 3
    manifest.append(dict(id=f's{i}', en=en, ko=m['ko'] or en, old=m['old'], key=m['key'], sys=m['sys'], grp=m['grp'],
                         f=m['sys'], vc=len(P), ic=len(I), c=c, r=round(r, 4), sg=segs))
    RECS.append(dict(file=m['sys'], qp=qp, I=I, man=manifest[-1]))
sizes = writer.emit(RECS, OUT)
REG = {RG.REGIONS[g]: dict(c=(v[0] / v[1]).round(4).tolist(), lo=v[2].round(4).tolist(), hi=v[3].round(4).tolist()) for g, v in RS.items()}
json.dump(dict(lo=lo.round(6).tolist(), sc=sc.tolist(), files=sizes, parts=manifest, regions=REG, regionNames=RG.REGIONS,
               source='BodyParts3D © DBCLS (CC BY 4.0)'), open(f'{OUT}/manifest.json', 'w'), ensure_ascii=False, separators=(',', ':'))
print('structures', len(manifest), 'skipped parts', skipped)
print('tris', tri); print('gz bytes', sizes, sum(sizes.values()) / 1e6, 'MB')
untr = [x['en'] for x in manifest if x['ko'] == x['en']]
print('untranslated', len(untr), untr[:40])
