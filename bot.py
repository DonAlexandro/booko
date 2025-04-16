import asyncio
import os
import re
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
import aiofiles
from dotenv import load_dotenv
from notion_client_wrapper import NotionClientWrapper
from aiogram.client.default import DefaultBotProperties
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

logging.basicConfig(level=logging.INFO)

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN") or ""
NOTION_TOKEN = os.getenv("NOTION_TOKEN") or ""
NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID") or ""

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(
    parse_mode=ParseMode.HTML))
dp = Dispatcher(storage=MemoryStorage())
notion = NotionClientWrapper(NOTION_TOKEN, NOTION_DATABASE_ID)

BOOKS_BASE_PATH = "/Users/olexandrpylypyshyn/Documents/Books"

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

    file_name = file.file_name
    file_obj = await bot.get_file(file.file_id)

    if not file_obj.file_path:
        await message.answer("⚠️ Не вдалося отримати шлях до файлу. Спробуй ще раз.")
        return

    file_data = await bot.download_file(file_obj.file_path)

    await state.update_data(file_name=file_name, file_data=file_data)
    await state.set_state(BookUpload.waiting_for_title)
    await message.answer("📖 Як називається книга?")

# Title


@dp.message(BookUpload.waiting_for_title)
async def process_title(message: types.Message, state: FSMContext):
    await state.update_data(title=message.text)
    await state.set_state(BookUpload.waiting_for_author)
    await message.answer("👤 Хто автор?")

# Автор


@dp.message(BookUpload.waiting_for_author)
async def handle_author(message: types.Message, state: FSMContext):
    await state.update_data(author=message.text)
    await state.set_state(BookUpload.waiting_for_genre)

    keyboard = types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(text="Саморозвиток"),
             types.KeyboardButton(text="Технічна література")],
            [types.KeyboardButton(text="Історія і мемуари"),
             types.KeyboardButton(text="Бізнес")]
        ],
        resize_keyboard=True
    )

    await message.answer("📚 Обери жанр книги:", reply_markup=keyboard)

# Жанр


@dp.message(BookUpload.waiting_for_genre)
async def handle_genre(message: types.Message, state: FSMContext):
    if not message.text:
        await message.answer("⚠️ Повідомлення не може бути порожнім. Спробуй ще раз.")
        return

    genre = message.text.strip()

    if genre not in ["Саморозвиток", "Технічна література", "Історія і мемуари", "Бізнес"]:
        await message.answer("⚠️ Вибери жанр з клавіатури")
        return

    await state.update_data(genre=genre)
    await state.set_state(BookUpload.waiting_for_technologies)
    await message.answer("💡 Вкажи технології через хештеги (наприклад: #Python #AI)")

# Технології


@dp.message(BookUpload.waiting_for_technologies)
async def handle_technologies(message: types.Message, state: FSMContext):
    hashtags = re.findall(r"#(\w+)", message.text or "")

    if not hashtags:
        await message.answer("⚠️ Введи хоча б один хештег")
        return

    await state.update_data(technologies=hashtags)
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
        if not message.text:
            await message.answer("⚠️ Повідомлення не може бути порожнім. Спробуй ще раз.")
            return

        page_count = int(message.text.strip())
    except ValueError:
        await message.answer("⚠️ Введи ціле число сторінок")
        return

    data = await state.get_data()
    file_name = data["file_name"]
    file_data = data["file_data"]
    title = data["title"]
    author = data["author"]
    genre = data["genre"]
    technologies = data["technologies"]
    first_tag = technologies[0]
    pages = page_count

    folder_path = os.path.join(BOOKS_BASE_PATH, first_tag)
    os.makedirs(folder_path, exist_ok=True)
    file_path = os.path.join(folder_path, file_name)

    async with aiofiles.open(file_path, "wb") as f:
        await f.write(file_data.read())

    notion.add_file_entry(
        title=title,
        author=author,
        genre=genre,
        technologies=technologies,
        pages=pages,
        file_path=file_path
    )

    await message.answer(f"✅ Книгу збережено в: <code>{file_path}</code>\n"
                         f"І додано в базу Notion! 🎉",
                         reply_markup=get_post_process_keyboard())
    await state.clear()


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
