import map from 'lodash-es/map'
import api, { nextPage } from '@core/api/client.js'

export default {
  data() {
    return {
      posts: [],
      nextUrl: null,
      hasMore: true,
      loading: false,
      error: null,
    }
  },
  methods: {
    postKey(post) {
      return post.id
    },
    appendPosts(posts) {
      this.posts.push(...posts)
    },
    onSentinel(visible) {
      if (visible) this.loadMore()
    },
    async loadMore() {
      if (this.loading || !this.hasMore || this.error) return
      this.loading = true
      try {
        const data = await api.get(this.nextUrl ?? this.url)
        this.appendPosts(data.results)
        this.nextUrl = nextPage(data.next)
        this.hasMore = Boolean(this.nextUrl)
      } catch {
        this.error = this.loadError
      } finally {
        this.loading = false
      }
    },
    replace(post) {
      this.posts = map(this.posts, (item) =>
        this.postKey(item) === this.postKey(post) ? post : item,
      )
    },
  },
}
