"""원본 데이터(BodyParts3D·HuBMAP)에 없는 구조물을 주변 구조에 맞춰 모식적으로 만든다.
- 온목동맥 끝(데이터는 반지연골 아래에서 끊김) → 방패연골 위모서리 높이 갈림점까지 연장
- 바깥목동맥과 주요 가지(위갑상동맥, 얼굴동맥, 위턱동맥, 얕은관자동맥)
- 갑상샘 (좌우엽 + 잘록)
좌표: +x = 환자 왼쪽, +y = 위, +z = 앞 (m)
"""
import numpy as np
import trimesh
from geo import verts, find, centroid
from nerves import tube, smooth

P = lambda *a: np.array(a, float)
NEW = []      # (en, meta, V, F)
APPEND = []   # (기존 구조물 en, V, F)


def slab_center(V, y, h=0.003):
    s = V[np.abs(V[:, 1] - y) < h]
    return (s.min(0) + s.max(0)) / 2, (np.ptp(s[:, 0]) + np.ptp(s[:, 2])) / 4


def vtube(pts, r0, r1, sides=14):
    return tube([np.asarray(p, float) for p in pts], [r0, r1], sides)


def cap(V, F, pts_end, r):
    """튜브 끝을 둥근 공으로 마감"""
    s = trimesh.creation.icosphere(subdivisions=2, radius=r); s.apply_translation(pts_end)
    return np.vstack([V, s.vertices]), np.vstack([F, s.faces + len(V)])


ART = dict(sys='arterial', key='extcarotid', grp='머리·목')
TRACH = verts('trachea')
MAND = verts('mandible')
SKULL = np.concatenate([verts(n) for n in find(r'^(right|left) (temporal|parietal) bone$')])

for side, sx, sk in (('right', -1, '오른쪽 '), ('left', 1, '왼쪽 ')):
    S = lambda x, y, z: P(sx * x, y, z)
    cca = verts(f'{side} common carotid artery')
    top = cca[cca[:, 1] > cca[:, 1].max() - 0.004].mean(0)
    rc = 0.0036
    # 1) 온목동맥 연장: 데이터 끝 → 갈림점 (방패연골 위모서리 높이, 판 바깥쪽)
    B = S(0.024, 1.500, 0.010)
    V, F = vtube([top + P(0, -0.004, 0), top, (top + B) / 2 + S(0.002, 0, 0.001), B], rc, rc * 1.08)
    V, F = cap(V, F, B, rc * 0.98)
    APPEND.append((f'{side.capitalize()} common carotid artery', V, F))

    # 2) 바깥목동맥 본줄기: 속목동맥 앞안쪽 → 아래턱가지 뒤모서리 안쪽 → 관절돌기 목 뒤
    side_m = MAND[MAND[:, 0] * sx > 0.030]
    rb = side_m[(side_m[:, 1] > 1.52) & (side_m[:, 1] < 1.55)]
    R = rb[np.argmin(rb[:, 2])]                               # 아래턱가지 뒤모서리
    C = side_m[np.argmax(side_m[:, 1])]                       # 관절돌기 꼭대기
    N = C + S(-0.002, -0.013, 0.002)                          # 관절돌기 목
    e1 = S(0.022, 1.512, 0.014)
    e2 = P(R[0] - sx * 0.006, R[1], R[2] - 0.004)
    e3 = N + P(0, 0, -0.007)
    trunk = [B, e1, (e1 + e2) / 2 + S(0, 0, 0.002), e2, e3]
    V, F = vtube(trunk, 0.0026, 0.0018)
    NEW.append((f'{side.capitalize()} external carotid artery', dict(ART, ko=sk + '바깥목동맥', old='외경동맥'), V, F))

    # 3) 얕은관자동맥: 귀 앞(관절돌기 가쪽) → 관자부위
    yy = C[1] + 0.065
    sl = SKULL[(np.abs(SKULL[:, 1] - yy) < 0.004) & (SKULL[:, 0] * sx > 0)]
    lat = sl[np.argmax(sl[:, 0] * sx)] if len(sl) else C + S(0.015, 0.065, 0)
    st = [e3, P(C[0] + sx * 0.007, C[1] + 0.002, C[2] - 0.006), P(C[0] + sx * 0.010, C[1] + 0.030, C[2] - 0.003),
          P(lat[0] + sx * 0.003, yy, lat[2] + 0.004)]
    V, F = vtube(st, 0.0014, 0.0010, 10); V, F = cap(V, F, st[-1], 0.0010)
    NEW.append((f'{side.capitalize()} superficial temporal artery', dict(ART, ko=sk + '얕은관자동맥', old='천측두동맥'), V, F))

    # 4) 위턱동맥: 관절돌기 목 뒤 → 앞안쪽(관자아래우묵)
    mx = [e3, N + S(-0.006, -0.001, 0.008), N + S(-0.013, 0.003, 0.022), N + S(-0.017, 0.006, 0.034)]
    V, F = vtube(mx, 0.0016, 0.0012, 10); V, F = cap(V, F, mx[-1], 0.0012)
    NEW.append((f'{side.capitalize()} maxillary artery', dict(ART, ko=sk + '위턱동맥', old='상악동맥'), V, F))

    # 5) 얼굴동맥: 턱밑샘 위 → 아래턱뼈 아래모서리(깨물근 앞) → 입꼬리 쪽
    sg = centroid(f'{side} submandibular gland')
    body = side_m[(side_m[:, 2] > R[2] + 0.024) & (side_m[:, 2] < R[2] + 0.030)]
    notch = body[np.argmin(body[:, 1])] if len(body) else sg + P(0, 0.01, 0.01)
    f0 = trunk[1] + (trunk[2] - trunk[1]) * 0.4
    fa = [f0, sg + P(0, 0.007, -0.004), P(notch[0] + sx * 0.001, notch[1] - 0.003, notch[2]),
          P(notch[0] + sx * 0.003, notch[1] + 0.009, notch[2] + 0.006), P(notch[0] - sx * 0.001, notch[1] + 0.024, notch[2] + 0.022), P(sx * 0.024, notch[1] + 0.036, notch[2] + 0.038)]
    V, F = vtube(fa, 0.0016, 0.0011, 10); V, F = cap(V, F, fa[-1], 0.0011)
    NEW.append((f'{side.capitalize()} facial artery', dict(ART, ko=sk + '얼굴동맥', old='안면동맥'), V, F))

    # 6) 위갑상동맥: 갈림점 바로 위 → 아래안쪽 → 갑상샘 위극
    pole = S(0.0165, 1.484, 0.004)
    stp = [B + P(0, 0.004, 0.002), B + S(-0.003, 0.001, 0.005), (B + pole) / 2 + S(0, 0, 0.006), pole + P(0, 0.003, 0.003)]
    V, F = vtube(stp, 0.0011, 0.0009, 10); V, F = cap(V, F, stp[-1], 0.0009)
    NEW.append((f'{side.capitalize()} superior thyroid artery', dict(ART, ko=sk + '위갑상동맥', old='상갑상선동맥'), V, F))


# ---------------- 갑상샘 ----------------
def ellipsoid(c, ax, sub=3, taper=0.0):
    s = trimesh.creation.icosphere(subdivisions=sub, radius=1.0); V = s.vertices.copy()
    t = V[:, 1]
    k = 1 - taper * np.clip(t, 0, 1)                    # 위쪽(위극)으로 갈수록 가늘게
    V[:, 0] *= ax[0] * k; V[:, 2] *= ax[2] * k; V[:, 1] *= ax[1]
    return V + c, s.faces


def push_out(V, axis_fn, rmin):
    """기관 등 관 구조 안으로 들어간 점을 축에서 바깥으로 밀어냄"""
    V = V.copy()
    for i, v in enumerate(V):
        c, r = axis_fn(v[1])
        if c is None: continue
        d = v - c; d[1] = 0; n = np.linalg.norm(d)
        lim = r + rmin
        if n < lim:
            V[i] = c + d / (n + 1e-9) * lim; V[i][1] = v[1]
    return V


def trach_axis(y):
    s = TRACH[np.abs(TRACH[:, 1] - y) < 0.002]
    if len(s) < 6:
        s = TRACH[np.abs(TRACH[:, 1] - min(y, 1.468)) < 0.002]
    c = (s.min(0) + s.max(0)) / 2; r = (np.ptp(s[:, 0]) + np.ptp(s[:, 2])) / 4
    return c, r


def tube_axis(name):
    V = verts(name)
    def f(y):
        s = V[np.abs(V[:, 1] - y) < 0.002]
        if len(s) < 6: return None, 0
        return (s.min(0) + s.max(0)) / 2, (np.ptp(s[:, 0]) + np.ptp(s[:, 2])) / 4
    return f


TV, TF = [], []
for sx in (-1, 1):
    c0, _ = trach_axis(1.462)
    V, F = ellipsoid(P(sx * 0.0165, 1.462, c0[2] + 0.0005), (0.0062, 0.024, 0.0085), taper=0.45)
    V = push_out(V, trach_axis, 0.0008)
    for nm in ('right common carotid artery', 'left common carotid artery'):
        V = push_out(V, tube_axis(nm), 0.0006)
    TF.append(F + sum(len(v) for v in TV)); TV.append(V)
# 잘록: 2–4번 기관연골 앞
c1, r1 = trach_axis(1.453)
V, F = ellipsoid(P(0, 1.453, c1[2] + r1 + 0.0022), (0.0145, 0.0050, 0.0021), sub=3)
V = push_out(V, trach_axis, 0.0008)
TF.append(F + sum(len(v) for v in TV)); TV.append(V)
NEW.append(('Thyroid gland', dict(sys='endocrine', ko='갑상샘', old='갑상선', key='thyroid', grp=None), np.vstack(TV), np.vstack(TF)))


def build():
    return NEW, APPEND


if __name__ == '__main__':
    for en, m, V, F in NEW: print(en, len(F), V.min(0).round(3), V.max(0).round(3))
    for en, V, F in APPEND: print('append', en, len(F))
