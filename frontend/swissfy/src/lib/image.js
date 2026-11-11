const MAX_SIDE = 1280
const QUALITY = 0.8

export async function compressImage(file) {
  try {
    const bitmap = await createImageBitmap(file, { imageOrientation: 'from-image' })
    const scale = Math.min(1, MAX_SIDE / Math.max(bitmap.width, bitmap.height))
    const canvas = document.createElement('canvas')
    canvas.width = Math.round(bitmap.width * scale)
    canvas.height = Math.round(bitmap.height * scale)
    canvas.getContext('2d').drawImage(bitmap, 0, 0, canvas.width, canvas.height)
    bitmap.close()
    const blob = await new Promise((resolve) => canvas.toBlob(resolve, 'image/webp', QUALITY))
    return blob && blob.size < file.size ? blob : file
  } catch {
    return file
  }
}

export async function imageSize(file) {
  const bitmap = await createImageBitmap(file, { imageOrientation: 'from-image' })
  const size = { width: bitmap.width, height: bitmap.height }
  bitmap.close()
  return size
}
