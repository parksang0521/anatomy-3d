"""HuBMAP HRA 여성 기준 장기(Visible Human Female) → 웹용 바이너리 + manifest_f.json"""
import re, json, gzip, glob, os, sys
import numpy as np, trimesh, fast_simplification
sys.path.insert(0, '/home/claude/data')
from names_ko import vessel_ko, vessel_key, W
import regions as RG

OUT = '/home/claude/anatomy-3d/models'
D = '/home/claude/data/ccf/'
FILES = {
 'v1.3/models/3d-vh-f-skin.glb': 'skin', 'v1.3/models/VH_F_Pelvis.glb': 'skeletal', 'v1.3/models/VH_F_Knee_L.glb': 'skeletal', 'v1.3/models/VH_F_Knee_R.glb': 'skeletal',
 'v1.3/models/VH_F_Heart.glb': 'cardio', 'v1.3/models/VH_F_Spleen.glb': 'cardio', 'v1.3/models/VH_F_Thymus.glb': 'cardio',
 'v1.4/models/3d-vh-f-lung.glb': 'respiratory', 'v1.4/models/3d-vh-f-trachea.glb': 'respiratory', 'v1.4/models/3d-vh-f-main-bronchus.glb': 'respiratory', 'v1.4/models/3d-vh-f-larynx.glb': 'respiratory',
 'v1.3/models/VH_F_Liver.glb': 'digestive', 'v2.0/models/3d-vh-f-pancreas.glb': 'digestive', 'v1.3/models/VH_F_Small_Intestine.glb': 'digestive', 'v1.3/models/SBU_F_Intestine_Large.glb': 'digestive',
 'v1.3/models/VH_F_Kidney_L.glb': 'urinary', 'v1.3/models/VH_F_Kidney_R.glb': 'urinary', 'v1.3/models/VH_F_Ureter_L.glb': 'urinary', 'v1.3/models/VH_F_Ureter_R.glb': 'urinary', 'v1.3/models/VH_F_Urinary_Bladder.glb': 'urinary',
 'v1.3/models/VH_F_Uterus.glb': 'reproductive', 'v1.3/models/VH_F_Ovary_L.glb': 'reproductive', 'v1.3/models/VH_F_Ovary_R.glb': 'reproductive',
 'v1.3/models/VH_F_Fallopian_Tube_L.glb': 'reproductive', 'v1.3/models/VH_F_Fallopian_Tube_R.glb': 'reproductive',
 'v1.3/models/3d-vh-f-mammary-gland-l.glb': 'reproductive', 'v1.3/models/3d-vh-f-mammary-gland-r.glb': 'reproductive',
 'v1.3/models/VH_F_Spinal_Cord.glb': 'nerves', 'v1.4/models/3d-vh-f-blood-vasculature.glb': 'vessels',
}
SKIP = r'impression|spongy|enthesis|perichondular|condyle|trochlear_groove|intercondylar|distal_most|segment1|_segment$|anterolateral_segment|superomedial|inferomedial|anterosuperior|posteroinferior|posterosuperior|anteroinferior|quadrate_lobe|caudate_lobe|bare_area|diaphragmatic_surface_of_liver|ostium|internal_cervical_os|external_cervical_os|areolar_tubercles|ileocecal_valve|carina'
SIDEK = {'L': '왼쪽 ', 'R': '오른쪽 '}
ORD = {'first': 1, 'second': 2, 'third': 3, 'fourth': 4, 'fifth': 5, 'sixth': 6, 'seventh': 7, 'eigth': 8, 'eighth': 8, 'ninth': 9, 'tenth': 10, 'eleventh': 11, 'twelfth': 12}

def side_of(n):
    m = re.search(r'_(L|R)(_[a-z])?$', n) or re.search(r'_(L|R)_', n)
    if m: return m.group(1)
    if re.search(r'(^|_)left_', n): return 'L'
    if re.search(r'(^|_)right_', n): return 'R'
    return None

def name(node, sysn):
    """→ (구조물 키(병합용 영문), ko, old, key, sys, grp) 또는 None"""
    n = node.replace('VH_F_', '')
    if re.search(SKIP, n): return None
    s = side_of(n); sk = SIDEK.get(s, ''); sfx = f' ({s})' if s else ''
    base = re.sub(r'_(L|R)(_[a-z])?$', '', n); base = re.sub(r'_(L|R)_', '_', base)
    base = re.sub(r'^(left|right)_', '', base).replace('_of_left_', '_of_').replace('_of_right_', '_of_')
    en = base.replace('_', ' ')
    if sysn == 'skin': return ('Skin', '피부', '', None, 'skin', None)
    if sysn == 'skeletal':
        m = re.match(r'(ilium|ischium|pubis)_compact_bone', base)
        if m: ko = {'ilium': '엉덩뼈', 'ischium': '궁둥뼈', 'pubis': '두덩뼈'}[m.group(1)]; return (f'{m.group(1)}{sfx}', sk + ko, {'ilium': '장골', 'ischium': '좌골', 'pubis': '치골'}[m.group(1)], 'hipbone', 'skeletal', '골반')
        D_ = {'sacrum': ('엉치뼈', '천골', 'sacrum', '골반'), 'coccyx': ('꼬리뼈', '미골', 'coccyx', '골반'), 'femur': ('넙다리뼈 (아래부분)', '대퇴골', 'femur', '무릎'),
              'tibia': ('정강뼈 (위부분)', '경골', 'tibia', '무릎'), 'fibula': ('종아리뼈 (위부분)', '비골', 'fibula', '무릎'), 'patella': ('무릎뼈', '슬개골', 'patella', '무릎'),
              'meniscus': ('반달연골', '반월상연골', 'meniscus', '무릎'), 'articular_cartilage_of_knee': ('무릎 관절연골', '관절연골', 'meniscus', '무릎')}
        if base in D_: ko, old, key, grp = D_[base]; return (f'{base}{sfx}', sk + ko, old, key, 'skeletal', grp)
        return None
    if sysn == 'cardio':
        H = {'interventricular_septum': '심실사이막', 'left_cardiac_atrium': '왼심방', 'right_cardiac_atrium': '오른심방', 'left_ventricle': '왼심실', 'right_ventricle': '오른심실',
             'aortic_valve': '대동맥판', 'pulmonary_valve': '폐동맥판', 'mitral_valve': '승모판', 'tricuspid_valve': '삼첨판'}
        if n in H: return (n, H[n], '', 'valves' if 'valve' in n else 'heart', 'cardio', '심장')
        if n.startswith('papillary'): return ('papillary', '꼭지근', '유두근', 'heartmus', 'cardio', '심장')
        if 'spleen' in n: return ('spleen', '지라', '비장', 'spleen', 'cardio', '림프기관')
        if 'thymus' in n: return (f'thymus{sfx}', sk + '가슴샘엽', '흉선', 'thymus', 'cardio', '림프기관')
    if sysn == 'respiratory':
        if 'cartilage_of_tertiary' in n or 'cartilage_of_lobar' in n or 'cartilage_of_main' in n: return ('bronchial cartilage' + sfx, sk + '기관지 연골', '', 'bronchi', 'respiratory', '기관지')
        m = re.match(r'(lingula_)?(.+?)_bronchopulmonary_segm', base)
        SEG = {'apical': '꼭대기', 'posterior': '뒤', 'anterior': '앞', 'superior': '위', 'lateral': '가쪽', 'medial': '안쪽', 'anterior_basal': '앞바닥',
               'lateral_basal': '가쪽바닥', 'posterior_basal': '뒤바닥', 'medial_basal': '안쪽바닥', 'inferior': '아래'}
        if m:
            t = m.group(2); lr = '왼' if (n.startswith('left') or 'lingula' in n) else '오른'
            nm = ('혀' + SEG.get(t, t)) if m.group(1) else SEG.get(t, t)
            if m.group(1): nm = ('위혀' if t == 'superior' else '아래혀')
            return (n, f'{lr}허파 {nm}구역', '폐구역', 'lung_l' if lr == '왼' else 'lung_r', 'respiratory', '허파구역')
        if n.startswith('hilum'): return ('hilum' + ('_L' if n.endswith('L') else '_R'), ('왼' if n.endswith('L') else '오른') + '허파문', '폐문', 'lung_l' if n.endswith('L') else 'lung_r', 'respiratory', '허파구역')
        m = re.match(r'(left|right)_(.+?)_(lobar_)?bronch(us|i)$', n)
        if m:
            t = m.group(2); lr = '왼' if m.group(1) == 'left' else '오른'
            if m.group(3): return (n, f'{lr} {dict(superior="위", inferior="아래", middle="중간").get(t, t)}엽기관지', '엽기관지', 'bronchi', 'respiratory', '기관지')
            t2 = t.replace('lingula_', ''); nm = SEG.get(t2, t2)
            if 'lingula' in t: nm = '위혀' if 'superior' in t else '아래혀'
            return (n, f'{lr} {nm}구역기관지', '구역기관지', 'bronchi', 'respiratory', '기관지')
        if n in ('right_main_bronchus', 'left_main_bronchus'): return (n, ('오른' if 'right' in n else '왼') + '주기관지', '주기관지', 'bronchi', 'respiratory', '기관지')
        if n in ('trachea', 'tracheal_cartilage'): return ('trachea', '기관', '기관', 'trachea', 'respiratory', None)
        L = {'arytenoid_cartilage': ('모뿔연골', '피열연골'), 'epiglotic_cartilage': ('후두덮개연골', '후두개연골'), 'cricoid_cartilage': ('반지연골', '윤상연골'),
             'thyroid_cartilage': ('방패연골', '갑상연골'), 'corniculate_cartilage': ('잔뿔연골', '소각연골')}
        if base in L: return (base + sfx, sk + L[base][0], L[base][1], 'larynx', 'respiratory', '후두')
    if sysn == 'digestive':
        G = {'capsule_of_the_liver': ('간', '간', 'liver', '간·이자'), 'porta_hepatis': ('간문', '간문', 'liver', '간·이자'), 'falciform_ligament': ('낫인대', '겸상인대', 'liver', '간·이자'),
             'round_ligament_of_liver': ('간원인대', '간원삭', 'liver', '간·이자'), 'coronary_ligament_of_liver': ('간관상인대', '관상인대', 'liver', '간·이자'),
             'triangular_ligament_of_liver': ('세모인대', '삼각인대', 'liver', '간·이자'), 'ligamentum_venosum': ('정맥관인대', '정맥관삭', 'liver', '간·이자'),
             'hepataduodenal_ligament': ('간샘창자인대', '간십이지장인대', 'liver', '간·이자'),
             'tail_of_pancreas': ('이자꼬리', '췌장꼬리', 'pancreas', '간·이자'), 'body_of_pancreas': ('이자몸통', '췌장체부', 'pancreas', '간·이자'), 'ucinate_process1': ('갈고리돌기', '구상돌기', 'pancreas', '간·이자'),
             'head_of_pancreas': ('이자머리', '췌장두부', 'pancreas', '간·이자'), 'neck_of_pancreas': ('이자목', '췌장경부', 'pancreas', '간·이자'),
             'duodenum_superior': ('샘창자 위부분', '십이지장 1부', 'smallint', '작은창자'), 'duodenal_ampulla': ('샘창자팽대', '십이지장구', 'smallint', '작은창자'),
             'duodenum_descending': ('샘창자 내림부분', '십이지장 2부', 'smallint', '작은창자'), 'sphincter_of_heptopancreatic_ampulla': ('간이자팽대조임근 (Oddi)', '오디괄약근', 'biliary', '작은창자'),
             'duodenum_horizontal': ('샘창자 수평부분', '십이지장 3부', 'smallint', '작은창자'), 'duodenum_ascending': ('샘창자 오름부분', '십이지장 4부', 'smallint', '작은창자'),
             'jejenum': ('빈창자', '공장', 'smallint', '작은창자'), 'ileum': ('돌창자', '회장', 'smallint', '작은창자'), 'ileum_terminal': ('돌창자 끝부분', '말단회장', 'smallint', '작은창자'),
             'hepatic_flexure_of_colon': ('오른잘록창자굽이', '간만곡', 'largeint', '큰창자'), 'transverse_colon': ('가로잘록창자', '횡행결장', 'largeint', '큰창자'),
             'ascending_colon': ('오름잘록창자', '상행결장', 'largeint', '큰창자'), 'vermiform_appendix': ('막창자꼬리', '충수', 'appendix', '큰창자'),
             'descending_colon': ('내림잘록창자', '하행결장', 'largeint', '큰창자'), 'caecum': ('막창자', '맹장', 'largeint', '큰창자'), 'rectum': ('곧창자', '직장', 'largeint', '큰창자'),
             'sigmoid_colon': ('구불잘록창자', 'S상결장', 'largeint', '큰창자'), 'splenic_flexure_of_colon': ('왼잘록창자굽이', '비만곡', 'largeint', '큰창자')}
        if n in G: ko, old, key, grp = G[n]; return (n, ko, old, key, 'digestive', grp)
    if sysn == 'urinary':
        if 'kidney_capsule' in n: return ('kidney' + sfx, sk + '콩팥 (피막)', '신장', 'kidney', 'urinary', '콩팥')
        if 'outer_cortex' in n: return ('cortex' + sfx, sk + '콩팥겉질', '신피질', 'kidney', 'urinary', '콩팥')
        if 'renal_column' in n: return ('column' + sfx, sk + '콩팥기둥', '신주', 'kidney', 'urinary', '콩팥')
        if 'renal_pyramid' in n: return ('pyramid' + sfx, sk + '콩팥피라미드', '신추체', 'kidney', 'urinary', '콩팥')
        if 'renal_papilla' in n: return ('papilla' + sfx, sk + '콩팥유두', '신유두', 'kidney', 'urinary', '콩팥')
        if 'minor_calyx' in n: return ('minor calyx' + sfx, sk + '작은콩팥잔', '소신배', 'kidney', 'urinary', '콩팥')
        if 'major_calyx' in n: return ('major calyx' + sfx, sk + '큰콩팥잔', '대신배', 'kidney', 'urinary', '콩팥')
        if 'renal_pelvis' in n: return ('pelvis' + sfx, sk + '콩팥깔때기', '신우', 'kidney', 'urinary', '콩팥')
        if 'hilum_of_kidney' in n: return ('hilum' + sfx, sk + '콩팥문', '신문', 'kidney', 'urinary', '콩팥')
        if n in ('left_ureter', 'right_ureter'): return (n, ('왼쪽 ' if 'left' in n else '오른쪽 ') + '요관', '요관', 'ureter', 'urinary', None)
        B = {'fundus_of_urinary_bladder_dome': '방광 꼭대기', 'fundus_of_urinary_bladder_base': '방광 바닥', 'urinary_bladder_neck_smooth_muscle': '방광목',
             'trigone_of_urinary_bladder': '방광삼각', 'ureteral_orifice': '요관구멍'}
        if base in B: return (base + sfx, sk + B[base], '방광', 'bladder', 'urinary', '방광')
    if sysn == 'reproductive':
        U = {'body_of_uterus': ('자궁몸통', '자궁체부'), 'fundus_of_uterus': ('자궁바닥', '자궁저부'), 'cornua': ('자궁뿔', '자궁각'), 'lower_uterine_segment': ('자궁 아래분절', '자궁하절'),
             'posterior_wall_of_uterus': ('자궁 뒤벽', '자궁후벽'), 'anterior_wall_of_uterus': ('자궁 앞벽', '자궁전벽'), 'cervix': ('자궁목', '자궁경부')}
        if n in U: return (n, U[n][0], U[n][1], 'cervix' if n == 'cervix' else 'uterus', 'reproductive', '자궁')
        if n in ('left_ovary', 'right_ovary'): return (n, ('왼쪽 ' if 'left' in n else '오른쪽 ') + '난소', '난소', 'ovary', 'reproductive', '난소·자궁관')
        T = {'ampulla_of_uterine_tube': ('자궁관팽대', '난관팽대부'), 'isthmus_of_fallopian_tube': ('자궁관잘록', '난관협부'), 'fibria_of_uterine_tube': ('자궁관술', '난관채'),
             'uterine_tube_infundibulum': ('자궁관깔때기', '난관누두')}
        if base in T: return (base + sfx, sk + T[base][0], T[base][1], 'uterinetube', 'reproductive', '난소·자궁관')
        M = {'fat': ('유방 지방조직', '유방 지방'), 'nipple': ('젖꼭지', '유두'), 'areola': ('젖꽃판', '유륜'), 'mammary_lobes': ('젖샘엽', '유선엽'),
             'main_lactiferous_ducts': ('젖샘관', '유관'), 'main_lactiferous_sinuses': ('젖샘관팽대', '유관동'), 'suspensory_ligaments': ('유방걸이인대 (Cooper)', '쿠퍼인대')}
        if base in M: return (base + sfx, sk + M[base][0], M[base][1], 'breast', 'reproductive', '유방')
    if sysn == 'nerves':
        m = re.match(r'(C\d)_segment', n)
        if m: return (n, f'척수 {m.group(1)} 분절', '척수분절', 'spinalcord', 'nerves', '척수')
        m = re.match(r'(\w+?)_(thoracic|lumbar|sacral)_spinal_cord_segment', n)
        if m: return (n, f"척수 {dict(thoracic='T', lumbar='L', sacral='S')[m.group(2)]}{ORD[m.group(1)]} 분절", '척수분절', 'spinalcord', 'nerves', '척수')
    if sysn == 'vessels':
        t = en.lower()
        t = re.sub(r' (a|b|c)$', '', t).replace('opthalmic', 'ophthalmic').replace('aortic arch', 'arch of aorta')
        m = re.match(r'pulmonary vein (inf|sup)$', t)
        if m: t = ('inferior' if m.group(1) == 'inf' else 'superior') + ' pulmonary vein'
        t = re.sub(r'\b(left|right) ', '', t).strip()
        EX = {'uterine artery': '자궁동맥', 'uterine vein': '자궁정맥', 'cystic artery': '쓸개동맥', 'cystic vein': '쓸개정맥', 'central retinal artery': '망막중심동맥',
              'central retinal vein': '망막중심정맥', 'long posterior ciliary artery': '긴뒤섬모체동맥', 'marginal artery of drummond': '잘록창자가장자리동맥 (Drummond)',
              'marginal branch': '심장동맥 모서리가지', 'middle hepatic artery branch of hepatic artery': '중간간동맥', 'oblique vein of atrium': '왼심방빗정맥',
              'posterior ventricular branch': '뒤심실가지', 'branch of portal vein': '문맥가지', 'ovarian artery': '난소동맥', 'ovarian vein': '난소정맥'}
        ko = EX.get(t) or vessel_ko(t) or vessel_ko(t + ' artery')
        if not ko: print('  ? vessel', t); ko = t
        isv = bool(re.search(r'vein|vena|sinus', t))
        key = 'uterineart' if t.startswith('uterine') else vessel_key(t)
        return (t + sfx, sk + ko, '', key, 'venous' if isv else 'arterial', None)
    print('  ? unmapped', sysn, n)
    return None

structs = {}
def put(key, meta, V, F):
    st = structs.setdefault(key, dict(meta=meta, P=[], I=[], n=0))
    st['I'].append(F.reshape(-1) + st['n']); st['P'].append(V); st['n'] += len(V)

YOFF = None
for f, sysn in FILES.items():
    sc = trimesh.load(D + f, force='scene')
    for node in sc.graph.nodes_geometry:
        T, gname = sc.graph[node]
        g = sc.geometry[gname]
        if not hasattr(g, 'faces') or len(g.faces) == 0: continue
        r = name(gname, sysn)
        if not r: continue
        key, ko, old, k, sy, grp = r
        m = g.copy(); m.apply_transform(T)
        V = np.asarray(m.vertices, float); F = np.asarray(m.faces, np.int64)
        # 경량화
        tgt = {'skin': 0.9, 'reproductive': 0.8, 'urinary': 0.75, 'respiratory': 0.7}.get(sy, 0.55)
        if 'fat' in gname: tgt = 0.97
        if 'cartilage_of_tertiary' in gname or 'cartilage_of_lobar' in gname or 'cartilage_of_main' in gname or 'tracheal_cartilage' in gname: tgt = 0.8
        if len(F) > 3000:
            v2, f2 = fast_simplification.simplify(V.astype(np.float32), F.astype(np.int32), target_reduction=tgt)
            V, F = v2.astype(float), f2.astype(np.int64)
        put(f'{sy}:{key}', dict(sys=sy, ko=ko, old=old, key=k, grp=grp, en=key), V, F)

allp = np.concatenate([np.concatenate(s['P']) for s in structs.values()])
yoff = -allp[:, 1].min()
for s in structs.values(): s['P'] = [p + np.array([0, yoff, 0]) for p in s['P']]
allp[:, 1] += yoff
lo = allp.min(0) - 0.001; hi = allp.max(0) + 0.001; sc = (hi - lo) / 65535
RS = {}
files = {}; manifest = []; tri = {}
def pretty(en):
    e = re.sub(r'\s*\((L|R)\)$', lambda m: '', en)
    side = re.search(r'\((L|R)\)$', en)
    e = e.replace('_', ' ')
    return (('Left ' if side and side.group(1) == 'L' else 'Right ' if side else '') + e).strip().capitalize() if not side else (('Left ' if side.group(1) == 'L' else 'Right ') + e)
for i, (k, st) in enumerate(sorted(structs.items(), key=lambda kv: (kv[1]['meta']['sys'], kv[0]))):
    m = st['meta']; P = np.concatenate(st['P']); I = np.concatenate(st['I'])
    I, segs, rst = RG.split(m['sys'], m['key'], m['en'], m['grp'], P, I, 'f')
    for g, (sm, n, mn, mx) in rst.items():
        a_ = RS.setdefault(g, [np.zeros(3), 0, np.full(3, 9.0), np.full(3, -9.0)]); a_[0] += sm; a_[1] += n; a_[2] = np.minimum(a_[2], mn); a_[3] = np.maximum(a_[3], mx)
    qp = np.round((P - lo) / sc).astype('<u2'); big = len(P) > 65535
    fsys = 'f_' + m['sys']; b = files.setdefault(fsys, bytearray())
    po = len(b); b += qp.tobytes()
    while len(b) % 4: b += b'\0'
    io = len(b); b += I.astype('<u4' if big else '<u2').tobytes()
    while len(b) % 4: b += b'\0'
    c = ((P.min(0) + P.max(0)) / 2).round(4).tolist(); r = float(np.linalg.norm(P.max(0) - P.min(0)) / 2)
    tri[m['sys']] = tri.get(m['sys'], 0) + len(I) // 3
    manifest.append(dict(id=f'f{i}', en='Female ' + pretty(m['en']), ko=m['ko'], old=m['old'], key=m['key'], sys=m['sys'], grp=m['grp'],
                         f=fsys, po=po, vc=len(P), io=io, ic=len(I), i32=big, c=c, r=round(r, 4), sg=segs))
sizes = {}
for s, b in files.items():
    gz = gzip.compress(bytes(b), 9); open(f'{OUT}/{s}.bin.gz', 'wb').write(gz); sizes[s] = len(gz)
REG = {RG.REGIONS[g]: dict(c=(v[0] / v[1]).round(4).tolist(), lo=v[2].round(4).tolist(), hi=v[3].round(4).tolist()) for g, v in RS.items()}
json.dump(dict(lo=lo.round(6).tolist(), sc=sc.tolist(), files=sizes, parts=manifest, regions=REG, regionNames=RG.REGIONS, sex='female',
               source='HuBMAP HRA 3D Reference Object Library (Visible Human Female), CC BY 4.0'),
          open(f'{OUT}/manifest_f.json', 'w'), ensure_ascii=False, separators=(',', ':'))
print('structures', len(manifest)); print('tris', tri); print('gz', sizes, sum(sizes.values()) / 1e6, 'MB')
