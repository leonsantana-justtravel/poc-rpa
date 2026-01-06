# Boilerplate para Projetos Django REST

Este é um boilerplate robusto para iniciar projetos em **Django**, com foco na construção de APIs RESTful. A estrutura foi pensada para ser organizada, escalável e pronta para produção.

-----

## ✨ Funcionalidades

  - **Estrutura Organizada:** Separação clara entre a configuração do projeto (`config`) e a lógica principal da aplicação (`core`).

  - **Pronto para APIs:** Inclui diretórios para `serializers`, `services` e `views`, ideal para usar com Django REST Framework.

  - **Variáveis de Ambiente:** Configuração desacoplada usando um arquivo `.env` para segurança e flexibilidade.

  - **Docker Ready:** Acompanha um `Dockerfile` para facilitar a criação de contêineres e o deploy.

  - **Gerenciamento de Dependências:** Utiliza `requirements.txt` para um controle claro dos pacotes necessários.

  - **Linting e Formatação:** Integração com **Ruff** para garantir um código limpo, organizado e padronizado.

-----

## 📂 Estrutura do Projeto

Este boilerplate utiliza uma estrutura de projeto organizada que promove a manutenibilidade e a separação de responsabilidades:

  - `config/` — Contém todas as configurações globais do projeto Django, como `settings.py` e `urls.py` principais.

  - `core/` — É a aplicação principal do projeto, onde a maior parte da lógica de negócio reside.

  - `core/middleware/` — Local para middlewares customizados que processam requisições e respostas.

  - `core/migrations/` — Armazena os arquivos de migração gerados pelo Django para versionar o banco de dados.

  - `core/serializers/` — Responsável pela serialização e desserialização de dados, convertendo objetos complexos em formatos como JSON.

  - `core/services/` — Camada de serviço para encapsular a lógica de negócio complexa, mantendo os `views` mais limpos.

  - `core/views/` — Onde as lógicas de requisição e resposta são definidas.

  - `.env.example` — Arquivo de exemplo que serve como um guia para as variáveis de ambiente necessárias no projeto.

  - `Dockerfile` — Define as instruções para construir uma imagem Docker da aplicação, facilitando o deploy.

  - `manage.py` — Utilitário de linha de comando para interagir com o projeto Django (ex: `runserver`, `migrate`).

  - `requirements.txt` — Lista todas as dependências Python do projeto para garantir um ambiente consistente.

  - `pyproject.toml` — Arquivo de configuração para ferramentas como o **Ruff**.

-----

## 📋 Pré-requisitos

  - **Python 3.10+**

  - **Pip** 

  - **Docker** 

-----

## 🚀 Como Começar

### 1\. Clone o Repositório

```bash
git clone https://github.com/Just-Travel-Tour/boilerplate-python.git
cd boilerplate-python
```

### 2\. Configure as Variáveis de Ambiente

Crie um arquivo `.env` na raiz do projeto, copiando o exemplo `.env.example`.

```bash
cp .env.example .env
```

Agora, **edite o arquivo `.env`** com suas próprias configurações (chaves secretas, configurações de banco de dados, etc.).

### 3\. Crie um Ambiente Virtual e Instale as Dependências

```bash
# Criar ambiente virtual
python -m venv venv

# Ativar o ambiente virtual
# No Windows:
venv\Scripts\activate

# No macOS/Linux:
source venv/bin/activate

# Instalar as dependências
pip install -r requirements.txt
```

### 4\. Aplique as Migrações

Execute as migrações para configurar o schema do banco de dados.

```bash
python manage.py migrate
```

### 5\. Inicie o Servidor

```bash
python manage.py runserver
```

O projeto estará rodando em `http://127.0.0.1:8000`.

-----

## 🐳 Rodando com Docker

1.  **Construa a Imagem Docker:**

    ` bash     docker build -t <nome-da-sua-imagem> .      `

2.  **Execute o Contêiner:**

    Passar o arquivo `.env` para que o contêiner tenha acesso às variáveis de ambiente.

    ` bash     docker run --env-file .env -p 8000:8000 <nome-da-sua-imagem>      `

-----

## ⚙️ Comandos Úteis do Django

  - **Criar novas migrações baseadas em alterações nos models:**

    ` bash     python manage.py makemigrations      `

  - **Aplicar migrações ao banco de dados:**

    ` bash     python manage.py migrate      `

-----

## 🧹 Comandos de Qualidade de Código (Ruff)

Use o **Ruff** para verificar e formatar seu código, garantindo que ele siga os padrões definidos no projeto.

  - **Verificar todo o projeto em busca de erros e warnings:**

    ` bash     ruff check .      `

  - **Corrigir automaticamente os problemas encontrados:**

    ` bash     ruff check . --fix      `

  - **Formatar o código de todo o projeto:**

    ` bash     ruff format .      `

  - **Verificar e formatar um arquivo ou diretório específico:**

    ` bash     ruff check core/views.py     ruff format core/services/      `

  - **Entender por que uma regra foi sinalizada:**

    ` bash     ruff rule F401  # Exemplo para a regra de "import não utilizado"      `
