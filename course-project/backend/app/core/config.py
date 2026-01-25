from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "Course Project API"

    # Пример: postgresql+psycopg2://postgres:postgres@postgres:5432/postgres
    DATABASE_URL: str = "postgresql+psycopg2://postgres:postgres@localhost:5432/postgres"

    # Путь до CSV внутри контейнера/локально (мы будем монтировать Data/ в контейнер).
    DATASET_PATH: str = "../Data/Dataset_kursach-List1.csv"

    # Если true — при старте импортировать CSV в БД (если таблица пустая).
    AUTO_IMPORT_ON_STARTUP: bool = True

    # CORS для фронта (если Live Server на 5500)
    CORS_ORIGINS: list[str] = ["http://localhost:5500", "http://127.0.0.1:5500"]

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
