<template>
  <BaseBreadcrumbs :items="breadcrumbs" />
  <div
    class="flex flex-col pb-8 px-6 max-sm:pb-0 max-h-[calc(100dvh-var(--mobile-chrome-height))] overflow-y-auto lg:max-h-none lg:overflow-y-visible lg:flex-1"
  >
    <div class="mx-auto w-full max-w-150 sm:pt-4">
      <BaseCard v-if="items.length" tag="ul" class="divide-y divide-app-border">
        <li
          v-for="item in items"
          :key="item.id"
          class="flex gap-3 px-4 py-3"
          :class="{ 'bg-swissfy-highlight': unreadIds.has(item.id) }"
        >
          <UserAvatar v-if="item.actor" class="size-10" :user="item.actor" />
          <span
            v-else
            class="flex size-10 shrink-0 items-center justify-center rounded-full"
            :class="KIND_BUBBLES[item.kind] ?? 'bg-base-200'"
          >
            <AppIcon :name="KIND_ICONS[item.kind]" class="size-6!" />
          </span>
          <div class="flex min-w-0 flex-1 flex-col gap-1">
            <RouterLink
              v-if="item.link"
              :to="item.link"
              class="break-words hover:underline"
              :class="KIND_COLORS[item.kind]"
            >
              {{ item.message }}
            </RouterLink>
            <span v-else class="break-words" :class="KIND_COLORS[item.kind]">
              {{ item.message }}
            </span>
            <span class="text-xs text-app-muted">{{ formatRelativeTime(item.created_at) }}</span>
            <div v-if="item.request === 'pending'" class="mt-1 flex gap-2">
              <BaseButton
                size="sm"
                variant="primary"
                :disabled="busy"
                @click="answer(item, 'accepted')"
              >
                <AppIcon name="check" />
                Annehmen
              </BaseButton>
              <BaseButton size="sm" :disabled="busy" @click="answer(item, 'declined')">
                <AppIcon name="cross" />
                Ablehnen
              </BaseButton>
            </div>
            <span v-else-if="item.request" class="text-xs text-app-muted">
              {{ item.request === 'accepted' ? 'Angenommen' : 'Abgelehnt' }}
            </span>
          </div>
          <RouterLink
            v-if="item.link"
            :to="item.link"
            class="flex shrink-0 self-center box-content p-2.5 -m-2.5 text-app-muted hover:text-base-content"
            title="Öffnen"
          >
            <AppIcon name="arrow-up-right-from-square" alt="Öffnen" class="size-6!" />
          </RouterLink>
        </li>
      </BaseCard>
      <BaseCard v-else-if="!loading && !error" class="p-6">
        <p class="text-app-muted">Noch keine Benachrichtigungen.</p>
      </BaseCard>

      <ErrorText :message="error" class="mt-4 text-center" />
      <div v-if="loading" class="skeleton h-24 w-full mt-4"></div>
      <BaseButton v-else-if="next" class="mt-4" size="sm" block @click="load">
        <AppIcon name="down" />
        Weitere laden
      </BaseButton>
    </div>
  </div>
  <BaseFooter />
</template>

<script>
import ErrorText from '@core/components/ErrorText.vue'
import asyncActionMixin from '@core/mixins/asyncActionMixin.js'
import { RouterLink } from 'vue-router'
import AppIcon from '@core/components/AppIcon.vue'
import BaseBreadcrumbs from '@/components/common/BaseBreadcrumbs.vue'
import BaseButton from '@core/components/BaseButton.vue'
import BaseCard from '@core/components/BaseCard.vue'
import BaseFooter from '@/components/common/BaseFooter.vue'
import UserAvatar from '@/components/common/UserAvatar.vue'
import notificationsApi from '@/api/notifications.js'
import profilesApi from '@/api/profiles.js'
import { formatRelativeTime } from '@/lib/time.js'
import { useNotificationsStore } from '@/stores/notifications.js'

const KIND_ICONS = {
  warning: 'shield-exclamation',
  warning_expired: 'check',
  suspension: 'lock',
}

const KIND_COLORS = {
  warning: 'text-warning',
  suspension: 'text-error',
}

const KIND_BUBBLES = {
  warning: 'bg-warning/15 text-warning',
  suspension: 'bg-error/15 text-error',
}

export default {
  name: 'NotificationsView',
  mixins: [asyncActionMixin],
  components: {
    RouterLink,
    AppIcon,
    BaseBreadcrumbs,
    BaseButton,
    BaseCard,
    BaseFooter,
    UserAvatar,
    ErrorText,
  },
  data() {
    return {
      KIND_ICONS,
      KIND_COLORS,
      KIND_BUBBLES,
      breadcrumbs: [{ label: 'Benachrichtigungen', to: '/notifications' }],
      items: [],
      unreadIds: new Set(),
      next: notificationsApi.listUrl(),
      loading: false,
    }
  },
  async created() {
    await this.load()
    useNotificationsStore()
      .markRead()
      .catch(() => {})
  },
  methods: {
    formatRelativeTime,
    async load() {
      this.loading = true
      this.error = null
      try {
        const data = await notificationsApi.list(this.next)
        this.items.push(...data.results)
        for (const item of data.results) if (!item.read) this.unreadIds.add(item.id)
        this.next = data.next
      } catch {
        this.error = 'Benachrichtigungen konnten nicht geladen werden.'
      } finally {
        this.loading = false
      }
    },
    async answer(item, state) {
      const respond = state === 'accepted' ? profilesApi.acceptRequest : profilesApi.declineRequest
      await this.runAction(() => respond(item.kind, item.actor.username), 'Aktion fehlgeschlagen.')
      if (!this.error) item.request = state
    },
  },
}
</script>
