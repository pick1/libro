with open('app.py', 'r') as f:
    content = f.read()

# Replace the entire search section with a cleaner pattern
old_search = '''    # Search/filter by genre tag
    st.markdown("### Search by genre tag")
    
    # Initialize if not exists
    if 'search_tag' not in st.session_state:
        st.session_state.search_tag = ''
    
    # Two column layout: search input + clear button
    col_search, col_clear = st.columns([5, 1])
    
    with col_search:
        new_search = st.text_input(
            label="Search",
            placeholder="Type or click a tag...",
            value=st.session_state.search_tag,
            key='genre_search_box',
            label_visibility="collapsed",
        )
        if new_search != st.session_state.search_tag:
            st.session_state.search_tag = new_search
            st.rerun()
    
    with col_clear:
        if st.button("✕ Clear", key='btn_clear_filter', use_container_width=True, help="Clear filter"):
            st.session_state.search_tag = ''
            st.rerun()'''

new_search = '''    # Search/filter by genre tag
    st.markdown("### Search by genre tag")
    
    # Initialize if not exists
    if 'search_tag' not in st.session_state:
        st.session_state.search_tag = ''
    
    # Handle clear button first (process buttons before inputs in Streamlit)
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

content = content.replace(old_search, new_search)

with open('app.py', 'w') as f:
    f.write(content)

print("Simplified filter logic - buttons before inputs!")
