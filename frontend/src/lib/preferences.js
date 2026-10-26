import { rootAttribute, storedChoice, storedFlag } from '@/lib/storedSetting.js'

const THEME_ATTRIBUTES = { auto: null, light: 'swissfy', dark: 'dark' }

export const themeMode = storedChoice('theme', ['auto', 'light', 'dark'], (mode) =>
  rootAttribute('data-theme', THEME_ATTRIBUTES[mode]),
)

export const design = storedChoice('design', ['default', 'glass', 'cyberpunk'], (value) =>
  rootAttribute('data-design', value === 'default' ? null : value),
)

export const dyslexiaFont = storedFlag('dyslexia-font', {
  apply: (enabled) => rootAttribute('data-dyslexia', enabled ? 'on' : null),
})

export const contrastMode = storedFlag('contrast-mode', {
  apply: (enabled) => rootAttribute('data-contrast', enabled ? 'on' : null),
})

export const videoAutoplay = storedFlag('video-autoplay')

export const videoLoop = storedFlag('video-loop')

export const persistentLogin = storedFlag('persistent-login', { fallback: true })
