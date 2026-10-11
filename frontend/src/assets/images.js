const avatarModules = import.meta.glob('./images/avatars/*.svg', { eager: true, import: 'default' })

export const avatars = Object.fromEntries(
  Object.entries(avatarModules).map(([path, src]) => [
    path.split('/').pop().replace('.svg', ''),
    src,
  ]),
)

const badgeModules = import.meta.glob('./badges/*.svg', { eager: true, import: 'default' })

export const badges = Object.fromEntries(
  Object.entries(badgeModules).map(([path, src]) => [
    path.split('/').pop().replace('.svg', ''),
    src,
  ]),
)
