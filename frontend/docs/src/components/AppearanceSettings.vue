<template>
  <div class="mb-10">
    <h3 class="my-4 text-xl">{{ $t('display.title') }}</h3>
    <BaseCard
      inset
      class="flex flex-col items-center gap-4 p-6 text-center sm:flex-row sm:justify-between sm:text-left"
    >
      <p class="min-w-0 text-app-muted">{{ $t('display.appearance') }}</p>
      <div class="flex flex-wrap justify-center gap-2">
        <BaseButton
          v-for="option in themeOptions"
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
    <h3 class="my-4 text-xl">{{ $t('display.language') }}</h3>
    <BaseCard
      inset
      class="flex flex-col items-center gap-4 p-6 text-center sm:flex-row sm:justify-between sm:text-left"
    >
      <p class="min-w-0 text-app-muted">{{ $t('display.languageHint') }}</p>
      <LanguageSelect :label="$t('display.language')" />
    </BaseCard>
  </div>

  <div class="mb-10">
    <h3 class="my-4 text-xl">{{ $t('display.accessibility') }}</h3>
    <BaseCard
      inset
      class="mb-4 flex flex-col items-center gap-4 p-6 text-center sm:flex-row sm:justify-between sm:text-left"
    >
      <p class="min-w-0 text-app-muted">{{ $t('display.dyslexia') }}</p>
      <div class="flex flex-wrap justify-center gap-2">
        <BaseButton
          v-for="option in toggleOptions"
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
      inset
      class="flex flex-col items-center gap-4 p-6 text-center sm:flex-row sm:justify-between sm:text-left"
    >
      <p class="min-w-0 text-app-muted">{{ $t('display.contrast') }}</p>
      <div class="flex flex-wrap justify-center gap-2">
        <BaseButton
          v-for="option in toggleOptions"
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
import AppIcon from '@core/components/AppIcon.vue'
import BaseButton from '@core/components/BaseButton.vue'
import BaseCard from '@core/components/BaseCard.vue'
import { contrastMode, dyslexiaFont, themeMode } from '@core/lib/appearance.js'
import LanguageSelect from '@core/components/LanguageSelect.vue'
import { t } from '@/i18n.js'

function themeOptions() {
  return [
    { value: 'auto', icon: 'laptop', label: t('display.auto') },
    { value: 'light', icon: 'brightness', label: t('display.light') },
    { value: 'dark', icon: 'moon-stars', label: t('display.dark') },
  ]
}

function toggleOptions() {
  return [
    { value: true, icon: 'check', label: t('display.on') },
    { value: false, icon: 'cross', label: t('display.off') },
  ]
}

export default {
  name: 'AppearanceSettings',
  components: { AppIcon, BaseButton, BaseCard, LanguageSelect },
  computed: {
    themeOptions,
    toggleOptions,
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
