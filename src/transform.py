import os
import pandas as pd
import py7zr

RAW_PATH = "data/raw"
PROCESSED_PATH = "data/processed"


def extrai_arquivo_zipado(file_path):
    with py7zr.SevenZipFile(file_path, mode='r') as z:
        z.extractall(path=RAW_PATH)


def encontra_arquivo_dados():
    for root, dirs, files in os.walk(RAW_PATH):
        for file in files:
            if file.endswith(".txt"):
                caminho = os.path.join(root, file)
                print(f"Arquivo encontrado: {caminho}")
                return caminho

    raise Exception("Arquivo de dados não encontrado após extração")


def processar_csv(csv_path):
    print("Processando dados...")

    chunks_final = []
    linhas_total = 0

    for chunk in pd.read_csv(
        csv_path,
        sep=";",
        encoding="utf-8",
        chunksize=500_000,
        low_memory=False
    ):
        chunk["uf"] = pd.to_numeric(chunk["uf"], errors="coerce")
        chunk = chunk[chunk["uf"] == 22]

        if chunk.empty:
            continue

        chunk = chunk[["município", "cbo2002ocupação", "salário"]]

        chunk["salário"] = (
            chunk["salário"]
            .astype(str)
            .str.replace(",", ".", regex=False)
        )

        chunk["salário"] = pd.to_numeric(chunk["salário"], errors="coerce")
        chunk = chunk.dropna(subset=["salário"])

        chunk = chunk.rename(columns={
            "município": "municipio",
            "cbo2002ocupação": "cbo",
            "salário": "salario"
        })

        linhas_total += len(chunk)
        chunks_final.append(chunk)

    if not chunks_final:
        raise Exception("Nenhum dado do Piauí foi encontrado")

    df_final = pd.concat(chunks_final, ignore_index=True)

    print(f"Total de linhas processadas (PI): {linhas_total}")
    return df_final


def run_transformation(file_path, mes, ano):
    extrai_arquivo_zipado(file_path)
    arquivo_dados = encontra_arquivo_dados()
    df = processar_csv(arquivo_dados)
    
    # AJUSTE AQUI: 
    # Se 'mes' vier como "202603", convertemos para texto e pegamos os 2 últimos dígitos ("03")
    mes_limpo = str(mes)[-2:]
    
    # colunas de controle gravadas de forma limpa
    df['mes'] = int(mes_limpo)  # Vai virar o número 3
    df['ano'] = int(ano)
    
    return df
