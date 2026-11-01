with open('app.py', 'r') as f:
    content = f.read()

# Add a clear filter button after the search box
old_search = '''    # Search/filter by genre tag
    st.markdown("### Search by genre tag")
    search_tag = st.text_input(
        label="Genre tag",
        placeholder="e.g., sci-fi, fantasy",
        label_visibility="collapsed",
    )'''

new_search = '''    # Search/filter by genre tag
    st.markdown("### Search by genre tag")
    search_tag = st.text_input(
        label="Genre tag",
        placeholder="e.g., sci-fi, fantasy",
        label_visibility="collapsed",
    )
    if st.button("Clear filter", use_container_width=True):
        st.session_state.search_tag = ""
        st.rerun()'''

content = content.replace(old_search, new_search)

with open('app.py', 'w') as f:
    f.write(content)

print("Added clear filter button!")
