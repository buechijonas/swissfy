import api, { withParams } from '@/api/client.js'

export default {
  roles() {
    return api.get('/api/administration/roles/')
  },
  usersUrl(params) {
    return withParams('/api/administration/users/', params)
  },
  list(page) {
    return api.get(page)
  },
  setRole(username, role) {
    return api.patch(`/api/administration/users/${encodeURIComponent(username)}/`, { role })
  },
}
