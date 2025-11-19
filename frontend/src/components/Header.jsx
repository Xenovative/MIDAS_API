import { Menu, Sparkles, LogOut, User as UserIcon } from 'lucide-react'
import { useStore } from '../store/useStore'
import ModelSelector from './ModelSelector'

export default function Header() {
  const { toggleSidebar, useAgent, setUseAgent, user, logout } = useStore()

  return (
    <header className="h-16 border-b border-border bg-background flex items-center justify-between px-4">
      <div className="flex items-center gap-4">
        <button
          onClick={toggleSidebar}
          className="p-2 hover:bg-accent rounded-lg transition-colors"
        >
          <Menu size={20} />
        </button>
        <div className="flex items-center gap-2">
          <Sparkles size={24} className="text-primary" />
          <h1 className="text-xl font-bold">MIDAS</h1>
        </div>
      </div>

      <div className="flex items-center gap-4">
        <label className="flex items-center gap-2 text-sm cursor-pointer">
          <input
            type="checkbox"
            checked={useAgent}
            onChange={(e) => setUseAgent(e.target.checked)}
            className="rounded border-border"
          />
          <span>Agent Mode</span>
        </label>
        <ModelSelector />
        
        {user && (
          <div className="flex items-center gap-2">
            <div className="flex items-center gap-2 px-3 py-1.5 bg-muted rounded-lg text-sm">
              <UserIcon size={14} />
              <span>{user.username}</span>
              <span className="text-xs bg-primary/20 text-primary px-1.5 py-0.5 rounded">
                {user.role}
              </span>
            </div>
            <button
              onClick={logout}
              className="p-2 hover:bg-accent rounded-lg transition-colors"
              title="Logout"
            >
              <LogOut size={18} />
            </button>
          </div>
        )}
      </div>
    </header>
  )
}
