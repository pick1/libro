with open('app.py', 'r') as f:
    content = f.read()

# Make sure search_tag is captured BEFORE filtering
old_filter = '''# Main feed
st.markdown("### Your Want-to-Read List")

# Filter books by search tag if provided
filtered_books = all_books
if search_tag:'''

new_filter = '''# Main feed
st.markdown("### Your Want-to-Read List")

# Update search_tag from session state one more time to be safe
current_filter = st.session_state.get('search_tag', '')

# Filter books by search tag if provided
filtered_books = all_books
if current_filter:'''

content = content.replace(old_filter, new_filter)

# Also update the filter logic to use current_filter
content = content.replace(
    '''if current_filter:
    filtered_books = [
        b for b in all_books
        if any(search_tag.lower() in tag.lower() for tag in b["genre_tags"])
    ]''',
    '''if current_filter:
    filtered_books = [
        b for b in all_books
        if any(current_filter.lower() in tag.lower() for tag in b.get("genre_tags", []))
    ]'''
)

with open('app.py', 'w') as f:
    f.write(content)

print("Fixed filter logic!")
