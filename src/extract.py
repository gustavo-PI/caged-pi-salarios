import os
from ftplib import FTP
from dotenv import load_dotenv

load_dotenv()

FTP_HOST = os.getenv("FTP_HOST")
FTP_DIR = os.getenv("FTP_DIR")
LOCAL_PATH = "data/raw"


def connect_ftp():
    try:
        ftp = FTP(FTP_HOST, timeout=60, encoding="latin-1")
        ftp.login()
        print("Conectado ao FTP")
        return ftp
    except Exception as e:
        raise Exception(f"Erro ao conectar ao FTP: {e}")


def run_extraction():
    ftp = connect_ftp()

    with ftp:
        try:
            # navega até o mês mais recente
            ftp.cwd(FTP_DIR)
            ultimo_ano = sorted([a for a in ftp.nlst() if a.isdigit()])[-1]
            
            ftp.cwd(f"{FTP_DIR}/{ultimo_ano}")
            ultimo_mes = sorted([m for m in ftp.nlst() if m.isdigit()])[-1]
            
            ftp.cwd(f"{FTP_DIR}/{ultimo_ano}/{ultimo_mes}")
            print(f"Competência encontrada: {ultimo_mes}/{ultimo_ano}")

            # localiza o arquivo das movimentações
            files = ftp.nlst()
            arquivos_mov = sorted([f for f in files if "CAGEDMOV" in f and f.endswith(".7z")])
            
            if not arquivos_mov:
                raise Exception("Arquivo CAGEDMOV não encontrado no servidor.")
            
            arquivo = arquivos_mov[-1]

            # download do arquivo
            os.makedirs(LOCAL_PATH, exist_ok=True)
            file_path = os.path.join(LOCAL_PATH, arquivo)

            if os.path.exists(file_path):
                print(f"Arquivo {arquivo} já existe localmente. Pulando download.")
            else:
                print(f"Baixando {arquivo}...")
                with open(file_path, "wb") as f:
                    ftp.retrbinary(f"RETR {arquivo}", f.write)
                print("Download concluído com sucesso!")

            return file_path, ultimo_mes, ultimo_ano

        except Exception as e:
            raise Exception(f"Erro no processo de extração: {e}")