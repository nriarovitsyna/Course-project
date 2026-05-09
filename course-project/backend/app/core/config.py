from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "Course Project API"

    DATABASE_URL: str = "postgresql+psycopg2://postgres:postgres@localhost:5432/postgres"

    DATASET_PATH: str = "../Data/Dataset_kursach-List1.csv"

    AUTO_IMPORT_ON_STARTUP: bool = True

    CORS_ORIGINS: list[str] = ["http://localhost:5500", "http://127.0.0.1:5500"]

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()