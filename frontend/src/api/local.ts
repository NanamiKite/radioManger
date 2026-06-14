const KEY = 'radiomanager_logs'

export function createLocalAPI() {
  return {
    async getLogs() {
      return JSON.parse(localStorage.getItem(KEY) || '[]')
    },

    async createLog(log: any) {
      const logs = JSON.parse(localStorage.getItem(KEY) || '[]')
      logs.push({ ...log, id: Date.now() })
      localStorage.setItem(KEY, JSON.stringify(logs))
      return log
    },

    async deleteLog(id: number) {
      let logs = JSON.parse(localStorage.getItem(KEY) || '[]')
      logs = logs.filter((l: any) => l.id !== id)
      localStorage.setItem(KEY, JSON.stringify(logs))
      return true
    }
  }
}