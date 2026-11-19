<template>
  <BaseBreadcrumbs :items="breadcrumbs" />
  <div
    class="flex max-h-[calc(100dvh-var(--mobile-chrome-height))] flex-col overflow-y-auto px-6 pb-8 lg:max-h-none lg:flex-1 lg:overflow-y-visible"
  >
    <div class="mx-auto w-full max-w-150 pt-4">
      <div class="mb-4 flex flex-wrap gap-2">
        <label class="input min-w-0 flex-1">
          <AppIcon name="search" class="text-app-muted" />
          <input
            v-model="term"
            type="search"
            class="grow"
            :placeholder="$t('administration.searchPlaceholder')"
            autocomplete="off"
          />
        </label>
        <select v-model="roleFilter" class="select w-auto">
          <option value="">{{ $t('administration.allRoles') }}</option>
          <option v-for="role in roles" :key="role.value" :value="role.value">
            {{ $t(`roles.${role.value}`) }}
          </option>
        </select>
      </div>

      <BaseCard v-if="users.length" tag="ul" class="divide-y divide-app-border">
        <li v-for="user in users" :key="user.username" class="flex items-center gap-4 px-6 py-3">
          <UserAvatar class="size-12" :user="user" />
          <RouterLink :to="profileLink(user)" class="flex min-w-0 flex-1 flex-col">
            <span class="flex min-w-0 items-center gap-2">
              <span class="truncate font-bold">{{ user.display_name }}</span>
              <RoleBadge :role="user.badge" />
            </span>
            <span class="truncate text-sm text-app-muted">@{{ user.username }}</span>
            <span v-if="user.role_locked_until" class="text-xs text-error">
              {{ lockText(user) }}
            </span>
          </RouterLink>
          <RoleSelect
            :role="user.role"
            :roles="roles"
            :disabled="user.is_self || !!user.role_locked_until || saving === user.username"
            :title="user.is_self ? $t('administration.ownRole') : $t('administration.role')"
            @change="(role) => changeRole(user, role)"
          />
        </li>
      </BaseCard>
      <BaseCard v-else-if="!loading && !error" class="p-6">
        <p class="text-app-muted">{{ $t('administration.noUsers') }}</p>
      </BaseCard>

      <ErrorText :message="error" class="mt-4 text-center" />
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
import debounce from 'lodash-es/debounce'
import { RouterLink } from 'vue-router'
import AppIcon from '@core/components/AppIcon.vue'
import BaseButton from '@core/components/BaseButton.vue'
import BaseCard from '@core/components/BaseCard.vue'
import ErrorText from '@core/components/ErrorText.vue'
import administrationApi from '@/api/administration.js'
import RoleSelect from '@/components/administration/RoleSelect.vue'
import BaseBreadcrumbs from '@/components/common/BaseBreadcrumbs.vue'
import BaseFooter from '@/components/common/BaseFooter.vue'
import RoleBadge from '@/components/common/RoleBadge.vue'
import UserAvatar from '@/components/common/UserAvatar.vue'
import { t } from '@/i18n.js'
import { formatDate } from '@/lib/time.js'

const DEBOUNCE_MS = 300

export default {
  name: 'AdministrationView',
  components: {
    RouterLink,
    AppIcon,
    BaseBreadcrumbs,
    BaseButton,
    BaseCard,
    BaseFooter,
    RoleBadge,
    RoleSelect,
    UserAvatar,
    ErrorText,
  },
  data() {
    return {
      roles: [],
      users: [],
      term: '',
      query: '',
      roleFilter: '',
      next: null,
      loading: false,
      saving: null,
      error: null,
    }
  },
  computed: {
    breadcrumbs() {
      return [{ label: t('administration.title'), to: '/administration' }]
    },
  },
  watch: {
    term(term) {
      this.debouncedQuery(term.trim())
    },
    query() {
      this.reload()
    },
    roleFilter() {
      this.reload()
    },
  },
  async created() {
    this.debouncedQuery = debounce((query) => (this.query = query), DEBOUNCE_MS)
    this.roles = await administrationApi.roles().catch(() => [])
    this.reload()
  },
  beforeUnmount() {
    this.debouncedQuery.cancel()
  },
  methods: {
    lockText(user) {
      if (user.role_locked_until === 'forever') return t('administration.roleLockedForever')
      return t('administration.roleLockedUntil', { date: formatDate(user.role_locked_until) })
    },
    profileLink(user) {
      return `/profile/${encodeURIComponent(user.username)}`
    },
    reload() {
      this.users = []
      this.next = administrationApi.usersUrl({
        ...(this.query && { q: this.query }),
        ...(this.roleFilter && { role: this.roleFilter }),
      })
      this.load()
    },
    async load() {
      const url = this.next
      this.loading = true
      this.error = null
      try {
        const data = await administrationApi.list(url)
        if (url !== this.next) return
        this.users.push(...data.results)
        this.next = data.next
      } catch {
        this.error = t('administration.loadFailed')
      } finally {
        this.loading = false
      }
    },
    async changeRole(user, role) {
      this.saving = user.username
      this.error = null
      try {
        Object.assign(user, await administrationApi.setRole(user.username, role))
      } catch (error) {
        this.error = error.detail ?? t('administration.changeFailed')
      } finally {
        this.saving = null
      }
    },
  },
}
</script>
