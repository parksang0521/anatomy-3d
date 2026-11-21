cd /home/claude/data && python3 - <<'PY'
t=open('index_tpl.html').read()
t=t.replace('/*INFO*/',open('info_v1.js').read()).replace('/*INFO_MV*/',open('info_mv.js').read()).replace('/*INFO_NV*/',open('info_nv.js').read()).replace("INFO.cerebrum = INFO.cerebrum;\n","").replace("p.ko.replace(/^(왼쪽|오른쪽) /,'')","p.ko.replace(/^(왼쪽 |오른쪽 |왼|오른)/,'')")
open('/home/claude/anatomy-3d/index.html','w').write(t)
PY
cd /home/claude/test && rm -rf site/models && cp -r /home/claude/anatomy-3d/models site/ && sed -e 's#https://cdn.jsdelivr.net/npm/three@0.160.0/#/node_modules/three/#g' -e 's#<link href="https://fonts[^>]*>##' /home/claude/anatomy-3d/index.html > site/index.html
curl -s -o /dev/null --noproxy localhost http://localhost:8124/index.html || (cd /home/claude/test/site && nohup python3 -m http.server 8124 >/dev/null 2>&1 &); sleep 1
