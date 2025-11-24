import { useEffect, useRef, useState } from 'react'
import { useStore } from '../store/useStore'
import { chatApi, conversationsApi } from '../lib/api'
import ChatMessage from './ChatMessage'
import ChatInput from './ChatInput'
import ArtifactViewer from './ArtifactViewer'
import ImageRatioSelector from './ImageRatioSelector'
import { Plus, Activity, Brain } from 'lucide-react'

export default function ChatArea() {
  const {
    currentConversation,
    selectedModel,
    selectedProvider,
    selectedBot,
    setSelectedBot,
    setSelectedModel,
    temperature,
    setTemperature,
    useAgent,
    useRealtimeData,
    useDeepResearch,
    setUseDeepResearch,
    systemPrompt,
    setSystemPrompt,
    maxTokens,
    setMaxTokens,
    imageRatio,
    imageSize,
    setImageRatio,
    addMessage,
    setCurrentConversation,
    addConversation,
    providers,
  } = useStore()

  const [isLoading, setIsLoading] = useState(false)
  const [streamingMessage, setStreamingMessage] = useState('')
  const [agentExecutions, setAgentExecutions] = useState([])
  const [currentArtifact, setCurrentArtifact] = useState(null)
  const messagesEndRef = useRef(null)
  
  // Apply bot configuration only when bot first loads
  const botAppliedRef = useRef(null)
  useEffect(() => {
    if (selectedBot && selectedBot.id !== botAppliedRef.current) {
      console.log('🔄 Applying bot configuration (first time):', selectedBot.name)
      
      // Apply bot's model and provider
      setSelectedModel(selectedBot.default_model || 'gpt-4o-mini', selectedBot.default_provider || 'openai')
      
      // Apply bot's system prompt and settings
      setSystemPrompt(selectedBot.system_prompt || '')
      setTemperature(selectedBot.temperature || 0.7)
      if (selectedBot.max_tokens) {
        setMaxTokens(selectedBot.max_tokens)
      }
      
      botAppliedRef.current = selectedBot.id
      console.log('✅ Bot configuration applied')
    } else if (!selectedBot) {
      botAppliedRef.current = null
    }
  }, [selectedBot?.id]) // Only run when bot ID changes
  
  // Load bot/model info when conversation changes
  useEffect(() => {
    const loadConversationContext = async () => {
      if (!currentConversation) return
      
      console.log('🔍 Conversation changed:', {
        id: currentConversation?.id,
        bot_id: currentConversation?.bot_id,
        messages: currentConversation?.messages?.length,
        title: currentConversation?.title
      })
      
      // If conversation has a bot_id, load the bot
      if (currentConversation.bot_id) {
        console.log('📦 Found bot_id, loading bot:', currentConversation.bot_id)
        try {
          const { botsApi } = await import('../lib/api')
          const response = await botsApi.get(currentConversation.bot_id)
          const bot = response.data
          setSelectedBot(bot)
          
          // Apply bot's configuration
          const botModel = bot.default_model || 'gpt-4o-mini'
          const botProvider = bot.default_provider || 'openai'
          setSelectedModel(botModel, botProvider)
          setSystemPrompt(bot.system_prompt || '')
          setTemperature(bot.temperature || 0.7)
          if (bot.max_tokens) {
            setMaxTokens(bot.max_tokens)
          }
          
          console.log('✅ Loaded bot for conversation:', bot.name)
        } catch (error) {
          console.error('Failed to load bot:', error)
        }
      } else if (currentConversation.title?.startsWith('Chat with ')) {
        // No bot_id, but title suggests it's a bot conversation - try to find bot by name
        const botName = currentConversation.title.replace('Chat with ', '')
        console.log('🔎 Trying to find bot by name:', botName)
        
        try {
          const { botsApi } = await import('../lib/api')
          const response = await botsApi.list()
          const bot = response.data.find(b => b.name === botName)
          
          if (bot) {
            console.log('✅ Found bot by name:', bot.name)
            setSelectedBot(bot)
            
            // Apply bot's configuration
            const botModel = bot.default_model || 'gpt-4o-mini'
            const botProvider = bot.default_provider || 'openai'
            setSelectedModel(botModel, botProvider)
            setSystemPrompt(bot.system_prompt || '')
            setTemperature(bot.temperature || 0.7)
            if (bot.max_tokens) {
              setMaxTokens(bot.max_tokens)
            }
          } else {
            console.warn('⚠️ Bot not found:', botName)
          }
        } catch (error) {
          console.error('Failed to find bot:', error)
        }
      } else if (currentConversation.messages && currentConversation.messages.length > 0) {
        // No bot_id, no bot title - load model from last message
        const lastMessage = currentConversation.messages[currentConversation.messages.length - 1]
        if (lastMessage.model) {
          // Try to determine provider from model name
          let provider = 'openai'
          if (lastMessage.model.includes('claude')) provider = 'anthropic'
          else if (lastMessage.model.includes('gemini')) provider = 'google'
          else if (lastMessage.model.includes('deepseek')) provider = 'deepseek'
          
          setSelectedModel(lastMessage.model, provider)
          setSelectedBot(null)
          setSystemPrompt('')
          console.log('✅ Loaded model from conversation:', lastMessage.model)
        }
      }
    }
    loadConversationContext()
  }, [currentConversation?.id])

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [currentConversation?.messages, streamingMessage])

  // Reset agent logs when switching conversations
  useEffect(() => {
    setAgentExecutions([])
  }, [currentConversation?.id])

  const handleRetry = async () => {
    if (!currentConversation?.messages?.length) return
    
    // Find the last user message
    const messages = [...currentConversation.messages]
    let lastUserMessage = null
    for (let i = messages.length - 1; i >= 0; i--) {
      if (messages[i].role === 'user') {
        lastUserMessage = messages[i]
        break
      }
    }
    
    if (lastUserMessage) {
      // Remove the last assistant message
      const filteredMessages = messages.slice(0, -1)
      setCurrentConversation({
        ...currentConversation,
        messages: filteredMessages
      })
      
      // Resend the last user message
      await handleSendMessage(lastUserMessage.content)
    }
  }

  const handleSuggestionClick = (suggestion) => {
    handleSendMessage(suggestion)
  }

  const handleArtifactClick = (artifact) => {
    setCurrentArtifact(artifact)
  }

  const handleImageIntent = () => {
    // Check if current model supports vision
    const currentModelInfo = providers
      .flatMap(p => p.models)
      .find(m => m.id === selectedModel && m.provider === selectedProvider)
    
    if (currentModelInfo?.supports_vision) return

    console.log('🎨 Image intent detected, switching to vision-capable model...')

    // Find a vision model
    // 1. Try to find one from the same provider
    let visionModel = providers
      .find(p => p.provider === selectedProvider)
      ?.models.find(m => m.supports_vision)

    // 2. If not, try OpenAI (gpt-4o/turbo)
    if (!visionModel) {
      visionModel = providers
        .find(p => p.provider === 'openai')
        ?.models.find(m => m.supports_vision && (m.id.includes('gpt-4') || m.id.includes('vision')))
    }

    // 3. If still not, take any vision model
    if (!visionModel) {
      visionModel = providers
        .flatMap(p => p.models)
        .find(m => m.supports_vision)
    }

    if (visionModel) {
      console.log('🔄 Switching to vision model:', visionModel.id)
      setSelectedModel(visionModel.id, visionModel.provider)
    }
  }

  const handleSendMessage = async (message, images = [], imageModel = null) => {
    if (!selectedModel || !selectedProvider) {
      alert('Please select a model first')
      return
    }

    setIsLoading(true)
    setStreamingMessage('')

    // Add user message immediately to UI with images
    const userMessage = {
      id: `temp-${Date.now()}`,
      conversation_id: currentConversation?.id,
      role: 'user',
      content: message,
      created_at: new Date().toISOString(),
      meta_data: images.length > 0 ? { 
        images: images.map(img => ({
          data: img.data,
          type: img.type || 'image/png'
        }))
      } : null
    }
    
    // Add to current conversation if it exists
    if (currentConversation) {
      addMessage(userMessage)
    }

    try {
      const requestData = {
        conversation_id: currentConversation?.id,
        message,
        model: selectedModel,
        provider: selectedProvider,
        temperature,
        use_agent: useAgent,
        use_realtime_data: useRealtimeData,
        use_deep_research: useDeepResearch,
        image_model: imageModel,
        image_size: imageSize,
      }
      
      console.log('💬 Sending chat request:')
      console.log('Model:', selectedModel, 'Provider:', selectedProvider)
      console.log('Image Model:', imageModel)
      console.log('Temperature:', temperature)
      console.log('System prompt:', systemPrompt ? systemPrompt.substring(0, 100) + '...' : 'None')
      console.log('Selected bot:', selectedBot?.name || 'None')
      console.log('Realtime data:', useRealtimeData)
      console.log('Deep research:', useDeepResearch)
      
      // Add system prompt if set
      if (systemPrompt) {
        requestData.system_prompt = systemPrompt
        console.log('✅ System prompt added to request')
      }
      
      // Add max tokens if set
      if (maxTokens) {
        requestData.max_tokens = maxTokens
        console.log('✅ Max tokens added:', maxTokens)
      }
      
      // Add bot info if selected
      if (selectedBot) {
        requestData.bot_id = selectedBot.id
        requestData.bot_name = selectedBot.name
        console.log('✅ Bot info added:', selectedBot.name)
      }
      
      // Add images if provided
      if (images.length > 0) {
        requestData.images = images.map(img => img.data)
      }
      
      console.log('Request data:', requestData)
      const response = await chatApi.stream(requestData)

      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let conversationId = currentConversation?.id
      let fullContent = ''
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() ?? ''

        for (const rawLine of lines) {
          const line = rawLine.trim()
          if (!line || !line.startsWith('data: ')) continue

          const payload = line.slice(6).trim()
          if (!payload) continue

          let data
          try {
            data = JSON.parse(payload)
          } catch (err) {
            console.error('Failed to parse SSE payload:', payload, err)
            continue
          }

          if (data.type === 'conversation_id') {
            conversationId = data.conversation_id
            if (!currentConversation) {
              // Create new conversation with user message
              const newConversation = {
                id: conversationId,
                messages: [userMessage],
                title: message.slice(0, 50),
                created_at: new Date().toISOString(),
                updated_at: new Date().toISOString()
              }
              setCurrentConversation(newConversation)
              addConversation(newConversation)
            } else {
              // Update existing conversation with new ID if needed
              if (currentConversation.id !== conversationId) {
                const updatedConversation = {
                  ...currentConversation,
                  id: conversationId
                }
                setCurrentConversation(updatedConversation)
                addConversation(updatedConversation)
              }
            }
          } else if (data.type === 'content') {
            fullContent += data.content
            setStreamingMessage(fullContent)
          } else if (data.type === 'image') {
            // Image generation started - show loading placeholder
            console.log('🎨 Image generating:', data.url)
            // The image will be included in the final 'done' event
          } else if (data.type === 'agent_executions') {
            setAgentExecutions(prev => [...prev, ...data.executions])
          } else if (data.type === 'title') {
            // Update conversation title
            if (currentConversation) {
              const updatedConversation = {
                ...currentConversation,
                title: data.title
              }
              setCurrentConversation(updatedConversation)
              addConversation(updatedConversation)
            }
          } else if (data.type === 'done') {
            const assistantMessage = {
              id: data.message_id,
              conversation_id: conversationId,
              role: 'assistant',
              content: fullContent,
              model: selectedModel,
              created_at: new Date().toISOString(),
              meta_data: data.meta_data || null // Include images and agent executions
            }
            addMessage(assistantMessage)
            setStreamingMessage('')
          } else if (data.type === 'error') {
            console.error('Stream error:', data.error)
            alert('Error: ' + data.error)
          }
        }
      }

      // Process any leftover buffered line (if reader ended without newline)
      if (buffer.trim().startsWith('data: ')) {
        try {
          const data = JSON.parse(buffer.trim().slice(6))
          if (data.type === 'error') {
            console.error('Stream error:', data.error)
            alert('Error: ' + data.error)
          }
        } catch (err) {
          console.error('Failed to parse trailing SSE payload:', buffer, err)
        }
      }
    } catch (error) {
      console.error('Failed to send message:', error)
      alert('Failed to send message: ' + error.message)
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="flex-1 flex flex-col h-screen">
      {/* Header showing bot or model name */}
      {(selectedBot || selectedModel) && (
        <div className="px-6 py-3 border-b border-border bg-muted/30 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="text-2xl">{selectedBot?.avatar || '🤖'}</span>
            <div>
              <div className="font-semibold">
                {(() => {
                  const displayName = selectedBot?.name || selectedModel
                  console.log('🎯 Header display name:', displayName, 'selectedBot:', selectedBot, 'selectedModel:', selectedModel)
                  return displayName
                })()}
              </div>
              <div className="text-xs text-muted-foreground">
                {selectedBot ? (selectedBot.default_model || 'Custom Bot') : selectedProvider}
              </div>
            </div>
          </div>
          
          <div className="flex items-center gap-2">
            {/* Image Ratio Selector - Show only for GPT-Image-1 */}
            {selectedModel === 'gpt-image-1' && (
              <ImageRatioSelector
                selectedRatio={imageRatio}
                onRatioChange={setImageRatio}
              />
            )}
            
            {/* Deep Research Toggle - Show for all RAG-enabled bots */}
            {(() => {
              const shouldShow = selectedBot?.use_rag || currentConversation?.id
              console.log('🔬 Deep Research Toggle visibility:', {
                shouldShow,
                'selectedBot?.use_rag': selectedBot?.use_rag,
                'currentConversation?.id': currentConversation?.id
              })
              return shouldShow
            })() && (
              <button
                onClick={() => {
                  console.log('🔬 Deep Research toggled:', !useDeepResearch)
                  setUseDeepResearch(!useDeepResearch)
                }}
                className={`flex items-center gap-2 px-3 py-2 rounded-lg transition-all text-sm ${
                  useDeepResearch
                    ? 'bg-purple-500/20 text-purple-400 border border-purple-500/30'
                    : 'bg-secondary text-secondary-foreground hover:bg-secondary/80'
                }`}
                title={useDeepResearch ? 'Deep Research: ON (uses o1-mini for complex analysis)' : 'Deep Research: OFF (fast retrieval)'}
              >
                <Brain size={16} className={useDeepResearch ? 'animate-pulse' : ''} />
                <span className="font-medium">Deep Research</span>
                {useDeepResearch && (
                  <span className="text-xs bg-purple-500/30 px-1.5 py-0.5 rounded">ON</span>
                )}
              </button>
            )}
            
            {/* New Chat Button */}
            <button
              onClick={async () => {
                try {
                  const response = await conversationsApi.create('New Conversation')
                  addConversation(response.data)
                  setCurrentConversation(response.data)
                } catch (error) {
                  console.error('Failed to create conversation:', error)
                }
              }}
              className="flex items-center gap-2 px-3 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors text-sm"
            >
              <Plus size={16} />
              New Chat
            </button>
          </div>
        </div>
      )}
      
      <div className="flex-1 overflow-y-auto">
        {!currentConversation || currentConversation.messages?.length === 0 ? (
          <div className="h-full flex items-center justify-center text-muted-foreground">
            <div className="text-center">
              <h2 className="text-2xl font-bold mb-2">Welcome to MIDAS</h2>
              <p>Start a conversation by typing a message below</p>
              {selectedBot && (
                <p className="mt-4 text-sm">
                  Chatting with <span className="font-semibold">{selectedBot.name}</span>
                </p>
              )}
            </div>
          </div>
        ) : (
          <>
            {currentConversation?.messages?.map((message, index) => {
              // Find previous user message for suggestions
              let previousUserMessage = null
              let previousAssistantMessage = null
              
              if (message.role === 'assistant') {
                // Find previous user message
                for (let i = index - 1; i >= 0; i--) {
                  if (currentConversation.messages[i].role === 'user') {
                    previousUserMessage = currentConversation.messages[i].content
                    break
                  }
                }
                
                // Find previous assistant message (for multi-turn image refinement)
                for (let i = index - 1; i >= 0; i--) {
                  if (currentConversation.messages[i].role === 'assistant') {
                    previousAssistantMessage = currentConversation.messages[i]
                    break
                  }
                }
              }
              
              return (
                <ChatMessage 
                  key={`${message.id}-${selectedBot?.id || 'no-bot'}`}
                  message={message}
                  botName={selectedBot?.name}
                  onRetry={handleRetry}
                  onSuggestionClick={handleSuggestionClick}
                  onArtifactClick={handleArtifactClick}
                  isLastMessage={index === currentConversation.messages.length - 1 && !streamingMessage}
                  previousUserMessage={previousUserMessage}
                  previousAssistantMessage={previousAssistantMessage}
                />
              )
            })}
            {streamingMessage && (
              <ChatMessage
                message={{
                  role: 'assistant',
                  content: streamingMessage,
                  model: selectedModel,
                }}
                botName={selectedBot?.name}
                isLastMessage={true}
              />
            )}
            <div ref={messagesEndRef} />
          </>
        )}
      </div>

      <ChatInput 
        onSend={handleSendMessage} 
        disabled={isLoading}
        onImageIntent={handleImageIntent}
        selectedBot={selectedBot}
        conversationId={currentConversation?.id}
        supportsVision={
          providers
            .flatMap(p => p.models)
            .find(m => m.id === selectedModel && m.provider === selectedProvider)
            ?.supports_vision || false
        }
      />

      {/* Artifact Viewer */}
      {currentArtifact && (
        <ArtifactViewer
          artifact={currentArtifact}
          onClose={() => setCurrentArtifact(null)}
        />
      )}
    </div>
  )
}
