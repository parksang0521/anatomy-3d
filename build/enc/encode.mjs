import fs from 'fs';
import { MeshoptEncoder } from '/home/claude/test/node_modules/meshoptimizer/index.module.js';
await MeshoptEncoder.ready;
const [,, hdrPath, rawPath, outPath, outHdr] = process.argv;
const hdr = JSON.parse(fs.readFileSync(hdrPath, 'utf8'));
const raw = fs.readFileSync(rawPath);
const chunks = []; let off = 0; const res = [];
for (const r of hdr) {
  const pos = new Uint8Array(raw.buffer, raw.byteOffset + r.poff, r.vc * 8);
  const idx = new Uint32Array(raw.buffer.slice(raw.byteOffset + r.ioff, raw.byteOffset + r.ioff + r.ic * 4));
  const ep = MeshoptEncoder.encodeVertexBuffer(pos, r.vc, 8);
  const ei = MeshoptEncoder.encodeIndexBuffer(new Uint8Array(idx.buffer), r.ic, 4);
  const pe = off; chunks.push(ep); off += ep.length; const pad1 = (4 - off % 4) % 4; if (pad1) { chunks.push(new Uint8Array(pad1)); off += pad1; }
  const ie = off; chunks.push(ei); off += ei.length; const pad2 = (4 - off % 4) % 4; if (pad2) { chunks.push(new Uint8Array(pad2)); off += pad2; }
  res.push({ pe, pl: ep.length, ie, il: ei.length });
}
fs.writeFileSync(outPath, Buffer.concat(chunks.map(c => Buffer.from(c.buffer, c.byteOffset, c.length))));
fs.writeFileSync(outHdr, JSON.stringify(res));
