import map from 'lodash-es/map'
import reject from 'lodash-es/reject'
import { reactive, toValue } from 'vue'
import api, { nextPage } from '@core/api/client.js'

function postId(post) {
  return post.id
}

export function usePostFeed({ url, loadError, initial = [], key = postId }) {
  const feed = reactive({
    posts: [...initial],
    nextUrl: null,
    hasMore: Boolean(toValue(url)),
    loading: false,
    error: null,
    key,
    onSentinel(visible) {
      if (visible) feed.loadMore()
    },
    async loadMore() {
      if (feed.loading || !feed.hasMore || feed.error) return
      feed.loading = true
      try {
        const data = await api.get(feed.nextUrl ?? toValue(url))
        const known = new Set(map(feed.posts, key))
        feed.posts.push(...reject(data.results, (post) => known.has(key(post))))
        feed.nextUrl = nextPage(data.next)
        feed.hasMore = Boolean(feed.nextUrl)
      } catch {
        feed.error = toValue(loadError)
      } finally {
        feed.loading = false
      }
    },
    replace(post) {
      feed.posts = map(feed.posts, (item) => (key(item) === key(post) ? post : item))
    },
    remove(predicate) {
      feed.posts = reject(feed.posts, predicate)
    },
  })
  return feed
}
