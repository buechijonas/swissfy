import api, { withParams } from '@/api/client.js'

function postPath(id, ...segments) {
  return ['/api/posts', id, ...segments, ''].join('/')
}

function hashtagPath(name, ...segments) {
  return postPath('hashtags', encodeURIComponent(name), ...segments)
}

export default {
  get(id) {
    return api.get(postPath(id))
  },
  create(formData) {
    return api.post('/api/posts/', formData)
  },
  update(id, body) {
    return api.patch(postPath(id), body)
  },
  remove(id) {
    return api.delete(postPath(id))
  },
  quota() {
    return api.get('/api/posts/quota/')
  },
  like(id) {
    return api.post(postPath(id, 'like'))
  },
  unlike(id) {
    return api.delete(postPath(id, 'like'))
  },
  repost(id) {
    return api.post(postPath(id, 'repost'))
  },
  unrepost(id) {
    return api.delete(postPath(id, 'repost'))
  },
  save(id, folder) {
    return api.put(postPath(id, 'save'), { folder })
  },
  unsave(id) {
    return api.delete(postPath(id, 'save'))
  },
  report(id) {
    return api.post(postPath(id, 'report'))
  },
  searchHashtags(query) {
    return api.get('/api/posts/hashtags/', { q: query })
  },
  hashtag(name) {
    return api.get(hashtagPath(name))
  },
  followHashtag(name) {
    return api.put(hashtagPath(name, 'follow'))
  },
  unfollowHashtag(name) {
    return api.delete(hashtagPath(name, 'follow'))
  },
  feedUrl() {
    return '/api/posts/'
  },
  reelsUrl() {
    return '/api/posts/reels/'
  },
  savedUrl(folder) {
    return withParams('/api/posts/saved/', folder ? { folder } : null)
  },
  userPostsUrl(username, params) {
    return withParams(postPath('users', encodeURIComponent(username)), params)
  },
  hashtagPostsUrl(name, params) {
    return withParams(hashtagPath(name, 'posts'), params)
  },
  commentsUrl(id) {
    return postPath(id, 'comments')
  },
}
