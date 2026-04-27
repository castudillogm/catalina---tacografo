import json
from datetime import datetime, timedelta

def find_exact_vehicle(vehicles, start_time_utc):
    for v in vehicles:
        if v['start'] - timedelta(minutes=1) <= start_time_utc <= v['end'] + timedelta(minutes=1):
            return v['plate']
    return None

with open('Ficheros TGD de pruebas/resultado.json', 'r', encoding='utf-16') as f:
    data = json.load(f)

vehicles = []
for gen in [1, 2]:
    key = f'card_vehicles_used_{gen}'
    if key in data and data[key] and 'card_vehicle_records' in data[key]:
        for v in data[key]['card_vehicle_records']:
            try:
                start = datetime.fromisoformat(v['vehicle_first_use'].replace('Z', '+00:00')).replace(tzinfo=None)
                end = datetime.fromisoformat(v['vehicle_last_use'].replace('Z', '+00:00')).replace(tzinfo=None)
                num = v.get('vehicle_registration', {}).get('vehicle_registration_number', '').replace(' ', '').strip()
                vehicles.append({'start': start, 'end': end, 'plate': num})
            except:
                continue

target_plates = ['2141HJT', '5988HDJ', '7487HGN', '2965JMK']
found_usage = {p: False for p in target_plates}

for gen in [1, 2]:
    key = f'card_driver_activity_{gen}'
    if key in data and data[key] and 'decoded_activity_daily_records' in data[key]:
        for day in data[key]['decoded_activity_daily_records']:
            base_date = datetime.fromisoformat(day['activity_record_date'].replace('Z', '+00:00')).replace(tzinfo=None)
            for act in day['activity_change_info']:
                start_utc = base_date + timedelta(minutes=act['minutes'])
                plate = find_exact_vehicle(vehicles, start_utc)
                if plate in target_plates:
                    found_usage[plate] = True

print('Usage found in activities:', found_usage)
