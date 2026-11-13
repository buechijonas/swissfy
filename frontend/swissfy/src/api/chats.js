import api from '@core/api/client.js'

function chatPath(username, ...segments) {
  return ['/api/chats', encodeURIComponent(username), ...segments, ''].join('/')
}

export default {
  requests() {
    return api.get('/api/chats/requests/')
  },
  conversations() {
    return api.get('/api/chats/conversations/')
  },
  markDelivered() {
    return api.post('/api/chats/delivered/')
  },
  archive(username) {
    return api.post(chatPath(username, 'archive'))
  },
  unarchive(username) {
    return api.delete(chatPath(username, 'archive'))
  },
  keys(username) {
    return api.get(chatPath(username, 'keys'))
  },
  receive(username, read) {
    return api.post(chatPath(username, 'receive'), { read })
  },
  messages(username, params) {
    return api.get(chatPath(username, 'messages'), params)
  },
  send(username, payload) {
    return api.post(chatPath(username, 'messages'), payload)
  },
  updateRequest(username, action) {
    if (action === 'send') return api.post(chatPath(username, 'request'))
    if (action === 'decline') return api.delete(chatPath(username, 'request'))
    return api.post(chatPath(username, 'request', action))
  },
  protection() {
    return api.get('/api/chats/protection/')
  },
  setProtection(body) {
    return api.put('/api/chats/protection/', body)
  },
  createKey(publicKey) {
    return api.post('/api/chats/keys/', { public_key: publicKey })
  },
}
