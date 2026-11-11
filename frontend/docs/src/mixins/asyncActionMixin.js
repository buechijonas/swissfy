export default {
  data() {
    return {
      error: '',
      saving: false,
    }
  },
  methods: {
    async runAction(fn) {
      this.error = ''
      this.saving = true
      try {
        return await fn()
      } catch (e) {
        this.error = e.message
      } finally {
        this.saving = false
      }
    },
  },
}
