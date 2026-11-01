with open('libro/analyzer.py', 'r') as f:
    lines = f.readlines()

output = []
for i, line in enumerate(lines):
    output.append(line)
    # After the docstring of _parse_json_result, add debug
    if 'def _parse_json_result(content: str) -> list[dict]:' in line:
        # Look ahead for the docstring end
        j = i + 1
        while j < len(lines) and '"""' not in lines[j]:
            output.append(lines[j])
            j += 1
        if j < len(lines):
            output.append(lines[j])  # closing """
            # Now add debug after docstring
            output.append('    import sys\n')
            output.append('    print(f"DEBUG _parse_json: input={repr(content[:300])}", file=sys.stderr)\n')
            # Skip the lines we already added
            i = j

# Actually simpler - just insert after first return statement check
with open('libro/analyzer.py', 'r') as f:
    content = f.read()

# Find the line with "if not content or not content.strip():" and add debug before it
lines = content.split('\n')
new_lines = []
for i, line in enumerate(lines):
    if 'if not content or not content.strip():' in line:
        new_lines.append('    import sys')
        new_lines.append('    print(f"DEBUG _parse_json: input={repr(content[:300])}", file=sys.stderr)')
    new_lines.append(line)

with open('libro/analyzer.py', 'w') as f:
    f.write('\n'.join(new_lines))

print("Fixed!")
