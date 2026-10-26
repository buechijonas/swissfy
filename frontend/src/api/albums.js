import api from '@/api/client.js'

export default {
  get(id) {
    return api.get(`/api/albums/${id}/`)
  },
  ofUser(username) {
    return api.get(`/api/posts/users/${encodeURIComponent(username)}/albums/`)
  },
  create(body) {
    return api.post('/api/albums/', body)
  },
  update(id, body) {
    return api.patch(`/api/albums/${id}/`, body)
  },
  remove(id) {
    return api.delete(`/api/albums/${id}/`)
  },
  reorder(ids) {
    return api.put('/api/albums/order/', { albums: ids })
  },
  addEntries(id, entries) {
    return api.post(`/api/albums/${id}/entries/`, { entries })
  },
  updateEntry(id, body) {
    return api.patch(`/api/album-entries/${id}/`, body)
  },
  removeEntry(id) {
    return api.delete(`/api/album-entries/${id}/`)
  },
}
