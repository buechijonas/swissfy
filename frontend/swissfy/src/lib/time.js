import { locale } from '@core/lib/language.js'
import { t } from '@/i18n.js'

export function formatRelativeTime(value, nowValue = Date.now()) {
  const date = new Date(value)
  const now = new Date(nowValue)
  const yesterday = new Date(now)
  yesterday.setDate(now.getDate() - 1)
  const time = date.toLocaleTimeString(locale(), { hour: '2-digit', minute: '2-digit' })

  if (date.toDateString() === now.toDateString()) {
    const minutes = Math.floor((now - date) / 60000)
    if (minutes < 60) return t('time.minutesAgo', { count: Math.max(minutes, 1) })
    const hours = Math.floor(minutes / 60)
    return t('time.hoursAgo', { count: hours }, hours)
  }
  if (date.toDateString() === yesterday.toDateString()) return t('time.yesterday', { time })
  const day = date.toLocaleDateString(locale(), {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
  })
  return t('time.dateTime', { day, time })
}

export function formatDate(value) {
  return new Date(value).toLocaleDateString(locale(), {
    day: 'numeric',
    month: 'long',
    year: 'numeric',
    timeZone: 'UTC',
  })
}
