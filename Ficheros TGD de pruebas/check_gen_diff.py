import json
with open('Ficheros TGD de pruebas/resultado.json', 'r', encoding='utf-16') as f:
    data = json.load(f)
for gen in [1, 2]:
    recs = data.get(f'card_driver_activity_{gen}', {}).get('decoded_activity_daily_records', [])
    for rec in recs:
        if rec.get('activity_record_date') == '2026-01-16T00:00:00Z':
            print(f"Gen {gen}: {len(rec.get('activity_change_info'))} records")
            for info in rec.get('activity_change_info'):
                print(f"  {info}")
