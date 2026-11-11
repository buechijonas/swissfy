<template>
  <div class="mx-auto flex w-full max-w-160 flex-1 flex-col px-6 pb-16">
    <h2 class="my-6 text-xl font-light">Einstellungen</h2>
    <AppearanceSettings />
  </div>
</template>

<script>
import AppearanceSettings from '@/components/AppearanceSettings.vue'

export default {
  name: 'SettingsView',
  components: { AppearanceSettings },
}
</script>
