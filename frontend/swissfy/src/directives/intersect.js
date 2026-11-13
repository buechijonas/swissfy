const bindings = new WeakMap()
const AHEAD = '0px 0px 200% 0px'

export default {
  mounted(el, { value, modifiers }) {
    const options = {
      root: modifiers.parent || modifiers.ahead ? el.parentElement : null,
      rootMargin: modifiers.ahead ? AHEAD : '0px',
      threshold: value.threshold ?? 0,
    }
    const observer = new IntersectionObserver(([entry]) => {
      bindings.get(el).handler(entry.isIntersecting)
    }, options)
    bindings.set(el, { observer, handler: value.handler ?? value })
    observer.observe(el)
  },
  updated(el, { value }) {
    const binding = bindings.get(el)
    binding.handler = value.handler ?? value
    binding.observer.unobserve(el)
    binding.observer.observe(el)
  },
  unmounted(el) {
    bindings.get(el).observer.disconnect()
    bindings.delete(el)
  },
}
