import { t } from '@/i18n.js'

export function onOffOptions() {
  return [
    { value: true, label: t('settings.on'), icon: 'check' },
    { value: false, label: t('settings.off'), icon: 'cross' },
  ]
}

export function themeOptions() {
  return [
    { value: 'auto', icon: 'laptop', label: t('settings.auto') },
    { value: 'light', icon: 'brightness', label: t('settings.light') },
    { value: 'dark', icon: 'moon-stars', label: t('settings.dark') },
  ]
}

export function designOptions() {
  return [
    { value: 'default', icon: 'grid', label: t('settings.standard') },
    { value: 'glass', icon: 'droplet', label: 'Glassmorphism' },
    { value: 'y2k', icon: 'world', label: 'Y2K' },
    { value: 'cyberpunk', icon: 'chip', label: 'Cyberpunk' },
    { value: 'ecopunk', icon: 'globe', label: 'Ecopunk' },
    { value: 'romance', icon: 'heart', label: 'Dark Romance' },
  ]
}

export const limitedDesigns = ['cyberpunk', 'romance', 'y2k']

export function visibilityOptions() {
  return [
    { value: 'public', label: t('settings.public'), icon: 'globe' },
    { value: 'followers', label: t('settings.followers'), icon: 'user' },
    { value: 'friends', label: t('settings.friends'), icon: 'users' },
  ]
}

export function privacyToggles() {
  return [
    {
      field: 'read_receipts',
      label: t('settings.readReceipts'),
      hint: t('settings.readReceiptsHint'),
    },
    {
      field: 'chat_requests',
      label: t('settings.chatRequests'),
      hint: t('settings.chatRequestsHint'),
    },
    {
      field: 'show_birthdate',
      label: t('settings.birthdate'),
      hint: t('settings.birthdateHint'),
    },
  ]
}

export function chatProtectionOptions() {
  return [
    { value: 'standard', label: t('settings.standard'), icon: 'shield-trust' },
    { value: 'device', label: t('settings.device'), icon: 'laptop' },
    { value: 'pin', label: t('settings.pin'), icon: 'lock' },
  ]
}

export function chatProtectionHints() {
  return {
    standard: t('settings.standardHint'),
    device: t('settings.deviceHint'),
    pin: t('settings.pinHint'),
  }
}
