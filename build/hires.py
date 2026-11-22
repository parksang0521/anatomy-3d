"""BodyParts3D 3.0 고해상도 STL로 구조물 교체 (4.0 위치에 정합) + 교체 못 한 저해상도 구조물 평활화"""
import os, struct, sys
import numpy as np
import trimesh, fast_simplification
from scipy.spatial import cKDTree
sys.path.insert(0, '/home/claude/data')
from common import to_ha

D = '/home/claude/data/bp3d/assets/BodyParts3D_data/stl/'
NAMES = {}
for l in open('/tmp/stlnames'):
    fid, nm = l.rstrip('\n').split('\t'); NAMES.setdefault(nm.lower(), fid)
FILES = {f.replace('.stl', '').replace('nsn', ''): f for f in os.listdir(D)}
OFF = np.array([0.0, 0.0600, -0.0985])
# 혈관은 교체하지 않음: 정합 시 축 방향으로 밀려 분기부가 끊어짐 → vfix.py에서 평활화
RATIO = {'skeletal': 0.30, 'muscular': 0.055, 'digestive': 0.5, 'respiratory': 0.4, 'cardio': 0.4, 'urinary': 0.6,
         'endocrine': 0.6, 'reproductive': 0.8}
CAP = {'skeletal': 30000, 'muscular': 12000}
SMOOTH_SYS = {'skeletal', 'muscular', 'digestive', 'respiratory', 'cardio', 'urinary', 'endocrine', 'reproductive', 'nervous'}

def load_stl(fid):
    b = open(D + FILES[fid], 'rb').read(); n = struct.unpack('<I', b[80:84])[0]
    a = np.frombuffer(b[84:84 + n * 50], dtype=np.dtype([('n', '<f4', 3), ('v', '<f4', (3, 3)), ('a', '<u2')]))
    v = to_ha(a['v'].reshape(-1, 3).astype(np.float64)) + OFF
    q = np.round(v * 2e5).astype(np.int64); uq, inv = np.unique(q, axis=0, return_inverse=True)
    F = inv.reshape(-1, 3); F = F[(F[:, 0] != F[:, 1]) & (F[:, 1] != F[:, 2]) & (F[:, 0] != F[:, 2])]
    return uq / 2e5, F

def sim_transform(src, dst):
    """src→dst 유사변환(회전+균일스케일+이동) 최소제곱"""
    ms, md = src.mean(0), dst.mean(0); a, b = src - ms, dst - md
    U, S, Vt = np.linalg.svd(a.T @ b); d = np.sign(np.linalg.det(U @ Vt))
    Dm = np.diag([1, 1, d]); R = (U @ Dm @ Vt).T
    s = (S * np.diag(Dm)).sum() / (a ** 2).sum()
    return s, R, md - s * R @ ms

def register(V3, V4, F4):
    """3.0 정점들을 4.0 메쉬에 맞추는 ICP(스케일 포함). (변환된 V3, 평균 양방향 오차, 대각선) 반환"""
    m4 = trimesh.Trimesh(V4, F4, process=False)
    S4 = m4.sample(4000) if len(F4) else V4
    t4 = cKDTree(np.vstack([V4, S4]))
    rng = np.random.default_rng(0)
    idx = rng.choice(len(V3), min(4000, len(V3)), replace=False)
    X = V3[idx].copy()
    # 초기: 무게중심 + 크기
    s0 = np.linalg.norm(V4.max(0) - V4.min(0)) / max(1e-9, np.linalg.norm(V3.max(0) - V3.min(0)))
    s0 = float(np.clip(s0, 0.85, 1.15))
    c3 = V3.mean(0); c4 = V4.mean(0)
    T = lambda P, s, R, t: (s * (R @ P.T)).T + t
    s, R, t = s0, np.eye(3), c4 - s0 * c3
    for it in range(40):
        Y = T(X, s, R, t)
        dist, j = t4.query(Y)
        keep = dist < np.percentile(dist, 90) + 1e-9
        s2, R2, t2 = sim_transform(Y[keep], t4.data[j[keep]])
        s, R, t = s2 * s, R2 @ R, s2 * (R2 @ t) + t2
        if it > 5 and abs(s2 - 1) < 1e-5 and np.linalg.norm(t2) < 1e-6: break
    s = float(np.clip(s, 0.8, 1.25))
    V3t = T(V3, s, R, t)
    d1 = cKDTree(V3t).query(np.vstack([V4, S4]))[0].mean()
    d2 = t4.query(V3t[idx])[0].mean()
    diag = np.linalg.norm(V4.max(0) - V4.min(0))
    return V3t, (d1 + d2) / 2, diag, s

def smooth_up(P, F, iters=1):
    try:
        v, f = trimesh.remesh.subdivide_loop(P, F, iterations=iters)
        m = trimesh.Trimesh(v, f, process=False)
        trimesh.smoothing.filter_taubin(m, lamb=0.5, nu=-0.53, iterations=6)
        return np.asarray(m.vertices), np.asarray(m.faces)
    except Exception as e:
        return P, F

def weld(P, F):
    q = np.round(P * 2e5).astype(np.int64); uq, first, inv = np.unique(q, axis=0, return_index=True, return_inverse=True)
    return P[first], inv.reshape(-1)[F]

def upgrade(structs, log=print):
    stat = dict(rep=0, rej=0, smooth=0)
    for en, st in structs.items():
        m = st['meta']; sy = m['sys']
        if sy in ('nerves', 'skin'): continue
        P4 = np.concatenate(st['P']); I4 = np.concatenate(st['I']); F4 = I4.reshape(-1, 3); t4 = len(F4)
        fid = NAMES.get(en.lower())
        done = False
        if fid and fid in FILES and sy in RATIO:
            V3, F3 = load_stl(fid); t3 = len(F3)
            if t3 > 2.0 * t4 and t3 > 300:
                V3t, err, diag, s = register(V3, P4, F4)
                ok = err < min(0.006, 0.05 * diag)
                if ok:
                    tgt = int(min(t3, max(t4 * 1.5, t3 * RATIO[sy]), CAP.get(sy, 40000)))
                    red = 1 - tgt / t3
                    if red > 0.02:
                        v2, f2 = fast_simplification.simplify(V3t.astype(np.float32), F3.astype(np.int32), target_reduction=red)
                        V3t, F3 = v2.astype(np.float64), f2.astype(np.int64)
                    st['P'] = [V3t]; st['I'] = [F3.reshape(-1)]; st['n'] = len(V3t)
                    stat['rep'] += 1; done = True
                else:
                    stat['rej'] += 1; log(f'  reject {en}: err={err*1000:.1f}mm diag={diag:.3f} s={s:.3f}')
        if not done and sy in SMOOTH_SYS and t4 < 6000 and sy != 'nervous':
            P, F = weld(P4, F4)
            v, f = smooth_up(P, F, 1)
            st['P'] = [v]; st['I'] = [f.reshape(-1)]; st['n'] = len(v); stat['smooth'] += 1
    log(f'hires: replaced {stat["rep"]}, rejected {stat["rej"]}, smoothed {stat["smooth"]}')
