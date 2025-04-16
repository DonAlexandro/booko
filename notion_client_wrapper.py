from notion_client import Client
import datetime


class NotionClientWrapper:
    def __init__(self, token: str, database_id: str):
        self.client = Client(auth=token)
        self.database_id = database_id

    def add_file_entry(self, title: str, author: str, genre: str, technologies: list[str], pages: int, file_path: str):
        self.client.pages.create(
            parent={"database_id": self.database_id},
            properties={
                "Name": {"title": [{"text": {"content": title}}]},
                "Tags": {"select": {"name": "Backlog"}},
                "Author": {"rich_text": [{"text": {"content": author}}]},
                "Жанр": {"select": {"name": genre}},
                "Технологія": {"multi_select": [{"name": tag} for tag in technologies]},
                "Кількість сторінок": {"number": pages},
                "Розташування": {"rich_text": [{"text": {"content": file_path}}]},
                "Тип": {"select": {"name": "Електронна копія"}},
            }
        )
