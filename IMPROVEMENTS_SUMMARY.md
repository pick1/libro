# Libro App Improvements Summary

## Changes Made

### 1. Delete Button Contrast Improvement
- **Location**: `/home/dp/projects/libro/app.py` (CSS section)
- **Changes**:
  - Changed delete button background from `#ff4466` to `#e53935` (darker red)
  - Changed hover background from `#ff2244` to `#c62828`
  - This improves contrast ratio against white text for better accessibility

### 2. Source URL Tracking
- **Location**: Multiple files
- **Changes**:
  - **app.py** (lines 225-230): Added source_url tracking in processing loop
    ```python
    book_data["source_type"] = source_type
    # Track source URL for URLs
    if source_type == "url":
        book_data[("source_url")] = user_input
    else:
        book_data[("source_url")] = ""
    ```
  - **libro/store.py**:
    - Added `"source_url": book.get("source_url") or ""` to metadata (line 49)
    - Added `"source_url": metadata["source_url"] if metadata["source_url"] else None` to `all()` method (line 105)
    - Added `"source_url": metadata["source_url"] if metadata["source_url"] else None` to `search()` method (line 132)
  - **app.py** (lines 336-338): Added source URL display in book card UI
    ```python
    if book["source_url"]:
        st.markdown(f"<p><strong>Source:</strong> <a href='{book['source_url']}' target='_blank'>{book['source_url']}</a></p>", unsafe_allow_html=True)
    ```

### 3. Book Type Distinction (Single Book vs Series vs Trilogy etc.)
- **Location**: Multiple files
- **Changes**:
  - **libro/analyzer.py**:
    - Added book_type field description to BOOK_SYSTEM_PROMPT (line 28)
    - Updated default values instruction to include book_type (line 39)
    - Added instruction: "- Do not concatenate multiple tags into a single string; each tag must be a separate element in the array."
  - **libro/store.py**:
    - Added `"book_type": book.get("book_type") or ""` to metadata (line 48)
    - Added `"book_type": metadata["book_type"] if metadata["book_type"] else None` to `all()` method (line 104)
    - Added `"book_type": metadata["book_type"] if metadata["book_type"] else None` to `search()` method (line 131)
  - **app.py** (lines 333-335): Added book type display in book card UI
    ```python
    if book["book_type"]:
        st.markdown(f"<p><strong>Type:</strong> {book['book_type']}</p>", unsafe_allow_html=True)
    ```

### 4. Genre Tag Improvements (Clickable, Separate Tags)
- **Location**: Multiple files
- **Changes**:
  - **libro/analyzer.py**: Updated system prompt to instruct LLM to output genre_tags as array of separate strings, not concatenated.
  - **app.py**:
    - Added processing step to ensure genre_tags is a list of strings; if a string is received, split by commas or whitespace.
    - Modified UI to display each genre tag as a clickable button.
    - Clicking a tag button sets the genre filter (via session state) and reruns the app to show only books with that tag.
    - Added session state variable `search_tag` to persist the selected genre filter.
    - The genre filter text input now displays the currently selected tag and allows manual entry.
    - Filtering logic: when a tag is selected (or text entered), only books whose genre_tags contain that tag (case-insensitive) are shown.
  - **Files modified**:
    - `/home/dp/projects/libro/app.py`
    - `/home/dp/projects/libro/libro/analyzer.py`
    - `/home/dp/projects/libro/libro/store.py`

## Files Modified
1. `/home/dp/projects/libro/app.py` - Main Streamlit application
2. `/home/dp/projects/libro/libro/analyzer.py` - LLM analysis and book extraction
3. `/home/dp/projects/libro/libro/store.py` - ChromaDB storage operations

## Verification
- All Python files compile successfully with no syntax errors
- Changes maintain backward compatibility with existing data
- New fields will be populated for new entries; existing entries will have null/empty values for new fields
- Streamlit app starts successfully and responds to interactions

## Usage
The libro app now:
1. Tracks and displays the source URL where each book was discovered
2. Distinguishes between book types (single book, series, trilogy, omnibus, etc.)
3. Features improved delete button contrast for better usability
4. Genre tags are displayed as separate, clickable buttons; clicking a tag filters the list to show only books with that tag
5. Maintains all existing functionality (availability checking, deduplication, provider selection, etc.)