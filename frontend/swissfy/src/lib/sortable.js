import isEqual from 'lodash-es/isEqual'
import map from 'lodash-es/map'

export function moveItem(items, id, overId) {
  const from = items.findIndex((item) => item.id === id)
  const to = items.findIndex((item) => item.id === overId)
  if (from < 0 || to < 0 || from === to) return items
  const moved = [...items]
  moved.splice(to, 0, ...moved.splice(from, 1))
  return moved
}

export function sameOrder(a, b) {
  return isEqual(map(a, 'id'), map(b, 'id'))
}
