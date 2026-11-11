import { rootAttribute, storedChoice, storedFlag } from '@core/lib/storedSetting.js'

export { contrastMode, dyslexiaFont, themeMode } from '@core/lib/appearance.js'

export const design = storedChoice(
  'design',
  ['default', 'glass', 'cyberpunk', 'ecopunk', 'romance', 'y2k'],
  (value) => rootAttribute('data-design', value === 'default' ? null : value),
)

export const videoAutoplay = storedFlag('video-autoplay')

export const videoLoop = storedFlag('video-loop')

export const persistentLogin = storedFlag('persistent-login', { fallback: true })
