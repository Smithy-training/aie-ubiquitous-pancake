from app.core.config import PROJECT_ROOT, get_settings


def test_project_root_contains_runtime_files() -> None:
    assert (PROJECT_ROOT / "configs" / "config.yaml").is_file()
    assert (PROJECT_ROOT / "artifacts" / "model_v1.pkl").is_file()


def test_env_override_takes_precedence(monkeypatch) -> None:
    get_settings.cache_clear()
    monkeypatch.setenv("APP__VERSION", "9.9.9-test")

    settings = get_settings()

    assert settings.app.version == "9.9.9-test"
    get_settings.cache_clear()
