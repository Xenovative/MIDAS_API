import { useState, useEffect } from 'react'
import { Plus, Trash2, Power, RefreshCw, Terminal, Box, Play, AlertCircle, CheckCircle, XCircle } from 'lucide-react'
import { mcpApi } from '../lib/api'

export default function MCPManager() {
  const [servers, setServers] = useState([])
  const [tools, setTools] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [showAddModal, setShowAddModal] = useState(false)
  
  // New server form state
  const [newServer, setNewServer] = useState({
    name: '',
    command: '',
    args: '',
    env: '',
    enabled: true
  })

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    setLoading(true)
    setError(null)
    try {
      const [serversRes, toolsRes] = await Promise.all([
        mcpApi.listServers(),
        mcpApi.listTools()
      ])
      setServers(serversRes.data.servers)
      setTools(toolsRes.data.tools)
    } catch (err) {
      console.error('Failed to load MCP data:', err)
      setError('Failed to load MCP configuration. Is the backend running?')
    } finally {
      setLoading(false)
    }
  }

  const handleAddServer = async (e) => {
    e.preventDefault()
    setLoading(true)
    try {
      // Parse args and env
      const argsList = newServer.args.split('\n').filter(line => line.trim())
      
      let envDict = {}
      try {
        if (newServer.env.trim()) {
          envDict = JSON.parse(newServer.env)
        }
      } catch (e) {
        // If not JSON, try KEY=VALUE format
        newServer.env.split('\n').forEach(line => {
          const [key, ...val] = line.split('=')
          if (key && val) envDict[key.trim()] = val.join('=').trim()
        })
      }

      const payload = {
        name: newServer.name,
        command: newServer.command,
        args: argsList,
        env: envDict,
        enabled: newServer.enabled
      }

      await mcpApi.addServer(payload)
      setShowAddModal(false)
      setNewServer({
        name: '',
        command: '',
        args: '',
        env: '',
        enabled: true
      })
      await loadData()
    } catch (err) {
      setError(err.response?.data?.detail || err.message)
    } finally {
      setLoading(false)
    }
  }

  const handleToggleConnection = async (server) => {
    try {
      if (server.connected) {
        await mcpApi.disconnectServer(server.name)
      } else {
        await mcpApi.connectServer(server.name)
      }
      await loadData()
    } catch (err) {
      setError(err.response?.data?.detail || err.message)
    }
  }

  const handleRemoveServer = async (serverName) => {
    if (!confirm(`Are you sure you want to remove server "${serverName}"?`)) return
    
    try {
      await mcpApi.removeServer(serverName)
      await loadData()
    } catch (err) {
      setError(err.response?.data?.detail || err.message)
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold">MCP Servers</h3>
          <p className="text-sm text-muted-foreground">
            Manage Model Context Protocol servers to provide tools and resources to the AI.
          </p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={loadData}
            className="p-2 text-muted-foreground hover:bg-accent rounded-lg transition-colors"
            title="Refresh"
          >
            <RefreshCw size={18} className={loading ? 'animate-spin' : ''} />
          </button>
          <button
            onClick={() => setShowAddModal(true)}
            className="flex items-center gap-2 px-3 py-2 bg-primary text-primary-foreground rounded-lg hover:opacity-90 transition-opacity text-sm"
          >
            <Plus size={16} />
            Add Server
          </button>
        </div>
      </div>

      {error && (
        <div className="p-3 bg-red-500/10 text-red-600 rounded-lg flex items-center gap-2 text-sm">
          <AlertCircle size={16} />
          {error}
        </div>
      )}

      {/* Servers List */}
      <div className="grid gap-4">
        {servers.map(server => (
          <div key={server.name} className="border border-border rounded-lg p-4 bg-card">
            <div className="flex items-start justify-between mb-4">
              <div className="flex items-center gap-3">
                <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${server.connected ? 'bg-green-500/10 text-green-600' : 'bg-muted text-muted-foreground'}`}>
                  <Terminal size={20} />
                </div>
                <div>
                  <div className="font-medium flex items-center gap-2">
                    {server.name}
                    {server.connected && <span className="text-xs bg-green-500/20 text-green-600 px-1.5 py-0.5 rounded">Connected</span>}
                  </div>
                  <div className="text-xs text-muted-foreground font-mono mt-1">
                    {server.command} {server.args.join(' ')}
                  </div>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => handleToggleConnection(server)}
                  className={`p-2 rounded-lg transition-colors ${server.connected ? 'bg-red-500/10 text-red-600 hover:bg-red-500/20' : 'bg-green-500/10 text-green-600 hover:bg-green-500/20'}`}
                  title={server.connected ? "Disconnect" : "Connect"}
                >
                  <Power size={18} />
                </button>
                <button
                  onClick={() => handleRemoveServer(server.name)}
                  className="p-2 text-muted-foreground hover:bg-accent rounded-lg transition-colors"
                  title="Remove"
                >
                  <Trash2 size={18} />
                </button>
              </div>
            </div>

            {/* Server Stats/Tools */}
            <div className="text-sm text-muted-foreground pt-4 border-t border-border">
              <div className="flex items-center gap-4">
                <div className="flex items-center gap-1.5">
                  <Box size={14} />
                  <span>{tools.filter(t => t.server === server.name).length} tools available</span>
                </div>
                {server.env && Object.keys(server.env).length > 0 && (
                  <div className="flex items-center gap-1.5">
                    <CheckCircle size={14} />
                    <span>Env vars configured</span>
                  </div>
                )}
              </div>
            </div>
          </div>
        ))}

        {servers.length === 0 && !loading && (
          <div className="text-center py-8 text-muted-foreground border border-dashed border-border rounded-lg">
            No MCP servers configured. Add one to get started.
          </div>
        )}
      </div>

      {/* Available Tools Summary */}
      {tools.length > 0 && (
        <div className="space-y-4 pt-6 border-t border-border">
          <h4 className="font-medium flex items-center gap-2">
            <Box size={18} />
            Available Tools ({tools.length})
          </h4>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {tools.map((tool, i) => (
              <div key={i} className="p-3 border border-border rounded-lg text-sm">
                <div className="font-medium mb-1 flex items-center justify-between">
                  {tool.name}
                  <span className="text-xs text-muted-foreground bg-muted px-1.5 py-0.5 rounded">
                    {tool.server}
                  </span>
                </div>
                <div className="text-muted-foreground text-xs line-clamp-2" title={tool.description}>
                  {tool.description}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Add Server Modal */}
      {showAddModal && (
        <div className="fixed inset-0 z-50 bg-background/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-card w-full max-w-lg border border-border rounded-xl shadow-lg flex flex-col max-h-[90vh]">
            <div className="flex items-center justify-between p-4 border-b border-border">
              <h3 className="font-semibold">Add MCP Server</h3>
              <button 
                onClick={() => setShowAddModal(false)}
                className="p-1 hover:bg-accent rounded"
              >
                <XCircle size={20} />
              </button>
            </div>
            
            <form onSubmit={handleAddServer} className="p-4 space-y-4 overflow-y-auto">
              <div>
                <label className="block text-sm font-medium mb-1">Name</label>
                <input
                  type="text"
                  required
                  value={newServer.name}
                  onChange={e => setNewServer({...newServer, name: e.target.value})}
                  placeholder="e.g. filesystem"
                  className="w-full px-3 py-2 border border-border rounded-lg bg-background focus:outline-none focus:ring-2 focus:ring-ring text-sm"
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-1">Command</label>
                <input
                  type="text"
                  required
                  value={newServer.command}
                  onChange={e => setNewServer({...newServer, command: e.target.value})}
                  placeholder="e.g. npx, python, node"
                  className="w-full px-3 py-2 border border-border rounded-lg bg-background focus:outline-none focus:ring-2 focus:ring-ring text-sm"
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-1">Arguments (one per line)</label>
                <textarea
                  value={newServer.args}
                  onChange={e => setNewServer({...newServer, args: e.target.value})}
                  placeholder="-y&#10;@modelcontextprotocol/server-filesystem&#10;/path/to/allow"
                  className="w-full px-3 py-2 border border-border rounded-lg bg-background focus:outline-none focus:ring-2 focus:ring-ring text-sm font-mono h-24"
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-1">Environment Variables</label>
                <textarea
                  value={newServer.env}
                  onChange={e => setNewServer({...newServer, env: e.target.value})}
                  placeholder="KEY=VALUE&#10;ANOTHER_KEY=VALUE"
                  className="w-full px-3 py-2 border border-border rounded-lg bg-background focus:outline-none focus:ring-2 focus:ring-ring text-sm font-mono h-24"
                />
                <p className="text-xs text-muted-foreground mt-1">
                  Format: KEY=VALUE (one per line) or JSON object
                </p>
              </div>

              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={newServer.enabled}
                  onChange={e => setNewServer({...newServer, enabled: e.target.checked})}
                  className="w-4 h-4"
                />
                <span className="text-sm">Enable immediately</span>
              </label>

              <div className="flex gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowAddModal(false)}
                  className="flex-1 px-4 py-2 border border-border rounded-lg hover:bg-accent transition-colors text-sm"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={loading}
                  className="flex-1 px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:opacity-90 transition-opacity text-sm flex items-center justify-center gap-2"
                >
                  {loading ? <RefreshCw size={16} className="animate-spin" /> : <Plus size={16} />}
                  Add Server
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
