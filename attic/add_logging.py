with open('app.py', 'r') as f:
    lines = f.readlines()

# Add logging imports at the top after other imports
insert_idx = 0
for i, line in enumerate(lines):
    if 'from libro.store import WantToReadStore' in line:
        insert_idx = i + 1
        break

new_imports = '''import logging
from datetime import datetime

# Set up logging
logging.basicConfig(
    filename='libro_events.log',
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
logger.info("=== Libro session started ===")

'''

lines.insert(insert_idx, new_imports)

# Add logging to tag button clicks
for i, line in enumerate(lines):
    if 'on_click=lambda t=tag:' in line:
        lines[i] = line.replace(
            'on_click=lambda t=tag: (st.session_state.update({"search_tag": t}), )',
            '''on_click=lambda t=tag: (logger.info(f"TAG CLICKED: {t}"), st.session_state.update({"search_tag": t}), logger.info(f"SESSION STATE UPDATED: search_tag={t}"))'''
        )

# Add logging to search input
for i, line in enumerate(lines):
    if 'if search_input != st.session_state.search_tag:' in line:
        lines[i] = line
        lines.insert(i+1, '        logger.info(f"SEARCH INPUT CHANGED: {search_input}")\n')

with open('app.py', 'w') as f:
    f.writelines(lines)

print("Added comprehensive logging!")
