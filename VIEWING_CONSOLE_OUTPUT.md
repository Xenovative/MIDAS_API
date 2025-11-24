# Viewing Console Output During Upload

## Where to Look

### Backend Console (Where Progress Shows)

When you run `./start.bat`, you should see **TWO console windows**:

1. **Backend Console** (Python/FastAPI) ← **LOOK HERE**
   - Shows upload progress
   - Shows batch processing
   - Shows timing information
   - Port 8000

2. **Frontend Console** (React/Vite)
   - Shows frontend build info
   - Shows HMR updates
   - Port 3000

## What You Should See

### During Upload

**Backend Console Output:**
```
============================================================
📄 Processing 漢語神學芻議.pdf: 320 chunks
============================================================
  ⏱️  Embedding generation took 8.23s for 20 chunks
  ✓ Batch 1/16: 20/320 chunks (took 8.45s)
📊 Progress: 15% - Batch 1/16: Generating embeddings for 20 chunks...
  ⏱️  Embedding generation took 7.89s for 20 chunks
  ✓ Batch 2/16: 40/320 chunks (took 8.12s) (ETA: ~120s)
📊 Progress: 20% - Batch 2/16 complete: 40/320 chunks processed (ETA: ~120s)
  ⏱️  Embedding generation took 8.01s for 20 chunks
  ✓ Batch 3/16: 60/320 chunks (took 8.23s) (ETA: ~105s)
📊 Progress: 25% - Batch 3/16 complete: 60/320 chunks processed (ETA: ~105s)
...
✅ Added document '漢語神學芻議.pdf' with 320 chunks
============================================================
```

### Before Upload Starts

**Backend Console:**
```
📤 Starting upload: 漢語神學芻議.pdf
📖 File read: 324567 bytes
📝 Document parsed: 318234 characters
⚠️  Large text content: 0.30MB - processing will be slow
```

## Troubleshooting

### Not Seeing Any Output?

**1. Check the Correct Console**
- Make sure you're looking at the **backend** console
- Not the frontend console
- Backend shows Python/FastAPI logs

**2. Console Might Be Minimized**
- Check taskbar for console windows
- Look for "python.exe" or "uvicorn" window

**3. Restart with Visible Console**
```bash
# Stop servers
# Press any key in start.bat window

# Start again
./start.bat

# Keep both console windows visible
```

### Output Appears Frozen?

**This is normal during embedding generation:**
- Each batch takes 5-15 seconds
- No output during API call
- Output appears after batch completes

**What's happening:**
```
[Silent for 8 seconds] ← Calling OpenAI API
⏱️  Embedding generation took 8.23s ← Output appears
```

### Want More Verbose Output?

**Add debug logging:**

Edit `backend/main.py`:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Expected Timeline

### For 320-chunk Document

```
0:00 - Upload starts
       📤 Starting upload: file.pdf

0:01 - File read and parsed
       📖 File read: 324567 bytes
       📝 Document parsed: 318234 characters

0:02 - First batch starts
       📄 Processing file.pdf: 320 chunks

0:10 - First batch completes
       ⏱️  Embedding generation took 8.23s
       ✓ Batch 1/16: 20/320 chunks

0:18 - Second batch completes
       ✓ Batch 2/16: 40/320 chunks (ETA: ~120s)

... (continues)

2:30 - All batches complete
       ✅ Added document 'file.pdf' with 320 chunks
```

## Console Commands

### View Backend Logs Only
```bash
# Windows
cd c:\AIapps\MIDAS_API
python -m uvicorn backend.main:app --reload
```

### Increase Log Verbosity
```bash
# Set environment variable
set PYTHONUNBUFFERED=1
./start.bat
```

### Save Logs to File
```bash
# Redirect output
python -m uvicorn backend.main:app --reload > backend.log 2>&1
```

## Visual Indicators

### Progress Symbols

- 📤 Upload started
- 📖 File read
- 📝 Document parsed
- ⚠️  Warning (large file)
- 📄 Processing started
- ⏱️  Timing information
- ✓ Batch completed
- 📊 Progress update
- ✅ Upload complete
- ❌ Error occurred

### Progress Format

```
============================================================
📄 Processing {filename}: {total_chunks} chunks
============================================================
  ⏱️  Embedding generation took {time}s for {count} chunks
  ✓ Batch {num}/{total}: {processed}/{total_chunks} chunks (took {time}s) (ETA: ~{eta}s)
📊 Progress: {percent}% - {status}
✅ Added document '{filename}' with {count} chunks
============================================================
```

## Frontend Progress Bar

While the backend console shows detailed logs, the **frontend** shows:

```
┌─────────────────────────────────────────┐
│ ⟳ Processing document...          45%  │
│ ████████████████░░░░░░░░░░░░░░░░        │
│ Batch 5/16: Generating embeddings for  │
│ chunks 81-100...                        │
└─────────────────────────────────────────┘
```

**Both should update together!**

## Common Issues

### Issue: No Console Output at All

**Solution:**
1. Check if backend is running
2. Look for error messages
3. Restart servers
4. Check Python version (should be 3.8+)

### Issue: Output Stops Mid-Upload

**Possible causes:**
- OpenAI API timeout (normal, will retry)
- Memory issue (check task manager)
- Network issue (check connection)

**What to do:**
- Wait 30 seconds
- Check if process is still running
- Look for error messages

### Issue: Output Too Fast to Read

**Solution:**
- Output is also logged to file
- Scroll up in console
- Use `> backend.log` to save logs

## Summary

### Where to Look
✅ **Backend console** (Python/FastAPI)
❌ Not frontend console (React/Vite)

### What to Expect
- Visual separators (====)
- Progress updates every 8-15 seconds
- Batch completion messages
- ETA calculations
- Final success message

### If Not Seeing Output
1. Check correct console window
2. Wait for first batch (takes 8-15s)
3. Restart servers if needed
4. Enable debug logging

---

**Tip**: Keep both console windows visible side-by-side to see backend logs and frontend UI simultaneously!
