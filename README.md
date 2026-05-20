Pipeline ETL - Ocupações com maiores medianas salariais do Piaui
Pipeline de dados automatizado que identifica, baixa e trata os microdados mensais do Novo CAGED para gerar o ranking das profissões com as maiores medianas salariais do Piauí, alimentando um dashboard no Data Studio.

Como Funciona
extract.py: Conecta via FTP ao Ministerio do Trabalho e identifica dinamicamente a pasta da competencia mais recente para realizar o download do arquivo .7z.

main.py: Consulta o banco de dados antes da transformacao. Se os dados da competencia atual ja estiverem presentes, a execucao é interrompida para evitar a duplicidade de registros.

transform.py: Processa o arquivo bruto em lotes de 500.000 linhas para otimizar o uso de memoria RAM. Aplica os filtros (apenas admissoes no prazo, regime de salario mensal e regime nao intermitente para a UF do Piaui).

load.py: Realiza a carga dos dados tratados no Supabase.

Tecnologias Utilizadas
Linguagem: Python (Pandas, SQLAlchemy, Py7zr)

Banco de Dados: Supabase

Orquestracao: GitHub Actions

Visualizacao: Data Studio

Como Executar o Projeto
Configure as variáveis de ambiente no arquivo .env utilizando o .env.example como referencia.

Instale as dependências necessarias: pip install -r requirements.txt

Execute o script orquestrador: python src/main.py

Desenvolvido por Gustavo Carvalho — https://www.linkedin.com/in/gustavo-carvalho-de-paula-471539303/
