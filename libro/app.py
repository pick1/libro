import sys
import hashlib
import logging
import streamlit as st
from libro.auth import is_password_set, verify_password, set_password
from libro.extractor import detect_source_type, fetch_url, clean_text
from libro.analyzer import extract_book, set_notification_callback
from libro.librarian import LibrarianIndex
from libro.store import WantToReadStore

# ─── LOGGING SETUP ─────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [LIBRO:%(levelname)s] %(name)s — %(message)s",
    datefmt="%H:%M:%S",
    handlers=[
        logging.FileHandler("/tmp/libro.log"),
        logging.StreamHandler(sys.stdout),
    ]
)
log = logging.getLogger("libro.app")
log.info("=" * 80)
log.info("Libro app started")
log.info("=" * 80)

# Initialize stores and indices
def get_store():
    return WantToReadStore()

def get_librarian():
    return LibrarianIndex()

store = get_store()
librarian = get_librarian()

# ─── AUTH GATE ────────────────────────────────────────────────────────────────
if not st.session_state.get("authenticated"):
    st.markdown(
        '<div class="signal-header" style="text-align:center;margin-top:40px">LIBRO</div>',
        unsafe_allow_html=True,
    )
    if not is_password_set():
        st.markdown('<div style="max-width:360px;margin:40px auto">', unsafe_allow_html=True)
        st.markdown("**Set a password** to secure this dashboard.")
        pw = st.text_input("Password", type="password", key="setup_pw")
        pw2 = st.text_input("Confirm", type="password", key="setup_pw2")
        if st.button("Set Password", type="primary", use_container_width=True):
            if pw and pw == pw2 and len(pw) >= 4:
                set_password(pw)
                st.session_state["authenticated"] = True
                st.rerun()
            else:
                st.error("Password must be 4+ chars and match.")
        st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.markdown('<div style="max-width:360px;margin:40px auto">', unsafe_allow_html=True)
        pw = st.text_input("Password", type="password", key="login_pw")
        if st.button("Unlock", type="primary", use_container_width=True):
            if verify_password(pw):
                st.session_state["authenticated"] = True
                st.rerun()
            else:
                st.error("Incorrect password.")
        st.markdown("</div>", unsafe_allow_html=True)
    st.stop()



# Set up notification callback for analyzer
def notify_callback(msg: str, icon: str = "ℹ️"):
    log.debug(f"Toast notification: {msg}")
    st.toast(msg, icon=icon)

set_notification_callback(notify_callback)

# Page config
st.set_page_config(
    page_title="Libro",
    page_icon="/home/dp/projects/libro/static/favicon.svg",
    layout="centered",
    initial_sidebar_state="expanded",
)

# Initialize session state for genre filter
if 'search_tag' not in st.session_state:
    st.session_state.search_tag = ''

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
    .book-card .genre-tag {
        display: inline-block;
        background-color: #2A2A35;
        color: #FFFFFF;
        padding: 0.25rem 0.5rem;
        border-radius: 4px;
        font-size: 0.875rem;
        margin-right: 0.5rem;
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
        background-color: #e53935;
        color: #FFFFFF;
        border: none;
        padding: 0.25rem 0.5rem;
        border-radius: 4px;
        cursor: pointer;
    }
    .book-card .delete-button:hover {
        background-color: #c62828;
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

# Sidebar
with st.sidebar:
    st.markdown("<h1 style='text-align: center; color: #00ff88; font-family: Syne;'>Libro</h1>", unsafe_allow_html=True)
    
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
            log.info(f"SCAN button clicked. Input: {user_input[:100]}...")
            with st.spinner("Scanning..."):
                try:
                    # Detect source type
                    log.debug("Detecting source type...")
                    source_type = detect_source_type(user_input)
                    log.info(f"Source type detected: {source_type}")
                    
                    # Fetch content if URL
                    raw_content = None
                    if source_type == "url":
                        log.info(f"Fetching URL: {user_input}")
                        raw_content = fetch_url(user_input)
                        log.info(f"URL fetched successfully: {len(raw_content)} chars")
                    else:
                        log.info("Using raw text input")
                        raw_content = user_input
                    
                    # Clean text
                    log.debug("Cleaning text...")
                    cleaned_content = clean_text(raw_content)
                    log.info(f"Text cleaned: {len(cleaned_content)} chars")
                    
                    # Extract book metadata (returns a list of books)
                    log.debug(f"Extracting book metadata using provider: {provider_key}")
                    book_list = extract_book(cleaned_content, source_type, provider_key)
                    log.info(f"Extracted {len(book_list)} book(s)")
                    
                    # Process each book
                    any_added = False
                    for i, book_data in enumerate(book_list, 1):
                        log.debug(f"Processing book {i}/{len(book_list)}: {book_data.get('title', 'Unknown')}")
                        
                        book_data["source_type"] = source_type
                        book_data.setdefault("book_type", "")
                        book_data.setdefault("source_url", "")
                        
                        # Ensure genre_tags is a list of strings
                        if isinstance(book_data.get("genre_tags"), str):
                            raw = book_data["genre_tags"]
                            if "," in raw:
                                book_data["genre_tags"] = [t.strip() for t in raw.split(",") if t.strip()]
                            else:
                                book_data["genre_tags"] = [t.strip() for t in raw.split() if t.strip()]
                        elif not isinstance(book_data.get("genre_tags"), list):
                            book_data["genre_tags"] = []
                        
                        # Track source URL for URLs
                        if source_type == "url":
                            book_data["source_url"] = user_input
                        
                        # Check availability via librarian
                        log.debug(f"Checking availability for: {book_data.get('title')} by {book_data.get('author')}")
                        available, matched_title = librarian.check_availability(
                            book_data["title"], book_data.get("author")
                        )
                        book_data["available_in_cloud_library"] = available
                        book_data["cloud_library_match"] = matched_title
                        log.debug(f"Availability: {available}, Match: {matched_title}")
                        
                        # Add to store (deduplication handled inside)
                        log.debug(f"Adding to store...")
                        added = store.add(book_data)
                        if added:
                            log.info(f"✓ Book added: {book_data.get('title')}")
                            any_added = True
                        else:
                            log.info(f"✗ Book already in list (deduplicated): {book_data.get('title')}")
                    
                    if any_added:
                        log.info("Scan completed: New books added")
                        st.success("Book(s) added to your want-to-read list!")
                    else:
                        log.info("Scan completed: All books were duplicates")
                        st.info("All scanned books are already in your list (deduplicated).")
                    
                    # Rerun to update the feed
                    st.rerun()
                except Exception as e:
                    log.error(f"Error during scan: {type(e).__name__}: {e}", exc_info=True)
                    st.error(f"Error: {str(e)}")
        else:
            log.warning("SCAN clicked but no input provided")
            st.warning("Please enter a URL or text to scan.")
    
    st.divider()
    
    # Search/filter by genre tag
    st.markdown("### Search by genre tag")
    search_tag = st.text_input(
        label="Genre tag",
        placeholder="e.g., sci-fi, fantasy",
        value=st.session_state.search_tag,
        label_visibility="collapsed",
    )
    if search_tag != st.session_state.search_tag:
        st.session_state.search_tag = search_tag
        log.debug(f"Genre filter changed: {search_tag}")
    
    # Stats
    all_books = store.all()
    total_saved = len(all_books)
    available_count = sum(1 for b in all_books if b["available_in_cloud_library"])
    st.markdown(f"<div class='stats'>Total saved: {total_saved}<br>Available in Cloud Library: {available_count}</div>", unsafe_allow_html=True)

# Main feed
st.markdown("### Your Want-to-Read List")

filtered_books = all_books
if search_tag:
    filtered_books = [
        b for b in all_books
        if any(search_tag.lower() in tag.lower() for tag in (b.get("genre_tags") or []))
    ]

if not filtered_books:
    st.info("No books match your filter. Try scanning a book URL or text to add to your list.")
else:
    for book in filtered_books:
        available = book.get("available_in_cloud_library", False)
        status = book.get('reading_status', 'want_to_read')
        status_colors = {'want_to_read': '#4488ff', 'already_read': '#ffaa00', 'loved_it': '#ff4488'}
        border_color = '#00ff88' if available else status_colors.get(status, '#4488ff')
        title = book.get("title", "Unknown")
        author = book.get("author") or ""
        summary = book.get("summary") or ""
        verdict = book.get("verdict") or ""
        genre_tags = book.get("genre_tags") or []
        confidence = book.get("confidence") or 0.0
        source_url = book.get("source_url") or ""
        match = book.get("cloud_library_match") or ""

        book_id = hashlib.md5(f"{title}{author}".encode()).hexdigest()
        is_read = book.get("is_read", False)
        is_loved = book.get("is_loved", False)

        # Status glyphs for card corner
        glyphs = []
        if is_read:
            glyphs.append('<span style="font-size:11px;color:#ffaa00;font-family:DM Mono,monospace;text-shadow:0 0 8px #ffaa00aa">[ read ]</span>')
        if is_loved:
            glyphs.append('<span style="font-size:11px;color:#ff4488;font-family:DM Mono,monospace;text-shadow:0 0 8px #ff4488aa">[ love ]</span>')
        status_glyph = ' '.join(glyphs)

        tag_html = "".join(
            f'<span style="display:inline-block;padding:2px 10px;border-radius:20px;font-size:10px;'
            f'letter-spacing:0.1em;text-transform:uppercase;border:1px solid #353550;'
            f'color:#7070a0;margin-right:4px;margin-bottom:4px">{t}</span>'
            for t in genre_tags
        )
        avail_html = (
            f'<span style="color:#00ff88;font-size:11px">✓ Cloud Library{" — " + match if match else ""}</span>'
            if available else
            '<span style="color:#404060;font-size:11px">not in cloud library</span>'
        )
        conf_pct = int(confidence * 100)
        source_html = (
            f'<a href="{source_url}" target="_blank" style="color:#44aaff;font-size:11px;text-decoration:none">source →</a>'
            if source_url else ""
        )

        st.markdown(f"""
<div style="background:#111118;border:1px solid #252535;border-left:3px solid #4488ff;
border-radius:12px;padding:18px 20px;margin-bottom:6px">
  <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:4px">
    <div style="font-family:Syne,sans-serif;font-size:17px;font-weight:700">{title}</div>
    <div>{status_glyph}</div>
  </div>
  <div style="font-size:12px;color:#9090b0;margin-bottom:8px">by {author}</div>
  <div style="margin-bottom:8px">{avail_html}</div>
  <div style="margin-bottom:8px">{tag_html}</div>
  <div style="font-size:12px;color:#9090b0;line-height:1.6;margin-bottom:10px">{summary}</div>
  <div style="font-style:italic;font-size:13px;color:#e8e8f0;margin-bottom:10px">{verdict}</div>
  <div style="display:flex;justify-content:space-between;align-items:center;border-top:1px solid #252535;padding-top:8px">
    <span>{source_html}</span>
    <span style="font-size:11px;color:#404060">confidence {conf_pct}%
      <span style="display:inline-block;width:60px;height:4px;background:#252535;border-radius:2px;vertical-align:middle;margin-left:6px">
        <span style="display:block;width:{conf_pct}%;height:100%;background:#4488ff;border-radius:2px"></span>
      </span>
    </span>
  </div>
</div>
""", unsafe_allow_html=True)

        col_read, col_love, col_drop = st.columns([3, 3, 1])
        with col_read:
            read_label = "[ read ]" if is_read else "read"
            if st.button(read_label, key=f"read_{book_id}"):
                log.debug(f"Toggling read status for: {title}")
                store.toggle_read(book_id, is_read)
                st.rerun()
        with col_love:
            love_label = "[ love ]" if is_loved else "love"
            if st.button(love_label, key=f"loved_{book_id}"):
                log.debug(f"Toggling loved status for: {title}")
                store.toggle_loved(book_id, is_loved)
                st.rerun()
        with col_drop:
            if st.button("drop", key=f"delete_{book_id}", help=f"Remove {title}"):
                log.info(f"Deleting book: {title}")
                store.delete(book_id)
                st.rerun()
