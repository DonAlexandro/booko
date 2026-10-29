import os
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


class MissingSetting(RuntimeError):
    pass


@dataclass(frozen=True)
class Settings:
    library: Path
    notion_token: str
    notion_database_id: str


def load_settings(environ: Mapping[str, str] | None = None) -> Settings:
    if environ is None:
        load_dotenv()
        environ = os.environ
    library = environ.get("BOOKO_LIBRARY") or Path.home() / "Documents" / "Books"
    return Settings(
        library=Path(library),
        notion_token=_required(environ, "NOTION_TOKEN"),
        notion_database_id=_required(environ, "NOTION_DATABASE_ID"),
    )


def _required(environ: Mapping[str, str], name: str) -> str:
    value = environ.get(name)
    if not value:
        raise MissingSetting(f"{name} is not set; add it to .env")
    return value
