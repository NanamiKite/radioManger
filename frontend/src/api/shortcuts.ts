import api from './index'

export interface Shortcut {
  id: number
  name: string
  url: string
  description?: string
}

export const shortcutsApi = {
  list(): Promise<Shortcut[]> {
    return api.get('/shortcuts')
  },

  create(data: { name: string; url: string; description?: string }): Promise<Shortcut> {
    return api.post('/shortcuts', data)
  },

  delete(id: number): Promise<void> {
    return api.delete(`/shortcuts/${id}`)
  }
}
