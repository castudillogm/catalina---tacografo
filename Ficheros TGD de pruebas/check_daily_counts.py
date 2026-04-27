import pandas as pd
import os

def load_pseudo_excel(path, is_oficial=True):
    dfs = pd.read_html(path, encoding='windows-1252')
    df = dfs[0]
    if is_oficial:
        df.columns = [str(c).strip() for c in df.columns]
    else:
        df.columns = [str(c).strip() for c in df.iloc[0]]
        df = df.iloc[1:]
    return df

df_of = load_pseudo_excel('Ficheros TGD de pruebas/C_E18237829W000003_E_20260422_0517.tgd_ACTIVIDADES.xls')
df_fo = load_pseudo_excel('Ficheros TGD de pruebas/resultado_fomento_html.xls', is_oficial=False)

days_of = df_of['Inicio'].str.split(' ').str[0].value_counts().sort_index()
days_fo = df_fo['Inicio'].str.split(' ').str[0].value_counts().sort_index()

total_of = 0
total_fo = 0
for day in sorted(set(days_of.index) | set(days_fo.index)):
    if day == 'Inicio': continue
    c_of = days_of.get(day, 0)
    c_fo = days_fo.get(day, 0)
    total_of += c_of
    total_fo += c_fo
    if c_of != c_fo:
        print(f"{day}: {c_of} vs {c_fo} (Diff {c_of - c_fo})")

print(f"\nTotal Oficial: {total_of}")
print(f"Total Fomento: {total_fo}")
