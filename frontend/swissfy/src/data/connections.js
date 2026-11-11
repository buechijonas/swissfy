export const CONNECTIONS = {
  followers: { title: 'Follower', emptyText: 'Noch keine Follower.' },
  following: { title: 'folgt', emptyText: 'Folgt noch niemandem.' },
  friends: { title: 'Freunde', emptyText: 'Noch keine Freunde.' },
}

export function connectionTitle(route) {
  return `@${route.params.username} ${CONNECTIONS[route.params.connection].title}`
}
