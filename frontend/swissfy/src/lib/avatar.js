import { avatars } from '@/assets/images.js'

export function avatarSrc(user) {
  return user?.picture ?? avatars[user?.avatar]
}
