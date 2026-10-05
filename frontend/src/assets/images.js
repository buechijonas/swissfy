const avatarModules = import.meta.glob('./images/avatars/*.svg', { eager: true, import: 'default' })

export const avatars = Object.fromEntries(
  Object.entries(avatarModules).map(([path, src]) => [
    path.split('/').pop().replace('.svg', ''),
    src,
  ]),
)
