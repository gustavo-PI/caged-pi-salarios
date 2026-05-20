import os
import pandas as pd
import py7zr

RAW_PATH = "data/raw"


def extrai_arquivo_zipado(file_path):
    print(f"Extraindo arquivo {file_path}...")
    with py7zr.SevenZipFile(file_path, mode='r') as z:
        z.extractall(path=RAW_PATH)


def encontra_arquivo_dados():
    for root, dirs, files in os.walk(RAW_PATH):
        for file in files:
            if file.endswith(".txt"):
                caminho = os.path.join(root, file)
                print(f"Arquivo de dados localizado: {caminho}")
                return caminho
    raise Exception("Arquivo de dados não encontrado após extração.")


def processar_csv(csv_path):

    chunks_final = []
    linhas_total = 0

    for chunk in pd.read_csv(
        csv_path,
        sep=";",
        encoding="utf-8",
        chunksize=500_000,
        low_memory=False
    ):
        # tipagem numérica
        chunk["uf"] = pd.to_numeric(chunk["uf"], errors="coerce")
        chunk["saldomovimentação"] = pd.to_numeric(chunk["saldomovimentação"], errors="coerce")
        chunk["indicadordeforadoprazo"] = pd.to_numeric(chunk["indicadordeforadoprazo"], errors="coerce")
        chunk["indtrabintermitente"] = pd.to_numeric(chunk["indtrabintermitente"], errors="coerce")
        chunk["unidadesaláriocódigo"] = pd.to_numeric(chunk["unidadesaláriocódigo"], errors="coerce")
        
        # Correção da vírgula decimal do salário
        chunk["salário"] = chunk["salário"].astype(str).str.replace(",", ".", regex=False)
        chunk["salário"] = pd.to_numeric(chunk["salário"], errors="coerce")

        # 2. Filtros
        mascara = (
            (chunk["uf"] == 22) &                         # Apenas Piauí
            (chunk["saldomovimentação"] == 1) &           # Apenas Admissões
            (chunk["indicadordeforadoprazo"] == 0) &      # Apenas no Prazo
            (chunk["indtrabintermitente"] == 0) &         # Exclui Intermitentes
            (chunk["unidadesaláriocódigo"] == 5) &        # Apenas Salário Mensal
            (chunk["salário"] > 0)                        # Salários maiores que zero
        )

        chunk_filtrado = chunk[mascara].copy()

        if chunk_filtrado.empty:
            continue

        # seleção de colunas para o Supabase
        chunk_filtrado = chunk_filtrado[["município", "cbo2002ocupação", "salário"]]
        chunk_filtrado = chunk_filtrado.rename(columns={
            "município": "municipio",
            "cbo2002ocupação": "cbo",
            "salário": "salario"
        })

        linhas_total += len(chunk_filtrado)
        chunks_final.append(chunk_filtrado)

    if not chunks_final:
        raise Exception("Nenhum registro atendeu aos critérios da metodologia para o PI.")

    df_final = pd.concat(chunks_final, ignore_index=True)
    print(f"Total de registros filtrados para o PI: {linhas_total}")
    
    return df_final


def run_transformation(file_path, mes, ano):

    extrai_arquivo_zipado(file_path)
    arquivo_dados = encontra_arquivo_dados()
    df = processar_csv(arquivo_dados)
    
    df['mes'] = int(str(mes)[-2:])
    df['ano'] = int(ano)
    
    if os.path.exists(arquivo_dados):
        os.remove(arquivo_dados)
        print(f"Arquivo temporário {arquivo_dados} removido para liberar espaço.")
        
    return df