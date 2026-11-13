<template>
  <BaseBreadcrumbs :items="breadcrumbs" />
  <div
    class="flex flex-col pb-8 px-6 max-h-[calc(100dvh-var(--mobile-chrome-height))] overflow-y-auto lg:max-h-none lg:overflow-y-visible lg:flex-1"
  >
    <div class="mx-auto w-full max-w-150 pt-4">
      <div class="flex flex-wrap gap-2 mb-4">
        <label class="input min-w-0 flex-1">
          <AppIcon name="search" class="text-app-muted" />
          <input
            v-model="term"
            type="search"
            class="grow"
            placeholder="Benutzername oder Name"
            autocomplete="off"
          />
        </label>
        <select v-model="roleFilter" class="select w-auto">
          <option value="">Alle Rollen</option>
          <option v-for="role in roles" :key="role.value" :value="role.value">
            {{ role.label }}
          </option>
        </select>
      </div>

      <BaseCard v-if="users.length" tag="ul" class="divide-y divide-app-border">
        <li v-for="user in users" :key="user.username" class="flex items-center gap-4 px-6 py-3">
          <UserAvatar class="size-12" :user="user" />
          <RouterLink :to="profileLink(user)" class="flex min-w-0 flex-1 flex-col">
            <span class="flex min-w-0 items-center gap-2">
              <span class="font-bold truncate">{{ user.display_name }}</span>
              <RoleBadge :role="user.badge" />
            </span>
            <span class="text-app-muted text-sm truncate">@{{ user.username }}</span>
            <span v-if="user.role_locked_until" class="text-error text-xs">
              {{ lockText(user) }}
            </span>
          </RouterLink>
          <RoleSelect
            :role="user.role"
            :roles="roles"
            :disabled="user.is_self || !!user.role_locked_until || saving === user.username"
            :title="user.is_self ? 'Deine eigene Rolle kannst du nicht ändern.' : 'Rolle'"
            @change="(role) => changeRole(user, role)"
          />
        </li>
      </BaseCard>
      <BaseCard v-else-if="!loading && !error" class="p-6">
        <p class="text-app-muted">Keine User gefunden.</p>
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
import debounce from 'lodash-es/debounce'
import RoleSelect from '@/components/administration/RoleSelect.vue'
import { RouterLink } from 'vue-router'
import AppIcon from '@core/components/AppIcon.vue'
import BaseBreadcrumbs from '@/components/common/BaseBreadcrumbs.vue'
import BaseButton from '@core/components/BaseButton.vue'
import BaseCard from '@core/components/BaseCard.vue'
import BaseFooter from '@/components/common/BaseFooter.vue'
import RoleBadge from '@/components/common/RoleBadge.vue'
import UserAvatar from '@/components/common/UserAvatar.vue'
import administrationApi from '@/api/administration.js'
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
      breadcrumbs: [{ label: 'Administration', to: '/administration' }],
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
      if (user.role_locked_until === 'forever') return 'Rolle dauerhaft gesperrt'
      return `Rolle gesperrt bis ${formatDate(user.role_locked_until)}`
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
        this.error = 'User konnten nicht geladen werden.'
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
        this.error = error.detail ?? 'Rolle konnte nicht geändert werden.'
      } finally {
        this.saving = null
      }
    },
  },
}
</script>
