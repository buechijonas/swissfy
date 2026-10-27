import { getCookie } from '@/lib/cookies.js'

export async function apiFetch(url, options = {}) {
  const isUnsafe = options.method && options.method !== 'GET'
  const isFormData = options.body instanceof FormData
  return fetch(url, {
    credentials: 'include',
    headers: {
      ...(isFormData ? {} : { 'Content-Type': 'application/json' }),
      ...(isUnsafe ? { 'X-CSRFToken': getCookie('swissfy_csrftoken') } : {}),
      ...options.headers,
    },
    ...options,
  })
}

export function extractErrorMessage(data, fallback) {
  if (!data) return fallback
  if (data.detail) return data.detail
  const firstField = Object.values(data)[0]
  if (Array.isArray(firstField)) return firstField[0]
  return fallback
}
