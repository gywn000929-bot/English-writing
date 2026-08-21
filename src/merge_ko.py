# -*- coding: utf-8 -*-
import json,io,re,os,sys,glob
sys.stdout.reconfigure(encoding='utf-8')
D=os.path.dirname(os.path.abspath(__file__))
u=json.load(io.open(os.path.join(D,'data.json'),encoding='utf-8'))
byid={}
for gi,x in enumerate(u):
    for j,it in enumerate(x['items']): byid[x['book']+":"+str(gi)+":"+str(j)]=it['en']
def nz(s):
    s=re.sub(r'[’‘]',"'",s).lower()
    s=re.sub(r'\(\s*=[^)]*\)','',s)
    s=re.sub(r'(?<!\()\s=\s.*$','',s)
    return re.sub(r'\s+',' ',re.sub(r"[^a-z0-9 ]",'',s.replace("'",""))).strip()

# 앱(template2.html)의 norm/stripAlt 와 같은 규칙. nz 보다 엄격해서 — nz 가 지우는
# / - $ & 같은 글자를 그대로 남긴다 — 청크 경계가 그런 글자를 잘라 먹으면 여기서 걸린다.
# nz 만 통과하고 이쪽에서 걸리면, 앱에서는 정답으로 인정되지 않는다.
def app_norm(s):
    s=re.sub(r'[’‘ʼ]',"'",s.lower()); s=re.sub(r'[“”]','"',s)
    return re.sub(r'\s+',' ',re.sub(r'[.,!?;:"()–—]',' ',s)).strip()
def app_strip_alt(s):
    s=re.sub(r'\(\s*=[^)]*\)',' ',s)
    return re.sub(r'(^|[^(])\s=\s[\s\S]*$',r'\1',s)
def app_same(a,b):
    return app_norm(a)==app_norm(b) or app_norm(a)==app_norm(app_strip_alt(b))
ko={}; bad=[]; loose=[]; miss=[]
for f in sorted([f for f in glob.glob(os.path.join(D,'ko*.json')) if not f.endswith('ko_all.json')]):
    part=json.load(io.open(f,encoding='utf-8'))
    for k,v in part.items():
        if k not in byid: miss.append((os.path.basename(f),k)); continue
        joined=' '.join(c[1] for c in v['c'])
        if nz(joined)!=nz(byid[k]): bad.append((k,joined,byid[k]))
        elif not app_same(joined,byid[k]): loose.append((k,joined,byid[k]))
        ko[k]=v
    print('%-14s %4d entries'%(os.path.basename(f),len(part)))
print('\nmerged total: %d | missing ids: %d | MISMATCH: %d | APP-REJECT: %d'
      %(len(ko),len(miss),len(bad),len(loose)))
for m in miss[:10]: print('  missing',m)
for k,a,b in bad[:15]: print('  %s\n     chunks: %s\n     answer: %s'%(k,a,b))
for k,a,b in loose[:15]:
    print('  APP-REJECT %s  (nz 는 통과하지만 앱 채점은 불일치)\n     chunks: %s\n     answer: %s'%(k,a,b))
if not bad and not loose and not miss:
    json.dump(ko,io.open(os.path.join(D,'ko_all.json'),'w',encoding='utf-8'),ensure_ascii=False)
    print('-> ko_all.json written')
