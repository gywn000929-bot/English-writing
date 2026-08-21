# -*- coding: utf-8 -*-
"""Inject data.json + ko_all.json into template2.html and write the app."""
import io, json, os, sys
sys.stdout.reconfigure(encoding='utf-8')

D = os.path.dirname(os.path.abspath(__file__))
OUT = r"C:/Users/manju/OneDrive - Dae-A Electronics (Thailand) Company Limited/문서_드라이브/2608 셋째주/영어로_문장만들기_훈련기.html"

tpl  = io.open(os.path.join(D, 'template2.html'), encoding='utf-8').read()
data = json.load(io.open(os.path.join(D, 'data.json'),   encoding='utf-8'))
ko   = json.load(io.open(os.path.join(D, 'ko_all.json'), encoding='utf-8'))

for x in data:
    x.pop('bookTitle', None)

CLOSE_TAG = '<' + '/'
ESCAPED   = '<' + chr(92) + '/'
def enc(o):
    return json.dumps(o, ensure_ascii=False, separators=(',', ':')).replace(CLOSE_TAG, ESCAPED)

tpl = tpl.replace('const KO = __KO__;',   'const KO = '   + enc(ko)   + ';')
tpl = tpl.replace('const DATA = __DATA__;', 'const DATA = ' + enc(data) + ';')
assert '__KO__' not in tpl and '__DATA__' not in tpl

for out in [OUT, os.path.join(D, 'app.html')]:
    io.open(out, 'w', encoding='utf-8').write(tpl)

tot = sum(len(x['items']) for x in data)
units_ko = sum(1 for x in data
               if any((x['book'] + ':' + str(i) + ':' + str(j)) in ko
                      for i in [data.index(x)] for j in range(len(x['items']))))
print('built %.0f KB | sentences %d | ko %d (%.1f%%)'
      % (len(tpl.encode('utf-8')) / 1024, tot, len(ko), len(ko) / tot * 100))
