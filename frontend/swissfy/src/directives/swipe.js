const bindings = new WeakMap()
const DIRECTION_THRESHOLD = 8
const EVENTS = ['touchstart', 'touchmove', 'touchend', 'touchcancel']

export default {
  mounted(el, { value }) {
    const state = { handlers: value, start: null, direction: null, swiped: false }
    const listeners = {
      touchstart(event) {
        const [touch] = event.touches
        state.start = { x: touch.clientX, y: touch.clientY }
        state.direction = null
        state.swiped = false
      },
      touchmove(event) {
        const [touch] = event.touches
        const dx = touch.clientX - state.start.x
        const dy = touch.clientY - state.start.y
        if (!state.direction) {
          if (Math.max(Math.abs(dx), Math.abs(dy)) < DIRECTION_THRESHOLD) return
          state.direction = Math.abs(dx) > Math.abs(dy) ? 'horizontal' : 'vertical'
          state.handlers.direction(state.direction)
        }
        if (state.direction === 'horizontal') state.handlers.move(dx, el.clientWidth)
      },
      touchend() {
        if (state.direction === 'horizontal') state.swiped = true
        state.handlers.end()
      },
      touchcancel() {
        state.handlers.cancel()
      },
    }
    const suppressClick = (event) => {
      if (!state.swiped) return
      state.swiped = false
      event.preventDefault()
      event.stopPropagation()
    }
    bindings.set(el, { state, listeners, suppressClick })
    for (const type of EVENTS) el.addEventListener(type, listeners[type], { passive: true })
    el.addEventListener('click', suppressClick, true)
  },
  updated(el, { value }) {
    bindings.get(el).state.handlers = value
  },
  unmounted(el) {
    const { listeners, suppressClick } = bindings.get(el)
    for (const type of EVENTS) el.removeEventListener(type, listeners[type])
    el.removeEventListener('click', suppressClick, true)
    bindings.delete(el)
  },
}
