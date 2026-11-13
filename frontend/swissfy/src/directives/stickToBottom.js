const NEAR_BOTTOM = 80
const nearBottom = new WeakMap()

export default {
  mounted(el) {
    el.scrollTop = el.scrollHeight
  },
  beforeUpdate(el) {
    nearBottom.set(el, el.scrollHeight - el.scrollTop - el.clientHeight < NEAR_BOTTOM)
  },
  updated(el, { value, oldValue }) {
    if (nearBottom.get(el) || value !== oldValue) el.scrollTop = el.scrollHeight
  },
}
