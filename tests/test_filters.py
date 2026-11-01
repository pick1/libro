import unittest

from libro.filters import (
    book_tags,
    build_tag_index,
    filter_books,
    normalize_tag,
    tag_slug,
)


def make_book(title, tags, summary="", author="Someone"):
    return {
        "title": title,
        "author": author,
        "genre_tags": tags,
        "summary": summary,
    }


LIBRARY = [
    make_book("Snow Crash", ["sci-fi", "cyberpunk", "dystopian"]),
    make_book("A Scanner Darkly", ["sci-fi", "dystopian"], "A hallucinatory trip."),
    make_book("Ready Player One", ["sci-fi", "dystopian", "gaming"]),
    make_book("Nettle & Bone", ["dark-fantasy", "cozy-fantasy"]),
    make_book("Dune", ["sci-fi", "political"]),
    make_book("Untitled", [], summary="No tags at all."),
]


class NormalizeTagTests(unittest.TestCase):
    def test_trims_and_lowercases(self):
        self.assertEqual(normalize_tag("  Sci-Fi "), "sci-fi")

    def test_handles_none_and_empty(self):
        self.assertEqual(normalize_tag(None), "")
        self.assertEqual(normalize_tag(""), "")


class BookTagsTests(unittest.TestCase):
    def test_de_duplicates_case_insensitively(self):
        book = make_book("X", ["Sci-Fi", "sci-fi", " sci-fi "])
        self.assertEqual(book_tags(book), ["sci-fi"])

    def test_handles_missing_and_empty_tag_lists(self):
        self.assertEqual(book_tags({"title": "X"}), [])
        self.assertEqual(book_tags(make_book("X", [])), [])


class TagIndexTests(unittest.TestCase):
    def test_counts_books_per_tag_sorted_by_count_then_alpha(self):
        index = build_tag_index(LIBRARY)
        # sci-fi appears on 4 books, dystopian on 3: highest count sorts first.
        self.assertEqual(index[0], ("sci-fi", 4))
        self.assertEqual(index[1], ("dystopian", 3))
        # Everything after the two 3/4-count tags is alphabetical within count 1.
        single = [tag for tag, count in index if count == 1]
        self.assertEqual(single, sorted(single))

    def test_counts_distinct_books_not_repeated_tags(self):
        index = dict(build_tag_index([make_book("X", ["a", "a", "a"])]))
        self.assertEqual(index["a"], 1)

    def test_excludes_untagged_books(self):
        tags = [tag for tag, _ in build_tag_index(LIBRARY)]
        self.assertNotIn("untitled", tags)
        self.assertNotIn("no tags at all", tags)


class FilterBooksTests(unittest.TestCase):
    def test_no_filters_returns_everything(self):
        self.assertEqual(len(filter_books(LIBRARY)), len(LIBRARY))

    def test_single_tag_matches_exactly_and_across_books(self):
        titles = [b["title"] for b in filter_books(LIBRARY, ["dystopian"])]
        self.assertEqual(
            titles, ["Snow Crash", "A Scanner Darkly", "Ready Player One"]
        )

    def test_tag_match_is_exact_not_substring(self):
        # "fantasy" must not pull in "dark-fantasy" / "cozy-fantasy".
        titles = [b["title"] for b in filter_books(LIBRARY, ["fantasy"])]
        self.assertEqual(titles, [])

    def test_multiple_tags_combine_with_or(self):
        titles = [
            b["title"]
            for b in filter_books(LIBRARY, ["dystopian", "cozy-fantasy"])
        ]
        self.assertEqual(
            titles, ["Snow Crash", "A Scanner Darkly", "Ready Player One", "Nettle & Bone"]
        )

    def test_tag_selection_is_case_and_whitespace_insensitive(self):
        titles = [b["title"] for b in filter_books(LIBRARY, ["  DYSTOPIAN "])]
        self.assertEqual(len(titles), 3)

    def test_blank_and_empty_selectors_are_ignored(self):
        self.assertEqual(
            len(filter_books(LIBRARY, ["", "  "], "")), len(LIBRARY)
        )

    def test_query_searches_title_and_summary(self):
        self.assertEqual(
            [b["title"] for b in filter_books(LIBRARY, [], "scanner")],
            ["A Scanner Darkly"],
        )
        self.assertEqual(
            [b["title"] for b in filter_books(LIBRARY, [], "hallucinatory")],
            ["A Scanner Darkly"],
        )

    def test_query_does_not_search_author(self):
        self.assertEqual(filter_books(LIBRARY, [], "someone"), [])

    def test_query_combines_with_tags_using_and(self):
        titles = [b["title"] for b in filter_books(LIBRARY, ["sci-fi"], "player")]
        self.assertEqual(titles, ["Ready Player One"])

    def test_untagged_book_is_hidden_when_any_tag_is_selected(self):
        titles = [b["title"] for b in filter_books(LIBRARY, ["sci-fi"])]
        self.assertNotIn("Untitled", titles)
        # ...but reachable by text search alone.
        self.assertIn("Untitled", [b["title"] for b in filter_books(LIBRARY, [], "untitled")])


class TagSlugTests(unittest.TestCase):
    def test_is_stable_and_case_insensitive(self):
        self.assertEqual(tag_slug("Sci-Fi"), tag_slug(" sci-fi "))

    def test_distinguishes_different_tags(self):
        self.assertNotEqual(tag_slug("sci-fi"), tag_slug("dystopian"))


if __name__ == "__main__":
    unittest.main()
