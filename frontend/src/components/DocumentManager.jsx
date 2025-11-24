import { useState, useEffect } from 'react'
import { Upload, Trash2, X, FileText, Search, BookOpen } from 'lucide-react'
import { documentsApi } from '../lib/api'

export default function DocumentManager({ bot, onClose }) {
  const [documents, setDocuments] = useState([])
  const [loading, setLoading] = useState(true)
  const [uploading, setUploading] = useState(false)
  const [uploadMethod, setUploadMethod] = useState('file') // 'file' or 'text'
  const [textContent, setTextContent] = useState('')
  const [filename, setFilename] = useState('')
  const [searchQuery, setSearchQuery] = useState('')
  const [searchResults, setSearchResults] = useState(null)
  const [searching, setSearching] = useState(false)

  useEffect(() => {
    loadDocuments()
  }, [bot.id])

  const loadDocuments = async () => {
    try {
      setLoading(true)
      const response = await documentsApi.list(bot.id)
      setDocuments(response.data)
    } catch (error) {
      console.error('Failed to load documents:', error)
      alert('Failed to load documents: ' + (error.response?.data?.detail || error.message))
    } finally {
      setLoading(false)
    }
  }

  const handleFileUpload = async (event) => {
    const file = event.target.files?.[0]
    if (!file) return

    // Check file type
    const supportedExtensions = ['txt', 'pdf', 'doc', 'docx', 'json']
    const fileExtension = file.name.split('.').pop().toLowerCase()
    
    if (!supportedExtensions.includes(fileExtension)) {
      alert(`Unsupported file format. Please upload: ${supportedExtensions.join(', ')}`)
      return
    }

    try {
      setUploading(true)
      await documentsApi.uploadFile(bot.id, file)
      await loadDocuments()
      event.target.value = '' // Reset file input
    } catch (error) {
      console.error('Failed to upload file:', error)
      alert('Failed to upload file: ' + (error.response?.data?.detail || error.message))
    } finally {
      setUploading(false)
    }
  }

  const handleTextUpload = async () => {
    if (!textContent.trim() || !filename.trim()) {
      alert('Please provide both filename and content')
      return
    }

    try {
      setUploading(true)
      await documentsApi.upload({
        bot_id: bot.id,
        filename: filename.endsWith('.txt') ? filename : `${filename}.txt`,
        content: textContent
      })
      await loadDocuments()
      setTextContent('')
      setFilename('')
      setUploadMethod('file')
    } catch (error) {
      console.error('Failed to upload text:', error)
      alert('Failed to upload text: ' + (error.response?.data?.detail || error.message))
    } finally {
      setUploading(false)
    }
  }

  const handleDelete = async (documentId) => {
    if (!confirm('Are you sure you want to delete this document?')) return

    try {
      await documentsApi.delete(documentId)
      await loadDocuments()
    } catch (error) {
      console.error('Failed to delete document:', error)
      alert('Failed to delete document: ' + (error.response?.data?.detail || error.message))
    }
  }

  const handleSearch = async () => {
    if (!searchQuery.trim()) return

    try {
      setSearching(true)
      const response = await documentsApi.search({
        bot_id: bot.id,
        query: searchQuery,
        top_k: bot.rag_top_k || 5,
        similarity_threshold: bot.rag_similarity_threshold || 0.7
      })
      setSearchResults(response.data)
    } catch (error) {
      console.error('Failed to search documents:', error)
      alert('Failed to search: ' + (error.response?.data?.detail || error.message))
    } finally {
      setSearching(false)
    }
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-background border border-border rounded-lg shadow-2xl w-full max-w-4xl max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-border">
          <div>
            <h2 className="text-xl font-semibold flex items-center gap-2">
              <BookOpen size={24} />
              Knowledge Base: {bot.name}
            </h2>
            <p className="text-sm text-muted-foreground mt-1">
              Upload documents to enhance this bot's knowledge
            </p>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-accent rounded transition-colors"
          >
            <X size={20} />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {/* Upload Section */}
          <div className="border border-border rounded-lg p-4">
            <h3 className="font-semibold mb-3 flex items-center gap-2">
              <Upload size={18} />
              Upload Document
            </h3>

            {/* Upload Method Tabs */}
            <div className="flex gap-2 mb-4">
              <button
                onClick={() => setUploadMethod('file')}
                className={`px-3 py-1 rounded text-sm transition-colors ${
                  uploadMethod === 'file'
                    ? 'bg-primary text-primary-foreground'
                    : 'bg-accent hover:bg-accent/80'
                }`}
              >
                Upload File
              </button>
              <button
                onClick={() => setUploadMethod('text')}
                className={`px-3 py-1 rounded text-sm transition-colors ${
                  uploadMethod === 'text'
                    ? 'bg-primary text-primary-foreground'
                    : 'bg-accent hover:bg-accent/80'
                }`}
              >
                Paste Text
              </button>
            </div>

            {uploadMethod === 'file' ? (
              <div>
                <input
                  type="file"
                  accept=".txt,.pdf,.doc,.docx,.json,application/pdf,application/msword,application/vnd.openxmlformats-officedocument.wordprocessingml.document,application/json"
                  onChange={handleFileUpload}
                  disabled={uploading}
                  className="w-full px-3 py-2 border border-border rounded-lg bg-background focus:outline-none focus:ring-2 focus:ring-ring disabled:opacity-50"
                />
                <p className="text-xs text-muted-foreground mt-2">
                  Supported: .txt, .pdf, .doc, .docx, .json
                </p>
              </div>
            ) : (
              <div className="space-y-3">
                <input
                  type="text"
                  value={filename}
                  onChange={(e) => setFilename(e.target.value)}
                  placeholder="Filename (e.g., product-manual)"
                  className="w-full px-3 py-2 border border-border rounded-lg bg-background focus:outline-none focus:ring-2 focus:ring-ring"
                />
                <textarea
                  value={textContent}
                  onChange={(e) => setTextContent(e.target.value)}
                  placeholder="Paste your document content here..."
                  rows={6}
                  className="w-full px-3 py-2 border border-border rounded-lg bg-background focus:outline-none focus:ring-2 focus:ring-ring resize-none"
                />
                <button
                  onClick={handleTextUpload}
                  disabled={uploading || !textContent.trim() || !filename.trim()}
                  className="px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:opacity-90 transition-opacity disabled:opacity-50"
                >
                  {uploading ? 'Uploading...' : 'Upload Text'}
                </button>
              </div>
            )}
          </div>

          {/* Test Search Section */}
          <div className="border border-border rounded-lg p-4">
            <h3 className="font-semibold mb-3 flex items-center gap-2">
              <Search size={18} />
              Test Search
            </h3>
            <div className="flex gap-2">
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
                placeholder="Test a search query..."
                className="flex-1 px-3 py-2 border border-border rounded-lg bg-background focus:outline-none focus:ring-2 focus:ring-ring"
              />
              <button
                onClick={handleSearch}
                disabled={searching || !searchQuery.trim() || documents.length === 0}
                className="px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:opacity-90 transition-opacity disabled:opacity-50"
              >
                {searching ? 'Searching...' : 'Search'}
              </button>
            </div>

            {searchResults && (
              <div className="mt-4 space-y-2">
                <p className="text-sm font-medium">
                  Found {searchResults.length} relevant chunks:
                </p>
                {searchResults.map((result, idx) => (
                  <div key={result.chunk_id} className="p-3 bg-accent rounded-lg text-sm">
                    <div className="flex items-center justify-between mb-1">
                      <span className="font-medium">{result.filename}</span>
                      <span className="text-xs text-muted-foreground">
                        Similarity: {(result.similarity * 100).toFixed(1)}%
                      </span>
                    </div>
                    <p className="text-muted-foreground text-xs line-clamp-3">
                      {result.content}
                    </p>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Documents List */}
          <div className="border border-border rounded-lg p-4">
            <h3 className="font-semibold mb-3 flex items-center gap-2">
              <FileText size={18} />
              Documents ({documents.length})
            </h3>

            {loading ? (
              <div className="text-center py-8 text-muted-foreground">Loading documents...</div>
            ) : documents.length === 0 ? (
              <div className="text-center py-8 text-muted-foreground">
                <p>No documents uploaded yet.</p>
                <p className="text-xs mt-1">Upload documents to create a knowledge base for this bot.</p>
              </div>
            ) : (
              <div className="space-y-2">
                {documents.map((doc) => (
                  <div
                    key={doc.id}
                    className="flex items-center justify-between p-3 border border-border rounded-lg hover:border-primary/50 transition-colors"
                  >
                    <div className="flex-1 min-w-0">
                      <p className="font-medium truncate">{doc.filename}</p>
                      <p className="text-xs text-muted-foreground">
                        {doc.chunk_count} chunks • {new Date(doc.created_at).toLocaleDateString()}
                      </p>
                    </div>
                    <button
                      onClick={() => handleDelete(doc.id)}
                      className="p-2 hover:bg-accent rounded transition-colors text-red-600"
                      title="Delete document"
                    >
                      <Trash2 size={16} />
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* RAG Settings Info */}
          <div className="border border-border rounded-lg p-4 bg-accent/50">
            <h3 className="font-semibold mb-2 text-sm">RAG Configuration</h3>
            <div className="text-xs text-muted-foreground space-y-1">
              <p>• Top K: {bot.rag_top_k} chunks per query</p>
              <p>• Similarity Threshold: {(bot.rag_similarity_threshold * 100).toFixed(0)}%</p>
              <p>• Embedding Model: OpenAI text-embedding-3-small</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
