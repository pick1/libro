with open('app.py', 'r') as f:
    content = f.read()

# Find and replace the search_tag section
old = '''    # Search/filter by genre tag
    st.markdown("### Search by genre tag")
    search_tag = st.text_input(
        label="Genre tag",
        placeholder="e.g., sci-fi, fantasy",
        label_visibility="collapsed",
    )
    if st.button("Clear filter", use_container_width=True):
        st.session_state.search_tag = ""
        st.rerun()'''

new = '''    # Search/filter by genre tag
    st.markdown("### Search by genre tag")
    col_search, col_clear = st.columns([4, 1])
    with col_search:
        search_tag = st.text_input(
            label="Genre tag",
            placeholder="e.g., sci-fi, fantasy",
            value=st.session_state.get('search_tag', ''),
            key='genre_input',
            label_visibility="collapsed",
        )
        # Sync back to session state
        if search_tag != st.session_state.get('search_tag', ''):
            st.session_state.search_tag = search_tag
            st.rerun()
    with col_clear:
        if st.button("✕", key='clear_filter_btn', help="Clear filter"):
            st.session_state.search_tag = ""
            st.rerun()'''

content = content.replace(old, new)

with open('app.py', 'w') as f:
    f.write(content)

print("Synced search_tag to session state!")
