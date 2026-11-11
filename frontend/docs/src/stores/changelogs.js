import { acceptHMRUpdate, defineStore } from 'pinia'
import api from '@core/api/client.js'

const API = '/api/docs/changelogs'

export const useChangelogsStore = defineStore('changelogs', () => {
  const list = () => api.get(`${API}/`)
  const get = (version) => api.get(`${API}/${encodeURIComponent(version)}/`)

  return { list, get }
})

if (import.meta.hot) {
  import.meta.hot.accept(acceptHMRUpdate(useChangelogsStore, import.meta.hot))
}
