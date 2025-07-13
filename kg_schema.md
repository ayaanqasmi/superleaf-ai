```markdown
# Knowledge Graph Schema

This document outlines the schema for the knowledge graph, which is designed to store and represent information from academic papers.

## Nodes

The following node types are used in the graph:

### Paper

Represents a single academic paper.

- **Label:** `Paper`
- **Properties:**
    - `title`: The title of the paper (string, unique).
    - `doi`: The Digital Object Identifier of the paper (string).
    - `publication_date`: The year the paper was published (integer).

### Author

Represents an author of a paper.

- **Label:** `Author`
- **Properties:**
    - `name`: The full name of the author (string, unique).
    - `email`: The email address of the author (string, optional).
    - `orcid`: The ORCID of the author (string, optional).
    - `affiliation`: The affiliation of the author (string, optional).

### Topic

Represents a keyword or topic associated with a paper.

- **Label:** `Topic`
- **Properties:**
    - `name`: The name of the topic (string, unique).

### Chunk

Represents a chunk of text from a paper.

- **Label:** `Chunk`
- **Properties:**
    - `chunkId`: A unique identifier for the chunk (string).
    - `text`: The text content of the chunk (string).
    - `source`: The source of the chunk (e.g., the paper's filename) (string).
    - `chunkSeqId`: The sequence number of the chunk within the paper (integer).
    - `embedding`: A vector embedding of the chunk's text (list of floats).

## Edges

The following edge types (relationships) are used to connect the nodes:

### AUTHORED_BY

Connects an `Author` to a `Paper` they have written.

- **Source:** `Author`
- **Target:** `Paper`
- **Type:** `AUTHORED_BY`

### REFERENCES

Connects a `Paper` to another `Paper` that it references.

- **Source:** `Paper`
- **Target:** `Paper`
- **Type:** `REFERENCES`

### HAS_TOPIC

Connects a `Paper` to a `Topic` it covers.

- **Source:** `Paper`
- **Target:** `Topic`
- **Type:** `HAS_TOPIC`

### CONTAINS

Connects a `Paper` to its `Chunk`s.

- **Source:** `Paper`
- **Target:** `Chunk`
- **Type:** `CONTAINS`
```