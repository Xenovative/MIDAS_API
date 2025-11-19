import { useState } from 'react'
import { Plus, MessageSquare, Trash2, Settings, Bot, Sun, Moon, Compass } from 'lucide-react'
import { useStore } from '../store/useStore'
import { conversationsApi } from '../lib/api'
import { cn } from '../lib/utils'
import { useTheme } from '../contexts/ThemeContext'
import SettingsModal from './Settings'
import BotManager from './BotManager'
import ModelExplorer from './ModelExplorer'

export default function Sidebar() {
  const {
    conversations,
    currentConversation,
    setCurrentConversation,
    addConversation,
    removeConversation,
    sidebarOpen,
    setSelectedModel,
    setSelectedBot,
    setSystemPrompt,
    setTemperature,
    setMaxTokens,
  } = useStore()

  const { theme, toggleTheme } = useTheme()
  const [settingsOpen, setSettingsOpen] = useState(false)
  const [botManagerOpen, setBotManagerOpen] = useState(false)
  const [modelExplorerOpen, setModelExplorerOpen] = useState(false)
  const [localSelectedBot, setLocalSelectedBot] = useState(null)

  const handleNewChat = async () => {
    try {
      const response = await conversationsApi.create('New Conversation')
      addConversation(response.data)
      setCurrentConversation(response.data)
    } catch (error) {
      console.error('Failed to create conversation:', error)
    }
  }

  const handleSelectConversation = async (id) => {
    try {
      // Check if conversation is already in store with messages
      const existingConv = conversations.find(c => c.id === id)
      if (existingConv && existingConv.messages && existingConv.messages.length > 0) {
        setCurrentConversation(existingConv)
        return
      }
      
      // Otherwise fetch from API
      const response = await conversationsApi.get(id)
      setCurrentConversation(response.data)
    } catch (error) {
      console.error('Failed to load conversation:', error)
    }
  }

  const handleDeleteConversation = async (e, id) => {
    e.stopPropagation()
    try {
      await conversationsApi.delete(id)
      removeConversation(id)
      if (currentConversation?.id === id) {
        setCurrentConversation(null)
      }
    } catch (error) {
      console.error('Failed to delete conversation:', error)
    }
  }

  if (!sidebarOpen) return null

  return (
    <div className="w-72 bg-sidebar border-r border-sidebar-border flex flex-col h-screen">
      {/* Header */}
      <div className="p-4 flex items-center justify-between border-b border-sidebar-border">
        <div className="flex items-center gap-2">
          <div className="text-xl font-bold">MIDAS</div>
        </div>
        <button
          onClick={toggleTheme}
          className="p-2 hover:bg-sidebar-hover rounded-lg transition-colors"
          title={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`}
        >
          {theme === 'dark' ? <Sun size={18} /> : <Moon size={18} />}
        </button>
      </div>

      {/* Action Buttons */}
      <div className="p-3 grid grid-cols-2 gap-2 border-b border-sidebar-border">
        <button
          onClick={() => setModelExplorerOpen(true)}
          className="flex flex-col items-center gap-2 px-4 py-3 bg-sidebar-button hover:bg-sidebar-hover rounded-xl transition-colors"
        >
          <Compass size={20} />
          <span className="text-xs">Explore</span>
        </button>
        <button
          onClick={() => setBotManagerOpen(true)}
          className="flex flex-col items-center gap-2 px-4 py-3 bg-sidebar-button hover:bg-sidebar-hover rounded-xl transition-colors"
        >
          <Plus size={20} />
          <span className="text-xs">Create</span>
        </button>
      </div>

      {/* Conversations List */}
      <div className="flex-1 overflow-y-auto">
        {conversations.length === 0 ? (
          <div className="p-4 text-center text-gray-500 text-sm">
            No conversations yet
          </div>
        ) : (
          conversations.map((conversation) => {
            // Get the model used in this conversation
            const firstAssistantMessage = conversation.messages?.find(m => m.role === 'assistant')
            const modelUsed = firstAssistantMessage?.model
            
            // Get model avatar/icon
            const getModelAvatar = (model) => {
              if (!model) return '💬'
              if (model.includes('gpt')) return '🟢'
              if (model.includes('claude')) return '🟠'
              if (model.includes('gemini')) return '🔵'
              if (model.includes('deepseek')) return '🔷'
              if (model.includes('doubao')) return '🔥'
              return '🤖'
            }
            
            // Get short model name
            const getModelName = (model) => {
              if (!model) return ''
              if (model.includes('gpt-4o')) return 'GPT-4o'
              if (model.includes('gpt-4')) return 'GPT-4'
              if (model.includes('gpt-3.5')) return 'GPT-3.5'
              if (model.includes('claude-3-5-sonnet')) return 'Claude 3.5 Sonnet'
              if (model.includes('claude-3-opus')) return 'Claude 3 Opus'
              if (model.includes('claude')) return 'Claude'
              if (model.includes('gemini')) return 'Gemini'
              if (model.includes('deepseek')) return 'DeepSeek'
              if (model.includes('doubao')) return '豆包'
              return model.split('/').pop()
            }
            
            const formatDate = (dateString) => {
              const date = new Date(dateString)
              const now = new Date()
              const diffDays = Math.floor((now - date) / (1000 * 60 * 60 * 24))
              
              if (diffDays === 0) return 'Today'
              if (diffDays === 1) return 'Yesterday'
              if (diffDays < 7) return `${diffDays}d ago`
              return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
            }
            
            return (
              <button
                key={conversation.id}
                onClick={() => handleSelectConversation(conversation.id)}
                className={cn(
                  "w-full flex items-center gap-3 px-4 py-3 hover:bg-sidebar-hover transition-colors group border-b border-sidebar-border",
                  currentConversation?.id === conversation.id && "bg-sidebar-active"
                )}
              >
                {/* Avatar */}
                <div className="w-10 h-10 rounded-full bg-gradient-to-br from-blue-500 to-purple-500 flex items-center justify-center text-xl flex-shrink-0">
                  {getModelAvatar(modelUsed)}
                </div>
                
                {/* Content */}
                <div className="flex-1 min-w-0 text-left">
                  <div className="flex items-center justify-between gap-2 mb-1">
                    <span className="text-sm font-medium truncate text-white">
                      {conversation.title}
                    </span>
                    <span className="text-xs text-gray-500 flex-shrink-0">
                      {formatDate(conversation.updated_at)}
                    </span>
                  </div>
                  <div className="text-xs text-gray-400 truncate">
                    {conversation.title?.startsWith('Chat with ') 
                      ? conversation.title.replace('Chat with ', '') 
                      : (getModelName(modelUsed) || 'New chat')}
                  </div>
                </div>
                
                {/* Delete button */}
                <button
                  onClick={(e) => handleDeleteConversation(e, conversation.id)}
                  className="opacity-0 group-hover:opacity-100 p-1.5 hover:bg-red-500/20 rounded transition-opacity flex-shrink-0"
                >
                  <Trash2 size={14} className="text-red-400" />
                </button>
              </button>
            )
          })
        )}
        
        {/* View All */}
        {conversations.length > 0 && (
          <button className="w-full py-3 text-sm text-muted-foreground hover:text-foreground hover:bg-sidebar-hover transition-colors">
            View all
          </button>
        )}
      </div>

      {/* Footer Menu */}
      <div className="border-t border-sidebar-border">
        <button 
          onClick={() => setBotManagerOpen(true)}
          className="w-full flex items-center gap-3 px-4 py-3 hover:bg-sidebar-hover transition-colors text-sm border-b border-sidebar-border"
        >
          <Bot size={18} />
          <span>Bots and apps</span>
        </button>
        <button 
          onClick={() => setSettingsOpen(true)}
          className="w-full flex items-center gap-3 px-4 py-3 hover:bg-sidebar-hover transition-colors text-sm"
        >
          <Settings size={18} />
          <span>Settings</span>
        </button>
      </div>

      <SettingsModal isOpen={settingsOpen} onClose={() => setSettingsOpen(false)} />
      
      {botManagerOpen && (
        <BotManager
          onClose={() => setBotManagerOpen(false)}
          onSelectBot={(bot) => {
            setLocalSelectedBot(bot)
            // TODO: Start new conversation with this bot
          }}
        />
      )}
      
      {modelExplorerOpen && (
        <ModelExplorer
          onClose={() => setModelExplorerOpen(false)}
          onSelectModel={(modelId, provider) => {
            console.log('📱 Regular model selected:', modelId)
            setSelectedModel(modelId, provider)
            setSelectedBot(null) // Clear bot when selecting regular model
            setSystemPrompt('') // Clear system prompt
            handleNewChat()
          }}
          onSelectBot={(bot) => {
            // Apply bot configuration
            console.log('🤖 Bot selected:', bot.name)
            console.log('Bot data:', bot)
            
            // Store the bot
            setSelectedBot(bot)
            
            const botModel = bot.default_model || 'gpt-4o-mini'
            const botProvider = bot.default_provider || 'openai'
            console.log('Setting model:', botModel, 'provider:', botProvider)
            setSelectedModel(botModel, botProvider)
            
            console.log('Setting system prompt:', bot.system_prompt?.substring(0, 100) + '...')
            setSystemPrompt(bot.system_prompt || '')
            
            console.log('Setting temperature:', bot.temperature)
            setTemperature(bot.temperature || 0.7)
            
            if (bot.max_tokens) {
              console.log('Setting max tokens:', bot.max_tokens)
              setMaxTokens(bot.max_tokens)
            }
            
            // Don't create conversation yet - let the first message create it with bot_id
            console.log('Bot configured - ready to chat (conversation will be created on first message)')
            setCurrentConversation(null)
          }}
        />
      )}
    </div>
  )
}
