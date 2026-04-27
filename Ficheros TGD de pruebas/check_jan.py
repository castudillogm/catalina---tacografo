import json
with open('Ficheros TGD de pruebas/resultado.json', 'r', encoding='utf-16') as f:
    data = json.load(f)

for v in data['card_vehicles_used_1']['card_vehicle_records']:
    num = v['vehicle_registration']['vehicle_registration_number']
    start = v['vehicle_first_use']
    end = v['vehicle_last_use']
    if '2026-01-15' in start or '2026-01-16' in start:
        print(f"{num} | {start} -> {end}")
