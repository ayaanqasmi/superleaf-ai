import psycopg2
import json
from sentence_transformers import SentenceTransformer
import google.generativeai as genai
import os
from dotenv import load_dotenv
load_dotenv()
# === SETUP ===
DB_CONFIG = {
    "dbname": "mydb",
    "user": "postgres",
    "password": "1234",
    "host": "localhost",
    "port": 5433
}

EMBEDDING_DIM = 384  # should match your DB vector dim
TOP_K = 5  # Number of chunks to retrieve
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# === INIT MODELS ===
model = SentenceTransformer("all-MiniLM-L6-v2")
genai.configure(api_key=GEMINI_API_KEY)
llm = genai.GenerativeModel("gemini-2.5-flash")

# === STEP 1: Semantic Retrieval ===
def get_relevant_chunks(question, k=TOP_K):
    embedding = model.encode(question).tolist()

    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT content, metadata
        FROM rag_documents
        ORDER BY embedding <-> %s::vector
        LIMIT %s
    """, (embedding, k))
    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    return [row[0] for row in rows]  # only return content

# === STEP 2: Build Prompt ===
def build_prompt(chunks, question):

    context = "\n---\n".join(chunks)
    print(context)
    prompt = f"""
You are a helpful assistant answering questions based on document context.

Context:
{context}

Question:
{question}

Answer:"""
    return prompt.strip()

# === STEP 3: Generate Answer with Gemini ===
def answer_question(question):
    chunks = get_relevant_chunks(question)
    prompt = build_prompt(chunks, question)
    response = llm.generate_content(prompt)
    return response.text.strip()

# === TEST ===
if __name__ == "__main__":
    question = input("Enter your question: ")
    answer = answer_question(question)
    print("\nGemini Answer:\n")
    print(answer)
