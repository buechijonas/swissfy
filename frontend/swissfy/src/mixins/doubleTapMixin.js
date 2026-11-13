import { useTimeoutFn } from '@vueuse/core'

const DOUBLE_TAP_MS = 250

export default {
  computed: {
    tapPending() {
      return this.tapTimer.isPending.value
    },
  },
  created() {
    this.tapTimer = useTimeoutFn(this.runPendingTap, DOUBLE_TAP_MS, { immediate: false })
  },
  beforeUnmount() {
    this.tapTimer.stop()
  },
  methods: {
    tap(action) {
      if (this.tapTimer.isPending.value) {
        this.tapTimer.stop()
        this.doubleTap()
        return
      }
      this.pendingTap = action
      this.tapTimer.start()
    },
    runPendingTap() {
      if (this.pendingTap) this.pendingTap()
    },
  },
}
