import { useEffect, useMemo, useState } from 'react'
import { ChevronDown } from 'lucide-react'
import { useStore } from '../store/useStore'
import { modelsApi, botsApi } from '../lib/api'

export default function ModelSelector() {
  const {
    providers,
    selectedModel,
    selectedProvider,
    selectedBot,
    setProviders,
    setSelectedModel,
    setSelectedBot,
    setSystemPrompt,
    setTemperature,
    setMaxTokens,
  } = useStore()
  
  const [bots, setBots] = useState([])

  useEffect(() => {
    loadModels()
    loadBots()
  }, [])

  const loadModels = async () => {
    try {
      const response = await modelsApi.list()
      setProviders(response.data)
      
      // Set default model to first enabled model
      const enabledModels = getEnabledModels(response.data)
      if (enabledModels.length > 0) {
        const firstEnabled = enabledModels[0]
        setSelectedModel(firstEnabled.modelId, firstEnabled.provider)
      }
    } catch (error) {
      console.error('Failed to load models:', error)
    }
  }
  
  const loadBots = async () => {
    try {
      const response = await botsApi.list()
      setBots(response.data)
    } catch (error) {
      console.error('Failed to load bots:', error)
    }
  }

  const isModelEnabled = (providerId, modelId) => {
    const saved = localStorage.getItem('enabledModels')
    if (!saved) return true // Default to enabled
    const enabledModels = JSON.parse(saved)
    const key = `${providerId}:${modelId}`
    return enabledModels[key] !== false
  }

  const getEnabledModels = (providersList) => {
    const enabled = []
    providersList.forEach(provider => {
      provider.models.forEach(model => {
        if (isModelEnabled(provider.provider, model.id)) {
          enabled.push({
            provider: provider.provider,
            modelId: model.id,
            modelName: model.name
          })
        }
      })
    })
    return enabled
  }

  const filteredProviders = useMemo(() => {
    return providers.map(provider => ({
      ...provider,
      models: provider.models.filter(model => isModelEnabled(provider.provider, model.id))
    })).filter(provider => provider.models.length > 0)
  }, [providers])

  const handleModelChange = (e) => {
    const value = e.target.value
    
    // Check if it's a bot selection
    if (value.startsWith('bot::')) {
      const botId = value.replace('bot::', '')
      const bot = bots.find(b => b.id === botId)
      if (bot) {
        // Apply bot configuration
        setSelectedBot(bot)
        setSelectedModel(bot.default_model || 'gpt-4o-mini', bot.default_provider || 'openai')
        setSystemPrompt(bot.system_prompt || '')
        setTemperature(bot.temperature || 0.7)
        if (bot.max_tokens) {
          setMaxTokens(bot.max_tokens)
        }
      }
    } else {
      // Regular model selection
      const [provider, modelId] = value.split('::')
      setSelectedModel(modelId, provider)
      setSelectedBot(null) // Clear bot when selecting regular model
      setSystemPrompt('') // Clear system prompt
    }
  }

  return (
    <div className="relative">
      <select
        value={selectedBot ? `bot::${selectedBot.id}` : (selectedProvider && selectedModel ? `${selectedProvider}::${selectedModel}` : '')}
        onChange={handleModelChange}
        className="appearance-none bg-secondary border border-border rounded-lg px-4 py-2 pr-10 text-sm focus:outline-none focus:ring-2 focus:ring-ring cursor-pointer"
      >
        {/* Currently selected bot (if not in list) */}
        {selectedBot && !bots.find(b => b.id === selectedBot.id) && (
          <optgroup label="🤖 CURRENT BOT">
            <option value={`bot::${selectedBot.id}`}>
              {selectedBot.avatar} {selectedBot.name}
            </option>
          </optgroup>
        )}
        
        {/* My Bots Section */}
        {bots.length > 0 && (
          <optgroup label="🤖 MY BOTS">
            {bots.map((bot) => (
              <option key={bot.id} value={`bot::${bot.id}`}>
                {bot.avatar} {bot.name}
              </option>
            ))}
          </optgroup>
        )}
        
        {/* Models Section */}
        {filteredProviders.length === 0 ? (
          <option value="">No models enabled</option>
        ) : (
          filteredProviders.map((provider) => (
            <optgroup key={provider.provider} label={provider.provider.toUpperCase()}>
              {provider.models.map((model) => (
                <option key={model.id} value={`${provider.provider}::${model.id}`}>
                  {model.name}
                </option>
              ))}
            </optgroup>
          ))
        )}
      </select>
      <ChevronDown size={16} className="absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none" />
    </div>
  )
}
