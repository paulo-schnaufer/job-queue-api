# Job Queue API

API em FastAPI para registrar jobs em PostgreSQL e processá-los por meio de um worker em Python. O fluxo principal é:

- a API recebe um payload e salva um registro em `jobs`;
- o worker consulta jobs em status `pending`;
- o worker atualiza o status para `running` e depois para `done` ou `failed`;
- a API permite consultar o histórico e o resultado final de cada job.

## Funcionalidades

- Criação de jobs via REST API;
- Consulta individual por ID;
- Listagem com filtro por status e limite;
- Worker assíncrono em loop para processar fila;
- Banco PostgreSQL em container via Docker Compose;
- Ambiente pronto para rodar com `docker compose up --build`.

## Estrutura do projeto

- `app/main.py`: inicializa a aplicação FastAPI;
- `app/routers/health.py`: healthcheck da API;
- `app/routers/jobs.py`: endpoints de criação, consulta e listagem de jobs;
- `app/database.py`: conexão com PostgreSQL usando variáveis de ambiente;
- `worker.py`: processo que processa jobs pendentes;
- `sql/create_tables.sql`: schema inicial do banco;
- `docker-compose.yml`: orquestração do PostgreSQL, API e worker;
- `Dockerfile`: imagem da aplicação.

## Requisitos

- Docker
- Docker Compose
- Python 3.11+ para execução local (opcional)

## Configuração do ambiente

Crie um arquivo `.env` na raiz do projeto com as variáveis abaixo:

```env
DB_HOST=localhost
DB_PORT=5433
DB_NAME=jobqueue
DB_USER=postgres
DB_PASSWORD=1234
```

Essas variáveis são usadas tanto pela API quanto pelo worker. O PostgreSQL expõe a porta `5433` no host local para evitar conflitos com outras instâncias locais.

## Executar com Docker Compose

Na raiz do projeto, rode:

```bash
docker compose up --build
```

Esse comando sobe os serviços:

- `db`: PostgreSQL com inicialização automática do schema em `sql/create_tables.sql`;
- `api`: aplicação FastAPI;
- `worker`: processo que processa jobs pendentes.

### URLs úteis

- API: http://localhost:8000
- Healthcheck: http://localhost:8000/health/
- PostgreSQL: localhost:5433

Para parar tudo:

```bash
docker compose down
```

Se quiser remover também o volume do banco:

```bash
docker compose down -v
```

## Executar localmente (sem Docker)

Crie e ative o ambiente virtual:

```bash
python -m venv .venv
source .venv/bin/activate
```

No Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Instale as dependências:

```bash
pip install -r requirements.txt
```

Inicie a API:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Em outro terminal, inicie o worker:

```bash
python worker.py
```

## Endpoints

### Root

```bash
curl http://localhost:8000/
```

### Healthcheck

```bash
curl http://localhost:8000/health/
```

### Criar job

```bash
curl -X POST http://localhost:8000/jobs/ \
  -H "Content-Type: application/json" \
  -d '{"client_id": 1, "payload": {"teste": true, "valor": 123}}'
```

### Consultar um job por ID

```bash
curl http://localhost:8000/jobs/1
```

### Listar jobs

```bash
curl "http://localhost:8000/jobs/?status=pending&limit=10"
```

## Fluxo de processamento

1. A API registra um job com status `pending`.
2. O worker seleciona até um job pendente.
3. O registro recebe `running`.
4. O processamento realiza a lógica do job.
5. O registro finaliza como `done` ou `failed`.

## Observações

- O projeto não usa RabbitMQ, Celery ou outra fila externa; a fila é implementada em PostgreSQL.
- O worker faz polling no banco em looping e processa os jobs disponíveis.
- O arquivo `sql/create_tables.sql` é montado no container do PostgreSQL e executado automaticamente na inicialização.
