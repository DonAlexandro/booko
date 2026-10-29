import asyncio
import inspect
from io import BytesIO
from types import SimpleNamespace

import pytest
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.base import StorageKey
from aiogram.fsm.storage.memory import MemoryStorage

import bot
from bot import BookUpload
from filing import BookDetails, CatalogEntry, Genre
from samples import RecordingCatalog, UnavailableCatalog

HANDLERS = {
    BookUpload.waiting_for_file.state: bot.handle_file,
    BookUpload.waiting_for_title.state: bot.process_title,
    BookUpload.waiting_for_author.state: bot.handle_author,
    BookUpload.waiting_for_genre.state: bot.handle_genre,
    BookUpload.waiting_for_technologies.state: bot.handle_technologies,
    BookUpload.waiting_for_page_count.state: bot.handle_page_count,
}


class FakeTelegram:
    """Stands in for aiogram's Bot: serves uploaded files and records direct messages."""

    def __init__(self, files=None):
        self.files = files or {}
        self.sent = []

    async def get_file(self, file_id):
        return SimpleNamespace(file_path=file_id if file_id in self.files else None)

    async def download_file(self, file_path):
        content = self.files[file_path]
        return None if content is None else BytesIO(content)

    async def send_message(self, chat_id, text):
        self.sent.append(text)


class Chat:
    """One user's chat with the bot, routing each message as the dispatcher would."""

    def __init__(self, library, catalog, telegram):
        self.state = FSMContext(MemoryStorage(), StorageKey(bot_id=1, chat_id=1, user_id=1))
        self.replies = []
        self.markups = []
        self.injected = {"bot": telegram, "library": library, "catalog": catalog}

    async def answer(self, text, reply_markup=None):
        self.replies.append(text)
        self.markups.append(reply_markup)

    def message(self, text=None, document=None):
        return SimpleNamespace(text=text, document=document, answer=self.answer)

    async def call(self, handler, event):
        wanted = inspect.signature(handler).parameters
        kwargs = {k: v for k, v in self.injected.items() if k in wanted}
        await handler(event, state=self.state, **kwargs) if "state" in wanted else (
            await handler(event, **kwargs))

    async def start(self):
        await self.call(bot.start_handler, self.message("/start"))

    async def send(self, text=None, document=None):
        await self.call(HANDLERS[await self.state.get_state()], self.message(text, document))

    async def press(self, data, in_chat=True):
        callback = SimpleNamespace(data=data, from_user=SimpleNamespace(id=1),
                                   message=self.message() if in_chat else None)
        handler = {"add_another": bot.callback_add_another, "finish": bot.callback_finish}[data]
        await self.call(handler, callback)


def document(name, file_id="file-1"):
    return SimpleNamespace(file_name=name, file_id=file_id)


@pytest.fixture
def library(tmp_path):
    return tmp_path / "Library"


def chat_with(library, catalog=None, files=None):
    return Chat(library, catalog or RecordingCatalog(),
                FakeTelegram({"file-1": b"pages"} if files is None else files))


async def send_book(chat, name="R&D.pdf"):
    await chat.start()
    for text, doc in [(None, document(name)), ("Clean Code", None), ("Robert C. Martin", None),
                      ("Технічна література", None), ("#Python #AI", None), ("464", None)]:
        await chat.send(text, doc)


def test_files_a_sent_book_and_offers_to_add_another(library):
    catalog = RecordingCatalog()
    chat = chat_with(library, catalog)

    asyncio.run(send_book(chat))

    location = library / "Python" / "R&D.pdf"
    assert location.read_bytes() == b"pages"
    assert catalog.entries == [CatalogEntry(BookDetails(
        "Clean Code", "Robert C. Martin", Genre.TECHNICAL, ("Python", "AI"), 464), location)]
    assert chat.replies[-1] == (f"✅ Книгу збережено в: <code>{library}/Python/R&amp;D.pdf</code>\n"
                                "І додано в базу Notion! 🎉")
    buttons = chat.markups[-1].inline_keyboard[0]
    assert [b.callback_data for b in buttons] == ["add_another", "finish"]
    assert asyncio.run(chat.state.get_state()) is None


def test_offers_every_genre_on_the_keyboard(library):
    chat = chat_with(library)

    async def until_genre():
        await chat.start()
        for text, doc in [(None, document("a.pdf")), ("Clean Code", None), ("Bob", None)]:
            await chat.send(text, doc)

    asyncio.run(until_genre())

    keyboard = chat.markups[-1].keyboard
    assert [[b.text for b in row] for row in keyboard] == [
        ["Саморозвиток", "Технічна література"], ["Історія і мемуари", "Бізнес"]]


@pytest.mark.parametrize("step, invalid, warning", [
    (BookUpload.waiting_for_title, " ", "⚠️ Назва не може бути порожньою. Спробуй ще раз."),
    (BookUpload.waiting_for_author, None, "⚠️ Автор не може бути порожнім. Спробуй ще раз."),
    (BookUpload.waiting_for_genre, "Фантастика", "⚠️ Вибери жанр з клавіатури"),
    (BookUpload.waiting_for_technologies, "Python", "⚠️ Введи хоча б один хештег"),
    (BookUpload.waiting_for_page_count, "0", "⚠️ Введи додатне ціле число сторінок"),
])
def test_asks_again_when_an_answer_is_invalid(library, step, invalid, warning):
    chat = chat_with(library)

    async def answer_invalid():
        await chat.state.set_state(step)
        await chat.send(invalid)

    asyncio.run(answer_invalid())

    assert chat.replies == [warning]
    assert asyncio.run(chat.state.get_state()) == step.state


@pytest.mark.parametrize("files, name, warning", [
    ({"file-1": b"pages"}, "../escape.pdf",
     "⚠️ У файлу некоректна назва. Перейменуй його і надішли ще раз."),
    ({}, "a.pdf", "⚠️ Не вдалося отримати шлях до файлу. Спробуй ще раз."),
    ({"file-1": None}, "a.pdf", "⚠️ Не вдалося завантажити файл. Спробуй ще раз."),
])
def test_waits_for_another_file_when_this_one_cannot_be_used(library, files, name, warning):
    chat = chat_with(library, files=files)

    async def send_file():
        await chat.start()
        await chat.send(document=document(name))

    asyncio.run(send_file())

    assert chat.replies[-1] == warning
    assert asyncio.run(chat.state.get_state()) == BookUpload.waiting_for_file.state


def test_files_nothing_when_the_catalog_fails(library):
    chat = chat_with(library, UnavailableCatalog())

    asyncio.run(send_book(chat))

    assert chat.replies[-1] == "⚠️ Не вдалося зберегти книгу. Нічого не змінено, спробуй ще раз."
    assert not (library / "Python" / "R&D.pdf").exists()
    assert asyncio.run(chat.state.get_state()) is None


def test_files_nothing_when_the_book_is_already_on_its_shelf(library):
    (library / "Python").mkdir(parents=True)
    (library / "Python" / "R&D.pdf").write_bytes(b"old")
    catalog = RecordingCatalog()
    chat = chat_with(library, catalog)

    asyncio.run(send_book(chat))

    assert chat.replies[-1] == (
        f"⚠️ Книга вже є в <code>{library}/Python/R&amp;D.pdf</code>. Нічого не змінено.")
    assert (library / "Python" / "R&D.pdf").read_bytes() == b"old"
    assert catalog.entries == []


@pytest.mark.parametrize("in_chat", [True, False])
def test_add_another_waits_for_the_next_book_file(library, in_chat):
    chat = chat_with(library)

    asyncio.run(chat.press("add_another", in_chat))

    assert asyncio.run(chat.state.get_state()) == BookUpload.waiting_for_file.state
    replies = chat.replies if in_chat else chat.injected["bot"].sent
    assert replies == ["📥 Надішли файл нової книги"]


@pytest.mark.parametrize("in_chat", [True, False])
def test_finish_says_goodbye(library, in_chat):
    chat = chat_with(library)

    asyncio.run(chat.press("finish", in_chat))

    replies = chat.replies if in_chat else chat.injected["bot"].sent
    assert replies == [
        "🔚 Ти завжди можеш додати більше книг пізніше — просто надішли мені команду /start."]
