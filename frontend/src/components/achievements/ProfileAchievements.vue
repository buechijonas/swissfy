<template>
  <BaseCard class="p-6 border-t-0">
    <p v-if="error" class="text-error text-sm">{{ error }}</p>
    <div v-else-if="!achievements" class="skeleton h-16 w-full"></div>
    <template v-else>
      <div class="mb-4 flex flex-wrap items-center justify-between gap-2">
        <p class="text-sm text-swissfy-muted">
          {{ unlockedCount }} von {{ regular.length }} Erfolgen freigeschaltet
          <template v-if="foundEggs">
            · {{ foundEggs }} von {{ eggs.length }} Easter Eggs gefunden
          </template>
        </p>
        <div class="flex gap-2">
          <BaseButton
            v-for="view in views"
            :key="view.key"
            size="sm"
            :variant="activeView === view.key ? 'primary' : 'neutral'"
            @click="activeView = view.key"
          >
            <AppIcon :name="view.icon" />
            {{ view.label }}
          </BaseButton>
        </div>
      </div>
      <p v-if="!timeline.length">Noch keine Erfolge.</p>
      <ul v-else-if="activeView === 'collection'" class="divide-y divide-swissfy-border">
        <li v-for="achievement in collection" :key="achievement.group" class="flex gap-4 py-3">
          <span
            class="flex size-10 shrink-0 items-center justify-center rounded-full"
            :class="accent(achievement).icon"
          >
            <AppIcon name="trophy" />
          </span>
          <div class="flex min-w-0 flex-1 flex-col gap-0.5">
            <span class="font-bold truncate" :class="accent(achievement).title">
              {{ achievement.title }}
            </span>
            <span class="text-sm text-swissfy-muted">{{ achievement.description }}</span>
            <span class="text-xs text-swissfy-muted">
              Seit {{ formatDate(achievement.unlocked_at) }}
              <template v-if="tierCounts[achievement.group] > 1">
                · Stufe {{ achievement.level }}/{{ tierCounts[achievement.group] }}
              </template>
            </span>
          </div>
        </li>
      </ul>
      <ol v-else>
        <li
          v-for="(achievement, index) in timeline"
          :key="achievement.key"
          class="relative flex gap-4 pb-6 last:pb-0"
        >
          <span
            v-if="index < timeline.length - 1"
            class="absolute left-5 top-10 -bottom-0.5 w-0.5 -translate-x-1/2 bg-swissfy-border"
          ></span>
          <span
            class="relative flex size-10 shrink-0 items-center justify-center rounded-full"
            :class="accent(achievement).icon"
          >
            <AppIcon :name="previousTitle(achievement) ? 'arrow-up' : 'trophy'" />
          </span>
          <div class="flex min-w-0 flex-1 flex-col gap-0.5">
            <span class="text-xs text-swissfy-muted">
              {{ formatDate(achievement.unlocked_at) }}
              <template v-if="tierCounts[achievement.group] > 1">
                · Stufe {{ achievement.level }}/{{ tierCounts[achievement.group] }}
              </template>
            </span>
            <span v-if="previousTitle(achievement)" class="text-sm text-swissfy-muted truncate">
              Aufgestiegen von <span class="line-through">{{ previousTitle(achievement) }}</span>
            </span>
            <span class="font-bold truncate" :class="accent(achievement).title">
              {{ achievement.title }}
            </span>
            <span class="text-sm text-swissfy-muted">{{ achievement.description }}</span>
          </div>
        </li>
      </ol>

      <template v-if="locked.length">
        <h3 class="mt-8 mb-2 text-swissfy-muted">
          {{ activeView === 'timeline' ? 'Nächste Ziele' : 'Noch nicht erreicht' }}
        </h3>
        <ul class="divide-y divide-swissfy-border">
          <li
            v-for="achievement in locked"
            :key="achievement.key"
            class="flex gap-4 py-3 opacity-60"
          >
            <span
              class="flex size-10 shrink-0 items-center justify-center rounded-full bg-base-200"
            >
              <AppIcon name="lock" />
            </span>
            <div class="flex min-w-0 flex-1 flex-col gap-1">
              <span v-if="previousTitle(achievement)" class="text-sm text-swissfy-muted truncate">
                Aufstieg von {{ previousTitle(achievement) }}
              </span>
              <span v-if="achievement.secret" class="text-xs text-swissfy-muted">
                Easter Egg · nur für Admins sichtbar
              </span>
              <span class="font-bold truncate">{{ achievement.title }}</span>
              <span class="text-sm text-swissfy-muted">{{ achievement.description }}</span>
              <template v-if="achievement.target">
                <progress
                  class="progress progress-primary h-1.5 w-full"
                  :value="achievement.count - achievement.previous"
                  :max="achievement.target - achievement.previous"
                ></progress>
                <span class="text-xs text-swissfy-muted">
                  {{ achievement.count }} / {{ achievement.target }}
                </span>
              </template>
            </div>
          </li>
        </ul>
      </template>
    </template>
  </BaseCard>
</template>

<script>
import AppIcon from '@/components/common/AppIcon.vue'
import BaseButton from '@/components/common/BaseButton.vue'
import BaseCard from '@/components/common/BaseCard.vue'
import { apiFetch } from '@/lib/api.js'
import { formatDate } from '@/lib/time.js'

const VIEWS = [
  { key: 'timeline', label: 'Timeline', icon: 'list-timeline' },
  { key: 'collection', label: 'Sammlung', icon: 'list' },
]
const DEFAULT_ACCENT = { icon: 'bg-primary text-primary-content', title: '' }
const SECRET_ACCENT = {
  icon: 'bg-amber-500/15 text-amber-500 ring-1 ring-amber-500/40',
  title: 'bg-linear-to-r from-amber-500 to-orange-500 bg-clip-text text-transparent',
}
const ACCENTS = {
  og: {
    icon: 'bg-violet-500/15 text-violet-500 ring-1 ring-violet-500/40',
    title:
      'bg-linear-to-r from-violet-500 to-fuchsia-500 bg-clip-text text-transparent tracking-widest',
  },
}

export default {
  name: 'ProfileAchievements',
  components: { AppIcon, BaseButton, BaseCard },
  props: {
    username: { type: String, required: true },
  },
  data() {
    return { achievements: null, error: null, activeView: 'timeline', views: VIEWS }
  },
  computed: {
    regular() {
      return this.achievements.filter((achievement) => !achievement.bonus && !achievement.secret)
    },
    eggs() {
      return this.achievements.filter((achievement) => achievement.secret)
    },
    foundEggs() {
      return this.eggs.filter((achievement) => achievement.unlocked).length
    },
    byKey() {
      return Object.fromEntries(
        this.achievements.map((achievement) => [achievement.key, achievement]),
      )
    },
    tierCounts() {
      const counts = {}
      for (const achievement of this.achievements) {
        counts[achievement.group] = (counts[achievement.group] ?? 0) + 1
      }
      return counts
    },
    unlockedCount() {
      return this.regular.filter((achievement) => achievement.unlocked).length
    },
    timeline() {
      return this.achievements
        .filter((achievement) => achievement.unlocked)
        .sort((a, b) => new Date(b.unlocked_at) - new Date(a.unlocked_at) || b.level - a.level)
    },
    collection() {
      const highest = {}
      for (const achievement of this.achievements) {
        if (achievement.unlocked) highest[achievement.group] = achievement
      }
      return Object.values(highest)
    },
    nextGoals() {
      const seen = new Set()
      return this.achievements.filter((achievement) => {
        if (achievement.unlocked || achievement.bonus || achievement.secret) return false
        if (seen.has(achievement.group)) return false
        seen.add(achievement.group)
        return !achievement.group.startsWith('topic_') || achievement.level > 1
      })
    },
    missing() {
      const owned = new Set(this.collection.map((achievement) => achievement.group))
      const seen = new Set()
      return this.achievements.filter((achievement) => {
        if (owned.has(achievement.group) || seen.has(achievement.group)) return false
        seen.add(achievement.group)
        return !achievement.bonus && (!achievement.secret || achievement.title)
      })
    },
    locked() {
      return this.activeView === 'timeline' ? this.nextGoals : this.missing
    },
  },
  async created() {
    try {
      const response = await apiFetch(
        `/api/social/profiles/${encodeURIComponent(this.username)}/achievements/`,
      )
      if (!response.ok) throw new Error()
      this.achievements = await response.json()
    } catch {
      this.error = 'Erfolge konnten nicht geladen werden.'
    }
  },
  methods: {
    formatDate,
    previousTitle(achievement) {
      return this.byKey[`${achievement.group}-${achievement.level - 1}`]?.title
    },
    accent(achievement) {
      if (achievement.secret) return SECRET_ACCENT
      return ACCENTS[achievement.group] ?? DEFAULT_ACCENT
    },
  },
}
</script>
