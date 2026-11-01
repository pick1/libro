with open('app.py', 'r') as f:
    content = f.read()

# Add debug output to tag button
old_tag = '''                        with tag_cols[i]:
                            if st.button(tag, key=f"tag_{tag}_{book['title']}", use_container_width=True):
                                st.session_state.search_tag = tag
                                st.rerun()'''

new_tag = '''                        with tag_cols[i]:
                            if st.button(tag, key=f"tag_{tag}_{book['title']}", use_container_width=True):
                                st.write(f"DEBUG: Tag clicked - {tag}")
                                st.session_state.search_tag = tag
                                st.rerun()'''

content = content.replace(old_tag, new_tag)

with open('app.py', 'w') as f:
    f.write(content)

print("Added debug output!")
