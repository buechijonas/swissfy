import { describe, expect, it } from 'vitest'
import { path, url } from '@/lib/link.js'

describe('url', () => {
  it.each(['https://swissfy.ch', 'http://example.com/a?b=c', 'mailto:hallo@swissfy.ch'])(
    'allows %s',
    (value) => {
      expect(url(value)).toBe(value)
    },
  )

  it.each([
    'javascript:alert(1)',
    'JaVaScRiPt:alert(1)',
    ' javascript:alert(1)',
    '\tjavascript:alert(1)',
    'java\nscript:alert(1)',
    'data:text/html,<script>alert(1)</script>',
    'vbscript:msgbox(1)',
    'file:///etc/passwd',
    '//evil.example',
    '/relative',
    'blob:https://swissfy.ch/x',
    '',
    null,
    undefined,
  ])('rejects %s', (value) => {
    expect(url(value)).toBeUndefined()
  })
})

describe('path', () => {
  it.each(['/', '/posts/abc', '/hashtags/swiss?x=1'])('allows %s', (value) => {
    expect(path(value)).toBe(value)
  })

  it.each([
    '//evil.example',
    '/\\evil.example',
    '\\\\evil.example',
    'https://evil.example',
    'javascript:alert(1)',
    '/posts/\nhttps://evil.example',
    '/posts/ x',
    '/posts\u0000',
    'posts',
    '',
  ])('rejects %s', (value) => {
    expect(path(value)).toBeUndefined()
  })
})
