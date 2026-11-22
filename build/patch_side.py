t=open('index_tpl.html').read()
def R(a,b):
    global t
    assert a in t, 'MISSING: '+a[:90]; t=t.replace(a,b,1)
R("#list{flex:1;overflow:auto;padding:6px 8px 20px}","""#sideScroll{flex:1;overflow:auto;min-height:0}
#list{padding:2px 8px 16px}
details.sect{border-bottom:1px solid var(--line)}
details.sect>summary{list-style:none;cursor:pointer;display:flex;align-items:center;gap:8px;padding:11px 16px;font-size:13px;font-weight:700;color:#dbe3ee;user-select:none}
details.sect>summary::-webkit-details-marker{display:none}
details.sect>summary:hover{background:rgba(255,255,255,.03)}
details.sect>summary .schev{color:var(--muted);font-size:11px;transition:transform .2s;margin-left:2px}
details.sect[open]>summary .schev{transform:rotate(90deg)}
details.sect>summary .opbtn{margin-left:auto}
details.sect .regbox{border-bottom:0;padding-top:0}
.panel .sub b{color:#e6eaf2;font-weight:500}""")
R("""    <div class="controls">""","""    <div id="sideScroll">
    <div class="controls">""")
R("""    <div class="regbox">
      <h3>구획 (해부 실습용) <button class="opbtn" id="regAll" title="모든 구획 켜기">전체</button></h3>""","""    <details class="sect" open id="regSect"><summary><span class="schev">▶</span>구획 <span style="font-weight:400;color:var(--muted);font-size:12px">해부 실습용</span><button class="opbtn" id="regAll" title="모든 구획 켜기">전체</button></summary>
    <div class="regbox">""")
R("""    </div>
    <div id="list"></div>""","""    </div>
    </details>
    <details class="sect" open id="sysSect"><summary><span class="schev">▶</span>계통 <span style="font-weight:400;color:var(--muted);font-size:12px">켜고 끄기 · 구조물 목록</span></summary>
    <div id="list"></div>
    </details>
    </div>""")
R("""document.getElementById('regAll').onclick=()=>{""","""document.getElementById('regAll').onclick=e=>{ e.preventDefault(); e.stopPropagation();""")
# 영어 크게, 한글 작게
R("""    <h2>${esc(p.ko)}</h2>
    <div class="sub">${p.old&&p.old!==p.ko?esc(p.old)+' · ':''}${esc(p.en)}</div>""","""    <h2>${esc(enName(p))}</h2>
    <div class="sub"><b>${esc(p.ko)}</b>${p.old&&p.old!==p.ko?' · '+esc(p.old):''}</div>""")
R("""tip.innerHTML=`${esc(p.ko)}<small>${esc(p.en)}</small>`;""","""tip.innerHTML=`${esc(enName(p))}<small>${esc(p.ko)}</small>`;""")
R("""const esc=s=>""","""const enName=p=>{ const e=p.en.replace(/^Female /,''); return e.charAt(0).toUpperCase()+e.slice(1); };
const esc=s=>""")
open('index_tpl.html','w').write(t); print('ok')
