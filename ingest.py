import os
import json
import re
from dotenv import load_dotenv
from groq import Groq
from PDF.text import extract_text_sections

# Load environment variables from .env file
load_dotenv()

# Get the API key from the environment
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Initialize the Groq client
client = Groq(api_key=GROQ_API_KEY)

def clean_extracted_data(json_string: str) -> str:
    """
    Cleans the JSON output from the language model.
    - Removes common non-author words (e.g., 'and') from author lists.
    - Removes trailing numbers from reference titles.
    """
    try:
        data = json.loads(json_string)
    except json.JSONDecodeError:
        return json_string  # Return original if not valid JSON

    # Words to remove from author lists
    JUNK_WORDS = {'and', 'or', 'et', 'al', 'et al.'}

    # Clean main authors
    if 'authors' in data and isinstance(data['authors'], list):
        data['authors'] = [author for author in data['authors'] if author.strip().lower() not in JUNK_WORDS]

    # Clean references
    if 'references' in data and isinstance(data['references'], list):
        for ref in data['references']:
            if isinstance(ref, dict):
                # Clean authors in reference
                if 'authors' in ref and isinstance(ref['authors'], list):
                    ref['authors'] = [author for author in ref['authors'] if author.strip().lower() not in JUNK_WORDS]
                # Clean title in reference (remove trailing numbers and punctuation)
                if 'title' in ref and isinstance(ref['title'], str):
                    ref['title'] = re.sub(r'[\s,.]*\d+,', '', ref['title']).strip()


    return json.dumps(data, indent=4)

def process_pdf(pdf_path: str) -> str:
    """
    Processes a PDF file to extract and clean structured information.
    """
    # Step 1: Extract text sections
    text_sections = extract_text_sections(pdf_path)
    title_and_authors_text = text_sections["title_and_authors"]
    references_text = text_sections["references"]

    # Step 2: Create prompt for the language model
    prompt = f'''
You are a meticulous expert in analyzing research papers and extracting structured information. Your task is to process the provided text from a research paper and return a flawless JSON object.

You will be given text from the paper's title and authors section, and text from its references section.

Here is the title and authors text:
---
{title_and_authors_text}
---

Here is the references text:
---
{references_text}
---

Please perform the following tasks with high precision:
1.  **title**: From the "title and authors text", extract the exact title of the paper. It should be a single, clean string.
2.  **authors**: From the "title and authors text", extract all authors. 
    - Return a list of strings.
    - CRITICAL: Do NOT include conjunctions like 'and' or abbreviations like 'et al.' as separate entries in the author list.
3.  **references**: From the "references text", parse each reference. 
    - Return a list of objects, where each object has a "title" (string) and "authors" (list of strings).
    - The reference "title" must be clean, containing only the title of the work. Do NOT include surrounding text, page numbers, volume numbers, or years.
    - The reference "authors" should be a list of strings. Do not include 'and' or 'et al.' as authors.
    - If you cannot determine the title or authors for a reference, omit the key or the entire reference object.

Your final output must be a single, valid JSON object with the keys "title", "authors", and "references". Do not include any other text, explanations, or apologies in your response.
'''

    # Step 3: Call the language model
    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
        model="llama-3.1-8b-instant",
        response_format={"type": "json_object"},
    )

    raw_output = chat_completion.choices[0].message.content

    # Step 4: Clean the extracted data
    cleaned_output = clean_extracted_data(raw_output)

    return cleaned_output

if __name__ == "__main__":
    pdf_path = r'C:\Users\ayaan\projects\current\superleaf\ai\RIS-Empowered_Ambient_Backscatter_Communication_Systems[1].pdf'
    extracted_data = process_pdf(pdf_path)
    print(extracted_data)
    pass
