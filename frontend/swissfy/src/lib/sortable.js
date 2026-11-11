export function itemAt(event, attribute) {
  const target = document.elementFromPoint(event.clientX, event.clientY)?.closest(`[${attribute}]`)
  return target?.getAttribute(attribute) ?? null
}

export function moveItem(items, id, overId) {
  const from = items.findIndex((item) => item.id === id)
  const to = items.findIndex((item) => item.id === overId)
  if (from < 0 || to < 0 || from === to) return items
  const moved = [...items]
  moved.splice(to, 0, ...moved.splice(from, 1))
  return moved
}

export function sameOrder(a, b) {
  return a.map((item) => item.id).join() === b.map((item) => item.id).join()
}
