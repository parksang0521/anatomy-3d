import re
# ---------------- 근육 ----------------
MUS = {
 'abductor digiti minimi of foot': ('새끼벌림근(발)', None), 'abductor digiti minimi of hand': ('새끼벌림근(손)', None),
 'abductor hallucis': ('엄지벌림근(발)', None), 'abductor pollicis brevis': ('짧은엄지벌림근', None), 'abductor pollicis longus': ('긴엄지벌림근', None),
 'adductor brevis': ('짧은모음근', 'adductors'), 'adductor longus': ('긴모음근', 'adductors'), 'adductor magnus': ('큰모음근', 'adductors'), 'adductor minimus': ('작은모음근', 'adductors'),
 'anconeus': ('팔꿈치근', None), 'aryepiglotticus': ('모뿔후두덮개근', None), 'brachialis': ('위팔근', 'brachialis'), 'brachioradialis': ('위팔노근', 'brachioradialis'),
 'cervical rotator': ('목돌림근', 'erector'), 'lumbar rotator': ('허리돌림근', 'erector'), 'thoracic rotator': ('가슴돌림근', 'erector'),
 'coccygeus': ('꼬리근', 'pelvicfloor'), 'coracobrachialis': ('부리위팔근', None), 'diaphragm': ('가로막', 'diaphragm'), 'digastric': ('두힘살근', None),
 'extensor carpi radialis brevis': ('짧은노쪽손목폄근', 'forearmext'), 'extensor carpi radialis longus': ('긴노쪽손목폄근', 'forearmext'),
 'extensor carpi ulnaris': ('자쪽손목폄근', 'forearmext'), 'extensor digiti minimi': ('새끼폄근', 'forearmext'), 'extensor digitorum': ('손가락폄근', 'forearmext'),
 'extensor digitorum longus': ('긴발가락폄근', 'legant'), 'extensor hallucis brevis': ('짧은엄지폄근(발)', None), 'extensor hallucis longus': ('긴엄지폄근(발)', 'legant'),
 'extensor indicis': ('집게폄근', 'forearmext'), 'extensor pollicis brevis': ('짧은엄지폄근', 'forearmext'), 'extensor pollicis longus': ('긴엄지폄근', 'forearmext'),
 'external anal sphincter': ('바깥항문조임근', 'pelvicfloor'), 'external intercostal muscle': ('바깥갈비사이근', 'intercostal'),
 'internal intercostal muscle': ('속갈비사이근', 'intercostal'), 'innermost intercostal muscle': ('맨속갈비사이근', 'intercostal'),
 'external oblique': ('배바깥빗근', 'extoblique'), 'flexor accessorius': ('발바닥네모근', None), 'flexor carpi radialis': ('노쪽손목굽힘근', 'forearmflex'),
 'flexor digiti minimi brevis of foot': ('짧은새끼굽힘근(발)', None), 'flexor digiti minimi brevis of hand': ('짧은새끼굽힘근(손)', None),
 'flexor digitorum brevis': ('짧은발가락굽힘근', None), 'flexor digitorum longus': ('긴발가락굽힘근', 'legpost'),
 'flexor digitorum profundus': ('깊은손가락굽힘근', 'forearmflex'), 'flexor digitorum superficialis': ('얕은손가락굽힘근', 'forearmflex'),
 'flexor hallucis longus': ('긴엄지굽힘근(발)', 'legpost'), 'flexor pollicis brevis': ('짧은엄지굽힘근', None), 'flexor pollicis longus': ('긴엄지굽힘근', 'forearmflex'),
 'gemellus inferior': ('아래쌍둥이근', 'hiprot'), 'gemellus superior': ('위쌍둥이근', 'hiprot'), 'genioglossus': ('턱끝혀근', None), 'geniohyoid': ('턱끝목뿔근', None),
 'gluteus maximus': ('큰볼기근', 'gmax'), 'gluteus medius': ('중간볼기근', 'gmed'), 'gluteus minimus': ('작은볼기근', 'gmed'), 'gracilis': ('두덩정강근', 'adductors'),
 'hyoglossus': ('목뿔혀근', None), 'iliacus': ('엉덩근', 'iliopsoas'), 'psoas major': ('큰허리근', 'iliopsoas'), 'iliococcygeus': ('엉덩꼬리근', 'pelvicfloor'),
 'pubococcygeus': ('두덩꼬리근', 'pelvicfloor'), 'puborectalis': ('두덩곧창자근', 'pelvicfloor'),
 'iliocostalis cervicis': ('목엉덩갈비근', 'erector'), 'iliocostalis lumborum': ('허리엉덩갈비근', 'erector'), 'iliocostalis thoracis': ('가슴엉덩갈비근', 'erector'),
 'longissimus capitis': ('머리가장긴근', 'erector'), 'longissimus cervicis': ('목가장긴근', 'erector'), 'longissimus thoracis': ('가슴가장긴근', 'erector'),
 'spinalis': ('가시근', 'erector'), 'spinalis thoracis': ('가슴가시근', 'erector'),
 'inferior oblique': ('아래빗근(눈)', 'eyemus'), 'superior oblique': ('위빗근(눈)', 'eyemus'), 'inferior rectus': ('아래곧은근', 'eyemus'), 'superior rectus': ('위곧은근', 'eyemus'),
 'lateral rectus': ('가쪽곧은근', 'eyemus'), 'medial rectus': ('안쪽곧은근', 'eyemus'), 'levator palpebrae superioris': ('위눈꺼풀올림근', 'eyemus'),
 'infraspinatus muscle': ('가시아래근', 'rotator'), 'supraspinatus': ('가시위근', 'rotator'), 'teres minor': ('작은원근', 'rotator'), 'subscapularis': ('어깨밑근', 'rotator'),
 'teres major': ('큰원근', None), 'interspinalis thoracis': ('가슴가시사이근', None), 'lateral crico-arytenoid': ('가쪽반지모뿔근', 'laryngeal'),
 'posterior crico-arytenoid': ('뒤반지모뿔근', 'laryngeal'), 'oblique arytenoid': ('빗모뿔근', 'laryngeal'), 'transverse arytenoid': ('가로모뿔근', 'laryngeal'),
 'thyro-arytenoid': ('방패모뿔근', 'laryngeal'), 'vocalis': ('성대근', 'laryngeal'),
 'lateral lumbar intertransversarius': ('가쪽허리가로돌기사이근', None), 'medial lumbar intertransversarius': ('안쪽허리가로돌기사이근', None),
 'levator veli palatini': ('입천장올림근', None), 'tensor veli palatini': ('입천장긴장근', None), 'uvular muscle': ('목젖근', None),
 'longus capitis': ('머리긴근', None), 'mylohyoid': ('턱목뿔근', None), 'obliquus capitis inferior': ('아래머리빗근', 'suboccipital'), 'obliquus capitis superior': ('위머리빗근', 'suboccipital'),
 'rectus capitis posterior major': ('큰뒤머리곧은근', 'suboccipital'), 'rectus capitis posterior minor': ('작은뒤머리곧은근', 'suboccipital'),
 'rectus capitis anterior': ('앞머리곧은근', None), 'rectus capitis lateralis': ('가쪽머리곧은근', None),
 'obturator externus': ('바깥폐쇄근', 'hiprot'), 'obturator internus': ('속폐쇄근', 'hiprot'), 'quadratus femoris': ('넙다리네모근', 'hiprot'), 'piriformis': ('궁둥구멍근', 'piriformis'),
 'omohyoid': ('어깨목뿔근', 'infrahyoid'), 'sternohyoid': ('복장목뿔근', 'infrahyoid'), 'sternothyroid': ('복장방패근', 'infrahyoid'), 'thyrohyoid': ('방패목뿔근', 'infrahyoid'),
 'stylohyoid': ('붓목뿔근', None), 'opponens digiti minimi of foot': ('새끼맞섬근(발)', None), 'opponens digiti minimi of hand': ('새끼맞섬근(손)', None),
 'opponens pollicis': ('엄지맞섬근', None), 'palmaris longus': ('긴손바닥근', 'forearmflex'), 'pectineus': ('두덩근', 'adductors'),
 'pectoralis minor': ('작은가슴근', 'pecminor'), 'plantaris': ('장딴지빗근', 'legpost'), 'platysma': ('넓은목근', None), 'popliteus': ('오금근', 'legpost'),
 'pronator quadratus': ('네모엎침근', 'forearmflex'), 'rectus femoris': ('넙다리곧은근', 'quadriceps'), 'vastus intermedius': ('중간넓은근', 'quadriceps'),
 'vastus lateralis': ('가쪽넓은근', 'quadriceps'), 'vastus medialis': ('안쪽넓은근', 'quadriceps'), 'rhomboid major': ('큰마름근', 'rhomboid'), 'rhomboid minor': ('작은마름근', 'rhomboid'),
 'sartorius': ('넙다리빗근', 'sartorius'), 'scalenus anterior': ('앞목갈비근', 'scalene'), 'scalenus medius': ('중간목갈비근', 'scalene'), 'scalenus posterior': ('뒤목갈비근', 'scalene'),
 'semimembranosus': ('반막근', 'hamstring'), 'semitendinosus': ('반힘줄근', 'hamstring'),
 'semispinalis capitis': ('머리반가시근', None), 'semispinalis cervicis': ('목반가시근', None), 'semispinalis thoracis': ('가슴반가시근', None),
 'serratus anterior': ('앞톱니근', 'serratus'), 'serratus posterior inferior': ('아래뒤톱니근', None), 'serratus posterior superior': ('위뒤톱니근', None),
 'set of anterior cervical intertransversarii': ('앞목가로돌기사이근', None), 'set of posterior cervical intertransversarii': ('뒤목가로돌기사이근', None),
 'set of dorsal interossei of hand': ('손등쪽뼈사이근', 'handintr'), 'set of palmar interossei of hand': ('바닥쪽뼈사이근(손)', 'handintr'),
 'set of lumbricals of hand': ('벌레근(손)', 'handintr'), 'set of interspinales cervicis': ('목가시사이근', None), 'set of interspinales lumborum': ('허리가시사이근', None),
 'set of levatores costarum breves': ('짧은갈비올림근', None), 'set of levatores costarum longi': ('긴갈비올림근', None),
 'soleus': ('가자미근', 'triceps_surae'), 'splenius capitis': ('머리널판근', None), 'splenius cervicis': ('목널판근', None),
 'sternocleidomastoid': ('목빗근', 'scm'), 'subclavius': ('빗장밑근', None), 'superficial perineal muscle': ('얕은샅가로근', 'pelvicfloor'),
 'supinator': ('손뒤침근', None), 'transversus thoracis': ('가슴가로근', None),
 'tibialis anterior': ('앞정강근', 'tibant'), 'tibialis posterior': ('뒤정강근', 'legpost'), 'fibularis brevis': ('짧은종아리근', 'fibularis'),
 'fibularis longus': ('긴종아리근', 'fibularis'), 'fibularis tertius': ('셋째종아리근', 'legant'), 'levator scapulae': ('어깨올림근', None),
 'iliotibial tract': ('엉덩정강띠', None), 'tensor fasciae latae': ('넙다리근막긴장근', 'tfl'), 'calcaneal tendon': ('발꿈치힘줄 (아킬레스힘줄)', 'triceps_surae'),
 'linea alba': ('백색선', None), 'interosseous membrane of forearm': ('아래팔뼈사이막', None), 'interosseous membrane of leg': ('종아리뼈사이막', None),
 'long plantar ligament': ('긴발바닥인대', None),
}
PARTS = {  # 'X part/head of Y'
 'deltoid': ('어깨세모근', 'deltoid'), 'pectoralis major': ('큰가슴근', 'pecmajor'), 'trapezius': ('등세모근', 'trapezius'),
 'triceps brachii': ('위팔세갈래근', 'triceps'), 'biceps brachii': ('위팔두갈래근', 'biceps'), 'biceps femoris': ('넙다리두갈래근', 'hamstring'),
 'gastrocnemius': ('장딴지근', 'triceps_surae'), 'flexor carpi ulnaris': ('자쪽손목굽힘근', 'forearmflex'), 'pronator teres': ('원엎침근', 'forearmflex'),
 'flexor hallucis brevis': ('짧은엄지굽힘근(발)', None), 'adductor hallucis': ('엄지모음근(발)', None), 'adductor pollicis': ('엄지모음근', None),
 'longus colli': ('목긴근', None), 'cricothyroid': ('반지방패근', 'laryngeal'), 'flexor pollicis brevis': ('짧은엄지굽힘근', None),
}
PART_W = {'acromial part': '봉우리부분', 'clavicular part': '빗장부분', 'spinal part': '가시부분', 'abdominal part': '배부분', 'sternocostal part': '복장갈비부분',
          'ascending part': '오름부분', 'transverse part': '가로부분', 'descending part': '내림부분', 'long head': '긴갈래', 'short head': '짧은갈래',
          'lateral head': '가쪽갈래', 'medial head': '안쪽갈래', 'humeral head': '위팔갈래', 'ulnar head': '자갈래', 'oblique head': '빗갈래', 'transverse head': '가로갈래',
          'superficial head': '얕은갈래', 'oblique part': '빗부분', 'straight part': '곧은부분', 'inferior oblique part': '아래빗부분', 'superior oblique part': '위빗부분',
          'vertical intermediate part': '수직부분'}
ORDW = {'first': '제1', 'second': '제2', 'third': '제3', 'fourth': '제4', 'fifth': '제5'}

def muscle_ko(b):
    """b: 좌우 제거된 소문자 이름 → (ko, key) 또는 None"""
    if b in MUS: return MUS[b]
    m = re.match(r'(\w+) (lumbrical|plantar interosseous) of foot$', b)
    if m: return (f'{ORDW[m.group(1)]}{"벌레근(발)" if m.group(2)=="lumbrical" else "바닥쪽뼈사이근(발)"}', None)
    m = re.match(r'(.+?) of (.+)$', b)
    if m and m.group(1) in PART_W and m.group(2) in PARTS:
        ko, key = PARTS[m.group(2)]; return (f'{ko} {PART_W[m.group(1)]}', key)
    if 'papillary muscle' in b:
        w = {'anterior': '앞', 'posterior': '뒤', 'septal': '중격', 'lateral': '가쪽'}
        t = b.split(' papillary')[0].replace('anterolateral head of ', '')
        return (f'{w.get(t.split()[0], "")}꼭지근', 'heartmus')
    return None

# ---------------- 혈관 ----------------
V = {  # 핵심 이름(동맥/정맥 접미사 제외) → 한글 어간
 'abdominal aorta': '배대동맥', 'arch of aorta': '대동맥활', 'ascending aorta': '오름대동맥', 'descending aorta': '내림대동맥', 'descending thoracic aorta': '가슴대동맥',
 'pulmonary trunk': '허파동맥줄기', 'celiac trunk': '복강동맥줄기', 'costocervical trunk': '갈비목동맥줄기', 'thyrocervical trunk': '갑상목동맥줄기',
 'superior vena cava': '위대정맥', 'inferior vena cava': '아래대정맥', 'coronary sinus': '심장정맥굴', 'plantar arch': '발바닥동맥활', 'deep palmar arch': '깊은손바닥동맥활',
 'superficial palmar arterial arch': '얕은손바닥동맥활', 'deep palmar venous arch': '깊은손바닥정맥활', 'superficial palmar venous arch': '얕은손바닥정맥활',
 'dorsal venous arch of foot': '발등정맥활', 'plantar venous arch of foot': '발바닥정맥활', 'dorsal venous network of hand': '손등정맥그물',
 'arteria princeps pollicis': '엄지으뜸동맥', 'arteria radialis indicis': '집게노쪽동맥', 'hepatic artery proper': '고유간동맥',
 'hepatic portal vein': '간문맥', 'portal vein': '문맥', 'pre-hepatic portal vein': '간앞 문맥', 'dorsal artery of penis': '음경등동맥', 'deep dorsal vein of penis': '깊은음경등정맥', 'superficial dorsal vein of penis': '얕은음경등정맥', 'marginal artery of colon': '잘록창자가장자리동맥', 'posterior vein of ventricle': '왼심실뒤정맥', 'dorsal digital artery of foot': '발등쪽발가락동맥', 'set of plantar digital arteries proper': '고유발바닥쪽발가락동맥들',
}
W = {  # 단어 단위
 'anterior': '앞', 'posterior': '뒤', 'superior': '위', 'inferior': '아래', 'medial': '안쪽', 'lateral': '가쪽', 'middle': '중간', 'deep': '깊은', 'superficial': '얕은',
 'common': '온', 'internal': '속', 'external': '바깥', 'ascending': '오름', 'descending': '내림', 'great': '큰', 'small': '작은', 'dorsal': '등쪽', 'palmar': '손바닥',
 'plantar': '발바닥', 'proper': '고유', 'recurrent': '되돌이', 'circumflex': '휘돌이', 'collateral': '곁', 'transverse': '가로', 'accessory': '덧', 'marginal': '모서리',
 'first': '제1', 'second': '제2', 'third': '제3', 'fourth': '제4', 'cerebral': '대뇌', 'cerebellar': '소뇌', 'carotid': '목', 'iliac': '엉덩', 'femoral': '넙다리',
 'humeral': '위팔', 'brachial': '위팔', 'radial': '노', 'ulnar': '자', 'tibial': '정강', 'fibular': '종아리', 'popliteal': '오금', 'axillary': '겨드랑', 'subclavian': '빗장밑',
 'brachiocephalic': '팔머리', 'vertebral': '척추', 'basilar': '뇌바닥', 'communicating': '교통', 'choroidal': '맥락얼기', 'ophthalmic': '눈', 'thoracic': '가슴',
 'intercostal': '갈비사이', 'subcostal': '갈비밑', 'epigastric': '배벽', 'phrenic': '가로막', 'musculophrenic': '근육가로막', 'thoracodorsal': '가슴등', 'subscapular': '어깨밑',
 'suprascapular': '어깨위', 'scapular': '어깨', 'cervical': '목', 'thyroid': '갑상', 'hepatic': '간', 'gastric': '위', 'gastro-epiploic': '위그물막', 'gastroepiploic': '위그물막',
 'gastroduodenal': '위샘창자', 'splenic': '지라', 'pancreatic': '이자', 'pancreaticoduodenal': '이자샘창자', 'mesenteric': '창자간막', 'ileocolic': '돌잘록창자', 'ileal': '돌창자',
 'colic': '잘록창자', 'sigmoid': '구불잘록창자', 'rectal': '곧창자', 'appendicular': '막창자꼬리', 'cecal': '막창자', 'renal': '콩팥', 'suprarenal': '부신', 'testicular': '고환',
 'lumbar': '허리', 'genicular': '무릎', 'tarsal': '발목', 'arcuate': '활꼴', 'metatarsal': '발허리', 'metacarpal': '손허리', 'digital': '손발가락', 'pulmonary': '허파',
 'bronchial': '기관지', 'esophageal': '식도', 'coronary': '심장', 'spinal': '척수', 'pontine': '다리뇌', 'callosomarginal': '뇌들보모서리', 'pericallosal': '뇌들보주위',
 'celiac': '복강', 'jugular': '목', 'azygos': '홀', 'hemiazygos': '반홀', 'cephalic': '노쪽피부', 'basilic': '자쪽피부', 'saphenous': '두렁', 'cubital': '팔오금',
 'antebrachial': '아래팔', 'median': '정중', 'sacral': '엉치', 'gluteal': '볼기', 'pudendal': '음부', 'obturator': '폐쇄', 'iliolumbar': '엉덩허리', 'cardiac': '심장',
 'interventricular': '심실사이', 'segmental': '구역', 'apical': '꼭대기', 'basal': '바닥', 'lingular': '혀', 'perforating': '관통', 'interosseous': '뼈사이',
 'thoraco-acromial': '가슴봉우리', 'acromial': '봉우리', 'deltoid': '어깨세모근', 'pectoral': '가슴근', 'carpal': '손목', 'calcaneal': '발꿈치', 'temporal': '관자',
 'occipital': '뒤통수', 'parietal': '마루', 'frontobasal': '이마바닥', 'prefrontal': '이마앞', 'insular': '섬', 'polar': '극', 'precuneal': '쐐기앞', 'paracentral': '중심옆',
 'thalamogeniculate': '시상무릎', 'thalamoperforating': '시상관통', 'splenial': '팽대', 'conus': '동맥원뿔', 'diagonal': '대각', 'septal': '사이막', 'vermian': '벌레',
 'hypothalamic': '시상하부', 'dorsalis pedis': '발등', 'penis': '음경', 'of penis': '음경', 'ureteric': '요관', 'upper': '위', 'lobar': '엽', 'lobe': '엽', 'caudal': '꼬리',
 'deep brachial': '깊은위팔', 'temporo-occipital': '관자뒤통수', 'intermediomedial': '중간안쪽', 'posteromedial': '뒤안쪽', 'anterolateral': '앞가쪽',
 'laterobasal': '가쪽바닥', 'caudate': '꼬리', 'distal': '먼쪽', 'ventricular': '심실', 'postcommunicating': '교통뒤', 'precommunicating': '교통앞', 'sphenoid': '나비', 'terminal': '끝', 'oesophageal': '식도', 'colon': '잘록창자', 'mediobasal': '안쪽바닥', 'subsuperior': '위아래', 'central': '중심', 'sulcus': '고랑', 'postcentral': '중심뒤', 'precentral': '중심앞',
}
PHR = {  # 다단어 형용 구 (어순 보정)
 'lateral circumflex femoral': '가쪽넙다리휘돌이', 'medial circumflex femoral': '안쪽넙다리휘돌이', 'anterior circumflex humeral': '앞위팔휘돌이',
 'posterior circumflex humeral': '뒤위팔휘돌이', 'circumflex scapular': '어깨휘돌이', 'anterior ulnar recurrent': '앞자쪽되돌이', 'posterior ulnar recurrent': '뒤자쪽되돌이',
 'radial recurrent': '노쪽되돌이', 'anterior tibial recurrent': '앞정강되돌이', 'superior ulnar collateral': '위자쪽곁', 'inferior ulnar collateral': '아래자쪽곁',
 'common palmar digital': '온손바닥쪽손가락', 'proper palmar digital': '고유손바닥쪽손가락', 'lateral proper palmar digital': '가쪽고유손바닥쪽손가락',
 'medial proper palmar digital': '안쪽고유손바닥쪽손가락', 'dorsal digital': '등쪽손발가락', 'plantar digital': '발바닥쪽발가락', 'common plantar digital': '온발바닥쪽발가락',
 'dorsal scapular': '등쪽어깨', 'great saphenous': '큰두렁', 'small saphenous': '작은두렁', 'median cubital': '팔오금중간', 'median antebrachial': '아래팔중간',
 'internal jugular': '속목', 'accessory hemiazygos': '덧반홀', 'anterior interventricular': '앞심실사이', 'posterior interventricular': '뒤심실사이',
 'dorsalis pedis': '발등', 'deep dorsal': '깊은등쪽', 'superficial dorsal': '얕은등쪽',
}
def _adj(s):
    if s in PHR: return PHR[s]
    if s in V: return V[s]
    out = []
    ws = s.split()
    i = 0
    while i < len(ws):
        two = ' '.join(ws[i:i+2])
        if two in PHR: out.append(PHR[two]); i += 2; continue
        if two in W: out.append(W[two]); i += 2; continue
        w = ws[i]
        if w in W: out.append(W[w])
        else: return None
        i += 1
    return ''.join(out)

def vessel_ko(b):
    """b: 좌우 제거된 소문자 이름 → 한글 또는 None"""
    if b in V: return V[b]
    m = re.match(r'set of (.+)$', b)
    if m:
        t = m.group(1).replace('arteries', 'artery').replace('veins', 'vein').replace('branches', 'branch').replace('intertransversarii', '')
        r = vessel_ko(t); return r and r + '들'
    m = re.match(r'hepatovenous segment (\w+)$', b)
    if m: return f'간정맥 구역 {m.group(1).upper()}'
    m = re.match(r'trunk of (.+)$', b)
    if m: r = vessel_ko(m.group(1)); return r and r + ' 줄기'
    m = re.match(r'(.+?) (branch|part|tributary|division|segment) of (.+)$', b)
    if m:
        a = _adj(m.group(1)) if m.group(1) else ''; r = vessel_ko(m.group(3))
        suf = {'branch': '가지', 'part': '부분', 'tributary': '지류', 'division': '분지', 'segment': '분절'}[m.group(2)]
        if a is None or r is None: return None
        return f'{r}의 {a}{suf}'
    m = re.match(r'(branch|tributary) of (.+?) to (.+)$', b)
    if m: r = vessel_ko(m.group(2)); return r and f'{r} 가지'
    m = re.match(r'(.+) (artery|arteries|vein|veins)$', b)
    if m:
        a = _adj(m.group(1));
        return a and a + ('동맥' if m.group(2).startswith('arter') else '정맥')
    m = re.match(r'(.+) (trunk|arch|sinus)$', b)
    if m: a = _adj(m.group(1)); return a and a + {'trunk': '줄기', 'arch': '활', 'sinus': '굴'}[m.group(2)]
    m = re.match(r'(.+) (artery|vein) of (thumb|index finger|middle finger|ring finger|little finger)$', b)
    if m:
        a = _adj(m.group(1)); f = {'thumb':'엄지','index finger':'집게손가락','middle finger':'가운데손가락','ring finger':'반지손가락','little finger':'새끼손가락'}[m.group(3)]
        return a and f'{f} {a}{"동맥" if m.group(2)=="artery" else "정맥"}'
    m = re.match(r'(artery|vein) of (.+)$', b)
    if m: a = _adj(m.group(2)); return a and a + ('동맥' if m.group(1) == 'artery' else '정맥')
    return None

VKEY = [  # (정규식, 설명키)
 (r'aorta', 'aorta'), (r'common carotid', 'carotid'), (r'internal carotid|cerebral artery|communicating artery|basilar|vertebral artery', 'willis'),
 (r'subclavian artery|axillary artery|brachial artery|radial artery$|ulnar artery$', 'armart'), (r'coronary|interventricular|cardiac vein|coronary sinus|marginal branch of coronary', 'coronary'),
 (r'celiac|splenic artery|hepatic artery|gastric artery|gastroduodenal', 'celiac'), (r'superior mesenteric artery|ileocolic artery|middle colic artery', 'sma'),
 (r'inferior mesenteric artery|sigmoid artery|superior rectal artery', 'ima'), (r'renal artery|renal vein', 'renalv'),
 (r'common iliac artery|external iliac artery|femoral artery$|popliteal artery|tibial artery', 'iliofemoral'), (r'internal iliac artery', 'iliofemoral'),
 (r'pulmonary', 'pulmonaryv'), (r'superior vena cava', 'svc'), (r'inferior vena cava', 'ivc'), (r'portal vein', 'portal'),
 (r'azygos', 'azygos'), (r'internal jugular', 'ijv'), (r'saphenous', 'saphenous'), (r'cephalic vein|basilic vein|median cubital', 'armveins'),
 (r'internal thoracic', 'intthoracic'),
]
def vessel_key(b):
    for rx, k in VKEY:
        if re.search(rx, b): return k
    return None
