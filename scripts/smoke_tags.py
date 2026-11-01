"""Headless smoke test: drive the real app and exercise tag filtering.

Run with:  venv/bin/python scripts/smoke_tags.py
"""

import os
import sys

from streamlit.testing.v1 import AppTest

APP = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "app.py")


def run():
    at = AppTest.from_file(APP, default_timeout=300).run()
    if at.exception:
        for e in at.exception:
            print("EXCEPTION:", e.value)
        sys.exit(1)
    return at


def buttons_named(at, name):
    return [b for b in at.button if b.label == name]


print("1. initial load")
at = run()
print(f"   books rendered : {len(at.markdown)}")
card_tag_btns = [b for b in at.button if b.key and b.key.startswith("card__")]
print(f"   card tag btns  : {len(card_tag_btns)}")
dystopian = [b for b in card_tag_btns if b.label == "dystopian"]
print(f"   'dystopian' btns: {len(dystopian)} (Snow Crash, A Scanner Darkly, Ready Player One)")
assert dystopian, "expected Snow Crash's 'dystopian' tag to render"
before = len(at.markdown)

print("\n2. click 'dystopian' on the first card")
dystopian[0].click().run()
active = [b for b in at.button if b.key and b.key.startswith("active__")]
print(f"   active chips   : {[b.label for b in active]}")
assert [b.label for b in active] == ["✕ dystopian"], active
card_tags = [b for b in at.button if b.key and b.key.startswith("card__")]
print(f"   books after    : {len(at.markdown)} markdown nodes (was {before})")
assert len(at.markdown) < before, "clicking a tag should shrink the feed"

print("\n3. clicking the same tag again unselects it")
[b for b in at.button if b.key and b.key.startswith("active__")][0].click().run()
active = [b for b in at.button if b.key and b.key.startswith("active__")]
print(f"   active chips   : {[b.label for b in active]}")
assert active == [], "toggle-off should clear the filter"
assert len(at.markdown) == before, "feed should be restored"


def book_count(at):
    """One Delete button per rendered card."""
    return len([b for b in at.button if b.key and b.key.startswith("delete_")])


def pick(at, key_prefix, label):
    for b in at.button:
        if b.key and b.key.startswith(key_prefix) and b.label == label:
            return b
    raise AssertionError(f"no {key_prefix}* button labelled {label!r}")


total_books = book_count(at)
print(f"   library size   : {total_books} books")

print("\n4. single tag -> only that kind of book")
pick(at, "card__", "dystopian").click().run()
dystopian_books = book_count(at)
print(f"   'dystopian'    : {dystopian_books} books")
assert 0 < dystopian_books < total_books, (dystopian_books, total_books)

print("\n5. adding a second tag -> OR, the feed widens")
# From the sidebar's full tag list: once `dystopian` is active, cozy-fantasy is
# correctly no longer in the feed, so this also exercises the sidebar browser.
cozy = [b for b in at.button
        if b.key and b.key.startswith("sidebar__")
        and b.label.startswith("cozy-fantasy")]
assert cozy, "expected cozy-fantasy in the sidebar tag list"
print(f"   sidebar button : {cozy[0].label!r}")
cozy[0].click().run()
active = sorted(b.label for b in at.button if b.key and b.key.startswith("active__"))
print(f"   active chips   : {active}")
assert active == ["✕ cozy-fantasy", "✕ dystopian"], active
or_books = book_count(at)
print(f"   books shown    : {or_books} (was {dystopian_books} with dystopian only)")
assert or_books > dystopian_books, (or_books, dystopian_books)

print("\n6. free-text search narrows further (AND with tags)")
at.text_input[0].set_value("nettle").run()
active = sorted(b.label for b in at.button if b.key and b.key.startswith("active__"))
searched = book_count(at)
print(f"   active chips   : {active} (tags survive the text search)")
print(f"   books shown    : {searched}")
assert active == ["✕ cozy-fantasy", "✕ dystopian"], active
assert searched < or_books, (searched, or_books)
assert not at.exception, at.exception

print("\n7. Clear filters resets everything")
at.button(key="clear_filters").click().run()
active = [b for b in at.button if b.key and b.key.startswith("active__")]
print(f"   active chips   : {active}")
print(f"   search box     : {at.text_input[0].value!r}")
print(f"   books shown    : {book_count(at)}")
assert active == [], active
assert at.text_input[0].value == "", at.text_input[0].value
assert book_count(at) == total_books
assert not at.exception, at.exception

print("\nAll smoke checks passed.")
