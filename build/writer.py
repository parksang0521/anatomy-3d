"""meshopt 인코딩으로 계통별 바이너리 작성"""
import json, gzip, subprocess, os, tempfile
import numpy as np

def prep(qp, I):
    """첫 사용 순서로 정점 재배열(압축 효율), 사용 안 하는 정점 제거"""
    u, first = np.unique(I, return_index=True)
    ordered = u[np.argsort(first)]
    remap = np.full(len(qp), -1, np.int64); remap[ordered] = np.arange(len(ordered))
    q4 = np.zeros((len(ordered), 4), '<u2'); q4[:, :3] = qp[ordered]
    return q4, remap[I].astype('<u4')

def emit(records, OUT):
    """records: [dict(file, qp(n,3 uint16), I(uint32), man(dict))] → man에 pe/pl/ie/il/vc/ic 기록, {file: gz크기} 반환"""
    byfile = {}
    for r in records: byfile.setdefault(r['file'], []).append(r)
    sizes = {}
    for fname, recs in byfile.items():
        hdr = []; raw = bytearray()
        for r in recs:
            q4, I = prep(r['qp'], r['I'])
            r['man']['vc'] = len(q4); r['man']['ic'] = len(I)
            po = len(raw); raw += q4.tobytes(); io = len(raw); raw += I.tobytes()
            hdr.append(dict(vc=len(q4), ic=len(I), poff=po, ioff=io))
        td = tempfile.mkdtemp()
        hp, rp, op, oh = [os.path.join(td, x) for x in ('h.json', 'r.bin', 'o.bin', 'o.json')]
        json.dump(hdr, open(hp, 'w')); open(rp, 'wb').write(bytes(raw))
        subprocess.run(['node', '/home/claude/data/enc/encode.mjs', hp, rp, op, oh], check=True)
        res = json.load(open(oh))
        for r, e in zip(recs, res):
            r['man'].update(e); r['man']['enc'] = 1
            for k in ('po', 'io', 'i32'): r['man'].pop(k, None)
        gz = gzip.compress(open(op, 'rb').read(), 9)
        open(f'{OUT}/{fname}.bin.gz', 'wb').write(gz); sizes[fname] = len(gz)
    return sizes
