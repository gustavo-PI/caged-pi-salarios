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
    print("Processando dados com filtros da nova metodologia...")

    chunks_final = []
    linhas_total = 0

    for chunk in pd.read_csv(
        csv_path,
        sep=";",
        encoding="utf-8",
        chunksize=500_000,
        low_memory=False
    ):
        # 1. Garante a tipagem numérica usando os nomes exatos das colunas do CAGED (com acentos)
        chunk["uf"] = pd.to_numeric(chunk["uf"], errors="coerce")
        chunk["saldomovimentação"] = pd.to_numeric(chunk["saldomovimentação"], errors="coerce")
        chunk["indicadordeforadoprazo"] = pd.to_numeric(chunk["indicadordeforadoprazo"], errors="coerce")
        chunk["indtrabintermitente"] = pd.to_numeric(chunk["indtrabintermitente"], errors="coerce")
        chunk["unidadesaláriocódigo"] = pd.to_numeric(chunk["unidadesaláriocódigo"], errors="coerce")
        
        # Tratamento do salário antes do filtro numérico
        chunk["salário"] = (
            chunk["salário"]
            .astype(str)
            .str.replace(",", ".", regex=False)
        )
        chunk["salário"] = pd.to_numeric(chunk["salário"], errors="coerce")

        # 2. Aplicação Rigorosa dos Filtros da Metodologia com os nomes corretos das colunas
        mascara = (
            (chunk["uf"] == 22) &                        # Mantém o escopo no Piauí
            (chunk["saldomovimentação"] == 1) &          # Apenas Admissões
            (chunk["indicadordeforadoprazo"] == 0) &     # Declarações no Prazo
            (chunk["indtrabintermitente"] == 0) &        # Exclui Trabalho Intermitente
            (chunk["unidadesaláriocódigo"] == 5) &       # Padronização: Apenas Salário Mensal
            (chunk["salário"] > 0)                       # Salários Válidos
        )

        chunk_filtrado = chunk[mascara].copy()

        if chunk_filtrado.empty:
            continue

        # 3. Isola apenas as 3 colunas necessárias para o seu banco de dados
        chunk_filtrado = chunk_filtrado[["município", "cbo2002ocupação", "salário"]]

        # 4. Renomeia de forma limpa para salvar no Supabase sem caracteres especiais
        chunk_filtrado = chunk_filtrado.rename(columns={
            "município": "municipio",
            "cbo2002ocupação": "cbo",
            "salário": "salario"
        })

        linhas_total += len(chunk_filtrado)
        chunks_final.append(chunk_filtrado)

    if not chunks_final:
        raise Exception("Nenhum dado válido do Piauí atendeu aos critérios da metodologia.")

    # Consolida todos os lotes limpos na memória e retorna diretamente
    df_final = pd.concat(chunks_final, ignore_index=True)
    print(f"Total de linhas processadas e salvas (PI): {linhas_total}")
    
    return df_final


def run_transformation(file_path, mes, ano):
    extrai_arquivo_zipado(file_path)
    arquivo_dados = encontra_arquivo_dados()
    df = processar_csv(arquivo_dados)
    
    mes_limpo = str(mes)[-2:]
    
    df['mes'] = int(mes_limpo)
    df['ano'] = int(ano)
    
    return df