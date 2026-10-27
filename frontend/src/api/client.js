import { getCookie } from '@/lib/cookies.js'

export class ApiError extends Error {
  constructor(status, data) {
    const detail = detailOf(data)
    super(detail ?? `Anfrage fehlgeschlagen (${status}).`)
    this.status = status
    this.detail = detail
    this.data = data
  }
}

function detailOf(data) {
  if (!data || typeof data !== 'object') return null
  if (data.detail) return data.detail
  const firstField = Object.values(data)[0]
  return Array.isArray(firstField) ? firstField[0] : null
}

async function parse(response) {
  const text = await response.text()
  if (!text) return null
  try {
    return JSON.parse(text)
  } catch {
    return null
  }
}

export function withParams(url, params) {
  if (!params) return url
  const query = new URLSearchParams(params).toString()
  return query ? `${url}${url.includes('?') ? '&' : '?'}${query}` : url
}

async function request(url, { method = 'GET', body } = {}) {
  const isFormData = body instanceof FormData
  const options = {
    method,
    credentials: 'include',
    headers: {
      ...(isFormData ? {} : { 'Content-Type': 'application/json' }),
      ...(method !== 'GET' ? { 'X-CSRFToken': getCookie('swissfy_csrftoken') } : {}),
    },
  }
  if (body !== undefined) options.body = isFormData ? body : JSON.stringify(body)
  const response = await fetch(url, options)
  const data = await parse(response)
  if (!response.ok) throw new ApiError(response.status, data)
  return data
}

export default {
  get(url, params) {
    return request(withParams(url, params))
  },
  post(url, body) {
    return request(url, { method: 'POST', body })
  },
  put(url, body) {
    return request(url, { method: 'PUT', body })
  },
  patch(url, body) {
    return request(url, { method: 'PATCH', body })
  },
  delete(url) {
    return request(url, { method: 'DELETE' })
  },
}

export function nextPage(next) {
  if (!next) return null
  const url = new URL(next, window.location.origin)
  return url.pathname + url.search
}
