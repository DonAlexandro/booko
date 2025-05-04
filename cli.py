import os
import re
import shutil
from notion_client_wrapper import NotionClientWrapper
from dotenv import load_dotenv

load_dotenv()

NOTION_TOKEN = os.getenv("NOTION_TOKEN") or ""
NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID") or ""

BOOKS_BASE_PATH = "/Users/olexandrpylypyshyn/Documents/Books"
DOWNLOADS_PATH = "/Users/olexandrpylypyshyn/Downloads/"

notion = NotionClientWrapper(NOTION_TOKEN, NOTION_DATABASE_ID)


def list_download_files():
    files = [f for f in os.listdir(DOWNLOADS_PATH)
             if os.path.isfile(os.path.join(DOWNLOADS_PATH, f)) and not f.startswith('.')]
    return files


def prompt_input(prompt, validator=None, error_msg=None):
    while True:
        value = input(prompt)
        if validator:
            if validator(value):
                return value
            else:
                if error_msg:
                    print(error_msg)
        else:
            return value


def main():
    print("Available files in Downloads:")
    files = list_download_files()
    for idx, f in enumerate(files):
        print(f"{idx+1}. {f}")
    if not files:
        print("No files found in Downloads.")
        return
    file_idx = int(prompt_input("Select file number: ", lambda x: x.isdigit(
    ) and 1 <= int(x) <= len(files), "Invalid selection.")) - 1
    file_name = files[file_idx]
    file_path = os.path.join(DOWNLOADS_PATH, file_name)

    title = prompt_input("Book title: ")
    author = prompt_input("Author: ")
    genres = ["Саморозвиток", "Технічна література",
              "Історія і мемуари", "Бізнес"]
    print("Genres:")
    for idx, g in enumerate(genres):
        print(f"{idx+1}. {g}")
    genre_idx = int(prompt_input("Select genre number: ", lambda x: x.isdigit(
    ) and 1 <= int(x) <= len(genres), "Invalid selection.")) - 1
    genre = genres[genre_idx]
    techs = prompt_input("Technologies (hashtags, e.g. #Python #AI): ",
                         lambda x: bool(re.findall(r"#(\w+)", x)),
                         "Enter at least one hashtag.")
    technologies = re.findall(r"#(\w+)", techs)
    pages = int(prompt_input("Page count: ",
                lambda x: x.isdigit(), "Enter a number."))

    first_tag = technologies[0]
    dest_folder = os.path.join(BOOKS_BASE_PATH, first_tag)
    os.makedirs(dest_folder, exist_ok=True)
    dest_path = os.path.join(dest_folder, file_name)
    shutil.move(file_path, dest_path)

    notion.add_file_entry(
        title=title,
        author=author,
        genre=genre,
        technologies=technologies,
        pages=pages,
        file_path=dest_path
    )
    print(f"✅ Book saved to: {dest_path} and added to Notion.")
    print(f"🗑️ Deleted original file from Downloads.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nBooko is stopped. Till next time! :)")
