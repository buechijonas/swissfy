import api from '@/api/client.js'

const REQUEST_ENDPOINTS = {
  follow_request: 'follow-requests',
  friend_request: 'friend-requests',
}

function profilePath(username, ...segments) {
  const name = username ? encodeURIComponent(username) : 'me'
  return ['/api/social/profiles', name, ...segments, ''].join('/')
}

function requestPath(kind, username) {
  return profilePath(null, REQUEST_ENDPOINTS[kind], encodeURIComponent(username))
}

export default {
  get(username) {
    return api.get(profilePath(username))
  },
  follow(username) {
    return api.post(profilePath(username, 'follow'))
  },
  unfollow(username) {
    return api.delete(profilePath(username, 'follow'))
  },
  requestFriendship(username) {
    return api.post(profilePath(username, 'friend-request'))
  },
  acceptRequest(kind, username) {
    return api.post(requestPath(kind, username))
  },
  declineRequest(kind, username) {
    return api.delete(requestPath(kind, username))
  },
  achievements(username) {
    return api.get(profilePath(username, 'achievements'))
  },
  status(username) {
    return api.get(profilePath(username, 'status'))
  },
  about() {
    return api.get(profilePath(null, 'about'))
  },
  updateAbout(changes) {
    return api.patch(profilePath(null, 'about'), changes)
  },
  pictures() {
    return api.get(profilePath(null, 'pictures'))
  },
  updatePictures(body) {
    return api.patch(profilePath(null, 'pictures'), body)
  },
  removePicture(kind) {
    return api.delete(profilePath(null, 'pictures', kind))
  },
  privacy() {
    return api.get(profilePath(null, 'privacy'))
  },
  updatePrivacy(changes) {
    return api.patch(profilePath(null, 'privacy'), changes)
  },
  listUrl() {
    return '/api/social/profiles/'
  },
  connectionsUrl(username, connection) {
    return profilePath(username, connection)
  },
  searchLibrary(kind, query) {
    return api.get(`/api/social/library/${kind}/`, { q: query })
  },
}
