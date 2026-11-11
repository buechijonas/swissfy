<template>
  <div class="mb-10">
    <h3 class="my-4 text-xl">Darstellung</h3>
    <BaseCard
      class="flex flex-col items-center gap-4 p-6 text-center sm:flex-row sm:justify-between sm:text-left"
    >
      <p class="min-w-0 text-docs-muted">Erscheinungsbild der Oberfläche.</p>
      <div class="flex flex-wrap justify-center gap-2">
        <BaseButton
          v-for="option in THEME_OPTIONS"
          :key="option.value"
          size="sm"
          :variant="themeMode === option.value ? 'primary' : 'neutral'"
          @click="themeMode = option.value"
        >
          <AppIcon :name="option.icon" />
          {{ option.label }}
        </BaseButton>
      </div>
    </BaseCard>
  </div>

  <div class="mb-10">
    <h3 class="my-4 text-xl">Barrierefreiheit</h3>
    <BaseCard
      class="mb-4 flex flex-col items-center gap-4 p-6 text-center sm:flex-row sm:justify-between sm:text-left"
    >
      <p class="min-w-0 text-docs-muted">Legasthenie</p>
      <div class="flex flex-wrap justify-center gap-2">
        <BaseButton
          v-for="option in TOGGLE_OPTIONS"
          :key="option.label"
          size="sm"
          :variant="dyslexiaFont === option.value ? 'primary' : 'neutral'"
          @click="dyslexiaFont = option.value"
        >
          <AppIcon :name="option.icon" />
          {{ option.label }}
        </BaseButton>
      </div>
    </BaseCard>
    <BaseCard
      class="flex flex-col items-center gap-4 p-6 text-center sm:flex-row sm:justify-between sm:text-left"
    >
      <p class="min-w-0 text-docs-muted">Kontrastmodus</p>
      <div class="flex flex-wrap justify-center gap-2">
        <BaseButton
          v-for="option in TOGGLE_OPTIONS"
          :key="option.label"
          size="sm"
          :variant="contrastMode === option.value ? 'primary' : 'neutral'"
          @click="contrastMode = option.value"
        >
          <AppIcon :name="option.icon" />
          {{ option.label }}
        </BaseButton>
      </div>
    </BaseCard>
  </div>
</template>

<script>
import AppIcon from '@/components/common/AppIcon.vue'
import BaseButton from '@/components/common/BaseButton.vue'
import BaseCard from '@/components/common/BaseCard.vue'
import { contrastMode, dyslexiaFont, themeMode } from '@core/lib/appearance.js'

const THEME_OPTIONS = [
  { value: 'auto', icon: 'laptop', label: 'Auto' },
  { value: 'light', icon: 'brightness', label: 'Hell' },
  { value: 'dark', icon: 'moon-stars', label: 'Dunkel' },
]

const TOGGLE_OPTIONS = [
  { value: true, icon: 'check-circle', label: 'An' },
  { value: false, icon: 'cross', label: 'Aus' },
]

export default {
  name: 'AppearanceSettings',
  components: { AppIcon, BaseButton, BaseCard },
  data() {
    return { THEME_OPTIONS, TOGGLE_OPTIONS }
  },
  computed: {
    themeMode: {
      get() {
        return themeMode.value
      },
      set(value) {
        themeMode.value = value
      },
    },
    dyslexiaFont: {
      get() {
        return dyslexiaFont.value
      },
      set(value) {
        dyslexiaFont.value = value
      },
    },
    contrastMode: {
      get() {
        return contrastMode.value
      },
      set(value) {
        contrastMode.value = value
      },
    },
  },
}
</script>
