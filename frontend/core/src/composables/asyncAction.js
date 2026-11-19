import { reactive } from 'vue'

export function useAsyncAction() {
  const action = reactive({
    busy: false,
    error: null,
    async run(task, fallback = null) {
      action.busy = true
      action.error = null
      try {
        return await task()
      } catch (error) {
        action.error = error.detail ?? fallback ?? error.message
        return null
      } finally {
        action.busy = false
      }
    },
  })
  return action
}
