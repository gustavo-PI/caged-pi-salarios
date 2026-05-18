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
        # 1. Garante a tipagem numérica das colunas de filtro para evitar falhas de máscara
        chunk["uf"] = pd.to_numeric(chunk["uf"], errors="coerce")
        chunk["saldomovimentacao"] = pd.to_numeric(chunk["saldomovimentacao"], errors="coerce")
        chunk["indicadordeforadoprazo"] = pd.to_numeric(chunk["indicadordeforadoprazo"], errors="coerce")
        chunk["indtrabintermitente"] = pd.to_numeric(chunk["indtrabintermitente"], errors="coerce")
        chunk["unidadesalariocodigo"] = pd.to_numeric(chunk["unidadesalariocodigo"], errors="coerce")
        
        # Tratamento do salário antes do filtro numérico
        chunk["salário"] = (
            chunk["salário"]
            .astype(str)
            .str.replace(",", ".", regex=False)
        )
        chunk["salário"] = pd.to_numeric(chunk["salário"], errors="coerce")

        # 2. Aplicação Rigorosa dos Filtros de Qualidade (Metodologia)
        mascara = (
            (chunk["uf"] == 22) &                       # Mantém o escopo no Piauí
            (chunk["saldomovimentacao"] == 1) &         # Apenas Admissões
            (chunk["indicadordeforadoprazo"] == 0) &     # Declarações no Prazo
            (chunk["indtrabintermitente"] == 0) &        # Exclui Trabalho Intermitente
            (chunk["unidadesalariocodigo"] == 5) &       # Padronização: Apenas Salário Mensal
            (chunk["salário"] > 0)                       # Salários Válidos
        )

        chunk_filtrado = chunk[mascara].copy()

        if chunk_filtrado.empty:
            continue

        # 3. Isola apenas as colunas necessárias para o banco
        chunk_filtrado = chunk_filtrado[["município", "cbo2002ocupação", "salário"]]

        # 4. Renomeia para o padrão do banco de dados
        chunk_filtrado = chunk_filtrado.rename(columns={
            "município": "municipio",
            "cbo2002ocupação": "cbo",
            "salário": "salario"
        })

        linhas_total += len(chunk_filtrado)
        chunks_final.append(chunk_filtrado)

    if not chunks_final:
        raise Exception("Nenhum dado válido do Piauí atendeu aos critérios da metodologia.")

    # Consolida todos os lotes limpos na memória
    df_consolidado = pd.concat(chunks_final, ignore_index=True)
    print(f"Total de linhas pré-filtradas (PI): {linhas_total}")

    # =========================================================================
    # FILTRO DE REPRESENTATIVIDADE ESTATÍSTICA (Mínimo de 10 Admissões)
    # =========================================================================
    print("Aplicando filtro de representatividade estatística (MIN_N = 10)...")
    
    # Calcula a contagem de contratações por ocupação (CBO)
    contagem_cbo = df_consolidado.groupby("cbo").size().reset_index(name="total_admissoes")
    
    # Filtra os CBOs que possuem pelo menos 10 registros
    cbos_validos = contagem_cbo[contagem_cbo["total_admissoes"] >= 10]
    
    # Faz um INNER JOIN para manter no DataFrame apenas as ocupações com representatividade
    df_final = df_consolidado.merge(cbos_validos[["cbo"]], on="cbo", how="inner")
    
    print(f"Linhas finais após filtro de representatividade: {len(df_final)}")
    return df_final


def run_transformation(file_path, mes, ano):
    extrai_arquivo_zipado(file_path)
    arquivo_dados = encontra_arquivo_dados()
    df = processar_csv(arquivo_dados)
    
    mes_limpo = str(mes)[-2:]
    
    df['mes'] = int(mes_limpo)
    df['ano'] = int(ano)
    
    return df