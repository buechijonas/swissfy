import api from '@/api/client.js'

export function collectionApi(url) {
  return {
    list() {
      return api.get(url)
    },
    create(body) {
      return api.post(url, body)
    },
    update(id, body) {
      return api.patch(`${url}${id}/`, body)
    },
    remove(id) {
      return api.delete(`${url}${id}/`)
    },
  }
}

export const foldersApi = collectionApi('/api/posts/folders/')

export const groupsApi = collectionApi('/api/posts/groups/')
