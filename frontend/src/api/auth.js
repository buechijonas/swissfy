import api from '@/api/client.js'

export default {
  loginUrl() {
    return '/api/auth/oidc/login/'
  },
  accountUrl() {
    return '/api/auth/oidc/account/'
  },
  me() {
    return api.get('/api/auth/me/')
  },
  logout() {
    return api.post('/api/auth/logout/')
  },
  acceptConsent(field) {
    return api.post(`/api/auth/consent/${field}/`)
  },
  syncDevice(token) {
    return api.post('/api/auth/device/', { token })
  },
  forgetDevice() {
    return api.delete('/api/auth/device/')
  },
  restoreDevice(token) {
    return api.post('/api/auth/device/restore/', { token })
  },
}
