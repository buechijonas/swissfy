<template>
  <SelectMenu
    :model-value="selected"
    :options="options"
    :label="label"
    icon="globe"
    @update:model-value="selectLanguage"
  />
</template>

<script>
import SelectMenu from '@core/components/SelectMenu.vue'
import { LANGUAGE_OPTIONS, language, selectLanguage } from '@core/lib/language.js'

export default {
  name: 'LanguageSelect',
  components: { SelectMenu },
  props: {
    label: { type: String, required: true },
  },
  data() {
    return {
      options: LANGUAGE_OPTIONS.map((option) => ({ ...option, lang: option.value })),
    }
  },
  computed: {
    selected() {
      return language.value
    },
  },
  methods: {
    selectLanguage,
  },
}
</script>
