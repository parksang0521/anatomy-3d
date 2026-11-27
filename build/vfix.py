import re
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
                (f'{s} renal vein', 'Inferior vena cava', 'side')]
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


def _frames(C):
    T = np.gradient(C, axis=0); T /= np.linalg.norm(T, axis=1)[:, None] + 1e-12
    n0 = np.cross(T[0], [0, 0, 1.0])
    if np.linalg.norm(n0) < 1e-3: n0 = np.cross(T[0], [1.0, 0, 0])
    n0 /= np.linalg.norm(n0); N = [n0]
    for i in range(1, len(C)):
        v = N[-1] - T[i] * (N[-1] @ T[i]); v /= np.linalg.norm(v) + 1e-12; N.append(v)
    N = np.array(N); return T, N, np.cross(T, N)


def _profile(P, c, t, n, b, sides, slab=0.002, reach=0.016):
    """c를 지나는 t-수직 단면에서 각도별 최대 반지름 (n,b 기준각)"""
    d = P - c; m = (np.abs(d @ t) < slab) & (np.linalg.norm(d, axis=1) < reach)
    d = d[m]; x, y = d @ n, d @ b; ang = np.arctan2(y, x) % (2 * np.pi); r = np.hypot(x, y)
    bins = (ang / (2 * np.pi) * sides).astype(int) % sides
    out = np.full(sides, np.nan)
    for k in range(sides):
        v = r[bins == k]
        if len(v): out[k] = v.max()
    ok = ~np.isnan(out)
    if ok.sum() < 3: return None
    idx = np.arange(sides); out = np.interp(idx, idx[ok], out[ok], period=sides)
    sm = (np.roll(out, 1) + 2 * out + np.roll(out, -1)) / 4
    return np.maximum(sm, out * 0.97)


def tube_shaped(C, RA, RB, sides):
    T, N, B = _frames(C)
    if RB is None: R = RA
    else:
        s = np.linspace(0, 1, len(C)); w = (3 * s**2 - 2 * s**3)[:, None]
        R = RA[None] * (1 - w) + RB[None] * w
    a = np.linspace(0, 2 * np.pi, sides, endpoint=False) + np.pi / sides
    V = (C[:, None, :] + R[:, :, None] * (np.cos(a)[None, :, None] * N[:, None, :] + np.sin(a)[None, :, None] * B[:, None, :])).reshape(-1, 3)
    i = np.arange(len(C) - 1)[:, None]; j = np.arange(sides)[None, :]
    a_ = i * sides + j; b_ = i * sides + (j + 1) % sides
    F = np.concatenate([np.stack([a_, a_ + sides, b_], -1).reshape(-1, 3), np.stack([b_, a_ + sides, b_ + sides], -1).reshape(-1, 3)])
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
    # 온엉덩 → 바깥엉덩 → 넙다리 동·정맥: 원본은 바깥엉덩 끝이 앞으로 튀어나와 넙다리 시작부와 나란히 겹치고
    # 각 마디가 끝끼리 맞붙어 있어 끊겨 보임 → 중심선을 따라 한 줄기 관으로 다시 만들고 넙다리 윗끝을 감싸 이음
    for sd in ('Left', 'Right'):
        for kind in ('artery', 'vein'):
            ci, a, b = f'{sd} common iliac {kind}', f'{sd} external iliac {kind}', f'{sd} femoral {kind}'
            if not all(k in structs for k in (ci, a, b)): continue
            r = retube(cur(a), cur(b), PC=cur(ci))
            if r is None: log(f'  retube FAILED {a}'); continue
            (V, FC), (_, FE), info = r
            for k, F_ in ((ci, FC), (a, FE)):
                structs[k]['P'] = [V]; structs[k]['I'] = [F_.reshape(-1)]; structs[k]['n'] = len(V)
            log(f'  retube {ci} + {a} -> {b}: r~{info[0]*1000:.1f}mm, {info[2]} pts')
        k, b = f'{sd} superficial epigastric artery', f'{sd} femoral artery'
        if k in structs and b in structs:
            PK = cur(k); r = branch_join(PK, np.concatenate(structs[k]['I']).reshape(-1, 3), cur(b))
            if r is None: log(f'    attach FAILED {k}')
            else:
                structs[k]['P'] = [PK]; structs[k]['I'] = [r[0].reshape(-1)]; structs[k]['n'] = len(PK)
                append(k, r[1], r[2]); log(f'    attach {k} -> {b}: r {r[3][0]*1000:.1f}mm len {r[3][1]*1000:.0f}mm')
    # 평활화로 벌어진 접점 복구 (작은 쪽에 짧은 연결관)
    nr = 0
    for a, b in touch:
        d = mindist(cur(a), cur(b))
        if d > 0.0012:
            small, big = (a, b) if len(orig[a]) < len(orig[b]) else (b, a)
            g, _ = bridge(cur(small), cur(big), 'side')
            if g is not None: append(small, *g); nr += 1
    log(f'vfix: smoothed {len(vk)} (subdivided {len(sub)}), bridged {nb}, rejoined {nr} of {len(touch)} contacts')


# ---- 바깥엉덩 → 넙다리 혈관 이음부 다시 만들기 (원본은 바깥엉덩 끝이 앞으로 튀어나와 넙다리 시작부와 나란히 겹침) ----
def _slice_center(P, y, h=0.0025):
    s = P[(P[:, 1] > y - h) & (P[:, 1] < y + h)]
    if len(s) < 6: return None, None
    c = s.mean(0); c[1] = y
    r = float(np.median(np.linalg.norm((s - c)[:, [0, 2]], axis=1)))
    return c, r


def _cut(P, F, c, t, keep_pos, lim):
    """c를 지나고 t에 수직인 평면으로 자름. keep_pos=True면 (p-c)·t>0 쪽을 남김. lim 반경 밖은 건드리지 않음."""
    s = (P - c) @ t; near = np.linalg.norm(P - c, axis=1) < lim
    drop_v = near & ((s < 0) if keep_pos else (s > 0))
    keep = ~drop_v[F].any(1); F2 = F[keep]
    # 잘린 뒤 떨어져 나온 조각(자른 곳 근처)은 버림
    import trimesh as _t
    comps = _t.graph.connected_components(_t.Trimesh(P, F2, process=False).face_adjacency, nodes=np.arange(len(F2)))
    if len(comps) > 1:
        big = max(comps, key=len); kf = np.ones(len(F2), bool)
        for cc in comps:
            if cc is big: continue
            if (np.linalg.norm(P[F2[cc].ravel()] - c, axis=1) < lim).any(): kf[cc] = False
        F2 = F2[kf]
    return F2


def _cut_conn(P, F, c, t_keep, r):
    """t_keep 반대쪽(평면 너머)에서, 자른 단면 고리와 이어진 부분만 통째로 제거"""
    from scipy.sparse import coo_matrix
    from scipy.sparse.csgraph import connected_components
    s = (P - c) @ t_keep; cand = s < 0
    e = np.vstack([F[:, [0, 1]], F[:, [1, 2]], F[:, [2, 0]]]); e = e[cand[e[:, 0]] & cand[e[:, 1]]]
    n = len(P); A = coo_matrix((np.ones(len(e)), (e[:, 0], e[:, 1])), shape=(n, n))
    _, lab = connected_components(A, directed=False)
    radial = np.linalg.norm((P - c) - np.outer(s, t_keep), axis=1)
    seeds = cand & (s > -0.003) & (radial < r * 2.2)
    drop = np.isin(lab, np.unique(lab[seeds])) & cand
    F2 = F[~drop[F].any(1)]
    import trimesh as _t
    comps = _t.graph.connected_components(_t.Trimesh(P, F2, process=False).face_adjacency, nodes=np.arange(len(F2)))
    if len(comps) > 1:
        big = max(comps, key=len); kf = np.ones(len(F2), bool)
        for cc in comps:
            if cc is not big and (np.linalg.norm(P[F2[cc].ravel()] - c, axis=1) < 0.03).any(): kf[cc] = False
        F2 = F2[kf]
    return F2


def junction(PA, FA, PB, FB, yA, yB):
    """위 혈관 A(바깥엉덩)를 yA 높이에서 축에 수직으로 자르고, 아래 혈관 B(넙다리)는 그대로 둔 채
    A의 끝에서 B의 열린 윗끝을 감싸며 B 속으로 들어가는 관 하나로 이음 → (FA', FB, V, F, info)"""
    cA, rA = _slice_center(PA, yA); cA2, _ = _slice_center(PA, yA + 0.010)
    if cA is None or cA2 is None: return None
    tA = cA - cA2; tA /= np.linalg.norm(tA)
    def perp(P, c, t):
        sl = None
        for _ in range(3):
            m = (np.abs((P - c) @ t) < 0.0015) & (np.linalg.norm(P - c, axis=1) < 0.014)
            if m.sum() < 6: break
            sl = P[m]; c = sl.mean(0)
        if sl is None: return c, 0.004
        d = np.linalg.norm((sl - c) - np.outer((sl - c) @ t, t), axis=1)
        return c, float(np.percentile(d, 70))
    cA, rA = perp(PA, cA, tA)
    FA2 = _cut_conn(PA, FA, cA, -tA, rA)
    # B 윗부분 축
    top = PB[PB[:, 1] > PB[:, 1].max() - 0.03]
    w = np.linalg.svd(top - top.mean(0), full_matrices=False)[2][0]
    if w[1] > 0: w = -w
    ytop = PB[:, 1].max(); seed = top[top[:, 1] > ytop - 0.006].mean(0)
    c1, r1 = perp(PB, seed + w * 0.004, w)
    c2, r2 = perp(PB, c1 + w * 0.014, w)
    ov = 0.004; S = cA - tA * ov
    Ln = np.linalg.norm(c1 - S); n1 = max(16, int(Ln / 0.0009))
    t = np.linspace(0, 1, n1)[:, None]
    h00 = 2 * t**3 - 3 * t**2 + 1; h10 = t**3 - 2 * t**2 + t; h01 = -2 * t**3 + 3 * t**2; h11 = t**3 - t**2
    C1 = h00 * S + h10 * tA * Ln * 1.1 + h01 * c1 + h11 * w * Ln * 1.1
    n2 = 14; C2 = c1 + np.linspace(0, 1, n2)[1:, None] * (c2 - c1)
    C = np.concatenate([C1, C2])
    sides = 32; T_, N_, B_ = _frames(C)
    RA = _profile(PA, cA, tA, N_[0], B_[0], sides)
    R1 = _profile(PB, c1, w, N_[n1 - 1], B_[n1 - 1], sides)
    R2 = _profile(PB, c2, w, N_[-1], B_[-1], sides)
    if RA is None: RA = np.full(sides, rA)
    if R1 is None: R1 = np.full(sides, r1)
    if R2 is None: R2 = np.full(sides, r2)
    RA = RA * 1.05 + 0.0002; R1 = R1 * 1.06 + 0.0002; R2 = R2 * 0.9
    sm = lambda x: 3 * x**2 - 2 * x**3
    s1 = sm(np.linspace(0, 1, n1))[:, None]; s2 = sm(np.clip((np.linspace(0, 1, n2)[1:] - 0.35) / 0.65, 0, 1))[:, None]
    R = np.concatenate([RA[None] * (1 - s1) + R1[None] * s1, R1[None] * (1 - s2) + R2[None] * s2])
    V, F = tube_shaped(C, R, None, sides)
    return FA2, FB, V, F, (rA, r1, float(Ln))

def branch_join(PA, FA, PB, cut=0.012):
    """가지 A의 끝(줄기 B에 가장 가까운 끝)을 cut만큼 잘라내고, 줄기 B 속으로 부드럽게 휘어 들어가는 관을 만듦"""
    TB = cKDTree(PB); d, _ = TB.query(PA); tip = PA[int(d.argmin())]
    L = PA[np.linalg.norm(PA - tip, axis=1) < cut * 2.2]
    c0 = L.mean(0); u = np.linalg.svd(L - c0, full_matrices=False)[2][0]
    if (c0 - tip) @ u < 0: u = -u                       # u: 끝 → 가지 몸통 방향
    cA = tip + u * cut
    for _ in range(3):
        sl = PA[(np.abs((PA - cA) @ u) < 0.0015) & (np.linalg.norm(PA - cA, axis=1) < 0.012)]
        if len(sl) < 6: return None
        cA = sl.mean(0)
    rA = float(np.percentile(np.linalg.norm((sl - cA) - np.outer((sl - cA) @ u, u), axis=1), 70))
    FA2 = _cut_conn(PA, FA, cA, u, rA)
    q = PB[int(TB.query(tip)[1])]
    nb = PB[np.linalg.norm(PB - q, axis=1) < 0.022]
    w = np.linalg.svd(nb - nb.mean(0), full_matrices=False)[2][0]
    if w[1] > 0: w = -w                                  # 줄기 아래쪽 방향
    cB = q.copy()
    for _ in range(4):
        sl = PB[(np.abs((PB - cB) @ w) < 0.002) & (np.linalg.norm(PB - cB, axis=1) < 0.014)]
        if len(sl) < 6: break
        cB = sl.mean(0)
    S = cA + u * 0.003; E = cB
    Ln = np.linalg.norm(E - S); t1 = (E - S) / Ln * 0.5 + w * 0.5; t1 /= np.linalg.norm(t1)
    n = max(12, int(Ln / 0.0009)); t = np.linspace(0, 1, n)[:, None]
    h00 = 2 * t**3 - 3 * t**2 + 1; h10 = t**3 - 2 * t**2 + t; h01 = -2 * t**3 + 3 * t**2; h11 = t**3 - t**2
    C = h00 * S + h10 * (-u) * Ln * 0.7 + h01 * E + h11 * t1 * Ln * 0.5
    V, F = tube_path(C, np.full(n, rA * 1.07), sides=18)
    return FA2, V, F, (rA, float(Ln))


def retube(PA, PB, FA=None, keep=0.035, PC=None):
    """A(바깥엉덩 동·정맥)를 중심선(높이별 단면 중심)을 따라 새 관으로 다시 만들고,
    아래끝은 B(넙다리)의 윗끝을 감싸며 B 속으로 들어가게 함 → (V, F, info)"""
    def slab(P, c, d, reach=0.014, h=0.002):
        m = (np.abs((P - c) @ d) < h) & (np.linalg.norm(P - c, axis=1) < reach)
        if m.sum() < 5: return None, None
        L = P[m]; cc = L.mean(0)
        r = np.linalg.norm((L - cc) - np.outer((L - cc) @ d, d), axis=1)
        return cc, float(np.percentile(r, 75))
    tb = PB[PB[:, 1] > PB[:, 1].max() - 0.03]
    w = np.linalg.svd(tb - tb.mean(0), full_matrices=False)[2][0]
    if w[1] > 0: w = -w
    btop = PB[np.argmax(PB @ (-w))]
    c1, r1 = slab(PB, btop + w * 0.007, w)
    if c1 is None: return None
    for _ in range(2): c1, r1 = slab(PB, c1, w)
    c2, r2 = slab(PB, c1 + w * 0.012, w)
    if c2 is None: c2, r2 = c1 + w * 0.012, r1
    PA0 = PA
    if PC is not None: PA = np.concatenate([PC, PA])
    ymax = PA[:, 1].max() if FA is None else min(PA[:, 1].max(), c1[1] + keep); ystop = c1[1] + 0.012
    ys = np.arange(ymax - 0.004, ystop, -0.002)
    C = []
    prev = None
    for y in ys:
        m = np.abs(PA[:, 1] - y) < 0.002
        if prev is not None: m &= np.linalg.norm(PA[:, [0, 2]] - prev[[0, 2]], axis=1) < 0.009
        if m.sum() < 4: continue
        c = PA[m].mean(0); c[1] = y; C.append(c); prev = c
    if len(C) < 5: return None
    C = np.array(C)
    for _ in range(6): C[1:-1] = (C[:-2] + 2 * C[1:-1] + C[2:]) / 4
    t0 = (C[1] - C[0]) / np.linalg.norm(C[1] - C[0])
    FA2 = None
    if FA is not None:
        _, r0 = slab(PA, C[0], t0)
        FA2 = _cut_conn(PA, FA, C[0], -t0, r0 or 0.005)
        # 잘린 가장자리 정점을 자른 평면 위로 붙여 들쭉날쭉한 테두리를 없앰 (PA를 직접 수정)
        e = np.sort(np.vstack([FA2[:, [0, 1]], FA2[:, [1, 2]], FA2[:, [2, 0]]]), 1)
        u_, cnt = np.unique(e, axis=0, return_counts=True); bv = np.unique(u_[cnt == 1])
        bv = bv[np.linalg.norm(PA[bv] - C[0], axis=1) < 0.02]
        sv = (PA[bv] - C[0]) @ t0; PA[bv] -= np.outer(np.minimum(sv, 0) * 0 + sv, t0)
    C = np.concatenate([[C[0] - t0 * 0.005], C])
    dl = C[-1] - C[-2]; dl /= np.linalg.norm(dl); S = C[-1]; Ln = np.linalg.norm(c1 - S); n1 = max(16, int(Ln / 0.0009))
    t = np.linspace(0, 1, n1)[1:, None]
    h00 = 2 * t**3 - 3 * t**2 + 1; h10 = t**3 - 2 * t**2 + t; h01 = -2 * t**3 + 3 * t**2; h11 = t**3 - t**2
    H = h00 * S + h10 * dl * Ln * 1.0 + h01 * c1 + h11 * w * Ln * 1.0
    n2 = 12; st = np.linspace(0, 1, n2)[1:]
    CC = np.concatenate([C, H, c1 + st[:, None] * (c2 - c1)])
    T_, N_, B_ = _frames(CC)
    def cov(P, c, t, n, b, h=0.0025, reach=0.013):
        m = (np.abs((P - c) @ t) < h) & (np.linalg.norm(P - c, axis=1) < reach)
        L = P[m] - c
        if len(L) < 6: return None
        x, y = L @ n, L @ b; x -= x.mean(); y -= y.mean()
        return np.array([[x @ x, x @ y], [x @ y, y @ y]]) / len(L) * 2.0   # 고리 위 점: 분산 = 반지름²/2
    nA = len(C); M = []
    for i in range(nA):
        M.append(cov(PA, CC[i], T_[i], N_[i], B_[i]))
    ok = [i for i in range(nA) if M[i] is not None]
    if len(ok) < 3: return None
    M = np.array([M[i] if M[i] is not None else M[min(ok, key=lambda j: abs(j - i))] for i in range(nA)])
    from scipy.ndimage import uniform_filter1d
    M = uniform_filter1d(M, 7, axis=0, mode='nearest')
    i1 = nA + n1 - 2; M1 = cov(PB, c1, T_[i1], N_[i1], B_[i1]); M2 = cov(PB, c2, T_[-1], N_[-1], B_[-1])
    if M1 is None: M1 = np.eye(2) * r1**2
    if M2 is None: M2 = M1
    sm = (3 * t[:, 0]**2 - 2 * t[:, 0]**3)[:, None, None]
    MH = M[-1][None] * 1.08 * (1 - sm) + M1[None] * 1.15 * sm
    MS = M1[None] * 1.15 * (1 - st[:, None, None]) + M2[None] * 0.72 * st[:, None, None]
    MM = np.concatenate([M * 1.08, MH, MS]); MM[:3] *= 1.12
    sides = 28; a = np.linspace(0, 2 * np.pi, sides, endpoint=False)
    V = []
    for c, n, b, m in zip(CC, N_, B_, MM):
        ev, evec = np.linalg.eigh(m); ev = np.sqrt(np.maximum(ev, 1e-8))
        loc = (evec @ np.diag(ev) @ evec.T) @ np.stack([np.cos(a), np.sin(a)])   # 행렬 제곱근 → 단면이 연속적으로 변함
        V.append(c + loc[0][:, None] * n + loc[1][:, None] * b)
    V = np.concatenate(V)
    def strip(i0, i1):
        i = np.arange(i0, i1)[:, None]; j = np.arange(sides)[None, :]
        a_ = i * sides + j; b_ = i * sides + (j + 1) % sides
        return np.concatenate([np.stack([a_, a_ + sides, b_], -1).reshape(-1, 3), np.stack([b_, a_ + sides, b_ + sides], -1).reshape(-1, 3)])
    info = (float(np.sqrt(np.linalg.eigvalsh(M[len(M) // 2]).mean())), r1, len(C))
    if PC is not None:
        dC = cKDTree(PC).query(CC[:nA])[0]; dA = cKDTree(PA0).query(CC[:nA])[0]
        k = int(np.argmax(dA < dC)) if (dA < dC).any() else nA - 1
        k = max(2, min(k, nA - 2))
        FC = strip(0, k); FE = strip(k, len(CC) - 1)
        return (V, FC), (V, FE), info
    return V, strip(0, len(CC) - 1), info, FA2
