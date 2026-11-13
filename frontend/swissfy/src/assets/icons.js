import { design } from '@/lib/preferences.js'

function byName(modules) {
  return Object.fromEntries(
    Object.entries(modules).map(([path, src]) => [path.split('/').pop().replace('.svg', ''), src]),
  )
}

export const icons = byName(import.meta.glob('./icons/*.svg', { eager: true, import: 'default' }))

export const y2kIcons = byName(
  import.meta.glob('./icons-y2k/*.svg', { eager: true, import: 'default', query: '?no-inline' }),
)

export const romanceIcons = byName(
  import.meta.glob('./icons-romance/*.svg', { eager: true, import: 'default' }),
)

const FADED = ['heart', 'bookmark', 'unlock']

export function iconSource(name) {
  const y2kIcon = design.value === 'y2k' ? y2kIcons[name] : null
  if (y2kIcon) {
    return {
      class: { 'opacity-50 grayscale': FADED.includes(name) },
      style: { backgroundImage: `url("${y2kIcon}")` },
    }
  }
  const icon = (design.value === 'romance' && romanceIcons[name]) || icons[name]
  return { class: 'bg-current', style: { maskImage: `url("${icon}")` } }
}
