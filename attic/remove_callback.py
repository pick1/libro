with open('app.py', 'r') as f:
    content = f.read()

# Remove the callback completely
old = '''    # Handle clear button first (process buttons before inputs in Streamlit)
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

new = '''    # Handle clear button first (process buttons before inputs in Streamlit)
    if st.button("✕ Clear", key='btn_clear_filter', use_container_width=True, help="Clear filter"):
        st.session_state.search_tag = ''
        st.rerun()
    
    # Search input - direct sync (no callback)
    search_input = st.text_input(
        label="Search",
        placeholder="Type or click a tag...",
        value=st.session_state.search_tag,
        key='genre_search_box',
        label_visibility="collapsed",
    )
    
    # Sync input changes to session state
    if search_input != st.session_state.search_tag:
        st.session_state.search_tag = search_input
        st.rerun()'''

content = content.replace(old, new)

with open('app.py', 'w') as f:
    f.write(content)

print("Removed callback!")
