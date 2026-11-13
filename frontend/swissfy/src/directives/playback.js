export default {
  updated(el, { value, oldValue }) {
    if (value === oldValue) return
    if (value) el.play().catch(() => el.dispatchEvent(new Event('pause')))
    else el.pause()
  },
}
