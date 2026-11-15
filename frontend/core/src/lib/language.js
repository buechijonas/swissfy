import { ref, watch } from 'vue'
import { getCookie, setSharedCookie } from '@core/lib/cookies.js'
import { rootAttribute, SHARED_MAX_AGE } from '@core/lib/storedSetting.js'

const COOKIE = 'language'
const FALLBACK = 'en'

export const LANGUAGE_OPTIONS = [
  { value: 'en', label: 'English', locale: 'en-GB', matches: ['en'] },
  { value: 'de', label: 'Deutsch', locale: 'de-CH', matches: ['de'] },
  { value: 'fr', label: 'Français', locale: 'fr-CH', matches: ['fr'] },
  { value: 'it', label: 'Italiano', locale: 'it-CH', matches: ['it'] },
  { value: 'rm', label: 'Rumantsch', locale: 'rm-CH', matches: ['rm'] },
  { value: 'es', label: 'Español', locale: 'es-ES', matches: ['es'] },
  {
    value: 'zh-hans',
    label: '简体中文',
    locale: 'zh-CN',
    matches: ['zh', 'zh-cn', 'zh-sg', 'zh-hans'],
  },
]

const LANGUAGES = Object.fromEntries(LANGUAGE_OPTIONS.map((option) => [option.value, option]))

function supported(tag) {
  const code = tag.toLowerCase()
  const base = code.split('-')[0]
  const exact = LANGUAGE_OPTIONS.find(({ matches }) => matches.includes(code))
  return exact ?? LANGUAGE_OPTIONS.find(({ matches }) => matches.includes(base) && base !== 'zh')
}

function browserLanguage() {
  const tags = navigator.languages?.length ? navigator.languages : [navigator.language ?? '']
  return tags.map(supported).find(Boolean)?.value ?? FALLBACK
}

function storedLanguage() {
  const stored = getCookie(COOKIE)
  return LANGUAGES[stored] ? stored : null
}

export const language = ref(storedLanguage() ?? browserLanguage())

watch(language, (value) => rootAttribute('lang', value), { immediate: true })

export function selectLanguage(value) {
  setSharedCookie(COOKIE, value, SHARED_MAX_AGE)
  language.value = value
}

export function locale() {
  return LANGUAGES[language.value].locale
}

document.addEventListener('visibilitychange', () => {
  if (document.visibilityState !== 'visible') return
  language.value = storedLanguage() ?? language.value
})
