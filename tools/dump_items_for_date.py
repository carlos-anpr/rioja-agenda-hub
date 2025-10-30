import json,sys
p=r'c:\PRUEBAS\CRAWLER-EVENTO\data\eventos_raw\elbalcon_mateo.json'
obj=json.load(open(p,encoding='utf-8'))
items=obj.get('items',[])
d=sys.argv[1] if len(sys.argv)>1 else '2025-10-30'
sel=[it for it in items if it.get('date_start')==d or it.get('date_end')==d or it.get('date')==d]
print('found', len(sel), 'items for', d)
for i,it in enumerate(sel[:30]):
    print('\n--- item', i)
    for k,v in it.items():
        print(k, ':', v)
