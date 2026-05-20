import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

DB_URL = os.getenv("DB_URL")

# Criamos o engine de conexão com o banco de dados
engine = create_engine(DB_URL)


def check_period_exists(table_name, mes, ano):
    """
    Verifica se a competência (mês/ano) já foi carregada no banco 
    para evitar duplicidade de dados.
    """
    # Usamos parâmetros nomeados (:mes, :ano) para evitar SQL Injection
    query = text(f"SELECT COUNT(*) FROM {table_name} WHERE mes = :mes AND ano = :ano")
    try:
        with engine.connect() as conn:
            result = conn.execute(query, {"mes": int(mes), "ano": int(ano)}).scalar()
            return result > 0
    except Exception:
        # Se a tabela não existir (primeira execução), retorna False para criá-la
        return False


def load_to_supabase(df, table_name: str):
    """
    Envia o DataFrame tratado para o Supabase de forma eficiente em lotes.
    """
    print(f"Iniciando a carga de {len(df)} linhas na tabela '{table_name}'...")
    
    # O chunksize e o método de append garantem performance e segurança na rede
    df.to_sql(
        name=table_name,
        con=engine,
        if_exists="append",
        index=False,
        chunksize=5000  # BOA PRÁTICA: Envia de 5k em 5k para não dar timeout no Supabase
    )
    
    print("Carga de dados finalizada com sucesso!")