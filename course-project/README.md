# Приложение для анализа образовательных программ по наукам о данных  
Головина Арина | Яровицына Наталья

## Архитектура

Проект сейчас состоит из двух основных частей:

- **Backend** — FastAPI + PostgreSQL, REST API для работы с программами, фильтрами и аналитикой.  
- **Data** — CSV‑файл с образовательными программами Data Science.

Фронтенд пока **не реализован** и будет добавлен позже.

### Логическая схема

```text
Пользователь (браузер)
        |
        | (позже) открывает catalog.html / analytics.html
        v
Frontend (HTML + JS)  <-- пока в разработке
        |
        | HTTP-запросы к backend (REST API)
        v
Backend (FastAPI, Python)
  - /health
  - /api/programs/
  - /api/programs/{program_id}
  - /api/filters/values
  - /api/analytics/dashboard
        |
        | SQL-запросы
        v
PostgreSQL
  таблица programs
  (данные из Data/Dataset_kursach-List1.csv)
```

***

## Backend

`backend/` — серверная часть на FastAPI, реализует REST API над базой данных PostgreSQL.

### Основные компоненты

- **Dockerfile** — образ backend.  
- **requirements.txt** — зависимости.

#### Пакет `app`

- `app/main.py`  
  Точка входа:
  - создаёт приложение FastAPI;
  - настраивает CORS;
  - подключает роутеры `/api/...`;
  - на старте вызывает `init_db()` (создание таблиц и импорт CSV);
  - эндпоинт `GET /health`.

- `app/core/config.py`  
  Настройки проекта:
  - `PROJECT_NAME`, `DATABASE_URL`, `DATASET_PATH`, `AUTO_IMPORT_ON_STARTUP`, `CORS_ORIGINS`.

- `app/api/routers/` — обработчики HTTP‑запросов:
  - `programs.py` — `GET /api/programs`, `GET /api/programs/{programs_id}` (каталог программ с фильтрами).
  - `filters.py` — `GET /api/filters/values` (значения для фильтров).
  - `analytics.py` — `GET /api/analytics/dashboard` (данные для аналитики и графиков Plotly).

- `app/db/base.py` — базовый класс SQLAlchemy `Base`.  
- `app/db/session.py` — создание `engine`, `SessionLocal`, dependency `get_db()`.  
- `app/db/init_db.py` — создание таблиц и первичный импорт CSV, если таблица `programs` пустая.

- `app/models/program.py` — ORM‑модель `Program` (структура таблицы `programs`, поля = столбцы CSV).

- `app/schemas/` — Pydantic‑схемы:
  - `ProgramOut`, `ProgramsListOut` — данные о программах;
  - `FiltersValuesOut` — списки значений фильтров;
  - `PlotlyFigure`, `AnalyticsDashboardOut` — структура данных для графиков.

- `app/services/` — бизнес‑логика:
  - `import_service.py` — импорт CSV в БД;
  - `programs_service.py` — получение списка программ и одной программы с учётом фильтров;
  - `filters_service.py` — получения списков значений для фильтров;
  - `analytics_service.py` — расчёт агрегатов и формирование JSON для Plotly.

***

## Data

`Data/Dataset_kursach-List1.csv` — исходный CSV‑файл с образовательными программами.  
При первом запуске backend импортирует этот файл в таблицу `programs` в PostgreSQL.

***

## Frontend (план)

`frontend/` — будет содержать:

- `templates/catalog.html` — каталог программ с фильтрами.  
- `templates/analytics.html` — аналитический дашборд с графиками Plotly.  
- `static/js/*.js` — запросы к REST API backend и отрисовка UI.

На данный момент фронтенд **не реализован**, взаимодействие с API выполняется через Swagger UI.

***

## Запуск проекта

1. Перейти в папку проекта:

```bash
cd course-project
```

2. Собрать и запустить контейнеры:

```bash
docker compose up --build
```

3. Проверить, что backend живой:

- `http://localhost:8000/health` — должно вернуть `{"status": "ok"}`.  
- `http://localhost:8000/docs` — Swagger UI со всеми доступными эндпоинтами.

4. Проверить API:

- `GET http://localhost:8000/api/programs`  
- `GET http://localhost:8000/api/filters/values`  
- `GET http://localhost:8000/api/analytics/dashboard`  
- `GET http://localhost:8000/api/programs/1`

***
