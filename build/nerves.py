"""척수·말초신경·뇌신경 경로 모델 (BodyParts3D 기준점에서 계산한 근사 경로)
좌표: +x = 환자 왼쪽, +y = 위, +z = 앞
"""
import numpy as np
from scipy.interpolate import splprep, splev
from geo import mesh, verts, centerline, along, extreme, bbox, centroid, find

P = lambda *a: np.array(a, float)
OUT = []   # dict(en, ko, key, grp, V, F)

# ---------------- 튜브 ----------------
def smooth(pts, step=0.0022, s=0.0):
    pts = np.array(pts, float)
    keep = [0]
    for i in range(1, len(pts)):
        if np.linalg.norm(pts[i] - pts[keep[-1]]) > 0.004 or i == len(pts) - 1: keep.append(i)
    if len(keep) > 2 and np.linalg.norm(pts[keep[-1]] - pts[keep[-2]]) < 0.004: keep.pop(-2)
    pts = pts[keep]
    if len(pts) == 2: pts = np.array([pts[0], (pts[0] + pts[1]) / 2, pts[1]])
    k = min(3, len(pts) - 1)
    tck, u = splprep(pts.T, k=k, s=s * len(pts))
    L = np.linalg.norm(np.diff(pts, axis=0), axis=1).sum()
    n = max(8, int(L / step))
    uu = np.linspace(0, 1, n)
    return np.array(splev(uu, tck)).T, uu, u

def tube(pts, r, sides=8):
    C, uu, uk = smooth(pts)
    if np.isscalar(r): R = np.full(len(C), r)
    else:
        r = np.array(r, float)
        R = np.interp(uu, np.linspace(0, 1, len(r)), r) if len(r) != len(uk) else np.interp(uu, uk, r)
    T = np.gradient(C, axis=0); T /= np.linalg.norm(T, axis=1)[:, None] + 1e-12
    n0 = np.cross(T[0], [0, 0, 1.0])
    if np.linalg.norm(n0) < 1e-3: n0 = np.cross(T[0], [1.0, 0, 0])
    n0 /= np.linalg.norm(n0); N = [n0]
    for i in range(1, len(C)):
        v = N[-1] - T[i] * (N[-1] @ T[i]); v /= np.linalg.norm(v) + 1e-12; N.append(v)
    N = np.array(N); B = np.cross(T, N)
    ang = np.linspace(0, 2 * np.pi, sides, endpoint=False)
    V = (C[:, None, :] + R[:, None, None] * (np.cos(ang)[None, :, None] * N[:, None, :] + np.sin(ang)[None, :, None] * B[:, None, :])).reshape(-1, 3)
    F = []
    for i in range(len(C) - 1):
        for j in range(sides):
            a = i * sides + j; b = i * sides + (j + 1) % sides; c = a + sides; d = b + sides
            F += [(a, c, b), (b, c, d)]
    # 마개
    base = len(V); V = np.vstack([V, C[0], C[-1]])
    last = (len(C) - 1) * sides
    for j in range(sides):
        F.append((base, (j + 1) % sides, j)); F.append((base + 1, last + j, last + (j + 1) % sides))
    return V, np.array(F)

def add(en, ko, key, grp, pts, r, sides=None):
    if sides is None:
        rm = float(np.max(r))
        sides = 14 if rm >= 0.0018 else 12 if rm >= 0.0010 else 10
    V, F = tube(pts, r, sides)
    for o in OUT:
        if o['en'] == en:
            o['F'] = np.vstack([o['F'], F + len(o['V'])]); o['V'] = np.vstack([o['V'], V]); return
    OUT.append(dict(en=en, ko=ko, key=key, grp=grp, V=V, F=F))

SIDES = [('left', 1, '왼쪽 '), ('right', -1, '오른쪽 ')]

# ---------------- 척주관 ----------------
DISK = {}
for nm in find(r'^intervertebral disk'):
    V = verts(nm); DISK[nm.replace('intervertebral disk of ', '').replace('intervertebral disk', 'twelfth thoracic vertebra')] = (V[:, 1].mean(), V[:, 2].min(), V[:, 2].max(), (V[:, 0].max() - V[:, 0].min()) / 2)
ORDN = 'first second third fourth fifth sixth seventh eighth ninth tenth eleventh twelfth'.split()
def dk(reg, n):
    if reg == 'C' and n == 2: return DISK['axis']
    return DISK[f"{ORDN[n-1]} {dict(C='cervical', T='thoracic', L='lumbar')[reg]} vertebra"]
LEVELS = [('C', i) for i in range(2, 8)] + [('T', i) for i in range(1, 13)] + [('L', i) for i in range(1, 6)]
canal = [P(0, 1.585, -0.033), P(0, 1.565, -0.037), P(0, 1.548, -0.037)]
for reg, n in LEVELS:
    y, zmin, zmax, hw = dk(reg, n)
    rr = 0.009 if reg == 'C' else (0.008 if reg == 'T' else 0.011)
    canal.append(P(0, y, zmin - rr))
canal += [P(0, 0.955, -0.062), P(0, 0.92, -0.075), P(0, 0.885, -0.09)]
canal = np.array(canal)
def canal_at(y):
    i = np.argsort(-canal[:, 1]); c = canal[i]
    return P(0, y, np.interp(-y, -c[:, 1], c[:, 2]))

# ---------------- 척수 ----------------
cy = np.linspace(1.585, 1.098, 60)
cord = [canal_at(y) for y in cy]
def cord_r(y):
    if y > 1.47: return 0.0060 + 0.0012 * np.exp(-((y - 1.49) / 0.03) ** 2)   # 목팽대
    if y > 1.2: return 0.0045
    if y > 1.13: return 0.0045 + 0.0010 * np.exp(-((y - 1.16) / 0.02) ** 2)   # 허리팽대
    return 0.0045 * max(0.15, (y - 1.095) / 0.035)                            # 척수원뿔
add('Spinal cord', '척수', 'spinalcord', '중추', cord, [cord_r(y) for y in cy], 12)
add('Filum terminale', '종말끈', 'cauda', '중추', [canal_at(y) for y in np.linspace(1.10, 0.90, 8)], 0.0007, 6)

# ---------------- 척수신경 뿌리 ----------------
EXIT = {}   # (side, 'C5') -> 앞가지 시작점
def root_origin(name):
    reg, n = name[0], int(name[1:])
    if reg == 'C': return 1.575 - (n - 1) * 0.0155
    if reg == 'T': return 1.44 - (n - 1) * 0.0215
    if reg == 'L': return 1.172 - (n - 1) * 0.009
    return 1.127 - (n - 1) * 0.006
def foramen_y(name):
    reg, n = name[0], int(name[1:])
    if reg == 'C':
        if n == 1: return 1.562
        if n == 2: return 1.540
        return dk('C', n - 1)[0]
    if reg in 'TL': return dk(reg, n)[0]
    return [0.958, 0.928, 0.900, 0.876, 0.86][n - 1]
NAMES = [f'C{i}' for i in range(1, 9)] + [f'T{i}' for i in range(1, 13)] + [f'L{i}' for i in range(1, 6)] + [f'S{i}' for i in range(1, 6)]
for side, sx, sk in SIDES:
    for nm in NAMES:
        reg = nm[0]; y0 = root_origin(nm); yf = foramen_y(nm)
        c0 = canal_at(y0); cf = canal_at(yf)
        r0 = cord_r(y0) if y0 > 1.098 else 0.003
        if reg == 'S':
            fx = 0.026 - (int(nm[1:]) - 1) * 0.003
            pts = [c0 + P(sx * r0, 0, 0), canal_at(y0 - 0.04) + P(sx * 0.004, 0, 0), canal_at(yf + 0.02) + P(sx * 0.006, 0, 0.004),
                   P(sx * fx, yf, -0.045 + 0.004 * int(nm[1:])), P(sx * (fx + 0.01), yf - 0.006, -0.035 + 0.004 * int(nm[1:]))]
            out = pts[-1]
        else:
            lat = {'C': 0.022, 'T': 0.020, 'L': 0.026}[reg]
            pts = [c0 + P(sx * r0, 0, 0)]
            if y0 - yf > 0.015:
                pts.append(canal_at((y0 + yf) / 2 + 0.01) + P(sx * (r0 + 0.002), 0, 0))
                pts.append(cf + P(sx * 0.007, 0.006, 0))
            pts.append(cf + P(sx * lat, -0.002, 0.004))
            out = cf + P(sx * (lat + 0.012), -0.004, 0.012 if reg != 'T' else 0.004)
            pts.append(out)
        EXIT[(side, nm)] = out
        rr = 0.0013 if reg == 'T' else (0.0011 if nm in ('C1', 'S5') else 0.0019)
        add(f'{side.capitalize()} {nm} spinal nerve', f'{sk}{nm} 척수신경', 'spinalroot',
            '척수신경 뿌리', pts, rr, 6)

# ---------------- 팔신경얼기와 종말가지 ----------------
for side, sx, sk in SIDES:
    S = lambda x, y, z: P(sx * x, y, z)
    ax = centerline(f'{side} axillary artery', 30, S(0.07, 1.42, 0))
    br = centerline(f'{side} brachial artery', 30, S(0.15, 1.35, 0))
    ra = centerline(f'{side} radial artery', 30, S(0.22, 1.1, 0))
    ul = centerline(f'{side} ulnar artery', 30, S(0.22, 1.1, 0))
    H = verts(f'{side} humerus'); lo = H.min(0); hi = H.max(0)
    dist = H[H[:, 1] < lo[1] + 0.05]
    med_epi = dist[np.argmin(np.abs(dist[:, 0]))]; lat_epi = dist[np.argmax(np.abs(dist[:, 0]))]
    def hum_at(y):  # 위팔뼈 몸통 단면 중심
        sl = H[np.abs(H[:, 1] - y) < 0.01]; return sl.mean(0), sl
    lat = lambda p, d: p + P(sx * d, 0, 0)
    grp = '팔신경'
    # 뿌리 → 줄기
    upper = S(0.058, 1.445, -0.014); middle = S(0.062, 1.432, -0.018); lower = S(0.060, 1.420, -0.022)
    for nm, tgt in [('C5', upper), ('C6', upper), ('C7', middle), ('C8', lower), ('T1', lower)]:
        e = EXIT[(side, nm)]
        add(f'{side.capitalize()} brachial plexus', f'{sk}팔신경얼기', 'brachialplexus', grp, [e, (e + tgt) / 2 + P(0, 0, -0.004), tgt], 0.0024)
    a1, a2, a3 = along(ax, 0.25), along(ax, 0.55), along(ax, 0.85)
    LC = [upper, S(0.085, 1.43, -0.010), a1 + P(0, 0.008, 0.002), a2 + P(0, 0.009, 0.004)]
    PC = [middle, S(0.085, 1.425, -0.018), a1 + P(0, 0, -0.010), a2 + P(0, 0, -0.010)]
    MC = [lower, S(0.082, 1.415, -0.016), a1 + P(0, -0.009, -0.002), a2 + P(0, -0.009, 0.0)]
    for pts in (LC, PC, MC): add(f'{side.capitalize()} brachial plexus', f'{sk}팔신경얼기', 'brachialplexus', grp, pts, 0.0026)
    # 근육피부신경
    cb = centroid(f'{side} coracobrachialis'); bm = along(br, 0.55)
    add(f'{side.capitalize()} musculocutaneous nerve', f'{sk}근육피부신경', 'musculocutaneous', grp,
        [LC[-1], cb + P(0, 0, 0.004), lat(bm, 0.014) + P(0, 0, 0.012), lat(along(br, 0.97), 0.020) + P(0, 0, 0.012),
         lat(along(ra, 0.5), 0.010) + P(0, 0, 0.004), lat(along(ra, 0.95), 0.008)], [0.0018, 0.0018, 0.0016, 0.0012, 0.0009, 0.0007])
    # 정중신경
    med_join = a3 + P(0, 0, 0.007)
    add(f'{side.capitalize()} median nerve', f'{sk}정중신경', 'median', grp, [LC[-1], med_join], 0.0018)
    add(f'{side.capitalize()} median nerve', f'{sk}정중신경', 'median', grp, [MC[-1], med_join], 0.0018)
    fm = lambda t: (along(ra, t) + along(ul, t)) / 2
    wrist = fm(0.99) + P(0, 0.0, 0.006)
    palm = S(0.262, 0.855, 0.035)
    add(f'{side.capitalize()} median nerve', f'{sk}정중신경', 'median', grp,
        [med_join, lat(along(br, 0.3), 0.004) + P(0, 0, 0.006), lat(along(br, 0.7), -0.006) + P(0, 0, 0.004), lat(along(br, 0.98), -0.008) + P(0, 0, 0.003),
         fm(0.3) + P(0, 0, -0.004), fm(0.7) + P(0, 0, 0.0), wrist, palm], 0.0022)
    for fing, r in [('thumb', 0.0011), ('index finger', 0.0011), ('middle finger', 0.0011)]:
        c = centroid(f'proximal phalanx of {side} {fing}')
        add(f'{side.capitalize()} median nerve', f'{sk}정중신경', 'median', grp, [palm, (palm + c) / 2 + P(0, 0, 0.004), c + P(0, 0, 0.008)], r, 6)
    # 자신경
    pis = centroid(f'{side} pisiform')
    upalm = S(0.236, 0.845, 0.034)
    add(f'{side.capitalize()} ulnar nerve', f'{sk}자신경', 'ulnar', grp,
        [MC[-1], a3 + P(0, -0.008, 0), lat(along(br, 0.35), -0.012) + P(0, 0, -0.002), lat(along(br, 0.7), -0.014) + P(0, 0, -0.012),
         med_epi + P(0, 0.012, -0.010), med_epi + P(sx * 0.002, -0.004, -0.010), lat(along(ul, 0.25), -0.008) + P(0, 0, -0.004),
         lat(along(ul, 0.7), -0.005) + P(0, 0, 0.0), pis + P(sx * 0.004, 0.006, 0.006), upalm], 0.0021)
    for fing in ('ring finger', 'little finger'):
        c = centroid(f'proximal phalanx of {side} {fing}')
        add(f'{side.capitalize()} ulnar nerve', f'{sk}자신경', 'ulnar', grp, [upalm, (upalm + c) / 2 + P(0, 0, 0.004), c + P(0, 0, 0.008)], 0.0011, 6)
    # 노신경
    c25, s25 = hum_at(1.25); c19, _ = hum_at(1.19)
    sg = P(c25[0], 1.25, s25[:, 2].min() - 0.005)
    elbow_l = lat_epi + P(-sx * 0.012, 0.03, 0.022)
    split = lat_epi + P(-sx * 0.010, -0.004, 0.022)
    add(f'{side.capitalize()} radial nerve', f'{sk}노신경', 'radialn', grp,
        [PC[-1], a3 + P(0, -0.004, -0.010), lat(along(br, 0.15), -0.004) + P(0, 0, -0.014), P(c25[0] - sx * 0.004, 1.29, s25[:, 2].min() - 0.002), sg,
         P(c19[0] + sx * 0.012, 1.19, c19[2] - 0.004), elbow_l, split], 0.0024)
    sup = centroid(f'{side} supinator')
    add(f'{side.capitalize()} radial nerve', f'{sk}노신경', 'radialn', grp,
        [split, lat(along(ra, 0.3), 0.008), lat(along(ra, 0.75), 0.006) + P(0, 0, -0.004), along(ra, 0.97) + P(sx * 0.006, 0, -0.014),
         S(0.29, 0.85, 0.020)], 0.0013)   # 얕은가지
    R_ = verts(f'{side} radius'); U_ = verts(f'{side} ulna')
    dors = (R_[R_[:, 1] < R_[:, 1].min() + 0.02].mean(0) + U_[U_[:, 1] < U_[:, 1].min() + 0.02].mean(0)) / 2 + P(0, 0.01, -0.012)
    add(f'{side.capitalize()} radial nerve', f'{sk}노신경', 'radialn', grp,
        [split, sup + P(0, 0, -0.004), sup + P(-sx * 0.004, -0.04, -0.010), P(dors[0], 0.98, dors[2] - 0.002), dors], 0.0014)   # 깊은가지(뒤뼈사이신경)
    # 겨드랑신경
    c36, s36 = hum_at(1.37)
    add(f'{side.capitalize()} axillary nerve', f'{sk}겨드랑신경', 'axillaryn', grp,
        [PC[-1], P(c36[0] - sx * 0.008, 1.372, s36[:, 2].min() - 0.006), P(c36[0] + sx * 0.008, 1.368, s36[:, 2].min() - 0.002),
         P(s36[:, 0].max() * 1 if sx > 0 else s36[:, 0].min(), 1.366, c36[2]) + P(sx * 0.010, 0, 0), P(c36[0] + sx * 0.012, 1.364, s36[:, 2].max() + 0.006)], 0.0018)
    # 가로막신경
    sa = centroid(f'{side} scalenus anterior')
    dV = verts('diaphragm'); dS = dV[(dV[:, 0] * sx > 0.05) & (dV[:, 0] * sx < 0.09)]; dtop = dS[np.argmax(dS[:, 1])]
    if sx > 0:
        hv = verts('wall of ventricle'); mid = P(hv[:, 0].max() + 0.006, 1.30, 0.03)
    else:
        hv = verts('wall of right atrium'); mid = P(hv[:, 0].min() - 0.006, 1.31, 0.03)
    add(f'{side.capitalize()} phrenic nerve', f'{sk}가로막신경', 'phrenic', '가슴·목 신경',
        [EXIT[(side, 'C4')], sa + P(0, 0.02, 0.012), sa + P(0, -0.02, 0.012), S(0.03, 1.40, 0.012), S(0.03, 1.37, 0.015), mid, dtop + P(0, 0.004, 0)], 0.0011)

# ---------------- 미주신경 · 되돌이후두신경 ----------------
for side, sx, sk in SIDES:
    S = lambda x, y, z: P(sx * x, y, z)
    ic = centerline(f'{side} internal carotid artery', 20, S(0.02, 1.5, 0))
    cc = centerline(f'{side} common carotid artery', 20, S(0.02, 1.38, 0))
    ij = centerline(f'{side} internal jugular vein', 12, S(0.02, 1.41, 0)) if find(f'^{side} internal jugular vein$') else None
    top = S(0.012, 1.56, -0.030)
    neck = [top, S(0.030, 1.545, -0.025), along(ic, 0.1) + P(sx * 0.006, 0, -0.010), along(ic, 0.0) + P(sx * 0.006, -0.01, -0.010),
            along(cc, 0.85) + P(sx * 0.007, 0, -0.008), along(cc, 0.4) + P(sx * 0.007, 0, -0.007), along(cc, 0.05) + P(sx * 0.004, 0, -0.003)]
    es = verts('esophagus')
    if sx < 0:
        sc = centerline('right subclavian artery', 20, P(-0.01, 1.39, 0))
        hook = along(sc, 0.2)
        thor = [hook + P(-0.004, 0.004, 0.008), P(-0.018, 1.37, -0.010), P(-0.020, 1.33, -0.028), P(-0.012, 1.26, -0.030), P(-0.006, 1.20, -0.030),
                P(0.010, 1.17, -0.020), P(0.030, 1.165, -0.005)]
        rln = [hook + P(-0.004, 0.004, 0.008), hook + P(0.0, -0.008, 0.0), hook + P(0.004, -0.004, -0.010), P(-0.012, 1.40, -0.012), P(-0.011, 1.45, -0.008), P(-0.010, 1.47, -0.004)]
    else:
        arch = centerline('arch of aorta', 20, P(0.0, 1.37, 0.03))
        hook = along(arch, 0.45) + P(0.006, 0.0, 0.006)
        thor = [hook, P(0.022, 1.36, -0.012), P(0.020, 1.32, -0.030), P(0.010, 1.26, -0.012), P(0.008, 1.20, -0.006), P(0.025, 1.17, 0.01), P(0.05, 1.18, 0.03)]
        rln = [hook, hook + P(0.0, -0.014, -0.006), hook + P(-0.010, -0.012, -0.018), P(0.011, 1.38, -0.016), P(0.011, 1.43, -0.010), P(0.010, 1.47, -0.004)]
    add(f'{side.capitalize()} vagus nerve', f'{sk}미주신경 (X)', 'vagus', '뇌신경', neck + thor, [0.0019] * 7 + [0.0017] * len(thor))
    add(f'{side.capitalize()} recurrent laryngeal nerve', f'{sk}되돌이후두신경', 'rln', '뇌신경', rln, 0.0009, 6)

# ---------------- 갈비사이신경 · 교감신경줄기 ----------------
ORDR = ORDN
for side, sx, sk in SIDES:
    for k in range(1, 13):
        nm = f'{side} {ORDR[k-1]} rib'
        try: cl = centerline(nm, 30, P(sx * 0.02, 1.3, -0.06))
        except KeyError: continue
        e = EXIT[(side, f'T{k}')]
        if np.linalg.norm(cl[-1] - e) < np.linalg.norm(cl[0] - e): cl = cl[::-1]
        pts = [e] + [p + P(0, -0.007, 0) + (P(0, 0, 0) if i < 2 else (np.array([0, 0, 0.0]))) for i, p in enumerate(cl[1:]) if True]
        # 갈비뼈 안쪽면 쪽으로 약간
        ctr = cl.mean(0)
        pts = [e] + [p + P(0, -0.007, 0) + 0.06 * (ctr - p) * P(1, 0, 1) for p in cl[2:]]
        if k == 12: pts += [pts[-1] + P(sx * 0.01, -0.05, 0.05), P(sx * 0.06, 0.98, 0.09)]
        elif k >= 7: pts += [pts[-1] + P(-sx * 0.02, -0.04, 0.03)]
        add(f'{side.capitalize()} {"subcostal" if k == 12 else "intercostal"} nerve T{k}', f'{sk}{"갈비밑신경" if k == 12 else "갈비사이신경"} (T{k})',
            'intercostal', '가슴·목 신경', pts, 0.0011, 6)
    # 교감신경줄기
    tr = []; rr = []
    for y in np.linspace(1.535, 1.46, 4): tr.append(P(sx * 0.016, y, -0.008)); rr.append(0.0016 if y > 1.52 else 0.0012)
    for reg, n in [('C', 7)] + [('T', i) for i in range(1, 13)] + [('L', i) for i in range(1, 6)]:
        y, zmin, zmax, hw = dk(reg, n)
        if reg == 'C': tr.append(P(sx * (hw + 0.004), y, (zmin + zmax) / 2)); rr.append(0.0022)   # 별신경절
        elif reg == 'T': tr.append(P(sx * (hw + 0.006), y, zmin + 0.25 * (zmax - zmin))); rr.append(0.0016 if n % 1 == 0 else 0.0012)
        else: tr.append(P(sx * (hw * 0.85), y, zmax - 0.006)); rr.append(0.0014)
    for y, x in [(0.955, 0.02), (0.92, 0.016), (0.89, 0.01), (0.865, 0.003)]: tr.append(P(sx * x, y, -0.035 - (0.955 - y) * 0.6)); rr.append(0.0011)
    add(f'{side.capitalize()} sympathetic trunk', f'{sk}교감신경줄기', 'sympathetic', '자율신경', tr, rr, 6)

# ---------------- 허리·엉치신경얼기 ----------------
for side, sx, sk in SIDES:
    S = lambda x, y, z: P(sx * x, y, z)
    fa = centerline(f'{side} femoral artery', 30, S(0.05, 0.9, 0.02))
    pa = centerline(f'{side} popliteal artery', 20, S(0.06, 0.56, 0))
    pt = centerline(f'{side} posterior tibial artery', 20, S(0.08, 0.37, 0))
    at = centerline(f'{side} anterior tibial artery', 20, S(0.09, 0.39, 0))
    ps = verts(f'{side} psoas major')
    def psoas_lat(y):
        sl = ps[np.abs(ps[:, 1] - y) < 0.01]; return sl[np.argmax(sl[:, 0] * sx)] if len(sl) else None
    def psoas_med(y):
        sl = ps[np.abs(ps[:, 1] - y) < 0.01]; return sl[np.argmin(sl[:, 0] * sx)] if len(sl) else None
    grp = '다리신경'
    # 넙다리신경
    fn_top = psoas_lat(1.02) + P(sx * 0.002, 0, -0.004)
    fn_mid = psoas_lat(0.95) + P(sx * 0.002, 0, 0.004)
    fstart = along(fa, 0.02) + P(sx * 0.013, 0.004, 0.0)
    for nm in ('L2', 'L3', 'L4'):
        e = EXIT[(side, nm)]; add(f'{side.capitalize()} femoral nerve', f'{sk}넙다리신경', 'femoraln', grp, [e, (e + fn_top) / 2 + P(sx * 0.006, 0, 0.004), fn_top], 0.0018)
    add(f'{side.capitalize()} femoral nerve', f'{sk}넙다리신경', 'femoraln', grp, [fn_top, fn_mid, fstart, along(fa, 0.08) + P(sx * 0.014, 0, 0.003)], 0.0032)
    fb = along(fa, 0.08) + P(sx * 0.014, 0, 0.003)
    for mus in (f'{side} rectus femoris', f'{side} vastus lateralis', f'{side} vastus medialis', f'{side} sartorius'):
        c = centroid(mus); c[1] = max(c[1], 0.66)
        add(f'{side.capitalize()} femoral nerve', f'{sk}넙다리신경', 'femoraln', grp, [fb, (fb + c) / 2 + P(0, 0, 0.012), c + P(0, 0, 0.012)], 0.0011, 6)
    T = verts(f'{side} tibia'); tmed = T[T[:, 1] > T[:, 1].max() - 0.04]; tmed = tmed[np.argmin(tmed[:, 0] * sx)]
    mm = T[T[:, 1] < T[:, 1].min() + 0.03]; mm = mm[np.argmin(mm[:, 0] * sx)]
    add(f'{side.capitalize()} saphenous nerve', f'{sk}두렁신경', 'saphenousn', grp,
        [fb, along(fa, 0.4) + P(-sx * 0.002, 0, 0.008), along(fa, 0.8) + P(-sx * 0.006, 0, 0.006), tmed + P(-sx * 0.010, 0.01, -0.004),
         P(tmed[0] - sx * 0.008, 0.25, -0.01), mm + P(-sx * 0.008, 0.01, 0.012)], 0.0009, 6)
    # 폐쇄신경
    ob = centroid(f'{side} obturator externus'); ob_can = P(ob[0] * 0.8, 0.878, ob[2] + 0.012)
    o1 = psoas_med(1.0) + P(-sx * 0.002, 0, 0.0)
    for nm in ('L2', 'L3', 'L4'):
        e = EXIT[(side, nm)]; add(f'{side.capitalize()} obturator nerve', f'{sk}폐쇄신경', 'obturatorn', grp, [e, (e + o1) / 2, o1], 0.0014)
    adl = centroid(f'{side} adductor longus'); adb = centroid(f'{side} adductor brevis')
    add(f'{side.capitalize()} obturator nerve', f'{sk}폐쇄신경', 'obturatorn', grp,
        [o1, S(abs(o1[0]) + 0.01, 0.96, -0.02), S(abs(ob_can[0]) + 0.005, 0.90, 0.005), ob_can, (ob_can + adb) / 2 + P(0, 0, 0.012), adl + P(0, 0, -0.004)], 0.0017)
    # 가쪽넙다리피부신경
    hb = verts(f'{side} hip bone'); asis = extreme(f'{side} hip bone', [sx * 0.4, 0.3, 1.0], 0.005)
    il = centroid(f'{side} iliacus')
    add(f'{side.capitalize()} lateral femoral cutaneous nerve', f'{sk}가쪽넙다리피부신경', 'lfcn', grp,
        [EXIT[(side, 'L2')], psoas_lat(1.06) + P(sx * 0.004, 0, 0), il + P(0, 0.02, 0.012), asis + P(-sx * 0.010, -0.012, 0.006),
         asis + P(sx * 0.005, -0.12, 0.012), asis + P(sx * 0.012, -0.30, 0.01)], 0.0009, 6)
    # 궁둥신경
    pir = verts(f'{side} piriformis'); pl = pir[pir[:, 1] < pir[:, 1].min() + 0.012]; below = pl.mean(0) + P(0, -0.012, -0.004)
    F_ = verts(f'{side} femur'); gt = F_[F_[:, 1] > 0.86]; gt = gt[np.argmax(gt[:, 0] * sx)]
    isch = extreme(f'{side} hip bone', [0, -1, -0.6], 0.01)
    gate = (gt + isch) / 2 + P(0, -0.01, -0.012)
    def fem_back(y):
        sl = F_[np.abs(F_[:, 1] - y) < 0.01]; return P(sl[:, 0].mean(), y, sl[:, 2].min() - 0.016)
    lstrunk = P(sx * 0.03, 0.97, -0.05)
    for nm in ('L4', 'L5'): add(f'{side.capitalize()} sciatic nerve', f'{sk}궁둥신경', 'sciatic', grp, [EXIT[(side, nm)], (EXIT[(side, nm)] + lstrunk) / 2 + P(0, 0, 0.01), lstrunk], 0.0026)
    conf = below + P(-sx * 0.02, 0.012, 0.022)
    add(f'{side.capitalize()} sciatic nerve', f'{sk}궁둥신경', 'sciatic', grp, [lstrunk, P(sx * 0.04, 0.93, -0.055), conf], 0.0034)
    for nm in ('S1', 'S2', 'S3'): add(f'{side.capitalize()} sciatic nerve', f'{sk}궁둥신경', 'sciatic', grp, [EXIT[(side, nm)], (EXIT[(side, nm)] + conf) / 2, conf], 0.0024)
    bif = along(pa, 0.05) + P(0, 0.02, -0.014)
    add(f'{side.capitalize()} sciatic nerve', f'{sk}궁둥신경', 'sciatic', grp,
        [conf, below, gate, fem_back(0.78), fem_back(0.68), fem_back(0.6) + P(0, 0, 0.002), bif], 0.0046, 10)
    # 정강신경
    calc = centroid(f'{side} calcaneus'); m1 = centroid(f'{side} first metatarsal bone'); m5 = centroid(f'{side} fifth metatarsal bone')
    tarsal = mm + P(sx * 0.004, -0.008, -0.014)
    add(f'{side.capitalize()} tibial nerve', f'{sk}정강신경', 'tibialn', grp,
        [bif, along(pa, 0.4) + P(0, 0, -0.010), along(pa, 0.9) + P(0, 0, -0.008), along(pt, 0.3) + P(0, 0, -0.006),
         along(pt, 0.75) + P(sx * 0.002, 0, -0.006), tarsal], 0.0032)
    plant = calc + P(0, -0.01, 0.03)
    add(f'{side.capitalize()} tibial nerve', f'{sk}정강신경', 'tibialn', grp, [tarsal, tarsal + P(0, -0.02, 0.012), plant + P(-sx * 0.012, 0, 0.02), m1 + P(0, -0.012, 0.0)], 0.0016)  # 안쪽발바닥
    add(f'{side.capitalize()} tibial nerve', f'{sk}정강신경', 'tibialn', grp, [tarsal, tarsal + P(0, -0.02, 0.012), plant + P(sx * 0.010, 0, 0.02), m5 + P(0, -0.008, 0.0)], 0.0013)  # 가쪽발바닥
    # 온종아리신경
    Fi = verts(f'{side} fibula'); fh = Fi[Fi[:, 1] > Fi[:, 1].max() - 0.02].mean(0); fneck = Fi[np.abs(Fi[:, 1] - (Fi[:, 1].max() - 0.035)) < 0.006].mean(0)
    add(f'{side.capitalize()} common fibular nerve', f'{sk}온종아리신경', 'fibularn', grp,
        [bif, bif + P(sx * 0.018, -0.04, 0.002), fh + P(sx * 0.008, 0.01, -0.012), fneck + P(sx * 0.010, 0, -0.002), fneck + P(sx * 0.006, -0.006, 0.012)], 0.0026)
    fsplit = fneck + P(sx * 0.006, -0.006, 0.012)
    dp = centerline(f'{side} dorsalis pedis artery', 10, S(0.07, 0.09, 0))
    add(f'{side.capitalize()} common fibular nerve', f'{sk}온종아리신경', 'fibularn', grp,
        [fsplit, along(at, 0.15) + P(sx * 0.004, 0, 0.004), along(at, 0.6) + P(sx * 0.004, 0, 0.004), along(at, 0.98) + P(sx * 0.003, 0, 0.004), along(dp, 0.6) + P(0, 0.004, 0.004), along(dp, 1.0) + P(0, 0.004, 0.008)], 0.0014)  # 깊은종아리신경
    fl = verts(f'{side} fibularis longus')
    def fl_at(y):
        sl = fl[np.abs(fl[:, 1] - y) < 0.01]; return sl.mean(0) + P(0, 0, 0.004) if len(sl) else None
    add(f'{side.capitalize()} common fibular nerve', f'{sk}온종아리신경', 'fibularn', grp,
        [fsplit, fl_at(0.33), fl_at(0.22), fl_at(0.12) + P(0, 0, 0.012), (m1 + m5) / 2 + P(0, 0.02, 0.0)], 0.0013)  # 얕은종아리신경
    # 위·아래볼기신경, 음부신경
    gm = centroid(f'{side} gluteus medius'); gx = centroid(f'{side} gluteus maximus')
    above = pir[pir[:, 1] > pir[:, 1].max() - 0.012].mean(0) + P(0, 0.006, -0.006)
    add(f'{side.capitalize()} superior gluteal nerve', f'{sk}위볼기신경', 'gluteal', grp, [lstrunk, above, (above + gm) / 2 + P(0, 0, -0.01), gm], 0.0015)
    add(f'{side.capitalize()} inferior gluteal nerve', f'{sk}아래볼기신경', 'gluteal', grp, [conf, below + P(sx * -0.006, -0.002, -0.006), gx + P(0, 0, 0.01)], 0.0015)
    add(f'{side.capitalize()} pudendal nerve', f'{sk}음부신경', 'pudendal', grp,
        [EXIT[(side, 'S3')], below + P(-sx * 0.02, -0.004, -0.004), isch + P(-sx * 0.012, 0.05, 0.004), S(0.025, 0.86, 0.0), S(0.01, 0.84, 0.03)], 0.0012, 6)

# ---------------- 뇌신경 ----------------
for side, sx, sk in SIDES:
    S = lambda x, y, z: P(sx * x, y, z)
    tb = verts(f'{side} temporal bone')
    # 삼차신경
    gang = S(0.020, 1.594, -0.004)
    add(f'{side.capitalize()} trigeminal nerve', f'{sk}삼차신경 (V)', 'cn5', '뇌신경', [S(0.016, 1.594, -0.020), S(0.018, 1.594, -0.012), gang], 0.0022)
    oph = find(f'^{side} ophthalmic nerve$')
    if oph:
        on = verts(oph[0]); o0 = on[np.argmin(on[:, 2])]
        add(f'{side.capitalize()} trigeminal nerve', f'{sk}삼차신경 (V)', 'cn5', '뇌신경', [gang, (gang + o0) / 2, o0], 0.0012, 6)
    mx = verts(f'{side} maxilla'); infra = P(sx * 0.024, 1.585, mx[:, 2].max() - 0.010)
    add(f'{side.capitalize()} trigeminal nerve', f'{sk}삼차신경 (V)', 'cn5', '뇌신경', [gang, S(0.022, 1.588, 0.012), S(0.022, 1.588, 0.030), infra], 0.0013, 6)   # V2
    mand = verts('mandible')
    def mand_inner(z):
        sl = mand[(np.abs(mand[:, 2] - z) < 0.006) & (mand[:, 0] * sx > 0)]
        return P(sx * (np.abs(sl[:, 0]).mean()), sl[:, 1].mean(), z) if len(sl) else None
    ramus = mand_inner(0.0); body = mand_inner(0.035); ment = mand_inner(0.058)
    v3 = [gang, S(0.026, 1.578, -0.004), ramus + P(-sx * 0.004, 0.01, 0.002), ramus + P(-sx * 0.003, -0.006, 0.0), body + P(-sx * 0.002, -0.004, 0), ment + P(sx * 0.004, 0, 0)]
    add(f'{side.capitalize()} trigeminal nerve', f'{sk}삼차신경 (V)', 'cn5', '뇌신경', v3, 0.0013, 6)   # V3 · 아래이틀신경
    tg = centroid('tongue') + P(sx * 0.010, 0.004, 0.006)
    add(f'{side.capitalize()} trigeminal nerve', f'{sk}삼차신경 (V)', 'cn5', '뇌신경', [v3[1], ramus + P(-sx * 0.008, 0.005, 0.006), S(0.018, 1.53, 0.03), tg], 0.0010, 6)  # 혀신경
    # 갓돌림신경
    lr = centroid(f'{side} lateral rectus')
    add(f'{side.capitalize()} abducens nerve', f'{sk}갓돌림신경 (VI)', 'cn6', '뇌신경', [S(0.004, 1.583, -0.010), S(0.007, 1.598, -0.004), S(0.014, 1.598, 0.010), lr + P(-sx * 0.004, 0, -0.012)], 0.0008, 6)
    # 얼굴신경 · 속귀신경
    iam = S(0.030, 1.586, -0.018); smf = S(0.048, 1.555, -0.020); parot = S(0.052, 1.545, -0.004)
    add(f'{side.capitalize()} facial nerve', f'{sk}얼굴신경 (VII)', 'cn7', '뇌신경', [S(0.014, 1.583, -0.020), iam, S(0.040, 1.582, -0.016), S(0.046, 1.575, -0.024), smf, parot], 0.0013, 6)
    for tgt in [S(0.064, 1.62, 0.030), S(0.058, 1.585, 0.050), S(0.050, 1.565, 0.062), S(0.042, 1.525, 0.055), S(0.040, 1.49, 0.03)]:
        add(f'{side.capitalize()} facial nerve', f'{sk}얼굴신경 (VII)', 'cn7', '뇌신경', [parot, (parot + tgt) / 2 + P(sx * 0.006, 0, 0), tgt], 0.0008, 6)
    add(f'{side.capitalize()} vestibulocochlear nerve', f'{sk}속귀신경 (VIII)', 'cn8', '뇌신경', [S(0.014, 1.580, -0.022), S(0.024, 1.583, -0.020), S(0.034, 1.585, -0.018)], 0.0014, 6)
    # 혀인두신경
    add(f'{side.capitalize()} glossopharyngeal nerve', f'{sk}혀인두신경 (IX)', 'cn9', '뇌신경', [S(0.011, 1.566, -0.026), S(0.026, 1.556, -0.028), S(0.030, 1.53, -0.012), S(0.020, 1.515, 0.004), S(0.012, 1.52, 0.02)], 0.0009, 6)
    # 더부신경
    scm = verts(f'{side} sternocleidomastoid'); scu = scm[(scm[:, 1] > 1.50) & (scm[:, 1] < 1.53)].mean(0)
    tz = verts(f'descending part of {side} trapezius'); tzu = tz[(tz[:, 1] > 1.43) & (tz[:, 1] < 1.46)]; tzu = tzu[np.argmax(tzu[:, 0] * sx)] if len(tzu) else tz.mean(0)
    add(f'{side.capitalize()} accessory nerve', f'{sk}더부신경 (XI)', 'cn11', '뇌신경', [S(0.010, 1.555, -0.032), S(0.028, 1.553, -0.028), S(0.036, 1.535, -0.020), scu + P(-sx * 0.004, 0, -0.008), scu + P(sx * 0.008, -0.04, -0.03), tzu + P(-sx * 0.006, 0, 0.004)], 0.0010, 6)
    # 혀밑신경
    gg = centroid(f'{side} genioglossus')
    add(f'{side.capitalize()} hypoglossal nerve', f'{sk}혀밑신경 (XII)', 'cn12', '뇌신경', [S(0.006, 1.560, -0.022), S(0.018, 1.553, -0.032), S(0.030, 1.535, -0.016), S(0.026, 1.515, 0.006), S(0.016, 1.512, 0.022), gg + P(sx * 0.006, 0, 0)], 0.0011, 6)
    # 후각망울·후각로
    eth = verts('ethmoid'); cr = P(sx * 0.005, eth[:, 1].max() + 0.004, eth[:, 2].max() - 0.012)
    add(f'{side.capitalize()} olfactory bulb and tract', f'{sk}후각망울·후각로 (I)', 'cn1', '뇌신경', [cr, cr + P(sx * 0.004, 0.003, -0.018), S(0.014, 1.615, 0.004)], [0.0026, 0.0014, 0.0012], 8)
    # 눈돌림신경 · 도르래신경 (뇌줄기 → 눈확 내 가지)
    for en_, ko_, key_, start, pat in [('oculomotor nerve', '눈돌림신경 (III)', 'cn3', S(0.004, 1.612, -0.008), f'branch of {side} oculomotor nerve'),
                                      ('trochlear nerve', '도르래신경 (IV)', 'cn4', S(0.010, 1.612, -0.030), f'^{side} trochlear nerve$')]:
        ms = find(pat)
        tgtv = np.concatenate([verts(m) for m in ms]) if ms else None
        tgt = tgtv[np.argmin(tgtv[:, 2])] if tgtv is not None else S(0.015, 1.60, 0.02)
        mid = S(0.014, 1.604, 0.0) if key_ == 'cn3' else S(0.020, 1.606, -0.012)
        add(f'{side.capitalize()} {en_}', f'{sk}{ko_}', key_, '뇌신경', [start, mid, tgt], 0.0012 if key_ == 'cn3' else 0.0007, 6)

def build():
    return OUT

if __name__ == '__main__':
    print(len(OUT), sum(len(o['F']) for o in OUT))
    for o in OUT: print(o['en'], len(o['F']))
