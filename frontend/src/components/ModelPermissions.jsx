import { useState, useEffect } from 'react'
import { Shield, Users, Zap, Hash, Eye, EyeOff, Save, Loader2, RefreshCw, X } from 'lucide-react'
import { adminApi, modelsApi } from '../lib/api'

export default function ModelPermissions({ isOpen, onClose }) {
  const [permissions, setPermissions] = useState([])
  const [providers, setProviders] = useState([])
  const [loading, setLoading] = useState(true)
  const [selectedModel, setSelectedModel] = useState(null)
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    if (isOpen) {
      loadData()
    }
  }, [isOpen])

  const loadData = async () => {
    try {
      setLoading(true)
      const [permsRes, providersRes] = await Promise.all([
        adminApi.listModelPermissions(),
        modelsApi.list()
      ])
      console.log('Permissions response:', permsRes.data)
      console.log('Providers response:', providersRes.data)
      setPermissions(permsRes.data.permissions || [])
      // The models API returns the array directly, not wrapped in an object
      setProviders(Array.isArray(providersRes.data) ? providersRes.data : (providersRes.data.providers || []))
      console.log('Set providers:', Array.isArray(providersRes.data) ? providersRes.data : (providersRes.data.providers || []))
    } catch (error) {
      console.error('Failed to load data:', error)
      setPermissions([])
      setProviders([])
      alert('Failed to load data: ' + (error.response?.data?.detail || error.message))
    } finally {
      setLoading(false)
    }
  }

  const handleBulkCreate = async () => {
    try {
      setSaving(true)
      await adminApi.bulkCreatePermissions()
      await loadData()
      alert('Permissions created for all models!')
    } catch (error) {
      console.error('Failed to bulk create:', error)
      alert('Failed to create permissions: ' + (error.response?.data?.detail || error.message))
    } finally {
      setSaving(false)
    }
  }

  const handleUpdatePermission = async (modelId, updates) => {
    try {
      await adminApi.updateModelPermission(modelId, updates)
      await loadData()
    } catch (error) {
      console.error('Failed to update permission:', error)
      alert('Failed to update: ' + (error.response?.data?.detail || error.message))
    }
  }

  const getPermissionForModel = (providerId, modelId) => {
    const fullModelId = `${providerId}:${modelId}`
    return permissions.find(p => p.model_id === fullModelId)
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50" onClick={onClose}>
      <div 
        className="bg-background border border-border rounded-lg w-full max-w-6xl max-h-[90vh] overflow-hidden m-4 flex flex-col"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between p-6 border-b border-border">
          <div>
            <h2 className="text-xl font-bold">Model Permissions & Rate Limits</h2>
            <p className="text-sm text-muted-foreground mt-1">
              Configure model access and rate limits for different user tiers
            </p>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={handleBulkCreate}
              disabled={saving}
              className="flex items-center gap-2 px-3 py-2 bg-primary text-primary-foreground rounded-lg hover:opacity-90 transition-opacity disabled:opacity-50 text-sm"
            >
              {saving ? <Loader2 size={16} className="animate-spin" /> : <RefreshCw size={16} />}
              {saving ? 'Creating...' : 'Create All'}
            </button>
            <button
              onClick={onClose}
              className="p-1 hover:bg-accent rounded transition-colors"
            >
              <X size={20} />
            </button>
          </div>
        </div>

        <div className="flex-1 overflow-y-auto p-6">
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 size={32} className="animate-spin text-primary" />
            </div>
          ) : providers.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-12 text-center">
              <p className="text-muted-foreground mb-4">No model providers found</p>
              <p className="text-sm text-muted-foreground">
                Make sure you have configured API keys in Settings → API Keys
              </p>
            </div>
          ) : (
            <div className="space-y-6">
              {providers.map((provider) => (
                <div key={provider.provider} className="border border-border rounded-lg overflow-hidden">
                  <div className="p-4 bg-muted/30 border-b border-border">
                    <h3 className="font-semibold capitalize">{provider.provider}</h3>
                    <p className="text-sm text-muted-foreground">{provider.models.length} models</p>
                  </div>
                  <div className="divide-y divide-border">
                    {provider.models.map((model) => {
                      const permission = getPermissionForModel(provider.provider, model.id)
                      const modelId = `${provider.provider}:${model.id}`
                      
                      return (
                        <ModelPermissionRow
                          key={model.id}
                          model={model}
                          modelId={modelId}
                          provider={provider.provider}
                          permission={permission}
                          onUpdate={handleUpdatePermission}
                        />
                      )
                    })}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

function ModelPermissionRow({ model, modelId, provider, permission, onUpdate }) {
  const [expanded, setExpanded] = useState(false)
  const [formData, setFormData] = useState(permission || {
    visible_to_guest: false,
    visible_to_free: true,
    visible_to_premium: true,
    visible_to_admin: true,
    guest_rate_limit: 0,
    free_rate_limit: 10,
    premium_rate_limit: 100,
    admin_rate_limit: 0,
    guest_max_tokens: 1000,
    free_max_tokens: 4000,
    premium_max_tokens: 0,
    admin_max_tokens: 0,
    is_enabled: true
  })

  useEffect(() => {
    if (permission) {
      setFormData(permission)
    }
  }, [permission])

  const handleSave = async () => {
    if (!permission) {
      // Create new permission first
      try {
        await adminApi.createModelPermission(modelId, provider)
        // Then update with form data
        await onUpdate(modelId, formData)
      } catch (error) {
        console.error('Failed to create permission:', error)
      }
    } else {
      await onUpdate(modelId, formData)
    }
    setExpanded(false)
  }

  const getRoleBadge = (role, visible, rateLimit) => {
    const colors = {
      guest: 'bg-gray-500/20 text-gray-600',
      free: 'bg-blue-500/20 text-blue-600',
      premium: 'bg-yellow-500/20 text-yellow-600',
      admin: 'bg-red-500/20 text-red-600'
    }
    
    return (
      <span className={`inline-flex items-center gap-1 px-2 py-1 rounded text-xs ${colors[role]}`}>
        {visible ? <Eye size={12} /> : <EyeOff size={12} />}
        {visible ? (rateLimit === 0 ? '∞' : `${rateLimit}/h`) : 'Hidden'}
      </span>
    )
  }

  return (
    <div className="p-4">
      <div className="flex items-center justify-between">
        <div className="flex-1">
          <div className="font-medium">{model.name}</div>
          <div className="text-xs text-muted-foreground">{model.id}</div>
        </div>
        <div className="flex items-center gap-2">
          {getRoleBadge('guest', formData.visible_to_guest, formData.guest_rate_limit)}
          {getRoleBadge('free', formData.visible_to_free, formData.free_rate_limit)}
          {getRoleBadge('premium', formData.visible_to_premium, formData.premium_rate_limit)}
          {getRoleBadge('admin', formData.visible_to_admin, formData.admin_rate_limit)}
          <button
            onClick={() => setExpanded(!expanded)}
            className="px-3 py-1 text-sm border border-border rounded hover:bg-accent transition-colors"
          >
            {expanded ? 'Collapse' : 'Configure'}
          </button>
        </div>
      </div>

      {expanded && (
        <div className="mt-4 pt-4 border-t border-border space-y-4">
          <div className="grid grid-cols-4 gap-4">
            {['guest', 'free', 'premium', 'admin'].map((role) => (
              <div key={role} className="space-y-3 p-3 border border-border rounded-lg">
                <div className="font-medium capitalize text-sm">{role}</div>
                
                <label className="flex items-center gap-2 text-sm">
                  <input
                    type="checkbox"
                    checked={formData[`visible_to_${role}`]}
                    onChange={(e) => setFormData({ ...formData, [`visible_to_${role}`]: e.target.checked })}
                    className="rounded border-border"
                  />
                  <span>Visible</span>
                </label>

                <div>
                  <label className="block text-xs text-muted-foreground mb-1">
                    Rate Limit (req/hour)
                  </label>
                  <input
                    type="number"
                    value={formData[`${role}_rate_limit`]}
                    onChange={(e) => setFormData({ ...formData, [`${role}_rate_limit`]: parseInt(e.target.value) || 0 })}
                    className="w-full px-2 py-1 text-sm border border-border rounded bg-background focus:outline-none focus:ring-2 focus:ring-ring"
                    min="0"
                    placeholder="0 = unlimited"
                  />
                  <p className="text-xs text-muted-foreground mt-1">0 = unlimited</p>
                </div>

                <div>
                  <label className="block text-xs text-muted-foreground mb-1">
                    Max Tokens
                  </label>
                  <input
                    type="number"
                    value={formData[`${role}_max_tokens`]}
                    onChange={(e) => setFormData({ ...formData, [`${role}_max_tokens`]: parseInt(e.target.value) || 0 })}
                    className="w-full px-2 py-1 text-sm border border-border rounded bg-background focus:outline-none focus:ring-2 focus:ring-ring"
                    min="0"
                    placeholder="0 = default"
                  />
                  <p className="text-xs text-muted-foreground mt-1">0 = model default</p>
                </div>
              </div>
            ))}
          </div>

          <div className="flex items-center gap-2 pt-2">
            <label className="flex items-center gap-2 text-sm">
              <input
                type="checkbox"
                checked={formData.is_enabled}
                onChange={(e) => setFormData({ ...formData, is_enabled: e.target.checked })}
                className="rounded border-border"
              />
              <span>Model Enabled</span>
            </label>
            <div className="flex-1"></div>
            <button
              onClick={() => setExpanded(false)}
              className="px-4 py-2 border border-border rounded-lg hover:bg-accent transition-colors"
            >
              Cancel
            </button>
            <button
              onClick={handleSave}
              className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:opacity-90 transition-opacity"
            >
              <Save size={16} />
              Save Changes
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
