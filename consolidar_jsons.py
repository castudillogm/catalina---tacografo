import json
import os
import sys

def get_card_number(data):
    """Extrae el número de tarjeta del JSON."""
    paths = [
        ['card_identification_and_driver_card_holder_identification_1', 'card_identification', 'card_number'],
        ['card_identification_and_driver_card_holder_identification_2', 'card_identification', 'card_number'],
        ['driver_card_application_identification_1', 'card_number'],
    ]
    for path in paths:
        val = data
        for key in path:
            if isinstance(val, dict):
                val = val.get(key)
            else:
                val = None
                break
        if val:
            return val
    return "UNKNOWN_DRIVER"

def consolidate(input_dir, output_dir):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    drivers_data = {}

    for filename in os.listdir(input_dir):
        if not filename.endswith('.tgd.json'):
            continue
            
        filepath = os.path.join(input_dir, filename)
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception as e:
            print(f"Error leyendo {filename}: {e}")
            continue

        card_no = get_card_number(data)
        if card_no not in drivers_data:
            drivers_data[card_no] = {
                'base': data,
                'activities': {},
                'places': {}
            }

        for gen in [1, 2]:
            act_key = f'card_driver_activity_{gen}'
            if act_key in data and isinstance(data[act_key], dict):
                records = data[act_key].get('decoded_activity_daily_records')
                if records:
                    for rec in records:
                        date = rec.get('activity_record_date')
                        if date:
                            drivers_data[card_no]['activities'][date] = rec

            place_key = f'card_place_daily_work_period_{gen}'
            if place_key in data and isinstance(data[place_key], dict):
                records = data[place_key].get('place_daily_work_period_records')
                if records:
                    for rec in records:
                        entry_time = rec.get('entry_time') or rec.get('place_record', {}).get('entry_time')
                        entry_type = rec.get('entry_type_daily_work_period') or rec.get('place_record', {}).get('entry_type_daily_work_period')
                        if entry_time:
                            key = f"{entry_time}_{entry_type}"
                            drivers_data[card_no]['places'][key] = rec

    for card_no, bundle in drivers_data.items():
        base = bundle['base']
        sorted_activities = [bundle['activities'][d] for d in sorted(bundle['activities'].keys())]
        sorted_places = [bundle['places'][k] for k in sorted(bundle['places'].keys())]

        for gen in [1, 2]:
            act_key = f'card_driver_activity_{gen}'
            if act_key in base and isinstance(base[act_key], dict):
                base[act_key]['decoded_activity_daily_records'] = sorted_activities
            
            place_key = f'card_place_daily_work_period_{gen}'
            if place_key in base and isinstance(base[place_key], dict):
                base[place_key]['place_daily_work_period_records'] = sorted_places

        output_filename = f"{card_no}_Consolidado.json"
        output_path = os.path.join(output_dir, output_filename)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(base, f, indent=2, ensure_ascii=False)
        print(f"CONSOLIDATED_FILE:{output_filename}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        sys.exit(1)
    consolidate(sys.argv[1], sys.argv[2])
