<template>
  <div class="mb-10">
    <h3 class="my-4 text-xl">{{ $t('display.title') }}</h3>
    <BaseCard
      class="flex flex-col items-center gap-4 p-6 text-center"
      :class="{ 'sm:flex-row sm:items-center sm:justify-between sm:text-left': !dyslexiaFont }"
    >
      <p class="min-w-0 text-app-muted">{{ $t('display.appearance') }}</p>
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
    <h3 class="my-4 text-xl">{{ $t('display.language') }}</h3>
    <BaseCard
      class="flex flex-col items-center gap-4 p-6 text-center sm:flex-row sm:items-center sm:justify-between sm:text-left"
    >
      <p class="min-w-0 text-app-muted">{{ $t('display.languageHint') }}</p>
      <LanguageSelect :label="$t('display.language')" />
    </BaseCard>
  </div>

  <div class="mb-10">
    <h3 class="my-4 text-xl">{{ $t('display.design') }}</h3>
    <div class="grid grid-cols-3 gap-3">
      <BaseButton
        v-for="option in designOptions"
        :key="option.value"
        class="app-design-tile aspect-square h-auto flex-col gap-3 px-2 text-center leading-tight whitespace-normal"
        :variant="design === option.value ? 'primary' : 'neutral'"
        :aria-pressed="design === option.value"
        @click="design = option.value"
      >
        <AppIcon :name="option.icon" class="size-8!" />
        {{ option.label }}
      </BaseButton>
    </div>
    <div v-if="limitedDesigns.includes(design)" role="status" class="mt-4 alert alert-warning">
      <AppIcon name="shield-exclamation" />
      <span>{{ $t('display.limitedDesign') }}</span>
    </div>
  </div>

  <div class="mb-10">
    <h3 class="my-4 text-xl">{{ $t('display.accessibility') }}</h3>
    <BaseCard
      class="mb-4 flex flex-col items-center gap-4 p-6 text-center sm:flex-row sm:items-center sm:justify-between sm:text-left"
    >
      <p class="min-w-0 text-app-muted">{{ $t('display.dyslexia') }}</p>
      <BaseSwitcher
        class="flex-wrap justify-center gap-2"
        size="sm"
        :options="onOffOptions"
        :active="dyslexiaFont"
        @select="dyslexiaFont = $event"
      />
    </BaseCard>
    <BaseCard
      class="flex flex-col items-center gap-4 p-6 text-center sm:flex-row sm:items-center sm:justify-between sm:text-left"
    >
      <p class="min-w-0 text-app-muted">{{ $t('display.contrast') }}</p>
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
import AppIcon from '@core/components/AppIcon.vue'
import BaseButton from '@core/components/BaseButton.vue'
import BaseCard from '@core/components/BaseCard.vue'
import LanguageSelect from '@core/components/LanguageSelect.vue'
import BaseSwitcher from '@/components/common/BaseSwitcher.vue'
import { designOptions, limitedDesigns, onOffOptions, themeOptions } from '@/data/settings.js'
import { contrastMode, design, dyslexiaFont, themeMode } from '@/lib/preferences.js'

export default {
  name: 'DisplaySettings',
  components: { AppIcon, BaseButton, BaseCard, BaseSwitcher, LanguageSelect },
  data() {
    return { limitedDesigns }
  },
  computed: {
    designOptions,
    onOffOptions,
    themeOptions,
    themeMode: {
      get() {
        return themeMode.value
      },
      set(value) {
        themeMode.value = value
      },
    },
    design: {
      get() {
        return design.value
      },
      set(value) {
        design.value = value
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
