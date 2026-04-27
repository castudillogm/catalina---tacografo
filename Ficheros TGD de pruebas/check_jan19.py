import json
with open('Ficheros TGD de pruebas/resultado.json', 'r', encoding='utf-16') as f:
    data = json.load(f)

for gen in [1, 2]:
    for v in data[f'card_vehicles_used_{gen}']['card_vehicle_records']:
        num = v['vehicle_registration']['vehicle_registration_number']
        start = v['vehicle_first_use']
        end = v.get('vehicle_last_use', 'OPEN')
        if '2026-01-19' in start:
            print(f"GEN {gen}: {num} | {start} -> {end}")
