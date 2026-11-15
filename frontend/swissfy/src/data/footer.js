import { docsUrl } from '@/data/navigation.js'
import { t } from '@/i18n.js'

export function legalUrl(page) {
  return `${docsUrl}/${page}`
}

export function footerLinks() {
  return [
    { label: t('legal.imprint'), icon: 'shield-trust', href: legalUrl('impressum') },
    { label: t('legal.privacy'), icon: 'incognito', href: legalUrl('privacy') },
    { label: t('legal.terms'), icon: 'terms-info', href: legalUrl('terms') },
    { label: t('legal.disclaimer'), icon: 'document-gavel', href: legalUrl('disclaimer') },
  ]
}
