<template>
  <div class="flex flex-col gap-3">
    <p class="text-sm" :class="reportCount ? 'text-error' : 'text-app-muted'">
      {{ reportCount ? `${reportCount}× gemeldet` : 'Keine offenen Meldungen' }}
    </p>
    <form class="flex flex-wrap gap-2" @submit.prevent="warn">
      <p v-if="!canWarn" class="flex-1 self-center text-sm text-app-muted">
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
    <ErrorText :message="error" />
    <ul v-if="warnings.length" class="flex flex-col gap-1 text-sm">
      <li v-for="warning in warnings" :key="warning.id" class="text-app-muted">
        Verwarnt: <span class="text-base-content">{{ warning.reason }}</span> ·
        {{ formatDate(warning.created_at) }}
      </li>
    </ul>
  </div>
</template>

<script>
import ErrorText from '@core/components/ErrorText.vue'
import asyncActionMixin from '@core/mixins/asyncActionMixin.js'
import AppIcon from '@core/components/AppIcon.vue'
import BaseButton from '@core/components/BaseButton.vue'
import moderationApi from '@/api/moderation.js'
import { formatDate } from '@/lib/time.js'

export default {
  name: 'ModerationPanel',
  mixins: [asyncActionMixin],
  components: { AppIcon, BaseButton, ErrorText },
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
      const data = await this.runAction(action, 'Aktion fehlgeschlagen.')
      if (data) this.reportCount = data.report_count
      return data
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
