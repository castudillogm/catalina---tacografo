import json
with open('Ficheros TGD de pruebas/resultado.json', 'r', encoding='utf-16') as f:
    data = json.load(f)

for key in data.keys():
    if 'card_identification' in key:
        print(f"Key: {key}")
        print(json.dumps(data[key], indent=2)[:500])
