import { useState, useEffect } from 'react'
import { Search, X, ChevronRight } from 'lucide-react'
import { useStore } from '../store/useStore'
import { botsApi } from '../lib/api'

export default function ModelExplorer({ onClose, onSelectModel, onSelectBot }) {
  const { providers } = useStore()
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedCategory, setSelectedCategory] = useState('all')
  const [bots, setBots] = useState([])

  // Load bots on mount
  useEffect(() => {
    loadBots()
  }, [])

  const loadBots = async () => {
    try {
      const response = await botsApi.list()
      setBots(response.data)
    } catch (error) {
      console.error('Failed to load bots:', error)
    }
  }

  // Get all models with metadata
  const allModels = providers.flatMap(provider =>
    provider.models.map(model => ({
      ...model,
      provider: provider.provider,
      providerName: provider.provider.toUpperCase(),
      avatar: getModelAvatar(model.id, provider.provider),
      category: getModelCategory(model.id),
      tags: getModelTags(model),
      type: 'model'
    }))
  )

  // Convert bots to model format
  const botModels = bots.map(bot => ({
    id: bot.id,
    name: bot.name,
    provider: 'bot',
    providerName: 'CUSTOM BOT',
    avatar: bot.avatar,
    category: 'bots',
    tags: ['Custom', 'Bot'],
    type: 'bot',
    description: bot.description,
    system_prompt: bot.system_prompt,
    default_model: bot.default_model,
    default_provider: bot.default_provider,
    temperature: bot.temperature,
    max_tokens: bot.max_tokens
  }))

  // Combine models and bots
  const allItems = [...botModels, ...allModels]

  // Filter items (models and bots)
  const filteredModels = allItems.filter(item => {
    const matchesSearch = searchQuery === '' || 
      item.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (item.id && item.id.toLowerCase().includes(searchQuery.toLowerCase())) ||
      item.providerName.toLowerCase().includes(searchQuery.toLowerCase())
    
    const matchesCategory = selectedCategory === 'all' || item.category === selectedCategory
    
    return matchesSearch && matchesCategory
  })

  // Categories
  const categories = [
    { id: 'all', label: 'All', icon: '⭐' },
    { id: 'bots', label: 'My Bots', icon: '🤖' },
    { id: 'coding', label: 'Coding', icon: '💻' },
    { id: 'creative', label: 'Creative', icon: '🎨' },
    { id: 'reasoning', label: 'Reasoning', icon: '🧠' },
    { id: 'vision', label: 'Vision', icon: '👁️' },
    { id: 'fast', label: 'Fast', icon: '⚡' },
  ]

  function getModelAvatar(modelId, provider) {
    if (modelId.includes('gpt')) return '🟢'
    if (modelId.includes('claude')) return '🟠'
    if (modelId.includes('gemini')) return '⭐'
    if (modelId.includes('deepseek')) return '🔷'
    if (modelId.includes('doubao')) return '🔥'
    if (modelId.includes('llama')) return '🦙'
    return '🤖'
  }

  function getModelCategory(modelId) {
    if (modelId.includes('coder') || modelId.includes('code')) return 'coding'
    if (modelId.includes('vision') || modelId.includes('4o')) return 'vision'
    if (modelId.includes('mini') || modelId.includes('haiku') || modelId.includes('lite')) return 'fast'
    if (modelId.includes('opus') || modelId.includes('reasoner')) return 'reasoning'
    return 'all'
  }

  function getModelTags(model) {
    const tags = []
    if (model.supports_vision) tags.push('Vision')
    if (model.supports_functions) tags.push('Functions')
    if (model.context_window >= 100000) tags.push('Long Context')
    if (model.id.includes('mini') || model.id.includes('haiku')) tags.push('Fast')
    return tags
  }

  function getModelDescription(model) {
    // If it's a bot, return its description
    if (model.type === 'bot') {
      return model.description || model.system_prompt?.substring(0, 150) + '...' || 'Custom AI assistant with specialized behavior.'
    }

    const descriptions = {
      'gpt-4o': "OpenAI's most advanced model with vision capabilities. Excels at complex reasoning, coding, and multimodal tasks.",
      'gpt-4o-mini': "Fast and cost-effective model optimized for everyday tasks. Great balance of speed and capability.",
      'gpt-4-turbo': "Advanced reasoning with 128K context. Perfect for long documents and complex analysis.",
      'claude-3-5-sonnet': "Anthropic's most intelligent model. Superior at coding, analysis, and nuanced conversations.",
      'claude-3-opus': "Most capable Claude model for highly complex tasks requiring deep reasoning and creativity.",
      'claude-3-haiku': "Fastest Claude model for quick responses while maintaining high quality.",
      'gemini-pro': "Google's advanced model with web search and 1M token context. Excellent for research.",
      'deepseek-chat': "Advanced conversational AI with strong reasoning capabilities and competitive performance.",
      'deepseek-coder': "Specialized coding model with deep understanding of programming languages and best practices.",
      'deepseek-reasoner': "R1 reasoning model designed for complex problem-solving and step-by-step analysis.",
    }

    for (const [key, desc] of Object.entries(descriptions)) {
      if (model.id && model.id.includes(key)) return desc
    }

    return `${model.name} from ${model.providerName}. Context: ${(model.context_window / 1000).toFixed(0)}K tokens.`
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-background border border-border rounded-lg shadow-2xl w-full max-w-5xl max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="p-6 border-b border-border">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-2xl font-bold">Explore Models</h2>
            <button
              onClick={onClose}
              className="p-2 hover:bg-accent rounded-lg transition-colors"
            >
              <X size={20} />
            </button>
          </div>

          {/* Search */}
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" size={20} />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search for models..."
              className="w-full pl-10 pr-4 py-3 border border-border rounded-lg bg-background focus:outline-none focus:ring-2 focus:ring-ring"
            />
          </div>
        </div>

        {/* Categories */}
        <div className="px-6 py-5 border-b border-border overflow-x-auto">
          <div className="flex gap-3 pb-1">
            {categories.map(category => (
              <button
                key={category.id}
                onClick={() => setSelectedCategory(category.id)}
                className={`flex items-center gap-2.5 px-5 py-3 rounded-full whitespace-nowrap transition-colors ${
                  selectedCategory === category.id
                    ? 'bg-primary text-primary-foreground'
                    : 'bg-secondary hover:bg-secondary/80'
                }`}
              >
                <span className="text-base">{category.icon}</span>
                <span className="text-sm font-medium">{category.label}</span>
              </button>
            ))}
          </div>
        </div>

        {/* Models List */}
        <div className="flex-1 overflow-y-auto p-6">
          {filteredModels.length === 0 ? (
            <div className="text-center py-12 text-muted-foreground">
              <p>No models found matching your search.</p>
            </div>
          ) : (
            <div className="space-y-4">
              {filteredModels.map((model) => (
                <button
                  key={`${model.id}-${model.provider}`}
                  onClick={() => {
                    console.log('🖱️ Model card clicked:', model.name, 'Type:', model.type)
                    // For bots, pass the full bot configuration
                    if (model.type === 'bot') {
                      console.log('✅ Detected as bot, calling onSelectBot')
                      console.log('onSelectBot exists?', !!onSelectBot)
                      if (onSelectBot) {
                        onSelectBot(model)
                      } else {
                        console.warn('⚠️ onSelectBot not provided, using fallback')
                        // Fallback: just select the model
                        const botModel = model.default_model || 'gpt-4o-mini'
                        const botProvider = model.default_provider || 'openai'
                        onSelectModel(botModel, botProvider)
                      }
                    } else {
                      console.log('📱 Regular model, calling onSelectModel')
                      onSelectModel(model.id, model.provider)
                    }
                    onClose()
                  }}
                  className="w-full flex items-start gap-4 p-4 border border-border rounded-lg hover:border-primary/50 hover:bg-accent/50 transition-all group text-left"
                >
                  {/* Avatar */}
                  <div className="w-16 h-16 rounded-xl bg-gradient-to-br from-blue-500 to-purple-500 flex items-center justify-center text-3xl flex-shrink-0">
                    {model.avatar}
                  </div>

                  {/* Content */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <h3 className="font-semibold text-lg">{model.name}</h3>
                      <ChevronRight size={16} className="text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity" />
                    </div>

                    <p className="text-sm text-muted-foreground mb-2 line-clamp-2">
                      {getModelDescription(model)}
                    </p>

                    {/* Tags */}
                    <div className="flex flex-wrap gap-2">
                      <span className="px-2 py-0.5 text-xs bg-primary/10 text-primary rounded">
                        {model.providerName}
                      </span>
                      {model.tags.map(tag => (
                        <span key={tag} className="px-2 py-0.5 text-xs bg-secondary text-secondary-foreground rounded">
                          {tag}
                        </span>
                      ))}
                      {model.context_window && (
                        <span className="px-2 py-0.5 text-xs bg-muted text-muted-foreground rounded">
                          {(model.context_window / 1000).toFixed(0)}K context
                        </span>
                      )}
                      {model.type === 'bot' && model.default_model && (
                        <span className="px-2 py-0.5 text-xs bg-muted text-muted-foreground rounded">
                          Uses {model.default_model}
                        </span>
                      )}
                    </div>
                  </div>
                </button>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
