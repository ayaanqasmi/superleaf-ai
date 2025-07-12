from langchain.text_splitter import RecursiveCharacterTextSplitter


text_splitter = RecursiveCharacterTextSplitter(
    chunk_size = 2000,
    chunk_overlap  = 200,
    length_function = len,
    is_separator_regex = False,
)



def chunk_text(text, title, source):
    """
    Chunks the input text and adds metadata.

    Args:
        text (str): The text to be chunked.
        title (str): The title of the document.
        source (str): The source of the document.

    Returns:
        list: A list of dictionaries, where each dictionary represents a chunk
              with its metadata.
    """
    chunks_with_metadata = []

    # Split the text into chunks
    text_chunks = text_splitter.split_text(text)

    chunk_seq_id = 0
    # Loop through chunks
    for chunk in text_chunks:
        # Create a record with metadata and the chunk text
        chunks_with_metadata.append({
            'text': chunk,
            'title': title,
            'source': source,
            'chunkSeqId': chunk_seq_id,
            'chunkId': f'{source}-chunk{chunk_seq_id:04d}',
        })
        chunk_seq_id += 1

    print(f'Split into {chunk_seq_id} chunks')
    return chunks_with_metadata