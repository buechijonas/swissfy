import isEqual from 'lodash-es/isEqual'

const bindings = new WeakMap()

function report(el) {
  const binding = bindings.get(el)
  const bounds = {
    left: el.offsetLeft,
    top: el.offsetTop,
    width: el.offsetWidth,
    height: el.offsetHeight,
    scrollWidth: el.scrollWidth,
    clientWidth: el.clientWidth,
  }
  if (isEqual(bounds, binding.bounds)) return
  binding.bounds = bounds
  binding.callback(bounds)
}

export default {
  mounted(el, { value }) {
    const observer = new ResizeObserver(() => report(el))
    bindings.set(el, { callback: value, observer, bounds: null })
    observer.observe(el)
    report(el)
  },
  updated(el, { value }) {
    bindings.get(el).callback = value
    report(el)
  },
  unmounted(el) {
    bindings.get(el).observer.disconnect()
    bindings.delete(el)
  },
}
