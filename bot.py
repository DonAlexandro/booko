import asyncio
import html
import logging
import os

from aiogram import Bot, Dispatcher, F, types
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from filing import (
    BookAlreadyOnShelf,
    BookDetails,
    Genre,
    InvalidBookDetails,
    InvalidBookFileName,
    ReceivedBookFile,
    file_book,
    parse_book_file_name,
    parse_genre,
    parse_page_count,
    parse_technologies,
    parse_text,
)
from notion_catalog import NotionCatalog
from settings import load_settings

logging.basicConfig(level=logging.INFO)

settings = load_settings()
BOT_TOKEN = os.getenv("BOT_TOKEN") or ""

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(
    parse_mode=ParseMode.HTML))
dp = Dispatcher(storage=MemoryStorage())
catalog = NotionCatalog.connect(settings.notion_token, settings.notion_database_id)

# FSM


class BookUpload(StatesGroup):
    waiting_for_file = State()
    waiting_for_title = State()
    waiting_for_author = State()
    waiting_for_genre = State()
    waiting_for_technologies = State()
    waiting_for_page_count = State()


# Start


@dp.message(CommandStart())
async def start_handler(message: types.Message, state: FSMContext):
    await state.set_state(BookUpload.waiting_for_file)
    await message.answer("Надішли файл книги 📚")

# Обробка файлу


@dp.message(BookUpload.waiting_for_file, F.document)
async def handle_file(message: types.Message, state: FSMContext):
    await message.answer("⏳ Обробка книги…")

    file = message.document

    if not file:
        await message.answer("⚠️ Не вдалося отримати файл. Спробуй ще раз.")
        return

    try:
        file_name = parse_book_file_name(file.file_name)
    except InvalidBookFileName:
        await message.answer("⚠️ У файлу некоректна назва. Перейменуй його і надішли ще раз.")
        return

    file_obj = await bot.get_file(file.file_id)

    if not file_obj.file_path:
        await message.answer("⚠️ Не вдалося отримати шлях до файлу. Спробуй ще раз.")
        return

    file_data = await bot.download_file(file_obj.file_path)

    if file_data is None:
        await message.answer("⚠️ Не вдалося завантажити файл. Спробуй ще раз.")
        return

    await state.update_data(file_name=file_name, file_content=file_data.read())
    await state.set_state(BookUpload.waiting_for_title)
    await message.answer("📖 Як називається книга?")

# Title


@dp.message(BookUpload.waiting_for_title)
async def process_title(message: types.Message, state: FSMContext):
    try:
        title = parse_text(message.text)
    except InvalidBookDetails:
        await message.answer("⚠️ Назва не може бути порожньою. Спробуй ще раз.")
        return

    await state.update_data(title=title)
    await state.set_state(BookUpload.waiting_for_author)
    await message.answer("👤 Хто автор?")

# Автор


@dp.message(BookUpload.waiting_for_author)
async def handle_author(message: types.Message, state: FSMContext):
    try:
        author = parse_text(message.text)
    except InvalidBookDetails:
        await message.answer("⚠️ Автор не може бути порожнім. Спробуй ще раз.")
        return

    await state.update_data(author=author)
    await state.set_state(BookUpload.waiting_for_genre)

    genres = [types.KeyboardButton(text=g.value) for g in Genre]
    keyboard = types.ReplyKeyboardMarkup(
        keyboard=[genres[i:i + 2] for i in range(0, len(genres), 2)],
        resize_keyboard=True
    )

    await message.answer("📚 Обери жанр книги:", reply_markup=keyboard)

# Жанр


@dp.message(BookUpload.waiting_for_genre)
async def handle_genre(message: types.Message, state: FSMContext):
    try:
        genre = parse_genre(message.text)
    except InvalidBookDetails:
        await message.answer("⚠️ Вибери жанр з клавіатури")
        return

    await state.update_data(genre=genre)
    await state.set_state(BookUpload.waiting_for_technologies)
    await message.answer("💡 Вкажи технології через хештеги (наприклад: #Python #AI)")

# Технології


@dp.message(BookUpload.waiting_for_technologies)
async def handle_technologies(message: types.Message, state: FSMContext):
    try:
        technologies = parse_technologies(message.text)
    except InvalidBookDetails:
        await message.answer("⚠️ Введи хоча б один хештег")
        return

    await state.update_data(technologies=technologies)
    await state.set_state(BookUpload.waiting_for_page_count)
    await message.answer("📄 Скільки сторінок у книзі?")

# Кількість сторінок + Завершення


def get_post_process_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📚 Додати ще 1 книгу",
                                 callback_data="add_another"),
            InlineKeyboardButton(text="✅ Завершити", callback_data="finish")
        ]
    ])


@dp.message(BookUpload.waiting_for_page_count)
async def handle_page_count(message: types.Message, state: FSMContext):
    try:
        page_count = parse_page_count(message.text)
    except InvalidBookDetails:
        await message.answer("⚠️ Введи додатне ціле число сторінок")
        return

    data = await state.get_data()
    await state.clear()
    details = BookDetails(data["title"], data["author"], data["genre"],
                          data["technologies"], page_count)
    book_file = ReceivedBookFile(data["file_name"], data["file_content"])

    try:
        location = await asyncio.to_thread(
            file_book, book_file, details, settings.library, catalog)
    except BookAlreadyOnShelf as e:
        reply = f"⚠️ Книга вже є в <code>{html.escape(str(e.location))}</code>. Нічого не змінено."
    except Exception:
        logging.exception("Filing failed")
        reply = "⚠️ Не вдалося зберегти книгу. Нічого не змінено, спробуй ще раз."
    else:
        reply = (f"✅ Книгу збережено в: <code>{html.escape(str(location))}</code>\n"
                 f"І додано в базу Notion! 🎉")

    await message.answer(reply, reply_markup=get_post_process_keyboard())


@dp.callback_query(F.data == "add_another")
async def callback_add_another(callback: types.CallbackQuery, state: FSMContext):
    message = "📥 Надішли файл нової книги"

    await state.set_state(BookUpload.waiting_for_file)
    if callback.message is not None:
        await callback.message.answer(message)
    else:
        await bot.send_message(callback.from_user.id, message)


@dp.callback_query(F.data == "finish")
async def callback_finish(callback: types.CallbackQuery):
    message = "🔚 Ти завжди можеш додати більше книг пізніше — просто надішли мені команду /start."

    if callback.message is not None:
        await callback.message.answer(message)
    else:
        await bot.send_message(callback.from_user.id, message)


async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
