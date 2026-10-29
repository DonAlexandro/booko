import re
import shutil
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Protocol

HASHTAG = re.compile(r"#(\w+)")
TECHNOLOGY = re.compile(r"\w+")
WHOLE_NUMBER = re.compile(r"[0-9]+")


class InvalidBookDetails(ValueError):
    pass


class Genre(StrEnum):
    SELF_DEVELOPMENT = "Саморозвиток"
    TECHNICAL = "Технічна література"
    HISTORY_AND_MEMOIRS = "Історія і мемуари"
    BUSINESS = "Бізнес"


@dataclass(frozen=True)
class BookDetails:
    title: str
    author: str
    genre: Genre
    technologies: tuple[str, ...]
    page_count: int

    def __post_init__(self):
        if not self.title.strip() or not self.author.strip():
            raise InvalidBookDetails("title and author must not be blank")
        if not isinstance(self.genre, Genre):
            raise InvalidBookDetails(f"unknown genre: {self.genre!r}")
        if not self.technologies or not all(TECHNOLOGY.fullmatch(t) for t in self.technologies):
            raise InvalidBookDetails(f"invalid technologies: {self.technologies!r}")
        if type(self.page_count) is not int or self.page_count < 1:
            raise InvalidBookDetails(f"invalid page count: {self.page_count!r}")


def parse_text(text: str | None) -> str:
    value = (text or "").strip()
    if not value:
        raise InvalidBookDetails("text must not be blank")
    return value


def parse_genre(text: str | None) -> Genre:
    try:
        return Genre((text or "").strip())
    except ValueError:
        raise InvalidBookDetails(f"unknown genre: {text!r}") from None


def parse_technologies(text: str | None) -> tuple[str, ...]:
    technologies = tuple(HASHTAG.findall(text or ""))
    if not technologies:
        raise InvalidBookDetails("at least one #technology is required")
    return technologies


def parse_page_count(text: str | None) -> int:
    value = (text or "").strip()
    if not WHOLE_NUMBER.fullmatch(value) or int(value) < 1:
        raise InvalidBookDetails(f"invalid page count: {text!r}")
    return int(value)


class FilingError(Exception):
    pass


class InvalidBookFileName(FilingError):
    def __init__(self, name: str | None):
        super().__init__(f"not a plain file name: {name!r}")
        self.name = name


class BookAlreadyOnShelf(FilingError):
    def __init__(self, location: Path):
        super().__init__(f"a book file already exists at {location}")
        self.location = location


@dataclass(frozen=True)
class CatalogEntry:
    details: BookDetails
    location: Path


class Catalog(Protocol):
    def add(self, entry: CatalogEntry) -> None: ...


class BookFile(Protocol):
    """A book file waiting in an inbox, which can be placed on a shelf and taken back."""

    @property
    def name(self) -> str | None: ...

    def place(self, location: Path) -> None: ...

    def take_back(self, location: Path) -> None: ...


@dataclass(frozen=True)
class DownloadedBookFile:
    path: Path

    @property
    def name(self) -> str:
        return self.path.name

    def place(self, location: Path) -> None:
        shutil.move(self.path, location)

    def take_back(self, location: Path) -> None:
        shutil.move(location, self.path)


@dataclass(frozen=True)
class ReceivedBookFile:
    name: str | None
    content: bytes

    def place(self, location: Path) -> None:
        with open(location, "xb") as f:
            f.write(self.content)

    def take_back(self, location: Path) -> None:
        location.unlink()


def shelf_location(library: Path, details: BookDetails, file_name: str | None) -> Path:
    if not file_name or file_name in (".", "..") or Path(file_name).name != file_name:
        raise InvalidBookFileName(file_name)
    return library / details.technologies[0] / file_name


def file_book(book_file: BookFile, details: BookDetails, library: Path, catalog: Catalog) -> Path:
    """Place the book file on its shelf and add its catalog entry, or do neither."""
    location = shelf_location(library, details, book_file.name)
    if location.exists():
        raise BookAlreadyOnShelf(location)
    location.parent.mkdir(parents=True, exist_ok=True)
    book_file.place(location)
    try:
        catalog.add(CatalogEntry(details, location))
    except BaseException:
        book_file.take_back(location)
        raise
    return location
