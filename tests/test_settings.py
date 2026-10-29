from pathlib import Path

import pytest

from settings import MissingSetting, load_settings

REQUIRED = {"NOTION_TOKEN": "secret", "NOTION_DATABASE_ID": "catalog-id"}


def test_reads_catalog_settings_and_defaults_the_library_to_documents_books():
    settings = load_settings(REQUIRED)

    assert settings.notion_token == "secret"
    assert settings.notion_database_id == "catalog-id"
    assert settings.library == Path.home() / "Documents" / "Books"


def test_reads_the_process_environment_by_default(monkeypatch, tmp_path):
    for name, value in (REQUIRED | {"BOOKO_LIBRARY": str(tmp_path)}).items():
        monkeypatch.setenv(name, value)

    assert load_settings() == load_settings(REQUIRED | {"BOOKO_LIBRARY": str(tmp_path)})


def test_library_can_be_moved_with_booko_library(tmp_path):
    settings = load_settings(REQUIRED | {"BOOKO_LIBRARY": str(tmp_path)})

    assert settings.library == tmp_path


@pytest.mark.parametrize("name", ["NOTION_TOKEN", "NOTION_DATABASE_ID"])
@pytest.mark.parametrize("value", [None, ""])
def test_refuses_to_start_without_catalog_settings(name, value):
    environ = {k: v for k, v in REQUIRED.items() if k != name}
    if value is not None:
        environ[name] = value

    with pytest.raises(MissingSetting, match=name):
        load_settings(environ)
