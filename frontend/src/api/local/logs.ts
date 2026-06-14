import type { QSOLog } from '@/types'

const KEY = 'radiomanager_logs'

function read(): QSOLog[] {
  return JSON.parse(localStorage.getItem(KEY) || '[]')
}

function write(data: QSOLog[]) {
  localStorage.setItem(KEY, JSON.stringify(data))
}

export const logsApiLocal = {
  async create(data: any): Promise<QSOLog> {
    const logs = read()
    const newLog = { ...data, id: Date.now() }
    logs.push(newLog)
    write(logs)
    return newLog
  },

  async list(): Promise<any> {
    const logs = read()
    return {
      items: logs,
      total: logs.length,
      page: 1,
      page_size: logs.length,
      pages: 1
    }
  },

  async get(id: number) {
    const logs = read()
    return logs.find(l => l.id === id)
  },

  async update(id: number, data: any) {
    const logs = read()
    const idx = logs.findIndex(l => l.id === id)
    if (idx !== -1) {
      logs[idx] = { ...logs[idx], ...data }
      write(logs)
    }
    return logs[idx]
  },

  async delete(id: number) {
    const logs = read().filter(l => l.id !== id)
    write(logs)
    return true
  },

  async getStats() {
    const logs = read()
    return { total: logs.length }
  }
}