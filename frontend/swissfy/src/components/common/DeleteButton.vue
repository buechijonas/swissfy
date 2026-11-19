<template>
  <BaseButton variant="error" outline shape="square" size="sm" :title="$t('common.delete')">
    <AppIcon name="trash" :alt="$t('common.delete')" />
  </BaseButton>
</template>

<script>
import AppIcon from '@core/components/AppIcon.vue'
import BaseButton from '@core/components/BaseButton.vue'

export default {
  name: 'DeleteButton',
  components: { BaseButton, AppIcon },
}
</script>
