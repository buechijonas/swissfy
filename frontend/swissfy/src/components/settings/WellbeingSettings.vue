<template>
  <div class="mb-10">
    <h3 class="text-xl my-4">{{ $t('wellbeing.title') }}</h3>
    <p class="text-app-muted text-sm mb-4">
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
          class="flex-wrap justify-center gap-2 shrink-0"
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
import { videoAutoplay, videoLoop } from '@/lib/preferences.js'
import { t } from '@/i18n.js'

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
