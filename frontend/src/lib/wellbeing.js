import { ref, watch } from 'vue'

function readStoredValue(key) {
  try {
    return localStorage.getItem(key) === 'on'
  } catch {
    return false
  }
}

function storedFlag(key) {
  const flag = ref(readStoredValue(key))
  watch(flag, (enabled) => {
    try {
      localStorage.setItem(key, enabled ? 'on' : 'off')
    } catch {}
  })
  return flag
}

export const videoAutoplay = storedFlag('video-autoplay')
export const videoLoop = storedFlag('video-loop')
