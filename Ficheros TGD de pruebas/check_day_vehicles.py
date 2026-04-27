import json
with open('Ficheros TGD de pruebas/resultado.json', 'r', encoding='utf-16') as f:
    data = json.load(f)
for gen in [1, 2]:
    key = f'card_vehicles_used_{gen}'
    recs = data.get(key, {}).get('card_vehicle_records', [])
    for r in recs:
        p = r.get('vehicle_registration', {}).get('vehicle_registration_number')
        if p in ['1185LFS', '2141HJT']:
            if '2026-03-26' in r.get('vehicle_first_use'):
                print(f"Gen {gen} {p}: {r.get('vehicle_first_use')} -> {r.get('vehicle_last_use')}")
