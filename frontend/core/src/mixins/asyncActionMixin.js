export default {
  data() {
    return {
      busy: false,
      error: null,
    }
  },
  methods: {
    async runAction(action, fallback = null) {
      this.busy = true
      this.error = null
      try {
        return await action()
      } catch (error) {
        this.error = error.detail ?? fallback ?? error.message
        return null
      } finally {
        this.busy = false
      }
    },
  },
}
