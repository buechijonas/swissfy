import { useIntervalFn } from '@vueuse/core'

const CLOCK_INTERVAL = 30000

export default {
  data() {
    return { now: Date.now() }
  },
  created() {
    this.clock = useIntervalFn(this.tick, CLOCK_INTERVAL)
  },
  beforeUnmount() {
    this.clock.pause()
  },
  methods: {
    tick() {
      this.now = Date.now()
    },
  },
}
