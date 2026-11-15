import { watch } from 'vue'
import { createI18n } from 'vue-i18n'
import { language } from '@core/lib/language.js'

const coreMessages = import.meta.glob('./locales/*.json', { import: 'default' })

let i18n = null
let appMessages = {}
let initialLanguage = null

export function byLanguage(modules) {
  return Object.fromEntries(
    Object.entries(modules).map(([path, messages]) => [
      path.split('/').pop().replace('.json', ''),
      messages,
    ]),
  )
}

async function loadMessages(value) {
  if (i18n.global.availableLocales.includes(value)) return
  const core = byLanguage(coreMessages)
  const [coreTexts, appTexts] = await Promise.all([core[value](), appMessages[value]()])
  i18n.global.setLocaleMessage(value, { ...coreTexts, ...appTexts })
}

export async function applyLanguage(value) {
  await loadMessages(value)
  if (language.value === value) i18n.global.locale.value = value
}

export function createAppI18n(messages) {
  appMessages = messages
  i18n = createI18n({ legacy: false, locale: language.value, fallbackLocale: 'en', messages: {} })
  initialLanguage = applyLanguage(language.value)
  watch(language, applyLanguage)
  return i18n
}

export function i18nReady() {
  return initialLanguage
}

export function t(...args) {
  return i18n.global.t(...args)
}
