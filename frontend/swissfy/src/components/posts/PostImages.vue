<template>
  <div class="group relative">
    <slot />
    <div
      class="flex snap-x snap-mandatory items-center overflow-x-auto bg-base-200 [scrollbar-width:none]"
    >
      <div
        v-for="image in images"
        :key="image.url"
        v-intersect.parent="{ handler: (visible) => onSlide(image, visible), threshold: 0.6 }"
        v-reveal="requestedUrl === image.url"
        class="w-full shrink-0 snap-center"
      >
        <img
          class="max-h-[80dvh] w-full object-contain"
          :style="{ aspectRatio: image.aspect_ratio }"
          :src="image.url"
          alt=""
          loading="lazy"
        />
      </div>
    </div>
    <template v-if="images.length > 1">
      <BaseButton
        v-if="previous"
        variant="neutral"
        shape="circle"
        size="sm"
        class="absolute left-2 top-1/2 -translate-y-1/2 opacity-0 transition-opacity group-hover:opacity-100 max-sm:hidden"
        title="Vorheriges Bild"
        @click.stop="requestedUrl = previous.url"
      >
        <AppIcon name="angle-left" alt="Vorheriges Bild" />
      </BaseButton>
      <BaseButton
        v-if="next"
        variant="neutral"
        shape="circle"
        size="sm"
        class="absolute right-2 top-1/2 -translate-y-1/2 opacity-0 transition-opacity group-hover:opacity-100 max-sm:hidden"
        title="Nächstes Bild"
        @click.stop="requestedUrl = next.url"
      >
        <AppIcon name="angle-right" alt="Nächstes Bild" />
      </BaseButton>
      <div class="pointer-events-none absolute inset-x-0 bottom-2 flex justify-center gap-1.5">
        <span
          v-for="image in images"
          :key="image.url"
          class="size-1.5 rounded-full shadow"
          :class="image.url === activeUrl ? 'bg-white' : 'bg-white/50'"
        />
      </div>
    </template>
  </div>
</template>

<script>
import findIndex from 'lodash-es/findIndex'
import head from 'lodash-es/head'
import AppIcon from '@core/components/AppIcon.vue'
import BaseButton from '@core/components/BaseButton.vue'
import intersect from '@/directives/intersect.js'
import reveal from '@/directives/reveal.js'

export default {
  name: 'PostImages',
  components: { AppIcon, BaseButton },
  directives: { intersect, reveal },
  props: {
    images: { type: Array, required: true },
  },
  data() {
    return {
      activeUrl: head(this.images).url,
      requestedUrl: null,
    }
  },
  computed: {
    position() {
      return findIndex(this.images, { url: this.activeUrl })
    },
    previous() {
      return this.images[this.position - 1] ?? null
    },
    next() {
      return this.images[this.position + 1] ?? null
    },
  },
  watch: {
    activeUrl(url) {
      if (url === this.requestedUrl) this.requestedUrl = null
    },
  },
  methods: {
    onSlide(image, visible) {
      if (visible) this.activeUrl = image.url
    },
  },
}
</script>
