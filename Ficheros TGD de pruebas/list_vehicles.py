import json
with open('Ficheros TGD de pruebas/resultado.json', 'r', encoding='utf-16') as f:
    data = json.load(f)

print("--- GEN 1 ---")
for i, v in enumerate(data['card_vehicles_used_1']['card_vehicle_records']):
    num = v['vehicle_registration']['vehicle_registration_number']
    start = v['vehicle_first_use']
    end = v['vehicle_last_use']
    if '2025-08' in start or '2025-09' in start:
        print(f"{i}: {num} | {start} -> {end}")

print("\n--- GEN 2 ---")
for i, v in enumerate(data['card_vehicles_used_2']['card_vehicle_records']):
    num = v['vehicle_registration']['vehicle_registration_number']
    start = v['vehicle_first_use']
    end = v['vehicle_last_use']
    if '2025-08' in start or '2025-09' in start:
        print(f"{i}: {num} | {start} -> {end}")
