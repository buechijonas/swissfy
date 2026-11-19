<template>
  <div class="mb-10">
    <h3 class="my-4 text-xl">{{ $t('wellbeing.title') }}</h3>
    <p class="mb-4 text-sm text-app-muted">
      {{ $t('wellbeing.intro') }}
    </p>
    <div class="flex flex-col gap-4">
      <SettingCard
        v-for="toggle in toggles"
        :key="toggle.label"
        :title="toggle.label"
        :hint="toggle.hint"
      >
        <BaseSwitcher
          class="shrink-0 flex-wrap justify-center gap-2"
          size="sm"
          :options="onOffOptions"
          :active="toggle.setting.value"
          @select="toggle.setting.value = $event"
        />
      </SettingCard>
    </div>
  </div>
</template>

<script>
import { markRaw } from 'vue'
import BaseSwitcher from '@/components/common/BaseSwitcher.vue'
import SettingCard from '@/components/settings/SettingCard.vue'
import { onOffOptions } from '@/data/settings.js'
import { t } from '@/i18n.js'
import { videoAutoplay, videoLoop } from '@/lib/preferences.js'

export default {
  name: 'WellbeingSettings',
  components: { BaseSwitcher, SettingCard },
  computed: {
    onOffOptions,
    toggles() {
      return markRaw([
        {
          setting: videoAutoplay,
          label: t('wellbeing.autoplay'),
          hint: t('wellbeing.autoplayHint'),
        },
        {
          setting: videoLoop,
          label: t('wellbeing.loop'),
          hint: t('wellbeing.loopHint'),
        },
      ])
    },
  },
}
</script>
