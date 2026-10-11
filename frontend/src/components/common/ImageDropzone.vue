<template>
  <label
    class="flex cursor-pointer flex-col items-center justify-center gap-2 rounded-box border-2 border-dashed text-swissfy-muted transition-colors"
    :class="dragging ? 'border-primary bg-swissfy-highlight' : 'border-swissfy-border bg-base-200'"
    @dragover.prevent="dragging = true"
    @dragleave.prevent="dragging = false"
    @drop.prevent="onDrop"
  >
    <input type="file" accept="image/*" class="sr-only" :multiple="multiple" @change="onChange" />
    <AppIcon name="picture" class="size-10!" />
    <span v-if="label" class="text-sm text-center px-4">{{ label }}</span>
  </label>
</template>

<script>
import AppIcon from '@/components/common/AppIcon.vue'

export default {
  name: 'ImageDropzone',
  components: { AppIcon },
  props: {
    label: { type: String, default: 'Bilder hierher ziehen oder klicken' },
    multiple: { type: Boolean, default: false },
  },
  emits: ['select'],
  data() {
    return { dragging: false }
  },
  methods: {
    emitImages(files) {
      const images = files.filter((file) => file.type.startsWith('image/'))
      if (images.length) this.$emit('select', this.multiple ? images : images.slice(0, 1))
    },
    onChange(event) {
      const files = [...event.target.files]
      event.target.value = ''
      this.emitImages(files)
    },
    onDrop(event) {
      this.dragging = false
      this.emitImages([...event.dataTransfer.files])
    },
  },
}
</script>
