<template>
  <div class="flex flex-col gap-3">
    <p class="text-sm" :class="reportCount ? 'text-error' : 'text-swissfy-muted'">
      {{ reportCount ? `${reportCount}× gemeldet` : 'Keine offenen Meldungen' }}
    </p>
    <form class="flex flex-wrap gap-2" @submit.prevent="warn">
      <p v-if="!canWarn" class="flex-1 self-center text-sm text-swissfy-muted">
        Bereits verwarnt und öffentlich verborgen.
      </p>
      <select v-else v-model="reason" class="select min-w-0 flex-1">
        <option value="" disabled>Grund der Verwarnung</option>
        <option v-for="option in reasons" :key="option.value" :value="option.value">
          {{ option.label }}
        </option>
      </select>
      <BaseButton v-if="canWarn" type="submit" variant="primary" :disabled="busy || !reason">
        <AppIcon name="shield-exclamation" />
        Verwarnen
      </BaseButton>
      <BaseButton v-if="reportCount" :disabled="busy" @click="dismiss">
        <AppIcon name="cross" />
        Verwerfen
      </BaseButton>
    </form>
    <p v-if="error" class="text-error text-sm">{{ error }}</p>
    <ul v-if="warnings.length" class="flex flex-col gap-1 text-sm">
      <li v-for="warning in warnings" :key="warning.id" class="text-swissfy-muted">
        Verwarnt: <span class="text-base-content">{{ warning.reason }}</span> ·
        {{ formatDate(warning.created_at) }}
      </li>
    </ul>
  </div>
</template>

<script>
import AppIcon from '@/components/common/AppIcon.vue'
import BaseButton from '@/components/common/BaseButton.vue'
import moderationApi from '@/api/moderation.js'
import { formatDate } from '@/lib/time.js'

export default {
  name: 'ModerationPanel',
  components: { AppIcon, BaseButton },
  props: {
    kind: { type: String, required: true },
    targetId: { type: String, required: true },
    details: { type: Object, required: true },
  },
  data() {
    return {
      reason: '',
      reportCount: this.details.report_count,
      canWarn: this.details.can_warn,
      warnings: [...this.details.warnings],
      busy: false,
      error: null,
    }
  },
  computed: {
    reasons() {
      return this.details.reasons
    },
  },
  methods: {
    formatDate,
    async send(action) {
      this.busy = true
      this.error = null
      try {
        const data = await action()
        this.reportCount = data.report_count
        return data
      } catch (error) {
        this.error = error.detail ?? 'Aktion fehlgeschlagen.'
        return null
      } finally {
        this.busy = false
      }
    },
    async warn() {
      const data = await this.send(() => moderationApi.warn(this.kind, this.targetId, this.reason))
      if (!data) return
      this.warnings.unshift(data.warning)
      this.canWarn = false
      this.reason = ''
    },
    async dismiss() {
      await this.send(() => moderationApi.dismiss(this.kind, this.targetId))
    },
  },
}
</script>
