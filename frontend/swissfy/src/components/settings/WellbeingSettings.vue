<template>
  <div class="mb-10">
    <h3 class="text-xl my-4">Suchtprävention</h3>
    <p class="text-swissfy-muted text-sm mb-4">
      Swissfy verzichtet standardmässig auf Funktionen, die dich länger am Bildschirm halten sollen.
      Du kannst sie hier bewusst einschalten. Gilt für dieses Gerät.
    </p>
    <SettingCard
      v-for="(toggle, index) in toggles"
      :key="toggle.label"
      :class="{ 'mt-4': index }"
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
</template>

<script>
import { markRaw } from 'vue'
import BaseSwitcher from '@/components/common/BaseSwitcher.vue'
import SettingCard from '@/components/settings/SettingCard.vue'
import { onOffOptions } from '@/data/settings.js'
import { videoAutoplay, videoLoop } from '@/lib/preferences.js'

export default {
  name: 'WellbeingSettings',
  components: { BaseSwitcher, SettingCard },
  data() {
    return {
      onOffOptions,
      toggles: markRaw([
        {
          setting: videoAutoplay,
          label: 'Autoplay',
          hint: 'Wenn an, starten Videos von selbst und ohne Ton, sobald du zu ihnen scrollst.',
        },
        {
          setting: videoLoop,
          label: 'Wiederholen',
          hint: 'Wenn an, beginnen Videos am Ende automatisch von vorne.',
        },
      ]),
    }
  },
}
</script>
