<template>
  <Transition
    enter-from-class="scale-50 opacity-0"
    leave-to-class="scale-125 opacity-0"
    enter-active-class="transition duration-200"
    leave-active-class="transition duration-300"
  >
    <AppIcon
      v-if="visible"
      name="heart-filled"
      class="pointer-events-none absolute top-1/2 left-1/2 z-10 -mt-12 -ml-12 size-24! text-error drop-shadow-lg"
    />
  </Transition>
</template>

<script>
import AppIcon from '@/components/common/AppIcon.vue'

const VISIBLE_MS = 600

export default {
  name: 'HeartBurst',
  components: { AppIcon },
  data() {
    return { visible: false }
  },
  beforeUnmount() {
    clearTimeout(this.timer)
  },
  methods: {
    show() {
      clearTimeout(this.timer)
      this.visible = true
      this.timer = setTimeout(() => (this.visible = false), VISIBLE_MS)
    },
  },
}
</script>
