with open('app.py', 'r') as f:
    content = f.read()

# Add session state init after imports
old_start = '''# Initialize stores and indices
@st.cache_resource
def get_store():'''

new_start = '''# Initialize session state
if 'search_tag' not in st.session_state:
    st.session_state.search_tag = ''

# Initialize stores and indices
@st.cache_resource
def get_store():'''

content = content.replace(old_start, new_start)

with open('app.py', 'w') as f:
    f.write(content)

print("Added session state initialization!")
