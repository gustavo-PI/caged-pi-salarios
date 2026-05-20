import os
from extract import run_extraction
from transform import run_transformation
from load import load_to_supabase, check_period_exists


def main():
    print("Iniciando pipeline...")

    # 1. Identifica o que tem no FTP e faz o download
    file_path, mes_alvo, ano_alvo = run_extraction() 

    # 2. Antes de transformar, verifica se já existe no banco (Idempotência)
    if check_period_exists("caged_pi", mes_alvo, ano_alvo):
        print(f"Dados de {mes_alvo}/{ano_alvo} já estão no banco. Finalizando sem alterações.")
        
        # Mesmo que já exista no banco, limpamos o arquivo baixado para não acumular lixo
        if os.path.exists(file_path):
            os.remove(file_path)
        return

    # 3. Se não existe, Transforma e Carrega
    df = run_transformation(file_path, mes_alvo, ano_alvo)
    load_to_supabase(df, "caged_pi")

    # 4. BOA PRÁTICA: Remove o arquivo .7z original após o sucesso de todo o processo
    if os.path.exists(file_path):
        os.remove(file_path)
        print(f"Arquivo compactado {file_path} removido para limpeza do ambiente.")

    print("Pipeline finalizado com sucesso!")


if __name__ == "__main__":
    main()