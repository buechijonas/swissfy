import { useTimeoutFn } from '@vueuse/core'
import { reactive } from 'vue'

const DOUBLE_TAP_MS = 250

export function useDoubleTap() {
  let single = null
  const timer = useTimeoutFn(() => single?.(), DOUBLE_TAP_MS, { immediate: false })
  return reactive({
    pending: timer.isPending,
    tap(onSingle, onDouble) {
      if (timer.isPending.value) {
        timer.stop()
        onDouble()
        return
      }
      single = onSingle
      timer.start()
    },
    stop: timer.stop,
  })
}
