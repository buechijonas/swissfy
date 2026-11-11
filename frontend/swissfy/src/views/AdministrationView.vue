<template>
  <BaseBreadcrumbs :items="breadcrumbs" />
  <div
    class="flex flex-col pb-8 px-6 max-h-[calc(100dvh-var(--mobile-chrome-height))] overflow-y-auto lg:max-h-none lg:overflow-y-visible lg:flex-1"
  >
    <div class="mx-auto w-full max-w-150 pt-4">
      <div class="flex flex-wrap gap-2 mb-4">
        <label class="input min-w-0 flex-1">
          <AppIcon name="search" class="text-swissfy-muted" />
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

      <BaseCard v-if="users.length" tag="ul" class="divide-y divide-swissfy-border">
        <li v-for="user in users" :key="user.username" class="flex items-center gap-4 px-6 py-3">
          <UserAvatar class="size-12" :user="user" />
          <RouterLink :to="profileLink(user)" class="flex min-w-0 flex-1 flex-col">
            <span class="flex min-w-0 items-center gap-2">
              <span class="font-bold truncate">{{ fullName(user) || user.username }}</span>
              <RoleBadge :role="user.badge" />
            </span>
            <span class="text-swissfy-muted text-sm truncate">@{{ user.username }}</span>
            <span v-if="user.role_locked_until" class="text-error text-xs">
              {{ lockText(user) }}
            </span>
          </RouterLink>
          <select
            class="select select-sm w-auto"
            :value="user.role"
            :disabled="user.is_self || !!user.role_locked_until || saving === user.username"
            :title="user.is_self ? 'Deine eigene Rolle kannst du nicht ändern.' : 'Rolle'"
            @change="changeRole(user, $event.target.value)"
          >
            <option v-for="role in roles" :key="role.value" :value="role.value">
              {{ role.label }}
            </option>
          </select>
        </li>
      </BaseCard>
      <BaseCard v-else-if="!loading && !error" class="p-6">
        <p class="text-swissfy-muted">Keine User gefunden.</p>
      </BaseCard>

      <p v-if="error" class="text-error text-sm mt-4 text-center">{{ error }}</p>
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
import { RouterLink } from 'vue-router'
import AppIcon from '@/components/common/AppIcon.vue'
import BaseBreadcrumbs from '@/components/common/BaseBreadcrumbs.vue'
import BaseButton from '@/components/common/BaseButton.vue'
import BaseCard from '@/components/common/BaseCard.vue'
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
    UserAvatar,
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
      clearTimeout(this.timer)
      this.timer = setTimeout(() => {
        this.query = term.trim()
      }, DEBOUNCE_MS)
    },
    query() {
      this.reload()
    },
    roleFilter() {
      this.reload()
    },
  },
  async created() {
    this.roles = await administrationApi.roles().catch(() => [])
    this.reload()
  },
  beforeUnmount() {
    clearTimeout(this.timer)
  },
  methods: {
    fullName(user) {
      return [user.first_name, user.last_name].filter(Boolean).join(' ')
    },
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
