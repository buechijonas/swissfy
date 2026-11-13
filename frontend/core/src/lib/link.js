const URL_PATTERN = /^(https?:\/\/|mailto:)/i
const PATH_PATTERN = /^\/(?![/\\])[^\s\\\p{Cc}]*$/u

export function url(value) {
  return URL_PATTERN.test(value) ? value : undefined
}

export function path(value) {
  return PATH_PATTERN.test(value) ? value : undefined
}
