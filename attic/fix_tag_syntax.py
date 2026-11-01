with open('app.py', 'r') as f:
    content = f.read()

# Remove the broken HTML approach, just use simple buttons without columns
old_tags = '''                if book["genre_tags"]:
                    # Create clickable tag HTML
                    tag_html = '<div style="margin: 0.5rem 0;">'
                    for tag in book["genre_tags"]:
                        tag_html += f'<a href="#" onclick="window.parent.postMessage({{type: \'streamlit:setComponentValue\', value: \'{tag}\'}}, \'*\'); return false;" style="display:inline-block;padding:4px 12px;margin-right:8px;background:#2A2A35;color:#fff;border-radius:4px;text-decoration:none;cursor:pointer;font-size:0.85rem;border:1px solid #3A3A45;transition:all 0.2s">{tag}</a>'
                    tag_html += '</div>'
                    st.markdown(tag_html, unsafe_allow_html=True)
                    
                    # Check if any tag was clicked (fallback: use a selectbox)
                    col_tag1, col_tag2 = st.columns([3, 1])
                    with col_tag1:
                        pass
                    with col_tag2:
                        for tag in book["genre_tags"]:
                            if st.button(f"🔍 {tag}", key=f"tag_btn_{tag}_{book['title']}", use_container_width=True):
                                st.session_state.search_tag = tag
                                st.rerun()'''

new_tags = '''                if book["genre_tags"]:
                    st.write("**Tags:**")
                    # Simple tag buttons without columns
                    for tag in book["genre_tags"]:
                        if st.button(tag, key=f"tag_{tag}_{book['title']}"):
                            st.session_state.search_tag = tag
                            st.rerun()'''

content = content.replace(old_tags, new_tags)

with open('app.py', 'w') as f:
    f.write(content)

print("Fixed syntax!")
