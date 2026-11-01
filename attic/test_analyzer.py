from libro.analyzer import extract_book

# Test with sample text
test_text = "I just finished reading Project Hail Mary by Andy Weir. It's a great sci-fi novel."
result = extract_book(test_text, "text")

print(f"Result type: {type(result)}")
print(f"Result: {result}")
print(f"Result repr: {repr(result)}")

if isinstance(result, list) and result:
    print(f"First book: {result[0]}")
    print(f"Title: {result[0].get('title')}")
