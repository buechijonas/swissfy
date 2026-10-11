export function commentLink(comment, moderation = false) {
  return moderation ? `/moderation/comments/${comment.id}` : `/comments/${comment.id}`
}
