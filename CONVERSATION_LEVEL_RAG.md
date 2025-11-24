# Conversation-Level RAG Implementation

## Overview

RAG functionality now works with **any conversation**, not just bot conversations! You can upload documents directly in the chat and they'll be used to enhance responses, regardless of whether you're using a bot or standard model.

## What Changed

### ✅ Before
- RAG only worked with RAG-enabled bots
- Upload button only showed for bots with `use_rag: true`
- Documents tied exclusively to bots

### ✅ After
- RAG works with **any conversation**
- Upload button shows for **all conversations**
- Documents can be tied to:
  - **Bots** (bot-level knowledge base)
  - **Conversations** (conversation-specific context)
  - **Users** (user-level documents)

## Key Features

### 1. Universal Upload Button
- Shows upload menu (⬆️) for any active conversation
- No need for RAG-enabled bot
- Works with standard models (GPT-4, Claude, etc.)

### 2. Conversation-Level Documents
- Upload documents specific to a conversation
- Documents automatically retrieved when chatting
- Perfect for ad-hoc context injection

### 3. Flexible Document Association
Documents can be associated with:
- **Bot** - Shared across all conversations with that bot
- **Conversation** - Specific to one conversation
- **User** - Personal documents (future use)

## How It Works

### Upload Flow
```
1. User starts conversation (any model)
2. Upload button (⬆️) appears
3. User clicks → menu shows:
   - Upload Image
   - Upload Document
4. User uploads document.txt
5. Document associated with conversation_id
6. RAG retrieval happens automatically
```

### Retrieval Flow
```
1. User sends message
2. System searches for documents:
   - Bot documents (if using bot)
   - Conversation documents
3. Top-k relevant chunks retrieved
4. Injected as context
5. LLM generates response
```

## Database Schema

### Updated `documents` Table
```sql
CREATE TABLE documents (
    id TEXT PRIMARY KEY,
    bot_id TEXT,              -- Optional: for bot-level docs
    conversation_id TEXT,     -- Optional: for conversation-level docs
    user_id TEXT,             -- Optional: for user-level docs
    filename TEXT NOT NULL,
    content TEXT NOT NULL,
    chunk_count INTEGER,
    created_at TIMESTAMP,
    FOREIGN KEY (bot_id) REFERENCES bots(id),
    FOREIGN KEY (conversation_id) REFERENCES conversations(id),
    FOREIGN KEY (user_id) REFERENCES users(id)
)
```

## Usage Examples

### Example 1: Standard Model with Context
```
User: [Starts chat with GPT-4]
User: [Uploads company-policy.txt]
User: "What's our vacation policy?"
Bot: [Uses uploaded document to answer]
```

### Example 2: Ad-hoc Research
```
User: [Chatting about a topic]
User: [Uploads research-paper.txt]
User: "Summarize the key findings"
Bot: [References the paper]
```

### Example 3: Mixed Sources
```
User: [Using RAG-enabled bot]
Bot has: product-manual.txt (bot-level)
User uploads: custom-config.txt (conversation-level)
User: "How do I configure this?"
Bot: [Uses both bot docs + conversation docs]
```

## API Changes

### Backend

**Updated `vector_store.add_document()`**
```python
await vector_store.add_document(
    db=db,
    filename="doc.txt",
    content="...",
    bot_id=None,              # Optional
    conversation_id="conv-123", # Optional
    user_id="user-456"        # Optional
)
```

**Updated `vector_store.search()`**
```python
results = await vector_store.search(
    db=db,
    query="search query",
    bot_id=None,              # Optional
    conversation_id="conv-123", # Optional
    user_id=None,             # Optional
    top_k=5,
    similarity_threshold=0.7
)
```

**Updated `fetch_rag_context()`**
```python
rag_context, rag_execs = await fetch_rag_context(
    query=message,
    bot_id=bot_id,           # Optional
    conversation_id=conv_id,  # Always provided
    db=db
)
```

### Frontend

**Updated `documentsApi.uploadFile()`**
```javascript
await documentsApi.uploadFile(
    file,
    botId,          // Optional
    conversationId  // Optional
)
```

**Updated `ChatInput` Props**
```javascript
<ChatInput
    conversationId={currentConversation?.id}  // New prop
    selectedBot={selectedBot}
    // ... other props
/>
```

## Files Modified

### Backend
1. **`backend/models.py`**
   - Made `bot_id` nullable
   - Added `conversation_id` column
   - Added `user_id` column
   - Added relationships

2. **`backend/vector_store.py`**
   - Updated `add_document()` to accept multiple IDs
   - Updated `search()` to search across multiple sources
   - Uses OR logic for flexible retrieval

3. **`backend/routes/chat.py`**
   - Updated `fetch_rag_context()` to accept conversation_id
   - Always calls RAG retrieval (not just for bots)
   - Searches bot + conversation documents

4. **`backend/routes/documents.py`**
   - Updated upload endpoints to accept conversation_id
   - Made bot_id optional
   - Removed RAG-enabled bot requirement

### Frontend
1. **`frontend/src/lib/api.js`**
   - Updated `uploadFile()` to accept conversation_id

2. **`frontend/src/components/ChatInput.jsx`**
   - Added `conversationId` prop
   - Shows upload button for any conversation
   - Passes conversation_id to upload API

3. **`frontend/src/components/ChatArea.jsx`**
   - Passes `conversationId` to ChatInput

### Migration
- **`migrate_rag_conversation_level.py`** - Database migration script

## Migration

Run the migration to update your database:
```bash
python migrate_rag_conversation_level.py
```

This adds:
- `conversation_id` column to documents
- `user_id` column to documents
- Indexes for performance

## Benefits

✅ **Flexibility**: Use RAG with any model, not just bots
✅ **Convenience**: Upload context mid-conversation
✅ **Simplicity**: No need to create RAG bots for one-off use
✅ **Power**: Combine bot-level + conversation-level docs
✅ **Intuitive**: Upload button always available

## Use Cases

### 1. Quick Reference
Upload a document for a specific conversation without creating a bot

### 2. Temporary Context
Add context for one conversation that doesn't need to persist

### 3. Mixed Knowledge
Use bot's permanent knowledge + conversation-specific documents

### 4. Standard Models with Context
Use GPT-4, Claude, etc. with your own documents

### 5. Research Sessions
Upload multiple papers/documents for a research conversation

## Retrieval Priority

When searching, the system retrieves from:
1. **Bot documents** (if bot is selected and has RAG enabled)
2. **Conversation documents** (always checked)
3. **User documents** (future feature)

Results are merged and ranked by similarity score.

## Configuration

### Default Settings
- **Top K**: 5 chunks
- **Similarity Threshold**: 0.7
- **Chunk Size**: 1000 characters
- **Overlap**: 200 characters

### Bot Settings Override
If using a RAG-enabled bot, its settings override defaults:
- Uses bot's `rag_top_k`
- Uses bot's `rag_similarity_threshold`

## Testing

### Test Conversation-Level RAG
1. Start a new conversation (any model)
2. Click upload button (⬆️)
3. Select "Upload Document"
4. Upload a .txt file
5. Ask a question about the content
6. Verify response uses the document

### Test Mixed Sources
1. Create RAG-enabled bot with documents
2. Start conversation with that bot
3. Upload additional document in chat
4. Ask question requiring both sources
5. Verify both are used

## Limitations

- Still only supports .txt files
- No document management UI for conversation docs yet
- Can't view conversation documents (only bot documents)

## Future Enhancements

- [ ] Document management for conversations
- [ ] View uploaded conversation documents
- [ ] Delete conversation documents
- [ ] PDF/DOCX support
- [ ] User-level document library
- [ ] Document sharing between conversations

---

**Status**: ✅ Complete and Deployed
**Migration**: ✅ Run `migrate_rag_conversation_level.py`
**Impact**: RAG now works universally across all conversations!
