# RAG Quick Start Guide

## 🚀 Get Started in 5 Minutes

### Step 1: Create a RAG-Enabled Bot

1. Open the **Bot Manager** (click the bot icon in the sidebar)
2. Click **"Create Bot"**
3. Fill in the basics:
   - **Name**: "Support Bot"
   - **System Prompt**: "You are a helpful support assistant. Use the knowledge base to answer questions accurately."
4. Scroll down to **"Enable RAG (Knowledge Base)"**
5. Check the box ✅
6. Adjust settings:
   - **Top K Results**: 5 (how many chunks to retrieve)
   - **Similarity Threshold**: 0.70 (minimum match quality)
7. Click **"Create"**

### Step 2: Upload Documents

1. Find your new bot in the list
2. Click the **📄 Document icon**
3. Choose upload method:
   - **Upload File**: Select a .txt file
   - **Paste Text**: Enter filename and paste content
4. Click upload
5. Wait for processing (documents are chunked and embedded)

### Step 3: Test Your Knowledge Base

1. In the Document Manager, find **"Test Search"**
2. Enter a test query: "How do I reset the device?"
3. Click **"Search"**
4. Review results:
   - See which chunks were retrieved
   - Check similarity scores
   - Verify content relevance

### Step 4: Chat with Your Bot

1. Close the Document Manager
2. Click the **💬 Chat icon** on your bot
3. Start asking questions!
4. The bot will automatically:
   - Search the knowledge base
   - Retrieve relevant chunks
   - Generate informed responses

## 📊 Example Use Case

### Customer Support Bot

**Documents to Upload:**
- `product-manual.txt` - Product specifications and features
- `troubleshooting-guide.txt` - Common issues and solutions
- `faq.txt` - Frequently asked questions
- `warranty-info.txt` - Warranty terms and conditions

**System Prompt:**
```
You are a customer support assistant for [Product Name]. 
Use the knowledge base to provide accurate answers to customer questions.
If you don't find the answer in the knowledge base, say so clearly.
Always be helpful and professional.
```

**Settings:**
- Top K: 5 (retrieve 5 most relevant chunks)
- Similarity: 0.70 (70% match threshold)

**Example Conversation:**
```
User: How do I reset my device?

Bot: According to the troubleshooting guide, here's how to reset your device:
1. Press and hold the power button for 10 seconds
2. Wait for the device to power off completely
3. Press the power button again to restart

If this doesn't work, you may need to perform a factory reset. Would you like instructions for that?
```

## 🎯 Tips for Best Results

### Document Quality
- ✅ Use well-structured text
- ✅ Include clear headings and sections
- ✅ Keep information accurate and up-to-date
- ❌ Avoid very short documents (less than 100 words)
- ❌ Don't upload duplicate information

### Chunk Size
- Default: 1000 characters with 200 overlap
- Works well for most documents
- Adjust in backend if needed for specific use cases

### Top K Setting
- **Low (1-3)**: Very focused, precise answers
- **Medium (4-6)**: Balanced, recommended for most cases
- **High (7-10)**: Broader context, good for complex queries

### Similarity Threshold
- **High (0.80-0.95)**: Only very relevant chunks
- **Medium (0.65-0.80)**: Balanced, recommended
- **Low (0.50-0.65)**: More results, less precise

## 🔧 Troubleshooting

### "No relevant information found"
- **Cause**: Similarity threshold too high or documents don't contain relevant info
- **Solution**: Lower similarity threshold or upload more comprehensive documents

### Bot gives generic answers
- **Cause**: RAG not enabled or no documents uploaded
- **Solution**: Verify RAG checkbox is enabled and documents are uploaded

### Search returns too many irrelevant results
- **Cause**: Similarity threshold too low
- **Solution**: Increase similarity threshold to 0.75 or higher

### Upload fails
- **Cause**: File not UTF-8 encoded or not a text file
- **Solution**: Ensure file is .txt and UTF-8 encoded

## 📝 Supported File Formats

Currently supported:
- ✅ `.txt` files (UTF-8 encoded)

Coming soon:
- 📄 PDF files
- 📄 DOCX files
- 📄 Markdown files
- 📄 CSV files

## 🎨 UI Elements Explained

### Bot Card Icons
- **📚 RAG Enabled**: This bot has a knowledge base
- **📄 Document Icon**: Manage documents (only on RAG bots)
- **💬 Chat Icon**: Start chatting with the bot
- **✏️ Edit Icon**: Edit bot settings
- **🗑️ Delete Icon**: Delete the bot

### Document Manager Sections
- **⬆️ Upload Document**: Add new documents
- **🔍 Test Search**: Verify retrieval quality
- **📄 Documents**: View and manage uploaded docs
- **⚙️ RAG Configuration**: View current settings

## 🌟 Advanced Features

### Multiple Documents
- Upload multiple documents per bot
- All documents are searched together
- More documents = more comprehensive knowledge

### Search Testing
- Test queries before chatting
- See exactly what the bot will retrieve
- Validate document quality and settings

### Real-time Updates
- Documents processed immediately
- Changes take effect instantly
- No restart required

## 📈 Best Practices

1. **Start Small**: Upload 2-3 documents first, test, then add more
2. **Test Thoroughly**: Use test search to validate retrieval
3. **Iterate Settings**: Adjust Top K and threshold based on results
4. **Update Regularly**: Keep documents current and accurate
5. **Monitor Performance**: Check if bot answers are improving

## 🎓 Learning Resources

- **RAG_GUIDE.md**: Comprehensive technical guide
- **RAG_IMPLEMENTATION_SUMMARY.md**: Backend architecture
- **FRONTEND_RAG_SUMMARY.md**: Frontend implementation details

## 🆘 Need Help?

Common questions:
- **Q**: Can I upload PDFs?
  - **A**: Not yet, only .txt files currently supported

- **Q**: How many documents can I upload?
  - **A**: No hard limit, but performance may vary with very large knowledge bases

- **Q**: Can I update a document?
  - **A**: Delete the old version and upload the new one

- **Q**: Does RAG work with streaming?
  - **A**: Yes! RAG context is injected before streaming starts

## ✅ Checklist

Before going live:
- [ ] Bot created with RAG enabled
- [ ] Documents uploaded and processed
- [ ] Test search validates retrieval quality
- [ ] System prompt instructs bot to use knowledge base
- [ ] Settings tuned (Top K, threshold)
- [ ] Test conversations confirm RAG is working
- [ ] Documents are accurate and up-to-date

---

**Ready to build knowledge-enhanced bots!** 🚀
