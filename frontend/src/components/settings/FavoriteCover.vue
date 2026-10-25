<template>
  <img
    v-if="item.cover"
    class="aspect-2/3 w-full rounded-box object-cover bg-base-200"
    :src="item.cover"
    :alt="item.title"
    loading="lazy"
  />
  <div
    v-else
    class="flex aspect-2/3 w-full items-center justify-center rounded-box bg-base-200 text-swissfy-muted"
  >
    <AppIcon :name="icon" class="size-8!" :alt="item.title" />
  </div>
</template>

<script>
import AppIcon from '@/components/common/AppIcon.vue'

export default {
  name: 'FavoriteCover',
  components: { AppIcon },
  props: {
    item: { type: Object, required: true },
    icon: { type: String, required: true },
  },
}
</script>
