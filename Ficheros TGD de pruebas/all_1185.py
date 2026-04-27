import json
with open('Ficheros TGD de pruebas/resultado.json', 'r', encoding='utf-16') as f:
    data = json.load(f)

recs = []
for gen in [1, 2]:
    for v in data[f'card_vehicles_used_{gen}']['card_vehicle_records']:
        recs.append(v)

recs.sort(key=lambda x: x['vehicle_first_use'])

for v in recs:
    num = v['vehicle_registration']['vehicle_registration_number']
    start = v['vehicle_first_use']
    end = v['vehicle_last_use']
    if '1185LFS' in num:
        print(f"{num} | {start} -> {end}")
