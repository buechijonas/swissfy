import { rootAttribute, sharedChoice, sharedFlag } from '@core/lib/storedSetting.js'

const THEME_ATTRIBUTES = { auto: null, light: 'swissfy', dark: 'dark' }

export const themeMode = sharedChoice('theme', ['auto', 'light', 'dark'], (mode) =>
  rootAttribute('data-theme', THEME_ATTRIBUTES[mode]),
)

export const dyslexiaFont = sharedFlag('dyslexia-font', {
  apply: (enabled) => rootAttribute('data-dyslexia', enabled ? 'on' : null),
})

export const contrastMode = sharedFlag('contrast-mode', {
  apply: (enabled) => rootAttribute('data-contrast', enabled ? 'on' : null),
})
