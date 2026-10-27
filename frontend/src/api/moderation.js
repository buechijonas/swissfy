import api, { withParams } from '@/api/client.js'

function targetPath(kind, id, ...segments) {
  return ['/api/moderation', kind, id, ...segments, ''].join('/')
}

export default {
  reportsUrl(status) {
    return withParams('/api/moderation/reports/', { status })
  },
  list(page) {
    return api.get(page)
  },
  get(kind, id) {
    return api.get(targetPath(kind, id))
  },
  childrenUrl(kind, id) {
    return targetPath(kind, id, kind === 'posts' ? 'comments' : 'replies')
  },
  warn(kind, id, reason) {
    return api.post(targetPath(kind, id, 'warnings'), { reason })
  },
  dismiss(kind, id) {
    return api.post(targetPath(kind, id, 'dismiss'), {})
  },
}
