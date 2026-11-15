<template>
  <BaseDialog ref="dialog" :title="$t('create.title')">
    <div class="grid grid-cols-2 gap-3">
      <BaseButton
        v-for="option in kinds"
        :key="option.value"
        class="h-auto flex-col gap-2 py-6"
        @click="choose(option.value)"
      >
        <AppIcon :name="option.icon" class="size-6!" />
        <span class="text-base">{{ option.label }}</span>
        <span class="text-xs font-normal text-app-muted">{{ option.hint }}</span>
      </BaseButton>
    </div>
  </BaseDialog>
</template>

<script>
import AppIcon from '@core/components/AppIcon.vue'
import BaseButton from '@core/components/BaseButton.vue'
import BaseDialog from '@/components/common/BaseDialog.vue'
import { t } from '@/i18n.js'

export default {
  name: 'CreateDialog',
  components: { AppIcon, BaseButton, BaseDialog },
  computed: {
    kinds() {
      return [
        {
          value: 'feed',
          label: t('create.post'),
          icon: 'list-timeline',
          hint: t('create.postHint'),
        },
        { value: 'story', label: t('create.story'), icon: 'clock', hint: t('create.storyHint') },
      ]
    },
  },
  methods: {
    open() {
      this.$refs.dialog.open()
    },
    choose(kind) {
      this.$refs.dialog.close()
      this.$router.push(`/upload/${kind}`)
    },
  },
}
</script>
