import { useState, useRef, useEffect } from 'react'
import { Send, Loader2, Image as ImageIcon, X, Mic, Volume2, Square, Sparkles, ChevronDown, FileText, Upload } from 'lucide-react'
import { generationApi, documentsApi } from '../lib/api'

export default function ChatInput({ onSend, disabled, supportsVision, onImageIntent, selectedBot, conversationId }) {
  const [message, setMessage] = useState('')
  const [images, setImages] = useState([])
  const [uploadMode, setUploadMode] = useState('image') // 'image' or 'document'
  const [uploadingDoc, setUploadingDoc] = useState(false)
  const [uploadProgress, setUploadProgress] = useState(0)
  const [uploadStatus, setUploadStatus] = useState('')
  const [showUploadMenu, setShowUploadMenu] = useState(false)
  const [isRecording, setIsRecording] = useState(false)
  const [isTranscribing, setIsTranscribing] = useState(false)
  const [showImageHint, setShowImageHint] = useState(false)
  const [isImageIntent, setIsImageIntent] = useState(false)
  const [imageModels, setImageModels] = useState([])
  const [selectedImageModel, setSelectedImageModel] = useState(null)
  const fileInputRef = useRef(null)
  const mediaRecorderRef = useRef(null)
  const audioChunksRef = useRef([])
  const uploadMenuRef = useRef(null)
  
  useEffect(() => {
    loadImageModels()
  }, [])

  // Close upload menu when clicking outside
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

  useEffect(() => {
    if (isImageIntent && onImageIntent) {
      onImageIntent()
    }
  }, [isImageIntent, onImageIntent])

  const loadImageModels = async () => {
    try {
      const response = await generationApi.listImageModels()
      const models = response.data.models
      setImageModels(models)
      if (models.length > 0) {
        // Default to gpt-image-1 if available, otherwise first one
        const defaultModel = models.find(m => m.id === 'gpt-image-1') || models[0]
        setSelectedImageModel(defaultModel.id)
      }
    } catch (error) {
      console.error('Failed to load image models:', error)
    }
  }
  
  // Detect if user is typing an image generation request
  const detectImageIntent = (text, hasImages = false) => {
    const lowerText = text.toLowerCase()
    
    // Check for image-to-image patterns if images are uploaded
    if (hasImages) {
      const img2imgPatterns = [
        /(?:transform|modify|edit|change|alter|convert|turn|make)\s+(?:this|the)\s+(?:image|picture|photo)/,
        /(?:apply|add)\s+(?:a\s+)?(?:style|effect|filter)/,
        /make\s+(?:it|this)/,
        /turn\s+(?:it|this)\s+into/,
        /(?:variation|version)\s+of\s+(?:this|the)/,
        // Catch references to uploaded content
        /(?:this|the)\s+(?:girl|boy|person|man|woman|face|scene|photo|picture)/,
        /(?:generate|create|make|draw)\s+(?:an?\s+)?(?:image|picture).*(?:this|the)\s+(?:girl|boy|person|man|woman|scene)/
      ]
      
      if (img2imgPatterns.some(pattern => pattern.test(lowerText))) {
        return true
      }
    }
    
    // Check for text-to-image patterns
    const text2imgPatterns = [
      /(?:generate|create|make|draw|paint|design|produce)\s+(?:an?\s+)?image/,
      /(?:generate|create|make|draw|paint|design|produce)\s+(?:a\s+)?(?:picture|photo|illustration|artwork)/,
      /image\s+(?:generation|of)/,
      /draw\s+(?:me\s+)?/,
      /paint\s+(?:me\s+)?/
    ]
    
    return text2imgPatterns.some(pattern => pattern.test(lowerText))
  }
  
  const handleMessageChange = (e) => {
    const newMessage = e.target.value
    setMessage(newMessage)
    const hasIntent = detectImageIntent(newMessage, images.length > 0)
    setIsImageIntent(hasIntent)
    // Don't show hint by default - let users naturally request images
    // setShowImageHint(hasIntent)
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    if (message.trim() && !disabled) {
      onSend(message, images, selectedImageModel)
      setMessage('')
      setImages([])
    }
  }

  const handleImageSelect = async (e) => {
    const files = Array.from(e.target.files)
    const imagePromises = files.map(file => {
      return new Promise((resolve) => {
        const reader = new FileReader()
        reader.onload = (e) => {
          resolve({
            file: file.name,
            type: file.type || 'image/png', // Store the MIME type
            data: e.target.result.split(',')[1] // Get base64 without data:image prefix
          })
        }
        reader.readAsDataURL(file)
      })
    })
    
    const newImages = await Promise.all(imagePromises)
    const updatedImages = [...images, ...newImages]
    setImages(updatedImages)
    // Re-check image intent with new images
    const hasIntent = detectImageIntent(message, updatedImages.length > 0)
    setIsImageIntent(hasIntent)
    e.target.value = '' // Reset input
  }

  const handleDocumentUpload = async (e) => {
    const file = e.target.files?.[0]
    if (!file) return

    // Check file type
    const supportedExtensions = ['txt', 'pdf', 'doc', 'docx', 'json']
    const fileExtension = file.name.split('.').pop().toLowerCase()
    
    if (!supportedExtensions.includes(fileExtension)) {
      alert(`Unsupported file format. Please upload: ${supportedExtensions.join(', ')}`)
      e.target.value = ''
      return
    }

    try {
      setUploadingDoc(true)
      setUploadProgress(0)
      setUploadStatus('Starting upload...')
      
      await documentsApi.uploadFileWithProgress(
        file, 
        selectedBot?.id, 
        conversationId,
        (data) => {
          if (data.progress !== undefined) {
            setUploadProgress(data.progress)
          }
          if (data.status) {
            setUploadStatus(data.status)
          }
        }
      )
      
      setUploadStatus('Complete!')
      setTimeout(() => {
        setUploadProgress(0)
        setUploadStatus('')
      }, 2000)
      
      e.target.value = ''
      setShowUploadMenu(false)
    } catch (error) {
      console.error('Failed to upload document:', error)
      alert('Failed to upload document: ' + error.message)
      e.target.value = ''
      setUploadProgress(0)
      setUploadStatus('')
    } finally {
      setUploadingDoc(false)
    }
  }

  const removeImage = (index) => {
    const updatedImages = images.filter((_, i) => i !== index)
    setImages(updatedImages)
    // Re-check image intent after removing image
    const hasIntent = detectImageIntent(message, updatedImages.length > 0)
    setIsImageIntent(hasIntent)
  }

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      const mediaRecorder = new MediaRecorder(stream)
      mediaRecorderRef.current = mediaRecorder
      audioChunksRef.current = []

      mediaRecorder.ondataavailable = (event) => {
        audioChunksRef.current.push(event.data)
      }

      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' })
        await transcribeAudio(audioBlob)
        stream.getTracks().forEach(track => track.stop())
      }

      mediaRecorder.start()
      setIsRecording(true)
    } catch (error) {
      console.error('Error accessing microphone:', error)
      alert('Could not access microphone. Please check permissions.')
    }
  }

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop()
      setIsRecording(false)
    }
  }

  const transcribeAudio = async (audioBlob) => {
    setIsTranscribing(true)
    try {
      const formData = new FormData()
      formData.append('file', audioBlob, 'recording.webm')
      
      const response = await generationApi.speechToText(formData)
      setMessage(prev => prev + (prev ? ' ' : '') + response.data.text)
    } catch (error) {
      console.error('Transcription error:', error)
      alert('Failed to transcribe audio: ' + error.message)
    } finally {
      setIsTranscribing(false)
    }
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit(e)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="p-4 border-t border-border bg-background">
      <div className="max-w-4xl mx-auto">
        {/* Upload progress */}
        {uploadingDoc && (
          <div className="mb-3 p-3 bg-accent rounded-lg border border-border">
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-2">
                <Loader2 className="w-4 h-4 animate-spin" />
                <span className="text-sm font-medium">Processing document...</span>
              </div>
              <span className="text-sm font-semibold text-primary">{uploadProgress}%</span>
            </div>
            <div className="w-full bg-background rounded-full h-2.5 overflow-hidden border border-border/50">
              <div 
                className="bg-primary h-full transition-all duration-300 ease-out"
                style={{ width: `${uploadProgress}%` }}
              />
            </div>
            {uploadStatus && (
              <div className="mt-2 flex items-start gap-2">
                <div className="flex-1">
                  <p className="text-xs text-muted-foreground leading-relaxed">{uploadStatus}</p>
                </div>
              </div>
            )}
          </div>
        )}
        
        {/* Image previews */}
        {images.length > 0 && (
          <div className="flex gap-2 mb-2 flex-wrap">
            {images.map((img, index) => (
              <div key={index} className="relative group">
                <img
                  src={`data:image/jpeg;base64,${img.data}`}
                  alt={img.file}
                  className="w-20 h-20 object-cover rounded border border-border"
                />
                <button
                  type="button"
                  onClick={() => removeImage(index)}
                  className="absolute -top-2 -right-2 bg-red-500 text-white rounded-full p-1 opacity-0 group-hover:opacity-100 transition-opacity"
                >
                  <X size={12} />
                </button>
              </div>
            ))}
          </div>
        )}
        
        
        <div className="flex gap-2">
          <textarea
            value={message}
            onChange={handleMessageChange}
            onKeyDown={handleKeyDown}
            placeholder="Type your message... Try 'generate an image of...' (Shift+Enter for new line)"
            disabled={disabled}
            className="flex-1 resize-none rounded-lg border border-input bg-background px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-ring disabled:opacity-50 min-h-[60px] max-h-[200px]"
            rows={1}
          />
          
          {(supportsVision || imageModels.length > 0 || conversationId) && (
            <div className="relative" ref={uploadMenuRef}>
              <input
                ref={fileInputRef}
                type="file"
                accept={uploadMode === 'image' ? 'image/*' : '.txt,.pdf,.doc,.docx,.json,application/pdf,application/msword,application/vnd.openxmlformats-officedocument.wordprocessingml.document,application/json'}
                multiple={uploadMode === 'image'}
                onChange={uploadMode === 'image' ? handleImageSelect : handleDocumentUpload}
                className="hidden"
              />
              
              {/* Show menu if conversation exists (allows document upload) */}
              {conversationId ? (
                <>
                  <button
                    type="button"
                    onClick={() => setShowUploadMenu(!showUploadMenu)}
                    disabled={disabled || uploadingDoc}
                    className="px-4 py-3 border border-border rounded-lg hover:bg-accent transition-colors disabled:opacity-50 disabled:cursor-not-allowed relative"
                    title="Upload images or documents"
                  >
                    {uploadingDoc ? (
                      <Loader2 size={20} className="animate-spin" />
                    ) : (
                      <Upload size={20} />
                    )}
                  </button>
                  
                  {showUploadMenu && (
                    <div className="absolute bottom-full mb-2 right-0 bg-background border border-border rounded-lg shadow-lg overflow-hidden z-10 min-w-[200px]">
                      <button
                        type="button"
                        onClick={() => {
                          setUploadMode('image')
                          setShowUploadMenu(false)
                          fileInputRef.current?.click()
                        }}
                        className="w-full px-4 py-2 text-left hover:bg-accent transition-colors flex items-center gap-2 whitespace-nowrap"
                      >
                        <ImageIcon size={16} />
                        Upload Image
                      </button>
                      <button
                        type="button"
                        onClick={() => {
                          setUploadMode('document')
                          setShowUploadMenu(false)
                          fileInputRef.current?.click()
                        }}
                        className="w-full px-4 py-2 text-left hover:bg-accent transition-colors flex items-center gap-2 whitespace-nowrap border-t border-border"
                      >
                        <FileText size={16} />
                        <div className="flex flex-col">
                          <span>Upload Document</span>
                          <span className="text-xs text-muted-foreground">.txt, .pdf, .docx, .json</span>
                        </div>
                      </button>
                    </div>
                  )}
                </>
              ) : (
                <button
                  type="button"
                  onClick={() => {
                    setUploadMode('image')
                    fileInputRef.current?.click()
                  }}
                  disabled={disabled}
                  className="px-4 py-3 border border-border rounded-lg hover:bg-accent transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                  title="Upload images (for vision chat or image transformation)"
                >
                  <ImageIcon size={20} />
                </button>
              )}
            </div>
          )}
          
          <button
            type="button"
            onClick={isRecording ? stopRecording : startRecording}
            disabled={disabled || isTranscribing}
            className={`px-4 py-3 border border-border rounded-lg hover:bg-accent transition-colors disabled:opacity-50 disabled:cursor-not-allowed ${
              isRecording ? 'bg-red-500 text-white hover:bg-red-600' : ''
            }`}
            title={isRecording ? 'Stop recording' : 'Start voice recording'}
          >
            {isTranscribing ? (
              <Loader2 size={20} className="animate-spin" />
            ) : isRecording ? (
              <Square size={20} />
            ) : (
              <Mic size={20} />
            )}
          </button>
          
          <button
            type="submit"
            disabled={disabled || !message.trim()}
            className="px-4 py-3 bg-primary text-primary-foreground rounded-lg hover:opacity-90 transition-opacity disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {disabled ? (
              <Loader2 size={20} className="animate-spin" />
            ) : (
              <Send size={20} />
            )}
          </button>
        </div>
      </div>
    </form>
  )
}
