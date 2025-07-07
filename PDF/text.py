import fitz  # PyMuPDF
import re
from typing import Dict


def extract_text_sections(pdf_path: str) -> Dict[str, str]:
    doc = fitz.open(pdf_path)
    full_text = ""
    for page in doc:
        full_text += page.get_text()

    # Normalize and clean
    clean_text = re.sub(r'\n{2,}', '\n', full_text.strip())
    
    # Split into lines to extract title/authors block (usually first few lines)
    lines = clean_text.split('\n')
    title_and_authors = []
    content_start_index = 0

    # Heuristic: first non-empty lines up to about 10 lines or until 'abstract' or intro
    for i, line in enumerate(lines[:20]):
        if re.match(r'(?i)\b(abstract|introduction)\b', line.strip()):
            content_start_index = i
            break
        title_and_authors.append(line.strip())

    if not content_start_index:
        content_start_index = len(title_and_authors)

    # Join everything after title/authors
    remaining_text = '\n'.join(lines[content_start_index:])

    # Identify References start using regex
    references_match = re.search(r'\n(references|bibliography)\s*\n', remaining_text, flags=re.IGNORECASE)

    
    if references_match:
        split_index = references_match.start()
        content = remaining_text[:split_index].strip()
        references = remaining_text[split_index:].strip()
    else:
        content = remaining_text.strip()
        references = ""

    return {
        "title_and_authors": '\n'.join(title_and_authors).strip(),
        "content": content,
        "references": references
    }
if __name__ == "__main__":
    pdf_path = "test.pdf"
    result = extract_text_sections(pdf_path)

    print("== TITLE & AUTHORS ==")
    print(result["title_and_authors"], "\n")

    print("== CONTENT (preview) ==")
    print(result["content"][:500], "...")

    print("== REFERENCES ==")
    print(result["references"], "...")
