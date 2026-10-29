import pytest

from cli import file_from_downloads
from filing import BookDetails, CatalogEntry, Genre
from samples import RecordingCatalog, UnavailableCatalog

ANSWERS = ["2", "Clean Code", "Robert C. Martin", "2", "#Python #AI", "464"]


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
    monkeypatch.setattr("builtins.input", lambda prompt: next(replies))


def test_files_the_chosen_download_after_asking_again_for_invalid_answers(
        monkeypatch, capsys, downloads, library):
    answer(monkeypatch, ["9", "x", "2", " ", "Clean Code", "Robert C. Martin",
                         "5", "2", "no tags", "#Python #AI", "0", "-3", "1.5", "464"])
    catalog = RecordingCatalog()

    file_from_downloads(downloads, library, catalog)

    location = library / "Python" / "b.pdf"
    assert location.read_bytes() == b"b pages"
    assert not (downloads / "b.pdf").exists()
    assert (downloads / "a.pdf").exists()
    assert catalog.entries == [CatalogEntry(BookDetails(
        "Clean Code", "Robert C. Martin", Genre.TECHNICAL, ("Python", "AI"), 464), location)]
    out = capsys.readouterr().out
    assert out.count("Invalid selection.") == 3
    assert out.count("Enter a title.") == 1
    assert out.count("Enter at least one hashtag.") == 1
    assert out.count("Enter a positive whole number.") == 3
    assert f"✅ Book moved from Downloads to {location} and added to Notion." in out


def test_lists_visible_download_files_and_genres_by_number(monkeypatch, capsys, downloads, library):
    (downloads / ".DS_Store").write_bytes(b"")
    (downloads / "folder").mkdir()
    answer(monkeypatch, ANSWERS)

    file_from_downloads(downloads, library, RecordingCatalog())

    out = capsys.readouterr().out
    assert out.startswith("Available files in Downloads:\n1. a.pdf\n2. b.pdf\nGenres:\n"
                          "1. Саморозвиток\n2. Технічна література\n3. Історія і мемуари\n4. Бізнес\n")


def test_says_so_when_downloads_is_empty(monkeypatch, capsys, tmp_path, library):
    answer(monkeypatch, [])

    file_from_downloads(tmp_path, library, RecordingCatalog())

    assert capsys.readouterr().out == "No files found in Downloads.\n"


def test_leaves_everything_alone_when_the_book_is_already_on_its_shelf(
        monkeypatch, capsys, downloads, library):
    (library / "Python").mkdir(parents=True)
    (library / "Python" / "b.pdf").write_bytes(b"old")
    answer(monkeypatch, ANSWERS)
    catalog = RecordingCatalog()

    file_from_downloads(downloads, library, catalog)

    assert f"⚠️ {library / 'Python' / 'b.pdf'} already exists; nothing was changed." in (
        capsys.readouterr().out)
    assert (library / "Python" / "b.pdf").read_bytes() == b"old"
    assert (downloads / "b.pdf").read_bytes() == b"b pages"
    assert catalog.entries == []


def test_keeps_the_book_in_downloads_when_the_catalog_fails(monkeypatch, capsys, downloads, library):
    answer(monkeypatch, ANSWERS)

    file_from_downloads(downloads, library, UnavailableCatalog())

    assert "⚠️ Could not file the book (Notion is down); it is still in Downloads." in (
        capsys.readouterr().out)
    assert (downloads / "b.pdf").read_bytes() == b"b pages"
    assert not (library / "Python" / "b.pdf").exists()
