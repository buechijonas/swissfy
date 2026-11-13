const bindings = new WeakMap()

export default {
  mounted(el, { value, modifiers }) {
    const type = modifiers.drop ? 'drop' : 'change'
    const listener = (event) => {
      if (modifiers.drop) event.preventDefault()
      const files = [...(modifiers.drop ? event.dataTransfer.files : el.files)]
      if (!modifiers.drop) el.value = ''
      bindings.get(el).callback(files)
    }
    bindings.set(el, { callback: value, type, listener })
    el.addEventListener(type, listener)
  },
  updated(el, { value }) {
    bindings.get(el).callback = value
  },
  unmounted(el) {
    const { type, listener } = bindings.get(el)
    el.removeEventListener(type, listener)
    bindings.delete(el)
  },
}
