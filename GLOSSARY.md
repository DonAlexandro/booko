# Booko

Booko files e-books into a personal library on disk and records each one in a Notion catalog.

## Books

**Book file**:
The e-book document itself (PDF, EPUB, etc.) as received from the user.
_Avoid_: Document, attachment, upload

**Book details**:
The descriptive facts the user supplies about a book: title, author, genre, technologies and page count.
_Avoid_: Metadata, book data, form

**Genre**:
One of a fixed set of broad categories a book belongs to (Саморозвиток, Технічна література, Історія і мемуари, Бізнес).
_Avoid_: Category, type

**Technology**:
A topic tag for a book, written by the user as a hashtag (e.g. `#Python`); a book has one or more, in order.
_Avoid_: Tag, hashtag, label

## Filing

**Inbox**:
Where a book file waits before it is filed: the Downloads folder for the CLI, a received Telegram document for the bot.
_Avoid_: Source, Downloads (as a general term)

**Library**:
The root folder on disk under which all filed book files live.
_Avoid_: Books folder, storage

**Shelf**:
The folder inside the library named after a book's first technology, where its book file is placed.
_Avoid_: Destination folder, tag folder

**Catalog**:
The Notion database holding one entry per filed book.
_Avoid_: Notion (as a domain term), database, records

**Catalog entry**:
A catalog row describing one book: its book details plus where its book file sits on its shelf.
_Avoid_: Notion page, record

**Filing**:
Taking a book file from the inbox together with its book details, placing it on its shelf and adding its catalog entry, as one all-or-nothing step.
_Avoid_: Ingestion, upload, saving, processing
