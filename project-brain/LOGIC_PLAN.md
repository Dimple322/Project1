# План логики, связок и реализации Project Brain

## 1. Сервисы и их роли

- **UI (Next.js)** — интерфейс пользователя: загрузка документов, поиск, Ask/RAG, просмотр результатов. UI общается с backend по `NEXT_PUBLIC_API_URL`.
- **Backend (FastAPI)** — API, управление сущностями, поиск, RAG, оркестрация задач.
- **Worker (Celery)** — фоновые задачи: парсинг документов, эмбеддинги, коррекция транскриптов.
- **PostgreSQL** — единый источник истины (DB-first).
- **MinIO** — объектное хранилище оригиналов и результатов парсинга.
- **Qdrant** — векторный поиск по чанкам.
- **Redis** — брокер/бэкенд для Celery.
- **Neo4j (опц.)** — граф отношений.
- **LM Studio (опц.)** — LLM‑провайдер для /ask.

## 2. Поток данных: ingest → parse → embed → search

1. **Upload** (`POST /ingest/file`)
   - Backend сохраняет файл во временный путь, считает SHA256.
   - Проверяет дубликаты в PostgreSQL.
   - Загружает оригинал в MinIO и создает `Document` + `DocumentVersion`.
   - Запускает задачу `parse_document_task`.
2. **Parse** (`parse_document_task`)
   - Worker скачивает оригинал из MinIO.
   - Парсит Docling/Unstructured.
   - Сохраняет `parsed.json` в MinIO.
   - Создает `Chunk` записи в PostgreSQL.
   - Запускает `embed_chunks_task`.
3. **Embed** (`embed_chunks_task`)
   - Worker генерирует эмбеддинги для чанков.
   - Создает коллекцию `documents` в Qdrant при необходимости.
   - Upsert в Qdrant с payload (doc_id, chunk_id, page_number и т.п.).

## 3. Поиск (`POST /search`)

- Backend генерирует эмбеддинг запроса.
- В Qdrant выполняется `query_points` по коллекции `documents`.
- Результаты приводятся к `SearchResult` и возвращаются UI.

## 4. Ask/RAG (`POST /ask`)

1. Получение вопроса и лимита контекста.
2. Генерация эмбеддинга запроса.
3. Поиск чанков в Qdrant (тот же `query_points`).
4. Сбор контекста + списка `sources` (по документам).
5. Вызов LLM (LM Studio) с системным промптом и контекстом.
6. Если LLM недоступен или вернул пустой ответ — fallback на “search only”.

## 5. Транскрипты

- `POST /transcript/correct` запускает `correct_transcript_task`.
- Worker загружает parsed.json, применяет лексикон и сохраняет результат.

## 6. Сущности, правила и аудит

- CRUD для сущностей (проекты/объекты/подсистемы/персоны).
- События кураторства и правила обучения фиксируются в БД.

## 7. Конфигурация и окружение

- Все сервисы читают env (через `config.Settings` в backend/worker).
- Для Docker значение `QDRANT_URL` задается в `docker-compose.yml`.
- Для локального режима по умолчанию используется `http://localhost:6333`.
- LLM параметры (таймауты, модель, токены) задаются env‑переменными.

## 8. Критические связки (что должно быть “зелёным”)

- **Backend ↔ PostgreSQL**: доступ к БД, миграции.
- **Backend/Worker ↔ MinIO**: чтение/запись файлов.
- **Worker ↔ Qdrant**: доступ к коллекции `documents`.
- **Backend ↔ Qdrant**: `query_points` для /search и /ask.
- **Backend ↔ LM Studio**: `/v1/chat/completions` для /ask.
- **UI ↔ Backend**: `NEXT_PUBLIC_API_URL` должен быть корректным.

## 9. Чеклист готовности

- Документы появляются в списке после ingest.
- `/search` возвращает результаты (не `Failed to fetch`).
- `/ask` возвращает ответ от LLM (не fallback).
- В логах worker нет постоянных retry из-за Qdrant.
- Все сервисы используют правильные URL из env.
