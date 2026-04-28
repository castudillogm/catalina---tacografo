import json

with open(r'Ficheros TGD de pruebas\test.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

for gen in [1, 2]:
    key = f'card_driver_activity_{gen}'
    if key in data and data[key] and 'decoded_activity_daily_records' in data[key]:
        for day in data[key]['decoded_activity_daily_records']:
            if '2026-04-22' in day.get('activity_record_date', ''):
                print(f"--- GEN {gen} ---")
                print(json.dumps(day, indent=2))
