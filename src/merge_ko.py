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
ko={}; bad=[]; miss=[]
for f in sorted([f for f in glob.glob(os.path.join(D,'ko*.json')) if not f.endswith('ko_all.json')]):
    part=json.load(io.open(f,encoding='utf-8'))
    for k,v in part.items():
        if k not in byid: miss.append((os.path.basename(f),k)); continue
        joined=' '.join(c[1] for c in v['c'])
        if nz(joined)!=nz(byid[k]): bad.append((k,joined,byid[k]))
        ko[k]=v
    print('%-14s %4d entries'%(os.path.basename(f),len(part)))
print('\nmerged total: %d | missing ids: %d | MISMATCH: %d'%(len(ko),len(miss),len(bad)))
for m in miss[:10]: print('  missing',m)
for k,a,b in bad[:15]: print('  %s\n     chunks: %s\n     answer: %s'%(k,a,b))
if not bad and not miss:
    json.dump(ko,io.open(os.path.join(D,'ko_all.json'),'w',encoding='utf-8'),ensure_ascii=False)
    print('-> ko_all.json written')
