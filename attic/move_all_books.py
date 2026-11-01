with open('app.py', 'r') as f:
    lines = f.readlines()

# Find and remove all_books from sidebar
output = []
skip_next_2 = False
for i, line in enumerate(lines):
    if 'all_books = store.all()' in line and i > 300 and i < 320:
        skip_next_2 = True
        continue
    elif skip_next_2 and ('total_saved' in line or 'available_count' in line or 'st.markdown' in line and 'stats' in line):
        continue
    elif skip_next_2 and 'st.markdown(f"<div class' in line and 'stats' in line:
        skip_next_2 = False
        continue
    output.append(line)

# Add all_books after the sidebar ends (after "# Main feed")
final_output = []
for i, line in enumerate(output):
    final_output.append(line)
    if '# Main feed' in line:
        final_output.append('all_books = store.all()\n')

with open('app.py', 'w') as f:
    f.writelines(final_output)

print("Moved all_books outside sidebar!")
