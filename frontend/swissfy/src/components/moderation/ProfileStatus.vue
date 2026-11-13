<template>
  <BaseCard class="p-6 border-t-0">
    <ErrorText v-if="error" :message="error" />
    <div v-else-if="!events" class="skeleton h-16 w-full"></div>
    <p v-else-if="!events.length">Keine Verwarnungen.</p>
    <ol v-if="events?.length">
      <li
        v-for="event in events"
        :key="`${event.type}-${event.id}`"
        class="group/event relative flex gap-4 pb-6 last:pb-0"
      >
        <span
          class="group-last/event:hidden absolute left-1.5 top-[1.375rem] -bottom-0.5 w-0.5 -translate-x-1/2 bg-app-border"
        ></span>
        <span class="mt-1.5 size-3 shrink-0 rounded-full" :class="dotClass(event)"></span>
        <div class="flex min-w-0 flex-1 flex-col gap-0.5" :class="{ 'opacity-60': event.past }">
          <span class="text-xs text-app-muted">{{ formatDate(event.created_at) }}</span>
          <template v-if="event.type === 'warning'">
            <span class="font-bold">Verwarnung: {{ event.reason }}</span>
            <span v-if="event.target" class="text-sm text-app-muted">{{ event.target }}</span>
            <span class="text-sm" :class="event.expired ? 'text-app-muted' : ''">
              {{ event.expired ? 'Verjährt seit' : 'Verjährt am' }}
              {{ formatDate(event.expires_at) }}
            </span>
            <RouterLink v-if="event.link" :to="event.link" class="link text-sm">Ansehen</RouterLink>
          </template>
          <template v-else>
            <span class="font-bold">Kontosperre: {{ event.duration }}</span>
            <span class="text-sm" :class="{ 'text-error': event.state === 'active' }">
              {{ event.status_text }}
            </span>
          </template>
        </div>
      </li>
    </ol>

    <template v-if="reports">
      <h3 class="mt-8 mb-2 text-app-muted">Gemeldete Inhalte</h3>
      <ul v-if="reports.length" class="divide-y divide-app-border">
        <li
          v-for="report in reports"
          :key="report.link"
          class="flex items-center justify-between gap-4 py-3"
        >
          <div class="flex min-w-0 flex-col">
            <span class="truncate">{{ report.text || report.type }}</span>
            <span class="text-xs" :class="report.open_count ? 'text-error' : 'text-app-muted'">
              {{ report.type }} · {{ report.report_count }}× gemeldet
              {{ report.open_count ? `· ${report.open_count} offen` : '· erledigt' }}
            </span>
          </div>
          <BaseButton size="sm" :to="report.link">
            <AppIcon name="eye" />
            Ansehen
          </BaseButton>
        </li>
      </ul>
      <p v-else>Keine gemeldeten Inhalte.</p>
    </template>
  </BaseCard>
</template>

<script>
import ErrorText from '@core/components/ErrorText.vue'
import { RouterLink } from 'vue-router'
import AppIcon from '@core/components/AppIcon.vue'
import BaseButton from '@core/components/BaseButton.vue'
import BaseCard from '@core/components/BaseCard.vue'
import profilesApi from '@/api/profiles.js'
import { formatDate } from '@/lib/time.js'

export default {
  name: 'ProfileStatus',
  components: { RouterLink, AppIcon, BaseButton, BaseCard, ErrorText },
  props: {
    username: { type: String, required: true },
  },
  data() {
    return { events: null, reports: null, error: null }
  },
  async created() {
    try {
      const data = await profilesApi.status(this.username)
      this.events = data.events
      this.reports = data.reports
    } catch {
      this.error = 'Status konnte nicht geladen werden.'
    }
  },
  methods: {
    formatDate,
    dotClass(event) {
      if (event.past) return 'bg-app-border'
      return event.type === 'suspension' ? 'bg-error' : 'bg-warning'
    },
  },
}
</script>
