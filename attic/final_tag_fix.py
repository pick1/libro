with open('app.py', 'r') as f:
    content = f.read()

# Remove columns, use plain HTML for display + simple buttons for clicks
old = '''                if book["genre_tags"]:
                    st.write("**Tags:**")
                    tag_cols = st.columns(len(book["genre_tags"]))
                    for i, tag in enumerate(book["genre_tags"]):
                        with tag_cols[i]:
                            if st.button(tag, key=f"tag_{tag}_{book['title']}", use_container_width=True):
                                st.session_state.search_tag = tag
                                st.rerun()'''

new = '''                if book["genre_tags"]:
                    st.write("**Tags:**")
                    # Display tags as HTML (no clicks here, just display)
                    tags_html = " ".join([f'<span style="display:inline-block;padding:4px 8px;margin-right:6px;background:#2A2A35;border-radius:4px;border:1px solid #3A3A45;font-size:0.85rem">{tag}</span>' for tag in book["genre_tags"]])
                    st.markdown(tags_html, unsafe_allow_html=True)
                    # Clickable buttons below tags (no columns)
                    st.write("Filter by:")
                    for tag in book["genre_tags"]:
                        if st.button(f"→ {tag}", key=f"filter_{book['title']}_{tag}"):
                            st.session_state.search_tag = tag
                            st.rerun()'''

content = content.replace(old, new)

with open('app.py', 'w') as f:
    f.write(content)

print("Fixed tag buttons - removed columns!")
