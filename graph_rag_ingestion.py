
import os
from dotenv import load_dotenv
from neo4j import GraphDatabase
from langchain.text_splitter import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer
from PDF.text import extract_text_sections
from PDF.image import extract_images_and_captions
from ingest import process_pdf
from thefuzz import fuzz
import json
from PIL import Image

# Load environment variables
load_dotenv()

# Neo4j connection details
NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

# Initialize models
text_embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
image_embedding_model = SentenceTransformer('clip-ViT-B-32')


class Neo4jConnection:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def query(self, query, parameters=None):
        with self.driver.session() as session:
            result = session.run(query, parameters)
            return [record for record in result]


def process_and_embed_text(pdf_path, neo4j_conn):
    """
    Chunks text from a PDF, embeds it, and stores it in Neo4j.
    """
    text_sections = extract_text_sections(pdf_path)
    content = text_sections.get("content", "")

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len
    )
    chunks = text_splitter.split_text(content)

    for i, chunk in enumerate(chunks):
        embedding = text_embedding_model.encode(chunk).tolist()
        neo4j_conn.query(
            "CREATE (c:Chunk {text: $text, embedding: $embedding, part: $part})",
            parameters={"text": chunk, "embedding": embedding, "part": i}
        )
    print(f"Stored {len(chunks)} text chunks in Neo4j.")


def process_and_embed_images(pdf_path, neo4j_conn):
    """
    Extracts images from a PDF, embeds them, and stores them in Neo4j.
    """
    image_data = extract_images_and_captions(pdf_path)

    for item in image_data:
        image_path = item.get("image_path")
        caption = item.get("caption")
        try:
            image = Image.open(image_path)
            embedding = image_embedding_model.encode(image).tolist()
            neo4j_conn.query(
                "CREATE (i:Image {path: $path, caption: $caption, embedding: $embedding})",
                parameters={"path": image_path, "caption": caption, "embedding": embedding}
            )
        except Exception as e:
            print(f"Could not process image {image_path}: {e}")

    print(f"Stored {len(image_data)} images in Neo4j.")


def create_knowledge_graph(pdf_path, neo4j_conn):
    """
    Extracts entities and relationships from the PDF and builds the knowledge graph.
    """
    # Get structured data from the LLM
    structured_data_str = process_pdf(pdf_path)
    structured_data = json.loads(structured_data_str)

    main_title = structured_data.get("title")
    main_authors = structured_data.get("authors", [])
    references = structured_data.get("references", [])

    # Create the main paper node
    neo4j_conn.query(
        "MERGE (p:Paper {title: $title})",
        parameters={"title": main_title}
    )

    # Create author nodes and connect them to the main paper
    for author_name in main_authors:
        neo4j_conn.query(
            "MERGE (a:Author {name: $name})",
            parameters={"name": author_name}
        )
        neo4j_conn.query(
            """
            MATCH (p:Paper {title: $paper_title})
            MATCH (a:Author {name: $author_name})
            MERGE (a)-[:AUTHORED_BY]->(p)
            """,
            parameters={"paper_title": main_title, "author_name": author_name}
        )

    # Process references
    for ref in references:
        ref_title = ref.get("title")
        if not ref_title:
            continue

        # Fuzzy match for existing paper
        existing_papers = neo4j_conn.query("MATCH (p:Paper) RETURN p.title AS title")
        best_match = None
        highest_score = 0
        for record in existing_papers:
            title = record["title"]
            score = fuzz.ratio(ref_title.lower(), title.lower())
            if score > highest_score:
                highest_score = score
                best_match = title

        # If a similar paper is found, use it; otherwise, create a new one
        if highest_score > 85:  # Threshold for matching
            target_paper_title = best_match
        else:
            target_paper_title = ref_title
            neo4j_conn.query(
                "MERGE (p:Paper {title: $title})",
                parameters={"title": target_paper_title}
            )

        # Create citation relationship
        neo4j_conn.query(
            """
            MATCH (p1:Paper {title: $title1})
            MATCH (p2:Paper {title: $title2})
            MERGE (p1)-[:CITES]->(p2)
            """,
            parameters={"title1": main_title, "title2": target_paper_title}
        )

    print("Knowledge graph created.")


if __name__ == "__main__":
    pdf_file_path = r'C:\Users\ayaan\projects\current\superleaf\ai\RIS-Empowered_Ambient_Backscatter_Communication_Systems[1].pdf'
    
    # Establish Neo4j connection
    neo4j_conn = Neo4jConnection(NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD)

    # Run the ingestion pipeline
    process_and_embed_text(pdf_file_path, neo4j_conn)
    process_and_embed_images(pdf_file_path, neo4j_conn)
    create_knowledge_graph(pdf_file_path, neo4j_conn)

    # Close the connection
    neo4j_conn.close()
    print("Ingestion pipeline complete.")
