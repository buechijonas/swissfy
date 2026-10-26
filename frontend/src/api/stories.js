import api from '@/api/client.js'

export default {
  create(formData) {
    return api.post('/api/stories/', formData)
  },
  remove(id) {
    return api.delete(`/api/stories/${id}/`)
  },
  view(id) {
    return api.post(`/api/stories/${id}/view/`)
  },
  like(id) {
    return api.post(`/api/stories/${id}/like/`)
  },
  unlike(id) {
    return api.delete(`/api/stories/${id}/like/`)
  },
  viewersUrl(id) {
    return `/api/stories/${id}/viewers/`
  },
}
