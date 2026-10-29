import re
from dataclasses import dataclass
from enum import StrEnum

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
