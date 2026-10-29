# Booko

## About

Telegram bot in Python, to which I will send files and add tags (for example, #AI, #Python, #Node.js, etc.), the bot will immediately download the files, organize them into folders according to the hashtag in the message and also create a record in the Notion library

## How it works

Booko files a book in one all-or-nothing step: it places the book file on its
shelf (a folder in your library named after the book's first technology) and
adds a catalog entry to Notion. If Notion fails, the book file goes back where
it came from; if the shelf already has a book file with that name, nothing is
changed. Terms are defined in [GLOSSARY.md](GLOSSARY.md).

## Setup

Install [uv](https://docs.astral.sh/uv/), then:

```sh
uv sync
cp .env.example .env   # fill in BOT_TOKEN, NOTION_TOKEN, NOTION_DATABASE_ID
```

`BOOKO_LIBRARY` is optional and defaults to `~/Documents/Books`.

## Usage

- Telegram bot: `uv run bot.py`, then send `/start` and a book file.
- CLI: `uv run cli.py` files a book from `~/Downloads`.

## Development

`uv sync` installs the dev tools too (pytest, coverage, radon, mutmut, pylint).

```sh
uv run pytest
```

Add dependencies with `uv add <package>` (or `uv add --dev <package>`);
commit both `pyproject.toml` and `uv.lock`.
