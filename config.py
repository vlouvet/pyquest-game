# config.py
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Base configuration"""

    SECRET_KEY = os.environ.get("SECRET_KEY") or "dev-secret-key-change-in-production"
    # Database selection via env vars:
    # Priority: if USE_SQLITE=1 (or true) -> use sqlite file; else if DATABASE_URL set -> use it; otherwise default sqlite instance file.
    use_sqlite_flag = os.environ.get("USE_SQLITE", "0").lower() in ("1", "true", "yes")
    database_url = os.environ.get("DATABASE_URL")
    if use_sqlite_flag:
        instance_path = os.environ.get("SQLITE_FILE", "instance/pyquest.db")
        Path(instance_path).parent.mkdir(parents=True, exist_ok=True)
        SQLALCHEMY_DATABASE_URI = f"sqlite:///{instance_path}"
    elif database_url:
        SQLALCHEMY_DATABASE_URI = database_url
    else:
        # fallback: simple file DB in instance folder
        instance_path = os.environ.get("SQLITE_FILE", "instance/pyquest.db")
        Path(instance_path).parent.mkdir(parents=True, exist_ok=True)
        SQLALCHEMY_DATABASE_URI = f"sqlite:///{instance_path}"

    # Ensure DATABASE_URL env var is set for tools like Alembic that read it from the environment
    os.environ.setdefault("DATABASE_URL", SQLALCHEMY_DATABASE_URI)

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    WTF_CSRF_ENABLED = True


class DevelopmentConfig(Config):
    """Development configuration"""

    DEBUG = True


class TestingConfig(Config):
    """Testing configuration"""

    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    WTF_CSRF_ENABLED = False
    DEBUG = False


class ProductionConfig(Config):
    """Production configuration"""

    DEBUG = False
    # In production, SECRET_KEY must be set via environment variable


config = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}
