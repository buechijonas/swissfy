<template>
  <BaseDialog ref="dialog" title="Was möchtest du hochladen?">
    <div class="grid grid-cols-2 gap-3">
      <BaseButton
        v-for="option in kinds"
        :key="option.value"
        class="h-auto flex-col gap-2 py-6"
        @click="choose(option.value)"
      >
        <AppIcon :name="option.icon" class="size-6!" />
        <span class="text-base">{{ option.label }}</span>
        <span class="text-xs font-normal text-swissfy-muted">{{ option.hint }}</span>
      </BaseButton>
    </div>
  </BaseDialog>
</template>

<script>
import AppIcon from '@/components/common/AppIcon.vue'
import BaseButton from '@/components/common/BaseButton.vue'
import BaseDialog from '@/components/common/BaseDialog.vue'

export default {
  name: 'CreateDialog',
  components: { AppIcon, BaseButton, BaseDialog },
  data() {
    return {
      kinds: [
        { value: 'feed', label: 'Feed', icon: 'list-timeline', hint: 'Bleibt in deinem Profil' },
        { value: 'story', label: 'Story', icon: 'clock', hint: 'Verschwindet nach 24 Stunden' },
      ],
    }
  },
  methods: {
    open() {
      this.$refs.dialog.open()
    },
    choose(kind) {
      this.$refs.dialog.close()
      this.$router.push(`/upload/${kind}`)
    },
  },
}
</script>
