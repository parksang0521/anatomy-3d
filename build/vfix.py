"""혈관 다듬기: (1) 매끈하게 평활화 (2) 원본 데이터에서 끊긴 혈관 이음 (3) 평활화로 벌어진 접점 복구"""
import numpy as np
import trimesh
from scipy.spatial import cKDTree

VSYS = ('arterial', 'venous')
BUDGET = 300000  # 분할로 늘어날 삼각형 상한

# 원본(BodyParts3D 4.0)에서 이어져야 하는데 떨어져 있는 혈관: (덧붙일 구조물, 이어질 구조물, 방식)
BRIDGES = []
for s in ('Right', 'Left'):
    BRIDGES += [(f'{s} internal carotid artery', f'{s} common carotid artery', 'tip'),
                (f'{s} posterior tibial vein', f'{s} popliteal vein', 'tip'),
                (f'{s} renal vein', 'Inferior vena cava', 'side'),
                (f'{s} femoral artery', f'{s} external iliac artery', 'tip')]
BRIDGES += [('Splenic vein', 'Hepatic portal vein', 'side'), ('Left common carotid artery', 'Arch of aorta', 'side')]


def weld(P, F):
    q = np.round(P * 2e5).astype(np.int64)
    _, first, inv = np.unique(q, axis=0, return_index=True, return_inverse=True)
    F = inv.reshape(-1)[F]
    F = F[(F[:, 0] != F[:, 1]) & (F[:, 1] != F[:, 2]) & (F[:, 0] != F[:, 2])]
    used = np.unique(F); remap = np.full(len(first), -1); remap[used] = np.arange(len(used))
    return P[first][used], remap[F]


def smooth_mesh(P, F, sub):
    P, F = weld(P, F)
    m = trimesh.Trimesh(P, F, process=False)
    if sub:
        v, f = trimesh.remesh.subdivide(P, F)          # 중점 분할(형태 유지)
        m = trimesh.Trimesh(v, f, process=False)
    v, f = np.asarray(m.vertices, float), np.asarray(m.faces)
    return taubin(v, f), f


def taubin(V, F, lamb=0.5, nu=-0.53, iters=8):
    """균일 가중 Taubin 평활화 (부피 유지형, 비다양체 메쉬에도 안전)"""
    from scipy.sparse import coo_matrix
    e = np.vstack([F[:, [0, 1]], F[:, [1, 2]], F[:, [2, 0]]]); e = np.unique(np.sort(e, 1), axis=0)
    n = len(V)
    A = coo_matrix((np.ones(2 * len(e)), (np.r_[e[:, 0], e[:, 1]], np.r_[e[:, 1], e[:, 0]])), shape=(n, n)).tocsr()
    A.data[:] = 1.0
    deg = np.asarray(A.sum(1)).ravel(); ok = deg > 0; inv = np.zeros(n); inv[ok] = 1 / deg[ok]
    X = V.copy()
    for _ in range(iters):
        for w in (lamb, nu):
            L = (A @ X) * inv[:, None] - X; L[~ok] = 0
            X = X + w * L
    return X


def local(P, p0, r0=0.003):
    """p0 근처 국소 형상: (중심, 축, 반지름)"""
    T = cKDTree(P); R = max(3 * r0, 0.003)
    for _ in range(3):
        L = P[T.query_ball_point(p0, R)]
        c = L.mean(0)
        u = np.linalg.svd(L - c, full_matrices=False)[2][0] if len(L) > 3 else np.array([0, 1.0, 0])
        d = np.linalg.norm((L - c) - np.outer((L - c) @ u, u), axis=1)
        r = min(float(np.percentile(d, 75)) if len(d) else r0, 0.009)
        R = min(max(2.5 * r, 0.003), 0.02)
    return c, u, max(r, 0.0006)


def tube_path(C, R, sides=16):
    T = np.gradient(C, axis=0); T /= np.linalg.norm(T, axis=1)[:, None] + 1e-12
    n0 = np.cross(T[0], [0, 0, 1.0])
    if np.linalg.norm(n0) < 1e-3: n0 = np.cross(T[0], [1.0, 0, 0])
    n0 /= np.linalg.norm(n0); N = [n0]
    for i in range(1, len(C)):
        v = N[-1] - T[i] * (N[-1] @ T[i]); v /= np.linalg.norm(v) + 1e-12; N.append(v)
    N = np.array(N); B = np.cross(T, N)
    a = np.linspace(0, 2 * np.pi, sides, endpoint=False)
    V = (C[:, None, :] + R[:, None, None] * (np.cos(a)[None, :, None] * N[:, None, :] + np.sin(a)[None, :, None] * B[:, None, :])).reshape(-1, 3)
    i = np.arange(len(C) - 1)[:, None]; j = np.arange(sides)[None, :]
    a_ = i * sides + j; b_ = i * sides + (j + 1) % sides
    F = np.concatenate([np.stack([a_, a_ + sides, b_], -1).reshape(-1, 3), np.stack([b_, a_ + sides, b_ + sides], -1).reshape(-1, 3)])
    # 둥근 마개(끝이 혈관 안에 묻히지 않는 경우 대비)
    return V, F


def bridge(PA, PB, mode):
    """PA 쪽 끝에서 PB로 이어지는 연결 튜브 (V, F)"""
    TA, TB = cKDTree(PA), cKDTree(PB)
    d, j = TB.query(PA); i = int(d.argmin()); a0 = PA[i]; b0 = PB[j[i]]
    cA, uA, rA = local(PA, a0)
    inA = cA - a0; inA /= np.linalg.norm(inA) + 1e-12
    if mode == 'tip':
        cB, uB, rB = local(PB, b0)
        inB = cB - b0; inB /= np.linalg.norm(inB) + 1e-12
    else:
        L = PB[TB.query_ball_point(b0, max(0.008, 3 * rA))]
        inB = L.mean(0) - b0; inB /= np.linalg.norm(inB) + 1e-12; rB = rA
    if mode == 'side': rA = rB = min(rA, 0.004)
    depth = lambda r: min(max(r, 0.0015) * 1.6, 0.008)
    S = a0 + inA * depth(rA); E = b0 + inB * depth(rB)
    Ln = np.linalg.norm(E - S)
    t0 = -inA * Ln * 0.9; t1 = inB * Ln * 0.9
    n = max(8, int(Ln / 0.0012))
    t = np.linspace(0, 1, n)[:, None]
    h00 = 2 * t**3 - 3 * t**2 + 1; h10 = t**3 - 2 * t**2 + t; h01 = -2 * t**3 + 3 * t**2; h11 = t**3 - t**2
    C = h00 * S + h10 * t0 + h01 * E + h11 * t1
    R = (rA + (rB - rA) * t[:, 0]) * 0.97
    if np.linalg.norm(C - (S + E) / 2, axis=1).max() > max(Ln, 0.01) * 1.2:
        return None, float(d.min())
    return tube_path(C, R), float(d.min())


def mindist(PA, PB):
    return float(cKDTree(PA).query(PB)[0].min())


def fix(structs, log=print):
    vk = [k for k, s in structs.items() if s['meta']['sys'] in VSYS]
    orig = {k: np.concatenate(structs[k]['P']) for k in vk}
    # 원래 맞닿아 있던 쌍(≤1.2mm) 기록
    bb = {k: (orig[k].min(0), orig[k].max(0)) for k in vk}
    tree = {k: cKDTree(orig[k]) for k in vk}
    touch = []
    for x, a in enumerate(vk):
        for b in vk[x + 1:]:
            if structs[a]['meta']['sys'] != structs[b]['meta']['sys']: continue
            if np.any(bb[a][0] - 0.002 > bb[b][1]) or np.any(bb[b][0] - 0.002 > bb[a][1]): continue
            if tree[a].query(orig[b])[0].min() <= 0.0012: touch.append((a, b))
    # 평활화: 굵고 거친 혈관부터 분할(삼각형 예산 안에서)
    score = {}
    for k in vk:
        P = orig[k]; F = np.concatenate(structs[k]['I']).reshape(-1, 3)
        e = np.linalg.norm(P[F[:, 0]] - P[F[:, 1]], axis=1).mean()
        rad = np.linalg.norm(P.max(0) - P.min(0))
        score[k] = (e, len(F))
    budget = BUDGET; sub = set()
    for k in sorted(vk, key=lambda k: -score[k][0]):
        e, n = score[k]
        if e < 0.0016: break
        if 3 * n <= budget: sub.add(k); budget -= 3 * n
    for k in vk:
        P = orig[k]; F = np.concatenate(structs[k]['I']).reshape(-1, 3)
        v, f = smooth_mesh(P, F, k in sub)
        structs[k]['P'] = [v]; structs[k]['I'] = [f.reshape(-1)]; structs[k]['n'] = len(v)
    cur = lambda k: np.concatenate(structs[k]['P'])
    def append(k, V, F):
        st = structs[k]; st['I'].append(F.reshape(-1) + st['n']); st['P'].append(V); st['n'] += len(V)
    # 원본 데이터의 끊긴 곳 잇기
    nb = 0
    for a, b, mode in BRIDGES:
        if a in structs and b in structs:
            g, d = bridge(cur(a), cur(b), mode)
            if g is None: log(f'  bridge FAILED {a} -> {b}'); continue
            append(a, *g); nb += 1; log(f'  bridge {a} -> {b}: gap {d*1000:.1f}mm')
    # 평활화로 벌어진 접점 복구 (작은 쪽에 짧은 연결관)
    nr = 0
    for a, b in touch:
        d = mindist(cur(a), cur(b))
        if d > 0.0012:
            small, big = (a, b) if len(orig[a]) < len(orig[b]) else (b, a)
            g, _ = bridge(cur(small), cur(big), 'side')
            if g is not None: append(small, *g); nr += 1
    log(f'vfix: smoothed {len(vk)} (subdivided {len(sub)}), bridged {nb}, rejoined {nr} of {len(touch)} contacts')
