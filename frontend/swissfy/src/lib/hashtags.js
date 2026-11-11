const PATTERN = /(?<![\p{L}\p{N}_#])#([\p{L}\p{N}_]{1,50})/gu

export function hashtagLink(name) {
  return `/hashtags/${encodeURIComponent(name.toLowerCase())}`
}

export function extractHashtags(text) {
  const names = [...text.matchAll(PATTERN)].map((match) => match[1].toLowerCase())
  return [...new Set(names)]
}

export function splitHashtags(text) {
  const parts = []
  let last = 0
  for (const match of text.matchAll(PATTERN)) {
    if (match.index > last) parts.push({ text: text.slice(last, match.index) })
    parts.push({ text: match[0], hashtag: match[1] })
    last = match.index + match[0].length
  }
  if (last < text.length) parts.push({ text: text.slice(last) })
  return parts
}
