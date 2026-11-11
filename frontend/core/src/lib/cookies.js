export function getCookie(name) {
  const match = document.cookie.match(new RegExp('(?:^|; )' + name + '=([^;]*)'))
  return match ? decodeURIComponent(match[1]) : null
}

export function setCookie(name, value, maxAge) {
  const secure = location.protocol === 'https:' ? '; Secure' : ''
  document.cookie = `${name}=${encodeURIComponent(value)}; max-age=${maxAge}; path=/; SameSite=Strict${secure}`
}

function parentDomain() {
  const { hostname } = location
  if (hostname === 'localhost' || /^[\d.:]+$/.test(hostname)) return ''
  return `; domain=${hostname.split('.').slice(-2).join('.')}`
}

export function setSharedCookie(name, value, maxAge) {
  const secure = location.protocol === 'https:' ? '; Secure' : ''
  document.cookie = `${name}=${encodeURIComponent(value)}; max-age=${maxAge}; path=/; SameSite=Lax${parentDomain()}${secure}`
}

export function deleteCookie(name) {
  document.cookie = `${name}=; max-age=0; path=/`
}
