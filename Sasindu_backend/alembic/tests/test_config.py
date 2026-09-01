from app.core.config import Settings


def test_settings_reads_env(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://x:x@localhost/x")
    monkeypatch.setenv("SEED", "7")
    settings = Settings()
    assert settings.database_url.startswith("postgresql+asyncpg://")
    assert settings.seed == 7
    assert settings.environment == "dev"
