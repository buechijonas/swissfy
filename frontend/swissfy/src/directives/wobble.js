import { wobble } from '@/lib/bubble.js'

export default {
  updated(el, { value, oldValue }) {
    if (value !== oldValue) wobble(el)
  },
}
