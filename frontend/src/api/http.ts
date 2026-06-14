// import axios from 'axios'

// export function createHttpAPI() {
//   const mode = import.meta.env.VITE_MODE

//   const instance = axios.create({
//     baseURL:
//       mode === 'cloud'
//         ? 'https://your-domain.com/api/v1'
//         : 'http://localhost:8000/api/v1',
//     timeout: 10000
//   })

//   return {
//     async getLogs() {
//       return (await instance.get('/logs')).data
//     },

//     async createLog(data: any) {
//       return (await instance.post('/logs', data)).data
//     },

//     async deleteLog(id: number) {
//       return (await instance.delete(`/logs/${id}`)).data
//     }
//   }
// }

import axios from 'axios'

const instance = axios.create({
  baseURL: '/api/v1',
  timeout: 10000
})

export default instance