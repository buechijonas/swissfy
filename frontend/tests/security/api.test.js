import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { apiFetch, extractErrorMessage } from '@/lib/api.js'

describe('apiFetch', () => {
  beforeEach(() => {
    vi.stubGlobal(
      'fetch',
      vi.fn(() => Promise.resolve(new Response('{}'))),
    )
    document.cookie = 'swissfy_csrftoken=token123'
    document.cookie = 'csrftoken=wrong'
  })

  afterEach(() => {
    vi.unstubAllGlobals()
  })

  function sentHeaders() {
    return fetch.mock.calls[0][1].headers
  }

  it.each(['POST', 'PUT', 'PATCH', 'DELETE'])(
    'sends the swissfy CSRF token on %s',
    async (method) => {
      await apiFetch('/api/x/', { method })
      expect(sentHeaders()['X-CSRFToken']).toBe('token123')
    },
  )

  it('does not leak the CSRF token on GET', async () => {
    await apiFetch('/api/x/')
    expect(sentHeaders()['X-CSRFToken']).toBeUndefined()
  })

  it('sends cookies only as credentials for same-origin requests', async () => {
    await apiFetch('/api/x/')
    expect(fetch.mock.calls[0][1].credentials).toBe('include')
    expect(fetch.mock.calls[0][0]).toBe('/api/x/')
  })
})

describe('extractErrorMessage', () => {
  it('returns server text as plain string', () => {
    expect(extractErrorMessage({ detail: '<b>x</b>' }, 'fallback')).toBe('<b>x</b>')
  })

  it('falls back on unexpected shapes', () => {
    expect(extractErrorMessage(null, 'fallback')).toBe('fallback')
    expect(extractErrorMessage({ a: { b: 1 } }, 'fallback')).toBe('fallback')
  })
})
