import { t } from '@/i18n.js'

export function navigationItems() {
  return [
    { key: 'changelogs', label: t('navigation.changelog'), icon: 'timeline', to: '/' },
    { key: 'impressum', label: t('legal.imprint'), icon: 'shield-trust', to: '/impressum' },
    { key: 'privacy', label: t('legal.privacy'), icon: 'incognito', to: '/privacy' },
    { key: 'terms', label: t('legal.terms'), icon: 'terms-info', to: '/terms' },
    { key: 'disclaimer', label: t('legal.disclaimer'), icon: 'document-gavel', to: '/disclaimer' },
    {
      key: 'donate',
      label: t('navigation.donate'),
      icon: 'hands-heart',
      href: 'https://buymeacoffee.com/wintersehn',
    },
  ]
}
