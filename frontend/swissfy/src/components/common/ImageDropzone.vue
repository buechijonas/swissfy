<template>
  <label
    v-files.drop="onDrop"
    class="flex cursor-pointer flex-col items-center justify-center gap-2 rounded-box border-2 border-dashed text-app-muted transition-colors"
    :class="dragging ? 'border-primary bg-swissfy-highlight' : 'border-app-border bg-base-200'"
    @dragover.prevent="dragging = true"
    @dragleave.prevent="dragging = false"
  >
    <input v-files="emitFiles" type="file" :accept="accept" class="sr-only" :multiple="multiple" />
    <AppIcon name="picture" class="size-10!" />
    <span v-if="label" class="text-sm text-center px-4">{{ label }}</span>
  </label>
</template>

<script>
import filter from 'lodash-es/filter'
import map from 'lodash-es/map'
import some from 'lodash-es/some'
import take from 'lodash-es/take'
import AppIcon from '@core/components/AppIcon.vue'
import files from '@core/directives/files.js'

export default {
  name: 'ImageDropzone',
  components: { AppIcon },
  directives: { files },
  props: {
    label: { type: String, default: 'Bilder hierher ziehen oder klicken' },
    multiple: { type: Boolean, default: false },
    accept: { type: String, default: 'image/*' },
  },
  emits: ['select'],
  data() {
    return { dragging: false }
  },
  computed: {
    acceptedTypes() {
      return map(this.accept.split(','), (type) => type.trim().replace('*', ''))
    },
  },
  methods: {
    matchesType(file, type) {
      if (type.startsWith('.')) return file.name.toLowerCase().endsWith(type)
      return file.type.startsWith(type)
    },
    isAccepted(file) {
      return some(this.acceptedTypes, (type) => this.matchesType(file, type))
    },
    emitFiles(files) {
      const accepted = filter(files, this.isAccepted)
      if (!accepted.length) return
      this.$emit('select', this.multiple ? accepted : take(accepted, 1))
    },
    onDrop(dropped) {
      this.dragging = false
      this.emitFiles(dropped)
    },
  },
}
</script>
