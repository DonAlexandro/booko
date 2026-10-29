from pathlib import Path

from filing import BookDetails, CatalogEntry, Genre
from notion_catalog import NotionCatalog


class RecordingPages:
    def __init__(self):
        self.created = []

    def create(self, **page):
        self.created.append(page)


class FakeNotionClient:
    def __init__(self):
        self.pages = RecordingPages()


def test_adds_one_notion_page_per_catalog_entry():
    client = FakeNotionClient()
    entry = CatalogEntry(
        BookDetails(
            title="Clean Code",
            author="Robert C. Martin",
            genre=Genre.TECHNICAL,
            technologies=("Python", "AI"),
            page_count=464,
        ),
        Path("/Library/Python/book.pdf"),
    )

    NotionCatalog(client, "catalog-id").add(entry)

    assert client.pages.created == [{
        "parent": {"database_id": "catalog-id"},
        "properties": {
            "Name": {"title": [{"text": {"content": "Clean Code"}}]},
            "Tags": {"select": {"name": "Backlog"}},
            "Author": {"rich_text": [{"text": {"content": "Robert C. Martin"}}]},
            "Жанр": {"select": {"name": "Технічна література"}},
            "Технологія": {"multi_select": [{"name": "Python"}, {"name": "AI"}]},
            "Кількість сторінок": {"number": 464},
            "Розташування": {"rich_text": [{"text": {"content": "/Library/Python/book.pdf"}}]},
            "Тип": {"select": {"name": "Електронна копія"}},
        },
    }]
