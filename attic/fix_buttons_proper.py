with open('app.py', 'r') as f:
    content = f.read()

# Put buttons OUTSIDE the columns context, in a simple horizontal layout
old = '''                if book["genre_tags"]:
                    st.write("**Tags:**")
                    # Display tags as HTML
                    tags_html = " ".join([f'<span style="display:inline-block;padding:4px 8px;margin-right:6px;background:#2A2A35;border-radius:4px;border:1px solid #3A3A45;font-size:0.85rem">{tag}</span>' for tag in book["genre_tags"]])
                    st.markdown(tags_html, unsafe_allow_html=True)'''

new = '''                if book["genre_tags"]:
                    st.write("**Tags:**")
                    # Display tags as HTML
                    tags_html = " ".join([f'<span style="display:inline-block;padding:4px 8px;margin-right:6px;background:#2A2A35;border-radius:4px;border:1px solid #3A3A45;font-size:0.85rem">{tag}</span>' for tag in book["genre_tags"]])
                    st.markdown(tags_html, unsafe_allow_html=True)
                    
                    # Buttons in a single row - use simple columns
                    btn_cols = st.columns(len(book["genre_tags"]))
                    for idx, tag in enumerate(book["genre_tags"]):
                        btn_cols[idx].button(tag, key=f"tag_click_{book['title']}_{tag}", use_container_width=True, 
                                            on_click=lambda t=tag: (st.session_state.update({"search_tag": t}), ))'''

content = content.replace(old, new)

with open('app.py', 'w') as f:
    f.write(content)

print("Fixed buttons with callback!")
