export default {
  updated(el, { value, oldValue }) {
    if (value && !oldValue) el.scrollIntoView({ behavior: 'smooth', block: 'nearest' })
  },
}
