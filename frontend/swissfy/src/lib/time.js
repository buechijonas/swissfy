export function formatRelativeTime(value, nowValue = Date.now()) {
  const date = new Date(value)
  const now = new Date(nowValue)
  const yesterday = new Date(now)
  yesterday.setDate(now.getDate() - 1)
  const time = date.toLocaleTimeString('de-CH', { hour: '2-digit', minute: '2-digit' })

  if (date.toDateString() === now.toDateString()) {
    const minutes = Math.floor((now - date) / 60000)
    if (minutes < 60) return `Vor ${Math.max(minutes, 1)} Min.`
    const hours = Math.floor(minutes / 60)
    return `Vor ${hours} ${hours === 1 ? 'Stunde' : 'Stunden'}`
  }
  if (date.toDateString() === yesterday.toDateString()) return `Gestern um ${time} Uhr`
  const day = date.toLocaleDateString('de-CH', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
  })
  return `${day}, ${time} Uhr`
}

export function formatDate(value) {
  return new Date(value).toLocaleDateString('de-CH', {
    day: 'numeric',
    month: 'long',
    year: 'numeric',
    timeZone: 'UTC',
  })
}
