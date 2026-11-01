with open('app.py', 'r') as f:
    content = f.read()

# Find the genre tags display section and replace it with clickable buttons
old_tags = '''                if book["genre_tags"]:
                    tags_html = " ".join([f"<span class='genre-tag'>{tag}</span>" for tag in book["genre_tags"]])
                    st.markdown(f"<div class='genre-tags'>{tags_html}</div>", unsafe_allow_html=True)'''

new_tags = '''                if book["genre_tags"]:
                    st.write("**Tags:**")
                    tag_cols = st.columns(len(book["genre_tags"]))
                    for i, tag in enumerate(book["genre_tags"]):
                        with tag_cols[i]:
                            if st.button(tag, key=f"tag_{tag}_{book['title']}", use_container_width=True):
                                st.session_state.search_tag = tag
                                st.rerun()'''

content = content.replace(old_tags, new_tags)

with open('app.py', 'w') as f:
    f.write(content)

print("Tags are now clickable!")
