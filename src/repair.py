# -*- coding: utf-8 -*-
"""Re-file STEP2/STEP3 blocks that the two-column PDF put under the wrong UNIT header.

Rule learned from c1 PART2 CH1: within one chapter, the k-th STEP-n block in *page*
order belongs to the k-th unit in *unit-number* order.  Also repairs blocks whose
items got rotated (labels like 10,11,12,1,2,...).
"""
import json, io, os, re, sys
from collections import Counter
sys.stdout.reconfigure(encoding='utf-8')

D = os.path.dirname(os.path.abspath(__file__))
u = json.load(io.open(os.path.join(D, 'data.json'), encoding='utf-8'))

def unum(x):
    m = re.search(r'UNIT\s*(\d+)', x['unit'], re.I)
    return int(m.group(1)) if m else 999

def runs_of(items):
    """split a unit's same-step items into blocks; a block ends when the label stops rising"""
    out, cur, prev = [], [], 0
    for it in items:
        n = int(it['label']) if it['label'].isdigit() else prev + 1
        if cur and n <= prev:
            out.append(cur); cur = []
        cur.append(it); prev = n
    if cur: out.append(cur)
    return out

def rotated_fix(block):
    """10,11,12,1..9  ->  1..12 (only when labels form a clean rotation)"""
    labs = [int(i['label']) for i in block if i['label'].isdigit()]
    if len(labs) != len(block): return block
    s = sorted(block, key=lambda i: int(i['label']))
    if [int(i['label']) for i in s] == list(range(1, len(s) + 1)): return s
    return block

groups = {}
for gi, x in enumerate(u):
    groups.setdefault((x['book'], x['part'], x['chapter']), []).append(gi)

moved = fixed_rot = skipped = 0
report = []
SKIP_BOOKS = {'c1'}   # c1 was repaired by hand already; re-running would undo it
for key, gis in groups.items():
    if key[0] in SKIP_BOOKS: continue
    units = [u[g] for g in gis]
    by_num = sorted(units, key=unum)
    for step in (2, 3):
        blocks = []
        for x in units:                                   # page order
            blocks.extend(runs_of([i for i in x['items'] if i['step'] == step]))
        if not blocks: continue
        targets = [x for x in by_num]
        if len(blocks) != len(targets):
            skipped += 1
            report.append('  SKIP %-6s %-30s step%d: %d blocks vs %d units'
                          % (key[0], key[2][:30], step, len(blocks), len(targets)))
            continue
        before = {id(x): [i['en'] for i in x['items'] if i['step'] == step] for x in units}
        for x, b in zip(targets, blocks):
            b = rotated_fix(b)
            keep = [i for i in x['items'] if i['step'] != step]
            s1 = [i for i in keep if i['step'] == 1]
            rest = [i for i in keep if i['step'] not in (1,)]
            x['items'] = s1 + (b if step == 2 else rest) + (rest if step == 2 else b)
        for x in units:
            if [i['en'] for i in x['items'] if i['step'] == step] != before[id(x)]: moved += 1

for x in u:                                               # final tidy: rotation inside a unit
    if x['book'] in SKIP_BOOKS: continue
    for step in (2, 3):
        blk = [i for i in x['items'] if i['step'] == step]
        if not blk: continue
        f = rotated_fix(blk)
        if f != blk:
            fixed_rot += 1
            others = [i for i in x['items'] if i['step'] != step]
            s1 = [i for i in others if i['step'] == 1]
            rest = [i for i in others if i['step'] != 1]
            x['items'] = s1 + (f if step == 2 else rest) + (rest if step == 2 else f)

print('blocks re-filed in %d units | rotations fixed: %d | chapters skipped: %d' % (moved, fixed_rot, skipped))
for r in report: print(r)

print('\n=== unit sizes after repair ===')
for b in ['c1', 'c2', 'c3', 'daily']:
    print(' %-6s %s' % (b, sorted(Counter(len(x['items']) for x in u if x['book'] == b).items())))

print('\n=== units with non-sequential STEP2 labels ===')
bad = 0
for gi, x in enumerate(u):
    labs = [int(i['label']) for i in x['items'] if i['step'] == 2 and i['label'].isdigit()]
    if labs and labs != list(range(1, len(labs) + 1)):
        bad += 1
        if bad <= 20: print('  gi=%-4d %-6s %-40s %s' % (gi, x['book'], x['unit'][:40], labs))
print('  total:', bad)

json.dump(u, io.open(os.path.join(D, 'data.json'), 'w', encoding='utf-8'), ensure_ascii=False)
