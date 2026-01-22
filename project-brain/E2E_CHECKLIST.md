# End-to-End (E2E) запуск и проверка

> Требуется установленный Docker + Docker Compose.

## 1) Подготовка окружения

```bash
cd project-brain
cp .env.example .env
```

Проверьте значения:
- `QDRANT_URL=http://qdrant:6333`
- `MINIO_URL=http://minio:9000`
- `DATABASE_URL=postgresql://brain_user:brain_password@postgres:5432/project_brain`
- `LM_STUDIO_URL=http://<host>:1234` (если нужен /ask)
- `LM_STUDIO_MODEL=<model_name>`

## 2) Запуск сервисов

```bash
docker-compose up -d
```

Проверьте, что сервисы поднялись:
```bash
docker-compose ps
```

## 3) Миграции и сиды

```bash
docker-compose exec backend python -m alembic upgrade head

docker-compose exec backend python seed_data.py
```

## 4) Smoke‑проверки API

```bash
curl http://localhost:8000/health
curl http://localhost:8000/documents
```

## 5) Проверка ingest → parse → embed

1. Откройте UI: http://localhost:3000
2. Загрузите PDF/DOCX/TXT через страницу **Documents**.
3. Убедитесь, что документ появился в списке, а статус меняется на `completed`.

## 6) Проверка Search

```bash
curl -X POST http://localhost:8000/search \
  -H "Content-Type: application/json" \
  -d '{"query": "test", "limit": 5}'
```

Ожидается массив `results` с `score` и `text`.

## 7) Проверка Ask/RAG

```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "What is this document about?", "max_context_chunks": 3}'
```

Ожидается `answer` и `sources`. Если LLM недоступен — вернется `status: "search_only"`.

## 8) Логи для диагностики

```bash
docker-compose logs -f backend

docker-compose logs -f worker
```

## 9) Проверка Qdrant

```bash
curl http://localhost:6333/collections
```

Проверьте наличие коллекции `documents`.
