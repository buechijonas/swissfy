<template>
  <BaseCard class="p-6">
    <h3 class="text-lg font-semibold">Timeline</h3>

    <p v-if="!entries.length" class="mt-4 text-swissfy-muted">Noch keine Posts in diesem Album.</p>
    <ol v-else class="mt-6">
      <li v-for="(entry, index) in entries" :key="entry.id" data-entry class="flex gap-4">
        <div class="flex w-3 shrink-0 flex-col items-center">
          <span
            class="mt-1.5 size-3 shrink-0 rounded-full"
            :class="entry.date ? 'bg-primary' : 'bg-swissfy-border'"
          ></span>
          <span
            v-if="index < entries.length - 1"
            class="mt-1 w-0.5 flex-1 bg-swissfy-border"
          ></span>
        </div>
        <div class="flex-1 min-w-0" :class="{ 'pb-8': index < entries.length - 1 }">
          <time v-if="entry.date" :datetime="entry.date" class="font-semibold">
            {{ formatDate(entry.date) }}
          </time>
          <span v-else class="text-swissfy-muted">Ohne Datum</span>
          <div class="mt-2 flex items-start gap-4">
            <PostTile :post="entry.post" class="w-28 shrink-0 overflow-hidden rounded-box" />
            <p class="flex-1 min-w-0 break-words pt-1">{{ entry.title }}</p>
            <BaseButton
              v-if="editable"
              variant="ghost"
              shape="square"
              title="Bearbeiten"
              @click="$emit('edit-entry', entry)"
            >
              <AppIcon name="pencil" alt="Bearbeiten" class="size-5!" />
            </BaseButton>
          </div>
        </div>
      </li>
    </ol>
  </BaseCard>
</template>

<script>
import AppIcon from '@/components/common/AppIcon.vue'
import BaseButton from '@/components/common/BaseButton.vue'
import BaseCard from '@/components/common/BaseCard.vue'
import PostTile from '@/components/posts/PostTile.vue'
import { formatDate } from '@/lib/time.js'

export default {
  name: 'AlbumTimeline',
  components: { AppIcon, BaseButton, BaseCard, PostTile },
  props: {
    entries: { type: Array, required: true },
    editable: { type: Boolean, default: false },
  },
  emits: ['edit-entry'],
  methods: {
    formatDate,
  },
}
</script>
