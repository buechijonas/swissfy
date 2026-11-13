import clamp from 'lodash-es/clamp'
import findKey from 'lodash-es/findKey'
import { design } from '@/lib/preferences.js'

export default {
  data() {
    return {
      boxes: {},
      dragging: false,
      dragBubble: null,
      targetKey: null,
      stretch: 1,
      wobbles: 0,
    }
  },
  computed: {
    bubble() {
      return this.dragBubble ?? this.boxes[this.targetKey ?? this.activeKey] ?? null
    },
  },
  watch: {
    activeKey() {
      this.targetKey = null
      this.wobbles += 1
    },
  },
  methods: {
    storeBox(key, box) {
      this.boxes[key] = box
    },
    keyAt(x) {
      return findKey(this.boxes, (box) => x >= box.left && x <= box.left + box.width)
    },
    canGrab() {
      return true
    },
    canSelect() {
      return true
    },
    grab(x) {
      if (design.value !== 'glass' || !this.canGrab(x)) return false
      this.dragging = true
      return true
    },
    drag(x, speed) {
      const width = this.dragWidth(x)
      this.dragBubble = { left: clamp(x - width / 2, 0, this.trackWidth - width), width }
      this.stretch = 1 + Math.min(speed * 0.3, 0.45)
    },
    cancel() {
      this.dragging = false
      this.dragBubble = null
      this.stretch = 1
    },
    release(x) {
      const key = this.keyAt(x)
      this.cancel()
      if (!key || !this.canSelect(key)) return
      if (key === this.activeKey) {
        this.wobbles += 1
        return
      }
      this.targetKey = key
      this.select(key)
    },
  },
}
