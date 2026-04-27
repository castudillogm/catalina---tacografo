import pandas as pd
import os

def load_pseudo_excel(path):
    dfs = pd.read_html(path, encoding='windows-1252')
    df = dfs[0]
    # Find row with 'Tarjeta'
    headers = None
    for i in range(min(5, len(df))):
        if 'Tarjeta' in str(df.iloc[i].values):
            headers = [str(c).strip() for c in df.iloc[i]]
            df = df.iloc[i+1:].reset_index(drop=True)
            df.columns = headers
            break
    if headers is None:
        # Fallback to current columns stripped
        df.columns = [str(c).strip() for c in df.columns]
    return df

df_of = load_pseudo_excel('Ficheros TGD de pruebas/C_E18237829W000003_E_20260422_0517.tgd_ACTIVIDADES.xls')
df_fo = load_pseudo_excel('Ficheros TGD de pruebas/resultado_fomento_html.xls')

days_of = df_of['Inicio'].str.split(' ').str[0].value_counts().sort_index()
days_fo = df_fo['Inicio'].str.split(' ').str[0].value_counts().sort_index()

for day in sorted(set(days_of.index) | set(days_fo.index)):
    of_count = days_of.get(day, 0)
    fo_count = days_fo.get(day, 0)
    if of_count != fo_count:
        print(f"Day {day}: Oficial={of_count}, Fomento={fo_count} | Diff={of_count - fo_count}")
