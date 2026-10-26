import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import api, { ApiError, withParams } from '@/api/client.js'

function respond(body, status = 200) {
  return vi.fn(() => Promise.resolve(new Response(body, { status })))
}

describe('api client', () => {
  beforeEach(() => {
    vi.stubGlobal('fetch', respond('{}'))
    document.cookie = 'swissfy_csrftoken=token123'
    document.cookie = 'csrftoken=wrong'
  })

  afterEach(() => {
    vi.unstubAllGlobals()
  })

  function sentHeaders() {
    return fetch.mock.calls[0][1].headers
  }

  it.each(['post', 'put', 'patch', 'delete'])(
    'sends the swissfy CSRF token on %s',
    async (method) => {
      await api[method]('/api/x/')
      expect(sentHeaders()['X-CSRFToken']).toBe('token123')
    },
  )

  it('does not leak the CSRF token on GET', async () => {
    await api.get('/api/x/')
    expect(sentHeaders()['X-CSRFToken']).toBeUndefined()
  })

  it('sends cookies only as credentials for same-origin requests', async () => {
    await api.get('/api/x/')
    expect(fetch.mock.calls[0][1].credentials).toBe('include')
    expect(fetch.mock.calls[0][0]).toBe('/api/x/')
  })

  it('returns null for empty responses', async () => {
    vi.stubGlobal('fetch', respond(null, 204))
    expect(await api.delete('/api/x/')).toBeNull()
  })

  it('throws server text as plain string', async () => {
    vi.stubGlobal('fetch', respond('{"detail":"<b>x</b>"}', 400))
    const error = await api.get('/api/x/').catch((error) => error)
    expect(error).toBeInstanceOf(ApiError)
    expect(error.status).toBe(400)
    expect(error.detail).toBe('<b>x</b>')
  })

  it('has no detail on unexpected shapes', async () => {
    vi.stubGlobal('fetch', respond('<html>oops</html>', 500))
    const error = await api.get('/api/x/').catch((error) => error)
    expect(error.detail).toBeNull()
    vi.stubGlobal('fetch', respond('{"a":{"b":1}}', 400))
    expect((await api.get('/api/x/').catch((error) => error)).detail).toBeNull()
  })
})

describe('withParams', () => {
  it('appends encoded params', () => {
    expect(withParams('/api/x/', { q: 'a b', page: 2 })).toBe('/api/x/?q=a+b&page=2')
    expect(withParams('/api/x/?a=1', { b: 2 })).toBe('/api/x/?a=1&b=2')
    expect(withParams('/api/x/', null)).toBe('/api/x/')
  })
})
