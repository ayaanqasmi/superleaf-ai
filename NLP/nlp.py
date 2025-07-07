import re
from typing import List, Dict
import spacy
from keybert import KeyBERT

# Load NLP models
spacy_model = spacy.load("en_core_web_sm")  # Swap with en_core_sci_sm for scientific texts
kw_model = KeyBERT()

# ========== 1. Extract Title ==========
def extract_title(lines: List[str]) -> str:
    candidates = [l for l in lines[:5] if '@' not in l and len(l.strip()) > 5]
    return max(candidates, key=len).strip() if candidates else ""

# ========== 2. Extract Authors ==========
def extract_authors(text: str) -> List[str]:
    doc = spacy_model(text)
    return list({ent.text.strip() for ent in doc.ents if ent.label_ == "PERSON"})

# ========== 3. Extract Reference Metadata ==========
def extract_reference_title(ref_text: str) -> str:
    quoted = re.findall(r'“([^”]+)”|\"([^\"]+)\"', ref_text)
    if quoted:
        return quoted[0][0] or quoted[0][1]
    parts = re.split(r'\.|\“|\”|\"', ref_text)
    return parts[1].strip() if len(parts) > 2 else ""

def extract_venue(ref_text: str) -> str:
    venue_keywords = ["IEEE", "ACM", "Springer", "Nature", "Science", "Elsevier", "arXiv", "Journal", "Proceedings"]
    for word in venue_keywords:
        if word.lower() in ref_text.lower():
            return word
    return ""

def extract_year(ref_text: str) -> str:
    matches = re.findall(r"\b(19[0-9]{2}|20[0-2][0-9]|2025)\b", ref_text)
    return matches[-1] if matches else ""

def parse_references(ref_block: str) -> List[Dict]:
    lines = [l.strip() for l in ref_block.split('\n') if l.strip()]
    refs = []
    for ref in lines:
        refs.append({
            "raw": ref,
            "title": extract_reference_title(ref),
            "venue": extract_venue(ref),
            "year": extract_year(ref)
        })
    return refs

# ========== 4. Extract Key Topics ==========
def extract_keyphrases(text: str, top_n: int = 10) -> List[str]:
    phrases = kw_model.extract_keywords(text, top_n=top_n)
    return [phrase[0] for phrase in phrases]

# ========== 5. Main Function ==========
def analyze_sections(sections: Dict[str, str]) -> Dict:
    title_author_lines = sections["title_and_authors"].split('\n')

    return {
        "title_and_authors": {
            "title": extract_title(title_author_lines),
            "authors": extract_authors(sections["title_and_authors"])
        },
        "content": {
            "topics": extract_keyphrases(sections["content"]),
            "text": sections["content"]
        },
        "references": parse_references(sections["references"])
    }

if __name__ == "__main__":
    import json
    from PDF.text import extract_text_sections  # Your previous script
    from nlp import analyze_sections        # Assuming this is where NLP processing is

    pdf_path = "test2.pdf"

    # Extract raw text sections
    raw_sections = extract_text_sections(pdf_path)

    # Save raw extracted text to a file
    with open("extracted_text.txt", "w", encoding="utf-8") as f:
        for section_name, section_text in raw_sections.items():
            f.write(f"=== {section_name.upper()} ===\n")
            f.write(section_text + "\n\n")   
    # Process sections using NLP
    structured = analyze_sections(raw_sections)

    # Save NLP processed structured output as formatted JSON
    with open("nlp_processed_text.txt", "w", encoding="utf-8") as f:
        json.dump(structured, f, ensure_ascii=False, indent=4)

    # Optional: Print summary to console
    print("\n=== TITLE ===")
    print(structured["title_and_authors"]["title"])
    print("\n=== AUTHORS ===")
    print(structured["title_and_authors"]["authors"])
    print("\n=== KEY TOPICS ===")
    print(structured["content"]["topics"])
    print("\n=== REFERENCES (parsed) ===")
    for ref in structured["references"]:
        print(ref)

