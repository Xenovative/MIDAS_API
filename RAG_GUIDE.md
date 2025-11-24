# RAG (Retrieval-Augmented Generation) Guide

## Overview

MIDAS now supports RAG functionality, allowing bots to access custom knowledge bases for more accurate and contextual responses. Documents are chunked, embedded using OpenAI's text-embedding models, and retrieved based on semantic similarity.

## Features

- **Document Upload**: Upload text documents to create knowledge bases for bots
- **Automatic Chunking**: Documents are automatically split into overlapping chunks for better retrieval
- **Semantic Search**: Uses OpenAI embeddings (text-embedding-3-small by default) for similarity search
- **Configurable Retrieval**: Adjust top-k results and similarity threshold per bot
- **Seamless Integration**: RAG context is automatically injected into chat conversations

## Architecture

### Components

1. **Embeddings Module** (`backend/embeddings.py`)
   - Handles text embedding generation using OpenAI API
   - Supports multiple embedding models
   - Default: `text-embedding-3-small` (1536 dimensions)

2. **Vector Store** (`backend/vector_store.py`)
   - In-memory vector storage with cosine similarity search
   - Document chunking with overlap
   - Efficient retrieval with configurable thresholds

3. **Database Models** (`backend/models.py`)
   - `Document`: Stores document metadata
   - `DocumentChunk`: Stores text chunks with embeddings
   - Bot RAG configuration fields

4. **API Endpoints** (`backend/routes/documents.py`)
   - Document upload and management
   - Search testing endpoint

## Usage

### 1. Enable RAG for a Bot

When creating or updating a bot, set RAG parameters:

```json
{
  "name": "Knowledge Bot",
  "system_prompt": "You are a helpful assistant with access to a knowledge base.",
  "use_rag": true,
  "rag_top_k": 5,
  "rag_similarity_threshold": 0.7
}
```

**Parameters:**
- `use_rag`: Enable/disable RAG for this bot
- `rag_top_k`: Number of document chunks to retrieve (default: 5)
- `rag_similarity_threshold`: Minimum similarity score (0-1, default: 0.7)

### 2. Upload Documents

**Option A: Upload text content directly**

```bash
POST /documents/upload
{
  "bot_id": "bot-uuid",
  "filename": "product_manual.txt",
  "content": "Your document text here..."
}
```

**Option B: Upload a file**

```bash
POST /documents/upload-file?bot_id=bot-uuid
Content-Type: multipart/form-data
file: <your-text-file>
```

### 3. List Documents

```bash
GET /documents/bot/{bot_id}
```

### 4. Delete Documents

```bash
DELETE /documents/{document_id}
```

### 5. Test Search (Optional)

```bash
POST /documents/search
{
  "bot_id": "bot-uuid",
  "query": "How do I reset the device?",
  "top_k": 5,
  "similarity_threshold": 0.7
}
```

## Chat Integration

When chatting with a RAG-enabled bot, relevant context is automatically retrieved and injected:

```bash
POST /chat/
{
  "bot_id": "bot-uuid",
  "message": "How do I configure the settings?",
  "model": "gpt-4",
  "provider": "openai"
}
```

The system will:
1. Generate an embedding for the user's query
2. Search the bot's knowledge base for relevant chunks
3. Inject the top-k most similar chunks as context
4. Generate a response using the LLM with the enriched context

## Document Processing

### Chunking Strategy

- **Chunk Size**: 1000 characters (configurable)
- **Overlap**: 200 characters (configurable)
- **Boundary Detection**: Attempts to break at sentence boundaries
- **Metadata**: Tracks chunk position and source document

### Embedding Generation

- Uses OpenAI's `text-embedding-3-small` model
- 1536-dimensional vectors
- Batch processing for efficiency
- Stored as JSON in SQLite

### Similarity Search

- **Algorithm**: Cosine similarity
- **Threshold**: Configurable per bot (default: 0.7)
- **Results**: Sorted by similarity score, top-k returned

## Configuration

### Environment Variables

Ensure your `.env` file contains:

```env
OPENAI_API_KEY=your-api-key-here
```

### Bot Configuration

Each bot can have different RAG settings:

```python
bot.use_rag = True                    # Enable RAG
bot.rag_top_k = 5                     # Retrieve top 5 chunks
bot.rag_similarity_threshold = 0.7    # Minimum 70% similarity
```

## API Reference

### Document Endpoints

#### Upload Document
```
POST /documents/upload
Authorization: Bearer <token>
Content-Type: application/json

{
  "bot_id": "string",
  "filename": "string",
  "content": "string"
}

Response: DocumentResponse
```

#### Upload File
```
POST /documents/upload-file?bot_id=<bot_id>
Authorization: Bearer <token>
Content-Type: multipart/form-data

file: <file>

Response: DocumentResponse
```

#### List Documents
```
GET /documents/bot/{bot_id}
Authorization: Bearer <token>

Response: List[DocumentResponse]
```

#### Delete Document
```
DELETE /documents/{document_id}
Authorization: Bearer <token>

Response: {"message": "Document deleted successfully"}
```

#### Search Documents
```
POST /documents/search
Authorization: Bearer <token>
Content-Type: application/json

{
  "bot_id": "string",
  "query": "string",
  "top_k": 5,
  "similarity_threshold": 0.7
}

Response: List[DocumentSearchResult]
```

## Best Practices

1. **Document Quality**: Upload well-structured, relevant documents
2. **Chunk Size**: Adjust based on document structure (default 1000 chars works well)
3. **Similarity Threshold**: Lower for broader results (0.6), higher for precision (0.8+)
4. **Top-K**: Balance between context richness (higher) and token usage (lower)
5. **System Prompt**: Instruct the bot to use the knowledge base appropriately

## Example Use Cases

### Customer Support Bot
```json
{
  "name": "Support Bot",
  "system_prompt": "You are a customer support assistant. Use the knowledge base to answer questions accurately. If information is not in the knowledge base, say so.",
  "use_rag": true,
  "rag_top_k": 3,
  "rag_similarity_threshold": 0.75
}
```

Upload: Product manuals, FAQs, troubleshooting guides

### Documentation Assistant
```json
{
  "name": "Docs Assistant",
  "system_prompt": "You are a technical documentation assistant. Provide accurate answers based on the documentation in your knowledge base. Include relevant code examples when available.",
  "use_rag": true,
  "rag_top_k": 5,
  "rag_similarity_threshold": 0.7
}
```

Upload: API documentation, code examples, tutorials

### Research Assistant
```json
{
  "name": "Research Bot",
  "system_prompt": "You are a research assistant. Use the research papers and articles in your knowledge base to provide informed answers. Cite sources when possible.",
  "use_rag": true,
  "rag_top_k": 7,
  "rag_similarity_threshold": 0.65
}
```

Upload: Research papers, articles, reports

## Limitations

- **Storage**: Embeddings stored in SQLite (consider PostgreSQL with pgvector for production)
- **Search**: In-memory cosine similarity (consider FAISS or Pinecone for scale)
- **File Types**: Currently supports UTF-8 text files only
- **Embedding Model**: Fixed to OpenAI (extensible to other providers)

## Future Enhancements

- [ ] Support for PDF, DOCX, and other file formats
- [ ] Advanced chunking strategies (semantic, recursive)
- [ ] Multiple embedding providers (Cohere, HuggingFace)
- [ ] Vector database integration (Pinecone, Weaviate, Qdrant)
- [ ] Hybrid search (keyword + semantic)
- [ ] Document versioning and updates
- [ ] Metadata filtering
- [ ] Citation tracking in responses

## Troubleshooting

### "OPENAI_API_KEY not found"
Ensure your `.env` file contains a valid OpenAI API key.

### "RAG is not enabled for this bot"
Set `use_rag: true` when creating/updating the bot.

### Low-quality results
- Increase `rag_top_k` to retrieve more context
- Lower `rag_similarity_threshold` to broaden results
- Improve document quality and structure
- Adjust chunk size if documents have specific structure

### High token usage
- Decrease `rag_top_k` to reduce context size
- Increase `rag_similarity_threshold` to only retrieve highly relevant chunks
- Use smaller chunk sizes

## Migration

To add RAG to an existing database:

```bash
python migrate_add_rag.py
```

This adds:
- RAG columns to `bots` table
- `documents` table
- `document_chunks` table
- Necessary indexes
