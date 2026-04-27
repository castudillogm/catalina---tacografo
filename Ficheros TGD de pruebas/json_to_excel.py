import json
import pandas as pd
from datetime import datetime, timedelta

def get_card_number(data):
    try:
        val = data.get('card_identification_and_driver_card_holder_identification_1', {}).get('card_identification', {}).get('card_number', '')
        if not val or val == 'UNKNOWN' or val == '0000000000000000':
             val = data.get('card_identification_and_driver_card_holder_identification_2', {}).get('card_identification', {}).get('card_number', 'UNKNOWN')
        return val
    except:
        return 'UNKNOWN'

def extract_vehicles(data):
    vehicles = []
    seen = set()
    for gen in [2, 1]:
        key = f'card_vehicles_used_{gen}'
        if key in data and data[key] and data[key].get('card_vehicle_records'):
            for v in data[key]['card_vehicle_records']:
                try:
                    start_str = v.get('vehicle_first_use')
                    if not start_str: continue
                    end_str = v.get('vehicle_last_use')
                    reg = v.get('vehicle_registration', {})
                    num = reg.get('vehicle_registration_number', 'N.I.').replace(' ', '').strip()
                    
                    ukey = (start_str, end_str, num)
                    if ukey not in seen:
                        start = datetime.fromisoformat(start_str.replace('Z', '+00:00')).replace(tzinfo=None)
                        if end_str:
                            end = datetime.fromisoformat(end_str.replace('Z', '+00:00')).replace(tzinfo=None)
                        else:
                            end = datetime(2099, 12, 31)
                        vehicles.append({'start': start, 'end': end, 'plate': num})
                        seen.add(ukey)
                except Exception:
                    continue
    
    vehicles.sort(key=lambda x: x['start'])
    return vehicles

def find_exact_vehicle(vehicles, start_time_utc):
    # Search from latest to earliest start time.
    # We want the most specific record.
    for v in reversed(vehicles):
        # 1-minute tolerance for card/VU clock misalignment
        if v['start'] - timedelta(minutes=1) <= start_time_utc <= v['end'] + timedelta(minutes=1):
            return v['plate']
    return None

def map_activity(work_type):
    mapping = {0: 'DES', 1: 'DIS', 2: 'TRA', 3: 'CON'}
    return mapping.get(work_type, 'DES')

def to_local_fomento(dt_utc):
    return dt_utc + timedelta(hours=1)

def json_to_fomento_excel(json_path, excel_path):
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except:
        with open(json_path, 'r', encoding='utf-16') as f:
            data = json.load(f)

    tarjeta = get_card_number(data)
    vehicles = extract_vehicles(data)

    activities_by_day = {}
    for gen in [1, 2]:
        key = f'card_driver_activity_{gen}'
        if f'card_driver_activity_{gen}' not in data: continue
        if key in data and data[key] and data[key].get('decoded_activity_daily_records'):
            for day in data[key]['decoded_activity_daily_records']:
                date_str = day.get('activity_record_date', '')
                if not date_str: continue
                try:
                    base_date = datetime.fromisoformat(date_str.replace('Z', '+00:00')).replace(tzinfo=None)
                except: continue
                
                day_acts = []
                infos = day.get('activity_change_info', [])
                for i, act in enumerate(infos):
                    start_min = act.get('minutes', 0)
                    end_min = infos[i+1].get('minutes', 1440) if i + 1 < len(infos) else 1440
                    if start_min >= end_min: continue
                    
                    start_utc = base_date + timedelta(minutes=start_min)
                    end_utc = base_date + timedelta(minutes=end_min)
                    
                    day_acts.append({
                        'start_utc': start_utc,
                        'end_utc': end_utc,
                        'work_type': act.get('work_type', 0),
                        'driver': act.get('driver', True),
                        'team': act.get('team', False),
                        'card_present': act.get('card_present', True)
                    })
                
                if date_str not in activities_by_day:
                    activities_by_day[date_str] = {}
                # Stick to the gen with more data for that day
                if gen not in activities_by_day[date_str] or len(day_acts) > len(activities_by_day[date_str].get(gen, [])):
                    activities_by_day[date_str][gen] = day_acts

    all_activities = []
    for date_str in sorted(activities_by_day.keys()):
        gens = activities_by_day[date_str]
        if 1 in gens and 2 in gens:
            if len(gens[1]) >= len(gens[2]):
                all_activities.extend(gens[1])
            else:
                all_activities.extend(gens[2])
        elif 1 in gens:
            all_activities.extend(gens[1])
        elif 2 in gens:
            all_activities.extend(gens[2])

    rows = []
    last_plate = 'N.I.'
    for act in all_activities:
        start_utc = act['start_utc']
        end_utc = act['end_utc']
        start_local = to_local_fomento(start_utc)
        end_local = to_local_fomento(end_utc)
        
        card_present = act['card_present']
        actividad = map_activity(act['work_type'])
        estado = 'I.' if card_present else 'N.I.'
        
        # Rule: Only include N.I. + DES + Team
        if estado == 'N.I.':
            if actividad != 'DES' or act['team'] == False:
                continue
            
        exact_plate = find_exact_vehicle(vehicles, start_utc)
        
        if exact_plate:
            last_plate = exact_plate
            matricula = exact_plate
        else:
            if estado == 'N.I.':
                matricula = '???????????'
            else:
                matricula = last_plate if last_plate != 'N.I.' else '???????????'
        
        ranura = 'CON.' if act['driver'] else 'SEG.'
        regimen = 'E.' if act['team'] else 'S.'
        
        rows.append({
            'Tarjeta': tarjeta,
            'Matrícula': matricula,
            'Actividad': actividad,
            'Inicio': start_local.strftime('%d/%m/%Y %H:%M'),
            'Fin': end_local.strftime('%d/%m/%Y %H:%M'),
            'Ranura': ranura,
            'Estado': estado,
            'Régimen': regimen
        })

    # NO CONSOLIDATION to match Sede's raw chunks
    df = pd.DataFrame(rows)
    if not df.empty:
        # Match Sede's start: the very first activity with 'I.' status
        first_i_idx = df[df['Estado'] == 'I.'].first_valid_index()
        if first_i_idx is not None:
             df = df.loc[first_i_idx:]
        
        cols_order = ['Tarjeta', 'Matrícula', 'Actividad', 'Inicio', 'Fin', 'Ranura', 'Estado', 'Régimen']
        df = df[cols_order].reset_index(drop=True)

    df.to_excel(excel_path, sheet_name='ACTIVIDADES', index=False)
    html_path = excel_path.replace('.xlsx', '_html.xls')
    html_content = "<html><head><meta charset='windows-1252'></head><body><table border=1>"
    html_content += "<tr>" + "".join([f"<td><b>{c}</b></td>" for c in df.columns]) + "</tr>"
    for _, row in df.iterrows():
        html_content += "<tr>" + "".join([f"<td>{val}</td>" for val in row]) + "</tr>"
    html_content += "</table></body></html>"
    
    with open(html_path, 'w', encoding='windows-1252', errors='replace') as f:
        f.write(html_content)
    
    print(f'Exported {len(df)} rows.')

if __name__ == '__main__':
    import sys
    if len(sys.argv) < 3:
        print("Usage: python json_to_excel.py <json_path> <excel_path>")
    else:
        json_to_fomento_excel(sys.argv[1], sys.argv[2])
