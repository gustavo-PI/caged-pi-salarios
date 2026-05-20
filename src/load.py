import os
from sqlalchemy import create_engine, text
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
        return False


def load_to_supabase(df, table_name: str):
    
    df.to_sql(
        name=table_name,
        con=engine,
        if_exists="append",
        index=False,
        chunksize=5000
    )
    
    print("Carga de dados finalizada com sucesso!")