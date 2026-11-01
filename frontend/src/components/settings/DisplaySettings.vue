<template>
  <div class="mb-10">
    <h3 class="text-xl my-4">Darstellung</h3>
    <BaseCard
      class="p-6 flex flex-col items-center text-center gap-4"
      :class="{ 'sm:flex-row sm:items-center sm:text-left sm:justify-between': !dyslexiaFont }"
    >
      <p class="text-swissfy-muted min-w-0">Erscheinungsbild der Oberfläche.</p>
      <BaseSwitcher
        class="flex-wrap justify-center gap-2"
        size="sm"
        :options="themeOptions"
        :active="themeMode"
        @select="themeMode = $event"
      />
    </BaseCard>
  </div>

  <div class="mb-10">
    <h3 class="text-xl my-4">Design</h3>
    <BaseCard
      class="p-6 flex flex-col items-center text-center gap-4 sm:flex-row sm:items-center sm:text-left sm:justify-between"
    >
      <p class="text-swissfy-muted min-w-0">Stil der Oberfläche.</p>
      <div class="flex flex-wrap justify-center gap-2">
        <BaseSwitcher
          v-for="(options, index) in designGroups"
          :key="index"
          class="gap-2"
          item-class="max-sm:btn-sm"
          vertical
          :options="options"
          :active="design"
          @select="design = $event"
        />
      </div>
    </BaseCard>
    <div v-if="limitedDesigns.includes(design)" role="status" class="alert alert-warning mt-4">
      <AppIcon name="shield-exclamation" />
      <span>
        Dieses Design kann die Barrierefreiheit einschränken, etwa bei Kontrast, Lesbarkeit und
        Animationen. Am besten für Barrierefreiheit optimiert ist das Standard-Design.
      </span>
    </div>
  </div>

  <div class="mb-10">
    <h3 class="text-xl my-4">Barrierefreiheit</h3>
    <BaseCard
      class="p-6 flex flex-col items-center text-center gap-4 mb-4 sm:flex-row sm:items-center sm:text-left sm:justify-between"
    >
      <p class="text-swissfy-muted min-w-0">Legasthenie</p>
      <BaseSwitcher
        class="flex-wrap justify-center gap-2"
        size="sm"
        :options="onOffOptions"
        :active="dyslexiaFont"
        @select="dyslexiaFont = $event"
      />
    </BaseCard>
    <BaseCard
      class="p-6 flex flex-col items-center text-center gap-4 sm:flex-row sm:items-center sm:text-left sm:justify-between"
    >
      <p class="text-swissfy-muted min-w-0">Kontrastmodus</p>
      <BaseSwitcher
        class="flex-wrap justify-center gap-2"
        size="sm"
        :options="onOffOptions"
        :active="contrastMode"
        @select="contrastMode = $event"
      />
    </BaseCard>
  </div>
</template>

<script>
import AppIcon from '@/components/common/AppIcon.vue'
import BaseCard from '@/components/common/BaseCard.vue'
import BaseSwitcher from '@/components/common/BaseSwitcher.vue'
import { designGroups, limitedDesigns, onOffOptions, themeOptions } from '@/data/settings.js'
import { contrastMode, design, dyslexiaFont, themeMode } from '@/lib/preferences.js'

function preference(setting) {
  return {
    get() {
      return setting.value
    },
    set(value) {
      setting.value = value
    },
  }
}

export default {
  name: 'DisplaySettings',
  components: { AppIcon, BaseCard, BaseSwitcher },
  data() {
    return { designGroups, limitedDesigns, onOffOptions, themeOptions }
  },
  computed: {
    themeMode: preference(themeMode),
    design: preference(design),
    dyslexiaFont: preference(dyslexiaFont),
    contrastMode: preference(contrastMode),
  },
}
</script>
