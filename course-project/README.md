Можно в бэк добавить тесты
В беке к каждому файлу пояснения их стереть наверное когда будем отправлять
Фронта пока нет

запуск
docker compose up --build
4) Проверь, что backend живой

Открой в браузере/через curl:

http://localhost:8000/health (должно вернуть {"status":"ok"})

И проверь документацию FastAPI:

http://localhost:8000/docs

5) Проверь API из ТЗ

Примеры:
​

GET http://localhost:8000/api/v1/programs

GET http://localhost:8000/api/v1/filters/values

GET http://localhost:8000/api/v1/analytics/dashboard

GET http://localhost:8000/api/v1/programs/1