<template>
  <footer
    class="flex lg:hidden h-12 w-full shrink-0 items-center justify-evenly bg-base-100 border-t border-swissfy-border border-solid max-lg:sticky max-lg:bottom-0 max-lg:mt-auto lg:h-auto lg:w-auto lg:justify-center lg:bg-transparent lg:border-0 lg:mt-6 lg:mb-6"
  >
    <RouterLink
      v-for="link in footerLinks"
      :key="link.label"
      :to="link.to"
      class="max-lg:btn max-lg:btn-square max-lg:btn-ghost max-lg:btn-sm lg:card mx-0 lg:mx-2 lg:bg-base-100 lg:shadow-none lg:border-swissfy-border lg:border-solid lg:border-1"
    >
      <div
        class="lg:card-body flex flex-row items-center justify-center text-xs text-swissfy-slate p-0 lg:p-4"
      >
        <AppIcon :name="link.icon" :alt="link.label" class="size-5! lg:size-4! lg:m-auto" />
        <p class="hidden lg:inline font-medium">{{ link.label }}</p>
      </div>
    </RouterLink>
  </footer>
</template>

<script>
import { RouterLink } from 'vue-router'
import AppIcon from '@/components/common/AppIcon.vue'
import { footerLinks } from '@/data/footer.js'

export default {
  name: 'BaseFooter',
  components: { RouterLink, AppIcon },
  data() {
    return { footerLinks }
  },
}
</script>
