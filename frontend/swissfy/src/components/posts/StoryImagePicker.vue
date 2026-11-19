<template>
  <div
    v-if="modelValue"
    class="relative mx-auto aspect-9/16 h-96 max-w-full overflow-hidden rounded-box bg-black"
  >
    <img :src="modelValue.preview" alt="" class="size-full object-contain" />
    <p
      v-if="caption.trim()"
      class="absolute inset-x-0 bottom-0 bg-black/50 px-4 py-3 text-center whitespace-pre-line text-white"
    >
      {{ caption }}
    </p>
    <BaseButton
      variant="neutral"
      shape="circle"
      size="sm"
      class="absolute top-2 right-2"
      :title="$t('upload.removeImage')"
      @click="clear"
    >
      <AppIcon name="cross" :alt="$t('upload.removeImage')" />
    </BaseButton>
  </div>
  <ImageDropzone v-else class="h-56" :label="$t('upload.storyDrop')" @select="select" />
  <ErrorText :message="error" class="mt-2" />
</template>

<script>
import AppIcon from '@core/components/AppIcon.vue'
import BaseButton from '@core/components/BaseButton.vue'
import ErrorText from '@core/components/ErrorText.vue'
import ImageDropzone from '@/components/common/ImageDropzone.vue'
import { t } from '@/i18n.js'
import { compressImage } from '@/lib/image.js'

export default {
  name: 'StoryImagePicker',
  components: { AppIcon, BaseButton, ErrorText, ImageDropzone },
  props: {
    modelValue: { type: Object, default: null },
    caption: { type: String, required: true },
  },
  emits: ['update:modelValue'],
  data() {
    return { error: null }
  },
  beforeUnmount() {
    this.revoke()
  },
  methods: {
    async select([file]) {
      this.error = null
      try {
        const blob = await compressImage(file)
        this.revoke()
        this.$emit('update:modelValue', { blob, preview: URL.createObjectURL(blob) })
      } catch {
        this.error = t('upload.imageUnreadable')
      }
    },
    clear() {
      this.revoke()
      this.$emit('update:modelValue', null)
    },
    revoke() {
      if (this.modelValue) URL.revokeObjectURL(this.modelValue.preview)
    },
  },
}
</script>
