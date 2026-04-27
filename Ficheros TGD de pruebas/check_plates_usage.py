import pandas as pd
cols = ['Tarjeta', 'Matrícula', 'Actividad', 'Inicio', 'Fin', 'Ranura', 'Estado', 'Régimen']
original = pd.read_csv('Ficheros TGD de pruebas/original_data.csv', names=cols)
for p in ['2141HJT', '2965JMK', '5988HDJ', '7487HGN']:
    rows = original[original['Matrícula'] == p]
    if not rows.empty:
        print(f"{p} used in {len(rows)} rows. First one: {rows.iloc[0]['Inicio']}")
    else:
        print(f"{p} NOT used in original report")
