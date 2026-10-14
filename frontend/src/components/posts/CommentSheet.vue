<template>
  <BaseDialog
    ref="dialog"
    title="Kommentare"
    class="modal-bottom sm:modal-middle"
    box-class="h-[80dvh] max-w-150 pb-0"
  >
    <div class="-mx-6 min-h-0 flex-1 overflow-y-auto px-6 pb-6">
      <CommentSection
        v-if="opened"
        :url="`/api/posts/${postId}/comments/`"
        @created="$emit('created')"
        @deleted="$emit('deleted', $event)"
      />
    </div>
  </BaseDialog>
</template>

<script>
import BaseDialog from '@/components/common/BaseDialog.vue'
import CommentSection from '@/components/posts/CommentSection.vue'

export default {
  name: 'CommentSheet',
  components: { BaseDialog, CommentSection },
  props: {
    postId: { type: String, required: true },
  },
  emits: ['created', 'deleted'],
  data() {
    return { opened: false }
  },
  methods: {
    open() {
      this.opened = true
      this.$refs.dialog.open()
    },
  },
}
</script>
