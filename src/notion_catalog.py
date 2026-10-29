from notion_client import Client

from filing import CatalogEntry


class NotionCatalog:
    def __init__(self, client, database_id: str):
        self.client = client
        self.database_id = database_id

    @classmethod
    def connect(cls, token: str, database_id: str) -> "NotionCatalog":
        return cls(Client(auth=token), database_id)

    def add(self, entry: CatalogEntry) -> None:
        details = entry.details
        self.client.pages.create(
            parent={"database_id": self.database_id},
            properties={
                "Name": {"title": [{"text": {"content": details.title}}]},
                "Tags": {"select": {"name": "Backlog"}},
                "Author": {"rich_text": [{"text": {"content": details.author}}]},
                "Жанр": {"select": {"name": details.genre.value}},
                "Технологія": {"multi_select": [{"name": t} for t in details.technologies]},
                "Кількість сторінок": {"number": details.page_count},
                "Розташування": {"rich_text": [{"text": {"content": str(entry.location)}}]},
                "Тип": {"select": {"name": "Електронна копія"}},
            },
        )
