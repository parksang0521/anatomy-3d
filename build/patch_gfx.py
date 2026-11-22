t=open('index_tpl.html').read()
def R(a,b):
    global t
    assert a in t, 'MISSING: '+a[:90]; t=t.replace(a,b,1)
R("""import { OrbitControls } from 'three/addons/controls/OrbitControls.js';""","""import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js';
import { EffectComposer } from 'three/addons/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/addons/postprocessing/RenderPass.js';
import { GTAOPass } from 'three/addons/postprocessing/GTAOPass.js';
import { OutlinePass } from 'three/addons/postprocessing/OutlinePass.js';
import { OutputPass } from 'three/addons/postprocessing/OutputPass.js';""")
R("""renderer.toneMapping=THREE.ACESFilmicToneMapping; renderer.toneMappingExposure=1.0;""","""renderer.toneMapping=THREE.AgXToneMapping; renderer.toneMappingExposure=1.15;""")
R("""scene.add(new THREE.HemisphereLight(0xeaf2ff,0x1a2233,1.0));
const key=new THREE.DirectionalLight(0xffffff,1.8); key.position.set(1,3,2.5); scene.add(key);
const fill=new THREE.DirectionalLight(0x9fc4ff,0.7); fill.position.set(-2,1,-1.5); scene.add(fill);
const rim=new THREE.DirectionalLight(0xffe2c4,0.6); rim.position.set(0,1,-3); scene.add(rim);
const headLight=new THREE.DirectionalLight(0xffffff,0.35); camera.add(headLight); scene.add(camera);""",
"""{ const pm=new THREE.PMREMGenerator(renderer); scene.environment=pm.fromScene(new RoomEnvironment(),0.04).texture; pm.dispose(); }
scene.add(new THREE.HemisphereLight(0xeaf2ff,0x1a2233,0.35));
const key=new THREE.DirectionalLight(0xfff6ea,2.2); key.position.set(1.2,3,2.5); scene.add(key);
const fill=new THREE.DirectionalLight(0x9fc4ff,0.6); fill.position.set(-2,1,-1.5); scene.add(fill);
const rim=new THREE.DirectionalLight(0xffe2c4,0.9); rim.position.set(0,1.5,-3); scene.add(rim);
const headLight=new THREE.DirectionalLight(0xffffff,0.45); camera.add(headLight); scene.add(camera);
/* 후처리: 앰비언트 오클루전 + 선택 윤곽선 (고화질) */
const HQ_DEFAULT=!matchMedia('(pointer:coarse)').matches && innerWidth>820;
let HQ=HQ_DEFAULT; try{ const s=localStorage.getItem('anat-hq'); if(s!=null) HQ=s==='1'; }catch(e){}
const rt=new THREE.WebGLRenderTarget(4,4,{type:THREE.HalfFloatType,samples:4});
const composer=new EffectComposer(renderer,rt);
composer.addPass(new RenderPass(scene,camera));
const gtao=new GTAOPass(scene,camera,4,4); gtao.output=GTAOPass.OUTPUT.Default; gtao.blendIntensity=0.9;
gtao.updateGtaoMaterial({radius:0.06,distanceExponent:1.4,thickness:0.6,scale:1.0,samples:16}); gtao.updatePdMaterial({lumaPhi:10,depthPhi:2,normalPhi:3,radius:6,rings:2,samples:12});
composer.addPass(gtao);
const outline=new OutlinePass(new THREE.Vector2(4,4),scene,camera);
outline.edgeStrength=4; outline.edgeThickness=1.2; outline.edgeGlow=0.25; outline.visibleEdgeColor.set(0x5eeaff); outline.hiddenEdgeColor.set(0x1e6f80);
composer.addPass(outline);
composer.addPass(new OutputPass());""")
# materials
R("""  const mat=new THREE.MeshStandardMaterial({color:colorOf(p),roughness:p.sys==='skeletal'?.7:.45,metalness:0});""",
"""  const mat=makeMat(p);""")
R("""/* ---------------- 로딩 ---------------- */""","""/* ---------------- 재질 ---------------- */
function makeMat(p){
  const color=colorOf(p), k=p.key||'';
  const base={color,metalness:0,envMapIntensity:0.55};
  if(p.sys==='skeletal'){
    const cart=/cartilage|disk|meniscus/i.test(p.en)||k==='costal'||k==='disk';
    return new THREE.MeshPhysicalMaterial({...base,roughness:cart?0.35:0.62,clearcoat:cart?0.4:0.12,clearcoatRoughness:0.5,sheen:0.25,sheenRoughness:0.8,sheenColor:new THREE.Color(0xfff2dc)});
  }
  if(p.sys==='muscular'){
    const tendon=/tendon|ligament|membrane|tract|linea/i.test(p.en);
    return new THREE.MeshPhysicalMaterial({...base,roughness:tendon?0.35:0.5,clearcoat:tendon?0.5:0.25,clearcoatRoughness:0.45,sheen:tendon?0.2:0.6,sheenRoughness:0.5,sheenColor:new THREE.Color(tendon?0xffffff:0xff9a8a)});
  }
  if(p.sys==='arterial'||p.sys==='venous') return new THREE.MeshPhysicalMaterial({...base,roughness:0.3,clearcoat:0.7,clearcoatRoughness:0.25});
  if(p.sys==='nerves') return new THREE.MeshPhysicalMaterial({...base,roughness:0.42,clearcoat:0.35,clearcoatRoughness:0.4,sheen:0.4,sheenColor:new THREE.Color(0xfff1b0)});
  if(p.sys==='nervous') return new THREE.MeshPhysicalMaterial({...base,roughness:0.45,clearcoat:0.3,clearcoatRoughness:0.5,sheen:0.35,sheenColor:new THREE.Color(0xffd6d0)});
  return new THREE.MeshPhysicalMaterial({...base,roughness:0.38,clearcoat:0.55,clearcoatRoughness:0.3,sheen:0.3,sheenColor:new THREE.Color(0xffe0d8)});
}

/* ---------------- 로딩 ---------------- */""")
# paint: lighter emissive + outline selection
R("""    if(p.id===hoverId){c=0x3b82f6;i=0.4;}
    if(p.id===selId){c=0x22d3ee;i=0.6;}""","""    if(p.id===hoverId){c=0x3b82f6;i=HQ?0.18:0.4;}
    if(p.id===selId){c=0x22d3ee;i=HQ?0.28:0.6;}""")
R("""  document.querySelectorAll('.item').forEach(b=>b.classList.toggle('on',b.dataset.id===selId));
}""","""  document.querySelectorAll('.item').forEach(b=>b.classList.toggle('on',b.dataset.id===selId));
  outline.selectedObjects = selId&&parts[selId] ? parts[selId].meshes.filter(m=>m.visible) : (quiz.on&&quiz.target&&quiz.type==='name'&&!quiz.answered ? quiz.target.meshes : []);
}""")
# render loop & resize
R("""  controls.update(); renderer.render(scene,camera);""","""  controls.update(); if(HQ) composer.render(); else renderer.render(scene,camera);""")
R("""function resize(){ const w=canvas.clientWidth, h=canvas.clientHeight; if(!w||!h) return; renderer.setSize(w,h,false); camera.aspect=w/Math.max(1,h); camera.updateProjectionMatrix(); }""",
"""function resize(){ const w=canvas.clientWidth, h=canvas.clientHeight; if(!w||!h) return; renderer.setSize(w,h,false); camera.aspect=w/Math.max(1,h); camera.updateProjectionMatrix();
  const pr=renderer.getPixelRatio(); composer.setPixelRatio(pr); composer.setSize(w,h); }""")
# HQ toggle in controls
R("""      <div class="row">자동 회전 <label class="sw"><input id="spin" type="checkbox"><span></span></label></div>""","""      <div class="row">자동 회전 <label class="sw"><input id="spin" type="checkbox"><span></span></label></div>
      <div class="row">고화질 (그림자 음영·윤곽선) <label class="sw"><input id="hq" type="checkbox"><span></span></label></div>""")
R("""document.getElementById('spin').onchange=e=>{ controls.autoRotate=e.target.checked; };""","""document.getElementById('spin').onchange=e=>{ controls.autoRotate=e.target.checked; };
document.getElementById('hq').checked=HQ;
document.getElementById('hq').onchange=e=>{ HQ=e.target.checked; try{ localStorage.setItem('anat-hq',HQ?'1':'0'); }catch(err){} paint(); };""")
open('index_tpl.html','w').write(t); print('ok')
