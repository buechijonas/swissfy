<script>
import { dragBubble, keyAt, stretchFor } from '@/lib/bubble.js'
import { design } from '@/lib/preferences.js'

export default {
  name: 'BubbleNavigation',
  props: {
    active: { type: String, default: null },
    trackWidth: { type: Number, default: 0 },
    widthOf: { type: String, default: null },
    grabActiveOnly: { type: Boolean, default: false },
    canSelect: { type: Function, default: () => true },
  },
  emits: ['select'],
  data() {
    return {
      boxes: {},
      dragging: false,
      dragged: null,
      targetKey: null,
      stretch: 1,
      wobbles: 0,
    }
  },
  computed: {
    bubble() {
      return this.dragged ?? this.boxes[this.targetKey ?? this.active] ?? null
    },
    handlers() {
      return { grab: this.grab, move: this.drag, release: this.release, cancel: this.cancel }
    },
  },
  watch: {
    active() {
      this.targetKey = null
      this.wobbles += 1
    },
  },
  methods: {
    storeBox(key, box) {
      this.boxes[key] = box
    },
    grab(x) {
      if (design.value !== 'glass') return false
      if (this.grabActiveOnly && keyAt(this.boxes, x) !== this.active) return false
      this.dragging = true
      return true
    },
    drag(x, speed) {
      const key = this.widthOf ?? keyAt(this.boxes, x) ?? this.active
      this.dragged = dragBubble(x, this.boxes[key].width, this.trackWidth)
      this.stretch = stretchFor(speed)
    },
    cancel() {
      this.dragging = false
      this.dragged = null
      this.stretch = 1
    },
    release(x) {
      const key = keyAt(this.boxes, x)
      this.cancel()
      if (!key || !this.canSelect(key)) return
      if (key === this.active) {
        this.wobbles += 1
        return
      }
      this.targetKey = key
      this.$emit('select', key)
    },
  },
  render() {
    return this.$slots.default({
      bubble: this.bubble,
      dragging: this.dragging,
      stretch: this.stretch,
      wobbles: this.wobbles,
      storeBox: this.storeBox,
      handlers: this.handlers,
    })
  },
}
</script>
