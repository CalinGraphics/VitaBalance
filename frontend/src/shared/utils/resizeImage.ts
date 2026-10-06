/** Mărimea pozei de profil trimise la server (pătrat, în pixeli). */
export const AVATAR_SIZE = 256

/** Fișiere mai mari nu sunt nici măcar citite (o poză de telefon are de obicei 2–8 MB). */
const MAX_SOURCE_BYTES = 20 * 1024 * 1024

export class ImageResizeError extends Error {
  constructor(public readonly reason: 'type' | 'read') {
    super(reason)
  }
}

function loadImage(file: File): Promise<HTMLImageElement> {
  return new Promise((resolve, reject) => {
    const url = URL.createObjectURL(file)
    const img = new Image()
    img.onload = () => {
      URL.revokeObjectURL(url)
      resolve(img)
    }
    img.onerror = () => {
      URL.revokeObjectURL(url)
      reject(new ImageResizeError('read'))
    }
    img.src = url
  })
}

/**
 * Decupează centrul imaginii la pătrat, o micșorează la `size` px și o întoarce ca data URL (WebP, sau JPEG
 * în browserele care nu pot codifica WebP). Poza trimisă are astfel câțiva KB, indiferent de original.
 */
export async function resizeImageToDataUrl(file: File, size = AVATAR_SIZE): Promise<string> {
  if (!file.type.startsWith('image/') || file.size > MAX_SOURCE_BYTES) {
    throw new ImageResizeError('type')
  }
  const img = await loadImage(file)
  const side = Math.min(img.naturalWidth, img.naturalHeight)
  if (!side) throw new ImageResizeError('read')

  const canvas = document.createElement('canvas')
  canvas.width = size
  canvas.height = size
  const ctx = canvas.getContext('2d')
  if (!ctx) throw new ImageResizeError('read')
  ctx.imageSmoothingQuality = 'high'
  ctx.drawImage(
    img,
    (img.naturalWidth - side) / 2,
    (img.naturalHeight - side) / 2,
    side,
    side,
    0,
    0,
    size,
    size
  )

  const webp = canvas.toDataURL('image/webp', 0.85)
  // Safari întoarce PNG când nu poate codifica WebP; JPEG e mult mai mic pentru o fotografie.
  return webp.startsWith('data:image/webp') ? webp : canvas.toDataURL('image/jpeg', 0.85)
}
