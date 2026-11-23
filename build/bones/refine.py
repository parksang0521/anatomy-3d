"""골학 핀 위치 보정 (data.json 후처리).

1) 오목·고랑·패임('deep' 규칙): 예전 방식은 '방향을 향한 면 중 가장 덜 튀어나온 점'이라
   넓은 구간에서는 반대쪽 면의 패인 곳을 잡는 경우가 있었다 (예: 종아리패임이 안쪽에 찍힘).
   → 바깥쪽 면 위에서 '주변 테두리보다 얼마나 들어갔는지(국소 오목 깊이)'가 가장 큰 점으로 다시 계산.
2) 둥근 관절머리: 맨 끝점(가장자리) 대신 구(球)를 맞춰 관절면 한가운데에 둔다.
3) 개별 오류 수정 (관절위결절, 왼쪽 어깨위패임 등).
4) 모든 핀(구멍 핀 제외)을 표면에 살짝 묻히게 해 '떠 있어' 보이지 않게 한다.

python3 refine.py  → /home/claude/anatomy-3d/bones/data.json 덮어씀
"""
import json, gzip, sys, os, numpy as np, trimesh
from scipy.spatial import cKDTree
sys.path.insert(0, os.path.dirname(__file__))
from rules import R as RULES, hand, foot

B_DIR = '/home/claude/anatomy-3d/bones/'
D = json.load(open(B_DIR + 'data.json'))
MS, LM = D['meshes'], D['lm']
_mc = {}


def mesh(i):
    if i in _mc: return _mc[i]
    c = MS[i]; ab = gzip.open(B_DIR + 'm/' + i + '.bin.gz').read()
    vc, ic = c['vc'], c['ic']
    q = np.frombuffer(ab, np.uint16, vc * 3, 0).reshape(-1, 3).astype(float)
    P = np.array(c['lo']) + q * np.array(c['sc'])
    I = np.frombuffer(ab, np.uint32 if c['i32'] else np.uint16, ic, vc * 6).reshape(-1, 3).astype(np.int64)
    _mc[i] = trimesh.Trimesh(P, I, process=True); return _mc[i]


def parse(spec):
    out = []; num = ''
    for ch in spec:
        if ch in '0123456789.': num += ch
        else: out.append((ch, float(num) if num else 1.0)); num = ''
    return out


class Bone:
    """auto.B 와 같은 좌표 규약: A=-y, S=+z, 오른쪽 뼈의 안쪽(M)=+x"""
    def __init__(s, ids, side='R'):
        s.ids = ids if isinstance(ids, list) else [ids]
        ms = [mesh(i) for i in s.ids]
        s.V = np.concatenate([m.vertices for m in ms]); s.N = np.concatenate([m.vertex_normals for m in ms])
        s.owner = np.concatenate([[i] * len(m.vertices) for i, m in zip(s.ids, ms)])
        mx = 1.0 if side != 'L' else -1.0
        s.D = {'M': np.array([mx, 0, 0]), 'L': np.array([-mx, 0, 0]), 'A': np.array([0, -1., 0]), 'P': np.array([0, 1., 0]), 'S': np.array([0, 0, 1.]), 'I': np.array([0, 0, -1.])}
        s.lo = s.V.min(0); s.hi = s.V.max(0); s.size = np.linalg.norm(s.hi - s.lo)
        n = (s.V - s.lo) / (s.hi - s.lo)
        s.m = n[:, 0] if mx > 0 else 1 - n[:, 0]; s.a = 1 - n[:, 1]; s.h = n[:, 2]

    def d(s, spec):
        v = sum(w * s.D[c] for c, w in parse(spec)); return v / np.linalg.norm(v)

    def mask(s, h=None, m=None, a=None, hm=None, own=None, **_):
        k = np.ones(len(s.V), bool) if own is None else (s.owner == own)
        if h is not None: k &= (s.h >= h[0]) & (s.h <= h[1])
        slab = k.copy() if hm is None else (s.h >= hm[0]) & (s.h <= hm[1])
        for arr, r in ((s.m, m), (s.a, a)):
            if r is not None:
                lo, hi = arr[slab].min(), arr[slab].max(); nn = (arr - lo) / (hi - lo + 1e-9)
                k &= (nn >= r[0]) & (nn <= r[1])
        return k

    def deep(s, spec, **r):
        """국소 오목 깊이가 가장 큰 바깥쪽 면의 점"""
        k = s.mask(**r); d = s.d(spec)
        face = k & ((s.N @ d) > 0.15)
        idx = np.where(face)[0]
        if len(idx) < 5: return None
        proj = s.V @ d
        # d에 수직인 평면으로 투영한 좌표
        u = np.cross(d, [0.31, 0.53, 0.79]); u /= np.linalg.norm(u); w = np.cross(d, u)
        Q = np.c_[s.V @ u, s.V @ w]
        outer = idx[proj[idx] >= np.quantile(proj[idx], 0.3)]
        rho = float(np.clip(0.05 * s.size, 4, 14))
        T = cKDTree(Q[idx])
        best, bd = None, -1
        for i in outer:
            nb = idx[T.query_ball_point(Q[i], rho)]
            if len(nb) < 6: continue
            rim = np.quantile(proj[nb], 0.9)
            dep = rim - proj[i]
            if dep > bd: bd, best = dep, i
        return best

    def face_center(s, spec, **r):
        """넓은 오목(엉덩뼈오목·절구 등): 방향을 향한 면의 한가운데"""
        k = s.mask(**r); d = s.d(spec)
        idx = np.where(k & ((s.N @ d) > 0.45))[0]
        if len(idx) < 5: return None
        u = np.cross(d, [0.31, 0.53, 0.79]); u /= np.linalg.norm(u); w = np.cross(d, u)
        Q = np.c_[s.V[idx] @ u, s.V[idx] @ w]; c = np.median(Q, 0)
        return idx[np.argmin(np.linalg.norm(Q - c, axis=1))]

    def ext(s, spec, **r):
        k = s.mask(**r); d = s.d(spec); idx = np.where(k)[0]
        return idx[np.argmax(s.V[idx] @ d)]

    def sphere_face(s, seed_spec, face_spec, rad_frac=0.09, **r):
        """관절머리: seed 방향 끝점 주변에 구를 맞추고, face 방향의 구면 위 점"""
        k = s.mask(**r); d0 = s.d(seed_spec); idx = np.where(k)[0]
        tip = s.V[idx[np.argmax(s.V[idx] @ d0)]]
        R0 = rad_frac * s.size
        sel = idx[np.linalg.norm(s.V[idx] - tip, axis=1) < 1.6 * R0]
        X = s.V[sel]
        A = np.c_[2 * X, np.ones(len(X))]; b = (X ** 2).sum(1)
        sol = np.linalg.lstsq(A, b, rcond=None)[0]; c = sol[:3]; rad = np.sqrt(sol[3] + c @ c)
        target = c + s.d(face_spec) * rad
        return int(np.argmin(np.linalg.norm(s.V - target, axis=1))), c, rad

    def pit(s, c, rad, face_spec, cone=0.75):
        """구면에서 face 방향 주변의 '움푹 들어간 곳' (넙다리뼈머리오목)"""
        d = s.d(face_spec); v = s.V - c; r = np.linalg.norm(v, axis=1); dirn = v / r[:, None]
        k = (dirn @ d > cone) & (r > rad * 0.6) & (r < rad * 1.15)
        idx = np.where(k)[0]
        if len(idx) < 5: return None
        return idx[np.argmin(r[idx])]


# ---- 항목 → 규칙 목록
def kind_of(iid):
    if iid == 'C1': return 'atlas'
    if iid == 'C2': return 'axis'
    if iid == 'C7': return 'c7'
    if iid[0] == 'C' and iid[1:].isdigit(): return 'cervical'
    if iid[0] == 'T' and iid[1:].isdigit(): return 'thoracic'
    if iid[0] == 'L' and iid[1:].isdigit(): return 'lumbar'
    if iid.startswith('rib'): return 'rib1' if iid == 'rib1' else 'rib'
    return iid


def rules_for(iid, side):
    k = kind_of(iid)
    if k == 'hand': return hand(side)
    if k == 'foot': return foot(side)
    return RULES.get(k)


moves = []
def setpt(key, mid, newp, why, side=None, newmid=None):
    """같은 key·mesh(·좌우) 핀 좌표 교체 — 골반 전체 등 다른 항목에 있는 같은 핀도 함께"""
    for it in D['items']:
        for v in it['var'].values():
            for p in v['pts']:
                if p[0] == key and p[4] == mid and (side is None or p[5] == side):
                    old = np.array(p[1:4]); p[1], p[2], p[3] = [round(float(x), 1) for x in newp]
                    if newmid: p[4] = newmid
                    moves.append((round(float(np.linalg.norm(old - newp)), 1), it['id'], key, mid, why))


WIDE = {'iliac_fossa', 'acetabulum', 'infraspinous_fossa', 'supraspinous_fossa', 'subscapular_fossa'}
done = set()
for it in D['items']:
    if it['id'] in ('skull', 'pelvis', 'spine'): continue
    for side, v in it['var'].items():
        rl = rules_for(it['id'], side or 'R')
        if not rl: continue
        bones = {}
        for rule in rl:
            k, kind, spec, reg = rule[0], rule[1], rule[2], rule[3]
            opt = rule[4] if len(rule) > 4 else {}
            if kind != 'deep': continue
            pins = [p for p in v['pts'] if p[0] == k]
            if not pins: continue
            sides = ['R', 'L'] if opt.get('bi') else [side or 'R']
            for sd in sides:
                if sd not in bones: bones[sd] = Bone(v['meshes'], sd)
                b = bones[sd]
                tag = (k, pins[0][4], sd if opt.get('bi') else '')
                if tag in done: continue
                i = b.face_center(spec, **reg) if k in WIDE else b.deep(spec, **reg)
                if i is None: continue
                setpt(k, pins[0][4], b.V[i], 'deep', side=(sd if opt.get('bi') else None), newmid=str(b.owner[i]))
                done.add(tag)

# ---- 관절머리 · 개별 수정
def side_items(iid):
    it = next(x for x in D['items'] if x['id'] == iid)
    for sd in ('R', 'L'):
        if sd in it['var']: yield sd, it['var'][sd]

for sd, v in side_items('femur'):
    b = Bone(v['meshes'], sd)
    i, c, rad = b.sphere_face('M2S1', 'M1S0.45A0.15', rad_frac=0.045, h=(0.85, 1))
    setpt('fem_head', v['meshes'][0], b.V[i], 'head-sphere')
    j = b.pit(c, rad, 'M1I0.35P0.15')
    if j is not None: setpt('fovea_capitis', v['meshes'][0], b.V[j], 'fovea-pit')
for sd, v in side_items('humerus'):
    b = Bone(v['meshes'], sd)
    i, c, rad = b.sphere_face('M1S1P0.4', 'M1S0.7P0.4', rad_frac=0.06, h=(0.85, 1))
    setpt('hum_head', v['meshes'][0], b.V[i], 'head-sphere')
for sd, v in side_items('scapula'):
    b = Bone(v['meshes'], sd)
    g = next(p for p in v['pts'] if p[0] == 'glenoid_cavity'); G = np.array(g[1:4])
    lat = b.d('L'); near = np.linalg.norm(b.V - G, axis=1) < 22
    near &= (b.V @ lat) > (G @ lat) - 7          # 관절오목 테두리 쪽 (부리돌기 뿌리 제외)
    near &= (b.V[:, 2] < G[2] + 25)
    idx = np.where(near)[0]; i = idx[np.argmax(b.V[idx, 2])]
    setpt('supraglenoid_tubercle', v['meshes'][0], b.V[i], 'above-glenoid')
    i = b.ext('L1I1', h=(0.55, 0.7), a=(0.25, 0.75))
    setpt('infraglenoid_tubercle', v['meshes'][0], b.V[i], 'below-glenoid')
for sd, v in side_items('hip'):
    b = Bone(v['meshes'], sd)
    sp = np.array(next(p for p in v['pts'] if p[0] == 'ischial_spine')[1:4])
    tb = np.array(next(p for p in v['pts'] if p[0] == 'ischial_tuberosity')[1:4])
    z0, z1 = tb[2] + 0.2 * (sp[2] - tb[2]), tb[2] + 0.8 * (sp[2] - tb[2])
    P = b.d('P'); xm = (sp[0] + tb[0]) / 2
    k = (b.V[:, 2] > z0) & (b.V[:, 2] < z1) & (np.abs(b.V[:, 0] - xm) < 22)
    idx = np.where(k)[0]; zb = np.round((b.V[idx, 2] - z0) / 2.5).astype(int)
    prof = {}
    for i, z in zip(idx, zb):
        if z not in prof or b.V[i] @ P > b.V[prof[z]] @ P: prof[z] = i
    i = min(prof.values(), key=lambda i: b.V[i] @ P)   # 뒤모서리 윤곽에서 가장 오목한 곳
    setpt('lesser_sciatic_notch', v['meshes'][0], b.V[i], 'notch-profile')

# 절구: 넙다리뼈머리 중심에서 가장 가까운 볼기뼈 표면 (절구오목 바닥)
heads = {}
for sd, v in side_items('femur'):
    b = Bone(v['meshes'], sd); _, c, _ = b.sphere_face('M2S1', 'M1', rad_frac=0.045, h=(0.85, 1)); heads[sd] = c
for sd, v in side_items('hip'):
    m = mesh(v['meshes'][0]); q, _, _ = m.nearest.on_surface([heads[sd]])
    setpt('acetabulum', v['meshes'][0], np.array(q[0]), 'femoral-head')

# 목말받침돌기: 발꿈치뼈 전체에서 가장 안쪽 점(=발꿈치융기 안쪽)이 잡혔음 → 앞·위쪽 절반에서 안쪽 선반
for sd, v in side_items('foot'):
    S = 'right' if sd == 'R' else 'left'; cal = f'{S}_calcaneus'
    b = Bone([cal], sd); i = b.ext('M', a=(0.45, 0.8), h=(0.5, 1))
    setpt('sustentaculum', cal, b.V[i], 'sustentaculum')

# 머리뼈: 브레그마는 머리덮개 바깥 점 — '바닥 속면' 보기 전용 표시(i) 해제
for it in D['items']:
    for v in it['var'].values():
        for p in v['pts']:
            if p[0] == 'bregma' and p[6] == 'i': p[6] = ''

# ---- 모든 핀을 표면에 살짝 묻기 (구멍·관 핀은 구멍 한가운데라 제외)
emb = 0
for it in D['items']:
    for v in it['var'].values():
        for p in v['pts']:
            L = LM.get(p[0], {})
            if L.get('t') == 'f' or p[4] not in MS: continue
            m = mesh(p[4]); q, dd, tri = m.nearest.on_surface([p[1:4]])
            if dd[0] > 6: continue
            n = m.face_normals[tri[0]]; np_ = np.array(q[0]) - n * 0.35
            p[1], p[2], p[3] = [round(float(x), 1) for x in np_]; emb += 1

moves.sort(reverse=True)
print(f'moved {len(moves)} pins, embedded {emb}')
for mv in moves[:60]: print('  ', mv)
s = json.dumps(D, ensure_ascii=False, separators=(',', ':'))
open(B_DIR + 'data.json', 'w').write(s)
