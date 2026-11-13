const bindings = new WeakMap()

export default {
  mounted(el, { value }) {
    const listener = (event) => {
      el.releasePointerCapture(event.pointerId)
      bindings.get(el).callback()
    }
    bindings.set(el, { callback: value, listener })
    el.addEventListener('pointerdown', listener)
  },
  updated(el, { value }) {
    bindings.get(el).callback = value
  },
  unmounted(el) {
    el.removeEventListener('pointerdown', bindings.get(el).listener)
    bindings.delete(el)
  },
}
