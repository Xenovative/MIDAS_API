import { create } from 'zustand'

export const useStore = create((set, get) => ({
  // Auth
  user: null,
  isAuthenticated: false,
  setUser: (user) => set({ user, isAuthenticated: !!user }),
  logout: () => {
    localStorage.removeItem('auth_token')
    localStorage.removeItem('user')
    set({ user: null, isAuthenticated: false, conversations: [], currentConversation: null })
  },
  
  // Conversations
  conversations: [],
  currentConversation: null,
  
  setConversations: (conversations) => set({ conversations }),
  setCurrentConversation: (conversation) => set((state) => {
    // Also update the conversation in the conversations array if it exists
    const exists = state.conversations.some(c => c.id === conversation?.id)
    if (exists && conversation) {
      return {
        currentConversation: conversation,
        conversations: state.conversations.map(c => 
          c.id === conversation.id ? conversation : c
        )
      }
    }
    return { currentConversation: conversation }
  }),
  addConversation: (conversation) => set((state) => {
    // Check if conversation already exists
    const exists = state.conversations.some(c => c.id === conversation.id)
    if (exists) {
      return {
        conversations: state.conversations.map(c => 
          c.id === conversation.id ? conversation : c
        )
      }
    }
    return {
      conversations: [conversation, ...state.conversations]
    }
  }),
  removeConversation: (id) => set((state) => ({
    conversations: state.conversations.filter(c => c.id !== id)
  })),
  updateConversation: (id, updates) => set((state) => ({
    conversations: state.conversations.map(c => 
      c.id === id ? { ...c, ...updates } : c
    )
  })),
  
  // Messages
  addMessage: (message) => set((state) => {
    if (!state.currentConversation) return state
    
    const updatedConversation = {
      ...state.currentConversation,
      messages: [...(state.currentConversation.messages || []), message],
      updated_at: new Date().toISOString()
    }
    
    // Update both currentConversation and the conversation in the conversations array
    return {
      currentConversation: updatedConversation,
      conversations: state.conversations.map(c => 
        c.id === state.currentConversation.id ? updatedConversation : c
      )
    }
  }),
  
  // Models
  providers: [],
  selectedModel: null,
  selectedProvider: null,
  selectedBot: (() => {
    try {
      const stored = localStorage.getItem('selectedBot')
      return stored ? JSON.parse(stored) : null
    } catch {
      return null
    }
  })(),
  
  setProviders: (providers) => set({ providers }),
  setSelectedModel: (model, provider) => set({ 
    selectedModel: model, 
    selectedProvider: provider 
  }),
  setSelectedBot: (bot) => {
    // Persist bot to localStorage
    if (bot) {
      localStorage.setItem('selectedBot', JSON.stringify(bot))
    } else {
      localStorage.removeItem('selectedBot')
    }
    set({ selectedBot: bot })
  },
  
  // UI State
  sidebarOpen: true,
  toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),
  
  // Settings
  temperature: 0.7,
  maxTokens: null,
  useAgent: false,
  imageRatio: '1:1',
  imageSize: '1024x1024',
  useRealtimeData: (() => {
    try {
      const stored = localStorage.getItem('useRealtimeData')
      return stored ? JSON.parse(stored) : false
    } catch {
      return false
    }
  })(),
  useDeepResearch: (() => {
    try {
      const stored = localStorage.getItem('useDeepResearch')
      return stored ? JSON.parse(stored) : false
    } catch {
      return false
    }
  })(),
  streamResponse: true,
  systemPrompt: '',
  setTemperature: (temperature) => set({ temperature }),
  setMaxTokens: (maxTokens) => set({ maxTokens }),
  setUseAgent: (useAgent) => set({ useAgent }),
  setImageRatio: (ratio, size) => set({ imageRatio: ratio, imageSize: size }),
  setUseRealtimeData: (useRealtimeData) => {
    try {
      localStorage.setItem('useRealtimeData', JSON.stringify(useRealtimeData))
    } catch (err) {
      console.warn('Failed to persist realtime toggle', err)
    }
    set({ useRealtimeData })
  },
  setUseDeepResearch: (useDeepResearch) => {
    try {
      localStorage.setItem('useDeepResearch', JSON.stringify(useDeepResearch))
    } catch (err) {
      console.warn('Failed to persist deep research toggle', err)
    }
    set({ useDeepResearch })
  },
  setStreamResponse: (streamResponse) => set({ streamResponse }),
  setSystemPrompt: (systemPrompt) => set({ systemPrompt }),
}))
