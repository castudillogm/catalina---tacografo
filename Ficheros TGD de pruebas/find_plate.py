import json
with open('Ficheros TGD de pruebas/resultado.json', 'r', encoding='utf-16') as f:
    data = json.load(f)

def find_key(obj, target, path=""):
    if isinstance(obj, dict):
        for k, v in obj.items():
            find_key(v, target, f"{path}.{k}" if path else k)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            find_key(v, target, f"{path}[{i}]")
    elif str(obj) == target:
        print(f"Found at: {path}")

find_key(data, "1185LFS")
