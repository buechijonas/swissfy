import { byLanguage, createAppI18n } from '@core/i18n.js'

const messages = import.meta.glob('./locales/*.json', { import: 'default' })

export const i18n = createAppI18n(byLanguage(messages))

export { i18nReady, t } from '@core/i18n.js'
