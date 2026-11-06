# Libro — Streamlit app for book discovery and want-to-read tracking.
#
# Logging: this app deliberately configures no file handler. libro.service sends
# stdout/stderr to the systemd journal (StandardOutput/StandardError=journal), so
# `journalctl -u libro -f` is the live log. A previous `logging.basicConfig`
# writing to libro_events.log at DEBUG level also captured third-party chatter
# from chromadb and sentence-transformers and grew past 3 GB with no rotation.
import streamlit as st

from libro.extractor import detect_source_type, fetch_url, clean_text
from libro.analyzer import extract_book, set_notification_callback
from libro.scanlog import log_scan, recent
import time as _time
from libro.sdpl import check_sdpl, as_fields, search_page_url, home_branch
import html as _html
from libro.auth import is_password_set, verify_password, set_password
from libro.librarian import LibrarianIndex
from libro.store import WantToReadStore
from libro.filters import book_id, book_tags, build_tag_index, filter_books, tag_slug
from libro.instagram import is_instagram_url, fetch_instagram

# Filter state. `active_tags` is a list of tags currently narrowing the feed;
# selecting more tags widens the result set (OR), and clicking a selected tag
# again removes it. `search_query` is the free-text box in the sidebar.
#
# Both are mutated from widget callbacks rather than mid-script, which is what
# Streamlit expects: callbacks run before the script re-executes, so every
# widget on the page renders from one consistent snapshot of the state.
if "active_tags" not in st.session_state:
    st.session_state.active_tags = []


def toggle_tag(tag: str) -> None:
    """Add `tag` to the active set, or remove it if already active."""
    active = [t for t in st.session_state.active_tags if t != tag]
    if len(active) == len(st.session_state.active_tags):
        active.append(tag)
    # Rebind rather than mutate, so Streamlit sees the state as changed.
    st.session_state.active_tags = active


def _ago(ts) -> str:
    if not ts:
        return ""
    s = int(_time.time() - float(ts))
    if s < 60:
        return "just now"
    if s < 3600:
        return f"{s // 60}m ago"
    if s < 86400:
        return f"{s // 3600}h ago"
    return f"{s // 86400}d ago"


def refresh_sdpl(bid: str, title: str, author) -> None:
    """Re-check one book's SDPL availability (button callback)."""
    try:
        store.update_fields(bid, as_fields(check_sdpl(title, author)))
        st.toast(f"SDPL refreshed: {title}")
    except Exception as e:
        log_scan(user_input=title, source_type="refresh", stage="sdpl", status="error", error=e)
        st.toast(f"SDPL lookup failed: {type(e).__name__}", icon="⚠️")
def clear_filters() -> None:
    st.session_state.active_tags = []
    st.session_state.search_query = ""

# Initialize stores and indices
@st.cache_resource
def get_store():
    return WantToReadStore()

@st.cache_resource
def get_librarian():
    return LibrarianIndex()

store = get_store()
librarian = get_librarian()

# Set up notification callback for analyzer
def notify_callback(msg: str, icon: str = "ℹ️"):
    st.toast(msg, icon=icon)

set_notification_callback(notify_callback)

# Page config
st.set_page_config(
    page_title="Libro",
    page_icon="📚",
    layout="centered",
    initial_sidebar_state="expanded",
)

# Custom CSS to match Signal's dark theme
st.markdown(
    """
    <style>
    /* Main background */
    .stApp {
        background-color: #111118;
        color: #FFFFFF;
    }
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background-color: #111118;
        border-right: 1px solid #2A2A35;
    }
    [data-testid="stSidebar"] .stButton>button {
        background-color: #00ff88;
        color: #111118;
        border: none;
        padding: 0.5rem 1rem;
        border-radius: 4px;
        font-weight: bold;
    }
    [data-testid="stSidebar"] .stButton>button:hover {
        background-color: #00cc6a;
    }
    /* Text area */
    [data-testid="stTextArea"] textarea {
        background-color: #1E1E28;
        color: #FFFFFF;
        border: 1px solid #2A2A35;
        border-radius: 4px;
    }
    /* Selectbox */
    [data-testid="stSelectbox"] div[data-baseweb="select"] > div {
        background-color: #1E1E28;
        color: #FFFFFF;
        border: 1px solid #2A2A35;
        border-radius: 4px;
    }
    /* Buttons in main area */
    .stButton>button {
        background-color: #2A2A35;
        color: #FFFFFF;
        border: 1px solid #3A3A45;
        border-radius: 4px;
    }
    .stButton>button:hover {
        background-color: #3A3A45;
        border-color: #4A4A55;
    }
    /* Cards for book entries */
    .book-card {
        background-color: #1E1E28;
        border-left: 4px solid #00ff88;
        padding: 1rem;
        margin-bottom: 1rem;
        border-radius: 0 4px 4px 0;
    }
    .book-card.not-available {
        border-left-color: #4488ff;
    }
    .book-card h4 {
        color: #00ff88;
        margin: 0 0 0.5rem 0;
        font-family: 'Syne', sans-serif;
    }
    .book-card p {
        color: #FFFFFF;
        margin: 0.25rem 0;
    }
    .book-card .author {
        font-style: italic;
        color: #CCCCCC;
    }
    .book-card .genre-tags {
        margin: 0.5rem 0;
    }
    /* Tag pills. Streamlit adds an st-key-<key> class to any element given a
       `key=`, so scoping to the card and sidebar tag rows keeps these styles
       off the Delete button. Prefix match, because the per-book container keys
       must be unique. */
    [class*="st-key-card_tags"] [data-testid="stBaseButton-secondary"],
    [class*="st-key-sidebar_tags"] [data-testid="stBaseButton-secondary"],
    [class*="st-key-active_tags"] [data-testid="stBaseButton-secondary"] {
        background-color: #1E1E28;
        color: #B8B8D0;
        border: 1px solid #3A3A45;
        border-radius: 999px;
        padding: 0.15rem 0.65rem;
        min-height: 0;
        font-size: 0.75rem;
        font-weight: 500;
        line-height: 1.6;
    }
    .st-key-card_tags [data-testid="stBaseButton-secondary"]:hover,
    .st-key-sidebar_tags [data-testid="stBaseButton-secondary"]:hover {
        background-color: #2A2A35;
        color: #FFFFFF;
        border-color: #00ff88;
    }
    /* Selected tag — rendered via type="primary" when the tag is active. */
    [class*="st-key-card_tags"] [data-testid="stBaseButton-primary"],
    [class*="st-key-sidebar_tags"] [data-testid="stBaseButton-primary"],
    [class*="st-key-active_tags"] [data-testid="stBaseButton-primary"] {
        background-color: #00ff88;
        color: #111118;
        border: 1px solid #00ff88;
        border-radius: 999px;
        padding: 0.15rem 0.65rem;
        min-height: 0;
        font-size: 0.75rem;
        font-weight: 700;
        line-height: 1.6;
    }
    [class*="st-key-card_tags"] button:focus,
    [class*="st-key-sidebar_tags"] button:focus {
        outline-color: #00ff88;
    }
    .book-card .summary {
        font-size: 0.9rem;
        color: #DDDDDD;
    }
    .book-card .verdict {
        font-style: italic;
        color: #00ff88;
        margin-top: 0.5rem;
    }
    .book-card .confidence-bar {
        height: 4px;
        background-color: #2A2A35;
        border-radius: 2px;
        overflow: hidden;
        margin: 0.5rem 0;
    }
    .book-card .confidence-fill {
        height: 100%;
        background-color: #00ff88;
    }
    .book-card .availability-badge {
        display: inline-block;
        background-color: #00ff88;
        color: #111118;
        padding: 0.25rem 0.5rem;
        border-radius: 4px;
        font-size: 0.875rem;
        margin-right: 0.5rem;
    }
    .book-card .availability-badge.not-available {
        background-color: #4488ff;
        color: #FFFFFF;
    }
    .book-card .delete-button {
        background-color: #ff4466;
        color: #FFFFFF;
        border: none;
        padding: 0.25rem 0.5rem;
        border-radius: 4px;
        cursor: pointer;
    }
    .book-card .delete-button:hover {
        background-color: #ff2244;
    }
    /* Stats text */
    .stats {
        font-size: 0.875rem;
        color: #AAAAAA;
        margin-top: 1rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Load the library up front so the sidebar can offer a browsable list of every
# tag in the collection, not just the tags of whatever is currently visible.
# ─── AUTH GATE ────────────────────────────────────────────────────────────
# Runs before any library data or sidebar renders; st.stop() ends the run
# for unauthenticated sessions.
if not st.session_state.get("authenticated"):
    st.markdown(
        "<h1 style='text-align:center;color:#00ff88;font-family:Syne;margin-top:40px'>Libro</h1>",
        unsafe_allow_html=True,
    )
    _, mid, _ = st.columns([1, 2, 1])
    with mid:
        if not is_password_set():
            st.markdown("**Set a password** to secure Libro.")
            with st.form("setup_pw"):
                pw = st.text_input("Password", type="password")
                pw2 = st.text_input("Confirm", type="password")
                if st.form_submit_button("Set password", type="primary", width="stretch"):
                    if len(pw) >= 8 and pw == pw2:
                        set_password(pw)
                        st.session_state.authenticated = True
                        st.rerun()
                    else:
                        st.error("Password must be 8+ characters and match.")
        else:
            with st.form("login"):
                pw = st.text_input("Password", type="password")
                if st.form_submit_button("Unlock", type="primary", width="stretch"):
                    if verify_password(pw):
                        st.session_state.authenticated = True
                        st.rerun()
                    else:
                        import time
                        time.sleep(1.5)  # slow down guessing
                        st.error("Incorrect password.")
    st.stop()
all_books = store.all()
tag_index = build_tag_index(all_books)
active_tags = list(st.session_state.active_tags)

# Sidebar
with st.sidebar:
    st.markdown("<h1 style='text-align: center; color: #00ff88; font-family: Syne;'>Libro</h1>", unsafe_allow_html=True)
    
    st.button("Lock", key="lock_app", width="stretch",
              on_click=lambda: st.session_state.pop("authenticated", None))
    # Provider selector
    provider_options = ["OpenCode (primary)", "Xavier LAN (fallback)", "Ollama (local)"]
    provider = st.selectbox("Provider", provider_options, index=0)
    
    # Map selector to provider key used in analyzer
    provider_map = {
        "OpenCode (primary)": "opencode",
        "Xavier LAN (fallback)": "xavier",
        "Ollama (local)": "ollama",
    }
    provider_key = provider_map[provider]
    
    # Input area
    st.markdown("### Paste a URL or book mention...")
    user_input = st.text_area(
        label="Input",
        placeholder="e.g., https://example.com/book-review or 'I just finished reading Project Hail Mary by Andy Weir...'",
        height=100,
        label_visibility="collapsed",
    )
    
    # SCAN button
    if st.button("SCAN", type="primary", use_container_width=True):
        if user_input.strip():
            with st.spinner("Scanning..."):
                stage, source_type = "detect", None
                try:
                    # Detect source type
                    source_type = detect_source_type(user_input)
                    
                    # Fetch content if URL
                    stage = "fetch"
                    if source_type == "url":
                        #raw_content = fetch_url(user_input)
                        raw_content = fetch_instagram(user_input) if is_instagram_url(user_input) else fetch_url(user_input)
                    else:
                        raw_content = user_input
                    
                    # Clean text
                    stage = "clean"
                    cleaned_content = clean_text(raw_content)
                    
                    # Extract book metadata (returns a list)
                    stage = "extract"
                    book_list = extract_book(cleaned_content, source_type)
                    if not book_list:
                        log_scan(user_input=user_input, source_type=source_type,
                                 stage="extract", status="empty")
                        st.warning("No books found in that content.")
                        st.stop()
                    
                    # Process each book
                    stage = "store"
                    any_added = False
                    for book_data in book_list:
                        # Skip items the model isn't confident are real books
                        try:
                            if float(book_data.get("confidence") or 0) < 0.5:
                                continue
                        except (TypeError, ValueError):
                            continue
                        book_data["source_type"] = source_type
                        book_data.setdefault("book_type", "")
                        book_data.setdefault("source_url", "")
                        if isinstance(book_data.get("genre_tags"), str):
                            raw = book_data["genre_tags"]
                            if "," in raw:
                                book_data["genre_tags"] = [t.strip() for t in raw.split(",") if t.strip()]
                            else:
                                book_data["genre_tags"] = [t.strip() for t in raw.split() if t.strip()]
                        elif not isinstance(book_data.get("genre_tags"), list):
                            book_data["genre_tags"] = []
                        
                        if source_type == "url":
                            book_data["source_url"] = user_input
                        
                        # Check availability via librarian
                        available, matched_title = librarian.check_availability(
                            book_data["title"], book_data.get("author")
                        )
                        book_data["available_in_cloud_library"] = available
                        book_data["cloud_library_match"] = matched_title
                        try:
                            book_data.update(as_fields(check_sdpl(book_data["title"], book_data.get("author"))))
                        except Exception as e:
                            log_scan(user_input=user_input, source_type=source_type,
                                     stage="sdpl", status="error", error=e)
                        
                        # Add to store
                        added = store.add(book_data)
                        if added:
                            any_added = True
                    
                    log_scan(user_input=user_input, source_type=source_type, stage="done",
                             status="ok", books=[b.get("title") for b in book_list])
                    if any_added:
                        st.success("Book(s) added to your want-to-read list!")
                    else:
                        st.info("All scanned books are already in your list.")
                    
                    st.rerun()
                except Exception as e:
                    import traceback
                    error_type = type(e).__name__
                    log_scan(user_input=user_input, source_type=source_type,
                             stage=stage, status="error", error=e)
                    st.error(f"**Scan failed:** {error_type}: {e}")
                    with st.expander("Error details"):
                        st.code(traceback.format_exc(), language="python")
                    with st.expander("Troubleshooting"):
                        st.markdown("""
                        **Try:**
                        - Check if URL is accessible
                        - Verify all API providers are configured
                        - Try a different book URL or text
                        - Check console logs for details
                        """)
        else:
            st.warning("Please enter a URL or text to scan.")
    
    st.divider()
    
    # Search / filter
    st.markdown("### Search")

    # Widgets write straight into session state under their own key; the return
    # value below is read back once, after the sidebar has rendered, so there is
    # no write-back-and-rerun dance to get out of sync.
    st.text_input(
        label="Search",
        placeholder="Search titles and summaries...",
        key="search_query",
        label_visibility="collapsed",
    )

    # Chips for whatever is currently narrowing the feed. Clicking one unselects
    # it; "Clear" drops every tag at once.
    with st.container(key="active_tags"):
        if active_tags:
            st.markdown(
                f"<p class='stats'>Filtering by {len(active_tags)} "
                f"tag{'s' if len(active_tags) > 1 else ''}</p>",
                unsafe_allow_html=True,
            )
            chip_cols = st.columns(len(active_tags))
            for col, tag in zip(chip_cols, active_tags):
                col.button(
                    f"✕ {tag}",
                    key=f"active__{tag_slug(tag)}",
                    type="primary",
                    on_click=toggle_tag,
                    args=(tag,),
                    width="stretch",
                    help=f"Remove the {tag} filter",
                )
            st.button(
                "Clear filters",
                key="clear_filters",
                on_click=clear_filters,
                width="stretch",
            )

    # Every tag in the library, most common first. Clicking one selects it.
    if tag_index:
        with st.expander(f"All tags ({len(tag_index)})"):
            with st.container(key="sidebar_tags"):
                for tag, count in tag_index:
                    is_active = tag in active_tags
                    st.button(
                        f"{tag} · {count}",
                        key=f"sidebar__{tag_slug(tag)}",
                        type="primary" if is_active else "secondary",
                        on_click=toggle_tag,
                        args=(tag,),
                        width="stretch",
                        help=(
                            f"Remove the {tag} filter"
                            if is_active
                            else f"Show the {count} book"
                            f"{'s' if count != 1 else ''} tagged {tag}"
                        ),
                    )

    # Stats
    errs = recent(10, "error")
    if errs:
        with st.expander(f"Recent scan errors ({len(errs)})"):
            for r in errs:
                st.markdown(f"**{r['ts']}** · `{r['stage']}` · {r.get('error_type', '')}")
                st.caption(r["input"][:120])
                st.code(r.get("error", ""), language=None)

# Main feed
st.markdown("### Your Want-to-Read List")

search_query = st.session_state.get("search_query", "")
filtered_books = filter_books(all_books, active_tags, search_query)

# Say what the feed is doing, so the result count never looks arbitrary.
filter_bits = []
if active_tags:
    filter_bits.append("tags: " + ", ".join(sorted(active_tags)))
if search_query.strip():
    filter_bits.append(f'search: "{search_query.strip()}"')
if filter_bits:
    summary = " · ".join(filter_bits)
    st.markdown(f"<p class='stats'>{len(filtered_books)} of {len(all_books)} books · {summary}</p>", unsafe_allow_html=True)
else:
    st.markdown(f"<p class='stats'>{len(all_books)} books</p>", unsafe_allow_html=True)

if not filtered_books:
    if filter_bits:
        st.info(
            f"No books match {summary}. "
            "Click an active tag above to remove it, or use Clear filters."
        )
    else:
        st.info("No books match your filter. Try scanning a book URL or text to add to your list.")
else:
    # Display books in cards
    for book in filtered_books:
        # Determine card class based on availability
        card_class = "book-card"
        if not book["available_in_cloud_library"]:
            card_class += " not-available"
        
        with st.container():
            st.markdown(f'<div class="{card_class}">', unsafe_allow_html=True)
            
            col1, col2 = st.columns([1, 4])
            with col1:
                # Availability badge
                if book["available_in_cloud_library"]:
                    badge_text = f"Available in Cloud Library ✓"
                    if book["cloud_library_match"]:
                        badge_text += f" ({book['cloud_library_match']})"
                    st.markdown(f"<span class='availability-badge'>{badge_text}</span>", unsafe_allow_html=True)
                else:
                    st.markdown("<span class='availability-badge not-available'>Not in Cloud Library</span>", unsafe_allow_html=True)
            
            with col2:
                st.markdown(f"<h4>{book['title']}</h4>", unsafe_allow_html=True)
                is_read = book.get("is_read", False)
                is_loved = book.get("is_loved", False)
                pills = [
                    "<span style='color:#ffaa00;font-family:DM Mono,monospace;font-size:11px'>[ read ]</span>"
                    if is_read else
                    "<span style='color:#606080;font-family:DM Mono,monospace;font-size:11px'>[ unread ]</span>"
                ]
                if is_loved:
                    pills.append("<span style='color:#ff4488;font-family:DM Mono,monospace;font-size:11px'>[ love ]</span>")
                st.markdown(" ".join(pills), unsafe_allow_html=True)
                if book["author"]:
                    st.markdown(f"<p class='author'>by {book['author']}</p>", unsafe_allow_html=True)
                bid_s = book_id(book)
                home = home_branch() or "your branch"
                checked = _ago(book.get("sdpl_checked_at"))
                rec_url = book.get("sdpl_url") or search_page_url(book.get("title", ""), book.get("author"))
                if not book.get("sdpl_checked_at"):
                    sdpl_color, sdpl_line, link_label = "#606080", "SDPL: not checked yet", "Search ↗"
                elif book.get("sdpl_at_home"):
                    sdpl_color, sdpl_line, link_label = "#00ff88", f"★ On shelf at {home}", "Open record ↗"
                    if book.get("sdpl_call_number"):
                        sdpl_line += f" · {book['sdpl_call_number']}"
                elif book.get("sdpl_available"):
                    sdpl_color, sdpl_line, link_label = "#44aaff", book.get("sdpl_summary", ""), f"Request to {home} ↗"
                elif book.get("sdpl_found") and book.get("sdpl_physical"):
                    sdpl_color, sdpl_line, link_label = "#ffaa00", book.get("sdpl_summary", ""), "Place hold ↗"
                elif book.get("sdpl_found"):
                    sdpl_color, sdpl_line, link_label = "#9090b0", book.get("sdpl_summary", ""), "Open record ↗"
                else:
                    sdpl_color, sdpl_line, link_label = "#606080", "Not in SDPL catalog", "Search / suggest ↗"
                c_sdpl, c_ref = st.columns([6, 1])
                with c_sdpl:
                    st.markdown(
                        f"<span style='color:{sdpl_color};font-size:12px'>{_html.escape(sdpl_line)}</span> "
                        f"<a href='{_html.escape(rec_url, quote=True)}' target='_blank' "
                        f"style='color:#44aaff;font-size:12px;text-decoration:none'>{_html.escape(link_label)}</a>"
                        + (f"<span style='color:#404060;font-size:11px'> · checked {checked}</span>" if checked else ""),
                        unsafe_allow_html=True,
                    )
                with c_ref:
                    st.button("↻", key=f"sdpl_refresh_{bid_s}", help="Re-check SDPL availability",
                              on_click=refresh_sdpl, args=(bid_s, book.get("title", ""), book.get("author")))
                tags = book_tags(book)
                if tags:
                    # Element keys must be unique across the whole page, so the
                    # container key is per-book. It keeps the `st-key-card_tags`
                    # prefix, which the CSS above matches on.
                    with st.container(key=f"card_tags__{book_id(book)}"):
                        tag_row = st.columns(len(tags))
                        for col, tag in zip(tag_row, tags):
                            is_active = tag in active_tags
                            col.button(
                                tag,
                                key=f"card__{book_id(book)}__{tag_slug(tag)}",
                                type="primary" if is_active else "secondary",
                                on_click=toggle_tag,
                                args=(tag,),
                                width="stretch",
                                help=(
                                    f"Remove the {tag} filter"
                                    if is_active
                                    else f"Filter by {tag}"
                                ),
                            )
                st.markdown(f"<p class='summary'>{book['summary']}</p>", unsafe_allow_html=True)
                st.markdown(f"<p class='verdict'>{book['verdict']}</p>", unsafe_allow_html=True)
                # Confidence bar
                confidence = book["confidence"]
                st.markdown(f"<div class='confidence-bar'><div class='confidence-fill' style='width: {confidence*100}%;'></div></div>", unsafe_allow_html=True)
                bid = book_id(book)
                c_read, c_love, c_del = st.columns([2, 2, 1])
                with c_read:
                    if st.button("[ read ]" if is_read else "mark read", key=f"read_{bid}"):
                        store.toggle_read(bid, is_read)
                        st.rerun()
                with c_love:
                    if st.button("[ love ]" if is_loved else "love", key=f"love_{bid}"):
                        store.toggle_loved(bid, is_loved)
                        st.rerun()
                with c_del:
                    if st.button("Delete", key=f"delete_{bid}", help="Remove this book"):
                        store.delete(bid)
                        st.rerun()
            
            st.markdown("</div>", unsafe_allow_html=True)
            st.divider()
