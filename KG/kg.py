
from tqdm import tqdm
from sentence_transformers import SentenceTransformer


# 1. Add main nodes without creating relationships
def create_nodes(graph, data: dict, node_label: str, node_name: str):
    # Create the main node
    main_node_query = f"""
    MERGE (main:{node_label} {{name: $name}})
    """
    graph.query(main_node_query, params={"name": node_name})

    # Create section nodes only (without relationships)
    for section, content in data.items():
        query = f"""
        MERGE (s:Section {{type: $type, parent_name: $name}})
     
        """
        params = {
            "type": section,
            "name": node_name
        }
        graph.query(query, params=params)


# 2. Add Chunks
def ingest_Chunks(graph, chunks, node_name, node_label):
    """
    Ingests file chunk data into the knowledge graph by merging chunk nodes.

    Args:
        graph: A knowledge graph client or connection object that has a `query` method.
        chunks: A list of dictionaries, each representing a file chunk with keys:
                     'chunkId', 'text', 'source', 'title', and 'chunkSeqId'.
        node_name: A string used to tag the chunk nodes.
        node_label: The dynamic label for the chunk nodes.
    """
    merge_chunk_node_query = f"""
    MERGE (mergedChunk:{node_label} {{chunkId: $chunkParam.chunkId}})
        ON CREATE SET
            mergedChunk.text = $chunkParam.text, 
            mergedChunk.source = $chunkParam.source, 
            mergedChunk.chunkSeqId = $chunkParam.chunkSeqId,
            mergedChunk.title=$chunkParam.title,
            mergedChunk.node_name = $node_name
    RETURN mergedChunk
    """

    node_count = 0
    for chunk in chunks:
        print(f"Creating `:{node_label}` node for chunk ID {chunk['chunkId']}")
        graph.query(merge_chunk_node_query, params={'chunkParam': chunk, 'node_name': node_name})
        node_count += 1
    print(f"Created {node_count} nodes")


# 3. Create Relationships

def create_relationship(graph, query: str, params: dict = None):
    """
    Executes the provided Cypher query on the given graph.
    
    Parameters:
        graph: An instance of your Neo4j connection.
        query: A string containing a valid Cypher query.
        params: A dictionary of parameters to pass to the query.
    """
    graph.query(query, params=params)






def create_vector_index(graph, index_name):
    # Create the vector index if it does not exist, using the dynamic node label
    vector_index_query = f"""
    CREATE VECTOR INDEX `{index_name}` IF NOT EXISTS
    FOR (n:{index_name}) ON (n.embedding) 
    OPTIONS {{ indexConfig: {{
        `vector.dimensions`: 384,
        `vector.similarity_function`: 'cosine'
    }}}}
    """
    graph.query(vector_index_query)





def embed_text(graph, embedding_model: SentenceTransformer, node_label: str):
    """
    Creates embeddings for nodes with a dynamic label using a Sentence Transformer model.
    
    Args:
        graph: A knowledge graph client/connection object.
        embedding_model: The loaded Sentence Transformer model.
        node_label: The label of nodes to process.
    """
    print("Starting embedding update...")

    # Fetch nodes without embeddings
    fetch_nodes_query = f"""
    MATCH (n:{node_label})
    WHERE n.embedding IS NULL
    RETURN elementId(n) AS node_id, n.text AS text
    """
    nodes = list(graph.query(fetch_nodes_query))
    total_nodes = len(nodes)
    print(f"Found {total_nodes} nodes without embeddings.")

    with tqdm(total=total_nodes, desc="Embedding nodes", ncols=100, leave=True) as pbar:
        for record in nodes:
            node_id = record["node_id"]
            text = record["text"]
            
            # Generate embedding
            embedding = embedding_model.encode(text).tolist()
            
            # Update the node with the new embedding
            update_query = f"""
            MATCH (n:{node_label})
            WHERE elementId(n) = $node_id
            SET n.embedding = $embedding
            """
            graph.query(update_query, params={
                "node_id": node_id,
                "embedding": embedding
            })
            pbar.update(1)

    print("Finished embedding update.")

def get_chunk_and_summary(graph, node_name):
    """
    Retrieves the text of all chunks and the summary for a given node name.

    Args:
        graph: A knowledge graph client or connection object.
        node_name: The name of the node to retrieve data for.

    Returns:
        A tuple containing:
        - A list of chunk texts.
        - The summary text.
    """
    # Query to get all chunk texts for the specified node_name
    chunk_query = f"""
    MATCH (c:Chunk {{node_name: '{node_name}'}})
    RETURN c.text AS chunk_text
    """
    chunk_texts = [record['chunk_text'] for record in graph.query(chunk_query)]

    # Query to get the summary for the specified node_name
    summary_query = f"""
    MATCH (s:Summary {{node_name: '{node_name}'}})
    RETURN s.text AS summary_text
    """
    summary_result = graph.query(summary_query)
    
    # Check if a summary was found
    if summary_result:
        summary_text = summary_result[0]['summary_text']
    else:
        summary_text = "No summary found for this node."

    return chunk_texts, summary_text