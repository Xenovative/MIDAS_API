# Multi-Format Document Support

## Overview

RAG now supports **multiple document formats** beyond plain text files!

## Supported Formats

✅ **TXT** - Plain text files
✅ **PDF** - Portable Document Format
✅ **DOC/DOCX** - Microsoft Word documents
✅ **JSON** - JSON data files

## Features

### PDF Support
- Extracts text from all pages
- Preserves page structure
- Handles multi-page documents
- Page markers for reference

### Word Document Support
- Extracts paragraphs
- Extracts table content
- Handles both .doc and .docx
- Preserves document structure

### JSON Support
- Converts JSON to readable text
- Handles nested objects
- Handles arrays
- Formatted for LLM consumption

## Implementation

### Backend

**Document Parser** (`backend/document_parser.py`)
- Unified interface for all formats
- Format detection by extension
- Error handling for corrupt files
- Text extraction and formatting

**Libraries Used:**
- `PyPDF2` - PDF parsing
- `python-docx` - Word document parsing
- Built-in `json` - JSON parsing

### Frontend

**Updated Components:**
- `ChatInput.jsx` - Accepts multiple formats
- `DocumentManager.jsx` - Shows supported formats
- File validation for all formats

## Usage

### Upload via Chat
1. Click upload button (⬆️)
2. Select "Upload Document"
3. Choose any supported file:
   - `.txt` - Text file
   - `.pdf` - PDF document
   - `.docx` - Word document
   - `.json` - JSON file
4. File is parsed and processed
5. Content available for RAG

### Upload via Bot Manager
1. Open Document Manager for bot
2. Click "Upload File"
3. Select supported document
4. File parsed automatically

## Examples

### PDF Upload
```
User uploads: product-manual.pdf (50 pages)
System extracts: All text content with page markers
Result: "--- Page 1 ---\n[content]\n--- Page 2 ---\n[content]..."
```

### Word Document Upload
```
User uploads: company-policy.docx
System extracts: Paragraphs + tables
Result: Formatted text with table data preserved
```

### JSON Upload
```
User uploads: api-docs.json
System converts: JSON → readable text
Result: "endpoint: /api/users\n  method: GET\n  params: ..."
```

## File Validation

### Frontend Validation
- Checks file extension
- Shows error for unsupported formats
- Lists supported formats in error message

### Backend Validation
- Verifies file format
- Attempts to parse content
- Returns detailed error messages

## Error Handling

### Common Errors

**Unsupported Format**
```
Error: "Unsupported file format. Supported formats: txt, pdf, doc, docx, json"
```

**Corrupt PDF**
```
Error: "Failed to parse PDF: [details]"
```

**Invalid JSON**
```
Error: "Invalid JSON format: [details]"
```

**Encoding Issues**
```
Error: "File must be UTF-8 encoded text"
```

## Technical Details

### PDF Parsing
```python
# Extracts text page by page
pdf_reader = PyPDF2.PdfReader(file)
for page in pdf_reader.pages:
    text = page.extract_text()
```

### Word Document Parsing
```python
# Extracts paragraphs and tables
doc = DocxDocument(file_path)
for para in doc.paragraphs:
    text_parts.append(para.text)
for table in doc.tables:
    # Extract table content
```

### JSON Parsing
```python
# Converts to readable format
data = json.load(file)
text = dict_to_text(data)  # Custom formatter
```

## Limitations

### PDF
- Text-based PDFs only (no OCR for scanned documents)
- Complex layouts may have formatting issues
- Images/graphics not extracted

### Word Documents
- .doc files require conversion (may have issues)
- Complex formatting may be lost
- Embedded objects not extracted

### JSON
- Very large JSON files may be slow
- Deeply nested structures converted to text
- Binary data not supported

## Future Enhancements

Potential additions:
- [ ] OCR for scanned PDFs
- [ ] Excel/CSV support
- [ ] Markdown files
- [ ] HTML files
- [ ] PowerPoint presentations
- [ ] Image text extraction
- [ ] Archive file support (.zip)

## Installation

Install required dependencies:
```bash
pip install PyPDF2==3.0.1 python-docx==1.1.0 python-magic-bin==0.4.14
```

Or install all requirements:
```bash
pip install -r requirements.txt
```

## Testing

### Test PDF Upload
1. Create a PDF with text content
2. Upload via chat or bot manager
3. Verify text extraction
4. Ask questions about content

### Test Word Document
1. Create a .docx with text and tables
2. Upload the document
3. Verify content extraction
4. Test RAG retrieval

### Test JSON
1. Create a JSON file with data
2. Upload the file
3. Verify conversion to text
4. Query the data

## Benefits

✅ **Versatility**: Support for common document formats
✅ **Convenience**: No need to convert to .txt
✅ **Automation**: Automatic format detection and parsing
✅ **Robustness**: Error handling for corrupt files
✅ **User-Friendly**: Clear error messages

## API Changes

### Upload Endpoint
```python
@router.post("/upload-file")
async def upload_document_file(
    file: UploadFile,
    bot_id: Optional[str] = None,
    conversation_id: Optional[str] = None
):
    # Check format support
    if not document_parser.is_supported(file.filename):
        raise HTTPException(...)
    
    # Parse content
    content = await file.read()
    text_content = document_parser.parse_bytes(content, file.filename)
    
    # Store in vector store
    await vector_store.add_document(...)
```

### Parser Interface
```python
# Parse from file path
text = document_parser.parse_file(path, filename)

# Parse from bytes
text = document_parser.parse_bytes(content, filename)

# Check support
is_supported = document_parser.is_supported(filename)

# Get supported formats
formats = document_parser.get_supported_extensions()
```

## UI Updates

### Upload Menu
```
┌─────────────────────────┐
│ 📷 Upload Image         │
├─────────────────────────┤
│ 📄 Upload Document      │
│    .txt, .pdf, .docx,   │
│    .json                │
└─────────────────────────┘
```

### File Input
```html
<input 
  type="file" 
  accept=".txt,.pdf,.doc,.docx,.json,
          application/pdf,
          application/msword,
          application/vnd.openxmlformats-officedocument.wordprocessingml.document,
          application/json"
/>
```

## Performance Considerations

- **PDF**: Parsing speed depends on page count
- **Word**: Generally fast for most documents
- **JSON**: Large files may take longer
- **Chunking**: All formats chunked the same way (1000 chars, 200 overlap)

## Security

- File type validation on frontend and backend
- Size limits enforced by FastAPI
- Content sanitization during parsing
- No executable code extraction

---

**Status**: ✅ Complete
**Formats**: TXT, PDF, DOC, DOCX, JSON
**Ready to Use**: Install dependencies and restart server
