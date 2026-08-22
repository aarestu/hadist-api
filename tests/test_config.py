import os
import pytest
from app.infrastructure.config import AppConfig, load_config


def test_default_config_loading():
    config = load_config("non_existent_config.yaml")
    assert isinstance(config, AppConfig)
    assert config.database_url == "sqlite+aiosqlite:///hadist.db"
    assert config.http.timeout_seconds == 30
    assert config.batch_size == 500


def test_env_database_url_override(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://user:pass@localhost:5432/testdb")
    config = load_config("non_existent_config.yaml")
    assert config.database_url == "postgresql+asyncpg://user:pass@localhost:5432/testdb"
