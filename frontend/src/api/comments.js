import api from '@/api/client.js'

export default {
  get(id) {
    return api.get(`/api/comments/${id}/`)
  },
  repliesUrl(id) {
    return `/api/comments/${id}/replies/`
  },
  list(url, cursor) {
    return api.get(url, cursor ? { cursor } : null)
  },
  create(url, text) {
    return api.post(url, { text })
  },
  remove(id) {
    return api.delete(`/api/comments/${id}/`)
  },
  vote(id, value) {
    return api.put(`/api/comments/${id}/vote/`, { value })
  },
  report(id) {
    return api.post(`/api/comments/${id}/report/`)
  },
}
