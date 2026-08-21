# -*- coding: utf-8 -*-
"""Re-file STEP2/STEP3 blocks that the two-column PDF put under the wrong UNIT header.

Rule learned from c1 PART2 CH1: within one chapter, the k-th STEP-n block in *page*
order belongs to the k-th unit in *unit-number* order.  Also repairs blocks whose
items got rotated (labels like 10,11,12,1,2,...).

Known limit: when one unit's STEP block got split into two fragments that landed under
two different unit headers, the block count no longer matches the unit count and the
whole chapter is skipped (see the SKIP lines it prints).  c3 CHAPTER 2 was that case and
was re-filed by hand from the label sequences; its units are now stored in unit-number
order so re-running this script leaves them alone.  Still open, same shape:
c3 CHAPTER 8 (12 blocks / 10 units), daily CHAPTER 4 (6 blocks / 5 units).

Worse, a split block can make the counts match by accident, so nothing is skipped and the
identity mapping silently keeps every block under the wrong header.  c3 CHAPTER 7 was that
case: UNIT 4 kept only the tail of its own block (labels 11,12) while its 1..10 sat under
UNIT 5, pushing every later unit's block one unit forward.  8 blocks / 8 units, no warning.
The tell is a block whose labels do not start at 1 — it is the tail of the previous unit's
block, not a block of its own.  Re-filed by hand; CHAPTER 7 now counts 7 blocks / 8 units
(UNIT 8's STEP2 is absent from the extract), so this script skips it from here on.

c3 CHAPTER 8 held three shapes at once: U1/U2/U3 blocks rotated among themselves, U6's
last three items stranded at the end of U5, and U4's STEP1 examples typed as STEP2 (labels
1,2,4).  Re-filed by hand; U2 and U3 were also swapped into unit-number order so the k-th
block really is the k-th unit.  Two sentences the extract never had: U4's STEP1 #3 and
U7's STEP2 #1.  Still open: daily CHAPTER 4 (6 blocks / 5 units).
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

# Every chapter has since been verified (and where needed re-filed) by hand, so the
# automatic pass now has nothing left to fix and plenty left to break: where a chapter's
# units are not stored in unit-number order, the k-th-block-to-k-th-unit rule would move
# correct blocks onto the wrong units.  So this runs as a REPORT by default and only
# re-files with an explicit --apply.  Read the report before ever passing it.
APPLY = '--apply' in sys.argv

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
        if not APPLY: continue
        before = {id(x): [i['en'] for i in x['items'] if i['step'] == step] for x in units}
        for x, b in zip(targets, blocks):
            b = rotated_fix(b)
            keep = [i for i in x['items'] if i['step'] != step]
            s1 = [i for i in keep if i['step'] == 1]
            rest = [i for i in keep if i['step'] not in (1,)]
            x['items'] = s1 + (b if step == 2 else rest) + (rest if step == 2 else b)
        for x in units:
            if [i['en'] for i in x['items'] if i['step'] == step] != before[id(x)]: moved += 1

for x in (u if APPLY else []):                            # final tidy: rotation inside a unit
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

print('%s | blocks re-filed in %d units | rotations fixed: %d | chapters skipped: %d'
      % ('APPLIED' if APPLY else 'report only (--apply 로 실제 재배치)', moved, fixed_rot, skipped))
for r in report: print(r)

print('\n=== 배열 순서가 UNIT 번호 순이 아닌 챕터 (자동 재배치를 걸면 어긋납니다) ===')
for key, gis in groups.items():
    if key[0] in SKIP_BOOKS: continue
    ns = [unum(u[g]) for g in gis]
    if ns != sorted(ns):
        print('  %-6s %-40s %s' % (key[0], (key[2] or '')[:40], ns))

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

if APPLY:
    json.dump(u, io.open(os.path.join(D, 'data.json'), 'w', encoding='utf-8'), ensure_ascii=False)
    print('\n-> data.json 갱신')
else:
    print('\n(data.json 은 건드리지 않았습니다)')
