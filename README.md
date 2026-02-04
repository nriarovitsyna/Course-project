# Приложение для анализа образовательных программ по наукам о данных  
Головина Арина | Яровицына Наталья

## Архитектура

Проект сейчас состоит из четырех основных частей:

- **Backend** — FastAPI + PostgreSQL, REST API для работы с программами, фильтрами и аналитикой.  
- **Data** — CSV‑файл с образовательными программами Data Science.
- **Parser** - сбор данных об образовательных программах из внешних источников, очистки и приведения к единому формату; результат сохраняется в файлы для дальнейшей загрузки в БД/Data.
- **Frontend** - веб‑клиент (HTML/CSS/JS) для работы с каталогом: поиск и фильтры, переключение «таблица/карточки», просмотр деталей программы, сравнение и переходы к аналитике/экспорту.

## Дерево проекта

```
.
├── Data
│   └── Dataset_kursach-List1.csv
├── backend
│   ├── Dockerfile
│   ├── app
│   │   ├── api
│   │   │   ├── api.py
│   │   │   └── routers
│   │   │       ├── analytics.py
│   │   │       ├── filters.py
│   │   │       └── programs.py
│   │   ├── core
│   │   │   └── config.py
│   │   ├── db
│   │   │   ├── base.py
│   │   │   ├── init_db.py
│   │   │   └── session.py
│   │   ├── main.py
│   │   ├── models
│   │   │   └── program.py
│   │   ├── schemas
│   │   │   ├── analytics.py
│   │   │   ├── filters.py
│   │   │   └── program.py
│   │   └── services
│   │       ├── analytics_service.py
│   │       ├── filters_service.py
│   │       ├── import_service.py
│   │       └── programs_service.py
│   └── requirements.txt
├── docker-compose.yml
├── frontend
│   ├── analytics.html
│   ├── catalog.html
│   ├── compare.html
│   ├── css
│   │   └── styles.css
│   ├── export.html
│   ├── index.html
│   ├── js
│   │   ├── analytics.js
│   │   ├── api.js
│   │   ├── app.js
│   │   ├── catalog.js
│   │   ├── compare.js
│   │   └── export.js
│   └── smart.html
└── parsers
    ├── save_state.py
    ├── state.json
    └── vuzopedia_scraper_auth.py
```

### Логическая схема

```text
Пользователь (браузер)
        |
        | (позже) открывает catalog.html / analytics.html
        v
Frontend (HTML + JS) 
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

4. Проверить frontend:

- Проверить в браузере страницу frontend.
- Проверить базовые сценарии в интерфейсе.

***
