const bindings = new WeakMap()
const EVENTS = ['pointerdown', 'pointermove', 'pointerup', 'pointercancel']

function position(el, event) {
  return event.clientX - el.getBoundingClientRect().left + el.scrollLeft
}

export default {
  mounted(el, { value }) {
    const state = { handlers: value, last: null, active: false }
    const listeners = {
      pointerdown(event) {
        if (!state.handlers.grab(position(el, event))) return
        state.active = true
        state.last = { x: event.clientX, time: event.timeStamp }
        el.setPointerCapture(event.pointerId)
        state.handlers.move(position(el, event), 0)
      },
      pointermove(event) {
        if (!state.active) return
        const speed =
          Math.abs(event.clientX - state.last.x) / (event.timeStamp - state.last.time || 1)
        state.last = { x: event.clientX, time: event.timeStamp }
        state.handlers.move(position(el, event), speed)
      },
      pointerup(event) {
        if (!state.active) return
        state.active = false
        state.handlers.release(position(el, event))
      },
      pointercancel() {
        state.active = false
        state.handlers.cancel()
      },
    }
    bindings.set(el, { state, listeners })
    for (const type of EVENTS) el.addEventListener(type, listeners[type])
  },
  updated(el, { value }) {
    bindings.get(el).state.handlers = value
  },
  unmounted(el) {
    const { listeners } = bindings.get(el)
    for (const type of EVENTS) el.removeEventListener(type, listeners[type])
    bindings.delete(el)
  },
}
