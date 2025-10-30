import json
from collections import Counter
p = r'c:\PRUEBAS\CRAWLER-EVENTO\data\eventos_raw\elbalcon_mateo.json'
obj = json.load(open(p, encoding='utf-8'))
items = obj.get('items', [])
visited = obj.get('metadata', {}).get('visited_urls', [])
print('visited count:', len(visited))
v_dates = [u for u in visited if 'f_inicio' in u or 'f_fin' in u or 'from=' in u or 'start=' in u]
print('visited with date params:', len(v_dates))
for u in v_dates[:40]:
    print('-', u)
ctr = Counter()
for it in items:
    ds = it.get('date_start') or it.get('date') or '(no-date)'
    ctr[ds] += 1
print('\nTop dates in raw items:')
for k, c in ctr.most_common(30):
    print(k, c)

for d in ('2025-10-29', '2025-10-30', '2025-10-31'):
    sample = [it for it in items if it.get('date_start') == d or it.get('date_end') == d or (it.get('date') == d)]
    print(f'\nSamples for {d}: count={len(sample)}')
    for it in sample[:15]:
        print('-', (it.get('title') or '')[:140], it.get('date_start'), it.get('link'))

# Check processed agrupados
pp = r'c:\PRUEBAS\CRAWLER-EVENTO\data\processed\eventos_por_dia.json'
try:
    proc = json.load(open(pp, encoding='utf-8'))
    for d in ('2025-10-29', '2025-10-30', '2025-10-31'):
        lst = proc.get(d, [])
        print(f"processed {d}: {len(lst)} items")
except FileNotFoundError:
    print('processed file not found')
