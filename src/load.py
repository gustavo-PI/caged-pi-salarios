import os
from sqlalchemy import create_engine
from sqlalchemy import text
from dotenv import load_dotenv

load_dotenv()

DB_URL = os.getenv("DB_URL")
engine = create_engine(DB_URL)

def check_period_exists(table_name, mes, ano):
    query = text(f"SELECT COUNT(*) FROM {table_name} WHERE mes = :mes AND ano = :ano")
    try:
        with engine.connect() as conn:
            result = conn.execute(query, {"mes": int(mes), "ano": int(ano)}).scalar()
            return result > 0
    except Exception:
        # Se a tabela ainda não existir (primeira rodada), retorna False
        return False

def load_to_supabase(df, table_name: str):
    """
    Envia um DataFrame para o Supabase/Postgres via SQLAlchemy.
    """
    df.to_sql(
        name=table_name,
        con=engine,
        if_exists="append",
        index=False
    )