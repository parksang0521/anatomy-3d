t=open('index_tpl.html').read()
def R(a,b):
    global t
    assert a in t, 'MISSING: '+a[:90]; t=t.replace(a,b,1)
# CSS
R(""".opbtn{""",""".regbox{padding:10px 14px 12px;border-bottom:1px solid var(--line)}
.regbox h3{margin:0 0 8px;font-size:12.5px;color:var(--muted);font-weight:500;display:flex;align-items:center;gap:6px}
.regbox h3 button{margin-left:auto}
.regs{display:grid;grid-template-columns:1fr 1fr;gap:5px}
.reg{display:flex;align-items:center;border:1px solid var(--line);border-radius:8px;background:rgba(255,255,255,.03);overflow:hidden}
.reg .rt{flex:1;text-align:left;background:none;border:0;padding:6px 8px;font-size:12.5px;color:#cbd5e1;display:flex;align-items:center;gap:6px}
.reg .rt:before{content:"";width:8px;height:8px;border-radius:2px;border:1px solid #64748b;flex:none}
.reg.on{border-color:rgba(34,211,238,.45);background:rgba(34,211,238,.08)}
.reg.on .rt{color:#fff}.reg.on .rt:before{background:var(--acc);border-color:var(--acc)}
.reg .rs{background:none;border:0;border-left:1px solid var(--line);color:var(--muted);font-size:11px;padding:6px 7px}
.reg .rs:hover{color:#fff;background:rgba(34,211,238,.15)}
.stepper{display:flex;gap:5px;margin-top:8px;align-items:center}
.stepper button{background:rgba(255,255,255,.05);border:1px solid var(--line);border-radius:7px;font-size:12px;padding:5px 8px;color:#cbd5e1}
.stepper button:hover{border-color:var(--acc);color:#fff}
.stepper span{flex:1;text-align:center;font-size:12px;color:var(--muted)}
.item.rhide{display:none!important}
.opbtn{""")
# HTML
R("""    <div id="list"></div>""","""    <div class="regbox">
      <h3>구획 (해부 실습용) <button class="opbtn" id="regAll" title="모든 구획 켜기">전체</button></h3>
      <div class="regs" id="regs"></div>
      <div class="stepper"><button id="stepPrev">◀ 이전</button><span id="stepLbl">실습 순서대로 보기</span><button id="stepNext">다음 ▶</button></div>
    </div>
    <div id="list"></div>""")
# REGIONS meta + state (after SYSTEMS block end marker GROUP_ORDER)
R("""const GROUP_ORDER=[""","""const REGIONS=[
  {k:'chestwall',ko:'가슴벽',tip:'가슴근육·갈비뼈·갈비사이근·유방'},
  {k:'abdwall',ko:'배벽',tip:'배근육·샅고랑 부위'},
  {k:'abdomen',ko:'배안 (복부 장기)',tip:'위·간·창자·콩팥·뒤배벽'},
  {k:'thorax',ko:'가슴안 (흉부 장기)',tip:'심장·허파·세로칸·가로막'},
  {k:'pelvis',ko:'골반·회음',tip:'골반뼈·골반 장기·생식기·회음'},
  {k:'neck',ko:'목',tip:'목 근육·후두·목 혈관·신경'},
  {k:'head',ko:'머리·얼굴',tip:'머리뼈·얼굴·눈·입'},
  {k:'brain',ko:'뇌',tip:'뇌·뇌혈관·뇌신경 시작부'},
  {k:'back',ko:'등·척주',tip:'척추·척수·등근육'},
  {k:'arm',ko:'팔',tip:'어깨·위팔·아래팔·손'},
  {k:'leg',ko:'다리',tip:'볼기·넙다리·종아리·발'},
];
const regionOn={}; REGIONS.forEach(r=>regionOn[r.k]=true);
const GROUP_ORDER=[""")
# buildMeshes: segments
R("""  g.computeVertexNormals(); g.computeBoundingSphere(); g.computeBoundingBox();
  if(p.sys==='skin'){ const m=new THREE.Mesh(g,skinMat); m.renderOrder=10; skinG.add(m); return; }""",
"""  g.computeVertexNormals(); g.computeBoundingSphere(); g.computeBoundingBox();
  const segs=(p.sg&&p.sg.length)?p.sg:[[-1,0,p.ic]];
  const geoms=segs.map(([rid,st,cnt])=>{ if(segs.length===1) return g; const g2=new THREE.BufferGeometry();
    g2.setAttribute('position',g.attributes.position); g2.setAttribute('normal',g.attributes.normal); g2.setIndex(g.index); g2.setDrawRange(st,cnt);
    g2.boundingSphere=g.boundingSphere; g2.boundingBox=g.boundingBox; return g2; });
  const regOf=i=>segs[i][0]>=0?MAN.regionNames[segs[i][0]]:null;
  if(p.sys==='skin'){ geoms.forEach((gg,i)=>{ const m=new THREE.Mesh(gg,skinMat); m.renderOrder=10; m.userData.region=regOf(i); m.visible=!m.userData.region||regionOn[m.userData.region]; skinG.add(m); }); return; }""")
R("""  const m=new THREE.Mesh(g,mat); m.userData.id=p.id; m.userData.bone=p.sys==='skeletal'; m.userData.baseOpacity=mat.opacity;
  m.visible=sysOn[p.sys]&&(!isoId||p.id===isoId); if(typeof clipOn!=='undefined'&&clipOn) mat.side=THREE.DoubleSide;
  groups[p.sys].add(m); pickables.push(m); parts[p.id].meshes.push(m);""",
"""  if(typeof clipOn!=='undefined'&&clipOn) mat.side=THREE.DoubleSide;
  geoms.forEach((gg,i)=>{
    const m=new THREE.Mesh(gg,mat); m.userData.id=p.id; m.userData.bone=p.sys==='skeletal'; m.userData.baseOpacity=mat.opacity; m.userData.region=regOf(i);
    m.visible=meshVisible(p,m); groups[p.sys].add(m); pickables.push(m); parts[p.id].meshes.push(m); });""")
# visibility
R("""function updateVisibility(){
  for(const p of Object.values(parts)){ const v=sysOn[p.sys]&&(!isoId||p.id===isoId); p.meshes.forEach(m=>m.visible=v); }""",
"""function meshVisible(p,m){ return isoId ? p.id===isoId : (sysOn[p.sys] && (!m.userData.region || regionOn[m.userData.region])); }
const inRegions=p=>!p.sg||p.sg.some(s=>regionOn[MAN.regionNames[s[0]]]);
function updateVisibility(){
  for(const p of Object.values(parts)) p.meshes.forEach(m=>m.visible=meshVisible(p,m));
  for(const m of skinG.children) m.visible=!m.userData.region||regionOn[m.userData.region];
  const allOn=REGIONS.every(r=>regionOn[r.k]);
  document.querySelectorAll('.item').forEach(b=>{ const p=parts[b.dataset.id]; b.classList.toggle('rhide',!allOn&&p&&!inRegions(p)); });
  document.querySelectorAll('details.sys').forEach(d=>{ const n=[...d.querySelectorAll('.item')].filter(b=>!b.classList.contains('rhide')).length; const c=d.querySelector('.cnt'); if(c) c.textContent=(c.textContent.includes('⤓')?'⤓ ':'')+n; });
  document.querySelectorAll('.reg').forEach(e=>e.classList.toggle('on',!!regionOn[e.dataset.r]));""")
# quiz pool visible
R("""const pool=()=>Object.values(parts).filter(p=>p.info&&p.meshes.length&&sysOn[p.sys]""","""const pool=()=>Object.values(parts).filter(p=>p.info&&p.meshes.some(m=>m.visible)&&sysOn[p.sys]""")
# focusPart only visible meshes
R("""  if(!p.meshes.length) return; const box=new THREE.Box3(); p.meshes.forEach(m=>box.expandByObject(m));""",
"""  if(!p.meshes.length) return; const box=new THREE.Box3(); const vm=p.meshes.filter(m=>m.visible);
  if(vm.length&&vm.length<p.meshes.length&&p.sg){ // 보이는 구획의 중심 쪽으로
    const lo=V(...MAN.lo); vm.forEach(m=>{ const r=MAN.regions[m.userData.region]; if(r){ box.expandByPoint(V(...r.lo)); box.expandByPoint(V(...r.hi)); } });
    p.meshes.forEach(m=>{}); const pb=new THREE.Box3(); p.meshes.forEach(m=>pb.expandByObject(m)); box.intersect(pb); if(box.isEmpty()) p.meshes.forEach(m=>box.expandByObject(m)); }
  else p.meshes.forEach(m=>box.expandByObject(m));""")
# region UI logic (before 공유 링크 section)
R("""/* ---------------- 공유 링크 ---------------- */""","""/* ---------------- 구획 ---------------- */
const STEP=['chestwall','abdwall','abdomen','thorax','pelvis','neck','head','brain','back','arm','leg']; let stepI=-1;
function buildRegions(){
  const box=document.getElementById('regs'); box.innerHTML='';
  for(const r of REGIONS){
    if(MAN&&!MAN.regions[r.k]) continue;
    const e=document.createElement('div'); e.className='reg'; e.dataset.r=r.k; e.title=r.tip;
    e.innerHTML=`<button class="rt">${r.ko}</button><button class="rs" title="이 구획만 보기">만</button>`;
    e.querySelector('.rt').onclick=()=>{ regionOn[r.k]=!regionOn[r.k]; stepI=-1; updStepLbl(); updateVisibility(); };
    e.querySelector('.rs').onclick=()=>soloRegion(r.k);
    box.appendChild(e);
  }
}
function soloRegion(k,fly=true){
  REGIONS.forEach(r=>regionOn[r.k]=(r.k===k)); if(selId&&!parts[selId]?.meshes.some(m=>m.userData.region===k)) select(null);
  updateVisibility(); stepI=STEP.indexOf(k); updStepLbl();
  const R_=MAN.regions[k]; if(fly&&R_){ const c=V(...R_.c), lo=V(...R_.lo), hi=V(...R_.hi); const size=hi.clone().sub(lo).length();
    const dir = k==='back'?V(0,0.15,-1): k==='brain'?V(0.35,0.55,1): V(0.25,0.12,1); dir.normalize();
    flyTo(c, c.clone().add(dir.multiplyScalar(Math.max(0.45,size*1.25)))); }
}
function updStepLbl(){ const r=REGIONS.find(x=>x.k===STEP[stepI]); document.getElementById('stepLbl').textContent=r?`${stepI+1}/${STEP.length} · ${r.ko}`:'실습 순서대로 보기'; }
const avail=()=>STEP.filter(k=>MAN.regions[k]);
document.getElementById('stepNext').onclick=()=>{ const a=avail(); let j=a.indexOf(STEP[stepI]); j=(j+1)%a.length; soloRegion(a[j]); };
document.getElementById('stepPrev').onclick=()=>{ const a=avail(); let j=a.indexOf(STEP[stepI]); j=j<=0?a.length-1:j-1; soloRegion(a[j]); };
document.getElementById('regAll').onclick=()=>{ REGIONS.forEach(r=>regionOn[r.k]=true); stepI=-1; updStepLbl(); updateVisibility(); flyTo(HOME.t,HOME.p); };

/* ---------------- 공유 링크 ---------------- */""")
# call buildRegions after load in initial and switch
R("""load().then(()=>{ buildList(); updateVisibility(); paint(); openHash(); })""","""load().then(()=>{ buildRegions(); buildList(); updateVisibility(); paint(); openHash(); })""")
R("""  showLoading(); await load(); buildList(); updateVisibility();""","""  REGIONS.forEach(r=>regionOn[r.k]=true); stepI=-1; updStepLbl();
  showLoading(); await load(); buildRegions(); buildList(); updateVisibility();""")
# openHash: if part not in active regions, turn all regions on
R("""  await ensureSys(p.sys); if(selId!==p.id) select(p.id,{focus:true});""","""  if(!inRegions(p)){ REGIONS.forEach(r=>regionOn[r.k]=true); updateVisibility(); }
  await ensureSys(p.sys); if(selId!==p.id) select(p.id,{focus:true});""")
# list click on hidden region items not possible (hidden). ok
# after ensureSys builds meshes -> updateVisibility to refresh counts
R("""    loaded[s]=true; chipL.style.display='none'; applyOpacity();""","""    loaded[s]=true; chipL.style.display='none'; applyOpacity(); updateVisibility();""")
open('index_tpl.html','w').write(t); print('patched')
