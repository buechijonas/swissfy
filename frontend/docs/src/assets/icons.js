const modules = import.meta.glob('./icons/*.svg', { eager: true, import: 'default' })

export const icons = Object.fromEntries(
  Object.entries(modules).map(([path, src]) => [path.split('/').pop().replace('.svg', ''), src]),
)
