import { useState, useEffect } from 'react'
import { Plus, Edit2, Trash2, MessageSquare, Globe, Lock, X, Save, BookOpen, FileText } from 'lucide-react'
import { botsApi } from '../lib/api'
import { useStore } from '../store/useStore'
import DocumentManager from './DocumentManager'

export default function BotManager({ onClose, onSelectBot }) {
  const { providers } = useStore()
  const [bots, setBots] = useState([])
  const [loading, setLoading] = useState(true)
  const [showCreateForm, setShowCreateForm] = useState(false)
  const [editingBot, setEditingBot] = useState(null)
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    system_prompt: '',
    avatar: '🤖',
    default_model: '',
    default_provider: '',
    temperature: 0.7,
    max_tokens: null,
    is_public: false,
    use_rag: false,
    rag_top_k: 5,
    rag_similarity_threshold: 0.7
  })
  const [showDocManager, setShowDocManager] = useState(null)

  // Get all available models grouped by provider
  const availableModels = providers.flatMap(provider => 
    provider.models.map(model => ({
      ...model,
      displayName: `${model.name} (${provider.provider})`
    }))
  )

  useEffect(() => {
    loadBots()
  }, [])

  const loadBots = async () => {
    try {
      setLoading(true)
      console.log('Loading bots...')
      const response = await botsApi.list()
      console.log('Bots loaded:', response.data)
      setBots(response.data)
    } catch (error) {
      console.error('Failed to load bots:', error)
      console.error('Error details:', error.response)
      if (error.response?.status === 401) {
        alert('Authentication required. Please log in again.')
      }
    } finally {
      setLoading(false)
    }
  }

  const handleCreate = async () => {
    try {
      // Clean up data - convert empty strings to null
      const cleanData = {
        ...formData,
        description: formData.description || null,
        default_model: formData.default_model || null,
        default_provider: formData.default_provider || null,
        max_tokens: formData.max_tokens || null,
        use_rag: formData.use_rag,
        rag_top_k: formData.rag_top_k,
        rag_similarity_threshold: formData.rag_similarity_threshold
      }
      console.log('Creating bot with data:', cleanData)
      const response = await botsApi.create(cleanData)
      console.log('Bot created successfully:', response.data)
      await loadBots()
      setShowCreateForm(false)
      resetForm()
    } catch (error) {
      console.error('Failed to create bot:', error)
      console.error('Error response:', error.response)
      console.error('Error detail:', error.response?.data?.detail)
      
      let errorMsg = error.message
      if (error.response?.status === 401) {
        errorMsg = 'Authentication failed. Please log in again.'
      } else if (error.response?.data?.detail) {
        // Handle validation errors (array) or simple error messages (string)
        if (Array.isArray(error.response.data.detail)) {
          errorMsg = error.response.data.detail.map(err => 
            `${err.loc?.join('.') || 'Field'}: ${err.msg}`
          ).join('\n')
        } else {
          errorMsg = error.response.data.detail
        }
      }
      alert('Failed to create bot:\n' + errorMsg)
    }
  }

  const handleUpdate = async () => {
    try {
      await botsApi.update(editingBot.id, formData)
      await loadBots()
      setEditingBot(null)
      resetForm()
    } catch (error) {
      console.error('Failed to update bot:', error)
      alert('Failed to update bot: ' + (error.response?.data?.detail || error.message))
    }
  }

  const handleDelete = async (botId) => {
    if (!confirm('Are you sure you want to delete this bot?')) return
    
    try {
      await botsApi.delete(botId)
      await loadBots()
    } catch (error) {
      console.error('Failed to delete bot:', error)
      alert('Failed to delete bot: ' + (error.response?.data?.detail || error.message))
    }
  }

  const handleEdit = (bot) => {
    setEditingBot(bot)
    setFormData({
      name: bot.name,
      description: bot.description || '',
      system_prompt: bot.system_prompt,
      avatar: bot.avatar,
      default_model: bot.default_model || '',
      default_provider: bot.default_provider || '',
      temperature: bot.temperature,
      max_tokens: bot.max_tokens,
      is_public: bot.is_public,
      use_rag: bot.use_rag || false,
      rag_top_k: bot.rag_top_k || 5,
      rag_similarity_threshold: bot.rag_similarity_threshold || 0.7
    })
    setShowCreateForm(true)
  }

  const resetForm = () => {
    setFormData({
      name: '',
      description: '',
      system_prompt: '',
      avatar: '🤖',
      default_model: '',
      default_provider: '',
      temperature: 0.7,
      max_tokens: null,
      is_public: false,
      use_rag: false,
      rag_top_k: 5,
      rag_similarity_threshold: 0.7
    })
  }

  const emojiOptions = ['🤖', '🧠', '💡', '🎯', '🚀', '⚡', '🔥', '💻', '📚', '🎨', '🎭', '🎪', '🎬', '🎮', '🎯', '🏆']

  return (
    <>
      {showDocManager && (
        <DocumentManager
          bot={showDocManager}
          onClose={() => setShowDocManager(null)}
        />
      )}
      <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-background border border-border rounded-lg shadow-2xl w-full max-w-4xl max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-border">
          <h2 className="text-xl font-semibold">Bot Manager</h2>
          <div className="flex items-center gap-2">
            <button
              onClick={() => {
                setShowCreateForm(true)
                setEditingBot(null)
                resetForm()
              }}
              className="flex items-center gap-2 px-3 py-2 bg-primary text-primary-foreground rounded-lg hover:opacity-90 transition-opacity"
            >
              <Plus size={18} />
              Create Bot
            </button>
            <button
              onClick={onClose}
              className="p-2 hover:bg-accent rounded transition-colors"
            >
              <X size={20} />
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-4">
          {showCreateForm ? (
            /* Create/Edit Form */
            <div className="space-y-4">
              <h3 className="text-lg font-semibold">
                {editingBot ? 'Edit Bot' : 'Create New Bot'}
              </h3>

              {/* Avatar Selection */}
              <div>
                <label className="block text-sm font-medium mb-2">Avatar</label>
                <div className="flex gap-2 flex-wrap">
                  {emojiOptions.map((emoji) => (
                    <button
                      key={emoji}
                      onClick={() => setFormData({ ...formData, avatar: emoji })}
                      className={`text-2xl p-2 rounded border-2 transition-colors ${
                        formData.avatar === emoji
                          ? 'border-primary bg-primary/10'
                          : 'border-border hover:border-primary/50'
                      }`}
                    >
                      {emoji}
                    </button>
                  ))}
                </div>
              </div>

              {/* Name */}
              <div>
                <label className="block text-sm font-medium mb-2">Name *</label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  placeholder="My Assistant"
                  className="w-full px-3 py-2 border border-border rounded-lg bg-background focus:outline-none focus:ring-2 focus:ring-ring"
                />
              </div>

              {/* Description */}
              <div>
                <label className="block text-sm font-medium mb-2">Description</label>
                <input
                  type="text"
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  placeholder="A helpful assistant for..."
                  className="w-full px-3 py-2 border border-border rounded-lg bg-background focus:outline-none focus:ring-2 focus:ring-ring"
                />
              </div>

              {/* System Prompt */}
              <div>
                <label className="block text-sm font-medium mb-2">System Prompt *</label>
                <textarea
                  value={formData.system_prompt}
                  onChange={(e) => setFormData({ ...formData, system_prompt: e.target.value })}
                  placeholder="You are a helpful assistant that..."
                  rows={6}
                  className="w-full px-3 py-2 border border-border rounded-lg bg-background focus:outline-none focus:ring-2 focus:ring-ring resize-none"
                />
              </div>

              {/* Model Selection */}
              <div>
                <label className="block text-sm font-medium mb-2">Default Model (Optional)</label>
                <select
                  value={formData.default_model && formData.default_provider ? `${formData.default_model}|${formData.default_provider}` : ''}
                  onChange={(e) => {
                    if (e.target.value) {
                      const [model, provider] = e.target.value.split('|')
                      setFormData({ ...formData, default_model: model, default_provider: provider })
                    } else {
                      setFormData({ ...formData, default_model: '', default_provider: '' })
                    }
                  }}
                  className="w-full px-3 py-2 border border-border rounded-lg bg-background focus:outline-none focus:ring-2 focus:ring-ring"
                >
                  <option value="">No default (use user's selection)</option>
                  {providers.map(provider => (
                    <optgroup key={provider.provider} label={provider.provider.toUpperCase()}>
                      {provider.models.map(model => (
                        <option 
                          key={`${model.id}-${provider.provider}`} 
                          value={`${model.id}|${provider.provider}`}
                        >
                          {model.name}
                          {model.context_window && ` (${(model.context_window / 1000).toFixed(0)}K)`}
                        </option>
                      ))}
                    </optgroup>
                  ))}
                </select>
                <p className="text-xs text-muted-foreground mt-1">
                  If set, this model will be used by default when chatting with this bot
                </p>
              </div>

              {/* Temperature */}
              <div>
                <label className="block text-sm font-medium mb-2">
                  Temperature: {formData.temperature}
                  <span className="ml-2 text-xs text-muted-foreground">
                    {formData.temperature < 0.3 ? '(Very Precise)' : 
                     formData.temperature < 0.7 ? '(Balanced)' : 
                     formData.temperature < 1.2 ? '(Creative)' : 
                     '(Very Creative)'}
                  </span>
                </label>
                <input
                  type="range"
                  min="0"
                  max="2"
                  step="0.1"
                  value={formData.temperature}
                  onChange={(e) => setFormData({ ...formData, temperature: parseFloat(e.target.value) })}
                  className="w-full"
                />
                <div className="flex justify-between text-xs text-muted-foreground mt-1">
                  <span>0 (Precise)</span>
                  <span>1 (Balanced)</span>
                  <span>2 (Creative)</span>
                </div>
              </div>

              {/* RAG Toggle */}
              <div className="border border-border rounded-lg p-4 space-y-4">
                <div className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    id="use_rag"
                    checked={formData.use_rag}
                    onChange={(e) => setFormData({ ...formData, use_rag: e.target.checked })}
                    className="rounded"
                  />
                  <label htmlFor="use_rag" className="text-sm font-medium flex items-center gap-2">
                    <BookOpen size={16} />
                    Enable RAG (Knowledge Base)
                  </label>
                </div>
                
                {formData.use_rag && (
                  <>
                    <div>
                      <label className="block text-sm font-medium mb-2">
                        Top K Results: {formData.rag_top_k}
                      </label>
                      <input
                        type="range"
                        min="1"
                        max="10"
                        step="1"
                        value={formData.rag_top_k}
                        onChange={(e) => setFormData({ ...formData, rag_top_k: parseInt(e.target.value) })}
                        className="w-full"
                      />
                      <p className="text-xs text-muted-foreground mt-1">
                        Number of document chunks to retrieve per query
                      </p>
                    </div>
                    
                    <div>
                      <label className="block text-sm font-medium mb-2">
                        Similarity Threshold: {formData.rag_similarity_threshold.toFixed(2)}
                      </label>
                      <input
                        type="range"
                        min="0.5"
                        max="0.95"
                        step="0.05"
                        value={formData.rag_similarity_threshold}
                        onChange={(e) => setFormData({ ...formData, rag_similarity_threshold: parseFloat(e.target.value) })}
                        className="w-full"
                      />
                      <p className="text-xs text-muted-foreground mt-1">
                        Minimum similarity score for retrieved chunks (higher = more precise)
                      </p>
                    </div>
                  </>
                )}
              </div>

              {/* Public Toggle */}
              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  id="is_public"
                  checked={formData.is_public}
                  onChange={(e) => setFormData({ ...formData, is_public: e.target.checked })}
                  className="rounded"
                />
                <label htmlFor="is_public" className="text-sm flex items-center gap-2">
                  <Globe size={16} />
                  Make this bot public (others can use it)
                </label>
              </div>

              {/* Actions */}
              <div className="flex gap-2 pt-4">
                <button
                  onClick={editingBot ? handleUpdate : handleCreate}
                  disabled={!formData.name || !formData.system_prompt}
                  className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:opacity-90 transition-opacity disabled:opacity-50"
                >
                  <Save size={18} />
                  {editingBot ? 'Update' : 'Create'}
                </button>
                <button
                  onClick={() => {
                    setShowCreateForm(false)
                    setEditingBot(null)
                    resetForm()
                  }}
                  className="px-4 py-2 border border-border rounded-lg hover:bg-accent transition-colors"
                >
                  Cancel
                </button>
              </div>
            </div>
          ) : (
            /* Bot List */
            <div className="space-y-3">
              {loading ? (
                <div className="text-center py-8 text-muted-foreground">Loading bots...</div>
              ) : bots.length === 0 ? (
                <div className="text-center py-8 text-muted-foreground">
                  <p>No bots yet. Create your first bot!</p>
                </div>
              ) : (
                bots.map((bot) => (
                  <div
                    key={bot.id}
                    className="p-4 border border-border rounded-lg hover:border-primary/50 transition-colors"
                  >
                    <div className="flex items-start gap-3">
                      <div className="text-3xl">{bot.avatar}</div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-1">
                          <h3 className="font-semibold">{bot.name}</h3>
                          {bot.is_public ? (
                            <Globe size={14} className="text-muted-foreground" />
                          ) : (
                            <Lock size={14} className="text-muted-foreground" />
                          )}
                        </div>
                        {bot.description && (
                          <p className="text-sm text-muted-foreground mb-2">{bot.description}</p>
                        )}
                        <p className="text-xs text-muted-foreground line-clamp-2">
                          {bot.system_prompt}
                        </p>
                        {bot.use_rag && (
                          <div className="flex items-center gap-1 mt-2">
                            <BookOpen size={12} className="text-primary" />
                            <span className="text-xs text-primary">RAG Enabled</span>
                          </div>
                        )}
                      </div>
                      <div className="flex gap-2">
                        {bot.use_rag && (
                          <button
                            onClick={() => setShowDocManager(bot)}
                            className="p-2 hover:bg-accent rounded transition-colors"
                            title="Manage documents"
                          >
                            <FileText size={18} />
                          </button>
                        )}
                        <button
                          onClick={() => {
                            onSelectBot(bot)
                            onClose()
                          }}
                          className="p-2 hover:bg-accent rounded transition-colors"
                          title="Chat with this bot"
                        >
                          <MessageSquare size={18} />
                        </button>
                        <button
                          onClick={() => handleEdit(bot)}
                          className="p-2 hover:bg-accent rounded transition-colors"
                          title="Edit bot"
                        >
                          <Edit2 size={18} />
                        </button>
                        <button
                          onClick={() => handleDelete(bot.id)}
                          className="p-2 hover:bg-accent rounded transition-colors text-red-600"
                          title="Delete bot"
                        >
                          <Trash2 size={18} />
                        </button>
                      </div>
                    </div>
                  </div>
                ))
              )}
            </div>
          )}
        </div>
      </div>
    </div>
    </>
  )
}
