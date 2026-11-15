<template>
  <div class="flex flex-col h-[calc(100dvh-var(--mobile-chrome-height))] lg:h-full">
    <BaseBreadcrumbs :items="breadcrumbs" />
    <div class="flex flex-col flex-1 min-h-0 px-6">
      <ChatConversation :key="username" :username="username" />
    </div>
  </div>
  <BaseFooter />
</template>

<script>
import BaseBreadcrumbs from '@/components/common/BaseBreadcrumbs.vue'
import BaseFooter from '@/components/common/BaseFooter.vue'
import ChatConversation from '@/components/chats/ChatConversation.vue'
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
