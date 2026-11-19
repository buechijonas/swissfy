<template>
  <BaseBreadcrumbs :items="breadcrumbs" />
  <div
    class="flex max-h-[calc(100dvh-var(--mobile-chrome-height))] flex-col overflow-y-auto px-6 pb-8 max-sm:pb-0 lg:max-h-none lg:flex-1 lg:overflow-y-visible"
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
                :disabled="action.busy"
                @click="answer(item, 'accepted')"
              >
                <AppIcon name="check" />
                {{ $t('notifications.accept') }}
              </BaseButton>
              <BaseButton size="sm" :disabled="action.busy" @click="answer(item, 'declined')">
                <AppIcon name="cross" />
                {{ $t('notifications.decline') }}
              </BaseButton>
            </div>
            <span v-else-if="item.request" class="text-xs text-app-muted">
              {{
                item.request === 'accepted'
                  ? $t('notifications.accepted')
                  : $t('notifications.declined')
              }}
            </span>
          </div>
          <RouterLink
            v-if="item.link"
            :to="item.link"
            class="-m-2.5 box-content flex shrink-0 self-center p-2.5 text-app-muted hover:text-base-content"
            :title="$t('notifications.open')"
          >
            <AppIcon
              name="arrow-up-right-from-square"
              :alt="$t('notifications.open')"
              class="size-6!"
            />
          </RouterLink>
        </li>
      </BaseCard>
      <BaseCard v-else-if="!loading && !action.error" class="p-6">
        <p class="text-app-muted">{{ $t('notifications.empty') }}</p>
      </BaseCard>

      <ErrorText :message="action.error" class="mt-4 text-center" />
      <div v-if="loading" class="mt-4 h-24 w-full skeleton"></div>
      <BaseButton v-else-if="next" class="mt-4" size="sm" block @click="load">
        <AppIcon name="down" />
        {{ $t('common.loadMore') }}
      </BaseButton>
    </div>
  </div>
  <BaseFooter />
</template>

<script>
import { RouterLink } from 'vue-router'
import AppIcon from '@core/components/AppIcon.vue'
import BaseButton from '@core/components/BaseButton.vue'
import BaseCard from '@core/components/BaseCard.vue'
import ErrorText from '@core/components/ErrorText.vue'
import { useAsyncAction } from '@core/composables/asyncAction.js'
import notificationsApi from '@/api/notifications.js'
import profilesApi from '@/api/profiles.js'
import BaseBreadcrumbs from '@/components/common/BaseBreadcrumbs.vue'
import BaseFooter from '@/components/common/BaseFooter.vue'
import UserAvatar from '@/components/common/UserAvatar.vue'
import { t } from '@/i18n.js'
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
      action: useAsyncAction(),
      KIND_ICONS,
      KIND_COLORS,
      KIND_BUBBLES,
      items: [],
      unreadIds: new Set(),
      next: notificationsApi.listUrl(),
      loading: false,
    }
  },
  computed: {
    breadcrumbs() {
      return [{ label: t('notifications.title'), to: '/notifications' }]
    },
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
      this.action.error = null
      try {
        const data = await notificationsApi.list(this.next)
        this.items.push(...data.results)
        for (const item of data.results) if (!item.read) this.unreadIds.add(item.id)
        this.next = data.next
      } catch {
        this.action.error = t('notifications.loadFailed')
      } finally {
        this.loading = false
      }
    },
    async answer(item, state) {
      const respond = state === 'accepted' ? profilesApi.acceptRequest : profilesApi.declineRequest
      await this.action.run(
        () => respond(item.kind, item.actor.username),
        t('notifications.actionFailed'),
      )
      if (!this.action.error) item.request = state
    },
  },
}
</script>
