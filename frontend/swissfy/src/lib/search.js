const MIN_QUERY_LENGTH = 2

export function searchQuery(route) {
  const query = (route.query.q ?? '').trim()
  return query.length >= MIN_QUERY_LENGTH ? query : ''
}
