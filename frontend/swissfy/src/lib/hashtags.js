const PATTERN = /(?<![\p{L}\p{N}_#])#([\p{L}\p{N}_]{1,50})/gu

export function hashtagLink(name) {
  return `/hashtags/${encodeURIComponent(name.toLowerCase())}`
}

export function extractHashtags(text) {
  const names = [...text.matchAll(PATTERN)].map((match) => match[1].toLowerCase())
  return [...new Set(names)]
}
