"""해부 실습용 구획(부위) 분류
구조물 전체를 한 구획에 넣는 경우(뼈·장기)와, 여러 구획에 걸친 구조물(근육·혈관·신경·피부·식도·요관 등)을
삼각형 단위로 나누는 경우를 함께 처리한다.  좌표: +x 왼쪽, +y 위, +z 앞 (m)
"""
import re
import numpy as np

REGIONS = ['chestwall', 'abdwall', 'abdomen', 'thorax', 'pelvis', 'neck', 'head', 'brain', 'back', 'arm', 'leg']
RID = {r: i for i, r in enumerate(REGIONS)}

# 남성(BodyParts3D) 기준 수치, 여성(HuBMAP)은 보정값 사용
PM = dict(dy=0.0, dz=0.0, head0=1.50, head1=0.055, neck0=1.40, neck1=0.045, cm0=1.245, cm1=1.2, cav=1.20, cavp=1.16,
          brim_y=0.99, brim_z=-0.035, brim_k=1.32, leg_y=0.835, pub_x=0.021, pub_y=0.875, ing_k=0.95, glut_z=-0.02, glut_x=0.07, glut_y=1.03,
          armx=0.165, army=0.70, peri_x=0.035, peri_y=0.90, peri_lo=0.745, zback=-0.055, zback_lat=-0.07,
          brain_c=(0.0, 1.64, -0.01), brain_r=(0.074, 0.088, 0.085))
PF = dict(PM, dy=-0.045, dz=-0.06, brim_y=0.935, brim_z=-0.09, brim_k=1.09, leg_y=0.75, pub_x=0.02, pub_y=0.845, glut_y=0.96,
          armx=0.17, army=0.78, peri_x=0.035, peri_y=0.85, peri_lo=0.70, brain_c=(0.0, 1.59, -0.07), brain_r=(0.07, 0.085, 0.08))

def classify_points(C, P, wall):
    """C: (n,3) 점들 → 구획 id 배열. wall: 몸통벽 쪽 구조물인지"""
    x, y, z = C[:, 0], C[:, 1], C[:, 2]
    ax = np.abs(x); dy = P['dy']; dz = P['dz']; zz = z - dz
    out = np.full(len(C), -1)
    clip = lambda a: np.clip(a, 0, 1)
    y_head = P['head0'] + dy + P['head1'] * clip((0.02 - zz) / 0.1)
    y_neck = P['neck0'] + dy + P['neck1'] * clip(-zz / 0.08)
    bc = np.array(P['brain_c']); br = np.array(P['brain_r'])
    inbrain = (((C - bc) / br) ** 2).sum(1) < 1
    is_arm = (ax > P['armx']) & (y > P['army']) & (y < y_neck + 0.08)
    peri = (ax <= P['peri_x']) & (y < P['peri_y']) & (y > P['peri_lo'])
    ing = P['pub_y'] + (ax - P['pub_x']) * P['ing_k']
    is_leg = ~peri & ((y < P['leg_y']) | ((zz > -0.02) & (ax > P['peri_x']) & (y < ing)) |
                      ((zz < P['glut_z']) & (ax > P['glut_x']) & (y < P['glut_y'])))
    is_leg &= ~is_arm
    y_brim = P['brim_y'] - P['brim_k'] * (z - P['brim_z'])
    back = ((ax < 0.14) & (zz < P['zback'])) | ((ax >= 0.14) & (zz < P['zback_lat']))
    back &= (y > y_brim - 0.02) & (y < y_neck + 0.03)
    # 순서대로 결정
    o = out
    o[(y > y_head) & inbrain] = RID['brain']
    o[(o < 0) & (y > y_head)] = RID['head']
    o[(o < 0) & is_arm] = RID['arm']
    nb = (o < 0) & (y > y_neck) & (ax > 0.08)
    o[nb & (zz < -0.02)] = RID['back']
    o[nb & (zz >= -0.02)] = RID['chestwall'] if wall else RID['arm']
    o[(o < 0) & (y > y_neck)] = RID['neck']
    if not wall:
        o[(o < 0) & (ax > 0.115) & (y > 1.24 + dy) & (y < y_neck + 0.05)] = RID['arm']
    o[(o < 0) & is_leg] = RID['leg']
    o[(o < 0) & back] = RID['back']
    o[(o < 0) & (y < y_brim) & (~np.full(len(C), wall) | peri)] = RID['pelvis']
    o[(o < 0) & peri] = RID['pelvis']
    if wall:
        y_cm = P['cm0'] + dy - P['cm1'] * ax
        o[(o < 0) & (y >= y_cm)] = RID['chestwall']
        o[(o < 0)] = RID['abdwall']
    else:
        y_cav = np.where(zz > -0.02, P['cav'], P['cavp']) + dy
        o[(o < 0) & (y >= y_cav)] = RID['thorax']
        o[(o < 0)] = RID['abdomen']
    return o

# 몸통벽 쪽으로 보는 혈관·신경 이름
WALL_RX = r'intercostal|internal thoracic|musculophrenic|epigastric|thoracodorsal|lateral thoracic|thoraco-acromial|subcostal|lumbar (artery|vein)|circumflex iliac|iliohypogastric|ilioinguinal|cutaneous|skin|thoracoepigastric|superficial'
CAVITY_MUS = r'psoas|iliacus|quadratus lumborum|papillary|diaphragm|levator ani|coccygeus|iliococcygeus|pubococcygeus|puborectalis|anal sphincter|perineal'

def structure_region(sys, key, en, grp):
    """구조물 전체를 한 구획으로 지정. 걸쳐 있는 구조물이면 None"""
    e = en.lower(); k = key or ''
    if sys == 'skeletal':
        if grp == '머리뼈' or grp == '치아' or k in ('skull', 'mandible', 'tooth'):
            return 'neck' if k == 'hyoid' else 'head'
        if k == 'hyoid' or k == 'larynx': return 'neck'
        if k in ('C1', 'C2', 'C3', 'C4', 'C5', 'C6', 'C7') or k == 'disk' or re.match(r'[CTL]\d+$', k): return 'back'
        if k.startswith('rib') or k in ('costal', 'sternum'): return 'chestwall'
        if k in ('clavicle', 'scapula', 'humerus', 'radius', 'ulna', 'hand'): return 'arm'
        if k in ('hipbone', 'sacrum', 'coccyx'): return 'pelvis'
        if k in ('femur', 'patella', 'tibia', 'fibula', 'foot', 'meniscus'): return 'leg'
        if 'alar cartilage' in e: return 'head'
        return None
    if sys == 'nervous':
        return 'head' if k == 'eye' else 'brain'
    if sys == 'endocrine':
        return 'brain' if k in ('pituitary', 'pineal') else 'abdomen'
    if sys == 'cardio':
        return 'abdomen' if k == 'spleen' else 'thorax'
    if sys == 'respiratory':
        if k in ('lung_r', 'lung_l', 'bronchi'): return 'thorax'
        if 'concha' in e or 'nasal' in e: return 'head'
        if k == 'larynx' or ('cartilage' in e and 'bronch' not in e): return 'neck'
        if k == 'diaphragm': return 'thorax'
        return None   # 기관: 목·가슴에 걸침
    if sys == 'digestive':
        if k in ('tongue', 'salivary'): return 'head'
        if k == 'esophagus': return None
        if 'rectum' in e: return 'pelvis'
        return 'abdomen'
    if sys == 'urinary':
        if k in ('kidney',): return 'abdomen'
        if k in ('bladder', 'urethra'): return 'pelvis'
        return None   # 요관
    if sys == 'reproductive':
        return 'chestwall' if k == 'breast' else 'pelvis'
    return None

def is_wall(sys, key, en):
    e = en.lower()
    if sys == 'skin': return True
    if sys == 'muscular': return not re.search(CAVITY_MUS, e)
    if sys in ('arterial', 'venous', 'nerves'): return bool(re.search(WALL_RX, e)) or (key in ('intercostal',))
    return False

def split(sys, key, en, grp, P_, I, sex='m'):
    """→ (재정렬된 인덱스, segs=[[rid,start,count],...], 구획별 삼각형 중심 합/개수)"""
    P = PF if sex == 'f' else PM
    T = I.reshape(-1, 3)
    r = structure_region(sys, key, en, grp)
    if r is not None:
        rid = np.full(len(T), RID[r])
    else:
        C = P_[T].mean(1)
        rid = classify_points(C, P, is_wall(sys, key, en))
    order = np.argsort(rid, kind='stable')
    T2 = T[order]; rs = rid[order]
    segs = []; stats = {}
    C2 = P_[T2].mean(1)
    for g in np.unique(rs):
        idx = np.where(rs == g)[0]
        segs.append([int(g), int(idx[0] * 3), int(len(idx) * 3)])
        stats[int(g)] = (C2[idx].sum(0), len(idx), C2[idx].min(0), C2[idx].max(0))
    return T2.reshape(-1), segs, stats
