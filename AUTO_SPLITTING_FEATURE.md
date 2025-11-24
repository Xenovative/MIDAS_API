# Automatic Document Splitting Feature

## Overview

Large documents (> 2MB) are now **automatically split** into smaller, manageable parts during upload. This happens transparently - you upload one file, the system handles the splitting!

## How It Works

### Automatic Detection

```
Upload file → Parse content → Check size

If size > 2MB:
  ✅ Auto-split into parts
  ✅ Upload each part
  ✅ All parts searchable
  
If size < 2MB:
  ✅ Upload normally
```

### Splitting Strategy

**1. Target Size: 1.5MB per part**
- Optimal for processing speed
- Good balance of context and performance

**2. Smart Boundaries**
- Tries to break at paragraph boundaries (\\n\\n)
- Falls back to sentence boundaries
- Maintains context with 5000-char overlap

**3. Part Naming**
```
Original: large_document.pdf
Parts:
  - large_document_part1of3.pdf
  - large_document_part2of3.pdf
  - large_document_part3of3.pdf
```

## Example Scenarios

### Scenario 1: Small Document (< 2MB)

```
Upload: report.pdf (500KB text)
Result: 
  ✅ Uploaded as single document
  ✅ No splitting needed
  ✅ Fast processing
```

### Scenario 2: Large Document (2-6MB)

```
Upload: thesis.pdf (4MB text)
System:
  📊 Large document detected (4.00MB) - auto-splitting enabled
  📄 Splitting large document (4,194,304 chars) into 3 parts
  ✂️  Part 1/3: 1,500,000 chars (thesis_part1of3.pdf)
  ✂️  Part 2/3: 1,500,000 chars (thesis_part2of3.pdf)
  ✂️  Part 3/3: 1,194,304 chars (thesis_part3of3.pdf)
  ✅ Split into 3 parts
  
  [Processing each part...]
  ✅ Uploaded part 1/3
  ✅ Uploaded part 2/3
  ✅ Uploaded part 3/3
  ✅ All 3 parts uploaded successfully
```

### Scenario 3: Very Large Document (6-10MB)

```
Upload: book.pdf (8MB text)
System:
  📊 Large document detected (8.00MB) - auto-splitting enabled
  📄 Splitting large document (8,388,608 chars) into 6 parts
  ✂️  Part 1/6: 1,500,000 chars
  ✂️  Part 2/6: 1,500,000 chars
  ✂️  Part 3/6: 1,500,000 chars
  ✂️  Part 4/6: 1,500,000 chars
  ✂️  Part 5/6: 1,500,000 chars
  ✂️  Part 6/6: 1,388,608 chars
  ✅ Split into 6 parts
  
  [Processing each part...]
  ✅ All 6 parts uploaded successfully
```

### Scenario 4: Too Large (> 10MB)

```
Upload: encyclopedia.pdf (15MB text)
System:
  ❌ Document too large (15.00MB). Maximum size is 10MB.
  
Solution: Split manually before uploading
```

## Benefits

### ✅ For Users

**1. No Manual Work**
- Upload large files directly
- System handles splitting
- No need for external tools

**2. Better Performance**
- Smaller parts = faster processing
- Parallel processing possible
- Less memory usage

**3. Seamless Search**
- All parts indexed together
- Search across entire document
- Results from any part

### ✅ For System

**1. Memory Efficiency**
- Process smaller chunks
- Avoid OOM errors
- Stable performance

**2. Faster Processing**
- Each part processes independently
- Better batch sizes
- Optimal API usage

**3. Reliability**
- If one part fails, others succeed
- Partial uploads possible
- Better error recovery

## Technical Details

### Splitting Algorithm

```python
def split_document(text, target_size=1_500_000, overlap=5000):
    parts = []
    start = 0
    
    while start < len(text):
        end = start + target_size
        
        # Find paragraph boundary
        para_break = text.rfind('\n\n', start, end)
        if para_break > start + target_size * 0.8:
            end = para_break + 2
        else:
            # Find sentence boundary
            for punct in ['. \n', '.\n', '. ']:
                sent_break = text.rfind(punct, end - 1000, end)
                if sent_break != -1:
                    end = sent_break + len(punct)
                    break
        
        parts.append(text[start:end])
        start = end - overlap  # 5000 char overlap
    
    return parts
```

### Overlap Strategy

**Why 5000 chars overlap?**
- Prevents context loss at boundaries
- Ensures sentences aren't cut off
- Maintains semantic continuity
- Small enough to not waste space

**Example:**
```
Part 1: chars 0 - 1,500,000
Part 2: chars 1,495,000 - 2,995,000  (5000 overlap)
Part 3: chars 2,990,000 - 4,194,304  (5000 overlap)
```

### Part Metadata

Each part stores:
```python
{
    'filename': 'doc_part1of3.pdf',
    'content': '...',
    'part_number': 1,
    'total_parts': 3,
    'start_char': 0,
    'end_char': 1500000,
    'size': 1500000
}
```

## Size Limits

### Thresholds

| Size | Behavior |
|------|----------|
| < 1MB | Normal upload, no warnings |
| 1-2MB | Normal upload, performance warning |
| 2-10MB | **Auto-split** into parts |
| > 10MB | Rejected (too large) |

### Part Sizes

| Document Size | Parts | Part Size |
|--------------|-------|-----------|
| 2MB | 2 | ~1MB each |
| 4MB | 3 | ~1.5MB each |
| 6MB | 4 | ~1.5MB each |
| 8MB | 6 | ~1.5MB each |
| 10MB | 7 | ~1.5MB each |

## Search Behavior

### Unified Search

**All parts are searchable as one document:**

```python
# User uploads: book.pdf (8MB, split into 6 parts)
# System creates:
#   - book_part1of6.pdf
#   - book_part2of6.pdf
#   - ...
#   - book_part6of6.pdf

# User searches: "quantum mechanics"
# System searches ALL parts
# Returns relevant chunks from ANY part
```

### Search Results

```python
# Example search result:
{
    "chunk_id": "abc123",
    "document_id": "doc456",
    "filename": "book_part3of6.pdf",  # Shows which part
    "content": "...quantum mechanics...",
    "similarity": 0.92,
    "chunk_index": 45
}
```

## Console Output

### Normal Upload (< 2MB)

```
📤 Starting upload: report.pdf
📖 File read: 524288 bytes
📝 Document parsed: 500000 characters
📄 Starting to split document: 500000 characters
  Estimated chunks: ~625
✂️  Document split into 625 chunks
✅ Added document 'report.pdf' with 625 chunks
```

### Auto-Split Upload (> 2MB)

```
📤 Starting upload: thesis.pdf
📖 File read: 4194304 bytes
📝 Document parsed: 4000000 characters
📊 Large document detected (3.81MB) - auto-splitting enabled
📄 Splitting large document (4,000,000 chars) into 3 parts
  ✂️  Part 1/3: 1,500,000 chars (thesis_part1of3.pdf)
  ✂️  Part 2/3: 1,500,000 chars (thesis_part2of3.pdf)
  ✂️  Part 3/3: 1,000,000 chars (thesis_part3of3.pdf)
✅ Split into 3 parts

[Processing Part 1/3]
============================================================
📄 Processing thesis_part1of3.pdf: 1875 chunks
============================================================
  ⏱️  Embedding generation took 8.23s for 20 chunks
  ✓ Batch 1/94: 20/1875 chunks
  ...
✅ Added document 'thesis_part1of3.pdf' with 1875 chunks
✅ Uploaded part 1/3

[Processing Part 2/3]
...
✅ Uploaded part 2/3

[Processing Part 3/3]
...
✅ Uploaded part 3/3

✅ All 3 parts uploaded successfully
```

## Configuration

### Adjustable Parameters

**In `backend/document_splitter.py`:**

```python
# Maximum size before splitting (default 2MB)
max_size = 2_000_000  # 2MB

# Target size per part (default 1.5MB)
target_size = 1_500_000  # 1.5MB

# Overlap between parts (default 5000 chars)
overlap = 5000  # 5KB
```

### Custom Settings

**For faster processing (smaller parts):**
```python
target_size = 1_000_000  # 1MB parts
# More parts, faster per-part processing
```

**For fewer parts (larger parts):**
```python
target_size = 2_000_000  # 2MB parts
# Fewer parts, slower per-part processing
```

## Limitations

### Current Limitations

1. **No manual control** - Splitting is automatic
2. **Fixed thresholds** - 2MB trigger, 1.5MB parts
3. **All or nothing** - Can't split some parts differently
4. **Part naming** - Automatic naming only

### Future Enhancements

- [ ] User-configurable split size
- [ ] Manual split points
- [ ] Custom part naming
- [ ] Split by chapters/sections
- [ ] Merge parts after upload
- [ ] Progress per part

## FAQ

### Q: Can I disable auto-splitting?

**A:** Not currently. Documents > 2MB are always split. This ensures reliable processing.

### Q: Can I see all parts in the UI?

**A:** Yes, each part appears as a separate document in the document list with its part number.

### Q: Does splitting affect search quality?

**A:** No! All parts are searched together. The 5000-char overlap ensures no context is lost at boundaries.

### Q: What if one part fails to upload?

**A:** Other parts still succeed. You can re-upload the file to retry failed parts.

### Q: Can I upload parts manually?

**A:** Yes, but auto-splitting is recommended for consistency.

## Summary

### Key Points

✅ **Automatic** - No user action needed
✅ **Smart** - Breaks at natural boundaries
✅ **Efficient** - 1.5MB parts for optimal processing
✅ **Seamless** - All parts searchable as one
✅ **Reliable** - Better error handling
✅ **Fast** - Smaller parts = faster processing

### When It Activates

- Document text > 2MB
- Automatically splits into ~1.5MB parts
- Each part processed independently
- All parts indexed together

### Result

**Upload one large file → Get multiple optimized parts → Search as one unified document!** 🎉

---

**Status**: ✅ Implemented
**Trigger**: Documents > 2MB
**Part Size**: ~1.5MB each
**Overlap**: 5000 characters
**Max Size**: 10MB total
