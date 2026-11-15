import { t } from '@core/i18n.js'
import { language } from '@core/lib/language.js'

const undraws = import.meta.glob('../assets/undraws/*.svg', { eager: true, import: 'default' })

const translations = import.meta.glob('./swissfy.*.js', { import: 'default' })

const CONTRACTS = Object.fromEntries(
  Object.entries(translations).map(([path, contracts]) => [path.split('.').at(-2), contracts]),
)

export const LEGAL_PAGES = ['impressum', 'privacy', 'terms', 'disclaimer']

export const illustrations = Object.fromEntries(
  Object.entries(undraws).map(([path, src]) => [path.split('/').pop().replace('.svg', ''), src]),
)

export function legalTitle(page) {
  return t(`core.legal.${page}`)
}

export async function loadContract(page, value = language.value) {
  const contracts = await (CONTRACTS[value] ?? CONTRACTS.en)()
  return contracts[page]
}
