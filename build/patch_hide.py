p='/home/claude/data/index_tpl.html'; s=open(p).read()
def R(a,b,n=1):
    global s; assert s.count(a)==n,(s.count(a),a[:60]); s=s.replace(a,b)
# CSS
R("#isoChip button{", "#hidChip{position:absolute;top:62px;left:50%;transform:translateX(-50%);background:var(--panel);border:1px solid var(--line);border-radius:20px;padding:5px 6px 5px 14px;font-size:12.5px;display:none;align-items:center;gap:6px;z-index:4;white-space:nowrap}\n#hidChip button{background:rgba(255,255,255,.08);border:1px solid var(--line);color:#e2e8f0;border-radius:14px;padding:3px 10px;font-size:12px}#hidChip button.pri{background:var(--acc);border-color:var(--acc);color:#04121a;font-weight:700}\n.item.gone{opacity:.45;text-decoration:line-through}\n.actions .btn{flex:1;padding-left:6px;padding-right:6px;white-space:nowrap}\n#isoChip button{")
# chip HTML
R('<div id="isoChip">', '<div id="hidChip"><span id="hidName"></span><button id="hidUndo" title="마지막으로 지운 것 되돌리기 (Ctrl+Z)">↶ 되돌리기</button><button class="pri" id="hidAll">모두 복원</button></div>\n    <div id="isoChip">')
R("Esc: 선택 해제</div>", "Esc: 선택 해제 · Delete: 지우기</div>")
# state + visibility
R("let selId=null, hoverId=null, isoId=null, xray=false;", "const hidden=[]; // 지운 구조물 id (순서 = 되돌리기 순서)\nlet selId=null, hoverId=null, isoId=null, xray=false;")
R("function meshVisible(p,m){ return isoId ? p.id===isoId : (sysOn[p.sys] &&", "function meshVisible(p,m){ return isoId ? p.id===isoId : (!hidden.includes(p.id) && sysOn[p.sys] &&")
R("  if(isoId) document.getElementById('isoName').textContent=`'${enName(parts[isoId])}'만 보는 중`;\n}",
  "  if(isoId) document.getElementById('isoName').textContent=`'${enName(parts[isoId])}'만 보는 중`;\n  const hc=document.getElementById('hidChip'); hc.style.display=!isoId&&hidden.length?'flex':'none';\n  if(hidden.length) document.getElementById('hidName').textContent=`지운 구조물 ${hidden.length}개`;\n  document.querySelectorAll('.item').forEach(b=>b.classList.toggle('gone',hidden.includes(b.dataset.id)));\n}\nfunction hidePart(id){ if(!id||hidden.includes(id)) return; hidden.push(id); if(isoId===id) isoId=null; if(selId===id) select(null); hoverId=null; updateVisibility(); paint(); }\nfunction unhidePart(id){ const i=hidden.indexOf(id); if(i<0) return false; hidden.splice(i,1); updateVisibility(); return true; }\nfunction unhideAll(){ hidden.length=0; updateVisibility(); paint(); }")
# info panel button
R('<button class="btn" id="bFocus">확대해서 보기</button>', '<button class="btn" id="bFocus">확대</button><button class="btn" id="bHide" title="이 구조물을 화면에서 지우기 (Delete)">지우기</button>')
R("  document.getElementById('bFocus').onclick=()=>focusPart(p);", "  document.getElementById('bFocus').onclick=()=>focusPart(p);\n  document.getElementById('bHide').onclick=()=>hidePart(id);")
R("document.getElementById('isoOff').onclick=", "document.getElementById('hidUndo').onclick=()=>{ const id=hidden.pop(); updateVisibility(); paint(); };\ndocument.getElementById('hidAll').onclick=unhideAll;\ndocument.getElementById('isoOff').onclick=")
# list item click restores a hidden part
R("await ensureSys(p.sys); select(p.id,{focus:true}); side.classList.remove('open'); }; return b; };", "await ensureSys(p.sys); unhidePart(p.id); select(p.id,{focus:true}); side.classList.remove('open'); }; return b; };")
# keys
R("addEventListener('keydown',e=>{ if(e.key==='Escape') select(null); });",
  "addEventListener('keydown',e=>{ if(/INPUT|TEXTAREA|SELECT/.test(document.activeElement?.tagName||'')) return;\n  if(e.key==='Escape') select(null);\n  else if((e.key==='Delete'||e.key==='Backspace')&&selId&&!quiz.on){ e.preventDefault(); hidePart(selId); }\n  else if((e.ctrlKey||e.metaKey)&&e.key.toLowerCase()==='z'&&hidden.length){ e.preventDefault(); hidden.pop(); updateVisibility(); paint(); } });")
# reset on sex switch
R("select(null); isoId=null; hoverId=null;\n  for(const s in groups)", "select(null); isoId=null; hoverId=null; hidden.length=0;\n  for(const s in groups)")
open(p,'w').write(s); print('ok')
