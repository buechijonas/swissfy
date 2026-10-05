import swissfy from './swissfy.js'

const undraws = import.meta.glob('../../assets/images/undraws/*.svg', {
  eager: true,
  import: 'default',
})

export const illustrations = Object.fromEntries(
  Object.entries(undraws).map(([path, src]) => [path.split('/').pop().replace('.svg', ''), src]),
)

export const contracts = swissfy
