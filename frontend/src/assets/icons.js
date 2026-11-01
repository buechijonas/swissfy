function byName(modules) {
  return Object.fromEntries(
    Object.entries(modules).map(([path, src]) => [path.split('/').pop().replace('.svg', ''), src]),
  )
}

export const icons = byName(import.meta.glob('./icons/*.svg', { eager: true, import: 'default' }))

export const y2kIcons = byName(
  import.meta.glob('./icons-y2k/*.svg', { eager: true, import: 'default', query: '?no-inline' }),
)
