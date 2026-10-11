<template>
  <BaseBreadcrumbs :items="breadcrumbs" />
  <div
    class="flex flex-col pb-8 px-6 max-sm:pb-0 max-h-[calc(100dvh-96px)] overflow-y-auto lg:max-h-none lg:overflow-y-visible lg:flex-1"
  >
    <div class="mx-auto w-full max-w-150 sm:pt-4">
      <BaseCard v-if="items.length" tag="ul" class="divide-y divide-swissfy-border">
        <li
          v-for="item in items"
          :key="item.id"
          class="flex gap-3 px-4 py-3"
          :class="{ 'bg-swissfy-highlight': unreadIds.has(item.id) }"
        >
          <img v-if="item.actor" class="size-10 shrink-0" :src="avatarSrc(item.actor)" alt="" />
          <span
            v-else
            class="flex size-10 shrink-0 items-center justify-center rounded-full"
            :class="KIND_BUBBLES[item.kind] ?? 'bg-base-200'"
          >
            <AppIcon :name="KIND_ICONS[item.kind]" class="size-5!" />
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
            <span class="text-xs text-swissfy-muted">{{
              formatRelativeTime(item.created_at)
            }}</span>
            <div v-if="item.friend_request === 'pending'" class="mt-1 flex gap-2">
              <BaseButton
                size="sm"
                variant="primary"
                :disabled="busy"
                @click="answer(item, 'POST', 'accepted')"
              >
                Annehmen
              </BaseButton>
              <BaseButton size="sm" :disabled="busy" @click="answer(item, 'DELETE', 'declined')">
                Ablehnen
              </BaseButton>
            </div>
            <span v-else-if="item.friend_request" class="text-xs text-swissfy-muted">
              {{ item.friend_request === 'accepted' ? 'Angenommen' : 'Abgelehnt' }}
            </span>
          </div>
          <RouterLink
            v-if="item.link"
            :to="item.link"
            class="flex shrink-0 self-center box-content p-2.5 -m-2.5 text-swissfy-muted hover:text-base-content"
            title="Öffnen"
          >
            <AppIcon name="arrow-up-right-from-square" alt="Öffnen" class="size-5!" />
          </RouterLink>
        </li>
      </BaseCard>
      <BaseCard v-else-if="!loading && !error" class="p-6">
        <p class="text-swissfy-muted">Noch keine Benachrichtigungen.</p>
      </BaseCard>

      <p v-if="error" class="text-error text-sm mt-4 text-center">{{ error }}</p>
      <div v-if="loading" class="skeleton h-24 w-full mt-4"></div>
      <BaseButton v-else-if="next" class="mt-4" size="sm" block @click="load">
        Weitere laden
      </BaseButton>
    </div>
  </div>
  <BaseFooter />
</template>

<script>
import { RouterLink } from 'vue-router'
import AppIcon from '@/components/common/AppIcon.vue'
import BaseBreadcrumbs from '@/components/common/BaseBreadcrumbs.vue'
import BaseButton from '@/components/common/BaseButton.vue'
import BaseCard from '@/components/common/BaseCard.vue'
import BaseFooter from '@/components/common/BaseFooter.vue'
import { icons } from '@/assets/icons.js'
import { avatars } from '@/assets/images.js'
import { apiFetch, extractErrorMessage } from '@/lib/api.js'
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
  components: { RouterLink, AppIcon, BaseBreadcrumbs, BaseButton, BaseCard, BaseFooter },
  data() {
    return {
      KIND_ICONS,
      KIND_COLORS,
      KIND_BUBBLES,
      breadcrumbs: [{ label: 'Benachrichtigungen', to: '/notifications' }],
      items: [],
      unreadIds: new Set(),
      next: '/api/notifications/',
      loading: false,
      busy: false,
      error: null,
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
    avatarSrc(user) {
      return avatars[user.avatar] ?? icons.user
    },
    async load() {
      this.loading = true
      this.error = null
      try {
        const response = await apiFetch(this.next)
        if (!response.ok) throw new Error()
        const data = await response.json()
        this.items.push(...data.results)
        for (const item of data.results) if (!item.read) this.unreadIds.add(item.id)
        this.next = data.next
      } catch {
        this.error = 'Benachrichtigungen konnten nicht geladen werden.'
      } finally {
        this.loading = false
      }
    },
    async answer(item, method, state) {
      this.busy = true
      this.error = null
      try {
        const response = await apiFetch(
          `/api/social/profiles/me/friend-requests/${encodeURIComponent(item.actor.username)}/`,
          { method },
        )
        if (!response.ok) {
          const data = await response.json().catch(() => null)
          this.error = extractErrorMessage(data, 'Aktion fehlgeschlagen.')
          return
        }
        item.friend_request = state
      } finally {
        this.busy = false
      }
    },
  },
}
</script>
