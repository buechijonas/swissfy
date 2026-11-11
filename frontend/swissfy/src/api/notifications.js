import api from '@core/api/client.js'

export default {
  listUrl() {
    return '/api/notifications/'
  },
  list(page) {
    return api.get(page)
  },
  unread() {
    return api.get('/api/notifications/unread/')
  },
  markRead() {
    return api.post('/api/notifications/read/')
  },
}
