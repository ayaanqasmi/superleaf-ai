from unstructured.partition.pdf import partition_pdf
import json


elements = partition_pdf("test.pdf")

from langchain.text_splitter import RecursiveCharacterTextSplitter

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,
    chunk_overlap=50,
    separators=["\n\n", "\n", ".", " ", ""]
)

chunks = text_splitter.create_documents(
    [el.text for el in elements if el.text.strip()],
    metadatas=[{"type": el.category} for el in elements]
)

for i, chunk in enumerate(chunks):
    chunk.metadata["source"] = "papers/llama.pdf"
    chunk.metadata["chunk_index"] = i
    chunk.metadata["embedding_model"] = "all-MiniLM-L6-v2"
    chunk.metadata["text_length"] = len(chunk.page_content)


from sentence_transformers import SentenceTransformer
import psycopg2

model = SentenceTransformer("all-MiniLM-L6-v2")

conn = psycopg2.connect(
    dbname="mydb", user="postgres", password="1234",
    host="localhost", port=5433
)
cursor = conn.cursor()

for chunk in chunks:
    embedding = model.encode(chunk.page_content).tolist()
    cursor.execute("""
        INSERT INTO rag_documents (content, embedding, metadata)
        VALUES (%s, %s, %s)
    """, (
        chunk.page_content,
        embedding,
        json.dumps(chunk.metadata)  # store metadata as JSON
    ))
conn.commit()
