import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

function clearCookie() {
  document.cookie = 'language=; max-age=0; path=/'
}

async function resolve({ cookie, languages }) {
  clearCookie()
  if (cookie) document.cookie = `language=${cookie}; path=/`
  vi.spyOn(navigator, 'languages', 'get').mockReturnValue(languages)
  vi.resetModules()
  return import('@core/lib/language.js')
}

describe('language', () => {
  beforeEach(clearCookie)

  afterEach(() => {
    vi.restoreAllMocks()
    clearCookie()
  })

  it('takes the first supported browser language', async () => {
    const { language } = await resolve({ languages: ['pt-BR', 'it-CH', 'de'] })
    expect(language.value).toBe('it')
  })

  it('maps simplified Chinese browsers to zh-hans', async () => {
    const { language } = await resolve({ languages: ['zh-CN'] })
    expect(language.value).toBe('zh-hans')
  })

  it('does not treat traditional Chinese as simplified', async () => {
    const { language } = await resolve({ languages: ['zh-TW'] })
    expect(language.value).toBe('en')
  })

  it('falls back to English', async () => {
    const { language } = await resolve({ languages: ['pt-BR', 'ja'] })
    expect(language.value).toBe('en')
  })

  it('prefers the cookie over the browser', async () => {
    const { language } = await resolve({ cookie: 'rm', languages: ['fr'] })
    expect(language.value).toBe('rm')
  })

  it('ignores an unknown cookie', async () => {
    const { language } = await resolve({ cookie: 'xx', languages: ['es'] })
    expect(language.value).toBe('es')
  })

  it('only writes the cookie when a language is chosen', async () => {
    const { language, selectLanguage } = await resolve({ languages: ['fr'] })
    expect(document.cookie).not.toContain('language=')
    selectLanguage('de')
    expect(language.value).toBe('de')
    expect(document.cookie).toContain('language=de')
  })

  it('lists English first and the Swiss languages after it', async () => {
    const { LANGUAGE_OPTIONS } = await resolve({ languages: [] })
    expect(LANGUAGE_OPTIONS.map(({ value }) => value)).toEqual([
      'en',
      'de',
      'fr',
      'it',
      'rm',
      'es',
      'zh-hans',
    ])
  })
})
