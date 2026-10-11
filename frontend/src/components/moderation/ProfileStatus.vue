<template>
  <BaseCard class="p-6 border-t-0">
    <p v-if="error" class="text-error text-sm">{{ error }}</p>
    <div v-else-if="!events" class="skeleton h-16 w-full"></div>
    <p v-else-if="!events.length">Keine Verwarnungen.</p>
    <ol v-if="events?.length">
      <li
        v-for="(event, index) in events"
        :key="`${event.type}-${event.id}`"
        class="relative flex gap-4 pb-6 last:pb-0"
      >
        <span
          v-if="index < events.length - 1"
          class="absolute left-1.5 top-[1.375rem] -bottom-0.5 w-0.5 -translate-x-1/2 bg-swissfy-border"
        ></span>
        <span class="mt-1.5 size-3 shrink-0 rounded-full" :class="dotClass(event)"></span>
        <div class="flex min-w-0 flex-1 flex-col gap-0.5" :class="{ 'opacity-60': isPast(event) }">
          <span class="text-xs text-swissfy-muted">{{ formatDate(event.created_at) }}</span>
          <template v-if="event.type === 'warning'">
            <span class="font-bold">Verwarnung: {{ event.reason }}</span>
            <span v-if="event.target" class="text-sm text-swissfy-muted">{{ event.target }}</span>
            <span class="text-sm" :class="event.expired ? 'text-swissfy-muted' : ''">
              {{ event.expired ? 'Verjährt seit' : 'Verjährt am' }}
              {{ formatDate(event.expires_at) }}
            </span>
            <RouterLink v-if="event.link" :to="event.link" class="link text-sm">Ansehen</RouterLink>
          </template>
          <template v-else>
            <span class="font-bold">Kontosperre: {{ event.duration }}</span>
            <span class="text-sm" :class="{ 'text-error': event.state === 'active' }">
              {{ suspensionText(event) }}
            </span>
          </template>
        </div>
      </li>
    </ol>

    <template v-if="reports">
      <h3 class="mt-8 mb-2 text-swissfy-muted">Gemeldete Inhalte</h3>
      <ul v-if="reports.length" class="divide-y divide-swissfy-border">
        <li
          v-for="report in reports"
          :key="report.link"
          class="flex items-center justify-between gap-4 py-3"
        >
          <div class="flex min-w-0 flex-col">
            <span class="truncate">{{ report.text || report.type }}</span>
            <span class="text-xs" :class="report.open_count ? 'text-error' : 'text-swissfy-muted'">
              {{ report.type }} · {{ report.report_count }}× gemeldet
              {{ report.open_count ? `· ${report.open_count} offen` : '· erledigt' }}
            </span>
          </div>
          <BaseButton size="sm" :to="report.link">Ansehen</BaseButton>
        </li>
      </ul>
      <p v-else>Keine gemeldeten Inhalte.</p>
    </template>
  </BaseCard>
</template>

<script>
import { RouterLink } from 'vue-router'
import BaseButton from '@/components/common/BaseButton.vue'
import BaseCard from '@/components/common/BaseCard.vue'
import { apiFetch } from '@/lib/api.js'
import { formatDate } from '@/lib/time.js'

export default {
  name: 'ProfileStatus',
  components: { RouterLink, BaseButton, BaseCard },
  props: {
    username: { type: String, required: true },
  },
  data() {
    return { events: null, reports: null, error: null }
  },
  async created() {
    try {
      const response = await apiFetch(
        `/api/social/profiles/${encodeURIComponent(this.username)}/status/`,
      )
      if (!response.ok) throw new Error()
      const data = await response.json()
      this.events = data.events
      this.reports = data.reports
    } catch {
      this.error = 'Status konnte nicht geladen werden.'
    }
  },
  methods: {
    formatDate,
    isPast(event) {
      return event.type === 'warning' ? event.expired : event.state === 'ended'
    },
    dotClass(event) {
      if (this.isPast(event)) return 'bg-swissfy-border'
      return event.type === 'suspension' ? 'bg-error' : 'bg-warning'
    },
    suspensionText(event) {
      const until = event.ends_at ? formatDate(event.ends_at) : null
      if (event.state === 'ended') return `Abgelaufen am ${until}`
      if (event.state === 'scheduled') {
        return until
          ? `Beginnt nach der laufenden Sperre, bis ${until}`
          : 'Beginnt nach der laufenden Sperre, dauerhaft'
      }
      return until ? `Gesperrt bis ${until}` : 'Dauerhaft gesperrt'
    },
  },
}
</script>
