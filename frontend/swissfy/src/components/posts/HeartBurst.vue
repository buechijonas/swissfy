<template>
  <span
    v-if="burst"
    :key="burst"
    class="pointer-events-none absolute top-1/2 left-1/2 z-10 -mt-12 -ml-12 animate-heart-burst"
    @animationend.self="burst = 0"
  >
    <AppIcon name="heart-filled" class="size-24! text-error drop-shadow-lg" />
  </span>
</template>

<script>
import AppIcon from '@core/components/AppIcon.vue'

export default {
  name: 'HeartBurst',
  components: { AppIcon },
  data() {
    return { burst: 0 }
  },
  methods: {
    show() {
      this.burst += 1
    },
  },
}
</script>
