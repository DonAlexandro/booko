import pytest

from books import clean_code
from filing import (
    BookAlreadyOnShelf,
    CatalogEntry,
    DownloadedBookFile,
    InvalidBookFileName,
    ReceivedBookFile,
    file_book,
    parse_book_file_name,
)

DETAILS = clean_code()


class RecordingCatalog:
    def __init__(self):
        self.entries = []

    def add(self, entry):
        self.entries.append(entry)


class UnavailableCatalog:
    def add(self, entry):
        raise ConnectionError("Notion is down")


@pytest.fixture
def library(tmp_path):
    return tmp_path / "Library"


@pytest.fixture
def downloads(tmp_path):
    folder = tmp_path / "Downloads"
    folder.mkdir()
    return folder


def downloaded(downloads, name="book.pdf", content=b"pages"):
    path = downloads / name
    path.write_bytes(content)
    return DownloadedBookFile(path)


class TestFilingAReceivedBookFile:
    def test_places_it_on_the_first_technology_shelf_and_catalogs_it(self, library):
        catalog = RecordingCatalog()

        location = file_book(ReceivedBookFile("book.pdf", b"pages"), DETAILS, library, catalog)

        assert location == library / "Python" / "book.pdf"
        assert location.read_bytes() == b"pages"
        assert catalog.entries == [CatalogEntry(DETAILS, location)]

    def test_removes_it_from_the_shelf_when_the_catalog_fails(self, library):
        with pytest.raises(ConnectionError):
            file_book(ReceivedBookFile("book.pdf", b"pages"), DETAILS, library, UnavailableCatalog())

        assert not (library / "Python" / "book.pdf").exists()

    @pytest.mark.parametrize("name", [None, "", ".", "..", "../book.pdf", "nested/book.pdf"])
    def test_refuses_names_that_are_not_plain_file_names(self, library, name):
        catalog = RecordingCatalog()

        with pytest.raises(InvalidBookFileName):
            file_book(ReceivedBookFile(name, b"pages"), DETAILS, library, catalog)

        assert not library.exists()
        assert catalog.entries == []


class TestFilingADownloadedBookFile:
    def test_moves_it_out_of_downloads_onto_the_shelf(self, library, downloads):
        catalog = RecordingCatalog()

        location = file_book(downloaded(downloads), DETAILS, library, catalog)

        assert not (downloads / "book.pdf").exists()
        assert location.read_bytes() == b"pages"
        assert catalog.entries == [CatalogEntry(DETAILS, location)]

    def test_uses_an_existing_shelf(self, library, downloads):
        (library / "Python").mkdir(parents=True)
        (library / "Python" / "other.pdf").write_bytes(b"other")

        location = file_book(downloaded(downloads), DETAILS, library, RecordingCatalog())

        assert location.read_bytes() == b"pages"
        assert (library / "Python" / "other.pdf").read_bytes() == b"other"

    def test_moves_it_back_to_downloads_when_the_catalog_fails(self, library, downloads):
        with pytest.raises(ConnectionError):
            file_book(downloaded(downloads), DETAILS, library, UnavailableCatalog())

        assert (downloads / "book.pdf").read_bytes() == b"pages"
        assert not (library / "Python" / "book.pdf").exists()


class TestNameClashOnTheShelf:
    def test_refuses_and_leaves_both_book_files_alone(self, library, downloads):
        (library / "Python").mkdir(parents=True)
        (library / "Python" / "book.pdf").write_bytes(b"old")
        catalog = RecordingCatalog()

        with pytest.raises(BookAlreadyOnShelf) as clash:
            file_book(downloaded(downloads, content=b"new"), DETAILS, library, catalog)

        assert clash.value.location == library / "Python" / "book.pdf"
        assert (library / "Python" / "book.pdf").read_bytes() == b"old"
        assert (downloads / "book.pdf").read_bytes() == b"new"
        assert catalog.entries == []

    def test_filing_the_same_book_twice_files_it_once(self, library):
        catalog = RecordingCatalog()
        file_book(ReceivedBookFile("book.pdf", b"pages"), DETAILS, library, catalog)

        with pytest.raises(BookAlreadyOnShelf):
            file_book(ReceivedBookFile("book.pdf", b"other"), DETAILS, library, catalog)

        assert (library / "Python" / "book.pdf").read_bytes() == b"pages"
        assert len(catalog.entries) == 1


class TestParseBookFileName:
    def test_accepts_a_plain_file_name(self):
        assert parse_book_file_name("Clean Code.pdf") == "Clean Code.pdf"

    @pytest.mark.parametrize("name", [None, "", ".", "..", "../book.pdf", "nested/book.pdf"])
    def test_refuses_anything_else(self, name):
        with pytest.raises(InvalidBookFileName):
            parse_book_file_name(name)
