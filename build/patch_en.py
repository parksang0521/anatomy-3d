t=open('index_tpl.html').read()
def R(a,b):
    global t
    assert a in t, 'MISSING: '+a[:90]; t=t.replace(a,b,1)
R("""      b.innerHTML=`${esc(p.ko)}<small>${esc(p.en)}</small>`;""","""      b.innerHTML=`${esc(enName(p))}<small>${esc(p.ko)}</small>`;""")
R(""".sort((a,b)=>a.ko.localeCompare(b.ko,'ko'));""",""".sort((a,b)=>sortKey(a).localeCompare(sortKey(b),'en',{numeric:true}));""")
R("""const enName=p=>{""","""const sortKey=p=>{ const e=enName(p); const m=e.match(/^(Left|Right) (.*)$/i); return m?m[2]+' '+m[1]:e; };
const enName=p=>{""")
R("""b.textContent=o.ko;""","""b.innerHTML=`${esc(enName(o))}<small style="color:var(--muted);margin-left:8px;font-size:12px">${esc(o.ko)}</small>`;""")
R("""    qprompt.innerHTML=`3D 모델에서 <b>${esc(t.ko)}</b>${t.old?` <span style="color:var(--muted)">(${esc(t.old)})</span>`:''}을(를) 클릭하세요.`;""",
"""    qprompt.innerHTML=`3D 모델에서 다음 구조물을 클릭하세요.<br><b>${esc(enName(t))}</b> <span style="color:var(--muted);font-size:13px">${esc(t.ko)}${t.old&&t.old!==t.ko?' · '+esc(t.old):''}</span>`;""")
R("""<br><b>${esc(t.ko)}</b> · ${esc(t.en)}<br>""","""<br><b>${esc(enName(t))}</b> · <span style="color:var(--muted)">${esc(t.ko)}</span><br>""")
R("""`'${parts[isoId].ko}'만 보는 중`""","""`'${enName(parts[isoId])}'만 보는 중`""")
R("""`클릭한 곳은 '${esc(parts[id].ko)}'예요.`""","""`클릭한 곳은 '${esc(enName(parts[id]))}'예요.`""")
# 모든 계통 처음부터 켜기
R("""  for(const s in SYSTEMS) sysOn[s]=!SYSTEMS[s].lazy;""","""  for(const s in SYSTEMS) sysOn[s]=true;""")
R("""const sysOn={}; for(const s in SYSTEMS) sysOn[s]=!SYSTEMS[s].lazy;""","""const sysOn={}; for(const s in SYSTEMS) sysOn[s]=true;""")
R("""  const first=Object.keys(MAN.files).filter(f=>!SYSTEMS[sysOfFile(f)]?.lazy);""","""  const first=Object.keys(MAN.files);""")
R("""<small id="ldSub">약 6MB · 신경·근육·혈관은 켤 때 따로 불러와요</small>""","""<small id="ldSub">전체 모델 약 12MB · 처음 한 번만 오래 걸려요</small>""")
R("""<br>신경·근육·혈관은 아래 목록에서 켜세요</div>""","""</div>""")
open('index_tpl.html','w').write(t); print('ok')
