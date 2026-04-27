import json
with open('Ficheros TGD de pruebas/resultado.json', 'r', encoding='utf-16') as f:
    data = json.load(f)
for p in ['2141HJT', '5988HDJ', '7487HGN', '2965 JMK']:
    v1 = data.get('card_vehicles_used_1', {})
    recs = v1.get('card_vehicle_records', [])
    for r in recs:
        if r.get('vehicle_registration', {}).get('vehicle_registration_number') == p:
            print(f"{p}: {r.get('vehicle_first_use')} -> {r.get('vehicle_last_use')}")
