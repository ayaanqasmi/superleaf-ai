import os
import json
from fuzzywuzzy import fuzz
from KG.config import load_neo4j_graph
from KG.chunking import chunk_text
from KG.kg import create_vector_index, embed_text
from PDF.text import extract_text_sections

# --- Constants ---
METADATA_PATH = "metadata.json"
PDF_PATH = "pdf_input/RIS-Empowered_Ambient_Backscatter_Communication_Systems[1].pdf"

# --- Fuzzy Matching Thresholds ---
AUTHOR_MATCH_THRESHOLD = 85
PAPER_MATCH_THRESHOLD = 90

def get_existing_nodes(graph, label, property_name):
    """Fetches existing nodes of a given label and property from the graph."""
    query = f"MATCH (n:{label}) RETURN n.{property_name} AS name"
    return {record['name'] for record in graph.query(query) if record['name'] is not None}

def find_best_match(name, existing_names, threshold):
    """Finds the best fuzzy match for a name from a list of existing names."""
    best_match_score = 0
    best_match_name = None
    for existing_name in existing_names:
        score = fuzz.ratio(name.lower(), existing_name.lower())
        if score > best_match_score:
            best_match_score = score
            best_match_name = existing_name
    
    if best_match_score >= threshold:
        return best_match_name
    return name

def ingest_paper(graph, paper_data, existing_authors, existing_papers):
    """Ingests a single paper and its relationships into the graph."""
    # --- Create or Merge Paper Node ---
    paper_title = paper_data.get('paper_title')
    if paper_title:
        matched_paper = find_best_match(paper_title, existing_papers, PAPER_MATCH_THRESHOLD)
    
    if matched_paper:
        print(f"Matching existing paper: '{paper_title}' with '{matched_paper}'")
        paper_title = matched_paper
    else:
        existing_papers.add(paper_title)

    graph.query(
        "MERGE (p:Paper {title: $title}) ON CREATE SET p.doi = $doi, p.publication_date = $pub_date",
        params={
            'title': paper_title,
            'doi': paper_data.get('doi'),
            'pub_date': paper_data.get('publication_date')
        }
    )

    # --- Create or Merge Author Nodes and Relationships ---
    for author in paper_data.get('authors', []):
        author_name = author['full_name']
        matched_author = find_best_match(author_name, existing_authors, AUTHOR_MATCH_THRESHOLD)

        if matched_author:
            print(f"Matching existing author: '{author_name}' with '{matched_author}'")
            author_name = matched_author
        else:
            existing_authors.add(author_name)
        
        graph.query(
            "MERGE (a:Author {name: $name}) ON CREATE SET a.email = $email, a.orcid = $orcid, a.affiliation = $affiliation",
            params={
                'name': author_name,
                'email': author.get('email'),
                'orcid': author.get('orcid'),
                'affiliation': author.get('affiliation')
            }
        )
        graph.query(
            "MATCH (a:Author {name: $author_name}), (p:Paper {title: $paper_title}) MERGE (a)-[:AUTHORED_BY]->(p)",
            params={'author_name': author_name, 'paper_title': paper_title}
        )

    # --- Create or Merge Topic Nodes and Relationships ---
    for keyword in paper_data.get('keywords', []):
        graph.query("MERGE (t:Topic {name: $name})", params={'name': keyword})
        graph.query(
            "MATCH (p:Paper {title: $paper_title}), (t:Topic {name: $keyword}) MERGE (p)-[:HAS_TOPIC]->(t)",
            params={'paper_title': paper_title, 'keyword': keyword}
        )

    # --- Create or Merge Referenced Papers and Relationships ---
    for ref in paper_data.get('references', []):
        ref_title = ref['title']
        matched_ref = find_best_match(ref_title, existing_papers, PAPER_MATCH_THRESHOLD)

        if matched_ref:
            print(f"Matching existing reference: '{ref_title}' with '{matched_ref}'")
            ref_title = matched_ref
        else:
            existing_papers.add(ref_title)

        graph.query(
            "MERGE (p:Paper {title: $title}) ON CREATE SET p.publication_date = $pub_date",
            params={'title': ref_title, 'pub_date': ref.get('date')}
        )
        graph.query(
            "MATCH (p1:Paper {title: $paper_title}), (p2:Paper {title: $ref_title}) MERGE (p1)-[:REFERENCES]->(p2)",
            params={'paper_title': paper_title, 'ref_title': ref_title}
        )

    return paper_title

def load_and_ingest(pdfPath):

    # --- Load Resources ---
    graph, embedding_model = load_neo4j_graph()
    
    # --- Metadata Extraction ---
    from NLP.grobid import generate_xml
    xmlDir=generate_xml(pdfPath)
    xmlFiles=os.listdir(xmlDir)
    xmlPath=os.path.join(xmlDir,xmlFiles[0])
    
    from NLP.extract_metadata import extract_metadata
    metadata=extract_metadata(xmlPath)

    # --- Get Existing Nodes for Fuzzy Matching ---
    existing_authors = get_existing_nodes(graph, 'Author', 'name')
    existing_papers = get_existing_nodes(graph, 'Paper', 'title')

    # --- Ingest Paper and its Metadata ---
    print("Ingesting paper metadata...")
    paper_title = ingest_paper(graph, metadata, existing_authors, existing_papers)

    # --- Extract Text and Ingest Chunks ---
    print(f"Extracting text from {pdfPath}...")
    extracted_data = extract_text_sections(pdfPath)
    
    print("Chunking text...")
    chunks = chunk_text(extracted_data['content'], title=paper_title, source=os.path.basename(pdfPath))

    print("Ingesting chunks...")
    for chunk in chunks:
        graph.query(
            "MERGE (c:Chunk {chunkId: $chunkId}) ON CREATE SET c.text = $text, c.source = $source, c.chunkSeqId = $chunkSeqId, c.title = $title",
            params=chunk
        )
        graph.query(
            "MATCH (p:Paper {title: $paper_title}), (c:Chunk {chunkId: $chunkId}) MERGE (p)-[:CONTAINS]->(c)",
            params={'paper_title': paper_title, 'chunkId': chunk['chunkId']}
        )

    # --- Create Vector Index and Embeddings ---
    print("Creating vector index...")
    create_vector_index(graph, "Chunk")

    print("Embedding text...")
    embed_text(graph, embedding_model, "Chunk")

    print("\nIngestion complete.")


