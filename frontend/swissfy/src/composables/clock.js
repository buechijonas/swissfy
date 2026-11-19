import { useIntervalFn } from '@vueuse/core'
import { reactive } from 'vue'

const CLOCK_INTERVAL = 30000

export function useClock() {
  const clock = reactive({
    now: Date.now(),
    tick() {
      clock.now = Date.now()
    },
  })
  useIntervalFn(clock.tick, CLOCK_INTERVAL)
  return clock
}
