with open('app.py', 'r') as f:
    content = f.read()

old = '''# Update search_tag from session state one more time to be safe
current_filter = st.session_state.get('search_tag', '')

# Filter books by search tag if provided
filtered_books = all_books
if current_filter:'''

new = '''# Update search_tag from session state one more time to be safe
current_filter = st.session_state.get('search_tag', '')
st.write(f"DEBUG: current_filter = '{current_filter}'")
st.write(f"DEBUG: session state = {st.session_state.search_tag}")

# Filter books by search tag if provided
filtered_books = all_books
if current_filter:'''

content = content.replace(old, new)

with open('app.py', 'w') as f:
    f.write(content)

print("Added debug output!")
