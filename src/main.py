import os
from extract import run_extraction
from transform import run_transformation
from load import load_to_supabase, check_period_exists


def main():
    print("Iniciando pipeline...")

    file_path, mes_alvo, ano_alvo = run_extraction() 

    if check_period_exists("caged_pi", mes_alvo, ano_alvo):
        print(f"Dados de {mes_alvo}/{ano_alvo} já estão no banco. Finalizando sem alterações.")
        
        if os.path.exists(file_path):
            os.remove(file_path)
        return

    df = run_transformation(file_path, mes_alvo, ano_alvo)
    load_to_supabase(df, "caged_pi")

    if os.path.exists(file_path):
        os.remove(file_path)
        print(f"Arquivo compactado {file_path} removido para limpeza do ambiente.")

    print("Pipeline finalizado com sucesso!")


if __name__ == "__main__":
    main()