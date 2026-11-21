"""BodyParts3D(4.0, ha 경량본) 메쉬에서 해부학 기준점을 계산하는 도구"""
import json, gzip, re
import numpy as np
from collections import defaultdict, deque

A = json.load(open('/home/claude/data/ha/public/models/atlas.json'))
_chunks = {}
def _chunk(i):
    if i not in _chunks: _chunks[i] = gzip.open('/home/claude/data/ha/public/models/body-%d.bin.gz' % i).read()
    return _chunks[i]
BY = defaultdict(list)
for p in A['parts']: BY[p['name'].lower()].append(p)

def mesh(name):
    """이름(대소문자 무시)으로 메쉬 (V,F) 반환. 같은 이름 여러 조각은 합침"""
    ps = BY[name.lower()]
    if not ps: raise KeyError(name)
    Vs, Fs, n = [], [], 0
    for p in ps:
        b = _chunk(p['chunk'])
        v = np.frombuffer(b, '<f4', p['vertexCount'] * 3, p['positions']).reshape(-1, 3).astype(float)
        f = np.frombuffer(b, '<u4', p['indexCount'], p['indices']).reshape(-1, 3).astype(int)
        Vs.append(v); Fs.append(f + n); n += len(v)
    return np.concatenate(Vs), np.concatenate(Fs)

def verts(name): return mesh(name)[0]
def find(pat):
    return sorted(k for k in BY if re.search(pat, k))

def centerline(name, n=40, start_hint=None):
    """관 모양 메쉬의 중심선: 측지 최장 경로 → 국소 무게중심으로 평활화. start_hint에 가까운 끝에서 시작"""
    V, F = mesh(name)
    # 정점 병합(조각 경계)
    q = np.round(V * 2e4).astype(np.int64); _, inv = np.unique(q, axis=0, return_inverse=True)
    inv = inv.reshape(-1)
    m = inv.max() + 1; P = np.zeros((m, 3)); cnt = np.zeros(m)
    np.add.at(P, inv, V); np.add.at(cnt, inv, 1); P /= cnt[:, None]
    F = inv[F]
    adj = defaultdict(set)
    for a, b, c in F:
        adj[a] |= {b, c}; adj[b] |= {a, c}; adj[c] |= {a, b}
    def bfs(s):
        d = {s: 0.0}; prev = {s: None}; dq = deque([s])
        # 가중치 대신 hop + 유클리드 근사: Dijkstra 간이 (작은 메쉬라 충분)
        import heapq
        h = [(0.0, s)]; d = {s: 0.0}; prev = {s: None}
        while h:
            dd, u = heapq.heappop(h)
            if dd > d[u]: continue
            for w in adj[u]:
                nd = dd + np.linalg.norm(P[u] - P[w])
                if nd < d.get(w, 1e9): d[w] = nd; prev[w] = u; heapq.heappush(h, (nd, w))
        return d, prev
    # 가장 큰 연결성분에서 시작
    s0 = 0 if start_hint is None else int(np.argmin(np.linalg.norm(P - np.array(start_hint), axis=1)))
    d, _ = bfs(s0); a = max(d, key=d.get)
    d2, prev = bfs(a); b = max(d2, key=d2.get)
    path = [b]
    while prev[path[-1]] is not None: path.append(prev[path[-1]])
    path = np.array([P[i] for i in path])
    # 등간격 재표본 후 국소 중심화
    seg = np.r_[0, np.cumsum(np.linalg.norm(np.diff(path, axis=0), axis=1))]
    ts = np.linspace(0, seg[-1], n)
    pts = np.array([np.interp(ts, seg, path[:, k]) for k in range(3)]).T
    out = []
    for i, p in enumerate(pts):
        t = pts[min(i + 1, n - 1)] - pts[max(i - 1, 0)]; t /= np.linalg.norm(t) + 1e-9
        dv = P - p; along = dv @ t
        near = P[(np.abs(along) < seg[-1] / n * 1.2) & (np.linalg.norm(dv - np.outer(along, t), axis=1) < 0.03)]
        out.append(near.mean(0) if len(near) > 3 else p)
    out = np.array(out)
    if start_hint is not None and np.linalg.norm(out[-1] - start_hint) < np.linalg.norm(out[0] - start_hint): out = out[::-1]
    return out

def along(cl, t):
    """중심선 위 비율 t(0~1) 지점"""
    seg = np.r_[0, np.cumsum(np.linalg.norm(np.diff(cl, axis=0), axis=1))]
    s = t * seg[-1]
    return np.array([np.interp(s, seg, cl[:, k]) for k in range(3)])

def extreme(name, d, frac=0.02):
    """방향 d로 가장 튀어나온 정점들의 평균"""
    V = verts(name); d = np.array(d, float); d /= np.linalg.norm(d)
    s = V @ d; k = max(3, int(len(V) * frac))
    return V[np.argsort(s)[-k:]].mean(0)

def bbox(name):
    V = verts(name); return V.min(0), V.max(0)

def centroid(name): return verts(name).mean(0)

def canal_center(vname):
    """척추뼈 척주관 중심: 정중면 근처 정점들의 z 분포에서 가장 큰 빈틈"""
    V = verts(vname); y0 = np.median(V[:, 1])
    S = V[np.abs(V[:, 0]) < 0.006]
    if len(S) < 10: S = V[np.abs(V[:, 0]) < 0.012]
    zs = np.sort(S[:, 2]); gaps = np.diff(zs); i = np.argmax(gaps)
    z = (zs[i] + zs[i + 1]) / 2; w = gaps[i]
    # 그 z 근처 고리 단면의 y 중심
    ring = V[(np.abs(V[:, 2] - z) < w) & (np.abs(V[:, 0]) < 0.03)]
    y = np.median(ring[:, 1]) if len(ring) else y0
    return np.array([0.0, y, z]), w
