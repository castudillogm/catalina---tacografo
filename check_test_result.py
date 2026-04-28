import pandas as pd
df = pd.read_excel(r'Ficheros TGD de pruebas\test_processed.xlsx')
row = df[df['Dia'] == '21/04/2026'].iloc[0]
print(f"Dia: {row['Dia']} | Inicio: {row['Inicio Jornada']} | Fin: {row['Fin Jornada']} | Descansos: {row['Descansos']} | Dif: {row['Dif JOR-DES']}")
