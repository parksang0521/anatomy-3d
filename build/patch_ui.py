t=open('index_tpl.html').read()
def R(a,b):
    global t
    assert a in t, 'MISSING: '+a[:80]; t=t.replace(a,b,1)
R("""#menuBtn{display:none}""","""#menuBtn{display:none}
#app.collapsed #side{display:none}
#app.collapsed #menuBtn{display:block}
#sideClose{background:none;border:1px solid var(--line);border-radius:7px;color:var(--muted);font-size:12px;padding:3px 8px;float:right;margin-top:-2px}
#sideClose:hover{color:#fff;border-color:var(--acc)}
#sexNote{position:absolute;left:50%;transform:translateX(-50%);bottom:40px;background:var(--panel);border:1px solid rgba(251,191,36,.4);border-radius:10px;padding:7px 12px;font-size:12px;color:#e6d3a0;z-index:4;max-width:min(560px,80%);text-align:center;display:none}
@media (min-width:821px){
  #stage.docked #c{width:calc(100% - 390px)}
  #stage.docked #quiz{top:0;right:0;bottom:0;width:390px;max-height:none;border-radius:0;border:0;border-left:1px solid var(--line)}
  #stage.docked #viewBar{right:404px}
  #stage.docked #sexNote{left:calc((100% - 390px)/2)}
}""")
R("""      <h1>인체 해부학 <span>3D</span> 아틀라스</h1>""","""      <button id="sideClose" title="목록 접기">⟨ 접기</button>
      <h1>인체 해부학 <span>3D</span> 아틀라스</h1>""")
R("""      <div class="seg"><button data-mode="explore" class="on">탐색</button><button data-mode="quiz">퀴즈</button></div>""",
"""      <div class="seg"><button data-mode="explore" class="on">탐색</button><button data-mode="quiz">퀴즈</button></div>
      <div class="seg"><button data-sex="male" class="on">남성</button><button data-sex="female">여성</button></div>""")
R("""    <div id="tip"></div>""","""    <div id="tip"></div>
    <div id="sexNote">여성 모델은 HuBMAP 기준 장기 모델이에요. 골반·무릎 부위 뼈, 주요 장기, 생식기관, 유방, 혈관, 척수가 있고 머리뼈·갈비뼈·팔뼈·근육·말초신경은 없어요.</div>""")
R("""    <footer>3D 모델:""","""    <footer id="foot">3D 모델:""")
R("""  endocrine:  {ko:'내분비계', dot:'#4fc3a1'},""","""  endocrine:  {ko:'내분비계', dot:'#4fc3a1'},
  reproductive:{ko:'생식계', dot:'#e48ab8'},""")
R("""/*INFO_NV*/""","""/*INFO_NV*/
/*INFO_RP*/""")
R("""const GROUP_ORDER=['심장·대혈관',""","""const GROUP_ORDER=['자궁','난소·자궁관','유방','콩팥','방광','허파구역','기관지','후두','간·이자','무릎','척수','심장·대혈관',""")
R("""  if(p.sys==='nerves')""","""  if(p.sys==='reproductive'){
    const m={testis:0xe9c9a8,epididymis:0xd7a98a,ductus:0xd8c08a,seminalv:0xd9b98a,prostate:0xc98a7a,penis:0xd99a8a,uterus:0xd98a8a,cervix:0xe3a3a3,ovary:0xf0d0c0,uterinetube:0xe8a0a0};
    if(k==='breast') return /fat/i.test(p.en)?0xf0d79a:/lobe/i.test(p.en)?0xf3b8b0:/duct|sinus/i.test(p.en)?0xe08a8a:/nipple|areola/i.test(p.en)?0xc8826e:0xe8e2d0;
    return m[k]??0xd99a9a; }
  if(p.sys==='urinary'&&/pyramid/i.test(p.en)) return 0x8a3a30;
  if(p.sys==='urinary'&&/calyx|pelvis|papilla/i.test(p.en)) return 0xd8b26a;
  if(k==='meniscus') return 0xb9d0da;
  if(p.sys==='nerves')""")
R("""  if(p.sys==='nervous'&&p.key==='eye'&&/cornea|lens|chamber|vitreous/i.test(p.en)){ mat.transparent=true; mat.opacity=.45; }""",
"""  if(p.sys==='nervous'&&p.key==='eye'&&/cornea|lens|chamber|vitreous/i.test(p.en)){ mat.transparent=true; mat.opacity=.45; }
  const ghost=/^Female .*\\bfat$|^Female (left |right )?kidney$/i.test(p.en)?0.3:/^Female .*cortex$/i.test(p.en)?0.5:null;
  if(ghost!=null){ mat.transparent=true; mat.opacity=ghost; mat.depthWrite=false; }""")
R("""let MAN=null; const loaded={}, loading={};""","""let MAN=null, SEX='male'; let loaded={}, loading={};
const fileOf=s=>(SEX==='female'?'f_':'')+s, sysOfFile=f=>f.replace(/^f_/,'');""")
R("""  const m=new THREE.Mesh(g,mat); m.userData.id=p.id; m.userData.bone=p.sys==='skeletal'; m.userData.baseOpacity=mat.opacity;""",
"""  const m=new THREE.Mesh(g,mat); m.userData.id=p.id; m.userData.bone=p.sys==='skeletal'; m.userData.baseOpacity=mat.opacity;""")
R("""async function load(){
  MAN=await (await fetch('models/manifest.json')).json();""","""async function load(){
  MAN=await (await fetch(SEX==='female'?'models/manifest_f.json':'models/manifest.json')).json();""")
R("""  const first=Object.keys(MAN.files).filter(f=>!SYSTEMS[f]?.lazy);""","""  const first=Object.keys(MAN.files).filter(f=>!SYSTEMS[sysOfFile(f)]?.lazy);""")
R("""  first.forEach(f=>loaded[f]=true);""","""  first.forEach(f=>loaded[sysOfFile(f)]=true);""")
R("""  if(loaded[s]) return; if(loading[s]) return loading[s];
  loading[s]=(async()=>{
    const total=MAN.files[s]; let got=0; chipL.style.display='block';
    const bufs=await loadFiles([s],n=>{ got+=n; chipL.textContent=`${SYSTEMS[s].ko} 불러오는 중… ${Math.round(got/total*100)}%`; });
    chipL.textContent=`${SYSTEMS[s].ko} 조립 중…`; await new Promise(r=>setTimeout(r,30));
    for(const p of MAN.parts) if(p.f===s) buildMeshes(p,bufs[s]);""","""  if(loaded[s]||!MAN.files[fileOf(s)]) return; if(loading[s]) return loading[s];
  const gen=GEN;
  loading[s]=(async()=>{
    const fn=fileOf(s), total=MAN.files[fn]; let got=0; chipL.style.display='block';
    const bufs=await loadFiles([fn],n=>{ got+=n; chipL.textContent=`${SYSTEMS[s].ko} 불러오는 중… ${Math.round(got/total*100)}%`; });
    if(gen!==GEN){ chipL.style.display='none'; return; }
    chipL.textContent=`${SYSTEMS[s].ko} 조립 중…`; await new Promise(r=>setTimeout(r,30));
    for(const p of MAN.parts) if(p.f===fn) buildMeshes(p,bufs[fn]);""")
R("""const chipL=document.createElement('div');""","""let GEN=0;
function showLoading(){
  if(document.getElementById('loading')) return;
  const L=document.createElement('div'); L.id='loading';
  L.innerHTML='<div class="box"><div id="ldText">3D 모델 불러오는 중…</div><div class="track"><div class="fill" id="ldFill"></div></div><small id="ldSub"></small></div>';
  document.getElementById('stage').appendChild(L); ldFill=document.getElementById('ldFill'); ldText=document.getElementById('ldText');
}
async function switchSex(sex,{keepHash=false}={}){
  if(sex===SEX&&MAN) return; GEN++;
  if(quiz.on) setMode('explore');
  select(null); isoId=null; hoverId=null;
  for(const s in groups){ const g=groups[s]; while(g.children.length){ const m=g.children.pop(); m.geometry.dispose(); m.material.dispose(); } }
  while(skinG.children.length){ skinG.children.pop().geometry.dispose(); }
  pickables.length=0; for(const k in parts) delete parts[k]; loaded={}; loading={}; chipL.style.display='none';
  for(const s in SYSTEMS) sysOn[s]=!SYSTEMS[s].lazy;
  SEX=sex; document.querySelectorAll('[data-sex]').forEach(b=>b.classList.toggle('on',b.dataset.sex===sex));
  document.getElementById('sexNote').style.display=sex==='female'?'block':'none';
  document.getElementById('foot').innerHTML = sex==='female'
    ? '3D 모델: <a href="https://humanatlas.io/3d-reference-library" target="_blank" rel="noopener">HuBMAP HRA 3D Reference Object Library</a> (Visible Human Female), CC BY 4.0 — 웹용으로 경량화·재구성함. 여성 1인 기반 기준 모델입니다. 교육용이며 진단용이 아닙니다.'
    : '3D 모델: <a href="https://dbarchive.biosciencedbc.jp/en/bodyparts3d/download.html" target="_blank" rel="noopener">BodyParts3D</a> © The Database Center for Life Science (DBCLS), CC BY 4.0 — 웹용으로 경량화·재구성함. 성인 남성 1인의 기준 모델로, 개인차는 반영되지 않습니다. 교육용이며 진단용이 아닙니다.';
  if(!keepHash){ try{ history.replaceState(null,'',location.pathname+location.search); }catch(e){} }
  showLoading(); await load(); buildList(); updateVisibility(); applyOpacity(); paint(); updateClip(); flyTo(HOME.t,HOME.p);
}
document.querySelectorAll('[data-sex]').forEach(b=>b.onclick=()=>switchSex(b.dataset.sex));

const chipL=document.createElement('div');""")
R("""const ldFill=document.getElementById('ldFill'), ldText=document.getElementById('ldText');""","""let ldFill=document.getElementById('ldFill'), ldText=document.getElementById('ldText');""")
R("""    const S=SYSTEMS[s], ps=Object.values(parts).filter(p=>p.sys===s).sort((a,b)=>a.ko.localeCompare(b.ko,'ko'));""",
"""    const S=SYSTEMS[s], ps=Object.values(parts).filter(p=>p.sys===s).sort((a,b)=>a.ko.localeCompare(b.ko,'ko'));
    if(!ps.length) continue;""")
R("""(MAN.files[s]/1e6).toFixed(1)""","""(MAN.files[fileOf(s)]/1e6).toFixed(1)""")
R("""  const h=decodeURIComponent(location.hash.slice(1)); if(!h) return;""","""  const h=decodeURIComponent(location.hash.slice(1)); if(!h) return;
  const want=h.startsWith('female-')?'female':'male'; if(want!==SEX) await switchSex(want,{keepHash:true});""")
R("""document.getElementById('menuToggle').onclick=()=>side.classList.toggle('open');""","""const appEl=document.getElementById('app');
document.getElementById('menuToggle').onclick=()=>{ if(innerWidth>820) appEl.classList.remove('collapsed'); else side.classList.toggle('open'); };
document.getElementById('sideClose').onclick=()=>{ if(innerWidth>820) appEl.classList.add('collapsed'); else side.classList.remove('open'); };""")
R("""  if(quiz.on){ select(null); isoId=null; updateVisibility(); qEl.classList.remove('hidden'); nextQ(); }""",
"""  stage.classList.toggle('docked',quiz.on);
  if(quiz.on){ select(null); isoId=null; updateVisibility(); qEl.classList.remove('hidden'); nextQ(); }""")
R("""function resize(){ const r=stage.getBoundingClientRect(); renderer.setSize(r.width,r.height,false); camera.aspect=r.width/Math.max(1,r.height); camera.updateProjectionMatrix(); }
new ResizeObserver(resize).observe(stage); resize();""","""function resize(){ const w=canvas.clientWidth, h=canvas.clientHeight; if(!w||!h) return; renderer.setSize(w,h,false); camera.aspect=w/Math.max(1,h); camera.updateProjectionMatrix(); }
new ResizeObserver(resize).observe(canvas); resize();""")
open('index_tpl.html','w').write(t)
print('patched')
