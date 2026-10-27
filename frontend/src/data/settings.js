export const onOffOptions = [
  { value: true, label: 'An', icon: 'check' },
  { value: false, label: 'Aus', icon: 'cross' },
]

export const themeOptions = [
  { value: 'auto', icon: 'laptop', label: 'Auto' },
  { value: 'light', icon: 'brightness', label: 'Hell' },
  { value: 'dark', icon: 'moon-stars', label: 'Dunkel' },
]

export const designOptions = [
  { value: 'default', icon: 'grid', label: 'Standard' },
  { value: 'glass', icon: 'droplet', label: 'Glassmorphism' },
  { value: 'cyberpunk', icon: 'chip', label: 'Cyberpunk' },
]

export const visibilityOptions = [
  { value: 'public', label: 'Öffentlich', icon: 'globe' },
  { value: 'followers', label: 'Follower', icon: 'user' },
  { value: 'friends', label: 'Freunde', icon: 'users' },
]

export const privacyToggles = [
  {
    field: 'read_receipts',
    label: 'Lesebestätigungen',
    hint: 'Wenn aus, sehen andere nicht, ob du ihre Nachrichten gelesen hast, und du siehst es bei ihnen auch nicht.',
  },
  {
    field: 'chat_requests',
    label: 'Chat-Anfragen',
    hint: 'Wenn aus, kann dir niemand eine neue Chat-Anfrage senden. Bestehende Chats bleiben.',
  },
  {
    field: 'show_birthdate',
    label: 'Geburtsdatum',
    hint: 'Wenn an, sehen alle, die dein Profil sehen dürfen, dein Geburtsdatum unter «Über mich».',
  },
]

export const chatProtectionOptions = [
  { value: 'standard', label: 'Standard', icon: 'shield-trust' },
  { value: 'device', label: 'Nur auf diesem Gerät', icon: 'laptop' },
  { value: 'pin', label: 'Chat-PIN', icon: 'lock' },
]

export const chatProtectionHints = {
  standard: 'Verschlüsselt gespeichert. Zugang auf jedem Gerät mit deinem Login.',
  device:
    'Ende-zu-Ende verschlüsselt. Nur dieses Gerät kann deine Chats lesen, neue Geräte sehen nur neue Nachrichten.',
  pin: 'Ende-zu-Ende verschlüsselt. Auf neuen Geräten entsperrst du deine Chats mit deiner PIN.',
}
