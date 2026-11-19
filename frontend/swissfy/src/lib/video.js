export const MAX_VIDEO_SIZE = 250 * 1024 * 1024
export const MAX_VIDEO_DURATION = 60

export function videoDuration(src) {
  return new Promise((resolve, reject) => {
    const video = document.createElement('video')
    video.preload = 'metadata'
    video.addEventListener('loadedmetadata', () => resolve(video.duration))
    video.addEventListener('error', reject)
    video.src = src
  })
}
