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
        raise Exception(f"Erro ao conectar: {e}")


def list_files(ftp):
    ftp.cwd(FTP_DIR)
    files = ftp.nlst()
    print(f"{len(files)} arquivos encontrados")
    return files


def get_latest_file(files):
    arquivos_7z = [f for f in files if f.endswith(".7z")]

    if not arquivos_7z:
        raise Exception("Nenhum arquivo .7z encontrado")

    arquivos_7z.sort()
    latest = arquivos_7z[-1]

    print(f"Arquivo mais recente: {latest}")
    return latest


def download_file(ftp, filename):
    os.makedirs(LOCAL_PATH, exist_ok=True)
    local_file = os.path.join(LOCAL_PATH, filename)

    if os.path.exists(local_file):
        print("Arquivo já existe. Pulando download.")
        return local_file

    with open(local_file, "wb") as f:
        ftp.retrbinary(f"RETR {filename}", f.write)

    print("Download concluído")
    return local_file


def run_extraction():
    ftp = connect_ftp()

    try:
        # entra na raiz
        ftp.cwd(FTP_DIR)

        # lista anos
        anos = [a for a in ftp.nlst() if a.isdigit()]
        ultimo_ano = sorted(anos)[-1]
        print(f"Ano mais recente: {ultimo_ano}")

        # entra no ano
        ftp.cwd(f"{FTP_DIR}/{ultimo_ano}")

        # lista meses
        meses = [m for m in ftp.nlst() if m.isdigit()]
        ultimo_mes = sorted(meses)[-1]
        print(f"Mês mais recente: {ultimo_mes}")

        # entra no mês
        caminho_final = f"{FTP_DIR}/{ultimo_ano}/{ultimo_mes}"
        ftp.cwd(caminho_final)

        # lista arquivos
        files = ftp.nlst()

        arquivos_mov = [f for f in files if "CAGEDMOV" in f and f.endswith(".7z")]

        if not arquivos_mov:
            raise Exception("Arquivo CAGEDMOV não encontrado")

        arquivo = sorted(arquivos_mov)[-1]
        print(f"Arquivo selecionado: {arquivo}")

        file_path = download_file(ftp, arquivo)

        # AJUSTE AQUI: Retorna os 3 valores necessários
        return file_path, ultimo_mes, ultimo_ano

    finally:
        ftp.quit()
        print("FTP encerrado")