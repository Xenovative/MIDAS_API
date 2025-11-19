import { useEffect, useState } from 'react'
import { useStore } from './store/useStore'
import { conversationsApi, authApi } from './lib/api'
import { ThemeProvider } from './contexts/ThemeContext'
import Sidebar from './components/Sidebar'
import Header from './components/Header'
import ChatArea from './components/ChatArea'
import Login from './components/Login'

function App() {
  const { setConversations, setUser, isAuthenticated } = useStore()
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    checkAuth()
  }, [])

  const checkAuth = async () => {
    const token = localStorage.getItem('auth_token')
    const savedUser = localStorage.getItem('user')
    
    if (token && savedUser) {
      try {
        // Verify token is still valid
        const response = await authApi.getCurrentUser()
        setUser(response.data)
        await loadConversations()
      } catch (error) {
        console.error('Auth check failed:', error)
        localStorage.removeItem('auth_token')
        localStorage.removeItem('user')
      }
    }
    
    setIsLoading(false)
  }

  const loadConversations = async () => {
    try {
      const response = await conversationsApi.list()
      setConversations(response.data)
    } catch (error) {
      console.error('Failed to load conversations:', error)
    }
  }

  const handleLogin = async (user) => {
    if (user === null) {
      // Guest mode - set a flag
      setUser({ username: 'Guest', role: 'guest', is_guest: true })
    } else {
      setUser(user)
    }
    await loadConversations()
  }

  if (isLoading) {
    return (
      <div className="flex h-screen items-center justify-center bg-background">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
          <p className="text-muted-foreground">Loading...</p>
        </div>
      </div>
    )
  }

  if (!isAuthenticated) {
    return (
      <ThemeProvider>
        <Login onLogin={handleLogin} />
      </ThemeProvider>
    )
  }

  return (
    <ThemeProvider>
      <div className="flex h-screen bg-background text-foreground">
        <Sidebar />
        <div className="flex-1 flex flex-col">
          <Header />
          <ChatArea />
        </div>
      </div>
    </ThemeProvider>
  )
}

export default App
