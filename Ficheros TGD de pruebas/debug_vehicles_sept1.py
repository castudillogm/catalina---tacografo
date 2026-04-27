import json
with open('Ficheros TGD de pruebas/resultado.json', 'r', encoding='utf-16') as f:
    data = json.load(f)
for gen in [1, 2]:
    key = f'card_vehicles_used_{gen}'
    if key in data and data[key] and 'card_vehicle_records' in data[key]:
        for v in data[key]['card_vehicle_records']:
            if '2025-09-01' in str(v.get('vehicle_first_use')):
                print(f"{key}: {v.get('vehicle_first_use')} -> {v.get('vehicle_last_use')}: {v.get('vehicle_registration', {}).get('vehicle_registration_number')}")
