import pytest

from filing import (
    BookDetails,
    Genre,
    InvalidBookDetails,
    parse_genre,
    parse_page_count,
    parse_technologies,
    parse_text,
)


def make_details(**overrides):
    fields = {
        "title": "Clean Code",
        "author": "Robert C. Martin",
        "genre": Genre.TECHNICAL,
        "technologies": ("Python", "AI"),
        "page_count": 464,
    }
    return BookDetails(**(fields | overrides))


class TestParseText:
    def test_trims_surrounding_whitespace(self):
        assert parse_text("  Clean Code ") == "Clean Code"

    @pytest.mark.parametrize("text", ["", "   ", None])
    def test_rejects_missing_text(self, text):
        with pytest.raises(InvalidBookDetails):
            parse_text(text)


class TestParseGenre:
    @pytest.mark.parametrize("genre", list(Genre))
    def test_accepts_every_known_genre(self, genre):
        assert parse_genre(f" {genre.value} ") is genre

    @pytest.mark.parametrize("text", ["Фантастика", "", None])
    def test_rejects_unknown_genre(self, text):
        with pytest.raises(InvalidBookDetails):
            parse_genre(text)

    def test_known_genres_are_the_catalog_ones(self):
        assert [g.value for g in Genre] == [
            "Саморозвиток", "Технічна література", "Історія і мемуари", "Бізнес"]


class TestParseTechnologies:
    def test_keeps_hashtags_in_order(self):
        assert parse_technologies("read #Python then #AI") == ("Python", "AI")

    @pytest.mark.parametrize("text", ["Python AI", "#", "", None])
    def test_rejects_text_without_hashtags(self, text):
        with pytest.raises(InvalidBookDetails):
            parse_technologies(text)


class TestParsePageCount:
    @pytest.mark.parametrize("text, expected", [("1", 1), (" 464 ", 464)])
    def test_accepts_positive_whole_numbers(self, text, expected):
        assert parse_page_count(text) == expected

    @pytest.mark.parametrize("text", ["0", "-5", "1.5", "abc", "²", "", None])
    def test_rejects_anything_else(self, text):
        with pytest.raises(InvalidBookDetails):
            parse_page_count(text)


class TestBookDetails:
    def test_holds_valid_details(self):
        details = make_details()
        assert details.technologies == ("Python", "AI")
        assert details.page_count == 464

    @pytest.mark.parametrize("overrides", [
        {"title": " "},
        {"author": ""},
        {"genre": "Бізнес"},
        {"technologies": ()},
        {"technologies": ("../escape",)},
        {"page_count": 0},
        {"page_count": True},
        {"page_count": "12"},
    ])
    def test_refuses_invalid_details(self, overrides):
        with pytest.raises(InvalidBookDetails):
            make_details(**overrides)
