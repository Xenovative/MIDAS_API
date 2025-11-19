import { useState, useRef } from 'react'
import { Send, Loader2, Image as ImageIcon, X, Mic, Volume2, Square, Sparkles } from 'lucide-react'
import { generationApi } from '../lib/api'

export default function ChatInput({ onSend, disabled, supportsVision }) {
  const [message, setMessage] = useState('')
  const [images, setImages] = useState([])
  const [isRecording, setIsRecording] = useState(false)
  const [isTranscribing, setIsTranscribing] = useState(false)
  const [showImageHint, setShowImageHint] = useState(false)
  const fileInputRef = useRef(null)
  const mediaRecorderRef = useRef(null)
  const audioChunksRef = useRef([])
  
  // Detect if user is typing an image generation request
  const detectImageIntent = (text) => {
    const lowerText = text.toLowerCase()
    return lowerText.includes('generate') || 
           lowerText.includes('create') || 
           lowerText.includes('draw') || 
           lowerText.includes('paint') ||
           lowerText.includes('make') && (lowerText.includes('image') || lowerText.includes('picture'))
  }
  
  const handleMessageChange = (e) => {
    const newMessage = e.target.value
    setMessage(newMessage)
    setShowImageHint(detectImageIntent(newMessage))
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    if (message.trim() && !disabled) {
      onSend(message, images)
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
            data: e.target.result.split(',')[1] // Get base64 without data:image prefix
          })
        }
        reader.readAsDataURL(file)
      })
    })
    
    const newImages = await Promise.all(imagePromises)
    setImages([...images, ...newImages])
    e.target.value = '' // Reset input
  }

  const removeImage = (index) => {
    setImages(images.filter((_, i) => i !== index))
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
        
        {/* Image generation hint */}
        {showImageHint && (
          <div className="mb-2 flex items-center gap-2 text-sm text-primary bg-primary/10 px-3 py-2 rounded-lg">
            <Sparkles size={16} />
            <span>Image generation detected! I'll create an image for you.</span>
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
          
          {supportsVision && (
            <>
              <input
                ref={fileInputRef}
                type="file"
                accept="image/*"
                multiple
                onChange={handleImageSelect}
                className="hidden"
              />
              <button
                type="button"
                onClick={() => fileInputRef.current?.click()}
                disabled={disabled}
                className="px-4 py-3 border border-border rounded-lg hover:bg-accent transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                title="Upload images"
              >
                <ImageIcon size={20} />
              </button>
            </>
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
