import clamp from 'lodash-es/clamp'
import findKey from 'lodash-es/findKey'
import { reducedMotion } from '@/lib/browser.js'
import { contrastMode, design } from '@/lib/preferences.js'

export function wobble(el) {
  if (!el || design.value !== 'glass' || contrastMode.value || reducedMotion.value === 'reduce')
    return
  el.animate(
    [
      { transform: 'scale(1)' },
      { transform: 'scale(1.25, 0.82)' },
      { transform: 'scale(0.92, 1.08)' },
      { transform: 'scale(1.04, 0.97)' },
      { transform: 'scale(1)' },
    ],
    { duration: 650, easing: 'ease-out' },
  )
}

const MAX_STRETCH = 0.45
const STRETCH_PER_SPEED = 0.3

export function keyAt(boxes, x) {
  return findKey(boxes, (box) => x >= box.left && x <= box.left + box.width)
}

export function dragBubble(x, width, trackWidth) {
  return { left: clamp(x - width / 2, 0, trackWidth - width), width }
}

export function stretchFor(speed) {
  return 1 + Math.min(speed * STRETCH_PER_SPEED, MAX_STRETCH)
}
