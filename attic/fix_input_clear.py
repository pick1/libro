with open('app.py', 'r') as f:
    content = f.read()

# Replace the search section with callback-based sync
old_input = '''    # Handle clear button first (process buttons before inputs in Streamlit)
    if st.button("✕ Clear", key='btn_clear_filter', use_container_width=True, help="Clear filter"):
        st.session_state.search_tag = ''
        st.rerun()
    
    # Search input - always sync to session state
    new_search = st.text_input(
        label="Search",
        placeholder="Type or click a tag...",
        value=st.session_state.search_tag,
        key='genre_search_box',
        label_visibility="collapsed",
    )
    
    # Update session state if text changed
    if new_search != st.session_state.search_tag:
        st.session_state.search_tag = new_search
        st.rerun()'''

new_input = '''    # Handle clear button first (process buttons before inputs in Streamlit)
    if st.button("✕ Clear", key='btn_clear_filter', use_container_width=True, help="Clear filter"):
        st.session_state.search_tag = ''
    
    # Callback to sync input -> session state
    def update_search():
        st.session_state.search_tag = st.session_state.genre_search_box
    
    # Search input with callback
    st.text_input(
        label="Search",
        placeholder="Type or click a tag...",
        value=st.session_state.search_tag,
        key='genre_search_box',
        on_change=update_search,
        label_visibility="collapsed",
    )'''

content = content.replace(old_input, new_input)

with open('app.py', 'w') as f:
    f.write(content)

print("Fixed with callback!")
