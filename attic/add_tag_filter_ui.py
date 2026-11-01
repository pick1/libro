with open('app.py', 'r') as f:
    content = f.read()

# Replace the old search section with a better one
old_search = '''    # Search/filter by genre tag
    st.markdown("### Search by genre tag")
    search_tag = st.text_input(
        label="Genre tag",
        placeholder="e.g., sci-fi, fantasy",
        value=st.session_state.search_tag,
        label_visibility="collapsed",
    )
    if search_tag != st.session_state.search_tag:
        st.session_state.search_tag = search_tag
    if st.button("Clear filter", use_container_width=True):
        st.session_state.search_tag = ""
        st.rerun()'''

new_search = '''    # Search/filter by genre tag
    col1, col2 = st.columns([4, 1])
    with col1:
        st.markdown("### Filter by tag")
    with col2:
        if st.button("✕", help="Clear filter", key="clear_filter_btn"):
            st.session_state.search_tag = ""
            st.rerun()
    
    search_tag = st.text_input(
        label="Genre tag",
        placeholder="e.g., sci-fi, fantasy",
        value=st.session_state.search_tag,
        key="genre_search_input",
        label_visibility="collapsed",
    )
    st.session_state.search_tag = search_tag'''

content = content.replace(old_search, new_search)

with open('app.py', 'w') as f:
    f.write(content)

print("Improved tag filter UI!")
