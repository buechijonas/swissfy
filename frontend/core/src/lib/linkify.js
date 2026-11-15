const LINK =
  /([\w.+-]+@[\w-]+(?:\.[\w-]+)+)|(https?:\/\/[^\s)]+)|((?:www\.)?(?:[a-z0-9-]+\.)+(?:com|ch|org|net|de)\b)/gi

function target([match, email, address]) {
  if (email) return { href: `mailto:${email}`, external: false }
  return { href: address ?? `https://${match}`, external: true }
}

export function linkParts(text) {
  const parts = []
  let start = 0
  for (const match of text.matchAll(LINK)) {
    if (match.index > start) parts.push({ start, text: text.slice(start, match.index) })
    parts.push({ start: match.index, text: match[0], ...target(match) })
    start = match.index + match[0].length
  }
  if (start < text.length) parts.push({ start, text: text.slice(start) })
  return parts
}
