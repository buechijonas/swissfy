import { contrastMode } from '@/lib/preferences.js'

export function wobble(el) {
  if (!el || contrastMode.value || matchMedia('(prefers-reduced-motion: reduce)').matches) return
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
