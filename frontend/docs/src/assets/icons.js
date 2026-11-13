const modules = import.meta.glob('./icons/*.svg', { eager: true, import: 'default' })

export const icons = Object.fromEntries(
  Object.entries(modules).map(([path, src]) => [path.split('/').pop().replace('.svg', ''), src]),
)

export function iconSource(name) {
  return { class: 'bg-current', style: { maskImage: `url("${icons[name]}")` } }
}
