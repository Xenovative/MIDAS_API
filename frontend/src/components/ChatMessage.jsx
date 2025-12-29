import { useState, useEffect, useMemo } from 'react'
import { User, Bot, Volume2, VolumeX, Loader2, RotateCcw, Copy, Check, Package, ExternalLink, FileText, Brain, Play, Download } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism'
import { cn } from '../lib/utils'
import { generationApi, suggestionsApi } from '../lib/api'
import MarkdownImage from './MarkdownImage'
import ImageLoadingPlaceholder from './ImageLoadingPlaceholder'
import { parseArtifacts } from '../lib/artifactParser'

const MAX_URL_DISPLAY = 70

const extractText = (children) => {
  if (!children) return ''
  if (typeof children === 'string') return children
  if (Array.isArray(children)) return children.map(extractText).join('')
  if (typeof children === 'object' && 'props' in children) {
    return extractText(children.props?.children)
  }
  return ''
}

const formatUrlDisplay = (url) => {
  if (!url) return ''
  const cleanUrl = url.replace(/^https?:\/\//i, '')
  if (cleanUrl.length <= MAX_URL_DISPLAY) return cleanUrl
  const suffixLength = 12
  const prefixLength = Math.max(10, MAX_URL_DISPLAY - suffixLength - 1)
  return `${cleanUrl.slice(0, prefixLength)}…${cleanUrl.slice(-suffixLength)}`
}

export default function ChatMessage({ 
  message, 
  botName,
  onRetry, 
  onSuggestionClick,
  onArtifactClick,
  isLastMessage = false,
  previousUserMessage = null,
  previousAssistantMessage = null
}) {
  const isUser = message.role === 'user'
  const [isPlaying, setIsPlaying] = useState(false)
  const [isGeneratingAudio, setIsGeneratingAudio] = useState(false)
  const [audioUrl, setAudioUrl] = useState(null)
  const [copied, setCopied] = useState(false)
  const [suggestions, setSuggestions] = useState([])
  const [loadingSuggestions, setLoadingSuggestions] = useState(false)
  const [isThinkingExpanded, setIsThinkingExpanded] = useState(true)
  
  // Parse thinking content (DeepSeek R1 style <think>...</think>)
  const { thinking, displayContent } = useMemo(() => {
    const thinkRegex = /<think>([\s\S]*?)<\/think>/g;
    let match;
    let thinkingParts = [];
    let lastIndex = 0;
    let cleanContent = message.content;

    // Extract all thinking blocks
    const matches = [...message.content.matchAll(thinkRegex)];
    if (matches.length > 0) {
      thinkingParts = matches.map(m => m[1].trim());
      // Remove think tags from the content displayed in markdown
      cleanContent = message.content.replace(thinkRegex, '').trim();
    }

    return { 
      thinking: thinkingParts.join('\n\n'), 
      displayContent: cleanContent 
    };
  }, [message.content]);

  // Parse artifacts from message content
  const { artifacts, contentWithoutArtifacts } = parseArtifacts(displayContent)
  
  // Check if this is an image or video generation in progress
  const isGeneratingMedia = !isUser && 
    (message.content.includes('🎨 Generating image') || 
     message.content.includes('🎨 Generating video') ||
     message.content.includes('🔄 Refining previous image')) &&
    (!message.meta_data?.images || message.meta_data.images.length === 0) &&
    (!message.meta_data?.videos || message.meta_data.videos.length === 0) &&
    !message.content.includes('❌') && // Don't show placeholder if there's an error
    !message.content.includes('🚫') && // Don't show placeholder for policy violations
    !message.content.includes('⏱️') && // Don't show placeholder for rate limits
    !message.content.includes('💳')    // Don't show placeholder for quota errors
  
  // Get previous image for multi-turn refinement
  const previousImage = previousAssistantMessage?.meta_data?.images?.[0] || null

  // Generate AI-powered suggestions when component mounts for last message
  useEffect(() => {
    if (!isUser && isLastMessage && previousUserMessage && onSuggestionClick) {
      generateAISuggestions()
    }
  }, [isLastMessage, previousUserMessage])

  const generateAISuggestions = async () => {
    setLoadingSuggestions(true)
    try {
      const response = await suggestionsApi.generate({
        user_message: previousUserMessage,
        assistant_message: message.content,
        model: 'gpt-4o-mini',
        provider: 'openai'
      })
      setSuggestions(response.data.suggestions)
    } catch (error) {
      console.error('Failed to generate suggestions:', error)
      // Fallback to simple suggestions
      setSuggestions(generateFallbackSuggestions())
    } finally {
      setLoadingSuggestions(false)
    }
  }

  // Fallback suggestions if AI generation fails
  const generateFallbackSuggestions = () => {
    const content = message.content.toLowerCase()
    const userQuestion = previousUserMessage?.toLowerCase() || ''
    const suggestions = []

    // Extract key topics and context from the user's question
    const extractContext = (text) => {
      // Clean up the text
      const cleaned = text.replace(/[?!.,]/g, '').trim()
      
      // Common stop words to filter out
      const stopWords = ['what', 'how', 'why', 'when', 'where', 'who', 'is', 'are', 'can', 'could', 'would', 'should', 'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'for', 'with', 'by', 'do', 'does', 'did', 'i', 'me', 'my', 'you', 'your']
      
      // Split into words and filter
      const words = cleaned.split(/\s+/)
      const meaningfulWords = words.filter(w => w.length > 2 && !stopWords.includes(w))
      
      // Try to find multi-word phrases (like "machine learning", "react hooks", "MTG")
      const phrases = []
      for (let i = 0; i < words.length - 1; i++) {
        if (!stopWords.includes(words[i]) && !stopWords.includes(words[i + 1])) {
          phrases.push(`${words[i]} ${words[i + 1]}`)
        }
      }
      
      // Prefer phrases over single words, or use the full meaningful part
      if (phrases.length > 0) {
        return { topic: phrases[0], words: meaningfulWords }
      }
      
      // If we have meaningful words, join them or use the first few
      if (meaningfulWords.length > 0) {
        if (meaningfulWords.length <= 3) {
          return { topic: meaningfulWords.join(' '), words: meaningfulWords }
        }
        return { topic: meaningfulWords.slice(0, 2).join(' '), words: meaningfulWords }
      }
      
      return { topic: 'this', words: [] }
    }

    const { topic: mainTopic, words: topicWords } = extractContext(userQuestion)

    // Check for code-related content
    if (content.includes('```') || content.includes('code') || content.includes('function') || content.includes('class')) {
      suggestions.push(`Explain this code in detail`)
      suggestions.push(`Show me more ${mainTopic} examples`)
      suggestions.push(`What are common ${mainTopic} mistakes?`)
    }

    // Check for explanations or concepts
    else if (content.includes('because') || content.includes('therefore') || content.includes('means') || content.includes('explanation')) {
      suggestions.push(`Explain ${mainTopic} in simpler terms`)
      suggestions.push(`Give me a ${mainTopic} analogy`)
      suggestions.push(`What's a real-world ${mainTopic} example?`)
    }

    // Check for lists or comparisons
    else if (content.includes('1.') || content.includes('2.') || content.includes('•') || content.includes('-') || content.includes('option')) {
      suggestions.push(`Which ${mainTopic} option is best?`)
      suggestions.push(`Compare these ${mainTopic} options`)
      suggestions.push(`What are the pros and cons?`)
    }

    // Check for how-to or tutorial content
    else if (content.includes('step') || content.includes('first') || content.includes('then') || content.includes('next')) {
      suggestions.push(`What's next in ${mainTopic}?`)
      suggestions.push(`Show me the complete ${mainTopic} process`)
      suggestions.push(`What if something goes wrong?`)
    }

    // Check for problems/errors/debugging
    else if (content.includes('error') || content.includes('issue') || content.includes('problem') || content.includes('fix') || content.includes('debug')) {
      suggestions.push(`How do I debug ${mainTopic}?`)
      suggestions.push(`What causes ${mainTopic} errors?`)
      suggestions.push(`${mainTopic} best practices`)
    }

    // Check if user asked "what" - suggest deeper dive
    else if (userQuestion.includes('what is') || userQuestion.includes('what are')) {
      suggestions.push(`How do I get started with ${mainTopic}?`)
      suggestions.push(`When should I use ${mainTopic}?`)
      suggestions.push(`Tell me more about ${mainTopic}`)
    }

    // Check if user asked "how" - suggest related questions
    else if (userQuestion.includes('how to') || userQuestion.includes('how do') || userQuestion.includes('how can')) {
      suggestions.push(`What are ${mainTopic} best practices?`)
      suggestions.push(`Show me ${mainTopic} examples`)
      suggestions.push(`Common ${mainTopic} mistakes to avoid`)
    }

    // Default contextual suggestions
    else {
      const contextual = [
        `Tell me more about ${mainTopic}`,
        `Give me a ${mainTopic} example`,
        `What should I know about ${mainTopic}?`,
        `How do I get better at ${mainTopic}?`,
        `What are ${mainTopic} tips for beginners?`
      ]
      contextual.forEach(s => {
        if (suggestions.length < 5) {
          suggestions.push(s)
        }
      })
    }

    // Fallback to generic if no topic found
    if (suggestions.length === 0) {
      suggestions.push(
        "Explain this in simpler terms",
        "Give me a practical example",
        "What are the best practices?",
        "Show me how to implement this",
        "What should I know next?"
      )
    }

    return suggestions.slice(0, 5) // Return max 5 suggestions
  }

  const handlePlayAudio = async () => {
    if (isPlaying) {
      // Stop audio
      setIsPlaying(false)
      if (audioUrl) {
        URL.revokeObjectURL(audioUrl)
        setAudioUrl(null)
      }
      return
    }

    if (audioUrl) {
      // Play existing audio
      const audio = new Audio(audioUrl)
      audio.play()
      setIsPlaying(true)
      audio.onended = () => setIsPlaying(false)
      return
    }

    // Generate new audio
    setIsGeneratingAudio(true)
    try {
      const response = await generationApi.textToSpeech({
        text: message.content,
        voice: 'alloy',
        model: 'tts-1'
      })
      
      const url = URL.createObjectURL(response.data)
      setAudioUrl(url)
      
      const audio = new Audio(url)
      audio.play()
      setIsPlaying(true)
      audio.onended = () => setIsPlaying(false)
    } catch (error) {
      console.error('TTS error:', error)
      alert('Failed to generate audio: ' + error.message)
    } finally {
      setIsGeneratingAudio(false)
    }
  }

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(message.content)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch (error) {
      console.error('Copy failed:', error)
    }
  }

  return (
    <div
      className={cn(
        "flex gap-4 p-6 border-b border-border",
        isUser ? "bg-background" : "bg-muted/30"
      )}
    >
      <div className={cn(
        "flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center",
        isUser ? "bg-primary text-primary-foreground" : "bg-accent text-accent-foreground"
      )}>
        {isUser ? <User size={18} /> : <Bot size={18} />}
      </div>

      <div className="flex-1 min-w-0">
        <div className="flex items-center justify-between mb-2">
          <div className="font-semibold text-sm">
            {isUser ? 'You' : botName || message.model || 'Assistant'}
          </div>
          {!isUser && (
            <button
              onClick={handlePlayAudio}
              disabled={isGeneratingAudio}
              className="p-1 hover:bg-accent rounded transition-colors disabled:opacity-50"
              title={isPlaying ? 'Stop audio' : 'Play audio'}
            >
              {isGeneratingAudio ? (
                <Loader2 size={16} className="animate-spin" />
              ) : isPlaying ? (
                <VolumeX size={16} />
              ) : (
                <Volume2 size={16} />
              )}
            </button>
          )}
        </div>
        
        {/* Display loading placeholder for media generation */}
        {isGeneratingMedia && (
          <ImageLoadingPlaceholder 
            message={
              message.content.includes('🔄 Refining') 
                ? "Refining image..." 
                : message.content.includes('video') 
                  ? "Generating video..." 
                  : "Generating image..."
            }
            previousImage={message.content.includes('🔄 Refining') ? previousImage : null}
          />
        )}
        
        {/* Display documents (PDFs for user messages) */}
        {message.meta_data?.documents && message.meta_data.documents.length > 0 && (
          <div className="flex flex-wrap gap-2 mb-3">
            {message.meta_data.documents.map((doc, idx) => (
              <div key={idx} className="flex items-center gap-2 px-3 py-2 bg-accent rounded-lg border border-border">
                <FileText size={16} className="text-red-500" />
                <span className="text-sm">{doc.name || `Document ${idx + 1}`}</span>
              </div>
            ))}
          </div>
        )}
        
        {/* Display images (uploaded for user, generated for assistant) */}
        {message.meta_data?.images && message.meta_data.images.length > 0 && (
          <div className="flex flex-wrap gap-2 mb-3">
            {message.meta_data.images.map((img, idx) => {
              // Handle different image formats:
              // 1. String: HTTP/HTTPS URLs, /static/ paths, data: URLs, or raw base64
              // 2. Object: { data: base64, type: mime-type } from temporary messages
              let imageSrc
              
              if (typeof img === 'object' && img.data) {
                // New format: object with data and type
                imageSrc = `data:${img.type};base64,${img.data}`
              } else if (typeof img === 'string') {
                // Old format: string (URL, path, or base64)
                if (img.startsWith('http') || img.startsWith('/') || img.startsWith('data:')) {
                  imageSrc = img
                } else {
                  // Raw base64 without prefix
                  imageSrc = `data:image/png;base64,${img}`
                }
              }
              
              return (
                <MarkdownImage
                  key={idx}
                  src={imageSrc}
                  alt={isUser ? `Uploaded ${idx + 1}` : `Generated ${idx + 1}`}
                />
              )
            })}
          </div>
        )}

        {/* Display videos (generated for assistant) */}
        {message.meta_data?.videos && message.meta_data.videos.length > 0 && (
          <div className="flex flex-wrap gap-4 mb-4">
            {message.meta_data.videos.map((videoUrl, idx) => (
              <div
                key={idx}
                className="relative group max-w-2xl rounded-xl overflow-hidden border border-border bg-black flex items-center justify-center shadow-lg"
              >
                <video
                  src={videoUrl}
                  controls
                  className="max-w-full max-h-[500px] w-auto h-auto object-contain bg-black"
                  style={{ aspectRatio: 'unset' }}
                >
                  Your browser does not support the video tag.
                </video>
                <div className="absolute top-2 right-2 flex gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                  <a
                    href={videoUrl}
                    download={`video-${idx}.mp4`}
                    className="p-2 bg-background/80 hover:bg-background rounded-full text-foreground shadow-sm"
                    title="Download video"
                  >
                    <Download size={16} />
                  </a>
                </div>
              </div>
            ))}
          </div>
        )}
        
        {/* Display thinking process if available */}
        {thinking && (
          <div className="mb-4 border-l-2 border-primary/30 bg-muted/50 rounded-r-lg overflow-hidden">
            <button 
              onClick={() => setIsThinkingExpanded(!isThinkingExpanded)}
              className="w-full flex items-center gap-2 px-3 py-2 text-xs font-medium text-muted-foreground hover:bg-muted transition-colors border-b border-border/50"
            >
              <Brain size={14} className="text-primary/70" />
              <span>Thinking Process</span>
              <div className="ml-auto opacity-50 text-[10px]">
                {isThinkingExpanded ? 'Click to collapse' : 'Click to expand'}
              </div>
            </button>
            {isThinkingExpanded && (
              <div className="p-3 text-sm italic text-muted-foreground whitespace-pre-wrap leading-relaxed">
                {thinking}
              </div>
            )}
          </div>
        )}

        <div className="markdown-content prose prose-sm max-w-none">
          <ReactMarkdown 
            remarkPlugins={[remarkGfm]}
            components={{
              img: ({ node, ...props }) => <MarkdownImage {...props} />,
              a: ({ node, href, children, className, ...props }) => {
                const textContent = extractText(children)
                const display = formatUrlDisplay(textContent || href)
                const isExternal = /^https?:/i.test(href || '')
                return (
                  <a
                    href={href}
                    target={isExternal ? '_blank' : undefined}
                    rel={isExternal ? 'noopener noreferrer' : undefined}
                    className={cn(
                      'inline-flex items-center max-w-full gap-1 text-primary hover:underline truncate',
                      className
                    )}
                    title={href}
                    {...props}
                  >
                    <span className="truncate">{display}</span>
                    {isExternal && <ExternalLink size={14} className="flex-shrink-0" />}
                  </a>
                )
              },
              code: ({ node, inline, className, children, ...props }) => {
                const match = /language-(\w+)/.exec(className || '')
                const language = match ? match[1] : ''
                const codeString = String(children).replace(/\n$/, '')
                const lineCount = codeString.split('\n').length
                
                // Show "View as Artifact" button for code blocks with 10+ lines
                const showArtifactButton = !inline && language && lineCount >= 10 && onArtifactClick
                
                return !inline && language ? (
                  <div className="relative group">
                    <SyntaxHighlighter
                      style={vscDarkPlus}
                      language={language}
                      PreTag="div"
                      customStyle={{
                        margin: '1rem 0',
                        borderRadius: '0.5rem',
                        fontSize: '0.875rem'
                      }}
                      showLineNumbers
                      {...props}
                    >
                      {codeString}
                    </SyntaxHighlighter>
                    {/* Action buttons for code blocks */}
                    <div className="absolute top-2 right-2 flex gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                      {showArtifactButton && (
                        <button
                          onClick={() => {
                            onArtifactClick({
                              id: `code-${Date.now()}`,
                              type: 'code',
                              language,
                              title: `${language.toUpperCase()} Code`,
                              content: codeString,
                              filename: `code.${language}`
                            })
                          }}
                          className="flex items-center gap-1 px-2 py-1 bg-primary/80 hover:bg-primary text-primary-foreground rounded text-xs"
                          title="View as artifact"
                        >
                          <Package size={14} />
                          View
                        </button>
                      )}
                      <button
                        onClick={() => {
                          navigator.clipboard.writeText(codeString)
                        }}
                        className="p-2 bg-background/80 hover:bg-background rounded"
                        title="Copy code"
                      >
                        <Copy size={14} />
                      </button>
                    </div>
                  </div>
                ) : (
                  <code className={className} {...props}>
                    {children}
                  </code>
                )
              }
            }}
          >
            {contentWithoutArtifacts}
          </ReactMarkdown>
        </div>

        {/* Artifact buttons */}
        {artifacts.length > 0 && onArtifactClick && (
          <div className="mt-4 flex flex-wrap gap-2">
            {artifacts.map((artifact) => (
              <button
                key={artifact.id}
                onClick={() => onArtifactClick(artifact)}
                className="flex items-center gap-2 px-3 py-2 bg-primary/10 hover:bg-primary/20 border border-primary/30 rounded-lg transition-colors text-sm"
              >
                <Package size={16} className="text-primary" />
                <span className="font-medium">{artifact.title}</span>
                <span className="text-xs text-muted-foreground">({artifact.language})</span>
              </button>
            ))}
          </div>
        )}

        {/* Action buttons for assistant messages */}
        {!isUser && (
          <div className="flex items-center gap-2 mt-3 pt-3 border-t border-border/50">
            <button
              onClick={handleCopy}
              className="flex items-center gap-1.5 px-2 py-1 text-xs hover:bg-accent rounded transition-colors"
              title="Copy to clipboard"
            >
              {copied ? (
                <>
                  <Check size={14} className="text-green-600" />
                  <span className="text-green-600">Copied!</span>
                </>
              ) : (
                <>
                  <Copy size={14} />
                  <span>Copy</span>
                </>
              )}
            </button>
            
            {onRetry && isLastMessage && (
              <button
                onClick={onRetry}
                className="flex items-center gap-1.5 px-2 py-1 text-xs hover:bg-accent rounded transition-colors"
                title="Regenerate response"
              >
                <RotateCcw size={14} />
                <span>Retry</span>
              </button>
            )}
          </div>
        )}

        {/* Suggestion chips for last assistant message */}
        {!isUser && isLastMessage && onSuggestionClick && (
          <div className="mt-4">
            {loadingSuggestions ? (
              <div className="flex items-center gap-2 text-xs text-muted-foreground">
                <Loader2 size={14} className="animate-spin" />
                <span>Generating suggestions...</span>
              </div>
            ) : suggestions.length > 0 ? (
              <div className="flex flex-wrap gap-2">
                {suggestions.map((suggestion, index) => (
                  <button
                    key={index}
                    onClick={() => onSuggestionClick(suggestion)}
                    className="px-3 py-1.5 text-xs bg-muted hover:bg-accent border border-border rounded-full transition-colors"
                  >
                    {suggestion}
                  </button>
                ))}
              </div>
            ) : null}
          </div>
        )}
      </div>
    </div>
  )
}
