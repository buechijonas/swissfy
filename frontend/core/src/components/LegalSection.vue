<template>
  <section class="flex flex-col gap-3">
    <h2 v-if="title" class="text-xl">{{ title }}</h2>
    <p v-if="text" class="text-app-muted"><LinkedText :text="text" /></p>
    <p v-for="line in lines" :key="line" class="text-app-muted">
      <LinkedText :text="line" />
    </p>
    <ul v-if="items.length" class="flex flex-col gap-3 ps-6">
      <li v-for="item in items" :key="item.title">
        <span class="font-medium">{{ item.title }}</span>
        <ul class="ps-6">
          <li class="text-app-muted"><LinkedText :text="item.description" /></li>
        </ul>
      </li>
    </ul>
  </section>
</template>

<script>
import LinkedText from '@core/components/LinkedText.vue'

export default {
  name: 'LegalSection',
  components: { LinkedText },
  props: {
    title: { type: String, default: '' },
    text: { type: String, default: '' },
    lines: { type: Array, default: () => [] },
    items: { type: Array, default: () => [] },
  },
}
</script>

<style scoped>
ul {
  list-style-type: disc;
}

ul ul {
  list-style-type: circle;
}
</style>
