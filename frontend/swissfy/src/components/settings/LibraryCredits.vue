<template>
  <p class="text-xs text-app-muted">
    <i18n-t keypath="favorites.credits">
      <template #imdb>
        <a class="link" href="https://www.imdb.com" target="_blank" rel="noopener noreferrer"
          >IMDb</a
        >
      </template>
      <template #steam>
        <a
          class="link"
          href="https://store.steampowered.com"
          target="_blank"
          rel="noopener noreferrer"
          >Steam</a
        >
      </template>
    </i18n-t>
  </p>
</template>

<script>
export default {
  name: 'LibraryCredits',
}
</script>
