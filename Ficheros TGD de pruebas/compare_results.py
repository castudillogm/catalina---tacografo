import pandas as pd
import os

def load_pseudo_excel(path, name):
    try:
        # Read HTML tables from the file
        dfs = pd.read_html(path, encoding='windows-1252')
        if not dfs:
            return None
        df = dfs[0]
        
        # Robust header finding
        header_row_idx = -1
        for i in range(min(10, len(df))):
            row_str = " ".join([str(v) for v in df.iloc[i].values])
            if 'Tarjeta' in row_str and 'Actividad' in row_str:
                header_row_idx = i
                break
        
        if header_row_idx != -1:
            df.columns = [str(c).strip() for c in df.iloc[header_row_idx]]
            df = df.iloc[header_row_idx+1:].reset_index(drop=True)
        else:
            # Maybe the columns are already headers?
            df.columns = [str(c).strip() for c in df.columns]
            if 'Tarjeta' not in df.columns:
                 print(f"Warning: Could not find headers in {name}")
        
        # Convert all to string and strip
        df = df.astype(str).apply(lambda x: x.str.strip())
        return df
    except Exception as e:
        print(f"Error reading {name}: {e}")
        return None

def compare():
    oficial_path = 'Ficheros TGD de pruebas/C_E18237829W000003_E_20260422_0517.tgd_ACTIVIDADES.xls'
    fomento_path = 'Ficheros TGD de pruebas/resultado_fomento_html.xls'
    
    df_of = load_pseudo_excel(oficial_path, "Oficial")
    df_fo = load_pseudo_excel(fomento_path, "Fomento")

    if df_of is None or df_fo is None:
        return

    print(f"Oficial: {len(df_of)} rows")
    print(f"Fomento: {len(df_fo)} rows")

    cols = ['Tarjeta', 'Matrícula', 'Actividad', 'Inicio', 'Fin', 'Ranura', 'Estado', 'Régimen']
    
    # Sort just in case (though they should be in order)
    # Actually, don't sort yet, let's see if they align naturally.
    
    diffs = 0
    max_rows = min(len(df_of), len(df_fo))
    
    for i in range(max_rows):
        row_of = df_of.iloc[i]
        row_fo = df_fo.iloc[i]
        
        row_diffs = []
        for col in cols:
            if col not in row_of or col not in row_fo:
                row_diffs.append(f"Missing column {col}")
                continue
            v_of = row_of[col]
            v_fo = row_fo[col]
            if v_of != v_fo:
                row_diffs.append(f"{col}: {repr(v_of)} != {repr(v_fo)}")
        
        if row_diffs:
            print(f"Diff at row {i} (Oficial {row_of['Inicio']}):")
            for d in row_diffs:
                print(f"  {d}")
            diffs += 1
        
        if diffs > 50:
            print("Too many diffs, stopping...")
            break

    if diffs == 0 and len(df_of) == len(df_fo):
        print("100% IDENTICAL! PERFECT!")
    else:
        print(f"Total rows with diffs: {diffs}")

if __name__ == '__main__':
    compare()
