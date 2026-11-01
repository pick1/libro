with open('app.py', 'r') as f:
    content = f.read()

# Simplify button keys and use a different approach
old = '''                if book["genre_tags"]:
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

new = '''                if book["genre_tags"]:
                    st.write("**Tags:**")
                    # Display tags as HTML
                    tags_html = " ".join([f'<span style="display:inline-block;padding:4px 8px;margin-right:6px;background:#2A2A35;border-radius:4px;border:1px solid #3A3A45;font-size:0.85rem">{tag}</span>' for tag in book["genre_tags"]])
                    st.markdown(tags_html, unsafe_allow_html=True)
                    # Use selectbox instead of buttons (more reliable in Streamlit)
                    tag_choice = st.selectbox(
                        "Filter:",
                        ["—"] + book["genre_tags"],
                        key=f"tag_select_{id(book)}",
                        label_visibility="collapsed"
                    )
                    if tag_choice != "—":
                        st.session_state.search_tag = tag_choice
                        st.rerun()'''

content = content.replace(old, new)

with open('app.py', 'w') as f:
    f.write(content)

print("Switched to selectbox for tag filtering!")
