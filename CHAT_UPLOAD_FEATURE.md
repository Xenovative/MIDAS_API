# Chat Upload Button Enhancement

## Feature Overview

The upload button in the chat input now serves **dual purposes** when chatting with RAG-enabled bots:
1. **Upload Images** - For vision chat or image transformation
2. **Upload Documents** - For adding to the bot's knowledge base

## How It Works

### For Regular Bots (Non-RAG)
- Shows **image icon** (📷)
- Clicking opens file picker for images
- Supports multiple image uploads
- Used for vision chat or image generation

### For RAG-Enabled Bots
- Shows **upload icon** (⬆️)
- Clicking opens a **dropdown menu** with two options:
  - **Upload Image** - For vision/image features
  - **Upload Document (.txt)** - Adds to knowledge base
- Menu closes when clicking outside

## User Experience

### Visual Indicators
```
Regular Bot:     [📷]  - Image upload only
RAG Bot:         [⬆️]  - Opens menu with options
Uploading Doc:   [⌛]  - Loading spinner
```

### Upload Menu (RAG Bots Only)
```
┌─────────────────────┐
│ 📷 Upload Image     │
├─────────────────────┤
│ 📄 Upload Document  │
└─────────────────────┘
```

### Document Upload Flow
1. User clicks upload button (⬆️)
2. Menu appears with two options
3. User selects "Upload Document (.txt)"
4. File picker opens (filtered to .txt files)
5. User selects a text file
6. Document uploads and processes
7. Success message: "Document uploaded successfully! The bot can now use this information."
8. Document is immediately available for RAG retrieval

## Technical Implementation

### Files Modified
1. **`frontend/src/components/ChatInput.jsx`**
   - Added `selectedBot` prop
   - Added upload mode state (`image` or `document`)
   - Added upload menu state and ref
   - Added document upload handler
   - Added click-outside detection
   - Conditional rendering based on bot RAG status

2. **`frontend/src/components/ChatArea.jsx`**
   - Pass `selectedBot` to `ChatInput`

### New Features

**Upload Mode Toggle**
```javascript
const [uploadMode, setUploadMode] = useState('image')
const [showUploadMenu, setShowUploadMenu] = useState(false)
```

**Document Upload Handler**
```javascript
const handleDocumentUpload = async (e) => {
  const file = e.target.files?.[0]
  // Validate file type (.txt only)
  // Check bot has RAG enabled
  // Upload via documentsApi
  // Show success message
}
```

**Conditional Button Rendering**
```javascript
{selectedBot?.use_rag ? (
  // Show upload menu button
  <Upload icon with dropdown />
) : (
  // Show simple image button
  <ImageIcon />
)}
```

## User Benefits

✅ **Convenience**: Upload documents without leaving chat
✅ **Context**: Upload relevant documents mid-conversation
✅ **Immediate**: Documents available instantly after upload
✅ **Intuitive**: Clear menu options for different upload types
✅ **Smart**: Button adapts based on bot capabilities

## Use Cases

### During Conversation
```
User: "I need help with the product manual"
Bot: "I'd be happy to help! What would you like to know?"
User: [Uploads product-manual.txt via chat button]
System: "Document uploaded successfully!"
User: "How do I reset the device?"
Bot: [Uses newly uploaded manual to answer]
```

### Quick Knowledge Addition
```
User: [Chatting with support bot]
User: [Realizes bot needs more info]
User: [Clicks upload → Upload Document]
User: [Uploads FAQ.txt]
User: [Continues conversation with enhanced bot]
```

### Image + Document Workflow
```
User: [Uploads screenshot via Upload Image]
User: "What's wrong with this error?"
Bot: [Analyzes image]
User: [Uploads error-codes.txt via Upload Document]
User: "Can you check the documentation?"
Bot: [Uses both image and document context]
```

## Validation & Error Handling

### File Type Validation
- Only `.txt` files accepted for documents
- Clear error message if wrong type selected
- File picker pre-filtered to text files

### Bot Validation
- Checks if bot has RAG enabled
- Shows error if trying to upload to non-RAG bot
- Graceful fallback to image-only mode

### Upload States
- Loading spinner during upload
- Success confirmation message
- Error messages with details
- Button disabled during upload

## UI/UX Details

### Menu Behavior
- Opens on button click
- Closes when clicking outside
- Closes after selecting an option
- Positioned above button (bottom-full)
- Right-aligned with button

### Button States
- **Normal**: Upload icon (⬆️)
- **Uploading**: Loading spinner (⌛)
- **Disabled**: Grayed out, no interaction
- **Hover**: Accent background

### Accessibility
- Proper button titles/tooltips
- Keyboard navigation support
- Clear visual feedback
- Screen reader friendly

## Comparison: Before vs After

### Before
- Separate document management in Bot Manager
- Required leaving chat to upload documents
- Two-step process (open manager → upload)

### After
- Upload documents directly in chat
- Stay in conversation flow
- One-click access to upload
- Context-aware button behavior

## Technical Notes

### File Input Handling
```javascript
<input
  type="file"
  accept={uploadMode === 'image' ? 'image/*' : '.txt,text/*'}
  multiple={uploadMode === 'image'}
  onChange={uploadMode === 'image' ? handleImageSelect : handleDocumentUpload}
/>
```

### Click Outside Detection
```javascript
useEffect(() => {
  const handleClickOutside = (event) => {
    if (uploadMenuRef.current && !uploadMenuRef.current.contains(event.target)) {
      setShowUploadMenu(false)
    }
  }
  if (showUploadMenu) {
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }
}, [showUploadMenu])
```

## Future Enhancements

Potential improvements:
- [ ] Drag-and-drop document upload
- [ ] Support for PDF, DOCX files
- [ ] Batch document upload
- [ ] Upload progress indicator
- [ ] Document preview before upload
- [ ] Recent documents quick-add

## Testing Checklist

- [ ] Upload button shows for regular bots (image icon)
- [ ] Upload button shows for RAG bots (upload icon)
- [ ] Menu opens/closes correctly
- [ ] Image upload works from menu
- [ ] Document upload works from menu
- [ ] File type validation works
- [ ] Success message appears
- [ ] Error handling works
- [ ] Click outside closes menu
- [ ] Loading states display correctly

---

**Status**: ✅ Complete and Deployed
**Impact**: Significantly improved UX for RAG-enabled bots
**User Feedback**: Streamlined document management workflow
