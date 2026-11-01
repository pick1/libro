with open('app.py', 'r') as f:
    lines = f.readlines()

output = []
i = 0
while i < len(lines):
    if '# Search/filter by genre tag' in lines[i]:
        # Found it, replace the whole section
        output.append(lines[i])  # "# Search/filter by genre tag"
        i += 1
        
        # Skip old lines until we hit the stats section
        while i < len(lines) and '# Stats' not in lines[i]:
            i += 1
        
        # Insert new code
        new_code = '''    st.markdown("### Search by genre tag")
    
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
            st.rerun()
    
'''
        output.append(new_code)
    else:
        output.append(lines[i])
        i += 1

with open('app.py', 'w') as f:
    f.writelines(output)

print("Fixed clear filter!")
