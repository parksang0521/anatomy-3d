p='/home/claude/data/index_tpl.html'; s=open(p).read()
def R(a,b):
    global s; assert s.count(a)==1,(s.count(a),a[:70]); s=s.replace(a,b)
R("#search:focus{border-color:var(--acc)}", """#search:focus{border-color:var(--acc)}
#side header{position:relative}
#sres{position:absolute;left:12px;right:12px;top:calc(100% - 6px);z-index:30;background:#111a2b;border:1px solid var(--line);border-radius:10px;box-shadow:0 14px 40px rgba(0,0,0,.55);max-height:min(60vh,520px);overflow:auto;display:none;padding:4px}
#sres.on{display:block}
#sres .r{display:flex;align-items:center;gap:9px;width:100%;text-align:left;background:none;border:0;color:var(--text);padding:7px 9px;border-radius:7px;font:inherit;cursor:pointer}
#sres .r:hover,#sres .r.act{background:rgba(94,234,255,.12)}
#sres .r i{width:8px;height:8px;border-radius:50%;flex:none}
#sres .r b{font-weight:600;font-size:13.5px;display:block;line-height:1.25}
#sres .r small{color:var(--muted);font-size:11.5px;display:block;margin-top:1px}
#sres .r em{font-style:normal;color:var(--acc)}
#sres .more,#sres .none{color:var(--muted);font-size:12px;padding:8px 10px}""")
R('<input id="search" type="search" placeholder="검색: 넙다리뼈, 대퇴골, femur…" autocomplete="off">',
  '<input id="search" type="search" placeholder="검색: 넙다리뼈, 대퇴골, femur, ㄴㄷㄹ…" autocomplete="off" enterkeyhint="search">\n      <div id="sres" role="listbox"></div>')
old_handler = s[s.index("document.getElementById('search').oninput=e=>{"):s.index("let skinBase=0.08;")]
R(old_handler, r"""/* ---------------- 검색 ---------------- */
// 새 용어 → 옛 한자어 (검색용 별칭). 긴 것부터 적용
const OLDTERM=[['위팔두갈래근','상완이두근'],['위팔세갈래근','상완삼두근'],['넙다리네갈래근','대퇴사두근'],['넙다리두갈래근','대퇴이두근'],['넙다리곧은근','대퇴직근'],['넙다리빗근','봉공근'],['넙다리근막긴장근','대퇴근막장근'],
 ['등세모근','승모근'],['어깨세모근','삼각근'],['큰가슴근','대흉근'],['작은가슴근','소흉근'],['넓은등근','광배근'],['배곧은근','복직근'],['배바깥빗근','외복사근'],['배속빗근','내복사근'],['배가로근','복횡근'],
 ['큰볼기근','대둔근'],['중간볼기근','중둔근'],['작은볼기근','소둔근'],['장딴지근','비복근'],['목빗근','흉쇄유돌근'],['깨물근','교근'],['관자근','측두근'],['앞톱니근','전거근'],['큰원근','대원근'],['작은원근','소원근'],['가시위근','극상근'],['가시아래근','극하근'],['어깨밑근','견갑하근'],
 ['두갈래근','이두근'],['세갈래근','삼두근'],['네갈래근','사두근'],['세모근','삼각근'],['네모근','방형근'],['가로막','횡격막'],
 ['넙다리뼈','대퇴골'],['위팔뼈','상완골'],['노뼈','요골'],['자뼈','척골'],['정강뼈','경골'],['종아리뼈','비골'],['빗장뼈','쇄골'],['어깨뼈','견갑골'],['복장뼈','흉골'],['갈비뼈','늑골'],['무릎뼈','슬개골'],['엉덩뼈','장골'],['궁둥뼈','좌골'],['두덩뼈','치골'],['엉치뼈','천골'],['꼬리뼈','미골'],['목뼈','경추'],['등뼈','흉추'],['허리뼈','요추'],['머리뼈','두개골'],['이마뼈','전두골'],['마루뼈','두정골'],['관자뼈','측두골'],['뒤통수뼈','후두골'],['나비뼈','접형골'],['벌집뼈','사골'],['광대뼈','관골'],['위턱뼈','상악골'],['아래턱뼈','하악골'],['목말뼈','거골'],['발꿈치뼈','종골'],['손배뼈','주상골'],['발배뼈','주상골'],['손허리뼈','중수골'],['발허리뼈','중족골'],['손가락뼈','수지골'],['발가락뼈','족지골'],['볼기뼈','관골'],
 ['온목동맥','총경동맥'],['속목동맥','내경동맥'],['바깥목동맥','외경동맥'],['속목정맥','내경정맥'],['바깥목정맥','외경정맥'],['척추동맥','추골동맥'],['빗장밑','쇄골하'],['겨드랑','액와'],['넙다리','대퇴'],['위팔','상완'],['아래팔','전완'],['궁둥','좌골'],['정강','경골'],['종아리','비골'],['오금','슬와'],['두렁','복재'],['볼기','둔'],['엉덩','장골'],['샅','서혜'],
 ['콩팥','신'],['허파','폐'],['가슴샘','흉선'],['방패','갑상'],['쓸개','담낭'],['이자','췌'],['지라','비장'],['막창자꼬리','충수'],['막창자','맹장'],['곧창자','직장'],['잘록창자','결장'],['샘창자','십이지장'],['빈창자','공장'],['돌창자','회장'],['큰창자','대장'],['작은창자','소장'],['후두덮개','후두개'],['코선반','비갑개'],['샘','선'],['솔방울','송과']];
const GRP_EN={'머리뼈':'skull cranium','척주':'spine vertebral column vertebrae','가슴우리':'thorax rib cage','팔뼈':'upper limb bones arm','다리뼈':'lower limb bones leg','골반':'pelvis','골반·엉덩이':'pelvis hip gluteal','심장·대혈관':'heart great vessels cardiac','심장':'heart','판막':'heart valves','치아':'teeth tooth','기관지':'bronchi bronchus','허파':'lung lungs','눈':'eye','입':'mouth oral','큰창자':'large intestine colon bowel','작은창자':'small intestine bowel','간·쓸개·이자':'liver gallbladder pancreas biliary','뇌':'brain cerebrum','뇌신경':'cranial nerves','척수신경 뿌리':'spinal nerve roots','팔신경':'arm nerves brachial','다리신경':'leg nerves lumbosacral','가슴·목 신경':'thoracic cervical nerves','연골':'cartilage','림프기관':'lymphoid','중추':'central nervous','자율신경':'autonomic','몸통':'trunk','머리·목':'head neck','팔':'arm upper limb','다리':'leg lower limb'};
const CHO='ㄱㄲㄴㄷㄸㄹㅁㅂㅃㅅㅆㅇㅈㅉㅊㅋㅌㅍㅎ';
const choOf=t=>[...t].map(c=>{const k=c.charCodeAt(0)-0xAC00; return k>=0&&k<11172?CHO[Math.floor(k/588)]:c;}).join('');
const hasHan=t=>/[가-힣ㄱ-ㅎ]/.test(t);
const normKo=t=>(t||'').toLowerCase().replace(/왼쪽|좌측/g,'왼').replace(/오른쪽|우측/g,'오른').replace(/[\s·\-,()]/g,'');
const toOld=t=>{ for(const [a,b] of OLDTERM) if(t.includes(a)) t=t.split(a).join(b); return t; };
let SIDX=[];
function buildSearch(){
  SIDX=Object.values(parts).map(p=>{
    const en=(p.en||'').toLowerCase(), ko=normKo(p.ko), old=normKo(p.old);
    const side=/^left\b|\bleft\b/.test(en)?'left lt 왼 좌':/^right\b|\bright\b/.test(en)?'right rt 오른 우':'';
    return {p, en, enW:en.split(/[^a-z0-9]+/).filter(Boolean), ko, old, alt:toOld(ko), cho:choOf(ko), grp:normKo(p.grp)+' '+(GRP_EN[p.grp]||''), side};
  });
}
function lev(a,b){ if(Math.abs(a.length-b.length)>2) return 9; const d=[...Array(b.length+1).keys()]; for(let i=1;i<=a.length;i++){ let pr=d[0]; d[0]=i; for(let j=1;j<=b.length;j++){ const t=d[j]; d[j]=Math.min(d[j]+1,d[j-1]+1,pr+(a[i-1]===b[j-1]?0:1)); pr=t; } } return d[b.length]; }
function scoreTok(e,t,fuzzy){
  if(hasHan(t)){
    let tk=normKo(t); if(tk==='좌') tk='왼'; if(tk==='우') tk='오른';
    if(/^[ㄱ-ㅎ]+$/.test(tk)) return e.cho.startsWith(tk)?30:e.cho.includes(tk)?14:0;
    let best=0;
    for(const [f,w] of [[e.ko,1],[e.old,0.95],[e.alt,0.9]]){ if(!f) continue;
      if(f===tk) best=Math.max(best,100*w); else if(f.startsWith(tk)) best=Math.max(best,45*w); else if(f.includes(tk)) best=Math.max(best,22*w); }
    if(!best && e.side.includes(tk)) best=8;
    if(!best && e.grp.includes(tk)) best=4;
    return best;
  }
  const tk=t.toLowerCase(); if(tk==='l'||tk==='lt') return e.side.startsWith('left')?8:0; if(tk==='r'||tk==='rt') return e.side.startsWith('right')?8:0;
  if(e.en===tk) return 100;
  if(e.enW.includes(tk)) return 40;
  if(e.enW.some(w=>w.startsWith(tk))) return 26;
  if(e.en.includes(tk)) return 14;
  if(e.grp.includes(tk)) return 4;
  if(fuzzy&&tk.length>=4){ const lim=tk.length>=7?2:1; if(e.enW.some(w=>lev(w,tk)<=lim||(w.length>tk.length&&lev(w.slice(0,tk.length),tk)<=lim))) return 9; }
  return 0;
}
function searchParts(q){
  q=q.trim(); if(!q) return [];
  const toks=q.split(/\s+/).filter(Boolean), whole=normKo(q);
  const run=fuzzy=>{ const out=[];
    for(const e of SIDX){ let sc=0, ok=true;
      for(const t of toks){ const v=scoreTok(e,t,fuzzy); if(!v){ ok=false; break; } sc+=v; }
      if(!ok && toks.length>1 && hasHan(q)){ const f=[e.ko,e.old,e.alt].find(f=>f&&f.includes(whole)); if(f){ ok=true; sc=f===whole?100:30; } }
      if(ok){ sc-=e.en.length*0.08; if(!sysOn[e.p.sys]) sc-=1; out.push([sc,e.p]); } }
    return out; };
  let r=run(false); if(!r.length) r=run(true);
  return r.sort((a,b)=>b[0]-a[0]||a[1].en.localeCompare(b[1].en)).map(x=>x[1]);
}
const sIn=document.getElementById('search'), sRes=document.getElementById('sres'); let sHits=[], sAct=0;
function hl(text,q){ const t=esc(text); const ws=q.trim().split(/\s+/).filter(w=>w&&!hasHan(w)&&w.length>1).map(w=>w.replace(/[.*+?^${}()|[\]\\]/g,'\\$&')); return ws.length?t.replace(new RegExp('('+ws.join('|')+')','ig'),'<em>$1</em>'):t; }
function renderSearch(){
  const q=sIn.value; sHits=q.trim()?searchParts(q):[]; sAct=0;
  if(!q.trim()){ sRes.classList.remove('on'); sRes.innerHTML=''; return; }
  const N=40;
  sRes.innerHTML = sHits.length ? sHits.slice(0,N).map((p,i)=>`<button class="r${i===0?' act':''}" data-id="${esc(p.id)}"><i style="background:${SYSTEMS[p.sys]?.dot||'#888'}"></i><span><b>${hl(enName(p),q)}</b><small>${esc(p.ko)}${p.old&&p.old!==p.ko?' · '+esc(p.old):''} · ${esc(SYSTEMS[p.sys]?.ko||'')}</small></span></button>`).join('')+(sHits.length>N?`<div class="more">외 ${sHits.length-N}개 — 검색어를 더 구체적으로 입력해 보세요</div>`:'')
    : `<div class="none">'${esc(q)}'에 맞는 구조물이 없어요</div>`;
  sRes.classList.add('on');
  sRes.querySelectorAll('.r').forEach(b=>{ b.onmousedown=e=>e.preventDefault(); b.onclick=()=>pickSearch(b.dataset.id); });
}
function pickSearch(id){
  const b=list.querySelector(`.item[data-id="${CSS.escape(id)}"]`); sRes.classList.remove('on'); sIn.blur();
  if(b) b.onclick();
}
sIn.oninput=renderSearch;
sIn.onfocus=()=>{ if(sIn.value.trim()) renderSearch(); };
sIn.onblur=()=>setTimeout(()=>sRes.classList.remove('on'),120);
sIn.onkeydown=e=>{
  const rows=[...sRes.querySelectorAll('.r')];
  if(e.key==='ArrowDown'||e.key==='ArrowUp'){ if(!rows.length) return; e.preventDefault(); sAct=(sAct+(e.key==='ArrowDown'?1:-1)+rows.length)%rows.length; rows.forEach((r,i)=>r.classList.toggle('act',i===sAct)); rows[sAct].scrollIntoView({block:'nearest'}); }
  else if(e.key==='Enter'){ e.preventDefault(); if(rows[sAct]) pickSearch(rows[sAct].dataset.id); }
  else if(e.key==='Escape'){ sIn.value=''; renderSearch(); sIn.blur(); }
};
""")
R("load().then(()=>{ buildRegions(); buildList();", "load().then(()=>{ buildRegions(); buildList(); buildSearch();")
R("showLoading(); await load(); buildRegions(); buildList();", "showLoading(); await load(); buildRegions(); buildList(); buildSearch(); sIn.value=''; renderSearch();")
open(p,'w').write(s); print('ok')
