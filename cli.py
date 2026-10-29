from pathlib import Path

from filing import (
    BookAlreadyOnShelf,
    BookDetails,
    DownloadedBookFile,
    Genre,
    file_book,
    parse_page_count,
    parse_technologies,
    parse_text,
)
from notion_catalog import NotionCatalog
from settings import MissingSetting, load_settings

DOWNLOADS_PATH = Path.home() / "Downloads"


def list_download_files():
    return sorted(p for p in DOWNLOADS_PATH.iterdir()
                  if p.is_file() and not p.name.startswith("."))


def ask(prompt, parse, error_msg):
    while True:
        try:
            return parse(input(prompt))
        except ValueError:
            print(error_msg)


def choose(prompt, options):
    def parse(text):
        text = text.strip()
        if not (text.isdigit() and 1 <= int(text) <= len(options)):
            raise ValueError(text)
        return options[int(text) - 1]

    return ask(prompt, parse, "Invalid selection.")


def ask_book_details():
    title = ask("Book title: ", parse_text, "Enter a title.")
    author = ask("Author: ", parse_text, "Enter an author.")
    genres = list(Genre)
    print("Genres:")
    for idx, g in enumerate(genres, 1):
        print(f"{idx}. {g.value}")
    genre = choose("Select genre number: ", genres)
    technologies = ask("Technologies (hashtags, e.g. #Python #AI): ",
                       parse_technologies, "Enter at least one hashtag.")
    pages = ask("Page count: ", parse_page_count, "Enter a positive whole number.")
    return BookDetails(title, author, genre, technologies, pages)


def main():
    try:
        settings = load_settings()
    except MissingSetting as e:
        print(f"⚠️ {e}")
        return

    files = list_download_files()
    if not files:
        print("No files found in Downloads.")
        return
    print("Available files in Downloads:")
    for idx, f in enumerate(files, 1):
        print(f"{idx}. {f.name}")
    book_file = DownloadedBookFile(choose("Select file number: ", files))
    details = ask_book_details()

    catalog = NotionCatalog.connect(settings.notion_token, settings.notion_database_id)
    try:
        location = file_book(book_file, details, settings.library, catalog)
    except BookAlreadyOnShelf as e:
        print(f"⚠️ {e.location} already exists; nothing was changed.")
        return
    except Exception as e:
        print(f"⚠️ Could not file the book ({e}); it is still in Downloads.")
        return
    print(f"✅ Book moved from Downloads to {location} and added to Notion.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nBooko is stopped. Till next time! :)")
