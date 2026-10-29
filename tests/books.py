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
