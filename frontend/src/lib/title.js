export function pageTitle(route) {
  const { title } = route.meta
  return typeof title === 'function' ? title(route) : title
}
