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

# ---- 갈비뼈: 상자 기준 규칙 대신 갈비뼈 곡선을 따라 척추끝에서 잰 거리로 배치
def rib_frame(m):
    V = m.vertices; c0 = V.mean(0)
    _, _, vt = np.linalg.svd(V - c0, full_matrices=False); e1, e2 = vt[0], vt[1]
    Q = np.c_[(V - c0) @ e1, (V - c0) @ e2]
    A = np.c_[2 * Q, np.ones(len(Q))]; sol = np.linalg.lstsq(A, (Q ** 2).sum(1), rcond=None)[0]; cc = sol[:2]
    th = np.unwrap(np.sort(np.arctan2(Q[:, 1] - cc[1], Q[:, 0] - cc[0])))
    ang = np.arctan2(Q[:, 1] - cc[1], Q[:, 0] - cc[0])
    # 각도 간격이 가장 큰 곳을 잘라 연속 구간으로
    srt = np.sort(ang); gaps = np.diff(np.r_[srt, srt[0] + 2 * np.pi]); cut = srt[(np.argmax(gaps) + 1) % len(srt)]
    t = (ang - cut) % (2 * np.pi)
    nb = 80; edges = np.linspace(t.min(), t.max(), nb + 1); bi = np.clip(np.searchsorted(edges, t) - 1, 0, nb - 1)
    C = np.array([V[bi == k].mean(0) if np.any(bi == k) else np.nan * np.ones(3) for k in range(nb)])
    ok = ~np.isnan(C[:, 0]); C = C[ok]; keep = np.where(ok)[0]
    s_ = np.r_[0, np.cumsum(np.linalg.norm(np.diff(C, axis=0), axis=1))]
    sv = np.interp(bi, keep, s_)   # 각 꼭짓점의 곡선거리
    # 척추끝 = 정중선(x=0)에 가깝고 뒤쪽(+y)인 끝
    e0, e1_ = C[0], C[-1]
    score = lambda e: -abs(e[0]) + e[1]
    if score(e1_) > score(e0): sv = s_[-1] - sv; C = C[::-1]
    return sv, s_[-1], C, cc, e1, e2, c0

for it in D['items']:
    if not it['id'].startswith('rib'): continue
    n = int(it['id'][3:])
    for sd, v in it['var'].items():
        mid = v['meshes'][0]; m = mesh(mid); V = m.vertices
        sv, L, C, cc, e1, e2, c0 = rib_frame(m)
        tipv = V[np.argmin(sv)]; tipdir = C[0] - C[min(4, len(C) - 1)]; tipdir /= np.linalg.norm(tipdir)
        w = sv < 6; head = V[w][np.argmax(V[w] @ tipdir)]
        setpt('rib_head', mid, head, 'rib-head')
        w = sv > L - 6; tipdir2 = C[-1] - C[max(-5, -len(C))]; tipdir2 /= np.linalg.norm(tipdir2)
        setpt('rib_sternal_end', mid, V[w][np.argmax(V[w] @ tipdir2)], 'rib-sternal')
        P_ = np.array([0, 1.0, 0])
        if n <= 10 and n != 1:
            w = (sv > 17) & (sv < 23); setpt('rib_neck', mid, V[w][np.argmax(V[w] @ (P_ + np.array([0, 0, 0.6])))], 'rib-neck')
            w = (sv > 30) & (sv < 40); setpt('rib_tubercle', mid, V[w][np.argmax(V[w] @ (P_ + np.array([0, 0, -0.3])))], 'rib-tubercle')
        if 'costal_groove' in [p[0] for p in v['pts']]:
            w = (sv > 0.3 * L) & (sv < 0.45 * L)
            # 곡률중심 쪽(안쪽) 아래모서리
            Q = np.c_[(V - c0) @ e1, (V - c0) @ e2]; rad = np.linalg.norm(Q - cc, axis=1)
            Ww = np.where(w)[0]; inner = Ww[rad[Ww] < np.median(rad[Ww])]
            g = inner[np.argmin(V[inner, 2])]
            setpt('costal_groove', mid, V[g] + np.array([0, 0, 1.5]), 'rib-groove')
        # 뜬갈비뼈: 없는 구조 핀 제거
        drop = {11: {'rib_tubercle', 'rib_neck'}, 12: {'rib_tubercle', 'rib_neck', 'rib_angle', 'costal_groove'}}.get(n, set())
        v['pts'] = [p for p in v['pts'] if p[0] not in drop]

# ---- 척추뼈: 척주관(척추뼈구멍) 기준으로 광선을 쏴서 실제 구조 위에 배치
def first_hit(m, o, d):
    loc, ri, ti = m.ray.intersects_location([o], [d], multiple_hits=True)
    if not len(loc): return None
    dd = (loc - o) @ np.asarray(d, float)
    k = dd > 0.3
    return loc[k][np.argmin(dd[k])] if np.any(k) else None

def vert_fix(it):
    iid = it['id']; v = it['var']['']; mid = v['meshes'][0]; m = mesh(mid); V = m.vertices
    pts = v['pts']
    F = np.array(next(p for p in pts if p[0] == 'vb_foramen')[1:4])
    near = V[np.abs(V[:, 2] - F[2]) < 3]
    dxy = np.linalg.norm(near[:, :2] - F[:2], axis=1); rc = float(np.percentile(dxy, 3))
    hA = first_hit(m, F, [0, -1, 0]); hR = first_hit(m, F, [-1, 0, 0]); hL = first_hit(m, F, [1, 0, 0])
    wv = V[(np.abs(V[:, 0] - F[0]) < 4) & (np.abs(V[:, 2] - F[2]) < 6) & (V[:, 1] < F[1] - 1)]
    if len(wv): rc = float(F[1] - wv[:, 1].max())
    if hR is not None and hL is not None: rcx = float((hL[0] - hR[0]) / 2)
    else:
        rx_ = near[np.abs(near[:, 1] - F[1]) < 2.5]; rcx = float(np.min(np.abs(rx_[:, 0] - F[0]))) if len(rx_) else rc
    ywall = F[1] - rc
    cv = V[(np.abs(np.abs(V[:, 0] - F[0]) - 0.85 * rcx) < 0.2 * rcx) & (np.abs(V[:, 2] - F[2]) < 6) & (V[:, 1] < F[1])]
    ywall_c = float(cv[:, 1].max()) if len(cv) else ywall
    body = V[(V[:, 1] < ywall - 1) & (np.abs(V[:, 0] - F[0]) < 2 * rcx)]
    zt, zb = np.percentile(body[:, 2], 99), np.percentile(body[:, 2], 1)
    body = None
    kind = iid[0]; n = int(iid[1:])
    def put(key, side, P_, why):
        if P_ is None: return
        for p in pts:
            if p[0] == key and p[5] == side:
                moves.append((round(float(np.linalg.norm(np.array(p[1:4]) - P_)), 1), iid, key, side, why))
                p[1], p[2], p[3] = [round(float(x), 1) for x in P_]
    for side, sx in (('R', -1.0), ('L', 1.0)):
        if kind == 'C' and n >= 2:
            off = rcx + 5
            put('sup_articular_process', side, first_hit(m, [F[0] + sx * off, F[1] - 0.2 * rc, V[:, 2].max() + 30], [0, 0, -1]), 'v-sap')
            put('inf_articular_process', side, first_hit(m, [F[0] + sx * off, F[1] + 0.2 * rc, V[:, 2].min() - 30], [0, 0, 1]), 'v-iap')
        if kind == 'T':
            loc = V[(np.abs(V[:, 1] - (ywall_c - 2)) < 2.5) & (np.abs(V[:, 0] - F[0]) < rcx + 10) & (np.abs(V[:, 2] - F[2]) < 30)]
            ztl, zbl = loc[:, 2].max(), loc[:, 2].min()
            put('sup_costal_facet', side, first_hit(m, [F[0] + sx * 90, ywall_c - 2, ztl - 3], [-sx, 0, 0]), 'v-scf')
            put('inf_costal_facet', side, first_hit(m, [F[0] + sx * 90, ywall_c - 2, zbl + 3], [-sx, 0, 0]), 'v-icf')
            xo = F[0] + sx * 0.9 * rcx
            col = V[(np.abs(V[:, 0] - xo) < 3) & (V[:, 1] > F[1])]
            put('sup_articular_process', side, first_hit(m, [xo, F[1] + 80, col[:, 2].max() - 4], [0, -1, 0]), 'v-sap')
            put('lamina', side, first_hit(m, [F[0] + sx * 0.55 * rcx, F[1] + 80, F[2] - 2], [0, -1, 0]), 'v-lamina')
        if kind == 'L':
            put('pedicle', side, first_hit(m, [F[0] + sx * 90, F[1] - 0.25 * rc, F[2] + 6], [-sx, 0, 0]), 'v-pedicle')
    if kind == 'T':
        zs = []
        for sx in (-1.0, 1.0):
            xo2 = F[0] + sx * 0.75 * rcx; col2 = V[(np.abs(V[:, 0] - xo2) < 3) & (V[:, 1] > F[1] + rc)]
            zs.append(col2[:, 2].min())
        zi = max(zs) + 4
        for side, sx in (('R', -1.0), ('L', 1.0)):
            put('inf_articular_process', side, first_hit(m, [F[0] + sx * 0.75 * rcx, F[1] + 80, zi], [0, -1, 0]), 'v-iap')
    # 없는 구조 제거: T10–12 아래갈비오목, T11–12 가로돌기갈비오목
    drop = set()
    if kind == 'T' and n >= 10: drop.add('inf_costal_facet')
    if kind == 'T' and n >= 11: drop.add('tp_costal_facet')
    v['pts'] = [p for p in pts if p[0] not in drop]

for it in D['items']:
    if it['id'][0] in 'CTL' and it['id'][1:].isdigit() and it['id'] != 'C1': vert_fix(it)

# ---- 고리뼈(C1): 위·아래관절면 = 위/아래에서 내려다본 가쪽덩이 관절면, 가쪽덩이 = 두 면 사이 앞면
it = next(x for x in D['items'] if x['id'] == 'C1'); v = it['var']['']; m = mesh(v['meshes'][0]); V = m.vertices
F = np.array(next(p for p in v['pts'] if p[0] == 'vb_foramen')[1:4])
for side, sx in (('R', -1.0), ('L', 1.0)):
    tp = next(p for p in v['pts'] if p[0] == 'atlas_tp' and p[5] == side)
    xm = F[0] + sx * 0.5 * abs(tp[1] - F[0]) * 0.95   # 가쪽덩이 가운데 (척주관 가장자리와 가로돌기 끝 사이)
    sf = first_hit(m, [xm, F[1] - 3, V[:, 2].max() + 30], [0, 0, -1]); inf_ = first_hit(m, [xm, F[1] - 3, V[:, 2].min() - 30], [0, 0, 1])
    for p in v['pts']:
        if p[5] != side: continue
        if p[0] == 'atlas_sup_facet' and sf is not None: p[1:4] = [round(float(x), 1) for x in sf]
        if p[0] == 'atlas_inf_facet' and inf_ is not None: p[1:4] = [round(float(x), 1) for x in inf_]
        if p[0] == 'atlas_lateral_mass' and sf is not None and inf_ is not None:
            mc = (sf + inf_) / 2; h = first_hit(m, mc + np.array([0, -30, 0]) * -0 , [sx * 0.35, -1, 0])
            if h is not None: p[1:4] = [round(float(x), 1) for x in h]

# ---- 좌우 짝 중 틀린 쪽을 맞는 쪽의 거울상으로 (정중선 뼈)
def mirror_fix(iid, key, src):
    it = next(x for x in D['items'] if x['id'] == iid)
    for v in it['var'].values():
        S_ = [p for p in v['pts'] if p[0] == key and p[5] == src]; T_ = [p for p in v['pts'] if p[0] == key and p[5] != src and p[5]]
        if not S_ or not T_: continue
        Vall = np.vstack([mesh(mm).vertices for mm in v['meshes']]); cx = (Vall[:, 0].min() + Vall[:, 0].max()) / 2
        q = np.array(S_[0][1:4]); q[0] = 2 * cx - q[0]
        tgt = T_[0]; mm = mesh(tgt[4]); c, _, _ = mm.nearest.on_surface([q])
        newp = c[0] if LM[key]['t'] != 'f' else q
        moves.append((round(float(np.linalg.norm(np.array(tgt[1:4]) - newp)), 1), iid, key, tgt[5], 'mirror'))
        setpt(key, tgt[4], newp, 'mirror', side=tgt[5])
def pair_mirror(iid, key, src):
    it = next(x for x in D['items'] if x['id'] == iid); dst = 'L' if src == 'R' else 'R'
    vs, vd = it['var'][src], it['var'][dst]
    ps = next(p for p in vs['pts'] if p[0] == key); pd = next(p for p in vd['pts'] if p[0] == key)
    cs = mesh(ps[4]).vertices.mean(0); cd = mesh(pd[4]).vertices.mean(0)
    q = np.array(ps[1:4]) - cs; q[0] = -q[0]; q = q + cd
    c, _, _ = mesh(pd[4]).nearest.on_surface([q])
    moves.append((round(float(np.linalg.norm(np.array(pd[1:4]) - c[0])), 1), iid, key, dst, 'pair-mirror'))
    setpt(key, pd[4], c[0], 'pair-mirror', side=pd[5])
pair_mirror('scapula', 'suprascapular_notch', 'R')

# 가쪽복사오목: 가쪽복사 끝보다 8~22mm 위, 안쪽·뒤쪽을 향한 면의 중심
it_f = next(x for x in D['items'] if x['id'] == 'fibula')
for sd_, v_ in it_f['var'].items():
    pf = next(p for p in v_['pts'] if p[0] == 'malleolar_fossa'); m_ = mesh(pf[4])
    V, N = m_.vertices, m_.vertex_normals; zt = V[:, 2].min()
    Mx = 1.0 if sd_ == 'R' else -1.0
    sel = (V[:, 2] > zt + 8) & (V[:, 2] < zt + 22) & (N[:, 0] * Mx > 0.2) & (N[:, 1] > 0.3)
    q = np.median(V[sel], 0); c, _, _ = m_.nearest.on_surface([q])
    moves.append((round(float(np.linalg.norm(np.array(pf[1:4]) - c[0])), 1), 'fibula', 'malleolar_fossa', sd_, 'fossa'))
    setpt('malleolar_fossa', pf[4], c[0], 'fossa', side=pf[5])
mirror_fix('hyoid', 'greater_horn', 'R')
mirror_fix('frontal', 'supraorbital_notch', 'R')
mirror_fix('sacrum', 'sacral_ala', 'R')
mirror_fix('ethmoid', 'cribriform_plate', 'R')
mirror_fix('C2', 'inf_articular_process', 'L')
# 허리뼈 아래관절돌기: 정중선에서 더 먼(가시돌기에 붙지 않은) 쪽을 기준으로 거울상
for n in range(1, 6):
    it = next(x for x in D['items'] if x['id'] == f'L{n}'); v = it['var']['']
    V_ = mesh(v['meshes'][0]).vertices; cx = (V_[:, 0].min() + V_[:, 0].max()) / 2
    pr = {p[5]: p for p in v['pts'] if p[0] == 'inf_articular_process'}
    if abs(abs(pr['R'][1] - cx) - abs(pr['L'][1] - cx)) > 3:
        mirror_fix(f'L{n}', 'inf_articular_process', 'R' if abs(pr['R'][1] - cx) > abs(pr['L'][1] - cx) else 'L')
# 머리뼈: 왼쪽 위턱뼈 이마돌기(26 mm 뒤로 들어가 있음) → 오른쪽 거울상, 시각신경관은 좌우 평균 위치로
def skull_mirror(key, src, avg=False):
    v = next(x for x in D['items'] if x['id'] == 'skull')['var']['']
    S_ = next(p for p in v['pts'] if p[0] == key and p[5] == src); T_ = next(p for p in v['pts'] if p[0] == key and p[5] and p[5] != src)
    a_ = np.array(S_[1:4]); b_ = np.array(T_[1:4]); cx = -1.0
    if avg:
        mb = b_.copy(); mb[0] = 2 * cx - mb[0]; na = (a_ + mb) / 2; nb = na.copy(); nb[0] = 2 * cx - nb[0]
        setpt(key, S_[4], na, 'skull-avg', side=S_[5]); setpt(key, T_[4], nb, 'skull-avg', side=T_[5])
    else:
        q = a_.copy(); q[0] = 2 * cx - q[0]; c, _, _ = mesh(T_[4]).nearest.on_surface([q])
        setpt(key, T_[4], c[0], 'skull-mirror', side=T_[5])
skull_mirror('frontal_process_maxilla', 'R')
skull_mirror('optic_canal', 'R', avg=True)

# 같은 핀이 두 번 들어간 경우(머리뼈 전체의 턱끝구멍 등) 첫 번째만 남김
for it in D['items']:
    for v in it['var'].values():
        seen = set(); out = []
        for p in v['pts']:
            k = (p[0], p[5], p[4])
            if k in seen: continue
            seen.add(k); out.append(p)
        v['pts'] = out

# ---- 넙다리뼈 융기사이오목: 뒤쪽, 두 관절융기 사이에서 가장 깊이 들어간 곳
for sd, v in side_items('femur'):
    b = Bone(v['meshes'], sd); Pd = b.d('P')
    k = b.mask(h=(0.02, 0.11), m=(0.4, 0.6)) & ((b.N @ Pd) > 0.2)
    idx = np.where(k)[0]; i = idx[np.argmin(b.V[idx] @ Pd)]
    setpt('intercondylar_fossa', v['meshes'][0], b.V[i], 'icf')
# ---- 어깨뼈 오목들: 면의 한가운데
for sd, v in side_items('scapula'):
    b = Bone(v['meshes'], sd)
    i = b.face_center('A', h=(0.3, 0.72), m=(0.3, 0.8)); setpt('subscapular_fossa', v['meshes'][0], b.V[i], 'ssf')
    sp = np.array(next(p for p in v['pts'] if p[0] == 'scap_spine')[1:4])
    # 가시 위쪽 면: 어깨뼈가시 핀보다 위, 안쪽 절반
    sa = np.array(next(p for p in v['pts'] if p[0] == 'superior_angle')[1:4])
    Mx = b.d('M')[0]; xm = (b.V[:, 0] * Mx).max(); W = np.ptp(b.V[:, 0])
    xx = b.V[:, 0] * Mx
    k = (b.V[:, 2] > sp[2] + 6) & (b.V[:, 2] < sa[2] - 4) & (xx < xm - 0.08 * W) & (xx > xm - 0.45 * W) & ((b.N @ b.d('P')) > 0.3)
    idx = np.where(k)[0]
    if len(idx):
        Q = b.V[idx][:, [0, 2]]; c = np.median(Q, 0); i = idx[np.argmin(np.linalg.norm(Q - c, axis=1))]
        setpt('supraspinous_fossa', v['meshes'][0], b.V[i], 'spf')
# ---- 엉치뼈 뒤엉치뼈구멍: 뒤에서 본 깊이지도에서 S1–S2 높이의 가장 깊은 구멍
it = next(x for x in D['items'] if x['id'] == 'sacrum'); v = it['var']['']; m = mesh(v['meshes'][0]); V = m.vertices
cx = (V[:, 0].min() + V[:, 0].max()) / 2
af = {p[5]: np.array(p[1:4]) for p in v['pts'] if p[0] == 'ant_sacral_foramen'}
for side, sx in (('R', -1.0), ('L', 1.0)):
    best = None
    for dx in np.arange(6, 30, 1.5):
        for z in np.arange(af[side][2] - 4, af[side][2] + 30, 1.5):
            o = np.array([cx + sx * dx, V[:, 1].max() + 40, z]); h = first_hit(m, o, [0, -1, 0])
            dep = (o[1] - h[1]) if h is not None else 999
            if best is None or dep > best[0]: best = (dep, o, h)
    dep, o, h = best
    P_ = np.array([o[0], (V[:, 1].max() if h is None else h[1] + 4), o[2]])
    P_[1] = min(P_[1], V[(np.abs(V[:, 0] - o[0]) < 6) & (np.abs(V[:, 2] - o[2]) < 6), 1].max() - 3)
    for p in v['pts']:
        if p[0] == 'post_sacral_foramen' and p[5] == side:
            moves.append((round(float(np.linalg.norm(np.array(p[1:4]) - P_)), 1), 'sacrum', 'post_sacral_foramen', side, 'depthmap'))
            p[1:4] = [round(float(x), 1) for x in P_]

# ---- 텍스트 바로잡기
def fixtxt(key, field, old, new):
    v = LM[key][field]; assert old in v, (key, field, old); LM[key][field] = v.replace(old, new)
fixtxt('fem_neck', 'd', '(앞굽음)', '(앞기울임, anteversion)')
fixtxt('pubic_tubercle', 'c', '샅굴헤르니아(결절 위가쪽)', '샅굴헤르니아(결절 위안쪽)')
LM['hook_hamate']['o'] = '유구골갈고리'
fixtxt('zygomatic_body', 'c', '광대뼈 골절(삼각골절)', '광대뼈 골절(삼각대골절, tripod fracture)')
fixtxt('aiis', 'd', 'ASIS 아래.', 'ASIS 아래. 넙다리곧은근 곧은갈래와 엉덩넙다리인대가 붙는다.')
fixtxt('gluteal_tuberosity', 'd', '몸통 위쪽 뒤가쪽의 거친면.', '몸통 위쪽 뒤가쪽의 거친면. 큰볼기근 일부가 붙는다.')
fixtxt('gerdy_tubercle', 'd', '가쪽관절융기 앞가쪽의 결절.', '가쪽관절융기 앞가쪽의 결절. 엉덩정강띠가 붙는다.')
fixtxt('infraglenoid_tubercle', 'd', '접시오목 바로 아래.', '접시오목 바로 아래. 위팔세갈래근 긴갈래가 시작한다.')
fixtxt('supraglenoid_tubercle', 'd', '접시오목 바로 위.', '접시오목 바로 위. 위팔두갈래근 긴갈래가 시작한다.')
ITM = {it['id']: it for it in D['items']}
t = ITM['talus']['info']
assert '쉼표 모양 가쪽 관절면(큰 세모꼴)' in t['lr']
t['lr'] = '도르래를 위, 머리를 앞으로 둔다. 도르래 양옆의 관절면 중 크고 세모꼴인 면이 가쪽(가쪽복사와 관절), 작은 쉼표 모양 면이 안쪽(안쪽복사와 관절).'
RIBD = {
 'rib2': '제2갈비뼈: 제1갈비뼈보다 길고 덜 납작하다. 바깥면 가운데쯤에 앞톱니근거친면이 있는 것이 특징. 머리 관절면 2개(T1·T2).',
 'rib10': '제10갈비뼈: 머리 관절면이 1개(T10 몸통)인 것이 전형적 갈비뼈와 다르다. 갈비연골이 위 갈비연골에 붙는 마지막 거짓갈비뼈.',
 'rib11': '뜬갈비뼈: 머리 관절면 1개, 목·결절이 없거나 흔적만 있고, 갈비뼈각·갈비뼈고랑이 약하다. 앞끝이 뾰족하고 복장뼈와 연결되지 않는다.',
 'rib12': '뜬갈비뼈: 가장 짧은 경우가 많다. 머리 관절면 1개, 목·결절·갈비뼈각·갈비뼈고랑이 없다. 앞끝이 뾰족하고 복장뼈와 연결되지 않는다.'}
for k, v in RIBD.items(): ITM[k]['info']['d'] = v

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
