<template>
  <div class="flex h-[calc(100dvh-var(--mobile-chrome-height))] flex-col lg:h-full">
    <BaseBreadcrumbs :items="breadcrumbs" />
    <div class="flex min-h-0 flex-1 flex-col px-6">
      <ChatConversation :key="username" :username="username" />
    </div>
  </div>
  <BaseFooter />
</template>

<script>
import ChatConversation from '@/components/chats/ChatConversation.vue'
import BaseBreadcrumbs from '@/components/common/BaseBreadcrumbs.vue'
import BaseFooter from '@/components/common/BaseFooter.vue'
import { t } from '@/i18n.js'

export default {
  name: 'ChatView',
  components: { BaseBreadcrumbs, BaseFooter, ChatConversation },
  computed: {
    username() {
      return this.$route.params.username
    },
    breadcrumbs() {
      return [
        { label: t('chats.tabChats'), to: '/chats' },
        { label: this.username, to: `/chats/${encodeURIComponent(this.username)}` },
      ]
    },
  },
}
</script>
