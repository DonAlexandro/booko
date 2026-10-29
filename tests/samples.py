from filing import BookDetails, Genre


def clean_code(**overrides) -> BookDetails:
    fields = {
        "title": "Clean Code",
        "author": "Robert C. Martin",
        "genre": Genre.TECHNICAL,
        "technologies": ("Python", "AI"),
        "page_count": 464,
    }
    return BookDetails(**(fields | overrides))


class RecordingCatalog:
    def __init__(self):
        self.entries = []

    def add(self, entry):
        self.entries.append(entry)


class UnavailableCatalog:
    def add(self, entry):
        raise ConnectionError("Notion is down")
