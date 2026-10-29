import pytest

from cli import file_from_downloads
from filing import BookDetails, CatalogEntry, Genre
from samples import RecordingCatalog, UnavailableCatalog

ANSWERS = ["1", "Clean Code", "Robert C. Martin", "4", "#Go", "1"]


@pytest.fixture
def downloads(tmp_path):
    folder = tmp_path / "Downloads"
    folder.mkdir()
    (folder / "b.pdf").write_bytes(b"b pages")
    (folder / "a.pdf").write_bytes(b"a pages")
    return folder


@pytest.fixture
def library(tmp_path):
    return tmp_path / "Library"


def answer(monkeypatch, answers):
    replies = iter(answers)
    def fake_input(prompt):
        reply = next(replies)
        print(f"{prompt}{reply}")
        return reply

    monkeypatch.setattr("builtins.input", fake_input)


def test_files_the_chosen_download_after_asking_again_for_invalid_answers(
        monkeypatch, capsys, downloads, library):
    answer(monkeypatch, ["9", "x", "2", " ", "Clean Code", "", "Robert C. Martin",
                         "5", "2", "no tags", "#Python #AI", "0", "-3", "1.5", "464"])
    catalog = RecordingCatalog()

    file_from_downloads(downloads, library, catalog)

    location = library / "Python" / "b.pdf"
    assert location.read_bytes() == b"b pages"
    assert not (downloads / "b.pdf").exists()
    assert (downloads / "a.pdf").exists()
    assert catalog.entries == [CatalogEntry(BookDetails(
        "Clean Code", "Robert C. Martin", Genre.TECHNICAL, ("Python", "AI"), 464), location)]
    assert capsys.readouterr().out == f"""Available files in Downloads:
1. a.pdf
2. b.pdf
Select file number: 9
Invalid selection.
Select file number: x
Invalid selection.
Select file number: 2
Book title:  
Enter a title.
Book title: Clean Code
Author: 
Enter an author.
Author: Robert C. Martin
Genres:
1. Self-development
2. Technical literature
3. History and memoirs
4. Business
Select genre number: 5
Invalid selection.
Select genre number: 2
Technologies (hashtags, e.g. #Python #AI): no tags
Enter at least one hashtag.
Technologies (hashtags, e.g. #Python #AI): #Python #AI
Page count: 0
Enter a positive whole number.
Page count: -3
Enter a positive whole number.
Page count: 1.5
Enter a positive whole number.
Page count: 464
✅ Book moved from Downloads to {location} and added to Notion.
"""


def test_accepts_the_first_listed_file_and_the_last_genre(monkeypatch, downloads, library):
    answer(monkeypatch, ANSWERS)
    catalog = RecordingCatalog()

    file_from_downloads(downloads, library, catalog)

    assert (library / "Go" / "a.pdf").read_bytes() == b"a pages"
    assert catalog.entries[0].details == BookDetails(
        "Clean Code", "Robert C. Martin", Genre.BUSINESS, ("Go",), 1)


def test_lists_visible_download_files_and_genres_by_number(monkeypatch, capsys, downloads, library):
    (downloads / ".DS_Store").write_bytes(b"")
    (downloads / "folder").mkdir()
    answer(monkeypatch, ANSWERS)

    file_from_downloads(downloads, library, RecordingCatalog())

    out = capsys.readouterr().out
    assert out.startswith("Available files in Downloads:\n1. a.pdf\n2. b.pdf\nSelect file number: 1\n"
                          "Book title: Clean Code\nAuthor: Robert C. Martin\nGenres:\n"
                          "1. Self-development\n2. Technical literature\n"
                          "3. History and memoirs\n4. Business\n")


@pytest.mark.parametrize("number, genre", list(enumerate(Genre, 1)))
def test_english_genre_selection_preserves_the_catalog_genre(
        monkeypatch, capsys, downloads, library, number, genre):
    answer(monkeypatch, ["1", "Clean Code", "Robert C. Martin", str(number), "#Go", "1"])
    catalog = RecordingCatalog()

    file_from_downloads(downloads, library, catalog)

    assert catalog.entries[0].details.genre is genre
    assert "Genres:\n1. Self-development\n2. Technical literature\n" \
           "3. History and memoirs\n4. Business\n" in capsys.readouterr().out


def test_says_so_when_downloads_is_empty(monkeypatch, capsys, tmp_path, library):
    answer(monkeypatch, [])

    file_from_downloads(tmp_path, library, RecordingCatalog())

    assert capsys.readouterr().out == "No files found in Downloads.\n"


def test_leaves_everything_alone_when_the_book_is_already_on_its_shelf(
        monkeypatch, capsys, downloads, library):
    (library / "Go").mkdir(parents=True)
    (library / "Go" / "a.pdf").write_bytes(b"old")
    answer(monkeypatch, ANSWERS)
    catalog = RecordingCatalog()

    file_from_downloads(downloads, library, catalog)

    assert f"⚠️ {library / 'Go' / 'a.pdf'} already exists; nothing was changed." in (
        capsys.readouterr().out)
    assert (library / "Go" / "a.pdf").read_bytes() == b"old"
    assert (downloads / "a.pdf").read_bytes() == b"a pages"
    assert catalog.entries == []


def test_keeps_the_book_in_downloads_when_the_catalog_fails(monkeypatch, capsys, downloads, library):
    answer(monkeypatch, ANSWERS)

    file_from_downloads(downloads, library, UnavailableCatalog())

    assert "⚠️ Could not file the book (Notion is down); it is still in Downloads." in (
        capsys.readouterr().out)
    assert (downloads / "a.pdf").read_bytes() == b"a pages"
    assert not (library / "Go" / "a.pdf").exists()
