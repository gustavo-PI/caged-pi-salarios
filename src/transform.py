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
    raise Exception("Arquivo de dados (.txt) não encontrado após extração.")


def processar_csv(csv_path):
    print("Processando dados em lotes (chunks) com filtros da metodologia...")

    chunks_final = []
    linhas_total = 0

    # Lendo de 500k em 500k para não estourar a memória do servidor
    for chunk in pd.read_csv(
        csv_path,
        sep=";",
        encoding="utf-8",
        chunksize=500_000,
        low_memory=False
    ):
        # 1. Garante a tipagem numérica nas colunas de corte
        chunk["uf"] = pd.to_numeric(chunk["uf"], errors="coerce")
        chunk["saldomovimentação"] = pd.to_numeric(chunk["saldomovimentação"], errors="coerce")
        chunk["indicadordeforadoprazo"] = pd.to_numeric(chunk["indicadordeforadoprazo"], errors="coerce")
        chunk["indtrabintermitente"] = pd.to_numeric(chunk["indtrabintermitente"], errors="coerce")
        chunk["unidadesaláriocódigo"] = pd.to_numeric(chunk["unidadesaláriocódigo"], errors="coerce")
        
        # Correção da vírgula decimal do salário
        chunk["salário"] = chunk["salário"].astype(str).str.replace(",", ".", regex=False)
        chunk["salário"] = pd.to_numeric(chunk["salário"], errors="coerce")

        # 2. Filtros estáveis da metodologia
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

        # 3. Seleção e Renomeação das colunas para o Supabase
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
    # Executa a extração e a transformação
    extrai_arquivo_zipado(file_path)
    arquivo_dados = encontra_arquivo_dados()
    df = processar_csv(arquivo_dados)
    
    # Adiciona as colunas de controle temporal baseadas no que veio do extract.py
    # Forçamos o int() para evitar que o mês vá como texto com zeros à esquerda
    df['mes'] = int(str(mes)[-2:])
    df['ano'] = int(ano)
    
    # BOA PRÁTICA DE PRODUÇÃO: Remove o arquivo .txt gigante para liberar espaço em disco
    if os.path.exists(arquivo_dados):
        os.remove(arquivo_dados)
        print(f"Arquivo temporário {arquivo_dados} removido para liberar espaço.")
        
    return df