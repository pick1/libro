with open('app.py', 'r') as f:
    lines = f.readlines()

output = []
for i, line in enumerate(lines):
    output.append(line)
    if 'book_data = extract_book(cleaned_content, source_type)' in line:
        indent = len(line) - len(line.lstrip())
        sp = ' ' * indent
        output.append(f"{sp}st.write(f'DEBUG: extract_book returned {{repr(book_data)}}')\n")

with open('app.py', 'w') as f:
    f.writelines(output)
    
print("Debug added!")
