with open('app.py', 'r') as f:
    content = f.read()

old = '''                        if tag_row[idx].button(tag, key=f"tag_{idx}_{book['title']}", use_container_width=True):
                            st.toast(f"Clicked: {tag}")
                            st.session_state.search_tag = tag
                            st.rerun()'''

new = '''                        if tag_row[idx].button(tag, key=f"tag_{idx}_{book['title']}", use_container_width=True):
                            st.toast(f"Clicked: {tag}")
                            print(f"DEBUG: Before rerun - session_tag={st.session_state.search_tag}, setting to {tag}", flush=True)
                            st.session_state.search_tag = tag
                            print(f"DEBUG: After set - session_tag={st.session_state.search_tag}", flush=True)
                            st.rerun()'''

content = content.replace(old, new)

with open('app.py', 'w') as f:
    f.write(content)

print("Added debug before/after rerun!")
