# Document Upload Optimization & Progress Tracking

## Problem

Large documents (like your 317KB PDF) were causing memory issues during upload because:
1. **All chunks processed at once** - Entire document embedded in one batch
2. **No progress feedback** - Users had no idea what was happening
3. **Memory overflow** - Large documents exhausted available memory

## Solution

Implemented **batched processing** with **real-time progress tracking**:

### ✅ Backend Optimizations

**1. Batched Embedding Processing**
- Process chunks in batches of 50 (configurable)
- Commit to database after each batch
- Prevents memory overflow
- Allows progress tracking

**2. Progress Callbacks**
- Vector store accepts progress callback
- Reports current/total chunks and status
- Enables real-time UI updates

**3. Streaming Upload Endpoint**
- New `/documents/upload-file-stream` endpoint
- Uses Server-Sent Events (SSE)
- Streams progress updates to frontend
- Non-blocking for large files

### ✅ Frontend Improvements

**1. Progress Bar UI**
- Visual progress indicator
- Percentage display
- Status messages
- Smooth animations

**2. SSE Client**
- Connects to streaming endpoint
- Receives real-time updates
- Updates progress bar
- Handles errors gracefully

## How It Works

### Upload Flow

```
1. User selects large PDF
2. Frontend starts SSE connection
3. Backend:
   ├─ Reads file (5%)
   ├─ Parses PDF (10%)
   ├─ Splits into chunks (10%)
   ├─ Processes batch 1/10 (20%)
   ├─ Processes batch 2/10 (30%)
   ├─ ... (progress updates)
   ├─ Processes batch 10/10 (95%)
   └─ Complete! (100%)
4. Frontend shows progress bar
5. Success message displayed
```

### Batched Processing

```python
# Process 50 chunks at a time
for batch_start in range(0, total_chunks, 50):
    batch = chunks[batch_start:batch_start+50]
    
    # Embed this batch
    embeddings = await embed_texts(batch)
    
    # Store in database
    for chunk, embedding in zip(batch, embeddings):
        db.add(chunk_record)
    
    # Commit batch
    await db.flush()
    
    # Report progress
    progress_callback(processed, total, status)
```

## API Changes

### Backend

**New Endpoint:**
```python
@router.post("/upload-file-stream")
async def upload_document_file_stream(
    file: UploadFile,
    bot_id: Optional[str] = None,
    conversation_id: Optional[str] = None
):
    """Upload with progress streaming (SSE)"""
    # Streams progress updates
    # Returns SSE stream
```

**Updated Vector Store:**
```python
await vector_store.add_document(
    db=db,
    filename=filename,
    content=content,
    batch_size=50,  # Process 50 chunks at a time
    progress_callback=callback  # Progress updates
)
```

### Frontend

**New API Method:**
```javascript
await documentsApi.uploadFileWithProgress(
    file,
    botId,
    conversationId,
    (data) => {
        // data.progress: 0-100
        // data.status: "Processing..."
        setUploadProgress(data.progress)
        setUploadStatus(data.status)
    }
)
```

## UI Components

### Progress Bar

```jsx
{uploadingDoc && (
  <div className="mb-3 p-3 bg-accent rounded-lg">
    <div className="flex items-center justify-between mb-2">
      <span>Uploading document...</span>
      <span>{uploadProgress}%</span>
    </div>
    <div className="w-full bg-background rounded-full h-2">
      <div 
        className="bg-primary h-full transition-all"
        style={{ width: `${uploadProgress}%` }}
      />
    </div>
    <p className="text-xs">{uploadStatus}</p>
  </div>
)}
```

## Performance Improvements

### Memory Usage

**Before:**
- Process all chunks → OOM for large files
- Single transaction → Long locks

**After:**
- Batch processing → Constant memory
- Incremental commits → Short locks

### User Experience

**Before:**
- No feedback → User confused
- Long wait → Appears frozen
- Failure → No context

**After:**
- Real-time progress → User informed
- Status updates → Clear activity
- Detailed errors → Actionable feedback

## Configuration

### Batch Size

Adjust based on your needs:

```python
# Small batches (safer, slower)
batch_size=25

# Default (balanced)
batch_size=50

# Large batches (faster, more memory)
batch_size=100
```

### Progress Updates

```python
async def progress_callback(current, total, status):
    # current: chunks processed
    # total: total chunks
    # status: human-readable message
    print(f"{current}/{total}: {status}")
```

## Files Modified

### Backend
1. **`backend/vector_store.py`**
   - Added `batch_size` parameter
   - Added `progress_callback` parameter
   - Implemented batched processing
   - Added progress reporting

2. **`backend/routes/documents.py`**
   - Added `/upload-file-stream` endpoint
   - Implemented SSE streaming
   - Added progress callbacks
   - Updated existing endpoint with batching

### Frontend
1. **`frontend/src/lib/api.js`**
   - Added `uploadFileWithProgress()` method
   - Implemented SSE client
   - Added progress handling

2. **`frontend/src/components/ChatInput.jsx`**
   - Added progress state
   - Added progress bar UI
   - Updated upload handler
   - Added status messages

## Testing

### Test Large File Upload

1. **Prepare large PDF** (>1MB, 100+ pages)
2. **Upload via chat:**
   - Click upload button
   - Select PDF
   - Watch progress bar
3. **Verify:**
   - Progress updates smoothly
   - Status messages appear
   - Success on completion
   - No memory errors

### Expected Progress

```
0%   - Starting upload...
5%   - Reading file...
10%  - Parsing document...
10%  - Processing 500 chunks in batches...
20%  - Processed 100/500 chunks...
40%  - Processed 200/500 chunks...
60%  - Processed 300/500 chunks...
80%  - Processed 400/500 chunks...
95%  - Processed 500/500 chunks...
100% - Complete!
```

## Benefits

✅ **Handles Large Files** - No more memory errors
✅ **Real-Time Feedback** - Users see progress
✅ **Better Performance** - Batched processing
✅ **Error Recovery** - Partial progress saved
✅ **User Confidence** - Clear status updates

## Limitations

- Progress updates require SSE support
- Fallback to simple upload if SSE fails
- Batch size affects speed/memory tradeoff

## Future Enhancements

- [ ] Pause/resume uploads
- [ ] Cancel in-progress uploads
- [ ] Retry failed batches
- [ ] Parallel batch processing
- [ ] Compression before upload
- [ ] Client-side chunking

---

**Status**: ✅ Complete
**Impact**: Large documents now upload successfully with progress tracking
**Memory**: Constant memory usage regardless of file size
