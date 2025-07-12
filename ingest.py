
import os
from KG.config import load_neo4j_graph
from KG.chunking import chunk_text
from KG.kg import create_nodes, ingest_Chunks, create_relationship, create_vector_index, embed_text
from PDF.text import extract_text_sections

# Define the path to the PDF file
PDF_PATH = "RIS-Empowered_Ambient_Backscatter_Communication_Systems[1].pdf"

def main():
    # Load Neo4j graph and embedding model
    graph, embedding_model = load_neo4j_graph()

    # Define node label and name
    node_label = "Paper"
    node_name = os.path.basename(PDF_PATH)

    # Extract text from the PDF
    print(f"Extracting text from {PDF_PATH}...")
    extracted_data = extract_text_sections(PDF_PATH)

    # Create main nodes
    print("Creating main nodes...")
    create_nodes(graph, extracted_data, node_label, node_name)

    # Chunk the content
    print("Chunking text...")
    chunks = chunk_text(extracted_data['content'], title=extracted_data['title_and_authors'], source=node_name)

    # Ingest chunks into Neo4j
    print("Ingesting chunks...")
    ingest_Chunks(graph, chunks, node_name, "Chunk")

    # Create vector index
    print("Creating vector index...")
    create_vector_index(graph, "Chunk")

    # Embed the text of the chunks
    print("Embedding text...")
    embed_text(graph, embedding_model, "Chunk")

    # Create relationships
    print("Creating relationships...")
    query = f"""
    MATCH (p:{node_label} {{name: $node_name}}), (s:Section {{parent_name: $node_name}})
    MERGE (p)-[:HAS_SECTION]->(s)
    """
    create_relationship(graph, query, params={"node_name": node_name})

    query = f"""
    MATCH (s:Section {{parent_name: $node_name}}), (c:Chunk {{node_name: $node_name}})
    WHERE s.type = c.title
    MERGE (s)-[:CONTAINS]->(c)
    """
    create_relationship(graph, query, params={"node_name": node_name})

    print("Ingestion complete.")

if __name__ == "__main__":
    main()
