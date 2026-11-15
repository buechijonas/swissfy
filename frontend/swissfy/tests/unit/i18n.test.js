import { afterEach, describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import { LANGUAGE_OPTIONS } from '@core/lib/language.js'
import ChatMessageList from '@/components/chats/ChatMessageList.vue'
import { i18n } from '@/i18n.js'
import { formatRelativeTime } from '@/lib/time.js'

function keys(messages, prefix = '') {
  return Object.entries(messages).flatMap(([key, value]) =>
    typeof value === 'object' ? keys(value, `${prefix}${key}.`) : [`${prefix}${key}`],
  )
}

const NOW = new Date('2026-11-14T15:00:00')

describe('i18n', () => {
  afterEach(() => {
    i18n.global.locale.value = 'de'
  })

  const appLocales = import.meta.glob('@/locales/*.json', { eager: true, import: 'default' })
  const coreLocales = import.meta.glob('@core/locales/*.json', { eager: true, import: 'default' })

  it.each(LANGUAGE_OPTIONS.map(({ value }) => value))('has every key in %s', (language) => {
    const app = Object.entries(appLocales).find(([path]) => path.endsWith(`/${language}.json`))
    const core = Object.entries(coreLocales).find(([path]) => path.endsWith(`/${language}.json`))
    const source = Object.entries(appLocales).find(([path]) => path.endsWith('/de.json'))[1]
    const coreSource = Object.entries(coreLocales).find(([path]) => path.endsWith('/de.json'))[1]
    expect(keys(app[1]).sort()).toEqual(keys(source).sort())
    expect(keys(core[1]).sort()).toEqual(keys(coreSource).sort())
  })

  it('formats relative times in German by default', () => {
    expect(formatRelativeTime(new Date('2026-11-14T14:40:00'), NOW)).toBe('Vor 20 Min.')
    expect(formatRelativeTime(new Date('2026-11-14T13:00:00'), NOW)).toBe('Vor 2 Stunden')
    expect(formatRelativeTime(new Date('2026-11-14T14:00:00'), NOW)).toBe('Vor 1 Stunde')
  })

  it('formats relative times in English', () => {
    i18n.global.locale.value = 'en'
    expect(formatRelativeTime(new Date('2026-11-14T13:00:00'), NOW)).toBe('2 hours ago')
    expect(formatRelativeTime(new Date('2026-11-14T14:00:00'), NOW)).toBe('1 hour ago')
  })

  it('renders components in the active language', () => {
    const props = { messages: [], ready: true, ownMessages: 0, retentionDays: 14 }
    expect(mount(ChatMessageList, { props }).text()).toContain('Noch keine Nachrichten.')
    i18n.global.locale.value = 'en'
    const english = mount(ChatMessageList, { props }).text()
    expect(english).toContain('No messages yet.')
    expect(english).toContain('Messages are deleted automatically after 14 days.')
  })
})
