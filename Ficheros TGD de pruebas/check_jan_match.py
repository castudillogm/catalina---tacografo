import json
from datetime import datetime
with open('Ficheros TGD de pruebas/resultado.json', 'r', encoding='utf-16') as f:
    data = json.load(f)

target = datetime(2026, 1, 16, 5, 0) # 06:00 Local

for gen in [1, 2]:
    for v in data[f'card_vehicles_used_{gen}']['card_vehicle_records']:
        start = datetime.fromisoformat(v['vehicle_first_use'].replace('Z', '+00:00')).replace(tzinfo=None)
        end_str = v.get('vehicle_last_use')
        if end_str:
            end = datetime.fromisoformat(end_str.replace('Z', '+00:00')).replace(tzinfo=None)
            if start <= target <= end:
                print(f"MATCH GEN {gen}: {v['vehicle_registration']['vehicle_registration_number']} | {start} -> {end}")
        else:
            if start <= target:
                print(f"MATCH GEN {gen} (OPEN): {v['vehicle_registration']['vehicle_registration_number']} | {start}")
