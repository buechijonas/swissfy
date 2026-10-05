<template>
  <section class="my-6">
    <h3 v-if="title" class="font-medium">{{ title }}</h3>
    <p v-if="text" class="font-light">{{ text }}</p>
    <p v-for="line in lines" :key="line" class="font-light">{{ line }}</p>
    <ul v-if="items.length" class="ps-6 mt-4">
      <li v-for="item in items" :key="item.title" class="mb-3">
        <span class="font-medium">{{ item.title }}</span>
        <ul class="ps-6">
          <li class="font-light">{{ item.description }}</li>
        </ul>
      </li>
    </ul>
  </section>
</template>

<script>
export default {
  name: 'LegalSection',
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
