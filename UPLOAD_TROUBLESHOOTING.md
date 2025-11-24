# Upload Troubleshooting Guide

## Quick Diagnosis

### Stuck at 0% (Chunking Phase)

**Symptoms:**
```
📊 Progress: 0% - Splitting document into chunks...
[No updates for 5+ minutes]
```

**Likely Causes:**
1. Document is very large (> 1MB text)
2. Chunking is slow but working
3. No progress updates yet

**Solutions:**
1. **Wait and watch backend console** - Look for chunking progress
2. **Check document size** - If > 5MB, will take several minutes
3. **Restart if > 10 minutes** - Something is wrong

### Stuck at 10% (Before First Batch)

**Symptoms:**
```
📊 Progress: 10% - Processing 500 chunks in batches...
[No updates for 2+ minutes]
```

**Likely Causes:**
1. First OpenAI API call is slow
2. Network latency
3. OpenAI rate limiting

**Solutions:**
1. **Wait 15-30 seconds** - First batch takes longest
2. **Check internet connection**
3. **Check OpenAI API status**

### Stuck Mid-Upload (e.g., 45%)

**Symptoms:**
```
📊 Progress: 45% - Batch 5/10 complete...
[No updates for 2+ minutes]
```

**Likely Causes:**
1. OpenAI API timeout
2. Network issue
3. Memory issue

**Solutions:**
1. **Wait 30 seconds** - May be slow batch
2. **Check backend console** for errors
3. **Restart if frozen**

## Common Issues

### Issue 1: Out of Memory

**Error:**
```
MemoryError: Unable to allocate array
```

**Cause:**
- Document too large
- Batch size too high
- System low on RAM

**Solution:**
```python
# Already reduced to batch_size=20
# If still failing, document is too large
# Split document into smaller files
```

### Issue 2: OpenAI API Timeout

**Error:**
```
httpx.ReadTimeout: timed out
```

**Cause:**
- OpenAI API slow
- Network issues
- Large batch

**Solution:**
- Automatic retry (built-in)
- Wait and it will continue
- Check OpenAI status page

### Issue 3: Document Too Large

**Error:**
```
Document too large (14.53MB). Maximum size is 10MB.
```

**Cause:**
- Document exceeds 10MB limit

**Solution:**
1. Split document into smaller files
2. Upload separately
3. Each file should be < 5MB ideally

### Issue 4: No Progress in Frontend

**Symptoms:**
- Progress bar stuck
- No status updates
- But backend shows progress

**Cause:**
- SSE connection issue
- Browser not receiving updates

**Solution:**
1. Refresh page
2. Try different browser
3. Check browser console for errors

### Issue 5: Upload Completes but No Success Message

**Symptoms:**
- Progress reaches 100%
- No "Complete!" message
- Document not in list

**Cause:**
- Database commit failed
- Error during finalization

**Solution:**
1. Check backend console for errors
2. Refresh document list
3. Try uploading again

## Step-by-Step Debugging

### Step 1: Check Backend Console

**What to look for:**
```
✅ Good signs:
- 📄 Starting to split document...
- Chunking progress: X/Y chunks
- ✂️  Document split into X chunks
- ⏱️  Embedding generation took X.XXs
- ✓ Batch X/Y complete

❌ Bad signs:
- Traceback (error)
- MemoryError
- Timeout errors
- No output for > 5 minutes
```

### Step 2: Check Document Size

**In backend console:**
```
📄 Starting to split document: 318234 characters

# Calculate MB:
318234 / 1024 / 1024 = 0.30 MB ✅ OK

# If > 5MB:
⚠️  Large text content: 5.23MB - processing will be slow

# If > 10MB:
❌ Document too large (14.53MB). Maximum size is 10MB.
```

### Step 3: Check Progress Updates

**Expected timeline:**
```
0:00 - 0% Splitting document
0:05 - 10% Processing chunks in batches
0:15 - 15% Batch 1 complete
0:25 - 20% Batch 2 complete
...
2:00 - 100% Complete!
```

**If stuck:**
- Wait 2x expected time
- Check backend for errors
- Restart if no progress

### Step 4: Check System Resources

**Windows Task Manager:**
```
1. Open Task Manager (Ctrl+Shift+Esc)
2. Find python.exe process
3. Check:
   - CPU: Should be 10-30%
   - Memory: Should be < 500MB
   - Disk: Should be minimal

If Memory > 1GB:
- Document too large
- Memory leak
- Restart server
```

### Step 5: Check Network

**Test OpenAI API:**
```bash
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer YOUR_API_KEY"

# Should return list of models
# If timeout or error, network issue
```

## Recovery Procedures

### Procedure 1: Restart Upload

1. Stop upload (refresh page)
2. Check backend console for errors
3. Restart servers if needed
4. Try uploading again

### Procedure 2: Split Document

1. Use PDF splitter tool
2. Split into < 5MB chunks
3. Upload each separately
4. All will be searchable

### Procedure 3: Reduce Batch Size

**Edit `backend/routes/documents.py`:**
```python
# Line 147 and 227
batch_size=10  # Reduce from 20 to 10
```

**Restart server and try again**

### Procedure 4: Clear Database

**If document partially uploaded:**
```python
# In Python console:
from backend.database import SessionLocal
from backend.models import Document

db = SessionLocal()
# Find and delete stuck document
doc = db.query(Document).filter_by(filename="stuck.pdf").first()
if doc:
    db.delete(doc)
    db.commit()
```

## Prevention

### Before Uploading

**Check document:**
1. File size < 5MB (ideal)
2. File format supported (.txt, .pdf, .docx, .json)
3. File not corrupted
4. Good internet connection

**Prepare system:**
1. Close other applications
2. Ensure stable internet
3. Keep backend console visible
4. Don't navigate away during upload

### During Upload

**Do:**
- Watch backend console
- Wait for progress updates
- Be patient (2-5 minutes normal)

**Don't:**
- Close browser tab
- Refresh page
- Upload multiple files simultaneously
- Navigate away

### After Upload

**Verify:**
1. "Complete!" message appears
2. Document in list
3. Can search/query document
4. No errors in console

## Getting Help

### Information to Provide

1. **Document details:**
   - File size
   - File format
   - Number of pages

2. **Error messages:**
   - From backend console
   - From browser console
   - Full error text

3. **Progress state:**
   - Where it got stuck (%)
   - How long waited
   - Last status message

4. **System info:**
   - OS version
   - Python version
   - Available RAM

### Where to Report

1. Check backend console first
2. Check browser console (F12)
3. Copy full error messages
4. Include document size
5. Report with context

---

**Remember**: 
- Most uploads take 2-5 minutes
- Large documents (> 2MB) take longer
- Progress updates every 8-15 seconds
- Be patient and watch console!
