import { useState, useEffect } from 'react'
import { Users, UserPlus, Edit2, Trash2, Shield, Crown, User as UserIcon, Ban, CheckCircle, XCircle, Loader2, Search } from 'lucide-react'
import { adminApi } from '../lib/api'
import { useStore } from '../store/useStore'

export default function UserManagement() {
  const { user: currentUser } = useStore()
  const [users, setUsers] = useState([])
  const [loading, setLoading] = useState(true)
  const [searchTerm, setSearchTerm] = useState('')
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [showEditModal, setShowEditModal] = useState(false)
  const [selectedUser, setSelectedUser] = useState(null)
  const [stats, setStats] = useState(null)

  useEffect(() => {
    loadUsers()
    loadStats()
  }, [])

  const loadUsers = async () => {
    try {
      setLoading(true)
      const response = await adminApi.listUsers()
      setUsers(response.data.users)
    } catch (error) {
      console.error('Failed to load users:', error)
      alert('Failed to load users: ' + (error.response?.data?.detail || error.message))
    } finally {
      setLoading(false)
    }
  }

  const loadStats = async () => {
    try {
      const response = await adminApi.getStats()
      setStats(response.data)
    } catch (error) {
      console.error('Failed to load stats:', error)
    }
  }

  const handleCreateUser = async (userData) => {
    try {
      await adminApi.createUser(userData)
      await loadUsers()
      await loadStats()
      setShowCreateModal(false)
    } catch (error) {
      console.error('Failed to create user:', error)
      alert('Failed to create user: ' + (error.response?.data?.detail || error.message))
    }
  }

  const handleUpdateUser = async (userId, updates) => {
    try {
      await adminApi.updateUser(userId, updates)
      await loadUsers()
      await loadStats()
      setShowEditModal(false)
      setSelectedUser(null)
    } catch (error) {
      console.error('Failed to update user:', error)
      alert('Failed to update user: ' + (error.response?.data?.detail || error.message))
    }
  }

  const handleDeleteUser = async (userId, username) => {
    if (!confirm(`Are you sure you want to delete user "${username}"? This will delete all their conversations and messages.`)) {
      return
    }

    try {
      await adminApi.deleteUser(userId)
      await loadUsers()
      await loadStats()
    } catch (error) {
      console.error('Failed to delete user:', error)
      alert('Failed to delete user: ' + (error.response?.data?.detail || error.message))
    }
  }

  const filteredUsers = users.filter(user =>
    user.username.toLowerCase().includes(searchTerm.toLowerCase()) ||
    user.email.toLowerCase().includes(searchTerm.toLowerCase())
  )

  const getRoleIcon = (role) => {
    switch (role) {
      case 'admin': return <Shield size={14} className="text-red-500" />
      case 'premium': return <Crown size={14} className="text-yellow-500" />
      case 'guest': return <UserIcon size={14} className="text-gray-500" />
      default: return <UserIcon size={14} className="text-blue-500" />
    }
  }

  const getRoleBadgeColor = (role) => {
    switch (role) {
      case 'admin': return 'bg-red-500/20 text-red-600 border-red-500/30'
      case 'premium': return 'bg-yellow-500/20 text-yellow-600 border-yellow-500/30'
      case 'guest': return 'bg-gray-500/20 text-gray-600 border-gray-500/30'
      default: return 'bg-blue-500/20 text-blue-600 border-blue-500/30'
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold">User Management</h3>
        <button
          onClick={() => setShowCreateModal(true)}
          className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:opacity-90 transition-opacity"
        >
          <UserPlus size={18} />
          Create User
        </button>
      </div>

      {/* Stats Cards */}
      {stats && (
        <div className="grid grid-cols-4 gap-4">
          <div className="p-4 border border-border rounded-lg bg-muted/30">
            <div className="text-2xl font-bold">{stats.users.total}</div>
            <div className="text-sm text-muted-foreground">Total Users</div>
          </div>
          <div className="p-4 border border-border rounded-lg bg-muted/30">
            <div className="text-2xl font-bold">{stats.users.active}</div>
            <div className="text-sm text-muted-foreground">Active Users</div>
          </div>
          <div className="p-4 border border-border rounded-lg bg-muted/30">
            <div className="text-2xl font-bold">{stats.users.by_role.admin}</div>
            <div className="text-sm text-muted-foreground">Admins</div>
          </div>
          <div className="p-4 border border-border rounded-lg bg-muted/30">
            <div className="text-2xl font-bold">{stats.users.guests}</div>
            <div className="text-sm text-muted-foreground">Guests</div>
          </div>
        </div>
      )}

      {/* Search */}
      <div className="relative">
        <Search size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" />
        <input
          type="text"
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          placeholder="Search users by username or email..."
          className="w-full pl-10 pr-4 py-2 border border-border rounded-lg bg-background focus:outline-none focus:ring-2 focus:ring-ring"
        />
      </div>

      {/* Users Table */}
      {loading ? (
        <div className="flex items-center justify-center py-12">
          <Loader2 size={32} className="animate-spin text-primary" />
        </div>
      ) : (
        <div className="border border-border rounded-lg overflow-hidden">
          <table className="w-full">
            <thead className="bg-muted/50 border-b border-border">
              <tr>
                <th className="text-left px-4 py-3 text-sm font-medium">User</th>
                <th className="text-left px-4 py-3 text-sm font-medium">Email</th>
                <th className="text-left px-4 py-3 text-sm font-medium">Role</th>
                <th className="text-left px-4 py-3 text-sm font-medium">Status</th>
                <th className="text-left px-4 py-3 text-sm font-medium">Created</th>
                <th className="text-right px-4 py-3 text-sm font-medium">Actions</th>
              </tr>
            </thead>
            <tbody>
              {filteredUsers.map((user) => (
                <tr key={user.id} className="border-b border-border hover:bg-muted/30 transition-colors">
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-2">
                      {getRoleIcon(user.role)}
                      <span className="font-medium">{user.username}</span>
                      {user.is_guest && (
                        <span className="text-xs bg-gray-500/20 text-gray-600 px-1.5 py-0.5 rounded">
                          Guest
                        </span>
                      )}
                    </div>
                  </td>
                  <td className="px-4 py-3 text-sm text-muted-foreground">{user.email}</td>
                  <td className="px-4 py-3">
                    <span className={`inline-flex items-center gap-1 px-2 py-1 rounded text-xs font-medium border ${getRoleBadgeColor(user.role)}`}>
                      {user.role}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    {user.is_active ? (
                      <span className="inline-flex items-center gap-1 text-xs text-green-600">
                        <CheckCircle size={14} />
                        Active
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1 text-xs text-red-600">
                        <XCircle size={14} />
                        Inactive
                      </span>
                    )}
                  </td>
                  <td className="px-4 py-3 text-sm text-muted-foreground">
                    {new Date(user.created_at).toLocaleDateString()}
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex items-center justify-end gap-2">
                      <button
                        onClick={() => {
                          setSelectedUser(user)
                          setShowEditModal(true)
                        }}
                        className="p-1.5 hover:bg-accent rounded transition-colors"
                        title="Edit user"
                      >
                        <Edit2 size={16} />
                      </button>
                      {user.id !== currentUser?.id && (
                        <button
                          onClick={() => handleDeleteUser(user.id, user.username)}
                          className="p-1.5 hover:bg-red-500/10 text-red-600 rounded transition-colors"
                          title="Delete user"
                        >
                          <Trash2 size={16} />
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {filteredUsers.length === 0 && (
            <div className="text-center py-12 text-muted-foreground">
              No users found
            </div>
          )}
        </div>
      )}

      {/* Create User Modal */}
      {showCreateModal && (
        <CreateUserModal
          onClose={() => setShowCreateModal(false)}
          onCreate={handleCreateUser}
        />
      )}

      {/* Edit User Modal */}
      {showEditModal && selectedUser && (
        <EditUserModal
          user={selectedUser}
          currentUser={currentUser}
          onClose={() => {
            setShowEditModal(false)
            setSelectedUser(null)
          }}
          onUpdate={handleUpdateUser}
        />
      )}
    </div>
  )
}

function CreateUserModal({ onClose, onCreate }) {
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    password: '',
    role: 'free'
  })
  const [creating, setCreating] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setCreating(true)
    try {
      await onCreate(formData)
    } finally {
      setCreating(false)
    }
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50" onClick={onClose}>
      <div className="bg-background border border-border rounded-lg w-full max-w-md p-6" onClick={(e) => e.stopPropagation()}>
        <h3 className="text-lg font-semibold mb-4">Create New User</h3>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-1">Username</label>
            <input
              type="text"
              value={formData.username}
              onChange={(e) => setFormData({ ...formData, username: e.target.value })}
              className="w-full px-3 py-2 border border-border rounded-lg bg-background focus:outline-none focus:ring-2 focus:ring-ring"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Email</label>
            <input
              type="email"
              value={formData.email}
              onChange={(e) => setFormData({ ...formData, email: e.target.value })}
              className="w-full px-3 py-2 border border-border rounded-lg bg-background focus:outline-none focus:ring-2 focus:ring-ring"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Password</label>
            <input
              type="password"
              value={formData.password}
              onChange={(e) => setFormData({ ...formData, password: e.target.value })}
              className="w-full px-3 py-2 border border-border rounded-lg bg-background focus:outline-none focus:ring-2 focus:ring-ring"
              required
              minLength={6}
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Role</label>
            <select
              value={formData.role}
              onChange={(e) => setFormData({ ...formData, role: e.target.value })}
              className="w-full px-3 py-2 border border-border rounded-lg bg-background focus:outline-none focus:ring-2 focus:ring-ring"
            >
              <option value="free">Free</option>
              <option value="premium">Premium</option>
              <option value="admin">Admin</option>
            </select>
          </div>
          <div className="flex gap-2 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 px-4 py-2 border border-border rounded-lg hover:bg-accent transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={creating}
              className="flex-1 px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:opacity-90 transition-opacity disabled:opacity-50"
            >
              {creating ? 'Creating...' : 'Create User'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

function EditUserModal({ user, currentUser, onClose, onUpdate }) {
  const [formData, setFormData] = useState({
    role: user.role,
    is_active: user.is_active,
    email: user.email
  })
  const [updating, setUpdating] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setUpdating(true)
    try {
      const updates = {}
      if (formData.role !== user.role) updates.role = formData.role
      if (formData.is_active !== user.is_active) updates.is_active = formData.is_active
      if (formData.email !== user.email) updates.email = formData.email
      
      if (Object.keys(updates).length > 0) {
        await onUpdate(user.id, updates)
      } else {
        onClose()
      }
    } finally {
      setUpdating(false)
    }
  }

  const isSelf = user.id === currentUser?.id

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50" onClick={onClose}>
      <div className="bg-background border border-border rounded-lg w-full max-w-md p-6" onClick={(e) => e.stopPropagation()}>
        <h3 className="text-lg font-semibold mb-4">Edit User: {user.username}</h3>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-1">Email</label>
            <input
              type="email"
              value={formData.email}
              onChange={(e) => setFormData({ ...formData, email: e.target.value })}
              className="w-full px-3 py-2 border border-border rounded-lg bg-background focus:outline-none focus:ring-2 focus:ring-ring"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Role</label>
            <select
              value={formData.role}
              onChange={(e) => setFormData({ ...formData, role: e.target.value })}
              className="w-full px-3 py-2 border border-border rounded-lg bg-background focus:outline-none focus:ring-2 focus:ring-ring"
              disabled={isSelf}
            >
              <option value="free">Free</option>
              <option value="premium">Premium</option>
              <option value="admin">Admin</option>
              <option value="guest">Guest</option>
            </select>
            {isSelf && (
              <p className="text-xs text-muted-foreground mt-1">You cannot change your own role</p>
            )}
          </div>
          <div>
            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={formData.is_active}
                onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
                className="rounded border-border"
                disabled={isSelf}
              />
              <span className="text-sm">Active</span>
            </label>
            {isSelf && (
              <p className="text-xs text-muted-foreground mt-1">You cannot deactivate your own account</p>
            )}
          </div>
          <div className="flex gap-2 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 px-4 py-2 border border-border rounded-lg hover:bg-accent transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={updating}
              className="flex-1 px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:opacity-90 transition-opacity disabled:opacity-50"
            >
              {updating ? 'Updating...' : 'Update User'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
