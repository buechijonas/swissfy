import { config } from '@vue/test-utils'
import { applyLanguage } from '@core/i18n.js'
import { language } from '@core/lib/language.js'
import { i18n } from '@/i18n.js'

language.value = 'de'
await applyLanguage('de')
await applyLanguage('en')
config.global.plugins.push(i18n)
