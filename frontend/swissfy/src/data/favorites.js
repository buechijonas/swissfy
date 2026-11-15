import { t } from '@/i18n.js'

export function favoriteKinds() {
  return [
    {
      kind: 'movies',
      field: 'favorite_movies',
      label: t('favorites.movies'),
      icon: 'clapperboard-play',
      placeholder: t('favorites.searchMovie'),
    },
    {
      kind: 'series',
      field: 'favorite_series',
      label: t('favorites.series'),
      icon: 'play',
      placeholder: t('favorites.searchSeries'),
    },
    {
      kind: 'games',
      field: 'favorite_games',
      label: t('favorites.games'),
      icon: 'trophy',
      placeholder: t('favorites.searchGame'),
    },
  ]
}
